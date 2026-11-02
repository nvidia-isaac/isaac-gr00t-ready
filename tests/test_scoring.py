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

"""Tests for gate verdicts with skipped and invalid results."""

import tempfile
import unittest
from pathlib import Path

from gr00t_ready.board import board_data
from gr00t_ready.loader import Category, Item, Result, RobotEvaluation
from gr00t_ready.report import render_report
from gr00t_ready.scoring import INCOMPLETE, PASS, score_evaluation


def _gate():
    must = Item(
        id="HW-TEST-01",
        name="Must-have criterion",
        method="Test",
        automation="auto",
        levels={0: "No", 1: "Partly", 2: "Fully"},
        must_have=True,
        must_have_level=1,
    )
    other = Item(
        id="HW-TEST-02",
        name="Binary criterion",
        method="Test",
        automation="auto",
        levels={0: "Unsupported", 2: "Supported"},
    )
    optional = Item(
        id="HW-TEST-03",
        name="Conditional criterion",
        method="Test",
        automation="auto",
        levels={0: "No", 2: "Yes"},
        conditional=True,
    )
    return [Category("test", "Test", "Hardware", [must, other, optional])]


def _evaluation(results):
    return RobotEvaluation(
        robot="robot",
        tier="self-serve",
        date="2026-11-01",
        evaluator="tester",
        results=results,
    )


class SkippedResultTest(unittest.TestCase):
    def test_skipped_must_have_keeps_gate_incomplete(self):
        evaluation = _evaluation({
            "HW-TEST-01": Result("HW-TEST-01", None, kind="skipped"),
            "HW-TEST-02": Result("HW-TEST-02", 2),
            "HW-TEST-03": Result("HW-TEST-03", 2),
        })

        score = score_evaluation(_gate(), evaluation)

        self.assertEqual(score.gates[0].verdict, INCOMPLETE)
        self.assertEqual(score.overall_verdict, INCOMPLETE)
        self.assertEqual(score.verdict_label(score.overall_verdict), "Incomplete")
        # the skipped item's points stay in the possible total
        self.assertEqual((score.achieved, score.possible), (4, 6))

    def test_all_skipped_is_not_compatible(self):
        evaluation = _evaluation({
            item_id: Result(item_id, None, kind="skipped")
            for item_id in ("HW-TEST-01", "HW-TEST-02", "HW-TEST-03")
        })

        score = score_evaluation(_gate(), evaluation)

        self.assertEqual(score.overall_verdict, INCOMPLETE)
        self.assertEqual((score.achieved, score.possible), (0, 6))

    def test_report_lists_skipped_must_have_as_pending(self):
        evaluation = _evaluation({
            "HW-TEST-01": Result("HW-TEST-01", None, notes="robot away", kind="skipped"),
            "HW-TEST-02": Result("HW-TEST-02", 2),
            "HW-TEST-03": Result("HW-TEST-03", 2),
        })

        report = render_report(score_evaluation(_gate(), evaluation))

        self.assertIn("**Overall verdict:** ⚪ **Incomplete**", report)
        self.assertIn("**Must-haves:** 0/1 met; 1 pending", report)
        self.assertIn("- **HW-TEST-01** Must-have criterion — skipped: robot away", report)
        self.assertNotIn("Compatible", report)

    def test_invalid_conditional_item_is_still_excluded(self):
        evaluation = _evaluation({
            "HW-TEST-01": Result("HW-TEST-01", 2),
            "HW-TEST-02": Result("HW-TEST-02", 2),
            "HW-TEST-03": Result("HW-TEST-03", None, kind="invalid"),
        })

        score = score_evaluation(_gate(), evaluation)

        self.assertEqual(score.overall_verdict, PASS)
        self.assertEqual((score.achieved, score.possible), (4, 4))

    def test_board_does_not_count_skipped_as_finished(self):
        evaluation = _evaluation({
            "HW-TEST-01": Result("HW-TEST-01", None, kind="skipped"),
            "HW-TEST-02": Result("HW-TEST-02", 2),
            "HW-TEST-03": Result("HW-TEST-03", None, kind="invalid"),
        })
        with tempfile.TemporaryDirectory() as tmp:
            data = board_data(_gate(), evaluation, Path(tmp))

        self.assertEqual(data["counts"]["skipped"], 1)
        self.assertEqual(data["finished"], 2)
        self.assertEqual((data["score_achieved"], data["score_possible"]), (2, 4))
        self.assertEqual(data["must_have"]["pending"], ["HW-TEST-01"])


if __name__ == "__main__":
    unittest.main()
