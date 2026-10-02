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

"""Scoring rules.

Per the framework's Phase 2, each gate (category) receives Pass / Conditional / Fail
for Official tier, or Compatible / Partial / Not Compatible for Self-Serve. The
mapping from item-level 0/1/2 scores to a gate verdict:

  - n/a results on conditional items are excluded.
  - INCOMPLETE  if any applicable item has no recorded result.
  - FAIL        if any applicable item scored 0.
  - PASS        if every applicable item reached its max defined level.
  - CONDITIONAL otherwise (all items functional, but some below full support).

The overall score is achieved points / possible points across tested items.
"""

from __future__ import annotations

from dataclasses import dataclass

from .loader import Category, Item, Result, RobotEvaluation

PASS = "Pass"
CONDITIONAL = "Conditional"
FAIL = "Fail"
INCOMPLETE = "Incomplete"

SELF_SERVE_LABELS = {
    PASS: "Compatible",
    CONDITIONAL: "Partial",
    FAIL: "Not Compatible",
    INCOMPLETE: "Incomplete",
}


@dataclass
class ItemScore:
    item: Item
    result: Result | None  # None = untested

    @property
    def tested(self) -> bool:
        return self.result is not None

    @property
    def applicable(self) -> bool:
        return not (self.result is not None and self.result.is_na)

    @property
    def achieved(self) -> int:
        if self.result is None or self.result.is_na:
            return 0
        return self.result.score

    @property
    def possible(self) -> int:
        return self.item.max_score


@dataclass
class GateScore:
    category: Category
    items: list[ItemScore]
    verdict: str
    achieved: int
    possible: int

    @property
    def percent(self) -> float:
        return 100.0 * self.achieved / self.possible if self.possible else 0.0


@dataclass
class EvaluationScore:
    evaluation: RobotEvaluation
    gates: list[GateScore]

    @property
    def achieved(self) -> int:
        return sum(g.achieved for g in self.gates)

    @property
    def possible(self) -> int:
        return sum(g.possible for g in self.gates)

    @property
    def percent(self) -> float:
        return 100.0 * self.achieved / self.possible if self.possible else 0.0

    @property
    def overall_verdict(self) -> str:
        verdicts = {g.verdict for g in self.gates}
        if INCOMPLETE in verdicts:
            return INCOMPLETE
        if FAIL in verdicts:
            return FAIL
        if CONDITIONAL in verdicts:
            return CONDITIONAL
        return PASS

    def verdict_label(self, verdict: str) -> str:
        if self.evaluation.tier in ("self-serve", "self_serve", "selfserve"):
            return SELF_SERVE_LABELS.get(verdict, verdict)
        return verdict


def score_gate(category: Category, evaluation: RobotEvaluation) -> GateScore:
    item_scores = [ItemScore(item, evaluation.results.get(item.id)) for item in category.items]
    applicable = [s for s in item_scores if s.applicable]

    if any(not s.tested for s in applicable):
        verdict = INCOMPLETE
    elif any(s.achieved == 0 for s in applicable):
        verdict = FAIL
    elif all(s.achieved == s.possible for s in applicable):
        verdict = PASS
    else:
        verdict = CONDITIONAL

    achieved = sum(s.achieved for s in applicable if s.tested)
    possible = sum(s.possible for s in applicable)
    return GateScore(category, item_scores, verdict, achieved, possible)


def score_evaluation(
    categories: list[Category], evaluation: RobotEvaluation
) -> EvaluationScore:
    tier1 = evaluation.tier not in ("self-serve", "self_serve", "selfserve")
    gates = [
        score_gate(cat, evaluation)
        for cat in categories
        if tier1 or not cat.tier1_only
    ]
    return EvaluationScore(evaluation, gates)
