"""Validate the supported HML host and run tests that do not need Blender."""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Iterator
import importlib.metadata
import importlib
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import sysconfig
import tempfile
import tomllib
import urllib.parse
import unittest


BACKEND_EXCLUSIONS = {
    "tests.test_blender_backend": "requires the pinned real Blender backend",
    "tests.test_pipeline_faults": "injects faults into the real Blender scene pipeline",
}
DIRECT_IMPORTS = {"PyYAML": "yaml", "jsonschema": "jsonschema", "Pillow": "PIL", "referencing": "referencing"}


def check_environment(
    project_root: Path | None = None,
    version_info: tuple[int, ...] = sys.version_info,
    implementation_name: str = sys.implementation.name,
) -> list[str]:
    """Return configuration/runtime disagreements; no implicit version coercion."""
    errors: list[str] = []
    if project_root is not None:
        try:
            project = tomllib.loads((project_root / "pyproject.toml").read_text())
            requirement = project["project"]["requires-python"]
            selector = (project_root / ".python-version").read_text().strip()
        except (OSError, KeyError, tomllib.TOMLDecodeError) as exc:
            return [f"cannot read contributor Python requirement: {exc}"]
        if not isinstance(requirement, str) or set(requirement.split(",")) != {">=3.14", "<3.15"}:
            errors.append(f"pyproject.toml requires-python is {requirement!r}, expected '>=3.14,<3.15'")
        if selector != "3.14":
            errors.append(f".python-version selects {selector!r}, expected '3.14'")
    else:
        try:
            requirement = importlib.metadata.metadata("humanmotionlib").get("Requires-Python")
        except importlib.metadata.PackageNotFoundError as exc:
            return [f"humanmotionlib distribution metadata is unavailable: {exc}"]
        if not isinstance(requirement, str) or set(requirement.split(",")) != {">=3.14", "<3.15"}:
            errors.append(f"installed Requires-Python is {requirement!r}, expected '>=3.14,<3.15'")
    if implementation_name != "cpython" or tuple(version_info[:2]) != (3, 14):
        errors.append(
            "actual interpreter must be CPython 3.14; got "
            f"{implementation_name} {version_info[0]}.{version_info[1]}"
        )

    for distribution, module in DIRECT_IMPORTS.items():
        try:
            importlib.metadata.version(distribution)
            importlib.import_module(module)
        except importlib.metadata.PackageNotFoundError:
            errors.append(f"direct dependency {distribution} is not installed")
        except (ImportError, ValueError) as exc:
            errors.append(f"direct dependency {distribution} cannot import as {module}: {exc}")
    try:
        from humanmotionlib.package_resources import verify_runtime_integrity
        verify_runtime_integrity()
    except (ImportError, OSError, ValueError, RuntimeError) as exc:
        errors.append(f"installed package resources are invalid: {exc}")
    return errors


def iter_cases(suite: unittest.TestSuite | unittest.TestCase) -> Iterator[unittest.TestCase]:
    if isinstance(suite, unittest.TestCase):
        yield suite
        return
    for item in suite:
        yield from iter_cases(item)


def is_backend_excluded(test: unittest.TestCase) -> str | None:
    test_id = test.id()
    # `unittest discover -s tests` imports these modules as `test_*`, while the
    # repository's file/module identity is `tests.test_*`.
    if not test_id.startswith("tests."):
        test_id = "tests." + test_id
    for module in BACKEND_EXCLUSIONS:
        if test_id == module or test_id.startswith(module + "."):
            return module
    return None


def discover_host_tests(project_root: Path) -> tuple[unittest.TestSuite, dict[str, int], list[str]]:
    loader = unittest.TestLoader()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    discovered = loader.discover(
        start_dir=str(project_root / "tests"),
        pattern="test*.py",
    )
    exclusions = {name: 0 for name in BACKEND_EXCLUSIONS}
    selected = unittest.TestSuite()
    for test in iter_cases(discovered):
        excluded_module = is_backend_excluded(test)
        if excluded_module:
            exclusions[excluded_module] += 1
        else:
            selected.addTest(test)
    return selected, exclusions, list(loader.errors)


def run_selected_tests(
    suite: unittest.TestSuite,
    exclusions: dict[str, int],
    discovery_errors: list[str],
    stream,
) -> int:
    return _test_outcome(suite, exclusions, discovery_errors, stream)["exit_code"]


