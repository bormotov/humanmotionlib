# SPDX-License-Identifier: Apache-2.0
"""Synthetic Git-history tests for automatic 0.x release selection."""

from __future__ import annotations

import importlib.util
import hashlib
import copy
from io import BytesIO
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
import zipfile
from urllib.error import HTTPError

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

    def test_draft_lookup_uses_release_list_when_tag_endpoint_returns_not_found(self):
        draft = {"id": 9, "tag_name": "v0.2.1", "draft": True}
        calls = []
        not_found_errors = []

        class Response:
            status = 200
            def __init__(self, body):
                self.body = body
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return self.body

        def opener(request, timeout):
            calls.append(request.full_url)
            if "/releases/tags/" in request.full_url:
                error = HTTPError(request.full_url, 404, "not found", {}, BytesIO(b"not found"))
                not_found_errors.append(error)
                raise error
            return Response(json.dumps([draft]).encode())

        client = release.GitHubClient("example/repo", "token", opener=opener)
        self.assertIsNone(client.request("/releases/tags/v0.2.1", allow_missing=True)[1])
        self.assertEqual(client.release_for_tag("v0.2.1"), draft)
        self.assertEqual(sum("/releases?per_page=100&page=1" in url for url in calls), 1)
        self.assertEqual(sum("/releases/tags/" in url for url in calls), 1)
        for error in not_found_errors:
            error.close()

    def test_release_history_rejects_malformed_records_instead_of_using_bootstrap(self):
        for records in ([None], [{"tag_name": "v0.2.1"}], [{"tag_name": "v0.2.1", "draft": "false"}]):
            with self.subTest(records=records):
                client = release.GitHubClient("example/repo", "token", opener=lambda *_args, **_kwargs: None)
                client.request = lambda *_args, _records=records, **_kwargs: (200, _records)
                with self.assertRaisesRegex(release.ReleaseError, "malformed release record"):
                    client.published_releases()

    def test_release_tag_creation_posts_an_exact_ref_without_force(self):
        calls = []

        class Response:
            status = 201
            def __init__(self, body):
                self.body = body
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return self.body

        sha = "a" * 40
        def opener(request, timeout):
            calls.append(request)
            return Response(json.dumps({
                "ref": "refs/tags/v0.2.1", "object": {"sha": sha, "type": "commit"},
            }).encode())

        client = release.GitHubClient("example/repo", "token", opener=opener)
        client.create_tag_ref("v0.2.1", sha)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].method, "POST")
        self.assertTrue(calls[0].full_url.endswith("/git/refs"))
        payload = json.loads(calls[0].data)
        self.assertEqual(payload, {"ref": "refs/tags/v0.2.1", "sha": sha})
        self.assertNotIn("force", payload)

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
            "upload_url": "https://uploads.github.test/releases/7/assets{?name,label}",
        }
        for name, data in ((wheel.name, wheel.read_bytes()),
                           ("SHA256SUMS", f"{checksum}  {wheel.name}\n".encode("ascii"))):
            client.release["asset_bytes"][name] = data
            client.release["assets"][name] = {
                "name": name, "digest": f"sha256:{hashlib.sha256(data).hexdigest()}",
                "url": f"https://api.github.test/assets/{name}",
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
        client.on_create_release = lambda _item: self.assertEqual(
            subprocess.run(["git", "--git-dir", str(remote), "for-each-ref", "refs/tags/v0.2.1"],
                           check=True, capture_output=True, text=True).stdout, "")
        client.on_create_tag_ref = lambda tag, sha: subprocess.run(
            ["git", "--git-dir", str(remote), "update-ref", f"refs/tags/{tag}", sha],
            check=True, capture_output=True, text=True)
        result = release.publish_pushed_release(
            self.repo.path, client, before, candidate, "refs/heads/main", "push", wheel,
            candidate, False, False, "https://example.invalid/actions/runs/601", checksum)
        self.assertTrue(result["published"])
        self.assertFalse(client.release["draft"])
        self.assertEqual(self.repo.git("rev-parse", "refs/tags/v0.2.1"), candidate)
        self.assertEqual(set(client.release["assets"]), {wheel.name, "SHA256SUMS"})
        self.assertEqual(release._latest_boundary(self.repo.path, client), (candidate, "0.2.1"))

    def test_publish_pushed_release_uses_only_wheel_filename_and_checksum(self):
        before, candidate, remote, wheel, checksum = self._pushed_fixture("opaque-wheel")
        wheel.write_bytes(b"wheel bytes are consumed as the tested artifact")
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
        checksum.write_text(f"{digest}  {wheel.name}\n", encoding="ascii")
        client = FakeGitHub()
        client.on_create_tag_ref = lambda tag, sha: subprocess.run(
            ["git", "--git-dir", str(remote), "update-ref", f"refs/tags/{tag}", sha],
            check=True, capture_output=True, text=True)

        result = release.publish_pushed_release(
            self.repo.path, client, before, candidate, "refs/heads/main", "push", wheel,
            candidate, False, False, "https://example.invalid/actions/runs/606", checksum)

        self.assertTrue(result["published"])
        self.assertEqual(client.release["asset_bytes"][wheel.name], wheel.read_bytes())
        self.assertEqual(client.release["asset_bytes"]["SHA256SUMS"],
                         f"{digest}  {wheel.name}\n".encode("ascii"))

    def test_publish_pushed_release_does_not_publish_if_remote_tag_races_to_wrong_target(self):
        before, candidate, remote, wheel, checksum = self._pushed_fixture("tag-race")
        client = FakeGitHub()
        client.on_create_release = lambda item: subprocess.run(
            ["git", "--git-dir", str(remote), "update-ref", f"refs/tags/{item['tag_name']}", before],
            check=True, capture_output=True, text=True)
        with self.assertRaisesRegex(release.ReleaseError, "does not target the checked commit"):
            release.publish_pushed_release(
                self.repo.path, client, before, candidate, "refs/heads/main", "push", wheel,
                candidate, False, False, "https://example.invalid/actions/runs/602", checksum)
        self.assertIsNotNone(client.release)
        self.assertTrue(client.release["draft"], "the raced draft must remain unpublished")
        self.assertEqual(set(client.release["assets"]), {wheel.name, "SHA256SUMS"})

    def test_same_target_tag_created_after_managed_draft_is_verified_without_rewrite(self):
        before, candidate, remote, wheel, checksum = self._pushed_fixture("same-target-tag-race")
        client = FakeGitHub()
        client.on_create_release = lambda item: subprocess.run(
            ["git", "--git-dir", str(remote), "update-ref", f"refs/tags/{item['tag_name']}", candidate],
            check=True, capture_output=True, text=True)
        create_ref_calls = []
        client.on_create_tag_ref = lambda tag, sha: create_ref_calls.append((tag, sha))
        result = release.publish_pushed_release(
            self.repo.path, client, before, candidate, "refs/heads/main", "push", wheel,
            candidate, False, False, "https://example.invalid/actions/runs/603", checksum)
        self.assertTrue(result["published"])
        self.assertFalse(client.release["draft"])
        self.assertEqual(create_ref_calls, [], "matching existing ref is verified without being rewritten")
        self.assertEqual(self.repo.git("rev-parse", "refs/tags/v0.2.1"), candidate)

    def test_publish_pushed_release_rejects_draft_mutated_before_tag_creation(self):
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
        self.assertEqual(subprocess.run(
            ["git", "--git-dir", str(remote), "for-each-ref", "refs/tags/v0.2.1"],
            check=True, capture_output=True, text=True).stdout, "",
            "a changed draft must be rejected before creating the release ref")

    def test_publish_pushed_release_rejects_draft_mutated_during_tag_creation(self):
        before, candidate, remote, wheel, checksum = self._pushed_fixture("draft-mutated-during-tag")
        client = FakeGitHub()

        def create_ref_then_mutate_draft(tag, sha):
            subprocess.run(
                ["git", "--git-dir", str(remote), "update-ref", f"refs/tags/{tag}", sha],
                check=True, capture_output=True, text=True)
            client.release["target_commitish"] = before

        client.on_create_tag_ref = create_ref_then_mutate_draft
        client.detached_release_reads = True
        with self.assertRaisesRegex(release.ReleaseError, "conflicting commit"):
            release.publish_pushed_release(
                self.repo.path, client, before, candidate, "refs/heads/main", "push", wheel,
                candidate, False, False, "https://example.invalid/actions/runs/605", checksum)
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
            "upload_url": "https://uploads.github.test/releases/303/assets{?name,label}",
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
            "upload_url": "https://uploads.github.test/releases/402/assets{?name,label}",
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
                "url": f"https://api.github.test/assets/{wheel.name}",
            }},
            "asset_bytes": {wheel.name: wheel_bytes},
            "upload_url": "https://uploads.github.test/releases/1/assets{?name,label}",
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
            "upload_url": f"https://uploads.github.test/releases/{release_id}/assets{{?name,label}}",
        }
        for name, data in ((wheel_name, wheel.read_bytes()), ("SHA256SUMS", checksum_bytes)):
            record["asset_bytes"][name] = data
            record["assets"][name] = {
                "name": name, "digest": f"sha256:{hashlib.sha256(data).hexdigest()}",
                "url": f"https://api.github.test/assets/{release_id}/{name}",
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
            "upload_url": "https://uploads.github.test/releases/42/assets{?name,label}",
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
        self.on_create_tag_ref = None
        self.detached_release_reads = False
        self.on_upload_asset = None

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

    def create_tag_ref(self, tag, candidate):
        self.request("/git/refs", method="POST", payload={
            "ref": f"refs/tags/{tag}", "sha": candidate,
        })

    def release_assets(self, release_record):
        return release_record["assets"]

    def asset_bytes(self, asset):
        if self.published_records is not None:
            for record in self.published_records:
                if asset["name"] in record["asset_bytes"] and asset in record["assets"].values():
                    return record["asset_bytes"][asset["name"]]
        return self.release["asset_bytes"][asset["name"]]

    def request(self, path, *, method="GET", payload=None, **kwargs):
        if path == "/git/refs" and method == "POST":
            if self.on_create_tag_ref is not None:
                self.on_create_tag_ref(payload["ref"].removeprefix("refs/tags/"), payload["sha"])
            return 201, {"ref": payload["ref"], "object": {"sha": payload["sha"]}}
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
            if self.on_create_release is not None:
                self.on_create_release(self.release)
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
        if self.on_upload_asset is not None:
            self.on_upload_asset(name)
        return self.release["assets"][name]


if __name__ == "__main__":
    unittest.main()
