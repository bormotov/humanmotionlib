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

from humanmotionlib.prepared import content_hash, read_prepared_backend, write_json
from humanmotionlib.blender_backend import SkeletonBackend
from humanmotionlib.character_midpoints import validate_native_midpoint_samples as _validate_sealed_midpoint_samples
from humanmotionlib.character_paths import validate_managed_output_entries
from humanmotionlib.package_resources import verify_runtime_integrity
from humanmotionlib.runtime import (resolve_workspace_path, validate_operation_root,
                                    validate_run_root, validate_matrix_content_destination,
                                    workspace_root, backend_contract)


def phase(name, **details):
    print("HML_PHASE " + json.dumps({"phase": name, **details}, sort_keys=True), flush=True)


def _rest_binding_closure(profile, template):
    """Resolve the declared rest-binding ancestry using the prepared profile IDs."""
    structures = profile.get("structures")
    if not isinstance(structures, list):
        raise ValueError("character source hash closure has no prepared profile structures")
    by_id = {row.get("id"): row for row in structures if isinstance(row, dict)}
    seeds = template.get("rest_contract_structures")
    if not isinstance(seeds, list) or not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("character template has an invalid rest-contract binding closure")
    closure = set()
    for seed in seeds:
        current = seed
        visited = set()
        while current is not None:
            if current in visited:
                raise ValueError("cycle in character rest-contract binding closure")
            visited.add(current)
            row = by_id.get(current)
            if row is None:
                raise ValueError("unresolved structure in character rest-contract binding closure: " + str(current))
            closure.add(current)
            current = row.get("parent")
    return closure


