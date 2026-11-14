"""Structural checks for the package and release workflow."""

from pathlib import Path
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def load_workflow(name: str) -> dict:
    return yaml.load((WORKFLOWS / name).read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


class CandidateWorkflowTests(unittest.TestCase):
    def test_fresh_uv_install_failure_stops_before_tests(self):
        uv_bin = shutil.which("uv")
        if uv_bin is None:
            self.skipTest("uv is not available in this execution environment")
        workflow = load_workflow("package.yml")
        step = next(step for step in workflow["jobs"]["tests"]["steps"]
                    if step.get("name") == "Verify received wheel and install it")
        with tempfile.TemporaryDirectory(prefix="hml-invalid-wheel-install-") as temporary:
            root = Path(temporary)
            received = root / "received-wheel"
            received.mkdir()
            wheel_name = "humanmotionlib-0.3.0-py3-none-any.whl"
            wheel = received / wheel_name
            wheel.write_bytes(b"not a wheel archive")
            digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
            env = os.environ.copy()
            env.update({
                "RUNNER_TEMP": str(root), "GITHUB_ENV": str(root / "github-env"),
                "GITHUB_WORKSPACE": str(ROOT), "EXPECTED_WHEEL_NAME": wheel_name,
                "EXPECTED_WHEEL_SHA256": digest, "UV_CACHE_DIR": str(root / "uv-cache"),
                "PATH": f"{Path(uv_bin).parent}{os.pathsep}{env['PATH']}",
            })
            result = subprocess.run(["bash", "-e", "-u", "-o", "pipefail", "-c", step["run"]],
                                    cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ARTIFACT received file=", result.stdout)
            self.assertFalse((root / "github-env").exists(), "failed install must not expose TEST_PYTHON")

    def test_received_wheel_step_executes_name_hash_and_install_gates(self):
        workflow = load_workflow("package.yml")
        consumer = next(step for step in workflow["jobs"]["tests"]["steps"]
                    if step.get("name") == "Verify received wheel and install it")
        producer = next(step for step in workflow["jobs"]["build"]["steps"]
                        if step.get("name") == "Build and identify wheel")
        with tempfile.TemporaryDirectory(prefix="hml-wheel-handoff-") as temporary:
            root = Path(temporary)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            uv_log = root / "uv.log"
            uv = fake_bin / "uv"
            uv.write_text("#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$UV_LOG\"\n"
                          "if [ \"$1\" = build ]; then\n"
                          "  while [ $# -gt 0 ]; do if [ \"$1\" = --out-dir ]; then out=$2; shift 2; else shift; fi; done\n"
                          "  mkdir -p \"$out\"\n"
                          "  printf 'selected wheel bytes' > \"$out/humanmotionlib-0.3.0-py3-none-any.whl\"\n"
                          "  printf 'extra wheel bytes' > \"$out/extra-0.3.0-py3-none-any.whl\"\n"
                          "  exit 0\nfi\n"
                          "if [ \"$UV_FAIL_INSTALL\" = 1 ] && [ \"$1 $2\" = 'pip install' ]; then exit 9; fi\n")
            uv.chmod(0o755)

            def env_for(expected_name="", expected_hash="", fail_install="0"):
                env = os.environ.copy()
                env.update({
                    "RUNNER_TEMP": str(root), "GITHUB_ENV": str(root / "github-env"),
                    "GITHUB_WORKSPACE": str(ROOT),
                    "EXPECTED_WHEEL_NAME": expected_name, "EXPECTED_WHEEL_SHA256": expected_hash,
                    "UV_LOG": str(uv_log), "UV_FAIL_INSTALL": fail_install,
                    "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
                })
                return env

            source_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                        check=True, capture_output=True, text=True).stdout.strip()
            producer_env = env_for()
            producer_env.update({"GITHUB_SHA": source_sha, "GITHUB_RUN_ID": "77",
                                 "GITHUB_RUN_ATTEMPT": "1", "GITHUB_OUTPUT": str(root / "outputs")})
            built = subprocess.run(["bash", "-e", "-u", "-o", "pipefail", "-c", producer["run"]],
                                   cwd=ROOT, env=producer_env, capture_output=True, text=True)
            self.assertEqual(built.returncode, 0, built.stderr)
            staged = root / "wheel-artifact"
            staged_wheels = list(staged.glob("*.whl"))
            self.assertEqual(len(staged_wheels), 1, "artifact staging must include only the selected wheel")
            wheel = staged_wheels[0]
            wheel_name = wheel.name
            digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
            outputs = dict(line.split("=", 1) for line in (root / "outputs").read_text().splitlines())
            self.assertEqual(outputs["wheel_name"], wheel_name)
            self.assertEqual(outputs["wheel_sha256"], digest)
            received = root / "received-wheel"
            received.mkdir()
            # Filesystem copy models the artifact action's opaque file handoff; the workflow uses
            # upload-artifact/download-artifact in the hosted run.
            for path in staged.iterdir():
                shutil.copy2(path, received / path.name)

            def run_step(expected_name=wheel_name, expected_hash=digest, fail_install="0"):
                return subprocess.run(["bash", "-e", "-u", "-o", "pipefail", "-c", consumer["run"]],
                                      cwd=ROOT, env=env_for(expected_name, expected_hash, fail_install),
                                      capture_output=True, text=True)

            success = run_step()
            self.assertEqual(success.returncode, 0, success.stderr)
            self.assertIn(f"ARTIFACT received file={wheel_name} sha256={digest}", success.stdout)
            uv_log.write_text("")
            wrong_name = run_step(expected_name="different.whl")
            self.assertNotEqual(wrong_name.returncode, 0)
            self.assertEqual(uv_log.read_text(), "", "wrong filename must stop before installation")
            wrong_hash = run_step(expected_hash="0" * 64)
            self.assertNotEqual(wrong_hash.returncode, 0)
            self.assertEqual(uv_log.read_text(), "", "wrong checksum must stop before installation")
            failed_install = run_step(fail_install="1")
            self.assertNotEqual(failed_install.returncode, 0)
            self.assertIn("venv", uv_log.read_text())
            self.assertIn("pip install", uv_log.read_text())

    def test_host_test_step_returns_failure_from_an_executable_failing_suite(self):
        workflow = load_workflow("package.yml")
        step = next(step for step in workflow["jobs"]["tests"]["steps"]
                    if step.get("name") == "Run host-only test suite")
        with tempfile.TemporaryDirectory(prefix="hml-host-failure-") as temporary:
            root = Path(temporary)
            tests = root / "tests"
            tests.mkdir()
            (tests / "test_failure_control.py").write_text(
                "import unittest\nclass FailingControl(unittest.TestCase):\n"
                "    def test_expected_failure(self):\n        self.fail('controlled failure')\n")
            env = os.environ.copy()
            env.update({"RUNNER_TEMP": str(root), "TEST_PYTHON": sys.executable,
                        "HUMANMOTIONLIB_SOURCE_ROOT": str(root)})
            result = subprocess.run(["bash", "-e", "-u", "-o", "pipefail", "-c", step["run"]],
                                    cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("controlled failure", result.stderr)

    def test_push_builds_one_wheel_then_runs_installed_tests(self):
        workflow = load_workflow("package.yml")
        jobs = workflow["jobs"]
        self.assertEqual(set(workflow["on"]), {"push", "pull_request"})
        self.assertEqual(set(jobs), {"build", "tests", "publish"})
        self.assertEqual(jobs["tests"]["needs"], "build")
        build = "\n".join(step.get("run", "") for step in jobs["build"]["steps"])
        upload = next(step for step in jobs["build"]["steps"]
                      if step.get("uses", "").startswith("actions/upload-artifact@"))
        self.assertIn("uv build --wheel", build)
        self.assertNotIn("--sdist", build)
        self.assertIn("git rev-parse HEAD", build)
        self.assertIn("sha256sum", build)
        self.assertEqual(upload["with"]["if-no-files-found"], "error")
        self.assertEqual(upload["with"]["path"], "${{ runner.temp }}/wheel-artifact/*")
        self.assertIn('cp "$wheel" "$RUNNER_TEMP/wheel-artifact/$wheel_name"', build)
        self.assertNotIn("if", upload)
        self.assertNotIn("if", jobs["build"])
        self.assertNotIn("if", jobs["tests"])
        self.assertIn("${source_sha}-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}", build)
        self.assertIn("${{ github.sha }}", "\n".join(
            step.get("with", {}).get("ref", "") for step in jobs["build"]["steps"]))
        tests = "\n".join(step.get("run", "") for step in jobs["tests"]["steps"])
        self.assertIn("actions/download-artifact@", "\n".join(
            step.get("uses", "") for step in jobs["tests"]["steps"]))
        self.assertIn("EXPECTED_WHEEL_NAME", "\n".join(
            str(step.get("env", {})) for step in jobs["tests"]["steps"]))
        self.assertIn("TEST_PYTHON", tests)
        self.assertIn("check_host.discover_host_tests", tests)
        self.assertIn("test_character_installation", tests)
        self.assertIn('test "$actual_sha256" = "$EXPECTED_WHEEL_SHA256"', tests)
        self.assertIn("set -euo pipefail", tests)

    def test_publication_waits_for_tests_and_requires_main_version_bump(self):
        workflow = load_workflow("package.yml")
        publish = workflow["jobs"]["publish"]
        self.assertEqual(publish["needs"], ["build", "tests"])
        self.assertEqual(publish["if"], "github.event_name == 'push' && github.ref == 'refs/heads/main'")
        self.assertEqual(publish["permissions"]["contents"], "write")
        self.assertEqual(publish["concurrency"]["queue"], "max")
        self.assertNotIn("cancel-in-progress", publish["concurrency"])
        intent = next(step for step in publish["steps"] if step.get("id") == "intent")
        self.assertEqual(intent["name"], "Evaluate version increase after tests")
        self.assertIn("--before", intent["run"])
        self.assertIn("--after", intent["run"])
        self.assertIn("release.py intent", intent["run"])
        self.assertTrue(any(step.get("if") == "steps.intent.outputs.eligible == 'true'"
                            and step.get("name") == "Publish the tested wheel"
                            for step in publish["steps"]))
        publisher = "\n".join(step.get("run", "") for step in publish["steps"])
        self.assertIn("publish-push", publisher)
        self.assertIn("BUILD_WHEEL_SHA256", str(publish))
        self.assertNotIn("reserve", publisher)
        self.assertFalse((WORKFLOWS / "release-pipeline-control.yml").exists())


if __name__ == "__main__":
    unittest.main()
