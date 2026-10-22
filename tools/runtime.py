# SPDX-License-Identifier: Apache-2.0
"""Backend contract shared by preparation and headless build checks."""

from pathlib import Path
import platform
import re
import shutil
import subprocess
import tomllib


def project_root():
    return Path(__file__).resolve().parent.parent


def backend_contract():
    with (project_root() / "pyproject.toml").open("rb") as stream:
        return tomllib.load(stream)["tool"]["humanmotionlib"]["backend"]


def check_blender_version(version, build_hash):
    expected = backend_contract()
    if version != expected["blender-version"] or build_hash != expected["blender-build"]:
        raise ValueError(
            f"Blender version mismatch: expected {expected['blender-version']} "
            f"({expected['blender-build']}), received {version} ({build_hash})"
        )
    return expected


def blender_executable():
    """Resolve symlinks so macOS app resource discovery sees the real executable."""
    executable = shutil.which("blender")
    if executable is None: raise ValueError("Blender is not on PATH")
    return str(Path(executable).resolve())


def inspect_blender():
    """Resolve Blender through PATH; never encode a workstation application path."""
    result = subprocess.run([blender_executable(), "--version"], check=True, capture_output=True, text=True)
    version = re.search(r"^Blender (.+)$", result.stdout, re.M)
    build_hash = re.search(r"build hash:\s*(\S+)", result.stdout)
    if version is None or build_hash is None:
        raise ValueError("Cannot identify Blender version/build from --version output")
    check_blender_version(version.group(1).strip(), build_hash.group(1))
    return {"version": version.group(1).strip(), "build_hash": build_hash.group(1),
            "platform": platform.system() + "-" + platform.machine()}
