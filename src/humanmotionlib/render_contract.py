# SPDX-License-Identifier: Apache-2.0
"""Host-only validation shared by public rendering and review-pack workflows."""

import json
import hashlib
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
    # Character render batches include this request file in their supervised
    # output inventory. Older standalone skeleton renders do not, so retain
    # that mode when the optional file is absent.
    request_path = output_root / "character-render-request.json"
    if request_path.exists() or request_path.is_symlink():
        if request_path.is_symlink() or not request_path.is_file():
            raise ValueError("Character render request must be a regular file inside the render output")
        required_paths.append(Path("character-render-request.json"))
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


def validate_character_manifest(manifest, prepared, frames, *, output, character_ids):
    """Validate a complete character batch manifest and every image file."""
    if manifest.get("format") != "character-render-manifest/v1":
        raise ValueError("Unsupported character render manifest format")
    if not isinstance(character_ids, (tuple, list)) or not character_ids:
        raise ValueError("Character manifest selection is invalid")
    if manifest.get("prepared_sha256") != prepared["content_sha256"]:
        raise ValueError("Stale character render manifest")
    root=Path(output).resolve(); frames_root=Path(frames).resolve()
    try: frames_relative=frames_root.relative_to(root)
    except ValueError as error: raise ValueError("Character render directory escapes output run") from error
    characters=manifest.get("characters")
    if not isinstance(characters,list) or [row.get("id") for row in characters if isinstance(row,dict)]!=list(character_ids):
        raise ValueError("Character manifest ID inventory mismatch")
    samples=prepared["samples"]
    required=[Path("input.json"),Path("build-metadata.json"),Path("skeleton.blend"),
              Path("render-manifest.json"),Path("character-render-request.json")]
    for character in characters:
        records=character.get("samples")
        if not isinstance(records,list) or [row.get("id") for row in records if isinstance(row,dict)]!=[s["id"] for s in samples]:
            raise ValueError(f"Character sample inventory mismatch for {character['id']}")
        identifier=character["id"]
        for sample,record in zip(samples,records):
            views=expected_views(prepared,sample) if identifier=="skeleton" else ({"front","side","rear"} if sample["fixture"] in ("neutral","rest") else {"front","side"})
            images=record.get("images")
            if not isinstance(images,dict) or set(images)!=views:
                raise ValueError(f"Character view inventory mismatch for {identifier} / {sample['id']}")
            for view,relative in images.items():
                expected=Path(identifier) / sample["fixture"] / view / (str(sample["frame_id"]).zfill(5)+".png") if identifier!="skeleton" else Path(sample["fixture"]) / view / (str(sample["frame_id"]).zfill(5)+".png")
                if not isinstance(relative,str) or Path(relative)!=expected:
                    raise ValueError(f"Character image path mismatch for {identifier} / {sample['id']} / {view}")
                image=(frames_root/relative).resolve()
                try:image.relative_to(frames_root)
                except ValueError as error:raise ValueError(f"Character image escapes frame root: {relative}") from error
                if not image.is_file() or image.stat().st_size==0:raise ValueError(f"Missing character image: {image}")
                try:
                    with Image.open(image) as decoded:decoded.verify()
                except (OSError,ValueError) as error:raise ValueError(f"Unreadable character image: {image}") from error
                required.append(frames_relative/expected)
    return required


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


def _validate_matrix_receipt_relocation(receipt, output):
    declaration = receipt.get("matrix_path_relocation")
    if declaration is None:
        return
    if (not isinstance(declaration, dict)
            or declaration.get("schema") != "matrix-receipt-relocation/v1"
            or declaration.get("mode") != "supervisor-path-rebase"
            or declaration.get("non_path_fields_preserved") is not True
            or not isinstance(declaration.get("source_receipt_path"), str)
            or not isinstance(declaration.get("source_receipt_sha256"), str)
            or declaration.get("result_slot") != str(Path(output).resolve(strict=True))):
        raise ValueError("Matrix receipt relocation declaration is malformed or targets another result slot")
    source_path = Path(declaration["source_receipt_path"])
    if not source_path.is_absolute() or source_path.is_symlink() or not source_path.is_file():
        raise ValueError("Matrix receipt relocation source is missing or unsafe")
    source_bytes = source_path.read_bytes()
    if hashlib.sha256(source_bytes).hexdigest() != declaration["source_receipt_sha256"]:
        raise ValueError("Matrix receipt relocation source hash changed")
    try:
        original = json.loads(source_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Matrix receipt relocation source is not valid JSON") from error
    source_root = source_path.parent.parent.parent.resolve(strict=True)
    result_root = Path(output).resolve(strict=True)
    expected = json.loads(json.dumps(original))
    validation = expected.get("output_validation", {})
    files = validation.get("files", []) if isinstance(validation, dict) else None
    if not isinstance(files, list):
        raise ValueError("Matrix receipt relocation source has no output inventory")
    rebound = []
    for index, item in enumerate(files):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise ValueError("Matrix receipt relocation source has a malformed output path")
        path = Path(item["path"])
        if not path.is_absolute():
            continue
        try:
            relative = path.resolve(strict=False).relative_to(source_root)
        except ValueError:
            continue
        item["path"] = str(result_root / relative)
        rebound.append(f"/output_validation/files/{index}/path")
    operation_root = expected.get("operation_root")
    if isinstance(operation_root, str) and Path(operation_root).is_absolute():
        try:
            relative = Path(operation_root).resolve(strict=False).relative_to(source_root)
        except ValueError:
            pass
        else:
            expected["operation_root"] = str(result_root / relative)
            rebound.append("/operation_root")
    if not rebound:
        raise ValueError("Matrix receipt relocation source contains no relocatable paths")
    if declaration.get("rebound_json_paths") != rebound:
        raise ValueError("Matrix receipt relocation path declaration does not match its source")
    expected["matrix_path_relocation"] = declaration
    if receipt != expected:
        raise ValueError("Matrix receipt relocation changed fields beyond declared output paths")


def read_supervised_receipt(output, prepared, required_paths, *, expected_operation="render-pass",
                            trusted_generation_identity=None):
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
        if receipt.get("operation") == expected_operation:
            candidates.append((path, receipt))
    if len(candidates) != 1:
        raise ValueError(
            f"Expected one supervised {expected_operation} receipt in {output}; found {len(candidates)}")
    path, receipt = candidates[0]
    _validate_matrix_receipt_relocation(receipt, output)
    comparison_identity = (expected_identity if trusted_generation_identity is None
                           else trusted_generation_identity)
    if any(receipt.get(key) != value for key, value in comparison_identity.items()):
        label = "active installation" if trusted_generation_identity is None else "trusted generation anchor"
        raise ValueError(f"Render receipt package identity does not match the {label}: {path}")
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