def _validate_character_request_closure(request, prepared, read_resource):
    """Check exact descriptor/resource closure and surface carriers before scene construction."""
    ids = request.get("character_ids")
    descriptors = request.get("character_descriptors")
    records = request.get("characters")
    if (not isinstance(ids, list) or not isinstance(descriptors, list)
            or not isinstance(records, list)):
        raise ValueError("character source hash closure is malformed")
    surface_ids = [identifier for identifier in ids if identifier != "skeleton"]
    if [record.get("id") for record in records if isinstance(record, dict)] != surface_ids:
        raise ValueError("character source hash closure has missing or extra surface descriptors")
    if len(descriptors) != len(ids) or [row.get("id") for row in descriptors if isinstance(row, dict)] != ids:
        raise ValueError("character source hash closure has missing or reordered registry descriptors")
    profile = prepared.get("sources", {}).get("profile")
    if not isinstance(profile, dict):
        raise ValueError("character source hash closure has no trusted profile")
    structure_rows = profile.get("structures", [])
    bone_ids = {row.get("id") for row in structure_rows if isinstance(row, dict)}
    by_id = {row.get("id"): row for row in structure_rows if isinstance(row, dict)}
    record_by_id = {row["id"]: row for row in records if isinstance(row, dict) and isinstance(row.get("id"), str)}
    required_common = {"characters/registry.yaml",
                       "schema/character-registry.schema.json",
                       "schema/character-definition.schema.json"}
    declared_all = {}
    for descriptor in descriptors:
        identifier = descriptor["id"]
        if descriptor.get("profile_id") != profile.get("id"):
            raise ValueError("character descriptor profile does not match prepared profile")
        expected = set(required_common)
        expected.add(f"characters/definitions/{identifier}.yaml")
        kind = descriptor.get("renderer_kind")
        if identifier == "skeleton":
            if kind != "skeletal" or descriptor.get("template_id") is not None or descriptor.get("appearance_id") is not None:
                raise ValueError("skeleton descriptor unexpectedly selects a surface source")
        else:
            if kind != "skinned-surface":
                raise ValueError("surface character descriptor has an unsupported renderer")
            template_id, appearance_id = descriptor.get("template_id"), descriptor.get("appearance_id")
            if not isinstance(template_id, str) or not isinstance(appearance_id, str):
                raise ValueError("surface descriptor is missing template or appearance identity")
            expected.update({f"characters/templates/{template_id}.yaml",
                             f"characters/appearances/{appearance_id}.yaml",
                             f"rig/profiles/{profile['id']}.yaml",
                             "schema/character-template.schema.json",
                             "schema/character-appearance.schema.json"})
        source_hashes = descriptor.get("source_hashes")
        if not isinstance(source_hashes, dict) or set(source_hashes) != expected:
            raise ValueError(f"character source hash closure is incomplete or has extras for {identifier}")
        for logical, digest in source_hashes.items():
            if not isinstance(digest, str) or len(digest) != 64:
                raise ValueError("character source hash closure has an invalid digest")
            import hashlib
            if hashlib.sha256(read_resource(logical)).hexdigest() != digest:
                raise ValueError("character source hash mismatch: " + logical)
            if logical in declared_all and declared_all[logical] != digest:
                raise ValueError("character descriptors disagree about shared source hash: " + logical)
            declared_all[logical] = digest
        record = record_by_id.get(identifier)
        if identifier == "skeleton":
            if record is not None:
                raise ValueError("surface-free skeleton has an unexpected surface record")
            continue
        if not isinstance(record, dict) or record.get("source_hashes") != source_hashes:
            raise ValueError("character source hash closure differs between descriptor and surface record")
        definition = record.get("definition")
        if (not isinstance(definition, dict) or definition.get("id") != identifier
                or definition.get("renderer_kind") != kind
                or definition.get("profile_id") != profile.get("id")
                or definition.get("template_id") != descriptor.get("template_id")
                or definition.get("appearance_id") != descriptor.get("appearance_id")):
            raise ValueError("character source descriptor and embedded definition disagree")
        template, appearance = record.get("template"), record.get("appearance")
        if (not isinstance(template, dict) or template.get("id") != descriptor.get("template_id")
                or template.get("compatible_profile") != profile.get("id")
                or not isinstance(appearance, dict) or appearance.get("id") != descriptor.get("appearance_id")):
            raise ValueError("character source descriptor and embedded template/preset disagree")
        bound_structures = _rest_binding_closure(profile, template)

        references = set()
        def visit_weighting(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in {"carrier", "from", "to", "hand_carrier"}:
                        if not isinstance(child, str) or child not in bone_ids:
                            raise ValueError("unresolved character skinning carrier: " + str(child))
                        references.add(child)
                    elif key == "carriers":
                        if (not isinstance(child, list) or
                                any(not isinstance(item, str) or item not in bone_ids for item in child)):
                            raise ValueError("unresolved character skinning carrier list")
                        references.update(child)
                    visit_weighting(child)
            elif isinstance(value, list):
                for child in value:
                    visit_weighting(child)
        components = template.get("components")
        if not isinstance(components, list):
            raise ValueError("character surface template has no component inventory")
        for component in components:
            if not isinstance(component, dict) or not isinstance(component.get("weighting"), dict):
                raise ValueError("character surface template has malformed weighting data")
            visit_weighting(component["weighting"])
        if not references.issubset(bound_structures):
            raise ValueError("character skinning carriers are outside the bound rest closure")
        if not isinstance(record.get("surface_sha256"), str) or len(record["surface_sha256"]) != 64:
            raise ValueError("character surface identity is malformed")
    expected_surface_ids = surface_ids
    identities = request.get("surface_identities")
    if (not isinstance(identities, dict) or list(sorted(identities)) != sorted(expected_surface_ids)
            or any(identities.get(identifier) != record_by_id[identifier].get("surface_sha256")
                   for identifier in expected_surface_ids)):
        raise ValueError("character surface descriptor identity mismatch")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--render-dir',type=Path,help='Internal review-pack fixed-camera PNG destination')
    parser.add_argument('--render-only',action='store_true',help='Build cleanly and render; full mesh measurements are a separate build')
    parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('--owner-run',type=Path,help=argparse.SUPPRESS)
    parser.add_argument('--matrix-element-root',type=Path,help=argparse.SUPPRESS)
    parser.add_argument('--expected-prepared-sha256', required=True,
                        help=argparse.SUPPRESS)
    parser.add_argument('--characters', nargs='+', default=['skeleton'])
    parser.add_argument('--expected-render-identity', help=argparse.SUPPRESS)
    parser.add_argument('--character-request', type=Path, help=argparse.SUPPRESS)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    workspace=workspace_root(args.workspace)
    input_path=resolve_workspace_path(args.input,workspace)
    if input_path.is_dir():
        input_root=input_path
        input_path=input_path/'input.json'
    else:
        input_root=input_path.parent
    if args.matrix_element_root is not None:
        if '..' in Path(args.output).parts:
            raise ValueError('matrix content root cannot contain traversal components')
        if args.render_dir is not None and '..' in Path(args.render_dir).parts:
            raise ValueError('matrix render directory cannot contain traversal components')
    output_operand=Path(args.output)
    if args.matrix_element_root is None:
        output_operand=resolve_workspace_path(output_operand,workspace)
    if args.matrix_element_root is not None:
        if args.owner_run is not None:
            raise ValueError('matrix element binding cannot be combined with --owner-run')
        matrix_operand=Path(args.matrix_element_root)
        if not matrix_operand.is_absolute() or '..' in matrix_operand.parts:
            raise ValueError('matrix element root must be an absolute canonical path')
        matrix_element=validate_run_root(matrix_operand,workspace)
        if matrix_operand != matrix_element:
            raise ValueError('matrix element root must be canonical and non-symlinked')
        matrix_element,output,_relative=validate_matrix_content_destination(
            output_operand,matrix_element,workspace,operation='render')
        owner=output
    else:
        output=validate_operation_root(output_operand,workspace,args.owner_run)
        owner=validate_run_root(args.owner_run,workspace) if args.owner_run is not None else output
    render_dir=resolve_workspace_path(args.render_dir,workspace) if args.render_dir else None
    if args.matrix_element_root is not None:
        if input_root == output or input_root.is_relative_to(output) or output.is_relative_to(input_root):
            raise ValueError('prepared input and matrix output content roots must be disjoint')
    elif input_root != owner and (input_root.is_relative_to(owner) or owner.is_relative_to(input_root)):
        raise ValueError('prepared input and output runs must be disjoint or share the designated run root')
    if render_dir is not None and not render_dir.is_relative_to(output):
        raise ValueError('render directory must stay inside the output run')
    if args.matrix_element_root is not None and render_dir is not None and render_dir != output / 'frames':
        raise ValueError('matrix render directory must be the declared output frames directory')
    if output.exists():
        allowed = {'processes'}
        if input_root == owner == output:
            allowed.add('input.json')
        if args.character_request is not None:
            allowed.add('character-render-request.json')
        unexpected = [item.name for item in output.iterdir() if item.name not in allowed]
        if unexpected:
            raise ValueError('backend output run is occupied: ' + ', '.join(sorted(unexpected)))
        validate_managed_output_entries(output, allowed)
    stale_names = ['build-metadata.json', 'skeleton.blend']
    if not args.render_only:
        stale_names.extend(('evaluated.json', 'geometry-reference.json'))
    if render_dir is not None:
        stale_names.append('render-manifest.json')
    stale = [name for name in stale_names if (output / name).exists()]
    if stale:
        raise ValueError('backend output files already exist: ' + ', '.join(stale))
    if render_dir is not None and render_dir.exists() and any(render_dir.iterdir()):
        raise ValueError('backend render directory is occupied')
    phase('script_started')
    manifest=verify_runtime_integrity()
    phase('package_verified', version=manifest['version'], resource_count=len(manifest['resources']))
    prepared=read_prepared_backend(input_path, args.expected_prepared_sha256)
    phase('input_loaded', prepared_sha256=prepared['content_sha256'], sample_count=len(prepared['samples']))
    character_request = None
    if args.character_request is not None:
        request_path=resolve_workspace_path(args.character_request,workspace)
        if request_path.parent != output or not args.expected_render_identity:
            raise ValueError('character render request is not sealed in its output run')
        character_request=json.loads(request_path.read_text())
        request_identity=character_request.pop('render_identity',None)
        if content_hash(character_request) != request_identity or request_identity != args.expected_render_identity:
            raise ValueError('character render request identity mismatch')
        if character_request.get('prepared_sha256') != prepared['content_sha256']:
            raise ValueError('character render request names a different prepared input')
        if character_request.get('character_ids') != args.characters:
            raise ValueError('character render request selection mismatch')
        if character_request.get('package_identity') != prepared.get('package_identity'):
            raise ValueError('character render request package identity mismatch')
        if character_request.get('backend_contract') != backend_contract():
            raise ValueError('character render request backend contract mismatch')
        descriptors=character_request.get('character_descriptors',[])
        if [item.get('id') for item in descriptors]!=args.characters:
            raise ValueError('character render request descriptor inventory mismatch')
        from humanmotionlib.package_resources import read_bytes
        _validate_character_request_closure(character_request, prepared, read_bytes)
        character_request['render_identity']=request_identity
    elif args.expected_render_identity is not None or args.characters != ['skeleton']:
        raise ValueError('character request and render identity are required for nondefault selection')
    else:
        character_request={'character_ids':['skeleton'],'render_identity':None}
    backend=SkeletonBackend(prepared, characters=args.characters, character_request=character_request)
    phase('backend_ready', prepared_sha256=prepared['content_sha256'],
          render_identity=(character_request.get('render_identity') if character_request else None),
          character_ids=args.characters)
    samples=[]
    rendered=[]
    rendered_by_character={identifier:[] for identifier in args.characters}
    surface_references={}
    surface_evaluated={}
    surface_midpoints={}
    if not args.render_only:
        for character_id in backend.surface_sources:
            surface_references[character_id]=backend.surface_reference_record(
                character_id,prepared['content_sha256'],character_request.get('render_identity'))
            surface_evaluated[character_id]=[]
            surface_midpoints[character_id]=[]
    for index,sample in enumerate(prepared['samples']):
        backend.apply_sample(sample)
        if not args.render_only:samples.append(backend.measure(sample))
        if not args.render_only:
            for character_id in backend.surface_sources:
                surface_evaluated[character_id].append(backend.measure_surface(character_id,sample))
        if args.render_dir:
            for character_id in args.characters:
                record={'id':sample['id'],'images':backend.render(sample,render_dir,character_id)}
                if character_id=='skeleton' and sample['fixture']=='squat':
                    record['balance_evidence']=backend.balance_evidence()
                rendered_by_character[character_id].append(record)
                if character_id=='skeleton':rendered.append(record)
        if index%25==0 or index+1==len(prepared['samples']):
            phase('samples_progress', sample_id=sample['id'], index=index+1, count=len(prepared['samples']))
    if not args.render_only and surface_midpoints:
        dense_samples=_validate_sealed_midpoint_samples(
            prepared,character_request.get('native_midpoint_samples'))
        midpoint_count=0
        for dense_sample in dense_samples:
            backend.apply_sample(dense_sample)
            for character_id in backend.surface_sources:
                surface_midpoints[character_id].append(backend.measure_surface(character_id,dense_sample))
            midpoint_count+=1
            if midpoint_count%25==0:
                phase('surface_midpoint_progress',sample_id=dense_sample['id'],
                      index=midpoint_count,count=None)
        phase('surface_midpoints_complete',sample_count=midpoint_count)
        # Keep the saved scene at the legacy final delivered pose; midpoint
        # audit samples are evidence-only and must not leak into the project scene.
        if prepared['samples']:
            backend.apply_sample(prepared['samples'][-1])
    output.mkdir(parents=True,exist_ok=True)
    write_json(output/'input.json',prepared)
    metadata=backend.metadata()
    metadata.update({'character_ids':args.characters,
                     'render_identity':character_request.get('render_identity') if character_request else None})
    if not args.render_only:write_json(output/'evaluated.json',{'format':'skeleton-evaluated/v1','prepared_sha256':prepared['content_sha256'],'samples':samples,'metadata':metadata})
    if not args.render_only:
        write_json(output/'geometry-reference.json',{
            'format':'skeleton-evaluated-geometry/v1','prepared_sha256':prepared['content_sha256'],
            'geometry':{name:{'structure':obj['structure_id'],'rigid':bool(obj['rigid']),
                              'vertices_m':backend.reference_local[name]}
                        for name,obj in sorted(backend.meshes.items())}})
        for character_id,record in surface_references.items():
            character_root=output/'characters'/character_id
            write_json(character_root/'surface-reference.json',record)
            write_json(character_root/'surface-evaluated.json',{
                'format':'hml-surface-evaluated/v1','prepared_sha256':prepared['content_sha256'],
                'render_identity':metadata.get('render_identity'),'character_id':character_id,
                'reference_metric':'canonical-double-world-dq/v1',
                'native_local_debug_metric':'blender-local-dq/v1',
                'samples':surface_evaluated[character_id],
                'dense_samples':surface_midpoints[character_id]})
    if render_dir:
        if args.characters==['skeleton']:
            manifest={'prepared_sha256':prepared['content_sha256'],'render_identity':metadata['render_identity'],
                      'samples':rendered,'metadata':metadata}
        else:
            manifest={'format':'character-render-manifest/v1',
                      'prepared_sha256':prepared['content_sha256'],
                      'render_identity':metadata['render_identity'],
                      'characters':[{'id':identifier,'samples':rendered_by_character[identifier]}
                                    for identifier in args.characters],
                      'metadata':metadata}
        write_json(output/'render-manifest.json',manifest)
    write_json(output/'build-metadata.json',metadata)
    phase('outputs_written', prepared_sha256=prepared['content_sha256'])
    import bpy
    bpy.ops.wm.save_as_mainfile(filepath=str((output/'skeleton.blend').resolve()))
    phase('script_complete', prepared_sha256=prepared['content_sha256'],
          render_identity=metadata.get('render_identity'),character_ids=args.characters,
          body_count=len(backend.carriers),
          mesh_count=len(backend.meshes), measured_sample_count=len(samples))


if __name__=='__main__':
    try:main()
    except Exception:
        import traceback
        traceback.print_exc()
        raise SystemExit(1)
