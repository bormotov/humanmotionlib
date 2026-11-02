# SPDX-License-Identifier: Apache-2.0
"""Pure deterministic expansion of the authored exercise mannequin surface."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import math
import re
from typing import Any


def _vec(value: Sequence[float], n: int, label: str) -> tuple[float, ...]:
    if isinstance(value, (str, bytes)) or len(value) != n:
        raise ValueError(f"{label} must have {n} numeric components")
    try:
        result = tuple(float(v) for v in value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{label} must have numeric components") from error
    if not all(math.isfinite(v) for v in result):
        raise ValueError(f"{label} must be finite")
    return result


def _add(a, b): return tuple(x + y for x, y in zip(a, b))
def _sub(a, b): return tuple(x - y for x, y in zip(a, b))
def _mul(a, k): return tuple(x * k for x in a)
def _dot(a, b): return sum(x * y for x, y in zip(a, b))
def _cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def _norm(a): return math.sqrt(_dot(a, a))


def _unit(a, label):
    length = _norm(a)
    if not math.isfinite(length) or length < 1e-12:
        raise ValueError(f"degenerate {label} frame")
    return _mul(a, 1.0 / length)


def _qmul(a, b):
    aw, ax, ay, az = a; bw, bx, by, bz = b
    return (aw*bw-ax*bx-ay*by-az*bz,
            aw*bx+ax*bw+ay*bz-az*by,
            aw*by-ax*bz+ay*bw+az*bx,
            aw*bz+ax*by-ay*bx+az*bw)


def _qrotate(q, v):
    q = _unit(_vec(q, 4, "orientation"), "orientation")
    x, y, z = _qmul(_qmul(q, (0.0, *v)), (q[0], -q[1], -q[2], -q[3]))[1:]
    return x, y, z


def _matrix_rotate(matrix, vector):
    return tuple(sum(float(matrix[row][column]) * vector[column] for column in range(3))
                 for row in range(3))


def _matrix_transpose_rotate(matrix, vector):
    return tuple(sum(float(matrix[row][column]) * vector[row] for row in range(3))
                 for column in range(3))


def _matrix_quaternion(matrix):
    """Convert an orthonormal 3x3 basis to a normalized wxyz quaternion."""
    m = matrix
    trace = m[0][0] + m[1][1] + m[2][2]
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        q = (0.25*s, (m[2][1]-m[1][2])/s, (m[0][2]-m[2][0])/s, (m[1][0]-m[0][1])/s)
    elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0]-m[1][1]-m[2][2]) * 2.0
        q = ((m[2][1]-m[1][2])/s, 0.25*s, (m[0][1]+m[1][0])/s, (m[0][2]+m[2][0])/s)
    elif m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1]-m[0][0]-m[2][2]) * 2.0
        q = ((m[0][2]-m[2][0])/s, (m[0][1]+m[1][0])/s, 0.25*s, (m[1][2]+m[2][1])/s)
    else:
        s = math.sqrt(1.0 + m[2][2]-m[0][0]-m[1][1]) * 2.0
        q = ((m[1][0]-m[0][1])/s, (m[0][2]+m[2][0])/s, (m[1][2]+m[2][1])/s, 0.25*s)
    return _unit(q, "neutral basis")


def _rest_frames(profile, stature_scale):
    rows = profile.get("structures")
    if not isinstance(rows, list):
        raise ValueError("profile must contain structures")
    by_id = {row.get("id"): row for row in rows if isinstance(row, Mapping)}
    frames = {}

    def resolve(identifier, trail=()):
        if identifier in frames:
            return frames[identifier]
        if identifier in trail or identifier not in by_id:
            raise ValueError(f"unresolved or cyclic structure frame {identifier}")
        row = by_id[identifier]
        q = _unit(_vec(row.get("rest_orientation", ()), 4, f"{identifier}.rest_orientation"),
                  f"{identifier} rest")
        t = _mul(_vec(row.get("rest_translation_m", ()), 3, f"{identifier}.rest_translation_m"), stature_scale)
        parent = row.get("parent")
        if parent is None:
            result = (q, t)
        else:
            pq, pt = resolve(parent, (*trail, identifier))
            result = (_unit(_qmul(pq, q), f"{identifier} global rest"),
                      _add(pt, _qrotate(pq, t)))
        frames[identifier] = result
        return result

    for identifier in by_id:
        resolve(identifier)
    return by_id, frames


def _landmark_rest(profile, by_id, frames, identifier, stature_scale):
    if identifier.endswith(".origin"):
        structure_id = identifier[:-7]
        if structure_id not in by_id:
            raise ValueError(f"unknown origin landmark {identifier}")
        return frames[structure_id][1]
    row = next((item for item in profile.get("landmarks", []) if item.get("id") == identifier), None)
    if row is None:
        raise ValueError(f"unknown surface landmark {identifier}")
    carrier = row.get("attachment_body")
    if carrier not in by_id:
        raise ValueError(f"unresolved landmark carrier {carrier} for {identifier}")
    neutral_basis = by_id[carrier].get("basis")
    neutral_origin = _mul(_vec(by_id[carrier].get("origin_m", ()), 3, f"{carrier}.origin_m"), stature_scale)
    neutral_position = _mul(_vec(row.get("position_m", ()), 3, f"{identifier}.position_m"), stature_scale)
    local = _matrix_transpose_rotate(neutral_basis, _sub(neutral_position, neutral_origin))
    q, t = frames[carrier]
    return _add(t, _qrotate(q, local))


def _carrier_origin_rest(carrier, by_id, frames):
    if carrier not in by_id:
        raise ValueError(f"unknown surface carrier {carrier}")
    return frames[carrier][1]


def _smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def _rings(control_rings, endpoints, appearance_scale=1.0):
    """Expand authored control rows to deterministic four-step loft rings."""
    controls = []
    for item in control_rings:
        span = item.get("span")
        if span not in endpoints:
            raise ValueError(f"unknown loft span {span}")
        start, end = endpoints[span]
        t = float(item["t"])
        center = _add(start, _mul(_sub(end, start), t))
        radii = _mul(_vec(item["radius_h"], 2, "control radius"), appearance_scale)
        if min(radii) <= 0.0:
            raise ValueError("control radii must be positive")
        controls.append((center, radii, span, t, item))
    if len(controls) < 2:
        raise ValueError("loft requires at least two control rings")
    expanded = []
    for index, current in enumerate(controls[:-1]):
        following = controls[index + 1]
        for step in range(4):
            alpha = step / 4.0
            center = _add(current[0], _mul(_sub(following[0], current[0]), alpha))
            radii = _add(current[1], _mul(_sub(following[1], current[1]), alpha))
            expanded.append((center, radii, current, following, alpha))
    expanded.append((*controls[-1][:2], controls[-1], controls[-1], 0.0))
    return expanded


def _weights_for_carrier(carrier):
    return {carrier: 1.0}


def _validate_welded_shoulder_component(component, allowed_carriers=None,
                                        expected_counts=(4162, 8320)):
    """Check the constructor's closed topology and regional binding contract."""
    vertices, ids, faces, weights = (component[key] for key in
                                     ("vertices_m", "vertex_ids", "faces", "weights"))
    expected_vertices, expected_faces = expected_counts
    if len(vertices) != expected_vertices or len(faces) != expected_faces:
        raise ValueError(f"welded shoulder topology mismatch: {len(vertices)} vertices, {len(faces)} triangles")
    if len(set(ids)) != len(ids) or len(vertices) != len(weights) or len(faces) != len(component["face_materials"]):
        raise ValueError("welded shoulder has duplicate IDs or inconsistent component arrays")
    directions = {}
    for face in faces:
        if len(face) != 3 or len(set(face)) != 3 or any(index < 0 or index >= len(vertices) for index in face):
            raise ValueError("welded shoulder has an invalid triangle")
        a,b,c=(vertices[index] for index in face)
        u=tuple(b[i]-a[i] for i in range(3));v=tuple(c[i]-a[i] for i in range(3))
        cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        if not all(math.isfinite(float(value)) for point in (a,b,c) for value in point) or \
                0.5*_norm(cross) <= 1e-12*float(component["stature_m"])**2:
            raise ValueError("welded shoulder has a non-finite or collapsed triangle")
        for x,y in zip(face,face[1:]+face[:1]):
            key=(min(x,y),max(x,y));directions.setdefault(key,[]).append(1 if x<y else -1)
    if any(len(value)!=2 or sum(value)!=0 for value in directions.values()):
        raise ValueError("welded shoulder is not a closed oriented manifold")
    used={index for face in faces for index in face}
    if len(used)!=len(vertices):
        raise ValueError("welded shoulder contains unused vertices")
    for vertex_id,row in zip(ids,weights):
        maximum=3 if vertex_id.startswith(("shoulder.R/", "shoulder.L/")) else 2
        if not row or len(row)>maximum or any(not math.isfinite(float(value)) or float(value)<0.0
                                               for value in row.values()) or \
                abs(math.fsum(float(value) for value in row.values())-1.0)>1e-12:
            raise ValueError(f"invalid surface weights at {vertex_id}: maximum influences {maximum}")
        if allowed_carriers is not None and not set(row).issubset(allowed_carriers):
            raise ValueError(f"unresolved surface carrier at {vertex_id}")
    return True


