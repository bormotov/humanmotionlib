# SPDX-License-Identifier: Apache-2.0
"""Deterministic source expansion checks for the authored mannequin."""

from __future__ import annotations

import math
import hashlib
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
import unittest

import yaml

from humanmotionlib.character_surface import (
    _rest_frames, _validate_closed_oriented_component, expand_surface,
)


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

    def test_six_components_have_stable_ids_and_welded_arm_mesh(self):
        expected = ["torso", "head", "leg.R", "leg.L", "foot.R", "foot.L"]
        self.assertEqual([component["id"] for component in self.male_surface["components"]], expected)
        for component in self.male_surface["components"]:
            with self.subTest(component=component["id"]):
                self.assertTrue(component["vertices_m"])
                self.assertTrue(component["faces"])
                self.assertEqual(len(component["vertices_m"]), len(component["vertex_ids"]))
                self.assertEqual(len(component["vertices_m"]), len(component["weights"]))
                self.assertEqual(len(component["faces"]), len(component["face_materials"]))
                self.assertEqual(len(set(component["vertex_ids"])), len(component["vertex_ids"]))
        torso_ids = set(self.male_surface["components"][0]["vertex_ids"])
        self.assertIn("arm.R/ring.008/sector.00", torso_ids)
        self.assertIn("arm.L/ring.008/sector.00", torso_ids)

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
                # The welded torso carries arm and shoulder source-region IDs;
                # only the component's own loft rings define its terminal cap.
                ring_ids = [identifier for identifier in component["vertex_ids"]
                            if identifier.startswith(f"{component['id']}/ring.")]
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
        torso = next(row for row in self.male_surface["components"] if row["id"] == "torso")
        by_id = {identifier: index for index, identifier in enumerate(torso["vertex_ids"])}

        def swap_carriers(weights):
            return {key.replace(".R", ".SIDE").replace(".L", ".R").replace(".SIDE", ".L"): value
                    for key, value in weights.items()}

        for prefix in ("arm", "shoulder"):
            right_ids = sorted(identifier for identifier in by_id if identifier.startswith(prefix + ".R/"))
            left_ids = {identifier for identifier in by_id if identifier.startswith(prefix + ".L/")}
            if prefix == "arm":
                self.assertEqual(len(right_ids), 1441)  # rings 008..052 and terminal cap
            else:
                loops = [identifier for identifier in right_ids if "/loop." in identifier]
                self.assertEqual(len(loops), 96)
                self.assertEqual(sum("/refine.1/" in value for value in right_ids), 416)
                self.assertEqual(sum("/refine.2/" in value for value in right_ids), 1600)
                right_ids = loops
            self.assertEqual(len(right_ids), len(left_ids) if prefix == "arm" else 96)
            for right_id in right_ids:
                left_id = right_id.replace(prefix + ".R/", prefix + ".L/")
                if prefix == "shoulder":
                    sector = int(right_id.rsplit("/sector.", 1)[1])
                    left_id = left_id.rsplit("/sector.", 1)[0] + f"/sector.{31 - sector:02d}"
                self.assertIn(left_id, left_ids)
                right = by_id[right_id]
                left = by_id[left_id]
                rpoint, lpoint = torso["vertices_m"][right], torso["vertices_m"][left]
                self.assertAlmostEqual(lpoint[0], -rpoint[0], delta=1e-12)
                self.assertAlmostEqual(lpoint[1], rpoint[1], delta=1e-12)
                self.assertAlmostEqual(lpoint[2], rpoint[2], delta=1e-12)
                self.assertEqual(swap_carriers(torso["weights"][right]), torso["weights"][left])

        # Refinement IDs follow per-side edge traversal. Compare the complete
        # mirrored coordinate and carrier multisets instead of assuming the
        # two traversals assign identical edge numbers.
        for refinement in ("refine.1", "refine.2"):
            def records(side):
                values = []
                for identifier, index in by_id.items():
                    if identifier.startswith(f"shoulder.{side}/{refinement}/"):
                        point = torso["vertices_m"][index]
                        if side == "R":
                            point = (-point[0], point[1], point[2])
                        weights = torso["weights"][index]
                        if side == "R":
                            weights = swap_carriers(weights)
                        values.append((point, tuple(sorted(weights.items())), identifier))
                return sorted(values)
            right,left=records("R"),records("L")
            self.assertEqual(len(right),len(left))
            unmatched=list(left)
            max_deviation=0.0
            for point,weights,identifier in right:
                matches=[row for row in unmatched if row[1]==weights and math.dist(point,row[0])<=1e-12]
                self.assertEqual(len(matches),1,identifier)
                max_deviation=max(max_deviation,math.dist(point,matches[0][0]))
                unmatched.remove(matches[0])
            self.assertFalse(unmatched)
            self.assertLessEqual(max_deviation,1e-12)

        # The merged torso surface retains symmetric rings under the actual
        # angular reflection map; topology winding is checked separately.
        for ring in range(37):
            for sector in range(32):
                right_id = f"torso/ring.{ring:03d}/sector.{sector:02d}"
                left_id = f"torso/ring.{ring:03d}/sector.{(16 - sector) % 32:02d}"
                if right_id not in by_id or left_id not in by_id:
                    self.assertEqual(right_id in by_id, left_id in by_id)
                    continue
                rp, lp = torso["vertices_m"][by_id[right_id]], torso["vertices_m"][by_id[left_id]]
                self.assertAlmostEqual(lp[0], -rp[0], delta=1e-12)
                self.assertAlmostEqual(lp[1], rp[1], delta=1e-12)
                self.assertAlmostEqual(lp[2], rp[2], delta=1e-12)

    def test_independent_waist_and_hip_slice_widths_match_frozen_presets(self):
        def width_at(surface, ring_index):
            torso = next(row for row in surface["components"] if row["id"] == "torso")
            points = self._ring(torso, ring_index)
            return max(point[0] for point in points) - min(point[0] for point in points)

        # Control ring 3 is z=.580H; ring 1 is z=.470H. Measure generated
        # coordinates independently of the appearance source table.
        self.assertAlmostEqual(width_at(self.male_surface, 12) / 1.70, .164, delta=1e-4)
        self.assertAlmostEqual(width_at(self.female_surface, 12) / 1.70, .140, delta=1e-4)
        self.assertAlmostEqual(width_at(self.male_surface, 4) / 1.70, .200, delta=1e-4)
        self.assertAlmostEqual(width_at(self.female_surface, 4) / 1.70, .216, delta=1e-4)

    def test_independent_upper_arm_radius_uses_declared_female_multiplier(self):
        def ring_radius(surface, ring_index):
            torso = next(row for row in surface["components"] if row["id"] == "torso")
            points = self._ring(torso, ring_index, prefix="arm.R")
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
                for vertex_id, weight in zip(component["vertex_ids"], component["weights"]):
                    max_influences = 3 if vertex_id.startswith(("shoulder.R/", "shoulder.L/")) else 2
                    self.assertLessEqual(len(weight), max_influences, vertex_id)
                    self.assertGreaterEqual(len(weight), 1)
                    self.assertTrue(all(math.isfinite(value) and value >= 0 for value in weight.values()))
                    self.assertAlmostEqual(sum(weight.values()), 1.0, delta=1e-12)
                for face in component["faces"]:
                    self.assertEqual(len(face), 3)
                    self.assertGreater(_area(component["vertices_m"], face), 1e-12 * (1.70 ** 2))
                self.assertGreater(_signed_volume(component["vertices_m"], component["faces"]), 0.0)

    def test_leg_caps_are_closed_and_one_flipped_triangle_is_rejected(self):
        for surface in (self.male_surface, self.female_surface):
            for component in (row for row in surface["components"] if row["id"].startswith("leg.")):
                with self.subTest(surface=surface["surface_sha256"][:8], component=component["id"]):
                    start=component["vertex_ids"].index(f"{component['id']}/cap.start")
                    end=component["vertex_ids"].index(f"{component['id']}/cap.end")
                    start_faces=[face for face in component["faces"] if start in face]
                    end_faces=[face for face in component["faces"] if end in face]
                    self.assertEqual((len(start_faces),len(end_faces)),(32,32))
                    self.assertTrue(_validate_closed_oriented_component(component))
                    damaged=deepcopy(component)
                    damaged["faces"][next(i for i,face in enumerate(damaged["faces"]) if start in face)].reverse()
                    with self.assertRaisesRegex(ValueError,"closed oriented manifold"):
                        _validate_closed_oriented_component(damaged)

    def test_refined_shoulder_bridge_topology_and_weights_are_mirror_pairs(self):
        torso=next(row for row in self.male_surface["components"] if row["id"]=="torso")
        ids=torso["vertex_ids"]
        vertices=torso["vertices_m"]
        weights=torso["weights"]
        left_lookup={}
        def swap(row):
            return {key.replace(".L",".SIDE").replace(".R",".L").replace(".SIDE",".R"):value
                    for key,value in row.items()}
        for index,identifier in enumerate(ids):
            if identifier.startswith("shoulder.L/"):
                left_lookup.setdefault(tuple(sorted(weights[index].items())),[]).append(index)
        mirror={}
        shoulder_vertex_count=0
        for index,identifier in enumerate(ids):
            if not identifier.startswith("shoulder.R/"):
                continue
            shoulder_vertex_count+=1
            point=vertices[index]
            key=tuple(sorted(swap(weights[index]).items()))
            reflected=(-point[0],point[1],point[2])
            matches=[candidate for candidate in left_lookup.get(key,[])
                     if math.dist(reflected,vertices[candidate])<=1e-12]
            self.assertEqual(len(matches),1,identifier)
            mirror[index]=matches[0]
        self.assertEqual(shoulder_vertex_count,2112)
        index_by_id={identifier:index for index,identifier in enumerate(ids)}
        import re
        for index,identifier in enumerate(ids):
            match=re.fullmatch(r"torso/ring\.(\d+)/sector\.(\d+)",identifier)
            if match:
                counterpart=f"torso/ring.{int(match.group(1)):03d}/sector.{(16-int(match.group(2)))%32:02d}"
            else:
                match=re.fullmatch(r"arm\.R/ring\.(\d+)/sector\.(\d+)",identifier)
                if not match:
                    continue
                counterpart=f"arm.L/ring.{int(match.group(1)):03d}/sector.{int(match.group(2)):02d}"
            if counterpart in index_by_id:
                mirror[index]=index_by_id[counterpart]
        right_loop=([(32,0)]+[(32,s) for s in (1,2,3,4)]+[(r,4) for r in range(31,23,-1)]+
                    [(24,s) for s in (3,2,1,0,31,30,29,28)]+[(r,28) for r in range(25,33)]+
                    [(32,s) for s in (29,30,31)])
        left_loop=[(r,(16-s)%32) for r,s in reversed(right_loop)]
        right_seam={f"torso/ring.{r:03d}/sector.{s:02d}" for r,s in right_loop}
        left_seam={f"torso/ring.{r:03d}/sector.{s:02d}" for r,s in left_loop}
        right_seam.update(f"arm.R/ring.008/sector.{sector:02d}" for sector in range(32))
        left_seam.update(f"arm.L/ring.008/sector.{sector:02d}" for sector in range(32))
        right_faces=[tuple(face) for face in torso["faces"]
                     if any(ids[index].startswith("shoulder.R/") for index in face)
                     and all(ids[index].startswith("shoulder.R/") or ids[index] in right_seam for index in face)]
        left_faces={tuple(sorted(face)) for face in torso["faces"]
                    if any(ids[index].startswith("shoulder.L/") for index in face)
                    and all(ids[index].startswith("shoulder.L/") or ids[index] in left_seam for index in face)}
        self.assertEqual((len(right_faces),len(left_faces)),(4096,4096))
        reflected={tuple(sorted(mirror[index] for index in face)) for face in right_faces}
        self.assertEqual(reflected,left_faces)
        self.assertEqual(len(right_faces),len(left_faces))

        right_index=next(index for index in mirror if ids[index].startswith("shoulder.R/"))
        left_index=mirror[right_index]
        perturbed=deepcopy(torso)
        point=perturbed["vertices_m"][left_index]
        perturbed["vertices_m"][left_index]=(point[0]+1e-4,point[1],point[2])
        with self.assertRaises(AssertionError):
            self.assertAlmostEqual(perturbed["vertices_m"][left_index][0],
                                   -torso["vertices_m"][right_index][0],delta=1e-12)

        wrong_weight=deepcopy(torso)
        row=wrong_weight["weights"][left_index]
        carrier=next(key for key in row if key.startswith("humerus."))
        row[carrier]+=1e-4
        other=next(key for key in row if key!=carrier)
        row[other]-=1e-4
        with self.assertRaises(AssertionError):
            self.assertEqual(swap(torso["weights"][right_index]),row)

        wrong_diagonal=deepcopy(torso)
        left_bridge_faces=[face for face in wrong_diagonal["faces"]
                           if any(wrong_diagonal["vertex_ids"][index].startswith("shoulder.L/")
                                  for index in face)
                           and all(wrong_diagonal["vertex_ids"][index].startswith("shoulder.L/") or
                                   wrong_diagonal["vertex_ids"][index] in left_seam for index in face)]
        quad=None
        for position,first in enumerate(left_bridge_faces):
            for second in left_bridge_faces[position+1:]:
                union=set(first)|set(second)
                shared=set(first)&set(second)
                if len(union)==4 and len(shared)==2:
                    quad=(first,second,tuple(sorted(union)))
                    break
            if quad:
                break
        self.assertIsNotNone(quad)
        first,second,(a,b,c,d)=quad
        face_positions={tuple(sorted(face)):i for i,face in enumerate(wrong_diagonal["faces"])}
        old=(tuple(sorted(first)),tuple(sorted(second)))
        replacements=((a,b,d),(b,c,d))
        for old_face,new_face in zip(old,replacements):
            wrong_diagonal["faces"][face_positions[old_face]]=list(new_face)
        corrupted_left={tuple(sorted(face)) for face in wrong_diagonal["faces"]
                        if any(wrong_diagonal["vertex_ids"][index].startswith("shoulder.L/")
                               for index in face)
                        and all(wrong_diagonal["vertex_ids"][index].startswith("shoulder.L/") or
                                wrong_diagonal["vertex_ids"][index] in left_seam for index in face)}
        with self.assertRaises(AssertionError):
            self.assertEqual(reflected,corrupted_left)

    def test_female_h190_keeps_repaired_surface_topology_and_mirror_contract(self):
        surface=expand_surface(self.profile,self.template,self.female,1.90)
        torso=next(row for row in surface["components"] if row["id"]=="torso")
        self.assertEqual((len(torso["vertices_m"]),len(torso["faces"])),(8194,16384))
        for component in surface["components"]:
            for point in component["vertices_m"]:
                self.assertTrue(all(math.isfinite(value) for value in point))
            for face in component["faces"]:
                self.assertGreater(_area(component["vertices_m"],face),1e-12*1.90**2)
            if component["id"].startswith("leg."):
                self.assertTrue(_validate_closed_oriented_component(component))
        previous=self.male_surface
        try:
            self.male_surface=surface
            self.test_refined_shoulder_bridge_topology_and_weights_are_mirror_pairs()
        finally:
            self.male_surface=previous

    def test_selected_delivered_pose_geometry_is_finite_and_noncollapsed(self):
        from humanmotionlib.character_skinning import skin_vertex, source_world_transforms
        from humanmotionlib.diagnostics import DiagnosticEvaluator
        from humanmotionlib.validate import load_sources
        sources,_=load_sources("adult-reference-v1",root=ROOT)
        profile=sources["profile"]
        evaluator=DiagnosticEvaluator(sources)
        for appearance,height in ((self.male,1.70),(self.female,1.90)):
            surface=expand_surface(profile,self.template,appearance,height)
            rest_scale=height/float(profile["stature_m"])
            _,rest_frames=_rest_frames(profile,rest_scale)
            weights=[row for component in surface["components"] for row in component["weights"]]
            carriers=sorted({carrier for row in weights for carrier in row})
            sample_points=([("neutral",0.0),("rest",0.0)]+
                           [(fixture,float(beat)) for fixture in ("arm-raise","squat")
                            for beat in range(5)])
            for fixture,beat in sample_points:
                frames=evaluator.evaluate(fixture,beat)["frames"]
                transforms=source_world_transforms(profile,frames,carriers,rest_frames=rest_frames)
                for component in surface["components"]:
                    posed=[skin_vertex(point,row,transforms)
                           for point,row in zip(component["vertices_m"],component["weights"])]
                    with self.subTest(character=appearance["id"],height=height,fixture=fixture,beat=beat,
                                      component=component["id"]):
                        for point in posed:
                            self.assertTrue(all(math.isfinite(value) for value in point))
                        for face in component["faces"]:
                            self.assertGreater(_area(posed,face),1e-12*height**2)

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
        foot = next(row for row in self.male_surface["components"] if row["id"] == "foot.L")
        self.assertAlmostEqual(min(v[2] for v in foot["vertices_m"]), 0.0, delta=1e-12)

    @staticmethod
    def _ring(component, index, *, prefix=None):
        prefix = prefix or component["id"]
        by_id = {identifier: position for position, identifier in enumerate(component["vertex_ids"])}
        identifiers = [f"{prefix}/ring.{index:03d}/sector.{sector:02d}" for sector in range(32)]
        points = [component["vertices_m"][by_id[name]] for name in identifiers if name in by_id]
        if len(points) not in (18, 32):
            raise AssertionError(f"{prefix} ring {index} has {len(points)} stable sector vertices")
        return points

    @staticmethod
    def _ring_radii_h(component, index, height, *, prefix=None):
        ring = CharacterSurfaceTests._ring(component, index, prefix=prefix)
        center = tuple(sum(point[axis] for point in ring) / len(ring) for axis in range(3))
        # Sector 00 and sector 08 are the independent semiaxis samples of the
        # 32-point ellipse; order them so frame-axis orientation is irrelevant.
        by_sector = {sector: ring[sector] for sector in (0, 8)}
        radii = [math.dist(by_sector[sector], center) / height for sector in (0, 8)]
        return tuple(sorted(radii))

    def test_every_torso_control_ring_center_and_radii_match_frozen_dossier(self):
        # Independent constants copied from design.md section 4.2.  Control
        # rings occur every four expanded rings (four subdivisions per span).
        z_h = (.430, .470, .520, .580, .650, .720, .780, .810, .840, .875)
        rx_h = {
            "male": (.080, .100, .098, .082, .100, .115, .110, .114, .028, .027),
            "female": (.085, .108, .106, .070, .086, .100, .100, .109, .027, .026),
        }
        ry_h = {
            "male": (.050, .065, .065, .052, .062, .070, .063, .055, .029, .028),
            "female": (.052, .070, .070, .052, .067, .077, .066, .055, .028, .027),
        }
        appearances = (("male", self.male), ("female", self.female))
        for height in (1.50, 1.70, 1.90):
            for label, appearance in appearances:
                surface = expand_surface(self.profile, self.template, appearance, height)
                torso = surface["components"][0]
                for control, (z, rx, ry) in enumerate(zip(z_h, rx_h[label], ry_h[label])):
                    ring = self._ring(torso, control * 4)
                    center = tuple(sum(point[axis] for point in ring) / len(ring)
                                   for axis in range(3))
                    with self.subTest(character=label, height=height, control_ring=control):
                        self.assertAlmostEqual(center[0] / height, 0.0, delta=1e-12)
                        self.assertAlmostEqual(center[1] / height, 0.0, delta=1e-12)
                        self.assertAlmostEqual(center[2] / height, z, delta=1e-12)
                        if control == 7:
                            # Ring 028 retains only 18 sectors at the welded
                            # shoulder junction, so its sampled extrema do not
                            # equal the analytic ellipse radii.
                            self.assertEqual(len(ring), 18)
                            for point in ring:
                                ellipse = ((point[0] / height) / rx) ** 2 + ((point[1] / height) / ry) ** 2
                                self.assertAlmostEqual(ellipse, 1.0, delta=1e-12)
                        else:
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
        torso = next(row for row in self.male_surface["components"] if row["id"] == "torso")
        for label, appearance in (("male", self.male), ("female", self.female)):
            expanded = expand_surface(self.profile, self.template, appearance, 1.70)
            for component_id, controls, female_scale in (
                    ("arm.R", arms, .90), ("leg.R", legs, None)):
                component = (next(row for row in expanded["components"] if row["id"] == "torso")
                             if component_id == "arm.R" else
                             next(row for row in expanded["components"] if row["id"] == component_id))
                control_rows = controls[2:] if component_id == "arm.R" else controls
                for control_index, expected in enumerate(control_rows):
                    scale = 1.0
                    if label == "female" and component_id == "arm.R":
                        scale = female_scale
                    elif label == "female" and component_id == "leg.R":
                        scale = 1.06 if control_index <= 4 else (1.0 if control_index == 5 else .97)
                    ring_index = control_index * 4 + (8 if component_id == "arm.R" else 0)
                    actual = self._ring_radii_h(component, ring_index, 1.70,
                                                prefix=component_id)
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
        for component_id, controls in (("arm.R", arm_centers[2:]), ("leg.R", leg_centers)):
            component = (next(row for row in self.male_surface["components"] if row["id"] == "torso")
                         if component_id == "arm.R" else
                         next(row for row in self.male_surface["components"] if row["id"] == component_id))
            for index, expected_h in enumerate(controls):
                ring_index = index * 4 + (8 if component_id == "arm.R" else 0)
                ring = self._ring(component, ring_index, prefix=component_id)
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

                foot = next(row for row in surface["components"] if row["id"] == "foot.R")
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
        expected = {
            "torso": (8194, 16384, "b2efe50eb66e06612afabbbe6f4400966cd94d87d6533413bc95ea3bad0666be"),
            "head": (482, 960, "e8c9d54393a9de3ed941f3f88fa912fe68740c2b40cad425b733b6f5ad2716b0"),
            "leg.R": (1314, 2624, "f7da33e806307b08f1f14688dca6b1e3e5de5d1ffbaa8950c5987cbd1aa0404b"),
            "leg.L": (1314, 2624, "e42fd536686908a175108e683411ff97f9bab6812dd02ba44f93e73245ada3a9"),
            "foot.R": (802, 1600, "b3cb9cac2863de1a6a8b21eea30ce22420d29763de112d94ba8e20fb6718d849"),
            "foot.L": (802, 1600, "9cc3de3b13497722265fc84215daf43aa9c60abc7e47a610ea2b42e388a8af00"),
        }
        for surface in (self.male_surface, self.female_surface):
            for component in surface["components"]:
                identifier = component["id"]
                with self.subTest(component=identifier):
                    vertex_count, face_count, id_digest = expected[identifier]
                    self.assertEqual(len(component["vertex_ids"]), vertex_count)
                    self.assertEqual(len(component["vertices_m"]), vertex_count)
                    self.assertEqual(len(component["faces"]), face_count)
                    self.assertEqual(hashlib.sha256(
                        ("\n".join(sorted(component["vertex_ids"])) + "\n").encode()).hexdigest(),
                        id_digest)
                    if identifier == "head":
                        self.assertEqual(component["vertex_ids"][0], "head/pole.north")
                        self.assertEqual(component["vertex_ids"][-1], "head/pole.south")
                    else:
                        self.assertIn(f"{identifier}/cap.start", component["vertex_ids"])
                        self.assertIn(f"{identifier}/cap.end", component["vertex_ids"])

        torso = next(row for row in self.male_surface["components"] if row["id"] == "torso")
        torso_ids = set(torso["vertex_ids"])
        for side in ("R", "L"):
            arm_ids = {identifier for identifier in torso_ids if identifier.startswith(f"arm.{side}/")}
            self.assertEqual(len(arm_ids), 1441)
            self.assertEqual(arm_ids, {
                f"arm.{side}/ring.{ring:03d}/sector.{sector:02d}"
                for ring in range(8, 53) for sector in range(32)
            } | {f"arm.{side}/cap.end"})
            shoulder_ids = {identifier for identifier in torso_ids
                            if identifier.startswith(f"shoulder.{side}/")}
            shoulder_digest = hashlib.sha256(
                ("\n".join(sorted(shoulder_ids)) + "\n").encode()).hexdigest()
            expected_shoulder_digest = {
                "R": "d87c1a36fb55da9bc6c85bde3a980a9ec0d425ff90c7b65e8896f42e098e229b",
                "L": "1ee8cc8cdfcd01bc3620f6a8c7b59842261120ebe971cf138e1c88eaae4c62a1",
            }
            self.assertEqual(shoulder_digest, expected_shoulder_digest[side])
            loops = {f"shoulder.{side}/loop.{loop}/sector.{sector:02d}"
                     for loop in (1, 2, 3) for sector in range(32)}
            self.assertEqual(len(shoulder_ids), 2112)
            self.assertTrue(loops <= shoulder_ids)
            self.assertEqual(sum(identifier.startswith(f"shoulder.{side}/refine.1/")
                                 for identifier in shoulder_ids), 416)
            self.assertEqual(sum(identifier.startswith(f"shoulder.{side}/refine.2/")
                                 for identifier in shoulder_ids), 1600)

        # R6 welds both arms into one torso manifold. Every edge must have two
        # incident faces with opposite directions, and each component is one
        # connected, positively oriented shell.
        for component in self.male_surface["components"]:
            edges = defaultdict(list)
            adjacent = [set() for _ in component["vertices_m"]]
            for face in component["faces"]:
                self.assertEqual(len(set(face)), 3)
                for first, second in zip(face, face[1:] + face[:1]):
                    key = (min(first, second), max(first, second))
                    edges[key].append(1 if first < second else -1)
                    adjacent[first].add(second)
                    adjacent[second].add(first)
            self.assertTrue(all(len(directions) == 2 and sum(directions) == 0
                                for directions in edges.values()), component["id"])
            reached = {0}
            frontier = [0]
            while frontier:
                current = frontier.pop()
                for neighbor in adjacent[current] - reached:
                    reached.add(neighbor)
                    frontier.append(neighbor)
            self.assertEqual(len(reached), len(component["vertices_m"]), component["id"])

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
