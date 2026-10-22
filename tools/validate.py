# SPDX-License-Identifier: Apache-2.0
"""Validate source schemas and references; never claim render acceptance."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import math3d as m
from tools.runtime import backend_contract, project_root
from tools.source_validation import SourceValidationError, load_yaml, validate_document


GROUPS = {"pelvis", "torso", "head_neck", "arm_L", "arm_R", "leg_L", "leg_R"}
REQUIRED_HUMANOID = {"hips", "spine", "head", "leftUpperLeg", "leftLowerLeg", "leftFoot",
                    "rightUpperLeg", "rightLowerLeg", "rightFoot", "leftUpperArm", "leftLowerArm",
                    "leftHand", "rightUpperArm", "rightLowerArm", "rightHand"}


def fail(identifier, field, message):
    raise SourceValidationError(f"{identifier} {field}: {message}")


def index_records(records, field):
    result = {}
    for record in records:
        identifier = record["id"]
        if identifier in result: fail(identifier, field, "duplicate identifier")
        result[identifier] = record
    return result


def load_sources(profile, root=None):
    root = Path(root or project_root())
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", profile):
        fail(profile, "profile", "invalid profile identifier")
    paths = {"profile": root/f"rig/profiles/{profile}.yaml",
             "mobility": root/f"rig/mobility/{profile}.yaml",
             "body-groups": root/"rig/body-groups.yaml",
             "humanoid-map": root/"rig/humanoid-map.yaml",
             "review-scene": root/"scenes/skeleton-review.yaml"}
    result = {}
    for name, path in paths.items():
        if not path.is_file(): fail(profile, str(path.relative_to(root)), "required source missing")
        result[name] = load_yaml(path)
    fixtures = sorted((root/"rig/diagnostics").glob("*.yaml"))
    if not fixtures: fail(profile, "rig/diagnostics", "no diagnostic sources")
    result["diagnostics"] = [load_yaml(path) for path in fixtures]
    return result, list(paths.values())+fixtures


def check_provenance(record, register):
    if "provenance" not in record: return
    p = record["provenance"]
    identifier = record.get("id", "source")
    if p["license"] != "CC-BY-4.0": fail(identifier, "provenance.license", "authored data must retain CC-BY-4.0")
    if p["kind"] == "adapted" and not p["sources"]:
        fail(identifier, "provenance.sources", "adapted material has no registered source")
    for source in p["sources"]:
        material = source["material"]
        rows = [row for row in register.splitlines() if row.startswith("| `"+material+"`:")]
        if len(rows) != 1: fail(identifier, "provenance.sources", f"unresolved material {material}")
        cells = rows[0].split("|")
        if len(cells) < 8 or "https://" not in cells[2] or "https://" not in cells[3]:
            fail(identifier, "provenance.sources", f"incomplete permission register entry {material}")
        license_cell = cells[3]
        if any(token in license_cell for token in ("CC BY-NC", "CC-BY-NC", "CC BY-ND", "CC-BY-ND")):
            fail(identifier, "provenance.sources", f"incompatible license for {material}")
        if not any(license in license_cell for license in ("CC BY 4.0", "MIT", "Apache-2.0", "Creative Commons Attribution License")):
            fail(identifier, "provenance.sources", f"uncleared license for {material}")


def walk_records(value):
    if isinstance(value, dict):
        if "provenance" in value: yield value
        for child in value.values(): yield from walk_records(child)
    elif isinstance(value, list):
        for child in value: yield from walk_records(child)


def validate_bundle(bundle, root=None):
    root = Path(root or project_root())
    for name in ("profile", "mobility", "body-groups", "humanoid-map", "review-scene"):
        validate_document(bundle[name], name, root)
    for fixture in bundle["diagnostics"]: validate_document(fixture, "diagnostic", root)
    register = (root/"docs/used-materials.md").read_text()
    for record in walk_records(bundle): check_provenance(record, register)
    profile, mobility = bundle["profile"], bundle["mobility"]
    bodies = index_records(profile["structures"], "structures")
    from tools.balance import validate_mass_model
    try: validate_mass_model(profile)
    except (ValueError,KeyError,TypeError) as error: fail(profile['id'], 'mass_model', str(error))
    landmarks = index_records(profile["landmarks"], "landmarks")
    attachments, primitives = {}, {}
    for body in bodies.values():
        identifier = body["id"]
        try:
            m.validate_basis(body["basis"]); m.validate_quaternion(body["rest_orientation"])
        except ValueError as error: fail(identifier, "frame", str(error))
        current, seen = body, set()
        while current["parent"] is not None:
            if current["id"] in seen: fail(identifier, "parent", "parent cycle")
            seen.add(current["id"])
            if current["parent"] not in bodies: fail(current["id"], "parent", "unresolved "+current["parent"])
            current = bodies[current["parent"]]
        for name in body["landmarks"]:
            if name not in landmarks: fail(identifier, "landmarks", "unresolved "+name)
        for attachment in body["attachments"]:
            name = attachment["id"]
            if name in attachments: fail(name, "attachments", "duplicate identifier")
            try: m.validate_quaternion(attachment["orientation"])
            except ValueError as error: fail(name, "orientation", str(error))
            attachments[name] = (identifier, attachment)
        local_ids = {g["id"] for g in body["geometry"]}
        for primitive in body["geometry"]:
            name = primitive["id"]
            if name in primitives: fail(name, "geometry", "duplicate identifier")
            primitives[name] = primitive
            if primitive["type"] == "recess" and primitive["target"] not in local_ids:
                fail(name, "target", "unresolved recess target")
            if primitive["type"] == "shell":
                if any(i >= len(primitive["points_m"]) for face in primitive["faces"] for i in face):
                    fail(name, "faces", "vertex index outside shell points")
            bindings = primitive.get("bindings",[])
            if bindings and body["rigid"]: fail(name, "bindings", "rigid structure cannot be deformed")
            indices = set()
            for binding in bindings:
                index = binding["point_index"]
                if index in indices or index >= len(primitive["points_m"]): fail(name, "bindings", "duplicate or invalid point index")
                indices.add(index)
    from tools.guides import compile_guides
    try:
        compile_guides(profile)
    except ValueError as error:
        fail(profile['id'], 'geometry.bindings', str(error))
    for record in landmarks.values():
        if record["frame"] not in bodies and record["frame"] != "world": fail(record["id"], "frame", "unresolved frame")
        if record.get("attachment_body") is not None and record["attachment_body"] not in bodies:
            fail(record["id"], "attachment_body", "unresolved rigid attachment")
    if mobility["profile"] != profile["id"]: fail(mobility["id"], "profile", "profile mismatch")
    actions = index_records(mobility["actions"]+mobility["placements"], "actions/placements")
    for action in actions.values():
        identifier = action["id"]
        if action["joint"] not in bodies: fail(identifier, "joint", "unresolved body")
        if action["frame"] not in bodies and action["frame"] != "world": fail(identifier, "frame", "unresolved frame")
        if abs(m.norm(action["axis"])-1) > 1e-6: fail(identifier, "axis", "non-unit action axis")
        suffix = "deg" if "bounds_deg" in action else "m"
        lo, hi = action["bounds_"+suffix]
        if not lo <= action["neutral_"+suffix] <= hi: fail(identifier, "bounds_"+suffix, "unordered bounds or neutral outside limits")
    for coupling in index_records(mobility["couplings"], "couplings").values():
        for name in coupling["action_ids"]:
            if name not in actions: fail(coupling["id"], "action_ids", "unresolved "+name)
        params = coupling["parameters"]
        if coupling["type"] == "patella_tracking" and not len(params["knots_deg"]) == len(params["lateral_h"]) == len(params["tilt_deg"]):
            fail(coupling["id"], "parameters", "curve sample lengths disagree")
        if coupling["type"] == "shoulder_sector" and len(params["azimuth_deg"]) != len(params["elevation_deg"]):
            fail(coupling["id"], "parameters", "sector sample lengths disagree")
    groups = index_records(bundle["body-groups"]["groups"], "groups")
    if set(groups) != GROUPS: fail("body-groups", "groups", "smallest group inventory mismatch")
    owners = {}
    for group in groups.values():
        for channel in group["channels"]:
            if channel in owners: fail(channel, "group", "overlapping channel ownership")
            owners[channel] = group["id"]
    expected_channels = set(actions) | {name+".transform" for name,b in bodies.items() if b["representation"] != "omitted"}
    if set(owners) != expected_channels: fail("body-groups", "channels", "missing or unknown channels: "+str(sorted(set(owners)^expected_channels)))
    for action in actions.values():
        if owners[action["id"]] != action["group"]: fail(action["id"], "group", "action ownership mismatch")
    for side in ("L", "R"):
        for name in ("clavicle", "scapula", "wrist", "hand"):
            if owners[f"{name}.{side}.transform"] != "arm_"+side: fail(name, "group", "arm ownership required")
        for name in ("hindfoot", "mtp"):
            if owners[f"{name}.{side}.transform"] != "leg_"+side: fail(name, "group", "leg ownership required")
    mapping = bundle["humanoid-map"]
    if mapping["profile"] != profile["id"]: fail(mapping["id"], "profile", "profile mismatch")
    if set(mapping["required"]) != REQUIRED_HUMANOID: fail(mapping["id"], "required", "required vocabulary mismatch")
    semantics = {}
    for entry in mapping["entries"]:
        name, target = entry["humanoid"], entry["target"]
        if name in semantics: fail(name, "mapping", "duplicate humanoid entry")
        if target not in bodies or bodies[target]["representation"] == "omitted": fail(name, "target", "unavailable target")
        if bodies[target]["kind"] == "helper": fail(name, "target", "helper cannot be a public humanoid bone")
        if entry["group"] != owners[target+".transform"]: fail(name, "group", "target ownership mismatch")
        semantics[name] = target
    if not REQUIRED_HUMANOID <= semantics.keys(): fail(mapping["id"], "entries", "required semantic missing")
    if set(semantics) & {e["humanoid"] for e in mapping["omissions"]}: fail(mapping["id"], "omissions", "mapped semantic also omitted")
    unmapped = {id for id,b in bodies.items() if b["representation"] != "omitted"} - set(semantics.values())
    if set(mapping["internal_only"]) != unmapped: fail(mapping["id"], "internal_only", "unmapped inventory mismatch")
    fixtures = index_records(bundle["diagnostics"], "diagnostics")
    for required in ("rest", "neutral"):
        if required not in fixtures: fail("diagnostics", required, "named base fixture missing")
    for fixture in fixtures.values():
        identifier, duration = fixture["id"], fixture["duration_beats"]
        if fixture["profile"] != profile["id"]: fail(identifier, "profile", "profile mismatch")
        base = fixture["rest_policy"]["base_fixture"]
        if base not in fixtures: fail(identifier, "rest_policy", "unresolved base fixture")
        if fixture["rest_policy"]["policy"] == "free" and set(fixture["controls"]) != GROUPS:
            fail(identifier, "rest_policy", "free channels have no parallel writer in diagnostic/v1")
        try: m.validate_quaternion(fixture["world_root"]["orientation"])
        except ValueError as error: fail(identifier, "world_root", str(error))
        writers = set()
        for track in fixture["tracks"]:
            channel = track["channel"]
            if channel not in actions: fail(identifier, "tracks.channel", "unresolved "+channel)
            if channel in writers: fail(identifier, "tracks", "conflicting writers for "+channel)
            writers.add(channel)
            if actions[channel].get("mode") in ("fixed", "coupled"): fail(identifier, "tracks.channel", "unsupported independent writer "+channel)
            if owners[channel] not in fixture["controls"]: fail(identifier, "controls", "omitted control for "+channel)
            beats = [key["beat"] for key in track["keys"]]
            if beats != sorted(set(beats)) or beats[-1] > duration: fail(identifier, "tracks.keys", "unordered or out-of-duration keys")
            if any(beat!=int(beat) for beat in beats):fail(identifier,'tracks.keys','fractional events are outside diagnostic/v1')
        kind = fixture["construction"]["type"]
        required_controls = GROUPS if identifier in ("rest", "neutral") else set()
        if kind == "squat_closed": required_controls = {"pelvis","torso","leg_L","leg_R","arm_L","arm_R"}
        if kind == "walking_flat": required_controls = {"leg_L","leg_R","arm_L","arm_R"}
        if kind == "forefoot_rocker": required_controls = {"pelvis","leg_L","leg_R"}
        if not required_controls <= set(fixture["controls"]): fail(identifier, "controls", "omitted construction control")
        contact_records = {}
        for contact in fixture["contacts"]:
            start, end = contact["start_beat"], contact["end_beat"]
            if start!=int(start) or end!=int(end):fail(identifier,'contacts','fractional events are outside diagnostic/v1')
            if not (0 <= start <= end <= duration) or (start == end and start != duration): fail(identifier, "contacts", "invalid interval")
            if len(contact["anchors"]) != len(contact["targets_m"]): fail(identifier, "contacts", "anchor/target length mismatch")
            for name in contact["anchors"]:
                if name not in attachments: fail(identifier, "contacts.anchors", "unresolved "+name)
                if owners[attachments[name][0]+".transform"] != "leg_"+contact["foot"]: fail(identifier, "contacts.anchors", "wrong-side anchor "+name)
            contact_records.setdefault(contact["foot"], []).append(contact)
        for terminal in fixture["terminal_contacts"]:
            if terminal["state"] != "none" and not any(c["state"] == terminal["state"] for c in contact_records.get(terminal["foot"], [])):
                fail(identifier, "terminal_contacts", "no anchor/target declaration for terminal state")
    scene = bundle["review-scene"]
    pin = backend_contract()
    if scene["backend"]["version"] != pin["blender-version"] or scene["backend"]["build"] != pin["blender-build"]:
        fail(scene["id"], "backend", "pinned backend mismatch")
    camera_ids = [c['id'] for c in scene['cameras']]
    if len(camera_ids) != len(set(camera_ids)) or set(camera_ids) != {"front","rear","side","thorax-front","thorax-side","thorax-three-quarter"}:
        fail(scene["id"], "cameras", "fixed camera inventory mismatch")
    return {"status":"valid-sources", "profile":profile["id"], "structures":len(bodies),
            "actions":len(mobility["actions"]), "placements":len(mobility["placements"]), "fixtures":len(fixtures),
            "scope":"Schema and source integrity only; generated anatomy, contacts, timing, renders and review require separate checks."}


def validate_sources(profile, root=None):
    root = Path(root or project_root())
    bundle, paths = load_sources(profile, root)
    report = validate_bundle(bundle, root)
    paths += sorted((root/"schema").glob("*.schema.json"))
    paths += [root/"docs/used-materials.md",root/"pyproject.toml",root/"uv.lock"]
    report["source_hashes"] = {str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(paths)}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(validate_sources(args.profile), indent=2))
    except (SourceValidationError, OSError, ValueError) as error:
        print(f"Invalid sources: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
