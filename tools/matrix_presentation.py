#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build a recoverable presentation from validated HML render outputs."""
from __future__ import annotations

from fractions import Fraction
import hashlib
import html
import json
import os
from pathlib import Path, PurePosixPath
import stat
from typing import Any, Mapping, Sequence


class PresentationError(ValueError):
    """Producer evidence is incomplete, stale, or unsafe to present."""


def _read_json(path: Path) -> dict[str, Any]:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise PresentationError(f"duplicate JSON field {key!r} in {path}")
            result[key] = value
        return result

    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)
    except (OSError, json.JSONDecodeError) as exc:
        raise PresentationError(f"cannot read producer JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PresentationError(f"expected a JSON object in {path}")
    return value


def _no_symlink_path(path: Path, workspace: Path) -> None:
    """Check owned path components without mistaking macOS /var for a symlink attack."""
    absolute = Path(os.path.abspath(path))
    workspace_absolute = Path(os.path.abspath(workspace))
    try:
        relative = absolute.relative_to(workspace_absolute)
    except ValueError as exc:
        raise PresentationError(f"producer or output path is outside workspace: {path}") from exc
    current = workspace_absolute.resolve(strict=True)
    for part in relative.parts:
        current /= part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise PresentationError(f"symlink path component is not allowed: {current}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _fraction(value: Mapping[str, Any]) -> Fraction:
    if (not isinstance(value, Mapping) or set(value) != {"numerator", "denominator"}
            or type(value["numerator"]) is not int or type(value["denominator"]) is not int
            or value["denominator"] <= 0):
        raise PresentationError(f"invalid rational time value: {value!r}")
    return Fraction(value["numerator"], value["denominator"])


def _safe_relative(value: Any, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise PresentationError(f"invalid relative path for {label}: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise PresentationError(f"unsafe relative path for {label}: {value!r}")
    return path


def _verify_prepared_timeline(prepared: Mapping[str, Any], fixtures: Sequence[str]):
    plans = {}
    for fixture in fixtures:
        group = prepared.get("sampling", {}).get(fixture)
        if not isinstance(group, list) or not group:
            raise PresentationError(f"prepared input has no sampling plan for {fixture!r}")
        for plan in group:
            bpm = plan.get("bpm")
            static, animation = plan.get("static"), plan.get("animation")
            if (not isinstance(bpm, (int, float)) or bpm <= 0 or not isinstance(static, list)
                    or not static or not isinstance(animation, list) or not animation):
                raise PresentationError(f"malformed sample plan for {fixture!r} at {bpm!r} BPM")
            for mode, entries in (("static", static), ("animation", animation)):
                ids = [row.get("sample_id") for row in entries]
                beats = [_fraction(row.get("beat")) for row in entries]
                seconds = [_fraction(row.get("seconds")) for row in entries]
                if (any(not isinstance(sample_id, str) for sample_id in ids)
                        or len(ids) != len(set(ids)) or beats != sorted(beats)):
                    raise PresentationError(f"invalid {fixture}/{bpm} {mode} timeline")
                if mode == "animation" and seconds != sorted(set(seconds)):
                    raise PresentationError(f"non-increasing {fixture}/{bpm} animation timeline")
            plans[(fixture, bpm)] = plan
    return plans


def _validate_producer(prepared_path: Path, manifest_path: Path, frames_base: Path,
                       character_ids: Sequence[str], workspace: Path):
    from humanmotionlib.prepared import read_prepared
    from humanmotionlib.render_contract import (
        read_supervised_receipt, validate_character_manifest, validate_manifest,
    )

    for path in (prepared_path, manifest_path, frames_base):
        _no_symlink_path(path, workspace)
    try:
        prepared_path = prepared_path.resolve(strict=True)
        manifest_path = manifest_path.resolve(strict=True)
        frames_base = frames_base.resolve(strict=True)
    except OSError as exc:
        raise PresentationError(f"prepared input, render manifest, or declared frames base is missing: {exc}") from exc
    if not prepared_path.is_file() or not manifest_path.is_file() or not frames_base.is_dir():
        raise PresentationError("prepared input, render manifest, and frames base must exist")
    try:
        prepared = read_prepared(prepared_path)
        manifest = _read_json(manifest_path)
        producer_root = manifest_path.parent.resolve(strict=True)
        if frames_base.parent != producer_root:
            raise PresentationError("frames base must be the producer run's direct frames directory")
        if manifest.get("prepared_sha256") != prepared.get("content_sha256"):
            raise PresentationError("render manifest and prepared input identities differ")
        if manifest.get("format") == "character-render-manifest/v1":
            required = validate_character_manifest(
                manifest, prepared, frames_base, output=producer_root,
                character_ids=tuple(character_ids))
        elif isinstance(manifest.get("samples"), list):
            if tuple(character_ids) != ("skeleton",):
                raise PresentationError("skeleton manifest requires character_ids=('skeleton',)")
            required = validate_manifest(manifest, prepared, frames_base, output=producer_root)
        else:
            raise PresentationError(f"unsupported render manifest format {manifest.get('format')!r}")
        read_supervised_receipt(producer_root, prepared, required)
    except PresentationError:
        raise
    except (ValueError, TypeError, KeyError, OSError) as exc:
        raise PresentationError(f"render producer validation failed: {exc}") from exc

    image_rows = []
    members = manifest.get("characters", [{"id": "skeleton", "samples": manifest.get("samples")}])
    for member in members:
        character = member["id"]
        if character not in character_ids:
            continue
        for sample in member["samples"]:
            for view, relative in sorted(sample["images"].items()):
                rel = _safe_relative(relative, f"{character}/{sample['id']}/{view}")
                source = (frames_base / Path(*rel.parts)).resolve(strict=True)
                try:
                    source.relative_to(frames_base)
                except ValueError as exc:
                    raise PresentationError(f"render image escapes frames base: {relative}") from exc
                image_rows.append({"character": character, "sample_id": sample["id"], "view": view,
                                   "path": str(rel), "sha256": _sha256(source), "source": source})
    return prepared, manifest, producer_root, frames_base, image_rows


def _fresh_output(output: Path, workspace: Path,
                  matrix_element_root: str | Path | None = None) -> Path:
    from humanmotionlib.runtime import validate_run_root
    try:
        if matrix_element_root is None:
            root = validate_run_root(output, workspace)
        else:
            element = validate_run_root(Path(matrix_element_root), workspace)
            root = Path(output).resolve(strict=False)
            if root != element / "presentation":
                raise ValueError("matrix presentation output must be the declared element presentation/ destination")
            resolved_element = element.resolve(strict=True)
            if root.parent.resolve(strict=True) != resolved_element:
                raise ValueError("matrix presentation output must be directly inside its stable element root")
    except (ValueError, OSError) as exc:
        raise PresentationError(str(exc)) from exc
    _no_symlink_path(root, Path(workspace).resolve(strict=True))
    try:
        mode = root.lstat().st_mode
    except FileNotFoundError as exc:
        raise PresentationError(f"presentation output run must be allocated by its caller: {root}") from exc
    if not stat.S_ISDIR(mode) or any(root.iterdir()):
        raise PresentationError(f"presentation output run must be a fresh empty caller-owned directory: {root}")
    return root


def assemble_presentation(prepared_path: str | Path, render_manifest_path: str | Path,
                          frames_base: str | Path, output_run: str | Path, *,
                          workspace: str | Path, character_ids: Sequence[str],
                          matrix_element_root: str | Path | None = None,
                          fixtures: Sequence[str] | None = None,
                          metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Assemble a fresh presentation run from validated raw renders, without Blender."""
    from humanmotionlib.review_graphics import gif, onion, sheet
    from PIL import Image

    if (isinstance(character_ids, (str, bytes)) or not character_ids
            or any(not isinstance(c, str) or not c for c in character_ids)
            or len(set(character_ids)) != len(character_ids)):
        raise PresentationError("character_ids must be a nonempty unique sequence")
    workspace_input = Path(os.path.abspath(workspace))
    workspace_path = workspace_input.resolve(strict=True)
    prepared, manifest, producer_root, frames_path, images = _validate_producer(
        Path(prepared_path), Path(render_manifest_path), Path(frames_base),
        tuple(character_ids), workspace_input)
    selected = sorted(prepared.get("sampling", {})) if fixtures is None else list(fixtures)
    if (not selected or len(selected) != len(set(selected))
            or any(not isinstance(f, str) or f not in prepared.get("sampling", {}) for f in selected)):
        raise PresentationError("fixtures must be a unique nonempty subset of prepared fixture IDs")
    plans = _verify_prepared_timeline(prepared, selected)
    output = _fresh_output(Path(output_run), workspace_path, matrix_element_root)
    lookup = {(r["character"], r["sample_id"], r["view"]): r for r in images}
    produced: list[dict] = []
    timings: list[dict] = []

    for fixture in selected:
        fixture_plans = sorted(((bpm, plan) for (item_fixture, bpm), plan in plans.items()
                                if item_fixture == fixture), key=lambda pair: pair[0])
        for bpm, plan in fixture_plans:
            static, animation = plan["static"], plan["animation"]
            views = sorted({row["view"] for row in images
                            if row["sample_id"] in {s["sample_id"] for s in static}})
            for view in views:
                characters = [c for c in character_ids
                              if all((c, entry["sample_id"], view) in lookup for entry in static)]
                if not characters:
                    continue
                count_target = output / f"{fixture}-{bpm}-{view}-counts.png"
                count_paths = [lookup[(c, entry["sample_id"], view)]["source"]
                               for entry in static for c in characters]
                captions = [f"{fixture} {Fraction(entry['beat']['numerator'], entry['beat']['denominator'])} {c}"
                            for entry in static for c in characters]
                sheet(count_paths, captions, count_target, columns=len(characters))
                with Image.open(count_target) as image:
                    produced.append({"path": count_target.name, "kind": "count-sheet",
                                     "width_px": image.width, "height_px": image.height,
                                     "sha256": _sha256(count_target)})

                interval_rows = animation
                times = [_fraction(row["seconds"]) for row in interval_rows]
                if len(times) < 2:
                    continue
                if any(b - a != times[1] - times[0] for a, b in zip(times, times[1:])):
                    raise PresentationError(f"invalid animation interval sequence for {fixture}/{bpm}")
                interval = times[1] - times[0]
                for character in characters:
                    keys = [(character, row["sample_id"], view) for row in interval_rows]
                    if any(key not in lookup for key in keys):
                        raise PresentationError(f"missing animation frame for {fixture}/{bpm}/{character}/{view}")
                    target = output / f"{fixture}-{bpm}-{character}-{view}.gif"
                    timing = gif([lookup[key]["source"] for key in keys], interval, target)
                    if timing.get("status") != "pass":
                        raise PresentationError(f"GIF duration validation failed: {target.name}: {timing}")
                    with Image.open(target) as image:
                        produced.append({"path": target.name, "kind": "animation-gif",
                                         "width_px": image.width, "height_px": image.height,
                                         "sha256": _sha256(target)})
                    timings.append({"fixture": fixture, "bpm": bpm, "character": character,
                                    "view": view, **timing})
                    onion_keys = [(character, row["sample_id"], view) for row in static]
                    onion_target = output / f"{fixture}-{bpm}-{character}-{view}-onion.png"
                    onion([lookup[key]["source"] for key in onion_keys], onion_target)
                    with Image.open(onion_target) as image:
                        produced.append({"path": onion_target.name, "kind": "onion-skin",
                                         "width_px": image.width, "height_px": image.height,
                                         "sha256": _sha256(onion_target)})

    source_images = [{k: row[k] for k in ("character", "sample_id", "view", "path", "sha256")}
                     for row in images]
    inventory = {
        "schema": "matrix-presentation-inventory/v1",
        "prepared_sha256": prepared["content_sha256"],
        "render_identity": manifest.get("render_identity"),
        "producer_manifest": str(Path(render_manifest_path).resolve()),
        "frames_base": str(frames_path),
        "selected_fixtures": selected,
        "characters": list(character_ids),
        "source_images": source_images,
        "media": produced,
        "gif_timing": timings,
        "metadata": dict(metadata or {}),
    }
    (output / "presentation-inventory.json").write_text(
        json.dumps(inventory, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    cards = "".join(
        f'<figure><img src="{html.escape(item["path"], quote=True)}" alt="{html.escape(item["path"], quote=True)}">'
        f'<figcaption><a href="{html.escape(item["path"], quote=True)}">{html.escape(item["path"])}</a></figcaption></figure>'
        for item in produced)
    media_list = "".join(
        f'<li><a href="{html.escape(item["path"], quote=True)}">{html.escape(item["path"])}</a> ({html.escape(item["kind"])})</li>'
        for item in produced)
    source_list = "".join(
        f'<li>{html.escape(row["character"])} / {html.escape(row["sample_id"])} / {html.escape(row["view"])} — '
        f'<a href="{html.escape(os.path.relpath(str(frames_path / row["path"]), str(output)), quote=True)}">{html.escape(row["path"])}</a></li>'
        for row in source_images)
    facts = "".join(f"<dt>{html.escape(str(k))}</dt><dd>{html.escape(str(v))}</dd>"
                     for k, v in sorted((metadata or {}).items()))
    (output / "index.html").write_text(
        "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>Matrix presentation</title><style>"
        "body{font:16px system-ui;max-width:1200px;margin:auto;padding:1rem;color:#18212b}"
        ".media{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:1rem}"
        "figure{margin:0;padding:.6rem;border:1px solid #ccd3da;border-radius:.4rem}"
        "figure img{display:block;max-width:100%;height:auto;object-fit:contain;margin:auto}"
        "a{overflow-wrap:anywhere}details{margin:1rem 0}</style><body><h1>Matrix presentation</h1>"
        f"<dl>{facts}</dl><p><a href=\"presentation-inventory.json\">Complete media and timing inventory</a></p>"
        f"<section class=\"media\">{cards}</section>"
        f"<h2>Generated media</h2><ul>{media_list}</ul>"
        f"<details><summary>All validated source images</summary><ul>{source_list}</ul></details></body></html>\n",
        encoding="utf-8")
    return {"output_run": str(output), "index": "index.html",
            "inventory": "presentation-inventory.json",
            "media_count": len(produced),
            "source_image_count": len(source_images), "gif_timing": timings}


def validate_presentation_inventory(inventory_path: str | Path, output_run: str | Path, *,
                                    prepared_path: str | Path, render_manifest_path: str | Path,
                                    frames_base: str | Path, workspace: str | Path,
                                    character_ids: Sequence[str], fixtures: Sequence[str]
                                    ) -> dict[str, Any]:
    """Read-only validation of an existing presentation against sealed render inputs."""
    from PIL import Image, ImageChops, ImageOps, ImageStat

    workspace_path = Path(workspace).resolve(strict=True)
    output = Path(output_run)
    inventory_file = Path(inventory_path)
    index_file = output / "index.html"
    for path in (output, inventory_file, index_file):
        _no_symlink_path(path, workspace_path)
    if output.is_symlink() or not output.is_dir():
        raise PresentationError("presentation output root is missing or linked")
    if inventory_file.parent.resolve(strict=True) != output.resolve(strict=True):
        raise PresentationError("presentation inventory is outside its declared output run")
    if index_file.is_symlink() or not index_file.is_file():
        raise PresentationError("presentation index is missing or linked")
    prepared, manifest, producer_root, frames, source_rows = _validate_producer(
        Path(prepared_path), Path(render_manifest_path), Path(frames_base),
        tuple(character_ids), workspace_path)
    inventory = _read_json(inventory_file)
    metadata = inventory.get("metadata")
    if (inventory.get("schema") != "matrix-presentation-inventory/v1"
            or inventory.get("prepared_sha256") != prepared.get("content_sha256")
            or inventory.get("render_identity") != manifest.get("render_identity")
            or inventory.get("producer_manifest") != str(Path(render_manifest_path).resolve(strict=True))
            or inventory.get("frames_base") != str(frames)
            or inventory.get("characters") != list(character_ids)
            or inventory.get("selected_fixtures") != list(fixtures)
            or not isinstance(metadata, dict)):
        raise PresentationError("presentation identity or selected scope is stale")

    expected_sources = [{key: row[key] for key in ("character", "sample_id", "view", "path", "sha256")}
                        for row in source_rows]
    if inventory.get("source_images") != expected_sources:
        raise PresentationError("presentation source-image links or hashes differ from validated render output")

    plans = _verify_prepared_timeline(prepared, fixtures)
    expected_media: set[tuple[str, str]] = set()
    expected_timings: set[tuple[str, int, str, str]] = set()
    source_by_key = {(row["character"], row["sample_id"], row["view"]): row for row in source_rows}
    for fixture in fixtures:
        for (plan_fixture, bpm), timeline in plans.items():
            if plan_fixture != fixture:
                continue
            static, animation = timeline["static"], timeline["animation"]
            sample_ids = {entry["sample_id"] for entry in static}
            views = sorted({row["view"] for row in source_rows if row["sample_id"] in sample_ids})
            for view in views:
                characters = [character for character in character_ids
                              if all((character, entry["sample_id"], view) in source_by_key for entry in static)]
                if not characters:
                    continue
                expected_media.add(("count-sheet", f"{fixture}-{bpm}-{view}-counts.png"))
                if len(animation) < 2:
                    continue
                interval = _fraction(animation[1]["seconds"]) - _fraction(animation[0]["seconds"])
                expected_duration = float(interval * (len(animation) - 1) * 1000)
                for character in characters:
                    name = f"{fixture}-{bpm}-{character}-{view}"
                    expected_media.add(("animation-gif", f"{name}.gif"))
                    expected_media.add(("onion-skin", f"{name}-onion.png"))
                    expected_timings.add((fixture, bpm, character, view))

    media = inventory.get("media")
    if not isinstance(media, list):
        raise PresentationError("presentation media inventory is absent")
    actual_media = []
    for row in media:
        if not isinstance(row, dict):
            raise PresentationError("presentation media member is malformed")
        relative = _safe_relative(row.get("path"), "presentation output")
        path = output.joinpath(*relative.parts)
        _no_symlink_path(path, workspace_path)
        if not path.is_file() or _sha256(path) != row.get("sha256"):
            raise PresentationError(f"presentation media is missing or altered: {path}")
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            kind = row.get("kind")
        actual_media.append((row.get("kind"), row.get("path")))
    if len(actual_media) != len(set(actual_media)) or set(actual_media) != expected_media:
        raise PresentationError("presentation count/GIF/onion membership is incomplete or unexpected")

    index_text = index_file.read_text(encoding="utf-8")
    for _, path in expected_media:
        if html.escape(path, quote=True) not in index_text:
            raise PresentationError(f"presentation index omits media link {path}")
    for source in expected_sources:
        if html.escape(source["path"], quote=True) not in index_text:
            raise PresentationError(f"presentation index omits source-image link {source['path']}")
    timing_rows = inventory.get("gif_timing")
    if not isinstance(timing_rows, list):
        raise PresentationError("presentation GIF timing inventory is absent")
    actual_timings = [(item.get("fixture"), item.get("bpm"), item.get("character"), item.get("view"))
                      for item in timing_rows if isinstance(item, dict)]
    if len(actual_timings) != len(set(actual_timings)) or set(actual_timings) != expected_timings:
        raise PresentationError("presentation GIF timing membership is incomplete or unexpected")
    for row in timing_rows:
        key = (row["fixture"], row["bpm"], row["character"], row["view"])
        timeline = plans[(row["fixture"], row["bpm"])]["animation"]
        interval = _fraction(timeline[1]["seconds"]) - _fraction(timeline[0]["seconds"])
        expected_duration = float(interval * (len(timeline) - 1) * 1000)
        expected_durations = []
        previous = 0
        for frame_index in range(len(timeline) - 1):
            rounded = round(Fraction(frame_index + 1) * interval * 100) * 10
            expected_durations.append(rounded - previous)
            previous = rounded
        gif_path = output / f"{key[0]}-{key[1]}-{key[2]}-{key[3]}.gif"
        with Image.open(gif_path) as image:
            if image.n_frames != len(timeline) - 1:
                raise PresentationError(f"GIF frame count differs from prepared timeline: {gif_path.name}")
            durations = []
            for frame_index in range(image.n_frames):
                image.seek(frame_index)
                durations.append(image.info.get("duration"))
            decoded = sum(value for value in durations if isinstance(value, (int, float)))
        if (row.get("status") != "pass" or row.get("expected_duration_ms") != expected_duration
                or row.get("decoded_duration_ms") != decoded or abs(decoded - expected_duration) >= 10
                or durations != expected_durations):
            raise PresentationError(f"GIF timing differs from prepared timeline: {gif_path.name}")
        # Confirm ordered GIF frames correspond to the ordered animation sources.
        with Image.open(gif_path) as image:
            for frame_index, sample in enumerate(timeline[:-1]):
                source = source_by_key[(key[2], sample["sample_id"], key[3])]
                with Image.open(frames / source["path"]) as source_image:
                    target = ImageOps.pad(source_image.convert("RGB"), (512, 512),
                                          method=Image.Resampling.LANCZOS, color=(245, 247, 248))
                image.seek(frame_index)
                actual = image.convert("RGB")
                difference = ImageChops.difference(target, actual)
                if ImageStat.Stat(difference.convert("L")).mean[0] > 28:
                    raise PresentationError(f"GIF frame order/content differs from source timeline: {gif_path.name}")
    return {"identity": "pass", "links": "pass", "gif_timing": "pass",
            "media_count": len(media), "source_image_count": len(source_rows),
            "gif_count": len(timing_rows)}
