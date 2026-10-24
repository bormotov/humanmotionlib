# SPDX-License-Identifier: Apache-2.0
"""Review-pack render supervision and protected presentation workflows."""

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from PIL import Image

from humanmotionlib import review_pack
from humanmotionlib.package_resources import manifest_sha256, verify_runtime_integrity
from humanmotionlib.runtime import InvocationError, file_sha256


def prepared_fixture():
    return {
        "content_sha256": "a" * 64,
        "samples": [{"id": "neutral-000", "fixture": "neutral", "frame_id": 0}],
        "sampling": {"neutral": []},
        "sources": {"review-scene": {"cameras": [
            {"id": "front"}, {"id": "side"}, {"id": "rear"}, {"id": "thorax-axial"},
        ]}},
    }


def fresh_run(workspace: Path, name: str) -> Path:
    build = workspace / "build"
    build.mkdir(parents=True, exist_ok=True)
    return build / f"package-humanmotionlib_r1_test_try-1_{name}"


def supervised_pass(root: Path, prepared=None, output=None):
    prepared = prepared or prepared_fixture()
    output = output or root / "clean-a"
    frames = output / "frames"
    output.mkdir(parents=True)
    images = {}
    for view in review_pack._expected_views(prepared, prepared["samples"][0]):
        relative = f"neutral/{view}/00000.png"
        path = frames / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (2, 2), (10, 20, 30, 255)).save(path)
        images[view] = relative
    manifest = {"prepared_sha256": prepared["content_sha256"],
                "samples": [{"id": "neutral-000", "images": images}]}
    manifest_path = output / "render-manifest.json"
    manifest_path.write_text(json.dumps(manifest))
    required = [output / "input.json", output / "build-metadata.json", output / "skeleton.blend"]
    for path in required:
        path.write_bytes(b"current output")
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
    def test_normal_review_pack_owns_pass_receipts_scratch_and_reuses_without_spawn(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            source = fresh_run(workspace, "input")
            source.mkdir()
            input_path = source / "input.json"
            input_path.write_text("{}")
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
parser.add_argument("--render-dir", required=True)
parser.add_argument("--render-only", action="store_true")
args = parser.parse_args(values)
prepared = json.loads(PREPARED_JSON)
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

            invocation_count = 0
            def count_spawn(*args, **kwargs):
                nonlocal invocation_count
                invocation_count += 1
                return _real_invocation(*args, **kwargs)

            from humanmotionlib.runtime import invocation as _real_invocation
            argv = ["review-pack", "--input", str(source), "--output", str(pack)]
            with mock.patch.dict(os.environ, {"PATH": str(fake_bin) + os.pathsep + os.environ.get("PATH", "")}), \
                 mock.patch.object(review_pack, "read_prepared", return_value=prepared), \
                 mock.patch("humanmotionlib.run_blender.read_prepared", return_value=prepared), \
                 mock.patch("humanmotionlib.run_blender.invocation", side_effect=count_spawn), \
                 mock.patch("humanmotionlib.runtime.invocation", side_effect=count_spawn), \
                 mock.patch.object(review_pack, "assemble", side_effect=assemble_calls) as assemble, \
                 mock.patch("sys.argv", argv):
                self.assertEqual(review_pack.main(workspace=workspace), 0)
                self.assertEqual(invocation_count, 4)  # probe and render child for each pass
                for name in ("clean-a", "clean-b"):
                    process_root = pack / name / "processes"
                    receipts = [json.loads(path.read_text()) for path in process_root.glob("*/outcome.json")]
                    self.assertEqual({receipt["operation"] for receipt in receipts}, {"version-probe", "render-pass"})
                    self.assertTrue(all(Path(receipt["stdout_log"]).is_relative_to(process_root) for receipt in receipts))
                    self.assertTrue(all(receipt["scratch_cleanup"]["status"] == "removed-after-child-exit"
                                        for receipt in receipts))
                    self.assertTrue(all(not Path(receipt["scratch_cleanup"]["path"]).exists()
                                        for receipt in receipts))
                    self.assertFalse((pack / name / "scratch").exists())
                self.assertFalse((pack / "processes").exists())
                self.assertFalse((pack / "scratch").exists())
                pass_hashes = {name: {path.relative_to(pack / name): file_sha256(path)
                                      for path in (pack / name).rglob("*") if path.is_file()}
                               for name in ("clean-a", "clean-b")}
                argv[:] = ["review-pack", "--input", str(source), "--output", str(pack), "--reuse-renders"]
                self.assertEqual(review_pack.main(workspace=workspace), 0)
                self.assertEqual(invocation_count, 4)
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

    def test_render_pass_delegates_to_supervised_launcher_and_checks_its_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prepared = prepared_fixture()
            output = root / "clean-pass"
            frames = output / "frames"
            input_path = root / "input.json"
            input_path.write_text("prepared")
            def completed_supervised_pass(*_args, **_kwargs):
                supervised_pass(root, prepared, output)

            with (mock.patch("humanmotionlib.run_blender.run", side_effect=completed_supervised_pass) as supervised,
                  mock.patch.object(review_pack, "read_prepared", return_value=prepared)):
                result = review_pack.render_pass(input_path, output, frames,
                                                 timeout_seconds=17, slot_timeout_seconds=4,
                                                 workspace=root)
            self.assertEqual(result['prepared_sha256'], prepared['content_sha256'])
            supervised.assert_called_once_with(input_path.resolve(), output.resolve(),
                                               render_dir=frames.resolve(), render_only=True,
                                               timeout_seconds=17, slot_timeout_seconds=4,
                                               workspace=root.resolve(), owner_run=None)

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
