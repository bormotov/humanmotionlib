# SPDX-License-Identifier: Apache-2.0
"""Explicit workspace and resolved build-ownership path contracts."""

from pathlib import Path
import tempfile
import unittest

from humanmotionlib.runtime import (resolve_workspace_path, validate_existing_run_root,
                                    validate_run_content_path, validate_run_root, workspace_root)


class WorkspaceContractTests(unittest.TestCase):
    def test_workspace_must_be_nonempty_absolute_and_directory(self):
        for value in (None, "", "relative/workspace"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                workspace_root(value)
        with tempfile.TemporaryDirectory() as temporary:
            file_path = Path(temporary) / "not-a-directory"
            file_path.write_text("x")
            with self.assertRaisesRegex(ValueError, "not a directory"):
                workspace_root(file_path)

    def test_relative_operands_are_workspace_relative_and_absolute_reads_stay_absolute(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "caller"
            external = Path(temporary) / "external"
            self.assertEqual(resolve_workspace_path("build/input.json", workspace),
                             (workspace / "build/input.json").resolve())
            self.assertEqual(resolve_workspace_path(external, workspace), external.resolve())

    def test_rejects_escaping_build_run_and_content_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "workspace"
            outside = Path(temporary) / "outside"
            outside.mkdir()
            root.mkdir()
            (root / "build").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "outside the workspace"):
                validate_run_root(root / "build/portable-runtime_r1_dev_try-1_check", root)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "workspace"
            build = root / "build"
            build.mkdir(parents=True)
            run = build / "portable-runtime_r1_dev_try-1_check"
            run.mkdir()
            external = Path(temporary) / "external"
            external.mkdir()
            (run / "evidence").symlink_to(external, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "outside build"):
                validate_run_content_path(run / "evidence/report.json", root)

    def test_accepts_cross_workspace_existing_run_as_read_only_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            owner = Path(temporary) / "owner"
            selected = Path(temporary) / "selected"
            run = owner / "build/portable-runtime_r1_dev_try-1_input"
            run.mkdir(parents=True)
            self.assertEqual(validate_existing_run_root(run, selected), run.resolve())
            self.assertEqual(validate_run_root(selected / "build/portable-runtime_r1_dev_try-2_output", selected),
                             (selected / "build/portable-runtime_r1_dev_try-2_output").resolve())


if __name__ == "__main__":
    unittest.main()
