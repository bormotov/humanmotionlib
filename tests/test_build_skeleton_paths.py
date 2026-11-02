# SPDX-License-Identifier: Apache-2.0
"""Output-root preflight keeps the sealed request as a file, not scratch."""

from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

from humanmotionlib.character_paths import validate_managed_output_entries


class BuildSkeletonPathTests(unittest.TestCase):
    def test_blender_entry_imports_with_yaml_and_schema_dependencies_forbidden(self):
        import humanmotionlib
        package_parent = str(Path(humanmotionlib.__file__).resolve().parent.parent)
        script = '''
import builtins, importlib, pathlib, sys, types
package_parent = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(package_parent))
original_import = builtins.__import__
def guarded_import(name, *args, **kwargs):
    if name.split(".", 1)[0] in {"yaml", "jsonschema"}:
        raise AssertionError("Blender entry imported forbidden dependency: " + name)
    return original_import(name, *args, **kwargs)
builtins.__import__ = guarded_import
bpy = types.ModuleType("bpy")
mathutils = types.ModuleType("mathutils")
mathutils.Matrix = object
mathutils.Vector = object
sys.modules["bpy"] = bpy
sys.modules["mathutils"] = mathutils
module = importlib.import_module("humanmotionlib.build_skeleton")
assert callable(module._validate_character_request_closure)
assert "yaml" not in sys.modules and "jsonschema" not in sys.modules
'''
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        with tempfile.TemporaryDirectory() as temporary:
            completed = subprocess.run(
                [sys.executable, "-c", script, package_parent],
                cwd=temporary, env=environment, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_character_request_file_is_allowed_alongside_process_scratch(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            (output / "character-render-request.json").write_text("{}", encoding="utf-8")
            (output / "processes").mkdir()
            validate_managed_output_entries(
                output, {"processes", "character-render-request.json"})

    def test_managed_scratch_must_be_a_contained_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            (output / "processes").write_text("not a directory", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "scratch escaped"):
                validate_managed_output_entries(output, {"processes"})


if __name__ == "__main__":
    unittest.main()
