# SPDX-License-Identifier: Apache-2.0
"""Deterministic, finite JSON interchange; independent input-integrity checks."""

from copy import deepcopy
from fractions import Fraction
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


def _read_prepared_integrity(path, check_sources=True, expected_sha256=None):
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
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError("Prepared input differs from the host-validated identity")
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
    if "consumer_motion" in value:
        _verify_consumer_integrity(value)
    return value


def _verify_consumer_integrity(value):
    """Check consumer snapshot hashes and references using only the stdlib."""
    snapshot = value["consumer_motion"]
    if not isinstance(snapshot, dict) or snapshot.get("format") != "hml-consumer-motion-snapshot/v1":
        raise ValueError("Unsupported consumer snapshot format")
    if content_hash(snapshot.get("document")) != snapshot.get("source_sha256"):
        raise ValueError("Consumer source snapshot hash mismatch")
    if content_hash(snapshot.get("resolved_definition")) != snapshot.get("resolved_sha256"):
        raise ValueError("Consumer resolved source hash mismatch")
    source_hashes = value.get("source_hashes", {})
    lineage = snapshot.get("base_lineage")
    if not isinstance(lineage, list) or not lineage:
        raise ValueError("Consumer base lineage is missing")
    logical_paths = []
    for item in lineage:
        if not isinstance(item, dict) or set(item) != {"id", "logical_path", "raw_sha256"}:
            raise ValueError("Consumer base lineage entry is malformed")
        logical = item["logical_path"]
        if item["id"] not in logical or logical != f"rig/diagnostics/{item['id']}.yaml":
            raise ValueError("Consumer base lineage identity/path mismatch")
        logical_paths.append(logical)
        if source_hashes.get(logical) != item["raw_sha256"]:
            raise ValueError("Consumer base lineage source hash mismatch: " + str(logical))
    if logical_paths != sorted(set(logical_paths)):
        raise ValueError("Consumer base lineage paths are not sorted and unique")
    sampling = value.get("sampling", {})
    if len(sampling) != 1:
        raise ValueError("Consumer preparation must contain exactly one movement")
    motion_id = next(iter(sampling))
    document = snapshot["document"]
    motion = document.get("motion") if isinstance(document, dict) else None
    source_id = (motion.get("id") if isinstance(motion, dict) else None) or snapshot["resolved_definition"].get("id")
    if motion_id != source_id:
        raise ValueError("Consumer identifier does not match prepared sample joins")
    samples = value.get("samples", [])
    if {sample.get("fixture") for sample in samples} != {motion_id}:
        raise ValueError("Consumer sample references do not match its prepared movement")
    if snapshot.get("validation", {}).get("delivered_samples") != len(samples):
        raise ValueError("Consumer delivered-sample count does not match prepared sample inventory")
    def sample_beat(sample):
        beat = sample.get("beat")
        if not isinstance(beat, dict) or set(beat) != {"numerator", "denominator"}:
            raise ValueError("Consumer sample beat is malformed")
        return Fraction(beat["numerator"], beat["denominator"])

    ordered = sorted(samples, key=sample_beat)
    sample_by_id = {sample.get("id"): sample for sample in samples}
    expected_references = set()
    for index, sample in enumerate(ordered):
        expected_id = f"{motion_id}/{index:05d}"
        if sample.get("id") != expected_id or sample.get("frame_id") != index:
            raise ValueError("Consumer sample IDs/frame indices do not match ordered timeline")
    for plans in sampling.values():
        for plan in plans:
            for mode in ("static", "animation"):
                records = plan.get(mode)
                if not isinstance(records, list):
                    raise ValueError("Consumer sampling timeline is malformed")
                for record in records:
                    sample_id = record.get("sample_id")
                    sample = sample_by_id.get(sample_id)
                    if sample is None or sample.get("beat") != record.get("beat"):
                        raise ValueError("Consumer sampling timeline has a dangling sample reference")
                    expected_references.add(sample_id)
    if expected_references != set(sample_by_id):
        raise ValueError("Consumer sampling timeline does not cover the prepared sample inventory")


def read_prepared(path,check_sources=True):
    """Read prepared JSON and perform full host validation for consumer sources."""
    value = _read_prepared_integrity(path, check_sources=check_sources)
    if "consumer_motion" in value:
        from humanmotionlib.consumer_prepared_validation import verify_consumer_prepared
        verify_consumer_prepared(value)
    return value


def read_prepared_backend(path, expected_sha256):
    """Read backend input without host YAML/schema dependencies, bound to host identity."""
    if (not isinstance(expected_sha256, str) or len(expected_sha256) != 64 or
            any(character not in "0123456789abcdef" for character in expected_sha256)):
        raise ValueError("A host-validated prepared identity is required")
    return _read_prepared_integrity(path, expected_sha256=expected_sha256)
