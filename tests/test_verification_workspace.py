# SPDX-License-Identifier: Apache-2.0
"""Workspace ownership for numerical verification outputs."""

import contextlib
import io
import json
from pathlib import Path
import unittest
from unittest import mock

from humanmotionlib.verify_skeleton import main
from humanmotionlib.verification_run import verify_collection
from tests.run_roots import test_case_root


class VerificationWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.case = test_case_root("verification-workspace", self._testMethodName)
        self.workspace = self.case / "workspace"
        self.build = self.workspace / "build"
        self.build.mkdir(parents=True)
        self.external_input = self.case / "external-input"
        self.external_input.mkdir()
        (self.external_input / "input.json").write_text("{}")
        (self.external_input / "evaluated.json").write_text(json.dumps({"samples": []}))
        self._attempt = 0

    def run_root(self):
        self._attempt += 1
        root = self.build / f"portable-installed-runtime_e3dcbf_test_try-{self._attempt}_verify"
        root.mkdir()
        return root

    @staticmethod
    def prepared(fixtures=("neutral", "rest")):
        return {
            "content_sha256": "prepared-hash",
            "samples": [{"id": fixture, "fixture": fixture} for fixture in fixtures],
            "sampling": {},
            "sources": {"profile": {}, "mobility": {}, "diagnostics": []},
        }

    def invoke_main(self, output, options=(), *, fixture_set=("neutral", "rest")):
        arguments = ["verify-skeleton", "--input", str(self.external_input),
                     "--output", str(output), *options]
        prepared = self.prepared(fixture_set)
        result = {"status": "pass", "scope": "test", "samples": []}
        error = io.StringIO()
        with mock.patch("sys.argv", arguments), \
             mock.patch("humanmotionlib.verify_skeleton.read_prepared", return_value=prepared) as read, \
             mock.patch("humanmotionlib.verify_skeleton.verify_transforms", return_value=result), \
             mock.patch("humanmotionlib.coverage.audit_action_cases", return_value={"status": "pass", "actions": {}}), \
             mock.patch("humanmotionlib.verification_run.verify_collection", return_value=result) as full, \
             mock.patch("humanmotionlib.backend_measurements.verify_backend", return_value=result) as backend, \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(error):
            status = main(workspace=self.workspace)
        return status, read, full, backend, error.getvalue()

    def test_full_preview_and_transforms_modes_write_inside_owned_run_from_external_inputs(self):
        modes = (
            ((), ("neutral", "rest"), "full"),
            (("--thorax-preview",), ("neutral", "rest"), "preview"),
            (("--squat-preview",), ("squat",), "preview"),
            (("--transforms-only",), ("neutral", "rest"), "transforms"),
        )
        for options, fixtures, kind in modes:
            with self.subTest(options=options):
                run = self.run_root()
                report = run / "metrics.json"
                status, read, full, backend, error = self.invoke_main(
                    report, options, fixture_set=fixtures)
                self.assertEqual(status, 0, error)
                self.assertTrue(report.is_file())
                self.assertEqual(read.call_args.args[0], self.external_input / "input.json")
                if kind == "full":
                    full.assert_called_once()
                    self.assertEqual(full.call_args.kwargs["workspace"], self.workspace.resolve())
                    self.assertEqual(full.call_args.args[2], report.resolve())
                elif kind == "preview":
                    backend.assert_called_once()
                    full.assert_not_called()
                else:
                    full.assert_not_called()
                    backend.assert_not_called()

    def test_relative_stature_inputs_resolve_from_workspace_and_remain_disjoint(self):
        run = self.run_root()
        stature_runs = []
        for index in range(3):
            path = self.build / f"portable-installed-runtime_e3dcbf_test_try-{index + 10}_stature"
            path.mkdir()
            (path / "input.json").write_text("{}")
            stature_runs.append(path)
        relative = [str(path.relative_to(self.workspace)) for path in stature_runs]
        prepared = self.prepared()
        report = run / "metrics.json"
        result = {"status": "pass", "scope": "transforms", "samples": []}
        error = io.StringIO()
        with mock.patch("sys.argv", ["verify-skeleton", "--input", str(self.external_input / "input.json"),
                                      "--output", str(report), "--transforms-only",
                                      "--stature-builds", *relative]), \
             mock.patch("humanmotionlib.verify_skeleton.read_prepared", return_value=prepared), \
             mock.patch("humanmotionlib.verify_skeleton.verify_transforms", return_value=result), \
             mock.patch("humanmotionlib.stature_comparison.compare_statures",
                        return_value={"status": "pass"}) as compare, \
             mock.patch("humanmotionlib.dense_verification.audit_squat_balance",
                        return_value={"status": "pass", "stature_m": 1.7, "samples": 0}), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(error):
            status = main(workspace=self.workspace)
        self.assertEqual(status, 0, f"{error.getvalue()} compare={compare.call_args}")
        self.assertEqual(compare.call_args.args[0], [path.resolve() for path in stature_runs])
        self.assertTrue(report.is_file())

    def test_invalid_report_and_shard_destinations_fail_before_writes(self):
        invalid_run = self.build / "not-a-valid-run"
        invalid_report = invalid_run / "metrics.json"
        for options, fixtures in (((), ("neutral", "rest")),
                                  (("--thorax-preview",), ("neutral", "rest")),
                                  (("--squat-preview",), ("squat",)),
                                  (("--transforms-only",), ("neutral", "rest"))):
            with self.subTest(options=options):
                status, read, full, backend, error = self.invoke_main(
                    invalid_report, options, fixture_set=fixtures)
                self.assertEqual(status, 1, error)
                self.assertFalse(invalid_report.exists())
                self.assertFalse((invalid_run / "metrics-samples").exists())
                read.assert_not_called()
                full.assert_not_called()
                backend.assert_not_called()

        run = self.run_root()
        report = run / "metrics.json"
        outside = self.case / "outside-shards"
        outside.mkdir()
        sentinel = outside / "sentinel.txt"
        sentinel.write_text("preserve")
        (run / "metrics-samples").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "outside build|nested run identity"):
            verify_collection({"content_sha256": "prepared-hash", "samples": []},
                              {"prepared_sha256": "mismatch", "samples": []},
                              report, lambda *_: {}, workspace=self.workspace)
        self.assertFalse(report.exists())
        self.assertEqual(sentinel.read_text(), "preserve")

    def test_full_writer_retains_numerical_checks_in_owned_summary_and_shard(self):
        run = self.run_root()
        output = run / "metrics.json"
        prepared = {
            "content_sha256": "prepared-hash",
            "source_hashes": {"profile": "profile-hash"},
            "samples": [{"id": "neutral@0", "fixture": "neutral",
                         "beat": {"numerator": 0, "denominator": 1},
                         "expected_actions": {}, "world_root": {}, "frame_id": 0}],
            "sampling": {},
            "sources": {"diagnostics": [{"id": "neutral", "duration_beats": 0}],
                        "profile": {"stature_m": 1.7, "structures": []},
                        "humanoid-map": {"entries": []}},
        }
        evaluated = {
            "prepared_sha256": "prepared-hash",
            "samples": [{"id": "neutral@0", "frames": {}, "geometry": {}, "scene": "stable"}],
            "metadata": {"native_bones": [], "semantic_targets": {}, "collections":
                         ["Anatomy", "Controls", "Humanoid", "Review"],
                         "independent_collection_visibility":
                         {key: True for key in ("Anatomy", "Controls", "Humanoid", "Review")}},
        }
        metric = {"id": "torso.height", "measured": 1.7001, "expected": 1.7,
                  "tolerance": 0.0002, "units": "m", "beat": 0,
                  "status": "pass"}
        sample_result = {"id": "neutral@0", "fixture": "neutral", "status": "pass",
                         "checks": [metric], "metric_count": 1}
        backend_result = {"samples": [sample_result]}
        with mock.patch("humanmotionlib.verification_run.verify_backend",
                        return_value=backend_result):
            summary = verify_collection(prepared, evaluated, output, lambda *_: {},
                                       workspace=self.workspace)
        details = run / "metrics-samples" / "neutral@0.json"
        self.assertTrue(details.is_file())
        persisted_detail = json.loads(details.read_text())
        self.assertEqual(summary["status"], "pass")
        self.assertEqual(summary["samples"][0]["details"], "metrics-samples/neutral@0.json")
        self.assertEqual(persisted_detail["checks"][0]["measured"], 1.7001)
        self.assertEqual(persisted_detail["checks"][0]["expected"], 1.7)
        self.assertEqual(persisted_detail["checks"][0]["tolerance"], 0.0002)
        self.assertEqual(persisted_detail["checks"][0]["status"], "pass")


if __name__ == "__main__":
    unittest.main()
