# SPDX-License-Identifier: Apache-2.0
"""Focused tests for the backend-independent character skinning oracle."""

import math

import unittest

from humanmotionlib.character_skinning import skin_vertex,source_world_transforms


def _transform(*, rest_t=(0.0, 0.0, 0.0), rest_q=(1.0, 0.0, 0.0, 0.0),
               posed_t=(0.0, 0.0, 0.0), posed_q=(1.0, 0.0, 0.0, 0.0)):
    return {
        "rest_translation": rest_t,
        "rest_orientation": rest_q,
        "posed_translation": posed_t,
        "posed_orientation": posed_q,
    }


class CharacterSkinningTests(unittest.TestCase):
    def assertClose(self, actual, expected, tolerance=1e-12):
        self.assertEqual(len(actual), len(expected))
        for left, right in zip(actual, expected):
            self.assertAlmostEqual(left, right, delta=tolerance)

    def test_identity_and_equal_rest_pose_are_exact_noops(self):
        rest = _transform(rest_t=(2.0, -3.0, 4.0), rest_q=(0.5, 0.5, 0.5, 0.5),
                          posed_t=(2.0, -3.0, 4.0), posed_q=(0.5, 0.5, 0.5, 0.5))
        self.assertClose(skin_vertex((0.2, -0.4, 0.8), {"pelvis": 1.0}, {"pelvis": rest}),
                         (0.2, -0.4, 0.8))

    def test_single_influence_applies_rigid_rotation_and_translation(self):
        half = math.sqrt(0.5)
        transform = _transform(posed_t=(2.0, 1.0, -1.0), posed_q=(half, 0.0, 0.0, half))
        self.assertClose(skin_vertex((1.0, 0.0, 0.0), {"wrist": 1.0}, {"wrist": transform}),
                         (2.0, 2.0, -1.0))

    def test_source_world_transform_builder_uses_canonical_double_rest_and_raw_pose(self):
        half=math.sqrt(0.5)
        profile={"structures":[
            {"id":"pelvis","parent":None,"rest_translation_m":[0.0,0.0,0.0],
             "rest_orientation":[1.0,0.0,0.0,0.0]},
            {"id":"arm.L","parent":"pelvis","rest_translation_m":[1.0,0.0,0.0],
             "rest_orientation":[1.0,0.0,0.0,0.0]},
        ]}
        frames={"pelvis":{"position_m":[0.0,0.0,0.0],
                            "rotation":[[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]]},
                "arm.L":{"position_m":[0.0,1.0,0.0],
                          "rotation":[[0.0,-1.0,0.0],[1.0,0.0,0.0],[0.0,0.0,1.0]]}}
        transforms=source_world_transforms(profile,frames,["arm.L"])
        self.assertEqual(transforms["arm.L"]["rest_translation"],(1.0,0.0,0.0))
        self.assertEqual(transforms["arm.L"]["posed_translation"],(0.0,1.0,0.0))
        self.assertClose(transforms["arm.L"]["posed_orientation"],(half,0.0,0.0,half))
        self.assertClose(skin_vertex((1.0,0.0,0.0),{"arm.L":1.0},transforms),(0.0,1.0,0.0))

    def test_source_world_transform_builder_rejects_missing_and_nonfinite_raw_frames(self):
        profile={"structures":[{"id":"pelvis","parent":None,
            "rest_translation_m":[0.0,0.0,0.0],"rest_orientation":[1.0,0.0,0.0,0.0]}]}
        with self.assertRaisesRegex(ValueError,"missing carrier"):
            source_world_transforms(profile,{},["pelvis"])
        frames={"pelvis":{"position_m":[float("nan"),0.0,0.0],
                           "rotation":[[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]]}}
        with self.assertRaisesRegex(ValueError,"finite"):
            source_world_transforms(profile,frames,["pelvis"])

    def test_two_influences_blend_translation_and_normalize_weights(self):
        transforms = {
            "a": _transform(posed_t=(2.0, 0.0, 0.0)),
            "b": _transform(posed_t=(0.0, 4.0, 0.0)),
        }
        self.assertClose(skin_vertex((1.0, 2.0, 3.0), {"a": 2.0, "b": 2.0}, transforms),
                         (2.0, 4.0, 3.0))

    def test_hemisphere_flip_keeps_equivalent_quaternion_signs_aligned(self):
        transforms = {
            "a": _transform(posed_t=(1.0, 0.0, 0.0), posed_q=(1.0, 0.0, 0.0, 0.0)),
            "b": _transform(posed_t=(3.0, 0.0, 0.0), posed_q=(-1.0, 0.0, 0.0, 0.0)),
        }
        self.assertClose(skin_vertex((0.0, 0.0, 0.0), {"a": 0.5, "b": 0.5}, transforms),
                         (2.0, 0.0, 0.0))

    def test_translation_uses_relative_rest_and_posed_frames(self):
        transform = _transform(rest_t=(5.0, 1.0, -2.0), posed_t=(7.0, 4.0, 0.0))
        self.assertClose(skin_vertex((5.5, 1.0, -2.0), {"bone": 1.0}, {"bone": transform}),
                         (7.5, 4.0, 0.0))

    def test_mirrored_rigid_result_commutes_with_reflection(self):
        half = math.sqrt(0.5)
        right = _transform(posed_t=(0.3, -0.2, 0.4), posed_q=(half, 0.0, 0.0, half))
        left = _transform(posed_t=(-0.3, -0.2, 0.4), posed_q=(half, 0.0, 0.0, -half))
        right_result = skin_vertex((0.4, 0.7, 1.1), {"wrist.R": 1.0}, {"wrist.R": right})
        left_result = skin_vertex((-0.4, 0.7, 1.1), {"wrist.L": 1.0}, {"wrist.L": left})
        self.assertClose(left_result, (-right_result[0], right_result[1], right_result[2]))

    def test_rigid_reference_is_homogeneous_in_world_unit_scale(self):
        half = math.sqrt(0.5)
        for scale in (1.50, 1.70, 1.90):
            transform = _transform(rest_t=(0.1*scale, 0.2*scale, -0.1*scale),
                                   posed_t=(0.3*scale, -0.2*scale, 0.4*scale),
                                   posed_q=(half, 0.0, 0.0, half))
            vertex = (0.4*scale, 0.7*scale, 1.1*scale)
            result = skin_vertex(vertex, {"wrist": 1.0}, {"wrist": transform})
            expected = tuple(scale * value for value in skin_vertex(
                (0.4, 0.7, 1.1), {"wrist": 1.0},
                {"wrist": _transform(rest_t=(0.1, 0.2, -0.1), posed_t=(0.3, -0.2, 0.4),
                                      posed_q=(half, 0.0, 0.0, half))}))
            self.assertClose(result, expected)


    def test_equal_weight_tie_uses_carrier_id_not_mapping_insertion_order(self):
        # Three equally weighted rotations span more than one hemisphere. The
        # lexically first carrier anchors the sign choices, regardless of mapping
        # insertion order.
        def qx(degrees):
            radians = math.radians(degrees) / 2.0
            return math.cos(radians), math.sin(radians), 0.0, 0.0

        items = [("a", qx(0)), ("b", qx(100)), ("c", qx(200))]
        transforms_1 = {key: _transform(posed_q=q) for key, q in items}
        transforms_2 = dict(reversed(list(transforms_1.items())))
        weights_1 = {"c": 1.0, "a": 1.0, "b": 1.0}
        weights_2 = dict(reversed(list(weights_1.items())))
        result_1 = skin_vertex((0.0, 1.0, 0.0), weights_1, transforms_1)
        result_2 = skin_vertex((0.0, 1.0, 0.0), weights_2, transforms_2)
        self.assertClose(result_1, result_2)
        self.assertLess(result_1[2], -0.2)  # lexical anchor `a`; `c` rotates the other way


    def test_singular_or_nonfinite_transform_fails(self):
        for bad_quaternion in ((0.0, 0.0, 0.0, 0.0),
                               (float("nan"), 0.0, 0.0, 1.0),
                               (float("inf"), 0.0, 0.0, 1.0)):
            with self.subTest(quaternion=bad_quaternion), self.assertRaises(ValueError):
                skin_vertex((0.0, 0.0, 0.0), {"bone": 1.0},
                            {"bone": _transform(posed_q=bad_quaternion)})

    def test_nonfinite_vertex_and_invalid_weights_fail(self):
        identity = {"bone": _transform()}
        with self.assertRaisesRegex(ValueError, "rest_vertex"):
            skin_vertex((float("nan"), 0.0, 0.0), {"bone": 1.0}, identity)
        with self.assertRaisesRegex(ValueError, "non-negative"):
            skin_vertex((0.0, 0.0, 0.0), {"bone": -1.0}, identity)
        with self.assertRaisesRegex(ValueError, "positive finite sum"):
            skin_vertex((0.0, 0.0, 0.0), {"bone": 0.0}, identity)


if __name__ == "__main__":
    unittest.main()
