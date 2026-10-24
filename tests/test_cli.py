# SPDX-License-Identifier: Apache-2.0
"""Installed dispatcher must preserve each operation's argument parser."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import unittest

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


if __name__ == "__main__":
    unittest.main()
