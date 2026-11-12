#!/usr/bin/env python3
"""Run host acceptance against a non-editable installed HML wheel.

This file is copied into an external CI-owned run before execution. It only
imports the installed distribution, uses the standard library, and creates all
caller data under the explicitly selected workspace.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.resources
import json
import os
import hashlib
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import re
import traceback
import urllib.parse


PROFILE = "adult-reference-v1"
RUN_COMPONENT = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RUN_KINDS = (
    "fixture-one", "fixture-two", "prepare-direct", "api-prepare",
    "invalid-one", "invalid-two", "invalid-three", "invalid-four", "api-failure",
    "host-verify", "tampered-input", "tampered-report", "host-reuse",
    "host-symlink", "html-only",
)
ACTIVE_RUN_ROOT: Path | None = None
ACTIVE_GENERATED_RUNS: list[dict[str, str]] = []
ACTIVE_CANDIDATE: dict | None = None


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): digest(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def outside_build_inventory(workspace: Path, build: Path) -> dict[str, dict]:
    """Hash the workspace outside build/ without following links or traversing build/."""
    root = workspace.resolve(strict=True)
    build = build.resolve(strict=True)
    records: dict[str, dict] = {}

    def visit(directory: Path) -> None:
        with os.scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path)
                if path == build:
                    continue
                relative = path.relative_to(root).as_posix()
                mode = stat.S_IMODE(path.lstat().st_mode)
                if entry.is_symlink():
                    records[relative] = {"type": "symlink", "target": os.readlink(path),
                                         "mode": mode}
                elif entry.is_dir(follow_symlinks=False):
                    records[relative] = {"type": "directory", "mode": mode}
                    visit(path)
                elif entry.is_file(follow_symlinks=False):
                    records[relative] = {"type": "file", "sha256": digest(path),
                                         "mode": mode}

    visit(root)
    return dict(sorted(records.items()))


def candidate_reference(manifest_path: Path | None, python: Path, run_identity: str | Path) -> dict | None:
    if manifest_path is None:
        return None
    manifest_path = manifest_path.expanduser().resolve(strict=True)
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema") != "matrix-candidate/v1" or manifest.get("status") != "succeeded":
        raise ValueError(f"candidate manifest is unsupported or unsuccessful: {manifest_path}")
    identity_parts = run_identity.name.split("_") if isinstance(run_identity, Path) else run_identity.split("_")
    role = identity_parts[2]
    runtime = manifest.get("runtime_environments", {}).get(role)
    if not isinstance(runtime, dict) or Path(runtime.get("python", "")).absolute() != python.absolute():
        raise ValueError("installed acceptance interpreter does not match the selected candidate role environment")
    artifacts = manifest.get("artifacts", [])
    adopted = "selected_wheel" in manifest or "artifact_origin" in manifest
    if adopted:
        selected = manifest.get("selected_wheel")
        origin = manifest.get("artifact_origin")
        if not isinstance(selected, dict) or not isinstance(origin, dict):
            raise ValueError("adopted candidate has incomplete selected-wheel provenance")
        if role != "reviewer" or manifest.get("identity", {}).get("role") != "reviewer":
            raise ValueError("adopted candidate must bind to the reviewer role")
        candidate_root = manifest_path.parent
        runtime_root = candidate_root / f"runtime-{role}-env"
        if not python.resolve().is_relative_to(runtime_root.resolve(strict=True)):
            raise ValueError("adopted candidate interpreter is outside its fresh role environment")
        raw_wheel = Path(str(selected.get("path", "")))
        selected_root = candidate_root / "artifacts" / "selected"
        if (not raw_wheel.is_absolute() or raw_wheel.is_symlink()
                or selected_root.is_symlink() or (candidate_root / "artifacts").is_symlink()
                or raw_wheel.resolve(strict=True) != raw_wheel.absolute()
                or raw_wheel.name != selected.get("name")
                or raw_wheel.resolve(strict=True) != (selected_root / raw_wheel.name).resolve(strict=True)
                or not raw_wheel.resolve(strict=True).is_relative_to(selected_root.resolve(strict=True))):
            raise ValueError("selected donor wheel is linked or outside candidate artifacts/selected")
        wheel = raw_wheel.resolve(strict=True)
        actual_wheel_sha256 = digest(wheel)
        if (wheel.stat().st_size != selected.get("bytes")
                or actual_wheel_sha256 != selected.get("sha256")
                or origin.get("direct_wheel_sha256") != actual_wheel_sha256
                or origin.get("wheel_size") != wheel.stat().st_size
                or origin.get("logical_closure_sha256") != manifest.get("wheel_closure_sha256")):
            raise ValueError("selected donor wheel or source pin differs from its manifest")
        if (Path(str(runtime.get("wheel", ""))).resolve() != wheel
                or runtime.get("wheel_sha256") != actual_wheel_sha256):
            raise ValueError("installed candidate runtime does not select the frozen donor wheel")
        required_origin = ("source_plan_path", "source_plan_sha256", "source_plan_digest",
                           "source_candidate_manifest_path", "source_candidate_manifest_sha256",
                           "source_manifest_sha256", "source_candidate_identity", "source_role",
                           "source_snapshot_sha256", "logical_closure_sha256")
        if any(not isinstance(origin.get(key), str) or not origin[key] for key in required_origin):
            raise ValueError("adopted candidate origin record is incomplete")
        if (origin.get("source_role") != "dev"
                or origin.get("source_manifest_sha256") != origin.get("source_candidate_manifest_sha256")
                or "source_ownership" in origin):
            raise ValueError("adopted candidate source role or origin record is invalid")
        if (not isinstance(origin.get("source_sdist_identity"), dict)
                or not isinstance(origin["source_sdist_identity"].get("path"), str)
                or not Path(origin["source_sdist_identity"]["path"]).is_absolute()
                or not isinstance(origin["source_sdist_identity"].get("sha256"), str)
                or len(origin["source_sdist_identity"]["sha256"]) != 64
                or not isinstance(origin["source_sdist_identity"].get("bytes"), int)
                or not isinstance(origin["source_sdist_identity"].get("source_hashes_sha256"), str)
                or len(origin["source_sdist_identity"]["source_hashes_sha256"]) != 64):
            raise ValueError("adopted candidate source-distribution identity is invalid")
        dependencies = origin.get("origin_dependencies")
        if not isinstance(dependencies, list) or not dependencies:
            raise ValueError("adopted candidate origin dependencies are incomplete")
        for item in dependencies:
            if (not isinstance(item, dict) or not isinstance(item.get("path"), str)
                    or not Path(item["path"]).is_absolute()
                    or not isinstance(item.get("sha256"), str)
                    or len(item["sha256"]) != 64):
                raise ValueError("adopted candidate origin dependency record is invalid")
            if any(term in str(item.get("kind", "")).lower()
                   for term in ("runtime", "environment", "acceptance")):
                raise ValueError("adopted candidate must not depend on donor environment or acceptance results")
            dependency_path = Path(item["path"])
            if (dependency_path.is_symlink() or not dependency_path.is_file()
                    or dependency_path.resolve(strict=True) != dependency_path.absolute()
                    or digest(dependency_path) != item["sha256"]):
                raise ValueError(f"adopted candidate source dependency is missing, linked, or changed: {dependency_path}")
        dependencies_by_kind = {}
        for item in dependencies:
            dependencies_by_kind.setdefault(item["kind"], []).append(item)
        for kind, expected_path, expected_hash in (
                ("source-plan", origin["source_plan_path"], origin["source_plan_sha256"]),
                ("source-candidate-manifest", origin["source_candidate_manifest_path"],
                 origin["source_candidate_manifest_sha256"]),
                ("direct-wheel", origin["direct_wheel_path"], origin["direct_wheel_sha256"]),
                ("source-distribution", origin["source_sdist_identity"]["path"],
                 origin["source_sdist_identity"]["sha256"])):
            matching = dependencies_by_kind.get(kind, [])
            if (len(matching) != 1 or matching[0]["path"] != expected_path
                    or matching[0]["sha256"] != expected_hash):
                raise ValueError(f"adopted candidate {kind} is not bound by its origin dependencies")
        source_plan = json.loads(Path(origin["source_plan_path"]).read_text(encoding="utf-8"))
        source_candidate = json.loads(Path(origin["source_candidate_manifest_path"]).read_text(encoding="utf-8"))
        source_plan_content = dict(source_plan)
        source_plan_content.pop("plan_digest", None)
        source_plan_content.pop("created_utc", None)
        source_plan_digest = hashlib.sha256(json.dumps(
            source_plan_content, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
        if (source_plan_digest != origin["source_plan_digest"]
                or source_plan.get("identity", {}).get("role") != "dev"
                or source_candidate.get("schema") != "matrix-candidate/v1"
                or source_candidate.get("status") != "succeeded"
                or source_candidate.get("plan_digest") != origin["source_plan_digest"]
                or source_candidate.get("identity") != source_plan.get("identity")
                or source_candidate.get("candidate_identity") != origin["source_candidate_identity"]
                or source_candidate.get("source_snapshot_sha256") != origin["source_snapshot_sha256"]
                or "artifact_origin" in source_candidate or "selected_wheel" in source_candidate):
            raise ValueError("adopted candidate donor plan or first-generation candidate is inconsistent")
        donor_identity_payload = {
            "plan_digest": source_candidate.get("plan_digest"),
            "source_snapshot_sha256": source_candidate.get("source_snapshot_sha256"),
            "artifacts": source_candidate.get("artifacts"),
            "wheel_closure_sha256": source_candidate.get("wheel_closure_sha256"),
        }
        donor_identity = hashlib.sha256(json.dumps(
            donor_identity_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
        donor_direct = [item for item in source_candidate.get("artifacts", [])
                        if item.get("path") == origin["direct_wheel_path"]]
        if (donor_identity != origin["source_candidate_identity"] or len(donor_direct) != 1
                or donor_direct[0].get("sha256") != actual_wheel_sha256
                or donor_direct[0].get("bytes") != origin["wheel_size"]):
            raise ValueError("adopted candidate donor identity or direct-wheel hash is invalid")
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                raise ValueError("independently built candidate artifact record is invalid")
            path = Path(str(artifact.get("path", "")))
            if (not path.is_absolute() or path.is_symlink() or not path.is_file()
                    or not path.resolve().is_relative_to(candidate_root.resolve(strict=True))
                    or path.stat().st_size != artifact.get("bytes") or digest(path) != artifact.get("sha256")):
                raise ValueError("independently built candidate artifact is missing, linked, or changed")
        identity_payload = {
            "plan_digest": manifest.get("plan_digest"),
            "source_snapshot_sha256": manifest.get("source_snapshot_sha256"),
            "artifacts": artifacts,
            "wheel_closure_sha256": manifest.get("wheel_closure_sha256"),
            "artifact_origin": origin,
            "selected_wheel": selected,
        }
        actual_candidate_identity = hashlib.sha256(json.dumps(
            identity_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
        if actual_candidate_identity != manifest.get("candidate_identity"):
            raise ValueError("adopted candidate identity does not bind its selected wheel and origin")
    else:
        direct = next((item for item in artifacts if "/artifacts/direct/" in item.get("path", "")), None)
        if not direct:
            raise ValueError("candidate manifest has no direct wheel artifact")
        wheel = Path(direct["path"]).resolve(strict=True)
        actual_wheel_sha256 = digest(wheel)
        if actual_wheel_sha256 != direct.get("sha256"):
            raise ValueError("candidate direct wheel hash differs from its manifest")
    audit = runtime.get("audit", {}).get("interpreter", {})
    installed = audit.get("humanmotionlib", {})
    return {
        "manifest": str(manifest_path),
        "manifest_sha256": digest(manifest_path),
        "candidate_identity": manifest["candidate_identity"],
        "source_snapshot_sha256": manifest["source_snapshot_sha256"],
        "wheel_sha256": actual_wheel_sha256,
        "wheel_path": str(wheel),
        "runtime_manifest_sha256": audit.get("runtime_manifest_sha256"),
        "runtime_python": runtime["python"],
        "runtime_origin": installed.get("origin"),
        "runtime_version": installed.get("version"),
        "role": role,
        "adopted": adopted,
    }


def validate_installed_candidate_origin(candidate: dict | None, package_identity: dict) -> None:
    """Ensure installed metadata identifies the exact candidate wheel artifact."""
    if candidate is None:
        return
    actual_url = package_identity.get("direct_url")
    if not isinstance(actual_url, str):
        raise ValueError("installed distribution has no candidate direct_url.json binding")
    actual_path = Path(urllib.parse.unquote(urllib.parse.urlparse(actual_url).path)).resolve(strict=True)
    expected_path = Path(candidate["wheel_path"]).resolve(strict=True)
    if actual_path != expected_path:
        raise ValueError("installed distribution direct_url does not identify the selected candidate wheel")
    declared_hash = package_identity.get("direct_url_sha256")
    if declared_hash is not None and declared_hash != candidate["wheel_sha256"]:
        raise ValueError("installed distribution direct_url hash differs from the selected candidate wheel")
    if digest(expected_path) != candidate["wheel_sha256"]:
        raise ValueError("selected candidate wheel changed after candidate manifest validation")


def run(argv: list[str], *, cwd: Path, env: dict[str, str], expected: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(argv, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    if result.returncode != expected:
        raise AssertionError(
            f"command exit {result.returncode}, expected {expected}: {argv!r}\n{result.stdout}"
        )
    return result


def make_synthetic_predecessor(root: Path) -> None:
    """Create a small complete synthetic predecessor for HTML-only coverage."""
    ids = [f"diag-{index:02d}" for index in range(32)]
    (root / "reference").mkdir(parents=True)
    (root / "composites").mkdir()
    (root / "clean-a").mkdir()
    (root / "clean-b").mkdir()
    (root / "reference/input.json").write_text(
        json.dumps({"sources": {"diagnostics": [{"id": item} for item in ids]}})
    )
    (root / "index.html").write_text("<!doctype html><html><body><h1>Pack</h1></body></html>")
    for item in ids:
        (root / f"{item}.html").write_text(
            f'<!doctype html><html><body><h1>{item}</h1><p>'
            f'<a href="composites/{item}-60-front-static.png">60 BPM front static sheet</a>'
            "</p></body></html>"
        )
        for view in ("front", "side"):
            for bpm in (60, 120, 180):
                for suffix in ("", "-static", "-animation"):
                    (root / "composites" / f"{item}-{bpm}-{view}{suffix}.png").write_bytes(
                        b"synthetic-media"
                    )
            for directory in ("clean-a", "clean-b"):
                frame = root / directory / "frames" / item / view / "00000.png"
                frame.parent.mkdir(parents=True, exist_ok=True)
                frame.write_bytes(b"synthetic-frame")
    names = (
        "metrics.json", "sample-timing.json", "gif-timing.json", "render-repeatability.json",
        "squat-balance.json", "build-metadata.json", "clean-a/render-manifest.json",
        "clean-b/render-manifest.json", "review-draft.md", "source-snapshot.json",
        "review-publication.json",
    )
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if name == "review-draft.md":
            path.write_text("Synthetic retained review evidence for installed HTML-only acceptance.\n")
        elif name == "source-snapshot.json":
            value = {"synthetic": "c" * 64}
        elif name == "review-publication.json":
            value = {"source_snapshot_sha256": digest(root / "source-snapshot.json"),
                     "verdict": "PASS WITH NOTES", "status": "published",
                     "review_sha256": digest(root / "review-draft.md")}
        else:
            value = {"status": "pass"}
        path.write_text(json.dumps(value))


def atomic_json(path: Path, value: dict) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def matrix_outcome(*, status: str, python: Path | None = None,
                   package_origin: str | None = None, package_version: str | None = None,
                   message: str | None = None) -> dict:
    passed = int(status == "passed")
    failed = int(status == "failed")
    errors = 0 if message is None else 1
    value = {
        "schema": "matrix-test-outcome/v1", "status": status,
        "tests": 1, "discovered": 1, "passed": passed, "failed": failed,
        "errors": errors, "skipped": 0, "excluded": [],
        "error_records": [] if message is None else [{"kind": "installed-acceptance", "message": message}],
        "exit_code": 0 if status == "passed" else 130 if status == "interrupted" else 1,
        "import_identity": {
            "python": str(python) if python else sys.executable,
            "sys_prefix": sys.prefix,
            "package_origin": package_origin,
            "package_version": package_version,
        },
    }
    return value


def owned_run_root(workspace: Path, raw: Path) -> tuple[Path, str, Path]:
    """Validate the selected matrix check's caller-owned transient harness root."""
    workspace_input = Path(workspace).expanduser().absolute()
    if workspace_input.is_symlink():
        raise ValueError(f"workspace root must not be a symlink: {workspace_input}")
    workspace = workspace_input.resolve(strict=True)
    value = raw.expanduser()
    if not value.is_absolute():
        raise ValueError("--run-root must be an absolute path")
    build = workspace / "build"
    if build.is_symlink() or not build.is_dir():
        raise ValueError(f"workspace build/ must exist and must not be a symlink: {build}")
    build = build.resolve(strict=True)
    absolute = value.absolute()
    if absolute.is_relative_to(workspace_input):
        relative = absolute.relative_to(workspace_input)
        current = workspace_input
    elif absolute.is_relative_to(workspace):
        relative = absolute.relative_to(workspace)
        current = workspace
    else:
        raise ValueError(f"--run-root must use the selected workspace path: {value}")
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise ValueError(f"--run-root contains a symlink component: {current}")
    if value.is_symlink() or not value.is_dir():
        raise ValueError(f"--run-root must be an existing real directory allocated by its caller: {value}")
    resolved = value.resolve(strict=True)
    if not resolved.is_relative_to(build):
        raise ValueError(f"--run-root must be inside workspace build/: {value}")
    identity_root = resolved
    while identity_root.parent != build and identity_root != build:
        identity_root = identity_root.parent
    parts = identity_root.name.split("_")
    if len(parts) != 5 or not all(RUN_COMPONENT.fullmatch(item) for item in parts):
        raise ValueError("--run-root must be within a selected five-component matrix element root")
    expected = identity_root / ".tmp" / "installed-acceptance"
    if resolved != expected:
        raise ValueError(f"--run-root must be the selected element's .tmp/installed-acceptance directory: {value}")
    for reserved in (value / "scratch", value / "installed-acceptance.json"):
        if reserved.is_symlink() or reserved.exists():
            raise FileExistsError(f"installed acceptance reserved path is occupied: {reserved}")
    return resolved, "_".join(parts[:4]), identity_root


