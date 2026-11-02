# SPDX-License-Identifier: Apache-2.0
"""Validation for sealed dense surface-audit samples."""

from __future__ import annotations

import math
from typing import Any, Mapping


def _finite_tree(value: Any) -> bool:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_finite_tree(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _finite_tree(item) for key, item in value.items())
    return False


def _finite_numeric_tree(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return isinstance(value, list) and all(_finite_numeric_tree(item) for item in value)
    return math.isfinite(value)


def expected_midpoint_inventory(prepared: Mapping[str, Any]) -> list[tuple[str, float]]:
    """Return the ordered un-delivered midpoint set implied by prepared sources."""
    fixture_samples = {
        fixture: {sample["beat"]["numerator"] / sample["beat"]["denominator"]
                  for sample in prepared["samples"] if sample["fixture"] == fixture}
        for fixture in sorted({sample["fixture"] for sample in prepared["samples"]})
    }
    diagnostics = {row["id"]: row for row in prepared["sources"]["diagnostics"]}
    expected: list[tuple[str, float]] = []
    for fixture_id, delivered_beats in fixture_samples.items():
        if fixture_id not in diagnostics:
            raise ValueError("prepared input is missing midpoint fixture " + fixture_id)
        fixture = diagnostics[fixture_id]
        key_beats = sorted({float(key["beat"]) for track in fixture.get("tracks", [])
                            for key in track.get("keys", [])})
        for left, right in zip(key_beats, key_beats[1:]):
            beat = (left + right) / 2.0
            if any(abs(beat - delivered) < 1e-10 for delivered in delivered_beats):
                continue
            expected.append((fixture_id, beat))
    return expected


def validate_native_midpoint_samples(prepared: Mapping[str, Any], dense_samples: Any) -> list[dict[str, Any]]:
    """Fail closed on missing, duplicate, malformed or carrier-incomplete records."""
    if not isinstance(dense_samples, list):
        raise ValueError("sealed character render request is missing native midpoint samples")
    expected = expected_midpoint_inventory(prepared)
    if len(dense_samples) != len(expected):
        raise ValueError("sealed native midpoint inventory count mismatch")
    sample_rows = prepared["samples"]
    frame_ids = set(sample_rows[0]["frames"]) if sample_rows else set()
    guide_reference = sample_rows[0]["guides"] if sample_rows else {}
    guide_ids = set(guide_reference)
    seen: set[str] = set()
    required_fields = {"id", "fixture", "beat", "frames", "guides", "world_root", "contacts"}
    for index, (record, (fixture_id, beat)) in enumerate(zip(dense_samples, expected)):
        if not isinstance(record, dict) or set(record) != required_fields:
            raise ValueError("sealed native midpoint record fields are malformed")
        identifier = f"{fixture_id}/native-midpoint/{index:05d}"
        if (record.get("id") != identifier or identifier in seen
                or record.get("fixture") != fixture_id or record.get("beat") != beat):
            raise ValueError("sealed native midpoint identity/order mismatch")
        seen.add(identifier)
        frames = record.get("frames")
        if not isinstance(frames, dict) or set(frames) != frame_ids:
            raise ValueError("sealed native midpoint carrier inventory mismatch")
        for carrier, frame in frames.items():
            if not isinstance(frame, dict) or set(frame) != {"position_m", "rotation"}:
                raise ValueError("sealed native midpoint frame is malformed: " + carrier)
            position, rotation = frame["position_m"], frame["rotation"]
            if (not isinstance(position, list) or len(position) != 3
                    or not isinstance(rotation, list) or len(rotation) != 3
                    or any(not isinstance(row, list) or len(row) != 3 for row in rotation)
                    or not _finite_numeric_tree(position) or not _finite_numeric_tree(rotation)):
                raise ValueError("sealed native midpoint frame shape/value is invalid: " + carrier)
        guides = record.get("guides")
        if not isinstance(guides, dict) or set(guides) != guide_ids:
            raise ValueError("sealed native midpoint guide inventory mismatch")
        for guide, points in guides.items():
            if (not isinstance(points, list) or len(points) != len(guide_reference[guide])
                    or any(not isinstance(point, list) or len(point) != 3 or not _finite_numeric_tree(point)
                           for point in points)):
                raise ValueError("sealed native midpoint guide is malformed: " + guide)
        root = record.get("world_root")
        if (not isinstance(root, dict) or set(root) != set(sample_rows[0]["world_root"])
                or not _finite_tree(root)):
            raise ValueError("sealed native midpoint world-root is malformed")
        contacts = record.get("contacts")
        if (not isinstance(contacts, list) or not _finite_tree(contacts)
                or any(not isinstance(contact, dict) for contact in contacts)):
            raise ValueError("sealed native midpoint contacts are malformed")
    return dense_samples
