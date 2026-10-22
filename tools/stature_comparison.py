# SPDX-License-Identifier: Apache-2.0
"""Cross-stature checks from evaluated local geometry and native T-pose frames."""

import json
from pathlib import Path
import re

from tools import math3d as m
from tools.measurements import Measurements
from tools.prepared import read_prepared


def evaluated_samples(path):
    """Stream the top-level sample array, without loading a large build report."""
    decoder=json.JSONDecoder()
    with Path(path).open() as stream:
        buffer=''
        while True:
            chunk=stream.read(65536)
            if not chunk:raise ValueError('Evaluated sample array missing')
            buffer+=chunk
            match=re.search(r'"samples"\s*:\s*\[',buffer)
            if match:buffer=buffer[match.end():];break
        while True:
            buffer=buffer.lstrip(' \r\n\t,')
            if buffer.startswith(']'):return
            try:
                value,end=decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                chunk=stream.read(1048576)
                if not chunk:raise ValueError('Truncated evaluated sample array')
                buffer+=chunk;continue
            yield value
            buffer=buffer[end:]


def compare_statures(directories):
    builds=[]
    for directory in directories:
        directory=Path(directory);prepared=read_prepared(directory/'input.json')
        height=prepared['sources']['profile']['stature_m']
        geometry=json.loads((directory/'geometry-reference.json').read_text())
        if geometry['prepared_sha256']!=prepared['content_sha256']:raise ValueError('Stale stature geometry reference')
        rest=next((s for s in evaluated_samples(directory/'evaluated.json') if s['id']=='rest/00000'),None)
        if rest is None:raise ValueError('Missing native rest pose in stature build')
        builds.append({'height':height,'geometry':geometry['geometry'],'rest':rest,
                       'mass_model':prepared['sources']['profile']['mass_model']})
        del prepared
    checks=Measurements(0)
    checks.scalar('stature_set',int({b['height'] for b in builds}!={1.5,1.7,1.9}),0,0,'boolean')
    base=next((b for b in builds if b['height']==1.7),None)
    if base is None:raise ValueError('Reference stature 1.70 m is missing')
    for build in builds:
        height=build['height'];prefix=f'H{height}.'
        checks.scalar(prefix+'geometry_inventory',len(set(base['geometry'])^set(build['geometry'])),0,0,'count')
        reference_mass=base['rest'].get('mass_points',{});measured_mass=build['rest'].get('mass_points',{})
        required={r['id'] for r in build['mass_model']['segments']}
        checks.scalar(prefix+'mass_inventory',len(required^set(measured_mass)),0,0,'count')
        checks.scalar(prefix+'reference_mass_inventory',len(required^set(reference_mass)),0,0,'count')
        for id in sorted(required & set(reference_mass) & set(measured_mass)):
            residual=m.norm(m.sub(m.scale(measured_mass[id]['position_m'],1/height),m.scale(reference_mass[id]['position_m'],1/base['height'])))
            checks.scalar(prefix+'mass.'+id+'.normalized_point',residual,0,1e-6,'H')
        for field in ('weight_kg','male_weight_kg','female_weight_kg'):
            a={r['id']:r[field] for r in build['mass_model']['segments']};b={r['id']:r[field] for r in base['mass_model']['segments']}
            for id in a:
                checks.scalar(prefix+'mass.'+id+'.'+field+'.fraction',a[id]/sum(a.values()),b[id]/sum(b.values()),1e-12,'ratio')
        for name,reference in base['geometry'].items():
            if name not in build['geometry']:continue
            measured=build['geometry'][name]
            checks.scalar(prefix+name+'.vertex_count',len(measured['vertices_m']),len(reference['vertices_m']),0,'count')
            if len(measured['vertices_m'])==len(reference['vertices_m']):
                residual=max(m.norm(m.sub(m.scale(a,1/height),m.scale(b,1/base['height']))) for a,b in zip(measured['vertices_m'],reference['vertices_m']))
                checks.scalar(prefix+name+'.normalized_vertices',residual,0,1e-6,'H')
            topology=build['rest']['geometry'].get(name,{}).get('topology_sha256')
            reference_topology=base['rest']['geometry'][name]['topology_sha256']
            checks.scalar(prefix+name+'.topology',int(topology!=reference_topology),0,0,'boolean')
        for id,reference in base['rest']['frames'].items():
            measured=build['rest']['frames'].get(id)
            if measured is None:checks.scalar(prefix+id+'.frame_inventory',1,0,0,'boolean');continue
            residual=m.norm(m.sub(m.scale(measured['position_m'],1/height),m.scale(reference['position_m'],1/base['height'])))
            checks.scalar(prefix+id+'.normalized_rest_origin',residual,0,1e-6,'H')
            matrix_residual=max(abs(measured['rotation'][i][j]-reference['rotation'][i][j]) for i in range(3) for j in range(3))
            checks.scalar(prefix+id+'.rest_orientation',matrix_residual,0,1e-6,'matrix element')
    return {'status':'pass' if checks.checks and all(c['status']=='pass' for c in checks.checks) else 'fail',
            'checks':checks.checks,'statures_m':[b['height'] for b in builds],
            'scope':'Actual evaluated body-local geometry and native T-pose frames; delivered samples at each stature are verified in their own reports.'}
