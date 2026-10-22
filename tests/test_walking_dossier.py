# SPDX-License-Identifier: Apache-2.0
"""Independent preflight of the frozen design, before building a Blender rig.

All values below are from anatomical-human-skeleton/design.md sections 3, 5,
and 7, including the human-authorized correction. The original penetrating
trajectory is retained as a negative regression, not accepted or skipped.
"""

import math
import unittest


def multiply(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3))
             for j in range(3)] for i in range(3)]


def transform(a, v):
    return [sum(a[i][j] * v[j] for j in range(3)) for i in range(3)]


def rx(degrees):
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return [[1, 0, 0], [0, c, -s], [0, s, c]]


def rz(degrees):
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def legacy_toe_bottom_height(beat):
    """World Z/H of the third toe's rigidly attached neutral bottom point.

    The neutral toe cap center is (0, .107, -.034) H relative to the
    ankle. Its radius is .006 H, so (0, .107, -.040) H is a surface point.
    Measuring this one point suffices to disprove whole-mesh floor clearance;
    it does not substitute for the later complete evaluated-mesh verifier.
    Left swing is the mirror of this right-side construction; mirroring
    through X=0 preserves its Z and hence the same floor violation.
    """
    if not 0 <= beat <= 2:
        raise ValueError("Expected a beat in the first swing interval [0,2]")
    w = math.sin(math.pi * beat / 2) ** 2
    hip, knee, ankle = 30 * w, 60 * w, 12 * w
    t = min(1.0, max(0.0, knee / 30))
    twist = -8 * (3 * t * t - 2 * t * t * t)
    k_matrix = multiply(rx(-knee), rz(twist))
    translation = [0, -.003 * math.sin(math.radians(knee)),
                   -.001 * (1 - math.cos(math.radians(knee)))]
    shank = transform(k_matrix, [0, 0, -.2155])
    hip_to_ankle = [shank[j] + translation[j] + [0, 0, -.234][j]
                   for j in range(3)]
    ankle_position = transform(rx(hip), hip_to_ankle)
    ankle_position[2] += .4895
    foot_rotation = multiply(multiply(rx(hip), k_matrix), rx(ankle))
    toe_offset = transform(foot_rotation, [0, .107, -.040])
    return ankle_position[2] + toe_offset[2]


def transpose(matrix):
    return list(map(list, zip(*matrix)))


def axis_rotation(axis, degrees):
    x, y, z = axis
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    d = 1 - c
    return [[c+x*x*d, x*y*d-z*s, x*z*d+y*s],
            [y*x*d+z*s, c+y*y*d, y*z*d-x*s],
            [z*x*d-y*s, z*y*d+x*s, c+z*z*d]]


def corrected_swing(beat):
    if not 0 <= beat <= 2:
        raise ValueError("Expected a beat in [0,2]")
    w = math.sin(math.pi * beat / 2) ** 2
    knee, ankle = 60 * w, 12 * w
    t = min(1.0, knee / 30)
    k = multiply(rx(-knee), rz(8 * (3*t*t - 2*t*t*t)))
    d = [0, -.003 * math.sin(math.radians(knee)),
         -.001 * (1 - math.cos(math.radians(knee)))]
    shank = transform(k, [0, 0, -.2155])
    offset = [shank[j] + d[j] + [0, 0, -.234][j] for j in range(3)]
    h = [-math.sin(math.radians(23))*math.cos(math.radians(40)),
         math.cos(math.radians(23))*math.cos(math.radians(40)),
         math.sin(math.radians(40))]

    def trial(inversion):
        a = multiply(rx(ankle), axis_rotation(h, inversion))
        hip = transpose(multiply(k, a))
        return hip, transform(hip, offset), a

    lo, hi = -10.0, 20.0
    if trial(lo)[1][0] * trial(hi)[1][0] > 0:
        raise ValueError("No sign-changing hindfoot bracket")
    for _ in range(60):
        mid = (lo + hi) / 2
        if trial(lo)[1][0] * trial(mid)[1][0] <= 0:
            hi = mid
        else:
            lo = mid
    inversion = (lo + hi) / 2
    hip, position, a = trial(inversion)
    position[0] += .055
    position[2] += .4895
    angles = [math.degrees(math.atan2(-hip[1][2], hip[2][2])),
              math.degrees(math.asin(hip[0][2])),
              -math.degrees(math.atan2(-hip[0][1], hip[0][0]))]
    return {"knee": knee, "ankle": ankle, "inversion": inversion,
            "hip": angles, "position": position,
            "foot": multiply(multiply(hip, k), a),
            "clearance": position[2] - .04}


