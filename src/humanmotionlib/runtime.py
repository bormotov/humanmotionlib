# SPDX-License-Identifier: Apache-2.0
"""Shared backend identity checks and bounded, auditable process execution."""

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid


DEFAULT_PROBE_TIMEOUT = 30.0
DEFAULT_BUILD_TIMEOUT = 1800.0
DEFAULT_RENDER_TIMEOUT = 14400.0
DEFAULT_SLOT_TIMEOUT = 30.0
TERMINATE_GRACE_SECONDS = 5.0
KILL_REAP_SECONDS = 5.0
MAX_TIMEOUT_SECONDS = 86400.0
_RUN_COMPONENT = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_MANAGED_RENDER_PASS_NAMES = frozenset({
    "clean-a", "clean-b", "skeleton-default", "skeleton-explicit",
    "male-singleton", "female-singleton", "stature-150", "stature-190",
})
_NESTED_MANAGED_RENDER_PASSES = frozenset({
    ("pair-skeleton", "clean-a"), ("pair-skeleton", "clean-b"),
    ("pair-male", "clean-a"), ("pair-male", "clean-b"),
    ("pair-female", "clean-a"), ("pair-female", "clean-b"),
    ("skeleton-mode-check", "skeleton-default"),
    ("skeleton-mode-check", "skeleton-explicit"),
})
_MATRIX_RENDER_PASSES = frozenset({
    "clean-a", "clean-b", "skeleton-default", "skeleton-explicit",
    "male-singleton", "female-singleton", "stature-150", "stature-190",
})
MATRIX_DESTINATIONS = {
    "prepare": frozenset({"prepared/input.json"}),
    "render": frozenset({"render", *(f"presentation/{name}" for name in _MATRIX_RENDER_PASSES)}),
}


class InvocationError(RuntimeError):
    """A failed invocation with its durable receipt attached."""

    def __init__(self, message, receipt):
        super().__init__(message)
        self.receipt = receipt


class SlotTimeout(TimeoutError):
    """Deprecated compatibility exception; backend slots are no longer used."""


def project_root():
    """Return an explicitly selected source checkout for contributor-only tests."""
    configured = os.environ.get("HUMANMOTIONLIB_SOURCE_ROOT")
    if configured:
        candidate = Path(configured).resolve()
        if (candidate / "pyproject.toml").is_file():
            return candidate
        raise RuntimeError("HUMANMOTIONLIB_SOURCE_ROOT does not contain pyproject.toml")
    candidate = Path(__file__).resolve().parents[2]
    if (candidate / "pyproject.toml").is_file():
        return candidate
    raise RuntimeError("No repository root is available in the installed package; use an explicit workspace")


def workspace_root(workspace):
    """Return the resolved, explicitly selected caller workspace."""
    if workspace is None:
        raise ValueError("an explicit absolute --workspace PATH is required for filesystem-writing operations")
    try:
        operand = os.fspath(workspace)
    except TypeError as error:
        raise ValueError("workspace must be a nonempty absolute path") from error
    if not operand or not Path(operand).is_absolute():
        raise ValueError("workspace must be a nonempty absolute path")
    root = Path(operand).resolve()
    if root.exists() and not root.is_dir():
        raise ValueError(f"workspace is not a directory: {root}")
    return root


def resolve_workspace_path(path, workspace):
    """Resolve a relative workflow operand from the selected workspace."""
    root = workspace_root(workspace)
    try:
        operand = os.fspath(path)
    except TypeError as error:
        raise ValueError("workflow path must be a nonempty path") from error
    if not operand:
        raise ValueError("workflow path must be a nonempty path")
    candidate = Path(operand)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate.resolve()


def _build_root(workspace):
    root = workspace_root(workspace)
    build = (root / "build").resolve()
    try:
        build.relative_to(root)
    except ValueError as error:
        raise ValueError(f"workspace build directory resolves outside the workspace: {root / 'build'}") from error
    if build.exists() and not build.is_dir():
        raise ValueError(f"workspace build path is not a directory: {build}")
    return build


def ensure_workspace_build(workspace):
    """Create the selected workspace/build after the caller has completed path preflight."""
    root = workspace_root(workspace)
    build = _build_root(root)
    probe = root
    while not probe.exists():
        probe = probe.parent
    if not probe.is_dir() or not os.access(probe, os.W_OK | os.X_OK):
        raise ValueError(f"workspace parent is not writable: {probe}")
    if root.exists() and not os.access(root, os.W_OK | os.X_OK):
        raise ValueError(f"workspace is not writable: {root}")
    build.mkdir(parents=True, exist_ok=True)
    # Re-resolve after creation in case a path component changed during setup.
    if _build_root(root) != build:
        raise ValueError("workspace build directory changed during setup")
    return build


