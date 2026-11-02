#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run the sequential repository workflows exposed by Make."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipfile

CHANGE = "package-humanmotionlib"
REVISION = "r1"
ROLE = "dev"
ROOT = Path(__file__).resolve().parents[1]
RESOURCE_PATTERNS = (
    ("characters", "*.yaml"),
    ("rig/profiles", "*.yaml"),
    ("rig/mobility", "*.yaml"),
    ("rig/diagnostics", "*.yaml"),
    ("schema", "*.schema.json"),
)
RESOURCE_FILES = (
    "rig/body-groups.yaml", "rig/humanoid-map.yaml", "scenes/skeleton-review.yaml",
    "docs/used-materials.md", "docs/anatomical-skeleton-acceptance.md", "docs/usage.md",
    "docs/character-models.md", "LICENSE-CODE", "LICENSE-DATA", "THIRD-PARTY-NOTICES.md",
)
SOURCE_CONTROL_FILES = ("pyproject.toml", ".python-version", "uv.lock", "hml_build_backend.py", "MANIFEST.in")
COMPONENT = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class WorkflowError(RuntimeError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_files() -> dict[str, Path]:
    """Return the complete package input set, including additions and deletions."""
    files: dict[str, Path] = {}
    package = ROOT / "src" / "humanmotionlib"
    if not package.is_dir():
        raise WorkflowError("Python source directory is missing")
    for path in sorted(package.rglob("*.py")):
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()):
            raise WorkflowError(f"unsafe package source: {path}")
        files[path.relative_to(ROOT).as_posix()] = path
    for directory, pattern in RESOURCE_PATTERNS:
        parent = ROOT / directory
        if not parent.is_dir() or not parent.resolve().is_relative_to(ROOT.resolve()):
            raise WorkflowError(f"required source directory is missing: {directory}")
        for path in sorted(parent.rglob(pattern)):
            if path.is_file():
                if path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()):
                    raise WorkflowError(f"unsafe package resource: {path}")
                files[path.relative_to(ROOT).as_posix()] = path
    for relative in (*RESOURCE_FILES, *SOURCE_CONTROL_FILES):
        path = ROOT / relative
        if not path.is_file() or path.is_symlink():
            raise WorkflowError(f"required package input is missing or unsafe: {relative}")
        files[relative] = path
    return files


def source_snapshot() -> dict[str, str]:
    return {name: sha256(path.read_bytes()) for name, path in source_files().items()}


def configured_tools_root(workspace: Path) -> Path:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    relative = config.get("tool", {}).get("humanmotionlib", {}).get("workflow", {}).get("tools-root")
    candidate = Path(relative) if isinstance(relative, str) else Path("/")
    if (not isinstance(relative, str) or not relative or candidate.is_absolute()
            or ".." in candidate.parts or len(candidate.parts) != 2 or candidate.parts[0] != "build"):
        raise WorkflowError("pyproject.toml tools-root must be a direct child of project build/")
    return workspace / candidate


def identity(snapshot: dict[str, str]) -> dict[str, object]:
    payload = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    return {"source_sha256": sha256(payload), "source_file_count": len(snapshot), "source_files": snapshot}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".tmp-{os.getpid()}")
    temp.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def allocate_run(workspace: Path, kind: str) -> Path:
    build = workspace / "build"
    build.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dt%H%M%S%f")
    token = f"run-{stamp}-{os.getpid()}"
    suffix = "check" if kind == "acceptance" else kind
    parts = (CHANGE, REVISION, ROLE, token, suffix)
    if not all(COMPONENT.fullmatch(part) for part in parts):
        raise WorkflowError("internal generated run identity is invalid")
    path = build / "_".join(parts)
    path.mkdir(exist_ok=False)
    return path


def command_env(workspace: Path, *, python: Path | None = None) -> dict[str, str]:
    env = os.environ.copy()
    tools_root = configured_tools_root(workspace)
    env["UV_CACHE_DIR"] = str(tools_root / "cache")
    env["UV_PYTHON_INSTALL_DIR"] = str(tools_root / "python")
    env["UV_PROJECT_ENVIRONMENT"] = str(tools_root / "environment")
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env.pop("HML_PACKAGE_BUILD_WORKSPACE", None)
    env.pop("HML_PACKAGE_BUILD_RUN_ROOT", None)
    if python:
        env["HML_WORKFLOW_PYTHON"] = str(python)
    return env


