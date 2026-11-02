# SPDX-License-Identifier: Apache-2.0
"""Hostile integrity tests for sealed character requests and batch outputs."""

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

from PIL import Image

from humanmotionlib import api
from humanmotionlib.prepared import content_hash
from humanmotionlib.render_contract import (
    _receipt_files_unchanged,
    validate_character_manifest,
)


CHARACTERS = ("skeleton", "male", "female")


class _BackendReached(Exception):
    """Sentinel proving a request passed all pre-backend integrity checks."""


def _reseal(request):
    payload = {key: value for key, value in request.items() if key != "render_identity"}
    request["render_identity"] = content_hash(payload)
    return request["render_identity"]


def _load_build_script():
    """Import the installed parser with inert bpy stubs; never launch Blender."""
    package = importlib.util.find_spec("humanmotionlib")
    package_root = Path(next(iter(package.submodule_search_locations)))
    spec = importlib.util.spec_from_file_location(
        "_hml_integrity_build_skeleton", package_root / "build_skeleton.py")
    module = importlib.util.module_from_spec(spec)
    bpy = types.ModuleType("bpy")
    mathutils = types.ModuleType("mathutils")
    mathutils.Matrix = object
    mathutils.Vector = object
    with mock.patch.dict(sys.modules, {"bpy": bpy, "mathutils": mathutils}):
        spec.loader.exec_module(module)
    return module


class CharacterIntegrityFaultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build_script = _load_build_script()

    def _request_case(self, mutate=None, reseal=False, external_identity=None, stature=1.70):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        workspace = Path(temporary.name).resolve()
        (workspace / "build").mkdir()
        prepared = api.prepare(
            workspace=workspace,
            output="build/character-request-test_r1_test_try-1_input/input.json",
            fixtures=("neutral",), bpms=(60,), stature=stature,
        )
        api_output_relative = "build/character-request-test_r1_test_try-1_api-request"
        api_output = workspace / api_output_relative

        def capture_request(prepared_path, output_path, **kwargs):
            request_path = Path(kwargs["character_request"])
            request = json.loads(request_path.read_text(encoding="utf-8"))
            self.assertEqual(kwargs["render_identity"], request["render_identity"])
            Path(output_path, "build-metadata.json").write_text(json.dumps({
                "blender_version": "5.2.2 LTS", "blender_build": "test", "platform": "test",
                "render_identity": request["render_identity"],
            }), encoding="utf-8")
            # API render-only mode does not consume an output receipt.
            return {"stdout_log": str(Path(output_path) / "mock" / "stdout.log"),
                    "backend_identity": {"version": "5.2.2 LTS", "build_hash": "test"}}

        with mock.patch.object(api.run_blender, "run", side_effect=capture_request):
            api.render(prepared, workspace=workspace, output=api_output_relative,
                       characters=CHARACTERS, images=False, render_only=True)
        source_request = api_output / "character-render-request.json"
        request = json.loads(source_request.read_text(encoding="utf-8"))
        output = workspace / "build/character-request-test_r1_test_try-1_parser-input"
        output.mkdir()
        request_path = output / "character-render-request.json"
        original_identity = request["render_identity"]
        if mutate is not None:
            mutate(request)
        identity = _reseal(request) if reseal else request["render_identity"]
        request_path.write_text(json.dumps(request, sort_keys=True, separators=(",", ":")),
                                encoding="utf-8")
        return workspace, prepared, output, request_path, identity if external_identity is None else external_identity, original_identity

    def _invoke_request_parser(self, workspace, prepared, output, request_path, expected_identity,
                               character_ids=CHARACTERS):
        argv = ["build_skeleton.py", "--", "--input", str(prepared.prepared_path),
                "--output", str(output), "--workspace", str(workspace),
                "--expected-prepared-sha256", prepared.prepared_sha256,
                "--characters", *character_ids,
                "--expected-render-identity", expected_identity,
                "--character-request", str(request_path)]
        with mock.patch.object(sys, "argv", argv), \
                mock.patch.object(self.build_script, "SkeletonBackend", side_effect=_BackendReached):
            self.build_script.main()

    def test_current_sealed_request_passes_parser_at_all_supported_statutes(self):
        for stature in (1.50, 1.70, 1.90):
            with self.subTest(stature=stature):
                workspace, prepared, output, request_path, identity, _ = self._request_case(
                    stature=stature)
                with self.assertRaises(_BackendReached):
                    self._invoke_request_parser(workspace, prepared, output, request_path, identity)

    def test_replaced_request_fails_against_original_external_identity(self):
        def replace(request):
            request["surface_identities"]["male"] = "0" * 64

        workspace, prepared, output, request_path, _, original = self._request_case(
            mutate=replace, reseal=False)
        with self.assertRaisesRegex(ValueError, "request identity mismatch"):
            self._invoke_request_parser(workspace, prepared, output, request_path, original)

    def test_resealed_selection_membership_still_must_match_invocation(self):
        def remove_female(request):
            request["character_ids"].remove("female")

        workspace, prepared, output, request_path, resealed, _ = self._request_case(
            mutate=remove_female, reseal=True)
        with self.assertRaisesRegex(ValueError, "selection mismatch"):
            self._invoke_request_parser(workspace, prepared, output, request_path, resealed)

    def test_resealed_source_hash_tamper_fails_against_packaged_bytes(self):
        logical = "characters/templates/exercise-mannequin-v1.yaml"

        def replace_hash(request):
            for descriptor in request["character_descriptors"]:
                if logical in descriptor["source_hashes"]:
                    descriptor["source_hashes"][logical] = "0" * 64
            for record in request["characters"]:
                record["source_hashes"][logical] = "0" * 64

        workspace, prepared, output, request_path, resealed, _ = self._request_case(
            mutate=replace_hash, reseal=True)
        with self.assertRaisesRegex(ValueError, "character source hash mismatch"):
            self._invoke_request_parser(workspace, prepared, output, request_path, resealed)

    def test_resealed_request_cannot_omit_a_selected_source_hash(self):
        logical = "characters/templates/exercise-mannequin-v1.yaml"

        def omit_hash(request):
            for descriptor in request["character_descriptors"]:
                descriptor["source_hashes"].pop(logical, None)
            for record in request["characters"]:
                record["source_hashes"].pop(logical, None)

        workspace, prepared, output, request_path, resealed, _ = self._request_case(
            mutate=omit_hash, reseal=True)
        with self.assertRaisesRegex(ValueError, "source hash closure"):
            self._invoke_request_parser(workspace, prepared, output, request_path, resealed)

    def test_resealed_template_carrier_mutation_fails_before_backend(self):
        def replace_carrier(request):
            request["characters"][0]["template"]["components"][2]["weighting"]["bands"][0]["from"] = "ghost.R"

        workspace, prepared, output, request_path, resealed, _ = self._request_case(
            mutate=replace_carrier, reseal=True)
        with self.assertRaisesRegex(ValueError, "carrier|source hash|descriptor"):
            self._invoke_request_parser(workspace, prepared, output, request_path, resealed)

    def test_api_rejects_manifest_with_stale_render_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            (workspace / "build").mkdir()
            prepared = api.prepare(
                workspace=workspace,
                output="build/manifest-identity-test_r1_test_try-1_input/input.json",
                fixtures=("neutral",), bpms=(60,),
            )

            def stale_manifest(prepared_path, output, **kwargs):
                output = Path(output)
                output.mkdir(parents=True, exist_ok=True)
                (output / "render-manifest.json").write_text(json.dumps({
                    "format": "character-render-manifest/v1",
                    "prepared_sha256": prepared.prepared_sha256,
                    "render_identity": "0" * 64,
                    "characters": [],
                }), encoding="utf-8")
                return {"stdout_log": str(output / "mock" / "stdout.log"),
                        "backend_identity": {"version": "5.2.2 LTS", "build_hash": "test"}}

            with mock.patch.object(api.run_blender, "run", side_effect=stale_manifest):
                with self.assertRaises(api.GenerationError) as caught:
                    api.render(prepared, workspace=workspace,
                               output="build/manifest-identity-test_r1_test_try-1_output",
                               characters=CHARACTERS, images=True, render_only=True)
            self.assertEqual(caught.exception.code, "output-integrity")

    @staticmethod
    def _manifest_fixture(root):
        output = root / "out"
        frames = output / "frames"
        prepared = {"content_sha256": "a" * 64, "samples": [
            {"id": "sample-0", "fixture": "arm-raise", "frame_id": 0},
            {"id": "sample-1", "fixture": "arm-raise", "frame_id": 1},
        ]}
        characters = []
        for character_id in CHARACTERS:
            samples = []
            for sample in prepared["samples"]:
                images = {}
                for view in ("front", "side"):
                    relative = (Path(character_id) if character_id != "skeleton" else Path()) / \
                        sample["fixture"] / view / f"{sample['frame_id']:05d}.png"
                    image_path = frames / relative
                    image_path.parent.mkdir(parents=True, exist_ok=True)
                    Image.new("RGBA", (2, 2), (80, 90, 100, 255)).save(image_path)
                    images[view] = relative.as_posix()
                samples.append({"id": sample["id"], "images": images})
            characters.append({"id": character_id, "samples": samples})
        manifest = {"format": "character-render-manifest/v1",
                    "prepared_sha256": prepared["content_sha256"],
                    "render_identity": "b" * 64, "characters": characters}
        return output, frames, prepared, manifest

    def test_valid_batch_manifest_has_exact_ordered_union_inventory(self):
        with tempfile.TemporaryDirectory() as temporary:
            output, frames, prepared, manifest = self._manifest_fixture(Path(temporary))
            required = validate_character_manifest(manifest, prepared, frames, output=output,
                                                    character_ids=CHARACTERS)
            image_paths = [path for path in required if str(path).endswith(".png")]
            self.assertEqual(len(image_paths), 12)
            self.assertEqual(len(set(required)), len(required))

    def test_batch_manifest_rejects_character_and_sample_membership_faults(self):
        faults = (
            (lambda manifest: manifest["characters"].pop(), "Character manifest ID inventory mismatch"),
            (lambda manifest: manifest["characters"].append(deepcopy(manifest["characters"][0])),
             "Character manifest ID inventory mismatch"),
            (lambda manifest: manifest["characters"].__setitem__(1, deepcopy(manifest["characters"][0])),
             "Character manifest ID inventory mismatch"),
            (lambda manifest: manifest["characters"].reverse(), "Character manifest ID inventory mismatch"),
            (lambda manifest: manifest["characters"][1]["samples"].pop(),
             "Character sample inventory mismatch"),
            (lambda manifest: manifest["characters"][1]["samples"].reverse(),
             "Character sample inventory mismatch"),
            (lambda manifest: manifest["characters"][1]["samples"][1].update(id="sample-0"),
             "Character sample inventory mismatch"),
        )
        for index, (mutate, message) in enumerate(faults):
            with self.subTest(index=index):
                with tempfile.TemporaryDirectory() as temporary:
                    output, frames, prepared, manifest = self._manifest_fixture(Path(temporary))
                    mutate(manifest)
                    with self.assertRaisesRegex(ValueError, message):
                        validate_character_manifest(manifest, prepared, frames, output=output,
                                                    character_ids=CHARACTERS)

    def test_batch_manifest_rejects_stale_missing_extra_and_escaping_inventory(self):
        faults = (
            (lambda manifest: manifest.update(prepared_sha256="f" * 64), "Stale character render manifest"),
            (lambda manifest: manifest["characters"][1]["samples"][0]["images"].pop("side"),
             "Character view inventory mismatch"),
            (lambda manifest: manifest["characters"][1]["samples"][0]["images"].update(up="extra.png"),
             "Character view inventory mismatch"),
            (lambda manifest: manifest["characters"][1]["samples"][0]["images"].update(front="../../outside.png"),
             "Character image path mismatch"),
        )
        for index, (mutate, message) in enumerate(faults):
            with self.subTest(index=index):
                with tempfile.TemporaryDirectory() as temporary:
                    output, frames, prepared, manifest = self._manifest_fixture(Path(temporary))
                    mutate(manifest)
                    with self.assertRaisesRegex(ValueError, message):
                        validate_character_manifest(manifest, prepared, frames, output=output,
                                                    character_ids=CHARACTERS)

    def test_union_receipt_requires_exact_unmodified_file_inventory(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "out"
            output.mkdir()
            first = output / "request.json"
            second = output / "frames" / "male" / "sample.png"
            second.parent.mkdir(parents=True)
            first.write_text("{}", encoding="utf-8")
            Image.new("RGBA", (2, 2), (1, 2, 3, 255)).save(second)
            required = [Path("request.json"), Path("frames/male/sample.png")]

            def record(path):
                from humanmotionlib.runtime import file_sha256
                return {"path": str((output / path).resolve()),
                        "size_bytes": (output / path).stat().st_size,
                        "sha256": file_sha256(output / path)}

            good = {"output_validation": {"status": "pass", "files": [record(item) for item in required]}}
            _receipt_files_unchanged(good, output, required)
            mutations = (
                ({"files": [record(required[0])]}, "inventory does not match"),
                ({"files": [record(item) for item in required] + [record(required[0])]},
                 "inventory does not match"),
                ({"files": [record(required[1]), record(required[0])]}, None),
                ({"files": [dict(record(required[0]), path=str(Path(temporary) / "outside")),
                              record(required[1])]}, "escapes pass directory"),
                ({"files": [dict(record(required[0]), sha256="0" * 64), record(required[1])]},
                 "missing or changed"),
            )
            for index, (validation, error) in enumerate(mutations):
                receipt = {"output_validation": {"status": "pass", **validation}}
                with self.subTest(index=index):
                    if error is None:
                        _receipt_files_unchanged(receipt, output, required)
                    else:
                        with self.assertRaisesRegex(ValueError, error):
                            _receipt_files_unchanged(receipt, output, required)


if __name__ == "__main__":
    unittest.main()
