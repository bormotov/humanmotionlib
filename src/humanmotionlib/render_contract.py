# SPDX-License-Identifier: Apache-2.0
"""Host-only validation shared by public rendering and review-pack workflows."""

import json
from pathlib import Path

from PIL import Image

from humanmotionlib.package_resources import manifest_sha256, verify_runtime_integrity
from humanmotionlib.runtime import file_sha256


def expected_views(prepared, sample):
    views = {"front", "side"}
    if sample["fixture"] in ("neutral", "rest"):
        views.add("rear")
        extra = {camera["id"] for camera in prepared["sources"]["review-scene"]["cameras"]
                 if camera["id"].startswith("thorax-")}
        views.update(extra)
        views.update(view + "-isolated" for view in extra)
    return views


def validate_manifest(manifest, prepared, frames, *, output=None):
    """Validate full image membership and return receipt paths relative to output."""
    if manifest.get("prepared_sha256") != prepared["content_sha256"]:
        raise ValueError("Stale render manifest: prepared input hash does not match")
    records = manifest.get("samples")
    expected_samples = prepared["samples"]
    if (not isinstance(records, list) or any(not isinstance(record, dict) for record in records)
            or [record.get("id") for record in records] != [sample["id"] for sample in expected_samples]):
        raise ValueError("Render manifest sample inventory mismatch")
    output_root = Path(output).resolve() if output is not None else Path(frames).resolve().parent
    frames_root = Path(frames).resolve()
    try:
        frames_relative = frames_root.relative_to(output_root)
    except ValueError as error:
        raise ValueError("Render directory must be inside output run") from error
    required_paths = [Path("input.json"), Path("build-metadata.json"), Path("skeleton.blend"),
                      Path("render-manifest.json")]
    for sample, record in zip(expected_samples, records):
        images = record.get("images")
        if not isinstance(images, dict) or set(images) != expected_views(prepared, sample):
            raise ValueError(f"Render manifest view inventory mismatch for {sample['id']}")
        for view, relative in images.items():
            expected_relative = Path(sample["fixture"]) / view / f"{str(sample['frame_id']).zfill(5)}.png"
            if not isinstance(relative, str) or Path(relative) != expected_relative:
                raise ValueError(f"Render manifest image path mismatch for {sample['id']} / {view}")
            image_path = (frames_root / relative).resolve()
            try:
                image_path.relative_to(frames_root)
            except ValueError as error:
                raise ValueError(f"Render manifest image escapes frame directory: {relative}") from error
            if not image_path.is_file() or image_path.stat().st_size == 0:
                raise ValueError(f"Missing or empty render image for {sample['id']} / {view}: {image_path}")
            try:
                with Image.open(image_path) as image:
                    image.verify()
            except (OSError, ValueError) as error:
                raise ValueError(f"Unreadable render image for {sample['id']} / {view}: {image_path}") from error
            required_paths.append(frames_relative / expected_relative)
    return required_paths


def _receipt_files_unchanged(receipt, output, required_paths):
    validation = receipt.get("output_validation", {})
    files = validation.get("files")
    if validation.get("status") != "pass" or not isinstance(files, list) or not files:
        raise ValueError("Render receipt has no successful output hash inventory")
    expected = {str((output / path).resolve()) for path in required_paths}
    observed = set()
    for record in files:
        if not isinstance(record, dict):
            raise ValueError("Render receipt contains a malformed output hash entry")
        path = Path(record.get("path", "")).resolve()
        try:
            path.relative_to(output.resolve())
        except ValueError as error:
            raise ValueError(f"Render receipt output escapes pass directory: {path}") from error
        if (not path.is_file() or path.stat().st_size != record.get("size_bytes")
                or file_sha256(path) != record.get("sha256")):
            raise ValueError(f"Render receipt output is missing or changed: {path}")
        observed.add(str(path))
    if len(observed) != len(files) or observed != expected:
        raise ValueError("Render receipt output inventory does not match the complete render output set")


def read_supervised_receipt(output, prepared, required_paths):
    package_manifest = verify_runtime_integrity()
    expected_identity = {
        "package_version": package_manifest["version"],
        "runtime_manifest_sha256": manifest_sha256(),
        "resource_hashes": package_manifest["resources"],
        "backend_contract_sha256": package_manifest["backend_contract"],
        "implementation_hashes": package_manifest["implementation"],
    }
    candidates = []
    for path in (output / "processes").glob("*/outcome.json"):
        try:
            receipt = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Unreadable render receipt: {path}") from error
        if receipt.get("operation") == "render-pass":
            candidates.append((path, receipt))
    if len(candidates) != 1:
        raise ValueError(f"Expected one supervised render receipt in {output}; found {len(candidates)}")
    path, receipt = candidates[0]
    if any(receipt.get(key) != value for key, value in expected_identity.items()):
        raise ValueError(f"Render receipt package identity does not match the active installation: {path}")
    if (receipt.get("state") != "succeeded" or receipt.get("outcome") != "exit"
            or receipt.get("return_code") != 0 or receipt.get("source_sha256") != prepared["content_sha256"]
            or receipt.get("last_script_phase") != "script_complete"
            or not any(phase.get("phase") == "input_loaded"
                       and phase.get("prepared_sha256") == prepared["content_sha256"]
                       for phase in receipt.get("phases", []))
            or not any(phase.get("phase") == "script_complete"
                       and phase.get("prepared_sha256") == prepared["content_sha256"]
                       for phase in receipt.get("phases", []))):
        raise ValueError(f"Render receipt is failed, incomplete, or stale: {path}")
    _receipt_files_unchanged(receipt, output, required_paths)
    return receipt
