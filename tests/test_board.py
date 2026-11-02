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

"""Tests for the must-have line on the progress board."""

import tempfile
import unittest
from pathlib import Path

from gr00t_ready.board import render_board, render_board_terminal
from gr00t_ready.loader import Category, Item, Result, RobotEvaluation


def _categories():
    levels = {0: "No", 1: "Partly", 2: "Fully"}
    return [Category("test", "Test", "Hardware", [
        Item("HW-TEST-01", "First must-have", "Test", "auto", levels,
             must_have=True, must_have_level=1),
        Item("HW-TEST-02", "Second must-have", "Test", "auto", levels,
             must_have=True, must_have_level=2),
    ])]


def _lines(results):
    evaluation = RobotEvaluation(robot="robot", tier="self-serve", date="2026-11-01",
                                 evaluator="tester", results=results)
    with tempfile.TemporaryDirectory() as tmp:
        board = render_board(_categories(), evaluation, Path(tmp))
        terminal = render_board_terminal(_categories(), evaluation, Path(tmp))
    md = next(line for line in board.splitlines() if line.startswith("**Must-haves:**"))
    term = next(line for line in terminal.splitlines() if "Must-haves:" in line)
    return md, term


class MustHaveLineTest(unittest.TestCase):
    def test_day_zero_board_shows_pending_not_a_checkmark(self):
        md, term = _lines({})

        self.assertEqual(md, "**Must-haves:** 0/2 met; 2 pending")
        self.assertNotIn("✅", md)
        self.assertIn("2 pending", term)

    def test_partly_tested_board_shows_pending(self):
        md, _ = _lines({"HW-TEST-01": Result("HW-TEST-01", 1)})

        self.assertEqual(md, "**Must-haves:** 1/2 met; 1 pending")

    def test_unmet_and_pending_are_both_shown(self):
        md, term = _lines({"HW-TEST-02": Result("HW-TEST-02", 1)})

        self.assertEqual(md, "**Must-haves:** 0/2 met — ⛔ UNMET: HW-TEST-02; 1 pending")
        self.assertIn("UNMET: HW-TEST-02", term)

    def test_checkmark_only_when_every_must_have_is_met(self):
        md, term = _lines({"HW-TEST-01": Result("HW-TEST-01", 1),
                           "HW-TEST-02": Result("HW-TEST-02", 2)})

        self.assertEqual(md, "**Must-haves:** 2/2 met ✅")
        self.assertTrue(term.endswith("2/2 met ✅"))


if __name__ == "__main__":
    unittest.main()
