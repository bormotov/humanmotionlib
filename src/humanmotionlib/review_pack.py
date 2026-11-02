# SPDX-License-Identifier: Apache-2.0
"""Two clean fixed-camera render passes and a linked visual/numeric review pack."""

import argparse
from fractions import Fraction
import hashlib
import html
import json
import math
from pathlib import Path
import shutil
import sys

from PIL import Image,ImageChops,ImageDraw,ImageOps
from humanmotionlib import math3d as m
from humanmotionlib.prepared import read_prepared,write_json
from humanmotionlib.review_graphics import gif,label,onion,sheet
from humanmotionlib.package_resources import manifest_sha256, read_text, verify_runtime_integrity
from humanmotionlib.render_contract import (expected_views as _expected_views,
                                            _receipt_files_unchanged,
                                            _validate_matrix_receipt_relocation,
                                            read_supervised_receipt as _read_supervised_receipt,
                                            validate_manifest as _validate_manifest)
from humanmotionlib.runtime import (DEFAULT_RENDER_TIMEOUT, DEFAULT_SLOT_TIMEOUT, InvocationError,
                           resolve_workspace_path, validate_existing_run_root,
                           validate_matrix_content_root, validate_run_root, validate_timeout,
                           workspace_root)


def decoded_digest(path):
    with Image.open(path) as image:
        image=image.convert('RGBA')
        return hashlib.sha256(str(image.size).encode()+image.tobytes()).hexdigest()


def _review_output_root(output, workspace, matrix_element_root=None):
    workspace = workspace_root(workspace)
    output_operand = Path(output)
    if ".." in output_operand.parts:
        raise ValueError("review-pack output cannot contain traversal components")
    output_path = resolve_workspace_path(output_operand, workspace)
    if matrix_element_root is None:
        return validate_run_root(output_path, workspace)
    element = validate_run_root(resolve_workspace_path(matrix_element_root, workspace), workspace)
    return validate_matrix_content_root(output_path, element, workspace,
                                        relative_path="presentation")


def render_pass(input_path, output, frames, *, timeout_seconds=DEFAULT_RENDER_TIMEOUT,
                slot_timeout_seconds=DEFAULT_SLOT_TIMEOUT, workspace=None, owner_run=None,
                matrix_destination=None):
    # Keep both standalone renders and owner-managed passes on the public API's
    # validated request path. Managed passes must be claimed by that API before
    # the supervisor probes Blender.
    validate_timeout(timeout_seconds)
    validate_timeout(slot_timeout_seconds, 'slot_timeout_seconds')
    workspace = workspace_root(workspace)
    input_path = resolve_workspace_path(input_path, workspace)
    output = resolve_workspace_path(output, workspace)
    frames = resolve_workspace_path(frames, workspace)
    if Path(output).exists():
        raise ValueError(f"Render pass output must be a fresh path: {output}")
    from humanmotionlib import api
    if matrix_destination is not None:
        api.render(input_path, workspace=workspace, output=output, images=True,
                   render_dir=frames, render_only=True,
                   timeout_seconds=timeout_seconds, slot_timeout_seconds=slot_timeout_seconds,
                   matrix_destination=matrix_destination)
    elif owner_run is None:
        api.render(input_path, workspace=workspace, output=output, images=True,
                   render_dir=frames, render_only=True,
                   timeout_seconds=timeout_seconds, slot_timeout_seconds=slot_timeout_seconds)
    else:
        api._render_owned_pass(input_path, workspace=workspace, output=output,
                               owner_run=owner_run, images=True,
                               render_dir=frames, render_only=True,
                               timeout_seconds=timeout_seconds,
                               slot_timeout_seconds=slot_timeout_seconds)
    prepared = read_prepared(input_path)
    # Treat a freshly completed pass exactly like a pass selected for reuse:
    # this also verifies the sealed request and its membership in the complete
    # receipt inventory, in addition to the legacy image/manifest checks.
    return reuse_render_pass(input_path, output, prepared, workspace=workspace)


