"""Synthetic tests for fixed-area, Python-independent build cleanup."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]
CLEANUP = REPOSITORY / "tools" / "project_cleanup.sh"
TOOLS_NAME = "project-tools_r1_contributor_current_environment"


class ProjectCleanupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="hml cleanup test ")
        self.workspace = Path(self.temp.name) / "checkout with spaces"
        self.workspace.mkdir()
        (self.workspace / "pyproject.toml").write_text(
            '[tool.humanmotionlib.workflow]\n'
            f'tools-root = "build/{TOOLS_NAME}"\n',
            encoding="utf-8",
        )
        self.fakebin = Path(self.temp.name) / "bin"
        self.fakebin.mkdir()
        self.write_ps()
        self.write_lsof()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_ps(self, *, mode: str = "normal") -> None:
        ps = self.fakebin / "ps"
        if mode == "fail":
            content = "#!/bin/sh\nexit 1\n"
        elif mode == "hide-self":
            content = (
                "#!/bin/sh\n"
                "case \"$1\" in -p) printf '%s\\n' \"$2\"; exit 0 ;; esac\n"
                "case \"$1\" in -A*) printf '1 /sbin/init\\n'; exit 0 ;; esac\n"
                "exit 1\n"
            )
        else:
            content = (
                "#!/bin/sh\n"
                "case \"$1\" in\n"
                "  -p) printf '%s\\n' \"$2\"; exit 0 ;;\n"
                "  -A*)\n"
                "    printf '%s 100 S /bin/sh cleanup\\n' \"$HML_PROJECT_CLEANUP_PID\"\n"
                "    printf '100 1 S make\\n1 0 S /sbin/init\\n'\n"
                "    if [ -n \"${FAKE_ACTIVE_PID:-}\" ]; then printf '%s 1 S %s\\n' \"$FAKE_ACTIVE_PID\" \"$FAKE_ACTIVE_COMMAND\"; fi\n"
                "    exit 0 ;;\n"
                "esac\n"
                "exit 1\n"
            )
        ps.write_text(content, encoding="utf-8")
        ps.chmod(0o755)

    def write_lsof(self, *, mode: str = "normal") -> None:
        lsof = self.fakebin / "lsof"
        if mode == "fail":
            content = "#!/bin/sh\nexit 1\n"
        elif mode == "hide-self":
            content = "#!/bin/sh\nprintf 'p1\\ncinit\\nn/\\n'\n"
        else:
            content = (
                "#!/bin/sh\n"
                "printf 'p%s\\nccleanup\\nfcwd\\nn%s\\n' \"$HML_PROJECT_CLEANUP_PID\" \"${WORKSPACE:-/tmp}\"\n"
                "if [ -n \"${FAKE_ACTIVE_PID:-}\" ]; then\n"
                "  printf 'p%s\\n cworker\\n' \"$FAKE_ACTIVE_PID\"\n"
                "  if [ -n \"${FAKE_ACTIVE_CWD:-}\" ]; then printf 'fcwd\\nn%s\\n' \"$FAKE_ACTIVE_CWD\"; fi\n"
                "  if [ -n \"${FAKE_ACTIVE_OPEN:-}\" ]; then printf 'f3\\nn%s\\n' \"$FAKE_ACTIVE_OPEN\"; fi\n"
                "fi\n"
            )
        lsof.write_text(content, encoding="utf-8")
        lsof.chmod(0o755)

    def run_cleanup(
        self,
        level: str,
        *,
        env: dict[str, str] | None = None,
        real_process_tools: bool = False,
        physical_workspace: bool = False,
        tools_root: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        merged = os.environ.copy()
        merged["PATH"] = "/usr/local/bin:/usr/sbin:/sbin:/usr/bin:/bin" if real_process_tools else f"{self.fakebin}:/usr/local/bin:/usr/sbin:/sbin:/usr/bin:/bin"
        merged["WORKSPACE"] = str(self.workspace)
        if env:
            merged.update(env)
        workspace_arg = str(self.workspace.resolve()) if physical_workspace else str(self.workspace)
        command = ["/bin/sh", str(CLEANUP), "--workspace", workspace_arg]
        if tools_root is not None:
            command.extend(["--tools-root", tools_root])
        command.append(level)
        return subprocess.run(
            command,
            cwd=self.workspace,
            env=merged,
            text=True,
            capture_output=True,
            check=False,
        )

    def add_build_entry(self, name: str, content: bytes = b"data") -> Path:
        path = self.workspace / "build" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def digest(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_mostlyclean_removes_direct_stage_check_and_hidden_matches_only(self) -> None:
        build = self.workspace / "build"
        stage = build / "package-humanmotionlib_r1_dev_try-1_stage"
        stage.mkdir(parents=True)
        (stage / "unknown nested file.txt").write_bytes(b"stage")
        hidden_stage = build / ".legacy_stage"
        hidden_stage.mkdir()
        (hidden_stage / "R6 history.txt").write_bytes(b"history")
        check = build / "package-humanmotionlib_r1_dev_run-2_check"
        check.mkdir()
        (check / "local log.log").write_bytes(b"check")
        hidden_check = build / ".mystery_check"
        hidden_check.write_bytes(b"hidden")
        package = self.add_build_entry("package-humanmotionlib_r1_dev_run-3_package", b"wheel")
        matrix = self.add_build_entry("automate-build-and-verification-matrix_r1_dev_current_male-h170", b"frames")
        tools = build / TOOLS_NAME
        tools.mkdir()
        (tools / "python").write_bytes(b"tool")
        package_hash = self.digest(package)
        matrix_hash = self.digest(matrix)
        tools_hash = self.digest(tools / "python")

        result = self.run_cleanup("mostlyclean")
        self.assertEqual(result.returncode, 0, result.stderr)
        for removed in (stage, hidden_stage, check, hidden_check):
            self.assertFalse(removed.exists(), removed)
        self.assertEqual(self.digest(package), package_hash)
        self.assertEqual(self.digest(matrix), matrix_hash)
        self.assertEqual(self.digest(tools / "python"), tools_hash)
        self.assertIn("selected-count=4", result.stdout)
        self.assertIn("removed-count=4", result.stdout)

    def test_clean_removes_all_direct_children_except_configured_tools(self) -> None:
        build = self.workspace / "build"
        ordinary = build / "ordinary-results"
        (ordinary / "nested").mkdir(parents=True)
        (ordinary / "nested" / "unknown.txt").write_bytes(b"unknown")
        history = build / "R6_protected_history"
        history.mkdir()
        (history / "review.log").write_bytes(b"old history")
        matrix = build / "automate-build-and-verification-matrix_r1_dev_current_male-h170"
        matrix.mkdir()
        (matrix / "logs").mkdir()
        (matrix / "logs" / "attempt.log").write_bytes(b"log")
        dotfile = build / ".unknown-user-entry"
        dotfile.write_bytes(b"hidden")
        tools = build / TOOLS_NAME
        tools.mkdir()
        (tools / "cache").mkdir()
        (tools / "cache" / "entry").write_bytes(b"cache")
        outside = self.workspace / "dist" / "release.whl"
        outside.parent.mkdir()
        outside.write_bytes(b"release")
        lock = self.workspace / "uv.lock"
        lock.write_bytes(b"lock")
        outside_hash = self.digest(outside)
        lock_hash = self.digest(lock)

        result = self.run_cleanup("clean")
        self.assertEqual(result.returncode, 0, result.stderr)
        for removed in (ordinary, history, matrix, dotfile):
            self.assertFalse(removed.exists(), removed)
        self.assertTrue((tools / "cache" / "entry").exists())
        self.assertEqual(self.digest(outside), outside_hash)
        self.assertEqual(self.digest(lock), lock_hash)
        self.assertIn("removed-count=4", result.stdout)
        self.assertIn(f"retained={tools.resolve()}", result.stdout)

    def test_clean_uses_tools_root_from_invoking_checkout_override(self) -> None:
        target_config_tools = self.workspace / "build" / TOOLS_NAME
        target_config_tools.mkdir(parents=True)
        (target_config_tools / "target-environment").write_bytes(b"remove")
        invoking_config_tools = self.workspace / "build" / "invoking-tools"
        invoking_config_tools.mkdir()
        (invoking_config_tools / "environment").write_bytes(b"keep")

        result = self.run_cleanup("clean", tools_root="build/invoking-tools")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(target_config_tools.exists())
        self.assertTrue((invoking_config_tools / "environment").exists())
        self.assertIn(f"retained={invoking_config_tools.resolve()}", result.stdout)

    def test_distclean_removes_build_tree_including_nested_history_and_links(self) -> None:
        build = self.workspace / "build"
        (build / TOOLS_NAME / "environment").mkdir(parents=True)
        (build / TOOLS_NAME / "environment" / "python").write_bytes(b"tool")
        (build / "R6_history" / "nested").mkdir(parents=True)
        (build / "R6_history" / "nested" / "review.txt").write_bytes(b"history")
        outside = Path(self.temp.name) / "outside target"
        outside.mkdir()
        sentinel = outside / "sentinel.txt"
        sentinel.write_bytes(b"keep")
        (build / "external-link").symlink_to(outside, target_is_directory=True)
        (build / "broken-link").symlink_to(outside / "missing")
        release = self.workspace / "dist" / "release.whl"
        release.parent.mkdir()
        release.write_bytes(b"release")
        release_hash = self.digest(release)

        result = self.run_cleanup("distclean")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(build.exists())
        self.assertEqual(sentinel.read_bytes(), b"keep")
        self.assertEqual(self.digest(release), release_hash)
        self.assertIn("selected-count=1", result.stdout)
        self.assertIn("removed-count=1", result.stdout)

    def test_mostlyclean_unlinks_inward_link_but_keeps_nonmatching_target(self) -> None:
        build = self.workspace / "build"
        target = build / "package-humanmotionlib_r1_dev_try-1_package"
        target.mkdir(parents=True)
        artifact = target / "wheel.whl"
        artifact.write_bytes(b"wheel")
        link = build / "obsolete_check"
        link.symlink_to(target, target_is_directory=True)
        before = self.digest(artifact)

        result = self.run_cleanup("mostlyclean")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(link.is_symlink())
        self.assertEqual(self.digest(artifact), before)

    def test_mostlyclean_preserves_configured_tools_root_even_if_name_matches_pattern(self) -> None:
        tools_name = "custom_tools_stage"
        (self.workspace / "pyproject.toml").write_text(
            '[tool.humanmotionlib.workflow]\n'
            f'tools-root = "build/{tools_name}"\n',
            encoding="utf-8",
        )
        tools = self.workspace / "build" / tools_name
        tools.mkdir(parents=True)
        (tools / "python").write_bytes(b"keep")

        result = self.run_cleanup("mostlyclean")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((tools / "python").read_bytes(), b"keep")
        self.assertIn("selected-count=0", result.stdout)

    def test_real_path_workspace_without_active_process_is_positive_control(self) -> None:
        target = self.add_build_entry("ordinary_stage/file", b"remove")

        result = self.run_cleanup("mostlyclean", physical_workspace=True)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(target.parent.exists())

    def test_active_process_command_reference_blocks_before_any_removal(self) -> None:
        first = self.add_build_entry("a_stage/file", b"first")
        second = self.add_build_entry("b_check/file", b"second")
        active_pid = "424242"
        active_command = f"worker --output {first.parents[0]}"
        result = self.run_cleanup(
            "mostlyclean",
            env={"FAKE_ACTIVE_PID": active_pid, "FAKE_ACTIVE_COMMAND": active_command},
        )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("active process", result.stderr)
        self.assertTrue(first.exists())
        self.assertTrue(second.exists())

    def test_process_path_prefix_without_area_boundary_does_not_block(self) -> None:
        target = self.add_build_entry("a_stage/file", b"remove")
        sibling_path = f"{target.parents[0]}-backup"
        result = self.run_cleanup(
            "mostlyclean",
            env={"FAKE_ACTIVE_PID": "424245", "FAKE_ACTIVE_COMMAND": f"worker {sibling_path}/file"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(target.parents[0].exists())

    def test_active_process_cwd_inside_selected_area_blocks_removal(self) -> None:
        target = self.add_build_entry("selected_check/file", b"keep")
        result = self.run_cleanup(
            "clean",
            env={"FAKE_ACTIVE_PID": "424243", "FAKE_ACTIVE_COMMAND": "worker", "FAKE_ACTIVE_CWD": str(target.parent)},
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("active process", result.stderr)
        self.assertTrue(target.exists())

    def test_active_process_with_cwd_outside_and_open_file_inside_blocks(self) -> None:
        target = self.add_build_entry("selected_check/open-file.bin", b"keep")
        outside = self.workspace / "outside-cwd"
        outside.mkdir()
        result = self.run_cleanup(
            "clean",
            env={
                "FAKE_ACTIVE_PID": "424244",
                "FAKE_ACTIVE_COMMAND": "worker",
                "FAKE_ACTIVE_CWD": str(outside),
                "FAKE_ACTIVE_OPEN": str(target),
            },
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("active process", result.stderr)
        self.assertTrue(target.exists())

    @unittest.skipUnless(os.environ.get("HML_TEST_REAL_PROCESS_VISIBILITY") == "1", "requires process-inspection access")
    def test_real_process_cwd_and_open_file_block_cleanup(self) -> None:
        selected = self.workspace / "build" / "active_check"
        selected.mkdir(parents=True)
        opened = selected / "open.bin"
        opened.write_bytes(b"active")
        outside = self.workspace / "outside-cwd"
        outside.mkdir()

        cwd_process = subprocess.Popen(
            ["/bin/sh", "-c", "sleep 60"],
            cwd=selected,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            result = self.run_cleanup("clean", real_process_tools=True)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("active process", result.stderr)
            self.assertTrue(opened.exists())
        finally:
            cwd_process.terminate()
            cwd_process.wait(timeout=10)

        child_env = os.environ.copy()
        child_env["HML_OPEN_FILE"] = str(opened)
        opener_code = "import os, time; handle=open(os.environ['HML_OPEN_FILE'], 'rb'); time.sleep(60)"
        open_process = subprocess.Popen(
            [sys.executable, "-c", opener_code],
            cwd=outside,
            env=child_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            result = self.run_cleanup("clean", real_process_tools=True)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("active process", result.stderr)
            self.assertTrue(opened.exists())
        finally:
            open_process.terminate()
            open_process.wait(timeout=10)

    def test_unavailable_process_inspection_blocks_before_any_removal(self) -> None:
        target = self.add_build_entry("selected_check/file", b"keep")
        self.write_ps(mode="fail")
        result = self.run_cleanup("clean")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("process visibility is unavailable", result.stderr)
        self.assertTrue(target.exists())

    def test_incomplete_process_listing_blocks_before_any_removal(self) -> None:
        target = self.add_build_entry("selected_check/file", b"keep")
        self.write_ps(mode="hide-self")
        result = self.run_cleanup("clean")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cleanup process is not visible", result.stderr)
        self.assertTrue(target.exists())

    def test_unavailable_lsof_blocks_before_any_removal(self) -> None:
        target = self.add_build_entry("selected_check/file", b"keep")
        self.write_lsof(mode="fail")
        result = self.run_cleanup("clean")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("process visibility is unavailable", result.stderr)
        self.assertTrue(target.exists())

    def test_incomplete_lsof_listing_blocks_before_any_removal(self) -> None:
        target = self.add_build_entry("selected_check/file", b"keep")
        self.write_lsof(mode="hide-self")
        result = self.run_cleanup("clean")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cleanup process is not visible", result.stderr)
        self.assertTrue(target.exists())

    def test_invalid_tools_root_settings_fail_before_removal(self) -> None:
        target = self.add_build_entry("ordinary/file", b"keep")
        (self.workspace / "pyproject.toml").write_text(
            '[tool.humanmotionlib.workflow]\ntools-root = "../../outside"\n',
            encoding="utf-8",
        )
        result = self.run_cleanup("clean")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("tools-root must be a direct child", result.stderr)
        self.assertTrue(target.exists())

    def test_invalid_explicit_tools_root_fails_before_removal(self) -> None:
        target = self.add_build_entry("ordinary/file", b"keep")

        result = self.run_cleanup("clean", tools_root="build/tools/nested")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("tools-root must be one safe direct-child name", result.stderr)
        self.assertTrue(target.exists())

    def test_nested_tools_root_setting_is_rejected_before_removal(self) -> None:
        target = self.add_build_entry("ordinary/file", b"keep")
        (self.workspace / "pyproject.toml").write_text(
            '[tool.humanmotionlib.workflow]\ntools-root = "build/tools/nested"\n',
            encoding="utf-8",
        )
        result = self.run_cleanup("distclean")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(target.exists())

    def test_symlink_tools_root_is_rejected_before_removal(self) -> None:
        build = self.workspace / "build"
        build.mkdir()
        outside = Path(self.temp.name) / "outside tools"
        outside.mkdir()
        (build / TOOLS_NAME).symlink_to(outside, target_is_directory=True)
        ordinary = build / "ordinary"
        ordinary.mkdir()
        (ordinary / "file").write_bytes(b"keep")
        result = self.run_cleanup("clean")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((ordinary / "file").exists())
        self.assertTrue((outside).is_dir())

    def test_workspace_and_build_symlink_boundaries_are_rejected(self) -> None:
        target = Path(self.temp.name) / "outside-workspace"
        target.mkdir()
        (target / "pyproject.toml").write_text(
            '[tool.humanmotionlib.workflow]\n'
            f'tools-root = "build/{TOOLS_NAME}"\n',
            encoding="utf-8",
        )
        (target / "build").mkdir()
        link = Path(self.temp.name) / "workspace-link"
        link.symlink_to(target, target_is_directory=True)
        workspace_link = subprocess.run(
            ["/bin/sh", str(CLEANUP), "--workspace", str(link), "clean"],
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(workspace_link.returncode, 0)

        (self.workspace / "build").symlink_to(target / "build", target_is_directory=True)
        build_link = self.run_cleanup("distclean")
        self.assertNotEqual(build_link.returncode, 0)
        self.assertTrue((target / "build").is_dir())

    def test_no_python_or_uv_is_needed_and_empty_cleanup_repeats(self) -> None:
        for utility in ("awk", "find", "wc", "rm", "sh"):
            target = shutil.which(utility)
            self.assertIsNotNone(target, utility)
            (self.fakebin / utility).symlink_to(target)
        path = str(self.fakebin)
        self.assertIsNone(shutil.which("python", path=path))
        self.assertIsNone(shutil.which("python3", path=path))
        self.assertIsNone(shutil.which("python3.14", path=path))
        self.assertIsNone(shutil.which("uv", path=path))
        first = self.run_cleanup("distclean", env={"PATH": path})
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn("selected-count=0", first.stdout)
        populated = self.workspace / "build" / "selected_stage"
        populated.mkdir(parents=True)
        (populated / "fixture.bin").write_bytes(b"cleanup fixture")
        second = self.run_cleanup("clean", env={"PATH": path})
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertFalse(populated.exists())
        third = self.run_cleanup("clean", env={"PATH": path})
        fourth = self.run_cleanup("clean", env={"PATH": path})
        self.assertEqual(third.returncode, 0, third.stderr)
        self.assertEqual(fourth.returncode, 0, fourth.stderr)

    def test_partial_removal_failure_reports_completed_and_pending_paths(self) -> None:
        first = self.add_build_entry("a_stage/file", b"first")
        second = self.add_build_entry("b_stage/file", b"second")
        failing_rm = self.fakebin / "rm"
        failing_rm.write_text(
            "#!/bin/sh\n"
            "case \"$*\" in *b_stage*) exit 1 ;; esac\n"
            "exec /bin/rm \"$@\"\n",
            encoding="utf-8",
        )
        failing_rm.chmod(0o755)
        result = self.run_cleanup("mostlyclean")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(first.parents[0].exists())
        self.assertTrue(second.parents[0].exists())
        self.assertIn("removed=", result.stdout)
        self.assertIn("pending=", result.stderr)
        self.assertNotIn("pending-count=0", result.stdout + result.stderr)

    def test_interrupt_reports_pending_selected_area(self) -> None:
        first = self.add_build_entry("a_stage/file", b"first")
        second = self.add_build_entry("b_stage/file", b"second")
        interrupting_rm = self.fakebin / "rm"
        interrupting_rm.write_text(
            "#!/bin/sh\n"
            "case \"$*\" in *b_stage*) kill -INT \"$PPID\"; exit 1 ;; esac\n"
            "exec /bin/rm \"$@\"\n",
            encoding="utf-8",
        )
        interrupting_rm.chmod(0o755)
        result = self.run_cleanup("mostlyclean")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(first.parents[0].exists())
        self.assertTrue(second.parents[0].exists())
        self.assertIn("pending=", result.stderr)
        self.assertNotIn("pending-count=0", result.stdout + result.stderr)

    def test_byte_count_matches_multiple_file_contents(self) -> None:
        root = self.workspace / "build" / "package-result"
        root.mkdir(parents=True)
        (root / "one").write_bytes(b"1234")
        (root / "two").write_bytes(b"567890")
        expected = 10
        result = self.run_cleanup("clean")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"removed={root.resolve()} bytes={expected}", result.stdout)


if __name__ == "__main__":
    unittest.main()
