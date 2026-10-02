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

"""Render markdown reports from an EvaluationScore."""

from __future__ import annotations

import datetime

from .board import must_have_met
from .scoring import CONDITIONAL, FAIL, INCOMPLETE, PASS, EvaluationScore, GateScore

VERDICT_ICONS = {PASS: "✅", CONDITIONAL: "🟡", FAIL: "❌", INCOMPLETE: "⚪"}


def render_report(score: EvaluationScore) -> str:
    ev = score.evaluation
    # must-have compliance
    mh = [(s.item, s.result) for g in score.gates for s in g.items if s.item.must_have]
    mh_unmet = [it for it, r in mh if must_have_met(it, r) is False]
    mh_pending = [it for it, r in mh if must_have_met(it, r) is None]
    mh_met = len(mh) - len(mh_unmet) - len(mh_pending)
    mh_line = (f"- **Must-haves:** {mh_met}/{len(mh)} met"
               + (f" — ❌ {len(mh_unmet)} UNMET (blocks certification): "
                  + ", ".join(it.id for it in mh_unmet) if mh_unmet else "")
               + (f"; {len(mh_pending)} pending" if mh_pending else ""))
    lines = [
        f"# GR00T-Ready Evaluation Report — {ev.robot}",
        "",
        f"- **Evaluation version:** {ev.evaluation_version}",
        f"- **Tier:** {'Tier 1: Official' if ev.tier == 'official' else 'Tier 2: Self-Serve'}",
        f"- **Date:** {ev.date}",
        f"- **Evaluator:** {ev.evaluator or 'n/a'}",
        f"- **Overall verdict:** {VERDICT_ICONS[score.overall_verdict]} "
        f"**{score.verdict_label(score.overall_verdict)}**",
        f"- **Overall score:** {score.achieved}/{score.possible} ({score.percent:.1f}%)",
        mh_line,
        f"- **Generated:** {datetime.date.today().isoformat()}",
        "",
    ]
    if mh_unmet or mh_pending:
        lines += ["## Must-Have Compliance", "",
                  "Certification requires every must-have item to reach its required level.", ""]
        for it, r in mh:
            m = must_have_met(it, r)
            icon = "✅" if m is True else ("❌" if m is False else "⚪")
            sc = ("invalid/skipped" if (r and r.is_na) else
                  (str(r.score) if r and r.score is not None else "untested"))
            lines.append(f"- {icon} **{it.id}** {it.name} — need ≥{it.must_have_level}, have {sc}")
        lines.append("")
    lines += [
        "## Gate Summary",
        "",
        "| Gate | Section | Verdict | Score | Tested |",
        "| --- | --- | --- | --- | --- |",
    ]
    for gate in score.gates:
        tested = sum(1 for s in gate.items if s.tested and s.applicable)
        applicable = sum(1 for s in gate.items if s.applicable)
        lines.append(
            f"| {gate.category.name} | {gate.category.section} | "
            f"{VERDICT_ICONS[gate.verdict]} {score.verdict_label(gate.verdict)} | "
            f"{gate.achieved}/{gate.possible} ({gate.percent:.0f}%) | "
            f"{tested}/{applicable} |"
        )

    blockers = _collect(score, lambda s: s.tested and s.applicable and s.achieved == 0)
    gaps = _collect(
        score, lambda s: s.tested and s.applicable and 0 < s.achieved < s.possible
    )
    untested = _collect(score, lambda s: not s.tested and s.applicable)

    if blockers:
        lines += ["", "## Blockers (score 0 — gate fails)", ""]
        lines += [f"- **{s.item.id}** {s.item.name}: {_result_note(s)}" for s in blockers]
    if gaps:
        lines += ["", "## Gaps (partial support — remediation candidates)", ""]
        lines += [
            f"- **{s.item.id}** {s.item.name}: scored {s.achieved}/{s.possible}"
            f" — level {s.possible} requires: {s.item.levels[s.item.max_score]}"
            for s in gaps
        ]
    if untested:
        lines += ["", "## Not Yet Tested", ""]
        lines += [f"- **{s.item.id}** {s.item.name}" for s in untested]

    lines += ["", "## Detailed Results", ""]
    for gate in score.gates:
        lines += [
            f"### {gate.category.name} — {VERDICT_ICONS[gate.verdict]} "
            f"{score.verdict_label(gate.verdict)}",
            "",
            "| ID | Item | Score | Result | Evidence / Notes |",
            "| --- | --- | --- | --- | --- |",
        ]
        for s in gate.items:
            if not s.applicable:
                if s.result is not None and s.result.is_skipped:
                    status = "skipped"
                    detail = (s.result.notes or "not testable now — deferred") + " (excluded from totals)"
                else:
                    status = "invalid"
                    detail = "feature not present on this platform — excluded from totals"
            elif not s.tested:
                status, detail = "—", "not tested"
            else:
                status = f"{s.achieved}/{s.possible}"
                detail = _result_note(s)
            lines.append(
                f"| {s.item.id} | {s.item.name} | {status} "
                f"| {s.item.levels.get(s.achieved, '') if s.tested and s.applicable else ''} "
                f"| {detail} |"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _collect(score: EvaluationScore, predicate) -> list:
    return [s for g in score.gates for s in g.items if predicate(s)]


def _result_note(s) -> str:
    parts = [p for p in (s.result.evidence, s.result.notes) if p]
    return "; ".join(parts) if parts else ""
