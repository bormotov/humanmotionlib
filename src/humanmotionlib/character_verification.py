# SPDX-License-Identifier: Apache-2.0
"""Independent host checks for sealed character render evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
import hashlib
import math
import os
from pathlib import Path
from typing import Any
import zipfile


def _json(path: Path) -> dict[str, Any]:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key {key!r} in {path.name}")
            result[key] = value
        return result
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def _content_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, indent=2, allow_nan=False, ensure_ascii=False) + "\n"
    import hashlib
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _json_shape(value):
    """Normalize tuple-backed source arrays to their decoded JSON list shape."""
    if isinstance(value,Mapping):
        return {key:_json_shape(item) for key,item in value.items()}
    if isinstance(value,(list,tuple)):
        return [_json_shape(item) for item in value]
    return value


class _GenerationAnchor:
    """Private evidence context produced only after wheel/install byte checks."""

    __slots__ = ("wheel_sha256", "runtime_manifest_sha256", "identity")

    def __init__(self, wheel_sha256, runtime_manifest_sha256, identity):
        self.wheel_sha256=wheel_sha256
        self.runtime_manifest_sha256=runtime_manifest_sha256
        self.identity=identity


_PINNED_GENERATION_DOC_DELTAS={
    "docs/usage.md":(
        "2e74f6e2ce27ec6c754cf087b4aeb8c259b56794f0c0e2ba2f870e9f0359db0f",
        "36b11bfa7b32839e9119e80ec00bbcb43565f5d7d2bb3fb6d8631df709b1b58c",
    ),
    "docs/character-models.md":(
        "dd343ad079938b6fb193c5e2581df6ad8f94a501582dd65ff909b83d7d702cd1",
        "05123532782675a9ed30a43e56d87d9596447b2cfff16d4cbf8dcbd2d96ffb8c",
    ),
}


def _is_reviewed_generation_doc_delta(name, generation_sha256, verifier_sha256):
    return _PINNED_GENERATION_DOC_DELTAS.get(name)==(generation_sha256,verifier_sha256)


def _load_generation_anchor(wheel_path: str | Path, installed_root: str | Path, *,
                            expected_wheel_sha256: str,
                            expected_runtime_manifest_sha256: str) -> _GenerationAnchor:
    """Verify one frozen generation wheel and its installed bytes.

    The expected hashes must come from an independently recorded pre-generation
    freeze, never from a receipt or prepared input.
    """
    wheel=Path(wheel_path).resolve(strict=True)
    installed=Path(installed_root).resolve(strict=True)
    if wheel.is_symlink() or installed.is_symlink() or not wheel.is_file() or not installed.is_dir():
        raise ValueError("generation anchor wheel and installation must be regular files/directories")
    wheel_sha=hashlib.sha256(wheel.read_bytes()).hexdigest()
    if wheel_sha!=expected_wheel_sha256:
        raise ValueError("generation wheel does not match the independently frozen wheel SHA-256")
    try:
        with zipfile.ZipFile(wheel) as archive:
            manifest_bytes=archive.read("humanmotionlib/resources/runtime-manifest.json")
            manifest=json.loads(manifest_bytes)
            manifest_sha=hashlib.sha256(manifest_bytes).hexdigest()
            if manifest_sha!=expected_runtime_manifest_sha256:
                raise ValueError("generation runtime manifest does not match the frozen manifest SHA-256")
            if (not isinstance(manifest,dict) or manifest.get("format")!="humanmotionlib-runtime-manifest/v1"
                    or not isinstance(manifest.get("resources"),dict)
                    or not isinstance(manifest.get("implementation"),dict)):
                raise ValueError("generation runtime manifest has an unsupported shape")
            for category,prefix in (("resources","humanmotionlib/resources/"),
                                     ("implementation","")):
                for logical,digest in manifest[category].items():
                    path=Path(logical)
                    if (not isinstance(logical,str) or path.is_absolute() or ".." in path.parts
                            or not isinstance(digest,str)):
                        raise ValueError(f"invalid {category} closure entry in generation manifest")
                    name=prefix+logical
                    data=archive.read(name)
                    if hashlib.sha256(data).hexdigest()!=digest:
                        raise ValueError(f"generation wheel {category} differs from its manifest: {logical}")
                    target=installed/name
                    if not target.is_file() or target.read_bytes()!=data:
                        raise ValueError(f"installed generation bytes differ from the frozen wheel: {logical}")
            contract=archive.read("humanmotionlib/resources/backend-contract.json")
            if hashlib.sha256(contract).hexdigest()!=manifest.get("backend_contract"):
                raise ValueError("generation backend contract differs from its runtime manifest")
            package_names={name for name in archive.namelist()
                           if name.startswith("humanmotionlib/") and not name.endswith("/")}
            for name in package_names:
                target=installed/"humanmotionlib"/name.removeprefix("humanmotionlib/")
                if not target.is_file() or target.read_bytes()!=archive.read(name):
                    raise ValueError(f"installed package file differs from the frozen wheel: {name}")
            package_root=installed/"humanmotionlib"
            actual_names={"humanmotionlib/"+path.relative_to(package_root).as_posix()
                          for path in package_root.rglob("*")
                          if path.is_file() and "__pycache__" not in path.parts and path.suffix!=".pyc"}
            if actual_names!=package_names:
                raise ValueError("installed generation package file inventory differs from the frozen wheel")
    except (OSError,KeyError,zipfile.BadZipFile,json.JSONDecodeError) as error:
        raise ValueError(f"cannot validate frozen generation wheel: {error}") from error
    identity={"package_version":manifest["version"],"runtime_manifest_sha256":manifest_sha,
              "resource_hashes":manifest["resources"],
              "backend_contract_sha256":manifest["backend_contract"],
              "implementation_hashes":manifest["implementation"]}
    return _GenerationAnchor(wheel_sha,manifest_sha,identity)


def _finite_vector(value, size: int, label: str) -> tuple[float, ...]:
    if not isinstance(value, (list, tuple)) or len(value) != size:
        raise ValueError(f"{label} must contain {size} values")
    result = tuple(float(item) for item in value)
    if not all(math.isfinite(item) for item in result):
        raise ValueError(f"{label} contains non-finite values")
    return result


def _distance(a, b):
    return math.sqrt(sum((x-y)*(x-y) for x, y in zip(a, b)))


def _minimum_vertex_z(vertices, vertex_ids):
    if len(vertices)!=len(vertex_ids):
        raise ValueError("vertex coordinate and ID inventories differ")
    minimum=min(((vertex[2],index) for index,vertex in enumerate(vertices)),
                default=(math.inf,None))
    return (minimum[0],vertex_ids[minimum[1]]) if minimum[1] is not None else (math.inf,None)


def _native_sample_floor_extremum(components, component_order):
    """Aggregate the native sample floor in backend component order."""
    minimum=(math.inf,None)
    for component_id in component_order:
        component=components[component_id]
        values=component.get("vertices_m")
        ids=component.get("vertex_ids")
        if not isinstance(values,list) or not isinstance(ids,list) or len(values)!=len(ids):
            raise ValueError(f"invalid native floor inventory for {component_id}")
        local=_minimum_vertex_z(values,ids)
        if local[0]<minimum[0]:
            minimum=local
    return minimum


def _canonical_reference_metric(evaluated, allow_anchored_legacy):
    """Resolve only the declared current metric or an absent try70 legacy marker."""
    marker=evaluated.get("reference_metric")
    if marker=="canonical-double-world-dq/v1":
        return True
    if marker is None and allow_anchored_legacy:
        return False
    raise ValueError("surface evidence does not declare the canonical double world DQ metric")


def _area(vertices, face):
    a, b, c = (vertices[index] for index in face)
    u = tuple(b[i]-a[i] for i in range(3)); v = tuple(c[i]-a[i] for i in range(3))
    cross = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
    return 0.5*math.sqrt(sum(value*value for value in cross))


def _closest_point_triangle(p, a, b, c):
    """Closest point by Ericson's Voronoi-region method."""
    sub=lambda x,y:tuple(x[i]-y[i] for i in range(3))
    dot=lambda x,y:sum(x[i]*y[i] for i in range(3))
    ab,ac,ap=sub(b,a),sub(c,a),sub(p,a)
    d1,d2=dot(ab,ap),dot(ac,ap)
    if d1<=0 and d2<=0:return a
    bp=sub(p,b);d3,d4=dot(ab,bp),dot(ac,bp)
    if d3>=0 and d4<=d3:return b
    vc=d1*d4-d3*d2
    if vc<=0 and d1>=0 and d3<=0:
        v=d1/(d1-d3);return tuple(a[i]+v*ab[i] for i in range(3))
    cp=sub(p,c);d5,d6=dot(ab,cp),dot(ac,cp)
    if d6>=0 and d5<=d6:return c
    vb=d5*d2-d1*d6
    if vb<=0 and d2>=0 and d6<=0:
        w=d2/(d2-d6);return tuple(a[i]+w*ac[i] for i in range(3))
    va=d3*d6-d5*d4
    if va<=0 and d4-d3>=0 and d5-d6>=0:
        w=(d4-d3)/((d4-d3)+(d5-d6));return tuple(b[i]+w*(c[i]-b[i]) for i in range(3))
    denom=1.0/(va+vb+vc);v=vb*denom;w=vc*denom
    return tuple(a[i]+ab[i]*v+ac[i]*w for i in range(3))


def _closest_mesh_distance(point, vertices, faces):
    best = math.inf
    for face in faces:
        closest = _closest_point_triangle(point, *(vertices[index] for index in face))
        best = min(best, _distance(point, closest))
    return best


_FOCUSED_VISUAL_FIXTURES = (
    "neutral", "rest", "arm-raise", "squat", "walking-in-place", "forefoot-rocker",
    "sweep-shoulder-bilateral-elevation", "sweep-shoulder-bilateral-plane",
    "sweep-shoulder-bilateral-external_twist", "sweep-forearm-bilateral-pronation",
    "sweep-knee-bilateral-flexion",
)


