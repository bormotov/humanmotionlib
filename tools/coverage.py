# SPDX-License-Identifier: Apache-2.0
"""Enumerated input/pose checks; visual coverage is recorded separately."""

from tools import math3d as m
from tools.actions import ActionError
from tools.kinematics import KinematicModel
from tools.measurements import measure_pose


def action_cases(mobility):
    for action in mobility["actions"]+mobility["placements"]:
        id = action["id"]
        if action.get("mode","independent") != "independent":
            yield id,action.get("mode"),"unsupported_write",{id:action["neutral_deg"]},"unsupported"
            continue
        suffix = "deg" if "bounds_deg" in action else "m"
        low,high = action["bounds_"+suffix]
        neutral = action["neutral_"+suffix]
        delta = .5 if suffix == "deg" else .0005
        companion = {f"shoulder.{id.split('.')[1]}.elevation":1} if id.startswith("shoulder.") and id.endswith(".plane") else {}
        positive = min(high,neutral+delta)
        for label,value,expected in (("positive",positive,"valid"),("lower",low,"valid"),
                                     ("interior",(low+high)/2,"valid"),("upper",high,"valid"),
                                     ("below",low-delta,"out-of-range"),("above",high+delta,"out-of-range")):
            yield id,"independent",label,companion|{id:value},expected


def audit_action_cases(profile,mobility):
    model = KinematicModel(profile,mobility)
    rows = {}
    for id,mode,label,request,expected in action_cases(mobility):
        row = rows.setdefault(id,{"mode":mode,"cases":{},"visual":"pending"})
        try:
            solved = model.solve(request)
            report = measure_pose(profile,mobility,solved["frames"],expected_actions=request)
            state = "valid"
            failed = [c["id"] for c in report["checks"] if c["status"]!="pass"]
            passed = expected==state and not failed
            case = {"expected_state":expected,"observed_state":state,"input":request,
                    "pose_generated":True,"passed":passed,"failed_measurements":failed,
                    "measured_value":report["measured_actions"].get(id)}
        except ActionError as error:
            state = error.report["state"]
            case = {"expected_state":expected,"observed_state":state,"input":request,
                    "pose_generated":False,"passed":state==expected,"errors":error.report["errors"]}
        row["cases"][label] = case
    directions = audit_anatomical_directions(profile,mobility)
    return {"status":"pass" if directions["status"]=="pass" and all(c["passed"] for row in rows.values() for c in row["cases"].values()) else "fail",
            "absolute_anatomical_directions":directions,
            "actions":rows,"scope":"Numeric action/pose coverage in unconstrained context. Rendered floating sweeps and visual review are pending."}


def anatomical_direction_measurement(profile,frames,side,kind):
    """Physical witness directions; no action-angle decoder or solver formulas."""
    bodies = {b["id"]:b for b in profile["structures"]}
    def orientation(id):
        return m.mm(frames[id]["rotation"],m.transpose(bodies[id]["basis"]))
    sign = 1 if side == "R" else -1
    if kind == "hip_external":
        value = sign*m.mv(orientation("hindfoot."+side),[0,1,0])[0]
        bound,meaning = [0,1],"Anterior foot direction turns laterally"
    elif kind == "forearm_midrotation":
        value = m.mv(orientation("radius."+side),[sign,0,0])[2]
        bound,meaning = [.9,1],"Radial/thumb direction points upward with elbow flexed 90 degrees"
    elif kind == "forearm_pronation":
        value = -m.mv(orientation("wrist."+side),[0,1,0])[2]
        bound,meaning = [0,1],"Palm direction turns toward floor with elbow flexed 90 degrees"
    elif kind == "knee_medial":
        value = -sign*m.mv(orientation("tibia."+side),[0,1,0])[0]
        bound,meaning = [0,1],"Anterior tibial direction turns medially"
    else: raise ValueError("Unknown anatomical direction witness")
    return {"id":kind+"."+side,"measured":value,"expected_bounds":bound,
            "unit":"direction cosine","meaning":meaning,
            "status":"pass" if bound[0]<value<=bound[1]+1e-12 else "fail",
            "requirement":"joint-mobility / Explicit joint action model / Verify absolute anatomical directions"}


def audit_anatomical_directions(profile,mobility):
    model = KinematicModel(profile,mobility)
    checks = []
    for side in ("R","L"):
        for kind,request in (
            ("hip_external",{f"hip.{side}.external_rotation":20}),
            ("forearm_midrotation",{f"elbow.{side}.flexion":90,f"forearm.{side}.pronation":0}),
            ("forearm_pronation",{f"elbow.{side}.flexion":90,f"forearm.{side}.pronation":75}),
            ("knee_medial",{f"knee.{side}.flexion":30})):
            frames = model.solve(request)["frames"]
            check = anatomical_direction_measurement(profile,frames,side,kind)
            check["input"] = request;checks.append(check)
    return {"status":"pass" if all(c["status"]=="pass" for c in checks) else "fail",
            "scope":"Absolute physical landmark directions independent of angle decoders", "checks":checks}