def preflight_generated_runs(run_root: Path, element_root: Path, run_identity: str,
                             raw_scratch: Path | None = None) -> tuple[Path, dict[str, Path]]:
    """Create a nested caller workspace with flat owned run roots for public APIs."""
    element_root_lexical = element_root.absolute()
    element_root_resolved = element_root_lexical.resolve(strict=True)
    if not run_root.resolve(strict=True).is_relative_to(element_root_resolved):
        raise ValueError("installed acceptance root is outside its validated owning element")
    tmp_root = element_root_lexical / ".tmp"
    scratch_input = (Path(raw_scratch).expanduser().absolute() if raw_scratch else
                     tmp_root / "installed-generated")
    try:
        relative = scratch_input.relative_to(tmp_root)
    except ValueError as error:
        raise ValueError(f"installed generated scratch must remain within the selected element .tmp/: {scratch_input}") from error
    current = element_root_lexical
    if current.is_symlink():
        raise ValueError(f"selected installed element contains a symlink: {current}")
    current = tmp_root
    if current.is_symlink():
        raise ValueError(f"installed generated scratch contains a symlink component: {current}")
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise ValueError(f"installed generated scratch contains a symlink component: {current}")
    scratch = scratch_input.resolve(strict=False)
    if not scratch.is_relative_to(element_root_resolved / ".tmp"):
        raise ValueError(f"installed generated scratch escapes the selected element .tmp/: {scratch}")
    resolved_harness = run_root.resolve(strict=True)
    if scratch == resolved_harness or scratch.is_relative_to(resolved_harness) \
            or resolved_harness.is_relative_to(scratch):
        raise ValueError("installed generated workspace must be disjoint from the acceptance harness")
    scratch.mkdir(parents=True, exist_ok=True)
    generated_build_lexical = scratch_input / "build"
    if generated_build_lexical.is_symlink():
        raise ValueError(f"installed generated workspace build/ contains a symlink: {generated_build_lexical}")
    generated_build_lexical.mkdir(exist_ok=True)
    generated_build = generated_build_lexical.resolve(strict=True)
    identity_parts = run_identity.split("_")
    if len(identity_parts) != 4 or not all(RUN_COMPONENT.fullmatch(item) for item in identity_parts):
        raise ValueError("selected installed acceptance identity must have four valid prefix components")
    result = {kind: generated_build / (run_identity + "_" + kind) for kind in RUN_KINDS}
    for path in result.values():
        if path.parent.resolve(strict=True) != generated_build:
            raise ValueError(f"generated output escaped the nested workspace build/: {path}")
        if len(path.name.split("_")) != 5 or not all(
                RUN_COMPONENT.fullmatch(item) for item in path.name.split("_")):
            raise ValueError(f"generated output does not have a five-component run identity: {path}")
        if path.is_symlink() or path.exists():
            raise FileExistsError(f"installed acceptance output root is occupied: {path}")
    return scratch, result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--run-root", required=True, type=Path,
                        help="caller-allocated fresh transient root inside the selected matrix element's .tmp directory")
    parser.add_argument("--generated-root", type=Path,
                        help="optional caller-declared transient fixture root in the selected element .tmp directory")
    parser.add_argument("--candidate-manifest", type=Path,
                        help="optional matrix-candidate/v1 manifest that binds this installed environment to its wheel")
    args = parser.parse_args()
    global ACTIVE_RUN_ROOT, ACTIVE_CANDIDATE
    # Preserve the venv executable path: resolving it follows the symlink to the
    # base interpreter and drops the environment's installed site-packages.
    python = args.python.expanduser().absolute()
    if not python.is_file():
        raise FileNotFoundError(f"installed environment interpreter is missing: {python}")
    workspace = args.workspace.expanduser().absolute()
    run_root, run_identity, element_root = owned_run_root(workspace, args.run_root)
    ACTIVE_RUN_ROOT = run_root
    bytecode_before = sorted(str(path.relative_to(run_root))
                             for path in run_root.rglob("*.pyc"))
    external_cwds = [run_root / "cwd-one", run_root / "cwd-two"]
    empty_external_cwd = run_root / "cwd-empty"
    build = workspace / "build"
    if build.is_symlink() or not build.is_dir():
        raise ValueError(f"workspace build/ must exist and must not be a symlink: {build}")
    workspace_before = outside_build_inventory(workspace, build)
    generated_workspace, generated_roots = preflight_generated_runs(
        run_root, element_root, run_identity, args.generated_root)
    generated_build = generated_workspace / "build"
    escape_sentinel = generated_workspace / "escape-sentinel.txt"
    escape_sentinel.write_text("protected\n")
    generated_workspace_before = outside_build_inventory(generated_workspace, generated_build)
    global ACTIVE_GENERATED_RUNS
    selected_role = run_identity.split("_")[2]
    ACTIVE_GENERATED_RUNS = [
        {"path": str(path), "role": selected_role,
         "status": "planned", "reason": kind}
        for kind, path in sorted(generated_roots.items())
    ]
    for cwd in [*external_cwds, empty_external_cwd]:
        cwd.mkdir()
    scratch_root = run_root / "scratch"
    scratch_root.mkdir()
    env = os.environ.copy()
    for key in ("PYTHONPATH", "PYTHONHOME", "HUMANMOTIONLIB_SOURCE_ROOT"):
        env.pop(key, None)
    env.update({
        "PYTHONDONTWRITEBYTECODE": "1",
        "TMPDIR": str(scratch_root / "tmp"),
        "TMP": str(scratch_root / "tmp"),
        "TEMP": str(scratch_root / "tmp"),
        "XDG_CACHE_HOME": str(scratch_root / "cache"),
        "XDG_CONFIG_HOME": str(scratch_root / "config"),
    })
    for key in ("TMPDIR", "XDG_CACHE_HOME", "XDG_CONFIG_HOME"):
        Path(env[key]).mkdir(parents=True, exist_ok=True)

    # Distribution and resource origins must point at the non-editable install.
    identity = run([str(python), "-c", """
import hashlib, importlib.metadata, importlib.resources, json, pathlib, sysconfig, urllib.parse, humanmotionlib
import yaml, jsonschema, PIL, referencing
from humanmotionlib.characters import resolve_character_selection, validate_character_sources
dist = importlib.metadata.distribution('humanmotionlib')
direct_url_text = dist.read_text('direct_url.json')
direct_url = json.loads(direct_url_text) if direct_url_text else {}
direct_url_path = urllib.parse.unquote(urllib.parse.urlparse(direct_url.get('url', '')).path) or None
direct_url_sha256 = direct_url.get('archive_info', {}).get('hashes', {}).get('sha256')
package = pathlib.Path(humanmotionlib.__file__).resolve()
resources = importlib.resources.files('humanmotionlib').joinpath('resources')
manifest = json.loads(resources.joinpath('runtime-manifest.json').read_text())
validate_character_sources()
character_ids = [item['id'] for item in resolve_character_selection(
 ('female', 'skeleton', 'male'), profile_id='adult-reference-v1')]
assert character_ids == ['skeleton', 'male', 'female'], character_ids
required_character_resources = {
 'characters/registry.yaml',
 'characters/definitions/skeleton.yaml',
 'characters/definitions/male.yaml',
 'characters/definitions/female.yaml',
 'characters/templates/exercise-mannequin-v1.yaml',
 'characters/appearances/male-v1.yaml',
 'characters/appearances/female-v1.yaml',
 'docs/character-models.md',
}
assert required_character_resources <= set(manifest['resources']), required_character_resources - set(manifest['resources'])
assert any(name.startswith('schema/character-') for name in manifest['resources'])
purelib = pathlib.Path(sysconfig.get_paths()['purelib']).resolve()
modules = {'PyYAML': yaml, 'jsonschema': jsonschema, 'Pillow': PIL, 'referencing': referencing}
dependencies = {name: {'version': importlib.metadata.version(name),
 'origin': str(pathlib.Path(module.__file__).resolve())} for name, module in modules.items()}
assert package.is_relative_to(purelib), package
assert all(pathlib.Path(value['origin']).is_relative_to(purelib) for value in dependencies.values()), dependencies
print(json.dumps({'version': dist.version, 'origin': str(package),
 'manifest_sha256': hashlib.sha256(resources.joinpath('runtime-manifest.json').read_bytes()).hexdigest(),
 'resources': manifest['resources'], 'implementation': manifest['implementation'],
 'character_ids': character_ids,
 'dependencies': dependencies,
 'purelib': str(purelib), 'direct_url': direct_url_path,
 'direct_url_sha256': direct_url_sha256}, sort_keys=True))
"""], cwd=external_cwds[0], env=env)
    package_identity = json.loads(identity.stdout)
    selected_candidate = candidate_reference(args.candidate_manifest, python, run_identity)
    ACTIVE_CANDIDATE = selected_candidate
    if selected_candidate:
        validate_installed_candidate_origin(selected_candidate, package_identity)
        if selected_candidate["runtime_origin"] != package_identity["origin"]:
            raise ValueError("installed package origin does not match the candidate manifest")
        if selected_candidate["runtime_manifest_sha256"] != package_identity["manifest_sha256"]:
            raise ValueError("installed runtime manifest does not match the candidate manifest")
    package_origin = Path(package_identity["origin"]).resolve()
    site_packages = Path(subprocess.check_output(
        [str(python), "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"],
        cwd=external_cwds[0], env=env, text=True,
    ).strip()).resolve()
    assert package_origin.is_relative_to(site_packages), (package_origin, site_packages)
    installed_files = package_origin.parent
    installed_before = tree_hashes(installed_files)
    assert installed_before

    # A distracting source-shaped sibling proves resource discovery stays in the wheel.
    hostile_roots = [external_cwds[0], run_root / "sibling-checkout"]
    hostile_hashes = {}
    for hostile in hostile_roots:
        hostile.mkdir(exist_ok=True)
        for relative in ("rig", "schema", "scenes", "docs", "characters"):
            path = hostile / relative
            path.mkdir()
            (path / "poison.yaml").write_text("not: valid HML data\n")
        (hostile / "pyproject.toml").write_text("[project]\nname='hostile-neighbor'\n")
        hostile_hashes[str(hostile)] = tree_hashes(hostile)
    cwd_hashes_before = {str(cwd): tree_hashes(cwd) for cwd in external_cwds}

    # Read-only commands and validation work without a workspace selection.
    cli = python.parent / "hml"
    run([str(cli), "--help"], cwd=external_cwds[0], env=env)
    run([str(cli), "check-environment"], cwd=external_cwds[0], env=env)
    validation = run([str(cli), "validate", "--profile", PROFILE], cwd=external_cwds[0], env=env)
    validation_data = json.loads(validation.stdout)
    assert validation_data["status"] == "valid-sources", validation_data
    assert (validation_data["structures"], validation_data["actions"],
            validation_data["placements"], validation_data["fixtures"]) == (180, 67, 3, 32)

    empty_cwd_before = tree_hashes(empty_external_cwd)
    empty_validation = run([str(cli), "validate", "--profile", PROFILE],
                           cwd=empty_external_cwd, env=env)
    empty_validation_data = json.loads(empty_validation.stdout)
    assert empty_validation_data["status"] == "valid-sources", empty_validation_data
    assert empty_cwd_before == tree_hashes(empty_external_cwd), \
        "read-only installed commands wrote into an empty external caller directory"

    # Fail closed before mutation for missing, empty, and relative workspace selection.
    invalid_cwd_before = {str(cwd): tree_hashes(cwd) for cwd in external_cwds}
    invalid_calls = (
        [str(cli), "prepare-skeleton", "--profile", PROFILE, "--output", "build/no-workspace/input.json"],
        [str(cli), "--workspace", "", "prepare-skeleton", "--profile", PROFILE,
         "--output", "build/empty-workspace/input.json"],
        [str(cli), "--workspace", "relative-workspace", "prepare-skeleton", "--profile", PROFILE,
         "--output", "build/relative-workspace/input.json"],
    )
    for command in invalid_calls:
        run(command, cwd=external_cwds[0], env=env, expected=1)
    assert invalid_cwd_before == {str(cwd): tree_hashes(cwd) for cwd in external_cwds}, \
        "invalid workspace calls changed their external working directories"

    # Console and module entry points receive the global option before the command.
    prepared_paths = []
    for index, cwd in enumerate(external_cwds):
        output = str(generated_roots[f"fixture-{'one' if index == 0 else 'two'}"] / "input.json")
        command = [str(cli), "--workspace", str(generated_workspace), "prepare-skeleton",
                   "--profile", PROFILE, "--output", output]
        if index:
            command = [str(python), "-m", "humanmotionlib", "--workspace", str(generated_workspace),
                       "prepare-skeleton", "--profile", PROFILE, "--output", output]
        run(command, cwd=cwd, env=env)
        prepared_paths.append(generated_workspace / output)
    assert prepared_paths[0].read_bytes() == prepared_paths[1].read_bytes()
    prepared = json.loads(prepared_paths[0].read_text())
    assert prepared["format"] == "skeleton-prepared/v1"
    assert len(prepared["samples"]) == 900
    assert set(prepared["sources"]) == {
        "body-groups", "diagnostics", "humanoid-map", "mobility", "profile", "review-scene"
    }

    # Direct module writer API follows the same explicit workspace contract.
    direct_output = str(generated_roots['prepare-direct'] / "input.json")
    direct = run([str(python), "-c", """
import sys
from humanmotionlib.prepare_skeleton import main
output, workspace = sys.argv[1:3]
sys.argv = ['prepare-skeleton', '--profile', 'adult-reference-v1', '--output', output]
raise SystemExit(main(workspace=workspace))
""", direct_output, str(generated_workspace)], cwd=external_cwds[0], env=env)
    assert "Prepared 900 samples" in direct.stdout
    assert (generated_workspace / direct_output).read_bytes() == prepared_paths[0].read_bytes()

    # The public API prepares structured records outside the checkout. A controlled
    # missing-backend probe verifies catchable failure and receipt evidence without
    # relying on the workstation's Blender installation.
    api_output = str(generated_roots['api-prepare'] / "input.json")
    api_result = run([str(python), "-c", """
import json, pathlib, sys
from humanmotionlib.api import prepare
workspace, output = map(pathlib.Path, sys.argv[1:3])
result = prepare(workspace=workspace, output=output, fixtures=('neutral','arm-raise'), bpms=(90,))
data = result.to_dict()
assert len(data['poses']) == len(result.poses)
assert data['timelines'][0]['entries'][0]['seconds'] == {'numerator': 0, 'denominator': 1}
assert result.prepared_path.is_file()
print(json.dumps({'prepared_sha256': result.prepared_sha256, 'poses': len(result.poses),
 'timelines': len(result.timelines), 'materials': result.provenance.material_ids}))
""", str(generated_workspace), api_output], cwd=external_cwds[0], env=env)
    api_identity = json.loads(api_result.stdout)
    selection_failures = run([str(python), "-c", """
import pathlib, sys
from humanmotionlib.api import GenerationError, render
workspace, prepared = map(pathlib.Path, sys.argv[1:3])
invalid_outputs = list(map(pathlib.Path, sys.argv[3:]))
assert len(invalid_outputs) == 4, invalid_outputs
cases = [('bare-string', 'male'), ('empty', ()), ('duplicate', ('male', 'male')),
         ('unknown', ('unregistered',))]
for index, (name, characters) in enumerate(cases, 1):
    output = invalid_outputs[index - 1]
    try:
        render(prepared, workspace=workspace, output=output, characters=characters)
    except GenerationError as error:
        assert error.code == 'invalid-request', (name, error.code, error.to_dict())
        assert not output.exists(), (name, output)
    else:
        raise AssertionError('invalid character selection was accepted: ' + name)
print('invalid character selections rejected before output allocation')
""", str(generated_workspace), api_output,
        *(str(generated_roots[kind]) for kind in
          ("invalid-one", "invalid-two", "invalid-three", "invalid-four"))],
        cwd=external_cwds[0], env=env)
    missing_path = run_root / "empty-path"
    missing_path.mkdir()
    api_failure = run([str(python), "-c", """
import json, pathlib, sys
from humanmotionlib.api import GenerationError, render
workspace, prepared, output = map(pathlib.Path, sys.argv[1:4])
try:
    render(prepared, workspace=workspace, output=output)
except GenerationError as error:
    assert error.code == 'backend-unavailable', (error.code, error.to_dict())
    assert error.receipt_path and error.receipt_path.is_file()
    print(json.dumps({'code': error.code, 'receipt_path': str(error.receipt_path),
      'run_root': str(error.run_root), 'outcome': error.details['supervisor_outcome']['outcome']}))
else:
    raise AssertionError('missing Blender should fail through a catchable API error')
""", str(generated_workspace), api_output, str(generated_roots['api-failure'])],
        cwd=external_cwds[1], env=env | {"PATH": str(missing_path)})
    api_failure_data = json.loads(api_failure.stdout)

    # Installed numeric host verification also writes relative to the selected workspace.
    verification_output = str(generated_roots['host-verify'] / "report.json")
    run([str(cli), "--workspace", str(generated_workspace), "verify-skeleton", "--input",
         str(generated_roots['fixture-one'] / "input.json"),
         "--output", verification_output, "--transforms-only"], cwd=external_cwds[1], env=env)
    verification = json.loads((generated_workspace / verification_output).read_text())
    assert verification["status"] == "pass", verification.get("status")
    assert len(verification["samples"]) == 900

    # Tampered canonical prepared content is rejected before a report is created.
    tampered_root = generated_roots["tampered-input"]
    tampered_root.mkdir()
    tampered_value = json.loads(prepared_paths[0].read_text())
    tampered_value["samples"][0]["beat"]["numerator"] += 1
    tampered_input = tampered_root / "input.json"
    tampered_input.write_text(json.dumps(tampered_value))
    tampered_report = str(generated_roots['tampered-report'] / "report.json")
    run([str(cli), "--workspace", str(generated_workspace), "verify-skeleton", "--input",
         str(tampered_input), "--output", tampered_report, "--transforms-only"],
        cwd=external_cwds[1], env=env, expected=1)
    assert not (generated_workspace / tampered_report).exists()

    # A stale/incomplete render-reuse root remains ineligible for reassembly.
    reuse_root = generated_roots["host-reuse"]
    reuse_root.mkdir()
    (reuse_root / "clean-a").mkdir()
    (reuse_root / "clean-a/render-manifest.json").write_text('{"status":"pass"}\n')
    reuse_before = tree_hashes(reuse_root)
    run([str(cli), "--workspace", str(generated_workspace), "review-pack", "--input",
         str(prepared_paths[0].parent), "--reuse-renders", "--output", str(reuse_root)],
        cwd=external_cwds[1], env=env, expected=1)
    assert tree_hashes(reuse_root) == reuse_before

    # Valid-looking source neighbors cannot repair missing or altered packaged data.
    integrity_failures = []
    resource_name = next(name for name in package_identity["resources"]
                         if name.startswith("characters/"))
    implementation_name = next(
        name for name in package_identity["implementation"]
        if name.endswith(".py") and name not in {
            "humanmotionlib/__init__.py", "humanmotionlib/__main__.py",
            "humanmotionlib/cli.py", "humanmotionlib/validate.py",
            "humanmotionlib/package_resources.py",
        }
    )
    for label, relative_name in (("resource", "humanmotionlib/resources/" + resource_name),
                                 ("implementation", implementation_name)):
        broken_root = run_root / ("broken-" + label)
        broken_root.mkdir()
        shutil.copytree(package_origin.parent, broken_root / "humanmotionlib")
        broken_file = broken_root / relative_name
        # Installed files and directories may be read-only. Make only this
        # disposable tamper copy writable so the negative reaches HML's
        # integrity validator instead of failing in the filesystem API.
        package_copy = broken_root / "humanmotionlib"
        parent = broken_file.parent
        while parent == package_copy or package_copy in parent.parents:
            parent.chmod(parent.stat().st_mode | stat.S_IWUSR | stat.S_IXUSR)
            if parent == package_copy:
                break
            parent = parent.parent
        if label == "resource":
            broken_file.unlink()
        else:
            broken_file.chmod(broken_file.stat().st_mode | stat.S_IWUSR)
            broken_file.write_bytes(broken_file.read_bytes() + b"\n# tampered acceptance copy\n")
        broken_env = env | {"PYTHONPATH": str(broken_root)}
        broken_result = run([str(cli), "--workspace", str(workspace), "validate",
                             "--profile", PROFILE], cwd=external_cwds[0], env=broken_env,
                            expected=1)
        assert "missing" in broken_result.stdout.lower() or "corrupt" in broken_result.stdout.lower(), \
            broken_result.stdout
        integrity_failures.append(label)

    # Reject traversal and an escaping output symlink before touching a sentinel.
    sentinel_before = digest(escape_sentinel)
    escape_output = "build/../outside-escape/input.json"
    run([str(cli), "--workspace", str(generated_workspace), "prepare-skeleton", "--profile", PROFILE,
         "--output", escape_output], cwd=external_cwds[0], env=env, expected=1)
    symlink_target = run_root / "symlink-escape-target"
    symlink_root = generated_roots["host-symlink"]
    symlink_root.symlink_to(symlink_target, target_is_directory=True)
    try:
        run([str(cli), "--workspace", str(generated_workspace), "prepare-skeleton", "--profile", PROFILE,
        "--output", str(generated_roots['host-symlink'] / "input.json")],
            cwd=external_cwds[0], env=env, expected=1)
    finally:
        symlink_root.unlink()
    assert not symlink_target.exists()
    assert digest(escape_sentinel) == sentinel_before

    # HTML-only presentation uses an explicitly supplied protected predecessor.
    predecessor = run_root / "protected-predecessor"
    make_synthetic_predecessor(predecessor)
    predecessor_before = tree_hashes(predecessor)
    html_output = str(generated_roots['html-only'])
    run([str(cli), "--workspace", str(generated_workspace), "review-pack", "--html-only-from",
         str(predecessor), "--output", html_output], cwd=external_cwds[0], env=env)
    assert (generated_workspace / html_output / "index.html").is_file()
    assert (generated_workspace / html_output / "presentation-provenance.json").is_file()
    assert (generated_workspace / html_output / "presentation-verification.json").is_file()
    assert tree_hashes(predecessor) == predecessor_before

    installed_after = tree_hashes(installed_files)
    assert installed_before == installed_after, "installed package changed during acceptance"
    validate_installed_candidate_origin(selected_candidate, package_identity)
    assert cwd_hashes_before == {str(cwd): tree_hashes(cwd) for cwd in external_cwds}, \
        "an invocation directory changed"
    assert empty_cwd_before == tree_hashes(empty_external_cwd), \
        "an empty external caller working directory changed"
    assert hostile_hashes == {path: tree_hashes(Path(path)) for path in hostile_hashes}, \
        "a misleading resource neighbor changed"
    workspace_after = outside_build_inventory(workspace, build)
    assert workspace_before == workspace_after, \
        "workspace content outside build/ was added, changed, removed or retargeted"
    generated_workspace_after = outside_build_inventory(generated_workspace, generated_build)
    assert generated_workspace_before == generated_workspace_after, \
        "generated workspace content outside build/ was added, changed, removed or retargeted"
    bytecode_after = sorted(str(path.relative_to(run_root))
                            for path in run_root.rglob("*.pyc"))
    assert bytecode_before == bytecode_after, "acceptance created or removed Python bytecode"
    result = {
        **matrix_outcome(status="passed", python=python,
                         package_origin=package_identity["origin"],
                         package_version=package_identity["version"]),
        "status": "passed",
        "scope": "installed-wheel-host-and-synthetic-presentation; real Blender render excluded; structured missing-backend failure checked",
        "backend_launches": 0,
        "backend_launch_evidence": [
            "installed acceptance selects host-only checks and HTML-only presentation",
            "the public render negative probe runs with an empty PATH and records backend-unavailable",
            "no Blender executable is invoked by the acceptance harness",
        ],
        "candidate": selected_candidate,
        "installed_harness_sha256": digest(Path(__file__).resolve()),
        "workspace_scope": "external caller workspace; baseline outside build/ compared exactly",
        "workspace_outside_build_unchanged": True,
        "workspace_outside_build_inventory_count": len(workspace_before),
        "generated_workspace": str(generated_workspace),
        "generated_workspace_outside_build_unchanged": True,
        "generated_workspace_outside_build_inventory_count": len(generated_workspace_before),
        "empty_external_workspace": {
            "cwd": str(empty_external_cwd),
            "validation_status": empty_validation_data["status"],
            "unchanged": True,
        },
        "distribution": package_identity,
        "python": subprocess.check_output([str(python), "--version"], text=True).strip(),
        "entry_points": ["console", "python -m", "direct prepare writer API", "public generation API"],
        "cwd_count": 2,
        "source_validation": {key: validation_data[key] for key in
                              ("status", "structures", "actions", "placements", "fixtures")},
        "prepared_samples": len(prepared["samples"]),
        "public_api": api_identity,
        "character_registry_order": package_identity["character_ids"],
        "character_selection_negative_cases": ["bare-string", "empty", "duplicate", "unknown"],
        "public_api_backend_failure": api_failure_data,
        "numeric_verification": verification["status"],
        "html_only": "pass; protected predecessor unchanged; no backend command",
        "integrity_negative_cases": integrity_failures + ["prepared-content", "stale-render-reuse",
                                                           "traversal", "escaping-symlink"],
        "installed_package_files": len(installed_after),
        "read_only_install": installed_before == installed_after,
        "workspace": str(workspace),
        "outer_run_root": str(run_root),
        "generated_runs": [
            {**item, "status": "generated" if Path(item["path"]).exists()
             else "not-created-negative-control"}
            for item in ACTIVE_GENERATED_RUNS
        ],
    }
    atomic_json(run_root / "installed-acceptance.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        traceback.print_exc()
        if ACTIVE_RUN_ROOT is not None:
            atomic_json(ACTIVE_RUN_ROOT / "installed-acceptance.json", {
                **matrix_outcome(status="failed", message=f"{type(exc).__name__}: {exc}"),
                "failure_traceback": traceback.format_exc(),
                "outer_run_root": str(ACTIVE_RUN_ROOT),
                "candidate": ACTIVE_CANDIDATE,
                "installed_harness_sha256": digest(Path(__file__).resolve()),
                "generated_runs": [
                    {**item, "status": "generated" if Path(item["path"]).exists()
                     else "not-created"}
                    for item in ACTIVE_GENERATED_RUNS
                ],
            })
        raise SystemExit(1) from exc
    except KeyboardInterrupt:
        if ACTIVE_RUN_ROOT is not None:
            atomic_json(ACTIVE_RUN_ROOT / "installed-acceptance.json", {
                **matrix_outcome(status="interrupted", message="KeyboardInterrupt"),
                "outer_run_root": str(ACTIVE_RUN_ROOT),
                "candidate": ACTIVE_CANDIDATE,
                "installed_harness_sha256": digest(Path(__file__).resolve()),
                "generated_runs": [
                    {**item, "status": "generated" if Path(item["path"]).exists()
                     else "not-created"}
                    for item in ACTIVE_GENERATED_RUNS
                ],
            })
        raise SystemExit(130)
