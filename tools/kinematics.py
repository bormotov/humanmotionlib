# SPDX-License-Identifier: Apache-2.0
"""Rigid anatomical FK with explicit, data-side dependent articulation."""

from tools import math3d as m
from tools.actions import ActionEvaluator, require_valid
from tools.articulation import hip_rotation, knee, patella, shoulder, spine, wrist_rotation
from tools.poses import ordered_bodies, vector3
from tools.guides import compile_guides, solve_guides


class KinematicModel:
    def __init__(self, profile, mobility):
        self.profile, self.mobility = profile,mobility
        self.height = profile["stature_m"]
        self.ordered = ordered_bodies(profile)
        self.bodies = {b["id"]:b for b in self.ordered}
        self.guide_plan = compile_guides(profile)
        self.evaluator = ActionEvaluator(mobility)
        self.couplings = {c["id"]:c["parameters"] for c in mobility["couplings"]}
        self.known = set()
        for side in ("L","R"):
            for prefix,names in (("hip",["flexion","adduction","external_rotation"]),
                                 ("shoulder",["elevation","plane","external_twist"]),
                                 ("elbow",["flexion"]),("forearm",["pronation"]),
                                 ("wrist",["flexion","ulnar_deviation"]),("knee",["flexion"]),
                                 ("ankle",["dorsiflexion"]),("hindfoot",["inversion"]),("mtp",["extension"])):
                self.known.update(f"{prefix}.{side}.{name}" for name in names)
        self.known.update(region+"."+name for region in ("cervical","thoracic","lumbar")
                          for name in ("flexion","lateral_flexion","rotation"))
        self.known.update("pelvis."+name for name in ("x","y","z","pitch","lateral_tilt","yaw"))
        if self.known != set(self.evaluator.defaults):
            raise ValueError("Unsupported independent-action inventory for this anatomical model")
        for index,name in enumerate(("x","y","z")):
            if abs(self.evaluator.defaults["pelvis."+name]-self.bodies["pelvis"]["origin_m"][index]) > 1e-6*self.height:
                raise ValueError("Profile/mobility neutral placement or stature mismatch")

    def solve(self, requested=None, beat=0, world_root=None):
        report = self.evaluator.evaluate(requested,beat)
        values = require_valid(report)
        frames, girdles = {}, {}
        def value(prefix,side,name): return values[f"{prefix}.{side}.{name}"]
        def action_rotation(id):
            return m.mm(frames[id]["rotation"],m.transpose(self.bodies[id]["basis"]))
        def point(id): return self.bodies[id]["origin_m"]
        for body in self.ordered:
            id,parent = body["id"],body["parent"]
            basis = body["basis"]
            if parent is None:
                position,rotation = list(body["origin_m"]),[list(row) for row in basis]
                inherited = [list(row) for row in m.I]
            else:
                inherited = action_rotation(parent)
                position = m.add(frames[parent]["position_m"],m.mv(inherited,m.sub(body["origin_m"],point(parent))))
                rotation = m.mm(inherited,basis)
            side = id.split(".")[-1]
            if id == "pelvis":
                position = [values["pelvis."+name] for name in ("x","y","z")]
                rotation = m.mm(spine(values["pelvis.pitch"],values["pelvis.lateral_tilt"],values["pelvis.yaw"],1),basis)
            elif id[0] in "CTL" and id[1:].isdigit():
                region = {"C":"cervical","T":"thoracic","L":"lumbar"}[id[0]]
                count = self.couplings[region+".distribution"]["count"]
                local = spine(*(values[region+"."+name] for name in ("flexion","lateral_flexion","rotation")),count)
                rotation = m.mm(m.mm(inherited,local),basis)
            elif id.startswith(("clavicle.","scapula.","humerus.")):
                if side not in girdles:
                    girdles[side] = shoulder(self.couplings[f"shoulder.{side}.girdle"],
                        *(value("shoulder",side,name) for name in ("elevation","plane","external_twist")),side)
                solved = girdles[side]
                thorax = action_rotation("T1")
                if id.startswith("clavicle."):
                    local_position = self.couplings[f"shoulder.{side}.girdle"]["sc_m"]
                    local_rotation = solved["clavicle"]
                elif id.startswith("scapula."):
                    local_position,local_rotation = solved["ac_m"],solved["scapula"]
                else:
                    local_position,local_rotation = solved["glenoid_m"],solved["total"]
                position = m.add(frames["T1"]["position_m"],m.mv(thorax,local_position))
                rotation = m.mm(m.mm(thorax,local_rotation),basis)
            elif id.startswith("elbow."):
                rotation = m.mm(m.mm(inherited,m.rx(value("elbow",side,"flexion"))),basis)
            elif id.startswith("radius."):
                axis = self.evaluator.actions[f"forearm.{side}.pronation"]["axis"]
                neutral = self.couplings[f"forearm.{side}.rotation"]["neutral_deg"]
                rotation = m.mm(m.mm(inherited,m.rot(axis,value("forearm",side,"pronation")-neutral)),basis)
            elif id.startswith("wrist."):
                rotation = m.mm(m.mm(inherited,wrist_rotation(value("wrist",side,"flexion"),value("wrist",side,"ulnar_deviation"),side)),basis)
            elif id.startswith("femur."):
                local = hip_rotation(*(value("hip",side,name) for name in ("flexion","adduction","external_rotation")),side)
                rotation = m.mm(m.mm(inherited,local),basis)
            elif id.startswith("knee."):
                local,shift = knee(self.couplings[f"knee.{side}.tracking"],value("knee",side,"flexion"),self.height,side)
                position = m.add(position,m.mv(inherited,shift))
                rotation = m.mm(m.mm(inherited,local),basis)
            elif id.startswith("patella."):
                angle = value("knee",side,"flexion")
                solved = patella(self.couplings[f"patella.{side}.tracking"],angle,self.height,side)
                nominal_knee = point("knee."+side)
                offset = m.add(m.sub(nominal_knee,point(parent)),
                    m.add(m.mv(solved["flexion_rotation"],m.sub(point(id),nominal_knee)),[solved["lateral_m"],0,0]))
                position = m.add(frames[parent]["position_m"],m.mv(inherited,offset))
                rotation = m.mm(m.mm(inherited,solved["rotation"]),basis)
            elif id.startswith("talus."):
                rotation = m.mm(m.mm(inherited,m.rx(value("ankle",side,"dorsiflexion"))),basis)
            elif id.startswith("hindfoot."):
                rotation = m.mm(m.mm(inherited,m.rot(self.couplings[f"hindfoot.{side}.oblique"]["axis"],value("hindfoot",side,"inversion"))),basis)
            elif id.startswith("mtp."):
                rotation = m.mm(m.mm(inherited,m.rot(self.couplings[f"mtp.{side}.hinge"]["axis"],value("mtp",side,"extension"))),basis)
            frames[id] = {"position_m":position,"rotation":rotation}
        if world_root is not None:
            root_rotation = m.qmatrix(world_root["orientation"])
            root_position = vector3(world_root["translation_m"])
            frames = {id:{"position_m":m.add(root_position,m.mv(root_rotation,f["position_m"])),
                          "rotation":m.mm(root_rotation,f["rotation"])} for id,f in frames.items()}
        return {"state":"valid","frames":frames,"actions":values,
                "action_measurements":report["measurements"],"scale":[1,1,1],
                "guides":solve_guides(self.profile,frames,self.guide_plan)}
