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

"""Tests for CLI commands that read or write a robot's results."""

import contextlib
import io
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from gr00t_ready.__main__ import cmd_board, cmd_checklist, cmd_report, cmd_score, cmd_validate
from gr00t_ready.loader import load_results


def _run(cmd, **kwargs):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = cmd(Namespace(**kwargs))
    return rc, out.getvalue(), err.getvalue()


class MissingResultsTest(unittest.TestCase):
    def test_validate_fails_without_a_results_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            for label, robot_dir in (("empty folder", Path(tmp) / "empty_robot"),
                                     ("no folder", Path(tmp) / "no_such_robot")):
                with self.subTest(label):
                    if label == "empty folder":
                        robot_dir.mkdir()

                    rc, out, _ = _run(cmd_validate, robot_dir=str(robot_dir))

                    self.assertEqual(rc, 1)
                    self.assertIn("results.yaml not found", out)
                    self.assertNotIn("is valid", out)

    def test_score_report_and_board_refuse_without_a_results_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            robot_dir = Path(tmp) / "no_such_robot"
            for cmd in (cmd_score, cmd_report, cmd_board):
                with self.subTest(cmd.__name__):
                    rc, out, err = _run(cmd, robot_dir=str(robot_dir))

                    self.assertEqual(rc, 1)
                    self.assertEqual(out, "")
                    self.assertIn("results.yaml not found", err)
            self.assertFalse(robot_dir.exists())

    def test_fresh_checklist_validates(self):
        with tempfile.TemporaryDirectory() as tmp:
            robot_dir = Path(tmp) / "example_robot"
            self.assertEqual(_run(cmd_checklist, robot_dir=str(robot_dir), force=False)[0], 0)

            rc, out, _ = _run(cmd_validate, robot_dir=str(robot_dir))

            self.assertEqual(rc, 0)
            self.assertIn("results.yaml is valid", out)


class ChecklistForceTest(unittest.TestCase):
    def _recorded_checklist(self, robot_dir: Path) -> Path:
        self.assertEqual(_run(cmd_checklist, robot_dir=str(robot_dir), force=False)[0], 0)
        path = robot_dir / "results" / "results.yaml"
        text = path.read_text().replace("date: YYYY-MM-DD", "date: 2026-11-01")
        # record a result for the first item, the way an evaluator would
        path.write_text(text.replace("    score:\n", "    score: 2\n", 1))
        self.assertEqual(load_results(robot_dir).results["HW-SI-01"].score, 2)
        return path

    def test_force_keeps_the_recorded_results_as_a_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            robot_dir = Path(tmp) / "example_robot"
            path = self._recorded_checklist(robot_dir)
            recorded = path.read_bytes()

            rc, out, _ = _run(cmd_checklist, robot_dir=str(robot_dir), force=True)

            self.assertEqual(rc, 0)
            self.assertNotIn("    score: 2\n", path.read_text())  # fresh stub written
            backups = sorted((robot_dir / "results").glob("results.yaml.bak-*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), recorded)
            self.assertIn(str(backups[0]), out)

    def test_repeated_force_never_overwrites_a_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            robot_dir = Path(tmp) / "example_robot"
            self._recorded_checklist(robot_dir)

            for _ in range(3):
                self.assertEqual(_run(cmd_checklist, robot_dir=str(robot_dir), force=True)[0], 0)

            backups = list((robot_dir / "results").glob("results.yaml.bak-*"))
            self.assertEqual(len(backups), 3)
            self.assertEqual(sum("    score: 2\n" in b.read_text() for b in backups), 1)

    def test_without_force_the_file_is_left_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            robot_dir = Path(tmp) / "example_robot"
            path = self._recorded_checklist(robot_dir)
            recorded = path.read_bytes()

            rc, _, err = _run(cmd_checklist, robot_dir=str(robot_dir), force=False)

            self.assertEqual(rc, 1)
            self.assertIn("already exists", err)
            self.assertEqual(path.read_bytes(), recorded)
            self.assertEqual(list((robot_dir / "results").glob("results.yaml.bak-*")), [])


if __name__ == "__main__":
    unittest.main()
