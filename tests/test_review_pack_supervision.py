# SPDX-License-Identifier: Apache-2.0
"""Review-pack render supervision and protected presentation workflows."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from PIL import Image

from tools import review_pack
from tools.runtime import InvocationError, file_sha256


def prepared_fixture():
    return {
        "content_sha256": "a" * 64,
        "samples": [{"id": "neutral-000", "fixture": "neutral", "frame_id": 0}],
        "sources": {"review-scene": {"cameras": [
            {"id": "front"}, {"id": "side"}, {"id": "rear"}, {"id": "thorax-axial"},
        ]}},
    }


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
    receipt = {
        "format": "backend-invocation/v1", "state": "succeeded", "operation": "render-pass",
        "outcome": "exit", "return_code": 0, "source_sha256": prepared["content_sha256"],
        "last_script_phase": "script_complete",
        "phases": [{"phase": "input_loaded", "prepared_sha256": prepared["content_sha256"]},
                   {"phase": "script_complete", "prepared_sha256": prepared["content_sha256"]}],
        "output_validation": {"status": "pass", "files": files},
    }
    receipt_path = output / "processes" / "render-1" / "outcome.json"
    receipt_path.parent.mkdir(parents=True)
    receipt_path.write_text(json.dumps(receipt))
    return output, frames, manifest


class ReviewPackSupervisionTests(unittest.TestCase):
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
            with self.assertRaisesRegex(ValueError, "failed, incomplete, or stale"):
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

            with (mock.patch("tools.run_blender.run", side_effect=completed_supervised_pass) as supervised,
                  mock.patch.object(review_pack, "read_prepared", return_value=prepared)):
                result = review_pack.render_pass(input_path, output, frames,
                                                 timeout_seconds=17, slot_timeout_seconds=4)
            self.assertEqual(result['prepared_sha256'], prepared['content_sha256'])
            supervised.assert_called_once_with(input_path, output, render_dir=frames, render_only=True,
                                               timeout_seconds=17, slot_timeout_seconds=4)

    def test_first_render_failure_does_not_retry_start_second_pass_or_assemble(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            argv = ["review_pack.py", "--input", str(root / "input"), "--output", str(root / "pack")]
            with (mock.patch("sys.argv", argv),
                  mock.patch.object(review_pack, "read_prepared", return_value=prepared_fixture()),
                  mock.patch.object(review_pack, "render_pass", side_effect=InvocationError("failed", "receipt")) as render,
                  mock.patch.object(review_pack, "assemble") as assemble):
                with self.assertRaises(InvocationError):
                    review_pack.main()
            self.assertEqual(render.call_count, 1)
            self.assertEqual(render.call_args.args[1], (root / "pack/clean-a").resolve())
            assemble.assert_not_called()

    def test_bounded_options_are_forwarded_for_each_supervised_render_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            argv = ["review_pack.py", "--input", str(root / "input"), "--output", str(root / "pack"),
                    "--timeout-seconds", "12", "--slot-timeout-seconds", "3"]
            with (mock.patch("sys.argv", argv),
                  mock.patch.object(review_pack, "read_prepared", return_value=prepared_fixture()),
                  mock.patch.object(review_pack, "render_pass", return_value={"prepared_sha256": "a" * 64}) as render,
                  mock.patch.object(review_pack, "assemble", return_value={"status": "pass"})):
                self.assertEqual(review_pack.main(), 0)
            self.assertEqual(render.call_count, 2)
            for call in render.call_args_list:
                self.assertEqual(call.kwargs["timeout_seconds"], 12.0)
                self.assertEqual(call.kwargs["slot_timeout_seconds"], 3.0)

    def test_html_only_mode_never_probes_or_launches_backend(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            argv = ["review_pack.py", "--html-only-from", str(root / "legacy"), "--output", str(root / "html")]
            with (mock.patch("sys.argv", argv),
                  mock.patch("tools.presentation.regenerate_html", return_value={"status": "pass"}),
                  mock.patch("tools.runtime.inspect_blender", side_effect=AssertionError("probe called")) as probe,
                  mock.patch("tools.runtime.invocation", side_effect=AssertionError("backend called")) as invocation):
                self.assertEqual(review_pack.main(), 0)
            probe.assert_not_called()
            invocation.assert_not_called()


if __name__ == "__main__":
    unittest.main()
