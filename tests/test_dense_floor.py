# SPDX-License-Identifier: Apache-2.0
import unittest
from humanmotionlib import math3d as m
from humanmotionlib.dense_floor import floor_bound


class DenseFloorTests(unittest.TestCase):
    def test_conservative_bound_cannot_hide_a_vertex_below_floor(self):
        vertices=[[-.1,-.2,-.3],[.1,-.2,.3],[-.1,.2,.3],[.1,.2,-.3]]
        for degrees in range(-180,181,15):
            frame={'position_m':[0,0,1],'rotation':m.mm(m.rx(degrees),m.ry(25))}
            lower,method=floor_bound(vertices,frame,-.0001)
            exact=min(m.add(frame['position_m'],m.mv(frame['rotation'],v))[2] for v in vertices)
            self.assertLessEqual(lower,exact+1e-12)
            self.assertGreaterEqual(exact,-.0001)

    def test_full_vertex_fallback_checks_non_contact_geometry(self):
        # An extra vertex on a torso-like mesh must still invalidate the floor;
        # declared foot targets or solver flags cannot hide it.
        vertices=[[0,0,.2],[1,0,.4],[0,1,-.5]]
        value,method=floor_bound(vertices,{'position_m':[0,0,.1],'rotation':m.I},-.0001)
        self.assertEqual(method,'complete-evaluated-vertex-minimum')
        self.assertAlmostEqual(value,-.4)
        self.assertLess(value,-.0001)


class CurvedGuideBoundTests(unittest.TestCase):
    def test_bezier_hull_contains_curved_tube_even_when_controls_overshoot(self):
        from humanmotionlib.dense_floor import guide_bounds
        from humanmotionlib.geometry import tube
        from humanmotionlib import math3d as m
        points=[[0,0,.3],[.05,.2,.1],[.1,.21,.12]]
        lo,hi=guide_bounds(points,.002)
        vertices,_=tube(points,.002)
        for v in vertices:
            self.assertTrue(all(lo[k]-1e-12<=v[k]<=hi[k]+1e-12 for k in range(3)))
        for rotation in (m.rx(35),m.ry(-65),m.rz(22)):
            frame={'position_m':[0,0,.3],'rotation':rotation}
            row=rotation[2]
            bound=.3+sum(row[i]*(lo[i] if row[i]>=0 else hi[i]) for i in range(3))
            exact=.3+min(m.mv(rotation,v)[2] for v in vertices)
            self.assertLessEqual(bound,exact+1e-12)
