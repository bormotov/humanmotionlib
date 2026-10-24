# SPDX-License-Identifier: Apache-2.0
from copy import deepcopy
import unittest

from humanmotionlib import math3d as m
from humanmotionlib.mirror import mirror_fixture, mirror_pose, mirror_structure, swap_side
from humanmotionlib.poses import neutral_pose, rest_pose
from humanmotionlib.runtime import project_root
from humanmotionlib.source_validation import load_yaml


class MirrorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_yaml(project_root()/"rig/profiles/adult-reference-v1.yaml")

    def assertVector(self, a, b): self.assertLess(m.norm(m.sub(a,b)),1e-10)

    def test_symmetric_reference_and_double_mirror(self):
        for pose in (neutral_pose(self.profile), rest_pose(self.profile)):
            mirrored = mirror_pose(pose)
            again = mirror_pose(mirrored)
            self.assertEqual(set(pose), set(mirrored))
            for id in pose:
                self.assertVector(again[id]["position_m"],pose[id]["position_m"])
                self.assertLessEqual(m.angle_error(again[id]["rotation"],pose[id]["rotation"]),.1)
                self.assertAlmostEqual(m.determinant(mirrored[id]["rotation"]),1)
                # Independent elementwise reflection of the partner frame.
                partner = pose[swap_side(id)]
                self.assertVector(pose[id]["position_m"],[-partner["position_m"][0],partner["position_m"][1],partner["position_m"][2]])
                signs = [-1,1,1]
                expected = [[signs[i]*partner["rotation"][i][j]*signs[j] for j in range(3)] for i in range(3)]
                self.assertLessEqual(m.angle_error(pose[id]["rotation"],expected),.1)

    def test_mirror_reverses_face_winding(self):
        body = next(b for b in self.profile["structures"] if b["id"] == "scapula.R")
        mirrored = mirror_structure(body)
        for a,b in zip(body["geometry"],mirrored["geometry"]):
            if "faces" not in a: continue
            for face,mirror_face in zip(a["faces"],b["faces"]):
                points = [a["points_m"][i] for i in face]
                mirrored_points = [b["points_m"][i] for i in mirror_face]
                normal = m.unit(m.cross(m.sub(points[1],points[0]),m.sub(points[2],points[0])))
                mirror_normal = m.unit(m.cross(m.sub(mirrored_points[1],mirrored_points[0]),m.sub(mirrored_points[2],mirrored_points[0])))
                self.assertVector(mirror_normal,[-normal[0],normal[1],normal[2]])
        again = mirror_structure(mirrored)
        self.assertEqual(again["geometry"],body["geometry"])
        self.assertVector(again["origin_m"],body["origin_m"])

    def test_fixture_ids_contacts_and_ownership(self):
        fixture = load_yaml(project_root()/"rig/diagnostics/neutral.yaml")
        mirrored = mirror_fixture(fixture)
        again = mirror_fixture(mirrored)
        self.assertEqual(again,fixture)
        by_side = {c["foot"]:c for c in fixture["contacts"]}
        for contact in mirrored["contacts"]:
            partner = by_side[swap_side(contact["foot"])]
            self.assertEqual(contact["anchors"],[swap_side(id) for id in partner["anchors"]])
            for a,b in zip(contact["targets_m"],partner["targets_m"]):self.assertVector(a,[-b[0],b[1],b[2]])
        for id in ("arm_L","leg_R","radius.R.attachment","leftUpperArm","pelvis"):
            self.assertEqual(swap_side(swap_side(id)),id)

    def test_named_positive_actions_keep_anatomical_direction(self):
        mobility = load_yaml(project_root()/"rig/mobility/adult-reference-v1.yaml")
        actions = {a["id"]:a for a in mobility["actions"]}
        for id, action in actions.items():
            if ".R." not in id or action["mode"] != "independent": continue
            partner = actions[swap_side(id)]
            self.assertEqual(partner["bounds_deg"],action["bounds_deg"])
            axis = action["axis"]
            self.assertVector(partner["axis"],[axis[0],-axis[1],-axis[2]])
            landmark = [.13,.26,-.37]
            moved = m.mv(m.rot(action["axis"],1),landmark)
            mirrored_landmark = [-landmark[0],landmark[1],landmark[2]]
            moved_partner = m.mv(m.rot(partner["axis"],1),mirrored_landmark)
            self.assertVector(moved_partner,[-moved[0],moved[1],moved[2]])
