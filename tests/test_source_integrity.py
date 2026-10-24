# SPDX-License-Identifier: Apache-2.0
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from humanmotionlib.source_validation import SourceValidationError, load_yaml
from humanmotionlib.validate import load_sources, validate_bundle, validate_sources


class SourceIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle, _ = load_sources("adult-reference-v1")

    def reject(self, mutate, message):
        bundle = deepcopy(self.bundle)
        mutate(bundle)
        with self.assertRaisesRegex(SourceValidationError, message):
            validate_bundle(bundle)

    def test_complete_source_validation(self):
        report = validate_sources("adult-reference-v1")
        self.assertEqual(report["status"], "valid-sources")
        self.assertEqual(report["structures"], 180)
        self.assertTrue(all(len(value)==64 for value in report["source_hashes"].values()))
        self.assertIn("separate checks", report["scope"])

    def test_duplicate_yaml_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"duplicate.yaml"
            path.write_text("outer:\n  coordinate: 1\n  coordinate: 2\n")
            with self.assertRaisesRegex(SourceValidationError, "Duplicate YAML key 'coordinate'"):
                load_yaml(path)

    def test_duplicate_identifiers(self):
        self.reject(lambda b: b["profile"]["structures"][1].update(id="pelvis"), "duplicate identifier")

    def test_parent_resolution_and_cycles(self):
        self.reject(lambda b: b["profile"]["structures"][0].update(parent="absent"), "parent: unresolved absent")
        self.reject(lambda b: b["profile"]["structures"][0].update(parent="sacrum"), "parent cycle")

    def test_transform_rejection(self):
        self.reject(lambda b: b["profile"]["structures"][0].update(rest_orientation=[2,0,0,0]), "unit quaternion")
        self.reject(lambda b: b["profile"]["structures"][0].update(basis=[[-1,0,0],[0,1,0],[0,0,1]]), "determinant")
        self.reject(lambda b: b["profile"]["landmarks"][0].update(position_m=[0,float("nan"),0]), "non-finite")

    def test_channel_ownership_is_exclusive(self):
        self.reject(lambda b: b["body-groups"]["groups"][0]["channels"].append(
            b["body-groups"]["groups"][1]["channels"][0]), "overlapping channel ownership")

    def diagnostic(self, bundle):
        fixture = next(f for f in bundle["diagnostics"] if f["id"]=="neutral")
        fixture["id"] = "integrity-test"
        fixture["construction"]["type"] = "action_sweep"
        fixture["tracks"] = [{"channel":"knee.R.flexion", "easing":"linear", "keys":[{"beat":0,"value":0}]}]
        # Retain the required rest/neutral base fixtures alongside this copy.
        original = deepcopy(next(f for f in self.bundle["diagnostics"] if f["id"]=="neutral"))
        bundle["diagnostics"].append(original)
        return fixture

    def test_conflicting_writers_and_omitted_controls(self):
        def conflict(b):
            f = self.diagnostic(b)
            f["tracks"].append(deepcopy(f["tracks"][0]))
        self.reject(conflict, "conflicting writers")
        def missing_control(b):
            self.diagnostic(b)["controls"] = ["arm_R"]
        self.reject(missing_control, "omitted control")

    def test_mapping_targets_and_helpers(self):
        self.reject(lambda b: b["humanoid-map"]["entries"][0].update(target="absent"), "unavailable target")
        self.reject(lambda b: b["humanoid-map"]["entries"][0].update(target="cartilage.1.L"), "helper cannot")

    def test_source_and_license_gaps(self):
        self.reject(lambda b: b["profile"]["provenance"]["sources"][0].update(material="uncleared-reference"), "unresolved material")
        self.reject(lambda b: b["profile"]["structures"][0]["provenance"].update(license="CC-BY-NC-4.0"), "license")

    def test_coupling_references(self):
        self.reject(lambda b: b["mobility"]["couplings"][0].update(action_ids=["unknown-action"]), "unresolved unknown-action")
