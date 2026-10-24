"""Validate the supported HML host and run tests that do not need Blender."""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Iterator
import importlib.metadata
import importlib
from pathlib import Path
import sys
import tomllib
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
    for module, reason in BACKEND_EXCLUSIONS.items():
        print(f"Excluded {module}: {reason} ({exclusions.get(module, 0)} tests)", file=stream)
    if discovery_errors:
        for error in discovery_errors:
            print(f"Discovery error: {error}", file=stream)
        return 1

    total = suite.countTestCases()
    print(f"Selected tests: {total}", file=stream)
    if total == 0:
        print("Host test selection is empty", file=stream)
        return 1

    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    print(f"Skipped tests: {len(result.skipped)}", file=stream)
    for test, reason in result.skipped:
        print(f"Skipped {test.id()}: {reason}", file=stream)
    return 0 if result.wasSuccessful() else 1


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-environment",
        action="store_true",
        help="check CPython/version metadata and direct dependency imports, then exit",
    )
    parser.add_argument("--test-root", type=Path,
                        help="Explicit contributor tests directory; never inferred by installed environment checks")
    args = parser.parse_args(argv)
    project_root = None if args.check_environment else (args.test_root.resolve().parent if args.test_root else Path(__file__).resolve().parents[2])
    errors = check_environment(project_root)
    if errors:
        for error in errors:
            print(f"Host environment error: {error}", file=sys.stderr)
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
    return run_selected_tests(suite, exclusions, discovery_errors, sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