def _required_dense_grid(prepared, fixture_ids=None):
    """List each fixture's <=.01 beat grid plus all explicit events."""
    fixtures = {row["id"]: row for row in prepared.get("sources", {}).get("diagnostics", [])}
    result = {}
    for fixture_id, fixture in sorted(fixtures.items()):
        if fixture_ids is not None and fixture_id not in fixture_ids:
            continue
        duration = float(fixture["duration_beats"])
        count = max(1, math.ceil(duration / 0.01))
        beats = {round(duration * index / count, 10) for index in range(count+1)}
        beats.update(float(sample["beat"]["numerator"]) / float(sample["beat"]["denominator"])
                     for sample in prepared.get("samples", []) if sample.get("fixture") == fixture_id)
        for track in fixture.get("tracks", []):
            beats.update(float(key["beat"]) for key in track.get("keys", []))
        for contact in fixture.get("contacts", []):
            beats.add(float(contact["start_beat"])); beats.add(float(contact["end_beat"]))
        result[fixture_id] = [round(value, 10) for value in sorted(beats)]
    return result


def _fixture_coverage(prepared):
    diagnostics=prepared.get("sources",{}).get("diagnostics",[])
    expected={row.get("id") for row in diagnostics
              if isinstance(row,Mapping) and isinstance(row.get("id"),str)}
    observed={row.get("fixture") for row in prepared.get("samples",[])
              if isinstance(row,Mapping) and isinstance(row.get("fixture"),str)}
    return {"status":"pass" if expected and expected==observed else "incomplete",
            "expected":sorted(expected),"observed":sorted(observed),
            "missing":sorted(expected-observed),"extra":sorted(observed-expected)}


def _focused_visual_sample_coverage(prepared):
    """Validate the exact canonical BPM90 input used by the diagonal visual pack."""
    from fractions import Fraction
    from humanmotionlib.sampling import delivered_beats, sampling

    diagnostics = {row.get("id"): row for row in prepared.get("sources", {}).get("diagnostics", [])
                   if isinstance(row, Mapping)}
    observed = {row.get("fixture") for row in prepared.get("samples", []) if isinstance(row, Mapping)}
    expected = set(_FOCUSED_VISUAL_FIXTURES)
    failures = []
    sampling_table = prepared.get("sampling")
    if not isinstance(sampling_table, Mapping) or set(sampling_table) != expected:
        failures.append({"expected_sampling_fixtures": sorted(expected),
                         "observed_sampling_fixtures": sorted(sampling_table)
                         if isinstance(sampling_table, Mapping) else None,
                         "code": "sampling-fixture-membership"})
    if observed != expected or not expected.issubset(diagnostics):
        failures.append({"expected": sorted(expected), "observed": sorted(observed),
                         "available": sorted(expected.intersection(diagnostics))})
    else:
        for fixture_id in sorted(expected):
            fixture = diagnostics[fixture_id]
            beats = delivered_beats(fixture["duration_beats"], (90,))
            expected_rows = [(fixture_id + f"/{index:05d}", beat)
                             for index, beat in enumerate(beats)]
            rows = [row for row in prepared["samples"] if row.get("fixture") == fixture_id]
            try:
                observed_rows = [(row.get("id"), Fraction(row["beat"]["numerator"],
                                                            row["beat"]["denominator"]))
                                 for row in rows]
            except (KeyError, TypeError, ValueError, ZeroDivisionError):
                observed_rows = []
            if observed_rows != expected_rows:
                failures.append({"fixture": fixture_id, "expected_count": len(expected_rows),
                                 "observed_count": len(observed_rows), "code": "sample-membership"})
            plan = sampling(fixture["duration_beats"], 90)
            sample_ids = {beat: fixture_id + f"/{index:05d}"
                          for index, beat in enumerate(beats)}
            for mode in ("static", "animation"):
                for record in plan[mode]:
                    beat = Fraction(record["beat"]["numerator"], record["beat"]["denominator"])
                    record["sample_id"] = sample_ids[beat]
            actual_plans = prepared.get("sampling", {}).get(fixture_id)
            if actual_plans != [plan]:
                failures.append({"fixture": fixture_id, "expected_bpm": [90],
                                 "observed_bpm": ([row.get("bpm") for row in actual_plans]
                                                   if isinstance(actual_plans, list) else None),
                                 "code": "sampling-plan"})
    return {"status": "fail" if failures else "pass", "scope": "focused-visual",
            "expected": sorted(expected), "observed": sorted(observed), "failures": failures}


def _reference_residual_summary_matches(component, measured_world_max, measured_world_vertex_id,
                                        vertex_ids, stature, *, canonical_metric):
    """Check normative canonical-world maxima and keep legacy combined summaries explicit."""
    try:
        reported_world=float(component.get("maximum_source_world_residual_m",math.nan))
        reported_local=float(component.get("maximum_native_local_residual_m",math.nan))
        reported_combined=float(component.get("maximum_reference_residual_m",math.nan))
    except (TypeError,ValueError):
        return False
    values=(reported_world,reported_local,reported_combined)
    if not all(math.isfinite(value) and value>=0.0 for value in values):
        return False
    bound=1e-5*stature
    reported_worst=component.get("worst_reference_vertex_id")
    if not all(value<=bound for value in values) or reported_worst not in vertex_ids:
        return False
    if canonical_metric:
        local_worst=component.get("worst_native_local_vertex_id")
        return (abs(reported_world-measured_world_max)<=1e-9*stature
                and abs(reported_combined-measured_world_max)<=1e-9*stature
                and reported_worst==measured_world_vertex_id
                and local_worst in vertex_ids)
    return abs(reported_combined-max(reported_world,reported_local))<=1e-9*stature


def _validate_manifest_images(manifest, prepared, run, character_ids):
    characters = manifest.get("characters")
    samples = prepared["samples"]
    if not isinstance(characters, list):
        raise ValueError("character manifest has no character list")
    fixtures = {item["id"]: item for item in prepared.get("sources", {}).get("diagnostics", [])}
    expected_paths = []
    for character in characters:
        identifier = character["id"]
        for sample, record in zip(samples, character.get("samples", [])):
            fixture = sample["fixture"]
            views = {"front", "side"}
            if fixture in ("neutral", "rest"):
                views.add("rear")
                if identifier == "skeleton":
                    scene = prepared.get("sources", {}).get("review-scene", {})
                    extra = {camera["id"] for camera in scene.get("cameras", [])
                             if camera["id"].startswith("thorax-")}
                    views.update(extra)
                    views.update(view+"-isolated" for view in extra)
            images = record.get("images")
            if not isinstance(images, Mapping) or set(images) != views:
                raise ValueError(f"manifest view inventory mismatch for {identifier}/{sample['id']}")
            for view, relative in images.items():
                prefix = [fixture, view, f"{int(sample['frame_id']):05d}.png"]
                if identifier != "skeleton":
                    prefix.insert(0, identifier)
                path = Path(relative)
                if path.is_absolute() or ".." in path.parts or path.parts != tuple(prefix):
                    raise ValueError(f"manifest image path mismatch for {identifier}/{sample['id']}/{view}")
                expected_paths.append(path)
    if not expected_paths:
        raise ValueError("character manifest contains no image files")
    candidate_roots = []
    for directory, names, _files in os.walk(run, followlinks=False):
        names[:] = [name for name in names if not (Path(directory)/name).is_symlink()]
        root = Path(directory)
        if all((root/path).is_file() for path in expected_paths):
            candidate_roots.append(root)
    if len(candidate_roots) != 1:
        raise ValueError(f"manifest images resolve to {len(candidate_roots)} complete frame roots")
    try:
        from PIL import Image
        verified_paths=[]
        for relative in expected_paths:
            image_path = (candidate_roots[0]/relative).resolve()
            if not image_path.is_relative_to(candidate_roots[0].resolve()):
                raise ValueError(f"manifest image escapes frame root: {relative}")
            if image_path.stat().st_size == 0:
                raise ValueError(f"manifest image is empty: {relative}")
            with Image.open(image_path) as image:
                image.verify()
            verified_paths.append(image_path.relative_to(run))
    except ImportError as error:
        raise ValueError("Pillow is required to verify character manifest images") from error
    return verified_paths


def _validate_request_closure(request, prepared, expected_ids):
    """Check the sealed request against current package and source identities."""
    if request.get("package_identity") != prepared.get("package_identity"):
        raise ValueError("render request package identity differs from prepared input")
    from humanmotionlib.runtime import backend_contract
    if request.get("backend_contract") != backend_contract():
        raise ValueError("render request backend contract differs from active implementation")
    descriptors = request.get("character_descriptors")
    if not isinstance(descriptors, list) or [row.get("id") for row in descriptors] != expected_ids:
        raise ValueError("render request descriptors do not match complete registry")
    declared = {}
    for row in descriptors:
        hashes = row.get("source_hashes")
        if not isinstance(hashes, Mapping):
            raise ValueError(f"character descriptor {row.get('id')} has no source hash closure")
        declared.update(hashes)
    for row in request.get("characters", []):
        if not isinstance(row, Mapping) or not isinstance(row.get("source_hashes"), Mapping):
            raise ValueError("render request has invalid numerical character source closure")
        declared.update(row["source_hashes"])
    import hashlib
    from humanmotionlib.package_resources import read_bytes
    for logical, expected in sorted(declared.items()):
        if not isinstance(logical, str) or not isinstance(expected, str):
            raise ValueError("render request contains an invalid source hash record")
        actual = hashlib.sha256(read_bytes(logical)).hexdigest()
        if actual != expected:
            raise ValueError(f"character source closure hash mismatch: {logical}")


