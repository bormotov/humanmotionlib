# SPDX-License-Identifier: Apache-2.0
import math
import unittest

from humanmotionlib import math3d as m


class TransformTests(unittest.TestCase):
    def assertVector(self, actual, expected, places=12):
        for a, b in zip(actual, expected): self.assertAlmostEqual(a, b, places=places)

    def assertMatrix(self, actual, expected):
        for a, b in zip(actual, expected): self.assertVector(a, b)

    def test_active_sign_and_parent_composition(self):
        self.assertVector(m.mv(m.rx(90), [0, 1, 0]), [0, 0, 1])
        p, r = m.compose(([1, 2, 3], m.rz(90)), [1, 0, 0], m.quaternion(m.rx(90)))
        self.assertVector(p, [1, 3, 3])
        self.assertVector(m.mv(r, [0, 1, 0]), [0, 0, 1])
        self.assertVector(m.mv(r, [1, 0, 0]), [0, 1, 0])

    def test_rest_relative_delta(self):
        rest = m.quaternion(m.ry(90))
        solved = m.quaternion(m.mm(m.ry(90), m.rx(30)))
        delta = m.local_delta(rest, solved)
        self.assertMatrix(m.qmatrix(delta), m.rx(30))
        self.assertMatrix(m.qmatrix(m.qmul(rest, delta)), m.qmatrix(solved))
        self.assertMatrix(m.qmatrix(m.scale(solved, -1)), m.qmatrix(solved))

    def test_quaternion_round_trips_near_pi(self):
        for axis in ([1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 2, 3]):
            for angle in (0, 90, 179.999999, 180, 270, 360):
                r = m.rot(axis, angle)
                self.assertMatrix(m.qmatrix(m.quaternion(r)), r)

    def test_reject_invalid_frames_and_quaternions(self):
        for q in ([2, 0, 0, 0], [1.000002, 0, 0, 0], [float("nan"), 0, 0, 0]):
            with self.assertRaises(ValueError): m.qmatrix(q)
        for basis in ([[2, 0, 0], [0, 1, 0], [0, 0, 1]],
                      [[-1, 0, 0], [0, 1, 0], [0, 0, 1]]):
            with self.assertRaises(ValueError): m.validate_basis(basis)

    def test_dossier_shaft_basis(self):
        for end in ([0, 0, -1], [0, 1, 0], [1, 2, 3]):
            b = m.shaft_basis([0, 0, 0], end)
            self.assertVector(m.mv(b, [0, 1, 0]), m.unit(end))
            self.assertAlmostEqual(m.determinant(b), 1)
        with self.assertRaises(ValueError): m.shaft_basis([0, 0, 0], [0, 0, 0])

    def test_mirrored_rotations_and_positions(self):
        r = m.mm(m.rx(35), m.ry(17))
        mirrored = m.mirror_rotation(r)
        self.assertAlmostEqual(m.determinant(mirrored), 1)
        self.assertMatrix(m.mirror_rotation(mirrored), r)
        self.assertVector(m.mirror_position(m.mirror_position([2, 3, 4])), [2, 3, 4])
        self.assertVector(m.mv(mirrored, m.mirror_position([1, 2, 3])),
                          m.mirror_position(m.mv(r, [1, 2, 3])))
