# SPDX-License-Identifier: Apache-2.0
"""Streaming dense numeric audit; retains maxima and every failing measurement."""

import math
from humanmotionlib import math3d as m
from humanmotionlib.contacts import attachments,contact_checks
from humanmotionlib.diagnostics import DiagnosticEvaluator
from humanmotionlib.diagnostics import interpolate
from humanmotionlib.measurements import measure_pose
from humanmotionlib.sampling import delivered_beats
from humanmotionlib.thorax_measurements import data_guide_residuals, MOTION_REQUIREMENT
from humanmotionlib.balance import mass_observations, measure_balance


def _balance_image_reference(beat,duration):
    """Link a dense pose to the nearest delivered render, without implying identity."""
    beats=delivered_beats(duration)
    index=min(range(len(beats)),key=lambda i:(abs(float(beats[i])-beat),float(beats[i])))
    delivered=float(beats[index]);sample=f'{index:05d}'
    return {'relationship':'nearest-delivered-render-context','sample_id':f'squat/{sample}',
            'beat':delivered,'exact_match':abs(delivered-beat)<=1e-12,
            'paths_relative_to':'review-pack-root',
            'page':f'squat.html#{index}',
            'front':f'clean-a/balance/squat-{sample}-front.png',
            'side':f'clean-a/balance/squat-{sample}-side.png'}


def _balance_observation(beat,index,result,observed,contacts,duration):
    anchors=sorted({anchor for contact in contacts for anchor in contact['anchors']})
    measured_support={anchor:{'position_m':observed['attachments'][anchor]['position_m']}
                      for anchor in anchors if anchor in observed['attachments']}
    return {'sample_id':f'squat/dense-{index:05d}','beat':beat,
            'units':{'beat':'beat','mass_positions':'m','support_positions':'m',
                     'support_hull':'m','edge_margins':'m','normalized_margins':'H',
                     'placement_allowance':'H','perturbation_lower_bound':'H'},
            'status':result['status'],'body_frames':observed['frames'],
            'mass_points':observed['mass_points'],
            'measured_support_points':measured_support,
            'contacts':contacts,'checks':result['checks'],'assessment':result['assessment'],
            'image_reference':_balance_image_reference(beat,duration)}


def _balance_extrema(observations):
    """Retain extrema with source sample identity for all static balance outputs."""
    values=[]
    for sample in observations:
        assessment=sample['assessment']
        if assessment is None:continue
        beat=sample['beat'];sample_id=sample['sample_id']
        for name,variant in assessment['variants'].items():
            for metric,value,unit in [('margin_h',variant['margin_h'],'H')]:
                values.append((f'{name}.{metric}',value,unit,beat,sample_id))
            for axis,value in zip(('x','y','z'),variant['com_m']):
                values.append((f'{name}.com_{axis}',value,'m',beat,sample_id))
            for edge,value in enumerate(variant['edge_margins_m']):
                values.append((f'{name}.edge_margin_{edge}',value,'m',beat,sample_id))
        values.extend([
            ('placement_allowance_h',assessment['placement_allowance_h'],'H',beat,sample_id),
            ('perturbation_lower_bound_h',assessment['perturbation_lower_bound_h'],'H',beat,sample_id)])
    grouped={}
    for metric,value,unit,beat,sample_id in values:
        row=grouped.setdefault(metric,{'unit':unit,'minimum':None,'maximum':None})
        for key,choose in [('minimum',lambda a,b:a<b),('maximum',lambda a,b:a>b)]:
            old=row[key]
            if old is None or choose(value,old['value']):row[key]={'value':value,'beat':beat,'sample_id':sample_id}
    return grouped


def dense_beats(fixture):
    maximum=0
    for track in fixture['tracks']:
        for a,b in zip(track['keys'],track['keys'][1:]):
            derivative=abs(b['value']-a['value'])/(b['beat']-a['beat'])*(math.pi/2 if track['easing']=='half_wave' else 1.5 if track['easing']=='ease_in_out' else 1)
            maximum=max(maximum,derivative)
    if fixture['construction']['type']=='walking_flat':
        maximum=max(maximum,math.pi/2*fixture['construction']['parameters']['knee_peak_deg'])
    intervals=max(100,math.ceil(maximum/.25))
    # Closed squat inputs include derived hip angles; their nonlinear slope
    # can exceed the authored knee-key slope. Oversample, then measure the
    # actual resulting input maximum against the same 0.25-degree bound.
    if fixture['construction']['type']=='squat_closed':intervals*=2
    times={i/intervals for i in range(fixture['duration_beats']*intervals+1)}
    times.update(float(beat) for beat in delivered_beats(fixture['duration_beats']))
    # Include exact engineering/reference inputs, not only nearby beat samples.
    for track in fixture['tracks']:
        for a,b in zip(track['keys'],track['keys'][1:]):
            lower,upper=sorted((a['value'],b['value']))
            references={15*j for j in range(math.ceil(lower/15),math.floor(upper/15)+1)}|{-80,-40,0,10,15,20,30,40,60,75,90,120,130,140,160,168}
            for value in sorted(v for v in references if lower<v<upper):
                low,high=a['beat'],b['beat']
                for _ in range(60):
                    middle=(low+high)/2
                    measured=interpolate([a,b],middle,track['easing'])
                    if (measured<value)==(b['value']>a['value']):low=middle
                    else:high=middle
                times.add((low+high)/2)
    return sorted(times)


