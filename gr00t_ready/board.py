# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Kanban-style progress board, derived from repo state.

Status per item:
  done         scored in results/results.yaml (invalid = feature absent, excluded from totals)
  blocked      item id mentioned in BLOCKERS.md
  in_progress  a test file exists under tests/ but no result recorded yet
  todo         nothing yet
"""

from __future__ import annotations

import datetime
import re
from pathlib import Path

from .loader import Category, RobotEvaluation

STATUS_ICONS = {
    "done": "✅",
    "na": "➖",
    "skipped": "⏭️",
    "blocked": "⛔",
    "in_progress": "🚧",
    "todo": "⚪",
}
STATUS_LABELS = {
    "done": "Done",
    "na": "Invalid",
    "skipped": "Skipped",
    "blocked": "Blocked",
    "in_progress": "In Progress",
    "todo": "To Do",
}
ORDER = ["todo", "in_progress", "blocked", "done", "na", "skipped"]


def item_status(item_id: str, evaluation: RobotEvaluation, robot_dir: Path,
                blocked_ids: set[str]) -> str:
    result = evaluation.results.get(item_id)
    if result is not None:
        if result.is_skipped:
            return "skipped"
        return "na" if result.is_na else "done"
    if item_id in blocked_ids:
        return "blocked"
    stem = f"test_{item_id.replace('-', '_')}"
    if any((robot_dir / "tests").glob(f"{stem}.*")) or _in_manual_checklist(item_id, robot_dir):
        return "in_progress"
    return "todo"


def _in_manual_checklist(item_id: str, robot_dir: Path) -> bool:
    checklist = robot_dir / "tests" / "manual_checklist.md"
    return checklist.exists() and item_id in checklist.read_text()


def load_blocked_ids(robot_dir: Path) -> set[str]:
    blockers = robot_dir / "BLOCKERS.md"
    if not blockers.exists():
        return set()
    return set(re.findall(r"\b(?:HW|SW|NT)-[A-Z]+-\d+\b", blockers.read_text()))


def must_have_met(item, result):
    """True/False if a must-have item met its required level; None if not yet
    assessed (untested, or excluded as invalid/skipped). Non-must-have → None."""
    if not item.must_have:
        return None
    if result is None or result.is_na or result.score is None:
        return None
    return result.score >= item.must_have_level


def board_data(categories: list[Category], evaluation: RobotEvaluation,
               robot_dir: Path) -> dict:
    """Board state as plain data (consumed by the web dashboard)."""
    media_root = robot_dir / "results" / "media"
    output_root = robot_dir / "tests" / "output"

    def cited_outputs(*texts):
        """Output files referenced in evidence/notes that actually exist."""
        names = set()
        for t in texts:
            for m in re.findall(r"[\w.-]+\.(?:txt|log)", t or ""):
                if (output_root / m).is_file():
                    names.add(m)
        return sorted(names)
    blocked_ids = load_blocked_ids(robot_dir)
    tier1 = evaluation.tier not in ("self-serve", "self_serve", "selfserve")
    counts = {s: 0 for s in ORDER}
    cats = []
    for cat in categories:
        if cat.tier1_only and not tier1:
            continue
        items = []
        for item in cat.items:
            status = item_status(item.id, evaluation, robot_dir, blocked_ids)
            counts[status] += 1
            result = evaluation.results.get(item.id)
            items.append({
                "id": item.id,
                "name": item.name,
                "method": item.method,
                "automation": item.automation,
                "conditional": item.conditional,
                "levels": {str(k): v for k, v in item.levels.items()},
                "max": item.max_score,
                "status": status,
                "score": (None if result is None or result.is_na else result.score),
                "evidence": result.evidence if result else "",
                "notes": result.notes if result else "",
                "media": sorted(
                    f.name for f in (media_root / item.id).iterdir() if f.is_file()
                ) if (media_root / item.id).is_dir() else [],
                "outputs": cited_outputs(
                    result.evidence if result else "", result.notes if result else ""),
                "must_have": item.must_have,
                "must_have_level": item.must_have_level,
                "must_have_met": must_have_met(item, result),
            })
        cats.append({"id": cat.id, "name": cat.name, "section": cat.section,
                     "items": items})
    total = sum(counts.values())
    finished = counts["done"] + counts["na"] + counts["skipped"]
    # must-have compliance: certification requires every must-have item to reach
    # its required level. met=True/False when tested; None when not yet assessed.
    mh = [(c, i) for c in cats for i in c["items"] if i["must_have"]]
    mh_met = [i["id"] for _, i in mh if i["must_have_met"] is True]
    mh_unmet = [i["id"] for _, i in mh if i["must_have_met"] is False]
    mh_pending = [i["id"] for _, i in mh if i["must_have_met"] is None]
    # point totals, same semantics as scoring.py: invalid items excluded from
    # both sides; untested items count toward possible
    achieved = possible = 0
    for c in cats:
        for i in c["items"]:
            if i["status"] in ("na", "skipped"):
                continue
            possible += i["max"]
            if i["score"] is not None:
                achieved += i["score"]
    return {
        "robot": evaluation.robot,
        "tier": evaluation.tier,
        "evaluation_version": evaluation.evaluation_version,
        "date": evaluation.date,
        "counts": counts,
        "total": total,
        "finished": finished,
        "score_achieved": achieved,
        "score_possible": possible,
        "must_have": {
            "total": len(mh),
            "met": len(mh_met),
            "unmet": mh_unmet,
            "pending": mh_pending,
        },
        "categories": cats,
    }


def render_board(categories: list[Category], evaluation: RobotEvaluation,
                 robot_dir: Path) -> str:
    blocked_ids = load_blocked_ids(robot_dir)
    tier1 = evaluation.tier not in ("self-serve", "self_serve", "selfserve")
    cats = [c for c in categories if tier1 or not c.tier1_only]

    rows: dict[str, list] = {s: [] for s in ORDER}
    for cat in cats:
        for item in cat.items:
            status = item_status(item.id, evaluation, robot_dir, blocked_ids)
            rows[status].append((cat, item))

    total = sum(len(v) for v in rows.values())
    finished = len(rows["done"]) + len(rows["na"]) + len(rows["skipped"])
    achieved = sum(
        r.score for r in evaluation.results.values() if r.score is not None
    )
    possible_done = sum(
        item.max_score
        for cat, item in rows["done"]
    )
    bar_len = 30
    filled = round(bar_len * finished / total) if total else 0
    bar = "█" * filled + "░" * (bar_len - filled)

    mh_items = [(c, i) for c in cats for i in c.items if i.must_have]
    mh_unmet = [i.id for c, i in mh_items
                if must_have_met(i, evaluation.results.get(i.id)) is False]
    mh_met = sum(1 for c, i in mh_items
                 if must_have_met(i, evaluation.results.get(i.id)) is True)
    mh_line = (f"**Must-haves:** {mh_met}/{len(mh_items)} met"
               + (f" — ⛔ UNMET: {', '.join(mh_unmet)}" if mh_unmet else " ✅"))

    lines = [
        f"# Test Board — {evaluation.robot}",
        "",
        f"**Evaluation version:** {evaluation.evaluation_version}",
        "",
        f"_Generated {datetime.date.today().isoformat()} — regenerate with_ "
        f"`python3 -m gr00t_ready board robots/{evaluation.robot}`",
        "",
        f"**Progress:** `{bar}` {finished}/{total} items ({100*finished//total if total else 0}%)",
        "",
        f"**Score so far:** {achieved}/{possible_done} points on completed items",
        "",
        mh_line,
        "",
        "| " + " | ".join(f"{STATUS_ICONS[s]} {STATUS_LABELS[s]}" for s in ORDER) + " |",
        "| " + " | ".join("---" for _ in ORDER) + " |",
        "| " + " | ".join(str(len(rows[s])) for s in ORDER) + " |",
    ]

    for status in ("in_progress", "blocked"):
        if rows[status]:
            lines += ["", f"## {STATUS_ICONS[status]} {STATUS_LABELS[status]}", ""]
            for cat, item in rows[status]:
                lines.append(f"- **{item.id}** {item.name} _({cat.name})_")

    lines += ["", "## All items", ""]
    section = None
    for cat in cats:
        if cat.section != section:
            section = cat.section
            lines += [f"### {section}", ""]
        lines += [
            f"#### {cat.name}",
            "",
            "| Status | ID | Item | Mode | Score | Evidence / Notes |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for item in cat.items:
            status = item_status(item.id, evaluation, robot_dir, blocked_ids)
            result = evaluation.results.get(item.id)
            if status == "done":
                score = f"{result.score}/{item.max_score}"
                detail = "; ".join(p for p in (result.evidence, result.notes) if p)
            elif status == "na":
                score = "invalid"
                detail = result.notes or "feature not present on this platform"
            elif status == "skipped":
                score = "skipped"
                detail = result.notes or "not testable now — deferred"
            else:
                score = ""
                detail = ""
            mhm = must_have_met(item, result)
            mtag = ("⭐✗ " if mhm is False else "⭐ " if item.must_have else "")
            lines.append(
                f"| {STATUS_ICONS[status]} {STATUS_LABELS[status]} | {item.id} "
                f"| {mtag}{item.name} | {item.automation} | {score} | {detail} |"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_board_terminal(categories: list[Category], evaluation: RobotEvaluation,
                          robot_dir: Path) -> str:
    """Compact one-line-per-item view for the terminal."""
    blocked_ids = load_blocked_ids(robot_dir)
    tier1 = evaluation.tier not in ("self-serve", "self_serve", "selfserve")
    out = []
    counts = {s: 0 for s in ORDER}
    for cat in categories:
        if cat.tier1_only and not tier1:
            continue
        shown = []
        for item in cat.items:
            status = item_status(item.id, evaluation, robot_dir, blocked_ids)
            counts[status] += 1
            result = evaluation.results.get(item.id)
            score = ""
            if status == "done":
                score = f" {result.score}/{item.max_score}"
            elif status == "na":
                score = " inval"
            elif status == "skipped":
                score = " skip"
            mhm = must_have_met(item, result)
            mtag = "⭐✗" if mhm is False else "⭐ " if item.must_have else "  "
            shown.append(f"  {STATUS_ICONS[status]} {mtag} {item.id:<10}{score:<5} {item.name}")
        out.append(f"{cat.section} / {cat.name}")
        out.extend(shown)
    total = sum(counts.values())
    finished = counts["done"] + counts["na"] + counts["skipped"]
    summary = "  ".join(f"{STATUS_ICONS[s]} {STATUS_LABELS[s]}: {counts[s]}" for s in ORDER)
    mh_items = [i for cat in categories if not (cat.tier1_only and not tier1) for i in cat.items if i.must_have]
    mh_unmet = [i.id for i in mh_items if must_have_met(i, evaluation.results.get(i.id)) is False]
    mh_met = sum(1 for i in mh_items if must_have_met(i, evaluation.results.get(i.id)) is True)
    mh = f"⭐ Must-haves: {mh_met}/{len(mh_items)} met" + (f"  ⛔ UNMET: {', '.join(mh_unmet)}" if mh_unmet else "")
    out.insert(
        0,
        f"{evaluation.robot} — evaluation v{evaluation.evaluation_version} — "
        f"{finished}/{total} items finished\n{summary}\n{mh}\n",
    )
    return "\n".join(out)