def _expected_anchor_positions(profile, sample):
    attachments = {}
    for structure in profile.get("structures", []):
        for attachment in structure.get("attachments", []):
            attachments[attachment["id"]] = (structure["id"], attachment["position_m"])
    frames = sample.get("frames", {})
    result = {}
    for contact in sample.get("contacts", []):
        for identifier in contact.get("anchors", []):
            if identifier not in attachments:
                raise ValueError(f"prepared contact references unknown anchor {identifier}")
            carrier, local = attachments[identifier]
            frame = frames.get(carrier)
            if not isinstance(frame, Mapping):
                raise ValueError(f"prepared sample is missing contact carrier frame {carrier}")
            position = _finite_vector(frame.get("position_m"), 3, carrier+".position_m")
            rotation = frame.get("rotation")
            if not isinstance(rotation, (list, tuple)) or len(rotation) != 3:
                raise ValueError(f"prepared sample has invalid rotation for {carrier}")
            offset = tuple(sum(float(rotation[row][column])*float(local[column]) for column in range(3))
                           for row in range(3))
            result[identifier] = tuple(position[index]+offset[index] for index in range(3))
    return result


def _prepared_sample_context(sample):
    """Return authoritative fixture/beat labels from a prepared sample row."""
    beat = sample.get("beat") if isinstance(sample, Mapping) else None
    if isinstance(beat, Mapping):
        try:
            numerator = int(beat["numerator"])
            denominator = int(beat["denominator"])
            if denominator:
                return sample.get("fixture", "<unknown>"), numerator / denominator
        except (KeyError, TypeError, ValueError, OverflowError):
            pass
    return (sample.get("fixture", "<unknown>") if isinstance(sample, Mapping) else "<unknown>"), None


def _beat_label(beat):
    return f"{beat:.10g}" if isinstance(beat, (int, float)) and math.isfinite(beat) else "unavailable"


def _surface_poses(profile, frames, components, rest_frames, *, compiled_pose=None,
                   component_offsets=None):
    """Apply canonical DQ transforms efficiently, sharing blends per weight row."""
    from humanmotionlib.character_skinning import skin_vertex
    from humanmotionlib.character_surface import _matrix_quaternion
    transforms={}
    blend_cache={}
    if compiled_pose is None:
        carriers = sorted({carrier for component in components for weights in component["weights"]
                           for carrier in weights})
        for carrier in carriers:
            if carrier not in rest_frames or carrier not in frames:
                raise ValueError(f"dense pose is missing carrier frame {carrier}")
            frame = frames[carrier]
            transforms[carrier] = {
                "rest_translation": rest_frames[carrier][1],
                "rest_orientation": rest_frames[carrier][0],
                "posed_translation": _finite_vector(frame.get("position_m"), 3, carrier+" position_m"),
                "posed_orientation": _matrix_quaternion(frame.get("rotation")),
            }
    posed_components = []
    for component in components:
        posed_vertices = []
        if compiled_pose is not None:
            if component_offsets is None or component["id"] not in component_offsets:
                raise ValueError(f"compiled pose has no weight-set offset for {component['id']}")
            offset=component_offsets[component["id"]]
            posed_vertices=[compiled_pose.apply(vertex,offset+index)
                            for index,vertex in enumerate(component["vertices_m"])]
        else:
            for vertex, weights in zip(component["vertices_m"], component["weights"]):
                key = tuple(sorted((carrier, float(weight)) for carrier, weight in weights.items()))
                affine = blend_cache.get(key)
                if affine is None:
                    origin = skin_vertex((0.0,0.0,0.0), dict(key), transforms)
                    basis_points = [skin_vertex(axis, dict(key), transforms) for axis in
                                    ((1.0,0.0,0.0),(0.0,1.0,0.0),(0.0,0.0,1.0))]
                    columns = [tuple(point[i]-origin[i] for i in range(3)) for point in basis_points]
                    affine = (origin, columns)
                    blend_cache[key] = affine
                origin, columns = affine
                posed_vertices.append(tuple(origin[row]+sum(vertex[col]*columns[col][row] for col in range(3))
                                            for row in range(3)))
        posed_components.append({"id":component["id"], "vertices_m":posed_vertices,
                                 "faces":component["faces"], "vertex_ids":component["vertex_ids"]})
    return posed_components


def _dense_contact_points(profile, frames, contacts):
    by_anchor = {}
    for structure in profile.get("structures", []):
        for attachment in structure.get("attachments", []):
            by_anchor[attachment["id"]] = (structure["id"], attachment["position_m"])
    result = {}
    for contact in contacts:
        for anchor_id in contact.get("anchors", []):
            if anchor_id not in by_anchor:
                raise ValueError(f"dense contact references unknown anchor {anchor_id}")
            carrier, local = by_anchor[anchor_id]
            frame = frames.get(carrier)
            if not isinstance(frame, Mapping):
                raise ValueError(f"dense contact is missing carrier frame {carrier}")
            position = _finite_vector(frame.get("position_m"),3,carrier+" position_m")
            rotation = frame.get("rotation")
            if not isinstance(rotation,(list,tuple)) or len(rotation)!=3:
                raise ValueError(f"dense contact has invalid carrier rotation {carrier}")
            rotated = tuple(sum(float(rotation[row][column])*float(local[column]) for column in range(3))
                            for row in range(3))
            result[anchor_id] = tuple(position[i]+rotated[i] for i in range(3))
    return result


def _audit_surface_sample(profile, sample, components, rest_frames, stature, *,
                          posed_components=None, compiled_pose=None, component_offsets=None):
    posed = posed_components if posed_components is not None else _surface_poses(
        profile,sample["frames"],components,rest_frames,compiled_pose=compiled_pose,
        component_offsets=component_offsets)
    threshold_area = 1e-12*stature*stature
    threshold_floor = -1e-4*stature
    threshold_sole = 1e-3*stature
    minimum = (math.inf, None)
    areas_ok = True
    worst_triangle_area = (math.inf, None, None)
    component_map = {component["id"]:component for component in posed}
    for component in posed:
        for index, vertex in enumerate(component["vertices_m"]):
            if vertex[2] < minimum[0]: minimum=(vertex[2],component["vertex_ids"][index])
        for face_index, face in enumerate(component["faces"]):
            area = _area(component["vertices_m"],face)
            if area <= threshold_area:
                areas_ok=False
            if area < worst_triangle_area[0]:
                worst_triangle_area=(area,component["id"],face_index)
    contact_points = _dense_contact_points(profile,sample["frames"],sample.get("contacts",[]))
    sole_distances=[]
    for anchor_id,anchor in contact_points.items():
        side=anchor_id.rsplit(".",1)[-1]
        foot=component_map.get("foot."+side)
        if foot is None:
            raise ValueError(f"dense anchor {anchor_id} has no foot surface")
        distance=_closest_mesh_distance(anchor,foot["vertices_m"],foot["faces"])
        sole_distances.append((distance,anchor_id))
    worst_sole=max(sole_distances,default=(0.0,None))
    return {"minimum_z_m":minimum[0],"worst_floor_vertex_id":minimum[1],
            "worst_sole_distance_m":worst_sole[0],"worst_anchor_id":worst_sole[1],
            "triangle_areas_pass":areas_ok,"worst_triangle_area_m2":worst_triangle_area[0],
            "worst_triangle_component_id":worst_triangle_area[1],
            "worst_triangle_index":worst_triangle_area[2],"allowed_triangle_area_m2":threshold_area,
            "floor_pass":minimum[0]>=threshold_floor,
            "sole_pass":worst_sole[0]<=threshold_sole,
            "vertices_checked":sum(len(component["vertices_m"]) for component in posed)}


def _native_midpoint_beats(prepared):
    evaluator_sources=prepared.get("sources",{})
    prepared_fixtures={sample.get("fixture") for sample in prepared.get("samples",[])}
    fixtures={row["id"]:row for row in evaluator_sources.get("diagnostics",[])
              if row.get("id") in prepared_fixtures}
    delivered={fixture:{float(sample["beat"]["numerator"])/float(sample["beat"]["denominator"])
                        for sample in prepared.get("samples",[]) if sample.get("fixture")==fixture}
               for fixture in fixtures}
    result={}
    for fixture_id,fixture in sorted(fixtures.items()):
        keys=sorted({float(key["beat"]) for track in fixture.get("tracks",[])
                     for key in track.get("keys",[])})
        result[fixture_id]=[(left+right)/2.0 for left,right in zip(keys,keys[1:])
                            if not any(abs((left+right)/2.0-beat)<1e-10 for beat in delivered[fixture_id])]
    return result


def _compiled_surface_weight_layout(surfaces):
    from humanmotionlib.character_skinning import compile_weight_set
    identifiers=sorted(surfaces)
    if not identifiers:
        raise ValueError("dense character audit requires at least one surface")
    reference=surfaces[identifiers[0]]
    offsets={};all_weights=[];offset=0
    for component in reference:
        offsets[component["id"]]=offset
        all_weights.extend(component["weights"])
        offset+=len(component["weights"])
    for identifier in identifiers[1:]:
        components=surfaces[identifier]
        if [(row["id"],row["vertex_ids"],row["weights"]) for row in components] != [
                (row["id"],row["vertex_ids"],row["weights"]) for row in reference]:
            raise ValueError("selected character surfaces do not share topology and weights")
    weight_set=compile_weight_set(all_weights)
    carriers=sorted({carrier for weights in all_weights for carrier in weights})
    return weight_set,offsets,carriers


