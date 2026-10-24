# SPDX-License-Identifier: Apache-2.0
"""Independent thoracic dossier and relational checks on measured mesh controls.

No geometry constructor or guide solver is used for expected positions. The
Hermite form below independently samples the declared Catmull–Rom centerline.
"""

import math
from humanmotionlib import math3d as m
from humanmotionlib.measurements import Measurements

RIB_ROWS = [(.045,.022,.024,.783),(.058,.030,.039,.759),(.070,.035,.047,.739),
            (.079,.038,.053,.719),(.085,.041,.057,.699),(.089,.043,.058,.681),
            (.090,.046,.057,.663),(.087,.052,.052,.650),(.081,.057,.041,.641),
            (.071,.054,.027,.635),(.057,.050,.007,.627),(.040,.033,-.002,.615)]
STERNUM_ROWS = [(.795,.018,.008),(.790,.018,.012),(.765,.042,.009),(.745,.050,.010),
                (.720,.058,.009),(.695,.062,.008),(.680,.063,.006),(.665,.059,.002)]
INSERTION_Z = [.783,.765,.746,.728,.710,.692,.681]
REQUIREMENT = 'anatomical-skeleton / Differentiated thoracic geometry and anatomical connections'
MOTION_REQUIREMENT = 'joint-mobility / Coupled motion is observable and constrained / Preserve thoracic attachments during motion'


def rib_controls(j, side='R'):
    w,x,a,e = RIB_ROWS[j-1]
    y,z = -.018*math.sin(math.pi*(12-j)/11), .645+.014*(12-j)
    points = [[.012,y-.002,z],[.60*w,y-.014,z-.008],[w,(y+a)/2,(z+e)/2],
              [.90*w,a-.006,e+.006],[x,a,e]]
    return points if side == 'R' else [m.mirror_position(p) for p in points]


def insertion(j, side='R'):
    z = INSERTION_Z[j-1]
    for (z0,y0,b0),(z1,y1,b1) in zip(STERNUM_ROWS,STERNUM_ROWS[1:]):
        if z1 <= z <= z0:
            t = (z0-z)/(z0-z1)
            return [(1 if side == 'R' else -1)*(b0+t*(b1-b0)),y0+t*(y1-y0),z]
    raise ValueError('Insertion outside sternal rows')


def hermite_curve(points, intervals=1024):
    output=[]
    for k in range(intervals+1):
        u=k/intervals*(len(points)-1);i=min(int(u),len(points)-2);t=u-i
        a,b=points[i],points[i+1]
        ta=m.scale(m.sub(b,points[max(i-1,0)]),.5)
        tb=m.scale(m.sub(points[min(i+2,len(points)-1)],a),.5)
        output.append([((2*t**3-3*t*t+1)*a[c]+(t**3-2*t*t+t)*ta[c]
                        +(-2*t**3+3*t*t)*b[c]+(t**3-t*t)*tb[c]) for c in range(3)])
    return output


