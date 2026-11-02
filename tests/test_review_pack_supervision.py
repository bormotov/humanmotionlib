# SPDX-License-Identifier: Apache-2.0
"""Review-pack render supervision and protected presentation workflows."""

import json
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import humanmotionlib as package

from PIL import Image

from humanmotionlib import api
from humanmotionlib import review_pack
from humanmotionlib.package_resources import manifest_sha256, verify_runtime_integrity
from humanmotionlib.runtime import InvocationError, file_sha256

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import matrix


def prepared_fixture():
    return {
        "content_sha256": "a" * 64,
        "samples": [{"id": "neutral-000", "fixture": "neutral", "frame_id": 0}],
        "sampling": {"neutral": []},
        "sources": {
            "profile": {"id": "adult-reference-v1", "stature_m": 1.7},
            "mobility": {"id": "neutral-reference-v1"},
            "review-scene": {"cameras": [
                {"id": "front"}, {"id": "side"}, {"id": "rear"}, {"id": "thorax-axial"},
            ]},
        },
    }


def fresh_run(workspace: Path, name: str) -> Path:
    build = workspace / "build"
    build.mkdir(parents=True, exist_ok=True)
    return build / f"package-humanmotionlib_r1_test_try-1_{name}"


def supervised_pass(root: Path, prepared=None, output=None, input_bytes=b"current output"):
    prepared = prepared or prepared_fixture()
    output = output or root / "clean-a"
    frames = output / "frames"
    output.mkdir(parents=True)
    records = []
    for sample in prepared["samples"]:
        images = {}
        for view in review_pack._expected_views(prepared, sample):
            relative = f"{sample['fixture']}/{view}/{str(sample['frame_id']).zfill(5)}.png"
            path = frames / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGBA", (2, 2), (10, 20, 30, 255)).save(path)
            images[view] = relative
        records.append({"id": sample["id"], "images": images})
    manifest = {"prepared_sha256": prepared["content_sha256"], "samples": records}
    manifest_path = output / "render-manifest.json"
    manifest_path.write_text(json.dumps(manifest))
    required = [output / "input.json", output / "build-metadata.json", output / "skeleton.blend"]
    for path in required:
        if path.name == "build-metadata.json":
            path.write_text(json.dumps({"blender_version": "5.2.2 LTS", "blender_build": "fixture"}))
        else:
            path.write_bytes(input_bytes)
    recorded = [*required, manifest_path, *frames.rglob("*.png")]
    files = [{"path": str(path.resolve()), "size_bytes": path.stat().st_size,
              "sha256": file_sha256(path)} for path in recorded]
    package = verify_runtime_integrity()
    receipt = {
        "format": "backend-invocation/v1", "state": "succeeded", "operation": "render-pass",
        "outcome": "exit", "return_code": 0, "source_sha256": prepared["content_sha256"],
        "package_version": package["version"], "runtime_manifest_sha256": manifest_sha256(),
        "resource_hashes": package["resources"], "backend_contract_sha256": package["backend_contract"],
        "implementation_hashes": package["implementation"],
        "last_script_phase": "script_complete",
        "phases": [{"phase": "input_loaded", "prepared_sha256": prepared["content_sha256"]},
                   {"phase": "script_complete", "prepared_sha256": prepared["content_sha256"]}],
        "output_validation": {"status": "pass", "files": files},
    }
    receipt_path = output / "processes" / "render-1" / "outcome.json"
    receipt_path.parent.mkdir(parents=True)
    receipt_path.write_text(json.dumps(receipt))
    return output, frames, manifest


def completed_pack(root: Path, prepared=None):
    prepared = prepared or prepared_fixture()
    source = fresh_run(root, "input")
    source.mkdir()
    input_path = source / "input.json"
    input_path.write_bytes(b"current output")
    pack = fresh_run(root, "pack")
    pack.mkdir()
    for name in ("clean-a", "clean-b"):
        supervised_pass(root, prepared, pack / name)
    (pack / "composites").mkdir()
    for name in (
        "acceptance-map.md", "attribution-and-limitations.md", "build-metadata.json",
        "gif-timing.json", "index.html", "render-repeatability.json", "sample-timing.json",
        "neutral.html",
    ):
        (pack / name).write_text("previous assembled output", encoding="utf-8")
    return source, pack


