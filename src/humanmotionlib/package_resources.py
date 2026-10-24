# SPDX-License-Identifier: Apache-2.0
"""Access and verify immutable resources supplied by the HML distribution."""

from __future__ import annotations

import hashlib
import json
from importlib.resources import files
from pathlib import PurePosixPath


_RESOURCE_ROOT = files("humanmotionlib").joinpath("resources")
_MANIFEST_NAME = "runtime-manifest.json"
_FORMAT = "humanmotionlib-runtime-manifest/v1"


class PackageResourceError(ValueError):
    """A required package resource is absent, corrupt, or unsupported."""


def _logical_name(name: str) -> str:
    path = PurePosixPath(name)
    if path.is_absolute() or not path.parts or any(part in ("", ".", "..") for part in path.parts):
        raise PackageResourceError(f"Invalid package resource name: {name!r}")
    return path.as_posix()


def read_bytes(name: str) -> bytes:
    """Read one allowlisted resource, rejecting absent or modified bytes."""
    logical = _logical_name(name)
    try:
        payload = _RESOURCE_ROOT.joinpath(*PurePosixPath(logical).parts).read_bytes()
    except (FileNotFoundError, OSError) as error:
        raise PackageResourceError(f"Required HML package resource is missing: {logical}") from error
    manifest = runtime_manifest()
    expected = manifest["resources"].get(logical)
    if logical == "backend-contract.json":
        expected = manifest["backend_contract"]
    if expected is None:
        raise PackageResourceError(f"Resource is not declared by the HML runtime manifest: {logical}")
    actual = hashlib.sha256(payload).hexdigest()
    if actual != expected:
        raise PackageResourceError(f"HML package resource is corrupt: {logical}")
    return payload


def read_text(name: str, encoding: str = "utf-8") -> str:
    return read_bytes(name).decode(encoding)


def runtime_manifest() -> dict:
    """Load the packaged manifest and verify its canonical structure."""
    try:
        raw = _RESOURCE_ROOT.joinpath(_MANIFEST_NAME).read_bytes()
        manifest = json.loads(raw)
    except (OSError, json.JSONDecodeError) as error:
        raise PackageResourceError("HML runtime manifest is missing or invalid") from error
    if not isinstance(manifest, dict) or manifest.get("format") != _FORMAT:
        raise PackageResourceError("Unsupported HML runtime manifest format")
    for field in ("version", "resources", "backend_contract", "implementation"):
        if field not in manifest:
            raise PackageResourceError(f"HML runtime manifest is missing {field}")
    if not isinstance(manifest["resources"], dict) or not isinstance(manifest["implementation"], dict):
        raise PackageResourceError("HML runtime manifest inventory is invalid")
    return manifest


def manifest_sha256() -> str:
    try:
        payload = _RESOURCE_ROOT.joinpath(_MANIFEST_NAME).read_bytes()
    except OSError as error:
        raise PackageResourceError("HML runtime manifest is missing") from error
    return hashlib.sha256(payload).hexdigest()


def verify_runtime_integrity() -> dict:
    """Verify every declared resource, implementation module and backend contract."""
    manifest = runtime_manifest()
    from humanmotionlib import __version__
    if manifest["version"] != __version__:
        raise PackageResourceError("HML runtime manifest and package version disagree")
    for logical, expected in sorted(manifest["resources"].items()):
        path = PurePosixPath(_logical_name(logical))
        try:
            data = _RESOURCE_ROOT.joinpath(*path.parts).read_bytes()
        except (OSError, ValueError) as error:
            raise PackageResourceError(f"Required HML package resource is missing: {logical}") from error
        if hashlib.sha256(data).hexdigest() != expected:
            raise PackageResourceError(f"HML package resource is corrupt: {logical}")
    contract = _RESOURCE_ROOT.joinpath("backend-contract.json").read_bytes()
    if hashlib.sha256(contract).hexdigest() != manifest["backend_contract"]:
        raise PackageResourceError("HML backend contract does not match its runtime manifest")
    package_root = files("humanmotionlib")
    for relative, expected in sorted(manifest["implementation"].items()):
        prefix = "humanmotionlib/"
        if not relative.startswith(prefix) or relative.endswith("/"):
            raise PackageResourceError(f"Invalid implementation path in runtime manifest: {relative}")
        parts = PurePosixPath(relative[len(prefix):]).parts
        try:
            data = package_root.joinpath(*parts).read_bytes()
        except (OSError, ValueError) as error:
            raise PackageResourceError(f"Packaged implementation module is missing: {relative}") from error
        if hashlib.sha256(data).hexdigest() != expected:
            raise PackageResourceError(f"Packaged implementation module is corrupt: {relative}")
    return manifest


def resource_path(name: str):
    """Return a Traversable for a declared resource (not a writable path)."""
    logical = _logical_name(name)
    read_bytes(logical)
    return _RESOURCE_ROOT.joinpath(*PurePosixPath(logical).parts)

