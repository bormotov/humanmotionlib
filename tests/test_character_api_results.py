# SPDX-License-Identifier: Apache-2.0
"""Public result records for shared character renders."""

import json
import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from humanmotionlib import api
from humanmotionlib.package_resources import manifest_sha256, verify_runtime_integrity
from humanmotionlib.render_contract import expected_views, validate_character_manifest
from humanmotionlib.runtime import file_sha256


class CharacterApiResultTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name).resolve()
        (self.workspace / "build").mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def _prepare(self, label):
        return api.prepare(
            workspace=self.workspace,
            output=f"build/result-api_r1_test_try-1_{label}-input/input.json",
            fixtures=("neutral",), bpms=(60,),
        )

    def _successful_images_backend(self, prepared_path, output, **kwargs):
        """Write a tiny, fully inventoried character image result for API projection tests."""
        output = Path(output).resolve()
        output.mkdir(parents=True, exist_ok=True)
        prepared = json.loads(Path(prepared_path).read_text(encoding="utf-8"))
        request_path = Path(kwargs["character_request"]).resolve()
        request = json.loads(request_path.read_text(encoding="utf-8"))
        (output / "input.json").write_bytes(Path(prepared_path).read_bytes())
        (output / "skeleton.blend").write_bytes(b"test scene")
        metadata = {"blender_version": "5.2.2 LTS", "blender_build": "fixture",
                    "platform": "test", "render_identity": request["render_identity"]}
        (output / "build-metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

        if kwargs.get("render_dir") is None:
            (output / "skeleton.blend").write_bytes(b"test scene")
            evidence = output / "processes" / "fixture"
            evidence.mkdir(parents=True)
            stdout = evidence / "stdout.log"
            stdout.write_text("fixture backend completed\n", encoding="utf-8")
            return {"stdout_log": str(stdout), "backend_identity": {
                "version": metadata["blender_version"], "build_hash": metadata["blender_build"]}}

        frames = Path(kwargs["render_dir"]).resolve()
        frames.mkdir(parents=True, exist_ok=True)
        (output / "skeleton.blend").write_bytes(b"test scene")

        ids = tuple(kwargs["characters"])
        rows = []
        for character_id in ids:
            samples = []
            for sample in prepared["samples"]:
                views = expected_views(prepared, sample) if character_id == "skeleton" else (
                    {"front", "side", "rear"} if sample["fixture"] in ("neutral", "rest")
                    else {"front", "side"})
                image_records = {}
                for view in sorted(views):
                    relative = (Path(sample["fixture"]) / view /
                                f"{str(sample['frame_id']).zfill(5)}.png")
                    if character_id != "skeleton":
                        relative = Path(character_id) / relative
                    image_path = frames / relative
                    image_path.parent.mkdir(parents=True, exist_ok=True)
                    # Pixel colors make the character/sample/view join observable.
                    color = ((len(character_id) * 41) % 256,
                             (len(sample["id"]) * 17) % 256,
                             (sum(map(ord, view)) * 3) % 256, 255)
                    Image.new("RGBA", (2, 2), color).save(image_path)
                    image_records[view] = relative.as_posix()
                samples.append({"id": sample["id"], "images": image_records})
            rows.append({"id": character_id, "samples": samples})
        manifest = {
            "format": "character-render-manifest/v1",
            "prepared_sha256": prepared["content_sha256"],
            "render_identity": request["render_identity"],
            "characters": rows,
        }
        (output / "render-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        required = validate_character_manifest(
            manifest, prepared, frames, output=output, character_ids=ids)
        if request_path != (output / "character-render-request.json").resolve():
            shutil.copyfile(request_path, output / "character-render-request.json")

        runtime = verify_runtime_integrity()
        evidence = output / "processes" / "fixture"
        evidence.mkdir(parents=True)
        stdout = evidence / "stdout.log"
        stdout.write_text("fixture backend completed\n", encoding="utf-8")
        receipt = {
            "operation": "render-pass", "state": "succeeded", "outcome": "exit",
            "return_code": 0, "source_sha256": prepared["content_sha256"],
            "last_script_phase": "script_complete",
            "phases": [{"phase": name, "prepared_sha256": prepared["content_sha256"]}
                       for name in ("input_loaded", "script_complete")],
            "package_version": runtime["version"],
            "runtime_manifest_sha256": manifest_sha256(),
            "resource_hashes": runtime["resources"],
            "backend_contract_sha256": runtime["backend_contract"],
            "implementation_hashes": runtime["implementation"],
            "output_validation": {"status": "pass", "files": [
                {"path": str((output / relative).resolve()),
                 "size_bytes": (output / relative).stat().st_size,
                 "sha256": file_sha256(output / relative)} for relative in required]},
        }
        (evidence / "outcome.json").write_text(json.dumps(receipt), encoding="utf-8")
        return {"stdout_log": str(stdout), "backend_identity": {
            "version": metadata["blender_version"], "build_hash": metadata["blender_build"]}}

    def test_rendered_image_three_argument_construction_defaults_to_skeleton(self):
        image = api.RenderedImage("neutral@0", "front", Path("image.png"))
        self.assertEqual(image.character_id, "skeleton")
        self.assertEqual(image.to_dict()["character_id"], "skeleton")

    def test_owned_pass_creates_singleton_request_and_private_claim(self):
        prepared = self._prepare("managed-claim")
        owner = self.workspace / "build" / "characters_r1_test_try-1_managed-owner"
        owner.mkdir()
        output = owner / "clean-a"
        observed = {}

        def inspect_claim(input_path, output_path, **kwargs):
            claim = kwargs["managed_claim"]
            request_path = Path(kwargs["character_request"])
            request_bytes = request_path.read_bytes()
            request = json.loads(request_bytes)
            observed.update({"claim": claim, "input": Path(input_path), "output": Path(output_path),
                             "request_path": request_path, "request": request,
                             "entries": sorted(path.name for path in Path(output_path).iterdir())})
            self.assertEqual(claim.owner_run, str(owner.resolve()))
            self.assertEqual(claim.pass_root, str(output.resolve()))
            self.assertEqual(claim.request_path, str(request_path.resolve()))
            self.assertEqual(claim.request_sha256, hashlib.sha256(request_bytes).hexdigest())
            self.assertEqual(claim.render_identity, request["render_identity"])
            self.assertEqual(claim.prepared_sha256, prepared.prepared_sha256)
            self.assertEqual(claim.character_ids, ("skeleton", "male", "female"))
            self.assertEqual(sorted(path.name for path in Path(output_path).iterdir()),
                             ["character-render-request.json"])
            raise ValueError("managed claim fixture stop")

        with patch.object(api.run_blender, "run", side_effect=inspect_claim) as backend:
            with self.assertRaisesRegex(api.GenerationError, "managed claim fixture stop"):
                api._render_owned_pass(prepared, workspace=self.workspace, owner_run=owner,
                                       output=output, images=False,
                                       characters=("skeleton", "male", "female"),
                                       render_only=True)
        backend.assert_called_once()
        self.assertEqual(observed["entries"], ["character-render-request.json"])

    def test_public_render_still_rejects_occupied_flat_output_before_backend(self):
        prepared = self._prepare("occupied-public")
        output = self.workspace / "build" / "result-api_r1_test_try-1_occupied-render"
        output.mkdir()
        sentinel = output / "foreign.txt"
        sentinel.write_text("keep")
        with patch.object(api.run_blender, "run") as backend:
            with self.assertRaisesRegex(api.GenerationError, "occupied"):
                api.render(prepared, workspace=self.workspace,
                           output="build/result-api_r1_test_try-1_occupied-render",
                           images=False, render_only=True)
        backend.assert_not_called()
        self.assertEqual(sentinel.read_text(), "keep")

    def test_character_result_projection_and_independent_later_request(self):
        prepared = self._prepare("projection")
        with patch.object(api.run_blender, "run", side_effect=self._successful_images_backend) as backend:
            result = api.render(prepared, workspace=self.workspace,
                                output="build/result-api_r1_test_try-1_projection-render",
                                characters=("female", "skeleton", "male"), images=False,
                                render_only=True)
            self.assertEqual(backend.call_count, 1)
            first_request = json.loads(Path(backend.call_args.kwargs["character_request"]).read_text())
            # Caller mutation of the returned result must not leak into the next request.
            projection = result.to_dict()
            projection["characters"][1]["source_hashes"].clear()
            projection["character_provenance"]["male"]["source_hashes"].clear()
            projection["prepared"]["provenance"]["sources"][0]["sha256"] = "changed"
            second = api.render(prepared, workspace=self.workspace,
                                output="build/result-api_r1_test_try-1_projection-render-again",
                                characters=("male", "female"), images=False,
                                render_only=True)
            second_request = json.loads(Path(backend.call_args.kwargs["character_request"]).read_text())

        self.assertEqual(first_request["character_ids"], ["skeleton", "male", "female"])
        self.assertEqual([row.character_id for row in second.characters], ["male", "female"])
        self.assertEqual(first_request["prepared_sha256"], prepared.prepared_sha256)
        self.assertEqual(second_request["prepared_sha256"], prepared.prepared_sha256)
        self.assertEqual(first_request["prepared_sha256"], second_request["prepared_sha256"])
        self.assertTrue(result.characters[1].source_hashes)  # detached projection did not mutate record
        self.assertTrue(result.character_provenance["male"]["source_hashes"])
        first_male = next(row for row in first_request["character_descriptors"] if row["id"] == "male")
        second_male = next(row for row in second_request["character_descriptors"] if row["id"] == "male")
        self.assertEqual(first_male["source_hashes"], second_male["source_hashes"])
        self.assertEqual(prepared.provenance.sources[0].sha256,
                         result.prepared.provenance.sources[0].sha256)
        first_request_path = result.artifacts["character_render_request"]
        self.assertEqual(json.loads(first_request_path.read_text())["render_identity"],
                         first_request["render_identity"])
        self.assertEqual(result.render_identity, first_request["render_identity"])
        self.assertEqual(set(result.character_provenance), {"skeleton", "male", "female"})
        self.assertEqual([item.character_id for item in result.character_artifacts],
                         ["skeleton", "male", "female"])
        for character in result.characters:
            expected = first_request["character_descriptors"][
                [row["id"] for row in first_request["character_descriptors"]].index(character.character_id)]
            self.assertEqual(character.source_hashes, expected["source_hashes"])
            self.assertEqual(character.profile_id, expected["profile_id"])
        self.assertTrue(all(path.is_absolute() for item in result.character_artifacts
                            for path in item.artifacts.values()))
        self.assertTrue(all(path.is_absolute() for path in result.artifacts.values()))
        self.assertEqual(json.loads(json.dumps(result.to_dict()))["render_identity"],
                         result.render_identity)
        self.assertEqual(result.prepared.prepared_sha256, prepared.prepared_sha256)

    def test_rendered_images_join_by_character_sample_and_view_on_shared_timeline(self):
        prepared = self._prepare("image-join")
        with patch.object(api.run_blender, "run", side_effect=self._successful_images_backend):
            result = api.render(prepared, workspace=self.workspace,
                                output="build/result-api_r1_test_try-1_image-join-render",
                                characters=("male", "female", "skeleton"), images=True,
                                render_only=True)

        ids = {"skeleton", "male", "female"}
        expected_keys = set()
        prepared_json = json.loads(prepared.prepared_path.read_text(encoding="utf-8"))
        for sample in prepared.poses:
            for character_id in ids:
                source_sample = next(row for row in prepared_json["samples"] if row["id"] == sample.sample_id)
                views = expected_views(prepared_json, source_sample) if character_id == "skeleton" else (
                    {"front", "side", "rear"} if source_sample["fixture"] in ("neutral", "rest")
                    else {"front", "side"})
                expected_keys.update((character_id, sample.sample_id, view) for view in views)
        observed = {(image.character_id, image.sample_id, image.view) for image in result.images}
        self.assertEqual(observed, expected_keys)
        self.assertEqual(len(result.images), len(observed))
        self.assertTrue(all(image.path.is_absolute() and image.path.is_file() for image in result.images))
        self.assertTrue(all(image.path.is_relative_to(result.output_root / "frames")
                            for image in result.images))
        self.assertEqual({image.character_id for image in result.images}, ids)
        timeline_ids = {entry.sample_id for timeline in prepared.timelines for entry in timeline.entries}
        self.assertEqual({image.sample_id for image in result.images}, timeline_ids)
        for image in result.images:
            sample = next(pose for pose in prepared.poses if pose.sample_id == image.sample_id)
            self.assertIn(sample.sample_id, timeline_ids)
            with Image.open(image.path) as decoded:
                decoded.verify()


if __name__ == "__main__":
    unittest.main()
