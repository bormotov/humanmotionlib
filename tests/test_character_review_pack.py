# SPDX-License-Identifier: Apache-2.0
"""Host contracts for complete character review-pack joins and coverage."""

from __future__ import annotations

import tempfile
import unittest
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from contextlib import redirect_stdout
from io import StringIO
import tempfile
from unittest import mock

from PIL import Image
import yaml

import humanmotionlib
from humanmotionlib import api

_SOURCE_MODULE = Path(__file__).resolve().parents[1] / "src" / "humanmotionlib" / "review_pack.py"
humanmotionlib.__path__ = [str(_SOURCE_MODULE.parent)]
_SPEC = importlib.util.spec_from_file_location("humanmotionlib.review_pack", _SOURCE_MODULE)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"Could not load source review-pack module: {_SOURCE_MODULE}")
_REVIEW_PACK = importlib.util.module_from_spec(_SPEC)
sys.modules["humanmotionlib.review_pack"] = _REVIEW_PACK
_SPEC.loader.exec_module(_REVIEW_PACK)

_character_grid = _REVIEW_PACK._character_grid
_character_images = _REVIEW_PACK._character_images
_character_plan_coverage = _REVIEW_PACK._character_plan_coverage
_character_sample_rows = _REVIEW_PACK._character_sample_rows
_baseline_sample_matches = _REVIEW_PACK._baseline_sample_matches
_optional_baseline_sample_matches = _REVIEW_PACK._optional_baseline_sample_matches
_sample_records_for_plan = _REVIEW_PACK._sample_records_for_plan
_stature_strip = _REVIEW_PACK._stature_strip
_JOINT_CENTER_IDS = _REVIEW_PACK._JOINT_CENTER_IDS
_sole_crop = _REVIEW_PACK._sole_crop
_baseline_report_record = _REVIEW_PACK._baseline_report_record
_current_mode_comparison_status = _REVIEW_PACK._current_mode_comparison_status
_complete_character_pack_status = _REVIEW_PACK._complete_character_pack_status
_preflight_skeleton_baseline = _REVIEW_PACK._preflight_skeleton_baseline
_preflight_current_candidate = _REVIEW_PACK._preflight_current_candidate
_stature_comparison_inputs = _REVIEW_PACK._stature_comparison_inputs
_parse_diagonal_inputs = _REVIEW_PACK._parse_diagonal_inputs
_diagonal_pack_status = _REVIEW_PACK._diagonal_pack_status

