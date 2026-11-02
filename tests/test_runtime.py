# SPDX-License-Identifier: Apache-2.0
"""Contract and synthetic failure tests for repository-owned child processes."""

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
import unittest
from unittest import mock

from humanmotionlib import __version__
from humanmotionlib.runtime import (DEFAULT_BUILD_TIMEOUT, DEFAULT_PROBE_TIMEOUT, DEFAULT_RENDER_TIMEOUT,
                           DEFAULT_SLOT_TIMEOUT, KILL_REAP_SECONDS, TERMINATE_GRACE_SECONDS,
                           MAX_TIMEOUT_SECONDS, InvocationError, SlotTimeout, backend_contract, check_blender_version,
                           inspect_blender as _inspect_blender, invocation as _invocation,
                           project_root, validate_managed_pass_root, validate_operation_root,
                           validate_timeout, _group_state)
from tests.run_roots import fresh_test_run_root, test_run_root, test_workspace


def invocation(*args, **kwargs):
    kwargs.setdefault("workspace", test_workspace("runtime"))
    return _invocation(*args, **kwargs)


def inspect_blender(*args, **kwargs):
    kwargs.setdefault("workspace", test_workspace("runtime"))
    return _inspect_blender(*args, **kwargs)


def setUpModule():
    test_run_root("runtime")
    global _CHECKS_ROOT
    _CHECKS_ROOT = fresh_test_run_root("runtime-checks", module="runtime")


def checks_root():
    return _CHECKS_ROOT


def case(name):
    return fresh_test_run_root(f"runtime-{name}", module="runtime")


def read_receipt(error):
    return json.loads(Path(error.receipt).read_text())


class ProcessGroupStateTests(unittest.TestCase):
    def test_process_group_state_uses_only_owned_group_probe(self):
        for raw_state in ("absent", "present", "ambiguous"):
            with self.subTest(raw_state=raw_state), \
                 mock.patch("humanmotionlib.runtime.subprocess.run",
                            side_effect=PermissionError("global process table denied")), \
                 mock.patch("humanmotionlib.runtime._raw_group_state", return_value=raw_state) as probe:
                self.assertEqual(_group_state(410, anchor_pid=410), raw_state)
                probe.assert_called_once_with(410)

    def test_process_group_runtime_has_no_process_table_command(self):
        import inspect
        import humanmotionlib.runtime as runtime_module
        source = inspect.getsource(runtime_module)
        self.assertNotIn("ps -Ao", source)
        self.assertNotIn("ps -o", source)


class BackendContractTests(unittest.TestCase):
    def test_documented_finite_runtime_defaults(self):
        self.assertEqual((DEFAULT_PROBE_TIMEOUT, DEFAULT_BUILD_TIMEOUT, DEFAULT_RENDER_TIMEOUT,
                          DEFAULT_SLOT_TIMEOUT, TERMINATE_GRACE_SECONDS, KILL_REAP_SECONDS,
                          MAX_TIMEOUT_SECONDS), (30.0, 1800.0, 14400.0, 30.0, 5.0, 5.0, 86400.0))

    def test_pinned_backend(self):
        expected = backend_contract()
        check_blender_version(expected["blender-version"], expected["blender-build"])
        for version, build in [("5.2.1 LTS", expected["blender-build"]),
                               (expected["blender-version"], "another-build")]:
            with self.subTest(version=version, build=build):
                with self.assertRaisesRegex(ValueError, "version mismatch"):
                    check_blender_version(version, build)

    def test_supervision_test_imports_do_not_allocate_roots(self):
        build = test_workspace("runtime") / "build"
        before = {entry.name for entry in build.iterdir()}
        environment = os.environ.copy()
        environment.pop("HUMANMOTIONLIB_TEST_RUN_ROOT", None)
        modules = ("tests.test_runtime", "tests.test_run_blender",
                   "tests.test_blender_backend", "tests.test_pipeline_faults")
        code = "import importlib; " + "; ".join(f"importlib.import_module({module!r})" for module in modules)
        checkout_root = Path(__file__).resolve().parents[1]
        subprocess.run([sys.executable, "-c", code], cwd=checkout_root, env=environment,
                       check=True, capture_output=True, text=True, timeout=10)
        after = {entry.name for entry in build.iterdir()}
        self.assertEqual(after, before, "importing the stock suites must not allocate or write test roots")


