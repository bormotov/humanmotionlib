# SPDX-License-Identifier: Apache-2.0
"""Two clean fixed-camera render passes and a linked visual/numeric review pack."""

import argparse
from fractions import Fraction
import hashlib
import html
import json
from pathlib import Path
import sys

from PIL import Image,ImageChops,ImageDraw
from humanmotionlib import math3d as m
from humanmotionlib.prepared import read_prepared,write_json
from humanmotionlib.review_graphics import gif,label,onion,sheet
from humanmotionlib.package_resources import read_text, verify_runtime_integrity
from humanmotionlib.render_contract import (expected_views as _expected_views,
                                            read_supervised_receipt as _read_supervised_receipt,
                                            validate_manifest as _validate_manifest)
from humanmotionlib.runtime import (DEFAULT_RENDER_TIMEOUT, DEFAULT_SLOT_TIMEOUT, InvocationError,
                           resolve_workspace_path, validate_existing_run_root,
                           validate_run_root, validate_timeout, workspace_root)


def decoded_digest(path):
    with Image.open(path) as image:
        image=image.convert('RGBA')
        return hashlib.sha256(str(image.size).encode()+image.tobytes()).hexdigest()


def render_pass(input_path, output, frames, *, timeout_seconds=DEFAULT_RENDER_TIMEOUT,
                slot_timeout_seconds=DEFAULT_SLOT_TIMEOUT, workspace=None, owner_run=None):
    # Use the same validated routine path as ordinary builds; it probes the
    # pinned executable and records render outputs under this clean-pass run.
    validate_timeout(timeout_seconds)
    validate_timeout(slot_timeout_seconds, 'slot_timeout_seconds')
    workspace = workspace_root(workspace)
    input_path = resolve_workspace_path(input_path, workspace)
    output = resolve_workspace_path(output, workspace)
    frames = resolve_workspace_path(frames, workspace)
    if Path(output).exists():
        raise ValueError(f"Render pass output must be a fresh path: {output}")
    from humanmotionlib import run_blender
    run_blender.run(input_path, output, render_dir=frames, render_only=True,
                    timeout_seconds=timeout_seconds, slot_timeout_seconds=slot_timeout_seconds,
                    workspace=workspace, owner_run=owner_run)
    manifest = json.loads((output / 'render-manifest.json').read_text())
    prepared = read_prepared(input_path)
    required_paths = _validate_manifest(manifest, prepared, frames, output=output)
    _read_supervised_receipt(output, prepared, required_paths)
    return manifest


def reuse_render_pass(input_path, output, prepared):
    manifest_path = output / 'render-manifest.json'
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Missing or malformed render manifest: {manifest_path}") from error
    required_paths = _validate_manifest(manifest, prepared, output / 'frames', output=output)
    _read_supervised_receipt(output, prepared, required_paths)
    return manifest


