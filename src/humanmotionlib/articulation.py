# SPDX-License-Identifier: Apache-2.0
"""Closed anatomical coupling formulas, parameterized by canonical records."""

import math

from humanmotionlib import math3d as m


def reflected(rotation, side):
    if side not in ("R","L"): raise ValueError("Expected anatomical side R or L")
    return rotation if side == "R" else m.mirror_rotation(rotation)


def hip_rotation(flexion, adduction, external, side="R"):
    return reflected(m.mm(m.mm(m.rx(flexion),m.ry(adduction)),m.rz(-external)),side)


def wrist_rotation(flexion, ulnar, side="R"):
    return reflected(m.mm(m.rx(flexion),m.ry(ulnar)),side)


def linear_sample(knots, values, x):
    if x < knots[0]-1e-9 or x > knots[-1]+1e-9:
        raise ValueError("Curve input outside declared domain")
    for i in range(len(knots)-1):
        if x <= knots[i+1]:
            t = (x-knots[i])/(knots[i+1]-knots[i])
            return values[i]+t*(values[i+1]-values[i])
    return values[-1]


def smooth_sample(knots, values, x):
    if x < knots[0]-1e-9 or x > knots[-1]+1e-9:
        raise ValueError("Curve input outside declared domain")
    for i in range(len(knots)-1):
        if x <= knots[i+1]:
            t = (x-knots[i])/(knots[i+1]-knots[i])
            return values[i]+(3*t*t-2*t*t*t)*(values[i+1]-values[i])
    return values[-1]


def shoulder(params, elevation, plane, twist, side="R"):
    if side not in ("R","L"): raise ValueError("Expected anatomical side R or L")
    sign = 1 if side == "R" else -1
    angle = math.radians(plane)
    axis = [math.cos(angle),-sign*math.sin(angle),0]
    sc,ac,gh = params["sc_m"],params["ac_m"],params["glenoid_m"]
    vector = m.sub(ac,sc)
    cf,sf = params["clavicle_factors"],params["scapula_factors"]
    clavicle = m.mm(m.mm(m.rz(sign*elevation*cf[0]),m.ry(sign*elevation*cf[1])),
                    m.rot(vector,sign*elevation*cf[2]))
    scapula = m.mm(m.mm(m.rot(axis,elevation*sf[0]),m.rx(elevation*sf[1])),
                   m.rz(sign*elevation*sf[2]))
    total = m.mm(m.rot(axis,elevation),m.rz(-sign*twist))
    moved_ac = m.add(sc,m.mv(clavicle,vector))
    moved_gh = m.add(moved_ac,m.mv(scapula,m.sub(gh,ac)))
    return {"clavicle":clavicle,"scapula":scapula,"total":total,
            "glenohumeral":m.mm(m.transpose(scapula),total),
            "ac_relative":m.mm(m.transpose(clavicle),scapula),
            "ac_m":moved_ac,"glenoid_m":moved_gh}


def swing_twist(rotation, axis=(0,0,-1)):
    q = m.quaternion(rotation)
    projection = m.dot(q[1:],axis)
    magnitude = math.hypot(q[0],projection)
    if magnitude < 1e-12: return 180.,0.
    twist = 2*math.degrees(math.atan2(projection,q[0]))
    twist = (twist+180)%360-180
    direction = m.mv(rotation,axis)
    swing = math.degrees(math.acos(max(-1.,min(1.,m.dot(direction,axis)))))
    return swing,twist


def knee(params, flexion, stature, side="R"):
    t = min(1.,max(0.,flexion/params["transition_deg"]))
    twist = params["twist_deg"]*(3*t*t-2*t*t*t)
    factors = params["translation_factors_h"]
    a = math.radians(flexion)
    translation = [factors[0]*stature,factors[1]*math.sin(a)*stature,
                   factors[2]*(1-math.cos(a))*stature]
    if side == "L": translation = m.mirror_position(translation)
    return reflected(m.mm(m.rx(-flexion),m.rz(-twist)),side),translation


def patella(params, flexion, stature, side="R"):
    lateral = smooth_sample(params["knots_deg"],params["lateral_h"],flexion)*stature
    tilt = smooth_sample(params["knots_deg"],params["tilt_deg"],flexion)
    rotation = m.mm(m.rx(-params["flexion_factor"]*flexion),m.rz(tilt))
    return {"rotation":reflected(rotation,side),
            "flexion_rotation":m.rx(-params["flexion_factor"]*flexion),
            "lateral_m":lateral if side == "R" else -lateral,"tilt_deg":tilt}


def spine(flexion, lateral, rotation, count):
    return m.mm(m.mm(m.rx(-flexion/count),m.ry(lateral/count)),m.rz(rotation/count))


def ankle_hindfoot(params, dorsiflexion, inversion):
    return m.mm(m.rx(dorsiflexion),m.rot(params["axis"],inversion))


def rotate_about_line(point, origin, axis, angle):
    return m.add(origin,m.mv(m.rot(axis,angle),m.sub(point,origin)))