def _loft_component(component_id, expanded_rings, ring_n=32, radii_scale=1.0,
                    weight_function=None, material_function=None, mirror=False,
                    unit_scale=1.0, coordinate_scale=1.0, base_material="suit"):
    vertices, vertex_ids, weights = [], [], []
    frames = []
    previous_axis = None
    centers = [row[0] for row in expanded_rings]
    for index, center in enumerate(centers):
        if index == 0:
            tangent = _unit(_sub(centers[1], center), f"{component_id} initial tangent")
        elif index == len(centers) - 1:
            tangent = _unit(_sub(center, centers[index - 1]), f"{component_id} terminal tangent")
        else:
            tangent = _unit(_sub(centers[index + 1], centers[index - 1]), f"{component_id} tangent")
        projection = _sub((0.0, 1.0, 0.0), _mul(tangent, tangent[1]))
        axis_a = _unit(projection, f"{component_id} section anterior")
        if previous_axis is not None and _dot(axis_a, previous_axis) < 0.0:
            axis_a = _mul(axis_a, -1.0)
        axis_b = _unit(_cross(tangent, axis_a), f"{component_id} section transverse")
        previous_axis = axis_a
        frames.append((axis_a, axis_b))

    for ring_index, (center, radii, current, following, alpha) in enumerate(expanded_rings):
        radius_a, radius_b = _mul(radii, radii_scale)
        axis_a, axis_b = frames[ring_index]
        ring_weights = weight_function(ring_index, center, current, following, alpha) if weight_function else {"pelvis": 1.0}
        if mirror:
            center = (-center[0], center[1], center[2])
            axis_a = (-axis_a[0], axis_a[1], axis_a[2])
            axis_b = (-axis_b[0], axis_b[1], axis_b[2])
            ring_weights = {carrier.replace(".R", ".L"): value for carrier, value in ring_weights.items()}
        for sector in range(ring_n):
            theta = 2.0 * math.pi * sector / ring_n
            point = _add(_mul(center, coordinate_scale),
                         _add(_mul(axis_a, radius_a * unit_scale * math.cos(theta)),
                              _mul(axis_b, radius_b * unit_scale * math.sin(theta))))
            vertices.append(point)
            vertex_ids.append(f"{component_id}/ring.{ring_index:03d}/sector.{sector:02d}")
            weights.append(dict(ring_weights))

    faces = []
    material_ids = ["suit", "head_mitten", "foot"]
    face_materials = []
    for ring_index in range(len(expanded_rings) - 1):
        for sector in range(ring_n):
            nxt = (sector + 1) % ring_n
            a = ring_index * ring_n + sector
            b = ring_index * ring_n + nxt
            c = (ring_index + 1) * ring_n + nxt
            d = (ring_index + 1) * ring_n + sector
            faces.extend(((a, b, c), (a, c, d)))
            material = material_function(ring_index, sector) if material_function else "suit"
            face_materials.extend((material, material))

    start_center = tuple(sum(vertices[i][axis] for i in range(ring_n)) / ring_n for axis in range(3))
    end_base = (len(expanded_rings) - 1) * ring_n
    end_center = tuple(sum(vertices[end_base + i][axis] for i in range(ring_n)) / ring_n for axis in range(3))
    start_weights = dict(weights[0])
    end_weights = dict(weights[end_base])
    faces.extend((tuple([0, sector, (sector + 1) % ring_n]) for sector in range(ring_n)))
    start_cap = len(vertices); vertices.append(start_center); vertex_ids.append(f"{component_id}/cap.start"); weights.append(start_weights)
    # The start fan was temporarily built against index zero; rewrite to cap index.
    for face_index in range(len(faces)-ring_n, len(faces)):
        face = faces[face_index]
        faces[face_index] = (start_cap, face[1], face[2])
    faces.extend((tuple([end_base + sector, -1, end_base + (sector + 1) % ring_n]) for sector in range(ring_n)))
    end_cap = len(vertices); vertices.append(end_center); vertex_ids.append(f"{component_id}/cap.end"); weights.append(end_weights)
    for face_index in range(len(faces)-ring_n, len(faces)):
        face = faces[face_index]
        faces[face_index] = tuple(end_cap if index == -1 else index for index in face)
    if mirror:
        faces = [tuple(reversed(face)) for face in faces]
    face_materials.extend((base_material,) * (2 * ring_n))
    return {"id": component_id, "material": base_material, "material_ids": material_ids,
            "face_materials": face_materials, "vertices_m": vertices,
            "vertex_ids": vertex_ids, "faces": [list(face) for face in faces],
            "weights": weights}


