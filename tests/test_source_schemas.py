# SPDX-License-Identifier: Apache-2.0
"""Schema contract tests; semantic inventory validation is a separate layer."""

from copy import deepcopy
import unittest

from humanmotionlib.source_validation import SourceValidationError, validate_document


PROVENANCE = {"kind": "authored", "license": "CC-BY-4.0", "sources": [],
              "rationale": "Synthetic schema test record, not anatomical evidence.",
              "changes": "Original test record."}
IDENTITY = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
GROUPS = ["pelvis", "torso", "head_neck", "arm_L", "arm_R", "leg_L", "leg_R"]


def base(kind):
    return {"schema_version": 1, "kind": kind, "id": "schema-test",
            "description": "Synthetic positive schema example.",
            "license": "CC-BY-4.0", "provenance": deepcopy(PROVENANCE)}


def examples():
    profile = base("skeleton-profile") | {
        "units": "m", "stature_m": 1.7,
        "space": {"handedness": "right", "right": "+X", "anterior": "+Y", "superior": "+Z",
                  "floor_z_m": 0, "quaternion_order": "wxyz",
                  "composition": "q_local=q_rest*q_delta;q_world=q_parent*q_local"},
        "proportions": {"upper_arm": .1605, "forearm": .1365, "thigh": .234, "shank": .2155},
        "landmarks": [{"id": "origin", "frame": "world", "position_m": [0, 0, 0],
                       "tolerance_h": 1e-4, "provenance": deepcopy(PROVENANCE)}],
        "structures": [{"id": "pelvis", "description": "Test structure.", "kind": "anatomical",
                        "representation": "grouped", "parent": None, "rigid": True,
                        "origin_m": [0, 0, .8], "basis": deepcopy(IDENTITY),
                        "rest_translation_m": [0, 0, .8], "rest_orientation": [1, 0, 0, 0],
                        "landmarks": ["origin"], "geometry": [
                            {"id": "pelvis.test", "type": "ellipsoid", "center_m": [0, 0, 0],
                             "radii_m": [.01, .01, .01]}],
                        "attachments": [{"id": "pelvis.attachment", "position_m": [0, 0, 0],
                                         "orientation": [1, 0, 0, 0]}],
                        "provenance": deepcopy(PROVENANCE)}],
        "resolution": {"ellipsoid_longitudes": 24, "ellipsoid_latitudes": 12,
                       "shaft_sides": 16, "curve_intervals": 16}}
    profile['mass_model'] = {'id':'adult-reference-point-masses-v1','assessment':'static',
        'description':'Synthetic schema example only.','provenance':deepcopy(PROVENANCE),
        'segments':[{'id':'region.'+str(i),'body':'pelvis','description':'Synthetic mass point.',
                     'weight_kg':1,'male_weight_kg':1,'female_weight_kg':1,
                     'position_m':[0,0,0],'provenance':deepcopy(PROVENANCE)} for i in range(16)]}
    mobility = base("skeleton-mobility") | {
        "profile": "schema-test", "units": "degrees", "actions": [{
            "id": "knee.R.flexion", "joint": "knee.R", "group": "leg_R", "side": "R",
            "mode": "independent", "description": "Test action.", "frame": "femur.R",
            "axis": [1, 0, 0], "neutral_deg": 0, "bounds_deg": [0, 130],
            "provenance": deepcopy(PROVENANCE)}],
        "couplings": [{"id": "knee.R.tracking", "type": "knee_tracking",
                       "action_ids": ["knee.R.flexion"],
                       "parameters": {"twist_deg": -8, "transition_deg": 30,
                                      "translation_factors_h": [0, -.003, -.001]},
                       "provenance": deepcopy(PROVENANCE)}],
        "reference_observations": [{"id": "knee.flexion", "action": "knee.flexion",
                                    "cohort": "Faisal Table 3, ages 20–44",
                                    "statistic": "mean", "female_deg": 141.9, "male_deg": 137.7,
                                    "provenance": deepcopy(PROVENANCE)}]}
    mobility["conventions"] = {
        "hip": "Rx(f)*Ry(b)*Rz(-r)", "wrist": "Rx(f)*Ry(b)", "spine_pelvis": "Rx(-f)*Ry(b)*Rz(r)",
        "shoulder": "Rot(u,e)*Rz(-tau)",
        "action_frame": "anatomical-neutral; axes inherit proximal rotation; basis change explicit"}
    mobility["placements"] = [
        {"id": "pelvis."+name, "joint": "pelvis", "group": "pelvis", "frame": "world",
         "axis": axis, "neutral_m": neutral, "bounds_m": bounds,
         "provenance": deepcopy(PROVENANCE)}
        for name, axis, neutral, bounds in [("x", [1,0,0], 0, [-.4,.4]),
                                          ("y", [0,1,0], 0, [-.4,.4]),
                                          ("z", [0,0,1], .8, [.34,1.02])]]
    groups = base("body-groups") | {
        "groups": [{"id": group, "description": "Test group.", "channels": [group+".channel"]}
                   for group in GROUPS]}
    mapping = base("humanoid-map") | {
        "semantic_version": "VRMC_vrm-1.0", "profile": "schema-test", "required": ["hips"],
        "entries": [{"humanoid": "hips", "target": "pelvis", "group": "pelvis"}],
        "omissions": [{"humanoid": "leftEye", "reason": "No eye geometry."}],
        "losses": ["Internal helper translation is not an export claim."], "internal_only": []}
    fixture = base("skeleton-diagnostic") | {
        "format": "skeleton-diagnostic/v1", "profile": "schema-test", "duration_beats": 4,
        "controls": ["leg_R"], "rest_policy": {"policy": "base", "base_fixture": "neutral"},
        "tracks": [{"channel": "knee.R.flexion", "easing": "ease_in_out",
                    "keys": [{"beat": 0, "value": 0}, {"beat": 2, "value": 90}]}],
        "construction": {"type": "squat_closed", "side": "bilateral", "start_beat": 0,
                         "end_beat": 4, "reference_knots": [{"beat": 2, "value": 90}]},
        "world_root": {"mode": "identity", "translation_m": [0, 0, 0],
                       "orientation": [1, 0, 0, 0], "clearance_h": 0},
        "contacts": [{"foot": "R", "start_beat": 0, "end_beat": 4, "state": "flat",
                      "anchors": ["heel.R"], "targets_m": [[.09, 0, 0]]}],
        "terminal_contacts": [{"foot": "R", "state": "flat"}],
        "procedural": {"noise": False, "follow_through": False}}
    scene = base("skeleton-review-scene") | {
        "backend": {"version": "5.2.2 LTS", "build": "d13f752e3b9c",
                    "renderer": "BLENDER_WORKBENCH", "reference_platform": "Darwin-arm64"},
        "cameras": [{"id": name, "position_m": position, "look_at_m": [0, 0, .95],
                     "up": [0, 0, 1], "orthographic_scale_m": 4}
                    for name, position in [("front", [0, 8, .95]), ("rear", [0, -8, .95]),
                                           ("side", [8, 0, .95])]],
        "resolution": [1024, 1024], "floor": {"size_m": 6, "z_m": 0, "color": [.35, .37, .40]},
        "shading": {"light": "FLAT", "color_type": "MATERIAL", "background": [.94, .95, .96],
                    "bone_color": [.80, .76, .64], "outlines": True, "outline_color": [0, 0, 0],
                    "shadows": False, "cavity": False, "transparent": False, "antialiasing": 16},
        "overlays": {"axis_length_h": .025, "labels": "stable_ids"}}
    return {"profile": profile, "mobility": mobility, "body-groups": groups,
            "humanoid-map": mapping, "diagnostic": fixture, "review-scene": scene}


