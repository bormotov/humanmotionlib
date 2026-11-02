# SPDX-License-Identifier: Apache-2.0
"""Synchronous API for packaged diagnostics and bounded consumer motions.

Consumer inputs use the installed skeleton-diagnostic action contract; this is
not a general pose or composition language. Blender is an external, pinned
backend used only by :func:`render`.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from humanmotionlib import prepare_skeleton, run_blender
from humanmotionlib.package_resources import PackageResourceError, read_bytes, read_text
from humanmotionlib.prepared import canonical_bytes, content_hash, read_prepared, write_json
from humanmotionlib.runtime import (
    DEFAULT_BUILD_TIMEOUT,
    DEFAULT_SLOT_TIMEOUT,
    InvocationError,
    MATRIX_DESTINATIONS,
    SlotTimeout,
    ensure_workspace_build,
    resolve_workspace_path,
    validate_run_root,
    validate_managed_pass_root,
    validate_matrix_content_destination,
    validate_timeout,
    workspace_root,
)
from humanmotionlib.source_validation import SourceValidationError


def _matrix_destination(value: Mapping[str, Any] | None, *, operation: str,
                        output: str | Path, workspace: Path,
                        allowed_destinations: frozenset[str],
                        inputs: Sequence[str | Path] = ()) -> tuple[Path, Path] | None:
    """Validate an explicit stable matrix binding before any filesystem writes.

    Matrix authority is conveyed only by the structured binding; path spelling
    alone never relaxes the standalone fresh-run rules.
    """
    if value is None:
        return None
    if not isinstance(value, Mapping) or set(value) != {"element_root", "allowed_destinations"}:
        raise _RequestError("matrix_destination must contain element_root and allowed_destinations")
    declared = value["allowed_destinations"]
    if (isinstance(declared, (str, bytes)) or not isinstance(declared, Sequence)
            or not declared or len(set(declared)) != len(declared)
            or any(not isinstance(item, str) or item not in allowed_destinations for item in declared)):
        raise _RequestError(f"matrix_destination has an invalid {operation} destination allowlist")
    declared_set = frozenset(declared)

    try:
        element, destination, _relative_destination = validate_matrix_content_destination(
            output, value["element_root"], workspace, operation=operation,
            allowed_destinations=declared_set)
    except (TypeError, ValueError, OSError) as error:
        raise _RequestError(str(error)) from error
    for source in inputs:
        source_path = resolve_workspace_path(source, workspace)
        if source_path == destination or source_path in destination.parents or destination in source_path.parents:
            raise _RequestError("matrix output overlaps a protected input")
    # Existing element content is allowed for repeat runs, but every existing
    # component from the stable root to the declared output must be a real,
    # non-symlink directory/file path.
    return element, destination


def _plain(value: Any) -> Any:
    """Convert a result to a detached JSON-compatible tree."""
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _plain(getattr(value, field.name)) for field in fields(value)
                if not (field.name == "consumer_motion" and getattr(value, field.name) is None)}
    if isinstance(value, Path):
        return str(value.resolve())
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator}
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return deepcopy(value)


class _Record:
    def to_dict(self) -> dict[str, Any]:
        return _plain(self)


@dataclass(frozen=True)
class PoseSample(_Record):
    sample_id: str
    fixture_id: str
    beat: Fraction
    actions: Mapping[str, Any]
    fk_deltas: Mapping[str, Any]
    world_root: Mapping[str, Any]
    controls: tuple[str, ...]
    rest_policy: Mapping[str, Any]
    contacts: tuple[Mapping[str, Any], ...]


@dataclass(frozen=True)
class TimelineEntry(_Record):
    sample_id: str
    frame_index: int
    beat: Fraction
    seconds: Fraction


@dataclass(frozen=True)
class Timeline(_Record):
    fixture_id: str
    bpm: int | float
    mode: str
    entries: tuple[TimelineEntry, ...]


@dataclass(frozen=True)
class SourceProvenance(_Record):
    logical_path: str
    sha256: str
    license: str | None
    provenance: Mapping[str, Any] | None
    nested_provenance: Mapping[str, Mapping[str, Any]]


@dataclass(frozen=True)
class ProvenanceInfo(_Record):
    sources: tuple[SourceProvenance, ...]
    material_ids: tuple[str, ...]
    register_text: str
    licenses: Mapping[str, str]


@dataclass(frozen=True)
class PreparedResult(_Record):
    workspace: Path
    run_root: Path
    prepared_path: Path
    prepared_sha256: str
    profile_id: str
    stature_m: float
    package_identity: Mapping[str, Any]
    poses: tuple[PoseSample, ...]
    timelines: tuple[Timeline, ...]
    provenance: ProvenanceInfo
    units: Mapping[str, Any]
    limitations: tuple[str, ...]
    consumer_motion: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class RenderedImage(_Record):
    sample_id: str
    view: str
    path: Path
    character_id: str = "skeleton"


@dataclass(frozen=True)
class CharacterInfo(_Record):
    character_id: str
    renderer_kind: str
    profile_id: str
    template_id: str | None
    appearance_id: str | None
    source_hashes: Mapping[str, str]


@dataclass(frozen=True)
class CharacterArtifactSet(_Record):
    character_id: str
    artifacts: Mapping[str, Path]


@dataclass(frozen=True)
class GenerationResult(_Record):
    prepared: PreparedResult
    output_root: Path
    images: tuple[RenderedImage, ...]
    artifacts: Mapping[str, Path]
    receipt_path: Path
    backend_identity: Mapping[str, Any]
    numerical_acceptance: str
    visual_acceptance: str
    characters: tuple[CharacterInfo, ...] = ()
    character_artifacts: tuple[CharacterArtifactSet, ...] = ()
    character_provenance: Mapping[str, Any] | None = None
    render_identity: str | None = None


class GenerationError(RuntimeError):
    """Expected public-operation failure with stable code and evidence paths."""

    def __init__(self, code: str, operation: str, message: str, *,
                 run_root: Path | None = None, receipt_path: Path | None = None,
                 details: Mapping[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.operation = operation
        self.run_root = run_root
        self.receipt_path = receipt_path
        self.details = deepcopy(dict(details or {}))

    def to_dict(self) -> dict[str, Any]:
        return _plain({"code": self.code, "operation": self.operation,
                       "message": str(self), "run_root": self.run_root,
                       "receipt_path": self.receipt_path, "details": self.details})


class _RequestError(ValueError):
    """A rejected public argument or destination preflight."""


_LICENSE_RESOURCES = ("LICENSE-CODE", "LICENSE-DATA", "THIRD-PARTY-NOTICES.md")


def _fraction(value: Mapping[str, Any]) -> Fraction:
    return Fraction(value["numerator"], value["denominator"])


def _unique_json(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _records_with_provenance(value: Any, prefix: str = "") -> dict[str, Mapping[str, Any]]:
    found: dict[str, Mapping[str, Any]] = {}
    if isinstance(value, dict):
        if isinstance(value.get("provenance"), dict):
            found[prefix or "/"] = deepcopy(value["provenance"])
        for key, child in value.items():
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            found.update(_records_with_provenance(child, prefix + "/" + escaped))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.update(_records_with_provenance(child, prefix + "/" + str(index)))
    return found


def _material_ids(value: Any) -> set[str]:
    result: set[str] = set()
    if isinstance(value, dict):
        if isinstance(value.get("sources"), list):
            for source in value["sources"]:
                if isinstance(source, dict) and isinstance(source.get("material"), str):
                    result.add(source["material"])
        for child in value.values():
            result.update(_material_ids(child))
    elif isinstance(value, list):
        for child in value:
            result.update(_material_ids(child))
    return result


def _source_documents(prepared: Mapping[str, Any]) -> dict[str, Any]:
    sources = prepared["sources"]
    documents = {
        "profile": sources["profile"], "mobility": sources["mobility"],
        "body-groups": sources["body-groups"], "humanoid-map": sources["humanoid-map"],
        "review-scene": sources["review-scene"],
    }
    for fixture in sources["diagnostics"]:
        documents[f"rig/diagnostics/{fixture['id']}.yaml"] = fixture
    return documents


def _provenance(prepared: Mapping[str, Any]) -> ProvenanceInfo:
    from humanmotionlib.validate import load_yaml_text

    docs = _source_documents(prepared)
    source_records: list[SourceProvenance] = []
    materials: set[str] = set()
    for logical, digest in sorted(prepared["source_hashes"].items()):
        # Character sources are rendered dependencies, not preparation inputs.
        # Their bytes are covered by the package manifest and per-character
        # closure; parsing them here would make skeleton preparation depend on
        # surface templates.
        if logical.startswith("characters/"):
            continue
        document_key = logical
        if logical.startswith("rig/profiles/"):
            document_key = "profile"
        elif logical.startswith("rig/mobility/"):
            document_key = "mobility"
        elif logical == "rig/body-groups.yaml":
            document_key = "body-groups"
        elif logical == "rig/humanoid-map.yaml":
            document_key = "humanoid-map"
        elif logical == "scenes/skeleton-review.yaml":
            document_key = "review-scene"
        document = docs.get(document_key)
        # Hashes and provenance describe packaged source bytes, not scaled copies.
        raw = read_bytes(logical)
        parsed = document
        if logical.endswith((".yaml", ".yml")):
            parsed = load_yaml_text(raw.decode("utf-8"), logical)
        nested = _records_with_provenance(parsed) if parsed is not None else {}
        root_provenance = parsed.get("provenance") if isinstance(parsed, dict) else None
        root_license = root_provenance.get("license") if isinstance(root_provenance, dict) else None
        source_records.append(SourceProvenance(
            logical_path=logical, sha256=digest, license=root_license,
            provenance=deepcopy(root_provenance) if isinstance(root_provenance, dict) else None,
            nested_provenance=nested,
        ))
        materials.update(_material_ids(parsed))
    consumer = prepared.get("consumer_motion")
    register = read_text("docs/used-materials.md")
    if consumer is not None:
        submitted = consumer["document"]
        resolved = consumer["resolved_definition"]
        for label, digest, source in (
            ("submitted", consumer["source_sha256"], submitted["motion"]),
            ("resolved", consumer["resolved_sha256"], resolved),
        ):
            root_provenance = deepcopy(source.get("provenance"))
            nested = _records_with_provenance(source)
            source_records.append(SourceProvenance(
                logical_path=f"consumer/{source['id']}/{label}", sha256=digest,
                license=source.get("license"), provenance=root_provenance,
                nested_provenance=nested,
            ))
        materials.update(_material_ids(submitted))
        clearances = submitted.get("materials", [])
        if clearances:
            register += "\n\n## Consumer-supplied clearance declarations\n\n"
            register += "| Identifier | Material / part | Source URL | License / terms URL | Permission basis | Conditions | Attribution | Checked on | Related outputs |\n"
            register += "|---|---|---|---|---|---|---|---|---|\n"
            for entry in clearances:
                row = [entry["id"], entry["material"] + ": " + entry["part_used"],
                       entry["source_url"], entry["license"] + ": " + entry["license_url"],
                       entry["permission_basis"], entry["conditions"], entry["attribution"],
                       entry["checked_on"], ", ".join(entry["related_outputs"])]
                register += "| " + " | ".join(value.replace("|", "\\|").replace("\n", " ") for value in row) + " |\n"
    licenses = {name: read_text(name) for name in _LICENSE_RESOURCES}
    return ProvenanceInfo(tuple(source_records), tuple(sorted(materials)),
                          register, licenses)


def _project(prepared: Mapping[str, Any], workspace: Path, prepared_path: Path) -> PreparedResult:
    fixtures = {item["id"]: item for item in prepared["sources"]["diagnostics"]}
    pose_by_id: dict[str, PoseSample] = {}
    poses: list[PoseSample] = []
    for sample in prepared["samples"]:
        fixture = fixtures[sample["fixture"]]
        pose = PoseSample(
            sample_id=sample["id"], fixture_id=sample["fixture"], beat=_fraction(sample["beat"]),
            actions=deepcopy(sample["expected_actions"]), fk_deltas=deepcopy(sample["fk_deltas"]),
            world_root=deepcopy(sample["world_root"]), controls=tuple(fixture["controls"]),
            rest_policy=deepcopy(fixture["rest_policy"]), contacts=tuple(deepcopy(sample["contacts"])),
        )
        pose_by_id[pose.sample_id] = pose
        poses.append(pose)
    requested_bpms = list(prepared["sampling"].values())
    # Preserve the caller's requested order as stored by the source preparation plans.
    bpm_order: list[int | float] = []
    if requested_bpms:
        for plan in next(iter(requested_bpms)):
            bpm_order.append(plan["bpm"])
    timelines: list[Timeline] = []
    for fixture_id in sorted(prepared["sampling"]):
        for bpm in bpm_order:
            plan = next(plan for plan in prepared["sampling"][fixture_id] if plan["bpm"] == bpm)
            for mode in ("static", "animation"):
                entries = tuple(TimelineEntry(
                    sample_id=record["sample_id"], frame_index=record["frame_id"],
                    beat=_fraction(record["beat"]), seconds=_fraction(record["seconds"]),
                ) for record in plan[mode])
                timelines.append(Timeline(fixture_id, bpm, mode, entries))
    package_identity = deepcopy(prepared["package_identity"])
    return PreparedResult(
        workspace=workspace, run_root=prepared_path.parent.resolve(), prepared_path=prepared_path.resolve(),
        prepared_sha256=prepared["content_sha256"], profile_id=prepared["sources"]["profile"]["id"],
        stature_m=prepared["sources"]["profile"]["stature_m"], package_identity=package_identity,
        poses=tuple(poses), timelines=tuple(timelines), provenance=_provenance(prepared),
        units=deepcopy(prepared["units"]), limitations=tuple(prepared["limitations"]),
        consumer_motion=deepcopy(prepared["consumer_motion"]) if "consumer_motion" in prepared else None,
    )


def _validate_selection(value: Any, name: str, *, allow_none: bool = False) -> list[Any] | None:
    if value is None and allow_none:
        return None
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{name} must be a nonempty sequence")
    result = list(value)
    if not result:
        raise ValueError(f"{name} must not be empty")
    return result


def _positive_number(value: Any, name: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite positive number")
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive number")
    return value


def _translate_error(error: Exception, operation: str, run_root: Path | None = None) -> GenerationError:
    receipt_path: Path | None = None
    details: dict[str, Any] = {}
    if isinstance(error, InvocationError):
        candidate = Path(error.receipt) if error.receipt else None
        receipt_path = candidate if candidate and candidate.is_file() and candidate.name == "outcome.json" else None
        outcome: str | None = None
        receipt: dict[str, Any] = {}
        if receipt_path:
            try:
                receipt = json.loads(receipt_path.read_text())
                outcome = receipt.get("outcome")
                details["supervisor_outcome"] = deepcopy(receipt)
                if receipt.get("cleanup", {}).get("status") == "cleanup_pending":
                    code = "cleanup-pending"
                    return GenerationError(code, operation, str(error), run_root=run_root,
                                           receipt_path=receipt_path, details=details)
                if receipt.get("output_validation", {}).get("status") == "fail" or outcome == "output-contract-failed":
                    code = "output-integrity"
                    return GenerationError(code, operation, str(error), run_root=run_root,
                                           receipt_path=receipt_path, details=details)
            except (OSError, json.JSONDecodeError):
                pass
        if outcome == "timeout":
            code = "backend-timeout"
        elif outcome == "spawn_error":
            code = ("backend-unavailable" if receipt and receipt.get("operation") == "version-probe"
                    and receipt.get("spawn_error", {}).get("errno") == 2 else "backend-spawn")
        elif outcome == "contention" or isinstance(error.__cause__, SlotTimeout):
            code = "backend-contention"
        elif outcome == "identity_error":
            code = "backend-mismatch"
        elif outcome in {"exit", "orphaned-descendant", "cancelled", "leader-state-running", "leader-state-ambiguous"}:
            code = "backend-failed"
        else:
            code = "backend-unavailable"
    elif isinstance(error, SourceValidationError):
        code = "source-validation"
        consumer_details = getattr(error, "consumer_details", None)
        if isinstance(consumer_details, Mapping):
            details.update(deepcopy(dict(consumer_details)))
        else:
            match = re.match(r"^([^\s:]+)\s+([^:]+):\s*(.*)$", str(error))
            if match:
                details["source_id"] = match.group(1)
                details["field"] = match.group(2)
                details["message"] = match.group(3)
        beat = re.search(r"\bbeat=([-+0-9.eE]+)", str(error))
        if beat:
            try:
                details["beat"] = float(beat.group(1))
            except ValueError:
                pass
        channel = re.search(r"\bchannel=([^\s:]+)", str(error))
        constraint = re.search(r"\bconstraint=([^\s:]+)", str(error))
        if channel:
            details["channel"] = channel.group(1)
        if constraint:
            details["constraint"] = constraint.group(1)
    elif isinstance(error, PackageResourceError):
        code = "source-validation"
    elif isinstance(error, OSError):
        code = "io-error"
    elif isinstance(error, _RequestError):
        code = "invalid-request"
    elif isinstance(error, (ValueError, TypeError, KeyError, json.JSONDecodeError)):
        code = "invalid-request"
    else:
        code = "backend-failed" if operation == "render" else "source-validation"
    return GenerationError(code, operation, str(error), run_root=run_root,
                          receipt_path=receipt_path, details=details)


def prepare(*, workspace: str | Path, output: str | Path,
            profile: str = "adult-reference-v1", stature: float | None = None,
            fixtures: Sequence[str] | None = None,
            bpms: Sequence[int | float] = (60, 120, 180),
            motion: Mapping[str, Any] | str | Path | None = None,
            matrix_destination: Mapping[str, Any] | None = None) -> PreparedResult:
    """Validate packaged sources, persist prepared data and return joined records.

    This host-only operation never probes Blender. ``workspace`` must be an
    absolute caller-owned workspace; ``output`` is a fresh JSON file in a new
    or empty flat run root below its ``build/`` directory.
    """
    run_root: Path | None = None
    try:
        root = workspace_root(workspace)
        if not isinstance(profile, str) or not profile:
            raise ValueError("profile must be a nonempty packaged profile identifier")
        if stature is not None:
            stature = _positive_number(stature, "stature")
        fixture_ids = _validate_selection(fixtures, "fixtures", allow_none=True)
        if motion is not None and fixture_ids is not None:
            raise _RequestError("motion and fixtures are mutually exclusive")
        if fixture_ids is not None:
            if any(not isinstance(item, str) or not item for item in fixture_ids):
                raise ValueError("fixtures must contain nonempty identifiers")
            if len(set(fixture_ids)) != len(fixture_ids):
                raise ValueError("fixtures must not contain duplicates")
        bpm_values = _validate_selection(bpms, "bpms")
        assert bpm_values is not None
        normalized_bpms: list[int | float] = []
        seen_bpms: set[Fraction] = set()
        for value in bpm_values:
            bpm = _positive_number(value, "BPM")
            normalized = Fraction(str(bpm))
            if normalized in seen_bpms:
                raise ValueError("bpms must not contain duplicate numeric values")
            seen_bpms.add(normalized)
            normalized_bpms.append(bpm)
        destination = resolve_workspace_path(output, root)
        matrix_binding = _matrix_destination(
            matrix_destination, operation="prepare", output=output, workspace=root,
            allowed_destinations=MATRIX_DESTINATIONS["prepare"],
            inputs=(motion,) if isinstance(motion, (str, Path)) else ())
        if matrix_binding is None:
            run_root = validate_run_root(destination.parent, root)
            if destination.exists():
                raise _RequestError(f"prepared output already exists: {destination}")
            if run_root.exists() and (not run_root.is_dir() or any(run_root.iterdir())):
                raise _RequestError(f"prepare run root is occupied: {run_root}")
        else:
            run_root, _ = matrix_binding
            if run_root.exists() and not run_root.is_dir():
                raise _RequestError(f"matrix element root is not a directory: {run_root}")
            if destination.exists() and not destination.is_file():
                raise _RequestError(f"prepared output is not a regular file: {destination}")
        if motion is None:
            value = prepare_skeleton.prepare(profile, stature, fixture_ids, tuple(normalized_bpms))
        else:
            value = prepare_skeleton.prepare_consumer(profile, motion, root, run_root,
                                                      stature, tuple(normalized_bpms))
        ensure_workspace_build(root)
        run_root.mkdir(parents=True, exist_ok=True)
        destination.parent.mkdir(parents=True, exist_ok=True)
        from humanmotionlib.prepared import write_json
        write_json(destination, value)
        persisted = read_prepared(destination)
        return _project(persisted, root, destination)
    except GenerationError:
        raise
    except (ValueError, TypeError, KeyError, OSError, SourceValidationError,
            PackageResourceError) as error:
        raise _translate_error(error, "prepare", run_root) from error


def _load_render_prepared(prepared: PreparedResult | str | Path,
                          workspace: Path) -> tuple[dict[str, Any], PreparedResult]:
    if isinstance(prepared, PreparedResult):
        path = prepared.prepared_path
        if not path.is_file():
            raise ValueError(f"prepared input is missing: {path}")
        actual = read_prepared(path)
        if actual["content_sha256"] != prepared.prepared_sha256:
            raise ValueError("PreparedResult identity does not match persisted input")
    elif isinstance(prepared, (str, Path)):
        path = resolve_workspace_path(prepared, workspace)
        if path.is_dir():
            path = path / "input.json"
        actual = read_prepared(path)
    else:
        raise _RequestError("prepared must be a PreparedResult or prepared JSON path")
    return actual, _project(actual, workspace, path)


def _build_render_request(actual: Mapping[str, Any], prepared_result: PreparedResult,
                          characters: Sequence[str], *, render_only: bool
                          ) -> tuple[dict[str, Any], tuple[str, ...], tuple[dict[str, Any], ...]]:
    """Build the canonical sealed request without allocating output or probing Blender."""
    from humanmotionlib.characters import expand_surface, resolve_character_selection
    from humanmotionlib.runtime import backend_contract

    selected_characters = resolve_character_selection(tuple(characters), profile_id=prepared_result.profile_id)
    selected_ids = tuple(item["id"] if isinstance(item, Mapping) else item.character_id
                         for item in selected_characters)
    surface_documents: list[dict[str, Any]] = []
    surface_identities: dict[str, str] = {}
    for item in selected_characters:
        if item["renderer_kind"] == "skinned-surface":
            surface = expand_surface(actual["sources"]["profile"], item["template"],
                                     item["appearance"], prepared_result.stature_m)
            surface_identities[item["id"]] = surface["surface_sha256"]
            surface_documents.append({"id": item["id"], "definition": {
                key: item[key] for key in ("id", "renderer_kind", "profile_id", "template_id", "appearance_id")},
                "template": item["template"], "appearance": item["appearance"],
                "source_hashes": item["source_hashes"], "surface_sha256": surface["surface_sha256"]})
    native_midpoint_samples = (
        _native_surface_midpoint_samples(actual)
        if surface_documents and not render_only else []
    )
    if surface_documents and not render_only:
        from humanmotionlib.character_midpoints import validate_native_midpoint_samples
        validate_native_midpoint_samples(actual, native_midpoint_samples)
    request_payload = {
        "format": "character-render-request/v1",
        "prepared_sha256": actual["content_sha256"],
        "character_ids": list(selected_ids),
        "characters": surface_documents,
        "character_descriptors": [{key: item.get(key) for key in
            ("id", "renderer_kind", "profile_id", "template_id", "appearance_id", "source_hashes")}
            for item in selected_characters],
        "surface_identities": dict(sorted(surface_identities.items())),
        "native_midpoint_samples": native_midpoint_samples,
        "package_identity": actual["package_identity"],
        "backend_contract": backend_contract(),
    }
    return {**request_payload, "render_identity": content_hash(request_payload)}, selected_ids, selected_characters


def _expected_render_request(prepared: PreparedResult | str | Path, *, workspace: str | Path,
                             characters: Sequence[str] = ("skeleton",),
                             render_only: bool = False) -> Mapping[str, Any]:
    """Return the exact current request identity for read-only managed-pass reuse checks."""
    if isinstance(characters, (str, bytes)) or not isinstance(characters, Sequence) or not characters:
        raise _RequestError("characters must be a nonempty sequence of character IDs")
    if any(not isinstance(item, str) or not item for item in characters) or len(set(characters)) != len(characters):
        raise _RequestError("characters must contain unique nonempty IDs")
    if not isinstance(render_only, bool):
        raise _RequestError("render_only must be a boolean")
    root = workspace_root(workspace)
    actual, prepared_result = _load_render_prepared(prepared, root)
    request, _selected_ids, _selected = _build_render_request(
        actual, prepared_result, tuple(characters), render_only=render_only)
    return request


def _native_surface_midpoint_samples(prepared: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Resolve key-interval audit samples on the host for the Blender runtime.

    The sealed render request carries these solved samples to Blender so the
    embedded runtime needs no YAML/schema dependencies to evaluate diagnostics.
    """
    from humanmotionlib.character_midpoints import expected_midpoint_inventory
    from humanmotionlib.diagnostics import DiagnosticEvaluator

    sources = prepared["sources"]
    evaluator = DiagnosticEvaluator({name: sources[name] for name in
                                     ("profile", "mobility", "body-groups", "diagnostics")})
    dense_samples: list[dict[str, Any]] = []
    for fixture_id, beat in expected_midpoint_inventory(prepared):
        solved = evaluator.evaluate(fixture_id, beat)
        dense_samples.append({
            "id": f"{fixture_id}/native-midpoint/{len(dense_samples):05d}",
            "fixture": fixture_id,
            "beat": beat,
            "frames": solved["frames"],
            "guides": solved["guides"],
            "world_root": solved["world_root"],
            "contacts": solved["contacts"],
        })
    return dense_samples


