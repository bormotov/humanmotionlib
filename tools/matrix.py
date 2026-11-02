#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build and check one fixed character and stature preview at a time."""
from __future__ import annotations

import argparse
import base64
import codecs
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import traceback
import inspect
from fractions import Fraction
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
_old_dont_write_bytecode = sys.dont_write_bytecode
sys.dont_write_bytecode = True
from matrix_presentation import (  # noqa: E402
    PresentationError, assemble_presentation, validate_presentation_inventory,
)
sys.dont_write_bytecode = _old_dont_write_bytecode

CHANGE = "automate-build-and-verification-matrix"
CHARACTERS = ("skeleton", "male", "female")
HEIGHTS = (1.50, 1.70, 1.90)
FIXTURES = ("neutral", "rest", "arm-raise")
HUMAN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class MatrixError(ValueError):
    pass


def element_root(workspace: Path, character: str, height: float) -> Path:
    height_key = f"h{int(round(height * 100)):03d}"
    name = f"{CHANGE}_r1_dev_current_{character}-{height_key}"
    if len(name.split("_")) != 5 or not all(HUMAN.fullmatch(item) for item in name.split("_")):
        raise MatrixError("internal matrix result path is invalid")
    return workspace / "build" / name


def selection(args: argparse.Namespace, *, workspace_arg: str | None = None) -> tuple[Path, Path, str, float]:
    workspace = Path(workspace_arg or args.workspace).expanduser()
    if not workspace.is_absolute():
        raise MatrixError("workspace must be an absolute path")
    workspace = workspace.resolve(strict=True)
    character = getattr(args, "character", None)
    height_text = getattr(args, "height", None)
    if character not in CHARACTERS:
        raise MatrixError(f"unknown character {character!r}; choose one of {', '.join(CHARACTERS)}")
    try:
        height = float(height_text)
    except (TypeError, ValueError):
        raise MatrixError("HEIGHT must be one of 1.50, 1.70, or 1.90") from None
    if height not in HEIGHTS:
        raise MatrixError("HEIGHT must be one of 1.50, 1.70, or 1.90")
    return workspace, element_root(workspace, character, height), character, height


def table(workspace: Path) -> list[dict[str, Any]]:
    return [{"character": character, "height_m": height,
             "path": str(element_root(workspace, character, height))}
            for character in CHARACTERS for height in HEIGHTS]


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_name(path.name + ".tmp")
    try:
        temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def no_symlink(path: Path, workspace: Path) -> None:
    absolute = Path(os.path.abspath(path))
    try:
        relative = absolute.relative_to(workspace)
    except ValueError as exc:
        raise MatrixError(f"path escapes workspace: {path}") from exc
    cursor = workspace
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise MatrixError(f"symlink component is not allowed: {cursor}")


