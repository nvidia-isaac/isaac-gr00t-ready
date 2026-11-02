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

"""Tests for reading and enforcing the results tier."""

import contextlib
import io
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from gr00t_ready.__main__ import cmd_board, cmd_report, cmd_score
from gr00t_ready.board import board_data
from gr00t_ready.loader import (
    Category,
    Item,
    load_results,
    validate_results,
)
from gr00t_ready.report import render_report
from gr00t_ready.scoring import score_evaluation


def _write(robot_dir: Path, tier_line: str) -> None:
    results_dir = robot_dir / "results"
    results_dir.mkdir(parents=True)
    (results_dir / "results.yaml").write_text(
        "robot: example_robot\n"
        f"{tier_line}"
        "date: 2026-11-01\n"
        "evaluator: tester\n"
        "results: {}\n"
    )


def _categories():
    item = Item("HW-TEST-01", "Criterion", "Test", "auto", {0: "No", 2: "Yes"})
    official = Item("NT-TEST-01", "Commercial criterion", "Test", "manual", {0: "No", 2: "Yes"})
    return [
        Category("test", "Test", "Hardware", [item]),
        Category("nt", "Commercial", "Non-technical", [official], tier1_only=True),
    ]


class TierTest(unittest.TestCase):
    def test_blank_missing_and_misspelled_tiers_are_problems(self):
        for label, tier_line in (("blank", "tier:\n"), ("missing", ""),
                                 ("misspelled", "tier: self serve\n")):
            with self.subTest(label), tempfile.TemporaryDirectory() as tmp:
                robot_dir = Path(tmp) / "example_robot"
                _write(robot_dir, tier_line)
                evaluation = load_results(robot_dir)

                problems = validate_results([], evaluation)

                self.assertEqual(len(problems), 1)
                self.assertIn("official, self-serve", problems[0])
                with self.assertRaises(ValueError):
                    score_evaluation(_categories(), evaluation)
                with self.assertRaises(ValueError):
                    board_data(_categories(), evaluation, robot_dir)

    def test_cli_refuses_to_score_an_unknown_tier(self):
        with tempfile.TemporaryDirectory() as tmp:
            robot_dir = Path(tmp) / "example_robot"
            _write(robot_dir, "tier:\n")
            for cmd in (cmd_score, cmd_report, cmd_board):
                with self.subTest(cmd.__name__):
                    out, err = io.StringIO(), io.StringIO()
                    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                        rc = cmd(Namespace(robot_dir=str(robot_dir)))
                    self.assertEqual(rc, 1)
                    self.assertIn("tier is blank or missing", err.getvalue())
                    self.assertEqual(out.getvalue(), "")
            self.assertFalse((robot_dir / "BOARD.md").exists())

    def test_accepted_spellings_score_their_own_tier(self):
        for tier_line, official in (("tier: official\n", True),
                                    ("tier: Self-Serve\n", False),
                                    ("tier: self_serve\n", False)):
            with self.subTest(tier_line), tempfile.TemporaryDirectory() as tmp:
                robot_dir = Path(tmp) / "example_robot"
                _write(robot_dir, tier_line)
                evaluation = load_results(robot_dir)

                self.assertEqual(validate_results([], evaluation), [])
                score = score_evaluation(_categories(), evaluation)
                self.assertEqual(len(score.gates), 2 if official else 1)
                header = "Tier 1: Official" if official else "Tier 2: Self-Serve"
                self.assertIn(f"**Tier:** {header}", render_report(score))


if __name__ == "__main__":
    unittest.main()
