# SPDX-License-Identifier: Apache-2.0
"""Measure action angles from matrices/landmark displacements in free context."""

import math
import unittest

from tools import math3d as m
from tools.actions import ActionEvaluator
from tools.articulation import ankle_hindfoot, hip_rotation, knee, rotate_about_line, shoulder, spine, wrist_rotation
from tools.runtime import project_root
from tools.source_validation import load_yaml


def signed_axis_angle(rotation, axis):
    sine = m.dot(axis,[(rotation[2][1]-rotation[1][2])/2,
                       (rotation[0][2]-rotation[2][0])/2,
                       (rotation[1][0]-rotation[0][1])/2])
    cosine = (sum(rotation[i][i] for i in range(3))-1)/2
    return math.degrees(math.atan2(sine,cosine))


class MeasuredActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_yaml(project_root()/"rig/mobility/adult-reference-v1.yaml")
        cls.actions = {a["id"]:a for a in cls.data["actions"]}
        cls.couplings = {c["id"]:c["parameters"] for c in cls.data["couplings"]}
        cls.evaluator = ActionEvaluator(cls.data)

    def test_hip_and_wrist_angles_from_rotation_elements(self):
        for side in ("L","R"):
            for kind,labels in (("hip",["flexion","adduction","external_rotation"]),
                               ("wrist",["flexion","ulnar_deviation"])):
                for index,label in enumerate(labels):
                    action = self.actions[f"{kind}.{side}.{label}"]
                    low,high = action["bounds_deg"]
                    for angle in (low,(low+high)/2,high):
                        inputs = [0]*len(labels);inputs[index] = angle
                        rotation = hip_rotation(*inputs,side=side) if kind == "hip" else wrist_rotation(*inputs,side=side)
                        if side == "L":
                            signs = [-1,1,1]
                            rotation = [[signs[i]*rotation[i][j]*signs[j] for j in range(3)] for i in range(3)]
                        if index == 0: measured = math.degrees(math.atan2(rotation[2][1],rotation[2][2]))
                        elif index == 1: measured = math.degrees(math.atan2(rotation[0][2],rotation[0][0]))
                        else: measured = -math.degrees(math.atan2(rotation[1][0],rotation[0][0]))
                        self.assertLessEqual(abs(measured-angle),.1)

    def test_forearm_angle_from_radial_landmark_trajectory(self):
        for side in ("L","R"):
            action = self.actions[f"forearm.{side}.pronation"]
            params = self.couplings[f"forearm.{side}.rotation"]
            axis,origin = action["axis"],params["axis_start_m"]
            point = [0,0,-.1365*1.7]
            offset = m.sub(point,origin)
            radial = m.sub(offset,m.scale(axis,m.dot(offset,axis)))
            low,high = action["bounds_deg"]
            for angle in (low,(low+high)/2,high):
                moved = rotate_about_line(point,origin,axis,angle-params["neutral_deg"])
                delta = m.sub(moved,origin)
                delta = m.sub(delta,m.scale(axis,m.dot(delta,axis)))
                measured = math.degrees(math.atan2(m.dot(axis,m.cross(radial,delta)),m.dot(radial,delta)))+params["neutral_deg"]
                self.assertLessEqual(abs(measured-angle),.1)
                self.assertAlmostEqual(m.norm(delta),m.norm(radial),places=12)

    def test_shoulder_total_elevation_from_humeral_direction(self):
        for side in ("L","R"):
            for elevation,plane in ((0,0),(40,-180),(20,-90),(168,0),(160,90),(40,180)):
                result = shoulder(self.couplings[f"shoulder.{side}.girdle"],elevation,plane,0,side)
                distal = m.mv(result["total"],[0,0,-1])
                measured = math.degrees(math.acos(max(-1,min(1,-distal[2]))))
                self.assertLessEqual(abs(measured-elevation),.1)
            report = self.evaluator.evaluate({f"shoulder.{side}.elevation":168})
            # Independent forward-plane identity: GH swing = e*(1-1/3-1/10).
            self.assertAlmostEqual(report["measurements"]["shoulder."+side]["glenohumeral_swing_deg"],95.2,places=9)

    def test_knee_ankle_and_hindfoot_bound_angles(self):
        for side in ("L","R"):
            for angle in (0,65,130):
                rotation,_ = knee(self.couplings[f"knee.{side}.tracking"],angle,1.7,side)
                measured = math.degrees(math.atan2(rotation[1][2],rotation[2][2]))
                self.assertLessEqual(abs(measured-angle),.1)
            params = self.couplings[f"hindfoot.{side}.oblique"]
            for angle in (-40,-14,12):
                rotation = ankle_hindfoot(params,angle,0)
                self.assertLessEqual(abs(signed_axis_angle(rotation,[1,0,0])-angle),.1)
            for angle in (-10,5,20):
                rotation = ankle_hindfoot(params,0,angle)
                self.assertLessEqual(abs(signed_axis_angle(rotation,params["axis"])-angle),.1)
            axis = self.couplings[f"mtp.{side}.hinge"]["axis"]
            for angle in (-10,17.5,45):
                self.assertLessEqual(abs(signed_axis_angle(m.rot(axis,angle),axis)-angle),.1)

    def test_spinal_and_pelvis_angles(self):
        for region,count in (("cervical",7),("thoracic",12),("lumbar",5),("pelvis",1)):
            labels = ["pitch","lateral_tilt","yaw"] if region == "pelvis" else ["flexion","lateral_flexion","rotation"]
            for index,label in enumerate(labels):
                low,high = self.actions[region+"."+label]["bounds_deg"]
                for angle in (low,(low+high)/2,high):
                    values = [0,0,0];values[index] = angle
                    rotation = spine(*values,count)
                    axes = [[-1,0,0],[0,1,0],[0,0,1]]
                    measured = signed_axis_angle(rotation,axes[index])*count
                    self.assertLessEqual(abs(measured-angle),.1)
