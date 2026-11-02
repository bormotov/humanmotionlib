# SPDX-License-Identifier: Apache-2.0
"""Host contracts for complete character review-pack joins and coverage."""

from __future__ import annotations

import tempfile
import unittest
import importlib.util
import json
from pathlib import Path
import shutil
import sys

from PIL import Image
import yaml

import humanmotionlib

_SOURCE_MODULE = Path(__file__).resolve().parents[1] / "src" / "humanmotionlib" / "review_pack.py"
humanmotionlib.__path__ = [str(_SOURCE_MODULE.parent)]
_SPEC = importlib.util.spec_from_file_location("humanmotionlib.review_pack", _SOURCE_MODULE)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"Could not load source review-pack module: {_SOURCE_MODULE}")
_REVIEW_PACK = importlib.util.module_from_spec(_SPEC)
sys.modules["humanmotionlib.review_pack"] = _REVIEW_PACK
_SPEC.loader.exec_module(_REVIEW_PACK)

_character_grid = _REVIEW_PACK._character_grid
_character_images = _REVIEW_PACK._character_images
_character_plan_coverage = _REVIEW_PACK._character_plan_coverage
_character_sample_rows = _REVIEW_PACK._character_sample_rows
_baseline_sample_matches = _REVIEW_PACK._baseline_sample_matches
_sample_records_for_plan = _REVIEW_PACK._sample_records_for_plan
_stature_strip = _REVIEW_PACK._stature_strip
_JOINT_CENTER_IDS = _REVIEW_PACK._JOINT_CENTER_IDS
_sole_crop = _REVIEW_PACK._sole_crop
_baseline_report_record = _REVIEW_PACK._baseline_report_record

