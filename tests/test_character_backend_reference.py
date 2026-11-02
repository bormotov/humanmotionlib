# SPDX-License-Identifier: Apache-2.0
"""Backend reference-cache equivalence on authored source poses.

This test uses small inert Blender import stubs only to access the backend's
cache method. No Blender objects, evaluated vertices, or physical measurements
are fabricated; the observation arrays below are explicitly synthetic solely
to verify unchanged residual maximum and first-argmax bookkeeping.
"""

from copy import deepcopy
import importlib
import math
from pathlib import Path
import sys
import types
import unittest
from unittest import mock

import yaml

from humanmotionlib.character_skinning import (
    compile_weight_set, skin_vertex, source_world_transforms,
)
from humanmotionlib.character_surface import _rest_frames, expand_surface
from humanmotionlib.diagnostics import DiagnosticEvaluator
from humanmotionlib.validate import load_sources


ROOT = Path(__file__).resolve().parents[1]


def _backend_class():
    existing = sys.modules.get("humanmotionlib.blender_backend")
    if existing is not None:
        return existing.SkeletonBackend
    fake_bpy = types.ModuleType("bpy")
    fake_mathutils = types.ModuleType("mathutils")
    fake_mathutils.Matrix = object
    fake_mathutils.Vector = object
    with mock.patch.dict(sys.modules, {"bpy": fake_bpy, "mathutils": fake_mathutils}):
        module = importlib.import_module("humanmotionlib.blender_backend")
    return module.SkeletonBackend


class CharacterBackendReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.SkeletonBackend = _backend_class()
        cls.sources, _ = load_sources("adult-reference-v1", root=ROOT)
        cls.evaluator = DiagnosticEvaluator(cls.sources)
        template = yaml.safe_load((ROOT / "characters/templates/exercise-mannequin-v1.yaml").read_text())
        appearance = yaml.safe_load((ROOT / "characters/appearances/male-v1.yaml").read_text())
        cls.surface = expand_surface(cls.sources["profile"], template, appearance, 1.70)
        _, cls.rest_frames = _rest_frames(cls.sources["profile"], 1.0)
        cls.carriers = sorted({carrier for component in cls.surface["components"]
                               for row in component["weights"] for carrier in row})

    def test_compiled_backend_cache_preserves_source_reference_maxima_and_first_ids(self):
        backend = self.SkeletonBackend.__new__(self.SkeletonBackend)
        backend._surface_pose_skinning_cache = {}
        root_translation = (0.23, -0.14, 0.07)
        cases = (("rest", 0.0), ("neutral", 0.0), ("squat", 2.0), ("arm-raise", 2.0))

        for fixture, beat in cases:
            with self.subTest(fixture=fixture, beat=beat):
                sample = self.evaluator.evaluate(fixture, beat)
                local_transforms = source_world_transforms(
                    self.sources["profile"], sample["frames"], self.carriers,
                    rest_frames=self.rest_frames)
                shifted_frames = deepcopy(sample["frames"])
                for frame in shifted_frames.values():
                    frame["position_m"] = [frame["position_m"][axis] + root_translation[axis]
                                            for axis in range(3)]
                world_transforms = source_world_transforms(
                    self.sources["profile"], shifted_frames, self.carriers,
                    rest_frames=self.rest_frames)

                for component in self.surface["components"]:
                    weight_set = compile_weight_set(component["weights"])
                    local_kernel = backend._compiled_surface_pose(
                        "native-local", local_transforms, weight_set)
                    world_kernel = backend._compiled_surface_pose(
                        "source-world", world_transforms, weight_set)
                    self.assertIsNot(local_kernel, world_kernel)
                    self.assertIs(world_kernel, backend._compiled_surface_pose(
                        "source-world", world_transforms, weight_set))

                    local_reference = []
                    world_reference = []
                    for index, (vertex, influences) in enumerate(zip(
                            component["vertices_m"], component["weights"])):
                        local_expected = skin_vertex(vertex, influences, local_transforms)
                        world_expected = skin_vertex(vertex, influences, world_transforms)
                        local_actual = local_kernel.apply(vertex, index)
                        world_actual = world_kernel.apply(vertex, index)
                        self.assertEqual(local_actual, local_expected)
                        self.assertEqual(world_actual, world_expected)
                        local_reference.append(local_actual)
                        world_reference.append(world_actual)

                    # Exercise the backend's existing max/list.index semantics
                    # against a deterministic synthetic observed array. This
                    # checks metadata bookkeeping only, not Blender deformation.
                    for reference in (local_reference, world_reference):
                        observed = []
                        for index, point in enumerate(reference):
                            error = 4e-7 if index in (0, len(reference) // 2) else 1e-8 * (index % 5 + 1)
                            observed.append((point[0] + error, point[1], point[2]))
                        scalar_errors = [math.dist(skin_vertex(vertex, weights,
                                                               local_transforms if reference is local_reference else world_transforms),
                                                   actual)
                                         for vertex, weights, actual in zip(
                                             component["vertices_m"], component["weights"], observed)]
                        compiled_errors = [math.dist(expected, actual)
                                           for expected, actual in zip(reference, observed)]
                        scalar_max = max(scalar_errors, default=0.0)
                        compiled_max = max(compiled_errors, default=0.0)
                        scalar_worst = scalar_errors.index(scalar_max) if scalar_errors else None
                        compiled_worst = compiled_errors.index(compiled_max) if compiled_errors else None
                        self.assertEqual(compiled_max, scalar_max)
                        self.assertEqual(compiled_worst, scalar_worst)
                        if scalar_worst is not None:
                            self.assertEqual(component["vertex_ids"][compiled_worst],
                                             component["vertex_ids"][scalar_worst])


if __name__ == "__main__":
    unittest.main()
