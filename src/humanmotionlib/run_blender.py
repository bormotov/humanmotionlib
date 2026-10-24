# SPDX-License-Identifier: Apache-2.0
"""Run one normal Blender build or render through the shared supervisor."""

import argparse
import json
from pathlib import Path
import re
import sys
from PIL import Image

from humanmotionlib.prepared import read_prepared
from humanmotionlib.runtime import (DEFAULT_BUILD_TIMEOUT, DEFAULT_SLOT_TIMEOUT, InvocationError,
                           file_sha256, inspect_blender, invocation,
                           update_receipt, validate_outputs, workspace_root)


_RUN_COMPONENT = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def owning_run_root(path, workspace=None):
    """Require one valid flat run identity under build, allowing tool content below it."""
    build = (workspace_root(workspace) / "build").resolve()
    path = Path(path).resolve()
    candidate = path
    while candidate != build and candidate.parent != build:
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


def expected_outputs(prepared, output, render_dir, render_only, input_file):
    outputs = [{"path": output / "input.json", "allow_existing_sha256": file_sha256(input_file)},
               output / "build-metadata.json", output / "skeleton.blend"]
    if not render_only:
        outputs.extend((output / "evaluated.json", output / "geometry-reference.json"))
    if render_dir is not None:
        outputs.append(output / "render-manifest.json")
        scene = prepared["sources"]["review-scene"]
        extra_views = [camera["id"] for camera in scene["cameras"] if camera["id"].startswith("thorax-")]
        for sample in prepared["samples"]:
            views = ["front", "side"]
            if sample["fixture"] in ("neutral", "rest"):
                views.extend(("rear", *extra_views, *(view + "-isolated" for view in extra_views)))
            for view in views:
                outputs.append(render_dir / sample["fixture"] / view / (str(sample["frame_id"]).zfill(5) + ".png"))
    return outputs


def run(input_path, output, *, render_dir=None, render_only=False,
        timeout_seconds=DEFAULT_BUILD_TIMEOUT, slot_timeout_seconds=DEFAULT_SLOT_TIMEOUT,
        workspace=None):
    input_path = Path(input_path).resolve()
    output = Path(output).resolve()
    owner_root = owning_run_root(output, workspace)
    render_dir = Path(render_dir).resolve() if render_dir else None
    if render_dir is not None:
        try:
            render_dir.relative_to(output)
        except ValueError as error:
            raise ValueError("render directory must be inside the owning output run") from error
    if input_path.is_relative_to(output) or output.is_relative_to(input_path.parent):
        # The designated output run may also own the prepared input. A sibling
        # output root may not contain or overwrite the independent input root.
        if input_path.parent != output:
            raise ValueError("prepared input and output roots must be disjoint or share the designated run root")
    prepared = read_prepared(input_path)
    outputs = expected_outputs(prepared, output, render_dir, render_only, input_path)
    failed_preflight = validate_fresh_targets(outputs)
    if failed_preflight:
        raise ValueError("stale output preflight failed: " + ", ".join(failed_preflight))
    if output == owner_root and output.exists():
        allowed = {input_path} if input_path.parent == owner_root else set()
        unexpected = [entry for entry in output.iterdir() if entry.resolve() not in allowed]
        if unexpected:
            raise ValueError("backend run root is occupied: " + ", ".join(str(path) for path in unexpected))
    output.mkdir(parents=True, exist_ok=True)
    probe = inspect_blender(output, slot_timeout_seconds=slot_timeout_seconds, workspace=workspace)
    script = Path(__file__).with_name("build_skeleton.py").resolve()
    command = [probe["receipt"]["executable"], "--background", "--factory-startup",
               "--python-exit-code", "1", "--python", str(script), "--",
               "--input", str(input_path), "--output", str(output), "--workspace", str(workspace_root(workspace))]
    if render_dir is not None:
        command.extend(("--render-dir", str(render_dir)))
    if render_only:
        command.append("--render-only")
    receipt = invocation(command, run_root=output, operation="render-pass" if render_dir else "build",
                         cwd=workspace_root(workspace), timeout_seconds=timeout_seconds,
                         slot_timeout_seconds=slot_timeout_seconds,
                         source_sha256=prepared["content_sha256"], expected_outputs=outputs,
                         workspace=workspace)
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
    try:
        input_result = read_prepared(output / "input.json")
        if input_result["content_sha256"] != prepared["content_sha256"]:
            raise ValueError("copied prepared input hash mismatch")
        metadata = json.loads((output / "build-metadata.json").read_text())
        probe_identity = {"version": probe["version"], "build_hash": probe["build_hash"]}
        if metadata.get("blender_version") != probe_identity["version"] or metadata.get("blender_build") != probe_identity["build_hash"]:
            raise ValueError("build metadata backend identity mismatch")
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
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
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


def main(workspace=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--render-dir", type=Path)
    parser.add_argument("--render-only", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_BUILD_TIMEOUT)
    parser.add_argument("--slot-timeout-seconds", type=float, default=DEFAULT_SLOT_TIMEOUT)
    args = parser.parse_args()
    try:
        receipt = run(args.input, args.output, render_dir=args.render_dir, render_only=args.render_only,
                      timeout_seconds=args.timeout_seconds, slot_timeout_seconds=args.slot_timeout_seconds,
                      workspace=workspace)
    except (ValueError, OSError, InvocationError) as error:
        print(str(error), file=sys.stderr, flush=True)
        return 1
    print(json.dumps({"state": receipt["state"], "operation": receipt["operation"],
                      "invocation_id": receipt["invocation_id"], "receipt": receipt["stdout_log"]}, sort_keys=True),
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