def _render_operation(prepared: PreparedResult | str | Path, *, workspace: str | Path,
           output: str | Path, images: bool = True,
           characters: Sequence[str] = ("skeleton",),
           render_dir: str | Path | None = None, render_only: bool = False,
           timeout_seconds: float = DEFAULT_BUILD_TIMEOUT,
           slot_timeout_seconds: float = DEFAULT_SLOT_TIMEOUT,
           _owner_run: str | Path | None = None,
           matrix_destination: Mapping[str, Any] | None = None) -> GenerationResult:
    """Build/render a persisted preparation with the pinned external Blender.

    ``output`` is a fresh flat run root. Relative paths resolve from the
    explicit absolute workspace. Images are rendered into ``output/frames``
    by default. ``numerical_acceptance`` remains ``not-run`` and
    ``visual_acceptance`` remains ``pending`` until their separate review gates.
    """
    output_root: Path | None = None
    phase = "request"
    try:
        root = workspace_root(workspace)
        output_root = resolve_workspace_path(output, root)
        if not isinstance(images, bool) or not isinstance(render_only, bool):
            raise _RequestError("images and render_only must be booleans")
        if isinstance(characters, (str, bytes)) or not isinstance(characters, Sequence) or not characters:
            raise _RequestError("characters must be a nonempty sequence of character IDs")
        if any(not isinstance(item, str) or not item for item in characters):
            raise _RequestError("characters must contain nonempty IDs")
        if len(set(characters)) != len(characters):
            raise _RequestError("characters must not contain duplicates")
        if not images and render_dir is not None:
            raise _RequestError("render_dir cannot be supplied when images are disabled")
        timeout_seconds = _positive_number(timeout_seconds, "timeout_seconds")
        slot_timeout_seconds = _positive_number(slot_timeout_seconds, "slot_timeout_seconds")
        timeout_seconds = validate_timeout(timeout_seconds, "timeout_seconds")
        slot_timeout_seconds = validate_timeout(slot_timeout_seconds, "slot_timeout_seconds")
        try:
            actual, prepared_result = _load_render_prepared(prepared, root)
        except (ValueError, TypeError, KeyError, OSError, PackageResourceError) as error:
            raise GenerationError("input-integrity", "render", str(error),
                                  run_root=output_root) from error
        matrix_binding = _matrix_destination(
            matrix_destination, operation="render", output=output, workspace=root,
            allowed_destinations=MATRIX_DESTINATIONS["render"],
            inputs=(prepared_result.prepared_path,))
        render_request, selected_ids, selected_characters = _build_render_request(
            actual, prepared_result, tuple(characters), render_only=render_only)
        if images:
            if matrix_binding is not None and render_dir is not None and ".." in Path(os.fspath(render_dir)).parts:
                raise _RequestError("matrix render directory cannot contain traversal components")
            frames = resolve_workspace_path(render_dir, root) if render_dir is not None else output_root / "frames"
            try:
                frames.relative_to(output_root)
            except ValueError as error:
                raise _RequestError("render directory must remain inside the output run") from error
            if matrix_binding is not None and frames != output_root / "frames":
                raise _RequestError("matrix render directory must be the declared output's frames directory")
        else:
            frames = None
        render_identity = render_request["render_identity"]
        owner_root = None
        if matrix_binding is not None:
            element_root, declared_output = matrix_binding
            if declared_output != output_root:
                raise _RequestError("matrix render output does not match its declared destination")
            if output_root.exists() and not output_root.is_dir():
                raise _RequestError(f"matrix render output is not a directory: {output_root}")
        elif _owner_run is None:
            output_root = validate_run_root(output_root, root)
            if output_root.exists() and (not output_root.is_dir() or any(output_root.iterdir())):
                raise _RequestError(f"render output run root is occupied: {output_root}")
        else:
            owner = validate_run_root(resolve_workspace_path(_owner_run, root), root)
            output_root = validate_managed_pass_root(output_root, owner, root)
            if output_root.exists():
                raise _RequestError(f"managed render pass must be fresh: {output_root}")
            owner_root = owner
        ensure_workspace_build(root)
        request_path = output_root / "character-render-request.json"
        managed_claim = None
        request_bytes = canonical_bytes(render_request)
        if owner_root is None:
            output_root.mkdir(parents=True, exist_ok=True)
            write_json(request_path, render_request)
        else:
            # Atomically claim the designated child before creating the sealed
            # request. The backend must match this inode and exact request bytes
            # both before and after its own Blender version probe.
            output_root.mkdir(parents=False, exist_ok=False)
            directory_stat = output_root.lstat()
            if stat.S_ISLNK(directory_stat.st_mode) or not stat.S_ISDIR(directory_stat.st_mode):
                raise _RequestError("managed render pass directory is not a real directory")
            with request_path.open("xb") as stream:
                stream.write(request_bytes)
                stream.flush()
                os.fsync(stream.fileno())
            request_stat = request_path.lstat()
            if stat.S_ISLNK(request_stat.st_mode) or not stat.S_ISREG(request_stat.st_mode):
                raise _RequestError("managed render request is not a regular file")
            managed_claim = run_blender._ManagedOutputClaim(
                owner_run=str(owner_root), pass_root=str(output_root),
                directory_device=directory_stat.st_dev, directory_inode=directory_stat.st_ino,
                request_path=str(request_path), request_device=request_stat.st_dev,
                request_inode=request_stat.st_ino,
                request_sha256=hashlib.sha256(request_bytes).hexdigest(),
                prepared_sha256=actual["content_sha256"], render_identity=render_identity,
                character_ids=tuple(selected_ids))
        phase = "backend"
        backend_kwargs = {
            "render_dir": frames, "render_only": render_only,
            "timeout_seconds": timeout_seconds, "slot_timeout_seconds": slot_timeout_seconds,
            "workspace": root, "owner_run": _owner_run,
            "characters": selected_ids, "render_identity": render_identity,
            "character_request": request_path,
        }
        if matrix_binding is not None:
            backend_kwargs["matrix_element_root"] = str(matrix_binding[0])
        if managed_claim is not None:
            backend_kwargs["managed_claim"] = managed_claim
        receipt = run_blender.run(
            prepared_result.prepared_path, output_root, **backend_kwargs,
        )
        receipt_path = Path(receipt["stdout_log"]).parent / "outcome.json"
        image_records: tuple[RenderedImage, ...] = ()
        phase = "outputs"
        if images:
            manifest_path = output_root / "render-manifest.json"
            from humanmotionlib.render_contract import read_supervised_receipt, validate_manifest
            try:
                manifest = json.loads(manifest_path.read_text(), object_pairs_hook=_unique_json)
                if manifest.get("render_identity") != render_identity:
                    raise ValueError("render manifest identity does not match sealed character request")
                if any(identifier != "skeleton" for identifier in selected_ids):
                    from humanmotionlib.render_contract import validate_character_manifest
                    required_paths = validate_character_manifest(manifest, actual, frames,
                                                                 output=output_root,
                                                                 character_ids=selected_ids)
                else:
                    required_paths = validate_manifest(manifest, actual, frames, output=output_root)
                    required_paths.append(Path("character-render-request.json"))
                if not render_only:
                    required_paths.extend((Path("evaluated.json"), Path("geometry-reference.json")))
                    if any(identifier != "skeleton" for identifier in selected_ids):
                        required_paths.extend(Path(path.relative_to(output_root))
                                              for path in sorted((output_root / "characters").glob("*/surface-*.json")))
                read_supervised_receipt(output_root, actual, required_paths)
            except (ValueError, TypeError, AttributeError, OSError, KeyError, json.JSONDecodeError) as error:
                raise GenerationError("output-integrity", "render", str(error), run_root=output_root,
                                      receipt_path=receipt_path) from error
            by_id = {pose.sample_id: pose for pose in prepared_result.poses}
            collected: list[RenderedImage] = []
            for sample in actual["samples"]:
                if any(identifier != "skeleton" for identifier in selected_ids):
                    for character in manifest["characters"]:
                        record = next(item for item in character["samples"] if item["id"] == sample["id"])
                        for view, relative in sorted(record["images"].items()):
                            collected.append(RenderedImage(sample["id"], view, (frames / relative).resolve(),
                                                           character["id"]))
                else:
                    record = next(item for item in manifest["samples"] if item["id"] == sample["id"])
                    for view, relative in sorted(record["images"].items()):
                        collected.append(RenderedImage(sample["id"], view, (frames / relative).resolve(), "skeleton"))
            image_records = tuple(collected)
            # A sample must have its corresponding structured pose before it is exposed.
            if any(item.sample_id not in by_id for item in image_records):
                raise ValueError("render manifest references an unknown pose sample")
        artifacts: dict[str, Path] = {
            "prepared": (output_root / "input.json").resolve(),
            "scene": (output_root / "skeleton.blend").resolve(),
            "metadata": (output_root / "build-metadata.json").resolve(),
            "character_render_request": (output_root / "character-render-request.json").resolve(),
        }
        if not render_only:
            artifacts.update({"evaluated": (output_root / "evaluated.json").resolve(),
                              "geometry": (output_root / "geometry-reference.json").resolve()})
        if images:
            artifacts["render_manifest"] = (output_root / "render-manifest.json").resolve()
        for identifier in selected_ids:
            if identifier != "skeleton":
                artifacts[f"characters/{identifier}/surface_reference"] = (output_root / "characters" / identifier / "surface-reference.json").resolve()
                if not render_only:
                    artifacts[f"characters/{identifier}/surface_evaluated"] = (output_root / "characters" / identifier / "surface-evaluated.json").resolve()
        metadata = json.loads(artifacts["metadata"].read_text())
        backend_identity = {
            "version": metadata.get("blender_version"),
            "build_hash": metadata.get("blender_build"),
            "platform": metadata.get("platform"),
        }
        character_records = tuple(CharacterInfo(
            character_id=item["id"], renderer_kind=item["renderer_kind"],
            profile_id=item.get("profile_id", prepared_result.profile_id),
            template_id=item.get("template_id"), appearance_id=item.get("appearance_id"),
            source_hashes=deepcopy(item.get("source_hashes", {})))
            for item in selected_characters)
        character_artifacts = tuple(CharacterArtifactSet(
            character_id=item.character_id,
            artifacts={key: value for key, value in artifacts.items()
                       if key.startswith(f"characters/{item.character_id}/")})
            for item in character_records)
        character_provenance = {}
        for info, source in zip(character_records, selected_characters):
            character_provenance[info.character_id] = {
                "source_hashes": deepcopy(info.source_hashes),
                "definition": deepcopy(source.get("provenance")),
                "template": deepcopy(source.get("template", {}).get("provenance")),
                "appearance": deepcopy(source.get("appearance", {}).get("provenance")),
            }
        return GenerationResult(prepared_result, output_root.resolve(), image_records,
                                artifacts, receipt_path.resolve(), backend_identity,
                                "not-run", "pending", character_records, character_artifacts,
                                character_provenance, render_identity)
    except GenerationError:
        raise
    except KeyboardInterrupt:
        raise
    except (ValueError, TypeError, AttributeError, KeyError, OSError, json.JSONDecodeError,
            PackageResourceError, SourceValidationError, InvocationError, SlotTimeout) as error:
        if isinstance(error, InvocationError) and isinstance(error.__cause__, KeyboardInterrupt):
            raise error.__cause__
        if phase == "request" and isinstance(error, (ValueError, TypeError)):
            raise GenerationError("invalid-request", "render", str(error),
                                  run_root=output_root) from error
        if phase == "backend" and isinstance(error, (ValueError, TypeError)):
            raise GenerationError("invalid-request", "render", str(error),
                                  run_root=output_root) from error
        raise _translate_error(error, "render", output_root) from error