def _weld_shoulder(torso, arm_r, arm_l, join, stature, torso_weight_function=None, profile=None):
    """Replace closed torso/arm caps with a deterministic shared shoulder bridge."""
    if join.get("constructor") != "welded_shoulder_bridge":
        raise ValueError("unsupported shoulder_join constructor")
    ring_n = 32
    lower_rings = tuple(range(24, 32))
    sectors = (28, 29, 30, 31, 0, 1, 2, 3)
    join_ring = int(join.get("arm_join_ring", -1))
    if tuple(join.get("torso_lower_rings", ())) != (24, 31) or \
            tuple(join.get("torso_lower_sectors_right", ())) != sectors or \
            join_ring != 8 or int(join.get("bridge_intermediate_loops", 0)) != 3:
        raise ValueError("unsupported welded shoulder bridge descriptor")

    torso_id_to_index = {name: i for i, name in enumerate(torso["vertex_ids"])}
    arm_id_to_index = {name: i for i, name in enumerate(arm_r["vertex_ids"])}
    expected_torso_boundary = []
    for side in ("R", "L"):
        # Explicit ordered loop around the removed patch.
        if side == "R":
            loop = [(32, 0)] + [(32, s) for s in (1, 2, 3, 4)] + \
                   [(r, 4) for r in range(31, 23, -1)] + \
                   [(24, s) for s in (3, 2, 1, 0, 31, 30, 29, 28)] + \
                   [(r, 28) for r in range(25, 33)] + [(32, s) for s in (29, 30, 31)]
        else:
            right_loop = [(32, 0)] + [(32, s) for s in (1, 2, 3, 4)] + \
                         [(r, 4) for r in range(31, 23, -1)] + \
                         [(24, s) for s in (3, 2, 1, 0, 31, 30, 29, 28)] + \
                         [(r, 28) for r in range(25, 33)] + [(32, s) for s in (29, 30, 31)]
            loop = [(r, (16-s) % ring_n) for r, s in reversed(right_loop)]
        if len(loop) != 32:
            raise ValueError("welded shoulder loop must contain 32 unique vertices")
        a_indices = [torso_id_to_index[f"torso/ring.{r:03d}/sector.{s:02d}"] for r, s in loop]
        arm_component = arm_r if side == "R" else arm_l
        arm_id_to_index_side = {name: i for i, name in enumerate(arm_component["vertex_ids"])}
        b_indices = [arm_id_to_index_side[
            f"arm.{side}/ring.{join_ring:03d}/sector.{((8-j) if side=='R' else (j-23))%ring_n:02d}"]
            for j in range(32)]
        expected_torso_boundary.append((side, a_indices, b_indices, loop))

    # Compute the exact source triangle patches and the vertices made unused by them.
    patch_cells = {(r, s) for r in lower_rings for s in sectors}
    patch_cells.update((r, s) for r in lower_rings for s in range(12, 20))
    remove_faces = set()
    for face_index, face in enumerate(torso["faces"]):
        face_ids = [torso["vertex_ids"][v] for v in face]
        parsed = []
        for value in face_ids:
            parts = value.split("/")
            if len(parts) != 3 or not parts[1].startswith("ring.") or not parts[2].startswith("sector."):
                parsed = []
                break
            parsed.append((int(parts[1][5:]), int(parts[2][7:])))
        if parsed and len({row[0] for row in parsed}) == 2:
            low = min(row[0] for row in parsed)
            sector_set = {row[1] for row in parsed}
            for cell_ring, cell_sector in patch_cells:
                if low == cell_ring and sector_set <= {cell_sector, (cell_sector+1)%ring_n}:
                    remove_faces.add(face_index)
                    break
    if len(remove_faces) != 2*8*8*2:
        raise ValueError(f"shoulder torso patches must remove 256 triangles, got {len(remove_faces)}")
    removed_torso_vertices = {f"torso/ring.{r:03d}/sector.{s:02d}" for r in range(25,32)
                              for s in (29,30,31,0,1,2,3,13,14,15,16,17,18,19)}
    kept_torso_ids = [v for i,v in enumerate(torso["vertex_ids"])
                      if v not in removed_torso_vertices]
    if len(removed_torso_vertices) != 98:
        raise AssertionError("unexpected mirrored torso patch interior size")

    vertices = [torso["vertices_m"][torso_id_to_index[v]] for v in kept_torso_ids]
    ids = list(kept_torso_ids)
    weights = [torso["weights"][torso_id_to_index[v]] for v in kept_torso_ids]
    index_map = {torso_id_to_index[v]: i for i,v in enumerate(kept_torso_ids)}
    faces, face_materials = [], []
    for i, face in enumerate(torso["faces"]):
        if i in remove_faces:
            continue
        assembled = [index_map[v] for v in face]
        if all(torso["vertex_ids"][v] == "torso/cap.end" or
               torso["vertex_ids"][v].startswith("torso/ring.") and
               int(torso["vertex_ids"][v].split("/ring.")[1].split("/")[0]) == 36 for v in face):
            assembled.reverse()
        faces.append(assembled)
        face_materials.append(torso["face_materials"][i])

    bridge_ranges = {}
    for side, a_indices, b_indices, loop in expected_torso_boundary:
        arm_component = arm_r if side == "R" else arm_l
        arm_id_index = {name: i for i,name in enumerate(arm_component["vertex_ids"])}
        # Retain original distal arm rings (including ring 8) and end cap; discard the proximal cap.
        keep_arm = [i for i,name in enumerate(arm_component["vertex_ids"])
                    if name.endswith("cap.end") or ("/ring." in name and int(name.split("/ring.")[1].split("/")[0]) >= join_ring)]
        arm_map = {}
        for old in keep_arm:
            arm_map[old] = len(vertices)
            vertices.append(arm_component["vertices_m"][old]); ids.append(arm_component["vertex_ids"][old])
            weights.append(arm_component["weights"][old])
        for fi, face in enumerate(arm_component["faces"]):
            if all(v in arm_map for v in face):
                faces.append([arm_map[v] for v in face]); face_materials.append(arm_component["face_materials"][fi])
        # Reversal is an orientation-only repair for the authored distal cap.
        cap_range = range(len(faces)-ring_n, len(faces))
        for fi in cap_range:
            faces[fi].reverse()
        a_new = [index_map[i] for i in a_indices]
        b_new = [arm_map[i] for i in b_indices]
        intermediate = []
        for loop_number, u in enumerate((0.25,0.5,0.75), start=1):
            row=[]
            blend=3*u*u-2*u*u*u
            for j,(ai,bi) in enumerate(zip(a_new,b_new)):
                av,bv=vertices[ai],vertices[bi]
                row.append(len(vertices)); vertices.append(tuple((1-u)*av[k]+u*bv[k] for k in range(3)))
                ids.append(f"shoulder.{side}/loop.{loop_number}/sector.{j:02d}")
                wa,wb=weights[ai],weights[bi]
                merged={key:value*(1-blend) for key,value in wa.items()}
                for key,value in wb.items(): merged[key]=merged.get(key,0.0)+value*blend
                weights.append({key:value for key,value in merged.items() if value>0.0})
            intermediate.append(row)
        loops=[a_new,*intermediate,b_new]
        bridge_face_indices=[]
        for lower,upper in zip(loops,loops[1:]):
            for j in range(ring_n):
                nxt=(j+1)%ring_n
                a,b,c,d=lower[j],lower[nxt],upper[nxt],upper[j]
                bridge_face_indices.extend((len(faces),len(faces)+1))
                faces.extend(([a,b,c],[a,c,d])); face_materials.extend(("suit","suit"))
        bridge_ranges[side]=(a_new,b_new,bridge_face_indices)

    # Resolve bridge winding from the actual retained boundary faces and verify the join is oriented.
    def edge_use(face_list, a, b):
        for face in face_list:
            for x,y in zip(face,face[1:]+face[:1]):
                if x==a and y==b:return 1
                if x==b and y==a:return -1
        return 0
    for side,(a_loop,b_loop,bridge_indices) in bridge_ranges.items():
        a_source_edge=edge_use(faces[:len(faces)-3*32*2],a_loop[0],a_loop[1])
        if not a_source_edge: raise ValueError(f"{side} torso shoulder seam is not a source boundary")
        # Current strip edge uses A[j] -> A[j+1]. It must oppose the source boundary.
        bridge_edge=edge_use([faces[i] for i in bridge_indices],a_loop[0],a_loop[1])
        if bridge_edge != -a_source_edge:
            for i in bridge_indices: faces[i].reverse()
        # One connected closed oriented manifold is mandatory.
    component={"id":"torso","material":"suit","material_ids":["suit","head_mitten","foot"],
            "face_materials":face_materials,"vertices_m":vertices,"vertex_ids":ids,
            "faces":faces,"weights":weights,"shoulder_bridge_vertex_ids":[v for v in ids if v.startswith("shoulder.")],
            "stature_m":stature}
    construction=[None]*len(ids); side_map=[None]*len(ids)
    seam_side={}
    bridge_z={}
    assembled_id_to_index={name:i for i,name in enumerate(ids)}
    for side,a_loop,b_loop,_ in expected_torso_boundary:
        arm_component=arm_r if side=="R" else arm_l
        for j,(ai,bi) in enumerate(zip(a_loop,b_loop)):
            a_id=torso["vertex_ids"][ai]; b_id=arm_component["vertex_ids"][bi]
            a_index=assembled_id_to_index[a_id]; b_index=assembled_id_to_index[b_id]
            z=vertices[a_index][2]/stature
            seam_side[a_index]=(side,0.0,z); seam_side[b_index]=(side,1.0,z)
            bridge_z[(side,j)]=z
    for index,vertex_id in enumerate(ids):
        if index in seam_side:
            side,u,z=seam_side[index]; construction[index]=(u,z); side_map[index]=side
        elif vertex_id.startswith("shoulder.") and "/loop." in vertex_id:
            match=re.fullmatch(r"shoulder\.([RL])/loop\.(\d+)/sector\.(\d+)",vertex_id)
            if not match: raise ValueError("invalid shoulder bridge vertex ID")
            side,loop_number,sector=match.group(1),int(match.group(2)),int(match.group(3))
            construction[index]=(loop_number/4.0,bridge_z[(side,sector)]); side_map[index]=side
    component["shoulder_construction_coordinates"]=construction
    component["shoulder_side_by_vertex"]=side_map
    # Paired anatomical-neutral seam references are retained privately for the
    # one-time R6 rest-shape operation. Refinement propagates these by midpoint.
    if profile is not None:
        from humanmotionlib.character_skinning import skin_vertex, source_world_transforms
        scale=stature/float(profile["stature_m"])
        neutral_by_id,neutral_rest_frames=_rest_frames(profile,scale)
        neutral_frames={identifier:{"position_m":_mul(_vec(row.get("origin_m",()),3,identifier+".origin_m"),scale),
                                    "rotation":row.get("basis")}
                        for identifier,row in neutral_by_id.items()}
        neutral_transforms=source_world_transforms(profile,neutral_frames,tuple(neutral_rest_frames),
                                                    rest_frames=neutral_rest_frames)
    else:
        neutral_transforms=None
    endpoint_refs=[None]*len(ids)
    for side,a_loop,b_loop,_ in expected_torso_boundary:
        for sector,(ai,bi) in enumerate(zip(a_loop,b_loop)):
            a_index=assembled_id_to_index[torso["vertex_ids"][ai]]
            arm_component=arm_r if side=="R" else arm_l
            arm_id=arm_component["vertex_ids"][bi]
            b_index=assembled_id_to_index[arm_id]
            if neutral_transforms is None:
                pair=(vertices[a_index],vertices[b_index])
            else:
                pair=(skin_vertex(vertices[a_index],weights[a_index],neutral_transforms),
                      skin_vertex(vertices[b_index],weights[b_index],neutral_transforms))
            endpoint_refs[a_index]=(pair[0],pair[1])
            endpoint_refs[b_index]=(pair[0],pair[1])
            for loop_number in (1,2,3):
                bridge_index=assembled_id_to_index[f"shoulder.{side}/loop.{loop_number}/sector.{sector:02d}"]
                endpoint_refs[bridge_index]=(pair[0],pair[1])
    component["shoulder_endpoint_references"]=endpoint_refs
    allowed_carriers={carrier for source in (torso,arm_r,arm_l)
                      for row in source["weights"] for carrier in row}
    refinement_passes=int(join.get("refinement_passes",0))
    if refinement_passes not in (0,2):
        raise ValueError("unsupported shoulder refinement pass count")
    refinement_fields={"position_rule","interior_relaxation","boundary_rule",
                       "weight_rule","maximum_rest_deviation_h"}
    if refinement_passes==0 and refinement_fields.intersection(join):
        raise ValueError("incomplete shoulder refinement descriptor")
    if refinement_passes:
        _refine_shoulder_component(component, join, stature, torso_weight_function)
    if "arms_down_profile" in join:
        if profile is None:
            raise ValueError("canonical-neutral shoulder shaping requires the source profile")
        _shape_shoulder_line(component, join, profile, stature)
    _validate_welded_shoulder_component(component,allowed_carriers,
                                         (8194,16384) if refinement_passes else (4162,8320))
    component.pop("shoulder_construction_coordinates",None)
    component.pop("shoulder_side_by_vertex",None)
    component.pop("shoulder_endpoint_references",None)
    component.pop("shoulder_shape_measurements",None)
    return component


