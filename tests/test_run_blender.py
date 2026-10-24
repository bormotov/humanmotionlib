# SPDX-License-Identifier: Apache-2.0
"""Contract tests for the supervised normal Blender build wrapper."""

import json
import importlib
from pathlib import Path
import sys
import types
import unittest
from unittest import mock

from humanmotionlib import __version__, run_blender
from humanmotionlib.runtime import InvocationError, file_sha256, project_root
from tests.run_roots import fresh_test_run_root, test_run_root, test_workspace


def _prepared():
    return {
        "content_sha256": "prepared-content-hash",
        "samples": [],
        "sources": {"review-scene": {"cameras": []}},
    }


class RunBlenderContractTests(unittest.TestCase):
    def setUp(self):
        test_run_root("run_blender")
        self.workspace = test_workspace("run_blender")
        self.case = fresh_test_run_root("run-blender", module="run_blender")
        self.output = self.case
        self.input_path = self.output / "input.json"
        self.input_path.write_text("prepared input\n")
        self.prepared = _prepared()

    def _successful_invocation(self, command, *, expected_outputs, **kwargs):
        self.command = command
        self.invocation_kwargs = kwargs
        self.expected_outputs = expected_outputs
        for item in expected_outputs:
            path = Path(item["path"] if isinstance(item, dict) else item)
            if path == self.input_path:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.name == "build-metadata.json":
                path.write_text(json.dumps({"blender_version": "5.2.2 LTS",
                                            "blender_build": "d13f752e3b9c"}))
            elif path.name == "evaluated.json":
                path.write_text(json.dumps({"prepared_sha256": self.prepared["content_sha256"],
                                            "samples": []}))
            elif path.name == "geometry-reference.json":
                path.write_text(json.dumps({"prepared_sha256": self.prepared["content_sha256"]}))
            elif path.name == "skeleton.blend":
                path.write_bytes(b"synthetic blend output")
            else:
                path.write_text("{}\n")
        return {
            "state": "succeeded", "operation": "build", "invocation_id": "synthetic",
            "stdout_log": str(self.case / "stdout.log"), "last_script_phase": "script_complete",
            "phases": [{"phase": "input_loaded", "prepared_sha256": self.prepared["content_sha256"]}],
            "output_validation": {"files": []},
        }

    def _run_with_mock(self, invocation_side_effect=None):
        with mock.patch.object(run_blender, "read_prepared", return_value=self.prepared), \
             mock.patch.object(run_blender, "inspect_blender", return_value={
                 "receipt": {"executable": "/resolved/blender"},
                 "version": "5.2.2 LTS", "build_hash": "d13f752e3b9c",
             }), \
             mock.patch.object(run_blender, "invocation",
                               side_effect=invocation_side_effect or self._successful_invocation), \
             mock.patch.object(run_blender, "update_receipt"):
            result = run_blender.run(self.input_path, self.output, workspace=self.workspace,
                                     timeout_seconds=17.5, slot_timeout_seconds=4.25)
        return result

    def test_build_forwards_supervised_argv_and_finite_overrides(self):
        result = self._run_with_mock()
        self.assertEqual(result["state"], "succeeded")
        self.assertEqual(self.command, [
            "/resolved/blender", "--background", "--factory-startup", "--python-exit-code", "1",
            "--python", str(Path(run_blender.__file__).with_name("build_skeleton.py").resolve()),
            "--", "--input", str(self.input_path), "--output", str(self.output),
            "--workspace", str(self.workspace),
        ])
        self.assertEqual(self.invocation_kwargs["timeout_seconds"], 17.5)
        self.assertEqual(self.invocation_kwargs["slot_timeout_seconds"], 4.25)
        self.assertEqual(self.invocation_kwargs["source_sha256"], self.prepared["content_sha256"])
        self.assertEqual(self.invocation_kwargs["operation"], "build")
        self.assertEqual(self.invocation_kwargs["workspace"], self.workspace)
        self.assertEqual(self.expected_outputs[0]["allow_existing_sha256"],
                         file_sha256(self.input_path))

    def test_embedded_build_preflight_accepts_only_the_explicit_managed_pass(self):
        fake_mathutils = types.ModuleType("mathutils")
        fake_mathutils.Matrix = object
        fake_mathutils.Vector = object
        saved_bytecode = sys.dont_write_bytecode
        with mock.patch.dict(sys.modules, {"bpy": types.ModuleType("bpy"),
                                           "mathutils": fake_mathutils}):
            build_skeleton = importlib.import_module("humanmotionlib.build_skeleton")
        sys.dont_write_bytecode = saved_bytecode
        owner = fresh_test_run_root("embedded-owner", module="run_blender")
        pass_root = owner / "clean-a"
        pass_root.mkdir()
        args = ["blender", "--", "--input", str(self.input_path), "--output", str(pass_root),
                "--workspace", str(self.workspace), "--owner-run", str(owner), "--render-only",
                "--render-dir", str(pass_root / "frames")]
        with mock.patch("sys.argv", args), \
             mock.patch.object(build_skeleton, "verify_runtime_integrity",
                               return_value={"version": __version__, "resources": {}}), \
             mock.patch.object(build_skeleton, "read_prepared", return_value=self.prepared), \
             mock.patch.object(build_skeleton, "SkeletonBackend", side_effect=RuntimeError("backend sentinel")) as backend:
            with self.assertRaisesRegex(RuntimeError, "backend sentinel"):
                build_skeleton.main()
        backend.assert_called_once()

        wrong_owner = fresh_test_run_root("wrong-owner", module="run_blender")
        with mock.patch("sys.argv", args[:-5] + ["--owner-run", str(wrong_owner), *args[-3:]]), \
             mock.patch.object(build_skeleton, "verify_runtime_integrity") as integrity:
            with self.assertRaisesRegex(ValueError, "managed render pass"):
                build_skeleton.main()
        integrity.assert_not_called()

    def test_stale_output_is_rejected_before_probe_or_spawn(self):
        (self.output / "skeleton.blend").write_bytes(b"stale")
        with mock.patch.object(run_blender, "read_prepared", return_value=self.prepared), \
             mock.patch.object(run_blender, "inspect_blender") as probe, \
             mock.patch.object(run_blender, "invocation") as launch:
            with self.assertRaisesRegex(ValueError, "stale output preflight"):
                run_blender.run(self.input_path, self.output, workspace=self.workspace)
        probe.assert_not_called()
        launch.assert_not_called()

    def test_zero_exit_without_completion_marker_fails_closed(self):
        def no_completion(command, **kwargs):
            self._successful_invocation(command, **kwargs)["last_script_phase"] = "outputs_written"
            receipt = {
                "state": "succeeded", "stdout_log": str(self.case / "stdout.log"),
                "last_script_phase": "outputs_written", "phases": [],
                "output_validation": {"files": []},
            }
            return receipt

        with self.assertRaisesRegex(InvocationError, "did not emit script_complete"):
            self._run_with_mock(no_completion)

    def test_zero_exit_with_missing_or_malformed_outputs_fails_closed(self):
        for malformed in (False, True):
            with self.subTest(malformed=malformed):
                for path in self.output.iterdir():
                    if path.name != "input.json":
                        path.unlink()

                def incomplete(command, *, expected_outputs, **kwargs):
                    receipt = self._successful_invocation(command, expected_outputs=expected_outputs, **kwargs)
                    metadata = self.output / "build-metadata.json"
                    if malformed:
                        metadata.write_text("{")
                    else:
                        metadata.unlink()
                    return receipt

                with self.assertRaises(InvocationError):
                    self._run_with_mock(incomplete)

    def test_nonzero_child_fails_closed_even_if_it_wrote_complete_outputs(self):
        def child_failure(command, **kwargs):
            self._successful_invocation(command, **kwargs)
            raise InvocationError("child exited nonzero", str(self.case / "outcome.json"))

        with self.assertRaisesRegex(InvocationError, "child exited nonzero"):
            self._run_with_mock(child_failure)


if __name__ == "__main__":
    unittest.main()
