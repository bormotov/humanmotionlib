# SPDX-License-Identifier: Apache-2.0
"""Exact equivalence checks for compiled, pose-scoped DQ reference evaluation."""

from pathlib import Path
import math
import unittest

import yaml

from humanmotionlib.character_skinning import (
    compile_pose_skinning, compile_weight_set, skin_vertex,
)
from humanmotionlib.character_surface import _rest_frames, expand_surface
from humanmotionlib.diagnostics import DiagnosticEvaluator
from humanmotionlib.validate import load_sources


ROOT = Path(__file__).resolve().parents[1]


def _transform(*, rest_t=(0.0, 0.0, 0.0), rest_q=(1.0, 0.0, 0.0, 0.0),
               posed_t=(0.0, 0.0, 0.0), posed_q=(1.0, 0.0, 0.0, 0.0)):
    return {"rest_translation": rest_t, "rest_orientation": rest_q,
            "posed_translation": posed_t, "posed_orientation": posed_q}


class CompiledSkinningTests(unittest.TestCase):
    def assertVectorEqual(self, actual, expected):
        self.assertEqual(actual, expected)

    def test_rigid_single_and_two_influence_match_scalar_and_hand_solution(self):
        half = math.sqrt(0.5)
        transforms = {
            "wrist": _transform(posed_t=(2.0, 1.0, -1.0), posed_q=(half, 0, 0, half)),
            "other": _transform(posed_t=(0.0, 4.0, 0.0)),
        }
        rows = [{"wrist": 1.0}, {"other": 2.0, "wrist": 2.0}]
        vertices = [(1.0, 0.0, 0.0), (1.0, 2.0, 3.0)]
        weights = compile_weight_set(rows)
        compiled = compile_pose_skinning(transforms, weights)
        for actual, expected in zip(compiled.apply(vertices[0], 0), (2.0, 2.0, -1.0)):
            self.assertAlmostEqual(actual, expected, delta=1e-14)
        for index, (vertex, row) in enumerate(zip(vertices, rows)):
            self.assertVectorEqual(compiled.apply(vertex, index), skin_vertex(vertex, row, transforms))

    def test_hemisphere_tie_mirror_and_scale_match_scalar(self):
        half = math.sqrt(0.5)
        transforms = {
            "a": _transform(posed_t=(0.3, -0.2, 0.4), posed_q=(half, 0, 0, half)),
            "b": _transform(posed_t=(-0.3, -0.2, 0.4), posed_q=(half, 0, 0, -half)),
            "c": _transform(posed_q=(-1.0, 0, 0, 0)),
        }
        rows = [{"c": 1.0, "b": 1.0, "a": 1.0}, {"a": 0.5, "b": 0.5}]
        weights = compile_weight_set(rows)
        compiled = compile_pose_skinning(transforms, weights)
        for scale in (1.5, 1.7, 1.9):
            vertex = (0.4 * scale, 0.7 * scale, 1.1 * scale)
            for index, row in enumerate(rows):
                self.assertVectorEqual(compiled.apply(vertex, index), skin_vertex(vertex, row, transforms))
        right = _transform(posed_t=(0.3, -0.2, 0.4), posed_q=(half, 0, 0, half))
        left = _transform(posed_t=(-0.3, -0.2, 0.4), posed_q=(half, 0, 0, -half))
        mirrored = compile_pose_skinning(
            {"wrist.L": left, "wrist.R": right},
            compile_weight_set([{"wrist.R": 1.0}, {"wrist.L": 1.0}]))
        right_result = mirrored.apply((0.4, 0.7, 1.1), 0)
        left_result = mirrored.apply((-0.4, 0.7, 1.1), 1)
        self.assertVectorEqual(left_result, (-right_result[0], right_result[1], right_result[2]))

    def test_compiled_real_arm_raise_surface_vertices_equal_scalar(self):
        sources, _ = load_sources("adult-reference-v1", root=ROOT)
        template = yaml.safe_load((ROOT / "characters/templates/exercise-mannequin-v1.yaml").read_text())
        appearance = yaml.safe_load((ROOT / "characters/appearances/male-v1.yaml").read_text())
        surface = expand_surface(sources["profile"], template, appearance, 1.70)
        evaluator = DiagnosticEvaluator(sources)
        frames = evaluator.evaluate("arm-raise", 1.0)["frames"]
        _, rest_frames = _rest_frames(sources["profile"], 1.0)
        transforms = {}
        all_rows = [row for component in surface["components"] for row in component["weights"]]
        weights = compile_weight_set(all_rows)
        carriers = sorted({carrier for key in weights.keys for carrier, _ in key})
        from humanmotionlib.character_skinning import source_world_transforms
        transforms = source_world_transforms(sources["profile"], frames, carriers,
                                             rest_frames=rest_frames)
        compiled = compile_pose_skinning(transforms, weights)
        offset = 0
        for component in surface["components"]:
            for local_index, (vertex, row) in enumerate(zip(component["vertices_m"], component["weights"])):
                self.assertVectorEqual(compiled.apply(vertex, offset + local_index),
                                       skin_vertex(vertex, row, transforms))
            offset += len(component["vertices_m"])
        self.assertEqual(offset, len(weights.indices))

    def test_invalid_rows_transforms_vertices_and_indices_fail(self):
        for bad in ({}, {"bone": -1.0}, {"bone": float("nan")}, {"bone": 0.0}):
            with self.subTest(weights=bad), self.assertRaises(ValueError):
                compile_weight_set([bad])
        with self.assertRaisesRegex(ValueError, "missing transform"):
            compile_pose_skinning({}, compile_weight_set([{"bone": 1.0}]))
        compiled = compile_pose_skinning({"bone": _transform()}, compile_weight_set([{"bone": 1.0}]))
        with self.assertRaisesRegex(ValueError, "rest_vertex"):
            compiled.apply((float("nan"), 0.0, 0.0), 0)
        with self.assertRaises(IndexError):
            compiled.apply((0.0, 0.0, 0.0), 1)


if __name__ == "__main__":
    unittest.main()
