# SPDX-License-Identifier: Apache-2.0
"""X-plane mirroring with proper rotations, stable side IDs and outward faces."""

from copy import deepcopy
import re

from tools import math3d as m


def swap_side(identifier):
    if identifier.endswith("_L"): return identifier[:-2]+"_R"
    if identifier.endswith("_R"): return identifier[:-2]+"_L"
    if re.match(r"left[A-Z]", identifier): return "right"+identifier[4:]
    if re.match(r"right[A-Z]", identifier): return "left"+identifier[5:]
    return ".".join({"L":"R", "R":"L"}.get(part,part) for part in identifier.split("."))


def mirror_quaternion(q):
    return m.quaternion(m.mirror_rotation(m.qmatrix(q)))


def mirror_structure(source):
    result = deepcopy(source)
    result["id"] = swap_side(source["id"])
    result["parent"] = None if source["parent"] is None else swap_side(source["parent"])
    result["description"] = re.sub(r"\b[LR]\b", lambda match:{"L":"R","R":"L"}[match[0]],source["description"])
    result["origin_m"] = m.mirror_position(source["origin_m"])
    result["basis"] = m.mirror_basis(source["basis"])
    result["rest_translation_m"] = m.mirror_position(source["rest_translation_m"])
    result["rest_orientation"] = mirror_quaternion(source["rest_orientation"])
    result["landmarks"] = [swap_side(id) for id in source["landmarks"]]
    for primitive in result["geometry"]:
        primitive["id"] = swap_side(primitive["id"])
        if "center_m" in primitive: primitive["center_m"] = m.mirror_position(primitive["center_m"])
        if "points_m" in primitive: primitive["points_m"] = [m.mirror_position(p) for p in primitive["points_m"]]
        if "faces" in primitive: primitive["faces"] = [list(reversed(face)) for face in primitive["faces"]]
        if "target" in primitive: primitive["target"] = swap_side(primitive["target"])
        for binding in primitive.get("bindings",[]):
            for key in ('structure', 'guide', 'offset_frame'):
                if key in binding: binding[key] = swap_side(binding[key])
            for key in ('position_m', 'offset_m'):
                if key in binding: binding[key] = m.mirror_position(binding[key])
    for attachment in result["attachments"]:
        attachment["id"] = swap_side(attachment["id"])
        attachment["position_m"] = m.mirror_position(attachment["position_m"])
        attachment["orientation"] = mirror_quaternion(attachment["orientation"])
    return result


def mirror_pose(frames):
    return {swap_side(id):{"position_m":m.mirror_position(frame["position_m"]),
                           "rotation":m.mirror_rotation(frame["rotation"])}
            for id,frame in frames.items()}


def mirror_fixture(source):
    result = deepcopy(source)
    result["id"] = swap_side(result["id"])
    result["controls"] = [swap_side(id) for id in result["controls"]]
    result["rest_policy"]["base_fixture"] = swap_side(result["rest_policy"]["base_fixture"])
    result["construction"]["side"] = swap_side(result["construction"]["side"])
    for track in result["tracks"]: track["channel"] = swap_side(track["channel"])
    result["world_root"]["translation_m"] = m.mirror_position(result["world_root"]["translation_m"])
    result["world_root"]["orientation"] = mirror_quaternion(result["world_root"]["orientation"])
    for contact in result["contacts"]:
        contact["foot"] = swap_side(contact["foot"])
        contact["anchors"] = [swap_side(id) for id in contact["anchors"]]
        contact["targets_m"] = [m.mirror_position(p) for p in contact["targets_m"]]
    for terminal in result["terminal_contacts"]: terminal["foot"] = swap_side(terminal["foot"])
    return result
