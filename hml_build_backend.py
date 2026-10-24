"""PEP 517 adapter that stages the installed HML package without editing sources.

Canonical authoring files remain in the repository.  A build uses a temporary
source tree containing the Python package, an explicit resource closure and
stable generated metadata, then delegates to setuptools.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import tomllib
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent
_RESOURCE_DIR = Path("resources")
_RESOURCE_PATTERNS = (
    ("rig/profiles", "*.yaml"),
    ("rig/mobility", "*.yaml"),
    ("rig/diagnostics", "*.yaml"),
    ("schema", "*.schema.json"),
)
_RESOURCE_FILES = (
    "rig/body-groups.yaml",
    "rig/humanoid-map.yaml",
    "scenes/skeleton-review.yaml",
    "docs/used-materials.md",
    "docs/anatomical-skeleton-acceptance.md",
    "docs/usage.md",
    "LICENSE-CODE",
    "LICENSE-DATA",
    "THIRD-PARTY-NOTICES.md",
)
_MANIFEST_FORMAT = "humanmotionlib-runtime-manifest/v1"
_CONTRACT_FORMAT = "humanmotionlib-backend-contract/v1"
_RUN_COMPONENT = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _copy_python_package(source: Path, target: Path) -> None:
    if not source.is_dir():
        raise RuntimeError(f"Python package source is missing: {source}")
    resolved_source = source.resolve()
    if not resolved_source.is_relative_to(_ROOT.resolve()) or any(path.is_symlink() for path in source.rglob("*")):
        raise RuntimeError("Python package sources must not escape the project or contain symlinks")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        source,
        target,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
    )


def _canonical_resources(root: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for relative_dir, pattern in _RESOURCE_PATTERNS:
        directory = root / relative_dir
        if not directory.is_dir() or not directory.resolve().is_relative_to(root.resolve()):
            raise RuntimeError(f"Required resource directory is missing: {relative_dir}")
        for path in sorted(directory.glob(pattern)):
            if path.is_file():
                if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
                    raise RuntimeError(f"Packaged resource must not use a symlink: {path.relative_to(root)}")
                files[path.relative_to(root).as_posix()] = path.read_bytes()
    for relative in _RESOURCE_FILES:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise RuntimeError(f"Required packaged resource is missing or unsafe: {relative}")
        files[relative] = path.read_bytes()
    return files


def _contract_from_project(root: Path) -> bytes:
    with (root / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)
    config = project.get("tool", {}).get("humanmotionlib", {}).get("backend")
    expected = {"blender-version", "blender-build", "reference-platform", "mpfb", "rigify"}
    if not isinstance(config, dict) or set(config) != expected:
        raise RuntimeError("[tool.humanmotionlib.backend] must declare the exact backend contract fields")
    payload = {"format": _CONTRACT_FORMAT, **config}
    return (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _stage_resources(root: Path, package_dir: Path, version: str) -> None:
    resources_dir = package_dir / _RESOURCE_DIR
    existing_manifest = resources_dir / "runtime-manifest.json"
    if existing_manifest.is_file():
        # An extracted sdist already carries the canonical, generated resource closure.
        # Verify it before using it as the source of the rebuilt wheel.
        old = json.loads(existing_manifest.read_text(encoding="utf-8"))
        if old.get("format") != _MANIFEST_FORMAT or old.get("version") != version:
            raise RuntimeError("Existing sdist runtime manifest has an unsupported format or version")
        _verify_resource_manifest(resources_dir, old)
        contract_path = resources_dir / "backend-contract.json"
        if not contract_path.is_file() or old.get("backend_contract") != _sha256(contract_path.read_bytes()):
            raise RuntimeError("Existing sdist backend contract does not match its runtime manifest")
        # Regenerate implementation hashes from the extracted source so changed code
        # cannot inherit stale metadata from an sdist.
        resource_bytes = {
            path.relative_to(resources_dir).as_posix(): path.read_bytes()
            for path in sorted(resources_dir.rglob("*"))
            if path.is_file() and path.name not in {"runtime-manifest.json", "backend-contract.json"}
        }
        contract = contract_path.read_bytes()
    else:
        resource_bytes = _canonical_resources(root)
        contract = _contract_from_project(root)
        resources_dir.mkdir(parents=True, exist_ok=True)
        for logical_name, content in resource_bytes.items():
            destination = resources_dir / logical_name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        (resources_dir / "backend-contract.json").write_bytes(contract)

    (package_dir / "_version.py").write_text(f'__version__ = "{version}"\n', encoding="utf-8", newline="\n")
    implementation: dict[str, str] = {}
    for path in sorted(package_dir.rglob("*.py")):
        if path.is_file():
            implementation[f"humanmotionlib/{path.relative_to(package_dir).as_posix()}"] = _sha256(path.read_bytes())
    if not implementation:
        raise RuntimeError("No humanmotionlib Python implementation files were staged")
    manifest = {
        "format": _MANIFEST_FORMAT,
        "version": version,
        "resources": {name: _sha256(content) for name, content in sorted(resource_bytes.items())},
        "backend_contract": _sha256(contract),
        "implementation": implementation,
    }
    (resources_dir / "runtime-manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _verify_resource_manifest(resources_dir: Path, manifest: dict[str, Any]) -> None:
    listed = manifest.get("resources")
    if not isinstance(listed, dict):
        raise RuntimeError("Runtime manifest resources must be a mapping")
    actual = {
        path.relative_to(resources_dir).as_posix(): _sha256(path.read_bytes())
        for path in sorted(resources_dir.rglob("*"))
        if path.is_file() and path.name not in {"runtime-manifest.json", "backend-contract.json"}
    }
    if actual != listed:
        raise RuntimeError("Staged resource files do not exactly match the runtime manifest")


def _stage_project(source_root: Path, stage_root: Path) -> Path:
    """Create an isolated setuptools source tree and return its root."""
    source_root = source_root.resolve()
    with (source_root / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)
    version = project.get("project", {}).get("version")
    if not isinstance(version, str) or not version:
        raise RuntimeError("Project version is missing from pyproject.toml")
    staged = stage_root / "project"
    staged.mkdir(parents=True)
    for name in (
        "pyproject.toml",
        ".python-version",
        "uv.lock",
        "hml_build_backend.py",
        "MANIFEST.in",
        "LICENSE-CODE",
        "LICENSE-DATA",
        "THIRD-PARTY-NOTICES.md",
    ):
        source = source_root / name
        if source.is_file():
            shutil.copy2(source, staged / name)
    _copy_python_package(source_root / "src" / "humanmotionlib", staged / "src" / "humanmotionlib")
    _stage_resources(source_root, staged / "src" / "humanmotionlib", version)
    return staged


def _valid_run_root(path: Path, build_root: Path) -> bool:
    if path.parent != build_root or not path.name:
        return False
    components = path.name.split("_")
    return len(components) == 5 and all(_RUN_COMPONENT.fullmatch(part) for part in components)


def _select_stage_run(output_dir: Path | None) -> tuple[Path, bool, bool]:
    """Return (run root, adapter-owned run, adapter-created build directory)."""
    project_root = _ROOT.resolve()
    build_root = project_root / "build"
    build_root_existed = build_root.exists()
    resolved_build = build_root.resolve()
    if resolved_build.parent != project_root:
        raise RuntimeError("The project build/ directory must be a real directory inside the source tree")
    if output_dir is not None:
        output = output_dir.resolve()
        try:
            relative = output.relative_to(resolved_build)
        except ValueError:
            relative = None
        if relative is not None and relative.parts:
            candidate = resolved_build / relative.parts[0]
            if _valid_run_root(candidate, resolved_build):
                return candidate, False, False

    build_root.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, 10000):
        candidate = build_root / f"package-humanmotionlib_r1_dev_try-{attempt}_stage"
        try:
            candidate.mkdir()
        except FileExistsError:
            continue
        return candidate, True, not build_root_existed
    raise RuntimeError("Could not allocate a unique package staging run under build/")


def _delegate(hook: str, *args: Any, **kwargs: Any) -> Any:
    from setuptools import build_meta

    output_dir = None
    if args and isinstance(args[0], str):
        output_dir = Path(args[0]).resolve()
    if output_dir is None and hook.startswith("get_requires_for_build_"):
        # setuptools' build requirements are already declared in [build-system].
        return []
    run_root, owned_run, owned_build_root = _select_stage_run(output_dir)
    stage_directory: str | None = None
    try:
        stage_directory = tempfile.mkdtemp(prefix="adapter-stage-", dir=run_root)
        staged = _stage_project(_ROOT, Path(stage_directory))
        previous = Path.cwd()
        try:
            os.chdir(staged)
            if output_dir is not None:
                output_dir.mkdir(parents=True, exist_ok=True)
                args = (str(output_dir), *args[1:])
            return getattr(build_meta, hook)(*args, **kwargs)
        finally:
            os.chdir(previous)
    finally:
        if stage_directory is not None:
            shutil.rmtree(stage_directory, ignore_errors=False)
        if owned_run:
            run_root.rmdir()
        if owned_build_root:
            try:
                (run_root.parent).rmdir()
            except OSError:
                pass


def build_wheel(wheel_directory: str, config_settings: dict[str, Any] | None = None, metadata_directory: str | None = None) -> str:
    return _delegate("build_wheel", wheel_directory, config_settings, metadata_directory)


def build_sdist(sdist_directory: str, config_settings: dict[str, Any] | None = None) -> str:
    return _delegate("build_sdist", sdist_directory, config_settings)


def prepare_metadata_for_build_wheel(metadata_directory: str, config_settings: dict[str, Any] | None = None) -> str:
    return _delegate("prepare_metadata_for_build_wheel", metadata_directory, config_settings)


def get_requires_for_build_wheel(config_settings: dict[str, Any] | None = None) -> list[str]:
    return _delegate("get_requires_for_build_wheel", config_settings)


def get_requires_for_build_sdist(config_settings: dict[str, Any] | None = None) -> list[str]:
    return _delegate("get_requires_for_build_sdist", config_settings)
