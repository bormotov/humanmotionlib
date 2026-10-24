# SPDX-License-Identifier: Apache-2.0
from copy import deepcopy
import math
import unittest

from humanmotionlib import math3d as m
from humanmotionlib.actions import ActionError, ActionEvaluator, constraint_failure, require_valid
from humanmotionlib.articulation import hip_rotation, wrist_rotation
from humanmotionlib.runtime import project_root
from humanmotionlib.source_validation import load_yaml


class ActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mobility = load_yaml(project_root()/"rig/mobility/adult-reference-v1.yaml")
        cls.evaluator = ActionEvaluator(cls.mobility)

    def test_valid_neutral_and_explicit_states(self):
        report = self.evaluator.evaluate()
        self.assertEqual(report["state"],"valid")
        self.assertEqual(require_valid(report)["forearm.R.pronation"],-80)
        for channel in ("knee.R.varus","jaw.rotation","digits.L.rotation","wrist.R.axial_rotation",
                        "hindfoot.R.yaw","knee.R.tibial_twist"):
            report = self.evaluator.evaluate({channel:10},beat=1.25)
            self.assertEqual(report["state"],"unsupported")
            self.assertEqual(report["errors"][0]["beat"],1.25)
            with self.assertRaises(ActionError): require_valid(report)

    def test_error_retains_value_bounds_time_without_mutation(self):
        request = {"elbow.R.flexion":140.5}
        before = deepcopy(self.mobility)
        report = self.evaluator.evaluate(request,beat=2.5)
        self.assertEqual(report["state"],"out-of-range")
        error = report["errors"][0]
        self.assertEqual((error["joint"],error["action"],error["measured"],error["bounds"],error["beat"]),
                         ("elbow.R","elbow.R.flexion",140.5,[0,140],2.5))
        self.assertEqual(report["values"]["elbow.R.flexion"],140.5)
        self.assertEqual(request,{"elbow.R.flexion":140.5})
        self.assertEqual(self.mobility,before)
        for value in (True,float("nan"),float("inf"),"90"):
            self.assertEqual(self.evaluator.evaluate({"elbow.R.flexion":value})["state"],"out-of-range")

    def test_unsatisfied_contact_record_preserves_target_and_residuals(self):
        target = [0,0,20]
        residuals = {"hip.R.flexion":2,"contact.R":19}
        report = constraint_failure("foot.R","floor_pin",19,.001,3,target,residuals)
        self.assertEqual(report["state"],"unsatisfied-constraint")
        self.assertEqual(report["errors"][0]["requested_target"],target)
        self.assertEqual(report["errors"][0]["joint_residuals"],residuals)
        self.assertEqual(target,[0,0,20])
        with self.assertRaises(ActionError): require_valid(report)

    def test_all_independent_boundaries_and_outside_samples(self):
        for id,action in self.evaluator.actions.items():
            if action.get("mode","independent") != "independent": continue
            suffix = "deg" if "bounds_deg" in action else "m"
            low,high = action["bounds_"+suffix]
            companion = {f"shoulder.{id.split('.')[1]}.elevation":1} if id.startswith("shoulder.") and id.endswith(".plane") else {}
            for value in (low,(low+high)/2,high):
                with self.subTest(action=id,value=value):
                    self.assertEqual(self.evaluator.evaluate(companion|{id:value})["state"],"valid")
            beyond = .5 if suffix == "deg" else .0005
            for value in (low-beyond,high+beyond):
                with self.subTest(action=id,outside=value):
                    self.assertEqual(self.evaluator.evaluate(companion|{id:value})["state"],"out-of-range")

    def test_multiaxis_and_global_spinal_conditions(self):
        for request in ({"hip.R.flexion":120,"hip.R.adduction":10},
                        {"wrist.L.flexion":70,"wrist.L.ulnar_deviation":25},
                        {"lumbar.flexion":35,"thoracic.flexion":35},
                        {"lumbar.lateral_flexion":15,"thoracic.lateral_flexion":20}):
            report = self.evaluator.evaluate(request)
            self.assertEqual(report["state"],"out-of-range")
            self.assertTrue(any(error["action"]=="combined" for error in report["errors"]))

    def test_shoulder_sectors_zero_plane_and_joint_report(self):
        for side in ("L","R"):
            for plane,maximum in ((-180,40),(-90,20),(0,168),(45,164),(90,160),(180,40)):
                request = {f"shoulder.{side}.elevation":maximum,f"shoulder.{side}.plane":plane}
                report = self.evaluator.evaluate(request)
                self.assertEqual(report["state"],"valid",str(report["errors"]))
                measured = report["measurements"]["shoulder."+side]
                self.assertEqual(measured["total_elevation_deg"],maximum)
                self.assertLess(measured["glenohumeral_swing_deg"],maximum)
                self.assertAlmostEqual(measured["sector_max_deg"],maximum)
                request[f"shoulder.{side}.elevation"] = maximum+.5
                self.assertEqual(self.evaluator.evaluate(request)["state"],"out-of-range")
            self.assertEqual(self.evaluator.evaluate({f"shoulder.{side}.plane":90})["state"],"out-of-range")
            self.assertEqual(self.evaluator.evaluate({f"shoulder.{side}.elevation":160,
                f"shoulder.{side}.external_twist":70})["state"],"out-of-range")
            self.assertEqual(self.evaluator.evaluate({f"shoulder.{side}.elevation":1,
                f"shoulder.{side}.plane":180.5})["state"],"out-of-range")
        right = self.evaluator.evaluate({"shoulder.R.external_twist":50})["measurements"]["shoulder.R"]
        left = self.evaluator.evaluate({"shoulder.L.external_twist":50})["measurements"]["shoulder.L"]
        self.assertAlmostEqual(right["glenohumeral_twist_deg"],left["glenohumeral_twist_deg"])

    def test_dependent_glenohumeral_guard_is_enforced(self):
        altered = deepcopy(self.mobility)
        for coupling in altered["couplings"]:
            if coupling["id"] == "shoulder.R.sector":
                coupling["parameters"]["gh_swing_max_deg"] = 1
        report = ActionEvaluator(altered).evaluate({"shoulder.R.elevation":60})
        self.assertTrue(any(error["action"]=="glenohumeral" for error in report["errors"]))

    def test_composition_against_scalar_rotation_arithmetic(self):
        vector = [.2,.3,-.4]
        f,b,r = 30,5,10
        c,s = math.cos(math.radians(-r)),math.sin(math.radians(-r))
        x,y,z = c*vector[0]-s*vector[1],s*vector[0]+c*vector[1],vector[2]
        c,s = math.cos(math.radians(b)),math.sin(math.radians(b))
        x,z = c*x+s*z,-s*x+c*z
        c,s = math.cos(math.radians(f)),math.sin(math.radians(f))
        y,z = c*y-s*z,s*y+c*z
        actual = m.mv(hip_rotation(f,b,r),vector)
        self.assertLess(m.norm(m.sub(actual,[x,y,z])),1e-12)
        mirrored = m.mv(hip_rotation(f,b,r,"L"),[-vector[0],vector[1],vector[2]])
        self.assertLess(m.norm(m.sub(mirrored,[-x,y,z])),1e-12)
        self.assertLess(m.angle_error(wrist_rotation(30,5),hip_rotation(30,5,0)),1e-6)