def measure_thorax(profile, sample, neutral=False, beat=0):
    height=profile['stature_m'];bodies={b['id']:b for b in profile['structures']}
    geometry=sample.get('geometry',{});frames=sample['frames'];checks=Measurements(beat)
    def flag(name, good):
        checks.scalar('thorax.'+name,int(not good),0,0,'boolean',REQUIREMENT)
    def position(name, measured, expected):
        checks.position('thorax.'+name,measured,expected,1e-4*height)
        checks.checks[-1]['requirement']=MOTION_REQUIREMENT
    def controls(name, count, curve=False):
        points=geometry.get(name+'.geometry.0',{}).get('controls_m',[])
        flag(name+'.controls_present',len(points)==count)
        return points if len(points)==count or (curve and len(points)>=2) else None
    def move(id, neutral_point):
        body=bodies[id];local=m.mv(m.transpose(body['basis']),m.sub(m.scale(neutral_point,height),body['origin_m']))
        return m.add(frames[id]['position_m'],m.mv(frames[id]['rotation'],local))
    sternal=controls('sternum',16)
    flag('sternum.T1_parent',bodies['sternum']['parent']=='T1')
    if sternal:
        for side,index in [('L',2),('R',3)]:
            position('SC.'+side,sternal[index],frames['clavicle.'+side]['position_m'])
        if neutral:
            expected=[[sign*b,y,z] for z,y,b in STERNUM_ROWS for sign in (-1,1)]
            for i,(point,nominal) in enumerate(zip(sternal,expected)):
                position('sternum.row.'+str(i),point,m.scale(nominal,height))
            thickness=geometry['sternum.geometry.0'].get('thicknesses_m',[])
            flag('sternum.thickness_evidence',len(thickness)==16)
            for i,value in enumerate(thickness):
                checks.scalar('thorax.sternum.thickness.'+str(i),value,.006*height,1e-4*height,'m',REQUIREMENT)
    for side in ('L','R'):
        previous_descent=None;widths={};lengths={}
        guide_controls={j:controls(f'cartilage.{j}.{side}',3) for j in range(1,11)}
        for j in range(1,13):
            id=f'rib.{j}.{side}';body=bodies[id];points=controls(id,5,True)
            flag(id+'.vertebral_parent',body['parent']=='T'+str(j))
            if not points:continue
            if neutral:
                for k,(point,nominal) in enumerate(zip(points,rib_controls(j,side))):
                    position(id+'.nominal.'+str(k),point,m.scale(nominal,height))
                curve=hermite_curve(points)
                widths[j]=max(abs(p[0])/height for p in curve)
                lengths[j]=sum(math.dist(a,b) for a,b in zip(curve,curve[1:]))
                checks.limit('thorax.'+id+'.posterior_angle',(bodies['T'+str(j)]['origin_m'][1]-points[1][1])/height,[.010,1e100],1e-4,'H')
                descent=(points[0][2]-points[-1][2])/height
                chord=[points[-1][i]-points[0][i] for i in range(3)]
                inclination=math.degrees(math.atan2(-chord[2],chord[1]))
                checks.limit('thorax.'+id+'.sagittal_chord_inclination',inclination,[0,180],1e-4)
                if j<=7:
                    checks.limit('thorax.'+id+'.descent',descent,[.014,.018] if j==1 else [.024,.056],1e-4,'H')
                    if previous_descent is not None:flag(id+'.increasing_descent',descent>previous_descent)
                    previous_descent=descent
                    s=insertion(j,side)
                    checks.limit('thorax.'+id+'.anterior_overhang',max(p[1] for p in curve)/height-s[1],[-1e100,.003],1e-4,'H')
            if j<=10:
                g=guide_controls[j]
                if g is None:continue
                position(f'cartilage.{j}.{side}.rib_endpoint',g[0],points[-1])
                target=move('sternum',insertion(j,side)) if j<=7 else (guide_controls[j-1][1] if guide_controls[j-1] else None)
                if target is not None:position(f'cartilage.{j}.{side}.distal_endpoint',g[2],target)
                offset=m.mv(frames['T'+str(j)]['rotation'],m.scale([0,.001,-(.003 if j==7 else .001)],height))
                position(f'cartilage.{j}.{side}.midpoint',g[1],m.add(m.scale(m.add(g[0],g[2]),.5),offset))
                primitive=bodies[f'cartilage.{j}.{side}']['geometry'][0]
                bindings={b['point_index']:b for b in primitive.get('bindings',[])}
                binding=bindings.get(2,{})
                correct=(binding.get('structure')=='sternum' if j<=7 else binding.get('kind')=='guide_point' and binding.get('guide')==f'cartilage.{j-1}.{side}.geometry.0' and binding.get('control_index')==1)
                flag(f'cartilage.{j}.{side}.connection_topology',correct)
                if neutral and j<=7:
                    checks.limit(f'thorax.cartilage.{j}.{side}.anterior_displacement',(g[2][1]-g[0][1])/height,[-1e-4,1e100],0,'H')
            else:
                flag(id+'.free_tip',not any(b.get('structure')==id for b0 in bodies.values() for g in b0['geometry'] for b in g.get('bindings',[])))
        if neutral:
            if set(widths)==set(range(1,13)):
                checks.limit('thorax.first_width.'+side,widths[1],[.040,.050],1e-4,'H')
                mid=max(widths[j] for j in (6,7,8))
                checks.limit('thorax.middle_width.'+side,mid,[.084,.094],1e-4,'H')
                checks.limit('thorax.widening.'+side,mid-widths[1],[.035,1e100],1e-4,'H')
                checks.limit('thorax.floating11_length_ratio.'+side,lengths[11]/lengths[10],[.65,.80],1e-4,'ratio')
                checks.limit('thorax.floating12_length_ratio.'+side,lengths[12]/lengths[11],[.70,.85],1e-4,'ratio')
    if neutral:
        for name,item in geometry.items():
            if not (name.startswith(('rib.','cartilage.')) or name=='sternum.geometry.0'):continue
            bounds=item.get('world_bounds_m')
            flag(name+'.bounds_evidence',bounds is not None)
            if bounds:
                for axis,allowed in enumerate([[-.095,.095],[-.038,.070],[.610,.803]]):
                    for end in (0,1):checks.limit('thorax.'+name+f'.surface.{axis}.{end}',bounds[end][axis]/height,allowed,1e-4,'H')
    for check in checks.checks:
        if check['id'].startswith('thorax.') and check['requirement'].startswith('joint-mobility / Joint'):
            check['requirement']=REQUIREMENT
    return checks.checks


def data_guide_residuals(profile, frames, guides):
    """Dense data-side closure only; native mesh evidence remains separate."""
    height=profile['stature_m'];bodies={b['id']:b for b in profile['structures']}
    def world(id,p):return m.add(frames[id]['position_m'],m.mv(frames[id]['rotation'],p))
    def neutral_point(id,p):
        b=bodies[id]
        return world(id,m.mv(m.transpose(b['basis']),m.sub(m.scale(p,height),b['origin_m'])))
    current={}
    for j in range(1,11):
        for side in ('L','R'):
            id=f'cartilage.{j}.{side}'
            points=guides.get(id+'.geometry.0',[])
            if len(points)!=3:return {'endpoint_h':float('inf'),'midpoint_h':float('inf'),'sc_h':float('inf')}
            current[(j,side)]=[world(id,p) for p in points]
    endpoint=midpoint=sc=0.
    for side in ('L','R'):
        sc=max(sc,math.dist(neutral_point('sternum',[(1 if side=='R' else -1)*.012,.018,.790]),frames['clavicle.'+side]['position_m'])/height)
        for j in range(1,11):
            g=current[(j,side)];rib=f'rib.{j}.{side}'
            tip=world(rib,bodies[rib]['geometry'][0]['points_m'][-1])
            target=neutral_point('sternum',insertion(j,side)) if j<=7 else current[(j-1,side)][1]
            offset=m.mv(frames['T'+str(j)]['rotation'],m.scale([0,.001,-(.003 if j==7 else .001)],height))
            endpoint=max(endpoint,math.dist(g[0],tip)/height,math.dist(g[2],target)/height)
            midpoint=max(midpoint,math.dist(g[1],m.add(m.scale(m.add(g[0],g[2]),.5),offset))/height)
    return {'endpoint_h':endpoint,'midpoint_h':midpoint,'sc_h':sc}