def run(command: list[str], *, cwd: Path, env: dict[str, str], log: Path,
        stage: str) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as stream:
        stream.write(f"stage={stage}\ncommand={json.dumps(command)}\ncwd={cwd}\n")
        stream.flush()
        result = subprocess.run(command, cwd=cwd, env=env, stdout=stream,
                                stderr=subprocess.STDOUT, check=False)
        stream.write(f"stage={stage} exit={result.returncode}\n")
    if result.returncode:
        raise WorkflowError(f"stage {stage} failed; see {log}")


def record_failure(log: Path, stage: str, error: str) -> None:
    """Keep post-command verification failures in the same durable run log."""
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as stream:
        stream.write(f"stage={stage} outcome=failure\nerror={error}\n")


def environment_diagnostics(python: Path, workspace: Path, package: dict[str, object],
                           env_override: dict[str, str] | None = None) -> dict[str, object]:
    env = env_override.copy() if env_override is not None else command_env(workspace, python=python)
    env["HML_WORKFLOW_UV"] = uv(workspace)
    uv_bin = env["HML_WORKFLOW_UV"]
    check = subprocess.run([uv_bin, "pip", "check", "--python", str(python)], cwd=Path(tempfile.gettempdir()),
                           env=env, text=True, capture_output=True, check=False)
    if check.returncode:
        raise WorkflowError(f"uv pip check failed before package checks: {check.stdout}{check.stderr}")
    probe = r'''import importlib.metadata as md, importlib.util, json, pathlib, site, sys
names = {"humanmotionlib": "humanmotionlib", "yaml": "PyYAML", "PIL": "Pillow", "jsonschema": "jsonschema", "referencing": "referencing"}
modules = {}
for module, distribution in names.items():
    spec = importlib.util.find_spec(module)
    if spec is None or not spec.origin:
        raise SystemExit("missing import: " + module)
    modules[module] = {"origin": spec.origin, "version": md.version(distribution)}
paths = site.getsitepackages()
pth = {}
for directory in paths:
    for path in pathlib.Path(directory).glob("*.pth"):
        pth[str(path)] = path.read_text(encoding="utf-8")
external = [entry for entry in sys.path if entry and not pathlib.Path(entry).resolve().is_relative_to(pathlib.Path(sys.prefix).resolve()) and "site-packages" in entry]
from humanmotionlib.package_resources import manifest_sha256, verify_runtime_integrity
manifest = verify_runtime_integrity()
print(json.dumps({"executable": sys.executable, "prefix": sys.prefix, "version": sys.version,
 "modules": modules, "site_packages": paths, "pth": pth, "external_site_paths": external,
 "runtime_manifest_sha256": manifest_sha256(), "package_version": manifest["version"]}, sort_keys=True))'''
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    try:
        observed = json.loads(subprocess.check_output([str(python), "-c", probe], cwd=tempfile.gettempdir(),
                                                      env=env, text=True, stderr=subprocess.STDOUT))
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        raise WorkflowError(f"could not record isolated environment identity: {error}") from error
    if Path(observed["executable"]).resolve() != python.resolve() or Path(observed["prefix"]).resolve() != python.parent.parent.resolve():
        raise WorkflowError("diagnostic probe did not use the selected isolated interpreter")
    if observed["package_version"] != package.get("version"):
        raise WorkflowError("installed package version differs from the selected wheel")
    if observed["runtime_manifest_sha256"] != package.get("manifest_sha256"):
        raise WorkflowError("installed package identity differs from the selected wheel")
    prefix = Path(observed["prefix"]).resolve()
    for module, info in observed["modules"].items():
        if not Path(info["origin"]).resolve().is_relative_to(prefix):
            raise WorkflowError(f"{module} imports outside the selected environment: {info['origin']}")
    if observed["external_site_paths"]:
        raise WorkflowError(f"unexpected external site-packages paths: {observed['external_site_paths']}")
    cache = Path(env["UV_CACHE_DIR"]).resolve()
    return {"interpreter": observed, "package": package, "uv_cache": str(cache),
            "uv_pip_check": check.stdout.strip(), "status": "pass"}


