# SPDX-License-Identifier: Apache-2.0
"""Run one normal Blender build or render through the shared supervisor."""

import argparse
import json
import hashlib
import os
from pathlib import Path
import re
import stat
import sys
from PIL import Image

from humanmotionlib.prepared import read_prepared
from humanmotionlib.prepared import content_hash
from humanmotionlib.runtime import (DEFAULT_BUILD_TIMEOUT, DEFAULT_SLOT_TIMEOUT, InvocationError,
                           ensure_workspace_build, file_sha256, inspect_blender, invocation,
                           resolve_workspace_path, update_receipt, validate_managed_pass_root,
                           validate_operation_root, validate_outputs, validate_run_root,
                           validate_matrix_content_destination, workspace_root)
from dataclasses import dataclass


_RUN_COMPONENT = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class _ManagedOutputClaim:
    """Private in-memory authorization for one API-created managed pass root."""
    owner_run: str
    pass_root: str
    directory_device: int
    directory_inode: int
    request_path: str
    request_device: int
    request_inode: int
    request_sha256: str
    prepared_sha256: str
    render_identity: str
    character_ids: tuple[str, ...]


def _validate_managed_output_claim(claim, output, owner_root, request, prepared,
                                   render_identity, characters, *, after_probe=False):
    if not isinstance(claim, _ManagedOutputClaim):
        raise ValueError("managed pass requires the private API output claim")
    claimed_owner = validate_run_root(claim.owner_run, owner_root.parent.parent)
    claimed_pass = validate_managed_pass_root(claim.pass_root, claimed_owner,
                                              owner_root.parent.parent)
    if claimed_owner != owner_root or claimed_pass != output:
        raise ValueError("managed output claim path identity changed")
    try:
        directory_stat = output.lstat()
    except OSError as error:
        raise ValueError("managed pass directory disappeared") from error
    if (stat.S_ISLNK(directory_stat.st_mode) or not stat.S_ISDIR(directory_stat.st_mode)
            or (directory_stat.st_dev, directory_stat.st_ino) !=
               (claim.directory_device, claim.directory_inode)):
        raise ValueError("managed pass directory identity changed")
    request_path = Path(claim.request_path)
    expected_request = output / "character-render-request.json"
    if request_path != expected_request or request is None or request["path"] != expected_request:
        raise ValueError("managed pass claim request path changed")
    try:
        request_stat = request_path.lstat()
        request_bytes = request_path.read_bytes()
    except OSError as error:
        raise ValueError("managed pass request disappeared") from error
    if (stat.S_ISLNK(request_stat.st_mode) or not stat.S_ISREG(request_stat.st_mode)
            or (request_stat.st_dev, request_stat.st_ino) !=
               (claim.request_device, claim.request_inode)
            or hashlib.sha256(request_bytes).hexdigest() != claim.request_sha256
            or claim.request_sha256 != request["sha256"]):
        raise ValueError("managed pass request identity changed")
    try:
        request_record = json.loads(request_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("managed pass request is unreadable") from error
    if not isinstance(request_record, dict):
        raise ValueError("managed pass request must be a JSON object")
    if (request_record.get("prepared_sha256") != prepared.get("content_sha256")
            or request_record.get("render_identity") != render_identity
            or render_identity != claim.render_identity
            or claim.prepared_sha256 != prepared.get("content_sha256")
            or request_record.get("character_ids") != list(characters)
            or claim.character_ids != tuple(characters)):
        raise ValueError("managed pass request identity does not match its invocation")
    sealed_request = dict(request_record)
    sealed_identity = sealed_request.pop("render_identity", None)
    if (request_record.get("format") != "character-render-request/v1"
            or content_hash(sealed_request) != sealed_identity):
        raise ValueError("managed pass request seal is invalid")
    names = {entry.name for entry in output.iterdir()}
    allowed = {"character-render-request.json"}
    if after_probe:
        allowed.add("processes")
        process_path = output / "processes"
        if process_path.is_symlink() or (process_path.exists() and not process_path.is_dir()):
            raise ValueError("managed pass supervisor evidence is not a contained directory")
    if names != allowed and (not after_probe or names - allowed):
        raise ValueError("managed pass contains foreign output entries")


def owning_run_root(path, workspace):
    """Require one valid flat run identity under build, allowing tool content below it."""
    build = (workspace_root(workspace) / "build").resolve()
    path = resolve_workspace_path(path, workspace)
    candidate = path
    while candidate != build and candidate.parent != build and candidate.parent != candidate:
        nested_parts = candidate.name.split("_")
        if len(nested_parts) == 5 and all(_RUN_COMPONENT.fullmatch(part) for part in nested_parts):
            raise ValueError(f"nested run identity is not tool content: {candidate}")
        candidate = candidate.parent
    if candidate.parent != build:
        raise ValueError(f"backend output is outside build/: {path}")
    parts = candidate.name.split("_")
    if len(parts) != 5 or not all(_RUN_COMPONENT.fullmatch(part) for part in parts):
        raise ValueError(f"backend output has no valid five-component run root: {candidate}")
    return candidate


def expected_outputs(prepared, output, render_dir, render_only, input_file, character_request=None,
                     characters=("skeleton",)):
    outputs = [{"path": output / "input.json", "allow_existing_sha256": file_sha256(input_file)},
               output / "build-metadata.json", output / "skeleton.blend"]
    if character_request is not None:
        outputs.append({"path": Path(character_request["path"]),
                        "allow_existing_sha256": character_request["sha256"]})
    if not render_only:
        outputs.extend((output / "evaluated.json", output / "geometry-reference.json"))
        for identifier in characters:
            if identifier!="skeleton":
                outputs.extend((output/"characters"/identifier/"surface-reference.json",
                                output/"characters"/identifier/"surface-evaluated.json"))
    if render_dir is not None:
        outputs.append(output / "render-manifest.json")
        scene = prepared["sources"]["review-scene"]
        extra_views = [camera["id"] for camera in scene["cameras"] if camera["id"].startswith("thorax-")]
        for sample in prepared["samples"]:
            for identifier in characters:
                views = ["front", "side"]
                if sample["fixture"] in ("neutral", "rest"):
                    views.extend(("rear", *extra_views, *(view + "-isolated" for view in extra_views))) if identifier=="skeleton" else views.append("rear")
                for view in views:
                    prefix=Path() if identifier=="skeleton" else Path(identifier)
                    outputs.append(render_dir / prefix / sample["fixture"] / view / (str(sample["frame_id"]).zfill(5) + ".png"))
    return outputs


def run(input_path, output, *, render_dir=None, render_only=False,
        timeout_seconds=DEFAULT_BUILD_TIMEOUT, slot_timeout_seconds=DEFAULT_SLOT_TIMEOUT,
        workspace=None, owner_run=None, characters=("skeleton",), render_identity=None,
        character_request=None, managed_claim=None, matrix_element_root=None):
    workspace = workspace_root(workspace)
    input_operand = resolve_workspace_path(input_path, workspace)
    if input_operand.is_dir():
        input_root = input_operand
        input_path = input_operand / "input.json"
    else:
        input_path = input_operand
        input_root = input_path.parent
    output_operand = Path(os.fspath(output))
    if matrix_element_root is None:
        output = validate_operation_root(resolve_workspace_path(output_operand, workspace),
                                         workspace, owner_run)
    else:
        if owner_run is not None:
            raise ValueError("matrix content mode cannot be combined with a managed owner run")
        matrix_root, output, _relative_path = validate_matrix_content_destination(
            output_operand, matrix_element_root, workspace, operation="render")
    owner_root = validate_run_root(owner_run, workspace) if owner_run is not None else output
    if owner_run is not None:
        validate_managed_pass_root(output, owner_root, workspace)
    render_dir = resolve_workspace_path(render_dir, workspace) if render_dir else None
    if render_dir is not None:
        try:
            render_dir.relative_to(output)
        except ValueError as error:
            raise ValueError("render directory must be inside the owning output run") from error
    if owner_run is None and managed_claim is not None:
        raise ValueError("managed output claim cannot authorize a public render root")
    if input_path.is_relative_to(owner_root) or owner_root.is_relative_to(input_root):
        # The designated output run may also own the prepared input. A sibling
        # output root may not contain or overwrite the independent input root.
        if input_root != owner_root:
            raise ValueError("prepared input and output roots must be disjoint or share the designated run root")
    prepared = read_prepared(input_path)
    request = None
    if character_request is not None:
        request_path = resolve_workspace_path(character_request, workspace)
        if request_path.parent != output or not isinstance(render_identity, str):
            raise ValueError("character render request must be sealed inside the output run")
        request = {"path": request_path, "sha256": file_sha256(request_path)}
    if owner_run is not None:
        _validate_managed_output_claim(managed_claim, output, owner_root, request, prepared,
                                       render_identity, characters)
    outputs = expected_outputs(prepared, output, render_dir, render_only, input_path, request, characters)
    failed_preflight = validate_fresh_targets(outputs)
    if failed_preflight:
        raise ValueError("stale output preflight failed: " + ", ".join(failed_preflight))
    if matrix_element_root is None and output == owner_root and output.exists():
        allowed = {input_path} if input_root == owner_root else set()
        if request is not None:
            allowed.add(request["path"])
        unexpected = [entry for entry in output.iterdir() if entry.resolve() not in allowed]
        if unexpected:
            raise ValueError("backend run root is occupied: " + ", ".join(str(path) for path in unexpected))
    ensure_workspace_build(workspace)
    output.mkdir(parents=True, exist_ok=True)
    probe = inspect_blender(output, slot_timeout_seconds=slot_timeout_seconds,
                            workspace=workspace, owner_run=owner_run)
    if owner_run is not None:
        _validate_managed_output_claim(managed_claim, output, owner_root, request, prepared,
                                       render_identity, characters, after_probe=True)
        failed_after_probe = validate_fresh_targets(outputs)
        if failed_after_probe:
            raise ValueError("managed pass stale output preflight failed after Blender probe: "
                             + ", ".join(failed_after_probe))
    script = Path(__file__).with_name("build_skeleton.py").resolve()
    command = [probe["receipt"]["executable"], "--background", "--factory-startup",
               "--python-exit-code", "1", "--python", str(script), "--",
               "--input", str(input_path), "--output", str(output), "--workspace", str(workspace_root(workspace))]
    command.extend(("--expected-prepared-sha256", prepared["content_sha256"]))
    if not isinstance(characters, (tuple, list)) or not characters:
        raise ValueError("characters must be a nonempty sequence")
    if tuple(characters) != ("skeleton",):
        command.extend(("--characters", *characters))
    if render_identity is not None:
        command.extend(("--expected-render-identity", render_identity))
    if request is not None:
        command.extend(("--character-request", str(request["path"])))
    if owner_run is not None:
        command.extend(("--owner-run", str(owner_root)))
    if matrix_element_root is not None:
        command.extend(("--matrix-element-root", str(matrix_root)))
    if render_dir is not None:
        command.extend(("--render-dir", str(render_dir)))
    if render_only:
        command.append("--render-only")
    receipt = invocation(command, run_root=output, operation="render-pass" if render_dir else "build",
                         cwd=workspace_root(workspace), timeout_seconds=timeout_seconds,
                         slot_timeout_seconds=slot_timeout_seconds,
                         source_sha256=prepared["content_sha256"], expected_outputs=outputs,
                         workspace=workspace, owner_run=owner_run)
    if receipt.get("last_script_phase") != "script_complete":
        update_receipt(receipt, state="failed", outcome="missing-completion-marker",
                       output_validation={"status": "fail", "reason": "script_complete marker missing"})
        receipt_path = Path(receipt["stdout_log"]).parent / "outcome.json"
        raise InvocationError("script did not emit script_complete; see " + str(receipt_path), str(receipt_path))
    if not any(phase.get("phase") == "input_loaded" and phase.get("prepared_sha256") == prepared["content_sha256"]
               for phase in receipt.get("phases", [])):
        receipt_path = Path(receipt["stdout_log"]).parent / "outcome.json"
        update_receipt(receipt, state="failed", outcome="input-identity-mismatch",
                       output_validation={"status": "fail", "reason": "input_loaded phase identity mismatch"})
        raise InvocationError("script completion does not identify the prepared input", str(receipt_path))
    if render_identity is not None and not any(
            phase.get("phase") == "script_complete"
            and phase.get("render_identity") == render_identity
            and phase.get("character_ids") == list(characters)
            for phase in receipt.get("phases", [])):
        receipt_path = Path(receipt["stdout_log"]).parent / "outcome.json"
        update_receipt(receipt, state="failed", outcome="render-identity-mismatch",
                       output_validation={"status":"fail","reason":"script completion identity mismatch"})
        raise InvocationError("script completion does not identify the sealed character request", str(receipt_path))
    try:
        input_result = read_prepared(output / "input.json")
        if input_result["content_sha256"] != prepared["content_sha256"]:
            raise ValueError("copied prepared input hash mismatch")
        metadata = json.loads((output / "build-metadata.json").read_text())
        probe_identity = {"version": probe["version"], "build_hash": probe["build_hash"]}
        if metadata.get("blender_version") != probe_identity["version"] or metadata.get("blender_build") != probe_identity["build_hash"]:
            raise ValueError("build metadata backend identity mismatch")
        if render_identity is not None and metadata.get("render_identity") != render_identity:
            raise ValueError("build metadata render identity mismatch")
        if not (output / "skeleton.blend").is_file() or (output / "skeleton.blend").stat().st_size == 0:
            raise ValueError("saved blend is missing or empty")
        contracts = {"input_sha256": prepared["content_sha256"], "backend_identity": probe_identity}
        if not render_only:
            evaluated = json.loads((output / "evaluated.json").read_text())
            geometry = json.loads((output / "geometry-reference.json").read_text())
            if evaluated.get("prepared_sha256") != prepared["content_sha256"] or geometry.get("prepared_sha256") != prepared["content_sha256"]:
                raise ValueError("evaluated output has a different prepared input hash")
            if [sample.get("id") for sample in evaluated.get("samples", [])] != [sample["id"] for sample in prepared["samples"]]:
                raise ValueError("evaluated output sample inventory mismatch")
            contracts["evaluated_sample_count"] = len(evaluated["samples"])
        if render_dir is not None:
            manifest_path = output / "render-manifest.json"
            manifest = json.loads(manifest_path.read_text())
            if manifest.get("prepared_sha256") != prepared["content_sha256"]:
                raise ValueError("render manifest has a different prepared input hash")
            if render_identity is not None and manifest.get("render_identity") != render_identity:
                raise ValueError("render manifest has a different character identity")
            if any(identifier!="skeleton" for identifier in characters):
                from humanmotionlib.render_contract import validate_character_manifest
                required = validate_character_manifest(manifest, prepared, render_dir,
                                                       output=output, character_ids=characters)
                if not render_only:
                    required.extend((Path("evaluated.json"), Path("geometry-reference.json")))
                if request is not None:
                    required.extend(Path(name) for name in
                                    (output / "characters").glob("*/surface-*.json"))
                # Character manifests are fully checked here, including all pixel paths.
                decoded = sum(1 for item in required if item.suffix==".png")
            else:
                manifest_samples = manifest.get("samples", [])
                if [sample.get("id") for sample in manifest_samples] != [sample["id"] for sample in prepared["samples"]]:
                    raise ValueError("render manifest sample inventory mismatch")
                decoded = 0
                for sample in manifest_samples:
                    for relative in sample.get("images", {}).values():
                        path = render_dir / relative
                        with Image.open(path) as image:
                            image.verify()
                        decoded += 1
            contracts["readable_image_count"] = decoded
        update_receipt(receipt, output_validation={"status": "pass", "contracts": contracts,
                                                   "files": receipt["output_validation"].get("files", [])})
    except (OSError, ValueError, TypeError, KeyError, AttributeError, json.JSONDecodeError) as error:
        receipt_path = Path(receipt["stdout_log"]).parent / "outcome.json"
        update_receipt(receipt, state="failed", outcome="output-contract-failed",
                       output_validation={"status": "fail", "reason": str(error)})
        raise InvocationError("operation outputs failed validation: " + str(error), str(receipt_path)) from error
    return receipt


def validate_fresh_targets(outputs):
    stale = []
    for item in outputs:
        path = Path(item["path"] if isinstance(item, dict) else item)
        allowed = item.get("allow_existing_sha256") if isinstance(item, dict) else None
        if path.exists() and (not path.is_file() or allowed is None or file_sha256(path) != allowed):
            stale.append(str(path))
    return stale


def main(workspace=None, argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--render-dir", type=Path)
    parser.add_argument("--render-only", action="store_true")
    parser.add_argument("--characters", nargs="+", default=["skeleton"])
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_BUILD_TIMEOUT)
    parser.add_argument("--slot-timeout-seconds", type=float, default=DEFAULT_SLOT_TIMEOUT)
    args = parser.parse_args(argv)
    try:
        from humanmotionlib.api import render as public_render
        result = public_render(args.input, workspace=workspace, output=args.output,
                               images=args.render_dir is not None, render_dir=args.render_dir,
                               render_only=args.render_only, characters=tuple(args.characters),
                               timeout_seconds=args.timeout_seconds,
                               slot_timeout_seconds=args.slot_timeout_seconds)
        receipt = json.loads(result.receipt_path.read_text())
    except (ValueError, OSError, InvocationError, RuntimeError) as error:
        print(str(error), file=sys.stderr, flush=True)
        return 1
    print(json.dumps({"state": receipt["state"], "operation": receipt["operation"],
                      "invocation_id": receipt["invocation_id"], "receipt": receipt["stdout_log"]}, sort_keys=True),
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