def preserve_render_failure_diagnostics(stream, error: BaseException, root: Path,
                                        workspace: Path) -> None:
    """Retain failed render receipt details and complete output logs before cleanup."""
    try:
        details = getattr(error, "details", {})
        receipt = details.get("supervisor_outcome") if isinstance(details, dict) else None
        receipt_path = getattr(error, "receipt_path", None)
        render_root = Path(os.path.abspath(root / "render"))

        def safe_render_file(value: Any) -> Path:
            if not isinstance(value, (str, os.PathLike)):
                raise MatrixError("backend evidence path is not a path string")
            candidate = Path(value)
            if not candidate.is_absolute() or ".." in candidate.parts:
                raise MatrixError("backend evidence path must be absolute and traversal-free")
            normalized = Path(os.path.abspath(candidate))
            if not normalized.is_relative_to(render_root):
                raise MatrixError("backend evidence path is outside the selected render output")
            no_symlink(normalized, workspace)
            resolved = normalized.resolve(strict=True)
            if not resolved.is_relative_to(render_root.resolve(strict=True)) or not resolved.is_file():
                raise MatrixError("backend evidence path is not a regular file in the selected render output")
            return resolved

        receipt_file = None
        receipt_path_error = None
        if receipt_path:
            try:
                receipt_file = safe_render_file(receipt_path)
            except (MatrixError, OSError) as path_error:
                receipt_path_error = str(path_error)
        if not isinstance(receipt, dict) and receipt_file is not None:
            receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
        if not isinstance(receipt, dict):
            return

        summary_keys = ("operation", "outcome", "return_code", "signal", "error",
                        "last_script_phase", "phases", "cleanup", "output_validation",
                        "spawn_error", "cancellation")
        summary = {key: receipt[key] for key in summary_keys if key in receipt}
        summary["receipt_path"] = str(receipt_file) if receipt_file else None
        if receipt_path_error:
            summary["receipt_path_error"] = receipt_path_error
        diagnostic_streams = {}
        for label in ("stdout", "stderr"):
            raw_path = receipt.get(f"{label}_log")
            if not isinstance(raw_path, str):
                continue
            try:
                source = safe_render_file(raw_path)
                digest = hashlib.sha256()
                byte_count = 0
                utf8_decoder = codecs.getincrementaldecoder("utf-8")("strict")
                utf8_valid = True
                with source.open("rb") as input_stream:
                    while chunk := input_stream.read(64 * 1024):
                        digest.update(chunk)
                        byte_count += len(chunk)
                        if utf8_valid:
                            try:
                                utf8_decoder.decode(chunk)
                            except UnicodeDecodeError:
                                utf8_valid = False
                    if utf8_valid:
                        try:
                            utf8_decoder.decode(b"", final=True)
                        except UnicodeDecodeError:
                            utf8_valid = False
                encoding = "utf-8-json-chunks" if utf8_valid else "base64"
                stream.write(f"backend_stream_begin label={label} source={source} bytes={byte_count} "
                             f"encoding={encoding}\n")
                copied_hash = hashlib.sha256()
                copied_bytes = 0
                if utf8_valid:
                    decoder = codecs.getincrementaldecoder("utf-8")("strict")
                    with source.open("rb") as input_stream:
                        while chunk := input_stream.read(8192):
                            copied_hash.update(chunk)
                            copied_bytes += len(chunk)
                            decoded = decoder.decode(chunk)
                            if decoded:
                                stream.write(f"backend_stream_text label={label} "
                                             f"{json.dumps(decoded, ensure_ascii=False)}\n")
                        decoded = decoder.decode(b"", final=True)
                        if decoded:
                            stream.write(f"backend_stream_text label={label} "
                                         f"{json.dumps(decoded, ensure_ascii=False)}\n")
                else:
                    carry = b""
                    with source.open("rb") as input_stream:
                        while chunk := input_stream.read(3 * 8192):
                            copied_hash.update(chunk)
                            copied_bytes += len(chunk)
                            packed = carry + chunk
                            aligned = len(packed) - (len(packed) % 3)
                            carry = packed[aligned:]
                            encoded = base64.b64encode(packed[:aligned]).decode("ascii")
                            for offset in range(0, len(encoded), 76):
                                stream.write(f"backend_stream_base64 label={label} "
                                             f"{encoded[offset:offset + 76]}\n")
                        if carry:
                            encoded = base64.b64encode(carry).decode("ascii")
                            stream.write(f"backend_stream_base64 label={label} {encoded}\n")
                copied_digest = copied_hash.hexdigest()
                diagnostic_streams[label] = {
                    "source_path": str(source), "bytes": byte_count,
                    "sha256": digest.hexdigest(), "encoding": encoding,
                    "complete": copied_bytes == byte_count and copied_digest == digest.hexdigest(),
                }
                stream.write(f"backend_stream_end label={label} bytes={copied_bytes} "
                             f"sha256={copied_digest} complete={diagnostic_streams[label]['complete']}\n")
            except (MatrixError, OSError) as path_error:
                diagnostic_streams[label] = {"source_path": raw_path, "error": str(path_error)}
        stream.write("backend_receipt_summary=" + json.dumps(summary, sort_keys=True) + "\n")
        stream.write("backend_diagnostic_streams=" + json.dumps(diagnostic_streams, sort_keys=True) + "\n")
        stream.flush()
    except Exception as capture_error:
        stream.write("backend_diagnostics_capture_failed="
                     + str(capture_error).replace("\n", " ") + "\n")
        stream.flush()


def log_path(root: Path, action: str) -> Path:
    return root / "logs" / f"{action}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')}-{os.getpid()}.log"


def selected_build_remedy(character: str, height: float) -> str:
    return f"Run `make matrix-build CHARACTER={character} HEIGHT={height:.2f}` to build this result."


