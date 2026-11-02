# SPDX-License-Identifier: Apache-2.0
"""Fail-closed checks for character-suite verification inputs."""

import json
import hashlib
import math
from copy import deepcopy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

from humanmotionlib.character_verification import (
    _audit_surface_sample, _beat_label, _closest_mesh_distance, _compiled_surface_weight_layout,
    _content_hash, _dense_contact_points,
    _fixture_coverage, _json_shape,
    _expected_anchor_positions, _load_generation_anchor, _minimum_vertex_z, _native_midpoint_beats,
    _prepared_sample_context, _reference_residual_summary_matches, _run_dense_surface_audit,
    _surface_poses, _verify_native_midpoints,
    _required_dense_grid, _validate_request_closure, verify_character_output,
)
from humanmotionlib.render_contract import read_supervised_receipt
from humanmotionlib.character_surface import _rest_frames


class CharacterVerificationTests(unittest.TestCase):
    def _write_generation_fixture(self,root):
        package=root/"installed"; files={
            "humanmotionlib/__init__.py":b"# frozen package\n",
            "humanmotionlib/resources/docs/guide.md":b"frozen documentation\n",
            "humanmotionlib/resources/backend-contract.json":b'{"format":"contract"}\n',
        }
        manifest={"format":"humanmotionlib-runtime-manifest/v1","version":"0.3.0",
            "resources":{"docs/guide.md":hashlib.sha256(files["humanmotionlib/resources/docs/guide.md"]).hexdigest()},
            "implementation":{"humanmotionlib/__init__.py":hashlib.sha256(files["humanmotionlib/__init__.py"]).hexdigest()},
            "backend_contract":hashlib.sha256(files["humanmotionlib/resources/backend-contract.json"]).hexdigest()}
        files["humanmotionlib/resources/runtime-manifest.json"]=(json.dumps(manifest,sort_keys=True,indent=2)+"\n").encode()
        wheel=root/"frozen.whl"
        with zipfile.ZipFile(wheel,"w") as archive:
            for name,data in files.items():archive.writestr(name,data)
        for name,data in files.items():
            target=package/name
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
        return wheel,package,hashlib.sha256(wheel.read_bytes()).hexdigest(),hashlib.sha256(
            files["humanmotionlib/resources/runtime-manifest.json"]).hexdigest()

    def test_generation_anchor_checks_frozen_wheel_manifest_and_installed_inventory(self):
        with tempfile.TemporaryDirectory(prefix="hml-generation-anchor-") as temporary:
            wheel,installed,wheel_sha,manifest_sha=self._write_generation_fixture(Path(temporary))
            anchor=_load_generation_anchor(wheel,installed,expected_wheel_sha256=wheel_sha,
                                           expected_runtime_manifest_sha256=manifest_sha)
            self.assertEqual(anchor.wheel_sha256,wheel_sha)
            self.assertEqual(anchor.runtime_manifest_sha256,manifest_sha)
            self.assertEqual(anchor.identity["package_version"],"0.3.0")
            (installed/"humanmotionlib/__init__.py").write_bytes(b"tampered\n")
            with self.assertRaisesRegex(ValueError,"installed generation bytes"):
                _load_generation_anchor(wheel,installed,expected_wheel_sha256=wheel_sha,
                                        expected_runtime_manifest_sha256=manifest_sha)

    def test_generation_anchor_rejects_unanchored_wheel_or_manifest_hash(self):
        with tempfile.TemporaryDirectory(prefix="hml-generation-anchor-hash-") as temporary:
            wheel,installed,wheel_sha,manifest_sha=self._write_generation_fixture(Path(temporary))
            with self.assertRaisesRegex(ValueError,"frozen wheel SHA"):
                _load_generation_anchor(wheel,installed,expected_wheel_sha256="0"*64,
                                        expected_runtime_manifest_sha256=manifest_sha)
            with self.assertRaisesRegex(ValueError,"frozen manifest SHA"):
                _load_generation_anchor(wheel,installed,expected_wheel_sha256=wheel_sha,
                                        expected_runtime_manifest_sha256="0"*64)

    def test_dense_grid_includes_events_and_never_exceeds_point_one_beat(self):
        prepared = {
            "samples": [{"fixture":"demo","beat":{"numerator":1,"denominator":3}}],
            "sources": {"diagnostics": [{"id":"demo","duration_beats":1.0,
                "tracks":[{"keys":[{"beat":0.25}]}],
                "contacts":[{"start_beat":0.2,"end_beat":0.8}]}]},
        }
        grid = _required_dense_grid(prepared)["demo"]
        self.assertIn(0.25, grid)
        self.assertIn(0.2, grid)
        self.assertIn(0.8, grid)
        self.assertTrue(any(abs(value-1/3)<1e-9 for value in grid))
        self.assertLessEqual(max(b-a for a,b in zip(grid,grid[1:])), 0.01+1e-10)

    def test_reference_field_equality_normalizes_json_array_container_shape(self):
        source={"vertices_m":((0.1,0.2,0.3),(0.4,0.5,0.6)),"faces":((0,1,2),)}
        decoded={"vertices_m":[[0.1,0.2,0.3],[0.4,0.5,0.6]],"faces":[[0,1,2]]}
        self.assertEqual(_json_shape(source),decoded)

    def test_component_extrema_aggregate_to_sample_floor_across_all_surfaces(self):
        components={"torso":_minimum_vertex_z([[0,0,0.4],[0,0,0.2]], ["t0","t1"]),
                    "foot.L":_minimum_vertex_z([[0,0,-1e-7],[0,0,0.1]], ["f0","f1"]),
                    "head":_minimum_vertex_z([[0,0,1.2]], ["h0"])}
        self.assertEqual(min(components.values()),(-1e-7,"f0"))
        self.assertEqual(_minimum_vertex_z([[0,0,0],[0,0,0]], ["later","earlier"]),(0,"later"))

    def test_native_sample_floor_id_is_recomputed_from_native_vertices_in_backend_order(self):
        from humanmotionlib.character_verification import _native_sample_floor_extremum
        components={"torso":{"vertices_m":[[0,0,0.2],[0,0,0.1]],"vertex_ids":["t0","t1"]},
                    "foot.L":{"vertices_m":[[0,0,0.1]],"vertex_ids":["f0"]}}
        self.assertEqual(_native_sample_floor_extremum(components,["torso","foot.L"]),(0.1,"t1"))
        self.assertEqual(_native_sample_floor_extremum(components,["foot.L","torso"]),(0.1,"f0"))
        self.assertEqual(_native_sample_floor_extremum(components,sorted(components)),(0.1,"f0"))

    def test_only_explicitly_anchored_missing_legacy_metric_marker_is_accepted(self):
        from humanmotionlib.character_verification import _canonical_reference_metric
        self.assertTrue(_canonical_reference_metric({"reference_metric":"canonical-double-world-dq/v1"},False))
        self.assertFalse(_canonical_reference_metric({},True))
        with self.assertRaises(ValueError):
            _canonical_reference_metric({},False)
        with self.assertRaises(ValueError):
            _canonical_reference_metric({"reference_metric":"unknown/v1"},True)

    def test_private_generation_context_allows_only_exact_reviewed_document_hash_pairs(self):
        from humanmotionlib.character_verification import _is_reviewed_generation_doc_delta
        self.assertTrue(_is_reviewed_generation_doc_delta(
            "docs/usage.md",
            "2e74f6e2ce27ec6c754cf087b4aeb8c259b56794f0c0e2ba2f870e9f0359db0f",
            "36b11bfa7b32839e9119e80ec00bbcb43565f5d7d2bb3fb6d8631df709b1b58c"))
        self.assertTrue(_is_reviewed_generation_doc_delta(
            "docs/character-models.md",
            "dd343ad079938b6fb193c5e2581df6ad8f94a501582dd65ff909b83d7d702cd1",
            "05123532782675a9ed30a43e56d87d9596447b2cfff16d4cbf8dcbd2d96ffb8c"))
        self.assertFalse(_is_reviewed_generation_doc_delta("docs/character-models.md", "0"*64,"1"*64))
        self.assertFalse(_is_reviewed_generation_doc_delta("docs/used-materials.md", "0"*64,"1"*64))

    def test_reference_residual_summary_uses_independent_world_measurement_and_bound(self):
        component={"maximum_source_world_residual_m":8.9e-8,
                   "maximum_native_local_residual_m":9.0e-8,
                   "maximum_reference_residual_m":9.0e-8,
                   "worst_reference_vertex_id":"v1"}
        self.assertTrue(_reference_residual_summary_matches(
            component,2.8e-7,"v2",["v1","v2"],1.5,canonical_metric=False))
        component.update({"maximum_source_world_residual_m":2.8e-7,
                          "maximum_native_local_residual_m":9.0e-8,
                          "maximum_reference_residual_m":2.8e-7,
                          "worst_reference_vertex_id":"v2",
                          "worst_native_local_vertex_id":"v1"})
        self.assertTrue(_reference_residual_summary_matches(
            component,2.8e-7,"v2",["v1","v2"],1.5,canonical_metric=True))
        component["worst_reference_vertex_id"]="v1"
        self.assertFalse(_reference_residual_summary_matches(
            component,2.8e-7,"v2",["v1","v2"],1.5,canonical_metric=True))
        component["maximum_native_local_residual_m"]=2e-5
        component["maximum_reference_residual_m"]=2e-5
        self.assertFalse(_reference_residual_summary_matches(
            component,2.8e-7,"v2",["v1","v2"],1.5,canonical_metric=False))

    def test_numeric_fixture_coverage_reports_unselected_source_diagnostics(self):
        prepared={"sources":{"diagnostics":[{"id":"neutral"},{"id":"squat"},{"id":"rocker"}]},
                  "samples":[{"fixture":"neutral"},{"fixture":"squat"}]}
        report=_fixture_coverage(prepared)
        self.assertEqual(report["status"],"incomplete")
        self.assertEqual(report["missing"],["rocker"])
        self.assertEqual(report["extra"],[])

    def test_sole_distance_uses_actual_triangle_surface(self):
        vertices = [(0,0,0),(1,0,0),(0,1,0)]
        self.assertAlmostEqual(_closest_mesh_distance((0.25,0.25,0.1),vertices,[(0,1,2)]),0.1)
        self.assertAlmostEqual(_closest_mesh_distance((2,0,0),vertices,[(0,1,2)]),1.0)

    def test_prepared_sample_failure_context_uses_authoritative_rational_beat(self):
        fixture, beat = _prepared_sample_context({"fixture":"walking-in-place",
            "beat":{"numerator":7,"denominator":12}})
        self.assertEqual(fixture,"walking-in-place")
        self.assertAlmostEqual(beat,7/12)
        self.assertEqual(_beat_label(beat),"0.5833333333")
        self.assertEqual(_prepared_sample_context({"fixture":"stale"}),("stale",None))

    def test_dense_contact_audit_measures_detached_sole_against_actual_triangles(self):
        profile = {"structures":[{"id":"pelvis","parent":None,"rest_translation_m":[0,0,0],
            "rest_orientation":[1,0,0,0],"origin_m":[0,0,0],"basis":[[1,0,0],[0,1,0],[0,0,1]],
            "attachments":[{"id":"contact.heel.R","position_m":[0.25,0.25,0]}]}]}
        _, rest = _rest_frames(profile,1.0)
        component = {"id":"foot.R","vertices_m":[[0,0,0.01],[1,0,0.01],[0,1,0.01]],
            "vertex_ids":["heel","toe","outer"],"faces":[[0,1,2]],
            "weights":[{"pelvis":1.0} for _ in range(3)]}
        sample = {"frames":{"pelvis":{"position_m":[0,0,0],
            "rotation":[[1,0,0],[0,1,0],[0,0,1]]}},
            "contacts":[{"anchors":["contact.heel.R"]}]}
        measured = _audit_surface_sample(profile,sample,[component],rest,1.0)
        self.assertFalse(measured["sole_pass"])
        self.assertAlmostEqual(measured["worst_sole_distance_m"],0.01)
        self.assertEqual(measured["worst_anchor_id"],"contact.heel.R")
        self.assertAlmostEqual(measured["worst_triangle_area_m2"],0.5)

    def test_dense_surface_audit_reports_detached_sole_with_authoritative_beat_and_bound(self):
        import yaml
        from humanmotionlib.character_surface import expand_surface
        from humanmotionlib.validate import load_sources

        root=Path(__file__).resolve().parents[1]
        sources,_=load_sources("adult-reference-v1",root=root)
        template=yaml.safe_load((root/"characters/templates/exercise-mannequin-v1.yaml").read_text())
        surfaces={}
        for identifier in ("male","female"):
            appearance=yaml.safe_load((root/f"characters/appearances/{identifier}-v1.yaml").read_text())
            components=expand_surface(sources["profile"],template,appearance,1.7)["components"]
            for component in components:
                if component["id"].startswith("foot."):
                    component["vertices_m"]=[[vertex[0],vertex[1],vertex[2]+0.01]
                                              for vertex in component["vertices_m"]]
            surfaces[identifier]=components
        prepared={"samples":[{"fixture":"walking-in-place","beat":{"numerator":0,"denominator":1}}],
                  "sources":sources}
        report=_run_dense_surface_audit(prepared,surfaces,1.7,{"walking-in-place":[0.5]})
        failures=[row for row in report["failures"] if row["code"]=="dense-sole-contact"]
        self.assertTrue(failures)
        for failure in failures:
            self.assertIn(failure["character_id"],("male","female"))
            self.assertEqual(failure["fixture"],"walking-in-place")
            self.assertEqual(failure["beat"],0.5)
            self.assertTrue(failure["anchor_id"])
            self.assertGreater(failure["measured_m"],failure["allowed_m"])

    def test_dense_reference_checks_floor_and_degenerate_faces_from_solved_frames(self):
        profile = {"structures":[{"id":"pelvis","parent":None,"rest_translation_m":[0,0,0],
            "rest_orientation":[1,0,0,0],"origin_m":[0,0,0],"basis":[[1,0,0],[0,1,0],[0,0,1]],
            "attachments":[]}]}
        _, rest = _rest_frames(profile,1.0)
        component = {"id":"foot.R","vertices_m":[[0,0,0],[1,0,0],[0,1,0]],
                     "vertex_ids":["v0","v1","v2"],"faces":[[0,1,2]],
                     "weights":[{"pelvis":1.0} for _ in range(3)]}
        sample = {"frames":{"pelvis":{"position_m":[0,0,0],
                    "rotation":[[1,0,0],[0,1,0],[0,0,1]]}},"contacts":[]}
        okay = _audit_surface_sample(profile,sample,[component],rest,1.0)
        self.assertTrue(okay["floor_pass"])
        self.assertTrue(okay["triangle_areas_pass"])
        penetrating = {**component,"vertices_m":[[0,0,-0.001],[1,0,0],[0,1,0]]}
        bad_floor = _audit_surface_sample(profile,sample,[penetrating],rest,1.0)
        self.assertFalse(bad_floor["floor_pass"])
        degenerate = {**component,"vertices_m":[[0,0,0],[1,0,0],[2,0,0]]}
        bad_area = _audit_surface_sample(profile,sample,[degenerate],rest,1.0)
        self.assertFalse(bad_area["triangle_areas_pass"])

    def test_cached_affine_blends_match_per_vertex_dual_quaternion_kernel(self):
        profile={"structures":[{"id":"pelvis","parent":None,"rest_translation_m":[0,0,0],
            "rest_orientation":[1,0,0,0],"origin_m":[0,0,0],"basis":[[1,0,0],[0,1,0],[0,0,1]],
            "attachments":[]}]}
        _,rest=_rest_frames(profile,1.0)
        rotation=[[0,-1,0],[1,0,0],[0,0,1]]
        frames={"pelvis":{"position_m":[2,3,4],"rotation":rotation}}
        component={"id":"test","vertices_m":[[1,0,0],[0,1,0]],
                   "vertex_ids":["a","b"],"faces":[],"weights":[{"pelvis":1.0},{"pelvis":1.0}]}
        result=_surface_poses(profile,frames,[component],rest)[0]["vertices_m"]
        for actual,expected in zip(result,((2.0,4.0,4.0),(1.0,3.0,4.0))):
            for left,right in zip(actual,expected):self.assertAlmostEqual(left,right,delta=1e-12)

    def test_native_midpoint_grid_is_limited_to_prepared_fixture_membership(self):
        prepared={"samples":[{"fixture":"arm-raise","beat":{"numerator":0,"denominator":1}}],
                  "sources":{"diagnostics":[
                      {"id":"arm-raise","tracks":[{"keys":[{"beat":0},{"beat":1},{"beat":2}]}]},
                      {"id":"squat","tracks":[{"keys":[{"beat":0},{"beat":1}]}]}]}}
        self.assertEqual(_native_midpoint_beats(prepared),{"arm-raise":[0.5,1.5]})

    def test_native_midpoint_evidence_must_cover_every_required_action_midpoint(self):
        prepared={"samples":[{"fixture":"arm-raise","beat":{"numerator":0,"denominator":1}}],
                  "sources":{"profile":{"structures":[{"id":"pelvis","parent":None,
                      "rest_translation_m":[0,0,0],"rest_orientation":[1,0,0,0]}]},
                      "mobility":{},"body-groups":{},"diagnostics":[{"id":"arm-raise",
                          "tracks":[{"keys":[{"beat":0},{"beat":1}]}]}]}}
        with patch("humanmotionlib.diagnostics.DiagnosticEvaluator"):
            report=_verify_native_midpoints(prepared,{"male":{"dense_samples":[]}},
                                             {"male":[]},1.7)
        self.assertEqual(report["status"],"fail")
        failures=report["failures"]
        membership=next(item for item in failures if item["code"]=="native-midpoint-membership")
        self.assertEqual(membership["missing"],[["arm-raise",0.5]])

    def test_native_midpoint_missing_vertex_reports_character_fixture_beat_and_inventory(self):
        import yaml
        from humanmotionlib.character_surface import expand_surface
        from humanmotionlib.diagnostics import DiagnosticEvaluator
        from humanmotionlib.validate import load_sources

        root=Path(__file__).resolve().parents[1]
        sources,_=load_sources("adult-reference-v1",root=root)
        template=yaml.safe_load((root/"characters/templates/exercise-mannequin-v1.yaml").read_text())
        appearance=yaml.safe_load((root/"characters/appearances/male-v1.yaml").read_text())
        components=expand_surface(sources["profile"],template,appearance,1.7)["components"]
        evaluator=DiagnosticEvaluator(sources)
        solved=evaluator.evaluate("arm-raise",0.5)
        _,rest=_rest_frames(sources["profile"],1.0)
        posed=_surface_poses(sources["profile"],solved["frames"],components,rest)
        actual=[]
        for component in posed:
            minimum=min((vertex[2],index) for index,vertex in enumerate(component["vertices_m"]))
            vertex_ids=list(component["vertex_ids"])
            if component["id"]==posed[0]["id"]:
                vertex_ids[0]="forged/missing-vertex"
            actual.append({"id":component["id"],"vertices_m":component["vertices_m"],
                "vertex_ids":vertex_ids,"minimum_z_m":minimum[0],
                "worst_floor_vertex_id":vertex_ids[minimum[1]]})
        anchors=_dense_contact_points(sources["profile"],solved["frames"],solved["contacts"])
        by_id={row["id"]:row for row in actual}
        component_by_id={row["id"]:row for row in posed}
        contacts=[]
        for anchor_id,anchor in anchors.items():
            side=anchor_id.rsplit(".",1)[-1]
            foot=by_id["foot."+side]
            distance=_closest_mesh_distance(anchor,foot["vertices_m"],component_by_id["foot."+side]["faces"])
            contacts.append({"anchor_id":anchor_id,"anchor_m":list(anchor),
                             "closest_sole_distance_m":distance})
        minimum=min((vertex[2],identifier) for row in actual for vertex,identifier in
            zip(row["vertices_m"],row["vertex_ids"]))
        prepared={"samples":[{"id":"arm-raise/00000","fixture":"arm-raise",
            "beat":{"numerator":0,"denominator":1}}],"sources":sources}
        report=_verify_native_midpoints(prepared,{"male":{"dense_samples":[{
            "fixture":"arm-raise","beat":0.5,"components":actual,"contacts":contacts,
            "minimum_z_m":minimum[0],"worst_floor_vertex_id":minimum[1]}]}},
            {"male":components},1.7)
        failure=next(row for row in report["failures"] if row["code"]=="native-midpoint-topology")
        self.assertEqual(failure["character_id"],"male")
        self.assertEqual(failure["fixture"],"arm-raise")
        self.assertEqual(failure["beat"],0.5)
        self.assertEqual(failure["sample_id"],"arm-raise@0.5")
        self.assertEqual(failure["component_id"],posed[0]["id"])
        self.assertEqual(failure["observed_vertex_count"],failure["expected_vertex_count"])
        self.assertTrue(failure["missing_vertex_ids"])

    def test_request_source_closure_is_verified_against_packaged_bytes(self):
        ids=["skeleton","male","female"]
        request={"package_identity":{"version":"test"},"backend_contract":{"version":1},
                 "character_descriptors":[{"id":identifier,"source_hashes":
                    ({"characters/registry.yaml":"good"} if identifier=="skeleton" else {})}
                    for identifier in ids], "characters":[]}
        prepared={"package_identity":{"version":"test"}}
        with patch("humanmotionlib.runtime.backend_contract",return_value={"version":1}), \
             patch("humanmotionlib.package_resources.read_bytes",return_value=b"source"):
            import hashlib
            request["character_descriptors"][0]["source_hashes"]["characters/registry.yaml"] = hashlib.sha256(b"source").hexdigest()
            _validate_request_closure(request,prepared,ids)
            request["character_descriptors"][0]["source_hashes"]["characters/registry.yaml"]="0"*64
            with self.assertRaisesRegex(ValueError,"source closure hash mismatch"):
                _validate_request_closure(request,prepared,ids)

    def test_missing_seal_and_registry_membership_fail_closed(self):
        sample = {"id":"neutral/00000","fixture":"neutral",
                  "beat":{"numerator":0,"denominator":1}}
        prepared = {"content_sha256":"prepared-test","samples":[sample],
                    "sources":{"profile":{"id":"adult-reference-v1","stature_m":1.7},
                               "diagnostics":[{"id":"neutral","duration_beats":1}]}}
        with tempfile.TemporaryDirectory(prefix="hml-verifier-invalid-") as temporary:
            run = Path(temporary)
            (run/"character-render-request.json").write_text(json.dumps({"format":"wrong"}))
            (run/"render-manifest.json").write_text(json.dumps({"format":"wrong"}))
            report = verify_character_output(prepared,run,("skeleton","male","female"))
        self.assertEqual(report["status"],"fail")
        self.assertTrue(report["failures"])
        self.assertEqual(report["stature"]["observed_m"],1.7)
        self.assertEqual(report["stature"]["missing_m"],[1.5,1.9])

    def test_numeric_only_is_explicit_and_does_not_require_a_render_manifest(self):
        sample={"id":"neutral/00000","fixture":"neutral",
                "beat":{"numerator":0,"denominator":1}}
        prepared={"content_sha256":"prepared-test","package_identity":{},"samples":[sample],
                  "sources":{"profile":{"id":"adult-reference-v1","stature_m":1.7},
                             "diagnostics":[{"id":"neutral","duration_beats":1}]}}
        with tempfile.TemporaryDirectory(prefix="hml-verifier-numeric-only-") as temporary:
            run=Path(temporary)
            from humanmotionlib.runtime import backend_contract
            ids=["skeleton","male","female"]
            request={"format":"character-render-request/v1","prepared_sha256":"prepared-test",
                "package_identity":{},"backend_contract":backend_contract(),"character_ids":ids,
                "character_descriptors":[{"id":identifier,"source_hashes":{}} for identifier in ids],
                "characters":[{"id":identifier,"source_hashes":{}} for identifier in ids[1:]],
                "surface_identities":{}}
            request["render_identity"]=_content_hash(request)
            (run/"character-render-request.json").write_text(json.dumps(request))
            report=verify_character_output(prepared,run,("skeleton","male","female"),numeric_only=True)
        codes={failure["code"] for failure in report["failures"]}
        self.assertEqual(report["mode"],"numeric-only")
        self.assertEqual(report["rendering"],"not-run")
        self.assertEqual(report["visual"],"not-assessed")
        self.assertNotIn("manifest-format",codes)
        self.assertIn("evidence-invalid",codes)
        self.assertIn("supervised build receipt",report["failures"][-1]["detail"])
        self.assertEqual(report["status"],"fail")

    def test_build_receipt_is_selected_only_for_explicit_numeric_operation(self):
        with tempfile.TemporaryDirectory(prefix="hml-receipt-operation-") as temporary:
            run=Path(temporary)
            process=run/"processes"/"one";process.mkdir(parents=True)
            (process/"outcome.json").write_text(json.dumps({"operation":"render-pass"}))
            with self.assertRaisesRegex(ValueError,"supervised build receipt"):
                read_supervised_receipt(run,{},[],expected_operation="build")

    def test_stale_self_sealed_request_is_not_accepted_as_prepared_identity(self):
        sample={"id":"neutral/00000","fixture":"neutral","beat":{"numerator":0,"denominator":1}}
        prepared={"content_sha256":"prepared-test","samples":[sample],
                  "sources":{"profile":{"id":"adult-reference-v1","stature_m":1.7},
                             "diagnostics":[{"id":"neutral","duration_beats":1}]}}
        with tempfile.TemporaryDirectory(prefix="hml-verifier-stale-") as temporary:
            run=Path(temporary)
            request={"format":"character-render-request/v1","prepared_sha256":"different-prepared",
                     "character_ids":["skeleton","male","female"],"character_descriptors":[],
                     "characters":[],"surface_identities":{}}
            request["render_identity"]=_content_hash(request)
            (run/"character-render-request.json").write_text(json.dumps(request),encoding="utf-8")
            (run/"render-manifest.json").write_text(json.dumps({"format":"character-render-manifest/v1",
                "prepared_sha256":"different-prepared","render_identity":request["render_identity"],
                "characters":[]}),encoding="utf-8")
            report=verify_character_output(prepared,run,("skeleton","male","female"))
        self.assertEqual(report["status"],"fail")
        stale=next(failure for failure in report["failures"] if failure["code"]=="stale-request")
        self.assertIn("artifact=character-render-request.json",stale["detail"])
        self.assertIn("field=prepared_sha256",stale["detail"])
        self.assertIn("expected_sha256=prepared-test",stale["detail"])
        self.assertIn("observed_sha256=different-prepared",stale["detail"])
        self.assertIn("beat=not-applicable",stale["detail"])

    def test_full_verifier_reports_delivered_fault_context_with_coherent_receipts(self):
        """Exercise delivered-sample failures through the complete read-only verifier."""
        from humanmotionlib import api
        from humanmotionlib.character_skinning import compile_pose_skinning, source_world_transforms
        from humanmotionlib.characters import expand_surface
        from humanmotionlib.package_resources import manifest_sha256, verify_runtime_integrity
        from humanmotionlib.prepared import seal, write_json
        from humanmotionlib.prepare_skeleton import prepare as prepare_skeleton
        from humanmotionlib.runtime import backend_contract
        from tests.run_roots import test_case_root

        base=test_case_root("character-verification","delivered-fault-context")
        generated=prepare_skeleton("adult-reference-v1",1.7,("walking-in-place",),(180,))
        prepared_base=seal({**generated,"samples":[deepcopy(generated["samples"][0])]})
        ids=("skeleton","male","female")
        _,rest=_rest_frames(prepared_base["sources"]["profile"],1.0)
        package=verify_runtime_integrity()

        def run_case(name,fault,selected_character_id=None):
            case=base/name
            output=case/"output"
            output.mkdir(parents=True)
            prepared=deepcopy(prepared_base)
            if fault=="floor":
                for frame in prepared["samples"][0]["frames"].values():
                    frame["position_m"][2]-=0.001
            elif fault=="detached-sole":
                prepared["samples"][0]["frames"]["calcaneus.R"]["position_m"][2]+=0.02
            prepared=seal(prepared)
            prepared_result=SimpleNamespace(profile_id="adult-reference-v1",stature_m=1.7)
            request,selected_ids,selected=api._build_render_request(
                prepared,prepared_result,([selected_character_id] if selected_character_id else ids),render_only=False)
            write_json(output/"input.json",prepared)
            write_json(output/"character-render-request.json",request)
            write_json(output/"build-metadata.json",{
                "format":"synthetic-character-evidence/v1","character_ids":list(selected_ids),
                "render_identity":request["render_identity"]})
            (output/"skeleton.blend").write_bytes(b"synthetic fixture; verifier does not inspect Blender scene")
            write_json(output/"evaluated.json",{"format":"skeleton-evaluated/v1",
                "prepared_sha256":prepared["content_sha256"],
                "samples":prepared["samples"] if selected_character_id == "skeleton" else [],
                "metadata":{"blender_version":"fixture", "blender_build":"fixture"}})
            write_json(output/"geometry-reference.json",{"format":"skeleton-evaluated-geometry/v1",
                "prepared_sha256":prepared["content_sha256"],"geometry":{}})

            surfaces={}
            for character in selected:
                if character["renderer_kind"]=="skinned-surface":
                    surfaces[character["id"]]=expand_surface(
                        prepared["sources"]["profile"],character["template"],
                        character["appearance"],1.7)["components"]
            sample=prepared["samples"][0]
            expected_anchors=_expected_anchor_positions(prepared["sources"]["profile"],sample)
            for character_id,components in surfaces.items():
                character_root=output/"characters"/character_id
                character_root.mkdir(parents=True)
                reference_components=[]
                for component in components:
                    vertex_id=component["vertex_ids"][0] if component["vertex_ids"] else None
                    reference_components.append({**component,
                        "native_rest_vertices_m":component["vertices_m"],
                        "maximum_rest_residual_m":0.0,"worst_rest_vertex_id":vertex_id})
                write_json(character_root/"surface-reference.json",{
                    "format":"hml-surface-reference/v1","prepared_sha256":prepared["content_sha256"],
                    "render_identity":request["render_identity"],"character_id":character_id,
                    "profile_id":prepared["sources"]["profile"]["id"],"stature_m":1.7,
                    "surface_sha256":request["surface_identities"][character_id],
                    "template_id":next(row["template"]["id"] for row in request["characters"] if row["id"]==character_id),
                    "appearance_id":next(row["appearance"]["id"] for row in request["characters"] if row["id"]==character_id),
                    "components":reference_components})

                weight_set,offsets,carriers=_compiled_surface_weight_layout({character_id:components})
                transforms=source_world_transforms(prepared["sources"]["profile"],sample["frames"],carriers,
                                                   rest_frames=rest)
                compiled=compile_pose_skinning(transforms,weight_set)
                posed=_surface_poses(prepared["sources"]["profile"],sample["frames"],components,rest,
                    compiled_pose=compiled,component_offsets=offsets)
                actual_components=[]
                for component in posed:
                    minimum=min((vertex[2],index) for index,vertex in enumerate(component["vertices_m"]))
                    first_id=component["vertex_ids"][0] if component["vertex_ids"] else None
                    vertex_ids=list(component["vertex_ids"])
                    if fault=="missing-vertex" and character_id=="male" and component is posed[0]:
                        vertex_ids[0]="forged/missing-vertex"
                    actual_components.append({"id":component["id"],"vertices_m":component["vertices_m"],
                        "vertex_ids":vertex_ids,"minimum_z_m":minimum[0],
                        "worst_floor_vertex_id":vertex_ids[minimum[1]],
                        "maximum_source_world_residual_m":0.0,
                        "maximum_native_local_residual_m":0.0,
                        "maximum_reference_residual_m":0.0,
                        "worst_reference_vertex_id":first_id,
                        "worst_native_local_vertex_id":first_id})
                posed_by_id={row["id"]:row for row in posed}
                contacts=[]
                for anchor_id,anchor in expected_anchors.items():
                    side=anchor_id.rsplit(".",1)[-1]
                    distance=_closest_mesh_distance(anchor,posed_by_id["foot."+side]["vertices_m"],
                        next(row["faces"] for row in components if row["id"]=="foot."+side))
                    reported=distance+0.01 if fault=="forged-sole-summary" and character_id=="male" else distance
                    contacts.append({"anchor_id":anchor_id,"anchor_m":list(anchor),
                        "closest_sole_distance_m":reported})
                minimum=(math.inf,None)
                for component in actual_components:
                    item=_minimum_vertex_z(component["vertices_m"],component["vertex_ids"])
                    if item[0]<minimum[0]:minimum=item
                evaluated={"format":"hml-surface-evaluated/v1",
                    "prepared_sha256":"stale-prepared" if fault=="stale-evidence" and character_id=="male"
                        else prepared["content_sha256"],
                    "render_identity":request["render_identity"],"character_id":character_id,
                    "reference_metric":"canonical-double-world-dq/v1",
                    "samples":[{"sample_id":sample["id"],"fixture":sample["fixture"],
                        "beat":sample["beat"],"components":actual_components,"contacts":contacts,
                        "minimum_z_m":minimum[0],"worst_floor_vertex_id":minimum[1]}],
                    "dense_samples":[]}
                write_json(character_root/"surface-evaluated.json",evaluated)

            required=["input.json","build-metadata.json","skeleton.blend","character-render-request.json",
                      "evaluated.json","geometry-reference.json"]
            for character_id in selected_ids:
                if character_id == "skeleton":
                    continue
                required.extend((f"characters/{character_id}/surface-reference.json",
                                 f"characters/{character_id}/surface-evaluated.json"))
            files=[]
            for relative in required:
                path=output/relative
                files.append({"path":str(path.resolve()),"size_bytes":path.stat().st_size,
                    "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
            process=output/"processes"/"synthetic";process.mkdir(parents=True)
            receipt={"operation":"build","package_version":package["version"],
                "runtime_manifest_sha256":manifest_sha256(),"resource_hashes":package["resources"],
                "backend_contract_sha256":package["backend_contract"],
                "implementation_hashes":package["implementation"],"state":"succeeded",
                "outcome":"exit","return_code":0,"source_sha256":prepared["content_sha256"],
                "last_script_phase":"script_complete","phases":[
                    {"phase":"input_loaded","prepared_sha256":prepared["content_sha256"]},
                    {"phase":"backend_ready","render_identity":request["render_identity"],
                     "character_ids":list(selected_ids)},
                    {"phase":"script_complete","prepared_sha256":prepared["content_sha256"],
                     "render_identity":request["render_identity"],"character_ids":list(selected_ids)}],
                "output_validation":{"status":"pass","files":files}}
            write_json(process/"outcome.json",receipt)
            return verify_character_output(prepared,output,ids,(1.7,),numeric_only=True,
                selected_character_id=selected_character_id)

        cases=("floor","detached-sole","forged-sole-summary","missing-vertex","stale-evidence")
        reports={name:run_case(name,name) for name in cases}
        floor=next(row for row in reports["floor"]["failures"] if row["code"]=="floor-bound")
        self.assertIn("character=male",floor["detail"])
        self.assertIn("fixture=walking-in-place",floor["detail"])
        self.assertIn("beat=0",floor["detail"])
        self.assertIn("vertex=",floor["detail"])
        self.assertIn("minimum_z_m=",floor["detail"])
        self.assertIn("allowed_z_m=",floor["detail"])
        sole=next(row for row in reports["detached-sole"]["failures"] if row["code"]=="sole-contact")
        self.assertIn("character=male",sole["detail"])
        self.assertIn("fixture=walking-in-place",sole["detail"])
        self.assertIn("beat=0",sole["detail"])
        self.assertIn("anchor=contact.heel.R",sole["detail"])
        self.assertIn("anchor_to_sole_distance_m=",sole["detail"])
        self.assertIn("allowed_m=",sole["detail"])
        forged=next(row for row in reports["forged-sole-summary"]["failures"]
                    if row["code"]=="surface-evidence")
        self.assertIn("reported sole distance mismatch",forged["detail"])
        self.assertIn("reported_distance_m=",forged["detail"])
        self.assertIn("recomputed_distance_m=",forged["detail"])
        missing=next(row for row in reports["missing-vertex"]["failures"]
                     if row["code"]=="surface-evidence")
        self.assertIn("at beat=0",missing["detail"])
        self.assertIn("component=",missing["detail"])
        self.assertIn("missing_ids=",missing["detail"])
        stale=next(row for row in reports["stale-evidence"]["failures"]
                   if row["code"]=="surface-evidence")
        self.assertIn("artifact=characters/male/surface-evaluated.json",stale["detail"])
        self.assertIn("prepared_sha256(expected=",stale["detail"])
        self.assertIn("observed=stale-prepared",stale["detail"])
        self.assertIn("beat=not-applicable",stale["detail"])
if __name__ == "__main__":
    unittest.main()
