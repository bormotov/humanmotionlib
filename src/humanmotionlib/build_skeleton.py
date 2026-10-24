# SPDX-License-Identifier: Apache-2.0
"""Factory-startup Blender construction from validated, prepared JSON."""

import argparse
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True


def _load_installed_package():
    """Load only the installed HML package, without adding site-packages to sys.path."""
    package_directory = Path(__file__).resolve().parent
    initializer = package_directory / "__init__.py"
    existing = sys.modules.get("humanmotionlib")
    if existing is not None:
        existing_file = getattr(existing, "__file__", None)
        if existing_file and Path(existing_file).resolve() == initializer:
            return existing
        raise ImportError("a conflicting humanmotionlib package is already loaded in Blender")
    spec = importlib.util.spec_from_file_location(
        "humanmotionlib", initializer, submodule_search_locations=[str(package_directory)]
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load installed humanmotionlib package from {initializer}")
    package = importlib.util.module_from_spec(spec)
    sys.modules["humanmotionlib"] = package
    try:
        spec.loader.exec_module(package)
    except BaseException:
        del sys.modules["humanmotionlib"]
        raise
    return package


_load_installed_package()

from humanmotionlib.prepared import read_prepared, write_json
from humanmotionlib.blender_backend import SkeletonBackend
from humanmotionlib.package_resources import verify_runtime_integrity


def phase(name, **details):
    print("HML_PHASE " + json.dumps({"phase": name, **details}, sort_keys=True), flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--render-dir',type=Path,help='Internal review-pack fixed-camera PNG destination')
    parser.add_argument('--render-only',action='store_true',help='Build cleanly and render; full mesh measurements are a separate build')
    parser.add_argument('--workspace',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    phase('script_started')
    manifest=verify_runtime_integrity()
    phase('package_verified', version=manifest['version'], resource_count=len(manifest['resources']))
    prepared=read_prepared(args.input)
    phase('input_loaded', prepared_sha256=prepared['content_sha256'], sample_count=len(prepared['samples']))
    backend=SkeletonBackend(prepared)
    phase('backend_ready', prepared_sha256=prepared['content_sha256'])
    samples=[]
    rendered=[]
    for index,sample in enumerate(prepared['samples']):
        backend.apply_sample(sample)
        if not args.render_only:samples.append(backend.measure(sample))
        if args.render_dir:
            record={'id':sample['id'],'images':backend.render(sample,args.render_dir)}
            if sample['fixture']=='squat':record['balance_evidence']=backend.balance_evidence()
            rendered.append(record)
        if index%25==0 or index+1==len(prepared['samples']):
            phase('samples_progress', sample_id=sample['id'], index=index+1, count=len(prepared['samples']))
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
    phase('outputs_written', prepared_sha256=prepared['content_sha256'])
    import bpy
    bpy.ops.wm.save_as_mainfile(filepath=str((args.output/'skeleton.blend').resolve()))
    phase('script_complete', prepared_sha256=prepared['content_sha256'], body_count=len(backend.carriers),
          mesh_count=len(backend.meshes), measured_sample_count=len(samples))


if __name__=='__main__':
    try:main()
    except Exception:
        import traceback
        traceback.print_exc()
        raise SystemExit(1)
