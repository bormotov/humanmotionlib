# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.backend_measurements import verify_backend
from tools.prepared import read_prepared
from tools.runtime import blender_executable,project_root
from tools.verify_skeleton import verify_transforms


class PipelineFaultTests(unittest.TestCase):
    def test_actual_scene_faults_are_rejected_for_the_intended_measurement(self):
        # Select a compact set of canonical samples in a fresh prepared payload.
        from tools.prepare_skeleton import prepare
        from tools.prepared import seal,write_json
        p=prepare('adult-reference-v1',fixtures=['neutral','arm-raise','squat','sweep-hip-bilateral-adduction','sweep-thoracic-flexion'])
        keep={('neutral',0),('arm-raise',1),('squat',2),('sweep-hip-bilateral-adduction',3),('sweep-thoracic-flexion',3)}
        p['samples']=[s for s in p['samples'] if (s['fixture'],s['beat']['numerator']/s['beat']['denominator']) in keep]
        from tools.diagnostics import DiagnosticEvaluator
        e=DiagnosticEvaluator(p['sources']);source=next(s for s in p['samples'] if s['fixture']=='squat')
        actions=dict(source['expected_actions']);i,hip,v=e.flat_leg(90,12,12)
        actions.update({'pelvis.y':-v[1],'pelvis.z':.04*e.height-v[2],'pelvis.pitch':12})
        for side in ('L','R'):
            actions['ankle.'+side+'.dorsiflexion']=12;actions['hindfoot.'+side+'.inversion']=i
            for name,value in zip(('flexion','adduction','external_rotation'),hip):actions['hip.'+side+'.'+name]=value
        old=e.model.solve(actions);p['fault_samples']={'former-squat':{'frames':old['frames'],'guides':old['guides']}}
        p=seal(p)
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp);write_json(directory/'input.json',p)
            result=subprocess.run([blender_executable(),'--background','--factory-startup','--python-exit-code','1','--python','tests/blender_fault_harness.py','--','--input',str(directory/'input.json'),'--output',str(directory/'faults.json')],cwd=project_root(),capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            faults=json.loads((directory/'faults.json').read_text())
            intended={'frozen-scapula':'shoulder.R.scapula_curve','frozen-patella':'patella.R.tracking',
                      'wrong-side-sign':'hip.L.adduction.intent','stretched-shank':'tibia.R.geometry.0.scale.1',
                      'undeclared-world-root':'world_root.translation',
                      'uniform-ribs':'thorax.rib.1.R.anterior_overhang',
                      'bony-costal-arch':'thorax.cartilage.8.R.distal_endpoint',
                      'stale-cartilage-midpoint':'thorax.cartilage.7.R.midpoint',
                      'former-squat':'balance.reference_margin','rearward-upper-body':'balance.reference_margin'}
            self.assertEqual({f['fault'] for f in faults['faults']},set(intended))
            for fault in faults['faults']:
                source=next(s for s in p['samples'] if s['id']==fault['expected_sample_id'])
                subset=p|{'samples':[source]}
                e={'format':'skeleton-evaluated/v1','prepared_sha256':p['content_sha256'],'metadata':faults['metadata'],'samples':[fault['measurement']]}
                r=verify_backend(subset,e,verify_transforms(subset,e['samples']))
                failures={c['id'] for s in r['samples'] for c in s['checks'] if c['status']=='fail'}
                self.assertEqual(r['status'],'fail',fault['fault'])
                self.assertIn(intended[fault['fault']],failures,fault['fault'])
