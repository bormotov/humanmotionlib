# SPDX-License-Identifier: Apache-2.0
"""Measure action/coupling conformance from frames, independently of solving.

No solver/evaluator/articulation routines or success flags are consumed here.
Expected relationships are independently transcribed from the numeric dossier;
the shared math module supplies only previously tested linear algebra.
"""

import math

from tools import math3d as m


def euler_xyz(rotation):
    return [math.degrees(math.atan2(-rotation[1][2],rotation[2][2])),
            math.degrees(math.asin(max(-1.,min(1.,rotation[0][2])))),
            math.degrees(math.atan2(-rotation[0][1],rotation[0][0]))]


def signed_angle(rotation,axis):
    vector = [(rotation[2][1]-rotation[1][2])/2,
              (rotation[0][2]-rotation[2][0])/2,(rotation[1][0]-rotation[0][1])/2]
    return math.degrees(math.atan2(m.dot(vector,axis),(sum(rotation[i][i] for i in range(3))-1)/2))


def smooth_reference(knots,values,angle):
    # Endpoint lookup tolerates measured rounding; raw angles are checked below.
    if angle <= knots[0]: return values[0]
    if angle >= knots[-1]: return values[-1]
    for index in range(len(knots)-1):
        if angle <= knots[index+1]:
            t = (angle-knots[index])/(knots[index+1]-knots[index])
            return values[index]+(values[index+1]-values[index])*(3*t*t-2*t*t*t)
    raise ValueError("Missing reference-curve interval")


class Measurements:
    def __init__(self,beat):
        self.beat,self.checks = beat,[]

    def record(self,id,measured,expected,tolerance,unit,residual,requirement):
        self.checks.append({"id":id,"beat":self.beat,"measured":measured,"expected":expected,
                           "tolerance":tolerance,"unit":unit,"residual":residual,
                           "status":"pass" if residual <= tolerance else "fail",
                           "requirement":requirement})

    def scalar(self,id,measured,expected,tolerance,unit="degrees",requirement="joint-mobility / Coupled motion is observable and constrained"):
        self.record(id,measured,expected,tolerance,unit,abs(measured-expected),requirement)

    def position(self,id,measured,expected,tolerance):
        self.record(id,measured,expected,tolerance,"m",m.norm(m.sub(measured,expected)),
                    "anatomical-skeleton / Rigid structure and bilateral mirroring")

    def rotation(self,id,measured,expected,tolerance=.1):
        self.record(id,measured,expected,tolerance,"degrees",m.angle_error(measured,expected),
                    "joint-mobility / Coupled motion is observable and constrained")

    def limit(self,id,measured,bounds,tolerance,unit="degrees"):
        self.record(id,measured,bounds,tolerance,unit,max(0,bounds[0]-measured,measured-bounds[1]),
                    "joint-mobility / Joint limits are validated without silent correction")