def reuse_render_pass(input_path, output, prepared, *, workspace=None):
    manifest_path = output / 'render-manifest.json'
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Missing or malformed render manifest: {manifest_path}") from error
    required_paths = _validate_manifest(manifest, prepared, output / 'frames', output=output)
    request_path = output / 'character-render-request.json'
    metadata_path = output / 'build-metadata.json'
    process_root = output / 'processes'
    if process_root.is_symlink() or not process_root.is_dir():
        raise ValueError(f"Expected a nonsymlink supervised process directory in {output}")
    process_dirs = list(process_root.iterdir())
    if any(path.is_symlink() or not path.is_dir() for path in process_dirs):
        raise ValueError(f"Supervised process inventory is invalid in {output}")
    receipt_paths = [path / 'outcome.json' for path in process_dirs if (path / 'outcome.json').exists()]
    if len(receipt_paths) != len(process_dirs) or any(path.is_symlink() for path in receipt_paths):
        raise ValueError(f"Expected one nonsymlink outcome receipt per supervised process in {output}")
    try:
        metadata = json.loads(metadata_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Missing or malformed render identity evidence: {output}") from error
    render_receipts = []
    probe_receipts = []
    for receipt_path in receipt_paths:
        try:
            candidate = json.loads(receipt_path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Unreadable supervised receipt: {receipt_path}") from error
        operation = candidate.get('operation')
        if operation == 'render-pass':
            render_receipts.append((receipt_path, candidate))
        elif operation == 'version-probe':
            probe_receipts.append((receipt_path, candidate))
        else:
            raise ValueError(f"Unexpected supervised operation in reusable pass: {receipt_path}")
    if len(render_receipts) != 1 or len(probe_receipts) > 1:
        raise ValueError(
            f"Expected one render-pass and at most one version-probe receipt in {output}; "
            f"found {len(render_receipts)} render-pass and {len(probe_receipts)} version-probe receipts")
    receipt_path, receipt = render_receipts[0]
    phases = receipt.get('phases', [])
    sealed_markers = (manifest.get('render_identity') is not None
                      or metadata.get('render_identity') is not None
                      or any(isinstance(phase, dict) and phase.get('render_identity') is not None
                             for phase in phases))
    if sealed_markers and len(probe_receipts) != 1:
        raise ValueError(f"Sealed pass requires exactly one version-probe receipt: {output}")
    if probe_receipts:
        probe_path, probe = probe_receipts[0]
        _validate_matrix_receipt_relocation(probe, output)
        package = verify_runtime_integrity()
        identity = {
            'package_version': package['version'],
            'runtime_manifest_sha256': manifest_sha256(),
            'resource_hashes': package['resources'],
            'backend_contract_sha256': package['backend_contract'],
            'implementation_hashes': package['implementation'],
        }
        backend = probe.get('backend_identity')
        validation = probe.get('output_validation', {})
        if (any(probe.get(key) != value for key, value in identity.items())
                or probe.get('state') != 'succeeded' or probe.get('outcome') != 'exit'
                or probe.get('return_code') != 0
                or probe.get('operation_root') != str(output.resolve())
                or validation.get('status') != 'not-required'
                or validation.get('files') not in (None, [])):
            raise ValueError(f"Version-probe receipt is failed, stale, or inconsistent: {probe_path}")
        if (not isinstance(backend, dict)
                or metadata.get('blender_version') != backend.get('version')
                or metadata.get('blender_build') != backend.get('build_hash')):
            raise ValueError(f"Version-probe backend identity does not match render metadata: {probe_path}")
    if request_path.is_symlink():
        raise ValueError(f"Sealed render request must not be a symlink: {request_path}")
    if request_path.exists():
        if not request_path.is_file():
            raise ValueError(f"Sealed render request is not a regular file: {request_path}")
        from humanmotionlib import api
        workspace = workspace_root(workspace)
        expected_request = api._expected_render_request(
            input_path, workspace=workspace, characters=('skeleton',), render_only=True)
        try:
            observed_request = json.loads(request_path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Sealed render request is unreadable: {request_path}") from error
        if observed_request != expected_request:
            raise ValueError(f"Sealed render request does not match the selected skeleton render: {request_path}")
        expected_identity = expected_request['render_identity']
        if (manifest.get('render_identity') != expected_identity
                or metadata.get('render_identity') != expected_identity
                or not any(isinstance(phase, dict) and phase.get('phase') == 'script_complete'
                           and phase.get('render_identity') == expected_identity
                           and phase.get('character_ids') == ['skeleton'] for phase in phases)):
            raise ValueError(f"Sealed render identity evidence is inconsistent: {output}")
        required_paths.append(Path('character-render-request.json'))
    elif sealed_markers:
        raise ValueError(f"Sealed render request is missing from a sealed pass: {output}")
    checked_receipt = _read_supervised_receipt(output, prepared, required_paths)
    if request_path.exists() and not any(
            phase.get('phase') == 'script_complete'
            and phase.get('render_identity') == expected_request['render_identity']
            and phase.get('character_ids') == ['skeleton']
            for phase in checked_receipt.get('phases', []) if isinstance(phase, dict)):
        raise ValueError(f"Sealed render receipt identity is inconsistent: {output}")
    return manifest


def _preflight_reuse_pack(input_path, output, prepared, *, workspace=None):
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
    legacy_pass_names = {
        'build-metadata.json', 'frames', 'input.json', 'processes',
        'render-manifest.json', 'skeleton.blend',
    }
    sealed_pass_names = legacy_pass_names | {'character-render-request.json'}
    for name in ('clean-a', 'clean-b'):
        directory = output / name
        entries = {path.name for path in directory.iterdir()}
        if entries not in (legacy_pass_names, sealed_pass_names) or any(path.is_symlink() for path in directory.iterdir()):
            raise ValueError(f"Reusable render pass has unexpected or missing content: {directory}")
        pass_input = directory / 'input.json'
        if not pass_input.is_file() or pass_input.read_bytes() != selected_bytes:
            raise ValueError(f"Reusable render pass input does not match the selected build input: {pass_input}")
        for path in directory.rglob('*'):
            if path.is_symlink():
                raise ValueError(f"Reusable render pass contains a symlink: {path}")
        passes.append(reuse_render_pass(input_path, directory, prepared, workspace=workspace))
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


_CHARACTER_LABELS = {"skeleton": "Skeleton", "male": "Male", "female": "Female"}
_JOINT_CENTER_IDS = (
    "clavicle.R", "humerus.R", "elbow.R", "wrist.R", "pelvis", "femur.R", "knee.R",
    "talus.R", "mtp.R", "clavicle.L", "humerus.L", "elbow.L", "wrist.L", "femur.L",
    "knee.L", "talus.L", "mtp.L",
)


def _character_sample_rows(manifest, character_ids, expected_sample_ids):
    """Return a complete ordered character/sample manifest or fail closed."""
    ids = tuple(character_ids)
    if ids == ("skeleton",) and "samples" in manifest:
        members = [{"id": "skeleton", "samples": manifest.get("samples")}]
    else:
        if manifest.get("format") != "character-render-manifest/v1":
            raise ValueError("Selected character render manifest is missing or unsupported")
        members = manifest.get("characters")
        if not isinstance(members, list) or [row.get("id") for row in members
                                                if isinstance(row, dict)] != list(ids):
            raise ValueError("Character review pack member inventory is incomplete or reordered")
    result = {}
    for member in members:
        identifier = member.get("id")
        rows = member.get("samples")
        if identifier not in ids or not isinstance(rows, list):
            raise ValueError(f"Malformed character sample inventory: {identifier!r}")
        if [row.get("id") for row in rows if isinstance(row, dict)] != list(expected_sample_ids):
            raise ValueError(f"Character {identifier} has missing, extra, or reordered samples")
        result[identifier] = rows
    if tuple(result) != ids:
        raise ValueError("Character review pack selection is incomplete")
    return result


def _character_images(manifest, frame_root, prepared, character_ids):
    sample_ids = [sample["id"] for sample in prepared["samples"]]
    members = _character_sample_rows(manifest, character_ids, sample_ids)
    images = {}
    for identifier, rows in members.items():
        images[identifier] = {}
        for sample, row in zip(prepared["samples"], rows):
            paths = row.get("images")
            expected = (_expected_views(prepared, sample) if identifier == "skeleton" else
                        ({"front", "side", "rear"} if sample["fixture"] in ("neutral", "rest")
                         else {"front", "side"}))
            if not isinstance(paths, dict) or set(paths) != set(expected):
                raise ValueError(f"Character {identifier}/{sample['id']} has incomplete view inventory")
            resolved = {}
            for view, relative in paths.items():
                if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts:
                    raise ValueError(f"Unsafe character image path: {identifier}/{sample['id']}/{view}")
                image_path = (frame_root / relative).resolve()
                try:
                    image_path.relative_to(frame_root.resolve())
                except ValueError as error:
                    raise ValueError(f"Character image escapes its frame root: {relative}") from error
                if not image_path.is_file() or image_path.stat().st_size == 0:
                    raise ValueError(f"Missing character image: {identifier}/{sample['id']}/{view}")
                try:
                    with Image.open(image_path) as decoded:
                        decoded.verify()
                except (OSError, ValueError) as error:
                    raise ValueError(f"Unreadable character image: {identifier}/{sample['id']}/{view}") from error
                resolved[view] = image_path
            images[identifier][sample["id"]] = resolved
    return images


def _character_grid(images_by_character, records, view, output, *, title, columns):
    """Create labeled rows with one column per selected character and no resampling of time."""
    cell = 300
    header = 64
    row_height = cell + 36
    canvas = Image.new("RGB", (cell * len(columns), header + row_height * len(records)), (245, 247, 248))
    for col, identifier in enumerate(columns):
        label(canvas, _CHARACTER_LABELS[identifier], (col * cell + 8, 32), scale=2)
    label(canvas, title, (8, 4), scale=1, color=(20, 70, 95))
    for index, record in enumerate(records):
        row_y = header + index * row_height
        beat = record.get("beat", {})
        caption = f"{record.get('sample_id')} / beat {beat.get('numerator')}/{beat.get('denominator')}"
        label(canvas, caption, (8, row_y + cell + 6), scale=1)
        for col, identifier in enumerate(columns):
            sample_id = record["sample_id"]
            path = images_by_character[identifier][sample_id].get(view)
            if path is None:
                raise ValueError(f"Missing {view} image for {identifier}/{sample_id}")
            with Image.open(path) as source:
                tile = ImageOps.pad(source.convert("RGB"), (cell, cell),
                                    method=Image.Resampling.LANCZOS, color=(245, 247, 248))
            canvas.paste(tile, (col * cell, row_y))
    canvas.save(output)
    return output


def _character_plan_coverage(prepared):
    """Report the design's required beat/sample coverage without inventing rows."""
    required = {"arm-raise": (5, 17), "squat": (5, 17), "walking-in-place": (9, 33)}
    by_fixture = prepared.get("sampling", {})
    coverage = {}
    missing = []
    for fixture, expected_counts in required.items():
        plans = by_fixture.get(fixture, [])
        plan = next((item for item in plans if item.get("bpm") == 90), None)
        if plan is None:
            missing.append(f"{fixture}@90bpm")
            continue
        actual = (len(plan.get("static", [])), len(plan.get("animation", [])))
        coverage[fixture] = {"static": actual[0], "animation": actual[1],
                             "status": "pass" if actual == expected_counts else "fail"}
        if actual != expected_counts:
            missing.append(f"{fixture}@90bpm expected {expected_counts}, found {actual}")
    rocker = by_fixture.get("forefoot-rocker", [])
    rocker_plan = next((item for item in rocker if item.get("bpm") == 90), None)
    if rocker_plan is None or not rocker_plan.get("animation"):
        missing.append("forefoot-rocker@90bpm animation samples")
    for fixture in ("neutral", "rest"):
        records = [sample for sample in prepared.get("samples", []) if sample.get("fixture") == fixture]
        if not records:
            missing.append(f"{fixture} sample")
    sweep_ids = ("sweep-shoulder-bilateral-elevation", "sweep-shoulder-bilateral-plane",
                 "sweep-shoulder-bilateral-external_twist", "sweep-forearm-bilateral-pronation",
                 "sweep-knee-bilateral-flexion")
    for fixture in sweep_ids:
        plans = by_fixture.get(fixture, [])
        if not any(item.get("bpm") == 90 and item.get("animation") for item in plans):
            missing.append(f"{fixture}@90bpm animation")
    return {"status": "pass" if not missing else "incomplete", "coverage": coverage,
            "missing": missing}


def _sample_records_for_plan(plan, fixture, mode, sample_lookup):
    records = plan.get(mode)
    if not isinstance(records, list) or not records:
        raise ValueError(f"Review pack is missing {fixture}@{plan.get('bpm')} {mode} samples")
    result = []
    for record in records:
        sample_id = record.get("sample_id")
        sample = sample_lookup.get(sample_id)
        if sample is None or sample.get("fixture") != fixture:
            raise ValueError(f"Review pack {fixture} plan references a missing or foreign sample {sample_id!r}")
        beat = record.get("beat")
        if not isinstance(beat, dict) or not {"numerator", "denominator"} <= set(beat):
            raise ValueError(f"Review pack {fixture}/{mode} sample has no exact beat")
        result.append({"sample_id": sample_id, "beat": beat})
    return result


def _annotate_joint_centers(image_path, sample, camera, output, *, height_m):
    """Overlay a fixed set of shared rest/posed centers and actual contact anchors."""
    expected = _JOINT_CENTER_IDS
    frames = sample.get("frames", {})
    absent = [identifier for identifier in expected if identifier not in frames]
    if absent:
        raise ValueError("Joint-center overlay lacks prepared structures: " + ", ".join(absent))
    with Image.open(image_path) as source:
        canvas = source.convert("RGB")
    draw = ImageDraw.Draw(canvas)
    resolution = canvas.width
    radius = max(3, round(height_m * resolution * 0.004))
    for identifier in expected:
        xy = project(frames[identifier]["position_m"], camera, resolution)
        x, y = round(xy[0]), round(xy[1])
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=(235, 30, 170), outline=(20, 20, 20))
    for contact in sample.get("contacts", []):
        for anchor in contact.get("targets_m", []):
            xy = project(anchor, camera, resolution)
            x, y = round(xy[0]), round(xy[1])
            draw.ellipse((x-5, y-5, x+5, y+5), fill=(255, 205, 20), outline=(15, 15, 15))
    label(canvas, "SHARED JOINT CENTERS / CONTACT TARGETS", (8, 8), scale=1)
    canvas.save(output)
    return output


def _sole_crop(image_path, output, caption):
    """Make a fixed pixel inspection crop from the original render, with no camera change."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(image_path) as source:
        image = source.convert("RGB")
    width, height = image.size
    crop = image.crop((round(width * 0.20), round(height * 0.56),
                       round(width * 0.80), height))
    canvas = Image.new("RGB", (crop.width, crop.height + 28), (245, 247, 248))
    canvas.paste(crop, (0, 28))
    label(canvas, caption, (5, 5), scale=1)
    canvas.save(output)
    return output


def _read_evaluated_candidate(run_root, *, matrix_mode=False):
    input_path = run_root / "prepared" / "input.json" if matrix_mode else run_root / "input.json"
    if not input_path.is_file() or input_path.is_symlink():
        raise ValueError(f"Candidate comparison run has no safe input.json: {run_root}")
    prepared = read_prepared(input_path)
    evaluated_path = run_root / "render" / "evaluated.json" if matrix_mode else run_root / "evaluated.json"
    if not evaluated_path.is_file() or evaluated_path.is_symlink():
        raise ValueError(f"Candidate comparison run has no evaluated.json: {run_root}")
    try:
        evaluated = json.loads(evaluated_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Candidate evaluated evidence is unreadable: {evaluated_path}") from error
    if evaluated.get("prepared_sha256") != prepared["content_sha256"]:
        raise ValueError(f"Candidate evaluated evidence is stale: {evaluated_path}")
    if [row.get("id") for row in evaluated.get("samples", [])] != [row["id"] for row in prepared["samples"]]:
        raise ValueError(f"Candidate evaluated sample inventory differs from input: {evaluated_path}")
    return prepared


def _stature_comparison_inputs(specifications, primary, output, workspace, *, matrix_mode=False):
    """Preflight caller-supplied H=1.50/1.90 candidate runs before any output write."""
    primary_height = float(primary["sources"]["profile"]["stature_m"])
    known = (1.50, 1.70, 1.90)
    if abs(primary_height - 1.70) > 1e-9:
        raise ValueError("The complete character comparison pack primary input must use H=1.70m")
    resolved = {1.70: {"run_root": None, "prepared": primary}}
    for specification in specifications:
        if not isinstance(specification, str) or "=" not in specification:
            raise ValueError("--stature-input must use H=RUN form")
        label_value, run_value = specification.split("=", 1)
        try:
            height = float(label_value)
        except ValueError as error:
            raise ValueError(f"Invalid stature label in --stature-input: {label_value!r}") from error
        if not math.isfinite(height) or height not in known or not run_value:
            raise ValueError(f"Unsupported or malformed --stature-input height: {label_value!r}")
        if height == 1.70:
            raise ValueError("H=1.70 is already supplied by --input; duplicate stature inputs are invalid")
        if height in resolved:
            raise ValueError(f"Duplicate --stature-input for H={height:.2f}m")
        input_operand = resolve_workspace_path(Path(run_value), workspace)
        if matrix_mode and input_operand.name == "prepared":
            input_operand = input_operand.parent
        run_root = validate_existing_run_root(input_operand, workspace)
        if run_root == output or run_root.is_relative_to(output) or output.is_relative_to(run_root):
            raise ValueError(f"Stature input and review-pack output must be disjoint: {run_root}")
        prepared = _read_evaluated_candidate(run_root, matrix_mode=matrix_mode)
        actual_height = float(prepared["sources"]["profile"]["stature_m"])
        if not math.isfinite(actual_height) or abs(actual_height - height) > 1e-9:
            raise ValueError(f"Stature label H={height:.2f} does not match run stature {actual_height}")
        if (prepared["package_identity"] != primary["package_identity"]
                or prepared["source_hashes"] != primary["source_hashes"]
                or prepared["sources"]["profile"]["id"] != primary["sources"]["profile"]["id"]
                or prepared["sources"]["mobility"]["id"] != primary["sources"]["mobility"]["id"]
                or prepared["sources"]["review-scene"] != primary["sources"]["review-scene"]):
            raise ValueError(f"Stature input H={height:.2f} has incompatible package/profile/scene sources")
        for fixture, expected_beat in (("neutral", Fraction(0)), ("squat", Fraction(2))):
            samples = [row for row in prepared["samples"] if row["fixture"] == fixture]
            if not any(Fraction(row["beat"]["numerator"], row["beat"]["denominator"]) == expected_beat
                       for row in samples):
                raise ValueError(f"Stature input H={height:.2f} is missing {fixture} beat {expected_beat}")
        resolved[height] = {"run_root": run_root, "prepared": prepared}
    missing = [height for height in (1.50, 1.90) if height not in resolved]
    return {"status": "pass" if not missing else "incomplete", "inputs": resolved,
            "missing_heights": missing}


def _preflight_skeleton_baseline(run_value, primary, candidate_run, output, workspace, *, matrix_mode=False):
    """Validate historical baseline content/output against its own sealed identity."""
    if run_value is None:
        return {"status": "incomplete", "missing": "--skeleton-baseline"}
    baseline_root = validate_existing_run_root(Path(run_value), workspace)
    if baseline_root == output or baseline_root.is_relative_to(output) or output.is_relative_to(baseline_root):
        raise ValueError("Skeleton baseline and review-pack output must be disjoint")
    input_path = baseline_root / "input.json"
    if not input_path.is_file() or input_path.is_symlink():
        raise ValueError("Skeleton baseline has no safe input.json")
    # The prepared content seal is checked, but the historical package identity
    # is intentionally not compared to the active candidate installation.
    baseline = read_prepared(input_path, check_sources=False)
    if baseline["sources"]["profile"]["id"] != primary["sources"]["profile"]["id"]:
        raise ValueError("Skeleton baseline profile does not match the candidate")
    if baseline["sources"]["review-scene"] != primary["sources"]["review-scene"]:
        raise ValueError("Skeleton baseline fixed scene differs from the candidate")
    # Forefoot-rocker and the surface-focused sweeps are additions of this
    # change. Historical skeleton comparison is limited to the shared core
    # samples; those new samples remain covered by current clean-pass checks.
    relevant = ("neutral", "rest", "arm-raise", "squat", "walking-in-place")
    comparisons = _baseline_sample_matches(primary, baseline, relevant)
    manifest_path = baseline_root / "render-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("Skeleton baseline render manifest is missing or invalid") from error
    if "samples" not in manifest or "characters" in manifest:
        raise ValueError("Skeleton baseline must use its historical skeleton-only render manifest")
    required = _validate_manifest(manifest, baseline, baseline_root / "frames", output=baseline_root)
    manifest_rows = {row["id"]: row for row in manifest["samples"]}
    for match in comparisons:
        record = manifest_rows.get(match["baseline_sample_id"])
        if record is None or set(record.get("images", {})) != set(match["required_views"]):
            raise ValueError(
                "Skeleton baseline is missing a required view at "
                f"{match['fixture']} beat {match['beat']['numerator']}/{match['beat']['denominator']}"
            )
    candidate_run = validate_existing_run_root(Path(candidate_run), workspace)
    candidate_content = candidate_run / "render" if matrix_mode else candidate_run
    if (candidate_content == output or candidate_content.is_relative_to(output)
            or output.is_relative_to(candidate_content)):
        raise ValueError("Candidate skeleton and review-pack output must be disjoint")
    baseline_evaluated = _read_evaluated_samples(baseline_root, baseline, "Skeleton baseline")
    candidate_evaluated = _read_evaluated_samples(candidate_run, primary, "Candidate skeleton",
                                                  matrix_mode=matrix_mode)
    baseline_geometry_checks = []
    for match in comparisons:
        old = baseline_evaluated[match["baseline_sample_id"]]
        new = candidate_evaluated[match["candidate_sample_id"]]
        baseline_geometry_checks.append(_compare_baseline_evaluated_geometry(
            old, new, float(primary["sources"]["profile"]["stature_m"]),
            f"{match['fixture']}/{match['beat']['numerator']}/{match['beat']['denominator']}"
        ))
    receipt_candidates = []
    for path in (baseline_root / "processes").glob("*/outcome.json"):
        try:
            receipt = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Skeleton baseline receipt is unreadable: {path}") from error
        if receipt.get("operation") == "render-pass":
            receipt_candidates.append((path, receipt))
    if len(receipt_candidates) != 1:
        raise ValueError(f"Expected exactly one baseline render receipt; found {len(receipt_candidates)}")
    receipt_path, receipt = receipt_candidates[0]
    if (receipt.get("state") != "succeeded" or receipt.get("outcome") != "exit"
            or receipt.get("source_sha256") != baseline["content_sha256"]):
        raise ValueError(f"Skeleton baseline receipt is failed or stale: {receipt_path}")
    output_records = receipt.get("output_validation", {}).get("files", [])
    if not output_records:
        raise ValueError("Skeleton baseline receipt has no output hash inventory")
    paths = []
    for record in output_records:
        path = Path(record.get("path", "")).resolve()
        try:
            paths.append(path.relative_to(baseline_root.resolve()))
        except ValueError as error:
            raise ValueError(f"Skeleton baseline receipt escapes its run: {path}") from error
    required_names = {path.as_posix() for path in required}
    if not required_names <= {path.as_posix() for path in paths}:
        raise ValueError("Skeleton baseline receipt does not hash every required render artifact")
    _receipt_files_unchanged(receipt, baseline_root, paths)
    return {"status": "pass", "run_root": baseline_root, "prepared": baseline,
            "manifest": manifest, "required_paths": required,
            "receipt_path": str(receipt_path), "common_sample_ids": [row["candidate_sample_id"] for row in comparisons],
            "common_sample_matches": comparisons,
            "evaluated_geometry": {"status": "pass", "samples": baseline_geometry_checks},
            "render_identity": manifest.get("render_identity"),
            "prepared_sha256": baseline["content_sha256"]}


def _baseline_sample_matches(candidate, baseline, relevant_fixtures):
    """Join historical/current schedules by fixture and exact rational beat."""
    relevant = set(relevant_fixtures)

    def indexed(prepared, label):
        rows = {}
        for sample in prepared["samples"]:
            fixture = sample.get("fixture")
            if fixture not in relevant:
                continue
            beat_record = sample.get("beat")
            try:
                beat = Fraction(beat_record["numerator"], beat_record["denominator"])
            except (KeyError, TypeError, ValueError, ZeroDivisionError) as error:
                raise ValueError(f"{label} has an invalid beat for {sample.get('id')}") from error
            key = (fixture, beat)
            if key in rows:
                raise ValueError(
                    f"{label} has duplicate logical sample key {fixture}@{beat.numerator}/{beat.denominator}"
                )
            rows[key] = sample
        return rows

    candidate_rows = indexed(candidate, "Candidate skeleton")
    baseline_rows = indexed(baseline, "Skeleton baseline")
    missing = sorted(candidate_rows.keys() - baseline_rows.keys())
    if missing:
        details = ", ".join(f"{fixture}@{beat.numerator}/{beat.denominator}" for fixture, beat in missing[:20])
        if len(missing) > 20:
            details += f", and {len(missing) - 20} more"
        raise ValueError("Skeleton baseline is missing required shared-core beats: " + details)

    matches = []
    for fixture, beat in sorted(candidate_rows):
        old = baseline_rows[(fixture, beat)]
        new = candidate_rows[(fixture, beat)]
        for field in ("frames", "actions", "contacts", "world_root"):
            if old.get(field) != new.get(field):
                raise ValueError(
                    f"Skeleton baseline movement differs at {fixture}@{beat.numerator}/{beat.denominator}/{field}"
                )
        matches.append({
            "fixture": fixture,
            "beat": {"numerator": beat.numerator, "denominator": beat.denominator},
            "baseline_sample_id": old["id"],
            "candidate_sample_id": new["id"],
            "required_views": sorted(_expected_views(candidate, new)),
        })
    if not matches:
        raise ValueError("Skeleton baseline has no logical sample matches for the shared-core comparison")
    return matches


def _baseline_candidate_run(primary, output, workspace):
    """Resolve the evaluated primary candidate associated with this preparation."""
    for key in ("_run_root", "run_root"):
        value = primary.get(key)
        if value is not None:
            run_root = validate_existing_run_root(Path(value), workspace)
            if run_root == output or run_root.is_relative_to(output) or output.is_relative_to(run_root):
                raise ValueError("Candidate skeleton and review-pack output must be disjoint")
            return run_root
    raise ValueError("Primary character input has no associated evaluated candidate run")


def _baseline_report_record(baseline):
    """Return the bounded JSON-safe summary persisted in the review pack."""
    omitted = {"manifest", "prepared", "run_root"}
    def json_safe(value):
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, dict):
            return {key: json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [json_safe(item) for item in value]
        return value
    return {key: json_safe(value) for key, value in (baseline or {}).items() if key not in omitted}


def _read_evaluated_samples(run_root, prepared, label, *, matrix_mode=False):
    path = run_root / "render" / "evaluated.json" if matrix_mode else run_root / "evaluated.json"
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"{label} has no safe evaluated.json: {path}")
    try:
        evaluated = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} evaluated evidence is unreadable: {path}") from error
    expected_ids = [row["id"] for row in prepared["samples"]]
    observed = evaluated.get("samples")
    if (evaluated.get("prepared_sha256") != prepared.get("content_sha256")
            or not isinstance(observed, list)
            or [row.get("id") for row in observed if isinstance(row, dict)] != expected_ids):
        raise ValueError(f"{label} evaluated evidence is stale or has incomplete sample membership: {path}")
    return {row["id"]: row for row in observed}


def _compare_baseline_evaluated_geometry(old, new, height, sample_label):
    """Compare source-bound skeletal frames and measured geometry at one shared beat."""
    position_tolerance = 1e-4 * height
    geometry_tolerance = 1e-5 * height
    if old.get("scene") != new.get("scene"):
        raise ValueError(f"Skeleton baseline fixed scene differs at {sample_label}")
    if old.get("world_root") != new.get("world_root"):
        raise ValueError(f"Skeleton baseline world root differs at {sample_label}")
    old_frames, new_frames = old.get("frames"), new.get("frames")
    if not isinstance(old_frames, dict) or not isinstance(new_frames, dict) or set(old_frames) != set(new_frames):
        raise ValueError(f"Skeleton baseline frame inventory differs at {sample_label}")
    for structure_id in old_frames:
        a, b = old_frames[structure_id], new_frames[structure_id]
        if (math.dist(a["position_m"], b["position_m"]) > position_tolerance
                or m.angle_error(a["rotation"], b["rotation"]) > 0.1):
            raise ValueError(f"Skeleton baseline frame differs at {sample_label}/{structure_id}")

    for field in ("attachments", "landmarks", "mass_points"):
        left, right = old.get(field), new.get(field)
        if not isinstance(left, dict) or not isinstance(right, dict) or set(left) != set(right):
            raise ValueError(f"Skeleton baseline {field} inventory differs at {sample_label}")
        for identifier in left:
            a, b = left[identifier], right[identifier]
            if a.get("structure") != b.get("structure"):
                raise ValueError(f"Skeleton baseline {field} structure differs at {sample_label}/{identifier}")
            for coordinate in ("position_m", "local_position_m"):
                if coordinate in a or coordinate in b:
                    if (coordinate not in a or coordinate not in b
                            or math.dist(a[coordinate], b[coordinate]) > position_tolerance):
                        raise ValueError(
                            f"Skeleton baseline {field} coordinate differs at {sample_label}/{identifier}/{coordinate}"
                        )

    old_geometry, new_geometry = old.get("geometry"), new.get("geometry")
    if (not isinstance(old_geometry, dict) or not isinstance(new_geometry, dict)
            or set(old_geometry) != set(new_geometry)):
        raise ValueError(f"Skeleton baseline geometry inventory differs at {sample_label}")
    for geometry_id in old_geometry:
        a, b = old_geometry[geometry_id], new_geometry[geometry_id]
        for field in ("structure", "topology_sha256", "vertex_count", "rigid", "scale"):
            if a.get(field) != b.get(field):
                raise ValueError(f"Skeleton baseline geometry {field} differs at {sample_label}/{geometry_id}")
        for field in ("local_bounds_m", "world_bounds_m"):
            left, right = a.get(field), b.get(field)
            if (not isinstance(left, list) or not isinstance(right, list) or len(left) != len(right)
                    or any(math.dist(x, y) > geometry_tolerance for x, y in zip(left, right))):
                raise ValueError(f"Skeleton baseline geometry {field} differs at {sample_label}/{geometry_id}")
        left_matrix, right_matrix = a.get("world_matrix"), b.get("world_matrix")
        if (not isinstance(left_matrix, list) or not isinstance(right_matrix, list)
                or len(left_matrix) != 4 or len(right_matrix) != 4):
            raise ValueError(f"Skeleton baseline geometry world matrix is missing at {sample_label}/{geometry_id}")
        if (math.dist([left_matrix[row][3] for row in range(3)],
                      [right_matrix[row][3] for row in range(3)]) > position_tolerance
                or max(abs(left_matrix[row][column] - right_matrix[row][column])
                       for row in range(3) for column in range(3)) > 1e-4):
            raise ValueError(f"Skeleton baseline geometry world matrix differs at {sample_label}/{geometry_id}")
        if abs(a.get("rigid_vertex_residual_m", 0.0) - b.get("rigid_vertex_residual_m", 0.0)) > geometry_tolerance:
            raise ValueError(f"Skeleton baseline geometry residual differs at {sample_label}/{geometry_id}")
    return {"fixture_beat": sample_label, "status": "pass",
            "frame_count": len(old_frames), "geometry_count": len(old_geometry),
            "position_tolerance_m": position_tolerance, "geometry_tolerance_m": geometry_tolerance,
            "rotation_tolerance_degrees": 0.1}


def _managed_render(input_path, root, workspace, name, characters, *,
                    timeout_seconds, slot_timeout_seconds, matrix_element_root=None):
    """Run one finite designated pass using the same sealed API as public render."""
    from humanmotionlib import api
    directory = root / name
    kwargs = {} if characters is None else {"characters": characters}
    if matrix_element_root is not None:
        result = api.render(
            input_path, workspace=workspace, output=directory,
            matrix_destination={"element_root": matrix_element_root,
                                "allowed_destinations": [f"presentation/{name}"]},
            images=True, render_dir=directory / "frames", render_only=True,
            timeout_seconds=timeout_seconds, slot_timeout_seconds=slot_timeout_seconds,
            **kwargs)
    else:
        result = api._render_owned_pass(
            input_path, workspace=workspace, output=directory, owner_run=root,
            images=True, render_dir=directory / "frames", render_only=True,
            timeout_seconds=timeout_seconds, slot_timeout_seconds=slot_timeout_seconds,
            **kwargs)
    manifest_path = result.artifacts.get("render_manifest")
    if manifest_path is None:
        raise ValueError(f"Managed review pass {name} has no render manifest")
    manifest = json.loads(manifest_path.read_text())
    manifest["metadata"] = json.loads(result.artifacts["metadata"].read_text())
    return manifest


def _manifest_character_images(manifest, pass_root, prepared, character_ids):
    return _character_images(manifest, pass_root / "frames", prepared, character_ids)


def _pixel_comparison(name, a, b, root, *, character_id, sample_id, view,
                      baseline_sample_id=None, beat=None):
    same = decoded_digest(a) == decoded_digest(b)
    result = {"comparison": name, "character_id": character_id, "sample_id": sample_id,
            "view": view, "status": "pass" if same else "fail",
            "candidate": str(a.relative_to(root)), "reference": str(b.relative_to(root))}
    if baseline_sample_id is not None:
        result["baseline_sample_id"] = baseline_sample_id
    if beat is not None:
        result["beat"] = beat
    return result


def _stature_strip(stature_inputs, character_ids, root):
    """Build actual neutral and squat-bottom strips for supplied stature runs."""
    composites = root / "composites"
    results = {"status": "pass", "missing_heights": list(stature_inputs["missing_heights"],),
               "cells": [], "images": [], "sources": []}
    height_data = {}
    for height, record in stature_inputs["inputs"].items():
        prepared = record["prepared"]
        results["sources"].append({"height_m": height, "prepared_sha256": prepared["content_sha256"],
                                   "package_identity": prepared["package_identity"],
                                   "input_run": str(record["run_root"]) if record["run_root"] else "primary-input"})
        if height == 1.70:
            pass_root = root / "clean-a"
            manifest = json.loads((pass_root / "render-manifest.json").read_text())
            manifest["metadata"] = json.loads((pass_root / "build-metadata.json").read_text())
        else:
            pass_root = root / f"stature-{int(round(height * 100)):03d}"
            manifest = json.loads((pass_root / "render-manifest.json").read_text())
            manifest["metadata"] = json.loads((pass_root / "build-metadata.json").read_text())
        height_data[height] = (prepared, _manifest_character_images(manifest, pass_root, prepared, character_ids))
    for fixture, beat_value in (("neutral", Fraction(0)), ("squat", Fraction(2))):
        row_images = {identifier: {} for identifier in character_ids}
        for height in (1.50, 1.70, 1.90):
            if height not in height_data:
                continue
            prepared, images = height_data[height]
            sample = next((item for item in prepared["samples"] if item["fixture"] == fixture and
                           Fraction(item["beat"]["numerator"], item["beat"]["denominator"]) == beat_value), None)
            if sample is None:
                raise ValueError(f"Stature H={height:.2f} is missing {fixture} beat {beat_value}")
            for identifier in character_ids:
                for view in ("front", "side"):
                    path = images[identifier][sample["id"]].get(view)
                    if path is None:
                        raise ValueError(f"Stature H={height:.2f} lacks {view} for {identifier}/{sample['id']}")
                    copied = composites / "stature-inputs" / f"h-{height:.2f}-{fixture}-{identifier}-{view}.png"
                    copied.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, copied)
                    row_images[identifier][f"{height:.2f}-{view}"] = copied
                    results["cells"].append({"height_m": height, "fixture": fixture,
                                             "sample_id": sample["id"], "character_id": identifier,
                                             "view": view, "source": str(path),
                                             "image": str(copied.relative_to(root)),
                                             "sha256": hashlib.sha256(copied.read_bytes()).hexdigest()})
        for view in ("front", "side"):
            # Each cell is a real render at its own H. Missing heights are not
            # filled; the report and the visible row retain that gap.
            available = [height for height in (1.50, 1.70, 1.90) if height in height_data]
            columns = tuple(f"{height:.2f}" for height in available)
            canvas = Image.new("RGB", (900 * len(columns), 480), (245, 247, 248))
            for col, height in enumerate(available):
                label(canvas, f"H={height:.2f}m", (col * 900 + 8, 28), scale=2)
                prepared, images = height_data[height]
                sample = next(item for item in prepared["samples"] if item["fixture"] == fixture and
                              Fraction(item["beat"]["numerator"], item["beat"]["denominator"]) == beat_value)
                # The strip is a registry-ordered set of character rows inside
                # each stature cell, with the same source resolution/cameras.
                grid_path = composites / "stature-inputs" / f"h-{height:.2f}-{fixture}-{view}-grid.png"
                record = {"sample_id": sample["id"], "beat": sample["beat"]}
                _character_grid(images, [record], view, grid_path,
                    title=f"H={height:.2f}m / {fixture} / {view}", columns=character_ids)
                with Image.open(grid_path) as source:
                    grid = source.convert("RGB")
                canvas.paste(grid, (col * 900, 55))
            output = composites / f"stature-{fixture}-{view}.png"
            canvas.save(output)
            results["images"].append(str(output.relative_to(root)))
    if results["missing_heights"]:
        results["status"] = "incomplete"
    return results


def assemble_character_pack(prepared, first, second, root, character_ids, *,
                            baseline=None, stature_inputs=None, comparison_passes=None):
    """Assemble a character comparison pack from two complete supervised passes."""
    ids = tuple(character_ids)
    first_identity = first.get("render_identity")
    second_identity = second.get("render_identity")
    if (first.get("prepared_sha256") != second.get("prepared_sha256")
            or first.get("prepared_sha256") != prepared.get("content_sha256")):
        raise ValueError("Character review passes do not share the prepared identity")
    if first_identity != second_identity or not isinstance(first_identity, str):
        raise ValueError("Character review passes do not share a sealed render identity")
    first_frames = root / "clean-a" / "frames"
    second_frames = root / "clean-b" / "frames"
    images = _character_images(first, first_frames, prepared, ids)
    second_images = _character_images(second, second_frames, prepared, ids)
    repeat = []
    for identifier in ids:
        for sample in prepared["samples"]:
            for view, path in images[identifier][sample["id"]].items():
                other = second_images[identifier][sample["id"]][view]
                same = decoded_digest(path) == decoded_digest(other)
                repeat.append({"character_id": identifier, "sample_id": sample["id"],
                               "view": view, "status": "pass" if same else "fail",
                               "image": str(path.relative_to(root))})
    repeat_report = {"status": "pass" if repeat and all(row["status"] == "pass" for row in repeat)
                     else "fail", "comparisons": repeat,
                     "criterion": "Exact decoded RGBA equality for each character/sample/view across clean passes."}
    comparison_rows = []
    comparison_passes = comparison_passes or {}
    if ids == ("skeleton", "male", "female"):
        required_comparisons = ("skeleton-default", "skeleton-explicit", "male-singleton", "female-singleton")
        absent = [name for name in required_comparisons if name not in comparison_passes]
        if absent:
            raise ValueError("Character review pack lacks managed regression passes: " + ", ".join(absent))
        batch_images = images
        for pass_name, identifier in (("skeleton-default", "skeleton"),
                                      ("skeleton-explicit", "skeleton"),
                                      ("male-singleton", "male"),
                                      ("female-singleton", "female")):
            pass_manifest, pass_root = comparison_passes[pass_name]
            singleton = _manifest_character_images(pass_manifest, pass_root, prepared, (identifier,))
            for sample in prepared["samples"]:
                for view, candidate_path in singleton[identifier][sample["id"]].items():
                    comparison_rows.append(_pixel_comparison(
                        pass_name, batch_images[identifier][sample["id"]][view], candidate_path,
                        root, character_id=identifier, sample_id=sample["id"], view=view))
        if baseline and baseline.get("status") == "pass":
            baseline_images = _manifest_character_images(
                baseline["manifest"], baseline["run_root"], baseline["prepared"], ("skeleton",))
            baseline_copied = []
            baseline_dir = root / "reference" / "baseline"
            for match in baseline["common_sample_matches"]:
                old_id, candidate_id = match["baseline_sample_id"], match["candidate_sample_id"]
                for view in match["required_views"]:
                    old_path = baseline_images["skeleton"][old_id].get(view)
                    candidate_path = batch_images["skeleton"][candidate_id].get(view)
                    if old_path is None or candidate_path is None:
                        raise ValueError(
                            f"Skeleton baseline view mapping differs at {match['fixture']} "
                            f"beat {match['beat']['numerator']}/{match['beat']['denominator']}/{view}"
                        )
                    target = baseline_dir / candidate_id / f"{view}.png"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(old_path, target)
                    comparison_rows.append(_pixel_comparison(
                        "skeleton-baseline", candidate_path, target,
                        root, character_id="skeleton", sample_id=candidate_id, view=view,
                        baseline_sample_id=old_id, beat=match["beat"]))
                    baseline_copied.append({"sample_id": candidate_id, "baseline_sample_id": old_id,
                                            "fixture": match["fixture"], "beat": match["beat"], "view": view,
                                            "image": str(target.relative_to(root)),
                                            "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
            baseline["copied_images"] = baseline_copied
        else:
            baseline = baseline or {"status": "incomplete", "missing": "--skeleton-baseline"}
    stature_report = {"status": "incomplete", "missing_heights": [1.50, 1.90], "images": []}
    if ids == ("skeleton", "male", "female") and stature_inputs:
        stature_report = _stature_strip(stature_inputs, ids, root)
    composites = root / "composites"
    composites.mkdir(exist_ok=True)
    sample_lookup = {sample["id"]: sample for sample in prepared["samples"]}
    fixture_lookup = {fixture["id"]: fixture for fixture in prepared["sources"]["diagnostics"]}
    coverage = _character_plan_coverage(prepared)
    composite_files = []
    gif_metrics = []
    pages = []
    for fixture_id, plans in prepared.get("sampling", {}).items():
        fixture = fixture_lookup.get(fixture_id, {"description": "Prepared diagnostic"})
        body = [f"<h1>{html.escape(fixture_id)}</h1>",
                f"<p>{html.escape(fixture.get('description', ''))}</p>"]
        fixture_has_images = any(sample.get("fixture") == fixture_id for sample in prepared["samples"])
        if not fixture_has_images:
            raise ValueError(f"Character review fixture has no supplied samples: {fixture_id}")
        for plan in plans:
            bpm = plan.get("bpm")
            for mode in ("static", "animation"):
                if not plan.get(mode):
                    continue
                records = _sample_records_for_plan(plan, fixture_id, mode, sample_lookup)
                for view in ("front", "side"):
                    filename = f"{fixture_id}-{bpm}-{view}-{mode}-characters.png"
                    _character_grid(images, records, view, composites / filename,
                                    title=f"{fixture_id} / {bpm} BPM / {mode} / {view}", columns=ids)
                    composite_files.append(f"composites/{filename}")
                    body.append(f'<p><a href="composites/{filename}">{html.escape(bpm.__str__())} BPM / {view} / {mode} character comparison</a></p>')
                if mode == "animation" and len(records) > 1:
                    for identifier in ids:
                        for view in ("front", "side"):
                            gif_path = composites / f"{fixture_id}-{bpm}-{identifier}-{view}.gif"
                            paths = [images[identifier][record["sample_id"]][view] for record in records]
                            metric = gif(paths, Fraction(60, bpm) / plan["intervals_per_beat"], gif_path)
                            gif_metrics.append(metric | {"fixture": fixture_id, "bpm": bpm,
                                                         "character_id": identifier, "view": view,
                                                         "image": f"composites/{gif_path.name}"})
                            composite_files.append(f"composites/{gif_path.name}")
                            body.append(f'<p><img width="512" src="composites/{gif_path.name}" alt="{html.escape(fixture_id)} {_CHARACTER_LABELS[identifier]} {view}"></p>')
            if fixture_id in ("arm-raise", "squat") and bpm == 90:
                counts = _sample_records_for_plan(plan, fixture_id, "static", sample_lookup)
                midpoint = len(counts) // 2
                for identifier in ids:
                    for view in ("front", "side"):
                        for direction, selected in (("first-half", counts[:midpoint+1]),
                                                    ("second-half", counts[midpoint:])):
                            name = f"{fixture_id}-90-{identifier}-{view}-{direction}-onion.png"
                            onion([images[identifier][record["sample_id"]][view] for record in selected],
                                  composites / name)
                            composite_files.append(f"composites/{name}")
                            body.append(f'<p><a href="composites/{name}">{direction} {view} onion skin / {_CHARACTER_LABELS[identifier]}</a></p>')
        body.append("<h2>Exact sample inventory</h2><table><tr><th>Character</th><th>Sample</th><th>Beat</th><th>Views</th></tr>")
        for identifier in ids:
            for sample in prepared["samples"]:
                if sample["fixture"] != fixture_id:
                    continue
                links = " ".join(f'<a href="{images[identifier][sample["id"]][view].relative_to(root)}">{view}</a>'
                                 for view in images[identifier][sample["id"]])
                beat = sample["beat"]
                body.append(f'<tr><td>{_CHARACTER_LABELS[identifier]}</td><td>{sample["id"]}</td><td>{beat["numerator"]}/{beat["denominator"]}</td><td>{links}</td></tr>')
        body.append("</table>")
        write_html(root / f"{fixture_id}.html", fixture_id, "\n".join(body))
        pages.append(f"{fixture_id}.html")

    # Unannotated neutral/rest images provide the silhouette rows; shared joint
    # centers are shown in a separate overlay sheet on the same fixed renders.
    center_ids = {"neutral": None, "rest": None, "arm-raise": None, "squat": None,
                  "walking-in-place": None}
    for fixture_id in center_ids:
        candidates = [sample for sample in prepared["samples"] if sample["fixture"] == fixture_id]
        if candidates:
            center_ids[fixture_id] = candidates[len(candidates)//2]["id"]
    cameras = {camera["id"]: camera for camera in prepared["sources"]["review-scene"]["cameras"]}
    stature = prepared["sources"]["profile"]["stature_m"]
    for fixture_id in ("neutral", "rest"):
        candidate_samples = [sample for sample in prepared["samples"] if sample["fixture"] == fixture_id]
        if not candidate_samples:
            continue
        sample_id = candidate_samples[0]["id"]
        record = {"sample_id": sample_id, "beat": candidate_samples[0]["beat"]}
        for view in ("front", "side", "rear"):
            name = f"silhouette-{fixture_id}-{view}.png"
            _character_grid(images, [record], view, composites / name,
                            title=f"Unannotated {fixture_id} silhouette / {view}", columns=ids)
            composite_files.append(f"composites/{name}")
    joint_files = []
    for fixture_id, sample_id in center_ids.items():
        if sample_id is None:
            continue
        sample = sample_lookup[sample_id]
        beat = {"sample_id": sample_id, "beat": sample["beat"]}
        for view in ("front", "side"):
            camera = cameras.get(view)
            if camera is None:
                raise ValueError(f"Review scene is missing fixed camera {view}")
            overlays = {}
            for identifier in ids:
                name = f"joint-centers-{fixture_id}-{identifier}-{view}.png"
                overlays[identifier] = _annotate_joint_centers(
                    images[identifier][sample_id][view], sample, camera,
                    composites / name, height_m=stature)
                joint_files.append(f"composites/{name}")
            grid = f"joint-centers-{fixture_id}-{view}-characters.png"
            # Point overlays already exist as ordinary image paths; preserve the
            # same temporal row keys to keep the comparison join explicit.
            _character_grid({identifier: {sample_id: {view: path}}
                             for identifier, path in overlays.items()}, [beat], view,
                            composites / grid, title=f"Shared joint centers / {fixture_id} / {view}",
                            columns=ids)
            joint_files.append(f"composites/{grid}")

    sole_files = []
    rocker_plan = next((plan for plan in prepared.get("sampling", {}).get("forefoot-rocker", [])
                        if plan.get("bpm") == 90), None)
    if rocker_plan:
        rocker_records = _sample_records_for_plan(rocker_plan, "forefoot-rocker", "animation", sample_lookup)
        positions = sorted({0, len(rocker_records)//2, len(rocker_records)-1})
        for sample_index in positions:
            record = rocker_records[sample_index]
            for view in ("front", "side"):
                crop_paths = {}
                for identifier in ids:
                    name = f"sole-{record['sample_id']}-{identifier}-{view}.png"
                    crop_paths[identifier] = _sole_crop(images[identifier][record["sample_id"]][view],
                                                        composites / name,
                                                        f"{_CHARACTER_LABELS[identifier]} / {view} / {record['sample_id']}")
                    sole_files.append(f"composites/{name}")
                comparison = f"sole-{record['sample_id']}-{view}-characters.png"
                _character_grid({identifier: {record["sample_id"]: {view: path}}
                                 for identifier, path in crop_paths.items()}, [record], view,
                                composites / comparison,
                                title=f"Fixed sole/contact crop / {record['sample_id']} / {view}",
                                columns=ids)
                sole_files.append(f"composites/{comparison}")

    request_path = root / "clean-a" / "character-render-request.json"
    if ids != ("skeleton",):
        if not request_path.is_file():
            raise ValueError("Character render request is missing from the first clean pass")
        request = json.loads(request_path.read_text())
        descriptors = request.get("character_descriptors")
        if (request.get("render_identity") != first_identity or
                not isinstance(descriptors, list) or [row.get("id") for row in descriptors] != list(ids)):
            raise ValueError("Character source identity does not match the render manifest")
    else:
        request = {"character_descriptors": [{"id": "skeleton", "renderer_kind": "skeletal",
                                               "profile_id": prepared["sources"]["profile"]["id"],
                                               "source_hashes": prepared.get("sources", {})}]}
    sources = {"render_identity": first_identity, "prepared_sha256": first["prepared_sha256"],
               "character_ids": list(ids), "characters": request.get("character_descriptors", [])}
    write_json(root / "character-sources.json", sources)
    write_json(root / "render-repeatability.json", repeat_report)
    complete_pack_status = ("pass" if coverage["status"] == "pass"
                             and ids == ("skeleton", "male", "female")
                             and (baseline or {}).get("status") == "pass"
                             and stature_report["status"] == "pass"
                             and comparison_rows
                             and all(row["status"] == "pass" for row in comparison_rows)
                             and repeat_report["status"] == "pass" else "incomplete")
    write_json(root / "character-pack-coverage.json", coverage | {"selected_characters": list(ids),
               "character_set_status": "pass" if ids == ("skeleton", "male", "female") else "incomplete",
               "baseline_status": (baseline or {}).get("status", "incomplete"),
               "stature_status": stature_report["status"] if stature_inputs else "incomplete",
               "complete_pack_status": complete_pack_status})
    write_json(root / "character-pack-inventory.json", {
        "characters": list(ids), "sample_ids": [sample["id"] for sample in prepared["samples"]],
        "render_identity": first_identity, "composites": sorted(set(
            composite_files + joint_files + sole_files + stature_report.get("images", []))),
        "fixture_pages": pages, "repeatability_comparisons": len(repeat),
        "joint_center_overlays": joint_files, "sole_contact_crops": sole_files,
        "gif_previews": gif_metrics,
        "regression_comparisons": len(comparison_rows),
        "stature_images": stature_report.get("images", []),
        "baseline_images": (baseline or {}).get("copied_images", []),
    })
    write_json(root / "gif-timing.json", {"status": "pass" if gif_metrics and all(
        metric["status"] == "pass" for metric in gif_metrics) else "fail", "previews": gif_metrics})
    write_json(root / "build-metadata.json", first["metadata"])
    write_json(root / "sample-timing.json", prepared["sampling"])
    baseline_status = baseline.get("status", "incomplete") if baseline else "incomplete"
    regression_status = "pass" if comparison_rows and all(row["status"] == "pass" for row in comparison_rows) else "fail"
    write_json(root / "character-regression.json", {
        "status": "incomplete" if ids != ("skeleton", "male", "female") or baseline_status != "pass"
                 else regression_status,
        "comparisons": comparison_rows,
        "baseline": _baseline_report_record(baseline),
        "criterion": "Decoded pixel equality for default/explicit/batch and singleton/batch; historical baseline identity remains separate."})
    write_json(root / "stature-comparison.json", stature_report)
    incomplete = complete_pack_status != "pass" or regression_status != "pass"
    links = "".join(f'<li><a href="{page}">{html.escape(page[:-5])}</a></li>' for page in pages)
    artifact_links = "".join(f'<li><a href="{name}">{html.escape(name)}</a></li>'
                              for name in sorted(set(composite_files + joint_files + sole_files)))
    body = f'''<h1>Skeleton / Male / Female comparison</h1>
<p>Reference stature {stature:.2f} m. Same prepared movement and fixed scene; appearance changes only the authored surface.</p>
<p><strong>{'Character or fixture coverage is incomplete.' if incomplete else 'Numerical acceptance and human visual acceptance remain separate.'}</strong></p>
<p>Prepared SHA-256: {html.escape(first['prepared_sha256'])}<br>Render identity: {html.escape(first_identity)}</p>
<p><a href="character-sources.json">Selected source closure and provenance</a> · <a href="character-pack-coverage.json">Coverage</a> · <a href="character-pack-inventory.json">Pack inventory</a> · <a href="character-regression.json">Default, singleton, and baseline regression</a> · <a href="stature-comparison.json">Stature comparison</a> · <a href="render-repeatability.json">Repeatability</a> · <a href="gif-timing.json">GIF timing</a> · <a href="sample-timing.json">Exact timing</a></p>
<h2>Diagnostics</h2><ul>{links}</ul><h2>Unannotated silhouettes, joint centers, and sole/contact crops</h2><ul>{artifact_links}</ul>'''
    write_html(root / "index.html", "Character comparison", body)
    gif_status = "pass" if gif_metrics and all(item["status"] == "pass" for item in gif_metrics) else "fail"
    return {"status": "incomplete" if incomplete or repeat_report["status"] != "pass"
            or gif_status != "pass" else "pass",
            "render_identity": first_identity, "selected_characters": list(ids),
            "coverage": coverage, "repeatability": repeat_report["status"],
            "regression": regression_status, "baseline": baseline_status,
            "stature": stature_report["status"],
            "complete_pack_status": complete_pack_status, "gif_status": gif_status,
            "composite_count": len(set(composite_files + joint_files + sole_files)),
            "sample_count": len(prepared["samples"])}


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
    parser.add_argument('--characters', nargs='+', default=('skeleton',), metavar='ID',
                        help='Character IDs to compare, normalized to registry order; default: skeleton')
    parser.add_argument('--stature-input', action='append', default=[], metavar='H=RUN',
                        help='Supplementary evaluated candidate run for H=1.50 or H=1.90; repeatable')
    parser.add_argument('--skeleton-baseline', type=Path,
                        help='Read-only immutable historical skeleton render run for regression comparison')
    parser.add_argument('--reuse-renders',action='store_true',help='Reassemble previously completed render passes after validating their input hash')
    parser.add_argument('--html-only-from',type=Path,help='Regenerate presentation HTML from an existing verified pack without rendering or re-encoding media')
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--matrix-element-root',type=Path,
                        help='Explicit stable matrix element root; enables only its declared presentation destinations')
    parser.add_argument('--timeout-seconds',type=float,default=DEFAULT_RENDER_TIMEOUT,
                        help='Finite deadline for each supervised render pass')
    parser.add_argument('--slot-timeout-seconds',type=float,default=DEFAULT_SLOT_TIMEOUT,
                        help='Finite wait for the checkout backend slot per invocation')
    args=parser.parse_args()
    verify_runtime_integrity()
    workspace = workspace_root(workspace)
    matrix_element_root = None
    if args.matrix_element_root is None:
        output = _review_output_root(args.output, workspace)
    else:
        matrix_element_root = validate_run_root(resolve_workspace_path(args.matrix_element_root, workspace), workspace)
        output = _review_output_root(args.output, workspace, matrix_element_root)
        if args.html_only_from or args.reuse_renders:
            parser.error('matrix destination mode supports complete review-pack builds only')
    if bool(args.input)==bool(args.html_only_from):
        parser.error('choose exactly one of --input or --html-only-from')
    if args.html_only_from:
        if args.reuse_renders or args.stature_input or args.skeleton_baseline or tuple(args.characters) != ('skeleton',):
            parser.error('character, baseline, stature, and reuse options apply only to normal render-pack mode')
        predecessor = resolve_workspace_path(args.html_only_from, workspace)
        if output.exists() and any(output.iterdir()):
            raise ValueError(f"review-pack output run root is occupied: {output}")
        from humanmotionlib.presentation import regenerate_html
        result=regenerate_html(predecessor,output,[Path(__file__).resolve(),Path(__file__).with_name('presentation.py').resolve()],workspace=workspace)
        print(json.dumps(result,sort_keys=True),flush=True)
        return 0 if result['status']=='pass' else 1
    if not args.input:
        parser.error('--input is required for normal render-pack mode')
    if matrix_element_root is None:
        input_root = validate_existing_run_root(args.input, workspace)
        input_path = input_root / 'input.json'
    else:
        input_operand = resolve_workspace_path(args.input, workspace)
        if input_operand.name == 'prepared':
            input_root = validate_existing_run_root(input_operand.parent, workspace)
        else:
            input_root = validate_existing_run_root(input_operand, workspace)
        input_path = input_root / 'prepared' / 'input.json'
    if args.reuse_renders:
        if tuple(args.characters) != ('skeleton',) or args.stature_input or args.skeleton_baseline:
            parser.error('--reuse-renders currently applies only to the existing skeleton-only pack')
        if input_root == output or input_root.is_relative_to(output) or output.is_relative_to(input_root):
            raise ValueError('review-pack input and output run roots must be distinct and disjoint')
        if not output.is_dir():
            raise ValueError(f"--reuse-renders requires an existing complete review-pack root: {output}")
        prepared = read_prepared(input_path)
        passes = _preflight_reuse_pack(input_path, output, prepared, workspace=workspace)
        result = assemble(prepared, *passes, output)
        print(json.dumps(result, sort_keys=True), flush=True)
        return 0 if result['status'] == 'pass' else 1
    if matrix_element_root is None:
        if input_root == output or input_root.is_relative_to(output) or output.is_relative_to(input_root):
            raise ValueError('review-pack input and output run roots must be distinct and disjoint')
    else:
        input_content = input_root / 'prepared'
        if (input_content == output or input_content.is_relative_to(output)
                or output.is_relative_to(input_content)):
            raise ValueError('review-pack prepared input and presentation output must be disjoint')
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"review-pack output run root is occupied: {output}")
    validate_timeout(args.timeout_seconds)
    validate_timeout(args.slot_timeout_seconds, 'slot_timeout_seconds')
    prepared=read_prepared(input_path)
    from humanmotionlib.characters import resolve_character_selection
    selected = resolve_character_selection(tuple(args.characters),
                                           profile_id=prepared['sources']['profile']['id'])
    character_ids = tuple(item['id'] for item in selected)
    character_mode = character_ids != ('skeleton',)
    if not character_mode and (args.stature_input or args.skeleton_baseline):
        parser.error('--stature-input and --skeleton-baseline require a character selection including a surface')
    stature_inputs = None
    baseline = None
    if character_mode:
        stature_inputs = _stature_comparison_inputs(args.stature_input, prepared, output, workspace,
                                                    matrix_mode=matrix_element_root is not None)
        baseline = _preflight_skeleton_baseline(args.skeleton_baseline, prepared, input_root,
                                                output, workspace,
                                                matrix_mode=matrix_element_root is not None)
        # A scoped preview is allowed without these optional inputs, but it is
        # always reported incomplete. Supplied inputs are fully preflighted
        # above before the first output or nested managed render is created.
    output.mkdir(parents=True,exist_ok=True)
    if character_mode:
        first = _managed_render(input_path, output, workspace, 'clean-a', character_ids,
                                timeout_seconds=args.timeout_seconds,
                                slot_timeout_seconds=args.slot_timeout_seconds,
                                matrix_element_root=matrix_element_root)
        print('Completed clean-a', flush=True)
        second = _managed_render(input_path, output, workspace, 'clean-b', character_ids,
                                 timeout_seconds=args.timeout_seconds,
                                 slot_timeout_seconds=args.slot_timeout_seconds,
                                 matrix_element_root=matrix_element_root)
        print('Completed clean-b', flush=True)
        comparison_passes = {}
        if character_ids == ('skeleton', 'male', 'female'):
            for pass_name, selection in (
                    ('skeleton-default', None), ('skeleton-explicit', ('skeleton',)),
                    ('male-singleton', ('male',)), ('female-singleton', ('female',))):
                manifest = _managed_render(input_path, output, workspace, pass_name, selection,
                                           timeout_seconds=args.timeout_seconds,
                                           slot_timeout_seconds=args.slot_timeout_seconds,
                                           matrix_element_root=matrix_element_root)
                comparison_passes[pass_name] = (manifest, output / pass_name)
                print('Completed ' + pass_name, flush=True)
            for height in (1.50, 1.90):
                record = stature_inputs['inputs'].get(height)
                if record is None:
                    continue
                pass_name = f"stature-{int(round(height * 100)):03d}"
                stature_input = (record['run_root'] / 'prepared' / 'input.json'
                                 if matrix_element_root is not None else record['run_root'] / 'input.json')
                manifest = _managed_render(stature_input, output, workspace,
                                           pass_name, character_ids,
                                           timeout_seconds=args.timeout_seconds,
                                           slot_timeout_seconds=args.slot_timeout_seconds,
                                           matrix_element_root=matrix_element_root)
                comparison_passes[pass_name] = (manifest, output / pass_name)
                print('Completed ' + pass_name, flush=True)
        result = assemble_character_pack(prepared, first, second, output, character_ids,
                                         baseline=baseline, stature_inputs=stature_inputs,
                                         comparison_passes=comparison_passes)
        print(json.dumps(result, sort_keys=True), flush=True)
        return 0 if result['status'] == 'pass' else 1
    passes=[]
    for name in ('clean-a','clean-b'):
        directory=output/name
        manifest=render_pass(input_path.resolve(),directory.resolve(),
                             (directory/'frames').resolve(),
                             timeout_seconds=args.timeout_seconds,
                             slot_timeout_seconds=args.slot_timeout_seconds,
                             workspace=workspace, owner_run=output,
                             matrix_destination=({"element_root": matrix_element_root,
                                                  "allowed_destinations": [f"presentation/{name}"]}
                                                 if matrix_element_root is not None else None))
        passes.append(manifest)
        print('Completed '+name,flush=True)
    result=assemble(prepared,*passes,output)
    return 0 if result['status']=='pass' else 1


if __name__=='__main__':
    try:raise SystemExit(main())
    except (InvocationError,ValueError,OSError,KeyError) as error:print(str(error),file=sys.stderr);raise SystemExit(1)