class ProbeTests(unittest.TestCase):
    def test_probe_resolves_symlink_and_records_pinned_identity(self):
        root = case("resolved-probe")
        real = root / "blender-real"
        real.touch()
        link = root / "blender-link"
        link.symlink_to(real)
        stdout = root / "probe.stdout"
        expected = backend_contract()
        stdout.write_text(f"Blender {expected['blender-version']}\nbuild hash: {expected['blender-build']}\n")
        receipt = {"stdout_log": str(stdout), "executable": str(real.resolve()), "invocation_id": "probe-test"}
        with mock.patch("humanmotionlib.runtime.shutil.which", return_value=str(link)), \
             mock.patch("humanmotionlib.runtime.invocation", return_value=receipt) as launch:
            identity = inspect_blender(root)
        self.assertEqual(identity["version"], expected["blender-version"])
        self.assertEqual(identity["build_hash"], expected["blender-build"])
        self.assertEqual(launch.call_args.args[0][0], str(real.resolve()))
        self.assertEqual(launch.call_args.args[0][1], "--version")

    def test_probe_identity_mismatch_finalizes_failure_receipt(self):
        root = case("mismatched-probe")
        stdout = root / "probe.stdout"
        stdout.write_text("Blender 5.2.1 LTS\nbuild hash: another-build\n")
        receipt = {"stdout_log": str(stdout), "executable": "blender", "invocation_id": "bad-probe"}
        with mock.patch("humanmotionlib.runtime.shutil.which", return_value="/usr/bin/blender"), \
             mock.patch("humanmotionlib.runtime.invocation", return_value=receipt) as launch:
            with self.assertRaises(InvocationError) as caught:
                inspect_blender(root)
        self.assertEqual(launch.call_count, 1)
        self.assertEqual(launch.call_args.args[0][1], "--version")
        failed = json.loads(Path(caught.exception.receipt).read_text())
        self.assertEqual(failed["outcome"], "identity_error")
        self.assertIn("version mismatch", failed["error"])

    def test_failed_probe_prevents_build_script_launch(self):
        from humanmotionlib import run_blender
        input_root = case("probe-failure-input")
        input_path = input_root / "input.json"
        input_path.write_text("prepared")
        output = fresh_test_run_root("probe-failure")
        prepared = {"content_sha256": "synthetic", "samples": [],
                    "sources": {"review-scene": {"cameras": []}}}
        with mock.patch.object(run_blender, "read_prepared", return_value=prepared), \
             mock.patch.object(run_blender, "inspect_blender", side_effect=InvocationError("probe failed", "receipt")), \
             mock.patch.object(run_blender, "invocation") as launch:
            with self.assertRaises(InvocationError):
                run_blender.run(input_path, output, workspace=test_workspace("runtime"))
        launch.assert_not_called()

    def test_runner_requires_flat_owned_run_identity_for_nested_tool_content(self):
        from humanmotionlib.run_blender import owning_run_root
        owner = checks_root()
        nested = owner / "clean-a"
        self.assertEqual(owning_run_root(nested, test_workspace("runtime")), owner)
        with self.assertRaisesRegex(ValueError, "five-component"):
            owning_run_root(test_workspace("runtime") / "build" / "bad-run", test_workspace("runtime"))
        with self.assertRaisesRegex(ValueError, "outside build"):
            owning_run_root(checks_root().parent, test_workspace("runtime"))
        nested_identity = checks_root() / "nested-run_r3_dev_try-1_pack" / "clean-a"
        with self.assertRaisesRegex(ValueError, "nested run identity"):
            owning_run_root(nested_identity, test_workspace("runtime"))


