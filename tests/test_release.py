# SPDX-License-Identifier: Apache-2.0
"""Synthetic Git-history tests for automatic 0.x release selection."""

from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
import zipfile

from tests.run_roots import test_case_root, test_run_root


def _load_release_module():
    path = Path(__file__).resolve().parents[1] / "tools" / "release.py"
    spec = importlib.util.spec_from_file_location("hml_release_tool", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


release = _load_release_module()


def setUpModule():
    test_run_root("release")


class SyntheticRepository:
    def __init__(self, path: Path):
        self.path = path
        subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True)
        self.git("config", "user.name", "Release tests")
        self.git("config", "user.email", "release-tests@example.invalid")
        self.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.0"\n')
        self.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.0"\nsource = { editable = "." }\n')
        self.write("openspec/specs/api/spec.md", "# API\n\nInitial.\n")
        self.write("openspec/changes/archive/old-accepted/.openspec.yaml", "schema: spec-driven\n")
        self.git("add", ".")
        self.git("commit", "-qm", "baseline")
        self.base = self.git("rev-parse", "HEAD")

    def git(self, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=self.path, check=True,
                              capture_output=True, text=True).stdout.strip()

    def write(self, path: str, content: str) -> None:
        target = self.path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    def commit(self, message: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-qm", message)
        return self.git("rev-parse", "HEAD")

    def archive(self, change_id: str) -> str:
        self.write(f"openspec/changes/archive/{change_id}/.openspec.yaml", "schema: spec-driven\n")
        return self.commit(f"archive {change_id}")

    def bootstrap_config(self) -> None:
        self.write("tools/release-config.toml",
                   f'bootstrap_commit = "{self.base}"\nbootstrap_version = "0.2.0"\n')


class ReleaseSelectionTests(unittest.TestCase):
    def setUp(self):
        self.root = test_case_root("release", self._testMethodName)
        self.repo = SyntheticRepository(self.root / "repo")

    def test_no_pending_archive_does_not_release(self):
        plan = release.build_plan(self.repo.path, self.repo.base, self.repo.base)
        self.assertFalse(plan["has_release"])
        self.assertIsNone(plan["version"])

    def test_archived_skip_specs_change_with_no_spec_delta_is_patch(self):
        self.repo.archive("skip-specs-fix")
        plan = release.build_plan(self.repo.path, self.repo.base, "HEAD")
        self.assertEqual(plan["version"], "0.2.1")
        self.assertEqual([entry["id"] for entry in plan["archives"]], ["skip-specs-fix"])
        self.assertFalse(plan["specification_changed"])

    def test_moved_active_marker_into_archive_is_acceptance(self):
        active = self.repo.path / "openspec/changes/rename-me"
        active.mkdir(parents=True)
        (active / ".openspec.yaml").write_text("schema: spec-driven\n")
        self.repo.commit("create active change")
        accepted = self.repo.path / "openspec/changes/archive/rename-me"
        accepted.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "mv", str(active), str(accepted)], cwd=self.repo.path, check=True)
        acceptance = self.repo.commit("archive accepted change")
        plan = release.build_plan(self.repo.path, self.repo.base, "HEAD")
        self.assertEqual(plan["version"], "0.2.1")
        self.assertEqual(plan["archives"], [{"id": "rename-me", "acceptance_commit": acceptance}])

    def test_canonical_edit_including_editorial_change_is_minor(self):
        self.repo.write("openspec/specs/api/spec.md", "# API\n\nUpdated punctuation!\n")
        self.repo.archive("spec-change")
        plan = release.build_plan(self.repo.path, self.repo.base, "HEAD")
        self.assertEqual(plan["version"], "0.3.0")
        self.assertEqual(plan["changed_specifications"], ["openspec/specs/api/spec.md"])

    def test_multiple_pending_changes_use_one_increment_and_keep_acceptance_commits(self):
        first = self.repo.archive("first")
        second = self.repo.archive("second")
        plan = release.build_plan(self.repo.path, self.repo.base, "HEAD")
        self.assertEqual(plan["version"], "0.2.1")
        self.assertEqual(plan["archives"], [
            {"id": "first", "acceptance_commit": first},
            {"id": "second", "acceptance_commit": second},
        ])

    def test_active_change_and_historical_archive_edit_are_not_acceptance(self):
        self.repo.write("openspec/changes/in-flight/.openspec.yaml", "schema: spec-driven\n")
        self.repo.write("openspec/changes/archive/old-accepted/.openspec.yaml", "schema: spec-driven\nupdated: true\n")
        self.repo.commit("edit planning and old archive")
        plan = release.build_plan(self.repo.path, self.repo.base, "HEAD")
        self.assertFalse(plan["has_release"])

    def test_delete_and_rename_of_canonical_specs_are_minor(self):
        (self.repo.path / "openspec/specs/api/spec.md").unlink()
        self.repo.write("openspec/specs/api-v2/spec.md", "# API v2\n")
        self.repo.archive("spec-rename")
        plan = release.build_plan(self.repo.path, self.repo.base, "HEAD")
        self.assertEqual(plan["version"], "0.3.0")
        self.assertEqual(set(plan["changed_specifications"]), {
            "openspec/specs/api/spec.md", "openspec/specs/api-v2/spec.md",
        })

    def test_wrong_or_non_ancestor_boundary_fails_closed(self):
        unrelated = self.root / "unrelated"
        subprocess.run(["git", "init", "-q", str(unrelated)], check=True)
        subprocess.run(["git", "-C", str(unrelated), "config", "user.name", "Other"], check=True)
        subprocess.run(["git", "-C", str(unrelated), "config", "user.email", "other@example.invalid"], check=True)
        (unrelated / "x").write_text("x")
        subprocess.run(["git", "-C", str(unrelated), "add", "x"], check=True)
        subprocess.run(["git", "-C", str(unrelated), "commit", "-qm", "unrelated"], check=True)
        bad = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / "tools" / "release.py"),
                              "plan", "--repo", str(self.repo.path), "--boundary", str(unrelated), "--target", "HEAD"],
                             capture_output=True, text=True)
        self.assertNotEqual(bad.returncode, 0)

    def test_versions_are_strict_pre_one_zero(self):
        for value in ("1.0.0", "0.2", "0.02.1", "0.2.01", "v0.2.1", "0.2.1rc1"):
            with self.subTest(value=value), self.assertRaises(release.ReleaseError):
                release.next_version(value, False)
        self.assertEqual(release.next_version("0.2.9", False), "0.2.10")
        self.assertEqual(release.next_version("0.2.9", True), "0.3.0")

    def test_only_authored_project_and_lock_version_fields_change(self):
        release.update_version_files(self.repo.path, "0.3.0")
        self.assertEqual(release.version_at(self.repo.path, self.repo.git("rev-parse", "HEAD")), "0.2.0")
        self.assertIn('version = "0.3.0"', (self.repo.path / "pyproject.toml").read_text())
        self.assertIn('version = "0.3.0"', (self.repo.path / "uv.lock").read_text())
        with self.assertRaises(release.ReleaseError):
            release.update_version_files(self.repo.path, "1.0.0")

    def test_fixed_bootstrap_and_version_reservation_are_recoverable(self):
        self.repo.bootstrap_config()
        acceptance = self.repo.archive("release-me")

        class NoReleaseClient:
            def latest_release(self):
                return None

        reservation = release.reserve_release(self.repo.path, NoReleaseClient(), "HEAD")
        self.assertEqual(reservation["version"], "0.2.1")
        self.assertEqual(reservation["archives"][0]["acceptance_commit"], acceptance)
        diff = self.repo.git("diff-tree", "--no-commit-id", "--name-only", "-r", reservation["candidate"])
        self.assertEqual(set(diff.splitlines()), {"pyproject.toml", "uv.lock"})
        resumed = release.reserve_release(self.repo.path, NoReleaseClient(), "HEAD")
        self.assertTrue(resumed["resumed"])
        self.assertEqual(resumed["candidate"], reservation["candidate"])

    def test_advancing_main_recomputes_and_coalesces_after_compare_and_swap_rejection(self):
        self.repo.bootstrap_config()
        first_acceptance = self.repo.archive("first")
        remote = self.root / "origin.git"
        subprocess.run(["git", "-c", "init.defaultBranch=master", "init", "-q", "--bare", str(remote)], check=True)
        subprocess.run(["git", "--git-dir", str(remote), "symbolic-ref", "HEAD", "refs/heads/main"], check=True)
        self.repo.git("remote", "add", "origin", str(remote))
        self.repo.git("push", "-q", "-u", "origin", "main")
        runner = self.root / "runner"
        subprocess.run(["git", "clone", "-q", str(remote), str(runner)], check=True)
        self.assertEqual(subprocess.run(["git", "rev-parse", "HEAD"], cwd=runner, check=True,
                                        capture_output=True, text=True).stdout.strip(), first_acceptance)
        self.assertTrue((runner / "tools" / "release-config.toml").is_file())
        subprocess.run(["git", "config", "user.name", "Release runner"], cwd=runner, check=True)
        subprocess.run(["git", "config", "user.email", "runner@example.invalid"], cwd=runner, check=True)

        class NoReleaseClient:
            def latest_release(self):
                return None

        stale = release.reserve_release(runner, NoReleaseClient(), "refs/remotes/origin/main")
        second_acceptance = self.repo.archive("second")
        self.repo.git("push", "-q", "origin", "main")
        rejected = subprocess.run(["git", "push", "origin", f"{stale['candidate']}:refs/heads/main"],
                                  cwd=runner, capture_output=True, text=True)
        self.assertNotEqual(rejected.returncode, 0, rejected.stdout + rejected.stderr)

        subprocess.run(["git", "fetch", "-q", "origin", "main"], cwd=runner, check=True)
        subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=runner, check=True,
                       capture_output=True)
        current = release.reserve_release(runner, NoReleaseClient(), "refs/remotes/origin/main")
        self.assertNotEqual(current["candidate"], stale["candidate"])
        self.assertEqual(current["version"], "0.2.1")
        self.assertEqual(current["archives"], [
            {"id": "first", "acceptance_commit": first_acceptance},
            {"id": "second", "acceptance_commit": second_acceptance},
        ])
        subprocess.run(["git", "push", "origin", f"{current['candidate']}:refs/heads/main"],
                       cwd=runner, check=True, capture_output=True)

    def test_superseded_wake_up_resumes_reservation_and_leaves_new_archive_pending(self):
        self.repo.bootstrap_config()
        self.repo.archive("first")

        class NoReleaseClient:
            def latest_release(self):
                return None

        reservation = release.reserve_release(self.repo.path, NoReleaseClient(), "HEAD")
        candidate = reservation["candidate"]
        wheel, checksum = self._wheel()
        published = FakeGitHub()
        release.publish_release(self.repo.path, published, candidate, wheel,
                                "https://example.invalid/run/first", checksum)
        self.repo.git("tag", "v0.2.1", candidate)
        self.repo.archive("accepted-after-snapshot")
        resumed = release.reserve_release(self.repo.path, NoReleaseClient(), "HEAD")
        self.assertTrue(resumed["resumed"])
        self.assertEqual(resumed["candidate"], candidate)
        pending = release.pending_after_latest_release(self.repo.path, published, "HEAD")
        self.assertEqual(pending["version"], "0.2.2")
        self.assertEqual([row["id"] for row in pending["archives"]], ["accepted-after-snapshot"])

    def test_unrelated_latest_tag_cannot_suppress_archived_changes(self):
        self.repo.bootstrap_config()
        self.repo.archive("must-remain-pending")
        self.repo.git("tag", "v0.2.0", self.repo.base)

        class UnrelatedPublishedRelease:
            def latest_release(self):
                return {"tag_name": "v0.2.0", "draft": False}

        with self.assertRaisesRegex(release.ReleaseError, "not a managed published release"):
            release.reserve_release(self.repo.path, UnrelatedPublishedRelease(), "HEAD")
        self.assertEqual(release.version_at(self.repo.path, "HEAD"), "0.2.0")

    def test_latest_managed_release_is_verified_against_chain_assets_and_bootstrap(self):
        candidate = self._reserved_candidate()
        wheel, checksum = self._wheel()
        client = FakeGitHub()
        release.publish_release(self.repo.path, client, candidate, wheel,
                                "https://example.invalid/run/complete", checksum)
        self.repo.git("tag", "v0.2.1", candidate)
        self.assertEqual(release._latest_boundary(self.repo.path, client), (candidate, "0.2.1"))
        (self.repo.path / "tools/release-config.toml").unlink()
        with self.assertRaisesRegex(release.ReleaseError, "bootstrap configuration"):
            release._latest_boundary(self.repo.path, client)

    def test_first_managed_spec_release_is_minor_from_fixed_baseline(self):
        self.repo.bootstrap_config()
        self.repo.write("openspec/specs/api/spec.md", "# API\n\nNew approved requirement.\n")
        self.repo.archive("versioned-releases")

        class NoReleaseClient:
            def latest_release(self):
                return None

        reservation = release.reserve_release(self.repo.path, NoReleaseClient(), "HEAD")
        self.assertEqual(reservation["version"], "0.3.0")
        self.assertEqual(reservation["boundary"], self.repo.base)

    def _reserved_candidate(self):
        self.repo.bootstrap_config()
        self.repo.archive("release-me")

        class NoReleaseClient:
            def latest_release(self):
                return None

        return release.reserve_release(self.repo.path, NoReleaseClient(), "HEAD")["candidate"]

    def _wheel(self, name="humanmotionlib-0.2.1-py3-none-any.whl", version="0.2.1"):
        path = self.root / name
        manifest = {"version": version, "resources": {"schema/demo": "0" * 64}}
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(f"humanmotionlib-{version}.dist-info/METADATA",
                             f"Metadata-Version: 2.1\nName: humanmotionlib\nVersion: {version}\n")
            archive.writestr("humanmotionlib/_version.py", f'__version__ = "{version}"\n')
            archive.writestr("humanmotionlib/resources/runtime-manifest.json", json.dumps(manifest))
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        checksum_path = self.root / "wheel.sha256"
        checksum_path.write_text(f"{checksum}  {path}\n")
        return path, checksum_path

    def test_publish_is_immutable_and_matching_retry_is_noop(self):
        candidate = self._reserved_candidate()
        wheel, checksum = self._wheel()
        client = FakeGitHub()
        first = release.publish_release(self.repo.path, client, candidate, wheel, "https://example.invalid/run/1", checksum)
        second = release.publish_release(self.repo.path, client, candidate, wheel, "https://example.invalid/run/1", checksum)
        self.assertFalse(first["already_complete"])
        self.assertTrue(second["already_complete"])
        self.assertEqual(set(client.release["asset_bytes"]), {wheel.name, "SHA256SUMS"})
        changed, changed_checksum = self._wheel()
        changed.write_bytes(changed.read_bytes() + b"different")
        changed_checksum.write_text(f"{hashlib.sha256(changed.read_bytes()).hexdigest()}  {changed}\n")
        with self.assertRaises(release.ReleaseError):
            release.publish_release(self.repo.path, client, candidate, changed, "https://example.invalid/run/2", changed_checksum)

    def test_partial_asset_publication_resumes_without_replacing_wheel(self):
        candidate = self._reserved_candidate()
        wheel, checksum = self._wheel()
        original_bytes = wheel.read_bytes()
        client = FakeGitHub(fail_once_asset="SHA256SUMS")
        with self.assertRaises(release.ReleaseError):
            release.publish_release(self.repo.path, client, candidate, wheel, "https://example.invalid/run/1", checksum)
        self.assertEqual(set(client.release["asset_bytes"]), {wheel.name})

        with zipfile.ZipFile(wheel, "a") as archive:
            archive.writestr("candidate-change.txt", "different checked candidate")
        changed_checksum = hashlib.sha256(wheel.read_bytes()).hexdigest()
        changed_checksum_path = self.root / "changed-wheel.sha256"
        changed_checksum_path.write_text(f"{changed_checksum}  {wheel.name}\n")
        with self.assertRaisesRegex(release.ReleaseError, "differs from the checked candidate"):
            release.publish_release(self.repo.path, client, candidate, wheel,
                                    "https://example.invalid/run/2", changed_checksum_path)
        self.assertEqual(client.release["asset_bytes"][wheel.name], original_bytes)
        self.assertEqual(set(client.release["asset_bytes"]), {wheel.name})

        wheel.write_bytes(original_bytes)
        recovered = release.publish_release(self.repo.path, client, candidate, wheel, "https://example.invalid/run/1", checksum)
        self.assertFalse(recovered["already_complete"])
        self.assertEqual(set(client.release["asset_bytes"]), {wheel.name, "SHA256SUMS"})

    def test_publication_fault_matrix_reconciles_each_boundary_without_overwrite(self):
        candidate = self._reserved_candidate()
        wheel, checksum = self._wheel()
        stages = ("draft-create", "after-draft-create", "wheel-upload", "checksum-upload",
                  "before-final-publish", "after-final-publish")
        for stage in stages:
            with self.subTest(stage=stage):
                client = FakeGitHub(fail_stage=stage)
                if stage == "wheel-upload":
                    client.fail_once_asset = wheel.name
                if stage == "checksum-upload":
                    client.fail_once_asset = "SHA256SUMS"
                with self.assertRaises(release.ReleaseError):
                    release.publish_release(self.repo.path, client, candidate, wheel,
                                             "https://example.invalid/run/fault", checksum)
                if stage == "draft-create":
                    self.assertIsNone(client.release, "denied draft creation must not create a release")
                    continue
                recovered = release.publish_release(self.repo.path, client, candidate, wheel,
                                                    "https://example.invalid/run/fault", checksum)
                if stage == "after-final-publish":
                    self.assertTrue(recovered["already_complete"])
                else:
                    self.assertFalse(recovered["already_complete"])
                self.assertEqual(set(client.release["asset_bytes"]), {wheel.name, "SHA256SUMS"})

    def test_missing_checksum_conflicting_tag_and_denied_write_fail_closed(self):
        candidate = self._reserved_candidate()
        wheel, checksum = self._wheel()
        client = FakeGitHub()
        with self.assertRaises(release.ReleaseError):
            release.publish_release(self.repo.path, client, candidate, wheel,
                                     "https://example.invalid/run/missing", self.root / "absent.sha256")
        self.assertIsNone(client.release)

        self.repo.git("tag", "v0.2.1", self.repo.base)
        with self.assertRaisesRegex(release.ReleaseError, "conflicting commit"):
            release.publish_release(self.repo.path, client, candidate, wheel,
                                    "https://example.invalid/run/tag", checksum)
        self.assertIsNone(client.release)
        self.repo.git("tag", "-d", "v0.2.1")

        denied = FakeGitHub(fail_stage="draft-create")
        with self.assertRaisesRegex(release.ReleaseError, "denied"):
            release.publish_release(self.repo.path, denied, candidate, wheel,
                                    "https://example.invalid/run/denied", checksum)
        self.assertIsNone(denied.release)

    def test_unrelated_empty_draft_or_completed_release_is_never_adopted(self):
        candidate = self._reserved_candidate()
        wheel, checksum = self._wheel()
        unrelated_draft = FakeGitHub()
        unrelated_draft.release = {
            "id": 42, "tag_name": "v0.2.1", "target_commitish": candidate,
            "name": "HumanMotionLib 0.2.1", "body": "", "draft": True,
            "assets": {}, "asset_bytes": {},
            "upload_url": "https://uploads.github.test/releases/42/assets{?name,label}",
        }
        with self.assertRaisesRegex(release.ReleaseError, "release notes do not identify"):
            release.publish_release(self.repo.path, unrelated_draft, candidate, wheel,
                                    "https://example.invalid/run/unrelated", checksum)
        self.assertEqual(unrelated_draft.release["body"], "")
        self.assertEqual(unrelated_draft.release["assets"], {})

        checksum_value = hashlib.sha256(wheel.read_bytes()).hexdigest()
        completed = FakeGitHub()
        completed.release = {
            "id": 43, "tag_name": "v0.2.1", "target_commitish": candidate,
            "name": "HumanMotionLib 0.2.1", "body": "unrelated published release",
            "draft": False, "assets": {}, "asset_bytes": {},
            "upload_url": "https://uploads.github.test/releases/43/assets{?name,label}",
        }
        for name, data in ((wheel.name, wheel.read_bytes()),
                           ("SHA256SUMS", f"{checksum_value}  {wheel.name}\n".encode("ascii"))):
            completed.release["asset_bytes"][name] = data
            completed.release["assets"][name] = {
                "name": name,
                "digest": f"sha256:{hashlib.sha256(data).hexdigest()}",
                "url": f"https://api.github.test/assets/{name}",
            }
        with self.assertRaisesRegex(release.ReleaseError, "release notes do not identify"):
            release.publish_release(self.repo.path, completed, candidate, wheel,
                                    "https://example.invalid/run/unrelated", checksum)


