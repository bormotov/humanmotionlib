# SPDX-License-Identifier: Apache-2.0
"""Host-side character registry, source closure and deterministic surface expansion.

Imports are intentionally light. YAML and JSON Schema are loaded only when a
surface character is selected; the standalone skeleton path never parses a
surface template.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import PurePosixPath
from typing import Any, Mapping, Sequence

from humanmotionlib.package_resources import read_bytes, read_text


class CharacterSourceError(ValueError):
    """A character source, binding, or generated surface failed validation."""


_SCHEMAS = {
    "character-registry": "schema/character-registry.schema.json",
    "character-definition": "schema/character-definition.schema.json",
    "character-surface-template": "schema/character-template.schema.json",
    "character-appearance": "schema/character-appearance.schema.json",
}


def _load_yaml(logical: str) -> dict[str, Any]:
    import yaml
    from humanmotionlib.source_validation import UniqueKeyLoader
    try:
        value = yaml.load(read_text(logical), Loader=UniqueKeyLoader)
    except Exception as error:
        raise CharacterSourceError(f"invalid character YAML {logical}: {error}") from error
    if not isinstance(value, dict):
        raise CharacterSourceError(f"character YAML must be an object: {logical}")
    return value


def _validate_schema(document: Mapping[str, Any], kind: str, source: str) -> None:
    import json
    from jsonschema import Draft202012Validator

    def ensure_finite(value: Any, pointer: str = "") -> None:
        if isinstance(value, float) and not math.isfinite(value):
            raise CharacterSourceError(f"{source}{pointer}: nonfinite numeric value")
        if isinstance(value, Mapping):
            for key, child in value.items():
                ensure_finite(child, pointer + "/" + str(key))
        elif isinstance(value, (list, tuple)):
            for index, child in enumerate(value):
                ensure_finite(child, pointer + "/" + str(index))

    ensure_finite(document)
    schema_name = _SCHEMAS.get(kind)
    if schema_name is None:
        raise CharacterSourceError(f"unsupported character document kind {kind}")
    try:
        schema = json.loads(read_text(schema_name))
        Draft202012Validator.check_schema(schema)
        errors = sorted(Draft202012Validator(schema).iter_errors(document),
                        key=lambda error: (list(error.absolute_path), error.message))
    except Exception as error:
        raise CharacterSourceError(f"cannot validate {source}: {error}") from error
    if errors:
        error = errors[0]
        path = "/" + "/".join(str(item) for item in error.absolute_path)
        raise CharacterSourceError(f"{source}{path}: {error.message}")


def _validate_provenance(document: Mapping[str, Any], source: str) -> None:
    provenance=document.get("provenance")
    if not isinstance(provenance,dict) or provenance.get("license")!="CC-BY-4.0":
        raise CharacterSourceError(f"{source} has invalid CC-BY-4.0 provenance")
    sources=provenance.get("sources",[])
    if provenance.get("kind")=="adapted" and not sources:
        raise CharacterSourceError(f"{source} is adapted but declares no inherited sources")
    if not sources:return
    register=read_text("docs/used-materials.md")
    for item in sources:
        material=item.get("material") if isinstance(item,dict) else None
        rows=[line for line in register.splitlines() if line.startswith(f"| `{material}`:")]
        if not isinstance(material,str) or len(rows)!=1:
            raise CharacterSourceError(f"{source} has unresolved provenance material {material!r}")


def rest_contract_digest(profile: Mapping[str, Any], template: Mapping[str, Any]) -> str:
    """Hash the template-selected rest transforms, hierarchy and attachments."""
    structures = profile.get("structures")
    if not isinstance(structures, list):
        raise CharacterSourceError("profile has no structure list for character binding")
    by_id = {row.get("id"): row for row in structures if isinstance(row, dict)}
    seeds = template.get("rest_contract_structures")
    if not isinstance(seeds, list) or not seeds or len(seeds) != len(set(seeds)):
        raise CharacterSourceError("template rest_contract_structures must be a nonempty unique list")
    closure: set[str] = set()
    for seed in seeds:
        current = seed
        visited: set[str] = set()
        while current is not None:
            if current in visited:
                raise CharacterSourceError(f"cycle in profile hierarchy at {current}")
            visited.add(current)
            row = by_id.get(current)
            if row is None:
                raise CharacterSourceError(f"unresolved rest-contract structure {current}")
            closure.add(current)
            current = row.get("parent")
    selected = []
    for identifier in sorted(closure):
        row = by_id[identifier]
        selected.append({
            "id": identifier,
            "parent": row.get("parent"),
            "origin_m": row.get("origin_m"),
            "basis": row.get("basis"),
            "rest_translation_m": row.get("rest_translation_m"),
            "rest_orientation": row.get("rest_orientation"),
            "attachments": sorted(({
                "id": attachment["id"],
                "position_m": attachment["position_m"],
                "orientation": attachment["orientation"],
            } for attachment in row.get("attachments", [])), key=lambda item: item["id"]),
        })
    try:
        canonical = json.dumps({"profile_id": profile.get("id"), "structures": selected},
                              sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except ValueError as error:
        raise CharacterSourceError("nonfinite numeric value in rest-contract data") from error
    return hashlib.sha256(canonical).hexdigest()


def _validate_template_carriers(profile: Mapping[str, Any], template: Mapping[str, Any],
                                 source: str) -> None:
    """Reject template carrier references that do not resolve in its bound profile."""
    structures = profile.get("structures")
    if not isinstance(structures, list):
        raise CharacterSourceError(f"{source}: profile has no structure inventory")
    available: set[str] = set()
    by_id: dict[str, Mapping[str, Any]] = {}
    for structure in structures:
        if not isinstance(structure, Mapping) or not isinstance(structure.get("id"), str):
            raise CharacterSourceError(f"{source}: invalid profile structure inventory")
        available.add(structure["id"])
        by_id[structure["id"]] = structure

    bound: set[str] = set()
    seeds = template.get("rest_contract_structures", [])
    for seed in seeds:
        current = seed
        while current is not None and current not in bound:
            structure = by_id.get(current)
            if structure is None:
                break  # rest_contract_digest reports the precise unresolved seed/parent.
            bound.add(current)
            current = structure.get("parent")
    references: set[str] = set()

    def visit(value: Any, key: str = "") -> None:
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                if child_key in {"carrier", "from", "to", "hand_carrier"}:
                    if not isinstance(child, str) or child not in available:
                        raise CharacterSourceError(
                            f"{source}: unresolved carrier {child!r} at {child_key}")
                    references.add(child)
                elif child_key == "carriers":
                    if (not isinstance(child, list) or
                            any(not isinstance(item, str) or item not in available for item in child)):
                        bad = next((item for item in child if not isinstance(item, str) or item not in available), child) if isinstance(child, list) else child
                        raise CharacterSourceError(f"{source}: unresolved carrier {bad!r} at carriers")
                    references.update(child)
                visit(child, child_key)
        elif isinstance(value, list):
            for child in value:
                visit(child, key)

    visit(template)
    outside_binding = sorted(references - bound)
    if outside_binding:
        raise CharacterSourceError(
            f"{source}: carrier references are outside rest-contract binding closure: {outside_binding}")


def resolve_character_selection(ids: Sequence[str], *, profile_id: str) -> tuple[dict[str, Any], ...]:
    """Validate and return selected descriptors in packaged registry order."""
    registry = _load_yaml("characters/registry.yaml")
    _validate_schema(registry, registry.get("kind"), "characters/registry.yaml")
    _validate_provenance(registry, "characters/registry.yaml")
    rows = registry.get("characters")
    if not isinstance(rows, list):
        raise CharacterSourceError("character registry has no characters list")
    order: list[str] = []
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            raise CharacterSourceError("invalid character registry entry")
        identifier = row["id"]
        if identifier in indexed:
            raise CharacterSourceError(f"duplicate character ID {identifier}")
        order.append(identifier)
        indexed[identifier] = row
    if len(set(ids)) != len(ids) or any(identifier not in indexed for identifier in ids):
        raise CharacterSourceError("unknown or duplicate character selection")
    selected = [identifier for identifier in order if identifier in ids]
    result = []
    for identifier in selected:
        definition_path = indexed[identifier].get("definition")
        safe = PurePosixPath(definition_path or "")
        if safe.is_absolute() or ".." in safe.parts:
            raise CharacterSourceError(f"unsafe definition path for {identifier}")
        logical = "characters/" + safe.as_posix()
        definition = _load_yaml(logical)
        _validate_schema(definition, definition.get("kind"), logical)
        _validate_provenance(definition, logical)
        if definition.get("id") != identifier or definition.get("profile_id") != profile_id:
            raise CharacterSourceError(f"character {identifier} is incompatible with profile {profile_id}")
        closure = {
            "characters/registry.yaml": hashlib.sha256(read_bytes("characters/registry.yaml")).hexdigest(),
            logical: hashlib.sha256(read_bytes(logical)).hexdigest(),
            _SCHEMAS["character-registry"]: hashlib.sha256(read_bytes(_SCHEMAS["character-registry"])).hexdigest(),
            _SCHEMAS["character-definition"]: hashlib.sha256(read_bytes(_SCHEMAS["character-definition"])).hexdigest(),
        }
        record: dict[str, Any] = dict(definition)
        record["source_hashes"] = dict(closure)
        if definition["renderer_kind"] == "skinned-surface":
            template_logical = f"characters/templates/{definition['template_id']}.yaml"
            appearance_logical = f"characters/appearances/{definition['appearance_id']}.yaml"
            template = _load_yaml(template_logical)
            appearance = _load_yaml(appearance_logical)
            _validate_schema(template, template.get("kind"), template_logical)
            _validate_schema(appearance, appearance.get("kind"), appearance_logical)
            _validate_provenance(template, template_logical)
            _validate_provenance(appearance, appearance_logical)
            if (definition.get("template_revision") != template.get("template_revision") or
                    definition.get("binding_revision") != template.get("binding_revision")):
                raise CharacterSourceError(f"template/binding revision mismatch for character {identifier}")
            if template.get("compatible_profile") != profile_id:
                raise CharacterSourceError(f"template {template['id']} is incompatible with profile {profile_id}")
            if appearance.get("id") != definition.get("appearance_id"):
                raise CharacterSourceError(f"appearance mismatch for character {identifier}")
            profile_logical = f"rig/profiles/{profile_id}.yaml"
            profile = _load_yaml(profile_logical)
            _validate_template_carriers(profile, template, template_logical)
            actual_digest = rest_contract_digest(profile, template)
            if actual_digest != template.get("expected_rest_contract_sha256"):
                raise CharacterSourceError(f"stale character binding for {identifier}: {actual_digest}")
            closure.update({name: hashlib.sha256(read_bytes(name)).hexdigest()
                            for name in (template_logical, appearance_logical,
                                         profile_logical,
                                         _SCHEMAS["character-surface-template"],
                                         _SCHEMAS["character-appearance"])})
            record.update({"template": template, "appearance": appearance,
                           "template_id": template["id"], "appearance_id": appearance["id"]})
            record["source_hashes"] = dict(sorted(closure.items()))
        result.append(record)
    return tuple(result)


def validate_character_sources() -> tuple[dict[str, Any], ...]:
    """Validate the complete registry and every selected dependency closure."""
    registry = _load_yaml("characters/registry.yaml")
    ids = tuple(row["id"] for row in registry["characters"])
    return resolve_character_selection(ids, profile_id="adult-reference-v1")


def expand_surface(profile: Mapping[str, Any], template_doc: Mapping[str, Any],
                   appearance_doc: Mapping[str, Any], stature_m: float) -> dict[str, Any]:
    """Expand a deterministic, stature-scaled analytic surface source."""
    from humanmotionlib.character_surface import expand_surface as expand
    try:
        return expand(profile, template_doc, appearance_doc, stature_m)
    except (ValueError, TypeError, KeyError, OverflowError) as error:
        raise CharacterSourceError(str(error)) from error


__all__ = ["CharacterSourceError", "expand_surface", "resolve_character_selection",
           "rest_contract_digest", "validate_character_sources"]
