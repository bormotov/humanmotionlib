# SPDX-License-Identifier: Apache-2.0
"""Neutral/T-pose frames and explicit rest-relative FK serialization."""

from copy import deepcopy
import math

from humanmotionlib import math3d as m
from humanmotionlib.source_validation import require_finite


def ordered_bodies(profile):
    pending = {b["id"]:b for b in profile["structures"]}
    if len(pending) != len(profile["structures"]):
        raise ValueError("Duplicate structure identifier")
    ordered, done = [], set()
    while pending:
        ready = sorted(id for id, b in pending.items() if b["parent"] is None or b["parent"] in done)
        if not ready: raise ValueError("Unresolved parent or parent cycle: "+str(sorted(pending)))
        for id in ready:
            ordered.append(pending.pop(id));done.add(id)
    return ordered


def vector3(value):
    if len(value) != 3 or not all(math.isfinite(v) for v in value):
        raise ValueError("Expected finite vector3")
    return list(value)


def neutral_pose(profile):
    result = {}
    for body in ordered_bodies(profile):
        result[body["id"]] = {"position_m":vector3(body["origin_m"]),
                             "rotation":deepcopy(m.validate_basis(body["basis"]))}
    return result


def apply_deltas(profile, channels=None):
    channels = channels or {}
    require_finite(channels)
    bodies = ordered_bodies(profile)
    unknown = set(channels)-{b["id"] for b in bodies}
    if unknown: raise ValueError("Unknown delta structures: "+str(sorted(unknown)))
    result = {}
    for body in bodies:
        delta = channels.get(body["id"], {})
        if set(delta)-{"translation_m", "rotation_delta"}:
            raise ValueError("Unsupported FK channel fields for "+body["id"])
        if body["parent"] is None:
            parent = ([0,0,0], m.I)
        else:
            record = result[body["parent"]]
            parent = (record["position_m"], record["rotation"])
        position, rotation = m.compose(
            parent, vector3(delta.get("translation_m", body["rest_translation_m"])),
            body["rest_orientation"], delta.get("rotation_delta", [1,0,0,0]))
        result[body["id"]] = {"position_m":position, "rotation":rotation}
    return result


def rest_pose(profile):
    return apply_deltas(profile)


def to_deltas(profile, world_frames):
    bodies = ordered_bodies(profile)
    if set(world_frames) != {b["id"] for b in bodies}:
        raise ValueError("World pose structure inventory mismatch")
    require_finite(world_frames)
    result = {}
    for body in bodies:
        frame = world_frames[body["id"]]
        rotation = m.validate_basis(frame["rotation"])
        position = vector3(frame["position_m"])
        if body["parent"] is None:
            pp, pr = [0,0,0], m.I
        else:
            parent = world_frames[body["parent"]]
            pp, pr = vector3(parent["position_m"]), m.validate_basis(parent["rotation"])
        local_r = m.mm(m.transpose(pr), rotation)
        local_p = m.mv(m.transpose(pr), m.sub(position, pp))
        result[body["id"]] = {"translation_m":local_p,
                             "rotation_delta":m.local_delta(body["rest_orientation"], m.quaternion(local_r))}
    return result


def scale_meter_fields(value, factor):
    """Scale dimensioned source fields, leaving angles, bases and H-ratios intact."""
    if not math.isfinite(factor) or factor <= 0:
        raise ValueError("Stature scale must be finite and positive")
    def numbers(item):
        if isinstance(item, list): return [numbers(v) for v in item]
        if isinstance(item, (int, float)) and not isinstance(item, bool): return item*factor
        raise ValueError("Meter field must contain numeric scalars/lists")
    if isinstance(value, dict):
        return {key:numbers(item) if key.endswith("_m") else scale_meter_fields(item, factor)
                for key,item in value.items()}
    if isinstance(value, list): return [scale_meter_fields(item, factor) for item in value]
    return deepcopy(value)


def scaled_profile(profile, stature):
    return scale_meter_fields(profile, stature/profile["stature_m"])
