# SPDX-License-Identifier: Apache-2.0
"""Actual Blender scene mutations used by the pipeline fault tests."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from mathutils import Matrix,Vector
import bpy
from tools.blender_backend import SkeletonBackend,matrix
from tools.prepared import read_prepared,write_json

parser=argparse.ArgumentParser();parser.add_argument('--input',required=True);parser.add_argument('--output',required=True)
a=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);p=read_prepared(a.input);backend=SkeletonBackend(p)

def find(fixture,beat):
 return next(s for s in p['samples'] if s['fixture']==fixture and s['beat']['numerator']/s['beat']['denominator']==beat)

rows=[]
baseline={name:[v.co.copy() for v in obj.data.vertices] for name,obj in backend.meshes.items()}
for fault,fixture,beat in [('frozen-scapula','arm-raise',1),('frozen-patella','squat',2),('wrong-side-sign','sweep-hip-bilateral-adduction',3),('stretched-shank','neutral',0),('undeclared-world-root','neutral',0),('uniform-ribs','neutral',0),('bony-costal-arch','sweep-thoracic-flexion',3),('stale-cartilage-midpoint','sweep-thoracic-flexion',3),('former-squat','squat',2),('rearward-upper-body','squat',2)]:
 sample=find(fixture,beat)
 backend.apply_sample(sample)
 if fault=='former-squat':
  # The uv-side test prepares the deliberate old intent. Blender consumes
  # validated plain JSON only; it must not import PyYAML or JSON Schema.
  backend.apply_sample(sample|p['fault_samples']['former-squat'])
 elif fault=='rearward-upper-body':
  for id in ('skull','T6','L1','pelvis'):backend.targets[id].location.y-=.3
 elif fault=='frozen-scapula':
  body=backend.index['scapula.R'];backend.targets['scapula.R'].matrix_world=matrix({'position_m':body['origin_m'],'rotation':body['basis']})
 elif fault=='frozen-patella':
  body=backend.index['patella.R'];backend.targets['patella.R'].matrix_world=matrix({'position_m':body['origin_m'],'rotation':body['basis']})
 elif fault=='wrong-side-sign':
  frame=sample['frames']['femur.R'];body=backend.index['femur.R'];left=backend.index['femur.L']
  from tools import math3d as m
  action=m.mm(frame['rotation'],m.transpose(body['basis']))
  backend.targets['femur.L'].matrix_world=matrix({'position_m':sample['frames']['femur.L']['position_m'],'rotation':m.mm(action,left['basis'])})
 elif fault=='stretched-shank':backend.meshes['tibia.R.geometry.0'].scale=(1,1.1,1)
 elif fault=='undeclared-world-root':backend.world_root.location.x+=.01*backend.height
 elif fault=='uniform-ribs':
  from tools.geometry import primitive_mesh
  for name,obj in backend.meshes.items():
   if not name.startswith('rib.'):continue
   body=backend.index[obj['structure_id']];j=int(body['id'].split('.')[1]);sign=1 if '.R.' in name else -1
   widths=[.055,.065,.075,.080,.082,.082,.078,.072,.065,.055,.045,.035];w=widths[j-1]
   points=[[0,0,0],[sign*w,.020,-.008]]+([[sign*.65*w,.100,-.012]] if j<=10 else [])
   primitive={'type':'tube','points_m':[[v*backend.height for v in p] for p in points],'radius_m':.002*backend.height}
   vertices,_=primitive_mesh(primitive)
   for v,position in zip(obj.data.vertices,vertices):v.co=position
 elif fault in ('bony-costal-arch','stale-cartilage-midpoint'):
  from tools.geometry import primitive_mesh
  name='cartilage.8.R.geometry.0' if fault=='bony-costal-arch' else 'cartilage.7.R.geometry.0'
  points=[list(p) for p in sample['guides'][name]]
  if fault=='bony-costal-arch':
   rib=backend.index['rib.7.R'];tip=Vector(rib['geometry'][0]['points_m'][-1])
   world=matrix(sample['frames']['rib.7.R']) @ tip
   points[2]=list(matrix(sample['frames']['cartilage.8.R']).inverted() @ world)
  else:points[1]=backend.primitive_index[name]['points_m'][1]
  vertices,_=primitive_mesh(backend.primitive_index[name],points)
  for v,position in zip(backend.meshes[name].data.vertices,vertices):v.co=position
 bpy.context.view_layer.update()
 measured=backend.measure(sample)
 rows.append({'fault':fault,'expected_sample_id':sample['id'],'measurement':measured})
 # Undo independent fault before applying the next source sample.
 backend.meshes['tibia.R.geometry.0'].scale=(1,1,1)
 for name,points in baseline.items():
  for vertex,position in zip(backend.meshes[name].data.vertices,points):vertex.co=position
write_json(a.output,{'prepared_sha256':p['content_sha256'],'metadata':backend.metadata(),'faults':rows})
