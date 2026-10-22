# SPDX-License-Identifier: Apache-2.0
from collections import Counter
import math
import unittest

from tools import math3d as m
from tools.geometry import ellipsoid, primitive_mesh, tube
from tools.source_validation import load_yaml
from tools.runtime import project_root


class GeometryTests(unittest.TestCase):
    def assertClosed(self,vertices,faces):
        edges=Counter(tuple(sorted((a,b))) for f in faces for a,b in zip(f,f[1:]+f[:1]))
        self.assertTrue(edges)
        self.assertEqual(set(edges.values()),{2})
        self.assertTrue(all(len(f)==3 and len(set(f))==3 for f in faces))
        self.assertTrue(all(math.isfinite(x) for v in vertices for x in v))

    def test_closed_ellipsoid_fixed_resolution_and_exact_extremes(self):
        vertices,faces=ellipsoid([1,2,3],[.1,.2,.3])
        self.assertEqual(len(vertices),266)
        self.assertClosed(vertices,faces)
        for axis in range(3):
            self.assertAlmostEqual(min(v[axis] for v in vertices),[.9,1.8,2.7][axis])
            self.assertAlmostEqual(max(v[axis] for v in vertices),[1.1,2.2,3.3][axis])
        for face in faces:
            a,b,c=(vertices[i] for i in face)
            self.assertGreater(m.dot(m.cross(m.sub(b,a),m.sub(c,a)),m.sub(a,[1,2,3])),0)

    def test_tube_caps_and_fixed_intervals(self):
        vertices,faces=tube([[0,0,0],[0,.2,0]],.01)
        self.assertEqual(len(vertices),17*16)
        self.assertClosed(vertices,faces)
        self.assertAlmostEqual(min(v[2] for v in vertices),-.01)
        self.assertAlmostEqual(max(v[2] for v in vertices),.01)

    def test_every_source_primitive_closed_and_stature_linear(self):
        profile=load_yaml(project_root()/'rig/profiles/adult-reference-v1.yaml')
        from tools.poses import scale_meter_fields
        for body in profile['structures']:
            for primitive in body['geometry']:
                a,faces=primitive_mesh(primitive)
                self.assertClosed(a,faces)
                b,bfaces=primitive_mesh(scale_meter_fields(primitive,1.9/1.7))
                self.assertEqual(faces,bfaces)
                self.assertLess(max(m.norm(m.sub(y,m.scale(x,1.9/1.7))) for x,y in zip(a,b)),1e-12,primitive['id'])
