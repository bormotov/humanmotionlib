# SPDX-License-Identifier: Apache-2.0
"""Factory-startup Blender construction from validated, prepared JSON."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from tools.prepared import read_prepared, write_json
from tools.blender_backend import SkeletonBackend


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--render-dir',type=Path,help='Internal review-pack fixed-camera PNG destination')
    parser.add_argument('--render-only',action='store_true',help='Build cleanly and render; full mesh measurements are a separate build')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    prepared=read_prepared(args.input)
    backend=SkeletonBackend(prepared)
    samples=[]
    rendered=[]
    for index,sample in enumerate(prepared['samples']):
        backend.apply_sample(sample)
        if not args.render_only:samples.append(backend.measure(sample))
        if args.render_dir:
            record={'id':sample['id'],'images':backend.render(sample,args.render_dir)}
            if sample['fixture']=='squat':record['balance_evidence']=backend.balance_evidence()
            rendered.append(record)
        if index%25==0:print(f"Sample {index+1}/{len(prepared['samples'])}: {sample['id']}",flush=True)
    args.output.mkdir(parents=True,exist_ok=True)
    write_json(args.output/'input.json',prepared)
    metadata=backend.metadata()
    if not args.render_only:write_json(args.output/'evaluated.json',{'format':'skeleton-evaluated/v1','prepared_sha256':prepared['content_sha256'],'samples':samples,'metadata':metadata})
    if not args.render_only:
        write_json(args.output/'geometry-reference.json',{
            'format':'skeleton-evaluated-geometry/v1','prepared_sha256':prepared['content_sha256'],
            'geometry':{name:{'structure':obj['structure_id'],'rigid':bool(obj['rigid']),
                              'vertices_m':backend.reference_local[name]}
                        for name,obj in sorted(backend.meshes.items())}})
    if args.render_dir:write_json(args.output/'render-manifest.json',{'prepared_sha256':prepared['content_sha256'],'samples':rendered,'metadata':metadata})
    write_json(args.output/'build-metadata.json',metadata)
    import bpy
    bpy.ops.wm.save_as_mainfile(filepath=str((args.output/'skeleton.blend').resolve()))
    print(f'Built {len(backend.carriers)} bodies and {len(backend.meshes)} meshes; measured {len(samples)} samples')


if __name__=='__main__':
    try:main()
    except Exception:
        import traceback
        traceback.print_exc()
        raise SystemExit(1)