class FakeGitHub:
    def __init__(self, fail_once_asset=None, fail_stage=None):
        self.release = None
        self.next_id = 1
        self.fail_once_asset = fail_once_asset
        self.fail_stage = fail_stage

    def latest_release(self):
        if self.release is not None and self.release.get("draft") is False:
            return self.release
        return None

    def release_for_tag(self, tag):
        if self.release is not None and self.release["tag_name"] == tag:
            return self.release
        return None

    def release_assets(self, release_record):
        return release_record["assets"]

    def asset_bytes(self, asset):
        return self.release["asset_bytes"][asset["name"]]

    def request(self, path, *, method="GET", payload=None, **kwargs):
        if path == "/releases" and method == "POST":
            if self.fail_stage == "draft-create":
                self.fail_stage = None
                raise release.ReleaseError("simulated denied GitHub draft write (403)")
            self.release = {
                **payload,
                "id": self.next_id,
                "upload_url": "https://uploads.github.test/releases/1/assets{?name,label}",
                "assets": {},
                "asset_bytes": {},
            }
            self.next_id += 1
            if self.fail_stage == "after-draft-create":
                self.fail_stage = None
                raise release.ReleaseError("simulated lost draft creation response")
            return 201, self.release
        if path == "/releases/1" and method == "PATCH":
            if payload.get("draft") is False and self.fail_stage == "before-final-publish":
                self.fail_stage = None
                raise release.ReleaseError("simulated denied final publication (403)")
            self.release.update(payload)
            if payload.get("draft") is False and self.fail_stage == "after-final-publish":
                self.fail_stage = None
                raise release.ReleaseError("simulated lost final publication response")
            return 200, self.release
        raise AssertionError((path, method, payload))

    def upload_asset(self, release_record, name, data):
        if self.fail_once_asset == name:
            self.fail_once_asset = None
            raise release.ReleaseError("simulated interrupted asset upload")
        self.release["asset_bytes"][name] = data
        self.release["assets"][name] = {
            "name": name,
            "digest": f"sha256:{hashlib.sha256(data).hexdigest()}",
            "url": f"https://api.github.test/assets/{name}",
        }
        return self.release["assets"][name]


if __name__ == "__main__":
    unittest.main()
