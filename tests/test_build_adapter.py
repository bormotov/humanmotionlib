"""Contract tests for deterministic package staging and sdist rebuild closure."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import hml_build_backend


class BuildAdapterTests(unittest.TestCase):
    def _package(self, root: Path) -> Path:
        package = root / "src" / "humanmotionlib"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("# staged fixture\n", encoding="utf-8")
        return package

    def test_stages_explicit_resources_and_generated_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = self._package(Path(temporary))
            hml_build_backend._stage_resources(hml_build_backend._ROOT, package, "0.2.0")

            resources = package / "resources"
            manifest = json.loads((resources / "runtime-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["format"], "humanmotionlib-runtime-manifest/v1")
            self.assertEqual(manifest["version"], "0.2.0")
            self.assertEqual(len(manifest["resources"]), 50)
            self.assertIn("rig/diagnostics/walking-in-place.yaml", manifest["resources"])
            self.assertIn("schema/profile.schema.json", manifest["resources"])
            self.assertIn("docs/usage.md", manifest["resources"])
            self.assertNotIn("backend-contract.json", manifest["resources"])
            self.assertIn("humanmotionlib/__init__.py", manifest["implementation"])
            self.assertIn("humanmotionlib/_version.py", manifest["implementation"])
            self.assertEqual(
                manifest["backend_contract"],
                hashlib.sha256((resources / "backend-contract.json").read_bytes()).hexdigest(),
            )
            self.assertEqual(
                manifest["implementation"]["humanmotionlib/_version.py"],
                hashlib.sha256((package / "_version.py").read_bytes()).hexdigest(),
            )

    def test_missing_canonical_resource_directory_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(RuntimeError, "Required resource directory"):
                hml_build_backend._canonical_resources(Path(temporary))

    def test_extracted_sdist_closure_rebuilds_without_canonical_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            extracted_package = self._package(root)
            hml_build_backend._stage_resources(hml_build_backend._ROOT, extracted_package, "0.2.0")

            # The adapter should consume the already staged closure; the extracted root
            # deliberately has no rig/, schema/, scenes/ or docs/ authoring directories.
            manifest_path = extracted_package / "resources" / "runtime-manifest.json"
            original_manifest = manifest_path.read_bytes()
            hml_build_backend._stage_resources(root, extracted_package, "0.2.0")
            self.assertEqual(manifest_path.read_bytes(), original_manifest)

            (extracted_package / "resources" / "rig" / "body-groups.yaml").write_text(
                "tampered\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(RuntimeError, "runtime manifest"):
                hml_build_backend._stage_resources(root, extracted_package, "0.2.0")

    def test_sdist_staging_carries_locked_contributor_context(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            staged = hml_build_backend._stage_project(hml_build_backend._ROOT, Path(temporary))
            for name in (".python-version", "uv.lock"):
                with self.subTest(name=name):
                    self.assertEqual((staged / name).read_bytes(), (hml_build_backend._ROOT / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
