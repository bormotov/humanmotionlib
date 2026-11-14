# SPDX-License-Identifier: Apache-2.0
"""Version and accepted-change selection for GitHub releases.

This contributor-only tool intentionally uses Git and the Python standard
library. Release evaluation is based on archived OpenSpec changes in Git
history; canonical specification bytes select the 0.x increment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


_VERSION = re.compile(r"^0\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_ARCHIVE_PREFIX = "openspec/changes/archive/"
_SPEC_PREFIX = "openspec/specs/"


class ReleaseError(RuntimeError):
    """The repository does not contain enough consistent release evidence."""


def _git(root: Path, *args: str, text: bool = True) -> str | bytes:
    result = subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True,
        text=text, encoding="utf-8" if text else None,
    )
    return result.stdout.strip() if text else result.stdout


def _commit(root: Path, ref: str) -> str:
    return str(_git(root, "rev-parse", "--verify", f"{ref}^{{commit}}"))


def _is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant], cwd=root,
        capture_output=True,
    ).returncode == 0


def read_version_text(text: str) -> str:
    try:
        version = tomllib.loads(text)["project"]["version"]
    except (KeyError, tomllib.TOMLDecodeError) as error:
        raise ReleaseError("pyproject.toml has no valid project.version") from error
    if not isinstance(version, str) or not _VERSION.fullmatch(version):
        raise ReleaseError(f"automatic releases require a valid 0.x.y version, got {version!r}")
    return version


def version_at(root: Path, commit: str) -> str:
    content = str(_git(root, "show", f"{commit}:pyproject.toml"))
    return read_version_text(content)


def version_key(version: str) -> tuple[int, int, int]:
    if not _VERSION.fullmatch(version):
        raise ReleaseError(f"invalid release version {version!r}")
    return tuple(map(int, version.split(".")))  # type: ignore[return-value]


def release_intent(root: Path, before: str, after: str, *, ref: str,
                   event: str, published_version: str | None = None,
                   event_after: str | None = None,
                   forced: bool = False, deleted: bool = False) -> dict[str, object]:
    """Return whether this main push explicitly raises the declared version."""
    if event != "push" or ref != "refs/heads/main":
        return {"eligible": False, "reason": "release publication applies only to pushes to main"}
    if deleted:
        return {"eligible": False, "reason": "branch deletion has no release snapshot; CI is not applicable"}
    if forced:
        return {"eligible": False, "reason": "GitHub marked this as a force push; CI still runs"}
    if event_after is not None and event_after != after:
        return {"eligible": False, "reason": "push event after SHA differs from the checked SHA; CI still runs"}
    if not re.fullmatch(r"[0-9a-f]{40,64}", after):
        return {"eligible": False, "reason": "push has no checkoutable after revision"}
    if not re.fullmatch(r"[0-9a-f]{40,64}", before):
        return {"eligible": False, "reason": "initial push has no before revision; CI still runs"}
    if before == "0" * len(before):
        return {"eligible": False, "reason": "initial push has no before revision; CI still runs"}
    try:
        before_sha, after_sha = _commit(root, before), _commit(root, after)
        if before_sha != before or after_sha != after:
            return {"eligible": False, "reason": "push revisions must be full immutable commit ids"}
        if not _is_ancestor(root, before_sha, after_sha):
            return {"eligible": False, "reason": "force push or non-fast-forward history; CI still runs"}
        old, new = version_at(root, before_sha), version_at(root, after_sha)
        if version_key(new) <= version_key(old):
            return {"eligible": False, "before_version": old, "version": new,
                    "reason": f"no version increase ({old} -> {new}); CI still runs"}
        if published_version is not None and version_key(new) <= version_key(published_version):
            return {"eligible": False, "before_version": old, "version": new,
                    "published_version": published_version,
                    "reason": f"version {new} is already published or superseded by {published_version}; CI still runs"}
    except (ReleaseError, OSError, subprocess.CalledProcessError) as error:
        return {"eligible": False, "reason": f"cannot establish release intent: {error}; CI still runs"}
    return {"eligible": True, "before_sha": before_sha, "source_sha": after_sha,
            "before_version": old, "version": new,
            "reason": f"version increased from {old} to {new} on pushed commit {after_sha}"}


def bootstrap_boundary(root: Path) -> tuple[str, str]:
    config_path = root / "tools" / "release-config.toml"
    try:
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
        expected_commit = config["bootstrap_commit"]
        expected_version = config["bootstrap_version"]
    except (OSError, KeyError, tomllib.TOMLDecodeError) as error:
        raise ReleaseError(f"cannot read fixed release bootstrap configuration at {config_path}") from error
    if not isinstance(expected_commit, str) or not re.fullmatch(r"[0-9a-f]{40,64}", expected_commit):
        raise ReleaseError("bootstrap_commit must be a full lowercase Git object id")
    if not isinstance(expected_version, str) or not _VERSION.fullmatch(expected_version):
        raise ReleaseError("bootstrap_version must be a valid 0.x.y release version")
    actual_commit = _commit(root, expected_commit)
    if actual_commit != expected_commit:
        raise ReleaseError("configured bootstrap is not an immutable full commit id")
    if version_at(root, actual_commit) != expected_version:
        raise ReleaseError("fixed bootstrap commit and declared bootstrap version disagree")
    return actual_commit, expected_version


def _legacy_reservation_version(previous: str, specification_changed: bool) -> str:
    match = _VERSION.fullmatch(previous)
    if not match:
        raise ReleaseError(f"automatic releases require a valid 0.x.y version, got {previous!r}")
    minor, patch = map(int, match.groups())
    return f"0.{minor + 1}.0" if specification_changed else f"0.{minor}.{patch + 1}"


def _commits_between(root: Path, base: str, target: str) -> list[str]:
    base_sha, target_sha = _commit(root, base), _commit(root, target)
    if not _is_ancestor(root, base_sha, target_sha):
        raise ReleaseError(f"release boundary {base_sha} is not an ancestor of {target_sha}")
    return str(_git(root, "rev-list", "--reverse", "--topo-order", f"{base_sha}..{target_sha}")).splitlines()


def _archive_markers(root: Path, commit: str) -> set[str]:
    """Return archived change ids present in a repository snapshot."""
    listing = _git(root, "ls-tree", "-r", "--name-only", commit, "--", _ARCHIVE_PREFIX)
    return {path[len(_ARCHIVE_PREFIX):-len("/.openspec.yaml")]
            for path in str(listing).splitlines()
            if path.startswith(_ARCHIVE_PREFIX) and path.endswith("/.openspec.yaml")}


def _new_archives(root: Path, boundary: str, target: str) -> list[dict[str, str]]:
    """Find archives added after the boundary and still present at the target snapshot."""
    boundary_sha, target_sha = _commit(root, boundary), _commit(root, target)
    commits = _commits_between(root, boundary_sha, target_sha)
    previous = _archive_markers(root, boundary_sha)
    current = _archive_markers(root, target_sha)
    acceptance: dict[str, str] = {}
    positions = {commit: index for index, commit in enumerate(commits)}
    for commit in commits:
        snapshot = _archive_markers(root, commit)
        parent_rows = str(_git(root, "rev-list", "--parents", "-n", "1", commit)).split()
        parents = parent_rows[1:]
        inherited: set[str] = set()
        for parent in parents:
            inherited.update(_archive_markers(root, parent))
        for change_id in snapshot - inherited:
            acceptance[change_id] = commit
    new_ids = [change_id for change_id in current - previous if change_id in acceptance]
    new_ids.sort(key=lambda change_id: (positions[acceptance[change_id]], change_id))
    return [{"id": change_id, "acceptance_commit": acceptance[change_id]} for change_id in new_ids]


def _new_archive_roots(root: Path, commit: str) -> list[str]:
    """Legacy helper retained for reservation history parsing."""
    parents = str(_git(root, "rev-list", "--parents", "-n", "1", commit)).split()
    parent = parents[1] if len(parents) > 1 else "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
    changes = str(_git(root, "diff-tree", "--no-commit-id", "--name-status", "-r", "-M",
                        parent, commit))
    found: set[str] = set()
    for line in changes.splitlines():
        fields = line.split("\t")
        status = fields[0]
        paths = fields[1:]
        destination = paths[-1]
        if status[0] in {"A", "R", "C"} and destination.startswith(_ARCHIVE_PREFIX):
            relative = destination[len(_ARCHIVE_PREFIX):]
            if relative.endswith("/.openspec.yaml"):
                found.add(relative[: -len("/.openspec.yaml")])
    return sorted(found)


def _spec_inventory(root: Path, commit: str) -> dict[str, str]:
    listing = _git(root, "ls-tree", "-r", "-z", "--full-tree", commit, "--", _SPEC_PREFIX, text=False)
    assert isinstance(listing, bytes)
    inventory: dict[str, str] = {}
    for record in listing.split(b"\0"):
        if not record:
            continue
        metadata, path_bytes = record.split(b"\t", 1)
        mode_type_sha = metadata.decode("ascii").split()
        path = path_bytes.decode("utf-8")
        if len(mode_type_sha) == 3 and mode_type_sha[1] == "blob" and path.endswith("/spec.md"):
            inventory[path] = mode_type_sha[2]
    return inventory


def build_plan(root: Path, boundary: str | None, target: str) -> dict[str, object]:
    """Compute the next release from a published/bootstrap boundary to main."""
    root = root.resolve()
    if boundary is None:
        boundary, _ = bootstrap_boundary(root)
    try:
        boundary_sha, target_sha = _commit(root, boundary), _commit(root, target)
    except subprocess.CalledProcessError as error:
        raise ReleaseError("release boundary or checked push commit is missing") from error
    archives = _new_archives(root, boundary_sha, target_sha)

    before, after = _spec_inventory(root, boundary_sha), _spec_inventory(root, target_sha)
    changed_paths = sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))
    previous = version_at(root, boundary_sha)
    return {
        "boundary": boundary_sha,
        "target": target_sha,
        "previous_version": previous,
        "version": _legacy_reservation_version(previous, bool(changed_paths)) if archives else None,
        "archives": archives,
        "specification_changed": bool(changed_paths),
        "changed_specifications": changed_paths,
        "has_release": bool(archives),
    }


def build_pushed_release_plan(root: Path, boundary: str, target: str,
                              version: str,
                              previously_released_archives: set[str] | None = None) -> dict[str, object]:
    """Attribute pending archives to an authored version and exact push snapshot."""
    root = root.resolve()
    if not _VERSION.fullmatch(version):
        raise ReleaseError(f"invalid declared release version {version!r}")
    try:
        boundary_sha, target_sha = _commit(root, boundary), _commit(root, target)
    except subprocess.CalledProcessError as error:
        raise ReleaseError("release boundary or checked push commit is missing") from error
    if version_at(root, target_sha) != version:
        raise ReleaseError("declared release version does not match the checked push commit")
    archives = _new_archives(root, boundary_sha, target_sha)
    if previously_released_archives:
        archives = [archive for archive in archives
                    if archive["id"] not in previously_released_archives]
    before, after = _spec_inventory(root, boundary_sha), _spec_inventory(root, target_sha)
    changed_paths = sorted(path for path in before.keys() | after.keys()
                           if before.get(path) != after.get(path))
    return {"boundary": boundary_sha, "target": target_sha,
            "previous_version": version_at(root, boundary_sha), "version": version,
            "archives": archives, "specification_changed": bool(changed_paths),
            "changed_specifications": changed_paths, "has_release": True}


def format_release_notes(plan: dict[str, object], release_commit: str, workflow_url: str) -> str:
    archives = plan["archives"]
    lines = [
        f"HumanMotionLib {plan['version']}",
        "",
        "Release automation identity: humanmotionlib-versioned-release/v1",
        "",
        "Included accepted changes:",
    ]
    for item in archives:
        lines.append(f"- `{item['id']}` (acceptance `{item['acceptance_commit']}`)")
    lines += [
        "",
        f"Previous release boundary: `{plan['boundary']}`",
        f"Release commit: `{release_commit}`",
        f"Verification workflow: {workflow_url}",
        "",
        "The release contains the checked wheel and SHA256SUMS. Host/package checks do not represent a new Blender or visual acceptance.",
    ]
    return "\n".join(lines) + "\n"


class GitHubClient:
    """Small stdlib GitHub REST client scoped to one repository."""

    def __init__(self, repository: str, token: str, opener=urlopen):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise ReleaseError(f"invalid GitHub repository identity: {repository!r}")
        if not token:
            raise ReleaseError("GITHUB_TOKEN is required for release automation")
        self.repository = repository
        self.token = token
        self.opener = opener
        self.api = f"https://api.github.com/repos/{repository}"

    def request(self, path: str, *, method: str = "GET", payload: object | None = None,
                content: bytes | None = None, content_type: str = "application/vnd.github+json",
                accept: str = "application/vnd.github+json", allow_missing: bool = False) -> tuple[int, object | bytes | None]:
        url = path if path.startswith("https://") else f"{self.api}{path}"
        data = content if content is not None else (
            json.dumps(payload, separators=(",", ":")).encode("utf-8") if payload is not None else None
        )
        headers = {
            "Accept": accept,
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "humanmotionlib-release",
        }
        if data is not None:
            headers["Content-Type"] = content_type
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with self.opener(request, timeout=60) as response:
                body = response.read()
                status = response.status
        except HTTPError as error:
            body = error.read()
            status = error.code
            if allow_missing and status == 404:
                return status, None
            detail = body.decode("utf-8", "replace")[:1000]
            raise ReleaseError(f"GitHub API {method} {url} returned {status}: {detail}") from error
        if not 200 <= status < 300:
            raise ReleaseError(f"GitHub API {method} {url} returned {status}")
        if not body:
            return status, None
        if accept == "application/octet-stream":
            return status, body
        try:
            return status, json.loads(body)
        except json.JSONDecodeError as error:
            raise ReleaseError(f"GitHub API returned invalid JSON for {method} {url}") from error

    def latest_release(self) -> dict[str, object] | None:
        _, release = self.request("/releases/latest", allow_missing=True)
        return release if isinstance(release, dict) else None

    def published_releases(self) -> list[dict[str, object]]:
        result: list[dict[str, object]] = []
        page = 1
        while True:
            _, records = self.request(f"/releases?per_page=100&page={page}")
            if not isinstance(records, list):
                raise ReleaseError("GitHub returned invalid release history")
            for record in records:
                if not isinstance(record, dict) or not isinstance(record.get("draft"), bool):
                    raise ReleaseError("GitHub returned a malformed release record")
                if record["draft"] is False:
                    result.append(record)
            if len(records) < 100:
                break
            page += 1
        return result

    def release_for_tag(self, tag: str) -> dict[str, object] | None:
        matches: list[dict[str, object]] = []
        page = 1
        while True:
            _, records = self.request(f"/releases?per_page=100&page={page}")
            if not isinstance(records, list):
                raise ReleaseError("GitHub returned invalid release history while looking up a draft")
            for record in records:
                if not isinstance(record, dict) or not isinstance(record.get("draft"), bool):
                    raise ReleaseError("GitHub returned a malformed release record while looking up a draft")
                if record.get("tag_name") == tag:
                    matches.append(record)
            if len(records) < 100:
                break
            page += 1
        if len(matches) > 1:
            raise ReleaseError(f"GitHub returned multiple releases for tag {tag}")
        return matches[0] if matches else None

    def create_tag_ref(self, tag: str, candidate: str) -> None:
        _, result = self.request("/git/refs", method="POST", payload={
            "ref": f"refs/tags/{tag}", "sha": candidate,
        })
        if (not isinstance(result, dict) or result.get("ref") != f"refs/tags/{tag}"
                or not isinstance(result.get("object"), dict)
                or result["object"].get("sha") != candidate):
            raise ReleaseError(f"GitHub did not confirm exact creation of tag {tag}")

    def release_assets(self, release: dict[str, object]) -> dict[str, dict[str, object]]:
        assets = release.get("assets")
        if not isinstance(assets, list):
            raise ReleaseError("GitHub release has no valid asset list")
        result: dict[str, dict[str, object]] = {}
        for asset in assets:
            if not isinstance(asset, dict) or not isinstance(asset.get("name"), str):
                raise ReleaseError("GitHub release contains an invalid asset record")
            if asset["name"] in result:
                raise ReleaseError(f"GitHub release contains duplicate asset {asset['name']!r}")
            result[asset["name"]] = asset
        return result

    def asset_bytes(self, asset: dict[str, object]) -> bytes:
        url = asset.get("url")
        if not isinstance(url, str):
            raise ReleaseError("GitHub release asset has no API URL")
        _, result = self.request(url, accept="application/octet-stream")
        if not isinstance(result, bytes):
            raise ReleaseError(f"could not download release asset {asset.get('name')!r}")
        return result

    def upload_asset(self, release: dict[str, object], name: str, data: bytes) -> dict[str, object]:
        template = release.get("upload_url")
        if not isinstance(template, str):
            raise ReleaseError("GitHub release has no upload URL")
        upload_url = template.split("{", 1)[0] + "?name=" + quote(name, safe="")
        _, result = self.request(upload_url, method="POST", content=data,
                                 content_type="application/octet-stream")
        if not isinstance(result, dict):
            raise ReleaseError(f"GitHub did not confirm upload of {name!r}")
        return result


def _managed_release_history(root: Path, client: GitHubClient) -> tuple[str, str, set[str]]:
    bootstrap, bootstrap_version = bootstrap_boundary(root)
    released_archive_ids = _archive_markers(root, bootstrap)
    if hasattr(client, "published_releases"):
        releases = client.published_releases()
    else:
        latest = client.latest_release()
        releases = [] if latest is None else [latest]
    if not releases:
        return bootstrap, bootstrap_version, released_archive_ids
    ordered: list[tuple[tuple[int, int, int], str, dict[str, object]]] = []
    seen_versions: set[str] = set()
    for record in releases:
        if record.get("prerelease") is True:
            continue
        body = record.get("body")
        if not isinstance(body, str) or "Release automation identity: humanmotionlib-versioned-release/v1" not in body.splitlines():
            continue
        tag = record.get("tag_name")
        if not isinstance(tag, str) or not re.fullmatch(r"v0\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", tag):
            raise ReleaseError(f"published release history has an unsupported version tag: {tag!r}")
        version = tag[1:]
        if version in seen_versions:
            raise ReleaseError(f"published release history contains duplicate version {version}")
        seen_versions.add(version)
        ordered.append((version_key(version), version, record))

    current_boundary, current_version = bootstrap, bootstrap_version
    for _, version, record in sorted(ordered, key=lambda row: row[0]):
        tag = str(record["tag_name"])
        boundary = _commit(root, f"refs/tags/{tag}")
        if version_at(root, boundary) != version:
            raise ReleaseError(f"published tag {tag} and source version disagree")
        if boundary == bootstrap or not _is_ancestor(root, bootstrap, boundary):
            raise ReleaseError(f"published release {tag} is unrelated to the configured bootstrap history")
        if version_key(version) <= version_key(current_version):
            raise ReleaseError(f"published release {tag} does not increase the previous published version")
        if not _is_ancestor(root, current_boundary, boundary):
            raise ReleaseError(f"published release {tag} is not after the previous published boundary")
        released_archive_ids.update(
            archive["id"] for archive in _new_archives(root, current_boundary, boundary)
        )
        current_boundary, current_version = boundary, version
    return current_boundary, current_version, released_archive_ids


def _latest_boundary(root: Path, client: GitHubClient) -> tuple[str, str]:
    boundary, version, _ = _managed_release_history(root, client)
    return boundary, version


def _parse_reservation(root: Path, commit: str) -> dict[str, object] | None:
    body = str(_git(root, "show", "-s", "--format=%B", commit))
    trailer_values: dict[str, list[str]] = {}
    for line in body.splitlines():
        if line.startswith("HML-Release-") and ": " in line:
            key, value = line.split(": ", 1)
            trailer_values.setdefault(key, []).append(value)
    version_values = trailer_values.get("HML-Release-Version", [])
    if not version_values:
        return None
    if len(version_values) != 1:
        raise ReleaseError(f"release reservation {commit} has multiple version trailers")
    version = version_values[0]
    if not _VERSION.fullmatch(version):
        raise ReleaseError(f"release reservation {commit} has invalid version {version!r}")
    boundary_values = trailer_values.get("HML-Release-Boundary", [])
    input_values = trailer_values.get("HML-Release-Input", [])
    if len(boundary_values) != 1 or len(input_values) != 1:
        raise ReleaseError(f"release reservation {commit} is missing its boundary/input identity")
    archive_rows = []
    for value in trailer_values.get("HML-Release-Change", []):
        change_id, separator, acceptance = value.rpartition(" ")
        if not separator or not re.fullmatch(r"[0-9a-f]{40,64}", acceptance):
            raise ReleaseError(f"release reservation {commit} has invalid change identity {value!r}")
        archive_rows.append({"id": change_id, "acceptance_commit": acceptance})
    if not archive_rows:
        raise ReleaseError(f"release reservation {commit} has no accepted change identities")
    return {
        "version": version,
        "boundary": boundary_values[0],
        "input": input_values[0],
        "candidate": commit,
        "archives": archive_rows,
    }


def _validate_reservation_chain(root: Path, candidate: str, bootstrap: str,
                                bootstrap_version: str, seen: set[str] | None = None) -> dict[str, object]:
    """Verify every managed version commit back to the fixed bootstrap."""
    candidate = _commit(root, candidate)
    seen = set() if seen is None else seen
    if candidate == bootstrap:
        return {"version": bootstrap_version, "boundary": bootstrap, "input": bootstrap,
                "archives": [], "candidate": bootstrap}
    if candidate in seen:
        raise ReleaseError("release reservation history contains a cycle")
    seen.add(candidate)
    record = _parse_reservation(root, candidate)
    if record is None:
        raise ReleaseError(f"release boundary {candidate} has no managed reservation trailers")
    version = version_at(root, candidate)
    if record["version"] != version:
        raise ReleaseError("reservation trailer and declared source version disagree")
    parent = _commit(root, f"{candidate}^1")
    if _commit(root, str(record["input"])) != parent:
        raise ReleaseError("reservation input trailer is not its first-parent source snapshot")
    previous = _commit(root, str(record["boundary"]))
    if not _is_ancestor(root, bootstrap, previous) or not _is_ancestor(root, previous, parent):
        raise ReleaseError("reservation does not descend from its previous managed release boundary")
    if previous == bootstrap:
        previous_version = bootstrap_version
    else:
        previous_record = _validate_reservation_chain(root, previous, bootstrap, bootstrap_version, seen)
        previous_version = str(previous_record["version"])
        previous_tag = f"v{previous_version}"
        if _commit(root, f"refs/tags/{previous_tag}") != previous:
            raise ReleaseError(f"previous managed release tag {previous_tag} is missing or conflicting")
    plan = build_plan(root, previous, parent)
    if not plan["has_release"] or plan["version"] != version or plan["archives"] != record["archives"]:
        raise ReleaseError("reservation does not match accepted changes and canonical specification history")
    changed_paths = set(str(_git(root, "diff-tree", "--no-commit-id", "--name-only", "-r",
                                 f"{candidate}^", candidate)).splitlines())
    if changed_paths != {"pyproject.toml", "uv.lock"}:
        raise ReleaseError("managed release reservation changed files beyond pyproject.toml and uv.lock")
    return {**record, "candidate": candidate}


def _load_reserved_candidate(root: Path, commit: str) -> dict[str, object]:
    candidate = _commit(root, commit)
    bootstrap, bootstrap_version = bootstrap_boundary(root)
    record = _validate_reservation_chain(root, candidate, bootstrap, bootstrap_version)
    return {**record, "candidate": candidate, "has_release": True}


def _asset_digest(client: GitHubClient, asset: dict[str, object]) -> str:
    digest = asset.get("digest")
    if isinstance(digest, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        return digest.split(":", 1)[1]
    return hashlib.sha256(client.asset_bytes(asset)).hexdigest()


def _create_or_get_draft(client: GitHubClient, tag: str, candidate: str,
                         title: str, body: str) -> dict[str, object]:
    existing = client.release_for_tag(tag)
    if existing is not None:
        if existing.get("tag_name") != tag:
            raise ReleaseError("GitHub returned a release for a different tag")
        if existing.get("draft") is False:
            return existing
        return existing
    _, release = client.request("/releases", method="POST", payload={
        "tag_name": tag,
        "target_commitish": candidate,
        "name": title,
        "body": body,
        "draft": True,
        "prerelease": False,
    })
    if not isinstance(release, dict):
        raise ReleaseError("GitHub did not confirm release draft creation")
    return release


def _verify_remote_tag(root: Path, tag: str, candidate: str) -> None:
    fetched = subprocess.run(["git", "fetch", "origin", f"+refs/tags/{tag}:refs/tags/{tag}"],
                             cwd=root, capture_output=True, text=True)
    if fetched.returncode != 0:
        raise ReleaseError(f"release tag {tag} could not be verified from origin: {fetched.stderr.strip()}")
    if _commit(root, f"refs/tags/{tag}") != candidate:
        raise ReleaseError(f"release tag {tag} does not target the checked commit")


def _remote_tag_exists(root: Path, tag: str) -> bool:
    result = subprocess.run(["git", "ls-remote", "--tags", "origin",
                             f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}"],
                            cwd=root, capture_output=True, text=True)
    if result.returncode != 0:
        raise ReleaseError(f"release tag {tag} could not be checked at origin: {result.stderr.strip()}")
    return bool(result.stdout.strip())


def _ensure_remote_tag(root: Path, client: GitHubClient, tag: str, candidate: str) -> None:
    if not _remote_tag_exists(root, tag):
        client.create_tag_ref(tag, candidate)
    _verify_remote_tag(root, tag, candidate)


def _validate_release_evidence(release: dict[str, object], plan: dict[str, object],
                               tag: str, candidate: str, wheel_checksum: str,
                               workflow_url: str | None = None) -> None:
    """Refuse to adopt a same-tag draft or release without our complete evidence."""
    if release.get("tag_name") != tag:
        raise ReleaseError("GitHub returned a release for a different tag")
    if release.get("name") != f"HumanMotionLib {plan['version']}":
        raise ReleaseError("existing release title does not match the reserved version")
    if release.get("draft") is True and release.get("target_commitish") != candidate:
        raise ReleaseError("existing draft release targets a conflicting commit")
    body = release.get("body")
    if not isinstance(body, str):
        raise ReleaseError("existing release has no managed verification notes")
    workflow_lines = [line for line in body.splitlines() if line.startswith("Verification workflow: ")]
    if len(workflow_lines) != 1:
        raise ReleaseError("existing release notes do not uniquely identify the verification workflow")
    recorded_url = workflow_lines[0].removeprefix("Verification workflow: ")
    if not recorded_url:
        raise ReleaseError("existing release notes have an empty verification workflow identity")
    if workflow_url is not None and recorded_url != workflow_url:
        raise ReleaseError("existing release notes identify a different qualifying workflow run")
    expected_body = format_release_notes(plan, candidate, recorded_url)
    expected_body += f"Checked wheel SHA-256: `{wheel_checksum}`\n"
    if body != expected_body:
        raise ReleaseError("existing release notes differ from the exact boundary and accepted-change plan")


def _read_verified_draft(client: GitHubClient, tag: str, release_id: int,
                         plan: dict[str, object], candidate: str, checksum: str,
                         workflow_url: str, wheel_name: str, checksum_bytes: bytes
                         ) -> dict[str, object]:
    """Read a fresh release snapshot and verify its complete immutable evidence."""
    release = client.release_for_tag(tag)
    if release is None:
        raise ReleaseError("release draft disappeared before publication")
    if release.get("id") != release_id:
        raise ReleaseError("release identity changed before publication")
    if release.get("draft") is not True:
        raise ReleaseError("release was no longer a draft before publication")
    _validate_release_evidence(release, plan, tag, candidate, checksum, workflow_url)
    assets = client.release_assets(release)
    if set(assets) != {wheel_name, "SHA256SUMS"}:
        raise ReleaseError("draft release asset set changed before publication")
    if _asset_digest(client, assets[wheel_name]) != checksum:
        raise ReleaseError("draft wheel changed before publication")
    if client.asset_bytes(assets["SHA256SUMS"]) != checksum_bytes:
        raise ReleaseError("draft checksum changed before publication")
    return release


def publish_release(root: Path, client: GitHubClient, candidate: str, wheel_path: Path,
                    workflow_url: str, checksum_path: Path,
                    plan_override: dict[str, object] | None = None) -> dict[str, object]:
    """Publish a checked wheel, reconciling only assets with matching bytes."""
    root = root.resolve()
    wheel_path = wheel_path.resolve()
    if not wheel_path.is_file() or wheel_path.suffix != ".whl":
        raise ReleaseError(f"checked wheel does not exist: {wheel_path}")
    checksum_path = checksum_path.resolve()
    try:
        checksum_rows = checksum_path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ReleaseError(f"package workflow checksum evidence is unavailable: {checksum_path}") from error
    if len(checksum_rows) != 1:
        raise ReleaseError("package workflow checksum evidence must contain exactly one wheel")
    expected_checksum = checksum_rows[0].split()[0] if checksum_rows[0].split() else ""
    if not re.fullmatch(r"[0-9a-f]{64}", expected_checksum):
        raise ReleaseError("package workflow checksum evidence is malformed")
    plan = _load_reserved_candidate(root, candidate) if plan_override is None else plan_override
    candidate_sha = str(plan["candidate"])
    if candidate_sha != _commit(root, candidate):
        raise ReleaseError("release plan does not identify the requested checked commit")
    tag = f"v{plan['version']}"
    local_tag = subprocess.run(["git", "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"],
                               cwd=root, capture_output=True, text=True)
    if local_tag.returncode == 0 and local_tag.stdout.strip() != candidate_sha:
        raise ReleaseError(f"tag {tag} points to a conflicting commit")
    existing = client.release_for_tag(tag)
    if local_tag.returncode == 0 and existing is None:
        raise ReleaseError(f"bare tag {tag} already exists without matching managed release evidence")
    if plan_override is not None and existing is None and _remote_tag_exists(root, tag):
        raise ReleaseError(f"bare tag {tag} already exists without matching managed release evidence")

    wheel_bytes = wheel_path.read_bytes()
    wheel_name = wheel_path.name
    checksum = hashlib.sha256(wheel_bytes).hexdigest()
    if checksum != expected_checksum:
        raise ReleaseError("downloaded wheel bytes differ from the package-check workflow checksum")
    checksum_bytes = f"{checksum}  {wheel_name}\n".encode("ascii")
    notes = format_release_notes(plan, candidate_sha, workflow_url)
    notes += f"Checked wheel SHA-256: `{checksum}`\n"
    release = _create_or_get_draft(client, tag, candidate_sha, f"HumanMotionLib {plan['version']}", notes)
    if release.get("tag_name") != tag:
        raise ReleaseError("release identity does not match reserved version")
    release_id = release.get("id")
    if not isinstance(release_id, int):
        raise ReleaseError("GitHub release has no numeric identity")
    if release.get("draft") is False:
        assets = client.release_assets(release)
        if set(assets) != {wheel_name, "SHA256SUMS"}:
            raise ReleaseError("published release assets do not match the reserved wheel/checksum")
        if _asset_digest(client, assets[wheel_name]) != checksum:
            raise ReleaseError("published release wheel checksum conflicts with the checked artifact")
        if client.asset_bytes(assets["SHA256SUMS"]) != checksum_bytes:
            raise ReleaseError("published SHA256SUMS conflicts with the checked wheel")
        _validate_release_evidence(release, plan, tag, candidate_sha, checksum, workflow_url)
        return {"published": True, "already_complete": True, "tag": tag, "candidate": candidate_sha,
                "wheel_sha256": checksum}

    assets = client.release_assets(release)
    unexpected = set(assets) - {wheel_name, "SHA256SUMS"}
    if unexpected:
        raise ReleaseError(f"draft release contains unexpected assets: {sorted(unexpected)}")
    if "SHA256SUMS" in assets and wheel_name not in assets:
        raise ReleaseError("draft contains a checksum file without its wheel")
    if wheel_name in assets:
        existing_checksum = _asset_digest(client, assets[wheel_name])
        if existing_checksum != checksum:
            raise ReleaseError(
                "existing draft wheel checksum differs from the checked candidate "
                f"(expected {checksum}, found {existing_checksum})"
            )
        _validate_release_evidence(release, plan, tag, candidate_sha, checksum, workflow_url)
    else:
        _validate_release_evidence(release, plan, tag, candidate_sha, checksum, workflow_url)
        client.request(f"/releases/{release_id}", method="PATCH", payload={"body": notes})
        client.upload_asset(release, wheel_name, wheel_bytes)
    assets = client.release_assets(client.release_for_tag(tag) or release)
    if "SHA256SUMS" in assets:
        if client.asset_bytes(assets["SHA256SUMS"]) != checksum_bytes:
            raise ReleaseError("draft SHA256SUMS conflicts with its immutable wheel asset")
    else:
        client.upload_asset(release, "SHA256SUMS", checksum_bytes)

    release = _read_verified_draft(client, tag, release_id, plan, candidate_sha,
                                   checksum, workflow_url, wheel_name, checksum_bytes)
    if plan_override is not None:
        _ensure_remote_tag(root, client, tag, candidate_sha)
    release = _read_verified_draft(client, tag, release_id, plan, candidate_sha,
                                   checksum, workflow_url, wheel_name, checksum_bytes)
    release_id = release.get("id")
    if not isinstance(release_id, int):
        raise ReleaseError("GitHub release has no numeric identity")
    _, result = client.request(f"/releases/{release_id}", method="PATCH", payload={"draft": False})
    if not isinstance(result, dict) or result.get("draft") is not False:
        raise ReleaseError("GitHub did not confirm publication")
    if plan_override is not None:
        _verify_remote_tag(root, tag, candidate_sha)
    if plan_override is not None:
        final_release = client.release_for_tag(tag)
        if final_release is None or final_release.get("draft") is not False:
            raise ReleaseError("GitHub did not retain the published release identity")
        final_assets = client.release_assets(final_release)
        if set(final_assets) != {wheel_name, "SHA256SUMS"}:
            raise ReleaseError("published release assets differ from the checked wheel")
        if _asset_digest(client, final_assets[wheel_name]) != checksum:
            raise ReleaseError("published release wheel differs from the checked wheel")
        if client.asset_bytes(final_assets["SHA256SUMS"]) != checksum_bytes:
            raise ReleaseError("published release checksum differs from the checked wheel")
        _validate_release_evidence(final_release, plan, tag, candidate_sha, checksum, workflow_url)
    return {"published": True, "already_complete": False, "tag": tag,
            "candidate": candidate_sha, "wheel_sha256": checksum}


def publish_pushed_release(root: Path, client: GitHubClient, before: str, candidate: str,
                           ref: str, event: str, wheel_path: Path,
                           event_after: str, forced: bool, deleted: bool,
                           workflow_url: str, checksum_path: Path) -> dict[str, object]:
    """Publish only the exact checked version-bump push, rechecking state under serialization."""
    root = root.resolve()
    boundary, published_version, released_archive_ids = _managed_release_history(root, client)
    intent = release_intent(root, before, candidate, ref=ref, event=event,
                            published_version=published_version,
                            event_after=event_after, forced=forced, deleted=deleted)
    if not intent["eligible"]:
        raise ReleaseError(str(intent["reason"]))
    candidate_sha = _commit(root, candidate)
    if candidate_sha != str(intent["source_sha"]):
        raise ReleaseError("checked release commit differs from the original push identity")
    plan = build_pushed_release_plan(root, boundary, candidate_sha, str(intent["version"]),
                                     previously_released_archives=released_archive_ids)
    plan["candidate"] = candidate_sha
    plan["has_release"] = True
    return publish_release(root, client, candidate_sha, wheel_path, workflow_url,
                           checksum_path, plan_override=plan)


def _client_from_args(args: argparse.Namespace) -> GitHubClient:
    return GitHubClient(args.repository, args.token or os.environ.get("GITHUB_TOKEN", ""))


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    intent_parser = subparsers.add_parser("intent", help="evaluate an original push version increase")
    intent_parser.add_argument("--before", required=True)
    intent_parser.add_argument("--after", required=True)
    intent_parser.add_argument("--event-after")
    intent_parser.add_argument("--ref", required=True)
    intent_parser.add_argument("--event", required=True)
    intent_parser.add_argument("--forced", action="store_true")
    intent_parser.add_argument("--deleted", action="store_true")
    intent_parser.add_argument("--repo", type=Path, default=Path.cwd())
    intent_parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    intent_parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    intent_parser.add_argument("--github-output", type=Path)
    pushed_parser = subparsers.add_parser("publish-push", help="publish the exact checked version-bump push")
    pushed_parser.add_argument("--repo", type=Path, default=Path.cwd())
    pushed_parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    pushed_parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    pushed_parser.add_argument("--before", required=True)
    pushed_parser.add_argument("--candidate", required=True)
    pushed_parser.add_argument("--event-after", required=True)
    pushed_parser.add_argument("--ref", required=True)
    pushed_parser.add_argument("--event", required=True)
    pushed_parser.add_argument("--forced", action="store_true")
    pushed_parser.add_argument("--deleted", action="store_true")
    pushed_parser.add_argument("--wheel", required=True, type=Path)
    pushed_parser.add_argument("--checksum", required=True, type=Path)
    pushed_parser.add_argument("--workflow-url", required=True)
    args = parser.parse_args()
    intent_error = False
    try:
        if args.command == "intent":
            result = release_intent(args.repo, args.before, args.after, ref=args.ref, event=args.event,
                                    event_after=args.event_after, forced=args.forced, deleted=args.deleted)
            if result["eligible"]:
                try:
                    boundary, published = _latest_boundary(args.repo, _client_from_args(args))
                    result.update(boundary=boundary, published_version=published)
                    if version_key(str(result["version"])) <= version_key(published):
                        result.update(eligible=False, reason=(
                            f"version {result['version']} is already published or superseded by "
                            f"{published}; CI still runs"))
                except (ReleaseError, OSError, subprocess.CalledProcessError) as error:
                    result.update(eligible=False, reason=f"cannot verify published history: {error}; CI still runs")
                    intent_error = True
            if args.github_output is not None:
                with args.github_output.open("a", encoding="utf-8") as output:
                    output.write(f"eligible={str(result['eligible']).lower()}\n")
                    for key in ("source_sha", "version", "boundary", "published_version"):
                        if key in result:
                            output.write(f"{key}={result[key]}\n")
                    if "reason" in result:
                        output.write(f"reason={result['reason']}\n")
            print(json.dumps(result, sort_keys=True))
            if intent_error:
                return 2
        else:
            result = publish_pushed_release(args.repo, _client_from_args(args), args.before,
                                            args.candidate, args.ref, args.event, args.wheel,
                                            args.event_after,
                                            args.forced, args.deleted,
                                            args.workflow_url, args.checksum)
            print(json.dumps(result, sort_keys=True))
    except (ReleaseError, OSError, subprocess.CalledProcessError) as error:
        print(f"release helper: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
