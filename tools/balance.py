# SPDX-License-Identifier: Apache-2.0
"""Whole-body point-mass static plausibility; never a dynamics/force solver.

The independent dossier below is deliberately separate from canonical YAML and
the pose constructor. Soft-tissue region masses are not skeletal mesh masses.
"""

import math
from tools import math3d as m
from tools.measurements import Measurements
from tools.mirror import swap_side

REQUIREMENT = 'joint-mobility / Squat diagnostic exercises balance and planted feet / Measure squat static balance independently'
MASS_REQUIREMENT = 'anatomical-skeleton / Whole-body mass metadata is explicit and separate from skeletal appearance'
# Male/female Proposed Table 3 weights; offsets are approved R3 adaptations.
DOSSIER = {
    'head': ('skull', 5.6, 5.3, [0,.010,.060]),
    'upper_trunk': ('T6', 11.5,12., [0,.020,0]),
    'abdomen': ('L1',11.,7., [0,.015,0]),
    'pelvis': ('pelvis',9.2,8.9, [0,.010,.030]),
}
for side in ('L','R'):
    for name,body,male,female,offset in (
        ('thigh','femur',10.4,12.,[0,0,-.103779]),
        ('shank','knee',3.5,3.9,[0,0,-.08781625]),
        ('foot','hindfoot',1.1,1.1,[0,.040,-.025]),
        ('upper_arm','humerus',2.1,1.9,[0,0,-.066447]),
        ('forearm','elbow',1.1,.9,[0,0,-.05726175]),
        ('hand','wrist',.5,.4,[0,0,-.041382])):
        DOSSIER[name+'.'+side]=(body+'.'+side,male,female,offset)


def mirror_mass_segment(segment):
    from copy import deepcopy
    result=deepcopy(segment)
    result['id']=swap_side(segment['id']);result['body']=swap_side(segment['body'])
    result['position_m']=m.mirror_position(segment['position_m'])
    return result


def validate_mass_model(profile):
    model=profile.get('mass_model',{})
    if model.get('id')!='adult-reference-point-masses-v1' or model.get('assessment')!='static':
        raise ValueError('Unsupported whole-body mass model')
    records=model.get('segments',[]);bodies={b['id']:b for b in profile['structures']}
    index={r['id']:r for r in records};height=profile['stature_m']
    if len(records)!=16 or len(index)!=16 or set(index)!=set(DOSSIER):
        raise ValueError('mass_model: exactly the 16 R3 mass regions required')
    for id,(body,male,female,offset) in DOSSIER.items():
        r=index[id]
        if r['body']!=body or body not in bodies or not bodies[body]['rigid'] or bodies[body]['representation']=='omitted':
            raise ValueError(id+': unresolved/nonrigid mass carrier')
        for field,expected in [('male_weight_kg',male),('female_weight_kg',female),('weight_kg',(male+female)/2)]:
            value=r[field]
            if isinstance(value,bool) or not math.isfinite(value) or value<=0 or abs(value-expected)>1e-12:
                raise ValueError(id+': mass coefficient does not match approved '+field)
        local=r['position_m']
        if len(local)!=3 or any(not math.isfinite(x) for x in local):raise ValueError(id+': nonfinite mass point')
        neutral_offset=m.mv(bodies[body]['basis'],local)
        if m.norm(m.sub(neutral_offset,[v*height for v in offset]))>1e-6*height:
            raise ValueError(id+': mass placement differs from R3 dossier')
        if id.endswith('.R'):
            mirror=mirror_mass_segment(r);left=index[mirror['id']]
            if left['body']!=mirror['body'] or m.norm(m.sub(left['position_m'],mirror['position_m']))>1e-6*height:
                raise ValueError(id+': asymmetric mass points')
    for field in ('weight_kg','male_weight_kg','female_weight_kg'):
        total=sum(r[field] for r in records)
        if total<=0 or abs(sum(r[field]/total for r in records)-1)>1e-12:raise ValueError('mass normalization failed')
    return index


def mass_observations(profile,frames):
    """Data-side observations only; native exporter uses actual bone matrices."""
    return {r['id']:{'structure':r['body'], 'position_m':m.add(frames[r['body']]['position_m'],m.mv(frames[r['body']]['rotation'],r['position_m']))}
            for r in profile['mass_model']['segments']}


def convex_hull(points):
    points=sorted(set(tuple(p) for p in points))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower=[];upper=[]
    for p in points:
        while len(lower)>=2 and cross(lower[-2],lower[-1],p)<=0:lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper)>=2 and cross(upper[-2],upper[-1],p)<=0:upper.pop()
        upper.append(p)
    return lower[:-1]+upper[:-1]


