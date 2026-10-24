# SPDX-License-Identifier: Apache-2.0
"""The Blender entry point imports only HML, never its host site-packages parent."""

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class BlenderBootstrapTests(unittest.TestCase):
    def test_bootstrap_loads_package_without_exposing_sibling_host_modules(self):
        installed = Path(importlib.util.find_spec("humanmotionlib").origin).parent
        source = Path(__file__).resolve().parents[1] / "src" / "humanmotionlib" / "build_skeleton.py"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / "humanmotionlib"
            shutil.copytree(installed, package)
            patched_script = package / "build_skeleton.py"
            os.chmod(patched_script, 0o600)
            shutil.copy2(source, patched_script)
            (root / "_hml_neighbor_sentinel.py").write_text("marker = True\n", encoding="utf-8")
            probe = root / "bootstrap_probe.py"
            probe.write_text(
                """import importlib.util, pathlib, runpy, sys, types
from pathlib import Path
root = Path(sys.argv[1]).resolve()
script = root / 'humanmotionlib' / 'build_skeleton.py'
assert str(root) not in {str(Path(item or '.').resolve()) for item in sys.path}
sys.modules['bpy'] = types.ModuleType('bpy')
mathutils = types.ModuleType('mathutils')
mathutils.Matrix = object
mathutils.Vector = object
sys.modules['mathutils'] = mathutils
runpy.run_path(str(script), run_name='bootstrap_probe')
import humanmotionlib
assert Path(humanmotionlib.__file__).resolve() == root / 'humanmotionlib' / '__init__.py'
assert str(root) not in {str(Path(item or '.').resolve()) for item in sys.path}
assert importlib.util.find_spec('_hml_neighbor_sentinel') is None
assert 'bpy' in sys.modules and sys.dont_write_bytecode
""",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            result = subprocess.run([sys.executable, "-c", probe.read_text(encoding="utf-8"), str(root)], cwd=root.parent,
                                    env=env, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
