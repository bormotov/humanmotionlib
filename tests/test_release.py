# SPDX-License-Identifier: Apache-2.0
"""Synthetic Git-history tests for automatic 0.x release selection."""

from __future__ import annotations

import importlib.util
import importlib.metadata
import hashlib
import copy
from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
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
        with self.assertRaises(release.ReleaseError):
            release.build_pushed_release_plan(self.repo.path, str(unrelated), "HEAD", "0.2.1")

    def test_release_boundary_can_be_on_any_parent_path_and_archives_are_snapshot_scoped(self):
        self.repo.bootstrap_config()
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.1"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.1"\nsource = { editable = "." }\n')
        self.repo.archive("already-published")
        boundary = self.repo.git("rev-parse", "HEAD")
        self.repo.git("branch", "published", boundary)
        self.repo.git("checkout", "-qb", "alternate", self.repo.base)
        self.repo.write("README.md", "alternate first parent\n")
        first_parent = self.repo.commit("alternate history")
        subprocess.run(["git", "merge", "-s", "ours", "--no-ff", "published", "-m", "swap parent fixture"],
                       cwd=self.repo.path, check=True, capture_output=True, text=True)
        self.assertEqual(self.repo.git("rev-parse", "HEAD^1"), first_parent)
        self.assertEqual(self.repo.git("rev-parse", "HEAD^2"), boundary)
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.2"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.2"\nsource = { editable = "." }\n')
        self.repo.archive("later-change")
        plan = release.build_pushed_release_plan(self.repo.path, boundary, "HEAD", "0.2.2")
        self.assertEqual(plan["archives"], [
            {"id": "later-change", "acceptance_commit": self.repo.git("rev-parse", "HEAD")},
        ])

    def test_parallel_branches_keep_each_archive_acceptance_commit(self):
        boundary = self.repo.base
        self.repo.git("checkout", "-qb", "topic-a", boundary)
        archive_a = self.repo.archive("parallel-a")
        self.repo.git("checkout", "-qb", "topic-b", boundary)
        archive_b = self.repo.archive("parallel-b")
        self.repo.git("checkout", "main")
        subprocess.run(["git", "merge", "--no-ff", "topic-a", "-m", "merge topic a"],
                       cwd=self.repo.path, check=True, capture_output=True, text=True)
        subprocess.run(["git", "merge", "--no-ff", "topic-b", "-m", "merge topic b"],
                       cwd=self.repo.path, check=True, capture_output=True, text=True)
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.1"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.1"\nsource = { editable = "." }\n')
        target = self.repo.commit("version bump")
        plan = release.build_pushed_release_plan(self.repo.path, boundary, target, "0.2.1")
        self.assertEqual(plan["archives"], [
            {"id": "parallel-a", "acceptance_commit": archive_a},
            {"id": "parallel-b", "acceptance_commit": archive_b},
        ])

    def test_archive_removed_and_restored_after_release_is_not_attributed_twice(self):
        boundary = self.repo.archive("already-released")
        self.repo.git("rm", "-qr", "openspec/changes/archive/already-released")
        self.repo.commit("remove released archive")
        subprocess.run(["git", "checkout", boundary, "--", "openspec/changes/archive/already-released"],
                       cwd=self.repo.path, check=True, capture_output=True, text=True)
        self.repo.commit("restore released archive")
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.1"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.1"\nsource = { editable = "." }\n')
        target = self.repo.commit("version bump")
        plan = release.build_pushed_release_plan(self.repo.path, boundary, target, "0.2.1")
        self.assertEqual(plan["archives"], [])

    def test_archive_present_in_a_then_removed_in_b_and_restored_in_c_is_not_re_attributed(self):
        self.repo.bootstrap_config()
        boundary_a = self.repo.base
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.1"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.1"\nsource = { editable = "." }\n')
        self.repo.archive("reappearing-change")
        release_a = self.repo.git("rev-parse", "HEAD")
        client = FakeGitHub()
        plan_a = release.build_pushed_release_plan(self.repo.path, boundary_a, release_a, "0.2.1")
        record_a = self._published_push_record(client, plan_a, release_a, "0.2.1", 301)
        self.repo.git("tag", "v0.2.1", release_a)

        self.repo.git("rm", "-qr", "openspec/changes/archive/reappearing-change")
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.2"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.2"\nsource = { editable = "." }\n')
        release_b = self.repo.commit("remove previously released archive")
        plan_b = release.build_pushed_release_plan(self.repo.path, release_a, release_b, "0.2.2")
        record_b = self._published_push_record(client, plan_b, release_b, "0.2.2", 302)
        self.repo.git("tag", "v0.2.2", release_b)

        subprocess.run(["git", "checkout", release_a, "--", "openspec/changes/archive/reappearing-change"],
                       cwd=self.repo.path, check=True, capture_output=True, text=True)
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.3"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.3"\nsource = { editable = "." }\n')
        release_c = self.repo.commit("restore old archive")
        client.published_records = [record_b, record_a]
        boundary, version, released_ids = release._managed_release_history(self.repo.path, client)
        self.assertEqual((boundary, version), (release_b, "0.2.2"))
        self.assertEqual(released_ids, {"old-accepted", "reappearing-change"})
        plan_c = release.build_pushed_release_plan(self.repo.path, boundary, release_c, "0.2.3",
                                                   previously_released_archives=released_ids)
        self.assertEqual(plan_c["archives"], [])

    def test_bootstrap_archive_removed_in_a_and_restored_in_b_is_not_attributed(self):
        self.repo.bootstrap_config()
        bootstrap = self.repo.base
        self.repo.git("rm", "-qr", "openspec/changes/archive/old-accepted")
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.1"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.1"\nsource = { editable = "." }\n')
        release_a = self.repo.commit("remove bootstrap archive")
        client = FakeGitHub()
        plan_a = release.build_pushed_release_plan(self.repo.path, bootstrap, release_a, "0.2.1")
        record_a = self._published_push_record(client, plan_a, release_a, "0.2.1", 401)
        self.repo.git("tag", "v0.2.1", release_a)

        subprocess.run(["git", "checkout", bootstrap, "--", "openspec/changes/archive/old-accepted"],
                       cwd=self.repo.path, check=True, capture_output=True, text=True)
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.2"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.2"\nsource = { editable = "." }\n')
        release_b = self.repo.commit("restore bootstrap archive")
        client.published_records = [record_a]
        boundary, version, released_ids = release._managed_release_history(self.repo.path, client)
        self.assertEqual((boundary, version), (release_a, "0.2.1"))
        self.assertEqual(released_ids, {"old-accepted"})
        plan_b = release.build_pushed_release_plan(self.repo.path, boundary, release_b, "0.2.2",
                                                   previously_released_archives=released_ids)
        self.assertEqual(plan_b["archives"], [])

    def test_archives_removed_before_checked_snapshot_are_not_attributed(self):
        self.repo.bootstrap_config()
        boundary = self.repo.base
        self.repo.archive("temporary")
        archived = self.repo.path / "openspec/changes/archive/temporary"
        subprocess.run(["git", "rm", "-qr", str(archived)], cwd=self.repo.path, check=True)
        self.repo.commit("remove archived change")
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.1"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.1"\nsource = { editable = "." }\n')
        self.repo.commit("version bump")
        plan = release.build_pushed_release_plan(self.repo.path, boundary, "HEAD", "0.2.1")
        self.assertEqual(plan["archives"], [])

    def test_legacy_reservation_writer_and_automatic_version_cli_are_retired(self):
        self.assertFalse(hasattr(release, "reserve_release"))
        self.assertFalse(hasattr(release, "update_version_files"))
        result = subprocess.run([sys.executable, str(Path(release.__file__)), "--help"],
                                capture_output=True, text=True, check=True)
        for command in ("intent", "publish-push"):
            self.assertIn(command, result.stdout)
        for command in ("reserve", "set-version", "pending", "dispatch"):
            self.assertNotIn(command, result.stdout)

    def test_release_client_lists_drafts_and_reads_fresh_objects_by_id(self):
        class SDKRelease:
            def __init__(self, release_id, tag_name, draft=True, name="HumanMotionLib 0.2.1",
                         body="release notes", target_commitish="commit"):
                self.id = release_id
                self.tag_name = tag_name
                self.draft = draft
                self.prerelease = False
                self.name = name
                self.body = body
                self.target_commitish = target_commitish
                self.assets = []

            def get_assets(self):
                return self.assets

        class SDKRepo:
            def __init__(self):
                self.draft = SDKRelease(9, "v0.2.1")
                self.other_page = [SDKRelease(8, "v0.2.0", draft=False)]
                self.release_reads = []

            def get_releases(self):
                return iter([self.draft, *self.other_page])

            def get_release(self, release_id):
                self.release_reads.append(release_id)
                return SDKRelease(9, "untagged-server-response")

            def get_latest_release(self):
                raise AssertionError("draft-only history has no latest published release")

        repo = SDKRepo()
        sdk = SimpleNamespace(get_repo=lambda name: repo)
        client = release.GitHubClient("example/repo", "token", github=sdk)
        self.assertEqual(client.release_for_tag("v0.2.1")["id"], 9)
        fresh = client.release_by_id(9)
        self.assertEqual(fresh["tag_name"], "untagged-server-response")
        self.assertEqual(repo.release_reads, [9])
        self.assertEqual(client.published_releases()[0]["id"], 8)

    def test_release_client_uses_sdk_for_creation_updates_and_exact_asset_bytes(self):
        uploaded = {}

        class SDKAsset:
            id = 53
            name = "humanmotionlib-0.2.1-py3-none-any.whl"
            digest = None
            size = 6

            def download_asset(self, *, chunk_size):
                self.chunk_size = chunk_size
                return 200, {"content-type": "application/octet-stream"}, iter((b"wheel ", b"bytes"))

        class SDKRelease:
            id = 42
            tag_name = "v0.2.1"
            draft = True
            prerelease = False
            name = "HumanMotionLib 0.2.1"
            body = "notes"
            target_commitish = "candidate-sha"

            def __init__(self):
                self.assets = [SDKAsset()]
                self.update_arguments = None
                self.upload_arguments = None

            def get_assets(self):
                return iter(self.assets)

            def update_release(self, **kwargs):
                self.update_arguments = kwargs
                self.name = kwargs["name"]
                self.body = kwargs["message"]
                self.draft = kwargs["draft"]
                return self

            def upload_asset_from_memory(self, file_like, file_size, *, name, content_type):
                uploaded["bytes"] = file_like.read()
                uploaded["size"] = file_size
                uploaded["name"] = name
                uploaded["content_type"] = content_type
                asset = SimpleNamespace(id=54, name=name, digest="sha256:abc", size=file_size)
                self.assets.append(asset)
                return asset

        class SDKRepo:
            def __init__(self):
                self.release = SDKRelease()
                self.create_arguments = None
                self.release_reads = []

            def create_git_release(self, **kwargs):
                self.create_arguments = kwargs
                return self.release

            def get_release(self, release_id):
                self.release_reads.append(release_id)
                return self.release

        repo = SDKRepo()
        client = release.GitHubClient("example/repo", "token",
                                      github=SimpleNamespace(get_repo=lambda _name: repo))
        created = client.create_release("v0.2.1", "candidate-sha", "HumanMotionLib 0.2.1", "notes")
        self.assertEqual(repo.create_arguments, {
            "tag": "v0.2.1", "name": "HumanMotionLib 0.2.1", "message": "notes",
            "draft": True, "prerelease": False, "target_commitish": "candidate-sha",
        })
        self.assertEqual(client.release_by_id(42)["tag_name"], "v0.2.1")
        assets = client.release_assets(created)
        asset = assets["humanmotionlib-0.2.1-py3-none-any.whl"]
        self.assertEqual(client.asset_bytes(asset), b"wheel bytes")
        uploaded_asset = client.upload_asset(created, "SHA256SUMS", b"checksum")
        self.assertEqual(uploaded["bytes"], b"checksum")
        self.assertEqual(uploaded["size"], len(b"checksum"))
        self.assertEqual(uploaded_asset["name"], "SHA256SUMS")
        updated = client.update_release(created, body="updated notes", draft=False)
        self.assertEqual(updated["draft"], False)
        self.assertEqual(repo.release.update_arguments, {
            "name": "HumanMotionLib 0.2.1", "message": "updated notes", "draft": False,
            "prerelease": False, "tag_name": "v0.2.1", "target_commitish": "candidate-sha",
        })
        self.assertEqual(repo.release_reads, [42])

    def test_release_client_maps_missing_objects_and_denied_sdk_operations(self):
        class SDKError(Exception):
            def __init__(self, status):
                super().__init__("controlled SDK failure")
                self.status = status

        missing_repo = SimpleNamespace(get_release=lambda _id: (_ for _ in ()).throw(SDKError(404)))
        missing = release.GitHubClient("example/repo", "secret-token",
                                       github=SimpleNamespace(get_repo=lambda _name: missing_repo))
        self.assertIsNone(missing.release_by_id(9))

        denied_repo = SimpleNamespace(get_releases=lambda: (_ for _ in ()).throw(SDKError(403)))
        denied = release.GitHubClient("example/repo", "secret-token",
                                      github=SimpleNamespace(get_repo=lambda _name: denied_repo))
        with self.assertLogs("humanmotionlib.release", level="ERROR") as captured:
            with self.assertRaisesRegex(release.ReleaseError, r"list releases failed \(HTTP 403\)"):
                denied.published_releases()
        output = "\n".join(captured.output)
        self.assertIn("operation='list releases' status=403", output)
        self.assertNotIn("secret-token", output)

    def test_controlled_publication_with_candidate_wheel_preserves_identity_and_failure_gate(self):
        wheel_value = os.environ.get("HML_CONTROLLED_WHEEL")
        if not wheel_value:
            self.skipTest("set HML_CONTROLLED_WHEEL to run the clean candidate integration")
        wheel = Path(wheel_value).resolve()
        repo = Path(os.environ.get("HML_CONTROLLED_REPO", Path(__file__).resolve().parents[1])).resolve()
        self.assertTrue(wheel.is_file())
        with zipfile.ZipFile(wheel) as archive:
            metadata_names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
            self.assertEqual(len(metadata_names), 1)
            metadata = archive.read(metadata_names[0]).decode("utf-8")
        package_name = next(line.split(":", 1)[1].strip() for line in metadata.splitlines()
                            if line.startswith("Name:"))
        package_version = next(line.split(":", 1)[1].strip() for line in metadata.splitlines()
                               if line.startswith("Version:"))
        self.assertEqual(package_name.lower(), "humanmotionlib")
        self.assertEqual(wheel.name, f"humanmotionlib-{package_version}-py3-none-any.whl")
        self.assertEqual(importlib.metadata.version("humanmotionlib"), package_version)
        candidate = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                                   check=True, capture_output=True, text=True).stdout.strip()
        self.assertRegex(candidate, r"^[0-9a-f]{40,64}$")
        wheel_bytes = wheel.read_bytes()
        checksum = hashlib.sha256(wheel_bytes).hexdigest()
        checksum_path = self.root / "candidate-wheel.sha256"
        checksum_path.write_text(f"{checksum}  {wheel.name}\n", encoding="ascii")
        plan = {
            "candidate": candidate,
            "version": package_version,
            "boundary": candidate,
            "archives": [{"id": "controlled-pygithub-integration", "acceptance_commit": candidate}],
        }
        client = FakeGitHub(fail_once_asset="SHA256SUMS")
        workflow_url = "https://example.invalid/controlled-candidate-integration"
        with patch.object(release, "_ensure_remote_tag"), \
                patch.object(release, "_remote_tag_commit", return_value=candidate):
            with self.assertRaisesRegex(release.ReleaseError, "simulated interrupted asset upload"):
                release.publish_release(repo, client, candidate, wheel, workflow_url,
                                        checksum_path, plan_override=plan)
            self.assertTrue(client.release["draft"], "failed checksum upload must leave release unpublished")
            self.assertEqual(set(client.release["assets"]), {wheel.name})
            self.assertEqual(client.release["asset_bytes"][wheel.name], wheel_bytes)
            result = release.publish_release(repo, client, candidate, wheel, workflow_url,
                                             checksum_path, plan_override=plan)

        checksum_bytes = f"{checksum}  {wheel.name}\n".encode("ascii")
        self.assertEqual(result["candidate"], candidate)
        self.assertEqual(result["wheel_sha256"], checksum)
        self.assertFalse(client.release["draft"])
        self.assertEqual(set(client.release["asset_bytes"]), {wheel.name, "SHA256SUMS"})
        self.assertEqual(client.release["asset_bytes"][wheel.name], wheel_bytes)
        self.assertEqual(client.release["asset_bytes"]["SHA256SUMS"], checksum_bytes)
        evidence = {
            "source_commit": candidate,
            "wheel": wheel.name,
            "wheel_sha256": checksum,
            "first_attempt": "failed-before-publication; draft retained with wheel only",
            "retry": "published; matching wheel and SHA256SUMS",
        }
        (self.root / "controlled-publication.json").write_text(
            json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    def test_pygithub_210_real_lazy_pagination_is_materialized_inside_safe_boundary(self):
        try:
            import github  # noqa: F401
            import requests
            import urllib3
        except ImportError:
            self.skipTest("PyGithub release dependency group is not installed")

        from urllib.parse import urlparse

        requests_seen = []

        def response(status, payload, headers=None):
            result = requests.Response()
            result.status_code = status
            result.headers.update({"X-RateLimit-Remaining": "5000",
                                   "X-RateLimit-Reset": "4102444800"})
            result.headers.update(headers or {})
            result._content = json.dumps(payload).encode("utf-8")
            result.url = "https://api.github.com"
            return result

        def request(_session, method, url, **kwargs):
            parsed_url = urlparse(url)
            path = parsed_url.path
            request_path = path + (f"?{parsed_url.query}" if parsed_url.query else "")
            requests_seen.append((method, request_path, kwargs.get("headers", {})))
            if path == "/repos/acme/widgets":
                return response(200, {"id": 5, "full_name": "acme/widgets"})
            if path == "/repos/acme/widgets/releases/99":
                return response(404, {"message": "Not Found"})
            if path == "/repos/acme/widgets/releases/latest":
                return response(404, {"message": "Not Found"})
            if path == "/repos/acme/widgets/releases" and "page=2" in parsed_url.query:
                return response(500, {"message": "sensitive server body must not be logged"})
            if path == "/repos/acme/widgets/releases":
                return response(200, [{"id": 10, "tag_name": "v0.2.1", "draft": True,
                                      "prerelease": False, "name": "release", "body": "notes",
                                      "target_commitish": "main"}],
                                {"Link": '<https://api.github.com/repos/acme/widgets/releases?page=2>; rel="next"'})
            self.fail(f"unexpected SDK request: {method} {path}")

        with patch("requests.Session.request", new=request), \
                patch("github.Requester.time.sleep", return_value=None):
            client = release.GitHubClient("acme/widgets", "secret-token")
            requester = client._github._Github__requester
            self.assertIsNone(requester.kwargs["retry"], "SDK retries must remain disabled")
            self.assertEqual(requester.kwargs["api_version"], "2022-11-28")
            with self.assertLogs("humanmotionlib.release", level="ERROR") as captured:
                with self.assertRaisesRegex(release.ReleaseError, r"list releases by tag failed \(HTTP 500\)"):
                    client.release_for_tag("v0.2.1")
            with self.assertLogs("humanmotionlib.release", level="ERROR") as missing_logs:
                self.assertIsNone(client.release_by_id(99))
            with self.assertLogs("humanmotionlib.release", level="ERROR") as latest_logs:
                self.assertIsNone(client.latest_release())

        logs = "\n".join(captured.output)
        logs += "\n" + "\n".join(missing_logs.output)
        logs += "\n" + "\n".join(latest_logs.output)
        self.assertNotIn("sensitive server body", logs)
        self.assertNotIn("secret-token", logs)
        self.assertEqual([path for _method, path, _headers in requests_seen], [
            "/repos/acme/widgets", "/repos/acme/widgets/releases?per_page=100",
            "/repos/acme/widgets/releases?page=2", "/repos/acme/widgets/releases/99",
            "/repos/acme/widgets/releases/latest",
        ])
        self.assertTrue(all(headers.get("X-GitHub-Api-Version") == "2022-11-28"
                            for _method, _path, headers in requests_seen))

    def test_pygithub_real_asset_download_upload_and_stream_failure_contract(self):
        try:
            import github  # noqa: F401
            import requests
            import urllib3
        except ImportError:
            self.skipTest("PyGithub release dependency group is not installed")

        from urllib.parse import urlparse

        uploaded = {}
        stream_failure = [True]

        class RawStream:
            def __init__(self, fail=False):
                self.fail = fail

            def stream(self, _chunk_size, decode_content=True):
                yield b"partial" if self.fail else b"wheel bytes"
                if self.fail:
                    raise urllib3.exceptions.ProtocolError("sensitive stream failure")

        release_payload = {
            "id": 42, "tag_name": "v0.2.1", "draft": True, "prerelease": False,
            "name": "HumanMotionLib 0.2.1", "body": "notes", "target_commitish": "candidate",
            "url": "https://api.github.com/repos/acme/widgets/releases/42",
            "assets_url": "https://api.github.com/repos/acme/widgets/releases/42/assets",
            "upload_url": "https://uploads.github.com/repos/acme/widgets/releases/42/assets{?name,label}",
        }

        def response(status, payload, url, headers=None, content=None):
            result = requests.Response()
            result.status_code = status
            result.headers.update({"X-RateLimit-Remaining": "5000",
                                   "X-RateLimit-Reset": "4102444800"})
            result.headers.update(headers or {})
            result._content = json.dumps(payload).encode("utf-8") if content is None else content
            result.url = url
            return result

        def request(_session, method, url, **kwargs):
            parsed_url = urlparse(url)
            if parsed_url.path == "/repos/acme/widgets":
                return response(200, {"id": 5, "full_name": "acme/widgets"}, url)
            if parsed_url.path == "/repos/acme/widgets/releases/42" and method == "GET":
                return response(200, release_payload, url)
            if parsed_url.path == "/repos/acme/widgets/releases/42/assets" and method == "GET":
                return response(200, [{
                    "id": 53, "name": "humanmotionlib-0.2.1-py3-none-any.whl",
                    "size": 11, "digest": None,
                    "url": "https://api.github.com/repos/acme/widgets/releases/assets/53",
                    "browser_download_url": "https://github.com/acme/widgets/releases/download/v0.2.1/humanmotionlib-0.2.1-py3-none-any.whl",
                }], url)
            if parsed_url.path == "/repos/acme/widgets/releases/assets/53" and method == "GET":
                result = response(200, None, url)
                result._content = False
                result.raw = RawStream(fail=stream_failure[0])
                stream_failure[0] = False
                return result
            if parsed_url.path == "/repos/acme/widgets/releases/42/assets" and method == "POST":
                file_like = kwargs["data"]
                uploaded["bytes"] = file_like.read() if hasattr(file_like, "read") else file_like
                uploaded["name"] = parsed_url.query.split("name=", 1)[1]
                return response(201, {
                    "id": 54, "name": "SHA256SUMS", "size": len(uploaded["bytes"]),
                    "digest": None, "url": "https://api.github.com/repos/acme/widgets/releases/assets/54",
                    "browser_download_url": "https://github.com/acme/widgets/releases/download/v0.2.1/SHA256SUMS",
                }, url)
            self.fail(f"unexpected SDK asset request: {method} {url}")

        with patch("requests.Session.request", new=request), \
                patch("github.Requester.time.sleep", return_value=None):
            client = release.GitHubClient("acme/widgets", "secret-token")
            record = client.release_by_id(42)
            assets = client.release_assets(record)
            wheel = assets["humanmotionlib-0.2.1-py3-none-any.whl"]
            with self.assertLogs("humanmotionlib.release", level="ERROR") as captured:
                with self.assertRaisesRegex(release.ReleaseError, r"download release asset .* failed"):
                    client.asset_bytes(wheel)
            self.assertNotIn("sensitive stream failure", "\n".join(captured.output))
            self.assertEqual(client.asset_bytes(wheel), b"wheel bytes")
            checksum = client.upload_asset(record, "SHA256SUMS", b"checksum bytes")

        self.assertEqual(uploaded, {"bytes": b"checksum bytes", "name": "SHA256SUMS"})
        self.assertEqual(checksum["name"], "SHA256SUMS")

    def test_release_history_rejects_malformed_records_instead_of_using_bootstrap(self):
        record = SimpleNamespace(id=None, tag_name="v0.2.1", draft=True)
        with self.subTest(record=record):
            sdk = SimpleNamespace(get_repo=lambda _name: SimpleNamespace(get_releases=lambda: [record]))
            client = release.GitHubClient("example/repo", "token", github=sdk)
            with self.assertRaisesRegex(release.ReleaseError, "numeric identity"):
                client.published_releases()

    def test_release_tag_push_creates_only_exact_local_tag_ref(self):
        before, candidate, remote, _wheel, _checksum = self._pushed_fixture("exact-tag-push")
        branches_before = subprocess.run(
            ["git", "--git-dir", str(remote), "for-each-ref", "--format=%(refname) %(objectname)", "refs/heads"],
            check=True, capture_output=True, text=True).stdout

        release._ensure_remote_tag(self.repo.path, "v0.2.1", candidate)

        self.assertEqual(self.repo.git("rev-parse", "refs/tags/v0.2.1^{commit}"), candidate)
        self.assertEqual(release._remote_tag_commit(self.repo.path, "v0.2.1"), candidate)
        branches_after = subprocess.run(
            ["git", "--git-dir", str(remote), "for-each-ref", "--format=%(refname) %(objectname)", "refs/heads"],
            check=True, capture_output=True, text=True).stdout
        self.assertEqual(branches_after, branches_before)
        self.assertEqual(subprocess.run(
            ["git", "--git-dir", str(remote), "for-each-ref", "--format=%(refname)", "refs/tags"],
            check=True, capture_output=True, text=True).stdout.splitlines(), ["refs/tags/v0.2.1"])

    def test_release_tag_push_reuses_same_commit_tag_and_preserves_conflict(self):
        _before, candidate, remote, _wheel, _checksum = self._pushed_fixture("reuse-tag-push")
        release._ensure_remote_tag(self.repo.path, "v0.2.1", candidate)
        release._ensure_remote_tag(self.repo.path, "v0.2.1", candidate)
        self.assertEqual(release._remote_tag_commit(self.repo.path, "v0.2.1"), candidate)

        other = self.repo.git("rev-parse", f"{candidate}^")
        subprocess.run(["git", "--git-dir", str(remote), "update-ref", "refs/tags/v0.2.1", other],
                       check=True, capture_output=True, text=True)
        with self.assertRaisesRegex(release.ReleaseError, "remote tag v0.2.1 points to a conflicting commit"):
            release._ensure_remote_tag(self.repo.path, "v0.2.1", candidate)
        self.assertEqual(subprocess.run(
            ["git", "--git-dir", str(remote), "rev-parse", "refs/tags/v0.2.1"],
            check=True, capture_output=True, text=True).stdout.strip(), other)

    def test_release_lookup_after_draft_creation_uses_release_id(self):
        draft = SimpleNamespace(id=42, tag_name="v0.2.1", draft=True, prerelease=False,
                                name="HumanMotionLib 0.2.1", body="notes", target_commitish="commit")
        repo = SimpleNamespace(get_release=lambda release_id: draft)
        client = release.GitHubClient("example/repo", "token",
                                      github=SimpleNamespace(get_repo=lambda _name: repo))
        self.assertEqual(client.release_by_id(42)["id"], 42)

    def test_rejected_release_tag_push_stops_before_release_writes(self):
        before, candidate, remote, wheel, checksum = self._pushed_fixture("reject-tag-push")
        hook = self.repo.path / ".git" / "hooks" / "pre-push"
        hook.write_text("#!/bin/sh\n"
                        f"git --git-dir='{remote}' update-ref refs/tags/v0.2.1 '{before}'\n")
        hook.chmod(0o755)
        client = FakeGitHub()

        with self.assertRaisesRegex(release.ReleaseError, "tag v0.2.1 push was rejected"):
            release.publish_pushed_release(
                self.repo.path, client, before, candidate, "refs/heads/main", "push", wheel,
                candidate, False, False, "https://example.invalid/actions/runs/600", checksum)

        self.assertIsNone(client.release, "a rejected tag push must precede and prevent draft creation")
        self.assertEqual(subprocess.run(
            ["git", "--git-dir", str(remote), "rev-parse", "refs/tags/v0.2.1"],
            check=True, capture_output=True, text=True).stdout.strip(), before)

    def test_release_intent_is_an_explicit_main_push_version_increase(self):
        before = self.repo.base
        self.assertFalse(release.release_intent(self.repo.path, before, before,
                                                ref="refs/heads/main", event="push")["eligible"])
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.1"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.1"\nsource = { editable = "." }\n')
        bumped = self.repo.commit("author version bump")
        intent = release.release_intent(self.repo.path, before, bumped,
                                        ref="refs/heads/main", event="push")
        self.assertTrue(intent["eligible"], intent)
        self.assertEqual(intent["version"], "0.2.1")
        self.assertEqual(intent["source_sha"], bumped)

    def test_intent_history_api_failure_fails_publish_decision_with_diagnostic(self):
        before = self.repo.base
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.1"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.1"\nsource = { editable = "." }\n')
        after = self.repo.commit("version bump")
        output_path = self.root / "github-output"
        args = ["release.py", "intent", "--before", before, "--after", after,
                "--event-after", after, "--ref", "refs/heads/main", "--event", "push",
                "--repo", str(self.repo.path), "--repository", "example/repo",
                "--token", "token", "--github-output", str(output_path)]
        stdout = StringIO()
        with patch.object(sys, "argv", args), patch.object(
                release, "_client_from_args", return_value=FakeGitHub()), patch.object(
                release, "_latest_boundary", side_effect=release.ReleaseError("GitHub API 503")), \
                redirect_stdout(stdout):
            status = release._main()
        self.assertEqual(status, 2)
        self.assertIn("cannot verify published history: GitHub API 503", stdout.getvalue())
        self.assertIn("eligible=false", output_path.read_text())

    def test_multi_commit_push_uses_final_commit_and_archive_alone_is_not_intent(self):
        before = self.repo.base
        archive_only = self.repo.archive("accepted")
        no_bump = release.release_intent(self.repo.path, before, archive_only,
                                         ref="refs/heads/main", event="push")
        self.assertFalse(no_bump["eligible"])
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.1"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.1"\nsource = { editable = "." }\n')
        bump = self.repo.commit("version increase")
        self.repo.write("README.md", "final pushed snapshot\n")
        final = self.repo.commit("follow-up in same push")
        intent = release.release_intent(self.repo.path, before, final,
                                        ref="refs/heads/main", event="push")
        self.assertTrue(intent["eligible"], intent)
        self.assertEqual(intent["source_sha"], final)
        self.assertEqual(intent["version"], "0.2.1")
        self.assertNotEqual(intent["source_sha"], bump)

    def test_release_intent_rejects_same_lower_invalid_initial_nonmain_and_published(self):
        before = self.repo.base
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.1"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.1"\nsource = { editable = "." }\n')
        bumped = self.repo.commit("version increase")
        self.assertFalse(release.release_intent(self.repo.path, "0" * 40, bumped,
                                                 ref="refs/heads/main", event="push")["eligible"])
        initial = release.release_intent(self.repo.path, "0" * 40, bumped,
                                         ref="refs/heads/main", event="push")
        self.assertIn("initial push", initial["reason"])
        self.assertFalse(release.release_intent(self.repo.path, before, bumped,
                                                 ref="refs/heads/feature", event="push")["eligible"])
        self.assertFalse(release.release_intent(self.repo.path, before, bumped,
                                                 ref="refs/heads/main", event="pull_request")["eligible"])
        self.assertFalse(release.release_intent(self.repo.path, before, bumped,
                                                 ref="refs/heads/main", event="push",
                                                 published_version="0.2.1")["eligible"])
        self.assertFalse(release.release_intent(self.repo.path, before, bumped,
                                                 ref="refs/heads/main", event="push",
                                                 published_version="0.2.2")["eligible"])
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.0"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.0"\nsource = { editable = "." }\n')
        lowered = self.repo.commit("downgrade")
        self.assertFalse(release.release_intent(self.repo.path, bumped, lowered,
                                                 ref="refs/heads/main", event="push")["eligible"])

    def test_release_intent_rejects_invalid_declared_version_metadata(self):
        before = self.repo.base
        for invalid in ("1.0.0", "0.02.1", "0.2.01", "0.2.1rc1"):
            with self.subTest(version=invalid):
                self.repo.write("pyproject.toml", f'[project]\nname = "humanmotionlib"\nversion = "{invalid}"\n')
                candidate = self.repo.commit(f"invalid version {invalid}")
                intent = release.release_intent(self.repo.path, before, candidate,
                                                ref="refs/heads/main", event="push")
                self.assertFalse(intent["eligible"])

    def test_release_intent_rejects_force_delete_and_event_sha_mismatch(self):
        before = self.repo.base
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.1"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.1"\nsource = { editable = "." }\n')
        bumped = self.repo.commit("version increase")
        self.assertFalse(release.release_intent(self.repo.path, before, bumped,
                                                 ref="refs/heads/main", event="push",
                                                 forced=True)["eligible"])
        self.assertFalse(release.release_intent(self.repo.path, before, bumped,
                                                 ref="refs/heads/main", event="push",
                                                 deleted=True)["eligible"])
        self.assertFalse(release.release_intent(self.repo.path, before, bumped,
                                                 ref="refs/heads/main", event="push",
                                                 event_after=before)["eligible"])
        self.assertFalse(release.release_intent(self.repo.path, before, "0" * 40,
                                                 ref="refs/heads/main", event="push")["eligible"])

    def test_unpublished_legacy_reservation_does_not_advance_bootstrap_or_drop_archives(self):
        bootstrap = self.repo.base
        legacy_reservation = self._reserved_candidate()
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.2"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.2"\nsource = { editable = "." }\n')
        later_acceptance = self.repo.archive("accepted-after-reservation")
        candidate = self.repo.git("rev-parse", "HEAD")
        client = FakeGitHub()
        boundary, version = release._latest_boundary(self.repo.path, client)
        self.assertEqual((boundary, version), (bootstrap, "0.2.0"))
        plan = release.build_pushed_release_plan(self.repo.path, boundary, candidate, "0.2.2")
        self.assertEqual(plan["archives"], [
            {"id": "release-me", "acceptance_commit": self.repo.git("rev-parse", f"{legacy_reservation}^1")},
            {"id": "accepted-after-reservation", "acceptance_commit": later_acceptance},
        ])

    def test_published_push_release_becomes_boundary_without_reservation_trailers(self):
        self.repo.bootstrap_config()
        prior = self.repo.base
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.1"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.1"\nsource = { editable = "." }\n')
        acceptance = self.repo.archive("accepted-after-bootstrap")
        candidate = self.repo.git("rev-parse", "HEAD")
        plan = release.build_pushed_release_plan(self.repo.path, prior, candidate, "0.2.1")
        self.assertEqual(plan["archives"], [{"id": "accepted-after-bootstrap", "acceptance_commit": acceptance}])
        wheel, checksum_path = self._wheel("humanmotionlib-0.2.1-py3-none-any.whl", "0.2.1")
        checksum = hashlib.sha256(wheel.read_bytes()).hexdigest()
        client = FakeGitHub()
        notes = release.format_release_notes(plan, candidate, "https://example.invalid/actions/runs/7")
        notes += f"Checked wheel SHA-256: `{checksum}`\n"
        self.repo.git("tag", "v0.2.1", candidate)
        client.release = {
            "id": 7, "tag_name": "v0.2.1", "target_commitish": candidate,
            "name": "HumanMotionLib 0.2.1", "body": notes, "draft": False,
            "assets": {}, "asset_bytes": {},
        }
        for name, data in ((wheel.name, wheel.read_bytes()),
                           ("SHA256SUMS", f"{checksum}  {wheel.name}\n".encode("ascii"))):
            client.release["asset_bytes"][name] = data
            client.release["assets"][name] = {
                "name": name, "digest": f"sha256:{hashlib.sha256(data).hexdigest()}",
            }
        self.assertEqual(release._latest_boundary(self.repo.path, client), (candidate, "0.2.1"))
        intent = release.release_intent(self.repo.path, prior, candidate,
                                        ref="refs/heads/main", event="push",
                                        published_version="0.2.1")
        self.assertFalse(intent["eligible"])

    def test_successive_push_releases_choose_highest_version_even_when_api_order_is_oldest_first(self):
        self.repo.bootstrap_config()
        first_before = self.repo.base
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.1"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.1"\nsource = { editable = "." }\n')
        first_archive = self.repo.archive("first-release-change")
        first = self.repo.git("rev-parse", "HEAD")
        first_plan = release.build_pushed_release_plan(self.repo.path, first_before, first, "0.2.1")
        client = FakeGitHub()
        first_record = self._published_push_record(client, first_plan, first, "0.2.1", 101)
        self.repo.git("tag", "v0.2.1", first)

        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.2"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.2"\nsource = { editable = "." }\n')
        second_archive = self.repo.archive("second-release-change")
        second = self.repo.git("rev-parse", "HEAD")
        second_plan = release.build_pushed_release_plan(self.repo.path, first, second, "0.2.2")
        second_record = self._published_push_record(client, second_plan, second, "0.2.2", 102)
        self.repo.git("tag", "v0.2.2", second)
        # GitHub's published-release API order is not a semantic version guarantee.
        client.published_records = [first_record, second_record]
        self.assertEqual(release._latest_boundary(self.repo.path, client), (second, "0.2.2"))
        self.assertEqual(first_plan["archives"], [{"id": "first-release-change", "acceptance_commit": first_archive}])
        self.assertEqual(second_plan["archives"], [{"id": "second-release-change", "acceptance_commit": second_archive}])

    def test_latest_boundary_does_not_revalidate_historical_release_notes(self):
        self.repo.bootstrap_config()
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.1"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.1"\nsource = { editable = "." }\n')
        acceptance = self.repo.archive("accepted")
        candidate = self.repo.git("rev-parse", "HEAD")
        # This is an ancestor with the old version, but it was never published.
        plan = release.build_pushed_release_plan(self.repo.path, self.repo.base, candidate, "0.2.1")
        client = FakeGitHub()
        published = self._published_push_record(client, plan, candidate, "0.2.1", 250)
        published["body"] = published["body"].replace(
            f"Previous release boundary: `{self.repo.base}`",
            f"Previous release boundary: `{acceptance}`")
        client.published_records = [published]
        self.repo.git("tag", "v0.2.1", candidate)
        self.assertEqual(release._latest_boundary(self.repo.path, client), (candidate, "0.2.1"))

    def test_racing_stale_candidate_fails_closed_after_higher_push_release_publishes(self):
        self.repo.bootstrap_config()
        before = self.repo.base
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.1"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.1"\nsource = { editable = "." }\n')
        self.repo.archive("first")
        stale_candidate = self.repo.git("rev-parse", "HEAD")
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.2"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.2"\nsource = { editable = "." }\n')
        self.repo.archive("second")
        current = self.repo.git("rev-parse", "HEAD")
        plan = release.build_pushed_release_plan(self.repo.path, before, current, "0.2.2")
        client = FakeGitHub()
        published = self._published_push_record(client, plan, current, "0.2.2", 201)
        client.published_records = [published]
        self.repo.git("tag", "v0.2.2", current)
        wheel, checksum = self._wheel("humanmotionlib-0.2.1-py3-none-any.whl", "0.2.1")
        with self.assertRaisesRegex(release.ReleaseError, "already published or superseded"):
            release.publish_pushed_release(self.repo.path, client, before, stale_candidate,
                                           "refs/heads/main", "push", wheel, stale_candidate,
                                           False, False, "https://example.invalid/actions/runs/199", checksum)
        self.assertEqual(set(published["assets"]), {"humanmotionlib-0.2.2-py3-none-any.whl", "SHA256SUMS"})
        self.assertIsNone(client.release, "stale candidate must not create a draft")

    def test_publish_pushed_release_path_checks_artifact_and_remote_tag_end_to_end(self):
        before, candidate, remote, wheel, checksum = self._pushed_fixture("positive")
        client = FakeGitHub()
        client.detached_release_reads = True
        client.tag_exists_for_create = lambda tag: release._remote_tag_commit(self.repo.path, tag) == candidate
        def assert_tag_precedes_draft(_item):
            self.assertEqual(release._remote_tag_commit(self.repo.path, "v0.2.1"), candidate)
            # GitHub may retain this field's default branch value when the tag
            # already exists; the pushed tag is the release identity.
            _item["target_commitish"] = "main"
        client.on_create_release = assert_tag_precedes_draft
        result = release.publish_pushed_release(
            self.repo.path, client, before, candidate, "refs/heads/main", "push", wheel,
            candidate, False, False, "https://example.invalid/actions/runs/601", checksum)
        self.assertTrue(result["published"])
        self.assertEqual(client.release["tag_name"], "v0.2.1")
        self.assertTrue(client.release_by_id_calls, "drafts are re-read using their release ID")
        self.assertFalse(client.release["draft"])
        self.assertEqual(self.repo.git("rev-parse", "refs/tags/v0.2.1"), candidate)
        self.assertEqual(set(client.release["assets"]), {wheel.name, "SHA256SUMS"})
        self.assertEqual(release._latest_boundary(self.repo.path, client), (candidate, "0.2.1"))

    def test_publish_stops_when_fresh_release_read_changes_tag_to_untagged(self):
        before, candidate, _remote, wheel, checksum = self._pushed_fixture("untagged-readback")
        client = FakeGitHub()
        client.on_read_by_id = lambda record: record.update(tag_name="untagged-sdk-response")

        with self.assertRaisesRegex(
            release.ReleaseError,
            r"release 1 tag mismatch: expected 'v0\.2\.1', GitHub returned 'untagged-sdk-response'",
        ):
            release.publish_pushed_release(
                self.repo.path, client, before, candidate, "refs/heads/main", "push", wheel,
                candidate, False, False, "https://example.invalid/actions/runs/611", checksum)

        self.assertTrue(client.release["draft"], "a conflicting fresh read must never publish the draft")
        self.assertEqual(client.release["tag_name"], "v0.2.1")
        self.assertEqual(set(client.release["assets"]), set(),
                         "a conflicting ID read must stop before any asset upload")

    def test_publish_stops_before_checksum_when_second_id_read_changes_to_untagged(self):
        before, candidate, _remote, wheel, checksum = self._pushed_fixture("untagged-second-read")
        client = FakeGitHub()
        reads = 0

        def change_tag_on_second_read(record):
            nonlocal reads
            reads += 1
            if reads == 2:
                record["tag_name"] = "untagged-sdk-response"

        client.on_read_by_id = change_tag_on_second_read
        with self.assertRaisesRegex(
            release.ReleaseError,
            r"release 1 tag mismatch: expected 'v0\.2\.1', GitHub returned 'untagged-sdk-response'",
        ):
            release.publish_pushed_release(
                self.repo.path, client, before, candidate, "refs/heads/main", "push", wheel,
                candidate, False, False, "https://example.invalid/actions/runs/612", checksum)

        self.assertEqual(reads, 2)
        self.assertTrue(client.release["draft"])
        self.assertEqual(set(client.release["assets"]), {wheel.name},
                         "conflicting second read must stop before SHA256SUMS upload")

    def test_publish_stops_before_wheel_when_draft_update_response_changes_identity(self):
        before, candidate, _remote, wheel, checksum = self._pushed_fixture("untagged-update-response")
        client = FakeGitHub()
        client.on_update_release = lambda record: record.update(tag_name="untagged-update-response")
        with self.assertRaisesRegex(
            release.ReleaseError,
            r"release 1 tag mismatch: expected 'v0\.2\.1', GitHub returned 'untagged-update-response'",
        ):
            release.publish_pushed_release(
                self.repo.path, client, before, candidate, "refs/heads/main", "push", wheel,
                candidate, False, False, "https://example.invalid/actions/runs/613", checksum)
        self.assertEqual(client.release["assets"], {},
                         "an update response with a conflicting tag must stop before the wheel upload")

    def test_publish_pushed_release_uses_only_wheel_filename_and_checksum(self):
        before, candidate, remote, wheel, checksum = self._pushed_fixture("opaque-wheel")
        wheel.write_bytes(b"wheel bytes are consumed as the tested artifact")
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
        checksum.write_text(f"{digest}  {wheel.name}\n", encoding="ascii")
        client = FakeGitHub()

        result = release.publish_pushed_release(
            self.repo.path, client, before, candidate, "refs/heads/main", "push", wheel,
            candidate, False, False, "https://example.invalid/actions/runs/606", checksum)

        self.assertTrue(result["published"])
        self.assertEqual(client.release["asset_bytes"][wheel.name], wheel.read_bytes())
        self.assertEqual(client.release["asset_bytes"]["SHA256SUMS"],
                         f"{digest}  {wheel.name}\n".encode("ascii"))

    def test_publish_pushed_release_resumes_after_tag_and_draft_with_same_checked_wheel(self):
        before, candidate, remote, wheel, checksum = self._pushed_fixture("tag-draft-retry")
        client = FakeGitHub(fail_stage="after-draft-create")
        with self.assertRaisesRegex(release.ReleaseError, "simulated lost draft creation response"):
            release.publish_pushed_release(
                self.repo.path, client, before, candidate, "refs/heads/main", "push", wheel,
                candidate, False, False, "https://example.invalid/actions/runs/607", checksum)

        self.assertEqual(release._remote_tag_commit(self.repo.path, "v0.2.1"), candidate)
        self.assertTrue(client.release["draft"])
        result = release.publish_pushed_release(
            self.repo.path, client, before, candidate, "refs/heads/main", "push", wheel,
            candidate, False, False, "https://example.invalid/actions/runs/607", checksum)

        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
        self.assertTrue(result["published"])
        self.assertEqual(result["wheel_sha256"], digest)
        self.assertEqual(client.release["asset_bytes"][wheel.name], wheel.read_bytes())
        self.assertEqual(client.release["asset_bytes"]["SHA256SUMS"],
                         f"{digest}  {wheel.name}\n".encode("ascii"))
        self.assertEqual(release._remote_tag_commit(self.repo.path, "v0.2.1"), candidate)

    def test_publish_pushed_release_does_not_publish_if_remote_tag_races_to_wrong_target(self):
        before, candidate, remote, wheel, checksum = self._pushed_fixture("tag-race")
        subprocess.run(["git", "--git-dir", str(remote), "update-ref", "refs/tags/v0.2.1", before],
                       check=True, capture_output=True, text=True)
        client = FakeGitHub()
        with self.assertRaisesRegex(release.ReleaseError, "remote tag v0.2.1 points to a conflicting commit"):
            release.publish_pushed_release(
                self.repo.path, client, before, candidate, "refs/heads/main", "push", wheel,
                candidate, False, False, "https://example.invalid/actions/runs/602", checksum)
        self.assertIsNone(client.release, "conflicting remote tag must stop before release writes")

    def test_publish_pushed_release_rechecks_remote_tag_after_upload_before_publishing(self):
        before, candidate, remote, wheel, checksum = self._pushed_fixture("tag-moves-during-upload")
        client = FakeGitHub()

        def move_tag_after_wheel_upload(name):
            if name == wheel.name:
                subprocess.run(["git", "--git-dir", str(remote), "update-ref",
                                "refs/tags/v0.2.1", before], check=True, capture_output=True, text=True)

        client.on_upload_asset = move_tag_after_wheel_upload
        with self.assertRaisesRegex(release.ReleaseError,
                                    "remote tag v0.2.1 does not target the checked commit"):
            release.publish_pushed_release(
                self.repo.path, client, before, candidate, "refs/heads/main", "push", wheel,
                candidate, False, False, "https://example.invalid/actions/runs/608", checksum)
        self.assertTrue(client.release["draft"], "a moved tag must leave the release unpublished")
        self.assertEqual(release._remote_tag_commit(self.repo.path, "v0.2.1"), before)

    def test_same_target_tag_created_after_managed_draft_is_verified_without_rewrite(self):
        before, candidate, remote, wheel, checksum = self._pushed_fixture("same-target-tag-race")
        subprocess.run(["git", "--git-dir", str(remote), "update-ref", "refs/tags/v0.2.1", candidate],
                       check=True, capture_output=True, text=True)
        client = FakeGitHub()
        result = release.publish_pushed_release(
            self.repo.path, client, before, candidate, "refs/heads/main", "push", wheel,
            candidate, False, False, "https://example.invalid/actions/runs/603", checksum)
        self.assertTrue(result["published"])
        self.assertFalse(client.release["draft"])
        self.assertEqual(release._remote_tag_commit(self.repo.path, "v0.2.1"), candidate,
                         "matching existing ref is reused without being rewritten")
        self.assertEqual(self.repo.git("rev-parse", "refs/tags/v0.2.1"), candidate)

    def test_publish_pushed_release_creates_tag_before_draft_and_keeps_mutated_draft_unpublished(self):
        before, candidate, remote, wheel, checksum = self._pushed_fixture("draft-mutated-before-tag")
        client = FakeGitHub()

        def mutate_after_wheel_upload(name):
            if name == wheel.name:
                client.release["body"] += "\nextra archive attribution\n"

        client.on_upload_asset = mutate_after_wheel_upload
        client.detached_release_reads = True
        with self.assertRaisesRegex(release.ReleaseError, "exact boundary and accepted-change plan"):
            release.publish_pushed_release(
                self.repo.path, client, before, candidate, "refs/heads/main", "push", wheel,
                candidate, False, False, "https://example.invalid/actions/runs/604", checksum)
        self.assertTrue(client.release["draft"], "changed draft must remain unpublished")
        self.assertEqual(release._remote_tag_commit(self.repo.path, "v0.2.1"), candidate,
                         "the local Git tag is pushed before creating a draft")
        self.assertTrue(client.release["draft"], "changed draft must remain unpublished")
        self.assertEqual(set(client.release["assets"]), {wheel.name, "SHA256SUMS"})

    def _pushed_fixture(self, name):
        self.repo.bootstrap_config()
        before = self.repo.base
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.1"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.1"\nsource = { editable = "." }\n')
        self.repo.archive(f"accepted-{name}")
        candidate = self.repo.git("rev-parse", "HEAD")
        remote = self.root / f"{name}.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True, text=True)
        subprocess.run(["git", "--git-dir", str(remote), "symbolic-ref", "HEAD", "refs/heads/main"], check=True)
        self.repo.git("remote", "add", "origin", str(remote))
        self.repo.git("push", "-q", "-u", "origin", "main")
        wheel, checksum = self._wheel("humanmotionlib-0.2.1-py3-none-any.whl", "0.2.1")
        return before, candidate, remote, wheel, checksum

    def test_same_target_bare_tag_and_wrong_run_draft_are_rejected_without_mutation(self):
        candidate = self._reserved_candidate()
        wheel, checksum = self._wheel()
        self.repo.git("tag", "v0.2.1", candidate)
        client = FakeGitHub()
        with self.assertRaisesRegex(release.ReleaseError, "bare tag"):
            release.publish_release(self.repo.path, client, candidate, wheel,
                                    "https://example.invalid/actions/runs/302", checksum)
        self.assertIsNone(client.release)
        self.repo.git("tag", "-d", "v0.2.1")

        draft_client = FakeGitHub()
        plan = release._load_reserved_candidate(self.repo.path, candidate)
        notes = release.format_release_notes(plan, candidate, "https://example.invalid/actions/runs/301")
        wheel_hash = hashlib.sha256(wheel.read_bytes()).hexdigest()
        notes += f"Checked wheel SHA-256: `{wheel_hash}`\n"
        draft_client.release = {
            "id": 303, "tag_name": "v0.2.1", "target_commitish": candidate,
            "name": "HumanMotionLib 0.2.1", "body": notes, "draft": True,
            "assets": {}, "asset_bytes": {},
        }
        with self.assertRaisesRegex(release.ReleaseError, "different qualifying workflow run"):
            release.publish_release(self.repo.path, draft_client, candidate, wheel,
                                    "https://example.invalid/actions/runs/302", checksum)
        self.assertEqual(draft_client.release["body"], notes)
        self.assertEqual(draft_client.release["assets"], {})

    def test_valid_notes_cannot_adopt_draft_for_another_commit(self):
        candidate = self._reserved_candidate()
        wheel, checksum = self._wheel()
        plan = release._load_reserved_candidate(self.repo.path, candidate)
        notes = release.format_release_notes(plan, candidate, "https://example.invalid/actions/runs/401")
        notes += f"Checked wheel SHA-256: `{hashlib.sha256(wheel.read_bytes()).hexdigest()}`\n"
        unrelated_target = self.repo.base
        client = FakeGitHub()
        client.release = {
            "id": 402, "tag_name": "v0.2.1", "target_commitish": unrelated_target,
            "name": "HumanMotionLib 0.2.1", "body": notes, "draft": True,
            "assets": {}, "asset_bytes": {},
        }
        with self.assertRaisesRegex(release.ReleaseError, "targets a conflicting commit"):
            release.publish_release(self.repo.path, client, candidate, wheel,
                                    "https://example.invalid/actions/runs/401", checksum)
        self.assertEqual(client.release["target_commitish"], unrelated_target)
        self.assertEqual(client.release["assets"], {})

    def test_uploaded_wheel_draft_requires_exact_current_attribution_notes(self):
        candidate = self._reserved_candidate()
        wheel, checksum_file = self._wheel()
        checksum = hashlib.sha256(wheel.read_bytes()).hexdigest()
        plan = release._load_reserved_candidate(self.repo.path, candidate)
        workflow = "https://example.invalid/actions/runs/501"
        exact_notes = release.format_release_notes(plan, candidate, workflow)
        exact_notes += f"Checked wheel SHA-256: `{checksum}`\n"
        stale = FakeGitHub()
        stale.release = self._draft_with_uploaded_wheel(candidate, wheel, exact_notes +
            f"- `stale-extra` (acceptance `{self.repo.base}`)\n"
            f"Previous release boundary: `{self.repo.base}`\n")
        with self.assertRaisesRegex(release.ReleaseError, "exact boundary and accepted-change plan"):
            release.publish_release(self.repo.path, stale, candidate, wheel, workflow, checksum_file)
        self.assertEqual(set(stale.release["assets"]), {wheel.name})
        self.assertEqual(stale.release["asset_bytes"][wheel.name], wheel.read_bytes())

        matching = FakeGitHub()
        matching.release = self._draft_with_uploaded_wheel(candidate, wheel, exact_notes)
        result = release.publish_release(self.repo.path, matching, candidate, wheel, workflow, checksum_file)
        self.assertFalse(result["already_complete"])
        self.assertEqual(set(matching.release["assets"]), {wheel.name, "SHA256SUMS"})

    def test_publication_revalidates_draft_notes_and_target_after_asset_upload(self):
        for mode in ("notes", "target"):
            with self.subTest(mode=mode):
                if mode == "target":
                    self.repo = SyntheticRepository(self.root / "repo-target-mutation")
                candidate = self._reserved_candidate()
                wheel, checksum = self._wheel()
                client = FakeGitHub()

                def mutate_after_wheel_upload(name):
                    if name != wheel.name:
                        return
                    if mode == "notes":
                        client.release["body"] += "\nextra stale attribution\n"
                    else:
                        client.release["target_commitish"] = self.repo.base

                client.on_upload_asset = mutate_after_wheel_upload
                expected = "exact boundary and accepted-change plan" if mode == "notes" else "conflicting commit"
                with self.assertRaisesRegex(release.ReleaseError, expected):
                    release.publish_release(self.repo.path, client, candidate, wheel,
                                            "https://example.invalid/actions/runs/701", checksum)
                self.assertTrue(client.release["draft"], "mutated publication evidence must stay unpublished")

    def _draft_with_uploaded_wheel(self, candidate, wheel, body):
        wheel_bytes = wheel.read_bytes()
        return {
            "id": 1, "tag_name": "v0.2.1", "target_commitish": candidate,
            "name": "HumanMotionLib 0.2.1", "body": body, "draft": True,
            "assets": {wheel.name: {
                "name": wheel.name,
                "digest": f"sha256:{hashlib.sha256(wheel_bytes).hexdigest()}",
            }},
            "asset_bytes": {wheel.name: wheel_bytes},
        }

    def _published_push_record(self, client, plan, candidate, version, release_id):
        wheel, _ = self._wheel(f"humanmotionlib-{version}-py3-none-any.whl", version)
        checksum = hashlib.sha256(wheel.read_bytes()).hexdigest()
        workflow_url = f"https://example.invalid/actions/runs/{release_id}"
        body = release.format_release_notes(plan, candidate, workflow_url)
        body += f"Checked wheel SHA-256: `{checksum}`\n"
        wheel_name = wheel.name
        checksum_bytes = f"{checksum}  {wheel_name}\n".encode("ascii")
        record = {
            "id": release_id, "tag_name": f"v{version}", "target_commitish": candidate,
            "name": f"HumanMotionLib {version}", "body": body, "draft": False,
            "assets": {}, "asset_bytes": {},
        }
        for name, data in ((wheel_name, wheel.read_bytes()), ("SHA256SUMS", checksum_bytes)):
            record["asset_bytes"][name] = data
            record["assets"][name] = {
                "name": name, "digest": f"sha256:{hashlib.sha256(data).hexdigest()}",
            }
        return record




    def test_latest_boundary_uses_published_tag_without_revalidating_old_assets_or_notes(self):
        candidate = self._reserved_candidate()
        wheel, checksum = self._wheel()
        client = FakeGitHub()
        release.publish_release(self.repo.path, client, candidate, wheel,
                                "https://example.invalid/run/complete", checksum)
        self.repo.git("tag", "v0.2.1", candidate)
        client.release["body"] = "Release automation identity: humanmotionlib-versioned-release/v1\nlegacy notes"
        client.release["assets"] = {}
        client.release["asset_bytes"] = {}
        self.assertEqual(release._latest_boundary(self.repo.path, client), (candidate, "0.2.1"))
        (self.repo.path / "tools/release-config.toml").unlink()
        with self.assertRaisesRegex(release.ReleaseError, "bootstrap configuration"):
            release._latest_boundary(self.repo.path, client)

    def test_latest_boundary_ignores_unmanaged_and_prerelease_releases(self):
        self.repo.bootstrap_config()
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.1"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.1"\nsource = { editable = "." }\n')
        managed = self.repo.commit("managed version bump")
        self.repo.git("tag", "v0.2.1", managed)
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.2"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.2"\nsource = { editable = "." }\n')
        unrelated = self.repo.commit("manual release candidate")
        self.repo.git("tag", "v0.2.2", unrelated)
        client = FakeGitHub()
        client.published_records = [
            {"draft": False, "tag_name": "v0.2.2", "body": "manual release"},
            {"draft": False, "prerelease": True, "tag_name": "v0.2.3-rc.1", "body":
             "Release automation identity: humanmotionlib-versioned-release/v1"},
            {"draft": False, "tag_name": "v0.2.1", "body":
             "Release automation identity: humanmotionlib-versioned-release/v1"},
        ]
        self.assertEqual(release._latest_boundary(self.repo.path, client), (managed, "0.2.1"))


    def _reserved_candidate(self):
        self.repo.bootstrap_config()
        acceptance = self.repo.archive("release-me")
        self.repo.write("pyproject.toml", '[project]\nname = "humanmotionlib"\nversion = "0.2.1"\n')
        self.repo.write("uv.lock", '[[package]]\nname = "humanmotionlib"\nversion = "0.2.1"\nsource = { editable = "." }\n')
        self.repo.git("add", "pyproject.toml", "uv.lock")
        subprocess.run([
            "git", "commit", "-m", "chore(release): 0.2.1",
            "--trailer", "HML-Release-Version: 0.2.1",
            "--trailer", f"HML-Release-Boundary: {self.repo.base}",
            "--trailer", f"HML-Release-Input: {acceptance}",
            "--trailer", f"HML-Release-Change: release-me {acceptance}",
        ], cwd=self.repo.path, check=True, capture_output=True, text=True)
        return self.repo.git("rev-parse", "HEAD")

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
        }
        with self.assertRaisesRegex(release.ReleaseError, "release notes"):
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
        }
        for name, data in ((wheel.name, wheel.read_bytes()),
                           ("SHA256SUMS", f"{checksum_value}  {wheel.name}\n".encode("ascii"))):
            completed.release["asset_bytes"][name] = data
            completed.release["assets"][name] = {
                "name": name,
                "digest": f"sha256:{hashlib.sha256(data).hexdigest()}",
            }
        with self.assertRaisesRegex(release.ReleaseError, "release notes"):
            release.publish_release(self.repo.path, completed, candidate, wheel,
                                    "https://example.invalid/run/unrelated", checksum)