def _run_dense_surface_audit(prepared, surfaces, stature, required_grid):
    """Stream full <=0.01-beat canonical-reference checks for every fixture."""
    from humanmotionlib.diagnostics import DiagnosticEvaluator
    from humanmotionlib.character_surface import _rest_frames
    from humanmotionlib.character_skinning import compile_pose_skinning,source_world_transforms
    sources=prepared["sources"]
    evaluator=DiagnosticEvaluator({name:sources[name] for name in
                                   ("profile","mobility","body-groups","diagnostics")})
    _,rest_frames=_rest_frames(sources["profile"],1.0)
    weight_set,component_offsets,carriers=_compiled_surface_weight_layout(surfaces)
    character_stats={identifier:{"character_id":identifier,"fixtures":[],"samples":0,
                         "worst_floor_m":math.inf,"worst_floor_vertex_id":None,
                         "worst_floor_fixture":None,"worst_floor_beat":None,
                         "worst_sole_distance_m":0.0,"worst_anchor_id":None,
                         "worst_sole_fixture":None,"worst_sole_beat":None,
                         "status":"pass"} for identifier in sorted(surfaces)}
    fixture_stats={}
    failures=[];observed_total=0
    for fixture_id,beats in sorted(required_grid.items()):
        spacing=max((right-left for left,right in zip(beats,beats[1:])),default=0.0)
        for identifier in sorted(surfaces):
            stats={"fixture":fixture_id,"samples":len(beats),"maximum_spacing_beats":spacing,
                   "minimum_z_m":math.inf,"worst_floor_vertex_id":None,
                   "worst_floor_beat":None,"maximum_sole_distance_m":0.0,
                   "worst_anchor_id":None,"worst_sole_beat":None,"status":"pass"}
            fixture_stats[(identifier,fixture_id)]=stats
            if spacing>0.01+1e-10:
                stats["status"]="fail"
                failures.append({"character_id":identifier,"fixture":fixture_id,
                                 "code":"dense-spacing","measured":spacing,"allowed":0.01})
        for beat in beats:
            solved=evaluator.evaluate(fixture_id,float(beat))
            sample={"frames":solved["frames"],"contacts":solved["contacts"]}
            transforms=source_world_transforms(sources["profile"],solved["frames"],carriers,
                                               rest_frames=rest_frames)
            compiled_pose=compile_pose_skinning(transforms,weight_set)
            for identifier,components in sorted(surfaces.items()):
                posed=_surface_poses(sources["profile"],solved["frames"],components,rest_frames,
                                     compiled_pose=compiled_pose,component_offsets=component_offsets)
                metrics=_audit_surface_sample(sources["profile"],sample,components,rest_frames,stature,
                                               posed_components=posed)
                stats=fixture_stats[(identifier,fixture_id)]
                character=character_stats[identifier]
                character["samples"]+=1;observed_total+=1
                if metrics["minimum_z_m"]<stats["minimum_z_m"]:
                    stats["minimum_z_m"]=metrics["minimum_z_m"]
                    stats["worst_floor_vertex_id"]=metrics["worst_floor_vertex_id"]
                    stats["worst_floor_beat"]=beat
                if metrics["worst_sole_distance_m"]>stats["maximum_sole_distance_m"]:
                    stats["maximum_sole_distance_m"]=metrics["worst_sole_distance_m"]
                    stats["worst_anchor_id"]=metrics["worst_anchor_id"]
                    stats["worst_sole_beat"]=beat
                if metrics["minimum_z_m"]<character["worst_floor_m"]:
                    character["worst_floor_m"]=metrics["minimum_z_m"]
                    character["worst_floor_vertex_id"]=metrics["worst_floor_vertex_id"]
                    character["worst_floor_fixture"]=fixture_id
                    character["worst_floor_beat"]=beat
                if metrics["worst_sole_distance_m"]>character["worst_sole_distance_m"]:
                    character["worst_sole_distance_m"]=metrics["worst_sole_distance_m"]
                    character["worst_anchor_id"]=metrics["worst_anchor_id"]
                    character["worst_sole_fixture"]=fixture_id
                    character["worst_sole_beat"]=beat
                for condition,code,extra in (
                    (metrics["triangle_areas_pass"],"dense-degenerate-triangle",{
                     "component_id":metrics["worst_triangle_component_id"],
                     "triangle_index":metrics["worst_triangle_index"],
                     "measured_area_m2":metrics["worst_triangle_area_m2"],
                     "allowed_area_m2":metrics["allowed_triangle_area_m2"]}),
                    (metrics["floor_pass"],"dense-floor",{"vertex_id":metrics["worst_floor_vertex_id"],
                     "measured_z_m":metrics["minimum_z_m"],"allowed_z_m":-1e-4*stature}),
                    (metrics["sole_pass"],"dense-sole-contact",{"anchor_id":metrics["worst_anchor_id"],
                     "measured_m":metrics["worst_sole_distance_m"],"allowed_m":1e-3*stature})):
                    if not condition:
                        stats["status"]="fail"
                        failures.append({"character_id":identifier,"fixture":fixture_id,
                                         "beat":beat,"code":code,**extra})
        for identifier in sorted(surfaces):
            stats=fixture_stats[(identifier,fixture_id)]
            character_stats[identifier]["fixtures"].append(stats)
            if stats["status"]!="pass":character_stats[identifier]["status"]="fail"
    return {"status":"fail" if failures else "pass","scope":"host-canonical-dq-reference",
            "maximum_grid_spacing_beats":0.01,"observed_sample_character_pairs":observed_total,
            "characters":list(character_stats.values()),"failures":failures}