def _preflight_reuse_pack(input_path, output, prepared):
    """Validate a completed pack and both saved passes before reassembly writes."""
    fixed_files = {
        'acceptance-map.md', 'attribution-and-limitations.md', 'build-metadata.json',
        'gif-timing.json', 'index.html', 'render-repeatability.json', 'sample-timing.json',
    }
    fixed_dirs = {'clean-a', 'clean-b', 'composites'}
    expected = fixed_files | fixed_dirs | {f'{fixture}.html' for fixture in prepared['sampling']}
    if (output / 'metrics.json').exists():
        expected.add('metrics.json')
    if 'squat' in prepared['sampling']:
        expected.add('squat-balance.json')
    reference = output / 'reference'
    if reference.exists():
        expected.add('reference')
        if (not reference.is_dir() or any(path.is_symlink() for path in reference.rglob('*'))
                or {path.relative_to(reference).as_posix() for path in reference.rglob('*') if path.is_file()} != {'input.json'}):
            raise ValueError(f"Unexpected reference content in reusable review pack: {reference}")
        reference_input = reference / 'input.json'
        if not reference_input.is_file() or reference_input.read_bytes() != input_path.read_bytes():
            raise ValueError('Reusable review pack reference input does not match the selected build input')
    actual = {path.name for path in output.iterdir()}
    if actual != expected:
        raise ValueError(
            f"Reusable review pack inventory mismatch: missing={sorted(expected - actual)}, "
            f"unexpected={sorted(actual - expected)}"
        )
    if any(path.is_symlink() for path in output.iterdir()):
        raise ValueError('Reusable review pack must not contain symlinked top-level entries')
    for name in fixed_files | {f'{fixture}.html' for fixture in prepared['sampling']}:
        if not (output / name).is_file():
            raise ValueError(f"Reusable review pack file is missing: {output / name}")
    for name in fixed_dirs:
        directory = output / name
        if not directory.is_dir():
            raise ValueError(f"Reusable review pack directory is missing: {directory}")

    selected_bytes = input_path.read_bytes()
    passes = []
    required_pass_names = {
        'build-metadata.json', 'frames', 'input.json', 'processes',
        'render-manifest.json', 'skeleton.blend',
    }
    for name in ('clean-a', 'clean-b'):
        directory = output / name
        entries = {path.name for path in directory.iterdir()}
        if entries != required_pass_names or any(path.is_symlink() for path in directory.iterdir()):
            raise ValueError(f"Reusable render pass has unexpected or missing content: {directory}")
        pass_input = directory / 'input.json'
        if not pass_input.is_file() or pass_input.read_bytes() != selected_bytes:
            raise ValueError(f"Reusable render pass input does not match the selected build input: {pass_input}")
        for path in directory.rglob('*'):
            if path.is_symlink():
                raise ValueError(f"Reusable render pass contains a symlink: {path}")
        passes.append(reuse_render_pass(input_path, directory, prepared))
    return passes


def project(point,camera,resolution):
    direction=m.unit(m.sub(camera['look_at_m'],camera['position_m']))
    right=m.unit(m.cross(direction,camera['up']));up=m.cross(right,direction)
    offset=m.sub(point,camera['look_at_m']);scale=resolution/camera['orthographic_scale_m']
    return resolution/2+m.dot(offset,right)*scale,resolution/2-m.dot(offset,up)*scale


def structural_sheets(prepared,images,output):
    profile=prepared['sources']['profile'];scene=prepared['sources']['review-scene'];height=profile['stature_m']
    neutral=next((s for s in prepared['samples'] if s['fixture']=='neutral'),None)
    if neutral is None:return []  # Explicit diagnostic-only development subset.
    regions={'axial':['pelvis','sacrum','coccyx','skull','mandible','sternum']+[f'{region}{i}' for region,count in [('C',7),('T',12),('L',5)] for i in range(1,count+1)],
             'girdle':['clavicle.R','scapula.R','humerus.R','clavicle.L','scapula.L','humerus.L'],
             'arms':['humerus.R','elbow.R','ulna.R','radius.R','wrist.R','hand.R','humerus.L','elbow.L','ulna.L','radius.L','wrist.L','hand.L'],
             'legs':['femur.R','patella.R','knee.R','tibia.R','fibula.R','talus.R','hindfoot.R','femur.L','patella.L','knee.L','tibia.L','fibula.L','talus.L','hindfoot.L']}
    regions['ribs']=[b['id'] for b in profile['structures'] if b['id'].startswith('rib.')]
    regions['hands']=[b['id'] for b in profile['structures'] if b['id'].startswith(('metacarpal.','phalanx.'))]
    regions['feet']=[b['id'] for b in profile['structures'] if b['id'].startswith(('calcaneus.','midfoot.','metatarsal.','mtp.','toe.'))]
    links=[]
    for view,camera in ((c['id'],c) for c in scene['cameras'] if not c['id'].startswith('thorax-')):
        path=images[neutral['id']][view]
        for region,ids in regions.items():
            with Image.open(path) as source:image=source.convert('RGB')
            draw=ImageDraw.Draw(image)
            for id in ids:
                frame=neutral['frames'][id];start=project(frame['position_m'],camera,1024)
                for axis,color in enumerate(((210,30,30),(20,150,35),(40,70,230))):
                    endpoint=m.add(frame['position_m'],m.mv(frame['rotation'],[.025*height if i==axis else 0 for i in range(3)]))
                    draw.line([start,project(endpoint,camera,1024)],fill=color,width=2)
            coordinates=[project(neutral['frames'][id]['position_m'],camera,1024) for id in ids]
            box=(max(0,int(min(v[0] for v in coordinates)-85)),max(0,int(min(v[1] for v in coordinates)-85)),min(1024,int(max(v[0] for v in coordinates)+85)),min(1024,int(max(v[1] for v in coordinates)+85)))
            crop=image.crop(box)
            enlargement=min(720/crop.width,860/crop.height)
            crop=crop.resize((round(crop.width*enlargement),round(crop.height*enlargement)),Image.Resampling.LANCZOS)
            canvas=Image.new('RGB',(1100,max(320,crop.height+40,len(ids)*16+40)),(245,247,248));canvas.paste(crop,(0,30))
            label(canvas,region+' / '+view,scale=2)
            for index,id in enumerate(ids):label(canvas,id,(740,30+16*index),scale=1)
            name=f'structure-{region}-{view}.png';canvas.save(output/name);links.append(name)
    links.extend(thoracic_sheets(prepared,images,output))
    return links


