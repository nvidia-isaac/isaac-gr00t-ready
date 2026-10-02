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

"""Load and validate criteria and robot result files."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .version import __version__

REPO_ROOT = Path(__file__).resolve().parent.parent
CRITERIA_PATH = REPO_ROOT / "criteria" / "criteria.yaml"


@dataclass
class Item:
    id: str
    name: str
    method: str
    automation: str
    levels: dict[int, str]
    conditional: bool = False
    must_have: bool = False
    must_have_level: int = 0  # minimum level required for certification

    @property
    def max_score(self) -> int:
        return max(self.levels)


@dataclass
class Category:
    id: str
    name: str
    section: str
    items: list[Item]
    tier1_only: bool = False


@dataclass
class Result:
    """A recorded result for one item.

    score is an int level, or None when the item is EXCLUDED from totals; the
    `kind` then says why: 'invalid' (feature absent — permanent) or 'skipped'
    (can't be tested now — deferred to a future session).
    """

    item_id: str
    score: int | None
    evidence: str = ""
    notes: str = ""
    executed: str = ""  # auto | semi | manual — how it was actually run
    kind: str = "value"  # value | invalid | skipped

    @property
    def is_na(self) -> bool:
        """Excluded from the score totals (invalid or skipped)."""
        return self.score is None

    @property
    def is_skipped(self) -> bool:
        return self.kind == "skipped"

    @property
    def is_invalid(self) -> bool:
        return self.kind == "invalid"


@dataclass
class RobotEvaluation:
    robot: str
    tier: str
    date: str
    evaluator: str
    evaluation_version: str = __version__
    results: dict[str, Result] = field(default_factory=dict)


def load_criteria(path: Path = CRITERIA_PATH) -> list[Category]:
    data = yaml.safe_load(path.read_text())
    categories = []
    for cat in data["categories"]:
        items = [
            Item(
                id=i["id"],
                name=i["name"],
                method=i.get("method", ""),
                automation=i.get("automation", "manual"),
                levels={int(k): v for k, v in i["levels"].items()},
                conditional=i.get("conditional", False),
                must_have=i.get("must_have", False),
                must_have_level=int(i.get("must_have_level", 0)),
            )
            for i in cat["items"]
        ]
        categories.append(
            Category(
                id=cat["id"],
                name=cat["name"],
                section=cat["section"],
                items=items,
                tier1_only=cat.get("tier1_only", False),
            )
        )
    _check_unique_ids(categories)
    return categories


def _check_unique_ids(categories: list[Category]) -> None:
    seen: set[str] = set()
    for cat in categories:
        for item in cat.items:
            if item.id in seen:
                raise ValueError(f"Duplicate item id in criteria: {item.id}")
            seen.add(item.id)


def load_results(robot_dir: Path) -> RobotEvaluation:
    path = Path(robot_dir) / "results" / "results.yaml"
    data = yaml.safe_load(path.read_text()) if path.exists() else {}
    data = data or {}
    results = {}
    for item_id, r in (data.get("results") or {}).items():
        if r is None:
            continue
        raw = r.get("score")
        kind = "value"
        if isinstance(raw, str) and raw.strip().lower() == "skipped":
            score, kind = None, "skipped"  # can't test now — deferred, excluded from totals
        elif isinstance(raw, str) and raw.strip().lower() in ("invalid", "n/a", "na"):
            score, kind = None, "invalid"  # feature absent — excluded from totals
        elif raw is None:
            continue  # untested — leave absent
        else:
            score = int(raw)
        results[item_id] = Result(
            item_id=item_id,
            score=score,
            evidence=str(r.get("evidence", "") or ""),
            notes=str(r.get("notes", "") or ""),
            executed=str(r.get("executed", "") or ""),
            kind=kind,
        )
    return RobotEvaluation(
        robot=data.get("robot", Path(robot_dir).name),
        tier=str(data.get("tier", "official")).lower(),
        date=str(data.get("date", datetime.date.today().isoformat())),
        evaluator=str(data.get("evaluator", "")),
        # Result files created before versioning are interpreted using the
        # current pipeline version, preserving backward compatibility.
        evaluation_version=str(data.get("evaluation_version") or __version__),
        results=results,
    )


def validate_results(categories: list[Category], evaluation: RobotEvaluation) -> list[str]:
    """Return problems such as unknown ids or undefined rubric scores."""
    problems = []
    items = {i.id: i for c in categories for i in c.items}
    for item_id, result in evaluation.results.items():
        item = items.get(item_id)
        if item is None:
            problems.append(f"{item_id}: unknown item id (not in criteria.yaml)")
            continue
        if result.is_na:
            if result.is_invalid and not item.conditional:
                problems.append(f"{item_id}: scored invalid but item is not marked conditional in criteria.yaml")
            # 'skipped' is allowed on any item (deferred, not a hardware-absence claim)
            continue
        if result.score not in item.levels:
            valid_levels = ", ".join(str(level) for level in sorted(item.levels))
            problems.append(
                f"{item_id}: score {result.score} is not a defined rubric level "
                f"(expected one of: {valid_levels})"
            )
    return problems
