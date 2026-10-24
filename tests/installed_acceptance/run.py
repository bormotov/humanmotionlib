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
from pathlib import Path
import shutil
import subprocess
import sys


PROFILE = "adult-reference-v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): digest(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--run-root", required=True, type=Path)
    args = parser.parse_args()
    # Preserve the venv executable path: resolving it follows the symlink to the
    # base interpreter and drops the environment's installed site-packages.
    python = args.python.expanduser().absolute()
    if not python.is_file():
        raise FileNotFoundError(f"installed environment interpreter is missing: {python}")
    workspace = args.workspace.resolve()
    run_root = args.run_root.resolve(strict=True)
    bytecode_before = sorted(str(path.relative_to(run_root))
                             for path in run_root.rglob("*.pyc"))
    external_cwds = [run_root / "cwd-one", run_root / "cwd-two"]
    for cwd in external_cwds:
        cwd.mkdir()
    build = workspace / "build"
    build.mkdir(parents=True, exist_ok=True)
    scratch_root = build / "portable-installed-runtime_e3dcbf_ci_attempt-5_host-scratch"
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
import hashlib, importlib.metadata, importlib.resources, json, pathlib, sysconfig, humanmotionlib
import yaml, jsonschema, PIL, referencing
dist = importlib.metadata.distribution('humanmotionlib')
package = pathlib.Path(humanmotionlib.__file__).resolve()
resources = importlib.resources.files('humanmotionlib').joinpath('resources')
manifest = json.loads(resources.joinpath('runtime-manifest.json').read_text())
purelib = pathlib.Path(sysconfig.get_paths()['purelib']).resolve()
modules = {'PyYAML': yaml, 'jsonschema': jsonschema, 'Pillow': PIL, 'referencing': referencing}
dependencies = {name: {'version': importlib.metadata.version(name),
 'origin': str(pathlib.Path(module.__file__).resolve())} for name, module in modules.items()}
assert package.is_relative_to(purelib), package
assert all(pathlib.Path(value['origin']).is_relative_to(purelib) for value in dependencies.values()), dependencies
print(json.dumps({'version': dist.version, 'origin': str(package),
 'manifest_sha256': hashlib.sha256(resources.joinpath('runtime-manifest.json').read_bytes()).hexdigest(),
 'resources': manifest['resources'], 'implementation': manifest['implementation'],
 'dependencies': dependencies,
 'purelib': str(purelib)}, sort_keys=True))
"""], cwd=external_cwds[0], env=env)
    package_identity = json.loads(identity.stdout)
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
        for relative in ("rig", "schema", "scenes", "docs"):
            path = hostile / relative
            path.mkdir()
            (path / "poison.yaml").write_text("not: valid HML data\n")
        (hostile / "pyproject.toml").write_text("[project]\nname='hostile-neighbor'\n")
        hostile_hashes[str(hostile)] = tree_hashes(hostile)
    cwd_hashes_before = {str(cwd): tree_hashes(cwd) for cwd in external_cwds}

    # Read-only commands and validation work without a workspace selection.
    cli = python.parent / "hml"
    assert "humanmotionlib" in run([str(cli), "--version"], cwd=external_cwds[0], env=env).stdout
    run([str(cli), "--help"], cwd=external_cwds[0], env=env)
    run([str(cli), "check-environment"], cwd=external_cwds[0], env=env)
    validation = run([str(cli), "validate", "--profile", PROFILE], cwd=external_cwds[0], env=env)
    validation_data = json.loads(validation.stdout)
    assert validation_data["status"] == "valid-sources", validation_data
    assert (validation_data["structures"], validation_data["actions"],
            validation_data["placements"], validation_data["fixtures"]) == (180, 67, 3, 32)

    # Fail closed before mutation for missing, empty, and relative workspace selection.
    baseline_workspace = tree_hashes(workspace)
    invalid_calls = (
        [str(cli), "prepare-skeleton", "--profile", PROFILE, "--output", "build/no-workspace/input.json"],
        [str(cli), "--workspace", "", "prepare-skeleton", "--profile", PROFILE,
         "--output", "build/empty-workspace/input.json"],
        [str(cli), "--workspace", "relative-workspace", "prepare-skeleton", "--profile", PROFILE,
         "--output", "build/relative-workspace/input.json"],
    )
    for command in invalid_calls:
        run(command, cwd=external_cwds[0], env=env, expected=1)
    assert tree_hashes(workspace) == baseline_workspace

    # Console and module entry points receive the global option before the command.
    prepared_paths = []
    for index, cwd in enumerate(external_cwds):
        run_name = f"portable-installed-runtime_e3dcbf_ci_attempt-{index + 1}_fixture"
        output = f"build/{run_name}/input.json"
        command = [str(cli), "--workspace", str(workspace), "prepare-skeleton",
                   "--profile", PROFILE, "--output", output]
        if index:
            command = [str(python), "-m", "humanmotionlib", "--workspace", str(workspace),
                       "prepare-skeleton", "--profile", PROFILE, "--output", output]
        run(command, cwd=cwd, env=env)
        prepared_paths.append(workspace / output)
    assert prepared_paths[0].read_bytes() == prepared_paths[1].read_bytes()
    prepared = json.loads(prepared_paths[0].read_text())
    assert prepared["format"] == "skeleton-prepared/v1"
    assert len(prepared["samples"]) == 900
    assert set(prepared["sources"]) == {
        "body-groups", "diagnostics", "humanoid-map", "mobility", "profile", "review-scene"
    }

    # Direct module writer API follows the same explicit workspace contract.
    direct_output = "build/portable-installed-runtime_e3dcbf_ci_attempt-3_prepare-direct/input.json"
    direct = run([str(python), "-c", """