def thoracic_sheets(prepared,images,output):
    """Label fixed inspection renders; projection and anatomy are unchanged."""
    links=[];profile=prepared['sources']['profile'];height=profile['stature_m']
    bodies={b['id']:b for b in profile['structures']}
    for sample in (s for s in prepared['samples'] if s['fixture'] in ('neutral','rest')):
        for camera in (c for c in prepared['sources']['review-scene']['cameras'] if c['id'].startswith('thorax-')):
            for isolated in (False,True):
                view=camera['id']+('-isolated' if isolated else '')
                with Image.open(images[sample['id']][view]) as source:image=source.convert('RGB')
                canvas=Image.new('RGB',(1420,1100),(245,247,248));canvas.paste(image,(0,45))
                label(canvas,sample['fixture']+' / '+view,(12,8),scale=2)
                draw=ImageDraw.Draw(canvas)
                if isolated:
                    from humanmotionlib.geometry import centerline
                    for j in range(1,11):
                        id=f'cartilage.{j}.R';frame=sample['frames'][id]
                        world=[m.add(frame['position_m'],m.mv(frame['rotation'],p)) for p in centerline(sample['guides'][id+'.geometry.0'])]
                        projected=[(x,y+45) for x,y in (project(p,camera,1024) for p in world)]
                        draw.line(projected,fill=(20,125,90),width=2)
                        if j in (2,5,7,8,9,10):
                            x,y=projected[8];label(canvas,'C'+str(j),(round(x)+6,round(y)-4),scale=1)
                    for j in range(1,13):
                        id=f'rib.{j}.R';frame=sample['frames'][id];p=bodies[id]['geometry'][0]['points_m'][1]
                        world=m.add(frame['position_m'],m.mv(frame['rotation'],p));x,y=project(world,camera,1024);y+=45
                        draw.ellipse((x-3,y-3,x+3,y+3),fill=(30,95,180))
                        if j==6:
                            draw.line([(x,y),(x-35,y)],fill=(30,95,180),width=1)
                            label(canvas,'P1',(round(x)-53,round(y)-4),scale=1)
                for j in range(1,13):
                    body=bodies[f'rib.{j}.R'];point=body['geometry'][0]['points_m'][2]
                    frame=sample['frames'][body['id']]
                    world=m.add(frame['position_m'],m.mv(frame['rotation'],point))
                    x,y=project(world,camera,1024);y+=45
                    draw.ellipse((x-3,y-3,x+3,y+3),fill=(100,50,0))
                    label(canvas,str(j),(round(x)+6,round(y)-7),scale=2)
                legend=['RIB NUMBERS 1-12','BONE: RIBS AND STERNUM','CARTILAGE: C1-C10','GREEN: CARTILAGE OVERLAY','1-7: STERNAL INSERTIONS','2: STERNAL ANGLE','8-10: CARTILAGE ARCH','11-12: FREE RIB TIPS','BLUE: POSTERIOR ANGLE P1','NUMBER DOT: LATERAL P2','STERNUM: MANUBRIUM,','BODY AND XIPHOID',f'STATURE: {height:.2f} M','AUTHORED APPROXIMATION']
                for i,text in enumerate(legend):label(canvas,text,(1036,65+30*i),scale=1)
                for name,landmark in [('ANGLE','sternum.angle'),('XIPHOID','sternum.bottom')]:
                    record=next(l for l in profile['landmarks'] if l['id']==landmark)
                    body=bodies['sternum'];local=m.mv(m.transpose(body['basis']),m.sub(record['position_m'],body['origin_m']))
                    frame=sample['frames']['sternum'];world=m.add(frame['position_m'],m.mv(frame['rotation'],local))
                    x,y=project(world,camera,1024);y+=45
                    draw.line([(x,y),(x+38,y)],fill=(40,85,125),width=2)
                    label(canvas,name,(round(x)+40,round(y)-5),scale=1)
                name=sample['fixture']+'-'+view+'.png';canvas.save(output/name);links.append(name)
    return links