class CharacterReviewPackTests(unittest.TestCase):
    def test_diagonal_main_reaches_nested_private_api_claim_without_blender(self):
        from humanmotionlib.prepare_skeleton import prepare
        from humanmotionlib.prepared import write_json

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            build = workspace / "build"
            build.mkdir()
            input_root = build / "add-shared-body-characters_r13_test_try-1_input"
            input_root.mkdir()
            prepared = prepare("adult-reference-v1", 1.50, fixtures=["neutral"])
            write_json(input_root / "input.json", prepared)
            output = build / "add-shared-body-characters_r13_test_try-1_main"
            observed = []

            def stop_before_child(_prepared, pass_root, **kwargs):
                observed.append((Path(pass_root), kwargs))
                raise KeyboardInterrupt

            argv = ["review-pack", "--acceptance-scope", "diagonal-v1",
                    "--input", str(input_root),
                    "--diagonal-input", f"skeleton={input_root}",
                    "--diagonal-input", f"male={input_root}",
                    "--diagonal-input", f"female={input_root}",
                    "--output", str(output)]
            with (mock.patch.object(sys, "argv", argv),
                  mock.patch.object(_REVIEW_PACK, "_preflight_diagonal_inputs",
                                    return_value=({"skeleton": prepared}, {"skeleton": input_root}, {"test": True})),
                  mock.patch.object(api.run_blender, "run", side_effect=stop_before_child)):
                with self.assertRaises(KeyboardInterrupt):
                    _REVIEW_PACK.main(workspace=workspace)

            self.assertEqual(len(observed), 1)
            pass_root, kwargs = observed[0]
            expected_pass = output / "pair-skeleton" / "clean-a"
            self.assertEqual(pass_root, expected_pass)
            self.assertEqual(Path(kwargs["owner_run"]), output)
            claim = kwargs["managed_claim"]
            self.assertEqual(Path(claim.owner_run), output)
            self.assertEqual(Path(claim.pass_root), expected_pass)
            request = json.loads(Path(kwargs["character_request"]).read_text())
            self.assertEqual(request["render_identity"], claim.render_identity)
            self.assertEqual(request["prepared_sha256"], prepared["content_sha256"])

    def test_diagonal_cli_rejects_overlapping_input_and_output_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            build = workspace / "build"
            build.mkdir()
            run = build / "add-shared-body-characters_r9_test_try-1_input"
            run.mkdir()
            argv = ["review-pack", "--acceptance-scope", "diagonal-v1",
                    "--input", str(run),
                    "--diagonal-input", f"skeleton={run}",
                    "--diagonal-input", f"male={run}",
                    "--diagonal-input", f"female={run}",
                    "--output", str(run)]
            with mock.patch.object(sys, "argv", argv):
                with self.assertRaisesRegex(ValueError, "input and output roots must be disjoint"):
                    _REVIEW_PACK.main(workspace=workspace)
            self.assertEqual(list(run.iterdir()), [])

    def test_diagonal_cli_rejects_explicit_characters_even_when_skeleton_default(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            build = workspace / "build"
            build.mkdir()
            run = build / "add-shared-body-characters_r9_test_try-1_input"
            run.mkdir()
            output = build / "add-shared-body-characters_r9_test_try-1_pack"
            argv = ["review-pack", "--acceptance-scope", "diagonal-v1",
                    "--input", str(run), "--characters", "skeleton",
                    "--diagonal-input", f"skeleton={run}",
                    "--diagonal-input", f"male={run}",
                    "--diagonal-input", f"female={run}",
                    "--output", str(output)]
            with mock.patch.object(sys, "argv", argv), \
                 mock.patch.object(_REVIEW_PACK, "verify_runtime_integrity"):
                with self.assertRaises(SystemExit) as error:
                    _REVIEW_PACK.main(workspace=workspace)
            self.assertEqual(error.exception.code, 2)
            self.assertFalse(output.exists())

    def test_html_only_explicit_skeleton_selection_keeps_ordinary_mode_behavior(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            build = workspace / "build"
            build.mkdir()
            predecessor = build / "add-shared-body-characters_r9_test_try-1_predecessor"
            predecessor.mkdir()
            output = build / "add-shared-body-characters_r9_test_try-1_html"
            argv = ["review-pack", "--html-only-from", str(predecessor),
                    "--characters", "skeleton", "--output", str(output)]
            with mock.patch.object(sys, "argv", argv), \
                 mock.patch.object(_REVIEW_PACK, "verify_runtime_integrity"), \
                 mock.patch("humanmotionlib.presentation.regenerate_html",
                            return_value={"status": "pass"}):
                with redirect_stdout(StringIO()):
                    status = _REVIEW_PACK.main(workspace=workspace)
            self.assertEqual(status, 0)

    def test_diagonal_cli_assembles_positive_review_without_blender(self):
        from humanmotionlib.prepare_skeleton import prepare
        from humanmotionlib.prepared import write_json

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            build = workspace / "build"
            build.mkdir()
            heights = {"skeleton": 1.50, "male": 1.70, "female": 1.90}
            records, runs = {}, {}
            for identifier, height in heights.items():
                run = build / f"add-shared-body-characters_r9_test_try-{int(height * 100)}_input"
                run.mkdir()
                prepared = prepare("adult-reference-v1", height, fixtures=["neutral", "squat"])
                write_json(run / "input.json", prepared)
                records[identifier], runs[identifier] = prepared, run
            output = build / "add-shared-body-characters_r9_test_try-1_pack"

            managed_calls = []
            def fake_invocation(command, *, expected_outputs, **kwargs):
                from humanmotionlib.package_resources import manifest_sha256, verify_runtime_integrity
                from humanmotionlib.prepared import read_prepared
                from humanmotionlib.runtime import validate_outputs

                output_root = Path(kwargs["run_root"])
                input_path = Path(command[command.index("--input") + 1])
                prepared = read_prepared(input_path)
                request_path = next(Path(item["path"] if isinstance(item, dict) else item)
                                    for item in expected_outputs
                                    if Path(item["path"] if isinstance(item, dict) else item).name
                                    == "character-render-request.json")
                request = json.loads(request_path.read_text())
                character_ids = request["character_ids"]
                render_identity = request["render_identity"]
                for item in expected_outputs:
                    path = Path(item["path"] if isinstance(item, dict) else item)
                    if path == output_root / "input.json":
                        path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(input_path, path)
                    elif path.name == "build-metadata.json":
                        path.write_text(json.dumps({"blender_version": "5.2.2 LTS",
                                                    "blender_build": "fixture-build",
                                                    "render_identity": render_identity}))
                    elif path.name == "skeleton.blend":
                        path.write_bytes(b"synthetic scene")
                    elif path.suffix == ".png":
                        path.parent.mkdir(parents=True, exist_ok=True)
                        Image.new("RGB", (64, 64), (40, 80, 120)).save(path)
                frames = output_root / "frames"
                image_paths = [Path(item["path"] if isinstance(item, dict) else item)
                               for item in expected_outputs
                               if Path(item["path"] if isinstance(item, dict) else item).suffix == ".png"]
                manifest = {"prepared_sha256": prepared["content_sha256"],
                            "render_identity": render_identity}
                if character_ids == ["skeleton"]:
                    manifest["samples"] = []
                    for sample in prepared["samples"]:
                        images = {path.relative_to(frames).parts[1]: path.relative_to(frames).as_posix()
                                  for path in image_paths
                                  if path.relative_to(frames).parts[0] == sample["fixture"]
                                  and path.name == f"{sample['frame_id']:05d}.png"}
                        manifest["samples"].append({"id": sample["id"], "images": images})
                else:
                    manifest["format"] = "character-render-manifest/v1"
                    manifest["characters"] = []
                    for identifier in character_ids:
                        sample_rows = []
                        for sample in prepared["samples"]:
                            images = {path.relative_to(frames).parts[2]: path.relative_to(frames).as_posix()
                                      for path in image_paths
                                      if path.relative_to(frames).parts[0] == identifier
                                      and path.relative_to(frames).parts[1] == sample["fixture"]
                                      and path.name == f"{sample['frame_id']:05d}.png"}
                            sample_rows.append({"id": sample["id"], "images": images})
                        manifest["characters"].append({"id": identifier, "samples": sample_rows})
                (output_root / "render-manifest.json").write_text(json.dumps(manifest))
                process_root = output_root / "processes" / "synthetic"
                process_root.mkdir(parents=True, exist_ok=True)
                stdout_log = process_root / "stdout.log"
                stdout_log.write_text("synthetic supervised backend\n")
                identity = verify_runtime_integrity()
                output_validation = validate_outputs(expected_outputs)
                self.assertEqual(output_validation["status"], "pass", output_validation)
                receipt = {
                    "format": "backend-invocation/v1", "state": "succeeded",
                    "operation": "render-pass", "outcome": "exit", "return_code": 0,
                    "stdout_log": str(stdout_log), "source_sha256": prepared["content_sha256"],
                    "package_version": identity["version"],
                    "runtime_manifest_sha256": manifest_sha256(),
                    "resource_hashes": identity["resources"],
                    "backend_contract_sha256": identity["backend_contract"],
                    "implementation_hashes": identity["implementation"],
                    "last_script_phase": "script_complete",
                    "phases": [
                        {"phase": "input_loaded", "prepared_sha256": prepared["content_sha256"]},
                        {"phase": "script_complete", "prepared_sha256": prepared["content_sha256"],
                         "render_identity": render_identity, "character_ids": character_ids},
                    ],
                    "output_validation": output_validation,
                }
                managed_calls.append((Path(kwargs["owner_run"]), request["character_ids"][0],
                                      output_root, request))
                return receipt

            def fake_probe(_output, **_kwargs):
                return {"receipt": {"executable": "/synthetic/blender"},
                        "version": "5.2.2 LTS", "build_hash": "fixture-build"}

            argv = ["review-pack", "--acceptance-scope", "diagonal-v1",
                    "--input", str(runs["skeleton"]),
                    "--diagonal-input", f"skeleton={runs['skeleton']}",
                    "--diagonal-input", f"male={runs['male']}",
                    "--diagonal-input", f"female={runs['female']}",
                    "--output", str(output)]
            with (mock.patch.object(sys, "argv", argv),
                  mock.patch.object(_REVIEW_PACK, "_preflight_diagonal_inputs",
                                    return_value=(records, runs, {"backend_identity": {},
                                        "render_identities": {}})),
                  mock.patch.object(api.run_blender, "inspect_blender", side_effect=fake_probe),
                  mock.patch.object(api.run_blender, "invocation", side_effect=fake_invocation),
                  mock.patch.object(_REVIEW_PACK, "assemble_character_pack", side_effect=lambda *args, **kwargs: {
                      "coverage": {"status": "pass"}, "repeatability": "pass", "gif_status": "pass"})):
                with redirect_stdout(StringIO()):
                    status = _REVIEW_PACK.main(workspace=workspace)
            report = json.loads((output / "diagonal-review.json").read_text())
            self.assertEqual(status, 0)
            self.assertEqual(report["status"], "pass")
            self.assertFalse(report.get("matrix_complete", False))
            self.assertEqual(len(report["observed_pairs"]), 3)
            self.assertEqual(len(report["unassessed_pairs"]), 6)
            self.assertEqual(len(managed_calls), 8)
            expected_routes = {
                (f"pair-{identifier}", name, identifier)
                for identifier in ("skeleton", "male", "female")
                for name in ("clean-a", "clean-b")
            } | {
                ("skeleton-mode-check", "skeleton-default", "skeleton"),
                ("skeleton-mode-check", "skeleton-explicit", "skeleton"),
            }
            self.assertEqual({(output_root.parent.relative_to(output.resolve()).as_posix(),
                               output_root.name, character)
                              for owner, character, output_root, _request in managed_calls}, expected_routes)
            self.assertTrue(all(owner == output.resolve()
                                for owner, _character, _output_root, _request in managed_calls))
            self.assertTrue((output / "diagonal-overview.png").is_file())
            self.assertTrue((output / "index.html").is_file())

    def test_diagonal_input_parser_requires_exact_unique_approved_pairs(self):
        parsed = _parse_diagonal_inputs([
            "female=/tmp/f", "skeleton=/tmp/s", "male=/tmp/m"])
        self.assertEqual({key for key, _ in parsed}, {"skeleton", "male", "female"})
        for invalid in (
                ["skeleton=/tmp/s", "male=/tmp/m"],
                ["skeleton=/tmp/s", "male=/tmp/m", "female=/tmp/f", "male=/tmp/other"],
                ["skeleton=/tmp/s", "male=/tmp/m", "unknown=/tmp/f"],
                ["skeleton=/tmp/s", "male=/tmp/m", "female="]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                _parse_diagonal_inputs(invalid)

    def test_diagonal_pack_requires_all_pair_media_and_skeleton_mode_control(self):
        reports = {key: {"coverage": {"status": "pass"},
                         "repeatability": "pass", "gif_status": "pass"}
                   for key in ("skeleton", "male", "female")}
        self.assertEqual(_diagonal_pack_status(reports, "pass"), "pass")
        self.assertEqual(_diagonal_pack_status(reports, "incomplete"), "incomplete")
        self.assertEqual(_diagonal_pack_status({"skeleton": reports["skeleton"]}, "pass"),
                         "incomplete")
        reports["female"]["repeatability"] = "fail"
        self.assertEqual(_diagonal_pack_status(reports, "pass"), "fail")

    def test_diagonal_source_preflight_positive_and_integrity_negative_cases(self):
        from humanmotionlib.prepare_skeleton import prepare
        from humanmotionlib.prepared import seal, write_json
        from humanmotionlib.runtime import backend_contract
        from humanmotionlib.character_verification import (
            _FOCUSED_VISUAL_FIXTURES, _focused_visual_sample_coverage)

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            build = workspace / "build"
            build.mkdir()
            output = build / "add-shared-body-characters_r9_test_try-1_pack"
            heights = {"skeleton": 1.50, "male": 1.70, "female": 1.90}
            runs = {}
            prepared_records = {}
            reject_invalid_focus = False
            observed_focus_statuses = []
            contract = backend_contract()
            for identifier, height in heights.items():
                run = build / f"add-shared-body-characters_r9_test_{identifier}-preflight_input"
                run.mkdir()
                prepared = prepare("adult-reference-v1", height,
                                   fixtures=_FOCUSED_VISUAL_FIXTURES, bpms=(90,))
                write_json(run / "input.json", prepared)
                render_identity = "render-" + identifier
                write_json(run / "character-render-request.json", {"render_identity": render_identity})
                write_json(run / "build-metadata.json", {
                    "blender_version": contract["blender-version"],
                    "blender_build": contract["blender-build"]})
                write_json(run / "evaluated.json", {
                    "content_sha256": prepared["content_sha256"],
                    "prepared_sha256": prepared["content_sha256"],
                    "package_identity": prepared["package_identity"],
                    "source_hashes": prepared["source_hashes"],
                    "sampling": prepared["sampling"],
                    "render_identity": render_identity,
                    "backend_identity": {"version": contract["blender-version"],
                                         "build_hash": contract["blender-build"]},
                    "samples": [{"id": sample["id"]} for sample in prepared["samples"]]})
                runs[identifier] = run
                prepared_records[identifier] = prepared

            specs = [(identifier, runs[identifier]) for identifier in heights]

            def verify_numeric(prepared, run, _ids, **_kwargs):
                request = json.loads((run / "character-render-request.json").read_text())
                identifier = _kwargs["selected_character_id"]
                self.assertTrue(_kwargs["_focused_visual"])
                focus_status = _focused_visual_sample_coverage(prepared)["status"]
                observed_focus_statuses.append(focus_status)
                na = "not-applicable-skeleton" if identifier == "skeleton" else "pass"
                status = "fail" if reject_invalid_focus and focus_status != "pass" else "pass"
                return {"numeric_status": status, "render_identity": request["render_identity"],
                        "verification_scope": "focused-visual",
                        "checked_character_ids": [identifier],
                        "native_midpoints": {"status": na}, "dense": {"status": na}}

            with mock.patch.object(_REVIEW_PACK, "verify_runtime_integrity"), \
                 mock.patch.object(_REVIEW_PACK, "_character_plan_coverage",
                                   return_value={"status": "pass", "coverage": {}, "missing": []}), \
                 mock.patch("humanmotionlib.character_verification.verify_character_output",
                            side_effect=verify_numeric):
                records, resolved, identities = _REVIEW_PACK._preflight_diagonal_inputs(
                    runs["skeleton"], prepared_records["skeleton"], specs, output, workspace)
                self.assertEqual(set(records), set(heights))
                self.assertEqual(set(resolved), set(heights))
                self.assertEqual(set(identities["render_identities"]), set(heights))
                self.assertEqual(set(identities["numeric_verification"]), set(heights))
                self.assertEqual({row["verification_scope"]
                                  for row in identities["numeric_verification"].values()},
                                 {"focused-visual"})
                self.assertEqual(observed_focus_statuses[-3:], ["pass", "pass", "pass"])

                with self.subTest("unobserved extra sampling fixture is rejected before pack output"):
                    mutated = json.loads(json.dumps(prepared_records["female"]))
                    mutated["sampling"]["extra-fixture"] = [{"bpm": 120}]
                    mutated = seal(mutated)
                    write_json(runs["female"] / "input.json", mutated)
                    evaluated_path = runs["female"] / "evaluated.json"
                    evaluated = json.loads(evaluated_path.read_text())
                    evaluated["prepared_sha256"] = mutated["content_sha256"]
                    evaluated["content_sha256"] = mutated["content_sha256"]
                    evaluated["sampling"] = mutated["sampling"]
                    write_json(evaluated_path, evaluated)
                    reject_invalid_focus = True
                    with self.assertRaisesRegex(ValueError, "no passing selected numeric evidence"):
                        _REVIEW_PACK._preflight_diagonal_inputs(
                            runs["skeleton"], prepared_records["skeleton"], specs, output, workspace)
                    reject_invalid_focus = False
                    self.assertFalse(output.exists())
                    self.assertEqual(observed_focus_statuses[-1], "fail")
                    write_json(runs["female"] / "input.json", prepared_records["female"])
                    evaluated["prepared_sha256"] = prepared_records["female"]["content_sha256"]
                    evaluated["content_sha256"] = prepared_records["female"]["content_sha256"]
                    evaluated["sampling"] = prepared_records["female"]["sampling"]
                    write_json(evaluated_path, evaluated)

                with self.subTest("wrong skeleton operand"):
                    wrong_specs = [(key, runs["male"] if key == "skeleton" else run)
                                   for key, run in specs]
                    with self.assertRaisesRegex(ValueError, "same H=1.50m run"):
                        _REVIEW_PACK._preflight_diagonal_inputs(
                            runs["skeleton"], prepared_records["skeleton"],
                            wrong_specs, output, workspace)

                with self.subTest("wrong height"):
                    wrong_run = build / "add-shared-body-characters_r9_test_wrong-height_input"
                    wrong_run.mkdir()
                    write_json(wrong_run / "input.json",
                               prepare("adult-reference-v1", 1.80, fixtures=["neutral", "rest"]))
                    wrong_specs = [(key, wrong_run if key == "female" else run)
                                   for key, run in specs]
                    with self.assertRaisesRegex(ValueError, "female input must be H=1.90"):
                        _REVIEW_PACK._preflight_diagonal_inputs(
                            runs["skeleton"], prepared_records["skeleton"],
                            wrong_specs, output, workspace)

                with self.subTest("stale evaluated identity"):
                    evaluated_path = runs["female"] / "evaluated.json"
                    evaluated = json.loads(evaluated_path.read_text())
                    evaluated["prepared_sha256"] = "stale-prepared-identity"
                    write_json(evaluated_path, evaluated)
                    with self.assertRaisesRegex(ValueError, "stale"):
                        _REVIEW_PACK._preflight_diagonal_inputs(
                            runs["skeleton"], prepared_records["skeleton"],
                            specs, output, workspace)
                    evaluated["prepared_sha256"] = prepared_records["female"]["content_sha256"]
                    write_json(evaluated_path, evaluated)

                with self.subTest("source definition mismatch"):
                    mutated = json.loads(json.dumps(prepared_records["female"]))
                    mutated["sources"]["review-scene"]["cameras"][0]["position_m"][0] += 0.001
                    mutated = seal(mutated)
                    write_json(runs["female"] / "input.json", mutated)
                    evaluated_path = runs["female"] / "evaluated.json"
                    evaluated = json.loads(evaluated_path.read_text())
                    evaluated["prepared_sha256"] = mutated["content_sha256"]
                    evaluated["content_sha256"] = mutated["content_sha256"]
                    evaluated["samples"] = [{"id": sample["id"]} for sample in mutated["samples"]]
                    write_json(evaluated_path, evaluated)
                    with self.assertRaisesRegex(ValueError, "canonical definition mismatch"):
                        _REVIEW_PACK._preflight_diagonal_inputs(
                            runs["skeleton"], prepared_records["skeleton"],
                            specs, output, workspace)
                    original = prepared_records["female"]
                    write_json(runs["female"] / "input.json", original)
                    evaluated["prepared_sha256"] = original["content_sha256"]
                    evaluated["content_sha256"] = original["content_sha256"]
                    evaluated["samples"] = [{"id": sample["id"]} for sample in original["samples"]]
                    write_json(evaluated_path, evaluated)

                with self.subTest("source hash mismatch"):
                    mutated = json.loads(json.dumps(prepared_records["female"]))
                    first_source = next(iter(mutated["source_hashes"]))
                    mutated["source_hashes"][first_source] = "0" * 64
                    mutated = seal(mutated)
                    write_json(runs["female"] / "input.json", mutated)
                    with self.assertRaisesRegex(ValueError, "Source/schema hash mismatch"):
                        _REVIEW_PACK._preflight_diagonal_inputs(
                            runs["skeleton"], prepared_records["skeleton"],
                            specs, output, workspace)

                with self.subTest("package identity mismatch"):
                    mutated = json.loads(json.dumps(prepared_records["female"]))
                    mutated["package_identity"]["version"] = "stale-candidate"
                    mutated = seal(mutated)
                    write_json(runs["female"] / "input.json", mutated)
                    with self.assertRaisesRegex(ValueError, "package release/resource identity mismatch"):
                        _REVIEW_PACK._preflight_diagonal_inputs(
                            runs["skeleton"], prepared_records["skeleton"],
                            specs, output, workspace)
                    write_json(runs["female"] / "input.json", prepared_records["female"])

                with self.subTest("failed native numeric leaf"):
                    with mock.patch("humanmotionlib.character_verification.verify_character_output",
                                    return_value={"numeric_status": "fail"}):
                        with self.assertRaisesRegex(ValueError, "no passing selected numeric evidence"):
                            _REVIEW_PACK._preflight_diagonal_inputs(
                                runs["skeleton"], prepared_records["skeleton"],
                                specs, output, workspace)

                with self.subTest("sampling identity mismatch"):
                    mutated = dict(prepared_records["female"])
                    mutated["sampling"] = dict(mutated["sampling"])
                    mutated["sampling"]["unapproved-extra"] = []
                    mutated = seal(mutated)
                    write_json(runs["female"] / "input.json", mutated)
                    evaluated_path = runs["female"] / "evaluated.json"
                    evaluated = json.loads(evaluated_path.read_text())
                    evaluated["prepared_sha256"] = mutated["content_sha256"]
                    evaluated["content_sha256"] = mutated["content_sha256"]
                    evaluated["sampling"] = mutated["sampling"]
                    evaluated["samples"] = [{"id": sample["id"]} for sample in mutated["samples"]]
                    write_json(evaluated_path, evaluated)
                    with self.assertRaisesRegex(ValueError, "diagnostic sampling coverage differs"):
                        _REVIEW_PACK._preflight_diagonal_inputs(
                            runs["skeleton"], prepared_records["skeleton"],
                            specs, output, workspace)
                with self.subTest("backend mismatch"):
                    metadata = json.loads((runs["female"] / "build-metadata.json").read_text())
                    metadata["blender_build"] = "stale-build"
                    write_json(runs["female"] / "build-metadata.json", metadata)
                    with self.assertRaisesRegex(ValueError, "Blender version mismatch"):
                        _REVIEW_PACK._preflight_diagonal_inputs(
                            runs["skeleton"], prepared_records["skeleton"],
                            specs, output, workspace)
            self.assertFalse(output.exists())

    def _assemble_minimal_current_pack(self, root: Path, *, stature_inputs, omit_mode=None,
                                       differing_mode=None, with_partial_baseline=False):
        identifiers = ("skeleton", "male", "female")
        samples = [
            {"id": "neutral-0", "fixture": "neutral", "beat": {"numerator": 0, "denominator": 1},
             "frames": {}, "contacts": []},
            {"id": "raise-0", "fixture": "arm-raise", "beat": {"numerator": 0, "denominator": 1},
             "frames": {}, "contacts": []},
            {"id": "raise-1", "fixture": "arm-raise", "beat": {"numerator": 1, "denominator": 1},
             "frames": {}, "contacts": []},
        ]
        cameras = [{"id": view, "position_m": [0, 0, 2], "look_at_m": [0, 0, 0],
                    "up": [0, 1, 0], "orthographic_scale_m": 2}
                   for view in ("front", "side")]
        prepared = {"content_sha256": "prepared", "samples": samples, "package_identity": "pkg",
                    "source_hashes": {}, "sampling": {
                        "neutral": [], "arm-raise": [{"bpm": 90, "intervals_per_beat": 3,
                            "static": [{"sample_id": "raise-0", "beat": {"numerator": 0, "denominator": 1}}],
                            "animation": [
                                {"sample_id": "raise-0", "beat": {"numerator": 0, "denominator": 1}},
                                {"sample_id": "raise-1", "beat": {"numerator": 1, "denominator": 1}}]}]},
                    "sources": {"profile": {"stature_m": 1.70, "structures": []},
                                "review-scene": {"cameras": cameras},
                                "diagnostics": [{"id": "neutral", "description": "Neutral"},
                                                {"id": "arm-raise", "description": "Arm raise"}]}}
        root.mkdir(parents=True, exist_ok=True)
        batch_images = {identifier: {} for identifier in identifiers}
        for identifier in identifiers:
            for sample in samples:
                batch_images[identifier][sample["id"]] = {}
                views = ("front", "side", "rear") if sample["fixture"] == "neutral" else ("front", "side")
                for view in views:
                    path = root / "clean-a" / "frames" / identifier / sample["id"] / f"{view}.png"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    Image.new("RGB", (8, 8), (40, 80, 120)).save(path)
                    batch_images[identifier][sample["id"]][view] = path
        pass_images = {}
        comparison_passes = {}
        for name, identifier in _REVIEW_PACK._CURRENT_MODE_COMPARISONS.items():
            if name == omit_mode:
                continue
            view_map = {identifier: {}}
            pass_root = root / name
            for sample in samples:
                view_map[identifier][sample["id"]] = {}
                for view in batch_images[identifier][sample["id"]]:
                    path = pass_root / "frames" / identifier / sample["id"] / f"{view}.png"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    color = (200, 10, 10) if name == differing_mode else (40, 80, 120)
                    Image.new("RGB", (8, 8), color).save(path)
                    view_map[identifier][sample["id"]][view] = path
            pass_images[name] = view_map
            comparison_passes[name] = ({"_test_name": name}, pass_root)
        baseline = None
        if with_partial_baseline:
            baseline_sample = "historical-neutral-0"
            historical_images = {"skeleton": {baseline_sample: {}}}
            for view in ("front", "side"):
                path = root / "historical-baseline" / "frames" / baseline_sample / f"{view}.png"
                path.parent.mkdir(parents=True, exist_ok=True)
                Image.new("RGB", (8, 8), (220, 20, 20)).save(path)
                historical_images["skeleton"][baseline_sample][view] = path
            pass_images["historical"] = historical_images
            historical_match = {"fixture": "neutral", "beat": {"numerator": 0, "denominator": 1},
                                "baseline_sample_id": baseline_sample,
                                "candidate_sample_id": "neutral-0",
                                "required_views": ["front", "side", "rear"],
                                "available_views": ["front", "side"]}
            baseline = {"status": "pass", "comparison_status": "incomplete",
                        "comparison": {"status": "incomplete", "missing_candidate_samples": [
                            {"fixture": "arm-raise", "sample_id": "historical-samples-absent"}],
                            "missing_views": [{"sample_id": baseline_sample, "views": ["rear"]}],
                            "geometry": {"status": "incomplete", "samples": []}},
                        "manifest": {"_test_name": "historical"},
                        "run_root": root / "historical-baseline",
                        "prepared": {"samples": []}, "common_sample_matches": [historical_match]}
        request_path = root / "clean-a" / "character-render-request.json"
        request_path.parent.mkdir(parents=True, exist_ok=True)
        request_path.write_text(json.dumps({"render_identity": "render",
            "character_descriptors": [{"id": identifier} for identifier in identifiers]}))

        def save_grid(_images, _records, _view, output, **_kwargs):
            output.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (8, 8), (1, 2, 3)).save(output)
            return output

        def save_overlay(image, _sample, _camera, output, **_kwargs):
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(image, output)
            return output

        def save_gif(_paths, _duration, output):
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"test-gif")
            return {"status": "pass"}

        def save_onion(_paths, output):
            output.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (8, 8), (1, 2, 3)).save(output)

        with (mock.patch.object(_REVIEW_PACK, "_character_images", return_value=batch_images),
              mock.patch.object(_REVIEW_PACK, "_manifest_character_images",
                                side_effect=lambda manifest, *_args: pass_images[manifest["_test_name"]]),
              mock.patch.object(_REVIEW_PACK, "_character_plan_coverage",
                                return_value={"status": "pass", "coverage": {}, "missing": []}),
              mock.patch.object(_REVIEW_PACK, "_stature_strip",
                                return_value={"status": "pass", "missing_heights": [], "images": []}),
              mock.patch.object(_REVIEW_PACK, "_character_grid", side_effect=save_grid),
              mock.patch.object(_REVIEW_PACK, "_annotate_joint_centers", side_effect=save_overlay),
              mock.patch.object(_REVIEW_PACK, "gif", side_effect=save_gif),
              mock.patch.object(_REVIEW_PACK, "onion", side_effect=save_onion)):
            result = _REVIEW_PACK.assemble_character_pack(
                prepared, {"prepared_sha256": "prepared", "render_identity": "render", "metadata": {}},
                {"prepared_sha256": "prepared", "render_identity": "render", "metadata": {}},
                root, identifiers, baseline=baseline, stature_inputs=stature_inputs,
                # This is a previously preflighted optional historical source;
                # its own comparison result is intentionally separate.
                comparison_passes=comparison_passes)
        return result, json.loads((root / "character-pack-coverage.json").read_text()), \
            json.loads((root / "character-regression.json").read_text())

    def test_assemble_pack_is_complete_without_baseline_and_marks_external_scopes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result, coverage, regression = self._assemble_minimal_current_pack(
                Path(temporary) / "pack", stature_inputs={"inputs": {}, "missing_heights": []})
            self.assertEqual(result["status"], "pass")
            self.assertEqual(coverage["complete_pack_status"], "pass")
            self.assertEqual(coverage["baseline_status"], "not-required")
            self.assertEqual(coverage["scope"], "visual-comparison-pack")
            self.assertEqual(coverage["full_change_acceptance"], "not-assessed")
            self.assertIn("source/package parity", coverage["external_verification_required"])
            self.assertEqual(regression["status"], "pass")
            self.assertEqual(regression["current_mode_comparisons"]["comparison_count"], 28)

    def test_assemble_pack_reports_missing_stature_and_rejects_missing_or_failed_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result, coverage, _ = self._assemble_minimal_current_pack(
                Path(temporary) / "no-stature", stature_inputs=None)
            self.assertEqual(result["status"], "incomplete")
            self.assertEqual(coverage["complete_pack_status"], "incomplete")
            self.assertEqual(coverage["stature_status"], "incomplete")
            with self.assertRaisesRegex(ValueError, "lacks managed regression passes: female-singleton"):
                self._assemble_minimal_current_pack(Path(temporary) / "no-mode",
                                                    stature_inputs=None,
                                                    omit_mode="female-singleton")
            failed, failed_coverage, failed_regression = self._assemble_minimal_current_pack(
                Path(temporary) / "failed-mode", stature_inputs=None,
                differing_mode="male-singleton")
            self.assertEqual(failed["status"], "fail")
            self.assertEqual(failed_regression["status"], "fail")
            self.assertEqual(failed_coverage["complete_pack_status"], "incomplete")

    def test_optional_historical_pixel_and_coverage_failures_do_not_gate_current_pack(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result, coverage, regression = self._assemble_minimal_current_pack(
                Path(temporary) / "pack", stature_inputs={"inputs": {}, "missing_heights": []},
                with_partial_baseline=True)
            self.assertEqual(result["status"], "pass")
            self.assertEqual(coverage["complete_pack_status"], "pass")
            self.assertEqual(coverage["baseline_status"], "fail")
            self.assertEqual(regression["baseline"]["comparison_status"], "fail")
            self.assertEqual(regression["baseline"]["comparison"]["pixel"]["status"], "fail")
            self.assertEqual(regression["baseline"]["comparison"]["missing_views"][0]["views"], ["rear"])

    def test_current_pack_can_complete_without_historical_baseline(self) -> None:
        self.assertEqual(_complete_character_pack_status(
            coverage_status="pass", character_ids=("skeleton", "male", "female"),
            current_mode_status="pass", stature_status="pass",
            repeatability_status="pass", gif_status="pass"), "pass")

    def test_current_pack_stays_incomplete_without_required_stature_or_mode_evidence(self) -> None:
        common = dict(coverage_status="pass", character_ids=("skeleton", "male", "female"),
                      repeatability_status="pass", gif_status="pass")
        self.assertEqual(_complete_character_pack_status(
            **common, current_mode_status="pass", stature_status="incomplete"), "incomplete")
        self.assertEqual(_complete_character_pack_status(
            **common, current_mode_status="incomplete", stature_status="pass"), "incomplete")

    def test_historical_baseline_is_optional_but_malformed_supplied_baseline_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            build = workspace / "build"
            build.mkdir()
            baseline = build / "characters_r1_dev_try-1_baseline"
            baseline.mkdir()
            output = build / "characters_r1_dev_try-1_pack"
            self.assertIsNone(_preflight_skeleton_baseline(
                None, {}, baseline, output, workspace))
            with self.assertRaisesRegex(ValueError, "no safe input.json"):
                _preflight_skeleton_baseline(baseline, {}, baseline / "candidate",
                                             output, workspace)

    def test_candidate_with_stale_evaluated_identity_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            run = workspace / "build" / "characters_r1_dev_try-1_candidate"
            run.mkdir(parents=True)
            (run / "input.json").write_text("{}")
            (run / "evaluated.json").write_text(json.dumps({
                "prepared_sha256": "stale", "samples": []}))
            prepared = {"content_sha256": "current", "samples": [], "sources": {}}
            with mock.patch.object(_REVIEW_PACK, "read_prepared", return_value=prepared):
                with self.assertRaisesRegex(ValueError, "stale"):
                    _preflight_current_candidate(run, prepared)

    def test_primary_candidate_package_identity_must_match_the_loaded_input(self) -> None:
        prepared = {"content_sha256": "current", "package_identity": "current-package",
                    "source_hashes": {"profile": "source"}}
        with mock.patch.object(_REVIEW_PACK, "_read_evaluated_candidate",
                               return_value={**prepared, "package_identity": "old-package"}):
            with self.assertRaisesRegex(ValueError, "stale package_identity"):
                _preflight_current_candidate(Path("unused"), prepared)

    def test_stature_input_with_stale_package_identity_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            run = workspace / "build" / "characters_r1_dev_try-1_h150"
            run.mkdir(parents=True)
            source_ids = {"profile": "profile", "mobility": "mobility",
                          "review-scene": {"id": "scene"}}
            primary = {"sources": {"profile": {"stature_m": 1.70, "id": "profile"},
                                   "mobility": {"id": "mobility"},
                                   "review-scene": {"id": "scene"}},
                       "package_identity": "current-package", "source_hashes": source_ids}
            stale = {"sources": {"profile": {"stature_m": 1.50, "id": "profile"},
                                  "mobility": {"id": "mobility"},
                                  "review-scene": {"id": "scene"}},
                     "package_identity": "old-package", "source_hashes": source_ids,
                     "samples": [{"fixture": "neutral", "beat": {"numerator": 0, "denominator": 1}},
                                 {"fixture": "squat", "beat": {"numerator": 2, "denominator": 1}}]}
            with mock.patch.object(_REVIEW_PACK, "_read_evaluated_candidate", return_value=stale):
                with self.assertRaisesRegex(ValueError, "incompatible package/profile/scene"):
                    _stature_comparison_inputs([f"1.50={run}"], primary,
                                               workspace / "build" / "characters_r1_dev_try-1_pack",
                                               workspace)

    def test_current_mode_completeness_requires_all_mode_sample_view_rows(self) -> None:
        prepared = {"samples": [{"id": "n"}, {"id": "r"}]}
        batch_images = {
            "skeleton": {sample: {"front": Path(sample + "-s-front"), "side": Path(sample + "-s-side")}
                         for sample in ("n", "r")},
            "male": {sample: {"front": Path(sample + "-m-front")} for sample in ("n", "r")},
            "female": {sample: {"side": Path(sample + "-f-side")} for sample in ("n", "r")},
        }
        rows = []
        for name, identifier in _REVIEW_PACK._CURRENT_MODE_COMPARISONS.items():
            for sample, views in batch_images[identifier].items():
                rows.extend({"comparison": name, "character_id": identifier,
                             "sample_id": sample, "view": view, "status": "pass"}
                            for view in views)
        result = _current_mode_comparison_status(rows, prepared, batch_images,
                                                 ("skeleton", "male", "female"))
        self.assertEqual(result["status"], "pass")
        missing = _current_mode_comparison_status(rows[:-1], prepared, batch_images,
                                                   ("skeleton", "male", "female"))
        self.assertEqual(missing["status"], "incomplete")
        self.assertTrue(missing["missing"])
        failed_rows = [dict(row, status="fail") if row["comparison"] == "male-singleton" else row
                       for row in rows]
        failed = _current_mode_comparison_status(failed_rows, prepared, batch_images,
                                                  ("skeleton", "male", "female"))
        self.assertEqual(failed["status"], "fail")

    def test_baseline_report_record_is_json_safe_and_omits_internal_objects(self) -> None:
        receipt = Path("build/old-run/processes/example/outcome.json").resolve()
        record = _baseline_report_record({
            "status": "pass", "receipt_path": receipt,
            "common_sample_ids": ["neutral/00000"],
            "required_paths": [Path("frames/neutral/front/00000.png")],
            "evaluated_geometry": {"samples": [{"artifact": Path("evaluated.json")} ]},
            "run_root": Path("build/old-run"), "manifest": object(), "prepared": object(),
        })
        self.assertEqual(record["receipt_path"], str(receipt))
        self.assertEqual(record["required_paths"], ["frames/neutral/front/00000.png"])
        self.assertEqual(record["evaluated_geometry"]["samples"][0]["artifact"], "evaluated.json")
        self.assertNotIn("manifest", record)
        self.assertNotIn("prepared", record)
        json.dumps(record)

    def test_sole_crop_creates_nested_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.png"
            Image.new("RGB", (64, 64), (120, 140, 160)).save(source)
            output = root / "composites" / "sole-forefoot-rocker" / "sample.png"
            self.assertEqual(_sole_crop(source, output, "Skeleton / front / sample"), output)
            self.assertTrue(output.is_file())

    def test_joint_center_markers_resolve_in_the_real_adult_profile(self) -> None:
        profile_path = Path(__file__).resolve().parents[1] / "rig" / "profiles" / "adult-reference-v1.yaml"
        profile = yaml.safe_load(profile_path.read_text())
        structure_ids = {item["id"] for item in profile["structures"]}
        self.assertEqual(len(_JOINT_CENTER_IDS), len(set(_JOINT_CENTER_IDS)))
        self.assertEqual(set(_JOINT_CENTER_IDS) - structure_ids, set())
        self.assertIn("talus.R", _JOINT_CENTER_IDS)
        self.assertIn("talus.L", _JOINT_CENTER_IDS)

    def test_baseline_join_uses_fixture_and_exact_fraction_not_schedule_ids(self) -> None:
        candidate = {"samples": [
            {"id": "new-arm-000", "fixture": "arm-raise", "beat": {"numerator": 1, "denominator": 4},
             "frames": {"arm": 1}, "actions": [], "contacts": [], "world_root": {},
             "frame_id": 11},
            {"id": "new-arm-001", "fixture": "arm-raise", "beat": {"numerator": 1, "denominator": 1},
             "frames": {"arm": 2}, "actions": [], "contacts": [], "world_root": {},
             "frame_id": 20},
        ]}
        baseline = {"samples": [
            {"id": "old-arm-A", "fixture": "arm-raise", "beat": {"numerator": 2, "denominator": 8},
             "frames": {"arm": 1}, "actions": [], "contacts": [], "world_root": {},
             "frame_id": 5},
            {"id": "old-arm-B", "fixture": "arm-raise", "beat": {"numerator": 4, "denominator": 4},
             "frames": {"arm": 2}, "actions": [], "contacts": [], "world_root": {},
             "frame_id": 6},
        ]}
        matches = _baseline_sample_matches(candidate, baseline, ("arm-raise",))
        self.assertEqual([(row["baseline_sample_id"], row["candidate_sample_id"]) for row in matches],
                         [("old-arm-A", "new-arm-000"), ("old-arm-B", "new-arm-001")])
        self.assertEqual(matches[0]["beat"], {"numerator": 1, "denominator": 4})

    def test_baseline_join_rejects_duplicate_or_missing_logical_beats(self) -> None:
        sample = {"id": "a", "fixture": "squat", "beat": {"numerator": 1, "denominator": 2},
                  "frames": {}, "actions": [], "contacts": [], "world_root": {}}
        with self.assertRaisesRegex(ValueError, "duplicate logical sample key"):
            _baseline_sample_matches({"samples": [sample, {**sample, "id": "b"}]},
                                     {"samples": [sample]}, ("squat",))
        with self.assertRaisesRegex(ValueError, "missing required shared-core beats"):
            _baseline_sample_matches({"samples": [sample]},
                                     {"samples": [{**sample, "beat": {"numerator": 1, "denominator": 1}}]},
                                     ("squat",))

    def test_baseline_join_requires_equal_movement_contract(self) -> None:
        candidate_row = {"id": "new", "fixture": "walking-in-place",
                         "beat": {"numerator": 3, "denominator": 4}, "frames": {"hip": 1},
                         "actions": [], "contacts": [], "world_root": {}}
        old_row = {**candidate_row, "id": "old", "frames": {"hip": 2}}
        with self.assertRaisesRegex(ValueError, "movement differs"):
            _baseline_sample_matches({"samples": [candidate_row]}, {"samples": [old_row]},
                                     ("walking-in-place",))

    def test_optional_baseline_reports_partial_overlap_and_differences_without_raising(self) -> None:
        candidate_sample = {"id": "new-0", "fixture": "neutral",
                            "beat": {"numerator": 0, "denominator": 1},
                            "frames": {"hip": 1}, "actions": [], "contacts": [], "world_root": {}}
        historical_sample = {**candidate_sample, "id": "old-0", "frames": {"hip": 2}}
        matches, report = _optional_baseline_sample_matches(
            {"samples": [candidate_sample], "sources": {"review-scene": {"cameras": []}}},
            {"samples": [historical_sample]}, ("neutral",))
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["baseline_sample_id"], "old-0")
        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["movement_differences"][0]["fields"], ["frames"])

    def test_character_manifest_requires_registry_and_sample_completeness(self) -> None:
        ids = ("skeleton", "male", "female")
        sample_ids = ("neutral-0", "arm-raise-1")
        manifest = {"format": "character-render-manifest/v1", "characters": [
            {"id": identifier, "samples": [{"id": sample_id} for sample_id in sample_ids]}
            for identifier in ids
        ]}
        rows = _character_sample_rows(manifest, ids, sample_ids)
        self.assertEqual(tuple(rows), ids)
        self.assertEqual([row["id"] for row in rows["female"]], list(sample_ids))

        reversed_manifest = {**manifest, "characters": list(reversed(manifest["characters"]))}
        with self.assertRaisesRegex(ValueError, "member inventory"):
            _character_sample_rows(reversed_manifest, ids, sample_ids)
        incomplete = {**manifest, "characters": manifest["characters"][:-1]}
        with self.assertRaisesRegex(ValueError, "member inventory"):
            _character_sample_rows(incomplete, ids, sample_ids)
        shortened = {**manifest, "characters": [
            {"id": identifier, "samples": rows[identifier] if identifier != "male"
             else rows[identifier][:-1]}
            for identifier in ids
        ]}
        with self.assertRaisesRegex(ValueError, "missing, extra, or reordered samples"):
            _character_sample_rows(shortened, ids, sample_ids)

    def test_image_inventory_rejects_missing_and_escaping_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            frames = root / "frames"
            sample = {"id": "neutral-0", "fixture": "neutral"}
            prepared = {"samples": [sample], "sources": {"review-scene": {"cameras": []}}}
            manifest = {"format": "character-render-manifest/v1", "characters": []}
            for identifier in ("skeleton", "male", "female"):
                views = ("front", "side", "rear")
                images = {}
                for view in views:
                    path = frames / (identifier if identifier != "skeleton" else "") / "neutral" / view / "00000.png"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    Image.new("RGB", (32, 32), (50, 80, 120)).save(path)
                    relative = path.relative_to(frames).as_posix()
                    images[view] = relative
                manifest["characters"].append({"id": identifier,
                                               "samples": [{"id": sample["id"], "images": images}]})
            result = _character_images(manifest, frames, prepared, ("skeleton", "male", "female"))
            self.assertEqual(tuple(result), ("skeleton", "male", "female"))
            self.assertEqual(set(result["female"]["neutral-0"]), {"front", "side", "rear"})

            bad = {"format": manifest["format"], "characters": [dict(row) for row in manifest["characters"]]}
            bad["characters"][1] = {"id": "male", "samples": [{"id": "neutral-0", "images": {
                "front": "../../outside.png", "side": "male/neutral/side/00000.png",
                "rear": "male/neutral/rear/00000.png"}}]}
            with self.assertRaisesRegex(ValueError, "Unsafe character image path"):
                _character_images(bad, frames, prepared, ("skeleton", "male", "female"))

    def test_comparison_grid_keeps_three_labeled_character_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            images = {}
            for index, identifier in enumerate(("skeleton", "male", "female")):
                image = root / f"{identifier}.png"
                Image.new("RGB", (40, 24), (index * 70, 40, 150)).save(image)
                images[identifier] = {"sample-0": {"front": image}}
            output = root / "comparison.png"
            _character_grid(images, [{"sample_id": "sample-0", "beat": {
                "numerator": 0, "denominator": 1}}], "front", output,
                title="Neutral silhouette / front", columns=("skeleton", "male", "female"))
            with Image.open(output) as result:
                self.assertEqual(result.size, (900, 400))

    def test_coverage_is_explicit_when_required_samples_are_absent(self) -> None:
        partial = {"sampling": {"arm-raise": [{"bpm": 90, "static": [1], "animation": [1]}]},
                   "samples": []}
        result = _character_plan_coverage(partial)
        self.assertEqual(result["status"], "incomplete")
        self.assertIn("squat@90bpm", result["missing"])
        self.assertIn("walking-in-place@90bpm", result["missing"])
        self.assertIn("forefoot-rocker@90bpm animation samples", result["missing"])

    def test_complete_focus_counts_and_references_are_not_synthesized(self) -> None:
        def records(count):
            return [{"sample_id": f"sample-{index}", "beat": {"numerator": index, "denominator": 1}}
                    for index in range(count)]
        sampling = {
            "arm-raise": [{"bpm": 90, "static": records(5), "animation": records(17)}],
            "squat": [{"bpm": 90, "static": records(5), "animation": records(17)}],
            "walking-in-place": [{"bpm": 90, "static": records(9), "animation": records(33)}],
            "forefoot-rocker": [{"bpm": 90, "static": records(2), "animation": records(3)}],
        }
        for identifier in ("sweep-shoulder-bilateral-elevation", "sweep-shoulder-bilateral-plane",
                           "sweep-shoulder-bilateral-external_twist", "sweep-forearm-bilateral-pronation",
                           "sweep-knee-bilateral-flexion"):
            sampling[identifier] = [{"bpm": 90, "animation": records(3)}]
        result = _character_plan_coverage({"sampling": sampling})
        self.assertEqual(result["status"], "incomplete")
        self.assertIn("neutral sample", result["missing"])
        self.assertIn("rest sample", result["missing"])
        self.assertEqual(result["coverage"]["walking-in-place"],
                         {"static": 9, "animation": 33, "status": "pass"})
        with self.assertRaisesRegex(ValueError, "missing or foreign sample"):
            _sample_records_for_plan(sampling["squat"][0], "squat", "static", {})

    def test_coverage_requires_supplied_neutral_rest_and_rocker_animation(self) -> None:
        data = {"sampling": {"forefoot-rocker": [{"bpm": 90, "animation": [1]}]},
                "samples": [{"fixture": "neutral"}, {"fixture": "rest"}]}
        result = _character_plan_coverage(data)
        self.assertIn("arm-raise@90bpm", result["missing"])
        self.assertNotIn("neutral sample", result["missing"])
        self.assertNotIn("rest sample", result["missing"])

    def test_stature_strip_uses_only_supplied_sample_images(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inputs = {"missing_heights": [], "inputs": {}}
            for height in (1.50, 1.70, 1.90):
                prepared = {"content_sha256": f"prep-{height}", "package_identity": "pkg",
                            "sources": {"profile": {"stature_m": height},
                                        "review-scene": {"cameras": []}},
                            "samples": [
                                {"id": "neutral-000", "fixture": "neutral",
                                 "beat": {"numerator": 0, "denominator": 1}, "frame_id": 0},
                                {"id": "squat-002", "fixture": "squat",
                                 "beat": {"numerator": 2, "denominator": 1}, "frame_id": 2},
                            ]}
                run = root / f"h-{height:.2f}"
                frames = run / "frames"
                manifest = {"format": "character-render-manifest/v1", "characters": []}
                for identifier_index, identifier in enumerate(("skeleton", "male", "female")):
                    rows = []
                    for sample in prepared["samples"]:
                        views = ("front", "side", "rear") if sample["fixture"] == "neutral" else ("front", "side")
                        paths = {}
                        for view in views:
                            path = frames / identifier / sample["fixture"] / view / "00000.png"
                            path.parent.mkdir(parents=True, exist_ok=True)
                            Image.new("RGB", (24, 32), (identifier_index * 60, int(height * 50), 30)).save(path)
                            paths[view] = path.relative_to(frames).as_posix()
                        rows.append({"id": sample["id"], "images": paths})
                    manifest["characters"].append({"id": identifier, "samples": rows})
                run.mkdir(parents=True, exist_ok=True)
                (run / "render-manifest.json").write_text(__import__("json").dumps(manifest))
                (run / "build-metadata.json").write_text("{}")
                if height == 1.70:
                    pass_root = root / "clean-a"
                    pass_root.mkdir()
                    shutil.copytree(frames, pass_root / "frames")
                    (pass_root / "render-manifest.json").write_text(__import__("json").dumps(manifest))
                    (pass_root / "build-metadata.json").write_text("{}")
                    inputs["inputs"][height] = {"run_root": None, "prepared": prepared}
                else:
                    inputs["inputs"][height] = {"run_root": run, "prepared": prepared}
                    pass_root = root / f"stature-{int(round(height * 100)):03d}"
                    pass_root.mkdir()
                    shutil.copytree(frames, pass_root / "frames")
                    (pass_root / "render-manifest.json").write_text(__import__("json").dumps(manifest))
                    (pass_root / "build-metadata.json").write_text("{}")

            report = _stature_strip(inputs, ("skeleton", "male", "female"), root)
            self.assertEqual(report["status"], "pass")
            self.assertEqual(len(report["cells"]), 36)
            self.assertEqual(len(report["images"]), 4)
            for image in report["images"]:
                self.assertTrue((root / image).is_file())
            self.assertEqual({row["height_m"] for row in report["sources"]}, {1.50, 1.70, 1.90})


if __name__ == "__main__":
    unittest.main()
