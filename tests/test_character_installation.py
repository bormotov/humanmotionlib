# SPDX-License-Identifier: Apache-2.0
"""Host acceptance for a real, non-editable character-enabled wheel install."""

import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import unittest
from unittest.mock import patch

import humanmotionlib
import jsonschema
import PIL
import referencing
import yaml
from humanmotionlib import api
from humanmotionlib.characters import resolve_character_selection, validate_character_sources


CHARACTER_IDS = ("skeleton", "male", "female")
_ACCEPTANCE_CONFIGURED = all(os.environ.get(name) for name in (
    "HML_ACCEPTANCE_WORKSPACE", "HML_ACCEPTANCE_REPOSITORY", "HML_ACCEPTANCE_ROOT"))


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_hashes(root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)): _file_hash(path)
            for path in sorted(root.rglob("*")) if path.is_file() and not path.is_symlink()}


class _BackendReached(Exception):
    pass


@unittest.skipUnless(_ACCEPTANCE_CONFIGURED,
                     "requires the explicit non-editable installed-wheel acceptance harness")
class InstalledCharacterAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package_root = Path(humanmotionlib.__file__).resolve().parent
        cls.purelib = Path(sysconfig.get_paths()["purelib"]).resolve()
        # API outputs live in the repository's flat build/ directory; the
        # invoking process itself runs from a separate decoy cwd.
        cls.workspace = Path(os.environ["HML_ACCEPTANCE_REPOSITORY"]).resolve()
        cls.workspace.mkdir(parents=True, exist_ok=True)
        (cls.workspace / "build").mkdir(exist_ok=True)
        cls.original_package_hashes = _tree_hashes(cls.package_root)
        cls.cwd = Path.cwd().resolve()
        cls.prepared_for_failures = api.prepare(
            workspace=cls.workspace,
            output="build/add-shared-body-characters_r1_dev_try-123_shared-input/input.json",
            fixtures=("neutral",), bpms=(60,), stature=1.70,
        )

    @classmethod
    def tearDownClass(cls):
        if _tree_hashes(cls.package_root) != cls.original_package_hashes:
            raise AssertionError("installed HML package changed during acceptance")

    def _backend(self, prepared_path, output, **kwargs):
        output = Path(output)
        output.mkdir(parents=True, exist_ok=True)
        request = json.loads(Path(kwargs["character_request"]).read_text(encoding="utf-8"))
        (output / "build-metadata.json").write_text(json.dumps({
            "blender_version": "5.2.2 LTS", "blender_build": "not-launched",
            "platform": "host-acceptance", "render_identity": request["render_identity"],
        }), encoding="utf-8")
        (output / "skeleton.blend").write_bytes(b"host acceptance fixture")
        log = output / "processes" / "fixture" / "stdout.log"
        log.parent.mkdir(parents=True)
        log.write_text("Backend boundary fixture; Blender was not launched.\n", encoding="utf-8")
        return {"stdout_log": str(log), "backend_identity": {
            "version": "5.2.2 LTS", "build_hash": "not-launched"}}

    def _prepare(self, label):
        return api.prepare(
            workspace=self.workspace,
            output=f"build/add-shared-body-characters_r1_dev_try-123_{label}-input/input.json",
            fixtures=("neutral",), bpms=(60,), stature=1.70,
        )

    def _disposable_package(self, label):
        target = Path(os.environ["HML_ACCEPTANCE_ROOT"]).resolve() / "disposable" / label / "humanmotionlib"
        target.parent.mkdir(parents=True, exist_ok=False)
        shutil.copytree(self.package_root, target)
        for item in target.rglob("*"):
            if item.is_dir():
                item.chmod(item.stat().st_mode | 0o700)
            else:
                item.chmod(item.stat().st_mode | 0o600)
        target.chmod(target.stat().st_mode | 0o700)
        return target

    def _run_disposable_case(self, target_package: Path, script: str, label: str,
                             extra: Path | None = None) -> subprocess.CompletedProcess:
        environment = os.environ.copy()
        for key in ("PYTHONPATH", "PYTHONHOME", "HUMANMOTIONLIB_SOURCE_ROOT"):
            environment.pop(key, None)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        argv = [sys.executable, "-c", script, str(target_package.parent), str(self.workspace), label]
        if extra is not None:
            argv.append(str(extra))
        return subprocess.run(
            argv,
            cwd=Path.cwd(), env=environment, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, check=False,
        )

    def test_origin_registry_closure_and_version_are_from_noneditable_site_install(self):
        distribution = importlib.metadata.distribution("humanmotionlib")
        self.assertTrue(self.package_root.is_relative_to(self.purelib), self.package_root)
        direct_url = distribution.read_text("direct_url.json")
        if direct_url:
            self.assertFalse(json.loads(direct_url).get("dir_info", {}).get("editable", False))
        self.assertEqual(distribution.version, humanmotionlib.__version__)
        self.assertEqual(distribution.version, "0.3.0")
        for dependency in (yaml, jsonschema, PIL, referencing):
            self.assertTrue(Path(dependency.__file__).resolve().is_relative_to(self.purelib),
                            dependency.__file__)
        # These source-shaped neighbors are deliberately unrelated to the wheel.
        self.assertTrue((self.cwd / "characters/poison.yaml").is_file())
        self.assertTrue((self.cwd / "pyproject.toml").is_file())
        self.assertFalse(Path(humanmotionlib.__file__).resolve().is_relative_to(self.cwd))

        selected = resolve_character_selection(("female", "skeleton", "male"),
                                               profile_id="adult-reference-v1")
        self.assertEqual(tuple(item["id"] for item in selected), CHARACTER_IDS)
        complete = validate_character_sources()
        self.assertEqual(tuple(item["id"] for item in complete), CHARACTER_IDS)
        self.assertEqual(selected, complete)
        self.assertEqual(selected[0]["renderer_kind"], "skeletal")
        self.assertTrue(selected[0]["source_hashes"])
        for item in selected[1:]:
            self.assertEqual(item["profile_id"], "adult-reference-v1")
            self.assertTrue(item["template"]["components"])
            self.assertTrue(item["appearance"]["radius_scales"])
            self.assertTrue(item["source_hashes"])

    def test_public_prepare_render_records_are_portable_and_keep_shared_skeleton(self):
        prepared = self._prepare("api")
        prepared_bytes = prepared.prepared_path.read_bytes()
        with patch.object(api.run_blender, "run", side_effect=self._backend) as backend:
            result = api.render(prepared, workspace=self.workspace,
                                output="build/add-shared-body-characters_r1_dev_try-123_api-render",
                                characters=("female", "skeleton", "male"),
                                images=False, render_only=True)
        backend.assert_called_once()
        self.assertEqual([item.character_id for item in result.characters], list(CHARACTER_IDS))
        self.assertEqual([item.character_id for item in result.character_artifacts], list(CHARACTER_IDS))
        self.assertEqual(set(result.character_provenance), set(CHARACTER_IDS))
        self.assertEqual(result.prepared.prepared_sha256, prepared.prepared_sha256)
        self.assertEqual(result.prepared.prepared_path.read_bytes(), prepared_bytes)
        self.assertEqual(result.render_identity,
                         json.loads(result.artifacts["character_render_request"].read_text())["render_identity"])
        for record in result.characters:
            self.assertTrue(record.source_hashes)
            self.assertEqual(record.profile_id, "adult-reference-v1")
        self.assertEqual(json.loads(json.dumps(result.to_dict()))["render_identity"],
                         result.render_identity)
        self.assertTrue(all(path.is_absolute() for path in result.artifacts.values()))
        self.assertTrue(all(path.is_absolute() for group in result.character_artifacts
                            for path in group.artifacts.values()))
        request = json.loads(result.artifacts["character_render_request"].read_text(encoding="utf-8"))
        self.assertEqual(request["character_ids"], list(CHARACTER_IDS))
        unsigned = dict(request)
        identity = unsigned.pop("render_identity")
        from humanmotionlib.prepared import content_hash
        self.assertEqual(identity, content_hash(unsigned))

    def test_console_entrypoint_works_from_unrelated_cwd_with_explicit_workspace(self):
        entrypoint = Path(sys.executable).with_name("hml")
        self.assertTrue(entrypoint.is_file(), entrypoint)
        env = os.environ.copy()
        for key in ("PYTHONPATH", "PYTHONHOME", "HUMANMOTIONLIB_SOURCE_ROOT"):
            env.pop(key, None)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        cwd = Path.cwd()
        result = subprocess.run(
            [str(entrypoint), "--workspace", str(self.workspace), "prepare-skeleton",
             "--profile", "adult-reference-v1",
             "--output", "build/add-shared-body-characters_r1_dev_try-123_cli-input/input.json"],
            cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue((self.workspace / "build/add-shared-body-characters_r1_dev_try-123_cli-input/input.json").is_file())

    def test_skeleton_selection_does_not_semantically_parse_surface_sources(self):
        script = r"""
import json, pathlib, sys
sys.path.insert(0, sys.argv[1])
from humanmotionlib import api, characters
workspace = pathlib.Path(sys.argv[2]); label = sys.argv[3]
original = characters._load_yaml
calls=[]
def guard(logical):
 calls.append(logical)
 if logical.startswith('characters/templates/') or logical.startswith('characters/appearances/'):
  raise AssertionError('surface YAML parsed for skeleton: ' + logical)
 return original(logical)
characters._load_yaml = guard
selected = characters.resolve_character_selection(('skeleton',), profile_id='adult-reference-v1')
assert [row['id'] for row in selected] == ['skeleton']
api.prepare(workspace=workspace, output='build/add-shared-body-characters_r1_dev_try-123_skeleton-lazy-input/input.json', fixtures=('neutral',), bpms=(60,), stature=1.70)
print(json.dumps({'status':'pass','character_ids':['skeleton'],'surface_yaml_calls':[x for x in calls if x.startswith('characters/templates/') or x.startswith('characters/appearances/')]}))
"""
        result = self._run_disposable_case(self.package_root, script, "skeleton-lazy")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('"surface_yaml_calls": []', result.stdout)

    def test_missing_and_corrupt_packaged_sources_fail_global_integrity_before_backend_or_output(self):
        for label, mutation in (
            ("missing-appearance", "path.unlink()"),
            ("corrupt-appearance", "path.write_text('not: valid: [yaml', encoding='utf-8')"),
        ):
            with self.subTest(label=label):
                package = self._disposable_package(label)
                path = package / "resources/characters/appearances/male-v1.yaml"
                if mutation == "path.unlink()":
                    path.unlink()
                else:
                    path.write_text("not: valid: [yaml", encoding="utf-8")
                script = r"""
import pathlib, sys
sys.path.insert(0, sys.argv[1])
from humanmotionlib import api
workspace=pathlib.Path(sys.argv[2]); label=sys.argv[3]; prepared=pathlib.Path(sys.argv[4])
from humanmotionlib import run_blender
def fail_backend(*args, **kwargs): raise AssertionError('backend must not be probed')
run_blender.run=fail_backend
output=workspace/('build/add-shared-body-characters_r1_dev_try-123_' + label + '-render')
try:
 api.render(prepared, workspace=workspace, output=output, images=False, characters=('male',))
except api.GenerationError as error:
 assert error.code == 'input-integrity', error.to_dict()
else:
 raise AssertionError('invalid package inventory was accepted')
assert not output.exists(), output
print('package resource rejected before output and backend probe')
"""
                result = self._run_disposable_case(package, script, label, self.prepared_for_failures.prepared_path)
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertIn("package resource rejected before output", result.stdout)

    def test_corrupt_implementation_copy_fails_integrity_without_touching_install(self):
        package = self._disposable_package("corrupt-implementation")
        source = package / "characters.py"
        source.write_bytes(source.read_bytes() + b"\n# disposable tamper\n")
        script = r"""
import pathlib, sys
sys.path.insert(0, sys.argv[1])
from humanmotionlib import api, run_blender
workspace=pathlib.Path(sys.argv[2]); label=sys.argv[3]; prepared=pathlib.Path(sys.argv[4])
output=workspace/('build/add-shared-body-characters_r1_dev_try-123_' + label + '-render')
def fail_backend(*args, **kwargs): raise AssertionError('backend must not be probed')
run_blender.run=fail_backend
try:
 api.render(prepared, workspace=workspace, output=output, images=False, characters=('skeleton',))
except api.GenerationError as error:
 assert error.code in ('input-integrity','source-validation'), error.to_dict()
else:
 raise AssertionError('modified implementation passed package integrity')
assert not output.exists()
print('implementation tamper rejected before operation output')
"""
        result = self._run_disposable_case(package, script, "implementation-tamper", self.prepared_for_failures.prepared_path)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("implementation tamper rejected", result.stdout)

    def test_invalid_character_selections_fail_before_backend_or_output(self):
        for label, characters in (("empty", ()), ("duplicate", ("male", "male")),
                                  ("unknown", ("not-a-character",))):
            with self.subTest(label=label):
                output = f"build/add-shared-body-characters_r1_dev_try-123_invalid-{label}"
                with patch.object(api.run_blender, "run", side_effect=AssertionError("backend probed")) as backend:
                    with self.assertRaises(api.GenerationError) as raised:
                        api.render(self.prepared_for_failures, workspace=self.workspace, output=output,
                                   images=False, characters=characters)
                backend.assert_not_called()
                self.assertIn(raised.exception.code, ("invalid-request", "source-validation"))
                self.assertFalse((self.workspace / output).exists())


if __name__ == "__main__":
    unittest.main()
