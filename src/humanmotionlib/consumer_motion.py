# SPDX-License-Identifier: Apache-2.0
"""Load and resolve the closed consumer-motion source contract."""

from __future__ import annotations

from copy import deepcopy
from collections.abc import Mapping
from datetime import date
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit

import yaml

from humanmotionlib.finite import SourceValidationError, require_finite
from humanmotionlib.package_resources import read_bytes, read_text
from humanmotionlib.prepared import canonical_bytes, content_hash
from humanmotionlib.source_validation import UniqueKeyLoader, validate_document
from humanmotionlib import math3d as m


_ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_MAX_DURATION = 256
_MAX_DELIVERED = 100_000
_LICENSES = {"CC-BY-4.0", "CC0-1.0", "MIT", "Apache-2.0"}


class ConsumerSampleBudgetError(ValueError):
    """A valid source exceeds the public request's delivered-sample budget."""


_CHANNELS_OVERWRITTEN = {
    "squat_closed": {
        "pelvis.y", "pelvis.z", "hindfoot.L.inversion", "hindfoot.R.inversion",
        *(f"hip.{side}.{name}" for side in ("L", "R")
          for name in ("flexion", "adduction", "external_rotation")),
    },
    "walking_flat": {
        *(f"{joint}.{side}.{name}" for side in ("L", "R")
          for joint, names in (("elbow", ("flexion",)), ("forearm", ("pronation",)),
                               ("hip", ("flexion", "adduction", "external_rotation")),
                               ("hindfoot", ("inversion",)), ("knee", ("flexion",)),
                               ("ankle", ("dorsiflexion",)),
                               ("shoulder", ("elevation", "plane")))
          for name in names),
    },
    "forefoot_rocker": {
        "pelvis.y", "pelvis.z",
        *(f"{joint}.{side}.{name}" for side in ("L", "R")
          for joint, name in (("ankle", "dorsiflexion"), ("mtp", "extension"))),
    },
    "rest": {f"shoulder.{side}.{name}" for side in ("L", "R")
             for name in ("elevation", "plane")},
}


