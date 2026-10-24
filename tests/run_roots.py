# SPDX-License-Identifier: Apache-2.0
"""Caller-owned flat build roots for the repository's executable test suites."""

import os
from pathlib import Path
import re

from humanmotionlib.runtime import project_root


_COMPONENT = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_ENVIRONMENT_ROOT = "HUMANMOTIONLIB_TEST_RUN_ROOT"
_ROOTS = {}
_FRESH_ATTEMPTS = {}


def test_run_root(module):
    """Return an owning flat build root, allocating lazily only for local dev runs.

    Reviewers and CI callers set HUMANMOTIONLIB_TEST_RUN_ROOT to a fresh direct
    child of build/. All module artifacts remain tool content under cases/.
    """
    if module in _ROOTS:
        return _ROOTS[module]
    build = (project_root() / "build").resolve()
    configured = os.environ.get(_ENVIRONMENT_ROOT)
    if configured:
        root = Path(configured).resolve()
        if root.parent != build or len(root.name.split("_")) != 5 or not all(
                _COMPONENT.fullmatch(part) for part in root.name.split("_")):
            raise ValueError(f"{_ENVIRONMENT_ROOT} must name a valid direct-child build run root")
        if not root.is_dir():
            raise ValueError(f"caller-owned test run root must already exist: {root}")
    else:
        pattern = re.compile(r"^harden-backend-process-execution_r3_dev_try-(\d+)_checks$")
        attempts = [int(match.group(1)) for entry in build.iterdir()
                    if (match := pattern.match(entry.name))]
        root = build / f"harden-backend-process-execution_r3_dev_try-{max(attempts, default=0)+1}_checks"
        root.mkdir(parents=False, exist_ok=False)
    cases = root / "cases" / module
    cases.mkdir(parents=True, exist_ok=True)
    _ROOTS[module] = root
    return root


def test_case_root(module, name):
    root = test_run_root(module)
    case = root / "cases" / module / name
    case.mkdir(parents=False, exist_ok=False)
    return case


def fresh_test_run_root(kind):
    """Allocate one fresh flat developer run under the checkout build/ tree."""
    build = (project_root() / "build").resolve()
    prefix = f"portable-installed-runtime_e3dcbf_dev_try-"
    attempt = _FRESH_ATTEMPTS.get(kind, 0)
    while True:
        attempt += 1
        root = build / f"{prefix}{attempt}_{kind}"
        if not root.exists():
            root.mkdir(parents=False, exist_ok=False)
            _FRESH_ATTEMPTS[kind] = attempt
            return root


def test_cases_directory(module):
    root = test_run_root(module)
    return root / "cases" / module