def _validate_owned_run_root(run_root, workspace=None):
    """Require evidence to live below a valid direct-child build run identity."""
    build = _build_root(workspace)
    path = Path(run_root).resolve()
    candidate = path
    while candidate != build and candidate.parent != build and candidate.parent != candidate:
        nested_parts = candidate.name.split("_")
        if len(nested_parts) == 5 and all(_RUN_COMPONENT.fullmatch(part) for part in nested_parts):
            raise ValueError(f"nested run identity is not a valid evidence path: {candidate}")
        candidate = candidate.parent
    if candidate.parent != build:
        raise ValueError(f"invocation evidence is outside build/: {path}")
    parts = candidate.name.split("_")
    if len(parts) != 5 or not all(_RUN_COMPONENT.fullmatch(part) for part in parts):
        raise ValueError(f"invocation evidence has no valid five-component run root: {candidate}")
    return candidate


def validate_run_root(run_root, workspace=None):
    """Validate a fresh run identity as a direct child of workspace/build."""
    build = _build_root(workspace)
    path = Path(run_root).resolve()
    if path.parent != build:
        raise ValueError(f"run root must be a direct child of workspace build/: {path}")
    parts = path.name.split("_")
    if len(parts) != 5 or not all(_RUN_COMPONENT.fullmatch(part) for part in parts):
        raise ValueError(f"run root must have five lowercase kebab-case components: {path}")
    return path


def validate_managed_pass_root(pass_root, owner_run, workspace):
    """Validate a direct or explicitly allowed nested pass below a flat owner."""
    root = workspace_root(workspace)

    def lexical_path(value, label):
        operand = Path(os.fspath(value))
        if ".." in operand.parts:
            raise ValueError(f"managed render {label} cannot contain traversal components")
        if not operand.is_absolute():
            operand = root / operand
        return Path(os.path.abspath(operand))

    owner_operand = lexical_path(owner_run, "owner")
    owner = validate_run_root(owner_operand, root)
    if owner_operand != owner or owner.is_symlink() or not owner.is_dir():
        raise ValueError(f"managed render pass owner must be a real existing run directory: {owner}")

    path = lexical_path(pass_root, "pass")
    try:
        relative = path.relative_to(owner)
    except ValueError as error:
        raise ValueError(f"managed render pass escapes its owner: {path}") from error
    parts = relative.parts
    allowed = (len(parts) == 1 and parts[0] in _MANAGED_RENDER_PASS_NAMES)
    allowed = allowed or tuple(parts) in _NESTED_MANAGED_RENDER_PASSES
    if not allowed:
        raise ValueError(f"managed render pass is not a designated owner destination: {path}")

    # All nested grouping directories must already exist as real directories;
    # a final pass may be absent until the API claims it, but cannot be a link.
    for component in (owner, *(owner / part for part in parts[:-1])):
        if component.is_symlink() or not component.is_dir():
            raise ValueError(f"managed render path has a missing or symlinked parent: {component}")
    if path.is_symlink():
        raise ValueError(f"managed render pass cannot be a symlink: {path}")
    return path


def validate_operation_root(run_root, workspace, owner_run=None):
    """Validate a standalone run or an explicitly owned internal render pass."""
    if owner_run is None:
        return validate_run_root(run_root, workspace)
    return validate_managed_pass_root(run_root, owner_run, workspace)


def validate_matrix_content_root(content_root, element_root, workspace, *, relative_path):
    """Validate one declared nested matrix destination without inferring authority."""
    workspace = workspace_root(workspace)
    operand = Path(os.fspath(element_root))
    if ".." in operand.parts:
        raise ValueError("matrix element root cannot contain traversal components")
    if not operand.is_absolute():
        operand = workspace / operand
    lexical_element = Path(os.path.abspath(operand))
    element = validate_run_root(lexical_element, workspace)
    if lexical_element != element:
        raise ValueError("matrix element root contains a symlink or noncanonical path")
    expected = element / relative_path
    content_operand = Path(os.fspath(content_root))
    if ".." in content_operand.parts:
        raise ValueError("matrix content root cannot contain traversal components")
    lexical_path = Path(os.path.abspath(
        content_operand if content_operand.is_absolute() else workspace / content_operand))
    if lexical_path != expected:
        raise ValueError(f"matrix content destination must be {expected}")
    cursor = element
    for part in Path(relative_path).parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"matrix content path contains a symlink: {cursor}")
    path = resolve_workspace_path(content_operand, workspace)
    if path != expected:
        raise ValueError(f"matrix content destination resolves outside its declared path: {path}")
    return path