def assemble(prepared,first,second,root):
    first_frames=root/'clean-a'/'frames';second_frames=root/'clean-b'/'frames'
    images={s['id']:{view:first_frames/path for view,path in s['images'].items()} for s in first['samples']}
    repeat=[]
    if first['prepared_sha256']!=second['prepared_sha256']:raise ValueError('Clean render input hashes differ')
    for sample in first['samples']:
        for view,path in sample['images'].items():
            a,b=first_frames/path,second_frames/path
            same=decoded_digest(a)==decoded_digest(b)
            repeat.append({'sample':sample['id'],'view':view,'status':'pass' if same else 'fail','image':str(a.relative_to(root))})
    composites=root/'composites';composites.mkdir(exist_ok=True)
    from humanmotionlib.balance_review import overlays
    balance_images,balance_pairs,balance_report=overlays(prepared,first,second,root,project,decoded_digest)
    repeat.extend(balance_pairs)
    structures=structural_sheets(prepared,images,composites)
    lookup={s['id']:s for s in prepared['samples']};fixtures={f['id']:f for f in prepared['sources']['diagnostics']}
    pages=[];gif_metrics=[]
    for id,plans in prepared['sampling'].items():
        fixture=fixtures[id];body=[f'<h1>{html.escape(id)}</h1>',f'<p>{html.escape(fixture["description"])}</p>']
        for plan in plans:
            if id=='squat':
                for view in ('front','side'):
                    for mode in ('static','animation'):
                        records=plan[mode];paths=[balance_images[s['sample_id']][view] for s in records]
                        captions=[f'BEAT {s["beat"]["numerator"]}/{s["beat"]["denominator"]} - {plan["bpm"]} BPM' for s in records]
                        filename=f'squat-{plan["bpm"]}-{view}-{mode}-balance.png'
                        sheet(paths,captions,composites/filename)
                        body.append(f'<p><a href="composites/{filename}">{plan["bpm"]} BPM / {view} / {mode} estimated COM/support sheet</a></p>')
                    paths=[balance_images[s['sample_id']][view] for s in plan['animation']]
                    name=f'squat-{plan["bpm"]}-{view}-balance.gif'
                    metric=gif(paths,Fraction(60,plan['bpm'])/plan['intervals_per_beat'],composites/name)
                    gif_metrics.append(metric|{'fixture':id,'bpm':plan['bpm'],'view':view+'-balance','image':'composites/'+name})
                    body.append(f'<p>Estimated whole-body COM including unrendered tissues; static plausibility only. Fixed crop; camera/floor unchanged.<br><img width="720" src="composites/{name}" alt="Squat {view} estimated COM/support"></p>')
            for view in ('front','side'):
                for mode in ('static','animation'):
                    records=plan[mode];paths=[images[s['sample_id']][view] for s in records]
                    captions=[f'BEAT {s["beat"]["numerator"]}/{s["beat"]["denominator"]} - {plan["bpm"]} BPM' for s in records]
                    filename=f'{id}-{plan["bpm"]}-{view}-{mode}.png'
                    sheet(paths,captions,composites/filename)
                    body.append(f'<p><a href="composites/{filename}">{plan["bpm"]} BPM / {view} / {mode} sheet</a></p>')
                if fixture['duration_beats']:
                    paths=[images[s['sample_id']][view] for s in plan['animation']]
                    name=f'{id}-{plan["bpm"]}-{view}.gif'
                    metric=gif(paths,Fraction(60,plan['bpm'])/plan['intervals_per_beat'],composites/name)
                    gif_metrics.append(metric|{'fixture':id,'bpm':plan['bpm'],'view':view,'image':'composites/'+name})
                    body.append(f'<p><img width="512" src="composites/{name}" alt="{html.escape(id)} {view}"></p>')
                    if id=='sweep-shoulder-bilateral-plane':
                        detail=f'{id}-{plan["bpm"]}-{view}-detail.gif'
                        metric=gif(paths,Fraction(60,plan['bpm'])/plan['intervals_per_beat'],composites/detail,crop_box=(372,360,652,640))
                        gif_metrics.append(metric|{'fixture':id,'bpm':plan['bpm'],'view':view,'image':'composites/'+detail,'fixed_crop_px':[372,360,652,640]})
                        body.append(f'<p>Fixed crop of the same render for the small elevation context (no camera change):<br><img width="512" src="composites/{detail}" alt="Plane sweep detail"></p>')
            if plan['bpm']==120 and fixture['duration_beats']:
                for view in ('front','side'):
                    name=f'{id}-{view}-onion.png';onion([images[s['sample_id']][view] for s in plan['static']],composites/name)
                    body.append(f'<p><a href="composites/{name}">{view} onion-skin count overlay</a></p>')
        body.append('<h2>Exact sample timestamps and PNGs</h2><table><tr><th>ID</th><th>Beat</th><th>PNG views</th></tr>')
        for sample in prepared['samples']:
            if sample['fixture']!=id:continue
            links=' '.join(f'<a href="{path.relative_to(root)}">{view}</a>' for view,path in images[sample['id']].items())
            b=sample['beat'];body.append(f'<tr id="{sample["frame_id"]}"><td>{sample["id"]}</td><td>{b["numerator"]}/{b["denominator"]}</td><td>{links}</td></tr>')
        body.append('</table>')
        if id=='squat':
            body.append('<p><a href="squat-balance.json">Actual rendered COM/support observations, weights, margins and checks</a></p>')
            for sample_id,views in balance_images.items():
                body.append('<p>'+html.escape(sample_id)+': '+ ' '.join(f'<a href="{path.relative_to(root)}">{view} COM/support detail</a>' for view,path in views.items())+'</p>')
        write_html(root/(id+'.html'),id,'\n'.join(body));pages.append(id)
        print('Assembled '+id,flush=True)
    repeat_report={'status':'pass' if repeat and all(r['status']=='pass' for r in repeat) else 'fail','comparisons':repeat,'criterion':'Exact equality of decoded RGBA pixels at identical settings on the recorded reference environment.'}
    write_json(root/'render-repeatability.json',repeat_report)
    write_json(root/'gif-timing.json',{'status':'pass' if all(r['status']=='pass' for r in gif_metrics) else 'fail','previews':gif_metrics})
    write_json(root/'build-metadata.json',first['metadata'])
    write_json(root/'sample-timing.json',prepared['sampling'])
    attribution='''# Attribution and limitations

Library-authored geometry and diagnostics: HumanMotionLib contributors, CC-BY-4.0.
Code: Apache-2.0. This is a symmetric procedural animation reference, not a scan,
clinical model, measured gait, muscle simulation or production motion library.
Digits and many cranial/tarsal structures are grouped/fixed or omitted as listed
in the source profile. Coupling formulas and supported envelopes are explicit
engineering approximations; cohort means remain reference observations only.
MPFB and Rigify are not used. No skin or muscles are included.

Squat R3 uses an estimated whole-body point-mass model including unrendered
tissues. Its measured contact-support margins establish static plausibility
for the declared approximation, not dynamic balance at playback tempos. The
point placements and perturbation allowance are authored adaptations. Separate
COM/support overlays preserve unannotated views and fixed cameras/floor.

Green markers are declared contact-envelope witnesses. Dark lines are fixed
floor references. General regional images are fixed full-view crops; thoracic
inspection uses the separately declared fixed source cameras in context and
isolation. Cameras, floor and scale are never fitted to an exercise. Axes use the
source 0.025 H object-space length. Lettering is repository-authored bitmap
artwork; no imported font asset is distributed. GIFs coalesce a closed-loop
terminal duplicate with the next cycle's first frame. PNG timestamps are exact.

All used anatomical text/data and vocabulary sources, their cleared licenses,
changes, commercial-use basis and attribution are recorded below.

'''+read_text('docs/used-materials.md')+'\n\n'+read_text('THIRD-PARTY-NOTICES.md')
    (root/'attribution-and-limitations.md').write_text(attribution)
    (root/'acceptance-map.md').write_text(read_text('docs/anatomical-skeleton-acceptance.md'))
    links=''.join(f'<li><a href="{id}.html">{id}</a></li>' for id in pages)
    structural=''.join(f'<li><a href="composites/{name}">{name}</a></li>' for name in structures)
    overview=f'''<h1>Anatomical human skeleton — review pack</h1>
<p>Reference stature {prepared['sources']['profile']['stature_m']} m. Authored diagnostic animation; no muscles. Numeric evidence and human visual judgement remain separate.</p>
<p><strong>Independent review and human visual approval are pending.</strong></p>
<p><a href="metrics.json">Numeric metrics</a> · <a href="acceptance-map.md">Scenario evidence map</a> · <a href="build-metadata.json">Backend/GPU/settings</a> · <a href="sample-timing.json">Exact timing</a> · <a href="render-repeatability.json">Clean render comparison: {repeat_report['status']}</a> · <a href="gif-timing.json">GIF timing</a> · <a href="attribution-and-limitations.md">Attribution and approximation limits</a></p>
<h2>Diagnostics and every independent joint axis</h2><ul>{links}</ul><h2>Regional fixed-view inspection and local axes</h2><ul>{structural}</ul>
<p>Full-resolution neutral and T-pose front/rear/side views are linked from their diagnostic pages. Local axes: red +X, green +Y, blue +Z. Data and renders: CC-BY-4.0.</p>'''
    write_html(root/'index.html','Anatomical human skeleton',overview)
    return repeat_report|{'gif_status':'pass' if all(row['status']=='pass' for row in gif_metrics) else 'fail',
                          'balance_status':balance_report['status'],
                          'status':'pass' if repeat_report['status']=='pass' and all(row['status']=='pass' for row in gif_metrics) and balance_report['status'] in ('pass','not-applicable') else 'fail'}


