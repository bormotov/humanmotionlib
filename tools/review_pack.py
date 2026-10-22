# SPDX-License-Identifier: Apache-2.0
"""Two clean fixed-camera render passes and a linked visual/numeric review pack."""

import argparse
from fractions import Fraction
import hashlib
import html
import json
from pathlib import Path
import subprocess
import sys

if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from PIL import Image,ImageChops,ImageDraw
from tools import math3d as m
from tools.prepared import read_prepared,write_json
from tools.review_graphics import gif,label,onion,sheet
from tools.runtime import blender_executable,project_root


def decoded_digest(path):
    with Image.open(path) as image:
        image=image.convert('RGBA')
        return hashlib.sha256(str(image.size).encode()+image.tobytes()).hexdigest()


def render_pass(input_path,output,frames):
    output.mkdir(parents=True,exist_ok=True)
    command=[blender_executable(),'--background','--factory-startup','--python','tools/build_skeleton.py','--','--input',str(input_path),'--output',str(output),'--render-dir',str(frames),'--render-only']
    with (output/'render.log').open('w') as log:
        result=subprocess.run(command,cwd=project_root(),stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:raise ValueError('Clean render failed; see '+str(output/'render.log'))
    return json.loads((output/'render-manifest.json').read_text())


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
                    from tools.geometry import centerline
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
    from tools.balance_review import overlays
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

'''+(project_root()/'docs/used-materials.md').read_text()+'\n\n'+(project_root()/'THIRD-PARTY-NOTICES.md').read_text()
    (root/'attribution-and-limitations.md').write_text(attribution)
    (root/'acceptance-map.md').write_text((project_root()/'docs/anatomical-skeleton-acceptance.md').read_text())
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


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,help='Evaluated skeleton build (normal render-pack mode)')
    parser.add_argument('--reuse-renders',action='store_true',help='Reassemble previously completed render passes after validating their input hash')
    parser.add_argument('--html-only-from',type=Path,help='Regenerate presentation HTML from an existing verified pack without rendering or re-encoding media')
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    if bool(args.input)==bool(args.html_only_from):
        parser.error('choose exactly one of --input or --html-only-from')
    if args.html_only_from:
        if args.reuse_renders:
            parser.error('--reuse-renders applies only to normal render-pack mode')
        from tools.presentation import regenerate_html
        result=regenerate_html(args.html_only_from,args.output,[Path(__file__).resolve(),Path(__file__).with_name('presentation.py').resolve()])
        print(json.dumps(result,sort_keys=True),flush=True)
        return 0 if result['status']=='pass' else 1
    if not args.input:
        parser.error('--input is required for normal render-pack mode')
    prepared=read_prepared(args.input/'input.json')
    args.output.mkdir(parents=True,exist_ok=True)
    passes=[]
    for name in ('clean-a','clean-b'):
        directory=args.output/name
        manifest=json.loads((directory/'render-manifest.json').read_text()) if args.reuse_renders else render_pass((args.input/'input.json').resolve(),directory.resolve(),(directory/'frames').resolve())
        if manifest['prepared_sha256']!=prepared['content_sha256']:raise ValueError('Stale render manifest')
        passes.append(manifest)
        print('Completed '+name,flush=True)
    result=assemble(prepared,*passes,args.output)
    return 0 if result['status']=='pass' else 1


if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError) as error:print(str(error),file=sys.stderr);raise SystemExit(1)