def _verify_native_midpoints(prepared, evaluated_by_character, surfaces, stature):
    """Recompute each required un-delivered action-key midpoint against native rows."""
    from humanmotionlib.diagnostics import DiagnosticEvaluator
    from humanmotionlib.character_surface import _rest_frames
    from humanmotionlib.character_skinning import compile_pose_skinning, source_world_transforms
    sources=prepared["sources"]
    evaluator=DiagnosticEvaluator({name:sources[name] for name in
                                   ("profile","mobility","body-groups","diagnostics")})
    expected=_native_midpoint_beats(prepared)
    _,rest_frames=_rest_frames(sources["profile"],1.0)
    weight_set,component_offsets,carriers=_compiled_surface_weight_layout(surfaces)
    solved_cache={}
    failures=[];per_character=[];total=0
    for character_id in sorted(surfaces):
        character_failure_start=len(failures)
        evidence=evaluated_by_character[character_id].get("dense_samples",[])
        keyed={}
        for row in evidence:
            try:key=(row["fixture"],round(float(row["beat"]),10))
            except (KeyError,TypeError,ValueError):
                failures.append({"character_id":character_id,"code":"invalid-native-midpoint-record"});continue
            if key in keyed:failures.append({"character_id":character_id,"fixture":key[0],"beat":key[1],"code":"duplicate-native-midpoint"})
            keyed[key]=row
        expected_keys={(fixture,round(beat,10)) for fixture,beats in expected.items() for beat in beats}
        if set(keyed)!=expected_keys:
            failures.append({"character_id":character_id,"code":"native-midpoint-membership",
                             "missing":[list(item) for item in sorted(expected_keys-set(keyed))],
                             "extra":[list(item) for item in sorted(set(keyed)-expected_keys)]})
        max_residual=(0.0,None,None,None,None);count=0
        for fixture_id,beats in sorted(expected.items()):
            for beat in beats:
                row=keyed.get((fixture_id,round(beat,10)))
                if row is None:continue
                pose_key=(fixture_id,round(beat,10))
                cached=solved_cache.get(pose_key)
                if cached is None:
                    solved=evaluator.evaluate(fixture_id,beat)
                    transforms=source_world_transforms(sources["profile"],solved["frames"],carriers,
                                                       rest_frames=rest_frames)
                    compiled_pose=compile_pose_skinning(transforms,weight_set)
                    cached=(solved,compiled_pose)
                    solved_cache[pose_key]=cached
                solved,compiled_pose=cached
                pose_components=_surface_poses(sources["profile"],solved["frames"],surfaces[character_id],rest_frames,
                                               compiled_pose=compiled_pose,component_offsets=component_offsets)
                metric_sample={"frames":solved["frames"],"contacts":solved["contacts"]}
                oracle_metrics=_audit_surface_sample(sources["profile"],metric_sample,
                                                     surfaces[character_id],rest_frames,stature,
                                                     posed_components=pose_components)
                actual_components={item.get("id"):item for item in row.get("components",[])}
                expected_components={item["id"]:item for item in pose_components}
                if set(actual_components)!=set(expected_components):
                    failures.append({"character_id":character_id,"fixture":fixture_id,"beat":beat,
                        "sample_id":f"{fixture_id}@{beat:.10g}","code":"native-midpoint-components",
                        "observed_components":sorted(actual_components),
                        "expected_components":sorted(expected_components)});continue
                for component_id,expected_component in expected_components.items():
                    actual=actual_components[component_id]
                    if actual.get("vertex_ids")!=expected_component["vertex_ids"]:
                        actual_ids=actual.get("vertex_ids") if isinstance(actual.get("vertex_ids"),list) else []
                        expected_ids=expected_component["vertex_ids"]
                        failures.append({"character_id":character_id,"fixture":fixture_id,"beat":beat,
                            "sample_id":f"{fixture_id}@{beat:.10g}","component_id":component_id,
                            "code":"native-midpoint-topology","observed_vertex_count":len(actual_ids),
                            "expected_vertex_count":len(expected_ids),
                            "missing_vertex_ids":sorted(set(expected_ids)-set(actual_ids))[:5],
                            "extra_vertex_ids":sorted(set(actual_ids)-set(expected_ids))[:5]});continue
                    vertices=actual.get("vertices_m",[])
                    if len(vertices)!=len(expected_component["vertices_m"]):
                        failures.append({"character_id":character_id,"fixture":fixture_id,"beat":beat,
                            "sample_id":f"{fixture_id}@{beat:.10g}","component_id":component_id,
                            "code":"native-midpoint-vertex-count","observed_vertex_count":len(vertices),
                            "expected_vertex_count":len(expected_component["vertices_m"]),
                            "expected_vertex_ids":expected_component["vertex_ids"][:5]});continue
                    residuals=[]
                    observed_vertices=[]
                    for expected_vertex,observed in zip(expected_component["vertices_m"],vertices):
                        observed=_finite_vector(observed,3,"native midpoint vertex")
                        observed_vertices.append(observed)
                        residuals.append(_distance(expected_vertex,observed))
                    expected_faces=surfaces[character_id][next(i for i,c in enumerate(surfaces[character_id]) if c["id"]==component_id)]["faces"]
                    if any(_area(observed_vertices,face)<=1e-12*stature*stature for face in expected_faces):
                        triangle_index=next(index for index,face in enumerate(expected_faces)
                            if _area(observed_vertices,face)<=1e-12*stature*stature)
                        triangle_area=_area(observed_vertices,expected_faces[triangle_index])
                        failures.append({"character_id":character_id,"fixture":fixture_id,"beat":beat,
                            "sample_id":f"{fixture_id}@{beat:.10g}","component_id":component_id,
                            "triangle_index":triangle_index,"code":"native-midpoint-degenerate-triangle",
                            "measured_area_m2":triangle_area,"allowed_area_m2":1e-12*stature*stature})
                    local_min=min((vertex[2],index) for index,vertex in enumerate(observed_vertices))
                    if (abs(float(actual.get("minimum_z_m",math.nan))-local_min[0])>1e-9*stature
                            or actual.get("worst_floor_vertex_id")!=expected_component["vertex_ids"][local_min[1]]):
                        failures.append({"character_id":character_id,"fixture":fixture_id,"beat":beat,
                            "sample_id":f"{fixture_id}@{beat:.10g}","component_id":component_id,
                            "vertex_id":expected_component["vertex_ids"][local_min[1]],
                            "code":"native-midpoint-floor-extremum","reported_z_m":actual.get("minimum_z_m"),
                            "recomputed_z_m":local_min[0]})
                    if local_min[0]<-1e-4*stature:
                        failures.append({"character_id":character_id,"fixture":fixture_id,"beat":beat,
                            "sample_id":f"{fixture_id}@{beat:.10g}","component_id":component_id,
                            "code":"native-midpoint-floor-bound",
                                         "vertex_id":expected_component["vertex_ids"][local_min[1]],
                            "measured_z_m":local_min[0],"allowed_z_m":-1e-4*stature,
                            "comparison":"minimum Z >= -1e-4H"})
                    worst=max(residuals,default=0.0);index=residuals.index(worst) if residuals else None
                    if worst>max_residual[0]:
                        max_residual=(worst,component_id,
                            expected_component["vertex_ids"][index] if index is not None else None,fixture_id,beat)
                    if worst>1e-5*stature:
                        failures.append({"character_id":character_id,"fixture":fixture_id,"beat":beat,
                            "sample_id":f"{fixture_id}@{beat:.10g}","component_id":component_id,
                            "code":"native-midpoint-residual",
                                         "vertex_id":expected_component["vertex_ids"][index],"measured_m":worst,
                                         "allowed_m":1e-5*stature})
                native_sample_floor=_native_sample_floor_extremum(
                    actual_components,sorted(expected_components))
                if (abs(float(row.get("minimum_z_m",math.nan))-native_sample_floor[0])>1e-9*stature
                        or row.get("worst_floor_vertex_id")!=native_sample_floor[1]
                        or abs(native_sample_floor[0]-oracle_metrics["minimum_z_m"])>1e-6*stature):
                    failures.append({"character_id":character_id,"fixture":fixture_id,"beat":beat,
                                     "code":"native-midpoint-oracle-floor-mismatch",
                                     "reported_z_m":row.get("minimum_z_m"),
                                     "native_vertex_z_m":native_sample_floor[0],
                                     "reported_vertex_id":row.get("worst_floor_vertex_id"),
                                     "native_vertex_id":native_sample_floor[1],
                                     "canonical_world_z_m":oracle_metrics["minimum_z_m"],
                                     "canonical_world_vertex_id":oracle_metrics["worst_floor_vertex_id"]})
                expected_anchors=_dense_contact_points(sources["profile"],solved["frames"],solved["contacts"])
                contacts=row.get("contacts")
                if not isinstance(contacts,list) or {item.get("anchor_id") for item in contacts}!=set(expected_anchors):
                    failures.append({"character_id":character_id,"fixture":fixture_id,"beat":beat,
                        "sample_id":f"{fixture_id}@{beat:.10g}","code":"native-midpoint-anchor-membership",
                        "observed_anchors":sorted(str(item.get("anchor_id")) for item in contacts)
                            if isinstance(contacts,list) else "invalid",
                        "expected_anchors":sorted(expected_anchors)})
                else:
                    foot_components={item["id"]:item for item in pose_components if item["id"].startswith("foot.")}
                    for contact in contacts:
                        anchor_id=contact["anchor_id"];anchor=_finite_vector(contact.get("anchor_m"),3,"midpoint anchor")
                        anchor_error=_distance(anchor,expected_anchors[anchor_id])
                        if anchor_error>1e-6*stature:
                            failures.append({"character_id":character_id,"fixture":fixture_id,"beat":beat,
                                "sample_id":f"{fixture_id}@{beat:.10g}","anchor_id":anchor_id,
                                "code":"native-midpoint-anchor-position","measured_residual_m":anchor_error,
                                "observed_anchor_m":list(anchor),"expected_anchor_m":list(expected_anchors[anchor_id]),
                                "allowed_m":1e-6*stature})
                            continue
                        side=anchor_id.rsplit(".",1)[-1];foot=actual_components.get("foot."+side)
                        faces=foot_components["foot."+side]["faces"]
                        distance=_closest_mesh_distance(anchor,foot["vertices_m"],faces)
                        reported=float(contact.get("closest_sole_distance_m",math.nan))
                        if abs(reported-distance)>1e-6*stature or distance>1e-3*stature:
                            failures.append({"character_id":character_id,"fixture":fixture_id,"beat":beat,
                                "sample_id":f"{fixture_id}@{beat:.10g}","anchor_id":anchor_id,
                                "code":"native-midpoint-sole-contact",
                                "measured_m":distance,"reported_m":reported,
                                "consistency_bound_m":1e-6*stature,"allowed_m":1e-3*stature})
                count+=1;total+=1
        per_character.append({"character_id":character_id,"status":"fail" if len(failures)>character_failure_start else "pass",
                              "expected_samples":len(expected_keys),"observed_samples":count,
                              "worst_residual_m":max_residual[0],"worst_component_id":max_residual[1],
                              "worst_vertex_id":max_residual[2],"worst_fixture":max_residual[3],
                              "worst_beat":max_residual[4]})
    return {"status":"fail" if failures else "pass","expected_samples_per_character":len({
                (fixture,round(beat,10)) for fixture,beats in expected.items() for beat in beats}),
            "observed_samples_per_character":total//max(1,len(surfaces)),
            "characters":per_character,"failures":failures}


