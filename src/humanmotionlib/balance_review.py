# SPDX-License-Identifier: Apache-2.0
"""Separate fixed-crop COM overlays from fresh native render-pass evidence."""

from PIL import Image,ImageDraw
from humanmotionlib.balance import measure_balance
from humanmotionlib.review_graphics import label
from humanmotionlib.prepared import write_json

CROP=(280,220,760,820)  # Same source pixels for every pose/view/stature.


def overlays(prepared,first,second,root,project,digest):
    sources={s['id']:s for s in prepared['samples'] if s['fixture']=='squat'}
    if not sources:return {},[],{'status':'not-applicable','samples':[]}
    cameras={c['id']:c for c in prepared['sources']['review-scene']['cameras']}
    profile=prepared['sources']['profile'];height=profile['stature_m']
    paths={};reports={};pairs=[];all_pass=True
    for pass_name,manifest in [('clean-a',first),('clean-b',second)]:
        rows={s['id']:s for s in manifest['samples']}
        for id,source in sources.items():
            native=rows[id].get('balance_evidence')
            if native is None:raise ValueError('Missing actual rendered COM/support evidence: '+id)
            beat=source['beat']['numerator']/source['beat']['denominator']
            report=measure_balance(profile,native,source['contacts'],beat,True)
            if report['assessment'] is None:raise ValueError('Missing support/COM assessment: '+id)
            all_pass &= report['status']=='pass'
            if pass_name=='clean-a':reports[id]=report|{'beat':source['beat'],'source_sample':id}
            a=report['assessment'];v=a['variants']['reference'];com=v['com_m'];polygon=a['support_xy_m']
            for view in ('front','side'):
                raw=root/pass_name/'frames'/rows[id]['images'][view]
                with Image.open(raw) as image:body=image.convert('RGB').crop(CROP).resize((800,1000),Image.Resampling.LANCZOS)
                canvas=Image.new('RGB',(1200,1000),(245,247,248));canvas.paste(body,(0,0));draw=ImageDraw.Draw(canvas)
                def xy(point):
                    x,y=project(point,cameras[view],1024)
                    return ((x-CROP[0])*1000/600,(y-CROP[1])*1000/600)
                color=(20,110,75) if report['status']=='pass' else (185,35,45)
                c=xy(com);floor=xy([com[0],com[1],0]);draw.line((c,floor),fill=color,width=3)
                for p in (c,floor):draw.ellipse((p[0]-7,p[1]-7,p[0]+7,p[1]+7),fill=color)
                label(canvas,'COM',(int(c[0]+12),int(c[1]-10)),scale=2,color=color)
                support=[xy([*p,0]) for p in polygon]
                draw.line(support+[support[0]],fill=(35,95,170),width=5)
                text=['SQUAT / '+view, f'BEAT {beat:.3f}', '',
                      'ESTIMATED WHOLE-BODY COM','STATIC PLAUSIBILITY ONLY',
                      'INCLUDES UNRENDERED TISSUES','',
                      f'REFERENCE MARGIN {v["margin_h"]:.5f} H','REQUIRED 0.01000 H','',
                      'PERTURBATION LOWER BOUND',f'{a["perturbation_lower_bound_h"]:.5f} H','REQUIRED 0.00500 H','',
                      'BODY POINTS ARE APPROXIMATE','NOT A DYNAMIC BALANCE TEST','',
                      'BLUE - MEASURED SUPPORT','GREEN - COM AND PROJECTION']
                for n,t in enumerate(text):label(canvas,t,(815,24+27*n),scale=2,color=(25,45,65))
                label(canvas,'SUPPORT PLAN VIEW / XY',(815,590),scale=2)
                # Native support plan inset; fixed metric scale normalized by H.
                def plan(p):return (1000+p[0]/height*1900,850-p[1]/height*1900)
                outline=[plan(p) for p in polygon];draw.polygon(outline,fill=(225,236,247),outline=(35,95,170),width=3)
                q=plan(com[:2]);draw.ellipse((q[0]-6,q[1]-6,q[0]+6,q[1]+6),fill=color)
                label(canvas,'Y ANTERIOR',(850,625),scale=2)
                label(canvas,'FIXED CROP OF SOURCE PNG',(815,940),scale=2)
                label(canvas,'CAMERA AND FLOOR UNCHANGED',(815,966),scale=2)
                path=root/pass_name/'balance'/(id.replace('/','-')+'-'+view+'.png')
                path.parent.mkdir(parents=True,exist_ok=True);canvas.save(path)
                if pass_name=='clean-a':paths.setdefault(id,{})[view]=path
                else:
                    original=paths[id][view]
                    pairs.append({'sample':id,'view':view+'-balance-overlay','status':'pass' if digest(original)==digest(path) else 'fail','image':str(original.relative_to(root))})
    result={'status':'pass' if all_pass and all(p['status']=='pass' for p in pairs) else 'fail',
            'scope':'Actual render-pass bone/mass/support evidence; static plausibility only.',
            'fixed_crop_px':list(CROP),'samples':reports}
    write_json(root/'squat-balance.json',result)
    return paths,pairs,result
