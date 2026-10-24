# SPDX-License-Identifier: Apache-2.0
"""Deterministic, finite JSON interchange; independent input-integrity checks."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from humanmotionlib.finite import require_finite
from humanmotionlib.package_resources import (PackageResourceError, manifest_sha256,
                                             read_bytes, verify_runtime_integrity)


def canonical_bytes(value):
    require_finite(value)
    return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False,ensure_ascii=False)+"\n").encode()


def content_hash(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def write_json(path,value):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def seal(payload):
    value = deepcopy(payload)
    value.pop("content_sha256",None)
    return value|{"content_sha256":content_hash(value)}


def read_prepared(path,check_sources=True):
    def unique(pairs):
        result = {}
        for key,value in pairs:
            if key in result: raise ValueError("Duplicate JSON key: "+key)
            result[key] = value
        return result
    value = json.loads(Path(path).read_text(),object_pairs_hook=unique)
    require_finite(value)
    digest = value.pop("content_sha256",None)
    if digest != content_hash(value): raise ValueError("Prepared content hash mismatch")
    value["content_sha256"] = digest
    if value.get("format") != "skeleton-prepared/v1": raise ValueError("Unsupported prepared format")
    if not value.get("samples"): raise ValueError("Missing prepared samples")
    if not value.get("source_hashes"): raise ValueError("Missing source/schema hashes")
    if check_sources:
        identity = value.get("package_identity")
        if not isinstance(identity, dict):
            raise ValueError("Prepared input belongs to a checkout-bound legacy package; regenerate it with the installed HML release")
        try:
            manifest = verify_runtime_integrity()
            if identity.get("version") != manifest["version"] or identity.get("manifest_sha256") != manifest_sha256():
                raise ValueError("Prepared input package release/resource identity mismatch; regenerate the prepared input")
            if identity.get("implementation") != manifest["implementation"]:
                raise ValueError("Prepared input implementation identity mismatch; regenerate the prepared input")
            for name, expected in value["source_hashes"].items():
                if Path(name).is_absolute() or ".." in Path(name).parts:
                    raise ValueError("Prepared input contains a non-logical package resource key; regenerate it")
                try:
                    actual = hashlib.sha256(read_bytes(name)).hexdigest()
                except PackageResourceError as error:
                    raise ValueError(f"Prepared input references an unavailable package resource {name}; regenerate it") from error
                if actual != expected:
                    raise ValueError("Source/schema hash mismatch: "+name+"; regenerate the prepared input")
        except PackageResourceError as error:
            raise ValueError("Installed HML package integrity check failed: "+str(error)) from error
    ids = [s["id"] for s in value["samples"]]
    if ids != sorted(set(ids)): raise ValueError("Prepared sample IDs are not sorted and unique")
    bodies = {b["id"] for b in value["sources"]["profile"]["structures"]}
    for sample in value["samples"]:
        if set(sample["frames"]) != bodies: raise ValueError("Prepared body inventory mismatch")
    return value
