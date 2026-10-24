# SPDX-License-Identifier: Apache-2.0
"""Rigid attachment measurements and deterministic bounded contact solving."""

from copy import deepcopy
import math
from humanmotionlib import math3d as m
from humanmotionlib.actions import ActionError, constraint_failure, require_valid
from humanmotionlib.measurements import Measurements


def attachments(profile,frames):
    return {a['id']:{'structure':b['id'],'position_m':m.add(frames[b['id']]['position_m'],m.mv(frames[b['id']]['rotation'],a['position_m']))} for b in profile['structures'] for a in b['attachments']}


def contact_checks(profile,declared,observed,beat=0,history=None):
    checks=Measurements(beat);height=profile['stature_m']
    source={a['id']:b['id'] for b in profile['structures'] for a in b['attachments']}
    for contact in declared:
        if contact['state']=='flat':
            required={f'contact.{name}.{contact["foot"]}' for name in ('heel','medial_ball','lateral_ball')}
            checks.scalar('contact.'+contact['foot']+'.flat_witnesses',len(required-set(contact['anchors'])),0,0,'count')
        if contact['state']=='ball':
            required={f'contact.{name}.{contact["foot"]}' for name in ('medial_ball','lateral_ball')}
            checks.scalar('contact.'+contact['foot']+'.ball_witnesses',len(required-set(contact['anchors'])),0,0,'count')
        for id,target in zip(contact['anchors'],contact['targets_m']):
            if id not in observed:
                checks.scalar(id+'.contact_evidence',1,0,0,'boolean');continue
            checks.scalar(id+'.permanent_attachment',int(observed[id]['structure']!=source[id]),0,0,'boolean')
            checks.position(id+'.target',observed[id]['position_m'],target,1e-3*height)
            if history is not None:
                key=(id,contact['start_beat'],contact['end_beat'])
                first=history.setdefault(key,observed[id]['position_m'])
                checks.position(id+'.sliding',observed[id]['position_m'],first,1e-3*height)
    return checks.checks


def linear_solve(matrix,vector):
    n=len(vector);rows=[list(a)+[b] for a,b in zip(matrix,vector)]
    for col in range(n):
        pivot=max(range(col,n),key=lambda row:abs(rows[row][col]))
        rows[col],rows[pivot]=rows[pivot],rows[col]
        if abs(rows[col][col])<1e-18:raise ValueError('Singular damped contact system')
        divisor=rows[col][col];rows[col]=[v/divisor for v in rows[col]]
        for row in range(n):
            if row==col:continue
            factor=rows[row][col]
            rows[row]=[a-factor*b for a,b in zip(rows[row],rows[col])]
    return [row[-1] for row in rows]


def solve_contacts(model,requested,pins,free_channels,owners,controls,previous=None,beat=0):
    """Fixed seed/order, damping 1e-4, 100 iterations, 1e-5 H target.

    Bounds project candidate solver variables, never the requested target or
    caller's fixed action values. Invalid coupled-envelope trials are rejected.
    """
    channels=sorted(free_channels)
    if not channels or len(channels)!=len(set(channels)):raise ValueError('Explicit unique contact-solver variables required')
    if any(c not in model.evaluator.defaults or owners[c] not in controls for c in channels):raise ValueError('Contact solver variable is unsupported or outside controls')
    # Validate caller intent before a previous/canonical seed can replace a
    # free variable. An invalid command must remain an invalid command.
    require_valid(model.evaluator.evaluate(requested,beat=beat))
    values=deepcopy(model.evaluator.defaults);values.update(requested)
    for channel in channels:
        values[channel]=previous.get(channel,model.evaluator.defaults[channel]) if previous is not None else model.evaluator.defaults[channel]
    original=deepcopy(pins);height=model.height
    limits={c:model.evaluator.actions[c]['bounds_deg' if 'bounds_deg' in model.evaluator.actions[c] else 'bounds_m'] for c in channels}
    for c in channels:
        if c.startswith('knee.'):limits[c]=[max(0,limits[c][0]),limits[c][1]]
    def residual(action):
        solved=model.solve(action,beat)
        measured=attachments(model.profile,solved['frames'])
        vector=[(measured[p['anchor']]['position_m'][axis]-p['target_m'][axis])/height for p in pins for axis in range(3)]
        return vector,solved,measured
    # Validate fixed intent and seed without silently changing it.
    r,solved,measured=residual(values)
    damping=1e-4;iterations=0
    for iterations in range(101):
        maximum=max(m.norm(r[i:i+3]) for i in range(0,len(r),3))
        if maximum<=1e-5:
            return {'state':'valid','actions':values,'solution':solved,'iterations':iterations,'normalized_residual':maximum,
                    'requested_targets':original,'limits':limits,'damping':damping}
        if iterations==100:break
        jacobian=[]
        for c in channels:
            step=1e-3 if 'bounds_deg' in model.evaluator.actions[c] else 1e-5*height
            direction=1 if values[c]+step<=limits[c][1] else -1
            candidate=values|{c:values[c]+direction*step}
            try:r2,_,_=residual(candidate)
            except ActionError:
                direction=-direction;candidate=values|{c:values[c]+direction*step}
                try:r2,_,_=residual(candidate)
                except ActionError:jacobian.append([0.]*len(r));continue
            jacobian.append([(b-a)/(direction*step) for a,b in zip(r,r2)])
        normal=[[m.dot(a,b)+(damping*damping if i==j else 0) for j,b in enumerate(jacobian)] for i,a in enumerate(jacobian)]
        delta=linear_solve(normal,[-m.dot(column,r) for column in jacobian])
        accepted=False
        for divisor in (1,2,4,8,16,32,64,128,256):
            candidate=deepcopy(values)
            for c,change in zip(channels,delta):candidate[c]=max(limits[c][0],min(limits[c][1],values[c]+change/divisor))
            try:r2,s2,a2=residual(candidate)
            except ActionError:continue
            if m.dot(r2,r2)<m.dot(r,r)-1e-18:
                values,r,solved,measured=candidate,r2,s2,a2;accepted=True;break
        if not accepted:break
    residuals={pin['anchor']:m.norm(m.sub(measured[pin['anchor']]['position_m'],pin['target_m'])) for pin in pins}
    failure=constraint_failure('contacts','pins',max(residuals.values()),1e-5*height,beat,original,
                               {'actions':values,'limits':limits,'anchor_residuals_m':residuals})
    return failure|{'iterations':iterations,'damping':damping,'requested_targets':original,'limits':limits}