def static_balance(profile,observations,observed_attachments,contacts):
    records=validate_mass_model(profile)
    if set(observations)!=set(records):raise ValueError('Missing/extra mass observations')
    for id,r in records.items():
        if observations[id].get('structure')!=r['body']:raise ValueError('Wrong mass carrier '+id)
        p=observations[id].get('position_m',[])
        if len(p)!=3 or any(not math.isfinite(x) for x in p):raise ValueError('Nonfinite mass observation '+id)
    if len(contacts)!=2 or {c['foot'] for c in contacts}!={'L','R'} or any(c['state']!='flat' for c in contacts):
        raise ValueError('Squat requires both measured flat-foot supports')
    required={f'contact.{name}.{side}' for side in ('L','R') for name in ('heel','medial_ball','lateral_ball')}
    ids={id for c in contacts for id in c['anchors']}
    if not required<=ids or not ids<=set(observed_attachments):raise ValueError('Missing support attachments')
    support=[observed_attachments[id]['position_m'] for id in sorted(ids)]
    height=profile['stature_m']
    if any(len(p)!=3 or any(not math.isfinite(x) for x in p) or abs(p[2])>1e-3*height for p in support):
        raise ValueError('Support is nonfinite or not on floor')
    polygon=convex_hull([p[:2] for p in support])
    area=sum(p[0]*polygon[(i+1)%len(polygon)][1]-p[1]*polygon[(i+1)%len(polygon)][0] for i,p in enumerate(polygon)) if polygon else 0
    if len(polygon)<3 or area<=1e-12*height*height:raise ValueError('Degenerate support hull')
    variants={}
    for variant,field in [('reference','weight_kg'),('male_weights','male_weight_kg'),('female_weights','female_weight_kg')]:
        total=sum(r[field] for r in records.values())
        fractions={id:r[field]/total for id,r in records.items()}
        com=[sum(fractions[id]*observations[id]['position_m'][axis] for id in records) for axis in range(3)]
        margins=[]
        for i,a in enumerate(polygon):
            b=polygon[(i+1)%len(polygon)];dx,dy=b[0]-a[0],b[1]-a[1]
            margins.append((dx*(com[1]-a[1])-dy*(com[0]-a[0]))/math.hypot(dx,dy))
        variants[variant]={'com_m':com,'fractions':fractions,'edge_margins_m':margins,
                           'margin_h':min(margins)/height,'worst_edge':margins.index(min(margins))}
    lower=min(v['margin_h'] for v in variants.values())-.005
    return {'assessment':'static plausibility only; estimated whole-body COM including unrendered tissues',
            'mass_points':observations,'support_xy_m':polygon,'variants':variants,
            'placement_allowance_h':.005,'perturbation_lower_bound_h':lower}


def measure_balance(profile,sample,contacts,beat=0,assess_support=False):
    checks=Measurements(beat)
    try:records=validate_mass_model(profile)
    except (ValueError,KeyError,TypeError) as error:
        checks.scalar('balance.mass_dossier',1,0,0,'boolean');checks.checks[-1]['reason']=str(error)
        return {'status':'fail','checks':checks.checks,'assessment':None}
    actual=sample.get('mass_points',{});height=profile['stature_m']
    checks.scalar('balance.mass_inventory',len(set(actual)^set(records)),0,0,'count')
    for id,r in records.items():
        if id not in actual:continue
        body=r['body'];frame=sample['frames'][body]
        expected=m.add(frame['position_m'],m.mv(frame['rotation'],r['position_m']))
        checks.scalar('balance.'+id+'.carrier',int(actual[id].get('structure')!=body),0,0,'boolean')
        point=actual[id].get('position_m',[])
        if len(point)!=3 or any(not math.isfinite(v) for v in point):checks.scalar('balance.'+id+'.finite',1,0,0,'boolean')
        else:checks.position('balance.'+id+'.binding',point,expected,1e-4*height)
    assessment=None
    if assess_support:
        try:
            assessment=static_balance(profile,actual,sample.get('attachments',{}),contacts)
            checks.limit('balance.reference_margin',assessment['variants']['reference']['margin_h'],[.010,1e100],0,'H')
            checks.limit('balance.perturbation_lower_bound',assessment['perturbation_lower_bound_h'],[.005,1e100],0,'H')
        except (ValueError,KeyError,TypeError) as error:
            checks.scalar('balance.support_evidence',1,0,0,'boolean');checks.checks[-1]['reason']=str(error)
    for c in checks.checks:c['requirement']=REQUIREMENT if assess_support else MASS_REQUIREMENT
    return {'status':'pass' if all(c['status']=='pass' for c in checks.checks) else 'fail','checks':checks.checks,'assessment':assessment}