def verify_character_output(prepared: Mapping[str, Any], render_run: str | Path,
                            expected_character_ids: Sequence[str],
                            stature_values: Sequence[float] = (1.5, 1.7, 1.9),
                            *, numeric_only: bool = False,
                            selected_character_id: str | None = None,
                            require_complete_diagnostic_coverage: bool = False,
                            _focused_visual: bool = False,
                            _generation_anchor: _GenerationAnchor | None = None) -> dict[str, Any]:
    """Verify one stature's complete character render and report missing scopes.

    Dense host-reference checks are regenerated from the prepared source and
    canonical solved frames at every required event/grid beat. Native rows for
    undelivered action-key midpoints are checked separately. Other stature
    runs remain explicitly missing in this single-run result.
    """
    run = Path(render_run).resolve()
    failures: list[dict[str, str]] = []
    report: dict[str, Any] = {
        "format": "hml-character-verification/v1", "status": "fail",
        "prepared_sha256": prepared.get("content_sha256") if isinstance(prepared, Mapping) else None,
        "registry": {"expected_ids": list(expected_character_ids), "observed_ids": [],
                     "missing_ids": [], "extra_ids": [], "checked_ids": [], "omitted_ids": []},
        "stature": {"required_m": [float(value) for value in stature_values],
                    "observed_m": None, "missing_m": []},
        "native": {"status": "not-verified", "characters": []},
        "native_midpoints": {"status": "not-run", "characters": [], "failures": []},
        "dense": {"status": "not-run", "scope": "host-canonical-dq-reference",
                  "required_beats_by_fixture": {}, "observed_samples": 0},
        "fixture_coverage": {"status":"not-verified","expected":[],"observed":[],
                             "missing":[],"extra":[]},
        "mode": "numeric-only" if numeric_only else "render-and-numeric",
        "numeric_status": "not-verified",
        "rendering": "not-run" if numeric_only else "required",
        "visual": "not-assessed",
        "failures": failures,
    }

    def fail(code, detail):
        failures.append({"code": code, "detail": str(detail)})

    if not isinstance(prepared, Mapping):
        fail("invalid-prepared", "prepared must be a mapping")
        return report
    if selected_character_id is not None and not numeric_only:
        fail("invalid-scope", "selected_character_id is only valid for numeric-only verification")
        return report
    if _generation_anchor is not None and (not numeric_only or not isinstance(_generation_anchor,_GenerationAnchor)):
        fail("invalid-generation-anchor","a trusted generation anchor is private to numeric-only verification")
        return report
    if require_complete_diagnostic_coverage and not (
            numeric_only and selected_character_id is not None):
        fail("invalid-scope", "complete diagonal diagnostic coverage applies only to selected-character numeric verification")
        return report
    if _focused_visual and not numeric_only:
        fail("invalid-scope", "focused visual verification is internal numeric preflight only")
        return report
    if _focused_visual and (selected_character_id not in {"skeleton", "male", "female"}
                            or require_complete_diagnostic_coverage):
        fail("invalid-scope", "focused visual verification requires one approved diagonal member")
        return report
    report["dense"]["required_beats_by_fixture"] = _required_dense_grid(
        prepared, _FOCUSED_VISUAL_FIXTURES if _focused_visual else None)
    report["fixture_coverage"] = _fixture_coverage(prepared)
    if _focused_visual:
        coverage = _focused_visual_sample_coverage(prepared)
        report["fixture_coverage"] = coverage
        for item in coverage["failures"]:
            fail("focused-visual-coverage", item)
        report["verification_scope"] = "focused-visual"
    samples = prepared.get("samples")
    if not isinstance(samples, list) or not samples:
        fail("invalid-prepared", "prepared samples are missing")
        return report
    profile = prepared.get("sources", {}).get("profile")
    if not isinstance(profile, Mapping):
        fail("invalid-profile", "prepared profile is missing")
        return report
    stature = float(profile.get("stature_m", math.nan))
    report["stature"]["observed_m"] = stature if math.isfinite(stature) else None
    required_statures = ([stature] if selected_character_id is not None
                         else [float(value) for value in stature_values])
    report["stature"]["required_m"] = required_statures
    if not any(math.isclose(stature, value, abs_tol=1e-9, rel_tol=0.0) for value in required_statures):
        fail("unexpected-stature", f"render stature {stature!r} is outside the required stature set")
    report["stature"]["missing_m"] = [value for value in required_statures
        if not math.isclose(stature, value, abs_tol=1e-9, rel_tol=0.0)]
    expected_ids = list(expected_character_ids)
    if not expected_ids or len(set(expected_ids)) != len(expected_ids):
        fail("invalid-registry", "expected character IDs must be nonempty and unique")
        return report
    try:
        from humanmotionlib.characters import _load_yaml
        registry = _load_yaml("characters/registry.yaml")
        registry_ids = [row["id"] for row in registry["characters"]]
    except (ValueError, KeyError, TypeError, OSError) as error:
        fail("invalid-registry", f"cannot resolve packaged character registry: {error}")
        return report
    if expected_ids != registry_ids:
        fail("invalid-registry", "expected_character_ids must equal the complete packaged registry order")
        return report
    if selected_character_id is not None and selected_character_id not in registry_ids:
        fail("invalid-registry", "selected_character_id is not present in the packaged registry")
        return report
    checked_ids = [selected_character_id] if selected_character_id is not None else expected_ids
    report["registry"]["checked_ids"] = list(checked_ids)
    report["registry"]["omitted_ids"] = [identifier for identifier in registry_ids
                                            if identifier not in checked_ids]
    report.update({"verification_scope": ("focused-visual" if _focused_visual else
                                          "selected-character-numeric-leaf" if selected_character_id
                                          else "complete-registry"),
                   "all_registry_ids": list(registry_ids),
                   "checked_character_ids": list(checked_ids),
                   "unassessed_character_ids": list(report["registry"]["omitted_ids"])})
    expected_ids = checked_ids
    if require_complete_diagnostic_coverage:
        from humanmotionlib.verify_skeleton import _diagonal_numeric_coverage_failures
        for detail in _diagonal_numeric_coverage_failures(prepared):
            fail("diagnostic-coverage", detail)
    try:
        request_path = run / "character-render-request.json"
        manifest_path = run / "render-manifest.json"
        request = _json(request_path)
        manifest = None if numeric_only else _json(manifest_path)
        unsigned = dict(request); identity = unsigned.pop("render_identity", None)
        if request.get("format") != "character-render-request/v1":
            fail("invalid-request", "unsupported character render request format")
        if identity != _content_hash(unsigned):
            fail("stale-request", f"artifact=character-render-request.json field=render_identity "
                 f"expected_sha256={_content_hash(unsigned)} observed_sha256={identity}; beat=not-applicable")
        if request.get("prepared_sha256") != prepared.get("content_sha256"):
            fail("stale-request", "artifact=character-render-request.json field=prepared_sha256 "
                 f"expected_sha256={prepared.get('content_sha256')} "
                 f"observed_sha256={request.get('prepared_sha256')}; beat=not-applicable")
        report["render_identity"] = identity
        ids = request.get("character_ids")
        report["registry"]["observed_ids"] = list(ids) if isinstance(ids, list) else []
        report["registry"]["missing_ids"] = [identifier for identifier in checked_ids if identifier not in report["registry"]["observed_ids"]]
        report["registry"]["extra_ids"] = [identifier for identifier in report["registry"]["observed_ids"] if identifier not in checked_ids]
        if ids != checked_ids:
            fail("registry-membership", "render request character selection differs from the declared verification scope")
        if not numeric_only:
            if manifest.get("format") != "character-render-manifest/v1":
                fail("manifest-format", "unsupported character manifest format")
            if manifest.get("render_identity") != identity or manifest.get("prepared_sha256") != prepared.get("content_sha256"):
                fail("stale-manifest", "artifact=render-manifest.json fields="
                     f"render_identity(expected={identity}, observed={manifest.get('render_identity')}), "
                     f"prepared_sha256(expected={prepared.get('content_sha256')}, "
                     f"observed={manifest.get('prepared_sha256')}); beat=not-applicable")
        descriptors = request.get("character_descriptors")
        if not isinstance(descriptors, list) or [row.get("id") for row in descriptors] != checked_ids:
            fail("descriptor-membership", "sealed character descriptors differ from the declared verification scope")
        manifest_characters = manifest.get("characters") if manifest is not None else None
        manifest_ids = [row.get("id") for row in manifest_characters if isinstance(row, Mapping)] if isinstance(manifest_characters, list) else []
        expected_sample_ids = [row.get("id") for row in samples]
        if not numeric_only:
            if manifest_ids != expected_ids:
                fail("manifest-membership", "manifest character membership is incomplete or reordered")
            for character in manifest_characters if isinstance(manifest_characters, list) else []:
                actual = [row.get("id") for row in character.get("samples", []) if isinstance(row, Mapping)]
                if actual != expected_sample_ids:
                    fail("manifest-samples", f"{character.get('id')} manifest sample inventory differs from prepared samples")
        verified_image_paths = []
        if not numeric_only and manifest_ids == expected_ids:
            verified_image_paths = _validate_manifest_images(manifest, prepared, run, expected_ids)
        _validate_request_closure(request, prepared, expected_ids)
        from humanmotionlib.render_contract import read_supervised_receipt
        required_paths = [Path("input.json"), Path("build-metadata.json"), Path("skeleton.blend"),
                          Path("character-render-request.json"),
                          Path("evaluated.json"), Path("geometry-reference.json")]
        if not numeric_only:
            required_paths.append(Path("render-manifest.json"))
        required_paths.extend(Path(path) for path in verified_image_paths)
        for identifier in expected_ids:
            if identifier != "skeleton":
                required_paths.extend((Path("characters") / identifier / "surface-reference.json",
                                       Path("characters") / identifier / "surface-evaluated.json"))
        generation_identity=None
        if _generation_anchor is not None:
            from humanmotionlib.package_resources import verify_runtime_integrity
            current=verify_runtime_integrity()
            anchor_identity=_generation_anchor.identity
            resource_delta=sorted(name for name in set(current["resources"])|set(anchor_identity["resource_hashes"])
                if current["resources"].get(name)!=anchor_identity["resource_hashes"].get(name))
            if (current["version"]!=anchor_identity["package_version"]
                    or current["backend_contract"]!=anchor_identity["backend_contract_sha256"]):
                raise ValueError("current canonical resources/backend contract differ from the trusted generator")
            for name in resource_delta:
                actual_pair=(anchor_identity["resource_hashes"].get(name),current["resources"].get(name))
                if not _is_reviewed_generation_doc_delta(name,*actual_pair):
                    raise ValueError(f"current resource delta is not an exact reviewed verifier-document change: {name}")
            package=prepared.get("package_identity",{})
            if (package.get("version")!=anchor_identity["package_version"]
                    or package.get("manifest_sha256")!=anchor_identity["runtime_manifest_sha256"]
                    or package.get("implementation")!=anchor_identity["implementation_hashes"]):
                raise ValueError("prepared input package identity differs from the trusted generation wheel")
            for logical,digest in prepared.get("source_hashes",{}).items():
                anchored=(anchor_identity["backend_contract_sha256"] if logical=="backend-contract.json"
                          else anchor_identity["resource_hashes"].get(logical))
                if anchored!=digest:
                    raise ValueError(f"prepared source hash differs from the trusted generation wheel: {logical}")
            generation_identity=anchor_identity
            report["generation_anchor"]={"wheel_sha256":_generation_anchor.wheel_sha256,
                "runtime_manifest_sha256":_generation_anchor.runtime_manifest_sha256,
                "noncanonical_resource_delta":{
                    name:{"generation_sha256":anchor_identity["resource_hashes"].get(name),
                          "verifier_sha256":current["resources"].get(name),
                          "classification":"reviewed verifier documentation only"}
                    for name in resource_delta},
                "scope":"read-only retained generator; verifier identity recorded separately"}
        receipt = read_supervised_receipt(
            run, prepared, required_paths,
            expected_operation="build" if numeric_only else "render-pass",
            trusted_generation_identity=generation_identity)
        from humanmotionlib.package_resources import manifest_sha256, verify_runtime_integrity
        verifier_package = verify_runtime_integrity()
        report["package_identity"] = {
            "generation": {key: receipt.get(key) for key in (
                "package_version", "runtime_manifest_sha256", "resource_hashes",
                "backend_contract_sha256", "implementation_hashes")},
            "verifier": {"package_version": verifier_package["version"],
                         "runtime_manifest_sha256": manifest_sha256(),
                         "resource_hashes": verifier_package["resources"],
                         "backend_contract_sha256": verifier_package["backend_contract"],
                         "implementation_hashes": verifier_package["implementation"]},
            "same_identity": all(receipt.get(key) == value for key, value in {
                "package_version": verifier_package["version"],
                "runtime_manifest_sha256": manifest_sha256(),
                "resource_hashes": verifier_package["resources"],
                "backend_contract_sha256": verifier_package["backend_contract"],
                "implementation_hashes": verifier_package["implementation"],
            }.items()),
        }
        phases = receipt.get("phases", [])
        for phase_name in ("backend_ready", "script_complete"):
            matching = [phase for phase in phases if phase.get("phase") == phase_name]
            if not matching or any(phase.get("render_identity") != identity
                                   or phase.get("character_ids") != checked_ids
                                   for phase in matching):
                fail("receipt-identity", f"supervised receipt {phase_name} identity or character set mismatch")

        if numeric_only and selected_character_id == "skeleton":
            evaluated = _json(run / "evaluated.json")
            from humanmotionlib.verify_skeleton import verify_transforms
            from humanmotionlib.backend_measurements import verify_backend
            transforms = verify_transforms(prepared, evaluated.get("samples"))
            backend = verify_backend(prepared, evaluated, transforms)
            report["skeleton_numeric"] = {"transforms": transforms, "backend": backend,
                                          "scope": "selected skeleton body/geometry/contact evidence"}
            if transforms.get("status") != "pass":
                fail("skeleton-transforms", "selected skeleton transform verification did not pass")
            if backend.get("status") != "pass":
                failed_checks = [check for sample in backend.get("samples", [])
                                 for check in sample.get("checks", []) if check.get("status") != "pass"]
                fail("skeleton-backend", f"selected skeleton backend verification failed {len(failed_checks)} checks")
            report["native"]["status"] = "pass" if not failures else "fail"
            report["native"]["characters"] = [{"character_id": "skeleton",
                "status": report["native"]["status"], "evidence": "skeleton-evaluated/v1"}]
            report["native_midpoints"]["status"] = "not-applicable-skeleton"
            report["dense"]["status"] = "not-applicable-skeleton"
            report["numeric_status"] = "pass" if not failures else "fail"
            report["status"] = "incomplete" if not failures else "fail"
            return report

        from humanmotionlib.character_surface import expand_surface, _rest_frames
        from humanmotionlib.character_skinning import compile_pose_skinning, source_world_transforms
        _, rest_frames = _rest_frames(profile, 1.0)
        surface_docs = {row.get("id"): row for row in request.get("characters", []) if isinstance(row, Mapping)}
        evaluated_by_character = {}
        canonical_surfaces = {}
        for identifier in expected_ids:
            record = {"character_id": identifier, "status": "fail", "samples": [], "worst_residual_m": None,
                      "worst_floor_m": None, "worst_sole_distance_m": None}
            report["native"]["characters"].append(record)
            if identifier == "skeleton":
                record["status"] = "skeleton-shared"
                continue
            try:
                reference = _json(run / "characters" / identifier / "surface-reference.json")
                evaluated = _json(run / "characters" / identifier / "surface-evaluated.json")
                canonical_metric=_canonical_reference_metric(evaluated,_generation_anchor is not None)
                if _generation_anchor is not None and not canonical_metric:
                    report["native"]["backend_combined_argmax_attestation"]=(
                        "incomplete: frozen generation predates canonical world metric declaration")
                elif canonical_metric:
                    report["native"]["backend_combined_argmax_attestation"]="verified canonical world metric"
                source = surface_docs.get(identifier)
                if source is None:
                    raise ValueError("sealed request has no numerical surface closure")
                definition = source.get("definition", {})
                expected_surface = expand_surface(profile, source["template"], source["appearance"], stature)
                if reference.get("format") != "hml-surface-reference/v1" or evaluated.get("format") != "hml-surface-evaluated/v1":
                    raise ValueError("unsupported surface evidence format")
                for document in (reference, evaluated):
                    if (document.get("prepared_sha256") != prepared.get("content_sha256")
                            or document.get("render_identity") != identity
                            or document.get("character_id") != identifier):
                        artifact = (f"characters/{identifier}/surface-reference.json" if document is reference
                                    else f"characters/{identifier}/surface-evaluated.json")
                        raise ValueError(f"artifact={artifact} stale identity fields: "
                            f"character_id(expected={identifier}, observed={document.get('character_id')}), "
                            f"prepared_sha256(expected={prepared.get('content_sha256')}, "
                            f"observed={document.get('prepared_sha256')}), "
                            f"render_identity(expected={identity}, observed={document.get('render_identity')}); "
                            "beat=not-applicable")
                if reference.get("profile_id") != profile.get("id") or reference.get("stature_m") != stature:
                    raise ValueError("surface reference profile/stature mismatch")
                if (reference.get("template_id") != definition.get("template_id")
                        or reference.get("appearance_id") != definition.get("appearance_id")):
                    raise ValueError("surface reference template/appearance identity mismatch")
                if reference.get("surface_sha256") != expected_surface["surface_sha256"]:
                    raise ValueError(f"artifact=characters/{identifier}/surface-reference.json field=surface_sha256 "
                        f"expected={expected_surface['surface_sha256']} observed={reference.get('surface_sha256')}; "
                        "beat=not-applicable")
                if request.get("surface_identities", {}).get(identifier) != reference.get("surface_sha256"):
                    raise ValueError(f"artifact=character-render-request.json/characters/{identifier}/surface-reference.json "
                        f"field=surface_sha256 expected={request.get('surface_identities',{}).get(identifier)} "
                        f"observed={reference.get('surface_sha256')}; beat=not-applicable")
                expected_components = {component["id"]: component for component in expected_surface["components"]}
                expected_component_order = sorted(expected_components)
                weight_set, component_offsets, carriers = _compiled_surface_weight_layout(
                    {identifier: list(expected_components.values())})
                canonical_surfaces[identifier] = list(expected_components.values())
                reference_components = {component.get("id"): component for component in reference.get("components", [])}
                if set(reference_components) != set(expected_components):
                    raise ValueError("surface reference component membership differs from template")
                for component_id, expected_component in expected_components.items():
                    observed_component = reference_components[component_id]
                    for field in ("material", "material_ids", "vertices_m", "vertex_ids", "faces", "face_materials", "weights"):
                        if _json_shape(observed_component.get(field)) != _json_shape(expected_component.get(field)):
                            raise ValueError(f"surface reference {component_id}.{field} differs from canonical expansion")
                    rest_vertices = observed_component.get("native_rest_vertices_m")
                    if not isinstance(rest_vertices, list) or len(rest_vertices) != len(expected_component["vertices_m"]):
                        raise ValueError(f"native rest vertex inventory mismatch for {identifier}/{component_id}")
                    rest_vertices = [_finite_vector(vertex, 3, f"{identifier}/{component_id} native rest vertex")
                                     for vertex in rest_vertices]
                    rest_residuals = [_distance(a,b) for a,b in zip(expected_component["vertices_m"],rest_vertices)]
                    max_rest = max(rest_residuals, default=0.0)
                    worst_rest_index = rest_residuals.index(max_rest) if rest_residuals else None
                    if max_rest > 1e-5*stature:
                        raise ValueError(f"native rest residual exceeds 1e-5H for {identifier}/{component_id}")
                    if (abs(float(observed_component.get("maximum_rest_residual_m", math.nan))-max_rest)>1e-9*stature
                            or observed_component.get("worst_rest_vertex_id") !=
                            (expected_component["vertex_ids"][worst_rest_index] if worst_rest_index is not None else None)):
                        raise ValueError(f"reported native rest residual mismatch for {identifier}/{component_id}")
                reference["components"] = [reference_components[component["id"]] for component in expected_surface["components"]]
                eval_samples = evaluated.get("samples")
                if not isinstance(eval_samples, list) or [row.get("sample_id") for row in eval_samples] != expected_sample_ids:
                    raise ValueError("surface evaluated sample inventory differs from prepared samples")
                expected_samples = {row["id"]: row for row in samples}
                worst_residual = (0.0, None); worst_floor = (math.inf, None); worst_sole = (0.0, None)
                for eval_sample in eval_samples:
                    sample_id = eval_sample["sample_id"]; expected_sample = expected_samples[sample_id]
                    fixture_id, authoritative_beat = _prepared_sample_context(expected_sample)
                    beat_text = _beat_label(authoritative_beat)
                    if (eval_sample.get("fixture") != expected_sample.get("fixture")
                            or eval_sample.get("beat") != expected_sample.get("beat")):
                        raise ValueError(f"surface sample metadata mismatch for {identifier}/{fixture_id}/{sample_id} "
                                         f"at beat={beat_text}; expected fixture/beat="
                                         f"{fixture_id}/{expected_sample.get('beat')}, observed="
                                         f"{eval_sample.get('fixture')}/{eval_sample.get('beat')}")
                    actual_components = {row.get("id"): row for row in eval_sample.get("components", [])}
                    if set(actual_components) != set(expected_components):
                        raise ValueError(f"surface component membership mismatch for sample {sample_id}")
                    pose_frames = expected_sample.get("frames", {})
                    sample_worst_residual = (0.0, None)
                    sample_floor = (math.inf, None)
                    transforms = source_world_transforms(profile,pose_frames,carriers,rest_frames=rest_frames)
                    compiled_pose = compile_pose_skinning(transforms,weight_set)
                    for component_id, expected_component in sorted(expected_components.items()):
                        actual_component = actual_components[component_id]
                        vertices = actual_component.get("vertices_m")
                        vertex_ids = actual_component.get("vertex_ids")
                        if vertex_ids != expected_component["vertex_ids"] or not isinstance(vertices, list) or len(vertices) != len(vertex_ids):
                            expected_ids = expected_component["vertex_ids"]
                            actual_ids = vertex_ids if isinstance(vertex_ids, list) else []
                            missing_ids = sorted(set(expected_ids)-set(actual_ids))
                            extra_ids = sorted(set(actual_ids)-set(expected_ids))
                            raise ValueError(f"evaluated topology mismatch for {identifier}/{fixture_id}/{sample_id} "
                                f"at beat={beat_text}, component={component_id}: vertex_count="
                                f"{len(vertices) if isinstance(vertices,list) else 'invalid'}/"
                                f"{len(expected_ids)} expected; vertex_id_count={len(actual_ids)}/"
                                f"{len(expected_ids)} expected; missing_ids={missing_ids[:5]}, "
                                f"extra_ids={extra_ids[:5]}")
                        vertices = [_finite_vector(vertex, 3, f"{identifier}/{sample_id}/{component_id} vertex") for vertex in vertices]
                        if any(_area(vertices, face) <= 1e-12*stature*stature for face in expected_component["faces"]):
                            raise ValueError(f"evaluated degenerate triangle for {identifier}/{sample_id}/{component_id}")
                        component_residuals=[]
                        for index, (rest_vertex, observed_vertex) in enumerate(zip(
                                expected_component["vertices_m"], vertices)):
                            expected_vertex = compiled_pose.apply(
                                rest_vertex,component_offsets[component_id]+index)
                            residual = _distance(expected_vertex, observed_vertex)
                            component_residuals.append(residual)
                            if residual > sample_worst_residual[0]:
                                sample_worst_residual = (residual, vertex_ids[index])
                        component_floor = _minimum_vertex_z(vertices,vertex_ids)
                        if component_floor[0] < sample_floor[0]:
                            sample_floor = component_floor
                        component_max=max(component_residuals,default=0.0)
                        component_worst=component_residuals.index(component_max) if component_residuals else None
                        # Evaluated vertices are world-space. Independently
                        # recompute the source-world DQ residual against them;
                        # the backend's aggregate reference maximum also includes
                        # its native-local residual, which cannot be reconstructed
                        # from a world-only vertex inventory.
                        reported_world=float(actual_component.get("maximum_source_world_residual_m",math.nan))
                        reported_local=float(actual_component.get("maximum_native_local_residual_m",math.nan))
                        if not _reference_residual_summary_matches(
                                actual_component,component_max,
                                vertex_ids[component_worst] if component_worst is not None else None,
                                vertex_ids,stature,canonical_metric=canonical_metric):
                            raise ValueError(f"reported DQ residual mismatch for {identifier}/{fixture_id}/{sample_id} "
                                f"at beat={beat_text}, component={component_id}, "
                                f"vertex={vertex_ids[component_worst] if component_worst is not None else 'none'}: "
                                f"source_world_residual_m={reported_world}, native_local_residual_m={reported_local}, "
                                f"recomputed_source_world_residual_m={component_max}, "
                                f"allowed_m={1e-5*stature} (1e-5H)")
                        reported_min = float(actual_component.get("minimum_z_m", math.nan))
                        reported_id = actual_component.get("worst_floor_vertex_id")
                        if not math.isfinite(reported_min) or abs(reported_min-component_floor[0]) > 1e-9*stature or reported_id != component_floor[1]:
                            raise ValueError(f"reported floor extremum mismatch for {identifier}/{fixture_id}/{sample_id} "
                                f"at beat={beat_text}, component={component_id}, vertex={component_floor[1]}: "
                                f"reported_z_m={reported_min}, recomputed_z_m={component_floor[0]}, "
                                f"reported_vertex={reported_id}")
                    if sample_floor < worst_floor: worst_floor = sample_floor
                    native_sample_floor = _native_sample_floor_extremum(actual_components,expected_component_order)
                    reported_sample_min = float(eval_sample.get("minimum_z_m", math.nan))
                    if (not math.isfinite(reported_sample_min)
                            or abs(reported_sample_min-native_sample_floor[0]) > 1e-9*stature
                            or eval_sample.get("worst_floor_vertex_id") != native_sample_floor[1]
                            or abs(native_sample_floor[0]-sample_floor[0]) > 1e-6*stature):
                        raise ValueError(f"reported sample floor extremum mismatch for {identifier}/{fixture_id}/{sample_id} "
                            f"at beat={beat_text}, vertex={native_sample_floor[1]}: "
                            f"reported_z_m={reported_sample_min}, recomputed_z_m={native_sample_floor[0]}, "
                            f"allowed_z_m={-1e-4*stature} (minimum Z >= -1e-4H)")
                    contacts = eval_sample.get("contacts")
                    if not isinstance(contacts, list):
                        raise ValueError(f"surface contact evidence missing for {identifier}/{sample_id}")
                    expected_anchors = _expected_anchor_positions(profile, expected_sample)
                    if {row.get("anchor_id") for row in contacts} != set(expected_anchors):
                        observed_anchors = sorted(str(row.get("anchor_id")) for row in contacts)
                        raise ValueError(f"surface anchor membership mismatch for {identifier}/{fixture_id}/{sample_id} "
                            f"at beat={beat_text}: observed={observed_anchors}, expected={sorted(expected_anchors)}")
                    for contact in contacts:
                        anchor_id = contact["anchor_id"]
                        anchor = _finite_vector(contact.get("anchor_m"), 3, f"{anchor_id} position")
                        if _distance(anchor, expected_anchors[anchor_id]) > 1e-6*stature:
                            measured_anchor_error = _distance(anchor, expected_anchors[anchor_id])
                            raise ValueError(f"surface evidence anchor position mismatch for {identifier}/{fixture_id}/"
                                f"{sample_id} at beat={beat_text}, anchor={anchor_id}: "
                                f"residual_m={measured_anchor_error}, allowed_m={1e-6*stature}")
                        side = anchor_id.rsplit(".", 1)[-1]
                        foot = actual_components.get("foot."+side)
                        if foot is None:
                            raise ValueError(f"surface contact has no foot component for {anchor_id}")
                        sole_distance = _closest_mesh_distance(anchor, foot["vertices_m"], expected_components["foot."+side]["faces"])
                        reported = float(contact.get("closest_sole_distance_m", math.nan))
                        if not math.isfinite(reported) or abs(reported-sole_distance)>1e-6*stature:
                            raise ValueError(f"reported sole distance mismatch for {identifier}/{fixture_id}/{sample_id} "
                                f"at beat={beat_text}, anchor={anchor_id}: reported_distance_m={reported}, "
                                f"recomputed_distance_m={sole_distance}, consistency_bound_m={1e-6*stature}")
                        if sole_distance>worst_sole[0]:worst_sole=(sole_distance,anchor_id)
                    residual_bound = 1e-5*stature
                    floor_bound = -1e-4*stature
                    if sample_worst_residual[0] > residual_bound:
                        fail("native-residual", f"character={identifier} fixture={fixture_id} sample={sample_id} "
                            f"beat={beat_text} component/vertex={sample_worst_residual[1]} "
                            f"source_world_residual_m={sample_worst_residual[0]} "
                            f"allowed_m={residual_bound} (<=1e-5H)")
                    if sample_floor[0] < floor_bound:
                        fail("floor-bound", f"character={identifier} fixture={fixture_id} sample={sample_id} "
                            f"beat={beat_text} vertex={sample_floor[1]} minimum_z_m={sample_floor[0]} "
                            f"allowed_z_m={floor_bound} (minimum Z >= -1e-4H)")
                    for contact in contacts:
                        if float(contact["closest_sole_distance_m"]) > 1e-3*stature:
                            anchor_id=contact["anchor_id"]
                            foot=actual_components["foot."+anchor_id.rsplit(".",1)[-1]]
                            measured=_closest_mesh_distance(_finite_vector(contact["anchor_m"],3,f"{anchor_id} position"),
                                foot["vertices_m"],expected_components["foot."+anchor_id.rsplit(".",1)[-1]]["faces"])
                            fail("sole-contact", f"character={identifier} fixture={fixture_id} sample={sample_id} "
                                f"beat={beat_text} anchor={anchor_id} anchor_to_sole_distance_m={measured} "
                                f"allowed_m={1e-3*stature} (<=1e-3H)")
                    record["samples"].append({"sample_id":sample_id,"worst_residual_m":sample_worst_residual[0],
                        "worst_vertex_id":sample_worst_residual[1],
                        "canonical_world_worst_residual_m":sample_worst_residual[0],
                        "canonical_world_worst_vertex_id":sample_worst_residual[1],
                        "backend_component_debug":[{"component_id":component_id,
                            "combined_worst_vertex_id":actual_components[component_id].get("worst_reference_vertex_id"),
                            "native_local_worst_vertex_id":actual_components[component_id].get("worst_native_local_vertex_id")}
                            for component_id in sorted(actual_components)],
                        "backend_combined_argmax_attestation":"verified" if canonical_metric else "incomplete",
                        "minimum_z_m":sample_floor[0],
                        "worst_floor_vertex_id":sample_floor[1],"contacts":len(contacts)})
                    if sample_worst_residual[0]>worst_residual[0]:worst_residual=(sample_worst_residual[0],sample_worst_residual[1])
                record.update({"status":"pass","surface_sha256":reference["surface_sha256"],
                               "worst_residual_m":worst_residual[0],"worst_vertex_id":worst_residual[1],
                               "worst_floor_m":worst_floor[0],"worst_floor_vertex_id":worst_floor[1],
                               "worst_sole_distance_m":worst_sole[0],"worst_anchor_id":worst_sole[1]})
                evaluated_by_character[identifier]=evaluated
            except (ValueError, TypeError, KeyError, IndexError, OSError, json.JSONDecodeError) as error:
                fail("surface-evidence", f"{identifier}: {error}")
                record["error"] = str(error)
        report["native"]["status"] = "fail" if failures else "pass"
        if report["native"]["status"] == "pass" and set(canonical_surfaces) == set(expected_ids)-{"skeleton"}:
            midpoint_report = _verify_native_midpoints(prepared,evaluated_by_character,
                                                       canonical_surfaces,stature)
            report["native_midpoints"] = midpoint_report
            if midpoint_report["status"] != "pass":
                for item in midpoint_report["failures"]:
                    fail("native-midpoint",item)
            dense_report = _run_dense_surface_audit(prepared,canonical_surfaces,stature,
                                                    report["dense"]["required_beats_by_fixture"])
            report["dense"].update(dense_report)
            if dense_report["status"] != "pass":
                for item in dense_report["failures"]:
                    fail("dense-reference",item)
        else:
            report["native_midpoints"]["status"] = "not-run-native-prerequisite-failed"
            report["dense"]["status"] = "not-run-native-prerequisite-failed"
        report["numeric_status"] = "fail" if failures else (
            "pass" if report["native"]["status"] == "pass"
            and report["native_midpoints"]["status"] == "pass"
            and report["dense"]["status"] == "pass"
            and report["fixture_coverage"]["status"] == "pass" else "incomplete")
        report["status"] = "fail" if failures else "incomplete"
        return report
    except (ValueError, TypeError, KeyError, OSError, json.JSONDecodeError) as error:
        fail("evidence-invalid", error)
        report["native"]["status"] = "fail"
        report["status"] = "fail"
        return report


__all__ = ["verify_character_output"]
