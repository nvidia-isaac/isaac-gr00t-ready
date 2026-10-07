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

"""Tests for evaluation pipeline version propagation."""

import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from gr00t_ready import __version__
from gr00t_ready.__main__ import cmd_checklist
from gr00t_ready.board import board_data, render_board
from gr00t_ready.loader import load_results
from gr00t_ready.report import render_report
from gr00t_ready.scoring import score_evaluation


class VersioningTest(unittest.TestCase):
    def test_package_version_comes_from_version_file(self):
        self.assertEqual(__version__, "0.3")

    def test_checklist_records_current_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            robot_dir = Path(tmp) / "example_robot"
            self.assertEqual(
                cmd_checklist(Namespace(robot_dir=str(robot_dir), force=False)),
                0,
            )
            results = (robot_dir / "results" / "results.yaml").read_text()
            self.assertIn("evaluation_version: 0.3\n", results)
            self.assertEqual(load_results(robot_dir).tier, "self-serve")

    def test_legacy_results_default_to_current_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            robot_dir = Path(tmp) / "legacy_robot"
            evaluation = load_results(robot_dir)
            self.assertEqual(evaluation.evaluation_version, __version__)

    def test_recorded_version_reaches_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            robot_dir = Path(tmp) / "example_robot"
            results_dir = robot_dir / "results"
            results_dir.mkdir(parents=True)
            (results_dir / "results.yaml").write_text(
                "robot: example_robot\n"
                "tier: official\n"
                "evaluation_version: 0.2.0\n"
                "date: 2026-07-16\n"
                "results: {}\n"
            )
            evaluation = load_results(robot_dir)
            score = score_evaluation([], evaluation)

            self.assertIn("**Evaluation version:** 0.2.0", render_report(score))
            self.assertIn(
                "**Evaluation version:** 0.2.0",
                render_board([], evaluation, robot_dir),
            )
            self.assertEqual(
                board_data([], evaluation, robot_dir)["evaluation_version"],
                "0.2.0",
            )


if __name__ == "__main__":
    unittest.main()
