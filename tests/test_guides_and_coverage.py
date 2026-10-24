# SPDX-License-Identifier: Apache-2.0
from copy import deepcopy
import unittest

from humanmotionlib import math3d as m
from humanmotionlib.coverage import audit_action_cases, audit_anatomical_directions, anatomical_direction_measurement
from humanmotionlib.kinematics import KinematicModel
from humanmotionlib.runtime import project_root
from humanmotionlib.source_validation import load_yaml


class GuideAndCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = project_root()
        cls.profile = load_yaml(root/"rig/profiles/adult-reference-v1.yaml")
        cls.mobility = load_yaml(root/"rig/mobility/adult-reference-v1.yaml")
        cls.model = KinematicModel(cls.profile,cls.mobility)

    def test_guides_bridge_explicit_targets_without_stretching_bones(self):
        original = deepcopy(self.profile)
        neutral = self.model.solve()
        posed = self.model.solve({"thoracic.flexion":30})
        changed = 0
        for body in self.profile["structures"]:
            for primitive in body["geometry"]:
                if not primitive.get("bindings"):continue
                self.assertFalse(body["rigid"])
                current = posed["guides"][primitive["id"]]
                rest = neutral["guides"][primitive["id"]]
                for binding in primitive["bindings"]:
                    index = binding["point_index"]
                    guide_frame = posed["frames"][body["id"]]
                    point = m.add(guide_frame["position_m"],m.mv(guide_frame["rotation"],current[index]))
                    kind = binding.get('kind','rigid_point')
                    if kind == 'rigid_point':
                        target_frame = posed['frames'][binding['structure']]
                        target = m.add(target_frame['position_m'],m.mv(target_frame['rotation'],binding['position_m']))
                    elif kind == 'guide_point':
                        target_id=binding['guide'].removesuffix('.geometry.0')
                        target_frame=posed['frames'][target_id]
                        target=m.add(target_frame['position_m'],m.mv(target_frame['rotation'],posed['guides'][binding['guide']][binding['control_index']]))
                    else:
                        endpoints=[m.add(guide_frame['position_m'],m.mv(guide_frame['rotation'],current[i])) for i in binding['endpoints']]
                        target=m.add(m.scale(m.add(*endpoints),.5),m.mv(posed['frames'][binding['offset_frame']]['rotation'],binding['offset_m']))
                    self.assertLess(m.norm(m.sub(point,target)),1e-4*1.7)
                if abs(m.norm(m.sub(current[1],current[0]))-m.norm(m.sub(rest[1],rest[0])))>1e-4*1.7:changed+=1
        self.assertGreater(changed,0)
        self.assertEqual(self.profile,original)

    def test_no_binding_can_deform_a_rigid_structure(self):
        profile = deepcopy(self.profile)
        guide = next(b for b in profile["structures"] if b["id"]=="cartilage.1.R")
        guide["rigid"] = True
        with self.assertRaisesRegex(ValueError,"cannot deform rigid"):
            KinematicModel(profile,self.mobility).solve()

    def test_all_actions_have_explicit_numeric_coverage(self):
        report = audit_action_cases(self.profile,self.mobility)
        self.assertEqual(report["status"],"pass",str({id:r for id,r in report["actions"].items() if any(not c["passed"] for c in r["cases"].values())}))
        self.assertEqual(len(report["actions"]),70)
        for id,row in report["actions"].items():
            self.assertEqual(row["visual"],"pending")
            if row["mode"]=="independent":
                self.assertEqual(set(row["cases"]),{"positive","lower","interior","upper","below","above"})
                self.assertFalse(row["cases"]["below"]["pose_generated"])
            else:
                self.assertEqual(row["cases"]["unsupported_write"]["observed_state"],"unsupported")


    def test_absolute_anatomical_directions_and_reversed_sign_mutations(self):
        report = audit_anatomical_directions(self.profile,self.mobility)
        self.assertEqual(report["status"],"pass",str(report))
        for side in ("L","R"):
            sign = 1 if side == "R" else -1
            for kind,body,rotation in (
                ("hip_external","hindfoot.",m.rz(sign*20)),
                ("forearm_midrotation","radius.",m.mm(m.rx(90),m.rot([-0.07306426627542377,0,-sign*0.9973272346595344],80))),
                ("knee_medial","tibia.",m.mm(m.rx(-30),m.rz(-sign*8)))):
                frames = self.model.solve()["frames"]
                id = body+side
                frames[id]["rotation"] = m.mm(rotation,self.model.bodies[id]["basis"])
                check = anatomical_direction_measurement(self.profile,frames,side,kind)
                self.assertEqual(check["status"],"fail",str(check))
