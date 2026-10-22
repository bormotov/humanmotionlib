# SPDX-License-Identifier: Apache-2.0
"""Deterministic, finite JSON interchange; independent input-integrity checks."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from tools.runtime import project_root
from tools.finite import require_finite


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
        root = project_root()
        for name,expected in value["source_hashes"].items():
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts: raise ValueError("Non-project source path")
            path = root/relative
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError("Source/schema hash mismatch: "+name)
    ids = [s["id"] for s in value["samples"]]
    if ids != sorted(set(ids)): raise ValueError("Prepared sample IDs are not sorted and unique")
    bodies = {b["id"] for b in value["sources"]["profile"]["structures"]}
    for sample in value["samples"]:
        if set(sample["frames"]) != bodies: raise ValueError("Prepared body inventory mismatch")
    return value