class ReviewPackSupervisionTests(unittest.TestCase):
    def test_review_pack_output_binding_is_opt_in_and_exact(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            build = workspace / "build"
            build.mkdir()
            element = build / "automate-build-and-verification-matrix_r1_test_current_comparison"
            expected = element / "presentation"
            self.assertEqual(review_pack._review_output_root(expected, workspace, element), expected)
            standalone = build / "pack_r1_test_try-1_review"
            self.assertEqual(review_pack._review_output_root(standalone, workspace), standalone)
            with self.assertRaises(ValueError):
                review_pack._review_output_root(element / "review-pack", workspace, element)
            with self.assertRaises(ValueError):
                review_pack._review_output_root(element / "presentation" / ".." / "presentation",
                                                workspace, element)
            self.assertFalse(element.exists())

    def test_matrix_render_pass_uses_declared_stable_presentation_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            build = workspace / "build"
            build.mkdir()
            element = build / "automate-build-and-verification-matrix_r1_test_current_comparison"
            output = element / "presentation" / "clean-a"
            input_path = build / "source_r1_test_try-1_prepared" / "prepared" / "input.json"
            input_path.parent.mkdir(parents=True)
            input_path.write_text("prepared")
            observed = {}
            def render(*args, **kwargs):
                observed.update(kwargs)
                observed["output"] = Path(kwargs["output"])
                return None
            sentinel = {"fixture": "pass"}
            with (mock.patch.object(api, "render", side_effect=render),
                  mock.patch.object(review_pack, "read_prepared", return_value=prepared_fixture()),
                  mock.patch.object(review_pack, "reuse_render_pass", return_value=sentinel)):
                result = review_pack.render_pass(
                    input_path, output, output / "frames", workspace=workspace,
                    matrix_destination={"element_root": element,
                                        "allowed_destinations": ["presentation/clean-a"]})
            self.assertIs(result, sentinel)
            self.assertEqual(observed["output"], output)
            self.assertEqual(observed["matrix_destination"], {
                "element_root": element,
                "allowed_destinations": ["presentation/clean-a"],
            })

    def test_published_nested_sealed_pass_reuses_rebased_render_and_probe_receipts(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            build = workspace / "build"
            build.mkdir()
            input_dir = build / "automate-build-and-verification-matrix_r1_test_try-1_input"
            input_dir.mkdir()
            selected_input = input_dir / "input.json"
            selected_input.write_text("selected input")
            prepared = prepared_fixture()
            work = build / "automate-build-and-verification-matrix_r1_test_try-1_work-review-pack"
            slot = build / "automate-build-and-verification-matrix_r1_test_try-1_result-review-pack"
            work.mkdir()
            output = work / "clean-a"
            source_review_pack = review_pack
            if not hasattr(source_review_pack, "_validate_matrix_receipt_relocation"):
                source_root = Path(__file__).resolve().parents[1] / "src/humanmotionlib"
                contract_spec = importlib.util.spec_from_file_location(
                    "humanmotionlib.render_contract", source_root / "render_contract.py")
                source_contract = importlib.util.module_from_spec(contract_spec)
                contract_spec.loader.exec_module(source_contract)
                source_spec = importlib.util.spec_from_file_location(
                    "matrix_test_review_pack", source_root / "review_pack.py")
                source_review_pack = importlib.util.module_from_spec(source_spec)
                with (mock.patch.dict(sys.modules, {"humanmotionlib.render_contract": source_contract}),
                      mock.patch.object(package, "render_contract", source_contract, create=True)):
                    source_spec.loader.exec_module(source_review_pack)
            with mock.patch.object(api, "_expected_render_request", create=True, return_value={
                    "render_identity": "fixture-render-identity", "character_ids": ["skeleton"]}):
                output, manifest, _request = self._sealed_pass(workspace, selected_input, prepared, output)

            journal = matrix._publish_stage_output(work, slot, "try-1", "review-pack")
            self.assertEqual(len(journal["receipt_path_rewrites"]), 2)
            published_pass = slot / "clean-a"
            probe = json.loads((published_pass / "processes" / "version-probe" / "outcome.json").read_text())
            self.assertEqual(probe["operation_root"], str(published_pass.resolve()))
            with mock.patch.object(api, "_expected_render_request", create=True, return_value={
                    "render_identity": "fixture-render-identity", "character_ids": ["skeleton"]}):
                self.assertEqual(source_review_pack.reuse_render_pass(
                    selected_input, published_pass, prepared, workspace=workspace), manifest)
                source_probe = work / "clean-a" / "processes" / "version-probe" / "outcome.json"
                source_probe_bytes = source_probe.read_bytes()
                source_probe.write_text("{}")
                with self.assertRaisesRegex(ValueError, "relocation source hash changed"):
                    source_review_pack.reuse_render_pass(
                        selected_input, published_pass, prepared, workspace=workspace)
                source_probe.write_bytes(source_probe_bytes)

    def test_default_main_reaches_owned_api_claim_before_backend(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            (workspace / "build").mkdir()
            prepared = api.prepare(workspace=workspace,
                                   output="build/review-pack_r1_test_try-1_main-input/input.json",
                                   fixtures=("neutral",), bpms=(60,))
            output = workspace / "build" / "review-pack_r1_test_try-1_main-output"
            argv = ["review-pack", "--input", str(prepared.prepared_path.parent), "--output", str(output)]
            observed = {}

            def stop_after_claim(input_path, output_path, **kwargs):
                claim = kwargs["managed_claim"]
                request_path = Path(kwargs["character_request"])
                request = json.loads(request_path.read_text())
                observed.update({"input": Path(input_path), "output": Path(output_path),
                                 "claim": claim, "request": request,
                                 "entries": sorted(path.name for path in Path(output_path).iterdir())})
                raise ValueError("stop after verifying review-pack managed claim")

            with (mock.patch("sys.argv", argv),
                  mock.patch("humanmotionlib.run_blender.run", side_effect=stop_after_claim)):
                with self.assertRaisesRegex(api.GenerationError, "stop after verifying"):
                    review_pack.main(workspace=workspace)
            self.assertEqual(observed["output"], output / "clean-a")
            self.assertEqual(observed["claim"].owner_run, str(output))
            self.assertEqual(observed["claim"].character_ids, ("skeleton",))
            self.assertEqual(observed["request"]["character_ids"], ["skeleton"])
            self.assertEqual(observed["entries"], ["character-render-request.json"])

    def test_normal_review_pack_owns_pass_receipts_scratch_and_reuses_without_spawn(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            source = fresh_run(workspace, "input")
            source.mkdir()
            input_path = source / "input.json"
            # The synthetic supervised passes persist these exact selected
            # bytes; reuse verifies byte identity against the caller input.
            input_path.write_bytes(b"current output")
            pack = fresh_run(workspace, "pack")
            prepared = prepared_fixture()
            fake_bin = workspace / "fake-bin"
            fake_bin.mkdir()
            blender = fake_bin / "blender"
            payload = json.dumps(prepared)
            script = '''#!PYTHON
import argparse, json, pathlib, shutil, sys
from PIL import Image

if "--version" in sys.argv[1:]:
    print("Blender 5.2.2 LTS")
    print("build hash: d13f752e3b9c")
    raise SystemExit(0)

values = sys.argv[sys.argv.index("--") + 1:]
parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--output", required=True)
parser.add_argument("--workspace", required=True)
parser.add_argument("--owner-run", required=True)
parser.add_argument("--expected-prepared-sha256", required=True)
parser.add_argument("--render-dir", required=True)
parser.add_argument("--render-only", action="store_true")
args = parser.parse_args(values)
prepared = json.loads(PREPARED_JSON)
if args.expected_prepared_sha256 != prepared["content_sha256"]:
    raise SystemExit("prepared identity argument mismatch")
output, frames = pathlib.Path(args.output), pathlib.Path(args.render_dir)
shutil.copyfile(args.input, output / "input.json")
(output / "build-metadata.json").write_text(json.dumps({"blender_version": "5.2.2 LTS", "blender_build": "d13f752e3b9c"}))
(output / "skeleton.blend").write_bytes(b"synthetic embedded render output")
records = []
for sample in prepared["samples"]:
    views = {"front", "side"}
    if sample["fixture"] in ("neutral", "rest"):
        views.add("rear")
        extra = {camera["id"] for camera in prepared["sources"]["review-scene"]["cameras"] if camera["id"].startswith("thorax-")}
        views.update(extra)
        views.update(view + "-isolated" for view in extra)
    images = {}
    for view in sorted(views):
        relative = f"{sample['fixture']}/{view}/{sample['frame_id']:05d}.png"
        path = frames / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (2, 2), (20, 30, 40, 255)).save(path)
        images[view] = relative
    records.append({"id": sample["id"], "images": images})
(output / "render-manifest.json").write_text(json.dumps({"prepared_sha256": prepared["content_sha256"], "samples": records}))
print("HML_PHASE " + json.dumps({"phase": "input_loaded", "prepared_sha256": prepared["content_sha256"]}), flush=True)
print("HML_PHASE " + json.dumps({"phase": "script_complete", "prepared_sha256": prepared["content_sha256"]}), flush=True)
'''.replace("PYTHON", sys.executable).replace("PREPARED_JSON", repr(payload))
            blender.write_text(script)
            blender.chmod(blender.stat().st_mode | 0o111)

            def assemble_fixture(_prepared, _pass_a, _pass_b, output):
                output = Path(output)
                (output / "composites").mkdir()
                for name in (
                    "acceptance-map.md", "attribution-and-limitations.md", "build-metadata.json",
                    "gif-timing.json", "index.html", "render-repeatability.json", "sample-timing.json",
                    "neutral.html",
                ):
                    (output / name).write_text("controlled assembly fixture")
                return {"status": "pass"}

            assemble_count = 0
            def assemble_calls(*args):
                nonlocal assemble_count
                assemble_count += 1
                if assemble_count == 1:
                    return assemble_fixture(*args)
                return {"status": "pass"}

            owned_calls = []
            def complete_owned_pass(input_path, *, workspace, output, **_kwargs):
                owned_calls.append((Path(input_path), Path(workspace), Path(output)))
                supervised_pass(Path(workspace), prepared, Path(output))

            invocation_count = 0
            def count_spawn(*args, **kwargs):
                nonlocal invocation_count
                invocation_count += 1
                return _real_invocation(*args, **kwargs)

            from humanmotionlib.runtime import invocation as _real_invocation
            argv = ["review-pack", "--input", str(source), "--output", str(pack)]
            with mock.patch.dict(os.environ, {"PATH": str(fake_bin) + os.pathsep + os.environ.get("PATH", "")}), \
                 mock.patch.object(review_pack, "read_prepared", return_value=prepared), \
                 mock.patch("humanmotionlib.api._render_owned_pass", side_effect=complete_owned_pass), \
                 mock.patch.object(review_pack, "assemble", side_effect=assemble_calls) as assemble, \
                 mock.patch("sys.argv", argv):
                self.assertEqual(review_pack.main(workspace=workspace), 0)
                self.assertEqual(len(owned_calls), 2)
                for name in ("clean-a", "clean-b"):
                    process_root = pack / name / "processes"
                    receipts = [json.loads(path.read_text()) for path in process_root.glob("*/outcome.json")]
                    self.assertEqual(len(receipts), 1)
                    self.assertEqual(receipts[0]["operation"], "render-pass")
                self.assertFalse((pack / "processes").exists())
                self.assertFalse((pack / "scratch").exists())
                pass_hashes = {name: {path.relative_to(pack / name): file_sha256(path)
                                      for path in (pack / name).rglob("*") if path.is_file()}
                               for name in ("clean-a", "clean-b")}
                argv[:] = ["review-pack", "--input", str(source), "--output", str(pack), "--reuse-renders"]
                self.assertEqual(review_pack.main(workspace=workspace), 0)
                self.assertEqual(len(owned_calls), 2)
                self.assertEqual(assemble.call_count, 2)
                self.assertEqual(pass_hashes,
                                 {name: {path.relative_to(pack / name): file_sha256(path)
                                         for path in (pack / name).rglob("*") if path.is_file()}
                                  for name in ("clean-a", "clean-b")})

    def test_reuse_reassembles_existing_pack_only_after_both_passes_are_preflighted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, pack = completed_pack(root)
            argv = ["review_pack.py", "--input", str(source), "--output", str(pack), "--reuse-renders"]
            with (mock.patch("sys.argv", argv),
                  mock.patch.object(review_pack, "read_prepared", return_value=prepared_fixture()),
                  mock.patch.object(review_pack, "render_pass") as render,
                  mock.patch.object(review_pack, "assemble", return_value={"status": "pass"}) as assemble):
                self.assertEqual(review_pack.main(workspace=root), 0)
            render.assert_not_called()
            self.assertEqual(assemble.call_count, 1)
            self.assertEqual(assemble.call_args.args[1:], (
                json.loads((pack / "clean-a" / "render-manifest.json").read_text()),
                json.loads((pack / "clean-b" / "render-manifest.json").read_text()),
                pack.resolve(),
            ))

    def test_reuse_rejects_unexpected_pack_content_without_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, pack = completed_pack(root)
            (pack / "unrelated.txt").write_text("untrusted", encoding="utf-8")
            before = {p.relative_to(pack): p.read_bytes() for p in pack.rglob("*") if p.is_file()}
            argv = ["review_pack.py", "--input", str(source), "--output", str(pack), "--reuse-renders"]
            with (mock.patch("sys.argv", argv),
                  mock.patch.object(review_pack, "read_prepared", return_value=prepared_fixture()),
                  mock.patch.object(review_pack, "assemble") as assemble):
                with self.assertRaisesRegex(ValueError, "inventory mismatch"):
                    review_pack.main(workspace=root)
            assemble.assert_not_called()
            after = {p.relative_to(pack): p.read_bytes() for p in pack.rglob("*") if p.is_file()}
            self.assertEqual(before, after)

    def test_reuse_rejects_changed_second_pass_before_any_assembly_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, pack = completed_pack(root)
            receipt_path = next((pack / "clean-b" / "processes").glob("*/outcome.json"))
            receipt = json.loads(receipt_path.read_text())
            receipt["source_sha256"] = "b" * 64
            receipt_path.write_text(json.dumps(receipt))
            before = {p.relative_to(pack): p.read_bytes() for p in pack.rglob("*") if p.is_file()}
            argv = ["review_pack.py", "--input", str(source), "--output", str(pack), "--reuse-renders"]
            with (mock.patch("sys.argv", argv),
                  mock.patch.object(review_pack, "read_prepared", return_value=prepared_fixture()),
                  mock.patch.object(review_pack, "assemble") as assemble):
                with self.assertRaisesRegex(ValueError, "package identity|failed, incomplete, or stale"):
                    review_pack.main(workspace=root)
            assemble.assert_not_called()
            after = {p.relative_to(pack): p.read_bytes() for p in pack.rglob("*") if p.is_file()}
            self.assertEqual(before, after)

    def test_reuse_rejects_selected_input_mismatch_without_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, pack = completed_pack(root)
            (source / "input.json").write_bytes(b"different selected input")
            before = {p.relative_to(pack): p.read_bytes() for p in pack.rglob("*") if p.is_file()}
            argv = ["review_pack.py", "--input", str(source), "--output", str(pack), "--reuse-renders"]
            with (mock.patch("sys.argv", argv),
                  mock.patch.object(review_pack, "read_prepared", return_value=prepared_fixture()),
                  mock.patch.object(review_pack, "assemble") as assemble):
                with self.assertRaisesRegex(ValueError, "does not match the selected build input"):
                    review_pack.main(workspace=root)
            assemble.assert_not_called()
            after = {p.relative_to(pack): p.read_bytes() for p in pack.rglob("*") if p.is_file()}
            self.assertEqual(before, after)

    def test_reuse_requires_successful_current_receipt_and_unchanged_output_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prepared = prepared_fixture()
            output, _frames, manifest = supervised_pass(root, prepared)
            self.assertEqual(review_pack.reuse_render_pass(root / "input.json", output, prepared), manifest)

            image = next((output / "frames").rglob("*.png"))
            image.write_bytes(image.read_bytes() + b"changed")
            with self.assertRaisesRegex(ValueError, "changed"):
                review_pack.reuse_render_pass(root / "input.json", output, prepared)

    def test_reuse_rejects_stale_or_incomplete_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prepared = prepared_fixture()
            output, _frames, _manifest = supervised_pass(root, prepared)
            receipt_path = next((output / "processes").glob("*/outcome.json"))
            receipt = json.loads(receipt_path.read_text())
            receipt["source_sha256"] = "b" * 64
            receipt_path.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, "package identity|failed, incomplete, or stale"):
                review_pack.reuse_render_pass(root / "input.json", output, prepared)

    def test_render_pass_uses_private_owned_api_and_checks_sealed_request_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "build").mkdir()
            prepared_result = api.prepare(
                workspace=root,
                output="build/review-pack_r1_test_try-1_api-input/input.json",
                fixtures=("neutral",), bpms=(60,),
            )
            prepared = json.loads(prepared_result.prepared_path.read_text())
            owner = root / "build" / "review-pack_r1_test_try-1_api-owner"
            owner.mkdir()
            output = owner / "clean-pass"
            frames = output / "frames"
            input_path = prepared_result.prepared_path
            def completed_supervised_pass(*_args, **_kwargs):
                self._sealed_pass(root, input_path, prepared, output)

            with (mock.patch("humanmotionlib.api._render_owned_pass", side_effect=completed_supervised_pass) as owned,
                  mock.patch.object(review_pack, "read_prepared", return_value=prepared)):
                result = review_pack.render_pass(input_path, output, frames,
                                                 timeout_seconds=17, slot_timeout_seconds=4,
                                                 workspace=root, owner_run=owner)
            self.assertEqual(result['prepared_sha256'], prepared['content_sha256'])
            owned.assert_called_once_with(input_path.resolve(), workspace=root.resolve(),
                                          output=output.resolve(), owner_run=owner,
                                          images=True, render_dir=frames.resolve(), render_only=True,
                                          timeout_seconds=17, slot_timeout_seconds=4)
            self.assertEqual(result['render_identity'],
                             json.loads((output / "character-render-request.json").read_text())[
                                 "render_identity"])
            receipt = review_pack._read_supervised_receipt(
                output, prepared,
                review_pack._validate_manifest(result, prepared, frames, output=output)
                + [Path("character-render-request.json")],
            )
            self.assertTrue(any(path["path"].endswith("character-render-request.json")
                                for path in receipt["output_validation"]["files"]))

    def test_standalone_render_pass_uses_public_api(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prepared = prepared_fixture()
            output = root / "clean-pass"
            frames = output / "frames"
            input_path = root / "input.json"
            input_path.write_text("prepared")

            def completed_public_pass(_input, *, output, **_kwargs):
                supervised_pass(root, prepared, output)

            with (mock.patch("humanmotionlib.api.render", side_effect=completed_public_pass) as public_render,
                  mock.patch.object(review_pack, "read_prepared", return_value=prepared)):
                review_pack.render_pass(input_path, output, frames, workspace=root)
            public_render.assert_called_once_with(input_path.resolve(), workspace=root.resolve(),
                                                  output=output.resolve(), images=True,
                                                  render_dir=frames.resolve(), render_only=True,
                                                  timeout_seconds=review_pack.DEFAULT_RENDER_TIMEOUT,
                                                  slot_timeout_seconds=review_pack.DEFAULT_SLOT_TIMEOUT)

    def _sealed_pass(self, workspace, input_path, prepared, output):
        output, _frames, manifest = supervised_pass(
            workspace, prepared, output, input_bytes=Path(input_path).read_bytes())
        request = api._expected_render_request(input_path, workspace=workspace,
                                               characters=("skeleton",), render_only=True)
        (output / "character-render-request.json").write_text(json.dumps(request), encoding="utf-8")
        manifest["render_identity"] = request["render_identity"]
        (output / "render-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        metadata_path = output / "build-metadata.json"
        metadata_path.write_text(json.dumps({"blender_version": "5.2.2 LTS",
                                             "blender_build": "fixture",
                                             "render_identity": request["render_identity"]}),
                                 encoding="utf-8")
        receipt_path = next((output / "processes").glob("*/outcome.json"))
        receipt = json.loads(receipt_path.read_text())
        receipt["phases"].append({"phase": "script_complete",
                                  "prepared_sha256": prepared["content_sha256"],
                                  "render_identity": request["render_identity"],
                                  "character_ids": ["skeleton"]})
        records = []
        for path in [output / "input.json", output / "build-metadata.json", output / "skeleton.blend",
                     output / "render-manifest.json", output / "character-render-request.json",
                     *(output / "frames").rglob("*.png")]:
            records.append({"path": str(path.resolve()), "size_bytes": path.stat().st_size,
                            "sha256": file_sha256(path)})
        receipt["output_validation"]["files"] = records
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        probe_root = output / "processes" / "version-probe"
        probe_root.mkdir()
        probe = {key: receipt[key] for key in (
            "format", "package_version", "runtime_manifest_sha256", "resource_hashes",
            "backend_contract_sha256", "implementation_hashes",
        )}
        probe.update({
            "operation": "version-probe", "state": "succeeded", "outcome": "exit",
            "return_code": 0, "source_sha256": None, "last_script_phase": "unknown",
            "phases": [], "expected_outputs": [],
            "output_validation": {"status": "not-required"},
            "backend_identity": {"version": "5.2.2 LTS", "build_hash": "fixture"},
            "operation_root": str(output.resolve()),
        })
        (probe_root / "outcome.json").write_text(json.dumps(probe), encoding="utf-8")
        return output, manifest, request

    def test_sealed_skeleton_pass_reuse_requires_exact_request_and_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            (workspace / "build").mkdir()
            result = api.prepare(workspace=workspace,
                                 output="build/review-pack_r1_test_try-1_sealed-input/input.json",
                                 fixtures=("neutral",), bpms=(60,))
            prepared = json.loads(result.prepared_path.read_text())
            output = workspace / "build" / "review-pack_r1_test_try-1_sealed-pass"
            output, manifest, request = self._sealed_pass(workspace, result.prepared_path,
                                                          prepared, output)
            self.assertEqual(review_pack.reuse_render_pass(result.prepared_path, output, prepared,
                                                           workspace=workspace), manifest)

            request_path = output / "character-render-request.json"
            original = request_path.read_bytes()
            request["character_ids"] = ["male"]
            request_path.write_text(json.dumps(request), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "(?i)sealed render request"):
                review_pack.reuse_render_pass(result.prepared_path, output, prepared,
                                              workspace=workspace)
            request_path.write_bytes(original)

            request_path.unlink()
            with self.assertRaisesRegex(ValueError, "(?i)sealed render request is missing"):
                review_pack.reuse_render_pass(result.prepared_path, output, prepared,
                                              workspace=workspace)

    def test_reuse_counts_render_operations_and_rejects_bad_probe_receipts(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            (workspace / "build").mkdir()
            result = api.prepare(workspace=workspace,
                                 output="build/review-pack_r1_test_try-1_process-input/input.json",
                                 fixtures=("neutral",), bpms=(60,))
            prepared = json.loads(result.prepared_path.read_text())

            def new_pass(label):
                output = workspace / "build" / f"review-pack_r1_test_try-1_{label}"
                return self._sealed_pass(workspace, result.prepared_path, prepared, output)[0]

            output = new_pass("two-operation-pass")
            self.assertEqual(review_pack.reuse_render_pass(result.prepared_path, output, prepared,
                                                           workspace=workspace)["render_identity"],
                             json.loads((output / "character-render-request.json").read_text())[
                                 "render_identity"])

            output = new_pass("failed-probe-pass")
            probe_path = next(path for path in (output / "processes").glob("*/outcome.json")
                              if json.loads(path.read_text())["operation"] == "version-probe")
            probe = json.loads(probe_path.read_text())
            probe["state"] = "failed"
            probe["outcome"] = "exit"
            probe_path.write_text(json.dumps(probe), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Version-probe receipt"):
                review_pack.reuse_render_pass(result.prepared_path, output, prepared,
                                              workspace=workspace)

            output = new_pass("failed-render-pass")
            render_path = next(path for path in (output / "processes").glob("*/outcome.json")
                               if json.loads(path.read_text())["operation"] == "render-pass")
            render = json.loads(render_path.read_text())
            render["state"] = "failed"
            render_path.write_text(json.dumps(render), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Render receipt is failed"):
                review_pack.reuse_render_pass(result.prepared_path, output, prepared,
                                              workspace=workspace)

            output = new_pass("duplicate-probe-pass")
            probe_path = next(path for path in (output / "processes").glob("*/outcome.json")
                              if json.loads(path.read_text())["operation"] == "version-probe")
            duplicate = output / "processes" / "duplicate-probe" / "outcome.json"
            duplicate.parent.mkdir()
            duplicate.write_bytes(probe_path.read_bytes())
            with self.assertRaisesRegex(ValueError, "at most one version-probe"):
                review_pack.reuse_render_pass(result.prepared_path, output, prepared,
                                              workspace=workspace)

            output = new_pass("missing-probe-pass")
            probe_path = next(path for path in (output / "processes").glob("*/outcome.json")
                              if json.loads(path.read_text())["operation"] == "version-probe")
            probe_path.unlink()
            probe_path.parent.rmdir()
            with self.assertRaisesRegex(ValueError, "requires exactly one version-probe"):
                review_pack.reuse_render_pass(result.prepared_path, output, prepared,
                                              workspace=workspace)

            output = new_pass("duplicate-render-pass")
            render_path = next(path for path in (output / "processes").glob("*/outcome.json")
                               if json.loads(path.read_text())["operation"] == "render-pass")
            duplicate = output / "processes" / "duplicate-render" / "outcome.json"
            duplicate.parent.mkdir()
            duplicate.write_bytes(render_path.read_bytes())
            with self.assertRaisesRegex(ValueError, "one render-pass"):
                review_pack.reuse_render_pass(result.prepared_path, output, prepared,
                                              workspace=workspace)

            output = new_pass("missing-render-pass")
            render_path = next(path for path in (output / "processes").glob("*/outcome.json")
                               if json.loads(path.read_text())["operation"] == "render-pass")
            render_path.unlink()
            render_path.parent.rmdir()
            with self.assertRaisesRegex(ValueError, "one render-pass"):
                review_pack.reuse_render_pass(result.prepared_path, output, prepared,
                                              workspace=workspace)

    def test_first_render_failure_does_not_retry_start_second_pass_or_assemble(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_root = fresh_run(root, "input")
            input_root.mkdir()
            (input_root / "input.json").write_text("prepared")
            output = fresh_run(root, "pack")
            argv = ["review_pack.py", "--input", str(input_root), "--output", str(output)]
            with (mock.patch("sys.argv", argv),
                  mock.patch.object(review_pack, "read_prepared", return_value=prepared_fixture()),
                  mock.patch.object(review_pack, "render_pass", side_effect=InvocationError("failed", "receipt")) as render,
                  mock.patch.object(review_pack, "assemble") as assemble):
                with self.assertRaises(InvocationError):
                    review_pack.main(workspace=root)
            self.assertEqual(render.call_count, 1)
            self.assertEqual(render.call_args.args[1], (output / "clean-a").resolve())
            assemble.assert_not_called()

    def test_bounded_options_are_forwarded_for_each_supervised_render_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_root = fresh_run(root, "input")
            input_root.mkdir()
            (input_root / "input.json").write_text("prepared")
            output = fresh_run(root, "pack")
            argv = ["review_pack.py", "--input", str(input_root), "--output", str(output),
                    "--timeout-seconds", "12", "--slot-timeout-seconds", "3"]
            with (mock.patch("sys.argv", argv),
                  mock.patch.object(review_pack, "read_prepared", return_value=prepared_fixture()),
                  mock.patch.object(review_pack, "render_pass", return_value={"prepared_sha256": "a" * 64}) as render,
                  mock.patch.object(review_pack, "assemble", return_value={"status": "pass"})):
                self.assertEqual(review_pack.main(workspace=root), 0)
            self.assertEqual(render.call_count, 2)
            for call in render.call_args_list:
                self.assertEqual(call.kwargs["timeout_seconds"], 12.0)
                self.assertEqual(call.kwargs["slot_timeout_seconds"], 3.0)

    def test_normal_review_accepts_explicit_valid_input_from_another_workspace_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_workspace = root / "protected-source"
            output_workspace = root / "caller-workspace"
            input_root = fresh_run(source_workspace, "input")
            input_root.mkdir(parents=True)
            input_path = input_root / "input.json"
            input_path.write_text("protected prepared bytes")
            before = input_path.read_bytes()
            output = fresh_run(output_workspace, "pack")
            argv = ["review_pack.py", "--input", str(input_root), "--output",
                    str(output.relative_to(output_workspace))]
            with (mock.patch("sys.argv", argv),
                  mock.patch.object(review_pack, "read_prepared", return_value=prepared_fixture()),
                  mock.patch.object(review_pack, "render_pass", return_value={"prepared_sha256": "a" * 64}),
                  mock.patch.object(review_pack, "assemble", return_value={"status": "pass"})):
                self.assertEqual(review_pack.main(workspace=output_workspace), 0)
            self.assertEqual(input_path.read_bytes(), before)

    def test_html_only_mode_never_probes_or_launches_backend(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = fresh_run(root, "html")
            argv = ["review_pack.py", "--html-only-from", str(root / "legacy"), "--output", str(output)]
            with (mock.patch("sys.argv", argv),
                  mock.patch("humanmotionlib.presentation.regenerate_html", return_value={"status": "pass"}),
                  mock.patch("humanmotionlib.runtime.inspect_blender", side_effect=AssertionError("probe called")) as probe,
                  mock.patch("humanmotionlib.runtime.invocation", side_effect=AssertionError("backend called")) as invocation):
                self.assertEqual(review_pack.main(workspace=root), 0)
            probe.assert_not_called()
            invocation.assert_not_called()


if __name__ == "__main__":
    unittest.main()