def validate_matrix_content_destination(content_root, element_root, workspace, *, operation,
                                        allowed_destinations=None):
    """Validate one explicit destination in the finite matrix content allowlist."""
    if operation not in MATRIX_DESTINATIONS:
        raise ValueError(f"unsupported matrix content operation: {operation}")
    allowed = MATRIX_DESTINATIONS[operation]
    if allowed_destinations is not None:
        allowed_destinations = frozenset(allowed_destinations)
        if not allowed_destinations or not allowed_destinations <= allowed:
            raise ValueError(f"invalid matrix destination allowlist for {operation}")
        allowed = allowed_destinations
    operand = Path(os.fspath(content_root))
    if ".." in operand.parts:
        raise ValueError("matrix content root cannot contain traversal components")
    workspace_path = workspace_root(workspace)
    lexical = Path(os.path.abspath(operand if operand.is_absolute() else workspace_path / operand))
    element_operand = Path(os.fspath(element_root))
    if ".." in element_operand.parts:
        raise ValueError("matrix element root cannot contain traversal components")
    if not element_operand.is_absolute():
        element_operand = workspace_path / element_operand
    lexical_element = Path(os.path.abspath(element_operand))
    try:
        relative_path = lexical.relative_to(lexical_element).as_posix()
    except ValueError as error:
        raise ValueError("matrix content destination is outside its declared element") from error
    if relative_path not in allowed:
        raise ValueError(f"matrix content destination is not allowed for {operation}: {relative_path}")
    element = validate_run_root(lexical_element, workspace_path)
    if lexical_element != element:
        raise ValueError("matrix element root contains a symlink or noncanonical path")
    destination = validate_matrix_content_root(
        content_root, element_root, workspace_path, relative_path=relative_path)
    return element, destination, relative_path


def validate_existing_run_root(run_root, workspace):
    """Validate a read-only run input under its actual workspace build directory."""
    path = resolve_workspace_path(run_root, workspace)
    if path.parent.name != "build":
        raise ValueError(f"existing run input must be a direct child of its actual build/: {path}")
    owner = path.parent.parent
    if _build_root(owner) != path.parent:
        raise ValueError(f"existing run input is outside its owning workspace build/: {path}")
    parts = path.name.split("_")
    if len(parts) != 5 or not all(_RUN_COMPONENT.fullmatch(part) for part in parts):
        raise ValueError(f"existing run input has no valid five-component run root: {path}")
    if not path.is_dir():
        raise ValueError(f"existing run input is not a directory: {path}")
    return path


def validate_run_content_path(path, workspace):
    """Resolve a writer destination and require it to remain in one valid run."""
    resolved = resolve_workspace_path(path, workspace)
    run_root = _validate_owned_run_root(resolved, workspace)
    return resolved, run_root


def backend_contract():
    from humanmotionlib.package_resources import read_bytes
    return json.loads(read_bytes("backend-contract.json"))


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
    if executable is None:
        raise ValueError("Blender is not on PATH")
    return str(Path(executable).resolve())


def validate_timeout(value, name="timeout_seconds"):
    try:
        value = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a finite positive number no greater than {MAX_TIMEOUT_SECONDS:g}") from error
    if not math.isfinite(value) or value <= 0 or value > MAX_TIMEOUT_SECONDS:
        raise ValueError(f"{name} must be a finite positive number no greater than {MAX_TIMEOUT_SECONDS:g}")
    return value


def _utc_now():
    return datetime.now(timezone.utc).isoformat()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{os.getpid()}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    os.replace(temporary, path)


def update_receipt(receipt, **updates):
    receipt.update(updates)
    path = Path(receipt["stdout_log"]).parent / "outcome.json"
    _atomic_json(path, receipt)
    return receipt


def _raw_group_state(pgid):
    if pgid is None:
        return "ambiguous"
    try:
        os.killpg(int(pgid), 0)
    except ProcessLookupError:
        return "absent"
    except PermissionError:
        return "ambiguous"
    except OSError:
        return "ambiguous"
    return "present"