def render(prepared: PreparedResult | str | Path, *, workspace: str | Path,
           output: str | Path, images: bool = True,
           characters: Sequence[str] = ("skeleton",),
           render_dir: str | Path | None = None, render_only: bool = False,
           timeout_seconds: float = DEFAULT_BUILD_TIMEOUT,
           slot_timeout_seconds: float = DEFAULT_SLOT_TIMEOUT,
           matrix_destination: Mapping[str, Any] | None = None) -> GenerationResult:
    """Build/render one fresh, flat public run root."""
    return _render_operation(prepared, workspace=workspace, output=output, images=images,
                             characters=characters, render_dir=render_dir,
                             render_only=render_only, timeout_seconds=timeout_seconds,
                             slot_timeout_seconds=slot_timeout_seconds,
                             matrix_destination=matrix_destination)


def _render_owned_pass(prepared: PreparedResult | str | Path, *, workspace: str | Path,
                       output: str | Path, owner_run: str | Path, images: bool = True,
                       characters: Sequence[str] = ("skeleton",),
                       render_dir: str | Path | None = None, render_only: bool = True,
                       timeout_seconds: float = DEFAULT_BUILD_TIMEOUT,
                       slot_timeout_seconds: float = DEFAULT_SLOT_TIMEOUT) -> GenerationResult:
    """Internal review-pack pass using the normal sealed, supervised render path.

    The owner is an existing flat run and ``output`` must be a fresh direct
    child with one of the finite managed pass names. This is intentionally
    private; public callers can only create independent flat run roots.
    """
    return _render_operation(prepared, workspace=workspace, output=output, images=images,
                             characters=characters, render_dir=render_dir,
                             render_only=render_only, timeout_seconds=timeout_seconds,
                             slot_timeout_seconds=slot_timeout_seconds,
                             _owner_run=owner_run)


__all__ = [
    "CharacterArtifactSet", "CharacterInfo", "GenerationError", "GenerationResult", "PoseSample", "PreparedResult",
    "ProvenanceInfo", "RenderedImage", "SourceProvenance", "Timeline",
    "TimelineEntry", "prepare", "render",
]