def _refine_shoulder_component(component, join, stature, torso_weight_function):
    """Deterministically refine and relax only the connected shoulder bridge."""
    if (join.get("position_rule") != "midpoint_then_neighbor_average" or
            join.get("boundary_rule") != "fixed_conforming_midpoints" or
            join.get("weight_rule") != "construction_coordinates" or
            float(join.get("interior_relaxation", -1)) != 0.25 or
            float(join.get("maximum_rest_deviation_h", -1)) != 0.005 or
            torso_weight_function is None):
        raise ValueError("unsupported shoulder refinement descriptor")
    vertices, ids, faces = component["vertices_m"], component["vertex_ids"], component["faces"]
    weights, materials = component["weights"], component["face_materials"]
    # Coordinates are only needed for shoulder vertices and their seam neighbors.
    coords = component.get("shoulder_construction_coordinates")
    if coords is None or len(coords) != len(vertices):
        raise ValueError("shoulder construction coordinates are incomplete")
    side_for_vertex = component.get("shoulder_side_by_vertex")
    if side_for_vertex is None or len(side_for_vertex) != len(vertices):
        raise ValueError("shoulder construction side map is incomplete")
    endpoint_refs=component.get("shoulder_endpoint_references")
    if endpoint_refs is None or len(endpoint_refs)!=len(vertices):
        raise ValueError("shoulder endpoint reference records are incomplete")
    relaxation = float(join["interior_relaxation"])

    selected = [any(ids[v].startswith(("shoulder.R/loop.", "shoulder.L/loop.")) for v in face)
                for face in faces]
    for pass_number in (1, 2):
        selected_edges = set()
        for active, face in zip(selected, faces):
            if active:
                selected_edges.update((min(a,b),max(a,b)) for a,b in zip(face,face[1:]+face[:1]))
        def edge_key(edge): return tuple(sorted((ids[edge[0]], ids[edge[1]])))
        ordered_edges = sorted(selected_edges, key=edge_key)
        midpoint = {}
        for ordinal, edge in enumerate(ordered_edges):
            a,b=edge; ca,cb=coords[a],coords[b]
            if ca is None or cb is None or side_for_vertex[a] != side_for_vertex[b]:
                raise ValueError("shoulder refinement edge lacks compatible construction coordinates")
            side=side_for_vertex[a]
            new_index=len(vertices)
            midpoint[edge]=new_index
            vertices.append(tuple((vertices[a][k]+vertices[b][k])*0.5 for k in range(3)))
            ids.append(f"shoulder.{side}/refine.{pass_number}/edge.{ordinal:06d}")
            u=(ca[0]+cb[0])*0.5; z=(ca[1]+cb[1])*0.5
            coords.append((u,z)); side_for_vertex.append(side)
            ra,rb=endpoint_refs[a],endpoint_refs[b]
            if ra is None or rb is None:
                raise ValueError("refined shoulder vertex lacks endpoint references")
            endpoint_refs.append((tuple((ra[0][k]+rb[0][k])*0.5 for k in range(3)),
                                  tuple((ra[1][k]+rb[1][k])*0.5 for k in range(3))))
            torso_weights=torso_weight_function(z)
            blend=3*u*u-2*u*u*u
            carrier=f"humerus.{side}"
            row={key:value*(1.0-blend) for key,value in torso_weights.items()}
            row[carrier]=row.get(carrier,0.0)+blend
            weights.append({key:value for key,value in row.items() if value>0.0})

        def split_face(face):
            v0,v1,v2=face
            m01=midpoint.get((min(v0,v1),max(v0,v1)))
            m12=midpoint.get((min(v1,v2),max(v1,v2)))
            m20=midpoint.get((min(v2,v0),max(v2,v0)))
            count=sum(m is not None for m in (m01,m12,m20))
            if count==0:return [face]
            if count==1:
                if m01 is not None:return [(v0,m01,v2),(m01,v1,v2)]
                if m12 is not None:return [(v1,m12,v0),(m12,v2,v0)]
                return [(v2,m20,v1),(m20,v0,v1)]
            if count==2:
                if m01 is not None and m12 is not None:
                    corner=(m01,v1,m12); quad=(v0,m01,m12,v2)
                elif m12 is not None and m20 is not None:
                    corner=(m12,v2,m20); quad=(v1,m12,m20,v0)
                else:
                    corner=(m20,v0,m01); quad=(v2,m20,m01,v1)
                d0=tuple(sorted((ids[quad[0]],ids[quad[2]])))
                d1=tuple(sorted((ids[quad[1]],ids[quad[3]])))
                if d0<=d1:return [corner,(quad[0],quad[1],quad[2]),(quad[0],quad[2],quad[3])]
                return [corner,(quad[0],quad[1],quad[3]),(quad[1],quad[2],quad[3])]
            return [(v0,m01,m20),(m01,v1,m12),(m20,m12,v2),(m01,m12,m20)]

        next_faces=[]; next_materials=[]; next_selected=[]
        for face,material,active in zip(faces,materials,selected):
            children=split_face(face)
            next_faces.extend(children); next_materials.extend([material]*len(children))
            next_selected.extend([active]*len(children))
        faces[:]=next_faces; materials[:]=next_materials
        selected=next_selected
        # Smooth only selected-region interior vertices using a simultaneous update.
        selected_edges_after=set(); selected_vertices=set(); boundary_vertices=set()
        for active,face in zip(next_selected,faces):
            if active:
                selected_vertices.update(face)
                selected_edges_after.update((min(a,b),max(a,b)) for a,b in zip(face,face[1:]+face[:1]))
        for active,face in zip(next_selected,faces):
            if not active:
                boundary_vertices.update(v for v in face if any((min(v,o),max(v,o)) in selected_edges_after for o in face if o!=v))
        seam_vertices={v for v,coord in enumerate(coords) if coord is not None and coord[0] in (0.0,1.0)}
        fixed=boundary_vertices|seam_vertices
        adjacency={v:set() for v in selected_vertices}
        for a,b in selected_edges_after:
            adjacency.setdefault(a,set()).add(b); adjacency.setdefault(b,set()).add(a)
        old_positions=list(vertices)
        for v in sorted(selected_vertices-fixed):
            neighbors=adjacency.get(v,set())
            if not neighbors:continue
            mean=tuple(math.fsum(old_positions[n][k] for n in sorted(neighbors))/len(neighbors) for k in range(3))
            vertices[v]=tuple((1.0-relaxation)*old_positions[v][k]+relaxation*mean[k] for k in range(3))

    component["shoulder_construction_coordinates"]=coords
    component["shoulder_side_by_vertex"]=side_for_vertex
    component["shoulder_endpoint_references"]=endpoint_refs
    component["shoulder_bridge_vertex_ids"]=[name for name in ids if name.startswith(("shoulder.R/","shoulder.L/"))]


