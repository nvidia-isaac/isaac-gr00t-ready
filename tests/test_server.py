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

"""Tests for dashboard server safety behavior."""

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import ANY, patch

from gr00t_ready.server import _write_upload, serve


class UploadTest(unittest.TestCase):
    def test_complete_upload_is_saved(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "evidence.txt"

            self.assertTrue(_write_upload(io.BytesIO(b"complete"), dest, 8))
            self.assertEqual(dest.read_bytes(), b"complete")

    def test_incomplete_upload_is_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "evidence.txt"

            self.assertFalse(_write_upload(io.BytesIO(b"short"), dest, 10))
            self.assertFalse(dest.exists())


class BindingTest(unittest.TestCase):
    @patch("gr00t_ready.server.ThreadingHTTPServer")
    def test_dashboard_binds_to_loopback_by_default(self, server_cls):
        with tempfile.TemporaryDirectory() as tmp:
            serve(Path(tmp) / "robot", upload_password="test-password")

        server_cls.assert_called_once_with(("127.0.0.1", 8321), ANY)


if __name__ == "__main__":
    unittest.main()
