# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from unittest import mock

from PIL import Image
from PIL import ImageChops

from tools import matrix_presentation as presentation


class PresentationHelpersTest(unittest.TestCase):
    def test_matrix_output_requires_exact_declared_nested_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            build = workspace / "build"
            build.mkdir()
            element = build / "change_r1_dev_current_element-demo"
            element.mkdir()
            output = element / "presentation"
            output.mkdir()
            self.assertEqual(presentation._fresh_output(output, workspace, element), output.resolve())
            with self.assertRaisesRegex(presentation.PresentationError, "declared element presentation"):
                presentation._fresh_output(element / "other", workspace, element)
            (output / "old.html").write_text("stale")
            with self.assertRaisesRegex(presentation.PresentationError, "fresh empty"):
                presentation._fresh_output(output, workspace, element)

    def test_relative_paths_reject_traversal_and_absolute_paths(self):
        for unsafe in ("../outside.png", "/tmp/outside.png", "a/../../b.png", "a\\..\\b.png"):
            with self.subTest(path=unsafe), self.assertRaises(presentation.PresentationError):
                presentation._safe_relative(unsafe, "test")
        self.assertEqual(str(presentation._safe_relative("fixture/front/00000.png", "test")),
                         "fixture/front/00000.png")

    def test_rational_time_requires_canonical_positive_denominator(self):
        self.assertEqual(presentation._fraction({"numerator": 1, "denominator": 3}), Fraction(1, 3))
        for value in ({"numerator": 1, "denominator": 0},
                      {"numerator": True, "denominator": 1},
                      {"numerator": 1, "denominator": 2, "extra": 0}):
            with self.subTest(value=value), self.assertRaises(presentation.PresentationError):
                presentation._fraction(value)

    def test_timeline_rejects_nonincreasing_animation(self):
        prepared = {"sampling": {"fixture": [{"bpm": 120,
            "static": [{"sample_id": "a", "beat": {"numerator": 0, "denominator": 1},
                        "seconds": {"numerator": 0, "denominator": 1}}],
            "animation": [
                {"sample_id": "a", "beat": {"numerator": 0, "denominator": 1},
                 "seconds": {"numerator": 0, "denominator": 1}},
                {"sample_id": "b", "beat": {"numerator": 1, "denominator": 1},
                 "seconds": {"numerator": 1, "denominator": 2}},
                {"sample_id": "c", "beat": {"numerator": 2, "denominator": 1},
                 "seconds": {"numerator": 1, "denominator": 2}},
            ]}]}}
        with self.assertRaisesRegex(presentation.PresentationError, "non-increasing"):
            presentation._verify_prepared_timeline(prepared, ("fixture",))

