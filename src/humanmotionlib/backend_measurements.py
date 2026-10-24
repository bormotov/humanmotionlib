# SPDX-License-Identifier: Apache-2.0
"""Checks of evaluated Blender evidence; does not construct geometry or solve FK."""

from humanmotionlib import math3d as m
from humanmotionlib.measurements import Measurements
from humanmotionlib.runtime import check_blender_version


def verify_backend(prepared,evaluated,transforms,contact_history=None):
    if evaluated.get('format')!='skeleton-evaluated/v1':raise ValueError('Unsupported evaluated format')
    if evaluated.get('prepared_sha256')!=prepared['content_sha256']:raise ValueError('Evaluated/prepared hash mismatch')
    metadata=evaluated['metadata']
    check_blender_version(metadata['blender_version'],metadata['blender_build'])
    profile=prepared['sources']['profile'];height=profile['stature_m']
    bodies={b['id']:b for b in profile['structures']}
    expected_geometry={g['id']:(b,g) for b in bodies.values() for g in b['geometry'] if g['type']!='recess'}
    expected_landmarks={l['id']:l for l in profile['landmarks']}
    expected_attachments={a['id']:(b,a) for b in bodies.values() if b['representation']!='omitted' for a in b['attachments']}
    reports={s['id']:s for s in transforms['samples']}
    prepared_samples={s['id']:s for s in prepared['samples']}
    if contact_history is None:contact_history={}
    reference_scene=None
    for sample in evaluated['samples']:
        report=reports[sample['id']];checks=Measurements(report['checks'][0]['beat'])
        geometry=sample.get('geometry',{})
        checks.scalar('geometry.inventory',len(set(geometry)^set(expected_geometry)),0,0,'count')
        frames=sample['frames']
        from humanmotionlib.thorax_measurements import measure_thorax
        checks.checks.extend(measure_thorax(profile,sample,report['fixture'] in ('neutral','rest'),checks.beat))
        from humanmotionlib.contacts import contact_checks
        declared=prepared_samples[sample['id']]
        checks.checks.extend(contact_checks(profile,declared['contacts'],sample.get('attachments',{}),checks.beat,contact_history))
        from humanmotionlib.balance import measure_balance
        balance=measure_balance(profile,sample,declared['contacts'],checks.beat,report['fixture']=='squat')
        checks.checks.extend(balance['checks'])
        if balance['assessment'] is not None: report['static_balance']=balance['assessment']
        root=sample.get('world_root')
        if root is None:checks.scalar('world_root.evidence',1,0,0,'boolean')
        else:
            checks.position('world_root.translation',root['position_m'],declared['world_root']['translation_m'],1e-4*height)
            checks.rotation('world_root.rotation',root['rotation'],m.qmatrix(declared['world_root']['orientation']))
        for name,(body,primitive) in sorted(expected_geometry.items()):
            if name not in geometry:continue
            item=geometry[name]
            checks.scalar(name+'.vertex_count',item['vertex_count'],1,0,'minimum count')
            checks.checks[-1]['residual']=max(0,1-item['vertex_count']);checks.checks[-1]['status']='pass' if item['vertex_count']>=1 else 'fail'
            checks.scalar(name+'.rigidity',item.get('rigid_vertex_residual_m',float('inf')),0,1e-6*height,'m')
            if item['structure']!=body['id']:checks.scalar(name+'.attachment_body',1,0,0,'boolean')
            matrix=item['world_matrix']
            if body['id'] in frames:
                frame=frames[body['id']]
                checks.position(name+'.attachment_origin',[matrix[i][3] for i in range(3)],frame['position_m'],1e-6*height)
                checks.rotation(name+'.attachment_rotation',[row[:3] for row in matrix[:3]],frame['rotation'])
            for axis,value in enumerate(item['scale']):checks.scalar(name+'.scale.'+str(axis),value,1,1e-6,'ratio')
            if primitive['type'] in ('ellipsoid','sphere','block'):
                center=primitive['center_m']
                radii=primitive.get('radii_m',[primitive.get('radius_m',0)]*3)
                if primitive['type']=='block':radii=[v/2 for v in primitive['dimensions_m']]
                for axis in range(3):
                    checks.scalar(name+f'.bound.min.{axis}',item['local_bounds_m'][0][axis],center[axis]-radii[axis],1e-4*height,'m')
                    checks.scalar(name+f'.bound.max.{axis}',item['local_bounds_m'][1][axis],center[axis]+radii[axis],1e-4*height,'m')
            checks.limit(name+'.floor',item['world_bounds_m'][0][2],[-1e-4*height,1e100],0,'m')
        for domain in ('object_scales','bone_scales'):
            values=sample.get(domain,{})
            active={id for id,b in bodies.items() if b['representation']!='omitted'}
            checks.scalar(domain+'.inventory',len(active^set(values)),0,0,'count')
            for id,scale in values.items():
                for axis,value in enumerate(scale):checks.scalar(domain+'.'+id+'.'+str(axis),value,1,1e-6,'ratio')
        for domain,expected in (('attachments',expected_attachments),('landmarks',expected_landmarks)):
            actual=sample.get(domain,{})
            checks.scalar(domain+'.inventory',len(set(expected)^set(actual)),0,0,'count')
            for id,source in expected.items():
                if id not in actual:continue
                if domain=='attachments':
                    body,attachment=source
                    frame=frames[body['id']]
                    target=m.add(frame['position_m'],m.mv(frame['rotation'],attachment['position_m']))
                    if actual[id].get('structure')!=body['id']:checks.scalar(id+'.attachment_identity',1,0,0,'boolean')
                else:
                    landmark=source;body_id=landmark.get('attachment_body')
                    if body_id is None:target=landmark['position_m']
                    elif bodies[body_id]['representation']=='omitted':
                        checks.scalar(id+'.declared_omission',int(actual[id].get('status')!='omitted'),0,0,'boolean');continue
                    else:
                        body=bodies[body_id];frame=frames[body_id]
                        local=m.mv(m.transpose(body['basis']),m.sub(landmark['position_m'],body['origin_m'])) if landmark['frame']=='world' else landmark['position_m']
                        target=m.add(frame['position_m'],m.mv(frame['rotation'],local))
                checks.position(id+'.evaluated_position',actual[id]['position_m'],target,1e-4*height)
        for side in ('L','R'):
            for proximal,distal,ratio in (('humerus','elbow',.1605),('elbow','radius',0),('femur','knee',.234),('knee','talus',.2155)):
                if not ratio:continue # forearm measured at its moving radiocarpal landmark below.
                # Knee rollback is a permitted joint-center translation; remove its measured femur-local offset.
                a,b=frames[proximal+'.'+side]['position_m'],frames[distal+'.'+side]['position_m']
                if proximal=='femur':
                    b=sample['landmarks']['knee.'+side]['position_m']
                    # The translated knee origin is not the fixed distal femoral endpoint.
                    body=bodies[proximal+'.'+side]
                    neutral_offset=m.sub(bodies['knee.'+side]['origin_m'],body['origin_m'])
                    rotation=m.mm(frames[proximal+'.'+side]['rotation'],m.transpose(body['basis']))
                    b=m.add(a,m.mv(rotation,neutral_offset))
                checks.scalar(f'{proximal}.{side}.mechanical_length',m.norm(m.sub(b,a))/height,ratio,1e-6,'H')
            a=frames['elbow.'+side]['position_m'];b=frames['wrist.'+side]['position_m']
            # The declared pronation axis shifts radiocarpal position; neutral W length is audited only in neutral/rest.
            if report['fixture'] in ('neutral','rest'):checks.scalar('forearm.'+side+'.neutral_mechanical_length',m.norm(m.sub(b,a))/height,.1365,1e-6,'H')
        scene=sample.get('scene')
        if scene is None:checks.scalar('scene.evidence',1,0,0,'boolean')
        elif reference_scene is None:reference_scene=scene
        else:checks.scalar('scene.stability',int(scene!=reference_scene),0,0,'boolean')
        if scene is not None:
            source=prepared['sources']['review-scene']
            for field,expected in [('resolution',source['resolution']),('renderer',source['backend']['renderer']),('light',source['shading']['light']),('color_type',source['shading']['color_type']),('shadows',False),('cavity',False),('transparent',False),('antialiasing','16'),('lights',[])]:
                checks.scalar('scene.'+field,int(scene.get(field)!=expected),0,0,'boolean')
            checks.scalar('scene.camera_inventory',len(set(scene['cameras'])^{c['id'] for c in source['cameras']}),0,0,'count')
            for camera in source['cameras']:
                actual=scene['cameras'].get(camera['id'])
                if actual:
                    checks.position('camera.'+camera['id']+'.origin',[actual['matrix_world'][i][3] for i in range(3)],camera['position_m'],1e-6)
                    checks.scalar('camera.'+camera['id']+'.ortho_scale',actual['ortho_scale_m'],camera['orthographic_scale_m'],1e-6,'m')
                    look=m.unit(m.sub(camera['look_at_m'],camera['position_m']))
                    actual_look=[-actual['matrix_world'][i][2] for i in range(3)]
                    checks.scalar('camera.'+camera['id']+'.direction',m.norm(m.sub(look,actual_look)),0,1e-6,'ratio')
            for axis in range(3):
                checks.scalar('scene.floor_color.'+str(axis),scene['floor_color'][axis],source['floor']['color'][axis],1e-6,'ratio')
                checks.scalar('scene.bone_color.'+str(axis),scene['bone_color'][axis],source['shading']['bone_color'][axis],1e-6,'ratio')
                checks.scalar('scene.background.'+str(axis),scene['background'][axis],source['shading']['background'][axis],1e-6,'ratio')
            floor=scene['floor_vertices'];size=source['floor']['size_m']
            checks.scalar('scene.floor_x',max(v[0] for v in floor)-min(v[0] for v in floor),size,1e-6,'m')
            checks.scalar('scene.floor_y',max(v[1] for v in floor)-min(v[1] for v in floor),size,1e-6,'m')
            checks.scalar('scene.floor_z',max(abs(v[2]) for v in floor),0,1e-6,'m')
        report['checks'].extend(checks.checks)
        report['status']='pass' if all(c['status']=='pass' for c in report['checks']) else 'fail'
    transforms['status']='pass' if all(r['status']=='pass' for r in reports.values()) else 'fail'
    transforms['scope']='evaluated-body-geometry-scene'
    transforms['acceptance']='incomplete: diagnostic/timing/determinism coverage and independent human review remain required'
    transforms['metadata']=metadata
    return transforms
