# SPDX-License-Identifier: Apache-2.0
"""Small deterministic dual-quaternion skinning reference kernel.

The kernel is intentionally backend-independent.  It mirrors the normalized
dual-quaternion blend specified for character surfaces and uses only the
Python standard library so it can serve as a host-side oracle.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import math
from dataclasses import dataclass


_EPS = 1e-8


def source_world_transforms(profile: Mapping[str, object], frames: Mapping[str, object],
                            carriers: Sequence[str], *, rest_frames=None):
    """Build canonical double-precision world-space DQ inputs from profile B and raw F."""
    from humanmotionlib.character_surface import _matrix_quaternion, _rest_frames
    if rest_frames is None:
        _,rest_frames=_rest_frames(profile,1.0)
    if not isinstance(frames,Mapping):
        raise ValueError("source pose frames must be a mapping")
    result={}
    for carrier in sorted(set(carriers)):
        if carrier not in rest_frames or carrier not in frames:
            raise ValueError(f"source world transform is missing carrier {carrier}")
        frame=frames[carrier]
        if not isinstance(frame,Mapping):
            raise ValueError(f"source frame for {carrier} must be a mapping")
        rest_orientation,rest_translation=rest_frames[carrier]
        result[carrier]={
            "rest_translation":_finite_vector(rest_translation,3,carrier+" rest translation"),
            "rest_orientation":_qnormalize(rest_orientation,carrier+" rest orientation"),
            "posed_translation":_finite_vector(frame.get("position_m",()),3,carrier+" posed translation"),
            "posed_orientation":_matrix_quaternion(frame.get("rotation")),
        }
    return result


def _finite_vector(value: Sequence[float], size: int, name: str) -> tuple[float, ...]:
    if isinstance(value, (str, bytes)) or len(value) != size:
        raise ValueError(f"{name} must contain exactly {size} numbers")
    result = tuple(float(component) for component in value)
    if not all(math.isfinite(component) for component in result):
        raise ValueError(f"{name} must contain only finite numbers")
    return result


def _qmul(a: tuple[float, float, float, float],
          b: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw)


def _qconj(q: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    return q[0], -q[1], -q[2], -q[3]


def _qnormalize(q: Sequence[float], name: str) -> tuple[float, float, float, float]:
    values = _finite_vector(q, 4, name)
    norm = math.sqrt(sum(value * value for value in values))
    if norm < _EPS:
        raise ValueError(f"{name} has a near-zero norm")
    return tuple(value / norm for value in values)  # type: ignore[return-value]


def _rotate(q: tuple[float, float, float, float],
            v: tuple[float, float, float]) -> tuple[float, float, float]:
    rotated = _qmul(_qmul(q, (0.0, *v)), _qconj(q))
    return rotated[1], rotated[2], rotated[3]


def _relative_transform(record: Mapping[str, Sequence[float]], carrier: str
                        ) -> tuple[tuple[float, float, float, float],
                                   tuple[float, float, float]]:
    try:
        rest_t = _finite_vector(record["rest_translation"], 3, f"{carrier}.rest_translation")
        posed_t = _finite_vector(record["posed_translation"], 3, f"{carrier}.posed_translation")
        rest_q = _qnormalize(record["rest_orientation"], f"{carrier}.rest_orientation")
        posed_q = _qnormalize(record["posed_orientation"], f"{carrier}.posed_orientation")
    except KeyError as error:
        raise ValueError(f"{carrier} transform is missing {error.args[0]}") from None
    relative_q = _qnormalize(_qmul(posed_q, _qconj(rest_q)), f"{carrier}.relative_orientation")
    relative_t = tuple(posed_t[i] - _rotate(relative_q, rest_t)[i] for i in range(3))
    return relative_q, relative_t


def _dual_quaternion(q: tuple[float, float, float, float],
                     translation: tuple[float, float, float]
                     ) -> tuple[tuple[float, float, float, float],
                                tuple[float, float, float, float]]:
    dual = _qmul((0.0, *translation), q)
    return q, tuple(component * 0.5 for component in dual)  # type: ignore[return-value]


def skin_vertex(rest_vertex: Sequence[float], influences: Mapping[str, float],
                transforms: Mapping[str, Mapping[str, Sequence[float]]]
                ) -> tuple[float, float, float]:
    """Apply normalized dual-quaternion skinning to one rest-space vertex.

    ``transforms`` maps carrier IDs to rigid rest and posed frames.  Weights
    are normalized here to make the reference robust to harmless input round
    off; negative, non-finite, empty, or unresolved influences are rejected.
    """
    vertex = _finite_vector(rest_vertex, 3, "rest_vertex")
    real, translation = blended_transform(influences, transforms)
    rotated_vertex = _rotate(real, vertex)
    result = tuple(rotated_vertex[i] + translation[i] for i in range(3))
    if not all(math.isfinite(component) for component in result):
        raise ValueError("skinning produced a non-finite vertex")
    return result


def blended_transform(influences: Mapping[str, float],
                      transforms: Mapping[str, Mapping[str, Sequence[float]]]
                      ) -> tuple[tuple[float, float, float, float], tuple[float, float, float]]:
    """Return the normalized DQ blend used by :func:`skin_vertex`."""
    if not isinstance(influences, Mapping) or not influences:
        raise ValueError("influences must be a non-empty mapping")

    weights: dict[str, float] = {}
    for carrier, weight in influences.items():
        if not isinstance(carrier, str) or not carrier:
            raise ValueError("influence carrier IDs must be non-empty strings")
        try:
            number = float(weight)
        except (TypeError, ValueError):
            raise ValueError(f"{carrier} influence weight must be numeric") from None
        if not math.isfinite(number) or number < 0:
            raise ValueError(f"{carrier} influence weight must be finite and non-negative")
        if carrier not in transforms:
            raise ValueError(f"missing transform for influence carrier {carrier}")
        if number > 0:
            weights[carrier] = number
    total = math.fsum(weights.values())
    if not math.isfinite(total) or total <= 0:
        raise ValueError("influence weights must have a positive finite sum")
    weights = {carrier: weight / total for carrier, weight in weights.items()}

    reference_id = min(weights, key=lambda carrier: (-weights[carrier], carrier))
    reference_q, _ = _relative_transform(transforms[reference_id], reference_id)
    blended_real = [0.0] * 4
    blended_dual = [0.0] * 4
    for carrier in sorted(weights):
        real, dual = _dual_quaternion(*_relative_transform(transforms[carrier], carrier))
        if sum(a * b for a, b in zip(reference_q, real)) < 0.0:
            real = tuple(-component for component in real)
            dual = tuple(-component for component in dual)
        weight = weights[carrier]
        for index in range(4):
            blended_real[index] += weight * real[index]
            blended_dual[index] += weight * dual[index]

    real_norm = math.sqrt(sum(component * component for component in blended_real))
    if not math.isfinite(real_norm) or real_norm < _EPS:
        raise ValueError("blended dual-quaternion real norm is below 1e-8")
    real = tuple(component / real_norm for component in blended_real)
    dual = tuple(component / real_norm for component in blended_dual)
    projection = sum(real[index] * dual[index] for index in range(4))
    dual = tuple(dual[index] - real[index] * projection for index in range(4))

    translation_q = _qmul(tuple(2.0 * component for component in dual), _qconj(real))
    translation = translation_q[1:]
    if not all(math.isfinite(component) for component in (*real, *translation)):
        raise ValueError("skinning produced a non-finite blended transform")
    return real, translation


def inverse_skin_vertex(neutral_vertex: Sequence[float], influences: Mapping[str, float],
                        transforms: Mapping[str, Mapping[str, Sequence[float]]]
                        ) -> tuple[float, float, float]:
    """Map a posed-space point back through the same blended DQ transform."""
    vertex = _finite_vector(neutral_vertex, 3, "neutral_vertex")
    real, translation = blended_transform(influences, transforms)
    q = _qconj(real)
    result = _rotate(q, tuple(vertex[i] - translation[i] for i in range(3)))
    if not all(math.isfinite(component) for component in result):
        raise ValueError("inverse skinning produced a non-finite vertex")
    return result


@dataclass(frozen=True)
class CompiledWeightSet:
    """Immutable normalized influence rows compiled in source vertex order."""

    keys: tuple[tuple[tuple[str, float], ...], ...]
    indices: tuple[int, ...]


def compile_weight_set(vertex_weights: Sequence[Mapping[str, float]]) -> CompiledWeightSet:
    """Validate and deduplicate vertex weights once, preserving first-seen key order."""
    key_indices: dict[tuple[tuple[str, float], ...], int] = {}
    keys: list[tuple[tuple[str, float], ...]] = []
    indices: list[int] = []
    for influences in vertex_weights:
        if not isinstance(influences, Mapping) or not influences:
            raise ValueError("influences must be a non-empty mapping")
        weights: dict[str, float] = {}
        for carrier, weight in influences.items():
            if not isinstance(carrier, str) or not carrier:
                raise ValueError("influence carrier IDs must be non-empty strings")
            try:
                number = float(weight)
            except (TypeError, ValueError):
                raise ValueError(f"{carrier} influence weight must be numeric") from None
            if not math.isfinite(number) or number < 0:
                raise ValueError(f"{carrier} influence weight must be finite and non-negative")
            if number > 0:
                weights[carrier] = number
        total = math.fsum(weights.values())
        if not math.isfinite(total) or total <= 0:
            raise ValueError("influence weights must have a positive finite sum")
        normalized = tuple((carrier, weights[carrier] / total) for carrier in sorted(weights))
        index = key_indices.get(normalized)
        if index is None:
            index = len(keys)
            key_indices[normalized] = index
            keys.append(normalized)
        indices.append(index)
    return CompiledWeightSet(tuple(keys), tuple(indices))


@dataclass(frozen=True)
class _BlendedRigid:
    real: tuple[float, float, float, float]
    translation: tuple[float, float, float]


class CompiledPoseSkinning:
    """Pose-scoped immutable blend cache for a compiled set of vertex weights."""

    def __init__(self, transforms: Mapping[str, Mapping[str, Sequence[float]]],
                 weight_set: CompiledWeightSet):
        if not isinstance(weight_set, CompiledWeightSet):
            raise TypeError("weight_set must be a CompiledWeightSet")
        carriers = {carrier for key in weight_set.keys for carrier, _ in key}
        relative = {}
        for carrier in sorted(carriers):
            if carrier not in transforms:
                raise ValueError(f"missing transform for influence carrier {carrier}")
            relative[carrier] = _dual_quaternion(*_relative_transform(transforms[carrier], carrier))
        blends = []
        for key in weight_set.keys:
            weights = dict(key)
            reference_id = min(weights, key=lambda carrier: (-weights[carrier], carrier))
            reference_q = relative[reference_id][0]
            blended_real = [0.0] * 4
            blended_dual = [0.0] * 4
            for carrier, weight in key:
                real, dual = relative[carrier]
                if sum(a * b for a, b in zip(reference_q, real)) < 0.0:
                    real = tuple(-component for component in real)
                    dual = tuple(-component for component in dual)
                for index in range(4):
                    blended_real[index] += weight * real[index]
                    blended_dual[index] += weight * dual[index]
            real_norm = math.sqrt(sum(component * component for component in blended_real))
            if not math.isfinite(real_norm) or real_norm < _EPS:
                raise ValueError("blended dual-quaternion real norm is below 1e-8")
            real = tuple(component / real_norm for component in blended_real)
            dual = tuple(component / real_norm for component in blended_dual)
            projection = sum(real[index] * dual[index] for index in range(4))
            dual = tuple(dual[index] - real[index] * projection for index in range(4))
            translation_q = _qmul(tuple(2.0 * component for component in dual), _qconj(real))
            blends.append(_BlendedRigid(real, translation_q[1:]))
        self.weight_set = weight_set
        self._blends = tuple(blends)

    def apply(self, rest_vertex: Sequence[float], vertex_index: int) -> tuple[float, float, float]:
        """Skin a vertex using its precompiled influence row and scalar operation order."""
        vertex = _finite_vector(rest_vertex, 3, "rest_vertex")
        if isinstance(vertex_index, bool) or not isinstance(vertex_index, int) or not 0 <= vertex_index < len(self.weight_set.indices):
            raise IndexError("vertex_index is outside the compiled weight set")
        blend = self._blends[self.weight_set.indices[vertex_index]]
        rotated_vertex = _rotate(blend.real, vertex)
        result = tuple(rotated_vertex[i] + blend.translation[i] for i in range(3))
        if not all(math.isfinite(component) for component in result):
            raise ValueError("skinning produced a non-finite vertex")
        return result


def compile_pose_skinning(transforms: Mapping[str, Mapping[str, Sequence[float]]],
                          weight_set: CompiledWeightSet) -> CompiledPoseSkinning:
    """Compile one pose's carrier transforms and all unique blends for a weight set."""
    return CompiledPoseSkinning(transforms, weight_set)