class InvocationTests(unittest.TestCase):
    def test_managed_pass_receipts_and_scratch_stay_below_designated_passes(self):
        owner = fresh_test_run_root("managed-pass")
        for name in ("clean-a", "skeleton-default", "male-singleton", "stature-190"):
            pass_root = owner / name
            pass_root.mkdir()
            self.assertEqual(validate_managed_pass_root(pass_root, owner, test_workspace("runtime")), pass_root)
            self.assertEqual(validate_operation_root(pass_root, test_workspace("runtime"), owner), pass_root)
        for invalid in (owner / "other", owner / "clean-a" / "nested_run_r1_dev_try-1_pack"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_operation_root(invalid, test_workspace("runtime"), owner)

        package_identity = {"version": __version__, "resources": {},
                            "backend_contract": "b" * 64, "implementation": {}}
        with mock.patch("humanmotionlib.package_resources.verify_runtime_integrity",
                        return_value=package_identity), \
             mock.patch("humanmotionlib.package_resources.manifest_sha256",
                        return_value="a" * 64):
            receipt = invocation([sys.executable, "-c", "print('managed pass')"],
                                 run_root=pass_root, owner_run=owner,
                                 operation="managed-pass-test", timeout_seconds=3)
        receipt_dir = Path(receipt["stdout_log"]).parent
        self.assertEqual(receipt_dir.parent, pass_root / "processes")
        self.assertEqual(receipt["operation_root"], str(pass_root))
        self.assertEqual(receipt["owning_run_root"], str(owner))
        self.assertEqual(receipt["scratch_cleanup"]["status"], "removed-after-child-exit")
        self.assertFalse((pass_root / "scratch").exists())
        self.assertFalse((owner / "processes").exists())
        self.assertFalse((owner / "scratch").exists())

    def test_deadline_validation_prevents_spawn(self):
        for value in (0, -1, float("nan"), float("inf"), 86401, None, "bad"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_timeout(value)
        root = case("invalid-deadline")
        with self.assertRaises(ValueError):
            invocation([sys.executable, "-c", "raise SystemExit(99)"], run_root=root,
                       operation="invalid-deadline", timeout_seconds=0)
        self.assertFalse((root / "processes").exists())

    def test_runtime_rejects_evidence_without_valid_build_owner(self):
        with self.assertRaisesRegex(ValueError, "five-component"):
            invocation([sys.executable, "-c", "print('must not spawn')"],
                run_root=test_workspace("runtime") / "build" / "invalid-run",
                       operation="invalid-run-root", timeout_seconds=2)
        with self.assertRaisesRegex(ValueError, "nested run identity"):
            invocation([sys.executable, "-c", "print('must not spawn')"],
                       run_root=checks_root() / "nested-run_r3_dev_try-1_pack" / "processes",
                       operation="nested-run-root", timeout_seconds=2)

    def test_missing_executable_and_spawn_error_have_receipts(self):
        root = case("spawn-errors")
        for command in ([str(root / "does-not-exist")], ["/dev/null/not-executable"]):
            with self.subTest(command=command), self.assertRaises(InvocationError) as caught:
                invocation(command, run_root=root, operation="missing-executable", timeout_seconds=2)
            receipt = read_receipt(caught.exception)
            self.assertEqual(receipt["outcome"], "spawn_error")
            self.assertEqual(receipt["state"], "failed")
            self.assertTrue(Path(receipt["stdout_log"]).is_file())
            self.assertTrue(Path(receipt["stderr_log"]).is_file())
            self.assertEqual(receipt["workspace"], str(test_workspace("runtime")))
            self.assertEqual(receipt["package_version"], __version__)
            self.assertEqual(len(receipt["runtime_manifest_sha256"]), 64)
            self.assertTrue(receipt["resource_hashes"])
            self.assertEqual(len(receipt["backend_contract_sha256"]), 64)
            self.assertTrue(receipt["implementation_hashes"])

    def test_zero_nonzero_and_signal_results_are_classified(self):
        root = case("exit-results")
        ok = invocation([sys.executable, "-c", "print('synthetic success')"], run_root=root,
                        operation="zero-exit", timeout_seconds=2)
        self.assertEqual(ok["state"], "succeeded")
        self.assertIn("synthetic success", Path(ok["stdout_log"]).read_text())
        for args, expected_code, expected_signal in ((["raise SystemExit(7)"], 7, None),
                                                      (["import os,signal; os.kill(os.getpid(),signal.SIGTERM)"], -signal.SIGTERM, signal.SIGTERM)):
            with self.subTest(expected_code=expected_code), self.assertRaises(InvocationError) as caught:
                invocation([sys.executable, "-c", args[0]], run_root=root,
                           operation="nonzero-exit", timeout_seconds=2)
            receipt = read_receipt(caught.exception)
            self.assertEqual(receipt["return_code"], expected_code)
            self.assertEqual(receipt["signal"], expected_signal)
            self.assertEqual(receipt["state"], "failed")

    def test_direct_child_exit_with_live_descendant_fails_and_cleans_owned_group(self):
        root = checks_root()
        sentinel = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"],
                                    start_new_session=True)
        try:
            for exit_code in (0, 7):
                with self.subTest(exit_code=exit_code), self.assertRaises(InvocationError) as caught:
                    script = ("import subprocess,sys; "
                              "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
                              "print(p.pid, flush=True); sys.exit(" + str(exit_code) + ")")
                    invocation([sys.executable, "-c", script], run_root=case(f"exit-descendant-{exit_code}"),
                               operation=f"exit-descendant-{exit_code}", timeout_seconds=3,
                               slot_timeout_seconds=2)
                receipt = read_receipt(caught.exception)
                self.assertEqual(receipt["outcome"], "orphaned-descendant")
                self.assertEqual(receipt["cleanup"]["status"], "confirmed")
                self.assertEqual(receipt["state"], "failed")
                self.assertIsNotNone(receipt["return_code"])
                self.assertEqual(_group_state(receipt["process_group_id"]), "absent")
                self.assertIsNone(sentinel.poll(), "cleanup must preserve an unrelated process group")
        finally:
            sentinel.terminate()
            sentinel.wait(timeout=2)

    def test_timeout_kills_resistant_descendant_and_preserves_sentinel(self):
        root = case("timeout-descendant")
        sentinel = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
        started = time.monotonic()
        script = ("import signal,subprocess,sys,time; "
                  "subprocess.Popen([sys.executable,'-c',\"import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(30)\"]); "
                  "time.sleep(30)")
        try:
            with self.assertRaises(InvocationError) as caught:
                invocation([sys.executable, "-c", script], run_root=root, operation="timeout-test",
                           timeout_seconds=1, slot_timeout_seconds=2)
            elapsed = time.monotonic() - started
            receipt = read_receipt(caught.exception)
            self.assertEqual(receipt["outcome"], "timeout")
            self.assertIn(receipt["cleanup"]["status"], {"confirmed", "cleanup_pending"})
            self.assertLess(elapsed, 13)
            self.assertEqual(os.kill(sentinel.pid, 0), None)
        finally:
            sentinel.terminate()
            sentinel.wait(timeout=2)

    def test_cancellation_cleans_owned_group_and_finalizes_receipt(self):
        root = case("cancellation")
        sentinel = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
        timer = subprocess.Popen([sys.executable, "-c", "import os,signal,time; time.sleep(.3); os.kill(os.getppid(),signal.SIGINT)"], start_new_session=True)
        try:
            with self.assertRaises(InvocationError) as caught:
                invocation([sys.executable, "-c", "import time; time.sleep(30)"], run_root=root,
                           operation="cancel-test", timeout_seconds=10, slot_timeout_seconds=2)
            timer.wait(timeout=2)
            receipt = read_receipt(caught.exception)
            self.assertEqual(receipt["outcome"], "cancelled")
            self.assertEqual(receipt["cleanup"]["status"], "confirmed")
            self.assertEqual(receipt["state"], "failed")
            self.assertIsNone(os.kill(sentinel.pid, 0))
            released = invocation([sys.executable, "-c", "print('slot released')"],
                                  run_root=case("after-cancellation"), operation="after-cancel",
                                  timeout_seconds=2, slot_timeout_seconds=2)
            self.assertEqual(released["state"], "succeeded")
        finally:
            if timer.poll() is None:
                timer.terminate()
            timer.wait(timeout=2)
            sentinel.terminate()
            sentinel.wait(timeout=2)

    def test_incomplete_output_fails_closed_and_logs_validation(self):
        root = case("incomplete-output")
        stale = root / "stale.json"
        stale.write_text("old output")
        with self.assertRaises(InvocationError) as caught:
            invocation([sys.executable, "-c", "print('no current output')"], run_root=root,
                       operation="output-test", timeout_seconds=2, expected_outputs=[root / "missing.json"])
        receipt = read_receipt(caught.exception)
        self.assertEqual(receipt["output_validation"]["status"], "fail")
        self.assertEqual(receipt["state"], "failed")

    def test_stale_output_is_rejected_before_child_spawn(self):
        root = case("stale-output")
        stale = root / "result.json"
        stale.write_text("previous attempt")
        with self.assertRaises(InvocationError) as caught:
            invocation([sys.executable, "-c", "raise SystemExit(99)"], run_root=root,
                       operation="stale-output", timeout_seconds=2, expected_outputs=[stale])
        receipt = read_receipt(caught.exception)
        self.assertEqual(receipt["outcome"], "stale_output")
        self.assertEqual(receipt["elapsed_seconds"], 0.0)
        self.assertFalse(Path(receipt["stdout_log"]).read_text())

    def test_nonzero_exit_fails_even_when_expected_output_was_written(self):
        root = case("nonzero-complete-output")
        output = root / "result.json"
        script = f"from pathlib import Path; Path({str(output)!r}).write_text('complete'); raise SystemExit(4)"
        with self.assertRaises(InvocationError) as caught:
            invocation([sys.executable, "-c", script], run_root=root,
                       operation="nonzero-complete-output", timeout_seconds=2, expected_outputs=[output])
        receipt = read_receipt(caught.exception)
        self.assertEqual(receipt["outcome"], "exit")
        self.assertEqual(receipt["return_code"], 4)
        self.assertEqual(receipt["output_validation"]["status"], "not-run")
        self.assertEqual(receipt["state"], "failed")

    def test_legacy_workspace_ownership_files_are_ignored_and_untouched(self):
        root = case("legacy-owner-files")
        build = test_workspace("runtime") / "build"
        build.mkdir(parents=True, exist_ok=True)
        lock_path = build / ".backend-execution.lock"
        state_path = build / ".backend-execution-state.json"
        lock_bytes = b"legacy lock bytes\x00"
        state_bytes = b"{malformed legacy state"
        lock_path.write_bytes(lock_bytes)
        state_path.write_bytes(state_bytes)
        with mock.patch("humanmotionlib.runtime.subprocess.run",
                        side_effect=PermissionError("global process table denied")):
            result = invocation([sys.executable, "-c", "import time; time.sleep(.15); print('ok')"],
                                run_root=root, operation="legacy-files-ignored", timeout_seconds=3,
                                slot_timeout_seconds=.01)
        self.assertEqual(result["state"], "succeeded")
        self.assertEqual(lock_path.read_bytes(), lock_bytes)
        self.assertEqual(state_path.read_bytes(), state_bytes)
        self.assertIn("ok", Path(result["stdout_log"]).read_text())

    def test_no_global_process_table_command_is_part_of_supervision(self):
        import inspect
        import humanmotionlib.runtime as runtime_module
        source = inspect.getsource(runtime_module)
        self.assertNotIn("flock", source)
        self.assertNotIn("ps -Ao", source)
        self.assertNotIn("ps -o", source)


if __name__ == "__main__":
    unittest.main()
