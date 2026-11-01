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


if __name__ == "__main__":
    unittest.main()
