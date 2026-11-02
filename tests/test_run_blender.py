# SPDX-License-Identifier: Apache-2.0
"""Contract tests for the supervised normal Blender build wrapper."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

from humanmotionlib import run_blender
from humanmotionlib.prepared import canonical_bytes, content_hash
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

    def _managed_output_claim(self):
        owner = fresh_test_run_root("managed-owner", module="run_blender")
        output = owner / "clean-a"
        output.mkdir()
        payload = {"format": "character-render-request/v1",
                   "prepared_sha256": self.prepared["content_sha256"],
                   "character_ids": ["skeleton", "male", "female"]}
        identity = content_hash(payload)
        request = {**payload, "render_identity": identity}
        request_path = output / "character-render-request.json"
        request_bytes = canonical_bytes(request)
        with request_path.open("xb") as stream:
            stream.write(request_bytes)
        directory_stat = output.lstat()
        request_stat = request_path.lstat()
        claim = run_blender._ManagedOutputClaim(
            owner_run=str(owner), pass_root=str(output),
            directory_device=directory_stat.st_dev, directory_inode=directory_stat.st_ino,
            request_path=str(request_path), request_device=request_stat.st_dev,
            request_inode=request_stat.st_ino,
            request_sha256=hashlib.sha256(request_bytes).hexdigest(),
            prepared_sha256=self.prepared["content_sha256"], render_identity=identity,
            character_ids=("skeleton", "male", "female"))
        return owner, output, request_path, claim, identity

    def _run_managed(self, owner, output, request_path, claim, identity, *, probe_action=None):
        invocation_calls = []
        self._managed_invocation_calls = invocation_calls
        def probe(run_root, **_kwargs):
            process_dir = Path(run_root) / "processes"
            process_dir.mkdir(exist_ok=True)
            if probe_action is not None:
                probe_action(Path(run_root), request_path)
            return {"receipt": {"executable": "/resolved/blender"},
                    "version": "5.2.2 LTS", "build_hash": "d13f752e3b9c"}

        def invocation(_command, *, expected_outputs, **kwargs):
            invocation_calls.append(True)
            for item in expected_outputs:
                path = Path(item["path"] if isinstance(item, dict) else item)
                if path in (self.input_path, request_path):
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.name == "input.json":
                    path.write_bytes(self.input_path.read_bytes())
                elif path.name in ("evaluated.json", "geometry-reference.json",
                                   "surface-reference.json", "surface-evaluated.json"):
                    path.write_text(json.dumps({"prepared_sha256": self.prepared["content_sha256"],
                                                "samples": []}))
                elif path.name == "build-metadata.json":
                    path.write_text(json.dumps({"blender_version": "5.2.2 LTS",
                                                "blender_build": "d13f752e3b9c",
                                                "render_identity": identity}))
                elif path.name == "skeleton.blend":
                    path.write_bytes(b"scene")
                else:
                    path.write_text("{}")
            return {"state": "succeeded", "operation": "build", "invocation_id": "synthetic",
                    "stdout_log": str(self.case / "stdout.log"), "last_script_phase": "script_complete",
                    "phases": [
                        {"phase": "input_loaded", "prepared_sha256": self.prepared["content_sha256"]},
                        {"phase": "script_complete", "render_identity": identity,
                         "character_ids": ["skeleton", "male", "female"]}],
                    "output_validation": {"status": "pass", "files": []}}

        with mock.patch.object(run_blender, "read_prepared", return_value=self.prepared), \
             mock.patch.object(run_blender, "inspect_blender", side_effect=probe) as probe_mock, \
             mock.patch.object(run_blender, "invocation", side_effect=invocation), \
             mock.patch.object(run_blender, "update_receipt"):
            result = run_blender.run(
                self.input_path, output, workspace=self.workspace, owner_run=owner,
                characters=("skeleton", "male", "female"), render_identity=identity,
                character_request=request_path, managed_claim=claim)
        return result, probe_mock, invocation_calls

    def test_private_managed_claim_accepts_api_created_singleton_request(self):
        owner, output, request_path, claim, identity = self._managed_output_claim()
        result, probe, _calls = self._run_managed(owner, output, request_path, claim, identity)
        self.assertEqual(result["state"], "succeeded")
        self.assertEqual(probe.call_count, 1)

    def test_managed_claim_rejects_foreign_top_level_entry_before_probe(self):
        owner, output, request_path, claim, identity = self._managed_output_claim()
        (output / "foreign.txt").write_text("foreign")
        with self.assertRaisesRegex(ValueError, "foreign output entries"):
            self._run_managed(owner, output, request_path, claim, identity)

    def test_managed_claim_rejects_replaced_or_symlinked_request_before_probe(self):
        owner, output, request_path, claim, identity = self._managed_output_claim()
        request_path.write_text("{}\n")
        with self.assertRaises(ValueError):
            self._run_managed(owner, output, request_path, claim, identity)

        owner, output, request_path, claim, identity = self._managed_output_claim()
        outside = self.case / "outside-request.json"
        outside.write_bytes(request_path.read_bytes())
        request_path.unlink()
        request_path.symlink_to(outside)
        with self.assertRaises(ValueError):
            self._run_managed(owner, output, request_path, claim, identity)

    def test_managed_claim_rejects_replaced_pass_directory_before_probe(self):
        owner, output, request_path, claim, identity = self._managed_output_claim()
        original_request = request_path.read_bytes()
        displaced = owner / "clean-a-displaced"
        output.rename(displaced)
        output.mkdir()
        (output / "character-render-request.json").write_bytes(original_request)
        with self.assertRaisesRegex(ValueError, "directory identity changed"):
            self._run_managed(owner, output, output / "character-render-request.json", claim, identity)

    def test_managed_claim_rechecks_foreign_entries_after_probe(self):
        owner, output, request_path, claim, identity = self._managed_output_claim()
        def foreign_after_probe(run_root, _request_path):
            (run_root / "unexpected.txt").write_text("race")
        with self.assertRaisesRegex(ValueError, "foreign output entries"):
            self._run_managed(owner, output, request_path, claim, identity,
                              probe_action=foreign_after_probe)
        self.assertEqual(self._managed_invocation_calls, [])

    def test_managed_claim_rechecks_request_and_directory_after_probe(self):
        owner, output, request_path, claim, identity = self._managed_output_claim()
        def replace_request(_run_root, request):
            request.write_text("{}\n")
        with self.assertRaisesRegex(ValueError, "request identity changed"):
            self._run_managed(owner, output, request_path, claim, identity,
                              probe_action=replace_request)
        self.assertEqual(self._managed_invocation_calls, [])

        owner, output, request_path, claim, identity = self._managed_output_claim()
        request_bytes = request_path.read_bytes()
        def replace_directory(run_root, _request):
            displaced = run_root.parent / "clean-a-displaced"
            run_root.rename(displaced)
            run_root.mkdir()
            (run_root / "character-render-request.json").write_bytes(request_bytes)
        with self.assertRaisesRegex(ValueError, "directory identity changed"):
            self._run_managed(owner, output, request_path, claim, identity,
                              probe_action=replace_directory)
        self.assertEqual(self._managed_invocation_calls, [])

    def test_managed_claim_rejects_broken_process_symlink_after_probe(self):
        owner, output, request_path, claim, identity = self._managed_output_claim()
        def replace_processes_with_broken_link(run_root, _request):
            process_path = run_root / "processes"
            process_path.rmdir()
            process_path.symlink_to(run_root / "missing-processes")
        with self.assertRaisesRegex(ValueError, "supervisor evidence is not a contained directory"):
            self._run_managed(owner, output, request_path, claim, identity,
                              probe_action=replace_processes_with_broken_link)
        self.assertEqual(self._managed_invocation_calls, [])

    def test_build_forwards_supervised_argv_and_finite_overrides(self):
        result = self._run_with_mock()
        self.assertEqual(result["state"], "succeeded")
        self.assertEqual(self.command, [
            "/resolved/blender", "--background", "--factory-startup", "--python-exit-code", "1",
            "--python", str(Path(run_blender.__file__).with_name("build_skeleton.py").resolve()),
            "--", "--input", str(self.input_path), "--output", str(self.output),
            "--workspace", str(self.workspace), "--expected-prepared-sha256",
            self.prepared["content_sha256"],
        ])
        self.assertEqual(self.invocation_kwargs["timeout_seconds"], 17.5)
        self.assertEqual(self.invocation_kwargs["slot_timeout_seconds"], 4.25)
        self.assertEqual(self.invocation_kwargs["source_sha256"], self.prepared["content_sha256"])
        self.assertEqual(self.invocation_kwargs["operation"], "build")
        self.assertEqual(self.invocation_kwargs["workspace"], self.workspace)
        self.assertEqual(self.expected_outputs[0]["allow_existing_sha256"],
                         file_sha256(self.input_path))

    def test_matrix_content_binding_reaches_embedded_command(self):
        element = fresh_test_run_root("matrix-element", module="run_blender")
        output = element / "render"
        def capture_invocation(command, **kwargs):
            self.command = command
            self.invocation_kwargs = kwargs
            raise RuntimeError("captured invocation")
        with mock.patch.object(run_blender, "read_prepared", return_value=self.prepared), \
             mock.patch.object(run_blender, "inspect_blender", return_value={
                 "receipt": {"executable": "/resolved/blender"},
                 "version": "5.2.2 LTS", "build_hash": "d13f752e3b9c",
             }), \
             mock.patch.object(run_blender, "invocation", side_effect=capture_invocation), \
             mock.patch.object(run_blender, "update_receipt"):
            with self.assertRaisesRegex(RuntimeError, "captured invocation"):
                run_blender.run(
                    self.input_path, output, render_dir=output / "frames",
                    render_only=True, workspace=self.workspace,
                    matrix_element_root=element)
        flag_index = self.command.index("--matrix-element-root")
        self.assertEqual(self.command[flag_index + 1], str(element))
        self.assertIsNone(self.invocation_kwargs.get("owner_run"))

    def test_matrix_content_binding_rejects_nonallowlisted_and_symlink_destinations(self):
        element = fresh_test_run_root("matrix-element", module="run_blender")
        outside = self.case / "outside"
        outside.mkdir()
        with mock.patch.object(run_blender, "inspect_blender") as probe, \
             mock.patch.object(run_blender, "invocation") as invocation:
            with self.assertRaisesRegex(ValueError, "not allowed"):
                run_blender.run(self.input_path, element / "foreign", workspace=self.workspace,
                                matrix_element_root=element)
            (element / "render").symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "symlink"):
                run_blender.run(self.input_path, element / "render", workspace=self.workspace,
                                matrix_element_root=element)
        probe.assert_not_called()
        invocation.assert_not_called()

    def test_embedded_build_preflight_accepts_only_the_explicit_managed_pass(self):
        owner = fresh_test_run_root("embedded-owner", module="run_blender")
        pass_root = owner / "clean-a"
        pass_root.mkdir()
        wrong_owner = fresh_test_run_root("wrong-owner", module="run_blender")
        matrix_element = fresh_test_run_root("matrix-element", module="run_blender")
        matrix_output = matrix_element / "render"
        matrix_foreign = matrix_element / "foreign"
        matrix_overlap_input = matrix_output / "nested" / "input.json"
        matrix_symlink = matrix_element / "render"
        matrix_outside = self.case / "matrix-outside"
        matrix_outside.mkdir()
        matrix_element_link = self.workspace / "build" / "matrix_revision_dev_try_alias"
        matrix_element_link.symlink_to(matrix_element)
        script = self.case / "embedded_import_probe.py"
        script.write_text('''
import importlib
import json
from pathlib import Path
import sys
import types

import humanmotionlib

source_package = Path(sys.argv[1]).resolve()
prepared_record = json.loads(sys.argv[2])
(input_path, output_path, workspace_path, owner_path, wrong_owner_path,
 matrix_element_path, matrix_output_path, matrix_foreign_path,
 matrix_overlap_input_path, matrix_outside_path, matrix_element_link_path) = sys.argv[3:14]
loaded_package = Path(humanmotionlib.__file__).resolve().parent
if loaded_package == source_package:
    raise AssertionError("embedded test loaded contributor source package")

fake_bpy = types.ModuleType("bpy")
fake_mathutils = types.ModuleType("mathutils")
fake_mathutils.Matrix = object
fake_mathutils.Vector = object
sys.modules["bpy"] = fake_bpy
sys.modules["mathutils"] = fake_mathutils
build_skeleton = importlib.import_module("humanmotionlib.build_skeleton")

integrity_calls = []
def verify_integrity():
    integrity_calls.append(True)
    return {"version": humanmotionlib.__version__, "resources": {}}

build_skeleton.verify_runtime_integrity = verify_integrity
build_skeleton.read_prepared_backend = lambda *_args: prepared_record
build_skeleton.SkeletonBackend = lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("backend sentinel"))

def run(args):
    sys.argv = ["blender", "--", *args]
    return build_skeleton.main()

common = ["--input", input_path, "--output", output_path, "--workspace", workspace_path,
          "--expected-prepared-sha256", "prepared-content-hash", "--render-only",
          "--render-dir", str(Path(output_path) / "frames")]
try:
    run([*common, "--owner-run", owner_path])
except RuntimeError as error:
    if str(error) != "backend sentinel":
        raise
else:
    raise AssertionError("backend sentinel was not reached")
if len(integrity_calls) != 1:
    raise AssertionError("valid managed pass did not verify the installed package exactly once")

try:
    run([*common, "--owner-run", wrong_owner_path])
except ValueError as error:
    if "managed render pass" not in str(error):
        raise
else:
    raise AssertionError("wrong owner was accepted")
if len(integrity_calls) != 1:
    raise AssertionError("wrong owner reached package verification")

matrix_common = ["--input", input_path, "--output", matrix_output_path,
                 "--workspace", workspace_path,
                 "--expected-prepared-sha256", "prepared-content-hash", "--render-only",
                 "--render-dir", str(Path(matrix_output_path) / "frames"),
                 "--matrix-element-root", matrix_element_path]
try:
    run(matrix_common)
except RuntimeError as error:
    if str(error) != "backend sentinel":
        raise
else:
    raise AssertionError("valid matrix binding did not reach backend sentinel")
if len(integrity_calls) != 2:
    raise AssertionError("valid matrix binding did not verify installed package exactly once")

def rejected(args, message):
    try:
        run(args)
    except ValueError as error:
        if message not in str(error):
            raise
    else:
        raise AssertionError("invalid matrix binding was accepted: " + message)

foreign_args = [*matrix_common]
foreign_args[foreign_args.index("--output") + 1] = matrix_foreign_path
foreign_args[foreign_args.index("--render-dir") + 1] = str(Path(matrix_foreign_path) / "frames")
rejected(foreign_args, "not allowed")
traversal = str(Path(matrix_element_path) / "render" / ".." / "foreign")
traversal_args = [*matrix_common]
traversal_args[traversal_args.index("--output") + 1] = traversal
traversal_args[traversal_args.index("--render-dir") + 1] = str(Path(traversal) / "frames")
rejected(traversal_args, "traversal")
overlap_args = [*matrix_common]
overlap_args[overlap_args.index("--input") + 1] = matrix_overlap_input_path
rejected(overlap_args, "disjoint")
Path(matrix_output_path).symlink_to(matrix_outside_path)
symlink_args = [*matrix_common]
rejected(symlink_args, "symlink")
rejected([*matrix_common, "--owner-run", owner_path], "cannot be combined")
alias_args = [*matrix_common]
alias_args[alias_args.index("--matrix-element-root") + 1] = matrix_element_link_path
rejected(alias_args, "canonical")
if len(integrity_calls) != 2:
    raise AssertionError("invalid matrix binding reached package verification")
print("embedded package:", loaded_package)
print("managed pass and matrix content reached backend sentinel; invalid matrix bindings failed before integrity check")
''', encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(script), str(Path(__file__).resolve().parents[1] / "src/humanmotionlib"),
             json.dumps(self.prepared), str(self.input_path), str(pass_root), str(self.workspace),
             str(owner), str(wrong_owner), str(matrix_element), str(matrix_output),
             str(matrix_foreign), str(matrix_overlap_input), str(matrix_outside),
             str(matrix_element_link)],
            capture_output=True, text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("managed pass and matrix content reached backend sentinel", completed.stdout)
        self.assertNotIn(str(Path(__file__).resolve().parents[1] / "src/humanmotionlib"),
                         completed.stdout)

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