def _json_tree(value, path="$", active=None):
    """Copy only JSON-shaped mappings/lists/scalars and reject container cycles."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise SourceValidationError(f"{path}: non-finite number")
        return value
    active = set() if active is None else active
    if isinstance(value, Mapping):
        identity = id(value)
        if identity in active:
            raise SourceValidationError(f"{path}: recursive mapping")
        active.add(identity)
        try:
            result = {}
            for key, child in value.items():
                if not isinstance(key, str):
                    raise SourceValidationError(f"{path}: object keys must be strings")
                result[key] = _json_tree(child, f"{path}.{key}", active)
            return result
        finally:
            active.remove(identity)
    if isinstance(value, (list, tuple)):
        identity = id(value)
        if identity in active:
            raise SourceValidationError(f"{path}: recursive list")
        active.add(identity)
        try:
            return [_json_tree(child, f"{path}[{index}]", active)
                    for index, child in enumerate(value)]
        finally:
            active.remove(identity)
    raise SourceValidationError(f"{path}: unsupported non-JSON value {type(value).__name__}")


def _reject_constant(value):
    raise SourceValidationError(f"JSON constant {value} is not finite")


def _unique_json(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SourceValidationError(f"Duplicate JSON key {key!r}")
        result[key] = value
    return result


def _managed_run(path: Path, workspace: Path) -> Path | None:
    build = (workspace / "build").resolve()
    try:
        relative = path.resolve().relative_to(build)
    except ValueError:
        return None
    if not relative.parts:
        return None
    return build / relative.parts[0]


def load_consumer_document(source, workspace: Path, output_run: Path) -> dict:
    """Load one mapping or local YAML/JSON file without mutating caller data."""
    source_path = None
    if isinstance(source, (str, Path)):
        source_path = Path(source)
        if not source_path.is_absolute():
            source_path = workspace / source_path
        source_path = source_path.resolve(strict=True)
        suffix = source_path.suffix.lower()
        if suffix not in {".json", ".yaml", ".yml"}:
            raise SourceValidationError("motion path must end in .json, .yaml or .yml")
        raw = source_path.read_bytes()
        try:
            text = raw.decode("utf-8")
            if suffix == ".json":
                value = json.loads(text, object_pairs_hook=_unique_json,
                                   parse_constant=_reject_constant)
            else:
                value = yaml.load(text, Loader=UniqueKeyLoader)
        except (UnicodeError, json.JSONDecodeError, yaml.YAMLError,
                SourceValidationError) as error:
            wrapped = SourceValidationError(f"{source_path} $: {error}")
            wrapped.consumer_details = {
                "source_id": str(source_path), "field": "$", "message": str(error),
            }
            raise wrapped from error
        source_run = _managed_run(source_path, workspace)
        try:
            source_path.relative_to(output_run.resolve())
        except ValueError:
            pass
        else:
            raise SourceValidationError("motion source is inside the output run")
        if source_run is not None:
            try:
                output_run.resolve().relative_to(source_run.resolve())
            except ValueError:
                pass
            else:
                raise SourceValidationError("output run overlaps the motion input run")
            try:
                source_run.resolve().relative_to(output_run.resolve())
            except ValueError:
                pass
            else:
                raise SourceValidationError("motion input run overlaps the output run")
    else:
        value = source
    try:
        result = _json_tree(value)
    except SourceValidationError as error:
        candidate = value.get("motion") if isinstance(value, Mapping) else None
        identifier = candidate.get("id") if isinstance(candidate, Mapping) else None
        path_error = re.match(r"^\$\.?(?:motion\.)?([^:]*):\s*(.*)$", str(error))
        field, message = ((path_error.group(1) or "source", path_error.group(2))
                          if path_error else ("source", str(error)))
        raise SourceValidationError(f"{identifier or 'source'} {field}: {message}") from error
    if not isinstance(result, dict):
        raise SourceValidationError("consumer motion document must be a JSON object")
    require_finite(result)
    return result


def _register_ids(register: str) -> dict[str, dict[str, str]]:
    result = {}
    for line in register.splitlines():
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) < 5:
            continue
        match = re.match(r"^`([^`]+)`: ?(.*)$", cells[1])
        if match:
            result[match.group(1)] = {"material": match.group(2), "source_url": cells[2],
                                      "license": cells[3]}
    return result


def _obligation_profile(license_id: str) -> dict[str, bool]:
    if license_id == "CC-BY-4.0":
        return {"retain_attribution": True, "retain_license_text": True,
                "retain_change_notice": True}
    if license_id == "MIT":
        return {"retain_license_text": True, "retain_copyright_notice": True}
    if license_id == "Apache-2.0":
        return {"retain_license_text": True, "retain_copyright_notice": True,
                "retain_change_notice": True, "retain_notice_if_present": True}
    if license_id == "CC0-1.0":
        return {}
    raise SourceValidationError(f"unsupported consumer license {license_id}")


def _validate_clearance(document: dict, packaged_register: str) -> dict[str, dict]:
    rows = _register_ids(packaged_register)
    supplied: dict[str, dict] = {}
    for record in document["materials"]:
        identifier = record["id"]
        if identifier in rows:
            raise SourceValidationError(f"materials.{identifier}: identifier shadows packaged register")
        if identifier in supplied:
            raise SourceValidationError(f"materials.{identifier}: duplicate clearance identifier")
        if record["license"] not in _LICENSES:
            raise SourceValidationError(f"materials.{identifier}.license: unsupported license")
        try:
            checked = date.fromisoformat(record["checked_on"])
        except (TypeError, ValueError) as error:
            raise SourceValidationError(f"materials.{identifier}.checked_on: expected a valid ISO date") from error
        if checked.isoformat() != record["checked_on"]:
            raise SourceValidationError(f"materials.{identifier}.checked_on: expected a valid ISO date")
        parts = urlsplit(record["source_url"]), urlsplit(record["license_url"])
        if any(item.scheme not in {"http", "https"} or not item.netloc for item in parts):
            raise SourceValidationError(f"materials.{identifier}: source and license URLs must be absolute HTTP(S) URLs")
        expected = _obligation_profile(record["license"])
        declared = record["obligations"]
        if not set(expected) <= set(declared):
            raise SourceValidationError(f"materials.{identifier}.obligations: missing requirements from the supported {record['license']} profile")
        if set(expected) & {"retain_attribution", "retain_copyright_notice"} and not record["attribution"].strip():
            raise SourceValidationError(f"materials.{identifier}.attribution: the {record['license']} profile requires attribution/copyright text")
        permissions = record["permissions"]
        if not all(permissions.get(name) is True for name in
                   ("commercial_use", "derivatives", "cc_by_4_0_distribution")):
            raise SourceValidationError(f"materials.{identifier}.permissions: commercial, derivative and CC-BY-4.0 distribution permission are required")
        supplied[identifier] = deepcopy(record)

    provenance = document["motion"].get("provenance", {})
    sources = provenance.get("sources", [])
    if provenance.get("kind") == "authored" and sources:
        raise SourceValidationError("motion.provenance.sources: authored contribution must not claim external sources")
    if provenance.get("kind") == "adapted" and not sources:
        raise SourceValidationError("motion.provenance.sources: adapted contribution requires a source")
    referenced = {source["material"] for source in sources}
    missing = referenced - rows.keys() - supplied.keys()
    if missing:
        raise SourceValidationError("motion.provenance.sources: unresolved material " + ", ".join(sorted(missing)))
    unused = supplied.keys() - referenced
    if unused:
        raise SourceValidationError("materials: unused clearance records " + ", ".join(sorted(unused)))
    for source in sources:
        identifier = source["material"]
        license_id = supplied[identifier]["license"] if identifier in supplied else None
        if license_id is None:
            license_id = _packaged_license(rows[identifier]["license"])
        if license_id not in _LICENSES:
            raise SourceValidationError(f"motion.provenance.sources.{identifier}: packaged license is not supported for consumer derivation")
        _obligation_profile(license_id)
    return supplied


def _packaged_license(register_label: str) -> str:
    normalized = register_label.lower()
    if "cc by 4.0" in normalized or "cc-by-4.0" in normalized:
        return "CC-BY-4.0"
    if "cc0-1.0" in normalized or "cc0 1.0" in normalized:
        return "CC0-1.0"
    if "mit" in normalized:
        return "MIT"
    if "apache-2.0" in normalized:
        return "Apache-2.0"
    raise SourceValidationError("referenced packaged material has no supported commercial/derivative license profile")


def _variant(base: dict, motion: dict) -> dict:
    identifier = motion.get("id", "source")

    def fail(field: str, message: str):
        raise SourceValidationError(f"{identifier} {field}: {message}")

    result = deepcopy(base)
    result["id"] = motion["id"]
    result["description"] = motion["description"]
    result["license"] = motion["license"]
    result["provenance"] = deepcopy(motion["provenance"])
    tracks = {track["channel"]: track for track in result["tracks"]}
    scales = motion["track_scales"]
    overrides = motion["track_overrides"]
    if not scales and not overrides:
        fail("track_scales", "variant must scale or replace at least one track")
    override_channels = [track["channel"] for track in overrides]
    if len(override_channels) != len(set(override_channels)):
        fail("track_overrides", "duplicate channel")
    overlap = set(scales) & set(override_channels)
    if overlap:
            fail("track_overrides", "scaling/replacement conflict for " + ", ".join(sorted(overlap)))
    for channel, factor in scales.items():
        if channel not in tracks:
            fail(f"track_scales.{channel}", "unknown base track")
        if isinstance(factor, bool) or not isinstance(factor, (int, float)) or not math.isfinite(factor):
            fail(f"track_scales.{channel}", "expected finite numeric factor")
        for key in tracks[channel]["keys"]:
            key["value"] *= factor
            if not math.isfinite(key["value"]):
                fail(f"track_scales.{channel}", "scaled value is non-finite")
    for track in overrides:
        channel = track["channel"]
        if channel not in tracks:
            fail(f"track_overrides.{channel}", "unknown base track")
        tracks[channel].clear()
        tracks[channel].update(deepcopy(track))
    if override_channels:
        result["tracks"] = [tracks[track["channel"]] for track in result["tracks"]]
    return result


def _constructor_channels(kind: str) -> set[str]:
    return _CHANNELS_OVERWRITTEN.get(kind, set())


def validate_resolved_motion(motion: dict, sources: dict, *, stature_m: float,
                             bpms: tuple[int | float, ...]) -> tuple[dict, dict]:
    """Apply semantic ownership and constructor validation after schema checks."""
    identifier = motion.get("id", "source")

    def fail(field: str, message: str):
        raise SourceValidationError(f"{identifier} {field}: {message}")

    validate_document(motion, "diagnostic")
    if not _ID.fullmatch(identifier) or "/" in identifier or "." in identifier or ".." in identifier:
        fail("id", "unsafe consumer identifier")
    packaged = {fixture["id"] for fixture in sources["diagnostics"]}
    if identifier in packaged:
        fail("id", "consumer identifier collides with a packaged fixture")
    if motion["profile"] != sources["profile"]["id"]:
        fail("profile", "must match the selected packaged profile")
    duration = motion["duration_beats"]
    if not 0 <= duration <= _MAX_DURATION:
        fail("duration_beats", f"must be between 0 and {_MAX_DURATION}")
    if motion["rest_policy"]["policy"] != "base":
        fail("rest_policy.policy", "consumer source requires explicit base rest context")
    bases = {fixture["id"]: fixture for fixture in sources["diagnostics"]}
    base = motion["rest_policy"]["base_fixture"]
    if base not in bases or base == identifier:
        fail("rest_policy.base_fixture", "must identify an installed packaged fixture")
    controls = set(motion["controls"])
    if len(controls) != len(motion["controls"]):
        fail("controls", "duplicate body group")
    owner = {channel: group["id"] for group in sources["body-groups"]["groups"]
             for channel in group["channels"]}
    actions = {action["id"]: action for action in
               sources["mobility"]["actions"] + sources["mobility"]["placements"]}
    if not controls <= {group["id"] for group in sources["body-groups"]["groups"]}:
        fail("controls", "unknown body group")
    kind = motion["construction"]["type"]
    required_controls = {
        "rest": {"pelvis", "torso", "head_neck", "arm_L", "arm_R", "leg_L", "leg_R"},
        "squat_closed": {"pelvis", "torso", "leg_L", "leg_R", "arm_L", "arm_R"},
        "walking_flat": {"leg_L", "leg_R", "arm_L", "arm_R"},
        "forefoot_rocker": {"pelvis", "leg_L", "leg_R"},
    }.get(kind, set())
    if not required_controls <= controls:
        fail("controls", "omits a body group written by the selected constructor")
    writers = set()
    for track_index, track in enumerate(motion["tracks"]):
        channel = track["channel"]
        if channel not in actions:
            fail(f"tracks[{track_index}].channel", f"unknown channel {channel}")
        if channel in writers:
            fail(f"tracks[{track_index}].channel", "duplicate writer")
        writers.add(channel)
        if actions[channel].get("mode") in {"fixed", "coupled"}:
            fail(f"tracks[{track_index}].channel", "cannot write a dependent channel")
        if owner.get(channel) not in controls:
            fail(f"tracks[{track_index}].channel", "channel is outside declared controls")
        if channel in _constructor_channels(kind):
            fail(f"tracks[{track_index}].channel", "track is overwritten by its constructor")
        keys = track["keys"]
        beats = [key["beat"] for key in keys]
        if not beats or beats != sorted(set(beats)) or beats[-1] > duration:
            fail(f"tracks[{track_index}].keys", "keys must be nonempty, ordered, unique and within duration")
        if any(isinstance(beat, bool) or int(beat) != beat for beat in beats):
            fail(f"tracks[{track_index}].keys", "fractional key events are unsupported")

    construction = motion["construction"]
    start, end = construction["start_beat"], construction["end_beat"]
    if isinstance(start, bool) or isinstance(end, bool) or int(start) != start or int(end) != end:
        fail("construction", "constructor events must use integer beats")
    if not 0 <= start <= end <= duration:
        fail("construction", "constructor interval must lie within duration")
    if kind in {"squat_closed", "walking_flat", "forefoot_rocker"} and start == end:
        fail("construction", "dynamic constructor interval must be nonempty")

    if kind == "walking_flat":
        phases = construction.get("phases")
        if not phases:
            fail("construction.phases", "walking_flat requires nonempty phases")
        previous_end = -1
        for index, phase in enumerate(phases):
            phase_start, phase_end = phase["start_beat"], phase["end_beat"]
            if phase_start >= phase_end or phase_start < previous_end or phase_end > duration:
                fail(f"construction.phases[{index}]", "phases must be ordered, nonempty, non-overlapping and within duration")
            previous_end = phase_end
    elif construction.get("parameters") or construction.get("phases"):
        fail("construction", "walking parameters/phases are unsupported by this constructor")

    knots = construction.get("reference_knots", [])
    if kind == "forefoot_rocker":
        knot_beats = [row["beat"] for row in knots]
        if not knots or knot_beats != sorted(set(knot_beats)) or knot_beats[0] < start or knot_beats[-1] > end:
            fail("construction.reference_knots", "rocker knots must be ordered within the constructor interval")
        if any(isinstance(beat, bool) or int(beat) != beat for beat in knot_beats):
            fail("construction.reference_knots", "fractional events are unsupported")
    elif knots:
        fail("construction.reference_knots", "reference knots are only used by forefoot_rocker")

    channels = set(actions)
    for index, contact in enumerate(motion["contacts"]):
        start, end = contact["start_beat"], contact["end_beat"]
        if isinstance(start, bool) or isinstance(end, bool) or int(start) != start or int(end) != end:
            fail(f"contacts[{index}]", "contact events must use integer beats")
        if not 0 <= start <= end <= duration or (start == end and start != duration):
            fail(f"contacts[{index}]", "invalid contact interval")
        if len(contact["anchors"]) != len(contact["targets_m"]):
            fail(f"contacts[{index}]", "anchor and target counts differ")
        if len(set(contact["anchors"])) != len(contact["anchors"]):
            fail(f"contacts[{index}].anchors", "duplicate anchor")
        attachments_by_id = {attachment["id"]: body["id"]
                             for body in sources["profile"]["structures"]
                             for attachment in body["attachments"]}
        for anchor in contact["anchors"]:
            if anchor not in attachments_by_id:
                fail(f"contacts[{index}].anchors", f"unknown anchor {anchor}")
            if owner.get(attachments_by_id[anchor] + ".transform") != "leg_" + contact["foot"]:
                fail(f"contacts[{index}].anchors", f"anchor {anchor} belongs to the wrong side")
        for prior_index, prior in enumerate(motion["contacts"][:index]):
            overlap = max(start, prior["start_beat"]) < min(end, prior["end_beat"])
            if not overlap:
                continue
            if prior["foot"] == contact["foot"] and prior["state"] != contact["state"]:
                fail(f"contacts[{index}]", f"overlapping state conflicts with contacts[{prior_index}]")
            shared = set(prior["anchors"]) & set(contact["anchors"])
            for anchor in shared:
                left = prior["targets_m"][prior["anchors"].index(anchor)]
                right = contact["targets_m"][contact["anchors"].index(anchor)]
                if any(abs(a-b) > 1e-12 for a, b in zip(left, right)):
                    fail(f"contacts[{index}]", f"overlapping target conflicts for anchor {anchor}")
    terminal_feet = set()
    for index, terminal in enumerate(motion["terminal_contacts"]):
        if terminal["foot"] in terminal_feet:
            fail(f"terminal_contacts[{index}].foot", "duplicate terminal foot")
        terminal_feet.add(terminal["foot"])
        if terminal["state"] != "none" and not any(
                contact["foot"] == terminal["foot"] and contact["state"] == terminal["state"]
                for contact in motion["contacts"]):
            fail(f"terminal_contacts[{index}]", "terminal contact lacks a matching declaration")
    try:
        m.validate_quaternion(motion["world_root"]["orientation"])
    except ValueError as error:
        fail("world_root.orientation", str(error))
    # Cardinality is checked before the sampler allocates per-frame records.
    delivered_count(motion, bpms)
    resolved = deepcopy(motion)
    return resolved, {"scope": "consumer-kinematic-preflight/v1", "stature_m": stature_m,
                     "dense_step_beats": 0.01}


def delivered_count(motion: dict, bpms: tuple[int | float, ...]) -> int:
    duration = motion["duration_beats"]
    beats: set[Fraction] = set()
    for bpm in bpms:
        intervals = max(3, math.ceil(Fraction(300, 1) / Fraction(str(bpm))))
        if duration * intervals + 1 > _MAX_DELIVERED:
            raise ConsumerSampleBudgetError(
                f"{motion['id']} sampling: BPM {bpm} exceeds the {_MAX_DELIVERED} delivered-sample budget")
        for index in range(duration * intervals + 1):
            beats.add(Fraction(index, intervals))
            if len(beats) > _MAX_DELIVERED:
                raise ConsumerSampleBudgetError(
                    f"{motion['id']} sampling: requested BPMs exceed the {_MAX_DELIVERED} delivered-sample budget")
    return len(beats)


def resolve_consumer_document(document: dict, profile: str, sources: dict,
                              source_hashes: dict[str, str], *, stature_m: float,
                              bpms: tuple[int | float, ...]) -> dict:
    """Validate envelope, resolve one consumer movement and capture base lineage."""
    validate_document(document, "consumer-motion")
    motion = document["motion"]
    if motion.get("format") == "skeleton-diagnostic/v1":
        resolved = deepcopy(motion)
    elif motion.get("kind") == "skeleton-motion-variant":
        bases = {fixture["id"]: fixture for fixture in sources["diagnostics"]}
        base_id = motion["base_fixture"]
        if base_id not in bases:
            raise SourceValidationError(f"{motion['id']} base_fixture: unknown packaged fixture {base_id}")
        if motion["profile"] != profile:
            raise SourceValidationError(f"{motion['id']} profile: must match selected profile {profile}")
        resolved = _variant(bases[base_id], motion)
    else:
        raise SourceValidationError("motion: unsupported consumer source format")
    if resolved["profile"] != profile:
        raise SourceValidationError(f"{resolved.get('id', 'source')} profile: must match selected profile {profile}")
    packaged_ids = {fixture["id"] for fixture in sources["diagnostics"]}
    if resolved.get("id") in packaged_ids:
        raise SourceValidationError(f"{resolved['id']} id: consumer identifier collides with a packaged fixture")
    supplied = _validate_clearance(document, read_text("docs/used-materials.md"))
    resolved, validation = validate_resolved_motion(resolved, sources, stature_m=stature_m, bpms=bpms)

    # Resolve base ancestry exclusively through packaged fixture identifiers.
    fixtures = {fixture["id"]: fixture for fixture in sources["diagnostics"]}
    base_lineage = []
    visited = set()
    pending = [resolved["rest_policy"]["base_fixture"]]
    while pending:
        identifier = pending.pop()
        if identifier in visited:
            raise SourceValidationError(f"{resolved['id']} rest_policy: cyclic packaged base dependency")
        visited.add(identifier)
        if identifier not in fixtures:
            raise SourceValidationError(f"{resolved['id']} rest_policy: unresolved packaged base {identifier}")
        logical = f"rig/diagnostics/{identifier}.yaml"
        if logical not in source_hashes:
            raise SourceValidationError(f"{resolved['id']} rest_policy: packaged base hash missing for {identifier}")
        base_lineage.append({"id": identifier, "logical_path": logical,
                             "raw_sha256": source_hashes[logical]})
        parent = fixtures[identifier]["rest_policy"]["base_fixture"]
        if parent != identifier and parent not in visited:
            pending.append(parent)
    if motion.get("kind") == "skeleton-motion-variant":
        base_id = motion["base_fixture"]
        if base_id not in visited:
            # A variant's base is an explicit dependency even if it is not its
            # resolved rest pose.
            logical = f"rig/diagnostics/{base_id}.yaml"
            base_lineage.append({"id": base_id, "logical_path": logical,
                                 "raw_sha256": source_hashes[logical]})
    base_lineage.sort(key=lambda row: row["logical_path"])
    snapshot = {
        "format": "hml-consumer-motion-snapshot/v1",
        "document": deepcopy(document),
        "source_sha256": content_hash(document),
        "resolved_definition": deepcopy(resolved),
        "resolved_sha256": content_hash(resolved),
        "base_lineage": base_lineage,
        "validation": validation,
    }
    return {"resolved": resolved, "snapshot": snapshot, "clearances": supplied,
            "delivered_count": delivered_count(resolved, bpms)}


def preflight_consumer_motion(sources: dict, motion_id: str, bpms: tuple[int | float, ...],
                              snapshot: dict) -> dict:
    """Check every delivered/event/dense input against action and contact limits."""
    from humanmotionlib.actions import ActionError
    from humanmotionlib.contacts import attachments, contact_checks
    from humanmotionlib.diagnostics import DiagnosticEvaluator
    from humanmotionlib.measurements import measure_pose
    from humanmotionlib.sampling import delivered_beats

    fixture = next(item for item in sources["diagnostics"] if item["id"] == motion_id)
    duration = fixture["duration_beats"]
    points = {Fraction(index, 100) for index in range(duration * 100 + 1)}
    points.update(delivered_beats(duration, bpms))
    for track in fixture["tracks"]:
        points.update(Fraction(key["beat"]) for key in track["keys"])
    for contact in fixture["contacts"]:
        points.update((Fraction(contact["start_beat"]), Fraction(contact["end_beat"])))
    construction = fixture["construction"]
    points.update((Fraction(construction["start_beat"]), Fraction(construction["end_beat"])))
    for phase in construction.get("phases", []):
        points.update((Fraction(phase["start_beat"]), Fraction(phase["end_beat"])))
    for knot in construction.get("reference_knots", []):
        points.add(Fraction(knot["beat"]))

    evaluator = DiagnosticEvaluator(sources)
    history = {}
    checked_contacts = 0

    def failure(message, **details):
        error = SourceValidationError(message)
        error.consumer_details = {"source_id": motion_id, **details}
        return error

    for beat in sorted(points):
        try:
            solved = evaluator.evaluate(motion_id, float(beat))
        except ActionError as error:
            first = error.report.get("errors", [{}])[0]
            field = first.get("action", first.get("joint", "action"))
            raise failure(
                f"{motion_id} beat={float(beat):g} channel={field}: {first.get('condition', 'invalid action')}",
                field=field, beat=float(beat), channel=field,
                constraint=first.get("joint"), state=first.get("state"),
                measured=first.get("measured"), allowed=first.get("bounds"),
                condition=first.get("condition")) from error
        except (ValueError, KeyError, TypeError, ZeroDivisionError) as error:
            raise failure(
                f"{motion_id} beat={float(beat):g} constraint=kinematics: {error}",
                field="construction", beat=float(beat), constraint="kinematics",
                message=str(error)) from error
        report = measure_pose(sources["profile"], sources["mobility"], solved["frames"],
                              float(beat), solved["actions"], solved["world_root"])
        observed = attachments(sources["profile"], solved["frames"])
        contact_report = contact_checks(sources["profile"], solved["contacts"], observed,
                                        float(beat), history)
        checked_contacts += len(solved["contacts"])
        for check in report["checks"] + contact_report:
            if check["status"] != "pass":
                field = check.get("id", check.get("constraint", "measurement"))
                raise failure(
                    f"{motion_id} beat={float(beat):g} constraint={field}: "
                    f"measured={check.get('measured')} allowed={check.get('expected')} "
                    f"residual={check.get('residual')} unit={check.get('unit')}",
                    field=field, beat=float(beat), constraint=field,
                    measured=check.get("measured"), allowed=check.get("expected"),
                    residual=check.get("residual"), unit=check.get("unit"),
                    state=check.get("status"))
    result = deepcopy(snapshot)
    result["validation"].update({
        "delivered_samples": delivered_count(fixture, bpms),
        "checked_samples": len(points),
        "checked_contacts": checked_contacts,
    })
    return result


def verify_consumer_snapshot(snapshot: dict, sources: dict, source_hashes: dict[str, str],
                             profile_id: str, bpms: tuple[int | float, ...], stature_m: float):
    """Re-resolve a sealed source and compare its package lineage before render."""
    validate_document(snapshot, "consumer-motion-snapshot")
    document = snapshot["document"]
    if content_hash(document) != snapshot["source_sha256"]:
        raise SourceValidationError("consumer source snapshot hash mismatch")
    if content_hash(snapshot["resolved_definition"]) != snapshot["resolved_sha256"]:
        raise SourceValidationError("consumer resolved source hash mismatch")
    resolution = resolve_consumer_document(document, profile_id, sources, source_hashes,
                                           stature_m=stature_m, bpms=bpms)
    resolved = resolution["resolved"]
    if canonical_bytes(resolved) != canonical_bytes(snapshot["resolved_definition"]):
        raise SourceValidationError("consumer source no longer resolves to the sealed definition")
    if canonical_bytes(resolution["snapshot"]["base_lineage"]) != canonical_bytes(snapshot["base_lineage"]):
        raise SourceValidationError("consumer base lineage does not match fresh packaged-base resolution")
    expected_lineage = snapshot["base_lineage"]
    for item in expected_lineage:
        logical = item["logical_path"]
        if logical not in source_hashes or source_hashes[logical] != item["raw_sha256"]:
            raise SourceValidationError(f"consumer packaged base lineage mismatch: {logical}")
        if hashlib.sha256(read_bytes(logical)).hexdigest() != item["raw_sha256"]:
            raise SourceValidationError(f"consumer packaged base resource changed: {logical}")
    return resolved

