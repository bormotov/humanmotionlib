# SPDX-License-Identifier: Apache-2.0
"""Contract, resolver and host API checks for consumer-authored motion."""

from __future__ import annotations

from copy import deepcopy
import json
import inspect
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from humanmotionlib import __version__
from humanmotionlib.api import GenerationError, prepare
import humanmotionlib.api as api
from humanmotionlib.consumer_motion import (load_consumer_document,
                                            resolve_consumer_document)
from humanmotionlib.package_resources import verify_runtime_integrity
from humanmotionlib.prepared import (content_hash, read_prepared,
                                    read_prepared_backend, seal, write_json)
from humanmotionlib.source_validation import (SourceValidationError,
                                               schema_validator,
                                               validate_document)
from humanmotionlib.validate import load_sources, validate_sources


def complete_source():
    return {
        "format": "hml-consumer-motion/v1", "materials": [],
        "motion": {
            "schema_version": 1, "kind": "skeleton-diagnostic",
            "format": "skeleton-diagnostic/v1", "id": "consumer-arm-sweep",
            "description": "Authored two-beat arm elevation used by a contract test.",
            "license": "CC-BY-4.0",
            "provenance": {"kind": "authored", "license": "CC-BY-4.0",
                           "sources": [], "rationale": "Original test input.",
                           "changes": "No external source was adapted."},
            "profile": "adult-reference-v1", "duration_beats": 2,
            "controls": ["arm_L"],
            "rest_policy": {"policy": "base", "base_fixture": "neutral"},
            "tracks": [{"channel": "shoulder.L.elevation", "easing": "linear",
                        "keys": [{"beat": 0, "value": 0},
                                 {"beat": 1, "value": 10},
                                 {"beat": 2, "value": 0}]}],
            "construction": {"type": "action_sweep", "side": "L",
                             "start_beat": 0, "end_beat": 2,
                             "reference_knots": []},
            "world_root": {"mode": "identity", "translation_m": [0, 0, 0],
                           "orientation": [1, 0, 0, 0], "clearance_h": 0},
            "contacts": [],
            "terminal_contacts": [{"foot": "L", "state": "none"},
                                  {"foot": "R", "state": "none"}],
            "procedural": {"noise": False, "follow_through": False},
        },
    }


def variant_source():
    return {
        "format": "hml-consumer-motion/v1", "materials": [],
        "motion": {
            "schema_version": 1, "kind": "skeleton-motion-variant",
            "format": "skeleton-motion-variant/v1", "id": "scaled-squat-test",
            "description": "Scaled packaged squat for contract testing.",
            "profile": "adult-reference-v1", "license": "CC-BY-4.0",
            "provenance": {"kind": "authored", "license": "CC-BY-4.0",
                           "sources": [], "rationale": "Original parameterized test.",
                           "changes": "Scales bilateral squat movement tracks."},
            "base_fixture": "squat",
            "track_scales": {"knee.L.flexion": 0.5, "knee.R.flexion": 0.5},
            "track_overrides": [],
        },
    }


class ConsumerMotionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        (self.workspace / "build").mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_installed_resources_and_schemas_are_integrity_checked(self):
        manifest = verify_runtime_integrity()
        self.assertIn("schema/consumer-motion.schema.json", manifest["resources"])
        schema_validator("consumer-motion")
        schema_validator("consumer-motion-snapshot")
        document = complete_source()
        validate_document(document, "consumer-motion")
        with self.assertRaises(SourceValidationError):
            validate_document(document | {"unexpected": 1}, "consumer-motion")
        malformed = deepcopy(document)
        malformed["motion"]["tracks"][0]["keys"][0]["value"] = True
        with self.assertRaises(SourceValidationError):
            validate_document(malformed, "consumer-motion")
        for change in (
            lambda data: data.update(format="hml-consumer-motion/v2"),
            lambda data: data["motion"].update(unrecognized=True),
            lambda data: data["motion"]["tracks"][0]["keys"][0].update(value=float("inf")),
        ):
            malformed = deepcopy(document)
            change(malformed)
            with self.assertRaises(SourceValidationError):
                validate_document(malformed, "consumer-motion")
        unsupported = self.workspace / "unsupported.json"
        unsupported.write_text('{"format":"x","format":"y"}', encoding="utf-8")
        with self.assertRaises(SourceValidationError):
            load_consumer_document(unsupported, self.workspace,
                                   self.workspace / "build" / "support-consumer-authored-motions_r1_test_try-1_prepare")

    def test_json_yaml_and_mapping_inputs_are_detached_and_duplicate_safe(self):
        value = complete_source()
        original = deepcopy(value)
        json_path = self.workspace / "motion.json"
        yaml_path = self.workspace / "motion.yaml"
        json_path.write_text(json.dumps(value), encoding="utf-8")
        import yaml
        yaml_path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
        run = self.workspace / "build" / "support-consumer-authored-motions_r1_test_try-1_prepare"
        mapped = load_consumer_document(value, self.workspace, run)
        from_json = load_consumer_document(json_path, self.workspace, run)
        from_yaml = load_consumer_document(yaml_path, self.workspace, run)
        self.assertEqual(mapped, from_json)
        self.assertEqual(mapped, from_yaml)
        self.assertEqual(value, original)
        recursive = {}
        recursive["self"] = recursive
        with self.assertRaises(SourceValidationError):
            load_consumer_document(recursive, self.workspace, run)
        class ObjectWithItems:
            def items(self):
                return [("format", "hml-consumer-motion/v1")]
        with self.assertRaises(SourceValidationError):
            load_consumer_document(ObjectWithItems(), self.workspace, run)
        duplicate = self.workspace / "duplicate.yaml"
        duplicate.write_text("format: x\nformat: y\n", encoding="utf-8")
        with self.assertRaises(SourceValidationError):
            load_consumer_document(duplicate, self.workspace, run)
        relative = load_consumer_document("motion.json", self.workspace, run)
        self.assertEqual(relative, mapped)
        output_run = self.workspace / "build" / "support-consumer-authored-motions_r1_test_try-2_prepare"
        output_run.mkdir()
        nested = output_run / "inside.yaml"
        nested.write_text(yaml.safe_dump(value), encoding="utf-8")
        with self.assertRaises(SourceValidationError):
            load_consumer_document(nested, self.workspace, output_run)

    def test_parse_failures_include_source_and_root_field_details(self):
        cases = (
            ("duplicate.yaml", "format: first\nformat: second\n"),
            ("malformed.yaml", "format: [\n"),
            ("duplicate.json", '{"format":"first","format":"second"}'),
            ("malformed.json", '{"format":'),
        )
        for attempt, (name, contents) in enumerate(cases, start=1):
            with self.subTest(name=name):
                source_path = self.workspace / name
                source_path.write_text(contents, encoding="utf-8")
                output = (f"build/support-consumer-authored-motions_r1_test_try-{attempt}"
                          "_parse-error/input.json")
                with self.assertRaises(GenerationError) as captured:
                    prepare(workspace=self.workspace, output=output,
                            motion=source_path, bpms=(90,))
                error = captured.exception
                self.assertEqual(error.code, "source-validation")
                self.assertEqual(error.details.get("source_id"), str(source_path.resolve()))
                self.assertEqual(error.details.get("field"), "$")
                self.assertTrue(error.details.get("message"))
                self.assertFalse((self.workspace / output).parent.exists())

    def test_variant_scales_only_selected_keys_and_preserves_base(self):
        profile = "adult-reference-v1"
        validation = validate_sources(profile)
        sources, _ = load_sources(profile)
        before = deepcopy(sources)
        result = resolve_consumer_document(variant_source(), profile, sources,
                                           validation["source_hashes"],
                                           stature_m=sources["profile"]["stature_m"],
                                           bpms=(90,))
        base = next(row for row in sources["diagnostics"] if row["id"] == "squat")
        resolved = result["resolved"]
        for channel in ("knee.L.flexion", "knee.R.flexion"):
            original = next(row for row in base["tracks"] if row["channel"] == channel)
            scaled = next(row for row in resolved["tracks"] if row["channel"] == channel)
            self.assertEqual([key["beat"] for key in original["keys"]],
                             [key["beat"] for key in scaled["keys"]])
            self.assertEqual([key["value"] * 0.5 for key in original["keys"]],
                             [key["value"] for key in scaled["keys"]])
            self.assertEqual(original["easing"], scaled["easing"])
        self.assertIn({"id": "squat", "logical_path": "rig/diagnostics/squat.yaml",
                       "raw_sha256": validation["source_hashes"]["rig/diagnostics/squat.yaml"]},
                      result["snapshot"]["base_lineage"])
        self.assertEqual(result["snapshot"]["resolved_sha256"],
                         content_hash(result["resolved"]))
        self.assertEqual(sources, before)
        replacement = variant_source()
        base_track = deepcopy(next(row for row in base["tracks"]
                                   if row["channel"] == "knee.L.flexion"))
        base_track["keys"][0]["value"] = 0
        replacement["motion"]["track_scales"] = {}
        replacement["motion"]["track_overrides"] = [base_track]
        replaced = resolve_consumer_document(replacement, profile, sources,
                                             validation["source_hashes"],
                                             stature_m=sources["profile"]["stature_m"],
                                             bpms=(90,))["resolved"]
        self.assertEqual(next(row for row in replaced["tracks"]
                              if row["channel"] == "knee.L.flexion"), base_track)
        self.assertEqual(len(replaced["tracks"]), len(base["tracks"]))
        conflict = variant_source()
        conflict["motion"]["track_overrides"] = [deepcopy(base_track)]
        with self.assertRaises(SourceValidationError):
            resolve_consumer_document(conflict, profile, sources,
                                      validation["source_hashes"],
                                      stature_m=sources["profile"]["stature_m"], bpms=(90,))
        duplicate = variant_source()
        duplicate["motion"]["track_scales"] = {}
        duplicate["motion"]["track_overrides"] = [deepcopy(base_track), deepcopy(base_track)]
        with self.assertRaises(SourceValidationError):
            resolve_consumer_document(duplicate, profile, sources,
                                      validation["source_hashes"],
                                      stature_m=sources["profile"]["stature_m"], bpms=(90,))
        bad = variant_source()
        bad["motion"]["track_scales"]["unknown.flexion"] = 0.5
        with self.assertRaises(SourceValidationError):
            resolve_consumer_document(bad, profile, sources,
                                      validation["source_hashes"],
                                      stature_m=sources["profile"]["stature_m"], bpms=(90,))

    def test_profile_semantics_and_provenance_closure_fail_before_output(self):
        profile = "adult-reference-v1"
        validation = validate_sources(profile)
        sources, _ = load_sources(profile)
        wrong_profile = complete_source()
        wrong_profile["motion"]["profile"] = "other-profile"
        with self.assertRaisesRegex(SourceValidationError, "consumer-arm-sweep profile"):
            resolve_consumer_document(wrong_profile, profile, sources,
                                      validation["source_hashes"],
                                      stature_m=sources["profile"]["stature_m"], bpms=(90,))
        unresolved = complete_source()
        unresolved["motion"]["provenance"]["kind"] = "adapted"
        unresolved["motion"]["provenance"]["sources"] = [
            {"material": "unregistered-material", "locator": "chapter 1"}]
        with self.assertRaisesRegex(SourceValidationError, "unresolved material"):
            resolve_consumer_document(unresolved, profile, sources,
                                      validation["source_hashes"],
                                      stature_m=sources["profile"]["stature_m"], bpms=(90,))
        adapted_empty = complete_source()
        adapted_empty["motion"]["provenance"]["kind"] = "adapted"
        with self.assertRaisesRegex(SourceValidationError, "adapted contribution requires a source"):
            resolve_consumer_document(adapted_empty, profile, sources,
                                      validation["source_hashes"],
                                      stature_m=sources["profile"]["stature_m"], bpms=(90,))

    def test_semantic_faults_name_the_consumer_and_field(self):
        profile = "adult-reference-v1"
        validation = validate_sources(profile)
        sources, _ = load_sources(profile)
        cases = []
        collision = complete_source()
        collision["motion"]["id"] = "squat"
        cases.append((collision, "squat id"))
        unknown_base = complete_source()
        unknown_base["motion"]["rest_policy"]["base_fixture"] = "missing"
        cases.append((unknown_base, "consumer-arm-sweep rest_policy.base_fixture"))
        hold = complete_source()
        hold["motion"]["rest_policy"]["policy"] = "hold"
        cases.append((hold, "consumer-arm-sweep rest_policy.policy"))
        unknown_channel = complete_source()
        unknown_channel["motion"]["tracks"][0]["channel"] = "made.up.channel"
        cases.append((unknown_channel, "consumer-arm-sweep tracks[0].channel"))
        dependent = complete_source()
        dependent["motion"]["tracks"][0]["channel"] = "wrist.L.axial_rotation"
        cases.append((dependent, "consumer-arm-sweep tracks[0].channel"))
        unordered = complete_source()
        unordered["motion"]["tracks"][0]["keys"][1:3] = reversed(
            unordered["motion"]["tracks"][0]["keys"][1:3])
        cases.append((unordered, "consumer-arm-sweep tracks[0].keys"))
        fractional = complete_source()
        fractional["motion"]["tracks"][0]["keys"][1]["beat"] = 0.5
        cases.append((fractional, "consumer-arm-sweep tracks[0].keys"))
        omitted = complete_source()
        omitted["motion"]["construction"].update(type="squat_closed", side="bilateral")
        cases.append((omitted, "consumer-arm-sweep controls"))
        bad_anchor = complete_source()
        bad_anchor["motion"]["contacts"] = [{
            "foot": "L", "start_beat": 0, "end_beat": 1, "state": "flat",
            "anchors": ["contact.unregistered.L"], "targets_m": [[0, 0, 0]],
        }]
        cases.append((bad_anchor, "consumer-arm-sweep contacts[0].anchors"))
        duplicate_writer = complete_source()
        duplicate_writer["motion"]["tracks"].append(
            deepcopy(duplicate_writer["motion"]["tracks"][0]))
        cases.append((duplicate_writer, "consumer-arm-sweep tracks[1].channel"))
        overwritten = complete_source()
        overwritten["motion"]["controls"] = ["pelvis", "torso", "leg_L", "leg_R", "arm_L", "arm_R"]
        overwritten["motion"]["construction"].update(type="squat_closed", side="bilateral")
        overwritten["motion"]["tracks"][0]["channel"] = "pelvis.y"
        cases.append((overwritten, "consumer-arm-sweep tracks[0].channel"))
        inconsistent = complete_source()
        inconsistent["motion"]["construction"]["end_beat"] = 3
        cases.append((inconsistent, "consumer-arm-sweep construction"))
        for document, expected in cases:
            with self.subTest(expected=expected):
                with self.assertRaisesRegex(SourceValidationError, expected.replace("[", r"\[")):
                    resolve_consumer_document(document, profile, sources,
                                              validation["source_hashes"],
                                              stature_m=sources["profile"]["stature_m"],
                                              bpms=(90,))
        cyclic_variant = variant_source()
        cyclic_variant["motion"]["base_fixture"] = cyclic_variant["motion"]["id"]
        with self.assertRaisesRegex(SourceValidationError, "base_fixture: unknown packaged fixture"):
            resolve_consumer_document(cyclic_variant, profile, sources,
                                      validation["source_hashes"],
                                      stature_m=sources["profile"]["stature_m"], bpms=(90,))

    def test_clearance_record_is_closed_and_preserved(self):
        profile = "adult-reference-v1"
        validation = validate_sources(profile)
        sources, _ = load_sources(profile)
        document = complete_source()
        document["motion"]["provenance"]["kind"] = "adapted"
        document["motion"]["provenance"]["sources"] = [
            {"material": "example-clearance", "locator": "section 1"}]
        document["materials"] = [{
            "id": "example-clearance", "material": "Synthetic test material",
            "part_used": "synthetic provenance only",
            "source_url": "https://example.invalid/material",
            "license": "CC-BY-4.0",
            "license_url": "https://example.invalid/license",
            "permission_basis": "Synthetic test declaration; no external content used.",
            "permissions": {"commercial_use": True, "derivatives": True,
                             "cc_by_4_0_distribution": True},
            "obligations": {"retain_attribution": True,
                            "retain_license_text": True,
                            "retain_copyright_notice": True,
                            "retain_change_notice": True,
                            "retain_notice_if_present": True},
            "conditions": "Synthetic test declaration.",
            "attribution": "Synthetic test only.", "checked_on": "2026-10-25",
            "related_outputs": ["tests/test_consumer_motion.py"],
        }]
        resolved = resolve_consumer_document(document, profile, sources,
                                            validation["source_hashes"],
                                            stature_m=sources["profile"]["stature_m"],
                                            bpms=(90,))
        self.assertEqual(resolved["clearances"]["example-clearance"], document["materials"][0])
        for license_id, obligations, attribution in (
            ("CC0-1.0", {}, ""),
            ("MIT", {"retain_license_text": True,
                     "retain_copyright_notice": True}, "Copyright Example"),
            ("Apache-2.0", {"retain_license_text": True,
                            "retain_copyright_notice": True,
                            "retain_change_notice": True,
                            "retain_notice_if_present": True}, "Copyright Example"),
        ):
            profile_document = deepcopy(document)
            record = profile_document["materials"][0]
            record["license"] = license_id
            record["obligations"] = obligations
            record["attribution"] = attribution
            result = resolve_consumer_document(
                profile_document, profile, sources, validation["source_hashes"],
                stature_m=sources["profile"]["stature_m"], bpms=(90,))
            self.assertEqual(result["clearances"]["example-clearance"]["obligations"], obligations)
        malformed = deepcopy(document)
        malformed["materials"][0]["obligations"]["retain_change_notice"] = False
        with self.assertRaisesRegex(SourceValidationError, "obligations"):
            resolve_consumer_document(malformed, profile, sources,
                                      validation["source_hashes"],
                                      stature_m=sources["profile"]["stature_m"], bpms=(90,))
        missing_attribution = deepcopy(document)
        missing_attribution["materials"][0]["attribution"] = ""
        with self.assertRaisesRegex(SourceValidationError, "attribution"):
            resolve_consumer_document(missing_attribution, profile, sources,
                                      validation["source_hashes"],
                                      stature_m=sources["profile"]["stature_m"], bpms=(90,))
        for mutation, expected in (
            (lambda item: item["permissions"].pop("derivatives"), "permissions"),
            (lambda item: item.update(license="CC-BY-NC-4.0"), "license"),
            (lambda item: item.update(checked_on="2026-99-99"), "checked_on"),
            (lambda item: item.update(id="setuptools-v83-release-notes"), "license"),
        ):
            malformed = deepcopy(document)
            mutation(malformed["materials"][0])
            if malformed["materials"][0]["id"] == "setuptools-v83-release-notes":
                malformed["motion"]["provenance"]["sources"][0]["material"] = "setuptools-v83-release-notes"
            with self.assertRaises(SourceValidationError):
                resolve_consumer_document(malformed, profile, sources,
                                          validation["source_hashes"],
                                          stature_m=sources["profile"]["stature_m"], bpms=(90,))
        unused = complete_source()
        unused["materials"] = deepcopy(document["materials"])
        with self.assertRaisesRegex(SourceValidationError, "unused clearance records"):
            resolve_consumer_document(unused, profile, sources,
                                      validation["source_hashes"],
                                      stature_m=sources["profile"]["stature_m"], bpms=(90,))

    def test_host_api_prepares_and_seals_complete_input(self):
        source = complete_source()
        before = deepcopy(source)
        result = prepare(workspace=self.workspace, output=(
            "build/support-consumer-authored-motions_r1_test_try-1_prepare/input.json"),
            motion=source, stature=11.0, bpms=(90,))
        self.assertEqual(result.stature_m, 11.0)
        self.assertTrue(result.prepared_path.is_file())
        self.assertEqual(source, before)
        self.assertEqual(result.consumer_motion["document"], source)
        self.assertIn("motion", inspect.signature(api.prepare).parameters)
        first = result.poses[0]
        self.assertEqual(first.controls, ("arm_L",))
        self.assertEqual(first.rest_policy, {"policy": "base", "base_fixture": "neutral"})
        self.assertEqual(first.world_root, source["motion"]["world_root"])
        self.assertEqual(first.contacts, ())
        projection = result.to_dict()
        json.dumps(projection, allow_nan=False)
        projection["consumer_motion"]["document"]["motion"]["description"] = "mutated projection"
        self.assertNotEqual(projection["consumer_motion"]["document"],
                            result.consumer_motion["document"])
        self.assertEqual({pose.fixture_id for pose in result.poses}, {"consumer-arm-sweep"})
        self.assertEqual(len(result.timelines), 2)
        self.assertEqual(result.consumer_motion["validation"]["dense_step_beats"], 0.01)
        baseline = read_prepared(result.prepared_path)
        snapshot = baseline["consumer_motion"]
        self.assertEqual(snapshot, result.consumer_motion)
        self.assertEqual(snapshot["source_sha256"], content_hash(source))
        self.assertEqual(snapshot["resolved_sha256"],
                         content_hash(snapshot["resolved_definition"]))
        self.assertEqual({record.logical_path for record in result.provenance.sources
                          if record.logical_path.startswith("consumer/")},
                         {"consumer/consumer-arm-sweep/submitted",
                          "consumer/consumer-arm-sweep/resolved"})
        self.assertIn("hands-on-anatomy-2024", result.provenance.material_ids)
        tampered = deepcopy(baseline)
        tampered["consumer_motion"]["resolved_definition"]["description"] = "changed"
        tampered["consumer_motion"]["resolved_sha256"] = content_hash(
            tampered["consumer_motion"]["resolved_definition"])
        tampered_path = result.run_root / "tampered.json"
        write_json(tampered_path, seal(tampered))
        with self.assertRaisesRegex(ValueError, "Consumer prepared input integrity failure"):
            read_prepared(tampered_path)
        tampered = deepcopy(baseline)
        tampered["consumer_motion"]["source_sha256"] = "0" * 64
        write_json(tampered_path, seal(tampered))
        with self.assertRaisesRegex(ValueError, "Consumer source snapshot hash mismatch"):
            read_prepared(tampered_path)
        tampered = deepcopy(baseline)
        tampered["consumer_motion"]["base_lineage"][0]["raw_sha256"] = "0" * 64
        write_json(tampered_path, seal(tampered))
        with self.assertRaisesRegex(ValueError, "base lineage"):
            read_prepared(tampered_path)
        tampered = deepcopy(baseline)
        tampered["consumer_motion"]["base_lineage"][0]["id"] = "forged-base"
        write_json(tampered_path, seal(tampered))
        with self.assertRaisesRegex(ValueError, "base lineage identity/path mismatch"):
            read_prepared(tampered_path)
        tampered = deepcopy(baseline)
        tampered["samples"][0]["expected_actions"]["shoulder.L.elevation"] = 1
        write_json(tampered_path, seal(tampered))
        with self.assertRaisesRegex(ValueError, "Consumer prepared payload does not match"):
            read_prepared(tampered_path)
        source_path = self.workspace / "source.yaml"
        import yaml
        source_path.write_text(yaml.safe_dump(source), encoding="utf-8")
        persisted = prepare(workspace=self.workspace, output=(
            "build/support-consumer-authored-motions_r1_test_try-2_prepare/input.json"),
            motion=source_path, bpms=(90,))
        source_path.unlink()
        self.assertEqual(persisted.consumer_motion["document"], source)

    def test_backend_reader_is_dependency_isolated_and_host_identity_bound(self):
        result = prepare(workspace=self.workspace, output=(
            "build/support-consumer-authored-motions_r1_test_try-1_backend-input/input.json"),
            motion=complete_source(), bpms=(90,))
        valid_path = result.prepared_path
        expected = result.prepared_sha256
        self.assertEqual(read_prepared_backend(valid_path, expected)["content_sha256"], expected)
        with self.assertRaisesRegex(ValueError, "host-validated prepared identity"):
            read_prepared_backend(valid_path, None)
        with self.assertRaisesRegex(ValueError, "differs from the host-validated identity"):
            read_prepared_backend(valid_path, "0" * 64)

        isolated_script = r'''import sys
blocked = {"yaml", "jsonschema", "referencing", "humanmotionlib.consumer_motion",
           "humanmotionlib.consumer_prepared_validation", "humanmotionlib.source_validation",
           "humanmotionlib.validate", "humanmotionlib.prepare_skeleton"}
class BlockHostValidation:
    def find_spec(self, fullname, path=None, target=None):
        if fullname in blocked or fullname.split(".")[0] in {"yaml", "jsonschema", "referencing"}:
            raise ModuleNotFoundError("blocked host dependency: " + fullname)
sys.meta_path.insert(0, BlockHostValidation())
from humanmotionlib.prepared import read_prepared_backend
value = read_prepared_backend(sys.argv[1], sys.argv[2])
assert value["content_sha256"] == sys.argv[2]
assert not (blocked & set(sys.modules))
print("backend integrity reader passed without host dependencies")
'''
        with tempfile.TemporaryDirectory() as unrelated:
            environment = {key: value for key, value in os.environ.items()
                           if key not in {"PYTHONPATH", "HUMANMOTIONLIB_SOURCE_ROOT"}}
            completed = subprocess.run(
                [sys.executable, "-c", isolated_script, str(valid_path), expected],
                cwd=unrelated, env=environment, check=True, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.assertIn("passed without host dependencies", completed.stdout)

        altered = read_prepared(valid_path)
        altered["sampling"]["consumer-arm-sweep"][0]["animation"][0]["sample_id"] = "missing/00000"
        altered = seal(altered)
        altered_path = self.workspace / "build" / "support-consumer-authored-motions_r1_test_try-1_backend-input" / "resealed.json"
        write_json(altered_path, altered)
        with self.assertRaisesRegex(ValueError, "differs from the host-validated identity"):
            read_prepared_backend(altered_path, expected)
        with self.assertRaisesRegex(ValueError, "dangling sample reference"):
            read_prepared_backend(altered_path, altered["content_sha256"])
        output = self.workspace / "build" / "support-consumer-authored-motions_r1_test_try-1_backend-render"
        from humanmotionlib import run_blender
        with mock.patch.object(run_blender, "inspect_blender") as probe:
            with self.assertRaisesRegex(ValueError, "dangling sample reference"):
                run_blender.run(altered_path, output, workspace=self.workspace)
        probe.assert_not_called()
        self.assertFalse(output.exists())

    def test_consumer_selected_squat_depth_reaches_count_pose(self):
        for attempt, degrees in enumerate((30, 30.5, 60), start=1):
            source = variant_source()
            source["motion"]["id"] = "consumer-selected-squat-depth"
            factor = degrees / 90
            source["motion"]["track_scales"] = {
                channel: factor for channel in (
                    "knee.L.flexion", "knee.R.flexion",
                    "ankle.L.dorsiflexion", "ankle.R.dorsiflexion",
                    "pelvis.pitch", "lumbar.flexion")}
            result = prepare(
                workspace=self.workspace,
                output=f"build/support-consumer-authored-motions_r1_test_try-{attempt}_squat/input.json",
                motion=source, bpms=(90,))
            beat_two = next(pose for pose in result.poses
                            if pose.fixture_id == "consumer-selected-squat-depth" and pose.beat == 2)
            self.assertAlmostEqual(beat_two.actions["knee.L.flexion"], degrees, places=8)
            self.assertAlmostEqual(beat_two.actions["knee.R.flexion"], degrees, places=8)
            timeline = next(item for item in result.timelines if item.mode == "animation")
            self.assertEqual(len(timeline.entries), 17)

    def test_api_rejects_mutual_exclusion_before_writing(self):
        with self.assertRaises(GenerationError) as error:
            prepare(workspace=self.workspace, output=(
                "build/support-consumer-authored-motions_r1_test_try-1_invalid/input.json"),
                fixtures=("neutral",), motion=complete_source(), bpms=(90,))
        self.assertEqual(error.exception.code, "invalid-request")
        self.assertFalse((self.workspace / "build" /
                          "support-consumer-authored-motions_r1_test_try-1_invalid").exists())
        bad_profile = complete_source()
        bad_profile["motion"]["profile"] = "not-packaged"
        with self.assertRaises(GenerationError) as error:
            prepare(workspace=self.workspace, output=(
                "build/support-consumer-authored-motions_r1_test_try-2_invalid/input.json"),
                motion=bad_profile, bpms=(90,))
        self.assertEqual(error.exception.code, "source-validation")
        self.assertEqual(error.exception.details.get("source_id"), "consumer-arm-sweep")
        self.assertEqual(error.exception.details.get("field"), "profile")
        bad_variant = variant_source()
        bad_variant["motion"]["track_scales"] = {"unknown.channel": 0.5}
        with self.assertRaises(GenerationError) as error:
            prepare(workspace=self.workspace, output=(
                "build/support-consumer-authored-motions_r1_test_try-3_invalid/input.json"),
                motion=bad_variant, bpms=(90,))
        self.assertEqual(error.exception.details.get("source_id"), "scaled-squat-test")
        self.assertEqual(error.exception.details.get("field"), "track_scales.unknown.channel")
        nonfinite = complete_source()
        nonfinite["motion"]["tracks"][0]["keys"][1]["value"] = float("inf")
        with self.assertRaises(GenerationError) as error:
            prepare(workspace=self.workspace, output=(
                "build/support-consumer-authored-motions_r1_test_try-4_invalid/input.json"),
                motion=nonfinite, bpms=(90,))
        self.assertEqual(error.exception.details.get("source_id"), "consumer-arm-sweep")
        self.assertIn("tracks[0].keys[1].value", error.exception.details.get("field", ""))

    def test_duration_and_delivered_sample_budgets_fail_before_writing(self):
        too_long = complete_source()
        too_long["motion"]["duration_beats"] = 257
        for attempt, source, bpms in ((1, too_long, (90,)),
                                      (2, complete_source(), (0.0001,))):
            run = self.workspace / "build" / f"support-consumer-authored-motions_r1_test_try-{attempt}_budget"
            with self.assertRaises(GenerationError) as error:
                prepare(workspace=self.workspace, output=run / "input.json",
                        motion=source, bpms=bpms)
            self.assertEqual(error.exception.code,
                             "source-validation" if attempt == 1 else "invalid-request")
            self.assertFalse(run.exists())

    def test_dense_preflight_rejects_out_of_range_consumer_variant(self):
        source = variant_source()
        for channel in source["motion"]["track_scales"]:
            source["motion"]["track_scales"][channel] = 100
        run = self.workspace / "build" / "support-consumer-authored-motions_r1_test_try-1_preflight"
        with self.assertRaises(GenerationError) as error:
            prepare(workspace=self.workspace, output=run / "input.json",
                    motion=source, bpms=(90,))
        self.assertEqual(error.exception.code, "source-validation")
        self.assertIn("beat", str(error.exception))
        self.assertEqual(error.exception.details.get("source_id"), "scaled-squat-test")
        self.assertIn("beat", error.exception.details)
        self.assertIn("channel", error.exception.details)
        self.assertIn("measured", error.exception.details)
        self.assertIn("allowed", error.exception.details)
        self.assertFalse(run.exists())

    def test_unreachable_contact_target_is_rejected_before_writing(self):
        source = complete_source()
        source["motion"]["contacts"] = [{
            "foot": "L", "start_beat": 0, "end_beat": 2, "state": "flat",
            "anchors": ["contact.heel.L", "contact.medial_ball.L",
                        "contact.lateral_ball.L"],
            "targets_m": [[10, 10, 10], [10, 10, 10], [10, 10, 10]],
        }]
        source["motion"]["terminal_contacts"][0]["state"] = "flat"
        run = self.workspace / "build" / "support-consumer-authored-motions_r1_test_try-1_contact"
        with self.assertRaises(GenerationError) as error:
            prepare(workspace=self.workspace, output=run / "input.json",
                    motion=source, bpms=(90,))
        self.assertEqual(error.exception.code, "source-validation")
        self.assertIn("beat=0", str(error.exception))
        self.assertIn("contact.heel.L.target", str(error.exception))
        self.assertIn("measured", error.exception.details)
        self.assertIn("allowed", error.exception.details)
        self.assertIn("residual", error.exception.details)
        self.assertFalse(run.exists())

    def test_dense_grid_catches_coupled_violation_between_delivered_frames(self):
        source = complete_source()
        motion = source["motion"]
        motion.update(id="consumer-wrist-coupling", duration_beats=1, controls=["arm_L"])
        motion["construction"].update(side="L", end_beat=1)
        x0, y0 = math.cos(math.radians(10)), math.sin(math.radians(10))
        x1, y1 = math.cos(math.radians(80)), math.sin(math.radians(80))
        motion["tracks"] = [
            {"channel": "wrist.L.flexion", "easing": "ease_in_out",
             "keys": [{"beat": 0, "value": 70 * x0},
                      {"beat": 1, "value": 70 * x1}]},
            {"channel": "wrist.L.ulnar_deviation", "easing": "linear",
             "keys": [{"beat": 0, "value": 25 * y0},
                      {"beat": 1, "value": 25 * y1}]},
        ]
        def score(t):
            eased = 3 * t * t - 2 * t * t * t
            return (x0 + (x1 - x0) * eased) ** 2 + (y0 + (y1 - y0) * t) ** 2
        delivered = {t: score(t) for t in (0, 0.25, 0.5, 0.75, 1)}
        self.assertTrue(all(value <= 1 + 1e-9 for value in delivered.values()))
        self.assertGreater(score(0.01), 1 + 1e-9)
        run = self.workspace / "build" / "support-consumer-authored-motions_r1_test_try-1_between-frame"
        with self.assertRaises(GenerationError) as error:
            prepare(workspace=self.workspace, output=run / "input.json",
                    motion=source, bpms=(90,))
        self.assertEqual(error.exception.code, "source-validation")
        self.assertEqual(error.exception.details.get("beat"), 0.01)
        self.assertIn("wrist.L.envelope", error.exception.details.get("constraint", ""))
        self.assertGreater(error.exception.details.get("measured", 0), 1)
        self.assertFalse(run.exists())

    def test_installed_wheel_inputs_from_unrelated_directory_are_self_contained(self):
        source_dir = self.workspace / "build" / "support-consumer-authored-motions_r1_test_try-1_external-input"
        source_dir.mkdir()
        profile = "adult-reference-v1"
        packaged, _ = load_sources(profile)
        squat = next(item for item in packaged["diagnostics"] if item["id"] == "squat")
        replacement = variant_source()
        replacement["motion"]["id"] = "replacement-squat-test"
        replacement["motion"]["track_scales"] = {}
        replacement["motion"]["track_overrides"] = [deepcopy(next(
            track for track in squat["tracks"] if track["channel"] == "knee.L.flexion"))]
        sources = (complete_source(), variant_source(), replacement)
        environment_before = Path(sys.prefix) / "bin" / "python"
        script = """
import json, pathlib, sys
from humanmotionlib.api import prepare
result = prepare(workspace=pathlib.Path(sys.argv[1]), output=sys.argv[2],
                 motion=pathlib.Path(sys.argv[3]), bpms=(90,))
print(json.dumps({'path': str(result.prepared_path), 'sha256': result.prepared_sha256,
                  'poses': len(result.poses), 'profile': result.profile_id,
                  'snapshot': result.consumer_motion['source_sha256'],
                  'module': __import__('humanmotionlib.api').api.__file__}))
"""
        unrelated = Path(tempfile.mkdtemp())
        try:
            for attempt, source in enumerate(sources, start=1):
                input_run = source_dir / f"attempt-{attempt}"
                input_run.mkdir()
                source_path = input_run / "motion.json"
                source_path.write_text(json.dumps(source), encoding="utf-8")
                original_bytes = source_path.read_bytes()
                output = (f"build/support-consumer-authored-motions_r1_test_try-{attempt}"
                          "_installed-prepare/input.json")
                completed = subprocess.run(
                    [str(environment_before), "-c", script, str(self.workspace), output,
                     str(source_path)], cwd=unrelated, env={
                         key: value for key, value in os.environ.items()
                         if key not in {"HUMANMOTIONLIB_SOURCE_ROOT", "PYTHONPATH"}}, text=True,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
                evidence = json.loads(completed.stdout)
                self.assertEqual(evidence["profile"], profile)
                self.assertEqual(evidence["poses"], 9 if attempt == 1 else 17)
                module = Path(evidence["module"]).resolve()
                self.assertNotIn("/src/humanmotionlib/", str(module))
                self.assertTrue(Path(evidence["path"]).is_absolute())
                self.assertEqual(source_path.read_bytes(), original_bytes)
                source_path.unlink()
                sealed = read_prepared(evidence["path"])
                self.assertEqual(sealed["consumer_motion"]["source_sha256"], evidence["snapshot"])
                self.assertEqual(sealed["package_identity"]["version"], __version__)
            verify_runtime_integrity()
        finally:
            import shutil
            shutil.rmtree(unrelated)


if __name__ == "__main__":
    unittest.main()