def write_html(path,title,body):
    style='body{font:16px/1.5 system-ui,sans-serif;max-width:1200px;margin:32px auto;color:#17232b;background:#f5f7f8}a{color:#075887}img{max-width:100%}td,th{padding:6px 16px;border-bottom:1px solid #ccd4da;text-align:left}'
    path.write_text(f'<!doctype html><html lang="en"><meta charset="utf-8"><title>{html.escape(title)}</title><style>{style}</style><body>{body}</body></html>')


def main(workspace=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,help='Evaluated skeleton build (normal render-pack mode)')
    parser.add_argument('--reuse-renders',action='store_true',help='Reassemble previously completed render passes after validating their input hash')
    parser.add_argument('--html-only-from',type=Path,help='Regenerate presentation HTML from an existing verified pack without rendering or re-encoding media')
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--timeout-seconds',type=float,default=DEFAULT_RENDER_TIMEOUT,
                        help='Finite deadline for each supervised render pass')
    parser.add_argument('--slot-timeout-seconds',type=float,default=DEFAULT_SLOT_TIMEOUT,
                        help='Finite wait for the checkout backend slot per invocation')
    args=parser.parse_args()
    verify_runtime_integrity()
    workspace = workspace_root(workspace)
    output_operand = resolve_workspace_path(args.output, workspace)
    output = validate_run_root(output_operand, workspace)
    if bool(args.input)==bool(args.html_only_from):
        parser.error('choose exactly one of --input or --html-only-from')
    if args.html_only_from:
        if args.reuse_renders:
            parser.error('--reuse-renders applies only to normal render-pack mode')
        predecessor = resolve_workspace_path(args.html_only_from, workspace)
        if output.exists() and any(output.iterdir()):
            raise ValueError(f"review-pack output run root is occupied: {output}")
        from humanmotionlib.presentation import regenerate_html
        result=regenerate_html(predecessor,output,[Path(__file__).resolve(),Path(__file__).with_name('presentation.py').resolve()],workspace=workspace)
        print(json.dumps(result,sort_keys=True),flush=True)
        return 0 if result['status']=='pass' else 1
    if not args.input:
        parser.error('--input is required for normal render-pack mode')
    input_root = validate_existing_run_root(args.input, workspace)
    input_path = input_root / 'input.json'
    if args.reuse_renders:
        if input_root == output or input_root.is_relative_to(output) or output.is_relative_to(input_root):
            raise ValueError('review-pack input and output run roots must be distinct and disjoint')
        if not output.is_dir():
            raise ValueError(f"--reuse-renders requires an existing complete review-pack root: {output}")
        prepared = read_prepared(input_path)
        passes = _preflight_reuse_pack(input_path, output, prepared)
        result = assemble(prepared, *passes, output)
        print(json.dumps(result, sort_keys=True), flush=True)
        return 0 if result['status'] == 'pass' else 1
    if input_root == output or input_root.is_relative_to(output) or output.is_relative_to(input_root):
        raise ValueError('review-pack input and output run roots must be distinct and disjoint')
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"review-pack output run root is occupied: {output}")
    validate_timeout(args.timeout_seconds)
    validate_timeout(args.slot_timeout_seconds, 'slot_timeout_seconds')
    prepared=read_prepared(input_path)
    output.mkdir(parents=True,exist_ok=True)
    passes=[]
    for name in ('clean-a','clean-b'):
        directory=output/name
        manifest=render_pass(input_path.resolve(),directory.resolve(),
                             (directory/'frames').resolve(),
                             timeout_seconds=args.timeout_seconds,
                             slot_timeout_seconds=args.slot_timeout_seconds,
                             workspace=workspace, owner_run=output)
        passes.append(manifest)
        print('Completed '+name,flush=True)
    result=assemble(prepared,*passes,output)
    return 0 if result['status']=='pass' else 1


if __name__=='__main__':
    try:raise SystemExit(main())
    except (InvocationError,ValueError,OSError,KeyError) as error:print(str(error),file=sys.stderr);raise SystemExit(1)
