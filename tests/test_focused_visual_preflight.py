# SPDX-License-Identifier: Apache-2.0
"""Bounded diagonal focused-visual kernel controls; no Blender is launched."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock

from humanmotionlib.api import _build_render_request
from humanmotionlib.character_surface import expand_surface
from humanmotionlib.character_verification import (
    _FOCUSED_VISUAL_FIXTURES, _fixture_coverage, _native_midpoint_beats,
    _required_dense_grid, _run_dense_surface_audit, _verify_native_midpoints,
    verify_character_output,
)
from humanmotionlib.characters import validate_character_sources
from humanmotionlib.prepare_skeleton import prepare


def _selected_male_surface(prepared):
    stature = float(prepared["sources"]["profile"]["stature_m"])
    _, _, selected = _build_render_request(
        prepared, SimpleNamespace(profile_id="adult-reference-v1", stature_m=stature),
        ("male",), render_only=False)
    character = selected[0]
    components = expand_surface(prepared["sources"]["profile"], character["template"],
                                character["appearance"], stature)["components"]
    return components


class FocusedVisualKernelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.focused = prepare("adult-reference-v1", 1.70,
                              fixtures=_FOCUSED_VISUAL_FIXTURES, bpms=(90,))
        cls.components = _selected_male_surface(cls.focused)

    def test_focused_verification_label_is_not_overwritten_by_selected_leaf_label(self):
        expected_ids = [row["id"] for row in validate_character_sources()]
        with tempfile.TemporaryDirectory(prefix="hml-focused-label-") as temporary:
            missing_run = Path(temporary) / "missing"
            focused = verify_character_output(
                self.focused, missing_run, expected_ids, numeric_only=True,
                selected_character_id="male", _focused_visual=True)
            ordinary = verify_character_output(
                self.focused, missing_run, expected_ids, numeric_only=True,
                selected_character_id="male")
        self.assertEqual(focused["verification_scope"], "focused-visual")
        self.assertEqual(ordinary["verification_scope"], "selected-character-numeric-leaf")

    def test_focused90_midpoint_inventory_is_empty_and_unexpected_row_fails(self):
        expected = _native_midpoint_beats(self.focused)
        self.assertEqual(set(expected), set(_FOCUSED_VISUAL_FIXTURES))
        self.assertTrue(all(not beats for beats in expected.values()))

        good = _verify_native_midpoints(self.focused, {"male": {"dense_samples": []}},
                                        {"male": self.components}, 1.70)
        self.assertEqual(good["status"], "pass")
        self.assertEqual(good["expected_samples_per_character"], 0)

        fixture = "arm-raise"
        bad = _verify_native_midpoints(self.focused,
            {"male": {"dense_samples": [{"fixture": fixture, "beat": 0.12345}]}},
            {"male": self.components}, 1.70)
        self.assertEqual(bad["status"], "fail")
        self.assertIn("native-midpoint-membership",
                      {failure["code"] for failure in bad["failures"]})

    def test_bounded_arm_raise_bpm60_midpoints_pass_without_claiming_full_scope(self):
        from tests.test_selected_numeric_fixture import SelectedSurfaceNumericFixtureTests

        prepared = prepare("adult-reference-v1", 1.70, fixtures=("arm-raise",), bpms=(60,))
        with tempfile.TemporaryDirectory(prefix="hml-focused-armraise-midpoints-") as temporary:
            run = Path(temporary) / "synthetic-run"
            run.mkdir()
            helper = SelectedSurfaceNumericFixtureTests(
                "test_selected_male_and_female_accept_complete_host_oracle_numeric_evidence")
            helper._make_surface_run("armraise-bpm60", "male", prepared=prepared, run_root=run)
            evaluated = json.loads((run / "characters/male/surface-evaluated.json").read_text())

        expected = _native_midpoint_beats(prepared)
        self.assertEqual(set(expected), {"arm-raise"})
        self.assertEqual(len(expected["arm-raise"]), 4)
        report = _verify_native_midpoints(prepared, {"male": evaluated},
                                          {"male": _selected_male_surface(prepared)}, 1.70)
        self.assertEqual(report["status"], "pass", report["failures"][:3])
        self.assertEqual(report["expected_samples_per_character"], 4)
        coverage = _fixture_coverage(prepared)
        self.assertEqual(coverage["status"], "incomplete")
        self.assertIn("rest", coverage["missing"])

    def test_focused_dense_grid_has_exact_eleven_fixture_membership(self):
        grid = _required_dense_grid(self.focused, _FOCUSED_VISUAL_FIXTURES)
        self.assertEqual(set(grid), set(_FOCUSED_VISUAL_FIXTURES))
        for fixture_id, beats in grid.items():
            self.assertTrue(beats)
            self.assertLessEqual(max((right-left for left, right in zip(beats, beats[1:])),
                                     default=0.0),
                                 0.01 + 1e-10)
            delivered = {float(sample["beat"]["numerator"]) /
                         float(sample["beat"]["denominator"])
                         for sample in self.focused["samples"]
                         if sample["fixture"] == fixture_id}
            self.assertTrue(delivered.issubset(set(beats)))

    def test_single_neutral_dense_event_measures_contact_and_detects_lifted_foot(self):
        grid = {"neutral": [0.0]}
        positive = _run_dense_surface_audit(self.focused, {"male": self.components}, 1.70, grid)
        self.assertEqual(positive["status"], "pass", positive["failures"][:3])
        self.assertEqual(positive["observed_sample_character_pairs"], 1)

        lifted = deepcopy(self.components)
        foot = next(component for component in lifted if component["id"] == "foot.L")
        foot["vertices_m"] = [(vertex[0], vertex[1], vertex[2] + 0.02 * 1.70)
                              for vertex in foot["vertices_m"]]
        negative = _run_dense_surface_audit(self.focused, {"male": lifted}, 1.70, grid)
        self.assertEqual(negative["status"], "fail")
        self.assertIn("dense-sole-contact", {failure["code"] for failure in negative["failures"]})

    def test_actual_diagonal_preflight_runs_focused_dense_once_and_rejects_coherent_dq_fault(self):
        from tests.test_selected_numeric_fixture import (
            SelectedSkeletonNumericFixtureTests, SelectedSurfaceNumericFixtureTests)
        from humanmotionlib.character_verification import verify_character_output
        from humanmotionlib.prepared import write_json
        from humanmotionlib.review_pack import _preflight_diagonal_inputs
        from humanmotionlib.runtime import check_blender_version

        heights = {"skeleton": 1.50, "male": 1.70, "female": 1.90}
        with tempfile.TemporaryDirectory(prefix="hml-focused-diagonal-preflight-") as temporary:
            workspace = Path(temporary)
            build = workspace / "build"
            build.mkdir()
            runs = {}
            prepared_records = {}
            skeleton_builder = SelectedSkeletonNumericFixtureTests(
                "test_selected_skeleton_runs_real_transform_verifier_and_stays_global_incomplete")
            surface_builder = SelectedSurfaceNumericFixtureTests(
                "test_selected_male_and_female_accept_complete_host_oracle_numeric_evidence")
            profile = {"prepare_s": 0.0, "skeleton_evidence_s": 0.0,
                       "surface_evidence_s": 0.0, "verify_character_output_s": {}}
            overall_started = time.perf_counter()
            for identifier, height in heights.items():
                run = build / f"add-shared-body-characters_r10_test_try-1_{identifier}-h{int(height * 100)}"
                run.mkdir()
                phase_started = time.perf_counter()
                prepared = prepare("adult-reference-v1", height,
                                   fixtures=_FOCUSED_VISUAL_FIXTURES, bpms=(90,))
                profile["prepare_s"] += time.perf_counter() - phase_started
                if identifier == "skeleton":
                    phase_started = time.perf_counter()
                    skeleton_builder._make_run(identifier, prepared=prepared, run_root=run)
                    profile["skeleton_evidence_s"] += time.perf_counter() - phase_started
                else:
                    phase_started = time.perf_counter()
                    surface_builder._make_surface_run(identifier, identifier,
                                                       prepared=prepared, run_root=run)
                    profile["surface_evidence_s"] += time.perf_counter() - phase_started
                runs[identifier] = run
                prepared_records[identifier] = prepared
            output = build / "add-shared-body-characters_r10_test_try-1-pack-output"
            specifications = [(identifier, runs[identifier]) for identifier in heights]
            captured = {}
            verifier = verify_character_output

            def capture(prepared, render_run, expected_ids, *args, **kwargs):
                character_id = kwargs.get("selected_character_id")
                phase_started = time.perf_counter()
                report = verifier(prepared, render_run, expected_ids, *args, **kwargs)
                profile["verify_character_output_s"][character_id] = \
                    time.perf_counter() - phase_started
                captured[character_id] = report
                return report

            with mock.patch("humanmotionlib.runtime.check_blender_version"), \
                 mock.patch("humanmotionlib.backend_measurements.verify_backend",
                                     return_value={"status": "pass", "samples": []}), \
                 mock.patch("humanmotionlib.character_verification.verify_character_output",
                                     side_effect=capture):
                phase_started = time.perf_counter()
                records, resolved, identities = _preflight_diagonal_inputs(
                    runs["skeleton"], prepared_records["skeleton"],
                    specifications, output, workspace)
                profile["diagonal_preflight_s"] = time.perf_counter() - phase_started
                profile["total_s"] = time.perf_counter() - overall_started
                print("TEST_PROFILE actual-diagonal-preflight " +
                      json.dumps(profile, sort_keys=True), flush=True)
                self.assertEqual(set(records), set(heights))
                self.assertEqual(set(resolved), set(heights))
                self.assertEqual(set(identities["numeric_verification"]), set(heights))
                for identifier in ("skeleton", "male", "female"):
                    self.assertEqual(captured[identifier]["fixture_coverage"]["scope"],
                                     "focused-visual")
                    self.assertEqual(captured[identifier]["fixture_coverage"]["status"], "pass")
                for identifier in ("male", "female"):
                    self.assertEqual(captured[identifier]["dense"]["status"], "pass")
                    self.assertEqual(captured[identifier]["dense"]["observed_sample_character_pairs"],
                                     sum(len(beats) for beats in
                                         captured[identifier]["dense"]["required_beats_by_fixture"].values()))
                self.assertFalse(output.exists())

                # Change one delivered male vertex and update its derived summary
                # and receipt hash, so the verifier must diagnose the measurement.
                surface_path = runs["male"] / "characters/male/surface-evaluated.json"
                surface = json.loads(surface_path.read_text())
                sample = surface["samples"][0]
                component = sample["components"][0]
                vertex_id = component["vertex_ids"][0]
                displacement = 0.02 * heights["male"]
                component["vertices_m"][0][0] += displacement
                component["maximum_source_world_residual_m"] = displacement
                component["maximum_native_local_residual_m"] = 0.0
                component["maximum_reference_residual_m"] = displacement
                component["worst_reference_vertex_id"] = vertex_id
                component["worst_native_local_vertex_id"] = vertex_id
                write_json(surface_path, surface)
                receipt_path = runs["male"] / "processes/fixture-build/outcome.json"
                receipt = json.loads(receipt_path.read_text())
                inventory = next(item for item in receipt["output_validation"]["files"]
                                 if item["path"].endswith("surface-evaluated.json"))
                payload = surface_path.read_bytes()
                inventory["size_bytes"] = len(payload)
                inventory["sha256"] = hashlib.sha256(payload).hexdigest()
                write_json(receipt_path, receipt)
                captured.clear()
                with self.assertRaisesRegex(ValueError, "no passing selected numeric evidence"):
                    _preflight_diagonal_inputs(
                        runs["skeleton"], prepared_records["skeleton"],
                        specifications, output, workspace)
                self.assertIn("surface-evidence", {item["code"]
                                   for item in captured["male"]["failures"]})
                self.assertTrue(any("reported DQ residual mismatch" in item["detail"]
                                    for item in captured["male"]["failures"]))
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