def _shape_shoulder_line(component, join, profile, stature):
    """Author the frozen R6 upper shoulder contour once in neutral space."""
    descriptor=join["arms_down_profile"]
    if (descriptor.get("kind")!="canonical_neutral_upper_plateau_v1" or
            float(descriptor.get("support_start_z_h",-1))!=0.810 or
            float(descriptor.get("support_end_z_h",-1))!=0.840 or
            float(descriptor.get("plateau_end_u",-1))!=0.5 or
            float(descriptor.get("maximum_rest_deviation_h",-1))!=0.020):
        raise ValueError("unsupported arms-down shoulder profile descriptor")
    coords=component.get("shoulder_construction_coordinates")
    refs=component.get("shoulder_endpoint_references")
    if coords is None or refs is None or len(coords)!=len(component["vertices_m"]) or len(refs)!=len(coords):
        raise ValueError("shoulder shaping references are incomplete")
    from humanmotionlib.character_skinning import inverse_skin_vertex, skin_vertex, source_world_transforms
    scale=stature/float(profile["stature_m"])
    by_id,rest_frames=_rest_frames(profile,scale)
    neutral_frames={identifier:{"position_m":_mul(_vec(row.get("origin_m",()),3,identifier+".origin_m"),scale),
                               "rotation":row.get("basis")}
                    for identifier,row in by_id.items()}
    transforms=source_world_transforms(profile,neutral_frames,tuple(rest_frames),rest_frames=rest_frames)
    vertices=component["vertices_m"]
    original=list(vertices)
    changed=[]
    start=float(descriptor["support_start_z_h"])
    end=float(descriptor["support_end_z_h"])
    for index,(coord,pair) in enumerate(zip(coords,refs)):
        if coord is None or pair is None:
            continue
        u,anchor_z=coord
        if not (0.0<u<1.0) or not component["vertex_ids"][index].startswith(("shoulder.R/","shoulder.L/")):
            continue
        a,b=pair
        q=_smooth((a[2]/stature-start)/(end-start))
        if q<=0.0:
            continue
        weights=component["weights"][index]
        neutral=skin_vertex(vertices[index],weights,transforms)
        d=0.0 if u<=float(descriptor["plateau_end_u"]) else _smooth((u-float(descriptor["plateau_end_u"]))/(1.0-float(descriptor["plateau_end_u"])))
        target_z=(1.0-d)*a[2]+d*b[2]
        shaped=(neutral[0],neutral[1],(1.0-q)*neutral[2]+q*target_z)
        rest=inverse_skin_vertex(shaped,weights,transforms)
        delta=_norm(_sub(rest,original[index]))/stature
        if not math.isfinite(delta) or delta>float(descriptor["maximum_rest_deviation_h"]):
            raise ValueError(f"arms-down shoulder correction exceeds bound at {component['vertex_ids'][index]}: "
                             f"delta_h={delta}, u={u}, anchor_z_h={anchor_z}, a_z_h={a[2]/stature}, "
                             f"A_N={a}, B_N={b}, N={neutral}, target_z={target_z}, support={q}")
        vertices[index]=rest
        changed.append((index,neutral,shaped,delta,u,anchor_z))
    if not changed:
        raise ValueError("arms-down shoulder profile selected no bridge vertices")
    component["shoulder_shape_measurements"]={
        "changed_vertices":len(changed),
        "maximum_rest_deviation_h":max(row[3] for row in changed),
        "upper_plateau_samples":sum(row[4]<=float(descriptor["plateau_end_u"]) and abs(row[1][2]/stature-end)<=1e-9 for row in changed),
    }