def cleanup_generated(root: Path, on_removed=None) -> tuple[list[str], int]:
    removed: list[str] = []
    size = 0
    # Invalidate prior success before touching any generated tree so an
    # interrupted or refused cleanup cannot leave an old pass current.
    for name in ("build.json", "check.json", "build.json.tmp", "check.json.tmp"):
        path = root / name
        if path.exists():
            if not path.is_file():
                raise MatrixError(f"matrix control path is not a regular file: {path}")
            size += path.stat().st_size
            path.unlink()
            removed.append(str(path))
            if on_removed is not None:
                on_removed(str(path), size)
    for name in ("prepared", "render", "presentation", ".tmp"):
        path = root / name
        if not path.exists() and not path.is_symlink():
            continue
        if path.is_symlink():
            raise MatrixError(f"refusing to clean symlink output: {path}")
        for child in path.rglob("*"):
            if child.is_symlink():
                raise MatrixError(f"refusing to clean output containing symlink: {child}")
        if path.is_file():
            size += path.stat().st_size
        else:
            size += sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
        shutil.rmtree(path) if path.is_dir() else path.unlink()
        removed.append(str(path))
        if on_removed is not None:
            on_removed(str(path), size)
    return removed, size


def matrix_binding(root: Path, allowed: tuple[str, ...]) -> dict[str, Any]:
    return {"element_root": str(root), "allowed_destinations": list(allowed)}