class SourceSchemaTests(unittest.TestCase):
    def test_positive_examples(self):
        for name, document in examples().items():
            with self.subTest(schema=name):
                validate_document(document, name)

    def test_closed_sources_and_required_metadata(self):
        for name, document in examples().items():
            for field in ("id", "description", "provenance", "license"):
                bad = deepcopy(document)
                del bad[field]
                with self.subTest(schema=name, missing=field):
                    with self.assertRaises(SourceValidationError):
                        validate_document(bad, name)
            for change in ({"unknown": 1}, {"schema_version": 2}, {"license": "unknown"}):
                with self.subTest(schema=name, change=change):
                    with self.assertRaises(SourceValidationError):
                        validate_document(document | change, name)

    def test_numeric_and_unit_failures(self):
        for value in (0, -1, True, float("nan"), float("inf"), float("-inf")):
            with self.subTest(stature=value):
                with self.assertRaises(SourceValidationError):
                    validate_document(examples()["profile"] | {"stature_m": value}, "profile")
        for name, units in (("profile", "cm"), ("mobility", "radians")):
            with self.assertRaises(SourceValidationError):
                validate_document(examples()[name] | {"units": units}, name)

    def test_nested_numeric_and_provenance_failures(self):
        for field, value in (("position_m", [0, float("nan"), 0]),
                             ("position_m", [0, float("inf"), 0]),
                             ("extra", "unknown")):
            document = examples()["profile"]
            document["landmarks"][0][field] = value
            with self.assertRaises(SourceValidationError):
                validate_document(document, "profile")
        document = examples()["profile"]
        del document["structures"][0]["provenance"]
        with self.assertRaises(SourceValidationError):
            validate_document(document, "profile")

    def test_executable_coupling_strings_rejected(self):
        document = examples()["mobility"]
        document["couplings"][0]["parameters"]["expression"] = "eval('anything')"
        with self.assertRaises(SourceValidationError):
            validate_document(document, "mobility")