class FakeGitHub:
    def __init__(self, fail_once_asset=None, fail_stage=None):
        self.release = None
        self.next_id = 1
        self.fail_once_asset = fail_once_asset
        self.fail_stage = fail_stage
        self.published_records = None
        self.on_create_release = None
        self.detached_release_reads = False
        self.tag_exists_for_create = None
        self.release_by_id_calls = []
        self.on_upload_asset = None
        self.on_read_by_id = None
        self.on_update_release = None

    def latest_release(self):
        if self.release is not None and self.release.get("draft") is False:
            return self.release
        return None

    def published_releases(self):
        if self.published_records is not None:
            return self.published_records
        release_record = self.latest_release()
        return [] if release_record is None else [release_record]

    def release_for_tag(self, tag):
        if self.release is not None and self.release["tag_name"] == tag:
            return copy.deepcopy(self.release) if self.detached_release_reads else self.release
        return None

    def release_by_id(self, release_id):
        self.release_by_id_calls.append(release_id)
        if self.release is not None and self.release.get("id") == release_id:
            result = copy.deepcopy(self.release) if self.detached_release_reads or self.on_read_by_id else self.release
            if self.on_read_by_id is not None:
                self.on_read_by_id(result)
            return result
        return None

    def release_assets(self, release_record):
        return release_record["assets"]

    def asset_bytes(self, asset):
        if self.published_records is not None:
            for record in self.published_records:
                if asset["name"] in record["asset_bytes"] and asset in record["assets"].values():
                    return record["asset_bytes"][asset["name"]]
        return self.release["asset_bytes"][asset["name"]]

    def create_release(self, tag, candidate, title, body):
        if self.fail_stage == "draft-create":
            self.fail_stage = None
            raise release.ReleaseError("simulated denied GitHub draft write (403)")
        payload = {
            "tag_name": tag, "target_commitish": candidate, "name": title,
            "body": body, "draft": True, "prerelease": False,
        }
        self.release = {
            **payload, "id": self.next_id, "assets": {}, "asset_bytes": {},
        }
        if self.tag_exists_for_create is not None and not self.tag_exists_for_create(tag):
            self.release["tag_name"] = "untagged-temporary"
        self.next_id += 1
        if self.on_create_release is not None:
            self.on_create_release(self.release)
        if self.fail_stage == "after-draft-create":
            self.fail_stage = None
            raise release.ReleaseError("simulated lost draft creation response")
        return self.release

    def update_release(self, release_record, *, body, draft):
        if draft is False and self.fail_stage == "before-final-publish":
            self.fail_stage = None
            raise release.ReleaseError("simulated denied final publication (403)")
        self.release.update(body=body, draft=draft)
        if self.on_update_release is not None:
            self.on_update_release(self.release)
        if draft is False and self.fail_stage == "after-final-publish":
            self.fail_stage = None
            raise release.ReleaseError("simulated lost final publication response")
        return self.release

    def upload_asset(self, release_record, name, data):
        if self.fail_once_asset == name:
            self.fail_once_asset = None
            raise release.ReleaseError("simulated interrupted asset upload")
        self.release["asset_bytes"][name] = data
        self.release["assets"][name] = {
            "name": name,
            "digest": f"sha256:{hashlib.sha256(data).hexdigest()}",
        }
        if self.on_upload_asset is not None:
            self.on_upload_asset(name)
        return self.release["assets"][name]


if __name__ == "__main__":
    unittest.main()
