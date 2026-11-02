# SPDX-License-Identifier: Apache-2.0
"""Focused installed-package fixtures for selected-character numeric checks."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from humanmotionlib import api
from humanmotionlib.character_verification import verify_character_output
from humanmotionlib.package_resources import manifest_sha256, verify_runtime_integrity
from humanmotionlib.prepare_skeleton import prepare
from humanmotionlib.prepared import write_json
from humanmotionlib.runtime import backend_contract
from tests.run_roots import test_case_root


class SelectedSkeletonNumericFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prepared = prepare("adult-reference-v1", 1.7, fixtures=["neutral", "rest"])
        from humanmotionlib.characters import _load_yaml
        cls.registry_ids = tuple(row["id"] for row in _load_yaml("characters/registry.yaml")["characters"])

    def _make_run(self, name, *, corrupt_transform=False, prepared=None, run_root=None):
        prepared = prepared or self.prepared
        run = test_case_root("selected-numeric-fixture", name) if run_root is None else Path(run_root)
        run.mkdir(parents=True, exist_ok=True)
        request, selected_ids, _ = api._build_render_request(
            prepared,
            SimpleNamespace(profile_id="adult-reference-v1", stature_m=prepared["sources"]["profile"]["stature_m"]),
            ("skeleton",), render_only=False)
        self.assertEqual(selected_ids, ("skeleton",))

        output_files = {
            "input.json": prepared,
            "character-render-request.json": request,
            "build-metadata.json": {
                "format": "synthetic-character-evidence/v1",
                "character_ids": ["skeleton"],
                "render_identity": request["render_identity"],
            },
            "evaluated.json": {
                "format": "skeleton-evaluated/v1",
                "prepared_sha256": prepared["content_sha256"],
                "samples": prepared["samples"],
                "metadata": {"blender_version": "fixture", "blender_build": "fixture"},
            },
            "geometry-reference.json": {
                "format": "skeleton-evaluated-geometry/v1",
                "prepared_sha256": prepared["content_sha256"],
                "geometry": {},
            },
        }
        if corrupt_transform:
            output_files["evaluated.json"]["samples"][0]["frames"]["scapula.R"]["rotation"][0][0] += 0.1
        for relative, value in output_files.items():
            write_json(run / relative, value)
        (run / "skeleton.blend").write_bytes(b"synthetic evidence fixture; scene is not evaluated here")

        identity = verify_runtime_integrity()
        required = ("input.json", "build-metadata.json", "skeleton.blend",
                    "character-render-request.json", "evaluated.json", "geometry-reference.json")
        file_inventory = []
        for relative in required:
            path = run / relative
            file_inventory.append({
                "path": str(path.resolve()),
                "size_bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
        process = run / "processes" / "fixture-build"
        process.mkdir(parents=True)
        phases = [
            {"phase": "input_loaded", "prepared_sha256": prepared["content_sha256"]},
            {"phase": "backend_ready", "render_identity": request["render_identity"],
             "character_ids": ["skeleton"]},
            {"phase": "script_complete", "prepared_sha256": prepared["content_sha256"],
             "render_identity": request["render_identity"], "character_ids": ["skeleton"]},
        ]
        receipt = {
            "operation": "build",
            "package_version": identity["version"],
            "runtime_manifest_sha256": manifest_sha256(),
            "resource_hashes": identity["resources"],
            "backend_contract_sha256": identity["backend_contract"],
            "implementation_hashes": identity["implementation"],
            "state": "succeeded", "outcome": "exit", "return_code": 0,
            "source_sha256": prepared["content_sha256"],
            "last_script_phase": "script_complete", "phases": phases,
            "output_validation": {"status": "pass", "files": file_inventory},
        }
        write_json(process / "outcome.json", receipt)
        return run

    def test_selected_skeleton_runs_real_transform_verifier_and_stays_global_incomplete(self):
        run = self._make_run("valid")
        backend_result = {"status": "pass", "samples": []}
        with patch("humanmotionlib.runtime.check_blender_version"), \
             patch("humanmotionlib.backend_measurements.verify_backend", return_value=backend_result):
            report = verify_character_output(
                self.prepared, run, self.registry_ids, (1.7,), numeric_only=True,
                selected_character_id="skeleton")

        self.assertEqual(report["numeric_status"], "pass")
        self.assertEqual(report["status"], "incomplete")
        self.assertEqual(report["registry"]["checked_ids"], ["skeleton"])
        self.assertEqual(report["registry"]["omitted_ids"], [item for item in self.registry_ids if item != "skeleton"])
        self.assertEqual(report["skeleton_numeric"]["transforms"]["status"], "pass")

    def test_tampered_evaluated_transform_fails_selected_numeric_leaf(self):
        run = self._make_run("tampered", corrupt_transform=True)
        with patch("humanmotionlib.runtime.check_blender_version"), \
             patch("humanmotionlib.backend_measurements.verify_backend", return_value={"status": "pass", "samples": []}):
            report = verify_character_output(
                self.prepared, run, self.registry_ids, (1.7,), numeric_only=True,
                selected_character_id="skeleton")

        self.assertEqual(report["numeric_status"], "fail")
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any(item["code"] == "skeleton-transforms" for item in report["failures"]))

    def test_selected_skeleton_rejects_mutated_evaluated_output_and_receipt(self):
        for case in ("mutated-output", "mutated-receipt"):
            with self.subTest(case=case):
                run = self._make_run(case)
                if case == "mutated-output":
                    evaluated = run / "evaluated.json"
                    evaluated.write_bytes(evaluated.read_bytes() + b" ")
                else:
                    receipt_path = run / "processes" / "fixture-build" / "outcome.json"
                    receipt = json.loads(receipt_path.read_text())
                    receipt["state"] = "failed"
                    receipt_path.write_text(json.dumps(receipt))
                with patch("humanmotionlib.runtime.check_blender_version"), \
                     patch("humanmotionlib.backend_measurements.verify_backend",
                           return_value={"status": "pass", "samples": []}):
                    report = verify_character_output(
                        self.prepared, run, self.registry_ids, (1.7,), numeric_only=True,
                        selected_character_id="skeleton")
                self.assertEqual(report["status"], "fail")
                self.assertNotEqual(report["numeric_status"], "pass")
                self.assertTrue(any(item["code"] == "evidence-invalid" for item in report["failures"]))

    def test_selected_character_scope_is_rejected_for_non_numeric_mode(self):
        report = verify_character_output(
            self.prepared, Path("unused"), self.registry_ids, (1.7,), numeric_only=False,
            selected_character_id="skeleton")
        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["failures"][0]["code"], "invalid-scope")


class SelectedSurfaceNumericFixtureTests(unittest.TestCase):
    """Host-oracle synthetic surface evidence for selected male/female checks.

    This deliberately exercises the real verifier and its dense midpoint checks.
    It is not evidence that Blender produced these vertices: Blender version
    probing is the sole mock, while observed vertices are independently
    generated from canonical source frames by the verifier's DQ reference path.
    """

    @classmethod
    def setUpClass(cls):
        from humanmotionlib.characters import _load_yaml
        # A selected numerical element covers every registered diagnostic.
        # One fixture would make the character leaf legitimately incomplete.
        cls.prepared = prepare("adult-reference-v1", 1.7, fixtures=None, bpms=(180,))
        cls.registry_ids = tuple(row["id"] for row in
                                 _load_yaml("characters/registry.yaml")["characters"])

    def _make_surface_run(self, name, character_id, *, prepared=None, tamper_dense=False,
                          omit_dense=False, run_root=None):
        from humanmotionlib.character_surface import _rest_frames
        from humanmotionlib.character_skinning import compile_pose_skinning, source_world_transforms
        from humanmotionlib.character_verification import (
            _compiled_surface_weight_layout, _expected_anchor_positions, _minimum_vertex_z,
            _native_sample_floor_extremum, _surface_poses,
        )
        from humanmotionlib.characters import expand_surface

        prepared = self.prepared if prepared is None else prepared
        run = Path(run_root).resolve() if run_root is not None else test_case_root("selected-numeric-fixture", name)
        if run_root is not None:
            if not run.is_dir() or any(run.iterdir()):
                raise ValueError("caller-supplied run_root must be an existing empty directory")
        request, selected_ids, selected = api._build_render_request(
            prepared,
            SimpleNamespace(profile_id="adult-reference-v1", stature_m=1.7),
            (character_id,), render_only=False)
        self.assertEqual(selected_ids, (character_id,))
        character = selected[0]
        components = expand_surface(prepared["sources"]["profile"], character["template"],
                                    character["appearance"], 1.7)["components"]
        surfaces = {character_id: components}
        weight_set, offsets, carriers = _compiled_surface_weight_layout(surfaces)
        _, rest_frames = _rest_frames(prepared["sources"]["profile"], 1.0)

        def make_row(sample_id, fixture, beat, frames, contacts):
            solved_sample = {"frames": frames, "contacts": contacts}
            transforms = source_world_transforms(prepared["sources"]["profile"], frames,
                                                  carriers, rest_frames=rest_frames)
            compiled = compile_pose_skinning(transforms, weight_set)
            posed = _surface_poses(prepared["sources"]["profile"], frames, components,
                                   rest_frames, compiled_pose=compiled, component_offsets=offsets)
            actual = []
            for component in posed:
                minimum = _minimum_vertex_z(component["vertices_m"], component["vertex_ids"])
                first_id = component["vertex_ids"][0] if component["vertex_ids"] else None
                actual.append({"id": component["id"], "vertices_m": component["vertices_m"],
                    "vertex_ids": list(component["vertex_ids"]), "minimum_z_m": minimum[0],
                    "worst_floor_vertex_id": minimum[1],
                    "maximum_source_world_residual_m": 0.0,
                    "maximum_native_local_residual_m": 0.0,
                    "maximum_reference_residual_m": 0.0,
                    "worst_reference_vertex_id": first_id,
                    "worst_native_local_vertex_id": first_id})
            posed_by_id = {item["id"]: item for item in posed}
            anchors = _expected_anchor_positions(prepared["sources"]["profile"], solved_sample)
            face_by_id = {item["id"]: item["faces"] for item in components}
            actual_contacts = []
            from humanmotionlib.character_verification import _closest_mesh_distance
            for anchor_id, anchor in anchors.items():
                side = anchor_id.rsplit(".", 1)[-1]
                distance = _closest_mesh_distance(anchor, posed_by_id["foot." + side]["vertices_m"],
                                                   face_by_id["foot." + side])
                actual_contacts.append({"anchor_id": anchor_id, "anchor_m": list(anchor),
                                        "closest_sole_distance_m": distance})
            sample_min = _native_sample_floor_extremum(
                {item["id"]: item for item in actual}, sorted(item["id"] for item in actual))
            return {"sample_id": sample_id, "fixture": fixture, "beat": beat,
                    "components": actual, "contacts": actual_contacts,
                    "minimum_z_m": sample_min[0], "worst_floor_vertex_id": sample_min[1]}

        reference_components = []
        for component in components:
            first_id = component["vertex_ids"][0] if component["vertex_ids"] else None
            reference_components.append({**component,
                "native_rest_vertices_m": component["vertices_m"],
                "maximum_rest_residual_m": 0.0, "worst_rest_vertex_id": first_id})
        character_root = run / "characters" / character_id
        character_root.mkdir(parents=True)
        write_json(character_root / "surface-reference.json", {
            "format": "hml-surface-reference/v1", "prepared_sha256": prepared["content_sha256"],
            "render_identity": request["render_identity"], "character_id": character_id,
            "profile_id": prepared["sources"]["profile"]["id"], "stature_m": 1.7,
            "surface_sha256": request["surface_identities"][character_id],
            "template_id": character["template"]["id"],
            "appearance_id": character["appearance"]["id"], "components": reference_components})

        evaluated_samples = [make_row(sample["id"], sample["fixture"], sample["beat"],
            sample["frames"], sample["contacts"]) for sample in prepared["samples"]]
        from humanmotionlib.api import _native_surface_midpoint_samples
        midpoints = _native_surface_midpoint_samples(prepared)
        from humanmotionlib.character_midpoints import expected_midpoint_inventory
        expected_midpoints = expected_midpoint_inventory(prepared)
        self.assertTrue(midpoints, "moving fixture must provide native midpoint evidence")
        self.assertEqual([(row["fixture"], row["beat"]) for row in midpoints], expected_midpoints)
        if tamper_dense or omit_dense:
            self.assertTrue(midpoints, "negative control must mutate a nonempty midpoint inventory")
        dense_rows = [make_row(row["id"], row["fixture"], row["beat"], row["frames"], row["contacts"])
                      for row in midpoints]
        if tamper_dense and dense_rows:
            dense_rows[0]["components"][0]["vertices_m"] = [list(vertex)
                for vertex in dense_rows[0]["components"][0]["vertices_m"]]
            dense_rows[0]["components"][0]["vertices_m"][0][0] += 0.02
        if omit_dense and dense_rows:
            dense_rows.pop()
        write_json(character_root / "surface-evaluated.json", {
            "format": "hml-surface-evaluated/v1", "prepared_sha256": prepared["content_sha256"],
            "render_identity": request["render_identity"], "character_id": character_id,
            "reference_metric": "canonical-double-world-dq/v1",
            "samples": evaluated_samples, "dense_samples": dense_rows})

        output_files = {
            "input.json": prepared,
            "character-render-request.json": request,
            "build-metadata.json": {"format": "synthetic-character-evidence/v1",
                "character_ids": [character_id], "render_identity": request["render_identity"]},
            "evaluated.json": {"format": "skeleton-evaluated/v1",
                "prepared_sha256": prepared["content_sha256"], "samples": [],
                "metadata": {"blender_version": "fixture", "blender_build": "fixture"}},
            "geometry-reference.json": {"format": "skeleton-evaluated-geometry/v1",
                "prepared_sha256": prepared["content_sha256"], "geometry": {}},
        }
        for relative, value in output_files.items():
            write_json(run / relative, value)
        (run / "skeleton.blend").write_bytes(b"synthetic evidence; Blender scene not evaluated")
        identity = verify_runtime_integrity()
        required = ["input.json", "build-metadata.json", "skeleton.blend",
                    "character-render-request.json", "evaluated.json", "geometry-reference.json",
                    f"characters/{character_id}/surface-reference.json",
                    f"characters/{character_id}/surface-evaluated.json"]
        files = []
        for relative in required:
            path = run / relative
            files.append({"path": str(path.resolve()), "size_bytes": path.stat().st_size,
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        process = run / "processes" / "fixture-build"
        process.mkdir(parents=True)
        receipt = {"operation": "build", "package_version": identity["version"],
            "runtime_manifest_sha256": manifest_sha256(), "resource_hashes": identity["resources"],
            "backend_contract_sha256": identity["backend_contract"],
            "implementation_hashes": identity["implementation"], "state": "succeeded",
            "outcome": "exit", "return_code": 0,
            "source_sha256": prepared["content_sha256"], "last_script_phase": "script_complete",
            "phases": [{"phase": "input_loaded", "prepared_sha256": prepared["content_sha256"]},
                {"phase": "backend_ready", "render_identity": request["render_identity"],
                 "character_ids": [character_id]},
                {"phase": "script_complete", "prepared_sha256": prepared["content_sha256"],
                 "render_identity": request["render_identity"], "character_ids": [character_id]}],
            "output_validation": {"status": "pass", "files": files}}
        write_json(process / "outcome.json", receipt)
        return run

    def test_selected_male_and_female_accept_complete_host_oracle_numeric_evidence(self):
        for character_id in ("male", "female"):
            with self.subTest(character_id=character_id):
                run = self._make_surface_run("valid-" + character_id, character_id)
                with patch("humanmotionlib.runtime.check_blender_version"):
                    report = verify_character_output(self.prepared, run, self.registry_ids,
                        (1.7,), numeric_only=True, selected_character_id=character_id)
                self.assertEqual(report["numeric_status"], "pass", report["failures"][:3])
                self.assertEqual(report["status"], "incomplete")
                self.assertEqual(report["registry"]["checked_ids"], [character_id])
                self.assertEqual(report["native_midpoints"]["status"], "pass")
                self.assertEqual(report["dense"]["status"], "pass")

    def test_selected_surface_rejects_tampered_and_missing_dense_midpoint_evidence(self):
        for name, kwargs, expected_code in (
            ("tampered-dense", {"tamper_dense": True}, "native-midpoint"),
            ("missing-dense", {"omit_dense": True}, "native-midpoint"),
        ):
            with self.subTest(case=name):
                run = self._make_surface_run(name, "male", **kwargs)
                with patch("humanmotionlib.runtime.check_blender_version"):
                    report = verify_character_output(self.prepared, run, self.registry_ids,
                        (1.7,), numeric_only=True, selected_character_id="male")
                self.assertEqual(report["numeric_status"], "fail")
                self.assertIn(expected_code, {item["code"] for item in report["failures"]})

    def test_verify_skeleton_selected_three_stature_scope_is_scoped_and_recomputed(self):
        """Exercise the installed CLI and real character leaves with no Blender run.

        Collection and backend measurements are controlled positives. The real
        cross-stature geometry comparator, action coverage, squat balance audits
        and skeleton leaves run against synthetic evaluated frames and sealed
        receipts; source scaling, scope routing and aggregate binding are real.
        """
        from humanmotionlib import verify_skeleton

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            build = workspace / "build"
            build.mkdir()
            heights = (1.5, 1.7, 1.9)
            prepared_by_height = {height: prepare("adult-reference-v1", height,
                fixtures=["neutral", "rest"]) for height in heights}
            runs = []
            for height in heights:
                run = build / f"selected-numeric_r1_dev_try-h{int(height * 100)}_generated"
                runs.append(SelectedSkeletonNumericFixtureTests._make_run(self, f"aggregate-h{int(height * 100)}",
                    prepared=prepared_by_height[height], run_root=run))
            base_mass = {row["id"]: row["position_m"] for row in
                         prepared_by_height[1.7]["sources"]["profile"]["mass_model"]["segments"]}
            for height, run in zip(heights, runs):
                prepared = prepared_by_height[height]
                evaluated_path = run / "evaluated.json"
                evaluated = json.loads(evaluated_path.read_text())
                rest = next(sample for sample in evaluated["samples"] if sample["id"] == "rest/00000")
                rest["geometry"] = {"synthetic-body": {"topology_sha256": "stable-topology"}}
                rest["mass_points"] = {id: {"position_m": [coordinate * height / 1.7
                    for coordinate in position]} for id, position in base_mass.items()}
                write_json(evaluated_path, evaluated)
                write_json(run / "geometry-reference.json", {
                    "format": "skeleton-evaluated-geometry/v1",
                    "prepared_sha256": prepared["content_sha256"],
                    "geometry": {"synthetic-body": {"vertices_m": [[0.0, 0.0, 0.0],
                        [0.0, 0.0, height]]}},
                })
                receipt_path = run / "processes" / "fixture-build" / "outcome.json"
                receipt = json.loads(receipt_path.read_text())
                for entry in receipt["output_validation"]["files"]:
                    output_path = Path(entry["path"])
                    if output_path.resolve() in (evaluated_path.resolve(),
                                                  (run / "geometry-reference.json").resolve()):
                        entry["size_bytes"] = output_path.stat().st_size
                        entry["sha256"] = hashlib.sha256(output_path.read_bytes()).hexdigest()
                write_json(receipt_path, receipt)
            output_run = build / "selected-numeric_r1_dev_try-positive_aggregate"
            output = output_run / "numeric-aggregate.json"

            argv = ["verify-skeleton", "--input", str(runs[0]), "--output", str(output),
                    "--numeric-only", "--selected-character", "skeleton",
                    "--character-output", str(runs[0]), "--stature-builds", *map(str, runs)]
            with patch.object(sys, "argv", argv), \
                 patch("humanmotionlib.verification_run.verify_collection",
                       return_value={"status": "pass", "scope": "controlled aggregate fixture",
                                     "samples": []}), \
                 patch("humanmotionlib.runtime.check_blender_version"), \
                 patch("humanmotionlib.backend_measurements.verify_backend",
                       return_value={"status": "pass", "samples": []}):
                main_status = verify_skeleton.main(workspace=workspace)
            if output.is_file():
                main_report = json.loads(output.read_text())
                self.assertEqual(main_status, 0, {
                    "status": main_report.get("status"),
                    "numeric_status": main_report.get("numeric_status"),
                    "matrix_failures": main_report.get("character_verification", {}).get("matrix_failures"),
                    "leaf_results": [{"status": item.get("report", {}).get("numeric_status"),
                                      "failures": item.get("report", {}).get("failures", [])[:4]}
                                     for item in main_report.get("character_verification", {}).get("runs", [])],
                    "stature_comparison": main_report.get("stature_comparison", {}).get("status"),
                    "stature_balance": [row.get("status") for row in main_report.get("stature_balance", [])],
                })
            else:
                self.assertEqual(main_status, 0)
            aggregate = json.loads(output.read_text())
            scoped = aggregate["character_verification"]
            self.assertEqual(aggregate["verification_scope"], "selected-character-three-stature-numeric")
            self.assertEqual(aggregate["checked_character_ids"], ["skeleton"])
            self.assertEqual(scoped["comparison_complete"], True)
            self.assertEqual(scoped["matrix_complete"], False)
            self.assertEqual(scoped["status"], "incomplete")
            self.assertEqual(scoped["observed_statures_m"], [1.5, 1.7, 1.9])
            self.assertEqual(len(scoped["runs"]), 3)
            self.assertEqual(aggregate["action_coverage"]["status"], "pass")
            self.assertEqual(aggregate["stature_comparison"]["status"], "pass")
            self.assertTrue(aggregate["stature_comparison"]["checks"])
            self.assertEqual([item["status"] for item in aggregate["stature_balance"]],
                             ["pass", "pass", "pass"])
            self.assertEqual([item["stature_m"] for item in aggregate["stature_balance"]], list(heights))

            # Exercise the real comparator's scaling assertion with one altered
            # native geometry vertex; the positive aggregate above used the same
            # comparator without mocks.
            from humanmotionlib.stature_comparison import compare_statures
            high_geometry_path = runs[2] / "geometry-reference.json"
            high_geometry_original = high_geometry_path.read_bytes()
            high_geometry = json.loads(high_geometry_original)
            high_geometry["geometry"]["synthetic-body"]["vertices_m"][1][2] *= 1.1
            write_json(high_geometry_path, high_geometry)
            tampered_comparison = compare_statures(runs)
            self.assertEqual(tampered_comparison["status"], "fail")
            self.assertTrue(any(check["id"] == "H1.9.synthetic-body.normalized_vertices"
                                and check["status"] == "fail"
                                for check in tampered_comparison["checks"]))
            high_geometry_path.write_bytes(high_geometry_original)

            bad_output = build / "selected-numeric_r1_dev_try-unknown_aggregate" / "numeric.json"
            bad_argv = ["verify-skeleton", "--input", str(runs[0]), "--output", str(bad_output),
                        "--numeric-only", "--selected-character", "unknown-character",
                        "--character-output", str(runs[0]), "--stature-builds", *map(str, runs)]
            with patch.object(sys, "argv", bad_argv), \
                 patch("humanmotionlib.verification_run.verify_collection",
                       side_effect=AssertionError("numerical work started for unknown character")):
                self.assertEqual(verify_skeleton.main(workspace=workspace), 1)
            self.assertFalse(bad_output.exists())

            duplicate_output = build / "selected-numeric_r1_dev_try-duplicate_aggregate" / "numeric.json"
            duplicate_argv = ["verify-skeleton", "--input", str(runs[0]), "--output", str(duplicate_output),
                "--numeric-only", "--selected-character", "skeleton", "--character-output", str(runs[0]),
                "--stature-builds", str(runs[0]), str(runs[0]), str(runs[2])]
            with patch.object(sys, "argv", duplicate_argv), \
                 patch("humanmotionlib.verification_run.verify_collection",
                       side_effect=AssertionError("numerical work started for duplicate heights")):
                self.assertEqual(verify_skeleton.main(workspace=workspace), 1)
            self.assertFalse(duplicate_output.exists())

            wrong_height_run = SelectedSkeletonNumericFixtureTests._make_run(
                self, "aggregate-h160", prepared=prepare("adult-reference-v1", 1.6,
                    fixtures=["neutral", "rest"]),
                run_root=build / "selected-numeric_r1_dev_try-h160_generated")
            wrong_height_output = build / "selected-numeric_r1_dev_try-wrong-height_aggregate" / "numeric.json"
            wrong_height_argv = ["verify-skeleton", "--input", str(runs[0]), "--output",
                str(wrong_height_output), "--numeric-only", "--selected-character", "skeleton",
                "--character-output", str(runs[0]), "--stature-builds", str(runs[0]),
                str(wrong_height_run), str(runs[2])]
            with patch.object(sys, "argv", wrong_height_argv), \
                 patch("humanmotionlib.verification_run.verify_collection",
                       side_effect=AssertionError("numerical work started for a wrong stature set")):
                self.assertEqual(verify_skeleton.main(workspace=workspace), 1)
            self.assertFalse(wrong_height_output.exists())


if __name__ == "__main__":
    unittest.main()
