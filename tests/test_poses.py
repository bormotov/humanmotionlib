# SPDX-License-Identifier: Apache-2.0
import unittest

from tools import math3d as m
from tools.poses import apply_deltas, neutral_pose, rest_pose, scaled_profile, to_deltas
from tools.runtime import project_root
from tools.source_validation import load_yaml


class CanonicalPoseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_yaml(project_root()/"rig/profiles/adult-reference-v1.yaml")

    def assertVector(self, actual, expected, tolerance=1e-10):
        self.assertLessEqual(m.norm(m.sub(actual,expected)), tolerance)

    def test_identity_deltas_reproduce_t_pose(self):
        pose = rest_pose(self.profile)
        h = self.profile["stature_m"]
        for side, sign in (("L",-1),("R",1)):
            shoulder, elbow, wrist = [pose[name+"."+side]["position_m"] for name in ("humerus","elbow","wrist")]
            self.assertVector(m.sub(elbow, shoulder), [sign*.1605*h,0,0])
            self.assertVector(m.sub(wrist, elbow), [sign*.1365*h,0,0])
            self.assertVector(m.mv(pose["hand."+side]["rotation"],[0,1,0]),[0,1,0])
            hip, knee, ankle = [pose[name+"."+side]["position_m"] for name in ("femur","knee","talus")]
            self.assertVector(m.sub(knee,hip),[0,0,-.234*h])
            self.assertVector(m.sub(ankle,knee),[0,0,-.2155*h])
            self.assertVector(m.mv(pose["hindfoot."+side]["rotation"],[0,1,0]),[0,1,0])

    def test_neutral_offsets_and_round_trip(self):
        neutral = neutral_pose(self.profile)
        rest = rest_pose(self.profile)
        for side in ("L","R"):
            self.assertVector(m.sub(neutral["elbow."+side]["position_m"],neutral["humerus."+side]["position_m"]),[0,0,-.1605*1.7])
            self.assertGreater(m.angle_error(neutral["humerus."+side]["rotation"],rest["humerus."+side]["rotation"]),89.9)
        channels = to_deltas(self.profile, neutral)
        rebuilt = apply_deltas(self.profile,channels)
        for id, expected in neutral.items():
            self.assertVector(rebuilt[id]["position_m"],expected["position_m"])
            for a,b in zip(rebuilt[id]["rotation"],expected["rotation"]): self.assertVector(a,b)

    def test_scale_preserves_angles_and_topology(self):
        source = self.profile
        for stature in (1.5,1.7,1.9):
            scaled = scaled_profile(source,stature)
            self.assertAlmostEqual(scaled["stature_m"],stature)
            a,b = rest_pose(source),rest_pose(scaled)
            self.assertEqual(set(a),set(b))
            for id in a:
                self.assertVector(b[id]["position_m"],m.scale(a[id]["position_m"],stature/1.7))
                for x,y in zip(a[id]["rotation"],b[id]["rotation"]): self.assertVector(x,y)
            self.assertEqual(scaled["proportions"],source["proportions"])
            self.assertEqual(scaled["resolution"],source["resolution"])

    def test_invalid_delta_does_not_silently_normalize_or_scale(self):
        for value in ({"pelvis":{"rotation_delta":[2,0,0,0]}},
                      {"pelvis":{"scale":[2,2,2]}},
                      {"pelvis":{"translation_m":[0,float("inf"),0]}}):
            with self.assertRaises(ValueError): apply_deltas(self.profile,value)
