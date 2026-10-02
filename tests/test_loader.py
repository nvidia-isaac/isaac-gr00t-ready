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

import unittest

from gr00t_ready.loader import Category, Item, Result, RobotEvaluation, validate_results


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


if __name__ == "__main__":
    unittest.main()
