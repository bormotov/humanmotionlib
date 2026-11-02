# SPDX-License-Identifier: Apache-2.0
"""Deterministic source expansion checks for the authored mannequin."""

from __future__ import annotations

import math
from copy import deepcopy
from pathlib import Path
import unittest

import yaml

from humanmotionlib.character_surface import expand_surface


ROOT = Path(__file__).resolve().parents[1]


def _read(relative):
    return yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))


def _area(vertices, face):
    a, b, c = (vertices[index] for index in face)
    u = tuple(b[index] - a[index] for index in range(3))
    v = tuple(c[index] - a[index] for index in range(3))
    cross = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
    return 0.5 * math.sqrt(sum(value*value for value in cross))


def _signed_volume(vertices, faces):
    total = 0.0
    for face in faces:
        a, b, c = (vertices[index] for index in face)
        cross = (b[1]*c[2]-b[2]*c[1], b[2]*c[0]-b[0]*c[2], b[0]*c[1]-b[1]*c[0])
        total += sum(a[axis] * cross[axis] for axis in range(3)) / 6.0
    return total


class CharacterSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = _read("rig/profiles/adult-reference-v1.yaml")
        cls.template = _read("characters/templates/exercise-mannequin-v1.yaml")
        cls.male = _read("characters/appearances/male-v1.yaml")
        cls.female = _read("characters/appearances/female-v1.yaml")
        cls.male_surface = expand_surface(cls.profile, cls.template, cls.male, 1.70)
        cls.female_surface = expand_surface(cls.profile, cls.template, cls.female, 1.70)

    def test_eight_components_have_stable_ids_and_nonempty_meshes(self):
        expected = ["torso", "head", "arm.R", "arm.L", "leg.R", "leg.L", "foot.R", "foot.L"]
        self.assertEqual([component["id"] for component in self.male_surface["components"]], expected)
        for component in self.male_surface["components"]:
            with self.subTest(component=component["id"]):
                self.assertTrue(component["vertices_m"])
                self.assertTrue(component["faces"])
                self.assertEqual(len(component["vertices_m"]), len(component["vertex_ids"]))
                self.assertEqual(len(component["vertices_m"]), len(component["weights"]))
                self.assertEqual(len(component["faces"]), len(component["face_materials"]))
                self.assertEqual(len(set(component["vertex_ids"])), len(component["vertex_ids"]))

    def test_appearance_variants_share_exact_topology_and_weights(self):
        for male, female in zip(self.male_surface["components"], self.female_surface["components"]):
            with self.subTest(component=male["id"]):
                self.assertEqual(male["id"], female["id"])
                self.assertEqual(male["vertex_ids"], female["vertex_ids"])
                self.assertEqual(male["faces"], female["faces"])
                self.assertEqual(male["weights"], female["weights"])
                self.assertEqual(male["face_materials"], female["face_materials"])
        self.assertNotEqual(self.male_surface["surface_sha256"], self.female_surface["surface_sha256"])

    def test_end_caps_keep_the_final_ring_carrier_weights(self):
        for surface in (self.male_surface, self.female_surface):
            for component in surface["components"]:
                ring_ids = [identifier for identifier in component["vertex_ids"]
                            if "/ring." in identifier]
                if not ring_ids:
                    continue  # The foot loft uses section/cap IDs from its dedicated topology.
                final_ring = max(int(identifier.split("/ring.", 1)[1].split("/", 1)[0])
                                 for identifier in ring_ids)
                cap_index = component["vertex_ids"].index(f"{component['id']}/cap.end")
                ring_index = component["vertex_ids"].index(
                    f"{component['id']}/ring.{final_ring:03d}/sector.00")
                with self.subTest(surface=surface["surface_sha256"][:8], component=component["id"]):
                    self.assertEqual(component["weights"][cap_index], component["weights"][ring_index])
        right_leg = next(row for row in self.male_surface["components"] if row["id"] == "leg.R")
        left_leg = next(row for row in self.male_surface["components"] if row["id"] == "leg.L")
        self.assertEqual(right_leg["weights"][right_leg["vertex_ids"].index("leg.R/cap.end")],
                         {"hindfoot.R": 1.0})
        self.assertEqual(left_leg["weights"][left_leg["vertex_ids"].index("leg.L/cap.end")],
                         {"hindfoot.L": 1.0})

    def test_left_limb_is_reflection_with_stable_sector_ids_and_corrected_winding(self):
        right = next(row for row in self.male_surface["components"] if row["id"] == "arm.R")
        left = next(row for row in self.male_surface["components"] if row["id"] == "arm.L")
        self.assertEqual([value.replace("arm.R/", "arm./") for value in right["vertex_ids"]],
                         [value.replace("arm.L/", "arm./") for value in left["vertex_ids"]])
        for rpoint, lpoint in zip(right["vertices_m"], left["vertices_m"]):
            self.assertAlmostEqual(lpoint[0], -rpoint[0], delta=1e-12)
            self.assertAlmostEqual(lpoint[1], rpoint[1], delta=1e-12)
            self.assertAlmostEqual(lpoint[2], rpoint[2], delta=1e-12)
        self.assertEqual(len(right["faces"]), len(left["faces"]))
        for rface, lface in zip(right["faces"], left["faces"]):
            self.assertEqual(lface, list(reversed(rface)))
        for rweights, lweights in zip(right["weights"], left["weights"]):
            self.assertEqual({key.replace(".R", ".L"): value for key, value in rweights.items()}, lweights)

    def test_independent_waist_and_hip_slice_widths_match_frozen_presets(self):
        def width_at(surface, ring_index):
            torso = surface["components"][0]
            points = torso["vertices_m"][ring_index * 32:(ring_index + 1) * 32]
            return max(point[0] for point in points) - min(point[0] for point in points)

        # Control ring 3 is z=.580H; ring 1 is z=.470H. Measure generated
        # coordinates independently of the appearance source table.
        self.assertAlmostEqual(width_at(self.male_surface, 12) / 1.70, .164, delta=1e-4)
        self.assertAlmostEqual(width_at(self.female_surface, 12) / 1.70, .140, delta=1e-4)
        self.assertAlmostEqual(width_at(self.male_surface, 4) / 1.70, .200, delta=1e-4)
        self.assertAlmostEqual(width_at(self.female_surface, 4) / 1.70, .216, delta=1e-4)

    def test_independent_upper_arm_radius_uses_declared_female_multiplier(self):
        def ring_radius(surface, ring_index):
            arm = next(row for row in surface["components"] if row["id"] == "arm.R")
            points = arm["vertices_m"][ring_index * 32:(ring_index + 1) * 32]
            center = tuple(sum(point[axis] for point in points) / len(points) for axis in range(3))
            return max(math.sqrt(sum((point[axis] - center[axis]) ** 2 for axis in range(3)))
                       for point in points)

        # Expanded ring 8 is the authored S-to-E t=.25 control ring.
        self.assertAlmostEqual(ring_radius(self.male_surface, 8) / 1.70, .040, delta=1e-9)
        self.assertAlmostEqual(ring_radius(self.female_surface, 8) / 1.70, .036, delta=1e-9)

    def test_positions_weights_and_triangle_areas_are_finite_and_valid(self):
        for component in self.male_surface["components"] + self.female_surface["components"]:
            with self.subTest(component=component["id"]):
                for vertex in component["vertices_m"]:
                    self.assertEqual(len(vertex), 3)
                    self.assertTrue(all(math.isfinite(value) for value in vertex))
                for weight in component["weights"]:
                    self.assertLessEqual(len(weight), 2)
                    self.assertGreaterEqual(len(weight), 1)
                    self.assertTrue(all(math.isfinite(value) and value >= 0 for value in weight.values()))
                    self.assertAlmostEqual(sum(weight.values()), 1.0, delta=1e-12)
                for face in component["faces"]:
                    self.assertEqual(len(face), 3)
                    self.assertGreater(_area(component["vertices_m"], face), 1e-12 * (1.70 ** 2))
                self.assertGreater(_signed_volume(component["vertices_m"], component["faces"]), 0.0)

    def test_stature_scaling_and_expected_silhouette_landmarks(self):
        scaled = {height: expand_surface(self.profile, self.template, self.male, height)
                  for height in (1.50, 1.70, 1.90)}
        male_torso = self.male_surface["components"][0]
        small_torso = scaled[1.50]["components"][0]
        # First control ring is the first 32-vertex ring; its prescribed rx is .080H.
        self.assertAlmostEqual(max(v[0] for v in male_torso["vertices_m"][:32]), .080 * 1.70, delta=1e-12)
        self.assertAlmostEqual(max(v[0] for v in small_torso["vertices_m"][:32]), .080 * 1.50, delta=1e-12)
        large_torso = scaled[1.90]["components"][0]
        self.assertAlmostEqual(max(v[0] for v in large_torso["vertices_m"][:32]), .080 * 1.90, delta=1e-12)
        self.assertAlmostEqual(min(v[2] for v in self.male_surface["components"][-1]["vertices_m"]), 0.0, delta=1e-12)

    @staticmethod
    def _ring(component, index):
        return component["vertices_m"][index * 32:(index + 1) * 32]

    @staticmethod
    def _ring_radii_h(component, index, height):
        ring = CharacterSurfaceTests._ring(component, index)
        center = tuple(sum(point[axis] for point in ring) / 32 for axis in range(3))
        # Sector 00 and sector 08 are the independent semiaxis samples of the
        # 32-point ellipse; order them so frame-axis orientation is irrelevant.
        radii = [math.dist(ring[sector], center) / height for sector in (0, 8)]
        return tuple(sorted(radii))

    def test_every_torso_control_ring_center_and_radii_match_frozen_dossier(self):
        # Independent constants copied from design.md section 4.2.  Control
        # rings occur every four expanded rings (four subdivisions per span).
        z_h = (.430, .470, .520, .580, .650, .720, .780, .810, .840, .875)
        rx_h = {
            "male": (.080, .100, .098, .082, .100, .115, .110, .080, .028, .027),
            "female": (.085, .108, .106, .070, .086, .100, .100, .075, .027, .026),
        }
        ry_h = {
            "male": (.050, .065, .065, .052, .062, .070, .063, .045, .029, .028),
            "female": (.052, .070, .070, .052, .067, .077, .066, .045, .028, .027),
        }
        appearances = (("male", self.male), ("female", self.female))
        for height in (1.50, 1.70, 1.90):
            for label, appearance in appearances:
                surface = expand_surface(self.profile, self.template, appearance, height)
                torso = surface["components"][0]
                for control, (z, rx, ry) in enumerate(zip(z_h, rx_h[label], ry_h[label])):
                    ring = self._ring(torso, control * 4)
                    center = tuple(sum(point[axis] for point in ring) / 32 for axis in range(3))
                    with self.subTest(character=label, height=height, control_ring=control):
                        self.assertAlmostEqual(center[0] / height, 0.0, delta=1e-12)
                        self.assertAlmostEqual(center[1] / height, 0.0, delta=1e-12)
                        self.assertAlmostEqual(center[2] / height, z, delta=1e-12)
                        self.assertAlmostEqual(max(point[0] for point in ring) / height, rx, delta=1e-12)
                        self.assertAlmostEqual(max(point[1] for point in ring) / height, ry, delta=1e-12)

    def test_shared_torso_base_change_moves_both_variants_without_topology_or_weight_changes(self):
        changed_template = deepcopy(self.template)
        ring = changed_template["components"][0]["control_rings"][3]
        ring["radius_h"][0] += .001
        changed_male = expand_surface(self.profile, changed_template, self.male, 1.70)
        changed_female = expand_surface(self.profile, changed_template, self.female, 1.70)
        for original, changed in ((self.male_surface, changed_male), (self.female_surface, changed_female)):
            old_torso, new_torso = original["components"][0], changed["components"][0]
            old_point = self._ring(old_torso, 12)[0]
            new_point = self._ring(new_torso, 12)[0]
            self.assertAlmostEqual(new_point[0] - old_point[0], .001 * 1.70, delta=1e-12)
            self.assertAlmostEqual(new_point[1], old_point[1], delta=1e-12)
            self.assertAlmostEqual(new_point[2], old_point[2], delta=1e-12)
            self.assertEqual(new_torso["vertex_ids"], old_torso["vertex_ids"])
            self.assertEqual(new_torso["faces"], old_torso["faces"])
            self.assertEqual(new_torso["weights"], old_torso["weights"])
            for before, after in zip(original["components"][1:], changed["components"][1:]):
                self.assertEqual(before["vertices_m"], after["vertices_m"])
                self.assertEqual(before["faces"], after["faces"])
                self.assertEqual(before["weights"], after["weights"])

    def test_female_only_torso_delta_changes_only_female_surface(self):
        changed_female = deepcopy(self.female)
        changed_female["torso_radii_delta_h"][3][0] += .001
        female_surface = expand_surface(self.profile, self.template, changed_female, 1.70)
        self.assertEqual(self.male_surface["surface_sha256"],
                         expand_surface(self.profile, self.template, self.male, 1.70)["surface_sha256"])
        before = self._ring(self.female_surface["components"][0], 12)[0]
        after = self._ring(female_surface["components"][0], 12)[0]
        self.assertAlmostEqual(after[0] - before[0], .001 * 1.70, delta=1e-12)
        self.assertAlmostEqual(after[1], before[1], delta=1e-12)
        self.assertAlmostEqual(after[2], before[2], delta=1e-12)
        self.assertNotEqual(female_surface["surface_sha256"], self.female_surface["surface_sha256"])
        for before_component, after_component in zip(self.female_surface["components"][1:], female_surface["components"][1:]):
            self.assertEqual(before_component["vertices_m"], after_component["vertices_m"])
            self.assertEqual(before_component["weights"], after_component["weights"])

    def test_torso_base_delta_contract_rejects_legacy_shapes_and_nonpositive_effective_radii(self):
        cases = []
        legacy_appearance = deepcopy(self.male)
        legacy_appearance.pop("torso_radii_delta_h")
        legacy_appearance["torso_radii_h"] = [[.08, .05]] * 10
        cases.append((self.template, legacy_appearance, "absolute appearance"))
        for value, message in (([[0.0, 0.0]] * 9, "exactly ten"),
                               ([[0.0, 0.0]] * 11, "exactly ten"),
                               ([[0.0]] * 10, "torso_radii_delta_h"),
                               ([[0.0, 0.0, 0.0]] * 10, "torso_radii_delta_h"),
                               ([[float("nan"), 0.0]] * 10, "torso_radii_delta_h"),
                               ([[float("inf"), 0.0]] * 10, "torso_radii_delta_h"),
                               ([["bad", 0.0]] * 10, "torso_radii_delta_h")):
            appearance = deepcopy(self.female)
            appearance["torso_radii_delta_h"] = value
            cases.append((self.template, appearance, message))
        for value in ((0.0, .05), (-.01, .05), (.08, 0.0)):
            template = deepcopy(self.template)
            template["components"][0]["control_rings"][2]["radius_h"] = list(value)
            cases.append((template, self.female, "shared torso base radius"))
        for delta in ((-.098, 0.0), (-.099, 0.0), (0.0, -.065)):
            appearance = deepcopy(self.female)
            appearance["torso_radii_delta_h"][2] = list(delta)
            cases.append((self.template, appearance, "effective torso radius"))
        nonzero_male = deepcopy(self.male)
        nonzero_male["torso_radii_delta_h"][0][0] = .001
        cases.append((self.template, nonzero_male, "male-v1 torso_radii_delta_h"))
        old_template = deepcopy(self.template)
        old_template["components"][0]["control_rings"][0]["radii_source"] = "appearance.torso_radii_h"
        cases.append((old_template, self.female, "shared base radius_h"))
        for template, appearance, message in cases:
            with self.subTest(message=message, appearance=appearance.get("id")), self.assertRaisesRegex(ValueError, message):
                expand_surface(self.profile, template, appearance, 1.70)

    def test_every_limb_control_ring_radius_matches_frozen_dossier(self):
        arms = ((.020, .020), (.038, .038), (.040, .037), (.032, .030),
                (.025, .025), (.025, .025), (.026, .026), (.029, .027),
                (.022, .021), (.017, .018), (.016, .023), (.015, .025),
                (.011, .019), (.004, .007))
        legs = ((.027, .027), (.047, .044), (.050, .046), (.038, .035),
                (.029, .028), (.029, .028), (.034, .032), (.036, .033),
                (.026, .024), (.020, .019), (.019, .018))
        for label, appearance in (("male", self.male), ("female", self.female)):
            expanded = expand_surface(self.profile, self.template, appearance, 1.70)
            for component_id, controls, female_scale in (
                    ("arm.R", arms, .90), ("leg.R", legs, None)):
                component = next(row for row in expanded["components"] if row["id"] == component_id)
                for control_index, expected in enumerate(controls):
                    scale = 1.0
                    if label == "female" and component_id == "arm.R":
                        scale = female_scale
                    elif label == "female" and component_id == "leg.R":
                        scale = 1.06 if control_index <= 4 else (1.0 if control_index == 5 else .97)
                    actual = self._ring_radii_h(component, control_index * 4, 1.70)
                    target = tuple(sorted(value * scale for value in expected))
                    with self.subTest(character=label, component=component_id, control_ring=control_index):
                        for measured, wanted in zip(actual, target):
                            self.assertAlmostEqual(measured, wanted, delta=1e-9)

    def test_every_limb_control_ring_center_matches_rest_landmark_chain(self):
        # Independent rest-T-pose coordinates (H units) resolved from the
        # approved adult-reference-v1 landmarks and the dossier's span/t.
        arm_centers = (
            (.08026301, -.00885976, .81604617), (.09952301, -.00885976, .81604617),
            (.13964801, -.00885976, .81604617), (.20384801, -.00885976, .81604617),
            (.24397301, -.00885976, .81604617), (.26002301, -.00885976, .81604617),
            (.27367301, -.00885976, .81604617), (.30779801, -.00885976, .81604617),
            (.35557301, -.00885976, .81604617), (.39652301, -.00885976, .81604617),
            (.41227301, -.00885976, .81604617), (.44377301, -.00885976, .81604617),
            (.48577301, -.00885976, .81604617), (.50152301, -.00885976, .81604617),
        )
        leg_centers = (
            (.055, 0., .51758), (.055, 0., .4895), (.055, 0., .431),
            (.055, 0., .3374), (.055, 0., .2789), (.055, 0., .2555),
            (.055, 0., .223175), (.055, 0., .180075), (.055, 0., .10465),
            (.055, 0., .050775), (.055, 0., .033535),
        )
        for component_id, controls in (("arm.R", arm_centers), ("leg.R", leg_centers)):
            component = next(row for row in self.male_surface["components"] if row["id"] == component_id)
            for index, expected_h in enumerate(controls):
                ring = self._ring(component, index * 4)
                center_m = tuple(sum(point[axis] for point in ring) / 32 for axis in range(3))
                with self.subTest(component=component_id, control_ring=index):
                    for actual, expected in zip(center_m, expected_h):
                        self.assertAlmostEqual(actual / 1.70, expected, delta=1e-8)

    def test_head_and_foot_control_extrema_match_frozen_dossier(self):
        # Head ellipsoid extrema from design.md 4.2, checked at both heights.
        for height in (1.50, 1.70, 1.90):
            for label, appearance in (("male", self.male), ("female", self.female)):
                surface = expand_surface(self.profile, self.template, appearance, height)
                head = surface["components"][1]
                xs = [point[0] for point in head["vertices_m"]]
                ys = [point[1] for point in head["vertices_m"]]
                zs = [point[2] for point in head["vertices_m"]]
                radii = (.045, .052, .0625) if label == "male" else (.043, .050, .0625)
                with self.subTest(character=label, height=height):
                    self.assertAlmostEqual((max(xs) - min(xs)) / (2 * height), radii[0], delta=1e-12)
                    self.assertAlmostEqual((max(ys) - min(ys)) / (2 * height), radii[1], delta=1e-12)
                    self.assertAlmostEqual((max(zs) - min(zs)) / (2 * height), radii[2], delta=1e-12)
                    self.assertAlmostEqual(max(zs) / height, 1.0, delta=1e-12)

                foot = surface["components"][6]
                # The seven frozen foot stations in design.md 4.5 each create
                # four expanded rings; extrema and every station are asserted.
                stations = ((-.040, .010, .020), (-.025, .021, .032), (0., .024, .055),
                            (.045, .025, .040), (.075, .023, .030), (.100, .018, .020),
                            (.118, .004, .008))
                for station, (y_h, half_width_h, top_h) in enumerate(stations):
                    ring = self._ring(foot, station * 4)
                    with self.subTest(character=label, height=height, foot_station=station):
                        ys = [point[1] for point in ring]
                        xs = [point[0] for point in ring]
                        zs = [point[2] for point in ring]
                        # Foot is attached at ankle.R neutral XY; station
                        # spacing and authored section width/top are invariant.
                        self.assertAlmostEqual((max(ys) - min(ys)) / height, 0.0, delta=1e-12)
                        self.assertAlmostEqual((max(xs) - min(xs)) / height,
                                               2 * half_width_h, delta=1e-12)
                        self.assertAlmostEqual((max(zs) - min(zs)) / height, top_h, delta=1e-12)
                        self.assertAlmostEqual(min(zs) / height, 0.0, delta=1e-12)
                        center_y = sum(point[1] for point in ring) / 32
                        first_y = sum(point[1] for point in self._ring(foot, 0)) / 32
                        self.assertAlmostEqual((center_y - first_y) / height,
                                               y_h - stations[0][0], delta=1e-12)

    def test_control_ring_ids_and_mirrored_topology_are_frozen(self):
        expected_counts = {"torso": 37, "head": 482, "arm.R": 53, "arm.L": 53,
                           "leg.R": 41, "leg.L": 41, "foot.R": 25, "foot.L": 25}
        for surface in (self.male_surface, self.female_surface):
            for component in surface["components"]:
                identifier = component["id"]
                with self.subTest(component=identifier):
                    if identifier == "head":
                        self.assertEqual(component["vertex_ids"][0], "head/pole.north")
                        self.assertEqual(component["vertex_ids"][-1], "head/pole.south")
                    else:
                        rings = [value for value in component["vertex_ids"] if "/ring." in value]
                        self.assertEqual(len(rings) // 32, expected_counts[identifier])
                        for index in range(expected_counts[identifier]):
                            self.assertEqual(component["vertex_ids"][index * 32],
                                             f"{identifier}/ring.{index:03d}/sector.00")
                        self.assertEqual(component["vertex_ids"][-2:],
                                         [f"{identifier}/cap.start", f"{identifier}/cap.end"])
        for suffix in ("arm", "leg", "foot"):
            right = next(row for row in self.male_surface["components"] if row["id"] == suffix + ".R")
            left = next(row for row in self.male_surface["components"] if row["id"] == suffix + ".L")
            self.assertEqual(len(right["faces"]), len(left["faces"]))
            self.assertEqual([list(reversed(face)) for face in right["faces"]], left["faces"])
            self.assertEqual([name.replace("." + "R", ".L") for name in right["vertex_ids"]],
                             left["vertex_ids"])

    def test_all_vertices_scale_linearly_at_three_frozen_statures(self):
        for label, appearance in (("male", self.male), ("female", self.female)):
            reference = expand_surface(self.profile, self.template, appearance, 1.70)
            for height in (1.50, 1.90):
                scaled = expand_surface(self.profile, self.template, appearance, height)
                for base, actual in zip(reference["components"], scaled["components"]):
                    self.assertEqual(base["vertex_ids"], actual["vertex_ids"])
                    self.assertEqual(base["faces"], actual["faces"])
                    factor = height / 1.70
                    for vertex_id, point, target in zip(base["vertex_ids"], base["vertices_m"],
                                                        actual["vertices_m"]):
                        for axis in range(3):
                            self.assertAlmostEqual(target[axis], point[axis] * factor, delta=1e-12,
                                                   msg=f"{label} H={height} {base['id']} {vertex_id} axis={axis}")

    def test_repeat_expansion_has_identical_digest_and_records(self):
        repeat = expand_surface(self.profile, self.template, self.male, 1.70)
        self.assertEqual(repeat, self.male_surface)

    def test_invalid_stature_profile_and_degenerate_frames_fail(self):
        for stature in (0.0, -1.0, float("nan"), float("inf")):
            with self.subTest(stature=stature), self.assertRaises(ValueError):
                expand_surface(self.profile, self.template, self.male, stature)
        with self.assertRaisesRegex(ValueError, "incompatible"):
            expand_surface(self.profile, {**self.template, "compatible_profile":"unknown"}, self.male, 1.70)
        bad_appearance = {**self.male, "radius_scales": {**self.male["radius_scales"], "arm": -0.1}}
        with self.assertRaisesRegex(ValueError, "radius scale must be finite and positive"):
            expand_surface(self.profile, self.template, bad_appearance, 1.70)


if __name__ == "__main__":
    unittest.main()
