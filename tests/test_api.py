# SPDX-License-Identifier: Apache-2.0
from fractions import Fraction
import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import shutil
from unittest.mock import patch
from PIL import Image

from humanmotionlib import api
from humanmotionlib.package_resources import (manifest_sha256, read_bytes, read_text,
                                              verify_runtime_integrity)
from humanmotionlib.prepare_skeleton import prepare as internal_prepare
from humanmotionlib.render_contract import expected_views, validate_manifest
from humanmotionlib.runtime import InvocationError, file_sha256


class PublicApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name).resolve()
        (self.workspace / "build").mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def output(self, identity):
        return f"build/public-api-test_r1_test_try-1_{identity}/input.json"

    def test_public_surface_and_portable_records(self):
        self.assertEqual(tuple(inspect.signature(api.prepare).parameters)[:2], ("workspace", "output"))
        self.assertEqual(tuple(inspect.signature(api.render).parameters)[:3], ("prepared", "workspace", "output"))
        with patch.object(api.run_blender, "run", side_effect=AssertionError("prepare probed backend")):
            result = api.prepare(workspace=self.workspace, output=self.output("prepare"),
                                 stature=1.5, fixtures=("neutral", "arm-raise"), bpms=(90,))
        self.assertEqual(result.stature_m, 1.5)
        self.assertEqual(json.loads(result.prepared_path.read_text())["content_sha256"],
                         result.prepared_sha256)
        timeline = next(item for item in result.timelines
                        if item.fixture_id == "arm-raise" and item.mode == "animation")
        self.assertEqual(len(timeline.entries), 17)
        beat_two = next(item for item in timeline.entries if item.beat == 2)
        self.assertEqual(beat_two.seconds, Fraction(4, 3))
        static = next(item for item in result.timelines
                      if item.fixture_id == "arm-raise" and item.mode == "static")
        self.assertEqual(len(static.entries), 5)
        self.assertEqual(static.entries[2].sample_id, beat_two.sample_id)
        self.assertTrue(all(any(p.sample_id == entry.sample_id for p in result.poses)
                            for entry in timeline.entries))
        encoded = json.dumps(result.to_dict(), sort_keys=True)
        self.assertIn('"numerator": 4', encoded)
        self.assertTrue({"hands-on-anatomy-2024", "wang-2024-segment-lengths"}
                        <= set(result.provenance.material_ids))
        self.assertGreater(len(result.provenance.material_ids), 2)
        self.assertIn("CC-BY-4.0", result.provenance.licenses["LICENSE-DATA"])
        self.assertEqual(result.provenance.register_text, read_text("docs/used-materials.md"))
        profile = next(source for source in result.provenance.sources
                       if source.logical_path.endswith("rig/profiles/adult-reference-v1.yaml"))
        self.assertEqual(profile.sha256, hashlib.sha256(read_bytes(profile.logical_path)).hexdigest())
        self.assertEqual(profile.provenance["license"], "CC-BY-4.0")
        self.assertIn("/", profile.nested_provenance)
        schema = next(source for source in result.provenance.sources
                      if source.logical_path == "schema/profile.schema.json")
        self.assertIsNone(schema.provenance)
        before = result.prepared_path.read_bytes()
        result.poses[0].actions["detached-test"] = 99
        self.assertEqual(result.prepared_path.read_bytes(), before)
        projection = result.to_dict()
        projection["provenance"]["sources"].clear()
        self.assertTrue(result.provenance.sources)

    def test_invalid_selections_do_not_allocate_workspace_state(self):
        workspace = self.workspace / "not-created"
        for kwargs in (
            {"bpms": ()}, {"bpms": (60, 60)}, {"bpms": (True,)},
            {"bpms": (float("nan"),)}, {"fixtures": ()},
            {"fixtures": ("neutral", "neutral")}, {"stature": True},
            {"stature": float("inf")}, {"bpms": (0,)}, {"stature": 0},
            {"fixtures": ("not-packaged",)},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(api.GenerationError) as caught:
                    api.prepare(workspace=workspace, output=self.output("invalid"), **kwargs)
                self.assertEqual(caught.exception.code, "invalid-request")
                self.assertFalse(workspace.exists())
        with self.assertRaises(api.GenerationError) as caught:
            api.prepare(workspace=workspace, output=self.output("invalid-profile"), profile="not-packaged")
        self.assertEqual(caught.exception.code, "source-validation")
        self.assertFalse(workspace.exists())

    def test_exact_timeline_joins_at_every_supported_bpm(self):
        result = api.prepare(workspace=self.workspace,
                             output=self.output("timing"),
                             fixtures=("arm-raise",), bpms=(60, 90, 120, 180))
        expected = {60: (21, Fraction(2)), 90: (17, Fraction(4, 3)),
                    120: (13, Fraction(1)), 180: (13, Fraction(2, 3))}
        pose_ids = {pose.sample_id for pose in result.poses}
        for bpm, (count, seconds) in expected.items():
            timeline = next(item for item in result.timelines
                            if item.fixture_id == "arm-raise" and item.bpm == bpm
                            and item.mode == "animation")
            self.assertEqual(len(timeline.entries), count)
            entry = next(item for item in timeline.entries if item.beat == 2)
            self.assertEqual(entry.seconds, seconds)
            self.assertIn(entry.sample_id, pose_ids)
            self.assertEqual(timeline.entries[-1].beat, 4)

    def test_import_does_not_consume_arguments_change_cwd_or_spawn(self):
        package_root = Path(api.__file__).resolve().parents[1]
        script = """
import os, pathlib, subprocess, sys
before=(list(sys.argv),os.getcwd())
def forbidden(*args, **kwargs): raise AssertionError('import performed an effect')
pathlib.Path.write_bytes=forbidden
pathlib.Path.write_text=forbidden
subprocess.Popen=forbidden
subprocess.run=forbidden
os.chdir=forbidden
import humanmotionlib.api as api
after=(list(sys.argv),os.getcwd())
assert before==after
assert callable(api.prepare) and callable(api.render)
assert 'bpy' not in sys.modules
"""
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env.pop("PYTHONPATH", None)
        proc = subprocess.run([sys.executable, "-c", script, "--unrelated", "app-arg"],
                              cwd=self.workspace, env=env, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(package_root.is_dir())

    def test_default_coverage_matches_internal_evaluator(self):
        result = api.prepare(workspace=self.workspace, output=self.output("defaults"))
        internal = internal_prepare("adult-reference-v1")
        self.assertEqual([pose.sample_id for pose in result.poses],
                         [sample["id"] for sample in internal["samples"]])
        for public_pose, sample in zip(result.poses, internal["samples"]):
            self.assertEqual(public_pose.actions, sample["expected_actions"])
            self.assertEqual(public_pose.fk_deltas, sample["fk_deltas"])
            self.assertEqual(public_pose.world_root, sample["world_root"])

    def test_tampered_persisted_preparation_is_catchable(self):
        prepared = api.prepare(workspace=self.workspace, output=self.output("tamper"),
                               fixtures=("neutral",), bpms=(60,))
        value = json.loads(prepared.prepared_path.read_text())
        value["sources"]["profile"]["stature_m"] += 0.01
        prepared.prepared_path.write_text(json.dumps(value))
        with self.assertRaises(api.GenerationError) as caught:
            api.render(prepared, workspace=self.workspace,
                       output="build/public-api-test_r1_test_try-1_render")
        self.assertEqual(caught.exception.code, "input-integrity")
        self.assertFalse((self.workspace / "build/public-api-test_r1_test_try-1_render").exists())

    def test_invalid_render_options_and_destinations_have_no_run_state(self):
        prepared = api.prepare(workspace=self.workspace, output=self.output("invalid-render"),
                               fixtures=("neutral",), bpms=(60,))
        output = "build/public-api-test_r1_test_try-1_invalid-render-target"
        with self.assertRaises(api.GenerationError) as caught:
            api.render(prepared, workspace=self.workspace, output=output,
                       images=False, render_dir="build/frames")
        self.assertEqual(caught.exception.code, "invalid-request")
        self.assertFalse((self.workspace / output).exists())
        with self.assertRaises(api.GenerationError) as caught:
            api.render(prepared, workspace="relative-workspace", output=output)
        self.assertEqual(caught.exception.code, "invalid-request")
        self.assertFalse((self.workspace / output).exists())

    def test_render_rejects_timeout_above_backend_limit_before_run_creation(self):
        prepared = api.prepare(workspace=self.workspace, output=self.output("timeout-limit"),
                               fixtures=("neutral",), bpms=(60,))
        output = "build/public-api-test_r1_test_try-1_timeout-too-large"
        with self.assertRaises(api.GenerationError) as caught:
            api.render(prepared, workspace=self.workspace, output=output, timeout_seconds=86401)
        self.assertEqual(caught.exception.code, "invalid-request")
        self.assertFalse((self.workspace / output).exists())

    def test_custom_render_dir_uses_shared_complete_receipt_contract(self):
        prepared = api.prepare(workspace=self.workspace, output=self.output("custom-frames"),
                               fixtures=("arm-raise",), bpms=(60,))

        def mock_render(prepared_path, output, **kwargs):
            output = Path(output)
            frames = Path(kwargs["render_dir"])
            output.mkdir(parents=True)
            frames.mkdir(parents=True)
            prepared_json = json.loads(Path(prepared_path).read_text())
            (output / "input.json").write_bytes(Path(prepared_path).read_bytes())
            metadata = {"blender_version": "5.2.2 LTS", "blender_build": "d13f752e3b9c",
                        "platform": "Darwin-arm64"}
            (output / "build-metadata.json").write_text(json.dumps(metadata))
            (output / "skeleton.blend").write_bytes(b"scene")
            (output / "evaluated.json").write_text(json.dumps({"prepared_sha256": prepared_json["content_sha256"]}))
            (output / "geometry-reference.json").write_text(json.dumps({"prepared_sha256": prepared_json["content_sha256"]}))
            samples = []
            for sample in prepared_json["samples"]:
                images = {}
                for view in expected_views(prepared_json, sample):
                    relative = Path(sample["fixture"]) / view / f"{str(sample['frame_id']).zfill(5)}.png"
                    path = frames / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    Image.new("RGBA", (2, 2), (10, 20, 30, 255)).save(path)
                    images[view] = relative.as_posix()
                samples.append({"id": sample["id"], "images": images})
            manifest = {"prepared_sha256": prepared_json["content_sha256"], "samples": samples}
            (output / "render-manifest.json").write_text(json.dumps(manifest))
            required = validate_manifest(manifest, prepared_json, frames, output=output)
            required.extend((Path("evaluated.json"), Path("geometry-reference.json")))
            evidence = output / "processes" / "mock"
            evidence.mkdir(parents=True)
            stdout = evidence / "stdout.log"
            stdout.write_text("")
            package = verify_runtime_integrity()
            receipt_data = {
                "operation": "render-pass", "state": "succeeded", "outcome": "exit",
                "return_code": 0, "source_sha256": prepared_json["content_sha256"],
                "last_script_phase": "script_complete",
                "phases": [{"phase": name, "prepared_sha256": prepared_json["content_sha256"]}
                           for name in ("input_loaded", "script_complete")],
                "package_version": package["version"],
                "runtime_manifest_sha256": manifest_sha256(),
                "resource_hashes": package["resources"],
                "backend_contract_sha256": package["backend_contract"],
                "implementation_hashes": package["implementation"],
                "output_validation": {"status": "pass", "files": [
                    {"path": str((output / relative).resolve()),
                     "size_bytes": (output / relative).stat().st_size,
                     "sha256": file_sha256(output / relative)} for relative in required]},
            }
            (evidence / "outcome.json").write_text(json.dumps(receipt_data))
            return {"stdout_log": str(stdout), "backend_identity": {
                "version": metadata["blender_version"], "build_hash": metadata["blender_build"]}}

        with patch.object(api.run_blender, "run", side_effect=mock_render):
            result = api.render(prepared, workspace=self.workspace,
                                output="build/public-api-test_r1_test_try-1_custom-render",
                                render_dir="build/public-api-test_r1_test_try-1_custom-render/custom-frames")
        self.assertEqual(len(result.images), len(prepared.poses) * 2)
        self.assertTrue(all(image.path.is_relative_to(result.output_root / "custom-frames")
                            for image in result.images))

    def _mock_build(self, prepared_path, output, **kwargs):
        output.mkdir(parents=True)
        shutil.copyfile(prepared_path, output / "input.json")
        (output / "build-metadata.json").write_text(json.dumps({
            "blender_version": "5.2.2 LTS", "blender_build": "d13f752e3b9c",
            "platform": "Darwin-arm64",
        }))
        (output / "skeleton.blend").write_bytes(b"fixture")
        if not kwargs["render_only"]:
            (output / "evaluated.json").write_bytes(b"{}")
            (output / "geometry-reference.json").write_bytes(b"{}")
        process = output / "processes" / "mock"
        process.mkdir(parents=True)
        stdout = process / "stdout.log"
        stdout.write_text("")
        (process / "outcome.json").write_text(json.dumps({"state": "succeeded"}))
        return {"stdout_log": str(stdout), "backend_identity": {"version": "5.2.2 LTS",
                                                                  "build_hash": "d13f752e3b9c"}}

    def test_no_image_build_modes_and_prepared_path_input(self):
        prepared = api.prepare(workspace=self.workspace, output=self.output("modes"),
                               fixtures=("neutral",), bpms=(60,))
        with patch.object(api.run_blender, "run", side_effect=self._mock_build) as runner:
            build = api.render(prepared.prepared_path, workspace=self.workspace,
                               output="build/public-api-test_r1_test_try-1_build", images=False)
            render_only = api.render(prepared, workspace=self.workspace,
                                     output="build/public-api-test_r1_test_try-1_render-only",
                                     images=False, render_only=True)
        self.assertEqual(build.images, ())
        self.assertIn("evaluated", build.artifacts)
        self.assertNotIn("render_manifest", build.artifacts)
        self.assertNotIn("evaluated", render_only.artifacts)
        self.assertEqual(runner.call_args_list[0].kwargs["render_dir"], None)
        self.assertTrue(runner.call_args_list[1].kwargs["render_only"])
        self.assertEqual((build.numerical_acceptance, build.visual_acceptance), ("not-run", "pending"))

    def test_malformed_manifest_is_output_integrity_failure(self):
        for index, manifest_text in enumerate((
                json.dumps({"prepared_sha256": "stale", "samples": []}),
                json.dumps([]), "{")):
            with self.subTest(manifest=manifest_text[:12]):
                prepared = api.prepare(workspace=self.workspace,
                                       output=self.output(f"manifest-{index}"),
                                       fixtures=("neutral",), bpms=(60,))

                def malformed(prepared_path, output, **kwargs):
                    output.mkdir(parents=True)
                    (output / "render-manifest.json").write_text(manifest_text)
                    process = output / "processes" / "mock"
                    process.mkdir(parents=True)
                    stdout = process / "stdout.log"
                    stdout.write_text("")
                    (process / "outcome.json").write_text("{}")
                    return {"stdout_log": str(stdout), "backend_identity": {}}

                with patch.object(api.run_blender, "run", side_effect=malformed):
                    with self.assertRaises(api.GenerationError) as caught:
                        api.render(prepared, workspace=self.workspace,
                                   output=f"build/public-api-test_r1_test_try-1_bad-manifest-{index}")
                self.assertEqual(caught.exception.code, "output-integrity")

    def test_backend_failures_use_structured_outcomes_and_keep_receipt(self):
        cases = (("timeout", "backend-timeout"), ("spawn_error", "backend-spawn"),
                 ("identity_error", "backend-mismatch"), ("contention", "backend-contention"),
                 ("output-contract-failed", "output-integrity"))
        for outcome, expected in cases:
            with self.subTest(outcome=outcome):
                receipt = self.workspace / outcome / "processes" / "mock" / "outcome.json"
                receipt.parent.mkdir(parents=True)
                receipt.write_text(json.dumps({"operation": "build", "outcome": outcome,
                                               "cleanup": {"status": "confirmed"},
                                               "output_validation": {"status": "fail" if "integrity" in expected else "not-run"}}))
                error = api._translate_error(InvocationError("backend operation failed", str(receipt)),
                                             "render", self.workspace)
                self.assertEqual(error.code, expected)
                self.assertEqual(error.receipt_path, receipt)
                self.assertEqual(error.to_dict()["details"]["supervisor_outcome"]["outcome"], outcome)
        unavailable = self.workspace / "unavailable.json"
        unavailable.write_text(json.dumps({"operation": "version-probe", "outcome": "spawn_error",
                                           "spawn_error": {"type": "FileNotFoundError", "errno": 2}}))
        error = api._translate_error(InvocationError("backend could not start", str(unavailable)),
                                     "render", self.workspace)
        self.assertEqual(error.code, "backend-unavailable")
        pending = self.workspace / "pending" / "processes" / "mock" / "outcome.json"
        pending.parent.mkdir(parents=True)
        pending.write_text(json.dumps({"operation": "build", "outcome": "orphaned-descendant",
                                       "cleanup": {"status": "cleanup_pending"}}))
        error = api._translate_error(InvocationError("cleanup pending", str(pending)),
                                     "render", self.workspace)
        self.assertEqual(error.code, "cleanup-pending")

    def test_keyboard_interrupt_is_re_raised_from_supervisor(self):
        prepared = api.prepare(workspace=self.workspace, output=self.output("cancel"),
                               fixtures=("neutral",), bpms=(60,))
        interrupted = KeyboardInterrupt("cancelled")
        with patch.object(api.run_blender, "run", side_effect=InvocationError("cancelled", "") ) as runner:
            runner.side_effect.__cause__ = interrupted
            with self.assertRaises(KeyboardInterrupt) as caught:
                api.render(prepared, workspace=self.workspace,
                           output="build/public-api-test_r1_test_try-1_cancelled")
        self.assertIs(caught.exception, interrupted)


if __name__ == "__main__":
    unittest.main()
