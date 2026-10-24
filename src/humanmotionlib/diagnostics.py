# SPDX-License-Identifier: Apache-2.0
"""Scoped skeleton-diagnostic/v1 intent evaluation, with closed analytic constructors."""

from copy import deepcopy
import math

from humanmotionlib import math3d as m
from humanmotionlib.articulation import knee
from humanmotionlib.kinematics import KinematicModel


def interpolate(keys,beat,easing):
    if beat<=keys[0]['beat']:return keys[0]['value']
    if beat>=keys[-1]['beat']:return keys[-1]['value']
    for a,b in zip(keys,keys[1:]):
        if beat<=b['beat']:
            t=(beat-a['beat'])/(b['beat']-a['beat'])
            if easing=='ease_in_out':t=3*t*t-2*t*t*t
            elif easing=='half_wave':t=(1-math.cos(math.pi*t))/2
            elif easing!='linear':raise ValueError('Unsupported easing')
            return a['value']+(b['value']-a['value'])*t
    raise ValueError('Missing key interval')


def decompose_hip(rotation):
    return [math.degrees(math.atan2(-rotation[1][2],rotation[2][2])),math.degrees(math.asin(rotation[0][2])),-math.degrees(math.atan2(-rotation[0][1],rotation[0][0]))]


class DiagnosticEvaluator:
    def __init__(self,sources):
        self.sources=sources;self.model=KinematicModel(sources['profile'],sources['mobility'])
        self.fixtures={f['id']:f for f in sources['diagnostics']}
        self.height=self.model.height
        self.owners={c:g['id'] for g in sources['body-groups']['groups'] for c in g['channels']}

    def flat_leg(self,k,a,p=0):
        params=self.model.couplings['knee.R.tracking']
        K,shift=knee(params,k,self.height)
        h=self.model.couplings['hindfoot.R.oblique']['axis']
        thigh=m.sub(self.model.bodies['knee.R']['origin_m'],self.model.bodies['femur.R']['origin_m'])
        shank=m.sub(self.model.bodies['talus.R']['origin_m'],self.model.bodies['knee.R']['origin_m'])
        vector=m.add(thigh,m.add(shift,m.mv(K,shank)))
        P=m.rx(-p)
        def state(i):
            U=m.mm(m.transpose(P),m.transpose(m.mm(K,m.mm(m.rx(a),m.rot(h,i)))))
            v=m.mv(m.mm(P,U),vector)
            return U,v
        low,high=self.model.evaluator.actions['hindfoot.R.inversion']['bounds_deg']
        fl=state(low)[1][0];fh=state(high)[1][0]
        if fl*fh>0:raise ValueError('Flat leg has no sign-changing inversion bracket')
        # Verify a single crossing over the declared bracket before deterministic bisection.
        samples=[state(low+(high-low)*j/60)[1][0] for j in range(61)]
        differences=[b-a for a,b in zip(samples,samples[1:])]
        if not (all(d>=-1e-12 for d in differences) or all(d<=1e-12 for d in differences)):
            raise ValueError('Flat-leg inversion root is not unique on the bracket')
        for _ in range(60):
            middle=(low+high)/2;fm=state(middle)[1][0]
            if fl*fm<=0:high=middle
            else:low=middle;fl=fm
        i=(low+high)/2;U,v=state(i)
        return i,decompose_hip(U),v

    def evaluate(self,id,beat,previous=None,layers=None,_stack=()):
        if id in _stack:raise ValueError('Recursive fixture base')
        fixture=self.fixtures[id];duration=fixture['duration_beats']
        if beat<0 or beat>duration:raise ValueError('Beat outside fixture duration')
        policy=fixture['rest_policy']['policy']
        if policy=='hold':
            if previous is None:raise ValueError('hold requires previous action intent')
            actions=deepcopy(previous)
        else:
            base=fixture['rest_policy']['base_fixture']
            if id==base=='neutral':actions=deepcopy(self.model.evaluator.defaults)
            else:
                actions=self.evaluate(base,min(beat,self.fixtures[base]['duration_beats']),_stack=(*_stack,id))['actions']
        if layers:
            writes=set(fixture['controls'])
            for layer in layers:
                if writes.intersection(layer['controls']):raise ValueError('Conflicting parallel group writers')
                writes.update(layer['controls'])
                for channel,value in layer['actions'].items():
                    if self.owners[channel] not in layer['controls']:raise ValueError('Layer writes unowned channel')
                    actions[channel]=value
        if policy=='free':
            unowned=set(self.owners.values())-set(fixture['controls'])
            supplied=set(g for layer in (layers or []) for g in layer['controls'])
            if not unowned<=supplied:raise ValueError('Unassigned free groups')
        for track in fixture['tracks']:
            if self.owners[track['channel']] not in fixture['controls']:raise ValueError('Fixture writes unowned action')
            actions[track['channel']]=interpolate(track['keys'],beat,track['easing'])
        construction=fixture['construction'];kind=construction['type']
        if kind=='rest':
            for side in ('L','R'):
                actions[f'shoulder.{side}.elevation']=actions[f'shoulder.{side}.plane']=90
        elif kind=='squat_closed':
            i,hip,v=self.flat_leg(actions['knee.R.flexion'],actions['ankle.R.dorsiflexion'],actions['pelvis.pitch'])
            actions['pelvis.y']=-v[1];actions['pelvis.z']=self.model.bodies['talus.R']['origin_m'][2]-v[2]
            for side in ('L','R'):
                for name,value in zip(('flexion','adduction','external_rotation'),hip):actions[f'hip.{side}.{name}']=value
                actions[f'hindfoot.{side}.inversion']=i
        elif kind=='walking_flat':
            p=construction['parameters']
            for side in ('L','R'):
                actions[f'elbow.{side}.flexion']=p['elbow_deg'];actions[f'forearm.{side}.pronation']=p['forearm_deg']
            for phase in construction['phases']:
                start,end=phase['start_beat'],phase['end_beat']
                if start<=beat<=end:
                    w=math.sin(math.pi*(beat-start)/(end-start))**2
                    side=phase['side'];other='R' if side=='L' else 'L'
                    k,a=p['knee_peak_deg']*w,p['ankle_peak_deg']*w
                    i,hip,_=self.flat_leg(k,a)
                    actions[f'knee.{side}.flexion']=k;actions[f'ankle.{side}.dorsiflexion']=a;actions[f'hindfoot.{side}.inversion']=i
                    for name,value in zip(('flexion','adduction','external_rotation'),hip):actions[f'hip.{side}.{name}']=value
                    for arm,e,plane in ((side,p['arm_backward_deg']*w,p['backward_plane_deg']),(other,p['arm_forward_deg']*w,p['forward_plane_deg'])):
                        actions[f'shoulder.{arm}.elevation']=e
                        actions[f'shoulder.{arm}.plane']=plane if w>1e-20 else 0
        elif kind=='forefoot_rocker':
            r=interpolate(construction['reference_knots'],beat,'ease_in_out');angle=math.radians(r)
            actions['pelvis.y']=self.height*(.075*(1-math.cos(angle))+.030*math.sin(angle))
            actions['pelvis.z']=self.model.evaluator.defaults['pelvis.z']+self.height*(.075*math.sin(angle)+.030*(math.cos(angle)-1))
            for side in ('L','R'):
                actions[f'ankle.{side}.dorsiflexion']=-r;actions[f'mtp.{side}.extension']=r
        elif kind not in ('neutral','action_sweep'):raise ValueError('Unknown closed diagnostic constructor')
        root=fixture['world_root']
        solved=self.model.solve(actions,beat,root)
        return solved|{'fixture':id,'beat':beat,'world_root':root,'contacts':self.contacts_at(fixture,beat)}

    def contacts_at(self,fixture,beat):
        terminal=beat==fixture['duration_beats']
        result=[]
        if terminal:
            for state in fixture['terminal_contacts']:
                if state['state']=='none':continue
                candidates=[c for c in fixture['contacts'] if c['foot']==state['foot'] and c['state']==state['state']]
                if not candidates:raise ValueError('Terminal contact has no anchor declaration')
                result.append(deepcopy(candidates[-1]))
        else:
            result=[deepcopy(c) for c in fixture['contacts'] if c['start_beat']<=beat<c['end_beat']]
        return result
