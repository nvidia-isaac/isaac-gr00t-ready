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

"""Tests for scoring, checklists, and published outputs."""

import io
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from pathlib import Path

import yaml

from gr00t_ready import SELF_ASSESSMENT_NOTICE
from gr00t_ready.__main__ import cmd_checklist
from gr00t_ready.board import board_data, render_board, render_board_terminal
from gr00t_ready.loader import (
    REPO_ROOT, Category, Item, load_criteria, load_results,
)
from gr00t_ready.report import render_report
from gr00t_ready.scoring import score_evaluation


class AssessmentTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.robot_dir = Path(tmp.name) / "robot"
        self.results_path = self.robot_dir / "results" / "results.yaml"
        self.results_path.parent.mkdir(parents=True)
        self.items = [
            Item("HW-TEST-01", "Controller", "Test", "auto",
                 {0: "Absent", 1: "Partial", 2: "Full"}),
            Item("HW-TEST-02", "Sensor", "Test", "auto",
                 {0: "Absent", 2: "Full"}, conditional=True),
            Item("SW-TEST-01", "Runtime", "Test", "auto",
                 {0: "Absent", 1: "Partial", 2: "Full"}),
        ]
        self.categories = [
            Category("hardware", "Hardware gate", "Hardware", self.items[:2]),
            Category("software", "Software gate", "Software", self.items[2:]),
        ]

    def record(self, scores):
        self.results_path.write_text(yaml.safe_dump({
            "robot": "robot",
            "date": "2026-11-04",
            "evaluator": "tester",
            "results": {
                item.id: {"score": score, "evidence": "test log"}
                for item, score in zip(self.items, scores)
            },
        }))
        return load_results(self.robot_dir)

    def test_verdicts_and_totals_agree_across_outputs(self):
        cases = [
            ([2, 2, 2], "Ready", ["Ready", "Ready"], 6, 6),
            ([1, 2, 2], "Partial", ["Partial", "Ready"], 5, 6),
            ([2, 0, 2], "Not Ready", ["Not Ready", "Ready"], 4, 6),
            ([0, None, 2], "Incomplete", ["Incomplete", "Ready"], 2, 6),
            ([0, 2, None], "Incomplete", ["Not Ready", "Incomplete"], 2, 6),
            ([2, "invalid", 2], "Ready", ["Ready", "Ready"], 4, 4),
            ([2, "skipped", 1], "Partial", ["Ready", "Partial"], 3, 4),
        ]
        for values, verdict, gate_verdicts, achieved, possible in cases:
            with self.subTest(values=values):
                evaluation = self.record(values)
                score = score_evaluation(self.categories, evaluation)
                self.assertEqual(score.overall_verdict, verdict)
                self.assertEqual([g.verdict for g in score.gates], gate_verdicts)
                self.assertEqual((score.achieved, score.possible), (achieved, possible))

                data = board_data(self.categories, evaluation, self.robot_dir)
                self.assertEqual(data["verdict"], verdict)
                self.assertEqual([c["verdict"] for c in data["categories"]], gate_verdicts)
                self.assertEqual(data["score_achieved"], achieved)
                self.assertEqual(data["score_possible"], possible)

                report = render_report(score)
                self.assertIn(f"**{verdict}**", report)
                self.assertIn(f"**Overall score:** {achieved}/{possible}", report)
                for gate_verdict in gate_verdicts:
                    self.assertIn(f"{gate_verdict} |", report)

    def test_cli_displays_each_verdict(self):
        items = [item for cat in load_criteria() for item in cat.items]
        results = {item.id: {"score": item.max_score} for item in items}
        item = next(item for item in items if set(item.levels) == {0, 1, 2})
        for value, verdict in (
            (2, "Ready"), (1, "Partial"), (0, "Not Ready"), (None, "Incomplete"),
        ):
            with self.subTest(verdict=verdict):
                results[item.id]["score"] = value
                self.results_path.write_text(yaml.safe_dump({"results": results}))
                completed = subprocess.run(
                    [sys.executable, "-m", "gr00t_ready", "score", str(self.robot_dir)],
                    cwd=REPO_ROOT, capture_output=True, text=True, check=True,
                )
                self.assertIn(f"Overall: {verdict} —", completed.stdout)

    def test_checklist_and_outputs_cover_only_technical_requirements(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(
                cmd_checklist(Namespace(robot_dir=str(self.robot_dir), force=False)), 0,
            )
        checklist = yaml.safe_load(self.results_path.read_text())
        self.assertEqual(
            set(checklist), {"robot", "evaluation_version", "date", "evaluator", "results"},
        )
        categories = load_criteria()
        self.assertEqual({cat.section for cat in categories}, {"Hardware", "Software"})
        expected_ids = {item.id for cat in categories for item in cat.items}
        self.assertEqual(set(checklist["results"]), expected_ids)
        evaluation = load_results(self.robot_dir)
        data = board_data(categories, evaluation, self.robot_dir)
        self.assertEqual(data["total"], len(expected_ids))
        self.assertEqual(data["verdict"], "Incomplete")
        for rendered in (
            render_report(score_evaluation(categories, evaluation)),
            render_board(categories, evaluation, self.robot_dir),
            render_board_terminal(categories, evaluation, self.robot_dir),
        ):
            for item_id in expected_ids:
                self.assertIn(item_id, rendered)

    def test_notice_is_prominent_and_consistent(self):
        for filename in ("README.md", "GR00T_Ready_Evaluation_Framework.md"):
            with self.subTest(filename=filename):
                text = " ".join((REPO_ROOT / filename).read_text().split())
                self.assertIn(SELF_ASSESSMENT_NOTICE, text)
        page = (REPO_ROOT / "gr00t_ready" / "web" / "index.html").read_text()
        header = page.split("<header>", 1)[1].split("</header>", 1)[0]
        self.assertIn(SELF_ASSESSMENT_NOTICE, header)
        score = score_evaluation(self.categories, self.record([2, 2, 2]))
        report = render_report(score)
        self.assertIn(SELF_ASSESSMENT_NOTICE, report.split("## Gate Summary", 1)[0])


if __name__ == "__main__":
    unittest.main()
