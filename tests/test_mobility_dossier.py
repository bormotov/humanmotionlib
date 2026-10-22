# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import math
import unittest

import yaml

from tools.runtime import project_root
from tools.source_validation import validate_document


def load_mobility():
    return yaml.safe_load((project_root()/"rig/mobility/adult-reference-v1.yaml").read_text())


class MobilityDossierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_mobility()

    def test_schema_inventory_and_frames(self):
        d = self.data
        validate_document(d, "mobility")
        profile = yaml.safe_load((project_root()/"rig/profiles/adult-reference-v1.yaml").read_text())
        bodies = {r["id"] for r in profile["structures"]}
        actions = {r["id"]: r for r in d["actions"]}
        self.assertEqual(len(actions), len(d["actions"]))
        for action in actions.values():
            self.assertIn(action["joint"], bodies)
            self.assertIn(action["frame"], bodies | {"world"})
            self.assertAlmostEqual(sum(x*x for x in action["axis"]), 1, places=12)
            low, high = action["bounds_deg"]
            self.assertLessEqual(low, action["neutral_deg"])
            self.assertLessEqual(action["neutral_deg"], high)
        for side in ("L", "R"):
            for prefix, action in [("hip","flexion"),("hip","adduction"),("hip","external_rotation"),
                                   ("shoulder","elevation"),("shoulder","plane"),("shoulder","external_twist"),
                                   ("elbow","flexion"),("forearm","pronation"),("wrist","flexion"),
                                   ("wrist","ulnar_deviation"),("knee","flexion"),("ankle","dorsiflexion"),
                                   ("hindfoot","inversion"),("mtp","extension")]:
                self.assertEqual(actions[f"{prefix}.{side}.{action}"]["mode"], "independent")
            self.assertEqual(actions[f"forearm.{side}.pronation"]["neutral_deg"], -80)
            self.assertEqual(actions[f"wrist.{side}.axial_rotation"]["mode"], "fixed")

    def test_reference_means_remain_separate(self):
        expected = {
            "hip.extension": (18.1,17.4), "hip.flexion": (133.8,130.4),
            "knee.flexion": (141.9,137.7), "knee.hyperextension": (1.6,1),
            "ankle.dorsiflexion": (13.8,12.7), "ankle.plantarflexion": (62.1,54.6),
            "shoulder.total_flexion": (172,168.8), "elbow.flexion": (150,144.6),
            "elbow.hyperextension": (4.7,.8), "forearm.pronation": (82,76.9),
            "forearm.supination": (90.6,85)}
        actual = {r["action"]: (r["female_deg"],r["male_deg"]) for r in self.data["reference_observations"]}
        self.assertEqual(actual, expected)
        for record in self.data["reference_observations"]:
            self.assertEqual(record["statistic"], "mean")
            self.assertIn("20–44", record["cohort"])
            self.assertIn("not the DXA", record["cohort"])
        actions = {r["id"]: r for r in self.data["actions"]}
        self.assertEqual(actions["hip.R.flexion"]["bounds_deg"], [-15,120])
        self.assertEqual(actions["elbow.R.flexion"]["bounds_deg"], [0,140])
        self.assertNotEqual(actions["hip.R.flexion"]["bounds_deg"][1], expected["hip.flexion"][0])

    def test_coupling_records_and_body_placement(self):
        actions = {r["id"] for r in self.data["actions"]}
        couplings = {r["id"]:r for r in self.data["couplings"]}
        self.assertEqual(len(couplings), len(self.data["couplings"]))
        for record in couplings.values():
            self.assertTrue(set(record["action_ids"]) <= actions)
        for side in ("L", "R"):
            self.assertEqual(couplings[f"patella.{side}.tracking"]["parameters"]["knots_deg"], [0,15,30,90,130])
            self.assertEqual(couplings[f"shoulder.{side}.sector"]["parameters"]["elevation_deg"], [40,20,168,160,40])
        for region, count in [("cervical",7),("thoracic",12),("lumbar",5)]:
            self.assertEqual(couplings[region+".distribution"]["parameters"]["count"], count)
        placements = {r["id"]:r for r in self.data["placements"]}
        self.assertEqual(set(placements), {"pelvis.x","pelvis.y","pelvis.z"})
        self.assertEqual(placements["pelvis.z"]["bounds_m"], [.20*1.7,.60*1.7])
        self.assertEqual(placements["pelvis.z"]["neutral_m"], .4895*1.7)

    def test_record_provenance_resolves(self):
        register = (project_root()/"docs/used-materials.md").read_text()
        for record in [self.data, *self.data["actions"], *self.data["placements"],
                       *self.data["couplings"], *self.data["reference_observations"]]:
            self.assertTrue(record["provenance"]["rationale"])
            for source in record["provenance"]["sources"]:
                self.assertIn(source["material"], register)
                self.assertTrue(source["locator"])
