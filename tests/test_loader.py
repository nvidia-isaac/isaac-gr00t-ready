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

"""Tests for criteria and result validation."""

import tempfile
import unittest
from pathlib import Path

from gr00t_ready.loader import (
    Category,
    Item,
    Result,
    RobotEvaluation,
    load_results,
    validate_results,
)


class ResultValidationTest(unittest.TestCase):
    def test_score_must_match_an_explicit_rubric_level(self):
        item = Item(
            id="HW-TEST-01",
            name="Binary criterion",
            method="Test",
            automation="auto",
            levels={0: "Unsupported", 2: "Supported"},
        )
        categories = [Category("test", "Test", "Hardware", [item])]
        evaluation = RobotEvaluation(
            robot="robot",
            tier="official",
            date="2026-07-16",
            evaluator="tester",
            results={"HW-TEST-01": Result("HW-TEST-01", 1)},
        )

        problems = validate_results(categories, evaluation)

        self.assertEqual(len(problems), 1)
        self.assertIn("expected one of: 0, 2", problems[0])


class ScoreParsingTest(unittest.TestCase):
    def _load(self, results_yaml: str) -> RobotEvaluation:
        with tempfile.TemporaryDirectory() as tmp:
            robot_dir = Path(tmp) / "robot"
            (robot_dir / "results").mkdir(parents=True)
            (robot_dir / "results" / "results.yaml").write_text(
                "robot: robot\ntier: self-serve\ndate: 2026-11-01\nevaluator: tester\n"
                "results:\n" + results_yaml
            )
            return load_results(robot_dir)

    def test_non_integer_scores_are_problems_not_results(self):
        evaluation = self._load(
            "  HW-TEST-01:\n    score: no\n"
            "  HW-TEST-02:\n    score: yes\n"
            "  HW-TEST-03:\n    score: true\n"
            "  HW-TEST-04:\n    score: 1.5\n"
            "  HW-TEST-05:\n    score: pass\n"
        )

        self.assertEqual(evaluation.results, {})  # all left untested
        problems = validate_results([], evaluation)
        self.assertEqual(len(problems), 5)
        for n in range(1, 6):
            self.assertTrue(any(p.startswith(f"HW-TEST-0{n}: score ") for p in problems))

    def test_scalar_entry_is_a_problem_not_a_crash(self):
        evaluation = self._load("  HW-TEST-01: 2\n")

        self.assertEqual(evaluation.results, {})
        self.assertIn("must be a mapping", validate_results([], evaluation)[0])

    def test_integer_scores_still_load(self):
        evaluation = self._load(
            "  HW-TEST-01:\n    score: 0\n"
            "  HW-TEST-02:\n    score: '2'\n"
            "  HW-TEST-03:\n    score: skipped\n"
        )

        self.assertEqual(evaluation.results["HW-TEST-01"].score, 0)
        self.assertEqual(evaluation.results["HW-TEST-02"].score, 2)
        self.assertTrue(evaluation.results["HW-TEST-03"].is_skipped)
        self.assertEqual(evaluation.load_problems, [])


if __name__ == "__main__":
    unittest.main()
