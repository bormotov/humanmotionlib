# SPDX-License-Identifier: Apache-2.0
"""Thoracic shape, native-evidence contract, and adversarial binding tests."""

from copy import deepcopy
import math
import unittest
from humanmotionlib import math3d as m
from humanmotionlib.geometry import primitive_mesh
from humanmotionlib.guides import compile_guides
from humanmotionlib.kinematics import KinematicModel
from humanmotionlib.mirror import mirror_structure
from humanmotionlib.poses import scaled_profile, scale_meter_fields
from humanmotionlib.source_validation import validate_document
from humanmotionlib.thorax_measurements import measure_thorax, rib_controls, hermite_curve
from humanmotionlib.validate import load_sources, validate_bundle


def mesh_evidence(profile, solved):
    """Synthetic measurement adapter for unit tests; Blender is verified separately."""
    geometry={}
    for body in profile['structures']:
        if body['id']!='sternum' and not body['id'].startswith(('rib.','cartilage.')):continue
        frame=solved['frames'][body['id']]
        move=lambda p:m.add(frame['position_m'],m.mv(frame['rotation'],p))
        for primitive in body['geometry']:
            pts=solved['guides'].get(primitive['id'],primitive['points_m'])
            vertices,_=primitive_mesh(primitive,pts if primitive['type']=='tube' else None)
            world=[move(v) for v in vertices]
            if primitive['type']=='shell':
                n=len(world)//2
                controls=[m.scale(m.add(world[i],world[i+n]),.5) for i in range(n)]
                thickness=[math.dist(world[i],world[i+n]) for i in range(n)]
            else:
                n=len(pts);controls=[m.scale([sum(world[k][c] for k in range(ring*16,(ring+1)*16)) for c in range(3)],1/16) for ring in [i*16//(n-1) for i in range(n)]]
                thickness=[]
            geometry[primitive['id']]={'controls_m':controls,'thicknesses_m':thickness,
                'world_bounds_m':[[min(v[k] for v in world) for k in range(3)],[max(v[k] for v in world) for k in range(3)]]}
    return {'frames':solved['frames'],'geometry':geometry}


class ThoraxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle,_=load_sources('adult-reference-v1')
        cls.profile=cls.bundle['profile'];cls.mobility=cls.bundle['mobility']

    def test_three_statures_and_spinal_motion_meet_independent_shape_and_closure(self):
        for h in (1.5,1.7,1.9):
            profile=scaled_profile(self.profile,h);mobility=scale_meter_fields(self.mobility,h/1.7)
            model=KinematicModel(profile,mobility)
            for actions in ({},{'thoracic.flexion':30},{'thoracic.lateral_flexion':15},{'thoracic.rotation':20}):
                evidence=mesh_evidence(profile,model.solve(actions))
                checks=measure_thorax(profile,evidence,not actions)
                self.assertTrue(checks)
                self.assertFalse([c for c in checks if c['status']!='pass'],str([c for c in checks if c['status']!='pass'][:4]))

    def test_old_uniform_geometry_fails_relational_checks(self):
        profile=deepcopy(self.profile);height=profile['stature_m']
        widths=[.055,.065,.075,.080,.082,.082,.078,.072,.065,.055,.045,.035]
        for body in profile['structures']:
            if not body['id'].startswith('rib.'):continue
            j=int(body['id'].split('.')[1]);sign=1 if body['id'].endswith('.R') else -1;w=widths[j-1]
            pts=[[0,0,0],[sign*w,.020,-.008]]
            if j<=10:pts.append([sign*.65*w,.100,-.012])
            body['geometry'][0]['points_m']=[m.scale(p,height) for p in pts]
        evidence=mesh_evidence(profile,KinematicModel(profile,self.mobility).solve())
        failed=[c['id'] for c in measure_thorax(profile,evidence,True) if c['status']=='fail']
        self.assertTrue(any('anterior_overhang' in c for c in failed),str(failed[:10]))
        self.assertTrue(any('.surface.1.' in c for c in failed))

    def test_bony_arch_and_stale_midpoint_fail_even_with_valid_transforms(self):
        model=KinematicModel(self.profile,self.mobility)
        solved=model.solve({'thoracic.flexion':30});evidence=mesh_evidence(self.profile,solved)
        nominal=deepcopy(evidence)
        profile=deepcopy(self.profile)
        body=next(b for b in profile['structures'] if b['id']=='cartilage.8.R')
        body['geometry'][0]['bindings'][2]={'point_index':2,'structure':'rib.7.R','position_m':[0,0,0]}
        evidence['geometry']['cartilage.8.R.geometry.0']['controls_m'][2]=evidence['geometry']['rib.7.R.geometry.0']['controls_m'][-1]
        failed=[c['id'] for c in measure_thorax(profile,evidence) if c['status']=='fail']
        self.assertTrue(any('distal_endpoint' in c for c in failed))
        self.assertTrue(any('connection_topology' in c for c in failed))
        rest=mesh_evidence(self.profile,model.solve())
        nominal['geometry']['cartilage.7.R.geometry.0']['controls_m'][1]=rest['geometry']['cartilage.7.R.geometry.0']['controls_m'][1]
        self.assertTrue(any('midpoint' in c['id'] and c['status']=='fail' for c in measure_thorax(self.profile,nominal)))

    def test_missing_native_evidence_fails(self):
        solved=KinematicModel(self.profile,self.mobility).solve()
        checks=measure_thorax(self.profile,{'frames':solved['frames']},True)
        self.assertTrue(any(c['status']=='fail' for c in checks))

    def test_binding_validation_and_closed_schemas(self):
        for mutation,expected in [
            (lambda g:g['bindings'][2].update(guide='missing'),'unresolved guide'),
            (lambda g:g['bindings'][2].update(control_index=99),'invalid or unbound'),
            (lambda g:g['bindings'][2].update(guide='cartilage.7.L.geometry.0'),'cross-side'),
            (lambda g:g['bindings'][2].update(guide='cartilage.8.R.geometry.0'),'cycle'),
            (lambda g:g['bindings'].append(deepcopy(g['bindings'][0])),'duplicate'),
            (lambda g:g['bindings'][1].update(endpoints=[1,2]),'midpoint')]:
            bundle=deepcopy(self.bundle);body=next(b for b in bundle['profile']['structures'] if b['id']=='cartilage.8.R');mutation(body['geometry'][0])
            with self.subTest(expected=expected),self.assertRaisesRegex(ValueError,expected):validate_bundle(bundle)
        for field,value in [('expression','eval()'),('kind','arbitrary')]:
            profile=deepcopy(self.profile);g=next(b for b in profile['structures'] if b['id']=='cartilage.8.R')['geometry'][0]
            g['bindings'][2][field]=value
            with self.assertRaises(ValueError):validate_document(profile,'profile')
        validate_document(self.profile,'profile')

    def test_order_independence_and_mirrored_bindings(self):
        profile=deepcopy(self.profile);profile['structures'].reverse()
        first=KinematicModel(self.profile,self.mobility).solve({'thoracic.rotation':20})
        other=KinematicModel(profile,self.mobility).solve({'thoracic.rotation':20})
        self.assertEqual(first['guides'],other['guides'])
        source=next(b for b in self.profile['structures'] if b['id']=='cartilage.8.R')
        self.assertEqual(mirror_structure(mirror_structure(source)),source)

    def test_independent_hermite_endpoints_and_monotonic_descent_dossier(self):
        for j in range(1,13):
            points=rib_controls(j);curve=hermite_curve(points)
            for k in range(5):self.assertLess(math.dist(curve[k*256],points[k]),1e-12)
