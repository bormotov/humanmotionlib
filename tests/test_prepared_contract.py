# SPDX-License-Identifier: Apache-2.0
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from humanmotionlib import math3d as m
from humanmotionlib.prepare_skeleton import prepare
from humanmotionlib.prepared import canonical_bytes, read_prepared, seal, write_json
from humanmotionlib.verify_skeleton import verify_transforms


class PreparedContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.prepared = prepare("adult-reference-v1",fixtures=["neutral","rest"])

    def test_deterministic_order_hashes_and_independent_frames(self):
        self.assertEqual(canonical_bytes(self.prepared),canonical_bytes(prepare("adult-reference-v1",fixtures=["neutral","rest"])))
        self.assertEqual(verify_transforms(self.prepared)["status"],"pass")
        self.assertTrue(any(p.startswith("schema/") for p in self.prepared["source_hashes"]))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"input.json"
            write_json(path,self.prepared)
            self.assertEqual(read_prepared(path),self.prepared)

    def test_separate_measurement_rejects_modified_frames_and_missing_samples(self):
        samples = deepcopy(self.prepared["samples"])
        samples[0]["frames"]["scapula.R"]["rotation"] = m.I
        self.assertEqual(verify_transforms(self.prepared,samples)["status"],"fail")
        with self.assertRaisesRegex(ValueError,"Missing/extra"): verify_transforms(self.prepared,samples[:-1])

    def test_content_and_source_hash_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"input.json"
            value = deepcopy(self.prepared)
            value["sources"]["profile"]["stature_m"] = 2
            write_json(path,value)
            with self.assertRaisesRegex(ValueError,"content hash"): read_prepared(path)
            value = deepcopy(self.prepared)
            value["source_hashes"]["schema/profile.schema.json"] = "0"*64
            write_json(path,seal(value))
            with self.assertRaisesRegex(ValueError,"Source/schema hash"): read_prepared(path)

    def test_stature_scales_positions_not_angles(self):
        value = prepare("adult-reference-v1",1.9,fixtures=["neutral","rest"])
        self.assertEqual(value["sources"]["profile"]["stature_m"],1.9)
        self.assertEqual(verify_transforms(value)["status"],"pass")
        self.assertAlmostEqual(value["samples"][0]["frames"]["pelvis"]["position_m"][2],.4895*1.9)