class _OutcomeResult(unittest.TextTestResult):
    """Text result which also retains machine-readable per-case outcomes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cases: list[dict[str, str]] = []
        self.successes: list[unittest.TestCase] = []
        self._case_positions: dict[int, int] = {}

    def startTest(self, test):
        super().startTest(test)
        self._case_positions[id(test)] = len(self.cases)
        self.cases.append({"id": test.id(), "status": "running"})

    def _set_status(self, test, status: str, detail: str | None = None):
        position = self._case_positions.get(id(test))
        if position is None:
            position = len(self.cases)
            self._case_positions[id(test)] = position
            self.cases.append({"id": test.id(), "status": status})
        self.cases[position]["status"] = status
        if detail:
            self.cases[position]["detail"] = detail

    def addSuccess(self, test):
        super().addSuccess(test)
        self.successes.append(test)
        self._set_status(test, "passed")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._set_status(test, "failed", self._exc_info_to_string(err, test))

    def addError(self, test, err):
        super().addError(test, err)
        self._set_status(test, "error", self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._set_status(test, "skipped", str(reason))

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self._set_status(test, "expected-failure", self._exc_info_to_string(err, test))

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self._set_status(test, "unexpected-success")


def _atomic_json(path: Path, value: dict) -> None:
    if path.is_symlink() or path.exists():
        raise FileExistsError(f"structured host outcome already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _test_outcome(
    suite: unittest.TestSuite,
    exclusions: dict[str, int],
    discovery_errors: list[str],
    stream,
) -> dict:
    excluded = [
        {"module": module, "reason": reason, "count": exclusions.get(module, 0)}
        for module, reason in BACKEND_EXCLUSIONS.items()
    ]
    for item in excluded:
        print(f"Excluded {item['module']}: {item['reason']} ({item['count']} tests)", file=stream)

    total = suite.countTestCases()
    print(f"Selected tests: {total}", file=stream)
    if discovery_errors:
        for error in discovery_errors:
            print(f"Discovery error: {error}", file=stream)
        return {
            "schema": "matrix-test-outcome/v1", "status": "failed", "tests": total,
            "discovered": total, "passed": 0, "failed": 0,
            "errors": len(discovery_errors), "skipped": 0, "excluded": excluded,
            "error_records": [{"kind": "discovery", "message": error} for error in discovery_errors],
            "failure_records": [], "skip_records": [], "cases": [], "exit_code": 1,
        }
    if total == 0:
        print("Host test selection is empty", file=stream)
        return {
            "schema": "matrix-test-outcome/v1", "status": "failed", "tests": 0,
            "discovered": 0, "passed": 0, "failed": 0, "errors": 0,
            "skipped": 0, "excluded": excluded, "error_records": [],
            "failure_records": [], "skip_records": [], "cases": [], "exit_code": 1,
        }

    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=_OutcomeResult).run(suite)
    print(f"Skipped tests: {len(result.skipped)}", file=stream)
    for test, reason in result.skipped:
        print(f"Skipped {test.id()}: {reason}", file=stream)
    failures = len(result.failures) + len(result.unexpectedSuccesses)
    errors = len(result.errors)
    ok = result.wasSuccessful()
    return {
        "schema": "matrix-test-outcome/v1", "status": "passed" if ok else "failed",
        "tests": total, "discovered": total, "passed": len(result.successes),
        "failed": failures, "errors": errors, "skipped": len(result.skipped),
        "excluded": excluded,
        "error_records": [
            {"kind": "error", "test_id": test.id(), "traceback": detail}
            for test, detail in result.errors
        ],
        "failure_records": [
            {"kind": "failure", "test_id": test.id(), "traceback": detail}
            for test, detail in result.failures
        ] + [
            {"kind": "unexpected-success", "test_id": test.id()}
            for test in result.unexpectedSuccesses
        ],
        "skip_records": [
            {"test_id": test.id(), "reason": reason} for test, reason in result.skipped
        ],
        "cases": result.cases, "exit_code": 0 if ok else 1,
    }


def _import_identity() -> dict[str, str | None]:
    try:
        import humanmotionlib
        origin = str(Path(humanmotionlib.__file__).resolve()) if humanmotionlib.__file__ else None
        version = importlib.metadata.version("humanmotionlib")
    except (ImportError, importlib.metadata.PackageNotFoundError, OSError) as exc:
        origin, version = None, None
        error = str(exc)
    else:
        error = ""
    return {"python": sys.executable, "sys_prefix": sys.prefix,
            "package_origin": origin, "package_version": version,
            "error": error}


def _validate_adopted_candidate(manifest_path: Path, manifest: dict, role: str,
                                environment: dict) -> tuple[Path, str]:
    """Validate the selected frozen wheel bound into a reviewer candidate."""
    selected = manifest.get("selected_wheel")
    origin = manifest.get("artifact_origin")
    if not isinstance(selected, dict) or not isinstance(origin, dict):
        raise ValueError("adopted candidate has incomplete selected-wheel provenance")
    recipient_identity = manifest.get("identity")
    if (role != "reviewer" or not isinstance(recipient_identity, dict)
            or recipient_identity.get("role") != "reviewer"):
        raise ValueError("adopted candidate must bind to the reviewer role")
    if "source_ownership" in origin:
        raise ValueError("candidate provenance must not persist the internal ownership proof")

    candidate_root = manifest_path.parent
    runtime_root = candidate_root / f"runtime-{role}-env"
    runtime_python = Path(str(environment.get("python", ""))).resolve()
    if not runtime_python.is_relative_to(runtime_root.resolve(strict=True)):
        raise ValueError("adopted candidate interpreter is outside its fresh role environment")
    raw_selected = Path(str(selected.get("path", "")))
    name = selected.get("name")
    if (not raw_selected.is_absolute() or not isinstance(name, str) or not name
            or Path(name).name != name):
        raise ValueError("selected donor wheel path or name is invalid")
    selected_root = candidate_root / "artifacts" / "selected"
    wheel = raw_selected
    if (candidate_root.is_symlink() or (candidate_root / "artifacts").is_symlink()
            or selected_root.is_symlink() or wheel.is_symlink()
            or wheel.resolve(strict=True) != wheel.absolute()
            or wheel.resolve(strict=True) != (selected_root / name).resolve(strict=True)
            or not wheel.resolve(strict=True).is_relative_to(selected_root.resolve(strict=True))):
        raise ValueError("selected donor wheel is linked or outside candidate artifacts/selected")
    wheel = wheel.resolve(strict=True)
    actual_hash = hashlib.sha256(wheel.read_bytes()).hexdigest()
    if (wheel.name != name or wheel.stat().st_size != selected.get("bytes")
            or actual_hash != selected.get("sha256")):
        raise ValueError("selected donor wheel bytes differ from the sealed selected_wheel record")
    runtime_wheel_value = environment.get("wheel")
    runtime_wheel = Path(runtime_wheel_value).resolve() if isinstance(runtime_wheel_value, str) else None
    if (runtime_wheel != wheel
            or environment.get("wheel_sha256") != actual_hash
            or origin.get("direct_wheel_sha256") != actual_hash
            or origin.get("wheel_size") != wheel.stat().st_size):
        raise ValueError("installed runtime does not bind to the selected frozen donor wheel")

    required_text = (
        "source_plan_path", "source_plan_sha256", "source_plan_digest",
        "source_candidate_manifest_path", "source_candidate_manifest_sha256",
        "source_manifest_sha256", "source_candidate_identity", "source_role",
        "source_snapshot_sha256", "logical_closure_sha256",
    )
    if any(not isinstance(origin.get(field), str) or not origin[field] for field in required_text):
        raise ValueError("adopted candidate origin record is incomplete")
    hex_digest = re.compile(r"^[0-9a-f]{64}$")
    for field in ("source_plan_sha256", "source_candidate_manifest_sha256",
                  "source_manifest_sha256", "source_snapshot_sha256",
                  "logical_closure_sha256", "direct_wheel_sha256"):
        if not isinstance(origin.get(field), str) or not hex_digest.fullmatch(origin[field]):
            raise ValueError(f"adopted candidate origin {field} is not a SHA-256")
    if (origin["source_role"] != "dev"
            or origin["source_manifest_sha256"] != origin["source_candidate_manifest_sha256"]
            or origin["logical_closure_sha256"] != manifest.get("wheel_closure_sha256")):
        raise ValueError("adopted candidate donor role or source identity is inconsistent")
    sdist = origin.get("source_sdist_identity")
    dependencies = origin.get("origin_dependencies")
    if not isinstance(sdist, dict) or not isinstance(dependencies, list) or not dependencies:
        raise ValueError("adopted candidate origin dependencies are incomplete")
    if (not isinstance(sdist.get("path"), str) or not Path(sdist["path"]).is_absolute()
            or not isinstance(sdist.get("sha256"), str) or not hex_digest.fullmatch(sdist["sha256"])
            or not isinstance(sdist.get("bytes"), int) or not isinstance(sdist.get("source_hashes_sha256"), str)
            or not hex_digest.fullmatch(sdist["source_hashes_sha256"])):
        raise ValueError("adopted candidate source-distribution identity is invalid")
    if not all(isinstance(item, dict) and isinstance(item.get("kind"), str)
               and isinstance(item.get("path"), str) and Path(item["path"]).is_absolute()
               and isinstance(item.get("sha256"), str) and hex_digest.fullmatch(item["sha256"])
               for item in dependencies):
        raise ValueError("adopted candidate origin dependency record is invalid")
    if any(any(term in item["kind"].lower() for term in ("runtime", "environment", "acceptance"))
           for item in dependencies):
        raise ValueError("adopted candidate must not depend on donor environments or acceptance results")

    dependency_by_kind: dict[str, list[dict]] = {}
    for item in dependencies:
        dependency_by_kind.setdefault(item["kind"], []).append(item)
        dependency_path = Path(item["path"])
        if (dependency_path.is_symlink() or not dependency_path.is_file()
                or dependency_path.resolve(strict=True) != dependency_path.absolute()
                or hashlib.sha256(dependency_path.read_bytes()).hexdigest() != item["sha256"]):
            raise ValueError(f"adopted candidate source dependency is missing, linked, or changed: {dependency_path}")
    for kind, expected_path, expected_sha in (
        ("source-plan", origin["source_plan_path"], origin["source_plan_sha256"]),
        ("source-candidate-manifest", origin["source_candidate_manifest_path"],
         origin["source_candidate_manifest_sha256"]),
        ("direct-wheel", origin["direct_wheel_path"], origin["direct_wheel_sha256"]),
        ("source-distribution", sdist["path"], sdist["sha256"]),
    ):
        matches = dependency_by_kind.get(kind, [])
        if (len(matches) != 1 or matches[0]["path"] != expected_path
                or matches[0]["sha256"] != expected_sha):
            raise ValueError(f"adopted candidate {kind} origin is not bound by its dependency inventory")
    source_plan_path = Path(origin["source_plan_path"])
    source_plan = json.loads(source_plan_path.read_text(encoding="utf-8"))
    source_manifest_path = Path(origin["source_candidate_manifest_path"])
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    source_identity = source_plan.get("identity")
    if (source_plan.get("plan_digest") != origin["source_plan_digest"]
            or not isinstance(source_identity, dict) or source_identity.get("role") != "dev"
            or source_manifest.get("schema") != "matrix-candidate/v1"
            or source_manifest.get("status") != "succeeded"
            or "artifact_origin" in source_manifest or "selected_wheel" in source_manifest
            or source_manifest.get("plan_digest") != origin["source_plan_digest"]
            or source_manifest.get("identity") != source_identity
            or source_manifest.get("candidate_identity") != origin["source_candidate_identity"]
            or source_manifest.get("source_snapshot_sha256") != origin["source_snapshot_sha256"]):
        raise ValueError("adopted candidate donor source plan or first-generation manifest is inconsistent")
    source_plan_content = dict(source_plan)
    source_plan_content.pop("plan_digest", None)
    source_plan_content.pop("created_utc", None)
    source_plan_digest = hashlib.sha256(json.dumps(
        source_plan_content, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    donor_identity_payload = {
        "plan_digest": source_manifest.get("plan_digest"),
        "source_snapshot_sha256": source_manifest.get("source_snapshot_sha256"),
        "artifacts": source_manifest.get("artifacts"),
        "wheel_closure_sha256": source_manifest.get("wheel_closure_sha256"),
    }
    donor_identity = hashlib.sha256(json.dumps(
        donor_identity_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    if (source_plan_digest != origin["source_plan_digest"]
            or donor_identity != origin["source_candidate_identity"]):
        raise ValueError("adopted candidate donor plan or candidate identity digest is invalid")
    donor_direct = [item for item in source_manifest.get("artifacts", [])
                    if item.get("path") == origin["direct_wheel_path"]]
    if (len(donor_direct) != 1 or donor_direct[0].get("sha256") != origin["direct_wheel_sha256"]
            or donor_direct[0].get("bytes") != origin["wheel_size"]):
        raise ValueError("adopted candidate donor direct-wheel record does not match the frozen pin")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValueError("adopted candidate has no independent build artifact inventory")
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise ValueError("adopted candidate build artifact record is invalid")
        path = Path(str(artifact.get("path", "")))
        if (not path.is_absolute() or path.is_symlink() or not path.is_file()
                or not path.resolve().is_relative_to(candidate_root.resolve(strict=True))
                or path.stat().st_size != artifact.get("bytes")
                or hashlib.sha256(path.read_bytes()).hexdigest() != artifact.get("sha256")):
            raise ValueError("independently built candidate artifact is missing, linked, or changed")

    identity_payload = {
        "plan_digest": manifest.get("plan_digest"),
        "source_snapshot_sha256": manifest.get("source_snapshot_sha256"),
        "artifacts": artifacts,
        "wheel_closure_sha256": manifest.get("wheel_closure_sha256"),
        "artifact_origin": origin,
        "selected_wheel": selected,
    }
    identity_hash = hashlib.sha256(json.dumps(
        identity_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    if not manifest.get("candidate_identity") or identity_hash != manifest["candidate_identity"]:
        raise ValueError("adopted candidate identity does not bind its selected wheel and origin")
    return wheel, actual_hash


def _validate_expected_candidate(args: argparse.Namespace, identity: dict[str, str | None],
                                 project_root: Path | None) -> list[str]:
    """Validate a run-local candidate only when its exact environment is declared."""
    names = ("expected_python", "expected_prefix", "expected_purelib",
             "expected_package_origin", "candidate_manifest")
    supplied = [getattr(args, name) is not None for name in names]
    if not any(supplied):
        return []
    if not all(supplied):
        return ["candidate runtime expectations must be supplied together"]

    canonical = lambda value: Path(value).resolve() if value else None
    expected_python = canonical(args.expected_python)
    expected_prefix = canonical(args.expected_prefix)
    expected_purelib = canonical(args.expected_purelib)
    expected_origin = canonical(args.expected_package_origin)
    live_values = (
        ("interpreter", expected_python, canonical(identity.get("python"))),
        ("prefix", expected_prefix, canonical(sys.prefix)),
        ("purelib", expected_purelib, canonical(sysconfig.get_paths().get("purelib"))),
        ("package origin", expected_origin, canonical(identity.get("package_origin"))),
    )
    errors = [f"candidate {name} does not match the live runtime"
              for name, expected, actual in live_values if expected is None or expected != actual]
    if expected_origin is None or expected_purelib is None or not expected_origin.is_relative_to(expected_purelib):
        errors.append("candidate package origin is outside the declared purelib")
    if expected_prefix is None or expected_purelib is None or not expected_purelib.is_relative_to(expected_prefix):
        errors.append("candidate purelib is outside the declared runtime prefix")
    if project_root is not None and expected_origin is not None:
        checkout_source = (project_root.resolve() / "src/humanmotionlib/__init__.py").resolve()
        if expected_origin == checkout_source:
            errors.append("candidate import resolves to checkout source")

    try:
        manifest_path = Path(args.candidate_manifest).resolve(strict=True)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema") != "matrix-candidate/v1" or manifest.get("status") != "succeeded":
            raise ValueError("candidate manifest is not a successful matrix-candidate/v1")
        role_matches = [(role, environment) for role, environment in manifest.get("runtime_environments", {}).items()
                        if canonical(environment.get("python")) == expected_python]
        if len(role_matches) != 1:
            raise ValueError("candidate manifest does not identify exactly one selected runtime role")
        role, environment = role_matches[0]
        audit = environment.get("audit", {}).get("interpreter", {})
        if role != environment.get("role"):
            raise ValueError("candidate runtime role metadata is inconsistent")
        for name, declared, actual in (
            ("interpreter", expected_python, canonical(audit.get("python"))),
            ("prefix", expected_prefix, canonical(audit.get("sys_prefix"))),
            ("purelib", expected_purelib, canonical(audit.get("purelib"))),
            ("package origin", expected_origin, canonical(audit.get("humanmotionlib", {}).get("origin"))),
        ):
            if declared is None or declared != actual:
                raise ValueError(f"candidate manifest {name} does not match the declaration")
        if audit.get("humanmotionlib", {}).get("version") != identity.get("package_version"):
            raise ValueError("candidate manifest package version does not match the installed distribution")
        is_adopted = "selected_wheel" in manifest or "artifact_origin" in manifest
        if is_adopted:
            wheel, wheel_hash = _validate_adopted_candidate(
                manifest_path, manifest, role, environment)
        else:
            wheel = canonical(environment.get("wheel"))
            wheel_hash = environment.get("wheel_sha256")
            artifact_matches = [artifact for artifact in manifest.get("artifacts", [])
                                if canonical(artifact.get("path")) == wheel
                                and artifact.get("sha256") == wheel_hash]
            if len(artifact_matches) != 1 or hashlib.sha256(wheel.read_bytes()).hexdigest() != wheel_hash:
                raise ValueError("candidate direct wheel artifact/hash is invalid")
        distribution = importlib.metadata.distribution("humanmotionlib")
        direct_url_text = distribution.read_text("direct_url.json")
        if not direct_url_text:
            raise ValueError("installed distribution has no direct_url.json candidate binding")
        installed_url = json.loads(direct_url_text).get("url", "")
        installed_wheel = canonical(urllib.parse.unquote(urllib.parse.urlparse(installed_url).path))
        if installed_wheel != wheel:
            raise ValueError("installed distribution direct_url does not identify the candidate wheel")
        installed_manifest = expected_purelib / "humanmotionlib/resources/runtime-manifest.json"
        runtime_hash = hashlib.sha256(installed_manifest.read_bytes()).hexdigest()
        if runtime_hash != audit.get("runtime_manifest_sha256"):
            raise ValueError("installed runtime manifest differs from the candidate audit")
        if not manifest.get("candidate_identity") or not manifest.get("source_snapshot_sha256"):
            raise ValueError("candidate manifest omits candidate/source identity")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
            importlib.metadata.PackageNotFoundError) as exc:
        errors.append(f"candidate manifest validation failed: {exc}")
    return errors


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-environment",
        action="store_true",
        help="check CPython/version metadata and direct dependency imports, then exit",
    )
    parser.add_argument("--test-root", type=Path,
                        help="Explicit contributor tests directory; never inferred by installed environment checks")
    parser.add_argument("--json-report", type=Path,
                        help="Write additive matrix-test-outcome/v1 results atomically to this path")
    parser.add_argument("--expected-python", help="Exact selected candidate interpreter")
    parser.add_argument("--expected-prefix", help="Exact selected candidate sys.prefix")
    parser.add_argument("--expected-purelib", help="Exact selected candidate purelib")
    parser.add_argument("--expected-package-origin", help="Exact selected installed package __init__.py")
    parser.add_argument("--candidate-manifest", help="Successful matrix-candidate/v1 manifest binding the installed wheel")
    args = parser.parse_args(argv)
    project_root = None if args.check_environment else (args.test_root.resolve().parent if args.test_root else Path(__file__).resolve().parents[2])
    errors = check_environment(project_root)
    identity = _import_identity()
    candidate_args = (args.expected_python, args.expected_prefix, args.expected_purelib,
                      args.expected_package_origin, args.candidate_manifest)
    errors.extend(_validate_expected_candidate(args, identity, project_root))
    if not any(candidate_args) and project_root is not None and identity["package_origin"]:
        package_origin = Path(identity["package_origin"]).resolve()
        if package_origin.is_relative_to(project_root.resolve()):
            errors.append(f"installed humanmotionlib import resolves inside the checkout: {package_origin}")
    if errors:
        for error in errors:
            print(f"Host environment error: {error}", file=sys.stderr)
        if args.json_report:
            _atomic_json(args.json_report, {
                "schema": "matrix-test-outcome/v1", "status": "blocked",
                "tests": 0, "discovered": 0, "passed": 0, "failed": 0,
                "errors": len(errors), "skipped": 0, "excluded": [],
                "error_records": [{"kind": "environment", "message": error} for error in errors],
                "failure_records": [], "skip_records": [], "cases": [],
                "exit_code": 1, "import_identity": identity,
            })
        return 1
    print(
        "Host interpreter: "
        f"{sys.implementation.name} {sys.version_info.major}.{sys.version_info.minor}."
        f"{sys.version_info.micro} ({sys.executable})"
    )
    if args.check_environment:
        print(f"humanmotionlib: {importlib.metadata.version('humanmotionlib')}")
        for distribution in DIRECT_IMPORTS:
            print(f"{distribution}: {importlib.metadata.version(distribution)}")
        return 0

    tests_root = args.test_root.resolve() if args.test_root else project_root / "tests"
    suite, exclusions, discovery_errors = discover_host_tests(tests_root.parent)
    outcome = _test_outcome(suite, exclusions, discovery_errors, sys.stderr)
    outcome["import_identity"] = identity
    if args.json_report:
        _atomic_json(args.json_report, outcome)
    return outcome["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