def expand_surface(profile: Mapping[str, Any], template_doc: Mapping[str, Any],
                   appearance_doc: Mapping[str, Any], stature_m: float) -> dict[str, Any]:
    """Expand the frozen template into deterministic rest vertices and weights."""
    stature = float(stature_m)
    if not math.isfinite(stature) or stature <= 0.0:
        raise ValueError("stature_m must be finite and positive")
    if profile.get("id") != template_doc.get("compatible_profile"):
        raise ValueError("surface template is incompatible with profile")
    height = float(profile.get("stature_m", 0.0))
    if not math.isfinite(height) or height <= 0.0:
        raise ValueError("profile stature_m must be finite and positive")
    scale = stature / height
    by_id, rest_frames = _rest_frames(profile, scale)
    components = []
    source_components = {item.get("id"): item for item in template_doc.get("components", [])}
    if not all(identifier in source_components for identifier in ("torso", "head", "arm.R", "leg.R", "foot.R")):
        raise ValueError("template is missing a required surface component")

    # Torso loft: each control interval is subdivided into four equal spans.
    torso_source = source_components["torso"]
    torso_controls = torso_source.get("control_rings", [])
    if "torso_radii_h" in appearance_doc:
        raise ValueError("absolute appearance torso_radii_h is unsupported; use torso_radii_delta_h")
    torso_deltas = appearance_doc.get("torso_radii_delta_h")
    if not isinstance(torso_controls, list) or not isinstance(torso_deltas, list) or \
            len(torso_controls) != 10 or len(torso_deltas) != 10:
        raise ValueError("shared template and appearance must provide exactly ten torso radius rows")
    torso_radii = []
    for index, (control, delta_source) in enumerate(zip(torso_controls, torso_deltas)):
        if "radii_source" in control or "radius_h" not in control:
            raise ValueError("torso control rings require shared base radius_h values")
        base = _vec(control["radius_h"], 2, "shared torso radius_h")
        delta = _vec(delta_source, 2, "appearance torso_radii_delta_h")
        effective = _add(base, delta)
        if min(base) <= 0.0:
            raise ValueError(f"shared torso base radius must be positive at ring {index}")
        if not all(math.isfinite(value) and value > 0.0 for value in effective):
            raise ValueError(f"effective torso radius must be finite and positive at ring {index}")
        torso_radii.append(effective)
    if appearance_doc.get("id") == "male-v1" and any(
            delta != (0.0, 0.0) for delta in (_vec(row, 2, "appearance torso delta") for row in torso_deltas)):
        raise ValueError("male-v1 torso_radii_delta_h must be exactly zero")
    torso_rings = []
    for index in range(len(torso_controls) - 1):
        first_z = float(torso_controls[index]["z_h"])
        second_z = float(torso_controls[index + 1]["z_h"])
        first_r = torso_radii[index]
        second_r = torso_radii[index + 1]
        if min(*first_r, *second_r) <= 0.0 or second_z <= first_z:
            raise ValueError("torso control rings must have positive radii and increasing heights")
        for step in range(4):
            alpha = step / 4.0
            z_h = first_z + (second_z - first_z) * alpha
            radii_h = _add(first_r, _mul(_sub(second_r, first_r), alpha))
            torso_rings.append(((0.0, 0.0, z_h), radii_h))
    torso_rings.append(((0.0, 0.0, float(torso_controls[-1]["z_h"])), torso_radii[-1]))
    chain = torso_source["weighting"]["carriers"]
    chain_z = sorted(((_carrier_origin_rest(carrier, by_id, rest_frames)[2], carrier)
                      for carrier in chain), key=lambda pair: (pair[0], pair[1]))
    if len({round(z, 12) for z, _ in chain_z}) != len(chain_z):
        raise ValueError("torso carrier origins have equal z values")

    def torso_weight(z_h):
        z = z_h * stature
        if z <= chain_z[0][0]:
            return {chain_z[0][1]: 1.0}
        if z >= chain_z[-1][0]:
            return {chain_z[-1][1]: 1.0}
        for (lower_z, lower_id), (upper_z, upper_id) in zip(chain_z, chain_z[1:]):
            if lower_z <= z <= upper_z:
                blend = _smooth((z - lower_z) / (upper_z - lower_z))
                return {carrier: weight for carrier, weight in ((lower_id, 1.0-blend), (upper_id, blend)) if weight > 0.0}
        raise AssertionError("unreachable torso chain bracket")

    torso_vertices, torso_ids, torso_weights = [], [], []
    ring_n = int(template_doc["topology"]["loft_ring_vertices"])
    if ring_n < 3:
        raise ValueError("loft ring must have at least three vertices")
    for ri, ((_, _, z_h), radii_h) in enumerate(torso_rings):
        rx, ry = _mul(radii_h, stature)
        for sector in range(ring_n):
            theta = 2.0 * math.pi * sector / ring_n
            torso_vertices.append((rx * math.cos(theta), ry * math.sin(theta), z_h * stature))
            torso_ids.append(f"torso/ring.{ri:03d}/sector.{sector:02d}")
            torso_weights.append(torso_weight(z_h))
    torso_faces = []
    for ri in range(len(torso_rings)-1):
        for sector in range(ring_n):
            nxt = (sector + 1) % ring_n
            a, b = ri*ring_n+sector, ri*ring_n+nxt
            c, d = (ri+1)*ring_n+nxt, (ri+1)*ring_n+sector
            torso_faces.extend(((a,b,c),(a,c,d)))
    start_cap = len(torso_vertices)
    torso_vertices.append((0.0, 0.0, torso_rings[0][0][2]*stature))
    torso_ids.append("torso/cap.start")
    torso_weights.append(dict(torso_weights[0]))
    for sector in range(ring_n):
        torso_faces.append((start_cap, (sector+1)%ring_n, sector))
    end_base = (len(torso_rings)-1)*ring_n
    end_cap = len(torso_vertices)
    torso_vertices.append((0.0, 0.0, torso_rings[-1][0][2]*stature))
    torso_ids.append("torso/cap.end")
    torso_weights.append(dict(torso_weights[end_base]))
    for sector in range(ring_n):
        torso_faces.append((end_base+sector, end_cap, end_base+(sector+1)%ring_n))
    torso_face_materials = ["suit"] * len(torso_faces)
    torso_component = {"id":"torso", "material":"suit", "material_ids":["suit","head_mitten","foot"],
                       "face_materials":torso_face_materials, "vertices_m":torso_vertices,
                       "vertex_ids":torso_ids, "faces":[list(face) for face in torso_faces],
                       "weights":torso_weights}

    # Closed head ellipsoid with shared deterministic latitude/longitude topology.
    head_source = source_components["head"]
    head_center_h = _vec(head_source["center_h"], 3, "head center")
    head_radii_h = _vec(appearance_doc.get("head_radii_h", ()), 3, "head radii")
    if min(head_radii_h) <= 0.0:
        raise ValueError("head radii must be positive")
    longitude_n = int(template_doc["topology"]["head_longitudes"])
    latitude_n = int(template_doc["topology"]["head_latitude_intervals"])
    if longitude_n < 3 or latitude_n < 2:
        raise ValueError("head topology is too small")
    center = _mul(head_center_h, stature)
    radii = _mul(head_radii_h, stature)
    head_vertices, head_ids, head_weights, head_faces = [], [], [], []
    head_weights.append({head_source["weighting"]["carrier"]: 1.0})
    head_vertices.append((center[0], center[1], center[2]+radii[2]))
    head_ids.append("head/pole.north")
    for lat in range(1, latitude_n):
        phi = math.pi * lat / latitude_n
        for lon in range(longitude_n):
            theta = 2.0 * math.pi * lon / longitude_n
            head_vertices.append((center[0]+radii[0]*math.sin(phi)*math.cos(theta),
                                  center[1]+radii[1]*math.sin(phi)*math.sin(theta),
                                  center[2]+radii[2]*math.cos(phi)))
            head_ids.append(f"head/lat.{lat:02d}/lon.{lon:02d}")
            head_weights.append({head_source["weighting"]["carrier"]: 1.0})
    south = len(head_vertices)
    head_vertices.append((center[0], center[1], center[2]-radii[2]))
    head_ids.append("head/pole.south")
    head_weights.append({head_source["weighting"]["carrier"]: 1.0})
    for lon in range(longitude_n):
        nxt = (lon+1)%longitude_n
        head_faces.append((0, 1+nxt, 1+lon))
    for lat in range(latitude_n-2):
        lower = 1+lat*longitude_n
        upper = lower+longitude_n
        for lon in range(longitude_n):
            nxt=(lon+1)%longitude_n
            a,b,c,d=lower+lon,lower+nxt,upper+nxt,upper+lon
            head_faces.extend(((a,b,c),(a,c,d)))
    last_ring = 1+(latitude_n-2)*longitude_n
    for lon in range(longitude_n):
        nxt=(lon+1)%longitude_n
        head_faces.append((last_ring+lon,last_ring+nxt,south))
    head_faces = [tuple(reversed(face)) for face in head_faces]
    components.append({"id":"head", "material":"head_mitten", "material_ids":["suit","head_mitten","foot"],
                       "face_materials":["head_mitten"]*len(head_faces), "vertices_m":head_vertices,
                       "vertex_ids":head_ids, "faces":[list(face) for face in head_faces],
                       "weights":head_weights})

    # Arm and leg lofts use rest joint landmarks and arclength bands.
    topology = template_doc["topology"]
    loft_n = int(topology["loft_ring_vertices"])
    subdivisions = int(topology["intervals_per_control_interval"])
    if subdivisions != 4:
        raise ValueError("this template's frozen loft subdivision must be four")

    def mirror_weights(mapping):
        return {key.replace(".R", ".L"): value for key, value in mapping.items()}

    radius_scales = appearance_doc.get("radius_scales", {})
    for scale_name in ("arm", "leg_thigh", "leg_knee", "leg_shank"):
        value = float(radius_scales.get(scale_name, float("nan")))
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"{scale_name} radius scale must be finite and positive")

    def blend_weights(s, start, end, carrier_from, carrier_to):
        if end <= start:
            raise ValueError("weight band has degenerate arclength")
        f = _smooth((s-start)/(end-start))
        return {carrier: weight for carrier, weight in ((carrier_from, 1.0-f), (carrier_to, f)) if weight > 0.0}

    def station_for(control, spans):
        span, t = control[2], control[3]
        if span not in spans:
            raise ValueError(f"unknown arclength span {span}")
        offset, length = spans[span]
        return offset + t*length

    # Arms.
    arm_source = source_components["arm.R"]
    S = _landmark_rest(profile, by_id, rest_frames, "shoulder.R", scale)
    E = _landmark_rest(profile, by_id, rest_frames, "elbow.R", scale)
    W = _landmark_rest(profile, by_id, rest_frames, "wrist.R", scale)
    se, ew = _norm(_sub(E,S)), _norm(_sub(W,E))
    if min(se, ew) < 1e-10:
        raise ValueError("arm rest centerline has a degenerate span")
    D = _add(W, _mul(_unit(_sub(W,E), "forearm direction"),
                     float(arm_source["endpoints"]["hand_tip_distance_h"])*stature))
    spans_arm = {"shoulder_to_elbow": (0.0,se), "elbow_to_wrist": (se,ew),
                 "wrist_to_hand_tip": (se+ew,_norm(_sub(D,W)))}
    arm_rings = _rings(arm_source["control_rings"],
                       {"shoulder_to_elbow":(S,E), "elbow_to_wrist":(E,W),
                        "wrist_to_hand_tip":(W,D)},
                       radius_scales["arm"])
    shoulder_start, shoulder_end = -.12*se, .10*se
    elbow_radius = .08*min(se,ew)
    elbow_start, elbow_end = se-elbow_radius, se+elbow_radius
    twist_start, twist_end = se+.15*ew, se+.85*ew
    wrist_distance = spans_arm["wrist_to_hand_tip"][0]
    wrist_start, wrist_end = wrist_distance-.06*ew, wrist_distance+.06*ew
    def arm_weights(ring_index, center, current, following, alpha):
        s0,s1=station_for(current,spans_arm),station_for(following,spans_arm)
        s=s0+(s1-s0)*alpha
        if s<=shoulder_end: return blend_weights(s,shoulder_start,shoulder_end,"clavicle.R","humerus.R")
        if s<elbow_start: return {"humerus.R":1.0}
        if s<=elbow_end: return blend_weights(s,elbow_start,elbow_end,"humerus.R","elbow.R")
        if s<twist_start: return {"elbow.R":1.0}
        if s<=twist_end: return blend_weights(s,twist_start,twist_end,"elbow.R","radius.R")
        if s<wrist_start: return {"radius.R":1.0}
        if s<=wrist_end: return blend_weights(s,wrist_start,wrist_end,"radius.R","wrist.R")
        return {"wrist.R":1.0}
    def arm_material(ring_index, sector):
        current=arm_rings[ring_index][2]
        following=arm_rings[ring_index+1][2]
        return "head_mitten" if current[2]=="wrist_to_hand_tip" and following[2]=="wrist_to_hand_tip" else "suit"
    arm_r= _loft_component("arm.R",arm_rings,ring_n=loft_n,weight_function=arm_weights,
                            material_function=arm_material,unit_scale=stature,coordinate_scale=1.0)
    arm_l= _loft_component("arm.L",arm_rings,ring_n=loft_n,weight_function=arm_weights,
                            material_function=arm_material,mirror=True,unit_scale=stature,coordinate_scale=1.0)
    join = template_doc.get("shoulder_join")
    if not isinstance(join, Mapping):
        raise ValueError("template requires shoulder_join descriptor")
    components.append(_weld_shoulder(torso_component, arm_r, arm_l, join, stature, torso_weight, profile))

    # Legs.
    leg_source = source_components["leg.R"]
    P = _landmark_rest(profile, by_id, rest_frames, "hip.R", scale)
    K = _landmark_rest(profile, by_id, rest_frames, "knee.R", scale)
    A = _landmark_rest(profile, by_id, rest_frames, "ankle.R", scale)
    pk,ka=_norm(_sub(K,P)),_norm(_sub(A,K))
    if min(pk,ka)<1e-10:
        raise ValueError("leg rest centerline has a degenerate span")
    spans_leg={"hip_to_knee":(0.0,pk),"knee_to_ankle":(pk,ka)}
    leg_rings=_rings(leg_source["control_rings"],{"hip_to_knee":(P,K),"knee_to_ankle":(K,A)})
    hip_start,hip_end=-.12*pk,.10*pk
    knee_radius=.08*min(pk,ka); knee_start,knee_end=pk-knee_radius,pk+knee_radius
    ankle_start,ankle_end=pk+ka-.08*ka,pk+ka
    def leg_weights(ring_index, center, current, following, alpha):
        s=station_for(current,spans_leg)+(station_for(following,spans_leg)-station_for(current,spans_leg))*alpha
        if s<=hip_end: return blend_weights(s,hip_start,hip_end,"pelvis","femur.R")
        if s<knee_start: return {"femur.R":1.0}
        if s<=knee_end: return blend_weights(s,knee_start,knee_end,"femur.R","knee.R")
        if s<ankle_start: return {"knee.R":1.0}
        if s<=ankle_end: return blend_weights(s,ankle_start,ankle_end,"knee.R","hindfoot.R")
        return {"hindfoot.R":1.0}
    # The exact scale key is applied at control stations, then linearly
    # interpolated along each generated interval.
    scaled_leg_rings=[]
    controls=leg_source["control_rings"]
    # Expand the authored controls again so the radius scale is interpolated
    # between its adjacent source rings along with the radii themselves.
    leg_controls=[]
    for item in controls:
        span=item["span"];start,end={"hip_to_knee":(P,K),"knee_to_ankle":(K,A)}[span]
        t=float(item["t"]); center=_add(start,_mul(_sub(end,start),t))
        leg_controls.append((center,_mul(_vec(item["radius_h"],2,"leg radius"),float(radius_scales[item["scale_key"]])),span,t,item))
    for index,current in enumerate(leg_controls[:-1]):
        following=leg_controls[index+1]
        for step in range(4):
            a=step/4.0
            scaled_leg_rings.append((_add(current[0],_mul(_sub(following[0],current[0]),a)),
                _add(current[1],_mul(_sub(following[1],current[1]),a)),current,following,a))
    scaled_leg_rings.append((*leg_controls[-1][:2],leg_controls[-1],leg_controls[-1],0.0))
    leg_r=_loft_component("leg.R",scaled_leg_rings,ring_n=loft_n,weight_function=leg_weights,unit_scale=stature,coordinate_scale=1.0)
    components.append(leg_r)
    leg_l=_loft_component("leg.L",scaled_leg_rings,ring_n=loft_n,weight_function=leg_weights,mirror=True,unit_scale=stature,coordinate_scale=1.0)
    components.append(leg_l)

    # Feet follow their declared neutral hindfoot/MTP frames into rest through
    # the same normalized dual-quaternion reference used by the skinning tests.
    foot_source=source_components["foot.R"]
    foot_controls=foot_source["control_rings"]
    foot_neutral=[]
    ankle_row=next(item for item in profile["landmarks"] if item["id"]=="ankle.R")
    ankle_neutral=_mul(_vec(ankle_row["position_m"],3,"ankle landmark"),scale)
    foot_rings=[]
    for index in range(len(foot_controls)-1):
        first,second=foot_controls[index],foot_controls[index+1]
        for step in range(subdivisions):
            a=step/subdivisions
            foot_rings.append(tuple(float(first[key])+(float(second[key])-float(first[key]))*a
                                    for key in ("y_h","half_width_h","top_height_h")))
    last=foot_controls[-1]
    foot_rings.append(tuple(float(last[key]) for key in ("y_h","half_width_h","top_height_h")))
    neutral_verts=[]; foot_ids=[]; foot_weights=[]; foot_faces=[]; foot_face_mats=[]
    for ri,(y_h,half_w_h,top_h_h) in enumerate(foot_rings):
        y=ankle_neutral[1]+y_h*stature
        for sector in range(loft_n):
            theta=2.0*math.pi*sector/loft_n
            x=ankle_neutral[0]+half_w_h*stature*math.cos(theta)
            z=top_h_h*stature*max(0.0,math.sin(theta))
            neutral_verts.append((x,y,z))
            foot_ids.append(f"foot.R/ring.{ri:03d}/sector.{sector:02d}")
            if y_h<=float(foot_source["weighting"]["hindfoot_only_at_or_below_y_h"]):
                weight={"hindfoot.R":1.0}
            elif y_h>=float(foot_source["weighting"]["mtp_only_at_or_above_y_h"]):
                weight={"mtp.R":1.0}
            else:
                limits=foot_source["weighting"]["smooth_transition"]["y_h"]
                weight=blend_weights(y_h,float(limits[0]),float(limits[1]),"hindfoot.R","mtp.R")
            foot_weights.append(weight)
    for ri in range(len(foot_rings)-1):
        for sector in range(loft_n):
            nxt=(sector+1)%loft_n
            a,b=ri*loft_n+sector,ri*loft_n+nxt
            c,d=(ri+1)*loft_n+nxt,(ri+1)*loft_n+sector
            foot_faces.extend(((a,d,c),(a,c,b)))
            foot_face_mats.extend(("foot","foot"))
    start_cap=len(neutral_verts)
    neutral_verts.append(tuple(sum(neutral_verts[i][axis] for i in range(loft_n))/loft_n for axis in range(3)))
    foot_ids.append("foot.R/cap.start");foot_weights.append(dict(foot_weights[0]))
    for sector in range(loft_n):
        foot_faces.append((start_cap,sector,(sector+1)%loft_n));foot_face_mats.append("foot")
    end_base=(len(foot_rings)-1)*loft_n;end_cap=len(neutral_verts)
    neutral_verts.append(tuple(sum(neutral_verts[end_base+i][axis] for i in range(loft_n))/loft_n for axis in range(3)))
    foot_ids.append("foot.R/cap.end");foot_weights.append(dict(foot_weights[end_base]))
    for sector in range(loft_n):
        foot_faces.append((end_cap,end_base+(sector+1)%loft_n,end_base+sector));foot_face_mats.append("foot")
    # Each carrier maps its neutral local frame to the authored rest frame.
    from humanmotionlib.character_skinning import skin_vertex
    foot_transforms={}
    for carrier in ("hindfoot.R","mtp.R"):
        row=by_id[carrier];rest_q,rest_t=rest_frames[carrier]
        basis=row["basis"];neutral_q=_matrix_quaternion(basis)
        neutral_t=_mul(_vec(row["origin_m"],3,f"{carrier}.origin_m"),scale)
        foot_transforms[carrier]={"rest_translation":neutral_t,"rest_orientation":neutral_q,
                                  "posed_translation":rest_t,"posed_orientation":rest_q}
    foot_rest=[skin_vertex(point,weight,foot_transforms) for point,weight in zip(neutral_verts,foot_weights)]
    foot_r={"id":"foot.R","material":"foot","material_ids":["suit","head_mitten","foot"],
            "face_materials":foot_face_mats,"vertices_m":foot_rest,"vertex_ids":foot_ids,
            "faces":[list(face) for face in foot_faces],"weights":foot_weights}
    components.append(foot_r)
    foot_l={"id":"foot.L","material":"foot","material_ids":["suit","head_mitten","foot"],
            "face_materials":foot_face_mats,"vertices_m":[(-v[0],v[1],v[2]) for v in foot_rest],
            "vertex_ids":[identifier.replace("foot.R","foot.L") for identifier in foot_ids],
            "faces":[list(reversed(face)) for face in foot_faces],
            "weights":[mirror_weights(weight) for weight in foot_weights]}
    components.append(foot_l)

    # Order exactly as the canonical template component inventory.
    order = ["torso", "head", "leg.R", "leg.L", "foot.R", "foot.L"]
    components = sorted(components, key=lambda component: order.index(component["id"]))
    for component in components:
        for vertex_id, row in zip(component["vertex_ids"], component["weights"]):
            limit = 3 if vertex_id.startswith(("shoulder.R/", "shoulder.L/")) else 2
            if not row or len(row) > limit or any(not math.isfinite(float(value)) or float(value) < 0.0
                                                   for value in row.values()) or \
                    abs(math.fsum(float(value) for value in row.values()) - 1.0) > 1e-12:
                raise ValueError(f"invalid surface weights at {vertex_id}: maximum influences {limit}")
    result = {"format": "hml-surface-mesh/v1", "components": components}
    result["surface_sha256"] = hashlib.sha256(json.dumps(
        result, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()
    return result
