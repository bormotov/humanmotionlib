# SPDX-License-Identifier: Apache-2.0
"""Shared backend identity checks and bounded, auditable process execution."""

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
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


class InvocationError(RuntimeError):
    """A failed invocation with its durable receipt attached."""

    def __init__(self, message, receipt):
        super().__init__(message)
        self.receipt = receipt


class SlotTimeout(TimeoutError):
    """The checkout's backend slot was not available before its deadline."""


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
    """Validate the two fixed render-pass directories owned by a pack run."""
    owner = validate_run_root(owner_run, workspace)
    if not owner.is_dir():
        raise ValueError(f"managed render pass owner must be an existing run directory: {owner}")
    path = resolve_workspace_path(pass_root, workspace)
    if path.parent != owner or path.name not in {"clean-a", "clean-b"}:
        raise ValueError(f"managed render pass must be clean-a or clean-b directly inside its owner: {path}")
    return path


def validate_operation_root(run_root, workspace, owner_run=None):
    """Validate a standalone run or an explicitly owned internal render pass."""
    if owner_run is None:
        return validate_run_root(run_root, workspace)
    return validate_managed_pass_root(run_root, owner_run, workspace)


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
    # Darwin's reference Python omits waitid and killpg can return EPERM for
    # zombie-only groups. On Linux, waitid(WNOWAIT) leaves the leader zombie
    # as the PGID anchor, so killpg alone would report an empty group present.
    # A bounded process-table snapshot distinguishes zombies from live work on
    # both systems while preserving the unreaped anchor until cleanup is safe.
    if platform.system() in ("Darwin", "Linux"):
        ps_executable = next((path for path in ("/bin/ps", "/usr/bin/ps")
                              if Path(path).is_file()), None)
        if ps_executable is None:
            return "ambiguous"
        try:
            listing = subprocess.run([ps_executable, "-Ao", "pid=,pgid=,stat="], check=True,
                                     capture_output=True, text=True, timeout=max(0.01, ps_timeout))
        except (OSError, subprocess.SubprocessError):
            return "ambiguous"
        entries = []
        try:
            for line in listing.stdout.splitlines():
                if not line.strip():
                    continue
                fields = line.split()
                if len(fields) != 3:
                    return "ambiguous"
                pid, group, process_state = int(fields[0]), int(fields[1]), fields[2]
                if group == int(pgid):
                    entries.append((pid, process_state))
        except (TypeError, ValueError):
            return "ambiguous"
        if entries:
            if anchor_pid is not None and not any(pid == int(anchor_pid) for pid, _ in entries):
                return "ambiguous"
            if all(process_state.startswith("Z") for _, process_state in entries):
                return "absent"
            return "present"
        if anchor_pid is not None:
            return "ambiguous"
        # A complete readable snapshot with no group entry is only accepted
        # when the kernel independently confirms ESRCH. EPERM stays unknown.
        return "absent" if _raw_group_state(pgid) == "absent" else "ambiguous"

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


def _wait_group_absent(pgid, deadline, *, anchor_pid=None):
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        state = _group_state(pgid, anchor_pid=anchor_pid, ps_timeout=min(0.2, remaining))
        if state != "present":
            return state
        remaining = deadline - time.monotonic()
        time.sleep(min(0.05, max(0.0, remaining)))
    return "present"