def find_one(directory: Path, suffix: str) -> Path:
    found = sorted(path for path in directory.glob(f"*{suffix}") if path.is_file())
    if len(found) != 1:
        raise WorkflowError(f"expected exactly one {suffix} in {directory}; found {len(found)}")
    return found[0]


def manifest_from_wheel(wheel: Path) -> tuple[dict[str, str], dict[str, object]]:
    with zipfile.ZipFile(wheel) as archive:
        members = set(archive.namelist())
        manifests = [name for name in members if name.endswith("/resources/runtime-manifest.json")]
        if len(manifests) != 1:
            raise WorkflowError("wheel does not contain exactly one runtime manifest")
        manifest = json.loads(archive.read(manifests[0]))
        return {name: sha256(archive.read(name)) for name in members if not name.endswith(".dist-info/RECORD")}, manifest


def verify_wheel_sources(wheel: Path, snapshot: dict[str, str]) -> dict[str, object]:
    files, manifest = manifest_from_wheel(wheel)
    if manifest.get("format") != "humanmotionlib-runtime-manifest/v1":
        raise WorkflowError("wheel runtime manifest has an unsupported format")
    resource_hashes = manifest.get("resources")
    implementation = manifest.get("implementation")
    if not isinstance(resource_hashes, dict) or not isinstance(implementation, dict):
        raise WorkflowError("wheel runtime manifest inventory is invalid")
    expected_resources = set(RESOURCE_FILES)
    for directory, pattern in RESOURCE_PATTERNS:
        suffix = pattern[1:] if pattern.startswith("*") else pattern
        expected_resources.update(name for name in snapshot
                                   if name.startswith(directory + "/") and name.endswith(suffix))
    expected_implementation = {
        "humanmotionlib/" + name.removeprefix("src/humanmotionlib/")
        for name in snapshot
        if name.startswith("src/humanmotionlib/") and name.endswith(".py")
    }
    expected_implementation.add("humanmotionlib/_version.py")
    if set(resource_hashes) != expected_resources:
        raise WorkflowError("wheel resource closure differs from current source")
    if set(implementation) != expected_implementation:
        raise WorkflowError("wheel implementation closure differs from current source")
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project_version = project.get("project", {}).get("version")
    if manifest.get("version") != project_version:
        raise WorkflowError("wheel runtime version differs from current project metadata")
    for logical, expected in resource_hashes.items():
        source_name = logical
        if snapshot.get(source_name) != expected:
            raise WorkflowError(f"wheel resource does not match current source: {logical}")
        packaged = f"humanmotionlib/resources/{logical}"
        if files.get(packaged) != expected:
            raise WorkflowError(f"wheel resource bytes differ from its record: {logical}")
    for logical, expected in implementation.items():
        if not isinstance(logical, str) or not logical.startswith("humanmotionlib/"):
            raise WorkflowError("wheel implementation path is invalid")
        packaged_hash = files.get(logical)
        if logical == "humanmotionlib/_version.py":
            # The backend generates this module from project metadata; there is
            # intentionally no corresponding checked-in Python source file.
            generated_hash = sha256(f'__version__ = "{project_version}"\n'.encode())
            source_matches = expected == generated_hash
        else:
            source_name = "src/" + logical
            source_matches = snapshot.get(source_name) == expected
        if not source_matches or packaged_hash != expected:
            raise WorkflowError(f"wheel implementation does not match current source: {logical}")
    return {"version": manifest.get("version"),
            "manifest_sha256": sha256(
                (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()),
            "resources": resource_hashes, "implementation": implementation,
            "backend_contract_sha256": manifest.get("backend_contract"),
            "wheel_sha256": sha256(wheel.read_bytes()), "wheel": str(wheel)}


def compare_wheels(first: Path, second: Path) -> dict[str, object]:
    files_a, manifest_a = manifest_from_wheel(first)
    files_b, manifest_b = manifest_from_wheel(second)
    runtime_a = {name: digest for name, digest in files_a.items()
                 if name.startswith("humanmotionlib/") and ".dist-info/" not in name}
    runtime_b = {name: digest for name, digest in files_b.items()
                 if name.startswith("humanmotionlib/") and ".dist-info/" not in name}
    if runtime_a != runtime_b or manifest_a != manifest_b:
        raise WorkflowError("wheel rebuilt from the source archive differs from the direct wheel runtime")
    return {"status": "pass", "runtime_file_count": len(runtime_a),
            "runtime_sha256": sha256(json.dumps(runtime_a, sort_keys=True, separators=(",", ":")).encode())}


def uv(workspace: Path) -> str:
    binary = shutil.which(os.environ.get("HML_WORKFLOW_UV", "uv"))
    if not binary:
        raise WorkflowError("required tool uv is not available")
    return binary


def current_python(workspace: Path) -> Path:
    value = os.environ.get("HML_WORKFLOW_PYTHON")
    path = Path(value) if value else configured_tools_root(workspace) / "environment/bin/python3.14"
    if not path.is_file() or not os.access(path, os.X_OK):
        raise WorkflowError(f"prepared CPython 3.14 is unavailable: {path}")
    return path


def build_current_wheel(workspace: Path) -> tuple[Path, Path, dict[str, object]]:
    python = current_python(workspace)
    uv_bin = uv(workspace)
    run_root = allocate_run(workspace, "stage")
    log = run_root / "logs" / "build.log"
    wheel_dir = run_root / "wheelhouse"
    wheel_dir.mkdir()
    before = source_snapshot()
    env = command_env(workspace, python=python)
    env["HML_WORKFLOW_UV"] = uv_bin
    try:
        run([uv_bin, "build", "--wheel", "--no-build-isolation", "--python", str(python),
             "--out-dir", str(wheel_dir)], cwd=ROOT, env=env, log=log, stage="build-wheel")
        wheel = find_one(wheel_dir, ".whl")
        after = source_snapshot()
        if before != after:
            error = "package inputs changed while the wheel was being built"
            record_failure(log, "source-closure-verification", error)
            raise WorkflowError(error)
        try:
            package_identity = verify_wheel_sources(wheel, after)
        except WorkflowError as error:
            record_failure(log, "wheel-source-verification", str(error))
            raise
        run([uv_bin, "pip", "install", "--python", str(python), "--no-deps", "--reinstall", str(wheel)],
            cwd=ROOT, env=env, log=log, stage="install-exact-wheel")
        run([uv_bin, "pip", "check", "--python", str(python)], cwd=ROOT,
            env=env, log=log, stage="dependency-check")
        diagnostics = environment_diagnostics(python, workspace, package_identity, env)
        write_json(configured_tools_root(workspace) / "environment-report.json", diagnostics)
        check = "from humanmotionlib.package_resources import verify_runtime_integrity; verify_runtime_integrity()"
        run([str(python), "-c", check], cwd=Path(tempfile.gettempdir()), env=env,
            log=log, stage="installed-integrity")
        report = {"status": "success", "run": str(run_root),
                  "source": identity(after), "package": package_identity,
                  "environment": diagnostics}
        write_json(run_root / "package-build.json", report)
        return run_root, wheel, package_identity
    except BaseException:
        raise


def validate_sources(python: Path, workspace: Path, log: Path) -> None:
    env = command_env(workspace, python=python)
    cli = python.parent / "hml"
    run([str(cli), "check-environment", "--check-environment"], cwd=Path(tempfile.gettempdir()), env=env,
        log=log, stage="development-environment")
    run([str(cli), "validate", "--profile", "adult-reference-v1"], cwd=Path(tempfile.gettempdir()), env=env,
        log=log, stage="validate-library-sources")


def cmd_dev(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).resolve(strict=True)
    run_root, _wheel, package_identity = build_current_wheel(workspace)
    log = run_root / "logs" / "build.log"
    validate_sources(current_python(workspace), workspace, log)
    report = {"status": "ready", "run": str(run_root), "package": package_identity,
              "next_actions": ["make matrix-list", "make matrix-build CHARACTER=<id> HEIGHT=<m>",
                               "make matrix-check CHARACTER=<id> HEIGHT=<m> after a selected build",
                               "make package", "make clean"]}
    write_json(run_root / "development-readiness.json", report)
    print(json.dumps(report, indent=2))
    return 0


def acceptance_install(workspace: Path, wheel: Path, package_identity: dict[str, object],
                       package_root: Path) -> tuple[Path, dict[str, object]]:
    uv_bin = uv(workspace)
    run_root = allocate_run(workspace, "check")
    env_root = run_root / "environment"
    env_root.parent.mkdir(parents=True, exist_ok=True)
    cache = run_root / "cache"
    python_dir = run_root / "python"
    cache.mkdir()
    python_dir.mkdir()
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env.update({"UV_CACHE_DIR": str(cache), "UV_PYTHON_INSTALL_DIR": str(python_dir),
                "UV_PROJECT_ENVIRONMENT": str(env_root), "HML_WORKFLOW_PYTHON": str(current_python(workspace))})
    log = run_root / "logs" / "acceptance.log"
    try:
        run([uv_bin, "venv", "--python", str(current_python(workspace)), str(env_root)],
            cwd=ROOT, env=env, log=log, stage="create-independent-environment")
        # Export the locked build dependency set, then install it with uv pip
        # into this new environment. The exact candidate wheel is installed
        # separately below, so the checkout project is never installed here.
        requirements = run_root / "locked-build-requirements.txt"
        run([uv_bin, "export", "--locked", "--no-emit-project", "--group", "build",
             "--format", "requirements.txt", "--output-file", str(requirements)], cwd=ROOT,
            env=env, log=log, stage="export-locked-dependencies")
        run([uv_bin, "pip", "install", "--python", str(env_root / "bin/python3.14"),
             "--requirement", str(requirements)], cwd=ROOT, env=env,
            log=log, stage="install-locked-dependencies")
        installed_python = env_root / "bin/python3.14"
        outside = Path(tempfile.gettempdir())
        run([uv_bin, "pip", "install", "--python", str(installed_python), "--no-deps", str(wheel)],
            cwd=outside, env=env, log=log, stage="install-exact-wheel")
        run([uv_bin, "pip", "check", "--python", str(installed_python)], cwd=ROOT,
            env=env, log=log, stage="dependency-check")
        diagnostics = environment_diagnostics(installed_python, workspace, package_identity, env)
        write_json(run_root / "pre-test-environment.json", diagnostics)
        env["PATH"] = str(installed_python.parent) + os.pathsep + env.get("PATH", "")
        purelib = subprocess.check_output([str(installed_python), "-c",
            "import sysconfig; print(sysconfig.get_paths()['purelib'])"], cwd=outside, env=env, text=True).strip()
        origin = str(Path(purelib) / "humanmotionlib" / "__init__.py")
        prefix = subprocess.check_output([str(installed_python), "-c", "import sys; print(sys.prefix)"],
                                         cwd=outside, env=env, text=True).strip()
        report = {"status": "success", "run": str(run_root),
                  "python": str(installed_python), "prefix": prefix, "purelib": purelib,
                  "package_origin": origin, "package": package_identity,
                  "environment_diagnostics": str(run_root / "pre-test-environment.json")}
        write_json(run_root / "installation.json", report)
        cli = env_root / "bin/hml"
        run([str(cli), "--version"], cwd=outside, env=env, log=log, stage="console-version")
        run([str(installed_python), "-m", "humanmotionlib", "--version"], cwd=outside,
            env=env, log=log, stage="module-version")
        # The package route validates its exact installed-wheel identity above.
        # Candidate-manifest runtime assertions belong to selected matrix runs;
        # package acceptance has no matrix-candidate manifest to supply.
        run([str(cli), "check-environment", "--check-environment"], cwd=outside, env=env,
            log=log, stage="host-check")
        run([str(cli), "validate", "--profile", "adult-reference-v1"], cwd=outside,
            env=env, log=log, stage="validate-installed-sources")
        preparation_root = allocate_run(workspace, "stage")
        preparation = preparation_root / "input.json"
        run([str(cli), "--workspace", str(workspace), "prepare-skeleton", "--profile",
             "adult-reference-v1", "--fixtures", "neutral", "--output", str(preparation)], cwd=outside,
            env=env, log=log, stage="bounded-neutral-preparation")
        report["prepared_input"] = str(preparation)
        report["preparation_run"] = str(preparation_root)
        write_json(run_root / "installation.json", report)
        return run_root, report
    except BaseException:
        raise


def cmd_package(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).resolve(strict=True)
    python = current_python(workspace)
    uv_bin = uv(workspace)
    package_root = allocate_run(workspace, "package")
    direct = package_root / "direct"
    rebuilt = package_root / "rebuilt"
    direct.mkdir()
    rebuilt.mkdir()
    log = package_root / "logs" / "package.log"
    before = source_snapshot()
    env = command_env(workspace, python=python)
    try:
        run([uv_bin, "build", "--wheel", "--sdist", "--no-build-isolation", "--python", str(python),
             "--out-dir", str(direct)], cwd=ROOT, env=env, log=log, stage="direct-wheel-sdist")
        wheel = find_one(direct, ".whl")
        sdist = find_one(direct, ".tar.gz")
        identity_record = verify_wheel_sources(wheel, before)
        after = source_snapshot()
        if before != after:
            error = "package inputs changed during direct package build"
            record_failure(log, "source-closure-verification", error)
            raise WorkflowError(error)
        run([uv_bin, "build", str(sdist), "--wheel", "--no-build-isolation", "--python", str(python),
             "--out-dir", str(rebuilt)], cwd=ROOT, env=env, log=log, stage="wheel-from-source-archive")
        rebuilt_wheel = find_one(rebuilt, ".whl")
        closure = compare_wheels(wheel, rebuilt_wheel)
        acceptance_root, installed = acceptance_install(workspace, wheel, identity_record, package_root)
        report = {"status": "verified", "run": str(package_root), "wheel": str(wheel),
                  "sdist": str(sdist), "rebuilt_wheel": str(rebuilt_wheel),
                  "package": identity_record, "closure_comparison": closure,
                  "acceptance_run": str(acceptance_root), "installed_checks": installed,
                  "blender": "not-run", "publication": "not-run"}
        write_json(package_root / "package-result.json", report)
        print(json.dumps(report, indent=2))
        return 0
    except BaseException:
        raise


def cmd_matrix_build(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).resolve(strict=True)
    if args.character not in {"skeleton", "male", "female"}:
        raise WorkflowError("CHARACTER must be skeleton, male, or female")
    if args.height not in {"1.50", "1.70", "1.90"}:
        raise WorkflowError("HEIGHT must be 1.50, 1.70, or 1.90")
    package_root, _wheel, _identity = build_current_wheel(workspace)
    env = command_env(workspace, python=current_python(workspace))
    matrix = ROOT / "tools" / "matrix.py"
    run([str(current_python(workspace)), str(matrix), "build", "--workspace", str(workspace),
         "--character", args.character, "--height", args.height], cwd=ROOT, env=env,
        log=package_root / "logs" / "matrix-orchestration.log", stage="selected-matrix-build")
    return 0


def cmd_matrix_check(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).resolve(strict=True)
    if args.character not in {"skeleton", "male", "female"}:
        raise WorkflowError("CHARACTER must be skeleton, male, or female")
    if args.height not in {"1.50", "1.70", "1.90"}:
        raise WorkflowError("HEIGHT must be 1.50, 1.70, or 1.90")
    env_path = current_python(workspace)
    env = command_env(workspace, python=env_path)
    matrix = ROOT / "tools" / "matrix.py"
    return subprocess.run([str(env_path), str(matrix), "check", "--workspace", str(workspace),
                           "--character", args.character, "--height", args.height],
                          cwd=ROOT, env=env, check=False).returncode


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    for name in ("dev", "package", "matrix-build", "matrix-check"):
        command = sub.add_parser(name)
        command.add_argument("--workspace", required=True)
        if name.startswith("matrix-"):
            command.add_argument("--character", required=True)
            command.add_argument("--height", required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return {"dev": cmd_dev, "package": cmd_package,
                "matrix-build": cmd_matrix_build, "matrix-check": cmd_matrix_check}[args.command](args)
    except (WorkflowError, OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"repository workflow: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
