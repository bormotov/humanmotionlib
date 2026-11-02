# SPDX-License-Identifier: Apache-2.0
"""Version identity remains derived from the declared project version."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib
import unittest

from humanmotionlib.runtime import project_root
from tests.run_roots import test_case_root, test_run_root


def setUpModule() -> None:
    test_run_root("version_builds")


class DeclaredVersionBuildTests(unittest.TestCase):
    def test_two_project_versions_stage_consistent_runtime_identity(self) -> None:
        case_root = test_case_root("version_builds", "two-declared-versions")
        repository = project_root()
        project_files = (
            "pyproject.toml", ".python-version", "uv.lock", "hml_build_backend.py",
            "MANIFEST.in", "LICENSE-CODE", "LICENSE-DATA", "THIRD-PARTY-NOTICES.md",
        )
        project_directories = ("src/humanmotionlib", "rig", "scenes", "schema", "docs", "characters")
        resource_inventory = None

        try:
            with (repository / "pyproject.toml").open("rb") as stream:
                canonical_version = tomllib.load(stream)["project"]["version"]
            versions = (canonical_version, "0.91.7")

            for index, version in enumerate(versions):
                with self.subTest(version=version):
                    source_root = case_root / f"source-{index}"
                    source_root.mkdir()
                    for name in project_files:
                        shutil.copy2(repository / name, source_root / name)
                    for name in project_directories:
                        shutil.copytree(repository / name, source_root / name)

                    project_file = source_root / "pyproject.toml"
                    project_text = project_file.read_text(encoding="utf-8")
                    if version != canonical_version:
                        project_text = project_text.replace(
                            f'version = "{canonical_version}"', f'version = "{version}"', 1
                        )
                        project_file.write_text(project_text, encoding="utf-8")

                    stage_parent = case_root / f"stage-{index}"
                    stage_parent.mkdir()
                    module_spec = importlib.util.spec_from_file_location(
                        f"hml_build_backend_release_{index}", source_root / "hml_build_backend.py"
                    )
                    self.assertIsNotNone(module_spec)
                    backend = importlib.util.module_from_spec(module_spec)
                    self.assertIsNotNone(module_spec.loader)
                    module_spec.loader.exec_module(backend)
                    staged = backend._stage_project(source_root, stage_parent)

                    staged_version = tomllib.loads(
                        (staged / "pyproject.toml").read_text(encoding="utf-8")
                    )["project"]["version"]
                    self.assertEqual(staged_version, version)
                    package_root = staged / "src"
                    self.assertEqual(
                        (package_root / "humanmotionlib" / "_version.py").read_text(encoding="utf-8"),
                        f'__version__ = "{version}"\n',
                    )
                    manifest = json.loads(
                        (package_root / "humanmotionlib" / "resources" / "runtime-manifest.json")
                        .read_text(encoding="utf-8")
                    )
                    self.assertEqual(manifest["version"], version)
                    if resource_inventory is None:
                        resource_inventory = manifest["resources"]
                    else:
                        self.assertEqual(manifest["resources"], resource_inventory)

                    outside = case_root / f"outside-{index}"
                    outside.mkdir()
                    environment = os.environ.copy()
                    environment["PYTHONPATH"] = str(package_root)
                    environment.pop("PYTHONHOME", None)
                    result = subprocess.run(
                        [sys.executable, "-m", "humanmotionlib", "--version"],
                        cwd=outside,
                        env=environment,
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    self.assertEqual(result.stdout.strip(), f"humanmotionlib {version}")
        finally:
            shutil.rmtree(case_root)


if __name__ == "__main__":
    unittest.main()
