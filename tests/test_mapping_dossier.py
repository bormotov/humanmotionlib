# SPDX-License-Identifier: Apache-2.0
from collections import Counter
import unittest

import yaml

from tools.runtime import project_root
from tools.source_validation import validate_document


class MappingDossierTests(unittest.TestCase):
    def test_complete_exclusive_channel_ownership(self):
        root = project_root()
        groups = yaml.safe_load((root/"rig/body-groups.yaml").read_text())
        validate_document(groups, "body-groups")
        channels = {g["id"]:set(g["channels"]) for g in groups["groups"]}
        self.assertEqual(set(channels), {"pelvis","torso","head_neck","arm_L","arm_R","leg_L","leg_R"})
        counts = Counter(c for g in groups["groups"] for c in g["channels"])
        self.assertTrue(all(count == 1 for count in counts.values()))
        mobility = yaml.safe_load((root/"rig/mobility/adult-reference-v1.yaml").read_text())
        for action in mobility["actions"]+mobility["placements"]:
            self.assertIn(action["id"], channels[action["group"]])
        profile = yaml.safe_load((root/"rig/profiles/adult-reference-v1.yaml").read_text())
        for body in profile["structures"]:
            if body["representation"] != "omitted": self.assertEqual(counts[body["id"]+".transform"], 1)
        for side in ("L","R"):
            for id in ("clavicle","scapula","radius","hand"):
                self.assertIn(id+"."+side+".transform", channels["arm_"+side])
            for id in ("hindfoot","mtp","toe.1"):
                self.assertIn(id+"."+side+".transform", channels["leg_"+side])

    def test_semantics_resolve_and_losses_are_explicit(self):
        root = project_root()
        data = yaml.safe_load((root/"rig/humanoid-map.yaml").read_text())
        validate_document(data, "humanoid-map")
        expected = {"hips","spine","head","leftUpperLeg","leftLowerLeg","leftFoot",
                    "rightUpperLeg","rightLowerLeg","rightFoot","leftUpperArm","leftLowerArm",
                    "leftHand","rightUpperArm","rightLowerArm","rightHand"}
        self.assertEqual(set(data["required"]), expected)
        entries = {e["humanoid"]:e for e in data["entries"]}
        self.assertEqual(len(entries), len(data["entries"]))
        self.assertTrue(expected <= entries.keys())
        profile = yaml.safe_load((root/"rig/profiles/adult-reference-v1.yaml").read_text())
        bodies = {b["id"]:b for b in profile["structures"]}
        for entry in entries.values():
            self.assertIn(entry["target"], bodies)
            self.assertNotEqual(bodies[entry["target"]]["kind"], "helper")
        mapped = {e["target"] for e in entries.values()}
        self.assertEqual(mapped & set(data["internal_only"]), set())
        for id in ("patella.L","scapula.R","radius.R","T12"):
            self.assertIn(id, data["internal_only"])
        self.assertEqual(len(data["omissions"]), 33)
        self.assertTrue({"jaw","leftEye","rightEye"} <= {e["humanoid"] for e in data["omissions"]})
        text = " ".join(data["losses"])
        for token in ("VRMA","rollback","radiocarpal","MPFB","Rigify","round trips"):
            self.assertIn(token, text)
        self.assertEqual(data["provenance"]["sources"][0]["material"], "three-vrm-humanoid-vocabulary")
