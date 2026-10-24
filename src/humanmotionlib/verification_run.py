# SPDX-License-Identifier: Apache-2.0
"""Sharded full backend evidence: retain every metric without a giant root file."""

from copy import deepcopy
from fractions import Fraction
import math
from pathlib import Path

from humanmotionlib import math3d as m
from humanmotionlib.backend_measurements import verify_backend
from humanmotionlib.measurements import Measurements
from humanmotionlib.prepared import write_json


def verify_collection(prepared,evaluated,output,transform_verifier):
    if evaluated.get('prepared_sha256')!=prepared['content_sha256']:raise ValueError('Evaluated/prepared hash mismatch')
    expected={s['id']:s for s in prepared['samples']};actual={s['id']:s for s in evaluated['samples']}
    if len(actual)!=len(evaluated['samples']) or set(actual)!=set(expected):raise ValueError('Missing/extra/duplicate evaluated samples')
    output=Path(output);details=output.parent/(output.stem+'-samples');details.mkdir(parents=True,exist_ok=True)
    reports=[];history={};first_scene=None;overall=Measurements(0);measured_action_values={}
    metadata=evaluated['metadata']
    declared_fixtures={f['id'] for f in prepared['sources']['diagnostics']}
    sampled_fixtures={s['fixture'] for s in prepared['samples']}
    overall.scalar('diagnostic_fixture_coverage',len(declared_fixtures^sampled_fixtures),0,0,'count')
    active={b['id'] for b in prepared['sources']['profile']['structures'] if b['representation']!='omitted'}
    overall.scalar('native_bone_inventory',len(set(metadata.get('native_bones',[]))^active),0,0,'count')
    semantics={e['humanoid']:e['target'] for e in prepared['sources']['humanoid-map']['entries']}
    overall.scalar('semantic_target_inventory',int(metadata.get('semantic_targets')!=semantics),0,0,'boolean')
    overall.scalar('collection_inventory',int(set(metadata.get('collections',[]))!={'Anatomy','Controls','Humanoid','Review'}),0,0,'boolean')
    visibility=metadata.get('independent_collection_visibility',{})
    overall.scalar('collection_independence',int(set(visibility)!={'Anatomy','Controls','Humanoid','Review'} or not all(visibility.values())),0,0,'boolean')
    for index,id in enumerate(sorted(expected)):
        p=prepared|{'samples':[expected[id]]};e=evaluated|{'samples':[actual[id]]}
        fixture_history=history.setdefault(expected[id]['fixture'],{})
        result=verify_backend(p,e,transform_verifier(p,e['samples']),fixture_history)
        sample=result['samples'][0]
        measured_action_values[id]=sample.get('measured_actions',{})
        scene=actual[id].get('scene')
        if first_scene is None:first_scene=scene
        checks=Measurements(expected[id]['beat']['numerator']/expected[id]['beat']['denominator'])
        checks.scalar('scene.cross_fixture_stability',int(scene!=first_scene),0,0,'boolean')
        sample['checks'].extend(checks.checks)
        failed=[c for c in sample['checks'] if c['status']!='pass']
        sample['status']='fail' if failed else 'pass'
        path=details/(id.replace('/','-')+'.json')
        image_id=expected[id]['frame_id'];fixture=expected[id]['fixture']
        for metric in sample['checks']:
            metric['image']=f'clean-a/frames/{fixture}/front/{image_id:05d}.png'
            if metric['id'].startswith('thorax.') and fixture in ('neutral','rest'):
                metric['image']=f'clean-a/frames/{fixture}/thorax-side-isolated/{image_id:05d}.png'
            if metric['id'].startswith('balance.') and fixture=='squat':
                metric['image']=f'clean-a/frames/{fixture}/side/{image_id:05d}.png'
        write_json(path,sample)
        reports.append({'id':id,'fixture':fixture,'status':sample['status'],'metric_count':len(sample['checks']),
                        'details':str(path.relative_to(output.parent)),'failed_checks':failed})
        if index%100==0:print(f'Verified {index+1}/{len(expected)}: {id}',flush=True)
    fixtures={f['id']:f for f in prepared['sources']['diagnostics']}
    height=prepared['sources']['profile']['stature_m']
    for id,fixture in fixtures.items():
        selected=sorted((s for s in prepared['samples'] if s['fixture']==id),key=lambda s:Fraction(s['beat']['numerator'],s['beat']['denominator']))
        if not selected:continue
        first,last=actual[selected[0]['id']],actual[selected[-1]['id']]
        for body,frame in first['frames'].items():
            other=last['frames'][body]
            overall.position(id+'.'+body+'.loop_origin',other['position_m'],frame['position_m'],1e-4*height)
            overall.rotation(id+'.'+body+'.loop_rotation',other['rotation'],frame['rotation'])
        if id=='walking-in-place':
            for beat,side in ((1,'L'),(5,'R')):
                match=next((s for s in selected if Fraction(s['beat']['numerator'],s['beat']['denominator'])==beat),None)
                if match is None:overall.scalar(id+'.apex_evidence.'+side,1,0,0,'boolean');continue
                sample=actual[match['id']]
                foot=[g for g in sample['geometry'].values() if g['structure'].endswith('.'+side) and g['structure'].split('.')[0] in ('calcaneus','midfoot','metatarsal','toe')]
                clearance=min(g['world_bounds_m'][0][2] for g in foot)/height
                overall.limit(id+'.'+side+'.complete_sole_apex',clearance,[.02,1e100],0,'H')
                measured_knee=measured_action_values[match['id']].get('knee.'+side+'.flexion')
                if measured_knee is None:overall.scalar(id+'.'+side+'.apex_knee_evidence',1,0,0,'boolean')
                else:overall.limit(id+'.'+side+'.apex_knee',measured_knee,[45,130],.1)
    for id,plans in prepared.get('sampling',{}).items():
        duration=fixtures[id]['duration_beats']
        overall.scalar(id+'.tempo_coverage',int({p['bpm'] for p in plans}!={60,120,180}),0,0,'boolean')
        for plan in plans:
            n=plan['intervals_per_beat'];bpm=plan['bpm']
            expected_n=max(3,math.ceil(Fraction(60,bpm)/Fraction(1,5)))
            overall.scalar(id+f'.{bpm}.intervals_per_beat',n,expected_n,0,'count')
            missing={record['sample_id'] for record in plan['animation']} - set(actual)
            overall.scalar(id+f'.{bpm}.delivered_sample_inventory',len(missing),0,0,'count')
            overall.scalar(id+f'.{bpm}.static_count',len(plan['static']),duration+1,0,'count')
            overall.scalar(id+f'.{bpm}.animation_count',len(plan['animation']),duration*n+1,0,'count')
            times=[Fraction(s['seconds']['numerator'],s['seconds']['denominator']) for s in plan['animation']]
            for index,record in enumerate(plan['animation']):
                beat=Fraction(record['beat']['numerator'],record['beat']['denominator'])
                expected_beat=Fraction(index,expected_n)
                seconds=times[index]
                overall.scalar(id+f'.{bpm}.beat.{index}',float(abs(beat-expected_beat)),0,0,'beats')
                overall.scalar(id+f'.{bpm}.seconds.{index}',float(abs(seconds-expected_beat*Fraction(60,bpm))),0,0,'s')
                if record['sample_id'] in expected:
                    sampled=expected[record['sample_id']]['beat']
                    sampled_beat=Fraction(sampled['numerator'],sampled['denominator'])
                    overall.scalar(id+f'.{bpm}.source_beat.{index}',float(abs(sampled_beat-beat)),0,0,'beats')
            overall.limit(id+f'.{bpm}.max_interval_ms',float(max((b-a for a,b in zip(times,times[1:])),default=0)*1000),[0,200],1e-9,'ms')
            lookup={Fraction(s['beat']['numerator'],s['beat']['denominator']):s['sample_id'] for s in plan['animation']}
            for static in plan['static']:
                beat=Fraction(static['beat']['numerator'],static['beat']['denominator'])
                overall.scalar(id+f'.{bpm}.shared_sample.{beat}',int(static['sample_id']!=lookup[beat]),0,0,'boolean')
    failures=[c for c in overall.checks if c['status']!='pass']
    for check in overall.checks:
        fixture=check['id'].split('.')[0]
        if fixture not in fixtures:fixture=prepared['samples'][0]['fixture']
        check['image']=f'clean-a/frames/{fixture}/front/00000.png'
    return {'status':'pass' if reports and not failures and all(r['status']=='pass' for r in reports) else 'fail',
            'scope':'evaluated-body-geometry-scene-contacts-timing','source_hashes':prepared['source_hashes'],
            'metadata':evaluated['metadata'],'samples':reports,'checks':overall.checks,
            'metric_count':sum(r['metric_count'] for r in reports)+len(overall.checks),
            'acceptance':'Independent rebuild/review and human visual verdict remain pending.'}