import sys
from humanmotionlib.prepare_skeleton import main
output, workspace = sys.argv[1:3]
sys.argv = ['prepare-skeleton', '--profile', 'adult-reference-v1', '--output', output]
raise SystemExit(main(workspace=workspace))
""", direct_output, str(workspace)], cwd=external_cwds[0], env=env)
    assert "Prepared 900 samples" in direct.stdout
    assert (workspace / direct_output).read_bytes() == prepared_paths[0].read_bytes()

    # Installed numeric host verification also writes relative to the selected workspace.
    verification_output = "build/portable-installed-runtime_e3dcbf_ci_attempt-1_host-verify/report.json"
    run([str(cli), "--workspace", str(workspace), "verify-skeleton", "--input",
         "build/portable-installed-runtime_e3dcbf_ci_attempt-1_fixture/input.json",
         "--output", verification_output, "--transforms-only"], cwd=external_cwds[1], env=env)
    verification = json.loads((workspace / verification_output).read_text())
    assert verification["status"] == "pass", verification.get("status")
    assert len(verification["samples"]) == 900

    # Tampered canonical prepared content is rejected before a report is created.
    tampered_root = workspace / "build/portable-installed-runtime_e3dcbf_ci_attempt-4_tampered-input"
    tampered_root.mkdir()
    tampered_value = json.loads(prepared_paths[0].read_text())
    tampered_value["samples"][0]["beat"]["numerator"] += 1
    tampered_input = tampered_root / "input.json"
    tampered_input.write_text(json.dumps(tampered_value))
    tampered_report = "build/portable-installed-runtime_e3dcbf_ci_attempt-4_tampered-report/report.json"
    run([str(cli), "--workspace", str(workspace), "verify-skeleton", "--input",
         str(tampered_input), "--output", tampered_report, "--transforms-only"],
        cwd=external_cwds[1], env=env, expected=1)
    assert not (workspace / tampered_report).exists()

    # A stale/incomplete render-reuse root remains ineligible for reassembly.
    reuse_root = workspace / "build/portable-installed-runtime_e3dcbf_ci_attempt-4_host-reuse"
    reuse_root.mkdir()
    (reuse_root / "clean-a").mkdir()
    (reuse_root / "clean-a/render-manifest.json").write_text('{"status":"pass"}\n')
    reuse_before = tree_hashes(reuse_root)
    run([str(cli), "--workspace", str(workspace), "review-pack", "--input",
         str(prepared_paths[0].parent), "--reuse-renders", "--output", str(reuse_root)],
        cwd=external_cwds[1], env=env, expected=1)
    assert tree_hashes(reuse_root) == reuse_before

    # Valid-looking source neighbors cannot repair missing or altered packaged data.
    integrity_failures = []
    resource_name = next(iter(package_identity["resources"]))
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
        if label == "resource":
            broken_file.unlink()
        else:
            broken_file.write_bytes(broken_file.read_bytes() + b"\n# tampered acceptance copy\n")
        broken_env = env | {"PYTHONPATH": str(broken_root)}
        broken_result = run([str(cli), "--workspace", str(workspace), "validate",
                             "--profile", PROFILE], cwd=external_cwds[0], env=broken_env,
                            expected=1)
        assert "missing" in broken_result.stdout.lower() or "corrupt" in broken_result.stdout.lower(), \
            broken_result.stdout
        integrity_failures.append(label)

    # Reject traversal and an escaping output symlink before touching a sentinel.
    escape_sentinel = run_root / "escape-sentinel.txt"
    escape_sentinel.write_text("protected\n")
    sentinel_before = digest(escape_sentinel)
    escape_output = "build/../outside-escape/input.json"
    run([str(cli), "--workspace", str(workspace), "prepare-skeleton", "--profile", PROFILE,
         "--output", escape_output], cwd=external_cwds[0], env=env, expected=1)
    symlink_target = run_root / "symlink-escape-target"
    symlink_root = workspace / "build/portable-installed-runtime_e3dcbf_ci_attempt-4_host-symlink"
    symlink_root.symlink_to(symlink_target, target_is_directory=True)
    try:
        run([str(cli), "--workspace", str(workspace), "prepare-skeleton", "--profile", PROFILE,
             "--output", "build/portable-installed-runtime_e3dcbf_ci_attempt-4_host-symlink/input.json"],
            cwd=external_cwds[0], env=env, expected=1)
    finally:
        symlink_root.unlink()
    assert not symlink_target.exists()
    assert digest(escape_sentinel) == sentinel_before

    # HTML-only presentation uses an explicitly supplied protected predecessor.
    predecessor = run_root / "protected-predecessor"
    make_synthetic_predecessor(predecessor)
    predecessor_before = tree_hashes(predecessor)
    html_output = "build/portable-installed-runtime_e3dcbf_ci_attempt-1_html-only"
    run([str(cli), "--workspace", str(workspace), "review-pack", "--html-only-from",
         str(predecessor), "--output", html_output], cwd=external_cwds[0], env=env)
    assert (workspace / html_output / "index.html").is_file()
    assert (workspace / html_output / "presentation-provenance.json").is_file()
    assert (workspace / html_output / "presentation-verification.json").is_file()
    assert tree_hashes(predecessor) == predecessor_before

    installed_after = tree_hashes(installed_files)
    assert installed_before == installed_after, "installed package changed during acceptance"
    assert cwd_hashes_before == {str(cwd): tree_hashes(cwd) for cwd in external_cwds}, \
        "an invocation directory changed"
    assert hostile_hashes == {path: tree_hashes(Path(path)) for path in hostile_hashes}, \
        "a misleading resource neighbor changed"
    workspace_files = [path for path in workspace.rglob("*") if path.is_file()]
    assert all(path.is_relative_to(build) for path in workspace_files), \
        f"workspace writes escaped build/: {workspace_files}"
    bytecode_after = sorted(str(path.relative_to(run_root))
                            for path in run_root.rglob("*.pyc"))
    assert bytecode_before == bytecode_after, "acceptance created or removed Python bytecode"
    result = {
        "status": "pass",
        "scope": "installed-wheel-host-and-synthetic-presentation; real Blender unexecuted",
        "distribution": package_identity,
        "python": subprocess.check_output([str(python), "--version"], text=True).strip(),
        "entry_points": ["console", "python -m", "direct prepare writer API"],
        "cwd_count": 2,
        "source_validation": {key: validation_data[key] for key in
                              ("status", "structures", "actions", "placements", "fixtures")},
        "prepared_samples": len(prepared["samples"]),
        "numeric_verification": verification["status"],
        "html_only": "pass; protected predecessor unchanged; no backend command",
        "integrity_negative_cases": integrity_failures + ["prepared-content", "stale-render-reuse",
                                                           "traversal", "escaping-symlink"],
        "installed_package_files": len(installed_after),
        "read_only_install": installed_before == installed_after,
        "workspace": str(workspace),
        "outer_run_root": str(run_root),
    }
    (run_root / "installed-acceptance.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
