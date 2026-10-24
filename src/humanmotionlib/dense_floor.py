# SPDX-License-Identifier: Apache-2.0
"""Continuous-domain floor proof from actual Blender-local mesh vertices."""

from humanmotionlib import math3d as m
from humanmotionlib.dense_verification import dense_beats
from humanmotionlib.diagnostics import DiagnosticEvaluator
from humanmotionlib.geometry import primitive_mesh


def guide_bounds(points, radius):
    """Conservative cubic Bezier hull, including Catmull–Rom overshoot."""
    hull=[]
    for i,(a,b) in enumerate(zip(points,points[1:])):
        before,after=points[max(0,i-1)],points[min(len(points)-1,i+2)]
        hull.extend([a,b,m.add(a,m.scale(m.sub(b,before),1/6)),m.sub(b,m.scale(m.sub(after,a),1/6))])
    return ([min(p[i] for p in hull)-radius for i in range(3)],
            [max(p[i] for p in hull)+radius for i in range(3)])


def floor_bound(vertices,frame,allowed):
    low=[min(v[i] for v in vertices) for i in range(3)]
    high=[max(v[i] for v in vertices) for i in range(3)]
    row=frame['rotation'][2];z=frame['position_m'][2]
    lower=z+sum(row[i]*(low[i] if row[i]>=0 else high[i]) for i in range(3))
    if lower>=allowed:return lower,'conservative-evaluated-local-aabb'
    minimum=z+min(sum(row[i]*v[i] for i in range(3)) for v in vertices)
    return minimum,'complete-evaluated-vertex-minimum'


def audit_dense_floor(prepared,reference,progress=None):
    if reference.get('format')!='skeleton-evaluated-geometry/v1' or reference.get('prepared_sha256')!=prepared['content_sha256']:
        raise ValueError('Missing/stale evaluated geometry reference')
    sources=prepared['sources'];evaluator=DiagnosticEvaluator(sources);height=evaluator.height
    records={g['id']:(b,g) for b in sources['profile']['structures'] for g in b['geometry'] if g['type']!='recess'}
    geometry=reference['geometry']
    if set(geometry)!=set(records):raise ValueError('Incomplete evaluated geometry inventory')
    bounds={}
    for name,item in geometry.items():
        vertices=item['vertices_m']
        if not vertices:raise ValueError('Empty evaluated mesh '+name)
        bounds[name]=([min(v[i] for v in vertices) for i in range(3)],[max(v[i] for v in vertices) for i in range(3)])
    rows=[];allowed=-1e-4*height
    for fixture in sorted(sources['diagnostics'],key=lambda f:f['id']):
        times=dense_beats(fixture);worst={};failures=[];exact=bounded=0
        for beat in times:
            solved=evaluator.evaluate(fixture['id'],beat)
            for name,item in geometry.items():
                body,primitive=records[name];frame=solved['frames'][item['structure']]
                low,high=bounds[name];vertices=item['vertices_m']
                if not item['rigid'] and name in solved['guides']:
                    points=solved['guides'][name]
                    # The Bezier control hull encloses each cubic span; expand
                    # by tube radius and float32 padding. If this proof fails,
                    # construct and check every vertex below as before.
                    low,high=guide_bounds(points,primitive['radius_m']+1e-6*height)
                    vertices=None
                direction=frame['rotation'][2];z=frame['position_m'][2]
                value=z+sum(direction[i]*(low[i] if direction[i]>=0 else high[i]) for i in range(3))
                method='conservative-evaluated-local-aabb'
                if value<allowed:
                    if vertices is None:vertices,_=primitive_mesh(primitive,solved['guides'][name])
                    value=z+min(direction[0]*v[0]+direction[1]*v[1]+direction[2]*v[2] for v in vertices)
                    method='complete-evaluated-vertex-minimum';exact+=1
                else:bounded+=1
                record={'id':name+'.dense_floor','beat':beat,'measured_lower_bound_m':value,'allowed_lower_bound_m':allowed,
                        'method':method,'status':'pass' if value>=allowed else 'fail','requirement':'joint-mobility / Contact and floor measurements'}
                if name not in worst or value<worst[name]['measured_lower_bound_m']:worst[name]=record
                if value<allowed:failures.append(record)
        row={'fixture':fixture['id'],'samples':len(times),'meshes':len(geometry),'checks':list(worst.values()),'failures':failures,
             'conservative_bound_checks':bounded,'full_vertex_checks':exact,'status':'pass' if len(worst)==len(geometry) and not failures else 'fail'}
        rows.append(row)
        if progress:progress(row)
    return {'status':'pass' if rows and all(r['status']=='pass' for r in rows) else 'fail','fixtures':rows,
            'geometry_source':'Blender evaluated body-local vertices, measured and exported by the headless build.',
            'transform_source':'Same canonical beat-keyed evaluator as delivery; delivered native frames are separately measured against it.',
            'method':'A transformed local AABB proves all vertices are above the floor when its lower bound passes. Otherwise every evaluated local vertex is transformed and checked. Non-rigid guides are rebuilt at each sample from their explicit bindings; no solver success flag is used.'}
