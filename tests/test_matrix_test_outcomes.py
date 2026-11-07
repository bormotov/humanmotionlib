"""Structured host-check outcomes retain unittest's existing selection semantics."""

from __future__ import annotations

import ast
from io import StringIO
import json
import importlib.util
import hashlib
from pathlib import Path
import tempfile
import sys
import unittest
from unittest import mock

CHECK_HOST_PATH = Path(__file__).resolve().parents[1] / "src/humanmotionlib/check_host.py"
spec = importlib.util.spec_from_file_location("matrix_check_host", CHECK_HOST_PATH)
assert spec is not None and spec.loader is not None
check_host = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = check_host
spec.loader.exec_module(check_host)

ACCEPTANCE_PATH = Path(__file__).resolve().parent / "installed_acceptance/run.py"
acceptance_spec = importlib.util.spec_from_file_location("installed_acceptance_runner", ACCEPTANCE_PATH)
assert acceptance_spec is not None and acceptance_spec.loader is not None
installed_acceptance = importlib.util.module_from_spec(acceptance_spec)
sys.modules[acceptance_spec.name] = installed_acceptance
acceptance_spec.loader.exec_module(installed_acceptance)


class StructuredOutcomeTests(unittest.TestCase):
    def run_report(self, suite, exclusions=None, discovery_errors=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "host-checks.json"
        outcome = check_host._test_outcome(
            suite, exclusions or {name: 0 for name in check_host.BACKEND_EXCLUSIONS},
            discovery_errors or [], StringIO(),
        )
        outcome["import_identity"] = check_host._import_identity()
        check_host._atomic_json(path, outcome)
        return json.loads(path.read_text()), path

    def test_success_skip_failure_error_and_exclusion_records(self):
        class Cases(unittest.TestCase):
            def test_pass(self):
                pass

            @unittest.skip("controlled skip")
            def test_skip(self):
                self.fail("must not run")

            def test_fail(self):
                self.fail("controlled failure")

            def test_error(self):
                raise RuntimeError("controlled error")

        suite = unittest.TestSuite(Cases(name) for name in (
            "test_pass", "test_skip", "test_fail", "test_error"))
        exclusions = {name: 0 for name in check_host.BACKEND_EXCLUSIONS}
        exclusions["tests.test_blender_backend"] = 2
        report, path = self.run_report(suite, exclusions)

        self.assertTrue(path.is_file())
        self.assertEqual(report["schema"], "matrix-test-outcome/v1")
        self.assertEqual(report["status"], "failed")
        self.assertEqual((report["tests"], report["discovered"], report["passed"],
                          report["failed"], report["errors"], report["skipped"],
                          report["exit_code"]), (4, 4, 1, 1, 1, 1, 1))
        self.assertEqual(next(item["count"] for item in report["excluded"]
                              if item["module"] == "tests.test_blender_backend"), 2)
        self.assertEqual(sum(item["count"] for item in report["excluded"]), 2)
        self.assertIn("test_fail", report["failure_records"][0]["test_id"])
        self.assertIn("controlled failure", report["failure_records"][0]["traceback"])
        self.assertIn("test_error", report["error_records"][0]["test_id"])
        self.assertEqual(report["skip_records"][0]["reason"], "controlled skip")
        self.assertEqual(report["import_identity"]["python"], check_host.sys.executable)

    def test_discovery_errors_and_zero_tests_are_non_success(self):
        discovery, _ = self.run_report(unittest.TestSuite(), discovery_errors=["broken import"])
        self.assertEqual((discovery["status"], discovery["errors"], discovery["exit_code"]),
                         ("failed", 1, 1))
        self.assertEqual(discovery["error_records"][0]["message"], "broken import")

        empty, _ = self.run_report(unittest.TestSuite())
        self.assertEqual((empty["status"], empty["tests"], empty["exit_code"]),
                         ("failed", 0, 1))

    def test_legacy_text_runner_keeps_failure_and_exclusion_behavior(self):
        class Failing(unittest.TestCase):
            def runTest(self):
                self.fail("legacy failure")

        output = StringIO()
        exclusions = {name: 0 for name in check_host.BACKEND_EXCLUSIONS}
        exclusions["tests.test_pipeline_faults"] = 3
        status = check_host.run_selected_tests(unittest.TestSuite([Failing()]), exclusions, [], output)
        self.assertEqual(status, 1)
        self.assertIn("Excluded tests.test_pipeline_faults", output.getvalue())
        self.assertIn("FAILED", output.getvalue())
        self.assertIn("legacy failure", output.getvalue())

    def test_cli_writes_atomic_outcome_for_selected_tests(self):
        class Passing(unittest.TestCase):
            def test_pass(self):
                pass

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tests = root / "tests"
            tests.mkdir()
            report_path = root / "host-checks.json"
            with mock.patch.object(check_host, "check_environment", return_value=[]), \
                 mock.patch.object(check_host, "discover_host_tests", return_value=(
                     unittest.TestSuite([Passing("test_pass")]),
                     {name: 0 for name in check_host.BACKEND_EXCLUSIONS}, [])):
                status = check_host.main(["--test-root", str(tests),
                                          "--json-report", str(report_path)])
            report = json.loads(report_path.read_text())
        self.assertEqual(status, 0)
        self.assertEqual(report["schema"], "matrix-test-outcome/v1")
        self.assertEqual((report["status"], report["tests"], report["passed"],
                          report["exit_code"]), ("passed", 1, 1, 0))
        self.assertIn("package_origin", report["import_identity"])

    def test_cli_blocks_checkout_import_before_discovery(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tests = root / "tests"
            tests.mkdir()
            report_path = root / "build/host-checks.json"
            identity = {"python": "/candidate/bin/python", "sys_prefix": "/candidate",
                        "package_origin": str(root / "src/humanmotionlib/__init__.py"),
                        "package_version": "0.0.0", "error": ""}
            with mock.patch.object(check_host, "check_environment", return_value=[]), \
                 mock.patch.object(check_host, "_import_identity", return_value=identity), \
                 mock.patch.object(check_host, "discover_host_tests", side_effect=AssertionError(
                     "test discovery must not run for a checkout import")):
                status = check_host.main(["--test-root", str(tests),
                                          "--json-report", str(report_path)])
            report = json.loads(report_path.read_text())
        self.assertEqual(status, 1)
        self.assertEqual((report["status"], report["errors"], report["exit_code"]),
                         ("blocked", 1, 1))
        self.assertIn("inside the checkout", report["error_records"][0]["message"])

    def test_exact_declared_candidate_environment_is_narrowly_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            prefix = root / "build/candidate/runtime"
            purelib = prefix / "lib/python/site-packages"
            package = purelib / "humanmotionlib"
            package.mkdir(parents=True)
            (package / "resources").mkdir()
            runtime_manifest = package / "resources/runtime-manifest.json"
            runtime_manifest.write_text('{"format":"test"}')
            origin = package / "__init__.py"
            origin.write_text("# installed package\n")
            wheel = root / "build/candidate/humanmotionlib.whl"
            wheel.write_bytes(b"candidate wheel")
            wheel_hash = hashlib.sha256(wheel.read_bytes()).hexdigest()
            interpreter = prefix / "bin/python"
            runtime_audit = {
                "python": str(interpreter), "sys_prefix": str(prefix), "purelib": str(purelib),
                "humanmotionlib": {"origin": str(origin), "version": "1.2.3"},
                "runtime_manifest_sha256": hashlib.sha256(runtime_manifest.read_bytes()).hexdigest(),
            }
            environment = {"python": str(interpreter), "role": "dev", "wheel": str(wheel),
                           "wheel_sha256": wheel_hash, "audit": {"interpreter": runtime_audit}}
            manifest = {"schema": "matrix-candidate/v1", "status": "succeeded",
                        "candidate_identity": "candidate-id", "source_snapshot_sha256": "source-hash",
                        "runtime_environments": {"dev": environment},
                        "artifacts": [{"path": str(wheel), "sha256": wheel_hash}]}
            manifest_path = root / "matrix-candidate.json"
            manifest_path.write_text(json.dumps(manifest))
            identity = {"python": str(interpreter), "sys_prefix": str(prefix),
                        "package_origin": str(origin), "package_version": "1.2.3", "error": ""}

            class Distribution:
                def read_text(self, name):
                    return json.dumps({"url": wheel.as_uri()}) if name == "direct_url.json" else None

            args = check_host.argparse.Namespace(
                expected_python=str(interpreter), expected_prefix=str(prefix),
                expected_purelib=str(purelib), expected_package_origin=str(origin),
                candidate_manifest=str(manifest_path))
            with mock.patch.object(check_host.importlib.metadata, "distribution", return_value=Distribution()), \
                 mock.patch.object(check_host.sys, "prefix", str(prefix)), \
                 mock.patch.object(check_host.sysconfig, "get_paths", return_value={"purelib": str(purelib)}):
                errors = check_host._validate_expected_candidate(args, identity, root)
            self.assertEqual(errors, [])

            args.expected_prefix = str(root / "another-env")
            with mock.patch.object(check_host.importlib.metadata, "distribution", return_value=Distribution()), \
                 mock.patch.object(check_host.sys, "prefix", str(prefix)), \
                 mock.patch.object(check_host.sysconfig, "get_paths", return_value={"purelib": str(purelib)}):
                rejected = check_host._validate_expected_candidate(args, identity, root)
            self.assertTrue(any("prefix" in error for error in rejected))


class InstalledRunOwnershipTests(unittest.TestCase):
    def test_installed_acceptance_outcome_distinguishes_pass_fail_and_interrupt(self):
        passed = installed_acceptance.matrix_outcome(status="passed", package_origin="/venv/pkg.py",
                                                     package_version="1.2.3")
        failed = installed_acceptance.matrix_outcome(status="failed", message="import failure")
        interrupted = installed_acceptance.matrix_outcome(status="interrupted",
                                                          message="KeyboardInterrupt")
        self.assertEqual((passed["schema"], passed["tests"], passed["passed"],
                          passed["exit_code"]), ("matrix-test-outcome/v1", 1, 1, 0))
        self.assertEqual((failed["failed"], failed["errors"], failed["exit_code"]), (1, 1, 1))
        self.assertEqual((interrupted["status"], interrupted["exit_code"]), ("interrupted", 130))

    def test_accepts_only_fresh_transient_root_within_stable_element_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            (workspace / "build").mkdir()
            element = workspace / "build/automate-build-and-verification-matrix_r1_dev_current_element-male-h170"
            root = element / ".tmp/installed-acceptance"
            root.mkdir(parents=True)
            allocated, identity, selected_element = installed_acceptance.owned_run_root(workspace, root)
            self.assertEqual(allocated, root.resolve())
            self.assertEqual(identity, "automate-build-and-verification-matrix_r1_dev_current")
            self.assertEqual(selected_element, element.resolve())
            with self.assertRaisesRegex(ValueError, r"\.tmp/installed-acceptance"):
                installed_acceptance.owned_run_root(workspace, element)
            wrong_harness = element / ".tmp/wrong-harness"
            wrong_harness.mkdir()
            with self.assertRaisesRegex(ValueError, r"\.tmp/installed-acceptance"):
                installed_acceptance.owned_run_root(workspace, wrong_harness)
            (root / "scratch").mkdir()
            with self.assertRaises(FileExistsError):
                installed_acceptance.owned_run_root(workspace, root)
            outside = workspace / "outside"
            outside.mkdir()
            linked = element / "linked"
            linked.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                installed_acceptance.owned_run_root(workspace, linked)

    def test_rejects_workspace_and_intermediate_element_aliases(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            workspace = base / "workspace"
            (workspace / "build").mkdir(parents=True)
            element = workspace / "build/portable-installed-runtime_1234567_ci_run-123-attempt-1_checks"
            harness = element / ".tmp/installed-acceptance"
            harness.mkdir(parents=True)

            workspace_alias = base / "workspace-alias"
            workspace_alias.symlink_to(workspace, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "selected workspace path"):
                installed_acceptance.owned_run_root(
                    workspace, workspace_alias / "build" / element.name / ".tmp/installed-acceptance")

            element_alias = element / "alias"
            element_alias.symlink_to(element / ".tmp", target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink component"):
                installed_acceptance.owned_run_root(
                    workspace, element_alias / "installed-acceptance")

            accepted, _, owner = installed_acceptance.owned_run_root(workspace, harness)
            self.assertEqual(accepted, harness.resolve())
            self.assertEqual(owner, element.resolve())

    def test_preflights_all_generated_outputs_inside_selected_scratch(self):
        with tempfile.TemporaryDirectory() as temporary:
            build = Path(temporary) / "build"
            build.mkdir()
            element = build / "automate-build-and-verification-matrix_r1_reviewer_current_element-male-h170"
            harness = element / ".tmp/installed-acceptance"
            harness.mkdir(parents=True)
            scratch = element / ".tmp/installed-generated"
            alias = element / ".tmp/generated-alias"
            alias.symlink_to(scratch, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink component"):
                installed_acceptance.preflight_generated_runs(
                    harness, element, "automate-build-and-verification-matrix_r1_reviewer_try-1", alias)
            alias.unlink()
            for overlapping in (element / ".tmp", harness, harness / "scratch"):
                with self.subTest(overlapping=overlapping), self.assertRaisesRegex(
                        ValueError, "disjoint from the acceptance harness"):
                    installed_acceptance.preflight_generated_runs(
                        harness, element,
                        "automate-build-and-verification-matrix_r1_reviewer_try-1", overlapping)
            self.assertFalse((element / ".tmp/build").exists())
            self.assertFalse((harness / "scratch").exists())
            scratch_workspace, paths = installed_acceptance.preflight_generated_runs(
                harness, element, "automate-build-and-verification-matrix_r1_reviewer_try-1", scratch)
            self.assertEqual(scratch_workspace, scratch.resolve())
            self.assertEqual(set(paths), set(installed_acceptance.RUN_KINDS))
            self.assertEqual(len(paths), 15)
            self.assertTrue(all(path.parent.resolve() == (scratch / "build").resolve()
                                for path in paths.values()))
            self.assertTrue(all(len(path.name.split("_")) == 5 for path in paths.values()))
            self.assertTrue(all(not path.exists() for path in paths.values()))

            obstructed = paths["api-failure"]
            obstructed.mkdir()
            with self.assertRaises(FileExistsError):
                installed_acceptance.preflight_generated_runs(
                    harness, element, "automate-build-and-verification-matrix_r1_reviewer_try-1", scratch)
            self.assertTrue(obstructed.is_dir())
            self.assertTrue(all(not path.exists() for key, path in paths.items()
                                if key != "api-failure"))

            linked_scratch = element / ".tmp/installed-generated-linked-build"
            linked_scratch.mkdir()
            outside_build = build.parent / "outside-build"
            outside_build.mkdir()
            (linked_scratch / "build").symlink_to(outside_build, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "build/ contains a symlink"):
                installed_acceptance.preflight_generated_runs(
                    harness, element, "automate-build-and-verification-matrix_r1_reviewer_try-1",
                    linked_scratch)

    def test_accepts_ci_harness_layout_and_uses_owning_element_scratch(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "caller" / "workspace"
            (workspace / "build").mkdir(parents=True)
            element = workspace / "build/portable-installed-runtime_1234567_ci_run-123-attempt-1_checks"
            harness = element / ".tmp/installed-acceptance"
            harness.mkdir(parents=True)

            allocated, identity, selected_element = installed_acceptance.owned_run_root(workspace, harness)
            self.assertEqual(allocated, harness.resolve())
            self.assertEqual(identity, "portable-installed-runtime_1234567_ci_run-123-attempt-1")
            self.assertEqual(selected_element, element.resolve())
            generated_workspace, generated = installed_acceptance.preflight_generated_runs(
                allocated, selected_element, identity)
            expected_scratch = element / ".tmp/installed-generated"
            self.assertEqual(generated_workspace, expected_scratch.resolve())
            self.assertTrue(all(path.parent == (expected_scratch / "build").resolve()
                                for path in generated.values()))
            self.assertTrue(all(not path.exists() for path in generated.values()))

    def test_installed_negative_probe_is_self_contained_python(self):
        source = ast.parse(ACCEPTANCE_PATH.read_text())
        snippets = [node.value for node in ast.walk(source)
                    if isinstance(node, ast.Constant) and isinstance(node.value, str)
                    and "workspace, prepared = map(pathlib.Path, sys.argv[1:3])" in node.value
                    and "invalid_outputs = list(map(pathlib.Path, sys.argv[3:]))" in node.value]
        self.assertEqual(len(snippets), 1)
        compile(snippets[0], str(ACCEPTANCE_PATH) + "#invalid-selection-probe", "exec")
        self.assertNotIn("generated_roots", snippets[0])

    def test_workspace_inventory_prunes_build_and_never_follows_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "workspace"
            build = root / "build"
            root.mkdir()
            build.mkdir()
            (root / "source.txt").write_text("stable source\n")
            (build / "generated.bin").write_bytes(b"generated")
            outside = Path(temporary) / "external-target.txt"
            outside.write_text("target\n")
            (root / "external-link").symlink_to(outside)
            before = installed_acceptance.outside_build_inventory(root, build)
            self.assertEqual(set(before), {"external-link", "source.txt"})
            self.assertEqual(before["external-link"]["type"], "symlink")
            self.assertNotIn("build/generated.bin", before)
            outside.write_text("changed target\n")
            self.assertEqual(before, installed_acceptance.outside_build_inventory(root, build))
            (root / "source.txt").write_text("modified source\n")
            after = installed_acceptance.outside_build_inventory(root, build)
            self.assertNotEqual(before, after)

    def test_candidate_manifest_binds_wheel_and_installed_role_environment(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            candidate_root = root / "candidate"
            artifacts = candidate_root / "artifacts" / "direct"
            artifacts.mkdir(parents=True)
            wheel = artifacts / "humanmotionlib-test.whl"
            wheel.write_bytes(b"synthetic candidate wheel")
            role_root = candidate_root / "runtime-dev-env"
            python = role_root / "bin/python"
            python.parent.mkdir(parents=True)
            python.write_text("synthetic interpreter identity")
            manifest_path = candidate_root / "matrix-candidate.json"
            manifest_path.write_text(json.dumps({
                "schema": "matrix-candidate/v1",
                "status": "succeeded",
                "candidate_identity": "candidate-fixture-identity",
                "source_snapshot_sha256": "a" * 64,
                "runtime_environments": {"dev": {"python": str(python)}},
                "artifacts": [{"path": str(wheel), "sha256": hashlib.sha256(
                    wheel.read_bytes()).hexdigest(), "bytes": wheel.stat().st_size}],
            }))
            run_root = root / "add-shared-body-characters_r10_dev_try-1_installed"
            candidate = installed_acceptance.candidate_reference(manifest_path, python, run_root)
            self.assertEqual(candidate["candidate_identity"], "candidate-fixture-identity")
            self.assertEqual(candidate["runtime_python"], str(python))
            self.assertEqual(candidate["wheel_path"], str(wheel))
            self.assertEqual(candidate["wheel_sha256"], hashlib.sha256(
                wheel.read_bytes()).hexdigest())

            with self.assertRaisesRegex(ValueError, "does not match"):
                installed_acceptance.candidate_reference(
                    manifest_path, candidate_root / "runtime-reviewer-env/bin/python", run_root)
            with self.assertRaisesRegex(ValueError, "hash differs"):
                wheel.write_bytes(b"tampered wheel")
                installed_acceptance.candidate_reference(manifest_path, python, run_root)


if __name__ == "__main__":
    unittest.main()