def _wait_child_unreaped(child, pgid, timeout):
    """Wait for leader exit without releasing its process-group identity anchor."""
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return "running"
        if hasattr(os, "waitid"):
            result = os.waitid(os.P_PID, child.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
            if result is not None and result.si_pid:
                return "exited"
        elif platform.system() == "Darwin":
            # The reference Python build omits os.waitid despite the OS libc
            # providing the operation. Observe the owned leader's zombie state
            # without reaping it; its PID continues to anchor the process group.
            try:
                status = subprocess.run(["/bin/ps", "-o", "pid=,pgid=,stat=", "-p", str(child.pid)],
                                        check=True, capture_output=True, text=True,
                                        timeout=max(0.01, min(0.2, remaining)))
            except (OSError, subprocess.SubprocessError):
                return "ambiguous"
            fields = status.stdout.split()
            if len(fields) != 3 or fields[0] != str(child.pid) or fields[1] != str(pgid):
                return "ambiguous"
            process_state = fields[2]
            if process_state.startswith("Z"):
                return "exited"
            if not process_state:
                return "ambiguous"
        else:
            return "unsupported"
        time.sleep(min(0.02, remaining))


def _cleanup_owned_group(child, pgid):
    """Terminate one owned group within fixed grace and reap budgets.

    Keep the unreaped direct child as a PGID identity anchor until all signals
    are sent. Reap it with the remaining kill budget, then confirm no live
    descendants remain before releasing the checkout slot.
    """
    _signal_group(pgid, signal.SIGTERM)
    term_deadline = time.monotonic() + TERMINATE_GRACE_SECONDS
    group_state = _wait_group_absent(pgid, term_deadline, anchor_pid=child.pid)
    kill_deadline = time.monotonic() + KILL_REAP_SECONDS
    if group_state != "absent":
        _signal_group(pgid, signal.SIGKILL)
    try:
        child.wait(timeout=max(0.0, kill_deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        return "cleanup_pending"
    group_state = _wait_group_absent(pgid, kill_deadline)
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


def _slot_paths(workspace=None):
    build = _build_root(workspace)
    return build / ".backend-execution.lock", build / ".backend-execution-state.json"


@contextmanager
def backend_slot(timeout_seconds=DEFAULT_SLOT_TIMEOUT, *, operation_id=None, workspace=None):
    """Hold the selected workspace slot; never unlink its persistent lock file."""
    timeout = validate_timeout(timeout_seconds, "slot_timeout_seconds")
    root = workspace_root(workspace)
    ensure_workspace_build(root)
    lock_path, state_path = _slot_paths(workspace)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if lock_path.is_symlink() or state_path.is_symlink():
        raise InvocationError("backend ownership files may not be symlinks", str(lock_path))
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    start = time.monotonic()
    acquired = False
    try:
        while not acquired:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except BlockingIOError:
                if time.monotonic() - start >= timeout:
                    raise SlotTimeout(f"backend slot contention after {timeout:g} seconds")
                time.sleep(min(0.05, timeout - (time.monotonic() - start)))
        if state_path.exists():
            try:
                state = json.loads(state_path.read_text())
            except (OSError, json.JSONDecodeError) as error:
                raise InvocationError("backend ownership state is unreadable; operator resolution required", str(state_path)) from error
            if state.get("state") == "preparing":
                raise InvocationError("backend ownership is ambiguous before child identity was recorded; operator resolution required", str(state_path))
            if state.get("state") == "running":
                pgid = state.get("process_group_id")
                group_state = _group_state(pgid)
                if group_state == "ambiguous":
                    raise InvocationError("backend ownership is ambiguous; operator resolution required", str(state_path))
                if group_state == "present":
                    while group_state == "present" and time.monotonic() - start < timeout:
                        time.sleep(min(0.05, timeout - (time.monotonic() - start)))
                        group_state = _group_state(pgid)
                    if group_state == "present":
                        raise SlotTimeout(f"unfinished backend owner still has process group {pgid}")
                    if group_state == "ambiguous":
                        raise InvocationError("backend ownership became ambiguous; operator resolution required", str(state_path))
                state.update({"state": "interrupted", "recovery": "previous process group confirmed absent", "recovered_at": _utc_now()})
                _atomic_json(state_path, state)
        yield
    finally:
        if acquired:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


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
    wait_anchor_supported = (hasattr(os, "waitid") and
                             all(hasattr(os, item) for item in ("P_PID", "WEXITED", "WNOHANG", "WNOWAIT")))
    wait_anchor_supported = wait_anchor_supported or (platform.system() == "Darwin" and Path("/bin/ps").is_file())
    if os.name != "posix" or not hasattr(os, "killpg") or not hasattr(fcntl, "flock") or not wait_anchor_supported:
        raise RuntimeError("supervised backend execution requires POSIX process groups and advisory file locks")
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
            _atomic_json(_slot_paths(workspace)[1], {"state": "preparing", "invocation_id": operation_id,
                                            "operation": operation, "updated_at": _utc_now()})
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
                    _atomic_json(_slot_paths(workspace)[1], {"state": "finished", "invocation_id": operation_id,
                                                    "updated_at": _utc_now()})
                    raise InvocationError(f"could not start {operation}: {error}", str(receipt_path)) from error
                pgid = child.pid
                receipt["process_group_id"] = pgid
                _atomic_json(_slot_paths(workspace)[1], {"state": "running", "invocation_id": operation_id,
                                                "process_group_id": pgid, "updated_at": _utc_now()})
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
                    leader_state = _wait_child_unreaped(child, pgid, timeout)
                    if leader_state == "running":
                        outcome = "timeout"
                        receipt["timeout"] = True
                        cleanup_status = _cleanup_owned_group(child, pgid)
                        receipt["cleanup"] = {"status": cleanup_status,
                                               "term_grace_seconds": TERMINATE_GRACE_SECONDS,
                                               "kill_reap_seconds": KILL_REAP_SECONDS}
                    elif leader_state == "exited":
                        group_state = _group_state(pgid, anchor_pid=child.pid)
                        if group_state != "absent":
                            outcome = "orphaned-descendant"
                            cleanup_status = _cleanup_owned_group(child, pgid)
                            receipt["cleanup"] = {"status": cleanup_status,
                                                   "term_grace_seconds": TERMINATE_GRACE_SECONDS,
                                                   "kill_reap_seconds": KILL_REAP_SECONDS,
                                                   "reason": "owned process group remained after direct child exit",
                                                   "initial_group_state": group_state}
                        else:
                            # The unreaped leader remains the PGID identity
                            # anchor until no live group members remain.
                            child.wait(timeout=0.1)
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
                slot_state = {"state": "finished", "invocation_id": operation_id,
                              "updated_at": _utc_now()}
                if receipt["cleanup"].get("status") == "cleanup_pending":
                    slot_state.update({"state": "running", "process_group_id": pgid,
                                       "cleanup_pending": True,
                                       "updated_at": _utc_now()})
                _atomic_json(_slot_paths(workspace)[1], slot_state)
                if not successful:
                    raise InvocationError(f"{operation} failed ({outcome}, return code {return_code}); see {receipt_path}", str(receipt_path))
                return receipt
    except KeyboardInterrupt as error:
        cleanup_status = "confirmed"
        if child is not None and pgid is not None:
            cleanup_status = _cleanup_owned_group(child, pgid)
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
        # If cancellation interrupted setup after spawn, retain running ownership
        # until the next caller confirms this exact group is absent. Never touch
        # a state record that now belongs to another invocation.
        if pgid is not None and cleanup_status == "confirmed":
            try:
                with backend_slot(slot_timeout, operation_id=operation_id, workspace=workspace):
                    state_path = _slot_paths(workspace)[1]
                    state = json.loads(state_path.read_text())
                    if state.get("invocation_id") == operation_id:
                        _atomic_json(state_path, {"state": "finished", "invocation_id": operation_id,
                                                  "updated_at": _utc_now()})
            except (SlotTimeout, InvocationError, OSError, json.JSONDecodeError):
                pass
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