class WalkingDossierTests(unittest.TestCase):
    def test_original_trajectory_is_rejected(self):
        self.assertLess(legacy_toe_bottom_height(.35), -1e-4)
        self.assertAlmostEqual(legacy_toe_bottom_height(.35), -.004545930449, places=10)

    def test_neutral_endpoints(self):
        for beat in (0, 2):
            sample = corrected_swing(beat)
            self.assertAlmostEqual(sample["clearance"], 0, places=12)
            for measured, expected in zip(sample["position"], [.055, 0, .04]):
                self.assertAlmostEqual(measured, expected, places=12)

    def test_corrected_reference_table(self):
        for w, inversion, hip, position in [(0.25, -0.7110441459852475, [11.756730884815061, -0.44986349281763405, 3.519858446240855], [0.03484105721527587, 0.04507094502071879]), (0.5, -2.6674604879707617, [22.99970126953395, -1.5833157425692888, 6.1110714480225585], [0.06447185549483554, 0.059593055497377145]), (0.75, -3.7643139784746484, [34.62308976496683, -2.0841007833975436, 5.225423699786239], [0.09323116864739983, 0.08367224178481592]), (1, -4.7316936771744125, [46.30963115841926, -2.422945563006178, 4.389235643242097], [0.11736975137003702, 0.11645028285316211])]:
            beat = 2 * math.asin(math.sqrt(w)) / math.pi
            sample = corrected_swing(beat)
            self.assertAlmostEqual(sample["inversion"], inversion, places=8)
            for measured, expected in zip(sample["hip"], hip):
                self.assertAlmostEqual(measured, expected, places=8)
            for measured, expected in zip(sample["position"][1:], position):
                self.assertAlmostEqual(measured, expected, places=8)

    def check_sample(self, beat):
        sample = corrected_swing(beat)
        self.assertGreaterEqual(sample["clearance"], -1e-4, f"beat={beat}")
        self.assertAlmostEqual(sample["position"][0], .055, places=12)
        f, b, r = sample["hip"]
        score = (max(0, f)/120)**2 + (b/(10 if b>=0 else 30))**2 + (r/(35 if r>=0 else 30))**2
        self.assertGreaterEqual(f, -15)
        self.assertLessEqual(score, 1 + 1e-12)
        self.assertTrue(-10 <= sample["inversion"] <= 20)
        self.assertTrue(0 <= sample["knee"] <= 60 + 1e-12)
        self.assertTrue(0 <= sample["ankle"] <= 12 + 1e-12)
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(sample["foot"][i][j], int(i == j), places=12)
        return sample

    def test_published_frame_times_clear_floor(self):
        for bpm, intervals in ((60, 5), (120, 3), (180, 3)):
            with self.subTest(bpm=bpm):
                for j in range(2 * intervals + 1):
                    self.check_sample(j / intervals)

    def test_dense_swing_clears_floor(self):
        previous = None
        for j in range(801):
            sample = self.check_sample(j / 400)
            if previous is not None:
                self.assertLessEqual(abs(sample["knee"]-previous["knee"]), .25)
            previous = sample
        apex = self.check_sample(1)
        self.assertGreaterEqual(apex["clearance"], .02)
        self.assertGreaterEqual(apex["knee"], 45)
        for stature in (1.50, 1.70, 1.90):
            self.assertGreaterEqual(apex["clearance"] * stature, .02 * stature)
