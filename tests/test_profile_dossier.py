# SPDX-License-Identifier: Apache-2.0
"""Independent checks of canonical records against the numerical dossier."""

from pathlib import Path
import math
import unittest

import yaml

from tools import math3d as m
from tools.runtime import project_root
from tools.source_validation import validate_document


def load_profile():
    return yaml.safe_load((project_root()/"rig/profiles/adult-reference-v1.yaml").read_text())


def foot_bounds(profile, side):
    """Exact neutral primitive bounds for the foot's declared numeric records.

    Ellipsoids and round caps include their cardinal extrema at the specified
    mesh resolution. Straight swept shafts use their perpendicular radial
    extent. The toe caps and calcaneus determine the reported extrema.
    """
    lo, hi = [math.inf]*3, [-math.inf]*3
    prefixes = ("talus.", "hindfoot.", "calcaneus.", "midfoot.", "metatarsal.", "mtp.", "toe.")
    for body in profile["structures"]:
        if not body["id"].startswith(prefixes) or not body["id"].endswith("."+side):
            continue
        origin, basis = body["origin_m"], body["basis"]
        for primitive in body["geometry"]:
            kind = primitive["type"]
            if kind in ("sphere", "ellipsoid"):
                center = m.add(origin, m.mv(basis, primitive["center_m"]))
                radii = [primitive["radius_m"]]*3 if kind == "sphere" else primitive["radii_m"]
                extent = [math.sqrt(sum((basis[i][j]*radii[j])**2 for j in range(3))) for i in range(3)]
                samples = [(center, extent)]
            elif kind == "tube":
                points = [m.add(origin, m.mv(basis, p)) for p in primitive["points_m"]]
                samples = []
                for a, b in zip(points, points[1:]):
                    axis = m.unit(m.sub(b, a))
                    extent = [primitive["radius_m"]*math.sqrt(max(0, 1-x*x)) for x in axis]
                    samples.extend([(a, extent), (b, extent)])
            else:
                raise AssertionError(f"Unmeasured foot primitive: {kind}")
            for center, extent in samples:
                for j in range(3):
                    lo[j] = min(lo[j], center[j]-extent[j])
                    hi[j] = max(hi[j], center[j]+extent[j])
    return lo, hi


class ProfileDossierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_profile()

    def test_schema_inventory_frames_and_references(self):
        p = self.profile
        validate_document(p, "profile")
        records = {record["id"]: record for record in p["structures"]}
        self.assertEqual(len(records), len(p["structures"]))
        landmarks = {record["id"]: record for record in p["landmarks"]}
        self.assertEqual(len(landmarks), len(p["landmarks"]))
        for record in records.values():
            m.validate_basis(record["basis"])
            m.validate_quaternion(record["rest_orientation"])
            for name in record["landmarks"]: self.assertIn(name, landmarks)
            seen = set()
            current = record
            while current["parent"] is not None:
                self.assertNotIn(current["id"], seen)
                seen.add(current["id"])
                self.assertIn(current["parent"], records)
                current = records[current["parent"]]
        for region, count in (("C", 7), ("T", 12), ("L", 5)):
            for i in range(1, count+1): self.assertIn(region+str(i), records)
        for side in ("L", "R"):
            for name in ("clavicle", "scapula", "humerus", "radius", "ulna", "femur", "patella", "tibia", "fibula", "talus", "calcaneus", "midfoot", "mtp"):
                self.assertIn(name+"."+side, records)
            for i in range(1, 13): self.assertIn(f"rib.{i}.{side}", records)

    def test_mechanical_segment_ratios(self):
        landmarks = {r["id"]: r["position_m"] for r in self.profile["landmarks"]}
        stature = self.profile["stature_m"]
        for side in ("L", "R"):
            for a, b, ratio in (("shoulder", "elbow", .1605), ("elbow", "wrist", .1365),
                                ("hip", "knee", .234), ("knee", "ankle", .2155)):
                self.assertAlmostEqual(m.norm(m.sub(landmarks[a+"."+side], landmarks[b+"."+side]))/stature, ratio, places=12)

    def test_dossier_foot_length(self):
        for side in ("L", "R"):
            lo, hi = foot_bounds(self.profile, side)
            measured = (hi[1]-lo[1])/self.profile["stature_m"]
            with self.subTest(side=side):
                self.assertAlmostEqual(measured, .158, delta=1e-4,
                    msg=f"Approved dossier length .158 H differs from numeric primitives: {measured:.9f} H")

    def test_dossier_foot_width(self):
        for side in ("L", "R"):
            lo, hi = foot_bounds(self.profile, side)
            measured = (hi[0]-lo[0])/self.profile["stature_m"]
            with self.subTest(side=side):
                self.assertAlmostEqual(measured, .050, delta=1e-4,
                    msg=f"Approved dossier width .050 H differs from numeric primitives: {measured:.9f} H")

    def test_record_provenance_resolves(self):
        register = (project_root()/"docs/used-materials.md").read_text()
        for record in [self.profile, *self.profile["structures"], *self.profile["landmarks"]]:
            provenance = record["provenance"]
            self.assertTrue(provenance["rationale"])
            self.assertTrue(provenance["changes"])
            for source in provenance["sources"]:
                self.assertIn(source["material"], register)
                self.assertTrue(source["locator"])
