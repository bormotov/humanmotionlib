"""Contract tests for deterministic package staging and sdist rebuild closure."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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
            hml_build_backend._stage_resources(hml_build_backend._ROOT, package, "0.91.7")

            resources = package / "resources"
            manifest = json.loads((resources / "runtime-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["format"], "humanmotionlib-runtime-manifest/v1")
            self.assertGreaterEqual(len(manifest["resources"]), 52)
            self.assertIn("rig/diagnostics/walking-in-place.yaml", manifest["resources"])
            self.assertIn("schema/profile.schema.json", manifest["resources"])
            self.assertIn("schema/consumer-motion.schema.json", manifest["resources"])
            self.assertIn("schema/consumer-motion-snapshot.schema.json", manifest["resources"])
            self.assertIn("docs/usage.md", manifest["resources"])
            self.assertIn("docs/character-models.md", manifest["resources"])
            self.assertIn("characters/registry.yaml", manifest["resources"])
            self.assertIn("characters/definitions/skeleton.yaml", manifest["resources"])
            self.assertIn("characters/definitions/male.yaml", manifest["resources"])
            self.assertIn("characters/definitions/female.yaml", manifest["resources"])
            self.assertIn("characters/templates/exercise-mannequin-v1.yaml", manifest["resources"])
            self.assertIn("characters/appearances/male-v1.yaml", manifest["resources"])
            self.assertIn("characters/appearances/female-v1.yaml", manifest["resources"])
            self.assertTrue(any(name.startswith("schema/character-") for name in manifest["resources"]))
            for logical_name in sorted(name for name in manifest["resources"]
                                        if name.startswith("characters/")
                                        or name.startswith("schema/character-")
                                        or name == "docs/character-models.md"):
                with self.subTest(resource=logical_name):
                    self.assertEqual(
                        (resources / logical_name).read_bytes(),
                        (hml_build_backend._ROOT / logical_name).read_bytes(),
                    )
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

    def test_repeated_staging_preserves_resource_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifests = []
            for index in range(2):
                package = self._package(root / f"build-{index}")
                hml_build_backend._stage_resources(hml_build_backend._ROOT, package, "fixture")
                manifest = json.loads(
                    (package / "resources" / "runtime-manifest.json").read_text(encoding="utf-8")
                )
                manifests.append(manifest["resources"])
            self.assertEqual(manifests[0], manifests[1])

    def test_missing_canonical_resource_directory_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(RuntimeError, "Required resource directory"):
                hml_build_backend._canonical_resources(Path(temporary))

    def test_read_only_snapshot_is_copied_into_writable_adapter_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._package(root)
            (source / "nested").mkdir()
            (source / "nested" / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
            for path in (source / "nested" / "module.py", source / "nested", source, source.parent):
                path.chmod(0o555 if path.is_dir() else 0o444)
            target = root / "adapter-stage" / "src" / "humanmotionlib"
            try:
                with mock.patch.object(hml_build_backend, "_ROOT", root):
                    hml_build_backend._copy_python_package(source, target)
                self.assertTrue(target.is_dir())
                self.assertTrue(target.stat().st_mode & 0o200)
                self.assertTrue((target / "nested").stat().st_mode & 0o200)
                self.assertTrue((target / "nested" / "module.py").stat().st_mode & 0o200)
                self.assertEqual((source / "nested" / "module.py").read_text(), "VALUE = 1\n")
            finally:
                for path in sorted(root.rglob("*"), reverse=True):
                    if path.is_file():
                        path.chmod(0o644)
                    elif path.is_dir():
                        path.chmod(0o755)
                root.chmod(0o755)

    def test_extracted_sdist_closure_rebuilds_without_canonical_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            extracted_package = self._package(root)
            hml_build_backend._stage_resources(hml_build_backend._ROOT, extracted_package, "0.91.7")

            # The adapter should consume the already staged closure; the extracted root
            # deliberately has no rig/, schema/, scenes/ or docs/ authoring directories.
            manifest_path = extracted_package / "resources" / "runtime-manifest.json"
            original_manifest = manifest_path.read_bytes()
            manifest = json.loads(original_manifest)
            character_resources = sorted(
                name for name in manifest["resources"]
                if name.startswith("characters/") or name.startswith("schema/character-")
                or name == "docs/character-models.md"
            )
            self.assertTrue(character_resources)
            original_character_bytes = {
                name: (extracted_package / "resources" / name).read_bytes()
                for name in character_resources
            }
            hml_build_backend._stage_resources(root, extracted_package, "0.91.7")
            self.assertEqual(manifest_path.read_bytes(), original_manifest)
            self.assertEqual({
                name: (extracted_package / "resources" / name).read_bytes()
                for name in character_resources
            }, original_character_bytes)

            (extracted_package / "resources" / "characters" / "registry.yaml").write_text(
                "tampered\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(RuntimeError, "runtime manifest"):
                hml_build_backend._stage_resources(root, extracted_package, "0.91.7")

    def test_sdist_staging_carries_locked_contributor_context(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            staged = hml_build_backend._stage_project(hml_build_backend._ROOT, Path(temporary))
            for name in (".python-version", "uv.lock"):
                with self.subTest(name=name):
                    self.assertEqual((staged / name).read_bytes(), (hml_build_backend._ROOT / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