def measure_pose(profile,mobility,frames,beat=0,expected_actions=None,world_root=None):
    height = profile["stature_m"]
    bodies = {b["id"]:b for b in profile["structures"]}
    actions = {a["id"]:a for a in mobility["actions"]+mobility["placements"]}
    params = {c["id"]:c["parameters"] for c in mobility["couplings"]}
    checks = Measurements(beat)
    measured = {}
    required = {id for id,b in bodies.items() if b["representation"] != "omitted"}
    missing = required-set(frames)
    if missing:
        checks.scalar("frame.inventory",len(missing),0,0,"count")
        return {"status":"fail","checks":checks.checks,"measured_actions":{},"missing":sorted(missing)}
    valid = True
    for id in sorted(required):
        try:
            m.validate_basis(frames[id]["rotation"])
            if len(frames[id]["position_m"]) != 3 or not all(math.isfinite(x) for x in frames[id]["position_m"]):
                raise ValueError("Invalid position")
            error = 0
        except (ValueError,KeyError,TypeError):
            error,valid = 1,False
        checks.scalar(id+".valid_frame",error,0,0,"boolean")
    if not valid: return {"status":"fail","checks":checks.checks,"measured_actions":{}}
    def ar(id): return m.mm(frames[id]["rotation"],m.transpose(bodies[id]["basis"]))
    def pos(id): return frames[id]["position_m"]
    def neutral(id): return bodies[id]["origin_m"]
    def reference(rotation,side): return rotation if side == "R" else [[(-1 if i==0 else 1)*rotation[i][j]*(-1 if j==0 else 1) for j in range(3)] for i in range(3)]
    root_rotation = m.qmatrix(world_root["orientation"]) if world_root else m.I
    root_position = world_root["translation_m"] if world_root else [0,0,0]
    pelvis_angles = euler_xyz(m.mm(m.transpose(root_rotation),ar("pelvis")))
    for name,value in zip(("pitch","lateral_tilt","yaw"),[-pelvis_angles[0],pelvis_angles[1],pelvis_angles[2]]): measured["pelvis."+name] = value
    pelvis_position = m.mv(m.transpose(root_rotation),m.sub(pos("pelvis"),root_position))
    for name,value in zip(("x","y","z"),pelvis_position):measured["pelvis."+name] = value
    driven = {a["joint"] for a in mobility["actions"] if a["mode"] in ("independent","coupled")}
    position_drivers = {"scapula.L","scapula.R","humerus.L","humerus.R","knee.L","knee.R","patella.L","patella.R"}
    for id in sorted(required):
        body = bodies[id];parent = body["parent"]
        if parent is None: continue
        inherited = ar(parent)
        if id not in position_drivers:
            expected = m.add(pos(parent),m.mv(inherited,m.sub(neutral(id),neutral(parent))))
            checks.position(id+".fixed_origin",pos(id),expected,1e-4*height)
        if id not in driven and not (id[0] in "CTL" and id[1:].isdigit()):
            checks.rotation(id+".fixed_rotation",frames[id]["rotation"],m.mm(inherited,body["basis"]))
    for side in ("R","L"):
        sign = 1 if side == "R" else -1
        hip = reference(m.mm(m.transpose(ar("pelvis")),ar("femur."+side)),side)
        hip_f,hip_b,hip_r = euler_xyz(hip)
        for name,value in zip(("flexion","adduction","external_rotation"),(hip_f,hip_b,-hip_r)):
            measured[f"hip.{side}.{name}"] = value
        torso = ar("T1")
        total = m.mm(m.transpose(torso),ar("humerus."+side))
        distal = m.mv(total,[0,0,-1])
        horizontal = math.hypot(distal[0],distal[1])
        elevation = math.degrees(math.atan2(horizontal,-distal[2]))
        # Azimuth is undefined at zero elevation. The frame contract permits
        # 1e-6 element uncertainty, so sub-contract horizontal noise cannot
        # identify an azimuth; the source convention is canonical zero there.
        plane = math.degrees(math.atan2(sign*distal[0],distal[1])) if horizontal > 1e-6 else 0.
        axis = [math.cos(math.radians(plane)),-sign*math.sin(math.radians(plane)),0]
        base = m.rot(axis,elevation)
        twist_r = m.mm(m.transpose(base),total)
        twist = -sign*math.degrees(math.atan2(twist_r[1][0],twist_r[0][0]))
        for name,value in zip(("elevation","plane","external_twist"),(elevation,plane,twist)):
            measured[f"shoulder.{side}.{name}"] = value
        p = params[f"shoulder.{side}.girdle"]
        cf,sf = p["clavicle_factors"],p["scapula_factors"]
        c_ref = m.mm(m.rz(sign*elevation*cf[0]),m.mm(m.ry(sign*elevation*cf[1]),m.rot(m.sub(p["ac_m"],p["sc_m"]),sign*elevation*cf[2])))
        g_ref = m.mm(m.rot(axis,elevation*sf[0]),m.mm(m.rx(elevation*sf[1]),m.rz(sign*elevation*sf[2])))
        actual_c = m.mm(m.transpose(torso),ar("clavicle."+side))
        actual_g = m.mm(m.transpose(torso),ar("scapula."+side))
        checks.rotation(f"shoulder.{side}.clavicle_curve",actual_c,c_ref)
        checks.rotation(f"shoulder.{side}.scapula_curve",actual_g,g_ref)
        ac_ref = m.add(p["sc_m"],m.mv(c_ref,m.sub(p["ac_m"],p["sc_m"])))
        gh_ref = m.add(ac_ref,m.mv(g_ref,m.sub(p["glenoid_m"],p["ac_m"])))
        checks.position(f"shoulder.{side}.ac_curve",pos("scapula."+side),m.add(pos("T1"),m.mv(torso,ac_ref)),1e-4*height)
        checks.position(f"shoulder.{side}.glenoid_curve",pos("humerus."+side),m.add(pos("T1"),m.mv(torso,gh_ref)),1e-4*height)
        gh_actual = m.mm(m.transpose(actual_g),total)
        swing = math.degrees(math.acos(max(-1.,min(1.,gh_actual[2][2]))))
        gh_twist = -sign*math.degrees(math.atan2(gh_actual[1][0]-gh_actual[0][1],gh_actual[0][0]+gh_actual[1][1]))
        sector = params[f"shoulder.{side}.sector"]
        checks.limit(f"glenohumeral.{side}.swing",swing,[0,sector["gh_swing_max_deg"]],.1)
        checks.limit(f"glenohumeral.{side}.twist",gh_twist,[-sector["gh_twist_max_deg"],sector["gh_twist_max_deg"]],.1)
        elbow = m.mm(m.transpose(ar("humerus."+side)),ar("elbow."+side))
        flex = math.degrees(math.atan2(elbow[2][1],elbow[2][2]))
        measured[f"elbow.{side}.flexion"] = flex
        checks.rotation(f"elbow.{side}.hinge",elbow,m.rx(flex))
        forearm_axis = actions[f"forearm.{side}.pronation"]["axis"]
        roll = m.mm(m.transpose(ar("elbow."+side)),ar("radius."+side))
        delta = signed_angle(roll,forearm_axis)
        forearm = params[f"forearm.{side}.rotation"]
        measured[f"forearm.{side}.pronation"] = delta+forearm["neutral_deg"]
        checks.rotation(f"forearm.{side}.axis",roll,m.rot(forearm_axis,delta))
        checks.rotation(f"forearm.{side}.ulna_fixed",m.mm(m.transpose(ar("elbow."+side)),ar("ulna."+side)),m.I)
        wrist_point = m.sub(neutral("wrist."+side),neutral("elbow."+side))
        expected_wrist = m.add(forearm["axis_start_m"],m.mv(roll,m.sub(wrist_point,forearm["axis_start_m"])))
        checks.position(f"forearm.{side}.radiocarpal_curve",pos("wrist."+side),m.add(pos("elbow."+side),m.mv(ar("elbow."+side),expected_wrist)),1e-4*height)
        wrist = reference(m.mm(m.transpose(ar("radius."+side)),ar("wrist."+side)),side)
        f,b,r = euler_xyz(wrist)
        measured[f"wrist.{side}.flexion"],measured[f"wrist.{side}.ulnar_deviation"] = f,b
        checks.limit(f"wrist.{side}.fixed_axial",r,[0,0],.1)
        k_actual = m.mm(m.transpose(ar("femur."+side)),ar("tibia."+side))
        k = math.degrees(math.atan2(k_actual[1][2],k_actual[2][2]))
        measured[f"knee.{side}.flexion"] = k
        p = params[f"knee.{side}.tracking"]
        t = min(1,max(0,k/p["transition_deg"]))
        z = -sign*p["twist_deg"]*(3*t*t-2*t*t*t)
        k_ref = m.mm(m.rx(-k),m.rz(z))
        checks.rotation(f"knee.{side}.dependent_twist",k_actual,k_ref)
        factors = p["translation_factors_h"]
        shift = [sign*factors[0]*height,factors[1]*math.sin(math.radians(k))*height,factors[2]*(1-math.cos(math.radians(k)))*height]
        knee_ref = m.add(pos("femur."+side),m.mv(ar("femur."+side),m.add(m.sub(neutral("knee."+side),neutral("femur."+side)),shift)))
        checks.position(f"knee.{side}.rollback",pos("knee."+side),knee_ref,1e-4*height)
        p = params[f"patella.{side}.tracking"]
        lateral = sign*smooth_reference(p["knots_deg"],p["lateral_h"],k)*height
        tilt = sign*smooth_reference(p["knots_deg"],p["tilt_deg"],k)
        patella_flex = m.rx(-p["flexion_factor"]*k)
        patella_ref = m.add(m.sub(neutral("knee."+side),neutral("femur."+side)),
            m.add(m.mv(patella_flex,m.sub(neutral("patella."+side),neutral("knee."+side))),[lateral,0,0]))
        checks.position(f"patella.{side}.tracking",pos("patella."+side),m.add(pos("femur."+side),m.mv(ar("femur."+side),patella_ref)),1e-4*height)
        checks.rotation(f"patella.{side}.rotation",ar("patella."+side),m.mm(ar("femur."+side),m.mm(patella_flex,m.rz(tilt))))
        ankle = m.mm(m.transpose(ar("tibia."+side)),ar("talus."+side))
        a = math.degrees(math.atan2(ankle[2][1],ankle[2][2]))
        measured[f"ankle.{side}.dorsiflexion"] = a
        checks.rotation(f"ankle.{side}.axis",ankle,m.rx(a))
        hindfoot = m.mm(m.transpose(ar("talus."+side)),ar("hindfoot."+side))
        axis = params[f"hindfoot.{side}.oblique"]["axis"]
        inversion = signed_angle(hindfoot,axis)
        measured[f"hindfoot.{side}.inversion"] = inversion
        checks.rotation(f"hindfoot.{side}.oblique_axis",hindfoot,m.rot(axis,inversion))
        toe = m.mm(m.transpose(ar("hindfoot."+side)),ar("mtp."+side))
        axis = params[f"mtp.{side}.hinge"]["axis"]
        extension = signed_angle(toe,axis)
        measured[f"mtp.{side}.extension"] = extension
        checks.rotation(f"mtp.{side}.axis",toe,m.rot(axis,extension))
    for region,prefix,count in (("cervical","C",7),("thoracic","T",12),("lumbar","L",5)):
        local_rotations = []
        for index in range(count,0,-1):
            id = prefix+str(index)
            local_rotations.append((id,m.mm(m.transpose(ar(bodies[id]["parent"])),ar(id))))
        triples = [euler_xyz(rotation) for id,rotation in local_rotations]
        total = [-sum(v[0] for v in triples),sum(v[1] for v in triples),sum(v[2] for v in triples)]
        labels = ("flexion","lateral_flexion","rotation")
        for label,value in zip(labels,total):measured[region+"."+label] = value
        expected = [expected_actions.get(region+"."+label,value) if expected_actions else value for label,value in zip(labels,total)]
        per_joint = m.mm(m.rx(-expected[0]/count),m.mm(m.ry(expected[1]/count),m.rz(expected[2]/count)))
        for id,rotation in local_rotations: checks.rotation(id+".distribution",rotation,per_joint)
    for id,action in sorted(actions.items()):
        if action.get("mode","independent") != "independent": continue
        if id not in measured:
            checks.scalar(id+".missing_measurement",1,0,0,"boolean")
            continue
        suffix = "deg" if "bounds_deg" in action else "m"
        tolerance = .1 if suffix == "deg" else 1e-4*height
        checks.limit(id+".limit",measured[id],action["bounds_"+suffix],tolerance,"degrees" if suffix=="deg" else "m")
        if expected_actions is not None and id in expected_actions:
            difference = measured[id]-expected_actions[id]
            residual = abs((difference+180)%360-180) if suffix=="deg" else abs(difference)
            checks.record(id+".intent",measured[id],expected_actions[id],tolerance,"degrees" if suffix=="deg" else "m",residual,
                          "joint-mobility / Diagnostic sources are explicit and reusable")
    for coupling in mobility["couplings"]:
        p = coupling["parameters"]
        if coupling["type"] == "multiaxis_envelope":
            score,minimum = 0.,0.
            for id in p["action_ids"]:
                denominator = actions[id]["bounds_deg"][1] if measured[id]>=0 else -actions[id]["bounds_deg"][0]
                score += (measured[id]/denominator)**2
                minimum += (max(0,abs(measured[id])-.1)/denominator)**2
            checks.limit(coupling["id"],score,[0,1],max(1e-9,score-minimum),"ratio")
            checks.checks[-1]["tolerance_basis"] = "Propagated 0.1-degree action-measurement tolerance; commanded envelopes remain exact"
        elif coupling["type"] == "spine_budget":
            checks.limit(coupling["id"],sum(measured[id] for id in p["action_ids"]),p["bounds_deg"],.1)
        elif coupling["type"] == "shoulder_sector":
            side = coupling["id"].split(".")[1]
            e,psi,tau = [measured[f"shoulder.{side}.{name}"] for name in ("elevation","plane","external_twist")]
            knots = p["azimuth_deg"]
            def sector_max(angle):
                angle = (angle+180)%360-180
                for index in range(len(knots)-1):
                    if knots[index] <= angle <= knots[index+1]:
                        t = (angle-knots[index])/(knots[index+1]-knots[index])
                        return p["elevation_deg"][index]*(1-t)+p["elevation_deg"][index+1]*t
                raise ValueError("Missing shoulder sector")
            maximum = sector_max(psi)
            bounds = actions[f"shoulder.{side}.external_twist"]["bounds_deg"]
            denom = bounds[1] if tau>=0 else -bounds[0]
            candidates = [psi-.1,psi,psi+.1]+[k for k in knots if abs((k-psi+180)%360-180)<=.1]
            possible_maximum = max(sector_max(angle) for angle in candidates)
            score = (e/maximum)**2+(tau/denom)**2
            minimum = (max(0,e-.1)/possible_maximum)**2+(max(0,abs(tau)-.1)/denom)**2
            checks.limit(coupling["id"],score,[0,1],max(1e-9,score-minimum),"ratio")
            checks.checks[-1]["tolerance_basis"] = "Propagated 0.1-degree elevation/plane/twist measurement tolerance; commanded sectors remain exact"
    return {"status":"fail" if any(c["status"]!="pass" for c in checks.checks) else "pass",
            "checks":checks.checks,"measured_actions":measured,
            "scope":"Action, frame and coupling measurements; geometry/contact/render acceptance is separate."}
