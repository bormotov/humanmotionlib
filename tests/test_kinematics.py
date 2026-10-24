# SPDX-License-Identifier: Apache-2.0
import math
import unittest

from humanmotionlib import math3d as m
from humanmotionlib.actions import ActionError
from humanmotionlib.kinematics import KinematicModel
from humanmotionlib.mirror import mirror_pose, swap_side
from humanmotionlib.poses import neutral_pose, rest_pose
from humanmotionlib.validate import load_sources


class KinematicModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sources,_ = load_sources("adult-reference-v1")
        cls.profile = sources["profile"]
        cls.mobility = sources["mobility"]
        cls.model = KinematicModel(cls.profile,cls.mobility)
        cls.bodies = cls.model.bodies

    def assertFrames(self, measured, expected):
        self.assertEqual(set(measured),set(expected))
        for id in measured:
            self.assertLessEqual(m.norm(m.sub(measured[id]["position_m"],expected[id]["position_m"])),1e-4*1.7,id)
            self.assertLessEqual(m.angle_error(measured[id]["rotation"],expected[id]["rotation"]),.1,id)

    def test_neutral_and_t_pose_match_frozen_frames(self):
        self.assertFrames(self.model.solve()["frames"],neutral_pose(self.profile))
        request = {f"shoulder.{side}.{name}":90 for side in ("L","R") for name in ("elevation","plane")}
        self.assertFrames(self.model.solve(request)["frames"],rest_pose(self.profile))

    def test_invalid_action_never_returns_a_valid_pose(self):
        for request in ({"knee.R.varus":10},{"elbow.L.flexion":150},{"hip.R.flexion":120,"hip.R.adduction":10}):
            with self.assertRaises(ActionError): self.model.solve(request)

    def test_finite_rigid_rotations_and_mirrored_actions(self):
        request = {"hip.R.flexion":45,"knee.R.flexion":60,"ankle.R.dorsiflexion":10,
                   "shoulder.R.elevation":100,"elbow.R.flexion":30,"forearm.R.pronation":40}
        right = self.model.solve(request)["frames"]
        left = self.model.solve({swap_side(k):v for k,v in request.items()})["frames"]
        self.assertFrames(left,mirror_pose(right))
        for frame in right.values():
            m.validate_basis(frame["rotation"])
            self.assertTrue(all(math.isfinite(x) for x in frame["position_m"]))

    def test_knee_translation_and_patella_do_not_stretch_shank(self):
        for angle,twist in ((0,0),(15,-4),(30,-8),(60,-8),(90,-8),(130,-8)):
            frame = self.model.solve({"knee.R.flexion":angle})["frames"]
            femur = frame["femur.R"]
            femur_action = m.mm(femur["rotation"],m.transpose(self.bodies["femur.R"]["basis"]))
            expected_shift = [0,-.003*math.sin(math.radians(angle))*1.7,-.001*(1-math.cos(math.radians(angle)))*1.7]
            nominal_offset = [0,0,-.234*1.7]
            expected = m.add(femur["position_m"],m.mv(femur_action,m.add(nominal_offset,expected_shift)))
            self.assertLess(m.norm(m.sub(frame["knee.R"]["position_m"],expected)),1e-10)
            distance = m.norm(m.sub(frame["talus.R"]["position_m"],frame["knee.R"]["position_m"]))
            self.assertAlmostEqual(distance,.2155*1.7,places=12)
            patella_action = m.mm(m.transpose(femur_action),frame["patella.R"]["rotation"])
            flexion = math.degrees(math.atan2(-patella_action[1][2],patella_action[2][2]))
            self.assertAlmostEqual(flexion,-.65*angle,places=9)
