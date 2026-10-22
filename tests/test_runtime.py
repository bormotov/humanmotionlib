# SPDX-License-Identifier: Apache-2.0
import unittest

from tools.runtime import backend_contract, check_blender_version, inspect_blender


class BackendContractTests(unittest.TestCase):
    def test_pinned_backend(self):
        expected = backend_contract()
        check_blender_version(expected["blender-version"], expected["blender-build"])
        for version, build in [("5.2.1 LTS", expected["blender-build"]),
                               (expected["blender-version"], "another-build")]:
            with self.subTest(version=version, build=build):
                with self.assertRaisesRegex(ValueError, "version mismatch"):
                    check_blender_version(version, build)

    def test_installed_backend(self):
        self.assertEqual(inspect_blender()["build_hash"], backend_contract()["blender-build"])