def validate_output(workspace: Path, root: Path, character: str, height: float,
                    build: dict[str, Any]) -> dict[str, Any]:
    """Validate current producer and assembled media directly from their files."""
    from matrix_presentation import _validate_producer
    from PIL import Image

    expected_paths = {
        "prepared": root / "prepared" / "input.json",
        "render_root": root / "render",
        "render_manifest": root / "render" / "render-manifest.json",
        "presentation": root / "presentation",
        "presentation_inventory": root / "presentation" / "presentation-inventory.json",
    }
    for key, expected in expected_paths.items():
        if Path(build.get(key, "")).absolute() != expected.absolute():
            raise MatrixError(f"current build {key} path does not match the selected result root")
    receipt_path = Path(build.get("render_receipt", ""))
    try:
        receipt_path.absolute().relative_to((root / "render").absolute())
    except ValueError as exc:
        raise MatrixError("render receipt path is outside the selected render output") from exc
    no_symlink(receipt_path, workspace)
    producer = _validate_producer(expected_paths["prepared"], expected_paths["render_manifest"],
                                  expected_paths["render_root"] / "frames", (character,), workspace)
    actual_receipts = sorted((expected_paths["render_root"] / "processes").glob("*/outcome.json"))
    render_receipts = []
    for candidate in actual_receipts:
        no_symlink(candidate, workspace)
        try:
            receipt_data = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise MatrixError(f"render receipt is unreadable: {candidate}") from exc
        if isinstance(receipt_data, dict) and receipt_data.get("operation") == "render-pass":
            render_receipts.append(candidate)
    if len(render_receipts) != 1:
        raise MatrixError(f"expected one original render-pass receipt, found {len(render_receipts)}")
    if receipt_path.absolute() != render_receipts[0].absolute():
        raise MatrixError("current build receipt path differs from the original render receipt")
    prepared = producer[0]
    if prepared.get("sources", {}).get("profile", {}).get("stature_m") != height:
        raise MatrixError("prepared producer stature does not match the selected height")
    _validate_matrix_sampling(prepared)
    presentation = validate_presentation_inventory(
        Path(build["presentation_inventory"]), Path(build["presentation"]),
        prepared_path=Path(build["prepared"]), render_manifest_path=Path(build["render_manifest"]),
        frames_base=Path(build["render_root"]) / "frames", workspace=workspace,
        character_ids=(character,), fixtures=FIXTURES,
    )
    inventory_path = expected_paths["presentation_inventory"]
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    listed: set[str] = set()
    from PIL import Image
    for media in inventory.get("media", []):
        relative = Path(media["path"])
        if (relative.is_absolute() or ".." in relative.parts or len(relative.parts) != 1
                or relative.suffix.lower() not in {".png", ".gif"}):
            raise MatrixError(f"unsafe presentation media path: {media.get('path')!r}")
        path = expected_paths["presentation"] / relative
        with Image.open(path) as image:
            size = image.size
        kind = media.get("kind")
        if kind == "animation-gif":
            expected_size = (512, 512)
        elif kind == "onion-skin":
            expected_size = (1024, 1024)
        elif kind == "count-sheet":
            fixture = next((item for item in FIXTURES if path.name.startswith(item + "-")), None)
            timeline = prepared.get("sampling", {}).get(fixture, [])
            if len(timeline) != 1:
                raise MatrixError(f"count sheet has an unknown or ambiguous fixture: {path.name}")
            expected_size = (320, 346 * len(timeline[0].get("static", [])))
        else:
            raise MatrixError(f"unexpected presentation media kind: {kind!r}")
        if size != expected_size or media.get("width_px") != size[0] or media.get("height_px") != size[1]:
            raise MatrixError(f"presentation media has wrong dimensions: {path.name} {size}")
        listed.add(relative.as_posix())
    actual_media: set[str] = set()
    for path in expected_paths["presentation"].rglob("*"):
        if path.is_symlink():
            raise MatrixError(f"presentation contains a symlink: {path}")
        if path.is_file():
            relative = path.relative_to(expected_paths["presentation"]).as_posix()
            if relative not in {"index.html", "presentation-inventory.json"}:
                actual_media.add(relative)
    if actual_media != listed:
        raise MatrixError("presentation files do not exactly match the validated media inventory")
    image_rows = producer[-1]
    expected_pngs = 44 if character == "skeleton" else 32
    if len(image_rows) != expected_pngs:
        raise MatrixError(f"expected {expected_pngs} source PNGs, found {len(image_rows)}")
    observed: set[str] = set()
    frames = expected_paths["render_root"] / "frames"
    actual_pngs: set[str] = set()
    for entry in frames.rglob("*"):
        if entry.is_symlink():
            raise MatrixError(f"render frames contain a symlink: {entry}")
        if entry.is_file() and entry.suffix.lower() == ".png":
            actual_pngs.add(entry.relative_to(frames).as_posix())
    for row in image_rows:
        relative = Path(row["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise MatrixError(f"unsafe source image path: {row['path']}")
        path = frames / relative
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            if image.size != (1024, 1024):
                raise MatrixError(f"source image has wrong dimensions: {row['path']} {image.size}")
        observed.add(row["path"])
    if len(observed) != expected_pngs:
        raise MatrixError("producer contains duplicate source image paths")
    if actual_pngs != observed:
        raise MatrixError("render PNG files do not exactly match the validated producer membership")
    return {"producer": "pass", "presentation": presentation,
            "source_images": {"status": "pass", "count": len(observed),
                              "dimensions": "1024x1024"}}


def _validate_matrix_sampling(prepared: dict[str, Any]) -> None:
    """Require the literal 120 BPM short-set timelines used by this matrix."""
    sampling = prepared.get("sampling")
    if not isinstance(sampling, dict) or set(sampling) != set(FIXTURES):
        raise MatrixError("prepared fixtures do not match the fixed matrix selection")

    def rational(value: Any) -> Fraction:
        if (not isinstance(value, dict) or set(value) != {"numerator", "denominator"}
                or any(isinstance(value[key], bool) or not isinstance(value[key], int)
                       for key in value)):
            raise MatrixError("prepared timeline contains a malformed rational value")
        try:
            return Fraction(value["numerator"], value["denominator"])
        except (ZeroDivisionError, ValueError) as exc:
            raise MatrixError("prepared timeline contains an invalid rational value") from exc

    expected_ids: set[str] = set()
    for fixture in FIXTURES:
        plans = sampling[fixture]
        if not isinstance(plans, list) or len(plans) != 1 or plans[0].get("bpm") != 120:
            raise MatrixError("prepared fixtures must have one 120 BPM plan each")
        plan = plans[0]
        if fixture == "arm-raise":
            expected_static = [(index, index // 3) for index in (0, 3, 6, 9, 12)]
            expected_animation = [(index, Fraction(index, 3)) for index in range(13)]
        else:
            expected_static = [(0, 0)]
            expected_animation = [(0, Fraction(0))]

        def check(rows: Any, expected: list[tuple[int, Any]], mode: str) -> None:
            if not isinstance(rows, list) or len(rows) != len(expected):
                raise MatrixError(f"prepared {fixture} {mode} timeline has the wrong member count")
            for row, (frame_id, beat) in zip(rows, expected):
                sample_id = f"{fixture}/{frame_id:05d}"
                if (not isinstance(row, dict) or row.get("frame_id") != frame_id
                        or row.get("sample_id") != sample_id
                        or rational(row.get("beat")) != Fraction(beat)
                        or rational(row.get("seconds")) != Fraction(beat, 2)):
                    raise MatrixError(f"prepared {fixture} {mode} timeline differs from the fixed sample plan")
                expected_ids.add(sample_id)

        check(plan.get("static"), expected_static, "static")
        check(plan.get("animation"), expected_animation, "animation")

    samples = prepared.get("samples")
    if (not isinstance(samples, list) or {row.get("id") for row in samples if isinstance(row, dict)}
            != expected_ids or len(samples) != len(expected_ids)):
        raise MatrixError("prepared sample inventory differs from the fixed matrix timeline")


def validate_installed_api(api) -> None:
    """Fail when the selected offline package is stale, after attempt invalidation."""
    if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 14):
        raise MatrixError("matrix build requires the approved CPython 3.14 offline environment")
    required = {"prepare": {"matrix_destination", "fixtures", "bpms", "stature"},
                "render": {"matrix_destination", "render_only", "characters", "images"}}
    for name, expected in required.items():
        actual = set(inspect.signature(getattr(api, name)).parameters)
        if not expected <= actual:
            missing = ", ".join(sorted(expected - actual))
            raise MatrixError(
                f"installed humanmotionlib {name} API is missing {missing}; "
                "install the approved package in the offline environment before building"
            )


def installed_package_identity() -> dict[str, Any]:
    from humanmotionlib.package_resources import manifest_sha256, verify_runtime_integrity
    manifest = verify_runtime_integrity()
    return {
        "package_version": manifest["version"],
        "runtime_manifest_sha256": manifest_sha256(),
        "resource_hashes": manifest["resources"],
        "backend_contract_sha256": manifest["backend_contract"],
        "implementation_hashes": manifest["implementation"],
    }


def command_list(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).expanduser()
    if not workspace.is_absolute():
        raise MatrixError("workspace must be an absolute path")
    workspace = workspace.resolve(strict=True)
    print(json.dumps({"rows": table(workspace)}, indent=2))
    return 0


def command_build(args: argparse.Namespace) -> int:
    workspace, root, character, height = selection(args)
    no_symlink(root, workspace)
    for name in ("prepared", "prepared/input.json", "render", "render/processes",
                 "render/render-manifest.json", "presentation", "presentation/index.html",
                 "presentation/presentation-inventory.json", ".tmp", "logs", "build.json",
                 "build.json.tmp", "check.json", "check.json.tmp"):
        no_symlink(root / name, workspace)
    if root.exists() and not root.is_dir():
        raise MatrixError(f"selected result root is not a directory: {root}")
    for name in ("build.json", "build.json.tmp", "check.json", "check.json.tmp"):
        path = root / name
        if path.exists() and not path.is_file():
            raise MatrixError(f"matrix result control path is not a regular file: {path}")
    root.mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(exist_ok=True)
    log = log_path(root, "build")
    # Open the attempt log before invalidating current success. Every started action is durable.
    with log.open("x", encoding="utf-8") as stream:
        stream.write(f"command=build CHARACTER={character} HEIGHT={height:.2f}\n")
        stream.write(f"started_utc={datetime.now(timezone.utc).isoformat()}\n")
        stream.write(f"workspace={workspace}\nroot={root}\n")
        stream.flush()
        removed: list[str] = []
        removed_bytes = 0
        cleanup_attempted = False

        def record_cleanup(path: str, total_bytes: int) -> None:
            removed.append(path)
            stream.write(f"cleanup_removed={path} cumulative_bytes={total_bytes}\n")
            stream.flush()

        try:
            cleanup_attempted = True
            removed, removed_bytes = cleanup_generated(root, on_removed=record_cleanup)
            from humanmotionlib import api
            validate_installed_api(api)
            prepared = api.prepare(
                workspace=workspace, output=root / "prepared" / "input.json",
                stature=height, fixtures=FIXTURES, bpms=(120,),
                matrix_destination=matrix_binding(root, ("prepared/input.json",)),
            )
            stream.write("step=prepare complete\n")
            stream.write(f"package_identity={json.dumps(prepared.package_identity, sort_keys=True)}\n")
            stream.flush()
            stream.write("step=render started\n")
            stream.flush()
            generated = api.render(
                prepared, workspace=workspace, output=root / "render", characters=(character,),
                images=True, render_only=True,
                matrix_destination=matrix_binding(root, ("render",)),
            )
            stream.write(f"step=render complete backend_identity={json.dumps(generated.backend_identity, sort_keys=True)}\n")
            stream.flush()
            stream.write("step=presentation started\n")
            stream.flush()
            (root / "presentation").mkdir()
            presentation = assemble_presentation(
                prepared.prepared_path, generated.artifacts["render_manifest"],
                root / "render" / "frames", root / "presentation", workspace=workspace,
                character_ids=(character,), fixtures=FIXTURES, matrix_element_root=root,
            )
            marker_paths = {
                "prepared": str(root / "prepared" / "input.json"),
                "render_root": str(root / "render"),
                "render_manifest": str(root / "render" / "render-manifest.json"),
                "render_receipt": str(generated.receipt_path),
                "presentation": str(root / "presentation"),
                "presentation_inventory": str(root / "presentation" / "presentation-inventory.json"),
            }
            build = {"schema": "matrix-current-build/v1", "status": "pending",
                     "character": character, "height_m": height, "fixtures": list(FIXTURES),
                     "bpm": 120, **marker_paths}
            validation = validate_output(workspace, root, character, height, build)
            build = {"schema": "matrix-current-build/v1", "status": "success",
                     "character": character, "height_m": height, "fixtures": list(FIXTURES),
                     "bpm": 120, "prepared": str(prepared.prepared_path),
                     "prepared_sha256": prepared.prepared_sha256,
                     "package_identity": prepared.package_identity,
                     "render_root": str(generated.output_root),
                     "backend_identity": generated.backend_identity,
                     "render_manifest": str(generated.artifacts["render_manifest"]),
                     "render_receipt": str(generated.receipt_path),
                     "presentation": str(root / "presentation"),
                     "presentation_inventory": str(root / "presentation" / "presentation-inventory.json"),
                     "source_png_count": presentation["source_image_count"],
                     "media_count": presentation["media_count"], "validation": validation,
                     "log": str(log)}
            write_json(root / "build.json", build)
            stream.write(f"prepared={prepared.prepared_path}\nrender={generated.output_root}\n")
            stream.write(f"presentation={presentation}\n")
            stream.write(f"cleanup_removed={json.dumps(removed)} bytes={removed_bytes}\n")
            stream.write("outcome=success\n")
            stream.write(f"ended_utc={datetime.now(timezone.utc).isoformat()}\n")
            print(json.dumps(build, indent=2))
            return 0
        except BaseException as exc:
            stream.write("error=" + str(exc).replace("\n", " ") + "\n")
            preserve_render_failure_diagnostics(stream, exc, root, workspace)
            stream.write(traceback.format_exc() + "\n")
            if cleanup_attempted:
                try:
                    partial, byte_count = cleanup_generated(root, on_removed=record_cleanup)
                    stream.write(f"failure_cleanup_total={json.dumps(partial)} bytes={byte_count}\n")
                except Exception as cleanup_error:
                    stream.write(f"cleanup_incomplete={cleanup_error}\n")
            else:
                stream.write("cleanup_skipped=prerequisite preflight failed; prior current data preserved\n")
            stream.write("outcome=failure\n")
            stream.write(f"ended_utc={datetime.now(timezone.utc).isoformat()}\n")
            raise


def command_check(args: argparse.Namespace) -> int:
    workspace, root, character, height = selection(args)
    no_symlink(root, workspace)
    if not root.exists():
        raise MatrixError(f"selected result is absent; {selected_build_remedy(character, height)}")
    if not root.is_dir():
        raise MatrixError(f"selected result root is not a directory: {root}")
    build_path = root / "build.json"
    no_symlink(build_path, workspace)
    if not build_path.exists():
        raise MatrixError(f"selected build record is absent; {selected_build_remedy(character, height)}")
    if not build_path.is_file():
        raise MatrixError(f"matrix result control path is not a regular file: {build_path}")
    try:
        current_identity = installed_package_identity()
    except (ImportError, OSError, ValueError, RuntimeError, TypeError) as exc:
        raise MatrixError(
            f"compatible project tools are unavailable ({exc}); {selected_build_remedy(character, height)}"
        ) from exc
    for name in ("prepared", "prepared/input.json", "render", "render/processes",
                 "render/render-manifest.json", "presentation", "presentation/index.html",
                 "presentation/presentation-inventory.json", ".tmp", "logs", "build.json",
                 "build.json.tmp", "check.json", "check.json.tmp"):
        no_symlink(root / name, workspace)
    if root.exists() and not root.is_dir():
        raise MatrixError(f"selected result root is not a directory: {root}")
    for name in ("build.json", "build.json.tmp", "check.json", "check.json.tmp"):
        path = root / name
        if path.exists() and not path.is_file():
            raise MatrixError(f"matrix result control path is not a regular file: {path}")
    root.mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(exist_ok=True)
    log = log_path(root, "check")
    result_path = root / "check.json"
    started = datetime.now(timezone.utc).isoformat()
    checks: dict[str, Any] = {}
    with log.open("x", encoding="utf-8") as stream:
        stream.write(f"command=check CHARACTER={character} HEIGHT={height:.2f}\n")
        stream.write(f"started_utc={started}\n")
        stream.write(f"workspace={workspace}\nroot={root}\n")
        stream.flush()
        for temporary in (root / "build.json.tmp", root / "check.json.tmp"):
            if temporary.exists():
                byte_count = temporary.stat().st_size
                temporary.unlink()
                stream.write(f"stale_temporary_removed={temporary} bytes={byte_count}\n")
                stream.flush()
        # Remove an earlier verdict before inspecting files, so interruption
        # cannot leave an old success current.
        if result_path.exists():
            prior_bytes = result_path.stat().st_size
            stream.write(f"replaced_current_check={result_path} bytes={prior_bytes}\n")
            stream.flush()
        result_path.unlink(missing_ok=True)
        failure: BaseException | None = None
        try:
            build = json.loads(build_path.read_text(encoding="utf-8"))
            if (build.get("schema") != "matrix-current-build/v1" or build.get("status") != "success"
                    or build.get("character") != character or build.get("height_m") != height
                    or build.get("fixtures") != list(FIXTURES) or build.get("bpm") != 120):
                raise MatrixError("current build completion does not match the selected character and height")
            recorded_identity = build.get("package_identity")
            if recorded_identity != current_identity:
                raise MatrixError(
                    "selected build was produced by a different installed library package; "
                    f"run `make matrix-build CHARACTER={character} HEIGHT={height:.2f}` to rebuild it"
                )
            checks["package_identity"] = build.get("package_identity")
            checks["backend_identity"] = build.get("backend_identity")
            checks.update(validate_output(workspace, root, character, height, build))
            outcome = "success"
        except BaseException as exc:
            failure = exc
            checks["error"] = str(exc)
            outcome = "interrupted" if isinstance(exc, KeyboardInterrupt) else "failure"
        ended = datetime.now(timezone.utc).isoformat()
        result = {"schema": "matrix-current-check/v1", "status": outcome,
                  "character": character, "height_m": height, "started_utc": started,
                  "ended_utc": ended, "checks": checks,
                  "build": str(root / "build.json"), "log": str(log)}
        write_json(result_path, result)
        stream.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
        stream.write(f"outcome={outcome}\nended_utc={ended}\n")
        stream.flush()
        if failure is not None and not isinstance(failure, Exception):
            raise failure
    print(json.dumps(result, indent=2))
    return 0 if outcome == "success" else 1


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    listing = sub.add_parser("list", help="show the fixed character/height table")
    listing.add_argument("--workspace", default=str(ROOT))
    for name, function in (("build", command_build), ("check", command_check)):
        command = sub.add_parser(name, help=f"run the complete selected {name}")
        command.add_argument("--workspace", default=str(ROOT))
        command.add_argument("--character", required=True)
        command.add_argument("--height", required=True)
        command.set_defaults(handler=function)
    listing.set_defaults(handler=command_list)
    return root


def main(argv: list[str] | None = None) -> int:
    try:
        args = parser().parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)
    try:
        return args.handler(args)
    except (MatrixError, PresentationError, OSError, ValueError, RuntimeError, ImportError, TypeError) as exc:
        print(f"matrix: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
