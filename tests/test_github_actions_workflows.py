"""Structural checks for the shared GitHub Actions candidate chain."""

from pathlib import Path
import os
import subprocess
import unittest
import re

import yaml
from tests.run_roots import test_case_root


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def load_workflow(name: str) -> dict:
    return yaml.load((WORKFLOWS / name).read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


class CandidateWorkflowTests(unittest.TestCase):
    def test_candidate_build_gates_both_verification_jobs(self):
        workflow = load_workflow("package.yml")
        jobs = workflow["jobs"]
        self.assertEqual(set(jobs), {"build", "host-checks", "package-checks"})
        self.assertNotIn("needs", jobs["build"])
        self.assertEqual(jobs["host-checks"]["needs"], "build")
        self.assertEqual(jobs["package-checks"]["needs"], "build")
        self.assertEqual(jobs["host-checks"]["uses"], "./.github/workflows/host-python.yml")
        self.assertEqual(jobs["package-checks"]["uses"], "./.github/workflows/package-checks.yml")
        build_actions = [step.get("uses", "") for step in jobs["build"]["steps"]]
        self.assertEqual(sum(action.startswith("actions/upload-artifact@") for action in build_actions), 1)
        for consumer in (jobs["host-checks"], jobs["package-checks"]):
            self.assertIn("${{ needs.build.outputs.source_sha }}", consumer["with"]["source_ref"])
            self.assertIn("${{ needs.build.outputs.artifact_name }}", consumer["with"]["artifact_name"])
            self.assertIn("${{ needs.build.outputs.wheel_sha256 }}", consumer["with"]["wheel_sha256"])
        build_script = "\n".join(step.get("run", "") for step in jobs["build"]["steps"])
        self.assertIn("shopt -s nullglob", build_script)
        self.assertIn("git rev-parse HEAD", build_script)

    def test_verification_workflows_consume_supplied_candidate_only(self):
        for name in ("host-python.yml", "package-checks.yml"):
            with self.subTest(name=name):
                workflow = load_workflow(name)
                triggers = workflow["on"]
                self.assertEqual(set(triggers), {"workflow_call"})
                self.assertTrue({"source_ref", "artifact_name", "wheel_sha256"} <=
                                set(triggers["workflow_call"]["inputs"]))
                steps = next(iter(workflow["jobs"].values()))["steps"]
                downloads = [step for step in steps if step.get("uses", "").startswith("actions/download-artifact@")]
                self.assertEqual(len(downloads), 1)
                self.assertEqual(downloads[0]["with"]["name"], "${{ inputs.artifact_name }}")
                if name == "host-python.yml":
                    self.assertEqual(next(iter(workflow["jobs"].values()))["timeout-minutes"], "300")
                    self.assertEqual(
                        next(step for step in steps if step.get("name") == "Upload host check evidence")
                        ["with"]["path"], "${{ env.HML_CI_RUN_ROOT }}/host-evidence")
                script = "\n".join(step.get("run", "") for step in steps)
                self.assertIn("HML_EXPECTED_WHEEL_SHA256", script)
                self.assertIn("ps -axo pid,ppid,pgid,state,command", script)
                if name == "host-python.yml":
                    self.assertIn("$GITHUB_WORKSPACE/build/upgrade-host-python-314_", script)
                    self.assertIn("$RUNNER_TEMP/build/fix-github-actions-failures_", script)
                    self.assertIn("env -u PYTHONPATH -u PYTHONHOME", script)
                else:
                    self.assertIn("HML_DIRECT_WHEEL", script)
                    self.assertIn("character-workspace", script)
                    self.assertIn("HML_PREPARED_ROOT", script)
                    self.assertNotIn("HML_ELEMENT_ROOT/prepared/input.json", script)
                    self.assertRegex(script, re.compile(
                        r'\(\s*cd "\$outside"\s+env -u PYTHONPATH -u PYTHONHOME '
                        r'"\$install_root/environment/bin/hml" --workspace "\$workspace" '
                        r'prepare-skeleton --profile adult-reference-v1 --output "\$HML_PREPARED_ROOT/input.json"',
                        re.MULTILINE))
                    self.assertRegex(script, re.compile(
                        r'\(\s*cd "\$outside"\s+env -u PYTHONPATH -u PYTHONHOME '
                        r'"\$installed_python" "\$HML_ACCEPTANCE_RUN_ROOT/run.py"',
                        re.MULTILINE))

    def test_host_evidence_artifact_excludes_generated_trees_and_allows_cancelled_report(self):
        workflow = load_workflow("host-python.yml")
        steps = workflow["jobs"]["host-python"]["steps"]
        stage = next(step for step in steps if step.get("name") == "Stage host check evidence")
        upload = next(step for step in steps if step.get("name") == "Upload host check evidence")
        self.assertEqual(stage["if"], "always()")
        self.assertEqual(upload["if"], "always()")
        self.assertIn("host-checks.json", stage["run"])
        self.assertIn("[[ -f \"$source_file\" && ! -L \"$source_file\" ]]", stage["run"])

        names = (
            "candidate-wheel.sha256", "requirements.txt", "lock-export.log", "venv.log",
            "dependencies.log", "wheel-install.log", "dependency-check.log",
            "pre-test-environment.json", "module-version.log", "cli-version.log",
            "environment-check.log", "process-preflight.txt", "source-validation.log",
            "host-tests.log", "summary.txt",
        )
        evidence_cases = test_case_root("github-actions-workflow", "host-evidence-allowlist")

        def make_run(name, *, include_report=False, summary="present", symlink_name=None):
            run_root = evidence_cases / name
            run_root.mkdir()
            for evidence_name in names:
                path = run_root / evidence_name
                if evidence_name == "summary.txt" and summary == "missing":
                    continue
                if evidence_name == "summary.txt" and summary == "empty":
                    path.touch()
                elif evidence_name == symlink_name:
                    target = evidence_cases / f"{name}-outside-target.txt"
                    target.write_text(f"external:{evidence_name}\n", encoding="utf-8")
                    path.symlink_to(target)
                else:
                    path.write_text(f"evidence:{evidence_name}\n", encoding="utf-8")
            if include_report:
                (run_root / "host-checks.json").write_text("{}\n", encoding="utf-8")
            (run_root / "cases").mkdir()
            (run_root / "cases" / "large-fixture.bin").write_bytes(b"fixture")
            (run_root / "build").mkdir()
            (run_root / "build" / "scratch.bin").write_bytes(b"scratch")
            return run_root

        def run_stage(run_root):
            return subprocess.run(
                ["bash", "-e", "-c", stage["run"]],
                cwd=evidence_cases,
                env={**os.environ, "HML_CI_RUN_ROOT": str(run_root)},
                capture_output=True,
                text=True,
                check=False,
            )

        cancelled = make_run("cancelled", symlink_name="source-validation.log")
        result = run_stage(cancelled)
        self.assertEqual(result.returncode, 0, result.stderr)
        staged = cancelled / "host-evidence"
        self.assertEqual({path.name for path in staged.iterdir()}, set(names) - {"source-validation.log"})
        self.assertFalse((staged / "cases").exists())
        self.assertFalse((staged / "build").exists())

        complete = make_run("complete", include_report=True)
        result = run_stage(complete)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({path.name for path in (complete / "host-evidence").iterdir()},
                         set(names) | {"host-checks.json"})

        for name, summary in (("missing-summary", "missing"), ("empty-summary", "empty")):
            with self.subTest(summary=summary):
                incomplete = make_run(name, summary=summary)
                result = run_stage(incomplete)
                self.assertNotEqual(result.returncode, 0)

        missing_root = evidence_cases / "missing-run-root"
        result = run_stage(missing_root)
        self.assertNotEqual(result.returncode, 0)

    def test_release_calls_chain_once_and_uses_producer_outputs(self):
        release = load_workflow("release.yml")
        jobs = release["jobs"]
        self.assertNotIn("host-checks", jobs)
        self.assertEqual(jobs["package-checks"]["uses"], "./.github/workflows/package.yml")
        self.assertEqual(jobs["publish"]["needs"], ["reserve", "package-checks"])
        download = next(step for step in jobs["publish"]["steps"]
                        if step.get("uses", "").startswith("actions/download-artifact@"))
        self.assertEqual(download["with"]["name"], "${{ needs.package-checks.outputs.artifact_name }}")
        self.assertNotIn("github.run_attempt", download["with"]["name"])
        publish_script = next(step["run"] for step in jobs["publish"]["steps"]
                              if step.get("id") == "publish")
        self.assertIn("BUILD_WHEEL_SHA256", publish_script)
        self.assertIn("BUILD_SOURCE_SHA", publish_script)


if __name__ == "__main__":
    unittest.main()