class PresentationRecoveryTest(unittest.TestCase):
    @contextmanager
    def _fixture(self, workspace: Path):
        from humanmotionlib import prepared as prepared_module
        from humanmotionlib import render_contract

        (workspace / "build").mkdir()
        producer = workspace / "build/change_r1_dev_try-1_visual-build"
        producer.mkdir()
        frames = producer / "frames"
        frames.mkdir()
        sample_ids = ["raise/00000", "raise/00001", "raise/00002"]
        sampling = {"raise": [{"bpm": 120, "intervals_per_beat": 2,
            "static": [
                {"sample_id": sample_ids[0], "beat": {"numerator": 0, "denominator": 1},
                 "seconds": {"numerator": 0, "denominator": 1}},
                {"sample_id": sample_ids[2], "beat": {"numerator": 1, "denominator": 1},
                 "seconds": {"numerator": 1, "denominator": 2}},
            ],
            "animation": [
                {"sample_id": sample_ids[0], "beat": {"numerator": 0, "denominator": 1},
                 "seconds": {"numerator": 0, "denominator": 1}},
                {"sample_id": sample_ids[1], "beat": {"numerator": 1, "denominator": 2},
                 "seconds": {"numerator": 1, "denominator": 4}},
                {"sample_id": sample_ids[2], "beat": {"numerator": 1, "denominator": 1},
                 "seconds": {"numerator": 1, "denominator": 2}},
            ]}]}
        prepared = {"content_sha256": "prepared-test", "sampling": sampling,
                    "samples": [{"id": sample, "fixture": "raise"} for sample in sample_ids]}
        prepared_path = producer / "input.json"
        prepared_path.write_text(json.dumps(prepared), encoding="utf-8")
        manifest = {"format": "character-render-manifest/v1", "prepared_sha256": "prepared-test",
                    "render_identity": "render-test",
                    "characters": [{"id": "skeleton", "samples": []}]}
        for sample in sample_ids:
            path = frames / "raise" / "front" / f"{sample[-5:]}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (40, 80), (15 + int(sample[-1]) * 30, 30, 45)).save(path)
            manifest["characters"][0]["samples"].append({"id": sample, "images": {
                "front": f"raise/front/{sample[-5:]}.png"}})
        manifest_path = producer / "render-manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        def read_prepared(path):
            return json.loads(Path(path).read_text(encoding="utf-8"))

        def validate_character(value, data, frame_root, *, output, character_ids):
            self.assertEqual(tuple(character_ids), ("skeleton",))
            self.assertEqual(Path(output), producer.resolve())
            for sample in value["characters"][0]["samples"]:
                image = frame_root / sample["images"]["front"]
                with Image.open(image) as decoded:
                    decoded.verify()
            return [Path("frames") / "raise/front/" / f"{sample['id'][-5:]}.png"
                    for sample in value["characters"][0]["samples"]]

        with mock.patch.object(prepared_module, "read_prepared", side_effect=read_prepared), \
             mock.patch.object(render_contract, "validate_character_manifest", side_effect=validate_character), \
             mock.patch.object(render_contract, "read_supervised_receipt", return_value={"state": "succeeded"}):
            yield prepared_path, manifest_path, frames, producer, prepared_module, render_contract

    def test_recovery_reuses_validated_images_writes_inventory_and_preserves_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            with self._fixture(workspace) as (prepared, manifest, frames, producer, _, _):
                before = {p: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (prepared, manifest, *frames.rglob("*.png"))}
                output = workspace / "build/change_r1_dev_try-2_present"
                output.mkdir()
                with mock.patch.object(subprocess, "Popen", side_effect=AssertionError("process spawned")):
                    result = presentation.assemble_presentation(
                        prepared, manifest, frames, output, workspace=workspace,
                        character_ids=("skeleton",), fixtures=("raise",),
                        metadata={"stature_m": 1.7, "bpm": 120})
                self.assertEqual(result["source_image_count"], 3)
                self.assertEqual(len(result["gif_timing"]), 1)
                self.assertEqual(result["gif_timing"][0]["decoded_duration_ms"], 500)
                inventory = json.loads((output / "presentation-inventory.json").read_text())
                self.assertEqual(len(inventory["source_images"]), 3)
                page = (output / "index.html").read_text()
                self.assertIn("height:auto", page)
                self.assertIn("All validated source images", page)
                self.assertIn("presentation-inventory.json", page)
                self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in before})
                with Image.open(output / "raise-120-front-counts.png") as image:
                    self.assertEqual(image.size, (320, 692))
                    first_tile = image.crop((0, 0, 320, 320))
                    bounds = ImageChops.difference(
                        first_tile.convert("RGB"), Image.new("RGB", first_tile.size, (245, 247, 248))).getbbox()
                    self.assertIsNotNone(bounds)
                    self.assertEqual(bounds[2] - bounds[0], 160)
                    self.assertEqual(bounds[3] - bounds[1], 320)
                with Image.open(output / "raise-120-skeleton-front.gif") as image:
                    self.assertEqual(image.size, (512, 512))
                    image.seek(0)
                    difference = ImageChops.difference(image.convert("RGB"), Image.new("RGB", image.size, (245, 247, 248)))
                    bounds = difference.getbbox()
                    self.assertIsNotNone(bounds)
                    self.assertEqual(bounds[2] - bounds[0], 256)
                    self.assertEqual(bounds[3] - bounds[1], 512)

    def test_check_validates_existing_identity_links_gif_timing_and_frame_order(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp).resolve()
            with self._fixture(workspace) as (prepared, manifest, frames, producer, prepared_module, render_contract):
                output = workspace / "build/change_r1_dev_try-2_presentation-h170"
                output.mkdir()
                with mock.patch.object(subprocess, "Popen", side_effect=AssertionError("process spawned")):
                    presentation.assemble_presentation(
                        prepared, manifest, frames, output, workspace=workspace,
                        character_ids=("skeleton",), fixtures=("raise",))
                    validation_args = {"inventory_path": output / "presentation-inventory.json",
                                       "output_run": output, "prepared_path": prepared,
                                       "render_manifest_path": manifest, "frames_base": frames,
                                       "workspace": workspace, "character_ids": ("skeleton",),
                                       "fixtures": ("raise",)}
                    with mock.patch.object(prepared_module, "read_prepared",
                                           side_effect=lambda path: json.loads(Path(path).read_text())), \
                         mock.patch.object(render_contract, "validate_character_manifest",
                                           side_effect=lambda value, data, frame_root, **kwargs: [
                                               Path("frames") / sample["images"]["front"]
                                               for sample in value["characters"][0]["samples"]]), \
                         mock.patch.object(render_contract, "read_supervised_receipt",
                                           return_value={"state": "succeeded"}):
                        result = presentation.validate_presentation_inventory(**validation_args)
                        self.assertEqual(result["identity"], "pass")
                        self.assertEqual(result["links"], "pass")
                        self.assertEqual(result["gif_timing"], "pass")

                        gif_path = output / "raise-120-skeleton-front.gif"
                        with Image.open(gif_path) as image:
                            frames_data = [image.seek(index) or image.convert("RGB").copy()
                                           for index in range(image.n_frames)]
                        frames_data[0].save(gif_path, save_all=True, append_images=frames_data[1:],
                                            duration=[250, 100], loop=0, disposal=2)
                        inventory_path = output / "presentation-inventory.json"
                        inventory = json.loads(inventory_path.read_text())
                        media = next(row for row in inventory["media"] if row["kind"] == "animation-gif")
                        media["sha256"] = hashlib.sha256(gif_path.read_bytes()).hexdigest()
                        inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
                        with self.assertRaisesRegex(presentation.PresentationError, "GIF timing"):
                            presentation.validate_presentation_inventory(**validation_args)

    def test_corrupt_manifest_image_is_rejected_before_output_allocation(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            with self._fixture(workspace) as (prepared, manifest, frames, producer, _, _):
                (frames / "raise/front/00001.png").write_bytes(b"not a png")
                output = workspace / "build/change_r1_dev_try-2_present"
                with self.assertRaises(presentation.PresentationError):
                    presentation.assemble_presentation(
                        prepared, manifest, frames, output, workspace=workspace,
                        character_ids=("skeleton",), fixtures=("raise",))
                self.assertFalse(output.exists())

    def test_missing_and_occupied_outputs_fail_without_touching_producer(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            with self._fixture(workspace) as (prepared, manifest, frames, producer, _, _):
                with self.assertRaises(presentation.PresentationError):
                    presentation.assemble_presentation(
                        prepared, manifest, frames.parent / "elsewhere", workspace / "build/change_r1_dev_try-2_present",
                        workspace=workspace, character_ids=("skeleton",), fixtures=("raise",))
                occupied = workspace / "build/change_r1_dev_try-2_present"
                occupied.mkdir()
                (occupied / "keep.txt").write_text("keep")
                with self.assertRaisesRegex(presentation.PresentationError, "fresh empty"):
                    presentation.assemble_presentation(
                        prepared, manifest, frames, occupied, workspace=workspace,
                        character_ids=("skeleton",), fixtures=("raise",))
                self.assertEqual((occupied / "keep.txt").read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
