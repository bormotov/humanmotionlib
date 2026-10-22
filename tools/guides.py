# SPDX-License-Identifier: Apache-2.0
"""Acyclic declarative cartilage bindings; rigid geometry is never deformed."""

from tools import math3d as m


def _ordered(dependencies, message):
    pending = {key: set(value) for key, value in dependencies.items()}
    result, done = [], set()
    while pending:
        ready = sorted(key for key, value in pending.items() if value <= done)
        if not ready:
            raise ValueError(message)
        for key in ready:
            result.append(key)
            done.add(key)
            del pending[key]
    return result


def compile_guides(profile):
    """Validate targets/writers and return deterministic guide/control order."""
    bodies = {b['id']: b for b in profile['structures']}
    guides = {g['id']: (b, g) for b in bodies.values() for g in b['geometry'] if g.get('bindings')}
    dependencies, controls = {}, {}
    for name, (body, primitive) in guides.items():
        if body['rigid']:
            raise ValueError(name+': bindings cannot deform rigid structure')
        bindings = {}
        for binding in primitive['bindings']:
            index = binding['point_index']
            if index in bindings or not 0 <= index < len(primitive['points_m']):
                raise ValueError(name+': duplicate or invalid point index')
            bindings[index] = binding
        dependencies[name] = set()
        local = {i: set() for i in bindings}
        for index, binding in bindings.items():
            kind = binding.get('kind', 'rigid_point')
            if kind == 'rigid_point':
                target = binding['structure']
                if target not in bodies or not bodies[target]['rigid']:
                    raise ValueError(name+': unresolved or non-rigid target '+target)
                target_side = target.split('.')[-1]
            elif kind == 'guide_point':
                target = binding['guide']
                if target not in guides:
                    raise ValueError(name+': unresolved guide '+target)
                target_body, target_primitive = guides[target]
                target_index = binding['control_index']
                if not 0 <= target_index < len(target_primitive['points_m']) or target_index not in {b['point_index'] for b in target_primitive['bindings']}:
                    raise ValueError(name+': invalid or unbound guide control')
                dependencies[name].add(target)
                target_side = target_body['id'].split('.')[-1]
            elif kind == 'midpoint':
                ends = binding['endpoints']
                if len(set(ends)) != 2 or index in ends or any(i not in bindings for i in ends):
                    raise ValueError(name+': invalid midpoint endpoints')
                local[index].update(ends)
                if binding['offset_frame'] not in bodies:
                    raise ValueError(name+': unresolved offset frame')
                target_side = binding['offset_frame'].split('.')[-1]
            else:
                raise ValueError(name+': unsupported binding '+kind)
            side = body['id'].split('.')[-1]
            if side in ('L', 'R') and target_side in ('L', 'R') and side != target_side:
                raise ValueError(name+': cross-side binding')
        controls[name] = (bindings, _ordered(local, 'control dependency cycle in '+name))
    order = _ordered(dependencies, 'guide dependency cycle')
    return [(guides[name][0], guides[name][1], *controls[name]) for name in order]


def solve_guides(profile, frames, plan=None):
    result, world_controls = {}, {}
    for body, primitive, bindings, order in (compile_guides(profile) if plan is None else plan):
        frame = frames[body['id']]
        points = [m.add(frame['position_m'], m.mv(frame['rotation'], p)) for p in primitive['points_m']]
        for index in order:
            binding = bindings[index]
            kind = binding.get('kind', 'rigid_point')
            if kind == 'rigid_point':
                target = frames[binding['structure']]
                world = m.add(target['position_m'], m.mv(target['rotation'], binding['position_m']))
            elif kind == 'guide_point':
                world = world_controls[binding['guide']][binding['control_index']]
            else:
                a, b = (points[i] for i in binding['endpoints'])
                world = m.add(m.scale(m.add(a, b), .5), m.mv(frames[binding['offset_frame']]['rotation'], binding['offset_m']))
            points[index] = world
        world_controls[primitive['id']] = points
        result[primitive['id']] = [m.mv(m.transpose(frame['rotation']), m.sub(p, frame['position_m'])) for p in points]
    return result