class CharacterReviewPackTests(unittest.TestCase):
    def test_baseline_report_record_is_json_safe_and_omits_internal_objects(self) -> None:
        receipt = Path("build/old-run/processes/example/outcome.json").resolve()
        record = _baseline_report_record({
            "status": "pass", "receipt_path": receipt,
            "common_sample_ids": ["neutral/00000"],
            "required_paths": [Path("frames/neutral/front/00000.png")],
            "evaluated_geometry": {"samples": [{"artifact": Path("evaluated.json")} ]},
            "run_root": Path("build/old-run"), "manifest": object(), "prepared": object(),
        })
        self.assertEqual(record["receipt_path"], str(receipt))
        self.assertEqual(record["required_paths"], ["frames/neutral/front/00000.png"])
        self.assertEqual(record["evaluated_geometry"]["samples"][0]["artifact"], "evaluated.json")
        self.assertNotIn("manifest", record)
        self.assertNotIn("prepared", record)
        json.dumps(record)

    def test_sole_crop_creates_nested_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.png"
            Image.new("RGB", (64, 64), (120, 140, 160)).save(source)
            output = root / "composites" / "sole-forefoot-rocker" / "sample.png"
            self.assertEqual(_sole_crop(source, output, "Skeleton / front / sample"), output)
            self.assertTrue(output.is_file())

    def test_joint_center_markers_resolve_in_the_real_adult_profile(self) -> None:
        profile_path = Path(__file__).resolve().parents[1] / "rig" / "profiles" / "adult-reference-v1.yaml"
        profile = yaml.safe_load(profile_path.read_text())
        structure_ids = {item["id"] for item in profile["structures"]}
        self.assertEqual(len(_JOINT_CENTER_IDS), len(set(_JOINT_CENTER_IDS)))
        self.assertEqual(set(_JOINT_CENTER_IDS) - structure_ids, set())
        self.assertIn("talus.R", _JOINT_CENTER_IDS)
        self.assertIn("talus.L", _JOINT_CENTER_IDS)

    def test_baseline_join_uses_fixture_and_exact_fraction_not_schedule_ids(self) -> None:
        candidate = {"samples": [
            {"id": "new-arm-000", "fixture": "arm-raise", "beat": {"numerator": 1, "denominator": 4},
             "frames": {"arm": 1}, "actions": [], "contacts": [], "world_root": {},
             "frame_id": 11},
            {"id": "new-arm-001", "fixture": "arm-raise", "beat": {"numerator": 1, "denominator": 1},
             "frames": {"arm": 2}, "actions": [], "contacts": [], "world_root": {},
             "frame_id": 20},
        ]}
        baseline = {"samples": [
            {"id": "old-arm-A", "fixture": "arm-raise", "beat": {"numerator": 2, "denominator": 8},
             "frames": {"arm": 1}, "actions": [], "contacts": [], "world_root": {},
             "frame_id": 5},
            {"id": "old-arm-B", "fixture": "arm-raise", "beat": {"numerator": 4, "denominator": 4},
             "frames": {"arm": 2}, "actions": [], "contacts": [], "world_root": {},
             "frame_id": 6},
        ]}
        matches = _baseline_sample_matches(candidate, baseline, ("arm-raise",))
        self.assertEqual([(row["baseline_sample_id"], row["candidate_sample_id"]) for row in matches],
                         [("old-arm-A", "new-arm-000"), ("old-arm-B", "new-arm-001")])
        self.assertEqual(matches[0]["beat"], {"numerator": 1, "denominator": 4})

    def test_baseline_join_rejects_duplicate_or_missing_logical_beats(self) -> None:
        sample = {"id": "a", "fixture": "squat", "beat": {"numerator": 1, "denominator": 2},
                  "frames": {}, "actions": [], "contacts": [], "world_root": {}}
        with self.assertRaisesRegex(ValueError, "duplicate logical sample key"):
            _baseline_sample_matches({"samples": [sample, {**sample, "id": "b"}]},
                                     {"samples": [sample]}, ("squat",))
        with self.assertRaisesRegex(ValueError, "missing required shared-core beats"):
            _baseline_sample_matches({"samples": [sample]},
                                     {"samples": [{**sample, "beat": {"numerator": 1, "denominator": 1}}]},
                                     ("squat",))

    def test_baseline_join_requires_equal_movement_contract(self) -> None:
        candidate_row = {"id": "new", "fixture": "walking-in-place",
                         "beat": {"numerator": 3, "denominator": 4}, "frames": {"hip": 1},
                         "actions": [], "contacts": [], "world_root": {}}
        old_row = {**candidate_row, "id": "old", "frames": {"hip": 2}}
        with self.assertRaisesRegex(ValueError, "movement differs"):
            _baseline_sample_matches({"samples": [candidate_row]}, {"samples": [old_row]},
                                     ("walking-in-place",))

    def test_character_manifest_requires_registry_and_sample_completeness(self) -> None:
        ids = ("skeleton", "male", "female")
        sample_ids = ("neutral-0", "arm-raise-1")
        manifest = {"format": "character-render-manifest/v1", "characters": [
            {"id": identifier, "samples": [{"id": sample_id} for sample_id in sample_ids]}
            for identifier in ids
        ]}
        rows = _character_sample_rows(manifest, ids, sample_ids)
        self.assertEqual(tuple(rows), ids)
        self.assertEqual([row["id"] for row in rows["female"]], list(sample_ids))

        reversed_manifest = {**manifest, "characters": list(reversed(manifest["characters"]))}
        with self.assertRaisesRegex(ValueError, "member inventory"):
            _character_sample_rows(reversed_manifest, ids, sample_ids)
        incomplete = {**manifest, "characters": manifest["characters"][:-1]}
        with self.assertRaisesRegex(ValueError, "member inventory"):
            _character_sample_rows(incomplete, ids, sample_ids)
        shortened = {**manifest, "characters": [
            {"id": identifier, "samples": rows[identifier] if identifier != "male"
             else rows[identifier][:-1]}
            for identifier in ids
        ]}
        with self.assertRaisesRegex(ValueError, "missing, extra, or reordered samples"):
            _character_sample_rows(shortened, ids, sample_ids)

    def test_image_inventory_rejects_missing_and_escaping_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            frames = root / "frames"
            sample = {"id": "neutral-0", "fixture": "neutral"}
            prepared = {"samples": [sample], "sources": {"review-scene": {"cameras": []}}}
            manifest = {"format": "character-render-manifest/v1", "characters": []}
            for identifier in ("skeleton", "male", "female"):
                views = ("front", "side", "rear")
                images = {}
                for view in views:
                    path = frames / (identifier if identifier != "skeleton" else "") / "neutral" / view / "00000.png"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    Image.new("RGB", (32, 32), (50, 80, 120)).save(path)
                    relative = path.relative_to(frames).as_posix()
                    images[view] = relative
                manifest["characters"].append({"id": identifier,
                                               "samples": [{"id": sample["id"], "images": images}]})
            result = _character_images(manifest, frames, prepared, ("skeleton", "male", "female"))
            self.assertEqual(tuple(result), ("skeleton", "male", "female"))
            self.assertEqual(set(result["female"]["neutral-0"]), {"front", "side", "rear"})

            bad = {"format": manifest["format"], "characters": [dict(row) for row in manifest["characters"]]}
            bad["characters"][1] = {"id": "male", "samples": [{"id": "neutral-0", "images": {
                "front": "../../outside.png", "side": "male/neutral/side/00000.png",
                "rear": "male/neutral/rear/00000.png"}}]}
            with self.assertRaisesRegex(ValueError, "Unsafe character image path"):
                _character_images(bad, frames, prepared, ("skeleton", "male", "female"))

    def test_comparison_grid_keeps_three_labeled_character_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            images = {}
            for index, identifier in enumerate(("skeleton", "male", "female")):
                image = root / f"{identifier}.png"
                Image.new("RGB", (40, 24), (index * 70, 40, 150)).save(image)
                images[identifier] = {"sample-0": {"front": image}}
            output = root / "comparison.png"
            _character_grid(images, [{"sample_id": "sample-0", "beat": {
                "numerator": 0, "denominator": 1}}], "front", output,
                title="Neutral silhouette / front", columns=("skeleton", "male", "female"))
            with Image.open(output) as result:
                self.assertEqual(result.size, (900, 400))

    def test_coverage_is_explicit_when_required_samples_are_absent(self) -> None:
        partial = {"sampling": {"arm-raise": [{"bpm": 90, "static": [1], "animation": [1]}]},
                   "samples": []}
        result = _character_plan_coverage(partial)
        self.assertEqual(result["status"], "incomplete")
        self.assertIn("squat@90bpm", result["missing"])
        self.assertIn("walking-in-place@90bpm", result["missing"])
        self.assertIn("forefoot-rocker@90bpm animation samples", result["missing"])

    def test_complete_focus_counts_and_references_are_not_synthesized(self) -> None:
        def records(count):
            return [{"sample_id": f"sample-{index}", "beat": {"numerator": index, "denominator": 1}}
                    for index in range(count)]
        sampling = {
            "arm-raise": [{"bpm": 90, "static": records(5), "animation": records(17)}],
            "squat": [{"bpm": 90, "static": records(5), "animation": records(17)}],
            "walking-in-place": [{"bpm": 90, "static": records(9), "animation": records(33)}],
            "forefoot-rocker": [{"bpm": 90, "static": records(2), "animation": records(3)}],
        }
        for identifier in ("sweep-shoulder-bilateral-elevation", "sweep-shoulder-bilateral-plane",
                           "sweep-shoulder-bilateral-external_twist", "sweep-forearm-bilateral-pronation",
                           "sweep-knee-bilateral-flexion"):
            sampling[identifier] = [{"bpm": 90, "animation": records(3)}]
        result = _character_plan_coverage({"sampling": sampling})
        self.assertEqual(result["status"], "incomplete")
        self.assertIn("neutral sample", result["missing"])
        self.assertIn("rest sample", result["missing"])
        self.assertEqual(result["coverage"]["walking-in-place"],
                         {"static": 9, "animation": 33, "status": "pass"})
        with self.assertRaisesRegex(ValueError, "missing or foreign sample"):
            _sample_records_for_plan(sampling["squat"][0], "squat", "static", {})

    def test_coverage_requires_supplied_neutral_rest_and_rocker_animation(self) -> None:
        data = {"sampling": {"forefoot-rocker": [{"bpm": 90, "animation": [1]}]},
                "samples": [{"fixture": "neutral"}, {"fixture": "rest"}]}
        result = _character_plan_coverage(data)
        self.assertIn("arm-raise@90bpm", result["missing"])
        self.assertNotIn("neutral sample", result["missing"])
        self.assertNotIn("rest sample", result["missing"])

    def test_stature_strip_uses_only_supplied_sample_images(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inputs = {"missing_heights": [], "inputs": {}}
            for height in (1.50, 1.70, 1.90):
                prepared = {"content_sha256": f"prep-{height}", "package_identity": "pkg",
                            "sources": {"profile": {"stature_m": height},
                                        "review-scene": {"cameras": []}},
                            "samples": [
                                {"id": "neutral-000", "fixture": "neutral",
                                 "beat": {"numerator": 0, "denominator": 1}, "frame_id": 0},
                                {"id": "squat-002", "fixture": "squat",
                                 "beat": {"numerator": 2, "denominator": 1}, "frame_id": 2},
                            ]}
                run = root / f"h-{height:.2f}"
                frames = run / "frames"
                manifest = {"format": "character-render-manifest/v1", "characters": []}
                for identifier_index, identifier in enumerate(("skeleton", "male", "female")):
                    rows = []
                    for sample in prepared["samples"]:
                        views = ("front", "side", "rear") if sample["fixture"] == "neutral" else ("front", "side")
                        paths = {}
                        for view in views:
                            path = frames / identifier / sample["fixture"] / view / "00000.png"
                            path.parent.mkdir(parents=True, exist_ok=True)
                            Image.new("RGB", (24, 32), (identifier_index * 60, int(height * 50), 30)).save(path)
                            paths[view] = path.relative_to(frames).as_posix()
                        rows.append({"id": sample["id"], "images": paths})
                    manifest["characters"].append({"id": identifier, "samples": rows})
                run.mkdir(parents=True, exist_ok=True)
                (run / "render-manifest.json").write_text(__import__("json").dumps(manifest))
                (run / "build-metadata.json").write_text("{}")
                if height == 1.70:
                    pass_root = root / "clean-a"
                    pass_root.mkdir()
                    shutil.copytree(frames, pass_root / "frames")
                    (pass_root / "render-manifest.json").write_text(__import__("json").dumps(manifest))
                    (pass_root / "build-metadata.json").write_text("{}")
                    inputs["inputs"][height] = {"run_root": None, "prepared": prepared}
                else:
                    inputs["inputs"][height] = {"run_root": run, "prepared": prepared}
                    pass_root = root / f"stature-{int(round(height * 100)):03d}"
                    pass_root.mkdir()
                    shutil.copytree(frames, pass_root / "frames")
                    (pass_root / "render-manifest.json").write_text(__import__("json").dumps(manifest))
                    (pass_root / "build-metadata.json").write_text("{}")

            report = _stature_strip(inputs, ("skeleton", "male", "female"), root)
            self.assertEqual(report["status"], "pass")
            self.assertEqual(len(report["cells"]), 36)
            self.assertEqual(len(report["images"]), 4)
            for image in report["images"]:
                self.assertTrue((root / image).is_file())
            self.assertEqual({row["height_m"] for row in report["sources"]}, {1.50, 1.70, 1.90})


if __name__ == "__main__":
    unittest.main()
