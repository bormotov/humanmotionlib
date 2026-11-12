# SPDX-License-Identifier: Apache-2.0
"""Focused checks for the Make workflow's source identity and failure controls."""
from __future__ import annotations

import os
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest import mock

from tools import matrix, repository_workflow as workflow

_RUN_ROOT: Path | None = None


def setUpModule() -> None:
    global _RUN_ROOT
    _RUN_ROOT = workflow.allocate_run(workflow.ROOT, "check")


class RepositoryWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        assert _RUN_ROOT is not None
        scratch = _RUN_ROOT / "test-scratch"
        scratch.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def write_package_inputs(self, root: Path) -> None:
        (root / "src/humanmotionlib").mkdir(parents=True)
        (root / "src/humanmotionlib/api.py").write_text("API = 1\n", encoding="utf-8")
        for directory, _pattern in workflow.RESOURCE_PATTERNS:
            (root / directory).mkdir(parents=True, exist_ok=True)
            (root / directory / "input.yaml" if directory != "schema" else
             root / directory / "input.schema.json").write_text("{}\n", encoding="utf-8")
        for name in (*workflow.RESOURCE_FILES, *workflow.SOURCE_CONTROL_FILES):
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(name + "\n", encoding="utf-8")

    def test_source_snapshot_tracks_added_changed_and_deleted_files(self) -> None:
        self.write_package_inputs(self.root)
        with mock.patch.object(workflow, "ROOT", self.root):
            first = workflow.source_snapshot()
            added = self.root / "src/humanmotionlib/new_module.py"
            added.write_text("NEW = True\n", encoding="utf-8")
            second = workflow.source_snapshot()
            self.assertNotEqual(workflow.identity(first)["source_sha256"],
                                workflow.identity(second)["source_sha256"])
            self.assertIn("src/humanmotionlib/new_module.py", second)
            added.unlink()
            (self.root / "src/humanmotionlib/api.py").write_text("API = 2\n", encoding="utf-8")
            third = workflow.source_snapshot()
            self.assertNotEqual(workflow.identity(first)["source_sha256"],
                                workflow.identity(third)["source_sha256"])
            self.assertNotEqual(first["src/humanmotionlib/api.py"], third["src/humanmotionlib/api.py"])

    def test_wheel_build_rejects_and_logs_source_edit_during_build(self) -> None:
        self.write_package_inputs(self.root)

        def build_then_mutate(command, *, cwd, env, log, stage):
            log.parent.mkdir(parents=True, exist_ok=True)
            output = Path(command[command.index("--out-dir") + 1])
            (output / "humanmotionlib-controlled.whl").write_bytes(b"controlled wheel")
            source = self.root / "src/humanmotionlib/api.py"
            source.write_text("API = 2\n", encoding="utf-8")

        with (mock.patch.object(workflow, "ROOT", self.root),
              mock.patch.object(workflow, "current_python", return_value=self.root / "python"),
              mock.patch.object(workflow, "uv", return_value="uv"),
              mock.patch.object(workflow, "command_env", return_value={}),
              mock.patch.object(workflow, "run", side_effect=build_then_mutate) as run):
            with self.assertRaisesRegex(workflow.WorkflowError,
                                        "package inputs changed while the wheel was being built"):
                workflow.build_current_wheel(self.root)

        self.assertEqual(run.call_count, 1, "wheel installation must not follow a failed source check")
        logs = list((self.root / "build").glob("package-humanmotionlib_*_stage/logs/build.log"))
        self.assertEqual(len(logs), 1)
        contents = logs[0].read_text(encoding="utf-8")
        self.assertIn("stage=source-closure-verification outcome=failure", contents)
        self.assertIn("package inputs changed while the wheel was being built", contents)
        self.assertNotIn("install-exact-wheel", contents)

    def test_source_snapshot_rejects_symlinked_package_input(self) -> None:
        self.write_package_inputs(self.root)
        outside = self.root / "outside.py"
        outside.write_text("OUTSIDE = True\n", encoding="utf-8")
        source = self.root / "src/humanmotionlib/api.py"
        source.unlink()
        source.symlink_to(outside)
        with mock.patch.object(workflow, "ROOT", self.root):
            with self.assertRaisesRegex(workflow.WorkflowError, "unsafe package source"):
                workflow.source_snapshot()

    def test_wheel_verification_accepts_backend_generated_identity_module(self) -> None:
        project = self.root / "pyproject.toml"
        project.write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")
        generated = b'__version__ = "1.2.3"\n'
        source_bytes = b"API = True\n"
        second_source_bytes = b"OMITTED = False\n"
        resource_bytes = b"id: controlled\n"
        documentation_bytes = b"Package resource.\n"
        (self.root / "docs").mkdir()
        (self.root / "docs/used-materials.md").write_bytes(documentation_bytes)
        snapshot = {
            "src/humanmotionlib/api.py": workflow.sha256(source_bytes),
            "src/humanmotionlib/omitted.py": workflow.sha256(second_source_bytes),
            "characters/controlled.yaml": workflow.sha256(resource_bytes),
            "docs/used-materials.md": workflow.sha256(documentation_bytes),
        }
        implementation = {
            "humanmotionlib/_version.py": workflow.sha256(generated),
            "humanmotionlib/api.py": workflow.sha256(source_bytes),
            "humanmotionlib/omitted.py": workflow.sha256(second_source_bytes),
        }
        manifest = {"format": "humanmotionlib-runtime-manifest/v1", "version": "1.2.3",
                    "resources": {"characters/controlled.yaml": workflow.sha256(resource_bytes),
                                  "docs/used-materials.md": workflow.sha256(documentation_bytes)},
                    "implementation": implementation,
                    "backend_contract": "test"}
        wheel = self.root / "humanmotionlib-test.whl"
        with zipfile.ZipFile(wheel, "w") as archive:
            archive.writestr("humanmotionlib/_version.py", generated)
            archive.writestr("humanmotionlib/api.py", source_bytes)
            archive.writestr("humanmotionlib/omitted.py", second_source_bytes)
            archive.writestr("humanmotionlib/resources/characters/controlled.yaml", resource_bytes)
            archive.writestr("humanmotionlib/resources/docs/used-materials.md", documentation_bytes)
            archive.writestr("humanmotionlib/resources/runtime-manifest.json",
                             (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode())
        with (mock.patch.object(workflow, "ROOT", self.root),
              mock.patch.object(workflow, "RESOURCE_FILES", ("docs/used-materials.md",)),
              mock.patch.object(workflow, "RESOURCE_PATTERNS", (("characters", "*.yaml"),))):
            package = workflow.verify_wheel_sources(wheel, snapshot)
        self.assertEqual(package["manifest_sha256"], workflow.sha256(
            (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()))

        incomplete = {**manifest, "resources": {}}
        broken_wheel = self.root / "humanmotionlib-incomplete.whl"
        with zipfile.ZipFile(broken_wheel, "w") as archive:
            archive.writestr("humanmotionlib/_version.py", generated)
            archive.writestr("humanmotionlib/api.py", source_bytes)
            archive.writestr("humanmotionlib/resources/characters/controlled.yaml", resource_bytes)
            archive.writestr("humanmotionlib/resources/docs/used-materials.md", documentation_bytes)
            archive.writestr("humanmotionlib/resources/runtime-manifest.json",
                             (json.dumps(incomplete, sort_keys=True, separators=(",", ":")) + "\n").encode())
        with (mock.patch.object(workflow, "ROOT", self.root),
              mock.patch.object(workflow, "RESOURCE_FILES", ("docs/used-materials.md",)),
              mock.patch.object(workflow, "RESOURCE_PATTERNS", (("characters", "*.yaml"),))):
            with self.assertRaisesRegex(workflow.WorkflowError, "resource closure"):
                workflow.verify_wheel_sources(broken_wheel, snapshot)

        incomplete_implementation = {**manifest, "implementation": {
            "humanmotionlib/_version.py": implementation["humanmotionlib/_version.py"],
            "humanmotionlib/api.py": implementation["humanmotionlib/api.py"],
        }}
        broken_module_wheel = self.root / "humanmotionlib-missing-module.whl"
        with zipfile.ZipFile(broken_module_wheel, "w") as archive:
            archive.writestr("humanmotionlib/_version.py", generated)
            archive.writestr("humanmotionlib/api.py", source_bytes)
            archive.writestr("humanmotionlib/omitted.py", second_source_bytes)
            archive.writestr("humanmotionlib/resources/characters/controlled.yaml", resource_bytes)
            archive.writestr("humanmotionlib/resources/docs/used-materials.md", documentation_bytes)
            archive.writestr("humanmotionlib/resources/runtime-manifest.json",
                             (json.dumps(incomplete_implementation, sort_keys=True,
                                         separators=(",", ":")) + "\n").encode())
        with (mock.patch.object(workflow, "ROOT", self.root),
              mock.patch.object(workflow, "RESOURCE_FILES", ("docs/used-materials.md",)),
              mock.patch.object(workflow, "RESOURCE_PATTERNS", (("characters", "*.yaml"),))):
            with self.assertRaisesRegex(workflow.WorkflowError, "implementation closure"):
                workflow.verify_wheel_sources(broken_module_wheel, snapshot)

    def test_allocate_run_uses_flat_unique_identity_without_cleanup_records(self) -> None:
        workspace = self.root / "checkout with spaces"
        workspace.mkdir()
        first = workflow.allocate_run(workspace, "package")
        second = workflow.allocate_run(workspace, "package")
        self.assertNotEqual(first, second)
        self.assertEqual(first.parent, workspace / "build")
        self.assertEqual(len(first.name.split("_")), 5)
        self.assertTrue(all(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", part)
                            for part in first.name.split("_")))
    def test_failed_stage_stops_and_keeps_actionable_log(self) -> None:
        log = self.root / "logs/failure.log"
        env = os.environ.copy()
        with self.assertRaisesRegex(workflow.WorkflowError, "stage controlled-failure failed"):
            workflow.run([sys.executable, "-c", "raise SystemExit(7)"], cwd=self.root,
                         env=env, log=log, stage="controlled-failure")
        contents = log.read_text(encoding="utf-8")
        self.assertIn('stage=controlled-failure exit=7', contents)
        self.assertIn(sys.executable, contents)

    def test_uv_sync_failure_stops_before_dependency_check_and_package_work(self) -> None:
        workspace = self.root / "checkout with spaces"
        workspace.mkdir()
        fake_uv = self.root / "fake uv"
        fake_uv.write_text(
            "#!/bin/sh\n"
            "if [ \"$1\" = --version ]; then echo 'uv 0.13.5'; exit 0; fi\n"
            "if [ \"$1\" = venv ]; then exit 0; fi\n"
            "if [ \"$1\" = sync ]; then echo 'controlled sync failure'; exit 17; fi\n"
            "echo 'unexpected later uv stage' >&2; exit 19\n",
            encoding="utf-8",
        )
        fake_uv.chmod(0o755)
        result = subprocess.run(
            ["sh", str(workflow.ROOT / "tools/repository.sh"), "dev", str(workspace), str(fake_uv)],
            cwd=workflow.ROOT, env={"PATH": "/usr/bin:/bin"}, text=True,
            capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 17, result.stdout + result.stderr)
        tools = workspace / "build/project-tools_r1_contributor_current_environment"
        self.assertTrue((tools / "logs/locked-dependencies.log").is_file())
        self.assertFalse((tools / "logs/dependency-check.log").exists())
        self.assertFalse(any(path.name.startswith("package-humanmotionlib_")
                             for path in (workspace / "build").iterdir()))

    def test_partial_tools_environment_reuses_valid_python_and_continues_sync(self) -> None:
        workspace = self.root / "checkout with spaces"
        tools = workspace / "build/project-tools_r1_contributor_current_environment"
        python = tools / "environment/bin/python3.14"
        python.parent.mkdir(parents=True)
        python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        python.chmod(0o755)
        fake_uv = self.root / "fake uv"
        calls = self.root / "uv calls.log"
        fake_uv.write_text(
            "#!/bin/sh\n"
            "printf '%s\\n' \"$*\" >> \"$UV_CALLS\"\n"
            "if [ \"$1\" = --version ]; then echo 'uv 0.13.5'; exit 0; fi\n"
            "if [ \"$1\" = sync ]; then exit 17; fi\n"
            "echo 'unexpected uv command' >&2; exit 19\n",
            encoding="utf-8",
        )
        fake_uv.chmod(0o755)
        result = subprocess.run(
            ["sh", str(workflow.ROOT / "tools/repository.sh"), "dev", str(workspace), str(fake_uv)],
            cwd=workflow.ROOT, env={"PATH": "/usr/bin:/bin", "UV_CALLS": str(calls)},
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 17, result.stdout + result.stderr)
        self.assertIn("Reusing project Python environment", result.stdout)
        self.assertNotIn("venv", calls.read_text(encoding="utf-8"))
        self.assertTrue((tools / "logs/locked-dependencies.log").is_file())

    def test_escaping_tools_environment_symlink_blocks_before_uv_writes(self) -> None:
        workspace = self.root / "checkout with spaces"
        tools = workspace / "build/project-tools_r1_contributor_current_environment"
        outside = self.root / "outside"
        outside.mkdir()
        tools.mkdir(parents=True)
        (tools / "environment").symlink_to(outside, target_is_directory=True)
        fake_uv = self.root / "fake uv"
        calls = self.root / "uv calls.log"
        fake_uv.write_text(
            "#!/bin/sh\n"
            "printf '%s\\n' \"$*\" >> \"$UV_CALLS\"\n"
            "if [ \"$1\" = --version ]; then echo 'uv 0.13.5'; exit 0; fi\n"
            "echo 'unexpected write stage' >&2; exit 19\n",
            encoding="utf-8",
        )
        fake_uv.chmod(0o755)
        result = subprocess.run(
            ["sh", str(workflow.ROOT / "tools/repository.sh"), "dev", str(workspace), str(fake_uv)],
            cwd=workflow.ROOT, env={"PATH": "/usr/bin:/bin", "UV_CALLS": str(calls)},
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("symbolic link", result.stderr)
        self.assertEqual(calls.read_text(encoding="utf-8").splitlines(), ["--version"])
        self.assertEqual(list(outside.iterdir()), [])

    def test_make_route_ignores_ambient_workflow_python_override(self) -> None:
        workspace = self.root / "checkout"
        configured = workspace / "build/project-tools_r1_contributor_current_environment/environment/bin/python3.14"
        configured.parent.mkdir(parents=True)
        env_seen = self.root / "environment seen.txt"
        configured.write_text("#!/bin/sh\nprintf '%s' \"$HML_WORKFLOW_PYTHON\" > \"$ENV_SEEN\"\n", encoding="utf-8")
        configured.chmod(0o755)
        external = self.root / "external-python"
        external.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
        external.chmod(0o755)
        result = subprocess.run(
            ["sh", str(workflow.ROOT / "tools/repository.sh"), "matrix-check", str(workspace),
             "/usr/bin/false", "male", "1.70"],
            cwd=workflow.ROOT,
            env={"PATH": "/usr/bin:/bin", "HML_WORKFLOW_PYTHON": str(external),
                 "ENV_SEEN": str(env_seen)},
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(env_seen.read_text(encoding="utf-8"), str(configured))

    def test_make_matrix_check_without_tools_returns_selected_rebuild_remedy_without_writes(self) -> None:
        workspace = self.root / "clean checkout"
        workspace.mkdir()
        before = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))
        result = subprocess.run(
            ["/usr/bin/make", "matrix-check", f"WORKSPACE={workspace}",
             "CHARACTER=female", "HEIGHT=1.90"],
            cwd=workflow.ROOT, env={"PATH": "/usr/bin:/bin"},
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("make matrix-build CHARACTER=female HEIGHT=1.90", result.stderr)
        after = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))
        self.assertEqual(after, before)

    def test_make_matrix_check_missing_result_is_read_only_but_existing_bad_record_is_logged(self) -> None:
        workspace = self.root / "prepared checkout"
        launcher = workspace / "build/project-tools_r1_contributor_current_environment/environment/bin/python3.14"
        launcher.parent.mkdir(parents=True)
        launcher.write_text(f"#!/bin/sh\nexec {sys.executable} \"$@\"\n", encoding="utf-8")
        launcher.chmod(0o755)
        selection_root = workspace / "build/automate-build-and-verification-matrix_r1_dev_current_female-h190"

        def snapshot() -> dict[str, bytes | None]:
            result: dict[str, bytes | None] = {}
            if workspace.exists():
                for path in workspace.rglob("*"):
                    key = path.relative_to(workspace).as_posix()
                    result[key] = path.read_bytes() if path.is_file() and not path.is_symlink() else None
            return result

        command = ["/usr/bin/make", "matrix-check", f"WORKSPACE={workspace}",
                   "CHARACTER=female", "HEIGHT=1.90"]
        before = snapshot()
        missing = subprocess.run(command, cwd=workflow.ROOT, env={"PATH": "/usr/bin:/bin"},
                                 text=True, capture_output=True, check=False)
        self.assertEqual(missing.returncode, 2, missing.stdout + missing.stderr)
        self.assertIn("make matrix-build CHARACTER=female HEIGHT=1.90", missing.stderr)
        self.assertEqual(snapshot(), before)

        selection_root.mkdir()
        (selection_root / "preserve.txt").write_text("fixture", encoding="utf-8")
        build_record = selection_root / "build.json"
        build_record.write_text("{ malformed", encoding="utf-8")
        before_record = build_record.read_bytes()
        malformed = subprocess.run(command, cwd=workflow.ROOT, env={"PATH": "/usr/bin:/bin"},
                                   text=True, capture_output=True, check=False)
        self.assertEqual(malformed.returncode, 2, malformed.stdout + malformed.stderr)
        self.assertIn("failure", malformed.stdout)
        self.assertEqual(build_record.read_bytes(), before_record)
        self.assertEqual(len(list((selection_root / "logs").glob("check-*.log"))), 1)
        self.assertEqual(json.loads((selection_root / "check.json").read_text())["status"], "failure")

        incompatible = {"schema": "matrix-current-build/v1", "status": "success",
                        "character": "female", "height_m": 1.9, "fixtures": ["neutral", "rest", "arm-raise"],
                        "bpm": 120, "package_identity": {"runtime_manifest_sha256": "outdated"}}
        build_record.write_text(json.dumps(incompatible), encoding="utf-8")
        before_incompatible = build_record.read_bytes()
        stale = subprocess.run(command, cwd=workflow.ROOT, env={"PATH": "/usr/bin:/bin"},
                               text=True, capture_output=True, check=False)
        self.assertEqual(stale.returncode, 2, stale.stdout + stale.stderr)
        self.assertIn("make matrix-build CHARACTER=female HEIGHT=1.90", stale.stdout)
        self.assertEqual(build_record.read_bytes(), before_incompatible)
        self.assertEqual(len(list((selection_root / "logs").glob("check-*.log"))), 2)
        self.assertEqual(json.loads((selection_root / "check.json").read_text())["status"], "failure")

    def test_repository_cleanup_uses_invoking_checkout_config_for_external_workspace(self) -> None:
        workspace = self.root / "external workspace"
        configured = workspace / "build/project-tools_r1_contributor_current_environment"
        target_configured = workspace / "build/target-specific-tools"
        configured.mkdir(parents=True)
        target_configured.mkdir(parents=True)
        (workspace / "pyproject.toml").write_text(
            '[tool.humanmotionlib.workflow]\ntools-root = "build/target-specific-tools"\n',
            encoding="utf-8",
        )
        (configured / "keep.txt").write_text("keep", encoding="utf-8")
        (target_configured / "remove.txt").write_text("remove", encoding="utf-8")
        disposable = workspace / "build/result_run"
        disposable.mkdir()
        (disposable / "output.txt").write_text("remove", encoding="utf-8")
        fakebin = self.root / "fake process tools"
        fakebin.mkdir()
        ps = fakebin / "ps"
        ps.write_text(
            "#!/bin/sh\n"
            "case \"$*\" in\n"
            "  *'-p '*) printf '%s\\n' \"$2\" ;;\n"
            "  *'-Aww '*) printf '%s 1 S cleanup-helper\\n' \"$HML_PROJECT_CLEANUP_PID\" ;;\n"
            "  *) exit 2 ;;\n"
            "esac\n",
            encoding="utf-8",
        )
        ps.chmod(0o755)
        lsof = fakebin / "lsof"
        lsof.write_text("#!/bin/sh\nprintf 'p%s\\n' \"$HML_PROJECT_CLEANUP_PID\"\n", encoding="utf-8")
        lsof.chmod(0o755)
        result = subprocess.run(
            [shutil.which("make") or "make", "clean", f"WORKSPACE={workspace}"],
            cwd=workflow.ROOT,
            env={"PATH": f"{fakebin}:/usr/bin:/bin:/opt/homebrew/bin"},
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((configured / "keep.txt").is_file())
        self.assertFalse(target_configured.exists())
        self.assertFalse(disposable.exists())

    def test_matrix_result_name_is_the_existing_fixed_table_path(self) -> None:
        workspace = self.root / "workspace with spaces"
        workspace.mkdir()
        result = matrix.element_root(workspace, "male", 1.70)
        self.assertEqual(result, workspace / "build/automate-build-and-verification-matrix_r1_dev_current_male-h170")
        self.assertEqual(len(result.name.split("_")), 5)

    def test_literal_make_clean_rejects_symlinked_workspace_without_touching_target(self) -> None:
        target = self.root / "physical workspace"
        target.mkdir()
        (target / "pyproject.toml").write_text(
            '[tool.humanmotionlib.workflow]\n'
            'tools-root = "build/project-tools_r1_contributor_current_environment"\n',
            encoding="utf-8")
        disposable = target / "build/result_run"
        disposable.mkdir(parents=True)
        sentinel = disposable / "keep.txt"
        sentinel.write_text("must remain", encoding="utf-8")
        link = self.root / "workspace link"
        link.symlink_to(target, target_is_directory=True)

        result = subprocess.run(
            [shutil.which("make") or "make", "clean", f"WORKSPACE={link}"],
            cwd=workflow.ROOT, text=True, capture_output=True, check=False)

        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("Workspace path contains a symbolic link", result.stderr)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "must remain")


if __name__ == "__main__":
    unittest.main()
