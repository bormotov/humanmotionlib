# SPDX-License-Identifier: Apache-2.0
from copy import deepcopy
import math
import unittest

from tools import math3d as m
from tools.kinematics import KinematicModel
from tools.measurements import measure_pose
from tools.runtime import project_root
from tools.source_validation import load_yaml


class CouplingMeasurementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = project_root()
        cls.profile = load_yaml(root/"rig/profiles/adult-reference-v1.yaml")
        cls.mobility = load_yaml(root/"rig/mobility/adult-reference-v1.yaml")
        cls.model = KinematicModel(cls.profile,cls.mobility)
        cls.bodies = cls.model.bodies
        cls.attachments = {a["id"]:(b["id"],a) for b in cls.profile["structures"] for a in b["attachments"]}

    def check(self,request):
        frames = self.model.solve(request)["frames"]
        report = measure_pose(self.profile,self.mobility,frames,expected_actions=request)
        failed = [c["id"] for c in report["checks"] if c["status"]!="pass"]
        self.assertEqual(report["status"],"pass",str(failed[:8]))
        return frames,report

    def action_rotation(self,frames,id):
        return m.mm(frames[id]["rotation"],m.transpose(self.bodies[id]["basis"]))

    def test_shoulder_reference_samples_and_intermediate_planes(self):
        for elevation,upward in ((0,0),(30,10),(60,20),(90,30),(120,40),(160,53.333333333),(168,56)):
            for side in ("L","R"):
                frames,_ = self.check({f"shoulder.{side}.elevation":elevation})
                g = self.action_rotation(frames,"scapula."+side)
                if side=="L":g=[[(-1 if i==0 else 1)*g[i][j]*(-1 if j==0 else 1) for j in range(3)] for i in range(3)]
                upward_only = m.mm(m.mm(g,m.rz(.075*elevation)),m.rx(-elevation/10))
                measured = math.degrees(math.atan2(upward_only[2][1],upward_only[2][2]))
                self.assertAlmostEqual(measured,upward,places=7)
        for side in ("L","R"):
            for plane in (-180,-135,-90,-45,0,45,90,135,180):
                self.check({f"shoulder.{side}.elevation":15,f"shoulder.{side}.plane":plane})

    def test_frozen_scapula_fails_without_exceeding_individual_gh_guard(self):
        request = {"shoulder.R.elevation":60}
        frames = self.model.solve(request)["frames"]
        frames["scapula.R"]["rotation"] = deepcopy(self.bodies["scapula.R"]["basis"])
        report = measure_pose(self.profile,self.mobility,frames,expected_actions=request)
        checks = {c["id"]:c for c in report["checks"]}
        self.assertEqual(checks["shoulder.R.scapula_curve"]["status"],"fail")
        self.assertEqual(checks["glenohumeral.R.swing"]["status"],"pass")

    def test_forearm_samples_and_wrist_twist_substitute(self):
        neutral = self.model.solve()["frames"]
        for side in ("L","R"):
            for angle in (-80,-40,0,40,75):
                frames,report = self.check({f"forearm.{side}.pronation":angle})
                self.assertAlmostEqual(report["measured_actions"][f"forearm.{side}.pronation"],angle,places=9)
                for a,b in zip(frames["ulna."+side]["rotation"],neutral["ulna."+side]["rotation"]):
                    self.assertLess(m.norm(m.sub(a,b)),1e-12)
        frames = self.model.solve({"forearm.R.pronation":40})["frames"]
        frames["radius.R"] = deepcopy(neutral["radius.R"])
        report = measure_pose(self.profile,self.mobility,frames,expected_actions={"forearm.R.pronation":40})
        checks = {c["id"]:c for c in report["checks"]}
        self.assertEqual(checks["forearm.R.pronation.intent"]["status"],"fail")
        self.assertEqual(checks["forearm.R.radiocarpal_curve"]["status"],"fail")

    def test_knee_and_patella_reference_knots(self):
        for side in ("L","R"):
            sign = 1 if side=="R" else -1
            for angle,twist in ((0,0),(7.5,-1.25),(15,-4),(22.5,-6.75),(30,-8),(60,-8),(90,-8),(130,-8)):
                frames,_ = self.check({f"knee.{side}.flexion":angle})
                rotation = self.action_rotation(frames,"tibia."+side)
                measured_twist = -sign*math.degrees(math.atan2(-rotation[0][1],rotation[0][0]))
                self.assertAlmostEqual(measured_twist,twist,places=9)
            for angle,lateral,tilt in ((0,0,0),(3.75,-.0000625,-.15625),(15,-.0004,-1),(30,.0003,0),(60,.00045,1.5),(90,.0006,3),(130,.0004,2)):
                frames,_ = self.check({f"knee.{side}.flexion":angle})
                displacement = (frames["patella."+side]["position_m"][0]-self.bodies["patella."+side]["origin_m"][0])/1.7
                self.assertAlmostEqual(displacement,sign*lateral,places=12)
                rotation = self.action_rotation(frames,"patella."+side)
                measured_tilt = sign*math.degrees(math.atan2(-rotation[0][1],rotation[0][0]))
                self.assertAlmostEqual(measured_tilt,tilt,places=9)

    def test_frozen_patella_fails(self):
        request = {"knee.R.flexion":90}
        frames = self.model.solve(request)["frames"]
        frames["patella.R"] = {"position_m":list(self.bodies["patella.R"]["origin_m"]),"rotation":deepcopy(self.bodies["patella.R"]["basis"])}
        report = measure_pose(self.profile,self.mobility,frames,expected_actions=request)
        self.assertTrue(any(c["id"]=="patella.R.tracking" and c["status"]=="fail" for c in report["checks"]))

    def test_spinal_distribution_and_frozen_vertebra(self):
        for region,prefix,count in (("cervical","C",7),("thoracic","T",12),("lumbar","L",5)):
            self.check({region+".flexion":20,region+".lateral_flexion":8,region+".rotation":5})
            for label,angle in (("flexion",30),("lateral_flexion",10),("rotation",5)):
                frames,report = self.check({region+"."+label:angle})
                self.assertAlmostEqual(report["measured_actions"][region+"."+label],angle,places=9)
            frames,_ = self.check({region+".flexion":30})
            # Every rigid vertebral process keeps its source endpoint distance.
            for index in range(1,count+1):
                body = self.bodies[prefix+str(index)]
                primitive = next(p for p in body["geometry"] if p["type"]=="tube")
                points = [m.add(frames[body["id"]]["position_m"],m.mv(frames[body["id"]]["rotation"],p)) for p in primitive["points_m"]]
                self.assertAlmostEqual(m.norm(m.sub(points[1],points[0])),.012*1.7,places=12)
        frames = self.model.solve({"lumbar.flexion":30})["frames"]
        parent = self.bodies["L3"]["parent"]
        frames["L3"]["rotation"] = m.mm(self.action_rotation(frames,parent),self.bodies["L3"]["basis"])
        report = measure_pose(self.profile,self.mobility,frames,expected_actions={"lumbar.flexion":30})
        self.assertTrue(any(c["id"]=="L3.distribution" and c["status"]=="fail" for c in report["checks"]))

    def test_oblique_hindfoot_and_forefoot_rocker(self):
        original = deepcopy(self.profile)
        for side in ("L","R"):
            frames,_ = self.check({f"hindfoot.{side}.inversion":20})
            rotation = self.action_rotation(frames,"hindfoot."+side)
            self.assertGreater(abs(rotation[0][2]),1e-4)
            self.assertGreater(abs(rotation[1][0]),1e-4)
        for degrees in (0,10,20,30):
            radians = math.radians(degrees)
            dy = (.075*(1-math.cos(radians))+.030*math.sin(radians))*1.7
            dz = (.075*math.sin(radians)+.030*(math.cos(radians)-1))*1.7
            request = {"pelvis.y":dy,"pelvis.z":.4895*1.7+dz}
            for side in ("L","R"):
                request[f"ankle.{side}.dorsiflexion"] = -degrees
                request[f"mtp.{side}.extension"] = degrees
            frames,_ = self.check(request)
            for side,sign in (("L",-1),("R",1)):
                self.assertLess(m.angle_error(self.action_rotation(frames,"toe.1."+side),m.I),.1)
                for name,x in (("medial_ball",-.018),("lateral_ball",.020)):
                    body,attachment = self.attachments[f"contact.{name}.{side}"]
                    point = m.add(frames[body]["position_m"],m.mv(frames[body]["rotation"],attachment["position_m"]))
                    target = [sign*(.055+x)*1.7,.075*1.7,0]
                    self.assertLess(m.norm(m.sub(point,target)),1e-3*1.7)
        self.assertEqual(self.profile,original)

    def test_wrong_hindfoot_axis_is_detected(self):
        request = {"hindfoot.R.inversion":20}
        frames = self.model.solve(request)["frames"]
        frames["hindfoot.R"]["rotation"] = m.rx(20)
        report = measure_pose(self.profile,self.mobility,frames,expected_actions=request)
        self.assertTrue(any(c["id"]=="hindfoot.R.oblique_axis" and c["status"]=="fail" for c in report["checks"]))
