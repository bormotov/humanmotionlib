# SPDX-License-Identifier: Apache-2.0
"""Installed dispatcher must preserve each operation's argument parser."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

from humanmotionlib import cli


class CliDispatchTests(unittest.TestCase):
    def test_check_environment_help_is_forwarded_to_operation_parser(self):
        output = StringIO()
        with redirect_stdout(output), self.assertRaises(SystemExit) as raised:
            cli.main(["check-environment", "--help"])
        self.assertEqual(raised.exception.code, 0)
        self.assertIn("--check-environment", output.getvalue())

    def test_check_environment_rejects_unknown_option(self):
        errors = StringIO()
        with redirect_stderr(errors), self.assertRaises(SystemExit) as raised:
            cli.main(["check-environment", "--not-an-option"])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("unrecognized arguments", errors.getvalue())

    def test_prepare_skeleton_delegates_without_consuming_sys_argv(self):
        result = SimpleNamespace(poses=(object(), object()), prepared_path=Path("/tmp/prepared.json"))
        before = list(sys.argv)
        with patch("humanmotionlib.api.prepare", return_value=result) as prepare:
            output = StringIO()
            with redirect_stdout(output):
                status = cli.main(["--workspace", "/tmp/workspace", "prepare-skeleton",
                                   "--profile", "adult-reference-v1", "--stature", "1.5",
                                   "--fixtures", "neutral", "arm-raise", "--output", "build/test/input.json"])
        self.assertEqual(status, 0)
        self.assertEqual(sys.argv, before)
        prepare.assert_called_once_with(workspace="/tmp/workspace", output=Path("build/test/input.json"),
                                        profile="adult-reference-v1", stature=1.5,
                                        fixtures=["neutral", "arm-raise"])
        self.assertIn("Prepared 2 samples", output.getvalue())

    def test_run_blender_delegates_no_images_and_preserves_cli_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            receipt_path = Path(temporary) / "processes" / "fake" / "outcome.json"
            receipt_path.parent.mkdir(parents=True)
            receipt_path.write_text(json.dumps({"state": "succeeded", "operation": "build",
                                                "invocation_id": "fake", "stdout_log": str(receipt_path.parent / "stdout.log")}))
            result = SimpleNamespace(receipt_path=receipt_path)
            before = list(sys.argv)
            with patch("humanmotionlib.api.render", return_value=result) as render:
                output = StringIO()
                with redirect_stdout(output):
                    status = cli.main(["--workspace", "/tmp/workspace", "run-blender", "--input", "build/input.json",
                                       "--output", "build/test", "--render-only"])
            self.assertEqual(status, 0)
            self.assertEqual(sys.argv, before)
            render.assert_called_once_with(Path("build/input.json"), workspace="/tmp/workspace",
                                           output=Path("build/test"), images=False, render_dir=None,
                                           render_only=True, timeout_seconds=1800.0,
                                           slot_timeout_seconds=30.0)
            self.assertIn('"state": "succeeded"', output.getvalue())


if __name__ == "__main__":
    unittest.main()
