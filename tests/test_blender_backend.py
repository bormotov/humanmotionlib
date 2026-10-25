# SPDX-License-Identifier: Apache-2.0
"""Clean headless backend builds; no GUI state or preexisting build outputs."""

from copy import deepcopy
import json
from pathlib import Path
import unittest

import importlib.util
from humanmotionlib import math3d as m
from humanmotionlib.backend_measurements import verify_backend
from humanmotionlib.prepare_skeleton import prepare
from humanmotionlib.prepared import write_json
from humanmotionlib.runtime import DEFAULT_BUILD_TIMEOUT, inspect_blender, invocation, project_root
from humanmotionlib.verify_skeleton import verify_transforms
from tests.run_roots import fresh_test_run_root, test_case_root, test_run_root


class BlenderBackendTests(unittest.TestCase):
    @classmethod
    def allocate_case(cls, name):
        return test_case_root('blender-backend', name)

    @classmethod
    def build(cls, prepared, operation):
        output_dir = fresh_test_run_root('backend-build')
        run_root = test_run_root('blender-backend')
        input_path = output_dir / 'input.json'
        write_json(input_path, prepared)
        identity = inspect_blender(run_root, workspace=project_root())
        if not identity['version'] or not identity['build_hash']:
            raise AssertionError('pinned Blender probe did not return a complete identity')
        executable = identity['receipt']['executable']
        result = invocation(
            [executable, '--background', '--factory-startup', '--python-exit-code', '1',
             '--python', str(Path(next(iter(importlib.util.find_spec('humanmotionlib').submodule_search_locations)) /
                                  'build_skeleton.py').resolve()), '--', '--input', str(input_path),
             '--output', str(output_dir), '--workspace', str(project_root()),
             '--expected-prepared-sha256', prepared['content_sha256']],
            run_root=output_dir, operation=operation, timeout_seconds=DEFAULT_BUILD_TIMEOUT,
            source_sha256=prepared['content_sha256'],
            expected_outputs=[output_dir / 'evaluated.json', output_dir / 'geometry-reference.json',
                              output_dir / 'build-metadata.json', output_dir / 'skeleton.blend'],
            workspace=project_root())
        cls.assert_receipt_outputs(result, [output_dir / 'evaluated.json',
                                            output_dir / 'geometry-reference.json',
                                            output_dir / 'build-metadata.json',
                                            output_dir / 'skeleton.blend'])
        evaluated = json.loads((output_dir / 'evaluated.json').read_text())
        if evaluated['prepared_sha256'] != prepared['content_sha256']:
            raise AssertionError('evaluated output does not match the prepared input')
        return evaluated

    @classmethod
    def assert_receipt_outputs(cls, receipt, outputs):
        if receipt['state'] != 'succeeded':
            raise AssertionError(receipt)
        if not receipt['source_sha256']:
            raise AssertionError('invocation receipt is missing prepared-input identity')
        if receipt['last_script_phase'] != 'script_complete':
            raise AssertionError(receipt)
        if receipt['output_validation']['status'] != 'pass':
            raise AssertionError(receipt)
        recorded = {entry['path'] for entry in receipt['output_validation']['files']}
        if not {str(path.resolve()) for path in outputs} <= recorded:
            raise AssertionError('invocation receipt does not validate every required output')

    @classmethod
    def setUpClass(cls):
        cls.builds=[]
        for index,height in enumerate((1.5,1.7,1.9,1.7)):
            prepared=prepare('adult-reference-v1',height,fixtures=['neutral','rest'])
            evaluated=cls.build(prepared, f'backend-stature-{index}')
            cls.builds.append((prepared,evaluated))

    def test_all_statures_have_valid_evaluated_geometry_frames_and_scene(self):
        for p,e in self.builds:
            report=verify_backend(p,e,verify_transforms(p,e['samples']))
            failed=[c['id'] for s in report['samples'] for c in s['checks'] if c['status']!='pass']
            self.assertEqual(report['status'],'pass',str(failed[:10]))
            self.assertEqual(len(e['metadata']['native_bones']),176)
            self.assertEqual(e['metadata']['collections'],['Anatomy','Controls','Humanoid','Review'])
            self.assertTrue(all(e['metadata']['independent_collection_visibility'].values()))
            for sample in e['samples']:
                for side in ('L','R'):
                    foot=[g for g in sample['geometry'].values() if g['structure'].endswith('.'+side) and g['structure'].split('.')[0] in ('talus','calcaneus','midfoot','metatarsal','toe')]
                    low=[min(g['world_bounds_m'][0][i] for g in foot) for i in range(3)]
                    high=[max(g['world_bounds_m'][1][i] for g in foot) for i in range(3)]
                    self.assertLess(abs((high[1]-low[1])/p['sources']['profile']['stature_m']-.158),1e-4)
                    self.assertLess(abs((high[0]-low[0])/p['sources']['profile']['stature_m']-.050),1e-4)

    def test_two_clean_builds_agree_in_topology_positions_and_rotations(self):
        _,a=self.builds[1];_,b=self.builds[3]
        self.assertEqual(a['metadata'],b['metadata'])
        for first,second in zip(a['samples'],b['samples']):
            self.assertEqual(set(first['geometry']),set(second['geometry']))
            for id,frame in first['frames'].items():
                self.assertLess(m.norm(m.sub(frame['position_m'],second['frames'][id]['position_m'])),1e-6*1.7)
                self.assertLess(max(abs(frame['rotation'][i][j]-second['frames'][id]['rotation'][i][j]) for i in range(3) for j in range(3)),1e-6)
            for id,entry in first['geometry'].items():
                self.assertEqual(entry['topology_sha256'],second['geometry'][id]['topology_sha256'])
                self.assertEqual(entry['vertex_count'],second['geometry'][id]['vertex_count'])
                self.assertLess(max(abs(a-b) for va,vb in zip(entry['world_bounds_m'],second['geometry'][id]['world_bounds_m']) for a,b in zip(va,vb)),1e-6*1.7)

    def test_missing_or_modified_backend_evidence_cannot_pass(self):
        p,e=self.builds[1]
        for mutation in ('geometry','attachment','scale','floor','bone','frame'):
            changed=deepcopy(e);sample=changed['samples'][0]
            if mutation=='geometry':sample['geometry'].pop(next(iter(sample['geometry'])))
            elif mutation=='attachment':sample['attachments']['contact.heel.R']['structure']='toe.1.R'
            elif mutation=='scale':sample['object_scales']['tibia.R']=[1,1.1,1]
            elif mutation=='floor':sample['geometry']['toe.1.R.geometry.1']['world_bounds_m'][0][2]=-.01
            elif mutation=='bone':sample['bone_scales'].pop('tibia.R')
            else:sample['frames']['scapula.R']['rotation']=m.I
            report=verify_backend(p,changed,verify_transforms(p,changed['samples']))
            self.assertEqual(report['status'],'fail',mutation)

    def test_rigid_deep_chains_do_not_accumulate_scale_or_shear(self):
        from fractions import Fraction
        from humanmotionlib.prepared import seal
        targets={'arm-raise':Fraction(4,3),'squat':Fraction(2),
                 'sweep-lumbar-rotation':Fraction(1,3),'sweep-pelvis-yaw':Fraction(1),
                 'sweep-thoracic-lateral_flexion':Fraction(2,3),'sweep-elbow-bilateral-flexion':Fraction(3)}
        p=prepare('adult-reference-v1',fixtures=list(targets))
        p['samples']=[s for s in p['samples'] if Fraction(s['beat']['numerator'],s['beat']['denominator'])==targets[s['fixture']]]
        p=seal(p)
        e=self.build(p, 'backend-rigid-chains')
        report=verify_backend(p,e,verify_transforms(p,e['samples']))
        failed=[c['id'] for s in report['samples'] for c in s['checks'] if c['status']=='fail']
        self.assertEqual(report['status'],'pass',str(failed[:10]))

    def test_isolated_subset_cannot_satisfy_complete_diagnostic_acceptance(self):
        from humanmotionlib.verification_run import verify_collection
        p,e=self.builds[1]
        metrics_case = self.allocate_case('collection-metrics')
        report=verify_collection(p,e,metrics_case/'metrics.json',verify_transforms,workspace=project_root())
        self.assertEqual(report['status'],'fail')
        failed={c['id'] for c in report['checks'] if c['status']=='fail'}
        self.assertIn('diagnostic_fixture_coverage',failed)
        self.assertTrue(all(s['status']=='pass' for s in report['samples']))

    def test_native_rest_frame_scaling_in_deep_spinal_chains(self):
        base=self.builds[1][1]
        for prepared,evaluated in self.builds:
            height=prepared['sources']['profile']['stature_m']
            for sample,reference in zip(evaluated['samples'],base['samples']):
                for id,frame in sample['frames'].items():
                    residual=m.norm(m.sub(m.scale(frame['position_m'],1/height),m.scale(reference['frames'][id]['position_m'],1/1.7)))
                    self.assertLessEqual(residual,1e-6,id)
