# SPDX-License-Identifier: Apache-2.0
"""Focused checks for the small manual character/stature matrix interface."""
from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import hashlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import matrix


class MatrixWorkflowTests(unittest.TestCase):
    def test_exact_matrix_timeline_rejects_changed_time_even_with_same_members(self):
        def entry(fixture, frame, beat_num, beat_den, sec_num, sec_den):
            return {"sample_id": f"{fixture}/{frame:05d}", "frame_id": frame,
                    "beat": {"numerator": beat_num, "denominator": beat_den},
                    "seconds": {"numerator": sec_num, "denominator": sec_den}}
        sampling = {}
        samples = []
        for fixture in matrix.FIXTURES:
            if fixture == "arm-raise":
                static_frames = (0, 3, 6, 9, 12)
                animation_frames = range(13)
            else:
                static_frames = (0,)
                animation_frames = (0,)
            static = [entry(fixture, f, f // 3 if fixture == "arm-raise" else 0, 1,
                            f if fixture == "arm-raise" else 0,
                            6 if fixture == "arm-raise" else 1)
                      for f in static_frames]
            animation = [entry(fixture, f, f, 3, f, 6) for f in animation_frames]
            if fixture != "arm-raise":
                animation = [entry(fixture, 0, 0, 1, 0, 1)]
            sampling[fixture] = [{"bpm": 120, "static": static, "animation": animation}]
            samples.extend({"id": f"{fixture}/{f:05d}"} for f in animation_frames)
        prepared = {"sampling": sampling, "samples": samples}
        matrix._validate_matrix_sampling(prepared)
        sampling["arm-raise"][0]["animation"][4]["seconds"] = {"numerator": 7, "denominator": 12}
        with self.assertRaisesRegex(matrix.MatrixError, "timeline differs"):
            matrix._validate_matrix_sampling(prepared)

    def test_actual_matrix_assembler_and_validator_accept_real_shaped_receipts(self):
        from humanmotionlib import api
        from humanmotionlib.package_resources import manifest_sha256, verify_runtime_integrity
        from humanmotionlib.render_contract import expected_views

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            (workspace / "build").mkdir()
            root = matrix.element_root(workspace, "male", 1.70)
            root.mkdir()
            prepared_path = root / "prepared" / "input.json"
            # Invoke the installed host API with its explicit matrix binding.
            prepared_result = api.prepare(workspace=workspace, output=prepared_path, stature=1.70,
                fixtures=matrix.FIXTURES, bpms=(120,),
                matrix_destination=matrix.matrix_binding(root, api.MATRIX_DESTINATIONS["prepare"]))
            self.assertEqual(prepared_result.prepared_path, prepared_path.resolve())
            prepared = json.loads(prepared_path.read_text(encoding="utf-8"))
            render_root = root / "render"
            frames = render_root / "frames"
            frames.mkdir(parents=True)
            (render_root / "input.json").write_bytes(prepared_path.read_bytes())
            (render_root / "build-metadata.json").write_text("{}", encoding="utf-8")
            (render_root / "skeleton.blend").write_bytes(b"controlled synthetic fixture")
            (render_root / "character-render-request.json").write_text("{}", encoding="utf-8")
            records = []
            for sample in prepared["samples"]:
                images = {}
                for view in sorted({"front", "side", "rear"} if sample["fixture"] in ("neutral", "rest")
                                   else {"front", "side"}):
                    relative = Path("male") / sample["fixture"] / view / f"{sample['frame_id']:05d}.png"
                    path = frames / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    from PIL import Image
                    Image.new("RGB", (1024, 1024),
                              (sample["frame_id"] % 255, len(view) * 17, len(sample["fixture"]) * 13)).save(path)
                    images[view] = str(relative)
                records.append({"id": sample["id"], "images": images})
            manifest = {"format": "character-render-manifest/v1",
                        "prepared_sha256": prepared["content_sha256"],
                        "characters": [{"id": "male", "samples": records}]}
            manifest_path = render_root / "render-manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (render_root / "processes" / "version").mkdir(parents=True)
            (render_root / "processes" / "version" / "outcome.json").write_text(
                json.dumps({"operation": "version-probe", "state": "succeeded"}), encoding="utf-8")
            receipt_path = render_root / "processes" / "render" / "outcome.json"
            receipt_path.parent.mkdir()
            runtime = verify_runtime_integrity()
            image_paths = [Path("frames") / Path(*row["images"][key].split("/"))
                           for row in records for key in row["images"]]
            required = [Path("input.json"), Path("build-metadata.json"), Path("skeleton.blend"),
                        Path("render-manifest.json"), Path("character-render-request.json"), *image_paths]
            files = []
            for relative in required:
                path = render_root / relative
                files.append({"path": str(path.resolve()), "size_bytes": path.stat().st_size,
                              "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            digest = prepared["content_sha256"]
            receipt = {"operation": "render-pass", "state": "succeeded", "outcome": "exit",
                "return_code": 0, "source_sha256": digest, "last_script_phase": "script_complete",
                "phases": [{"phase": name, "prepared_sha256": digest}
                           for name in ("input_loaded", "script_complete")],
                "package_version": runtime["version"], "runtime_manifest_sha256": manifest_sha256(),
                "resource_hashes": runtime["resources"], "backend_contract_sha256": runtime["backend_contract"],
                "implementation_hashes": runtime["implementation"],
                "output_validation": {"status": "pass", "files": files}}
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            presentation = root / "presentation"
            presentation.mkdir()
            result = matrix.assemble_presentation(prepared_path, manifest_path, frames, presentation,
                workspace=workspace, character_ids=("male",), matrix_element_root=root,
                fixtures=matrix.FIXTURES, metadata={"stature_m": 1.7, "bpm": 120})
            self.assertEqual(result["source_image_count"], 32)
            build = {"prepared": str(prepared_path), "render_root": str(render_root),
                     "render_manifest": str(manifest_path), "presentation": str(presentation),
                     "presentation_inventory": str(presentation / "presentation-inventory.json"),
                     "render_receipt": str(receipt_path)}
            self.assertEqual(matrix.validate_output(workspace, root, "male", 1.70, build)["producer"], "pass")
            (frames / "unlisted-extra.png").write_bytes((frames / "male/neutral/front/00000.png").read_bytes())
            with self.assertRaisesRegex(matrix.MatrixError, "exactly match"):
                matrix.validate_output(workspace, root, "male", 1.70, build)

    def test_skeleton_manifest_receipt_includes_character_request_and_keeps_legacy_optional(self):
        from humanmotionlib import api
        from humanmotionlib.package_resources import manifest_sha256, verify_runtime_integrity
        from humanmotionlib.render_contract import expected_views, validate_manifest
        from PIL import Image

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            (workspace / "build").mkdir()
            root = matrix.element_root(workspace, "skeleton", 1.50)
            root.mkdir()
            prepared_path = root / "prepared" / "input.json"
            api.prepare(workspace=workspace, output=prepared_path, stature=1.50,
                        fixtures=matrix.FIXTURES, bpms=(120,),
                        matrix_destination=matrix.matrix_binding(root, api.MATRIX_DESTINATIONS["prepare"]))
            prepared = json.loads(prepared_path.read_text(encoding="utf-8"))
            render_root = root / "render"
            frames = render_root / "frames"
            frames.mkdir(parents=True)
            (render_root / "input.json").write_bytes(prepared_path.read_bytes())
            (render_root / "build-metadata.json").write_text("{}", encoding="utf-8")
            (render_root / "skeleton.blend").write_bytes(b"controlled synthetic skeleton")
            request_path = render_root / "character-render-request.json"
            request_path.write_text("{}", encoding="utf-8")
            records = []
            for sample in prepared["samples"]:
                images = {}
                for view in sorted(expected_views(prepared, sample)):
                    relative = Path(sample["fixture"]) / view / f"{sample['frame_id']:05d}.png"
                    path = frames / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    Image.new("RGB", (1024, 1024),
                              (sample["frame_id"] % 255, len(view) * 11, len(sample["fixture"]) * 9)).save(path)
                    images[view] = relative.as_posix()
                records.append({"id": sample["id"], "images": images})
            manifest = {"prepared_sha256": prepared["content_sha256"], "samples": records}
            manifest_path = render_root / "render-manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            render_receipt = render_root / "processes" / "pass" / "outcome.json"
            render_receipt.parent.mkdir(parents=True)
            runtime = verify_runtime_integrity()
            required = validate_manifest(manifest, prepared, frames, output=render_root)
            self.assertIn(Path("character-render-request.json"), required)
            files = []
            for relative in required:
                path = render_root / relative
                files.append({"path": str(path.resolve()), "size_bytes": path.stat().st_size,
                              "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            digest = prepared["content_sha256"]
            receipt = {"operation": "render-pass", "state": "succeeded", "outcome": "exit",
                "return_code": 0, "source_sha256": digest, "last_script_phase": "script_complete",
                "phases": [{"phase": name, "prepared_sha256": digest}
                           for name in ("input_loaded", "script_complete")],
                "package_version": runtime["version"], "runtime_manifest_sha256": manifest_sha256(),
                "resource_hashes": runtime["resources"], "backend_contract_sha256": runtime["backend_contract"],
                "implementation_hashes": runtime["implementation"],
                "output_validation": {"status": "pass", "files": files}}
            render_receipt.write_text(json.dumps(receipt), encoding="utf-8")
            (render_root / "processes" / "probe").mkdir()
            (render_root / "processes" / "probe" / "outcome.json").write_text(
                json.dumps({"operation": "version-probe"}), encoding="utf-8")
            presentation = root / "presentation"
            presentation.mkdir()
            assembled = matrix.assemble_presentation(prepared_path, manifest_path, frames, presentation,
                workspace=workspace, character_ids=("skeleton",), matrix_element_root=root,
                fixtures=matrix.FIXTURES)
            self.assertEqual(assembled["source_image_count"], 44)
            build = {"prepared": str(prepared_path), "render_root": str(render_root),
                     "render_manifest": str(manifest_path), "presentation": str(presentation),
                     "presentation_inventory": str(presentation / "presentation-inventory.json"),
                     "render_receipt": str(render_receipt)}
            self.assertEqual(matrix.validate_output(workspace, root, "skeleton", 1.50, build)["producer"], "pass")

            legacy_root = workspace / "build" / "legacy_skeleton_fixture"
            legacy_root.mkdir()
            legacy_frames = legacy_root / "frames"
            legacy_frames.mkdir()
            legacy_manifest = {"prepared_sha256": prepared["content_sha256"], "samples": []}
            self.assertNotIn(Path("character-render-request.json"),
                             validate_manifest(legacy_manifest, {"content_sha256": prepared["content_sha256"],
                                 "samples": [], "sources": {"review-scene": {"cameras": []}}},
                                 legacy_frames, output=legacy_root))

    def test_list_is_read_only_and_lists_all_nine_stable_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            before = list(workspace.iterdir())
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(matrix.main(["list", "--workspace", str(workspace)]), 0)
            rows = json.loads(output.getvalue())["rows"]
            self.assertEqual(len(rows), 9)
            self.assertEqual([(row["character"], row["height_m"]) for row in rows],
                             [(c, h) for c in matrix.CHARACTERS for h in matrix.HEIGHTS])
            self.assertTrue(all(Path(row["path"]).parent == workspace / "build" for row in rows))
            self.assertEqual(list(workspace.iterdir()), before)

    def test_direct_cli_list_does_not_create_bytecode_or_workspace_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            cache = ROOT / "tools" / "__pycache__"
            before = ({path.relative_to(cache): path.read_bytes() for path in cache.rglob("*.pyc")}
                      if cache.exists() else {})
            result = subprocess.run([sys.executable, str(ROOT / "tools/matrix.py"), "list",
                                      "--workspace", str(workspace)], cwd=ROOT,
                                     text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(result.returncode, 0, result.stderr)
            after = ({path.relative_to(cache): path.read_bytes() for path in cache.rglob("*.pyc")}
                     if cache.exists() else {})
            self.assertEqual(after, before)
            self.assertEqual(list(workspace.iterdir()), [])

    def test_missing_unknown_and_invalid_selection_fail_before_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            for argv in (
                ["build", "--workspace", str(workspace)],
                ["build", "--workspace", str(workspace), "--character", "other", "--height", "1.70"],
                ["check", "--workspace", str(workspace), "--character", "male", "--height", "1.8"],
            ):
                with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()):
                    self.assertNotEqual(matrix.main(argv), 0)
            self.assertEqual(list(workspace.iterdir()), [])

    def test_selection_derives_same_five_component_root_each_time(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            parser = matrix.parser()
            args_a = parser.parse_args(["build", "--workspace", str(workspace),
                                        "--character", "male", "--height", "1.70"])
            args_b = parser.parse_args(["check", "--workspace", str(workspace),
                                        "--character", "male", "--height", "1.70"])
            self.assertEqual(matrix.selection(args_a)[1], matrix.selection(args_b)[1])
            self.assertEqual(matrix.selection(args_a)[1].name,
                             "automate-build-and-verification-matrix_r1_dev_current_male-h170")
            self.assertEqual(len(matrix.selection(args_a)[1].name.split("_")), 5)

    def test_make_routes_literal_commands_to_same_cli_selection(self):
        for target, action in (("matrix-build", "build"), ("matrix-check", "check")):
            command = ["make", "-n", "-f", str(ROOT / "Makefile"), target,
                       "WORKSPACE=/tmp", "UV=uv", "CHARACTER=male", "HEIGHT=1.70"]
            result = subprocess.run(command, cwd=ROOT, check=True, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertIn(f"sh tools/repository.sh matrix-{action} \"/tmp\" \"uv\" \"male\" \"1.70\"",
                          result.stdout)

    def test_build_repeats_whole_selected_sequence_at_original_paths(self):
        import humanmotionlib.api as api
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            root = matrix.element_root(workspace, "female", 1.90)
            root.mkdir(parents=True)
            (root / "check.json").write_text('{"status":"success"}', encoding="utf-8")
            (root / "prepared").mkdir()
            (root / "prepared" / "old.bin").write_bytes(b"old generated bytes")
            (root / "unrelated.txt").write_text("preserve", encoding="utf-8")
            calls: list[tuple[str, dict]] = []

            def prepare(**kwargs):
                calls.append(("prepare", kwargs))
                Path(kwargs["output"]).parent.mkdir(parents=True, exist_ok=True)
                Path(kwargs["output"]).write_text("{}", encoding="utf-8")
                return SimpleNamespace(prepared_path=Path(kwargs["output"]), prepared_sha256="p" * 64,
                                       package_identity={"version": "fixture"})

            def render(prepared, **kwargs):
                calls.append(("render", kwargs))
                output = Path(kwargs["output"])
                (output / "frames").mkdir(parents=True, exist_ok=True)
                manifest = output / "render-manifest.json"
                manifest.write_text("{}", encoding="utf-8")
                return SimpleNamespace(output_root=output, artifacts={"render_manifest": manifest},
                                       backend_identity={"version": "fixture"},
                                       receipt_path=output / "receipt.json")

            def assemble(*args, **kwargs):
                calls.append(("presentation", kwargs))
                return {"source_image_count": 32, "media_count": 12}

            (workspace / "build").mkdir(exist_ok=True)
            with patch.object(api, "prepare", side_effect=prepare), \
                    patch.object(api, "render", side_effect=render), \
                    patch.object(matrix, "assemble_presentation", side_effect=assemble), \
                    patch.object(matrix, "validate_installed_api"), \
                    patch.object(matrix, "validate_output", return_value={"producer": "pass"}):
                with contextlib.redirect_stdout(io.StringIO()):
                    for _ in range(2):
                        self.assertEqual(matrix.main(["build", "--workspace", str(workspace),
                                                      "--character", "female", "--height", "1.90"]), 0)
            self.assertEqual([name for name, _ in calls],
                             ["prepare", "render", "presentation"] * 2)
            self.assertTrue(all(call[1]["fixtures"] == matrix.FIXTURES and
                                call[1]["bpms"] == (120,) for call in calls if call[0] == "prepare"))
            self.assertTrue(all(call[1]["characters"] == ("female",) and call[1]["render_only"]
                                for call in calls if call[0] == "render"))
            self.assertTrue(all(call["output"] == root / "render" for name, call in calls
                                if name == "render"))
            build = json.loads((root / "build.json").read_text(encoding="utf-8"))
            self.assertFalse((root / "check.json").exists())
            self.assertEqual((root / "unrelated.txt").read_text(encoding="utf-8"), "preserve")
            self.assertEqual(build["render_manifest"], str(root / "render" / "render-manifest.json"))
            self.assertEqual(build["render_receipt"], str(root / "render" / "receipt.json"))
            self.assertEqual(len(list((root / "logs").glob("build-*.log"))), 2)

    def test_check_refuses_absent_result_and_build_record_without_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            root = matrix.element_root(workspace, "male", 1.70)
            arguments = ["check", "--workspace", str(workspace),
                         "--character", "male", "--height", "1.70"]

            def snapshot() -> dict[str, bytes | None]:
                found: dict[str, bytes | None] = {}
                if not workspace.exists():
                    return found
                for path in workspace.rglob("*"):
                    relative = path.relative_to(workspace).as_posix()
                    found[relative] = path.read_bytes() if path.is_file() and not path.is_symlink() else None
                return found

            for setup in ("absent-root", "absent-build"):
                if setup == "absent-build":
                    root.mkdir(parents=True)
                    (root / "unrelated.txt").write_text("preserve", encoding="utf-8")
                before = snapshot()
                error = io.StringIO()
                with contextlib.redirect_stderr(error):
                    status = matrix.main(arguments)
                self.assertEqual(status, 2)
                self.assertIn("make matrix-build CHARACTER=male HEIGHT=1.70", error.getvalue())
                self.assertEqual(snapshot(), before)

    def test_check_with_missing_compatible_package_is_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            root = matrix.element_root(workspace, "male", 1.70)
            root.mkdir(parents=True)
            record = root / "build.json"
            record.write_text("{}", encoding="utf-8")
            before = {p.relative_to(workspace).as_posix(): p.read_bytes()
                      for p in workspace.rglob("*") if p.is_file()}
            error = io.StringIO()
            with patch.object(matrix, "installed_package_identity", side_effect=ImportError("missing HML")), \
                    contextlib.redirect_stderr(error):
                status = matrix.main(["check", "--workspace", str(workspace),
                                      "--character", "male", "--height", "1.70"])
            self.assertEqual(status, 2)
            self.assertIn("make matrix-build CHARACTER=male HEIGHT=1.70", error.getvalue())
            after = {p.relative_to(workspace).as_posix(): p.read_bytes()
                     for p in workspace.rglob("*") if p.is_file()}
            self.assertEqual(after, before)

    def test_check_logs_malformed_existing_build_record_without_changing_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            root = matrix.element_root(workspace, "male", 1.70)
            root.mkdir(parents=True)
            build = root / "build.json"
            build.write_text("{ malformed", encoding="utf-8")
            before = build.read_bytes()
            with contextlib.redirect_stdout(io.StringIO()):
                status = matrix.main(["check", "--workspace", str(workspace),
                                      "--character", "male", "--height", "1.70"])
            self.assertEqual(status, 1)
            self.assertEqual(build.read_bytes(), before)
            report = json.loads((root / "check.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "failure")
            self.assertEqual(len(list((root / "logs").glob("check-*.log"))), 1)

    def test_check_logs_incompatible_record_package_and_preserves_build_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            root = matrix.element_root(workspace, "male", 1.70)
            (root / "prepared").mkdir(parents=True)
            prepared = root / "prepared/input.json"
            prepared.write_text("preserve prepared input", encoding="utf-8")
            record = root / "build.json"
            record.write_text(json.dumps({"schema": "matrix-current-build/v1", "status": "success",
                "character": "male", "height_m": 1.7, "fixtures": list(matrix.FIXTURES),
                "bpm": 120, "package_identity": {"runtime_manifest_sha256": "old-package"}}),
                encoding="utf-8")
            before = {path.relative_to(root).as_posix(): path.read_bytes()
                      for path in (record, prepared)}
            with contextlib.redirect_stdout(io.StringIO()):
                status = matrix.main(["check", "--workspace", str(workspace),
                                      "--character", "male", "--height", "1.70"])
            self.assertEqual(status, 1)
            after = {path.relative_to(root).as_posix(): path.read_bytes()
                     for path in (record, prepared)}
            self.assertEqual(after, before)
            report = json.loads((root / "check.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "failure")
            self.assertIn("make matrix-build CHARACTER=male HEIGHT=1.70", report["checks"]["error"])
            self.assertEqual(len(list((root / "logs").glob("check-*.log"))), 1)

    def test_check_repeats_validators_without_touching_generated_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            root = matrix.element_root(workspace, "female", 1.50)
            (root / "logs").mkdir(parents=True)
            prepared = root / "prepared" / "input.json"
            prepared.parent.mkdir()
            prepared.write_text("prepared fixture", encoding="utf-8")
            build = {"schema": "matrix-current-build/v1", "status": "success",
                     "character": "female", "height_m": 1.5,
                     "fixtures": list(matrix.FIXTURES), "bpm": 120,
                     "package_identity": matrix.installed_package_identity()}
            (root / "build.json").write_text(json.dumps(build), encoding="utf-8")
            before = prepared.read_bytes()
            arguments = ["check", "--workspace", str(workspace),
                         "--character", "female", "--height", "1.50"]
            with patch.object(matrix, "validate_output", return_value={"producer": "pass"}) as validate, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(matrix.main(arguments), 0)
                self.assertEqual(matrix.main(arguments), 0)
            self.assertEqual(validate.call_count, 2)
            self.assertEqual(prepared.read_bytes(), before)
            self.assertEqual(len(list((root / "logs").glob("check-*.log"))), 2)
            self.assertEqual(json.loads((root / "check.json").read_text())["status"], "success")

    def test_late_build_failure_cleans_partial_output_and_full_retry_passes(self):
        import humanmotionlib.api as api

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            root = matrix.element_root(workspace, "skeleton", 1.50)
            calls: list[str] = []

            def prepare(**kwargs):
                calls.append("prepare")
                Path(kwargs["output"]).parent.mkdir(parents=True, exist_ok=True)
                Path(kwargs["output"]).write_text("{}", encoding="utf-8")
                return SimpleNamespace(prepared_path=Path(kwargs["output"]), prepared_sha256="p" * 64,
                                       package_identity={"version": "fixture"})

            def render(prepared, **kwargs):
                calls.append("render")
                output = Path(kwargs["output"])
                (output / "frames").mkdir(parents=True, exist_ok=True)
                manifest = output / "render-manifest.json"
                manifest.write_text("{}", encoding="utf-8")
                return SimpleNamespace(output_root=output, artifacts={"render_manifest": manifest},
                                       backend_identity={"version": "fixture"},
                                       receipt_path=output / "processes" / "one" / "outcome.json")

            def assemble(*args, **kwargs):
                calls.append("presentation")
                if calls.count("presentation") == 1:
                    raise RuntimeError("controlled late presentation failure")
                return {"source_image_count": 44, "media_count": 24}

            arguments = ["build", "--workspace", str(workspace), "--character", "skeleton", "--height", "1.50"]
            with patch.object(api, "prepare", side_effect=prepare), \
                    patch.object(api, "render", side_effect=render), \
                    patch.object(matrix, "assemble_presentation", side_effect=assemble), \
                    patch.object(matrix, "validate_installed_api"), \
                    patch.object(matrix, "validate_output", return_value={"producer": "pass"}):
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(matrix.main(arguments), 2)
                self.assertFalse((root / "build.json").exists())
                self.assertFalse((root / "prepared").exists())
                self.assertFalse((root / "render").exists())
                self.assertFalse((root / "presentation").exists())
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(matrix.main(arguments), 0)
            self.assertEqual(calls, ["prepare", "render", "presentation"] * 2)
            logs = sorted((root / "logs").glob("build-*.log"))
            self.assertEqual(len(logs), 2)
            self.assertIn("controlled late presentation failure", logs[0].read_text(encoding="utf-8"))
            self.assertIn(f"cleanup_removed={root / 'prepared'}", logs[0].read_text(encoding="utf-8"))
            self.assertIn("cumulative_bytes=", logs[0].read_text(encoding="utf-8"))
            self.assertEqual(json.loads((root / "build.json").read_text())["status"], "success")

    def test_check_rejects_symlink_log_root_before_writing_outside_workspace(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            workspace = base / "workspace"
            outside = base / "outside"
            workspace.mkdir()
            outside.mkdir()
            root = matrix.element_root(workspace, "male", 1.70)
            root.mkdir(parents=True)
            (root / "logs").symlink_to(outside, target_is_directory=True)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(matrix.main(["check", "--workspace", str(workspace),
                                              "--character", "male", "--height", "1.70"]), 2)
            self.assertEqual(list(outside.iterdir()), [])
            self.assertFalse((root / "check.json").exists())

    def test_stale_installed_api_is_rejected_with_actionable_prerequisite_message(self):
        class StaleApi:
            @staticmethod
            def prepare(*, workspace, output, fixtures, bpms, stature):
                pass

            @staticmethod
            def render(*, prepared, workspace, output, images, characters, render_only):
                pass

        with self.assertRaisesRegex(matrix.MatrixError, "approved package in the offline environment"):
            matrix.validate_installed_api(StaleApi)

    def test_render_failure_preserves_backend_diagnostics_before_cleanup(self):
        from humanmotionlib import api

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            (workspace / "build").mkdir()
            root = matrix.element_root(workspace, "male", 1.70)
            stdout_bytes = b"backend started\n" + b"a" * (180 * 1024) + b"MIDDLE-STDOUT-MARKER" + b"b" * (180 * 1024)
            stderr_bytes = b"backend stderr prefix\n" + b"c" * (180 * 1024) + \
                b"ERROR: controlled backend failure detail in middle\n" + b"d" * (180 * 1024)

            def prepare(**kwargs):
                output = Path(kwargs["output"])
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text("{}", encoding="utf-8")
                return SimpleNamespace(prepared_path=output.resolve(), prepared_sha256="p" * 64,
                                       package_identity={"version": "fixture"})

            def render(_prepared, **kwargs):
                render_root = Path(kwargs["output"])
                slot = render_root / "processes" / "failed-pass"
                slot.mkdir(parents=True)
                receipt_path = slot / "outcome.json"
                stdout_path = slot / "stdout.log"
                stderr_path = slot / "stderr.log"
                stdout_path.write_bytes(stdout_bytes)
                stderr_path.write_bytes(stderr_bytes)
                receipt = {"operation": "render-pass", "outcome": "exit", "return_code": 1,
                           "signal": None, "last_script_phase": "rendering",
                           "stdout_log": str(stdout_path), "stderr_log": str(stderr_path),
                           "phases": [{"phase": "input_loaded"}],
                           "cleanup": {"status": "confirmed"}}
                receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
                raise api.GenerationError("backend-failed", "render", "render returned failure",
                    run_root=render_root, receipt_path=receipt_path,
                    details={"supervisor_outcome": receipt})

            args = ["build", "--workspace", str(workspace), "--character", "male", "--height", "1.70"]
            with patch.object(api, "prepare", side_effect=prepare), \
                    patch.object(api, "render", side_effect=render), \
                    patch.object(matrix, "validate_installed_api"), \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(matrix.main(args), 2)

            self.assertFalse((root / "render").exists())
            self.assertFalse((root / "build.json").exists())
            logs = [path for path in (root / "logs").glob("build-*.log")
                    if "-backend-" not in path.name]
            self.assertEqual(len(logs), 1)
            self.assertEqual(len(list((root / "logs").glob("*.log"))), 1)
            log = logs[0].read_text(encoding="utf-8")
            self.assertIn('backend_receipt_summary=', log)
            self.assertIn('"return_code": 1', log)
            self.assertIn('backend_diagnostic_streams=', log)
            diagnostic_line = next(line for line in log.splitlines()
                                    if line.startswith("backend_diagnostic_streams="))
            diagnostics = json.loads(diagnostic_line.split("=", 1)[1])
            for label, expected in (("stdout", stdout_bytes), ("stderr", stderr_bytes)):
                self.assertEqual(diagnostics[label]["bytes"], len(expected))
                self.assertTrue(diagnostics[label]["complete"])
                self.assertEqual(diagnostics[label]["encoding"], "utf-8-json-chunks")
            self.assertIn("MIDDLE-STDOUT-MARKER", log)
            self.assertIn("ERROR: controlled backend failure detail in middle", log)

    def test_render_diagnostic_paths_reject_traversal_foreign_and_symlink_inputs(self):
        import io
        from types import SimpleNamespace

        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            workspace = base / "workspace"
            external = base / "external"
            workspace.mkdir()
            external.mkdir()
            root = matrix.element_root(workspace, "male", 1.70)
            render = root / "render"
            logs = root / "logs"
            (render / "processes").mkdir(parents=True)
            logs.mkdir(parents=True)
            protected = external / "protected.log"
            protected.write_text("must remain external", encoding="utf-8")
            (render / "processes" / "linked.log").symlink_to(protected)
            receipt_path = render / "processes" / "outcome.json"
            receipt_path.write_text("{}", encoding="utf-8")
            bad_streams = {
                "traversal": str(render / "processes" / ".." / "protected.log"),
                "foreign": str(protected),
                "symlink": str(render / "processes" / "linked.log"),
            }
            for label, stream_path in bad_streams.items():
                receipt = {"operation": "render-pass", "outcome": "exit", "return_code": 1,
                           "stdout_log": stream_path}
                error = SimpleNamespace(details={"supervisor_outcome": receipt},
                                        receipt_path=receipt_path)
                output = io.StringIO()
                matrix.preserve_render_failure_diagnostics(output, error, root, workspace)
                self.assertIn('backend_diagnostic_streams=', output.getvalue())
            self.assertEqual(protected.read_text(encoding="utf-8"), "must remain external")

            outside_receipt = SimpleNamespace(details={"supervisor_outcome": {
                "operation": "render-pass", "outcome": "exit", "return_code": 1}},
                receipt_path=protected)
            output = io.StringIO()
            matrix.preserve_render_failure_diagnostics(
                output, outside_receipt, root, workspace)
            summary = next(line for line in output.getvalue().splitlines()
                           if line.startswith("backend_receipt_summary="))
            self.assertIn("receipt_path_error", summary)
            self.assertEqual(protected.read_text(encoding="utf-8"), "must remain external")

    def test_binary_backend_diagnostic_uses_lossless_base64_in_same_attempt_log(self):
        import base64
        import io
        from types import SimpleNamespace

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            (workspace / "build").mkdir()
            root = matrix.element_root(workspace, "male", 1.70)
            render = root / "render"
            slot = render / "processes" / "failed-pass"
            slot.mkdir(parents=True)
            source = slot / "stderr.log"
            expected = b"prefix\xff\x00middle-error\xfe suffix"
            source.write_bytes(expected)
            receipt = {"operation": "render-pass", "outcome": "exit", "return_code": 1,
                       "stderr_log": str(source)}
            receipt_path = slot / "outcome.json"
            receipt_path.write_text("{}", encoding="utf-8")
            error = SimpleNamespace(details={"supervisor_outcome": receipt}, receipt_path=receipt_path)
            output = io.StringIO()
            matrix.preserve_render_failure_diagnostics(output, error, root, workspace)
            lines = output.getvalue().splitlines()
            chunks = [line.split(" ", 2)[2] for line in lines
                      if line.startswith("backend_stream_base64 label=stderr ")]
            self.assertTrue(chunks)
            self.assertEqual(base64.b64decode("".join(chunks)), expected)
            self.assertIn('"encoding": "base64"', next(line for line in lines
                         if line.startswith("backend_diagnostic_streams=")))

    def test_build_preflight_failure_invalidates_current_result_and_cleans_outputs(self):
        import humanmotionlib.api as api

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            root = matrix.element_root(workspace, "male", 1.70)
            (root / "logs").mkdir(parents=True)
            (root / "prepared").mkdir()
            (root / "prepared" / "input.json").write_text("old prepared data", encoding="utf-8")
            (root / "render").mkdir()
            (root / "render" / "render-manifest.json").write_text("old manifest", encoding="utf-8")
            (root / "presentation").mkdir()
            (root / "unrelated.txt").write_text("preserve", encoding="utf-8")
            (root / "build.json").write_text('{"status":"success"}', encoding="utf-8")
            (root / "check.json").write_text('{"status":"success"}', encoding="utf-8")
            with patch.object(matrix, "validate_installed_api",
                              side_effect=matrix.MatrixError("installed API preflight failed")), \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(matrix.main(["build", "--workspace", str(workspace),
                                              "--character", "male", "--height", "1.70"]), 2)
            self.assertFalse((root / "build.json").exists())
            self.assertFalse((root / "check.json").exists())
            self.assertFalse((root / "prepared").exists())
            self.assertFalse((root / "render").exists())
            self.assertFalse((root / "presentation").exists())
            self.assertEqual((root / "unrelated.txt").read_text(encoding="utf-8"), "preserve")
            log = next((root / "logs").glob("build-*.log")).read_text(encoding="utf-8")
            self.assertIn("installed API preflight failed", log)
            self.assertIn("cleanup_removed=", log)

    def test_cleanup_refusal_still_invalidates_old_success_and_preserves_external_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            workspace = base / "workspace"
            external = base / "protected"
            workspace.mkdir()
            external.mkdir()
            sentinel = external / "sentinel.txt"
            sentinel.write_text("protected", encoding="utf-8")
            root = matrix.element_root(workspace, "male", 1.70)
            (root / "logs").mkdir(parents=True)
            (root / "prepared").mkdir()
            (root / "prepared" / "external-link").symlink_to(external, target_is_directory=True)
            (root / "build.json").write_text('{"status":"success"}', encoding="utf-8")
            (root / "check.json").write_text('{"status":"success"}', encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(matrix.main(["build", "--workspace", str(workspace),
                                              "--character", "male", "--height", "1.70"]), 2)
            self.assertFalse((root / "build.json").exists())
            self.assertFalse((root / "check.json").exists())
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "protected")
            log = next((root / "logs").glob("build-*.log")).read_text(encoding="utf-8")
            self.assertIn("external-link", log)
            self.assertIn("cleanup_incomplete=", log)

    def test_check_rejects_forged_external_marker_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            workspace = base / "workspace"
            foreign = base / "foreign"
            workspace.mkdir()
            foreign.mkdir()
            protected = foreign / "protected.json"
            protected.write_text('{"untouched":true}', encoding="utf-8")
            root = matrix.element_root(workspace, "male", 1.70)
            root.mkdir(parents=True)
            (root / "build.json").write_text(json.dumps({
                "schema": "matrix-current-build/v1", "status": "success",
                "character": "male", "height_m": 1.7, "fixtures": list(matrix.FIXTURES),
                "bpm": 120, "package_identity": matrix.installed_package_identity(),
                "prepared": str(protected), "render_root": str(foreign),
                "render_manifest": str(protected), "render_receipt": str(protected),
                "presentation": str(foreign), "presentation_inventory": str(protected),
            }), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(matrix.main(["check", "--workspace", str(workspace),
                                              "--character", "male", "--height", "1.70"]), 1)
            result = json.loads((root / "check.json").read_text(encoding="utf-8"))
            self.assertIn("path does not match", result["checks"]["error"])
            self.assertEqual(protected.read_text(encoding="utf-8"), '{"untouched":true}')

    def test_current_output_validation_rejects_unlisted_png_member(self):
        from PIL import Image
        import matrix_presentation

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            root = matrix.element_root(workspace, "male", 1.70)
            prepared_path = root / "prepared" / "input.json"
            render = root / "render"
            frames = render / "frames"
            presentation = root / "presentation"
            frames.mkdir(parents=True)
            presentation.mkdir()
            (presentation / "presentation-inventory.json").write_text(
                json.dumps({"media": []}), encoding="utf-8")
            receipt = render / "processes" / "one" / "outcome.json"
            receipt.parent.mkdir(parents=True)
            receipt.write_text(json.dumps({"operation": "render-pass"}), encoding="utf-8")
            rows = []
            tile = Image.new("RGB", (1024, 1024), (20, 30, 40))
            for index in range(32):
                relative = f"source-{index:02d}.png"
                tile.save(frames / relative)
                rows.append({"path": relative})
            build = {"prepared": str(prepared_path), "render_root": str(render),
                     "render_manifest": str(render / "render-manifest.json"),
                     "render_receipt": str(receipt), "presentation": str(presentation),
                     "presentation_inventory": str(presentation / "presentation-inventory.json")}
            prepared = {"sources": {"profile": {"stature_m": 1.7}},
                        "sampling": {fixture: [{"bpm": 120}] for fixture in matrix.FIXTURES}}
            with patch.object(matrix_presentation, "_validate_producer",
                              return_value=(prepared, {}, render, frames, rows)), \
                    patch.object(matrix, "_validate_matrix_sampling"), \
                    patch.object(matrix, "validate_presentation_inventory", return_value={"status": "pass"}):
                self.assertEqual(matrix.validate_output(workspace, root, "male", 1.70, build)["producer"], "pass")
                (frames / "unexpected.png").write_bytes((frames / "source-00.png").read_bytes())
                with self.assertRaisesRegex(matrix.MatrixError, "do not exactly match"):
                    matrix.validate_output(workspace, root, "male", 1.70, build)


if __name__ == "__main__":
    unittest.main()