def audit_squat_balance(sources):
    """Complete existing dense squat grid at one stature; no native-build claim."""
    evaluator=DiagnosticEvaluator(sources);fixture=evaluator.fixtures['squat']
    times=dense_beats(fixture);failures=[];minimum=None;observations=[]
    for index,beat in enumerate(times):
        p=evaluator.evaluate('squat',beat)
        observed={'frames':p['frames'],'mass_points':mass_observations(sources['profile'],p['frames']),
                  'attachments':attachments(sources['profile'],p['frames'])}
        result=measure_balance(sources['profile'],observed,p['contacts'],beat,True)
        failures.extend(c for c in result['checks'] if c['status']!='pass')
        observations.append(_balance_observation(beat,index,result,observed,p['contacts'],fixture['duration_beats']))
        assessment=result['assessment']
        if assessment is not None and (minimum is None or assessment['perturbation_lower_bound_h']<minimum['perturbation_lower_bound_h']):
            minimum={'beat':beat,**assessment}
    return {'status':'pass' if minimum is not None and not failures else 'fail','samples':len(times),
            'stature_m':evaluator.height,'minimum':minimum,'extrema':_balance_extrema(observations),
            'observations':observations,'failures':failures,
            'scope':'Dense canonical-frame squat static plausibility; native delivered conformance checked separately.'}


def audit_dense(sources,progress=None):
    evaluator=DiagnosticEvaluator(sources);reports=[]
    for fixture in sorted(sources['diagnostics'],key=lambda f:f['id']):
        id=fixture['id'];times=dense_beats(fixture)
        previous=None;failures=[];history={};max_position=max_orientation=max_input=max_beat=0.
        thorax_maxima={'endpoint_h':0.,'midpoint_h':0.,'sc_h':0.}
        balance_minimum=None;balance_observations=[]
        for sample_index,beat in enumerate(times):
            solved=evaluator.evaluate(id,beat)
            thorax=data_guide_residuals(sources['profile'],solved['frames'],solved['guides'])
            for name,value in thorax.items():
                thorax_maxima[name]=max(thorax_maxima[name],value)
                if value>1e-4:failures.append({'id':'thorax.'+name,'beat':beat,'measured':value,'expected':[0,1e-4],'status':'fail','requirement':MOTION_REQUIREMENT})
            result=measure_pose(sources['profile'],sources['mobility'],solved['frames'],beat,solved['actions'],solved['world_root'])
            checks=result['checks']+contact_checks(sources['profile'],solved['contacts'],attachments(sources['profile'],solved['frames']),beat,history)
            if id=='squat':
                observed={'frames':solved['frames'],'mass_points':mass_observations(sources['profile'],solved['frames']),
                          'attachments':attachments(sources['profile'],solved['frames'])}
                balance=measure_balance(sources['profile'],observed,solved['contacts'],beat,True)
                checks.extend(balance['checks'])
                balance_observations.append(_balance_observation(beat,sample_index,balance,observed,solved['contacts'],fixture['duration_beats']))
                if balance['assessment'] is not None:
                    candidate=balance['assessment']['perturbation_lower_bound_h']
                    if balance_minimum is None or candidate<balance_minimum['perturbation_lower_bound_h']:
                        balance_minimum={'beat':beat,**balance['assessment']}
            failures.extend(c for c in checks if c['status']!='pass')
            if previous is not None:
                max_beat=max(max_beat,beat-previous['beat'])
                for body,frame in solved['frames'].items():
                    other=previous['frames'][body]
                    max_position=max(max_position,m.norm(m.sub(frame['position_m'],other['position_m']))/evaluator.height)
                    max_orientation=max(max_orientation,m.angle_error(frame['rotation'],other['rotation']))
                # Driving amplitudes are scalar inputs. Walking plane is an
                # authored direction selector whose value is undefined at e=0;
                # all body matrices (including that transition) remain audited.
                for action in evaluator.model.evaluator.actions.values():
                    channel=action['id']
                    if action.get('mode')!='independent' or 'bounds_deg' not in action:continue
                    if fixture['construction']['type']=='walking_flat' and channel.endswith('.plane'):continue
                    max_input=max(max_input,abs(solved['actions'][channel]-previous['actions'][channel]))
            previous=solved
        bounds={'max_step_beats':(.01,max_beat),'max_origin_step_h':(.02,max_position),'max_orientation_step_deg':(5,max_orientation),'max_driving_input_step_deg':(.25,max_input)}
        for metric,(bound,value) in bounds.items():
            if value>bound+1e-9:failures.append({'id':id+'.'+metric,'measured':value,'expected':[0,bound],'status':'fail','beat':None})
        row={'fixture':id,'samples':len(times),'maxima':{name:{'measured':value,'upper_bound':bound,'status':'pass' if value<=bound+1e-9 else 'fail'} for name,(bound,value) in bounds.items()},'failures':failures,'status':'pass' if not failures else 'fail'}
        row['thoracic_closure']={name:{'measured':value,'upper_bound':1e-4,'status':'pass' if value<=1e-4 else 'fail'} for name,value in thorax_maxima.items()}
        if id=='squat':
            row['static_balance_minimum']=balance_minimum
            row['static_balance']={'samples':len(balance_observations),
                                   'observations':balance_observations,
                                   'extrema':_balance_extrema(balance_observations)}
        reports.append(row)
        if progress:progress(row)
    return {'status':'pass' if reports and all(r['status']=='pass' for r in reports) else 'fail','fixtures':reports,
            'scope':'Dense data-side body/action/coupling/contact audit; evaluated Blender mesh floor checks remain separate.',
            'direction_parameters':'Walking shoulder azimuth selects a fixed forward/backward plane; at zero elevation it is canonically zero. This singular selector is excluded from scalar driving-step maxima; its resulting matrices are included in orientation continuity.'}