def _group_state(pgid, *, anchor_pid=None, ps_timeout=2.0):
    # Inspect only the process group created by this invocation. A zombie-only
    # group may remain visible until the OS reaps it; report that conservatively
    # as present/cleanup-pending rather than querying the global process table.
    state = _raw_group_state(pgid)
    if state != "present":
        return state
    return "present"


def _signal_group(pgid, sig):
    try:
        os.killpg(int(pgid), sig)
        return "sent"
    except ProcessLookupError:
        return "absent"
    except (PermissionError, OSError):
        return "ambiguous"


def _unreaped_child_state(child):
    """Observe child exit without releasing its PID/PGID identity anchor."""
    if child.returncode is not None:
        return "reaped"
    waitid = getattr(os, "waitid", None)
    required = (getattr(os, "WEXITED", 0), getattr(os, "WNOHANG", 0), getattr(os, "WNOWAIT", 0))
    if waitid is None or not all(required):
        return "ambiguous"
    try:
        info = waitid(os.P_PID, child.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
    except ChildProcessError:
        return "reaped"
    except OSError:
        return "ambiguous"
    return "exited" if info is not None and info.si_pid == child.pid else "running"


def _wait_child_unreaped(child, timeout):
    """Wait for the direct child without reaping its PID/PGID identity anchor."""
    deadline = time.monotonic() + timeout
    while True:
        state = _unreaped_child_state(child)
        if state != "running":
            return state
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return "running"
        time.sleep(min(0.02, remaining))


def _cleanup_owned_group(child, pgid):
    """Clean a live owned group while the direct-child identity remains anchored.

    Never probe or signal a PGID after the direct child has been reaped. If the
    group cannot be confirmed absent before reaping, preserve diagnostics and
    report cleanup_pending.
    """
    child_state = _unreaped_child_state(child)
    if child_state in {"reaped", "ambiguous"}:
        return "not-attempted-after-reap" if child_state == "reaped" else "cleanup_pending"
    _signal_group(pgid, signal.SIGTERM)
    term_deadline = time.monotonic() + TERMINATE_GRACE_SECONDS
    group_state = "present"
    while time.monotonic() < term_deadline:
        child_state = _unreaped_child_state(child)
        if child_state in {"reaped", "ambiguous"}:
            break
        group_state = _group_state(pgid, anchor_pid=child.pid)
        if group_state == "absent":
            break
        time.sleep(min(0.05, max(0.0, term_deadline - time.monotonic())))
    kill_deadline = time.monotonic() + KILL_REAP_SECONDS
    child_state = _unreaped_child_state(child)
    if group_state != "absent" and child_state in {"running", "exited"}:
        _signal_group(pgid, signal.SIGKILL)
    while time.monotonic() < kill_deadline:
        child_state = _unreaped_child_state(child)
        if child_state in {"reaped", "ambiguous"}:
            break
        group_state = _group_state(pgid, anchor_pid=child.pid)
        if group_state == "absent":
            break
        time.sleep(min(0.05, max(0.0, kill_deadline - time.monotonic())))
    child_state = _unreaped_child_state(child)
    if child_state == "reaped":
        return "not-attempted-after-reap"
    if child_state == "exited":
        child.wait()
    else:
        try:
            child.wait(timeout=max(0.0, kill_deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            return "cleanup_pending"
    return "confirmed" if group_state == "absent" else "cleanup_pending"


def _observed_phases(stdout_path):
    phases = []
    for line in Path(stdout_path).read_text(errors="replace").splitlines():
        if not line.startswith("HML_PHASE "):
            continue
        try:
            phases.append(json.loads(line[len("HML_PHASE "):]))
        except json.JSONDecodeError:
            phases.append({"phase": "malformed-marker", "line": line[:512]})
    return phases


@contextmanager
def backend_slot(timeout_seconds=DEFAULT_SLOT_TIMEOUT, *, operation_id=None, workspace=None):
    """Deprecated no-op retained for callers using the former slot API.

    ``timeout_seconds`` remains accepted for source compatibility. Calls do
    not read, create, or update legacy workspace lock/state files.
    """
    yield


def _make_receipt(operation_root, operation_id):
    directory = Path(operation_root) / "processes" / operation_id
    directory.mkdir(parents=True, exist_ok=False)
    receipt, stdout, stderr = directory / "outcome.json", directory / "stdout.log", directory / "stderr.log"
    stdout.touch()
    stderr.touch()
    return receipt, stdout, stderr


def invocation(command, *, run_root, operation, cwd=None, timeout_seconds,
               slot_timeout_seconds=DEFAULT_SLOT_TIMEOUT, source_sha256=None,
               expected_outputs=None, env=None, workspace=None, owner_run=None):
    """Run one command in an owned process group and persist bounded evidence.

    The caller supplies a unique owning run root. No shell is used and output is
    streamed directly to files. An unsuccessful call raises ``InvocationError``.
    """
    root = workspace_root(workspace)
    if owner_run is None:
        # Generic supervision may be owned by validated tool content inside a
        # run (for example tests/runtime/<caller>). This is evidence placement,
        # not allocation of another independent run.
        operation_root = resolve_workspace_path(run_root, root)
        owning_root = _validate_owned_run_root(operation_root, root)
    else:
        operation_root = validate_operation_root(run_root, root, owner_run)
        owning_root = validate_run_root(owner_run, root)
    timeout = validate_timeout(timeout_seconds)
    slot_timeout = validate_timeout(slot_timeout_seconds, "slot_timeout_seconds")
    if os.name != "posix" or not hasattr(os, "killpg"):
        raise RuntimeError("supervised backend execution requires POSIX process groups")
    args = [os.fspath(item) for item in command]
    if not args:
        raise ValueError("command must contain an executable")
    working_directory = resolve_workspace_path(cwd if cwd is not None else root, root)
    if working_directory != root:
        raise ValueError("supervised backend cwd must be the selected workspace")
    if expected_outputs is not None:
        for item in expected_outputs:
            target = Path(item["path"] if isinstance(item, dict) else item).resolve()
            try:
                target.relative_to(owning_root)
            except ValueError as error:
                raise ValueError(f"expected output escapes its owning run: {target}") from error
    from humanmotionlib.package_resources import manifest_sha256, verify_runtime_integrity
    package_manifest = verify_runtime_integrity()
    package_identity = {
        "package_version": package_manifest["version"],
        "runtime_manifest_sha256": manifest_sha256(),
        "resource_hashes": package_manifest["resources"],
        "backend_contract_sha256": package_manifest["backend_contract"],
        "implementation_hashes": package_manifest["implementation"],
    }
    operation_id = uuid.uuid4().hex
    ensure_workspace_build(root)
    receipt_path, stdout_path, stderr_path = _make_receipt(operation_root, operation_id)
    scratch_root = receipt_path.parent / "scratch"
    if scratch_root.is_symlink() or not scratch_root.resolve().is_relative_to(receipt_path.parent):
        raise ValueError(f"backend scratch escapes its invocation evidence directory: {scratch_root}")
    executable = shutil.which(args[0]) if not os.path.isabs(args[0]) else args[0]
    executable = str(Path(executable).resolve()) if executable else args[0]
    command = [executable, *args[1:]]
    receipt = {
        "format": "backend-invocation/v1", "state": "running", "invocation_id": operation_id,
        "operation": operation, "command": command, "cwd": str(Path(cwd or root).resolve()),
        "source_sha256": source_sha256, "executable": executable,
        **package_identity, "workspace": str(root),
        "platform": platform.system() + "-" + platform.machine(), "python": platform.python_version(),
        "started_at": _utc_now(), "deadline_seconds": timeout, "slot_timeout_seconds": slot_timeout,
        "stdout_log": str(stdout_path), "stderr_log": str(stderr_path),
        "owning_run_root": str(owning_root), "operation_root": str(operation_root),
        "scratch_paths": {"temporary": str(scratch_root / "tmp"),
                          "cache": str(scratch_root / "cache"),
                          "configuration": str(scratch_root / "config")},
        "scratch_cleanup": {"path": str(scratch_root), "status": "not-created"},
        "last_script_phase": "unknown", "output_validation": {"status": "not-run"},
        "cleanup": {"status": "not-needed"}, "process_group_id": None,
    }
    output_specs = []
    for item in expected_outputs or []:
        if isinstance(item, dict):
            output_specs.append({"path": Path(item["path"]),
                                 "allow_existing_sha256": item.get("allow_existing_sha256")})
        else:
            output_specs.append({"path": Path(item), "allow_existing_sha256": None})
    stale = []
    for spec in output_specs:
        path = spec["path"]
        if path.exists():
            digest = file_sha256(path) if path.is_file() else None
            if digest is None or digest != spec["allow_existing_sha256"]:
                stale.append(str(path))
    receipt["expected_outputs"] = [{"path": str(item["path"].resolve()),
                                    "preexisting_sha256": file_sha256(item["path"])
                                    if item["path"].is_file() else None,
                                    "allowed_preexisting_sha256": item["allow_existing_sha256"]}
                                   for item in output_specs]
    if stale:
        receipt.update({"state": "failed", "outcome": "stale_output",
                        "error": "output paths already exist: " + ", ".join(stale),
                        "finished_at": _utc_now(), "elapsed_seconds": 0.0,
                        "output_validation": {"status": "fail", "reason": "stale-output-preflight", "paths": stale}})
        _atomic_json(receipt_path, receipt)
        raise InvocationError(receipt["error"], str(receipt_path))
    scratch_env = {
        "TMPDIR": str(scratch_root / "tmp"), "TMP": str(scratch_root / "tmp"),
        "TEMP": str(scratch_root / "tmp"),
        "XDG_CACHE_HOME": str(scratch_root / "cache"),
        "XDG_CONFIG_HOME": str(scratch_root / "config"),
        "BLENDER_USER_CONFIG": str(scratch_root / "blender-config"),
        "BLENDER_USER_SCRIPTS": str(scratch_root / "blender-scripts"),
        "BLENDER_USER_DATAFILES": str(scratch_root / "blender-data"),
    }
    for directory in scratch_env.values():
        Path(directory).mkdir(parents=True, exist_ok=True)
    receipt["scratch_cleanup"] = {"path": str(scratch_root), "status": "pending"}
    _atomic_json(receipt_path, receipt)
    started = time.monotonic()
    child = None
    pgid = None
    outer_handlers = {}

    def cancel_before_wait(signum, _frame):
        raise KeyboardInterrupt(f"cancelled by signal {signum}")

    for signum in (signal.SIGINT, signal.SIGTERM):
        try:
            outer_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, cancel_before_wait)
        except ValueError:  # signal handlers can only be changed by the main thread
            outer_handlers = {}
            break
    try:
        with backend_slot(slot_timeout, operation_id=operation_id, workspace=workspace):
            with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
                try:
                    child_env = os.environ.copy()
                    child_env.update(scratch_env)
                    child_env["PYTHONDONTWRITEBYTECODE"] = "1"
                    if env is not None:
                        child_env.update(env)
                    for variable in ("PYTHONPATH", "PYTHONHOME"):
                        child_env.pop(variable, None)
                    child_env["PYTHONNOUSERSITE"] = "1"
                    child = subprocess.Popen(command, cwd=working_directory, stdout=stdout, stderr=stderr,
                                             stdin=subprocess.DEVNULL, env=child_env, start_new_session=True)
                except OSError as error:
                    receipt.update({"state": "failed", "outcome": "spawn_error", "error": str(error),
                                    "spawn_error": {"type": type(error).__name__, "errno": error.errno},
                                    "finished_at": _utc_now(), "elapsed_seconds": time.monotonic() - started})
                    receipt["cleanup"] = {"status": "confirmed"}
                    receipt["scratch_cleanup"] = {"path": str(scratch_root),
                                                   "status": "retained-for-diagnostics",
                                                   "reason": "backend process could not be started"}
                    _atomic_json(receipt_path, receipt)
                    raise InvocationError(f"could not start {operation}: {error}", str(receipt_path)) from error
                pgid = child.pid
                receipt["process_group_id"] = pgid
                _atomic_json(receipt_path, receipt)
                previous_handlers = {}

                def cancel(signum, _frame):
                    raise KeyboardInterrupt(f"cancelled by signal {signum}")

                for signum in (signal.SIGINT, signal.SIGTERM):
                    try:
                        previous_handlers[signum] = signal.getsignal(signum)
                        signal.signal(signum, cancel)
                    except ValueError:  # non-main thread
                        previous_handlers = {}
                        break
                try:
                    outcome = "exit"
                    leader_state = _wait_child_unreaped(child, timeout)
                    if leader_state == "running":
                        outcome = "timeout"
                        receipt["timeout"] = True
                        cleanup_status = _cleanup_owned_group(child, pgid)
                        receipt["cleanup"] = {"status": cleanup_status,
                                               "term_grace_seconds": TERMINATE_GRACE_SECONDS,
                                               "kill_reap_seconds": KILL_REAP_SECONDS}
                    elif leader_state == "exited":
                        # Once the direct child exits normally, reap it and do
                        # not inspect or signal its now-reusable process group.
                        child.wait(timeout=0.1)
                        receipt["cleanup"] = {"status": "not-needed",
                                               "reason": "direct child exited normally; process group was not inspected"}
                    else:
                        outcome = "leader-state-" + leader_state
                        cleanup_status = _cleanup_owned_group(child, pgid)
                        receipt["cleanup"] = {"status": cleanup_status,
                                               "term_grace_seconds": TERMINATE_GRACE_SECONDS,
                                               "kill_reap_seconds": KILL_REAP_SECONDS,
                                               "reason": "could not safely determine direct-child exit state"}
                except KeyboardInterrupt as error:
                    outcome = "cancelled"
                    receipt["cancellation"] = str(error)
                    cleanup_status = _cleanup_owned_group(child, pgid)
                    receipt["cleanup"] = {"status": cleanup_status,
                                           "term_grace_seconds": TERMINATE_GRACE_SECONDS,
                                           "kill_reap_seconds": KILL_REAP_SECONDS}
                    if scratch_root.exists():
                        receipt["scratch_cleanup"] = {"path": str(scratch_root),
                                                      "status": "retained-for-diagnostics",
                                                      "reason": "invocation cancelled"}
                finally:
                    for signum, handler in previous_handlers.items():
                        signal.signal(signum, handler)
                return_code = child.returncode
                receipt.update({"return_code": return_code,
                                "signal": -return_code if return_code is not None and return_code < 0 else None,
                                "outcome": outcome, "finished_at": _utc_now(),
                                "elapsed_seconds": time.monotonic() - started})
                receipt["phases"] = _observed_phases(stdout_path)
                receipt["last_script_phase"] = receipt["phases"][-1].get("phase", "unknown") if receipt["phases"] else "unknown"
                if expected_outputs is not None and outcome == "exit" and return_code == 0:
                    receipt["output_validation"] = validate_outputs(output_specs)
                else:
                    receipt["output_validation"] = {"status": "not-run" if expected_outputs is not None else "not-required"}
                successful = (outcome == "exit" and return_code == 0
                              and receipt["cleanup"].get("status") != "cleanup_pending"
                              and receipt["output_validation"]["status"] in ("pass", "not-required"))
                if successful:
                    try:
                        if scratch_root.is_symlink() or not scratch_root.resolve().is_relative_to(receipt_path.parent):
                            raise ValueError(f"backend scratch changed ownership: {scratch_root}")
                        if scratch_root.exists():
                            shutil.rmtree(scratch_root)
                        receipt["scratch_cleanup"] = {"path": str(scratch_root),
                                                      "status": "removed-after-child-exit"}
                    except (OSError, ValueError) as error:
                        successful = False
                        receipt["outcome"] = "scratch-cleanup-failed"
                        receipt["error"] = str(error)
                        receipt["scratch_cleanup"] = {"path": str(scratch_root),
                                                      "status": "cleanup-pending",
                                                      "reason": str(error)}
                else:
                    receipt["scratch_cleanup"] = {"path": str(scratch_root),
                                                  "status": "retained-for-diagnostics",
                                                  "reason": f"{outcome}, return code {return_code}"}
                receipt["state"] = "succeeded" if successful else "failed"
                _atomic_json(receipt_path, receipt)
                if not successful:
                    raise InvocationError(f"{operation} failed ({outcome}, return code {return_code}); see {receipt_path}", str(receipt_path))
                return receipt
    except KeyboardInterrupt as error:
        cleanup_status = "confirmed"
        if child is not None:
            # start_new_session makes the child PID its PGID. Recover the
            # identity if cancellation arrived between spawn and assignment;
            # cleanup itself will refuse PGID work once the child is reaped.
            cleanup_status = _cleanup_owned_group(child, pgid if pgid is not None else child.pid)
        receipt.update({"state": "failed", "outcome": "cancelled", "cancellation": str(error),
                        "finished_at": _utc_now(), "elapsed_seconds": time.monotonic() - started,
                        "cleanup": {"status": cleanup_status,
                                    "term_grace_seconds": TERMINATE_GRACE_SECONDS,
                                    "kill_reap_seconds": KILL_REAP_SECONDS},
                        "return_code": child.returncode if child is not None else None})
        if scratch_root.exists():
            receipt["scratch_cleanup"] = {"path": str(scratch_root),
                                          "status": "retained-for-diagnostics",
                                          "reason": "invocation cancelled"}
        receipt["phases"] = _observed_phases(stdout_path)
        receipt["last_script_phase"] = receipt["phases"][-1].get("phase", "unknown") if receipt["phases"] else "unknown"
        _atomic_json(receipt_path, receipt)
        raise InvocationError(f"{operation} cancelled; see {receipt_path}", str(receipt_path)) from error
    except SlotTimeout as error:
        receipt.update({"state": "failed", "outcome": "contention", "error": str(error),
                        "finished_at": _utc_now(), "elapsed_seconds": time.monotonic() - started})
        if scratch_root.exists():
            receipt["scratch_cleanup"] = {"path": str(scratch_root),
                                          "status": "retained-for-diagnostics",
                                          "reason": "backend slot was not acquired"}
        _atomic_json(receipt_path, receipt)
        raise InvocationError(str(error), str(receipt_path)) from error
    except InvocationError as error:
        if receipt.get("state") == "running":
            receipt.update({"state": "failed", "outcome": "ownership_blocked", "error": str(error),
                            "finished_at": _utc_now(), "elapsed_seconds": time.monotonic() - started})
            if scratch_root.exists():
                receipt["scratch_cleanup"] = {"path": str(scratch_root),
                                              "status": "retained-for-diagnostics",
                                              "reason": str(error)}
            _atomic_json(receipt_path, receipt)
            raise InvocationError(str(error), str(receipt_path)) from error
        raise
    finally:
        for signum, handler in outer_handlers.items():
            signal.signal(signum, handler)


def validate_outputs(paths):
    """Validate fresh nonempty files and record their hashes."""
    checked = []
    for item in paths:
        spec = item if isinstance(item, dict) else {"path": Path(item), "allow_existing_sha256": None}
        path = Path(spec["path"])
        if not path.is_file() or path.stat().st_size == 0:
            return {"status": "fail", "reason": f"missing-or-empty:{path}"}
        digest = file_sha256(path)
        allowed = spec.get("allow_existing_sha256")
        if allowed is not None and digest != allowed:
            return {"status": "fail", "reason": f"input-identity-changed:{path}"}
        checked.append({"path": str(path.resolve()), "size_bytes": path.stat().st_size, "sha256": digest})
    return {"status": "pass", "files": checked}


def _inspect_blender_output(stdout):
    version = re.search(r"^Blender (.+)$", stdout, re.M)
    build_hash = re.search(r"build hash:\s*(\S+)", stdout)
    if version is None or build_hash is None:
        raise ValueError("Cannot identify Blender version/build from --version output")
    check_blender_version(version.group(1).strip(), build_hash.group(1))
    return {"version": version.group(1).strip(), "build_hash": build_hash.group(1)}


def inspect_blender(run_root=None, *, timeout_seconds=DEFAULT_PROBE_TIMEOUT,
                    slot_timeout_seconds=DEFAULT_SLOT_TIMEOUT, workspace=None, owner_run=None):
    """Resolve Blender through PATH, then probe it under the shared supervisor."""
    if run_root is None:
        raise ValueError("inspect_blender requires an owning run_root for durable evidence")
    discovered = shutil.which("blender")
    executable = str(Path(discovered).resolve()) if discovered else "blender"
    receipt = invocation([executable, "--version"], run_root=run_root, operation="version-probe",
                         cwd=workspace_root(workspace), timeout_seconds=timeout_seconds,
                         slot_timeout_seconds=slot_timeout_seconds, workspace=workspace,
                         owner_run=owner_run)
    stdout = Path(receipt["stdout_log"]).read_text(errors="replace")
    try:
        identity = _inspect_blender_output(stdout)
    except ValueError as error:
        receipt.update({"state": "failed", "outcome": "identity_error", "error": str(error),
                        "finished_at": _utc_now()})
        _atomic_json(Path(receipt["stdout_log"]).parent / "outcome.json", receipt)
        raise InvocationError(str(error), str(Path(receipt["stdout_log"]).parent / "outcome.json")) from error
    receipt["backend_identity"] = identity
    _atomic_json(Path(receipt["stdout_log"]).parent / "outcome.json", receipt)
    return identity | {"platform": platform.system() + "-" + platform.machine(),
                      "invocation_id": receipt["invocation_id"], "receipt": receipt}
