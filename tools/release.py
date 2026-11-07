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
import zipfile
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


def next_version(previous: str, specification_changed: bool) -> str:
    match = _VERSION.fullmatch(previous)
    if not match:
        raise ReleaseError(f"automatic releases require a valid 0.x.y version, got {previous!r}")
    minor, patch = map(int, match.groups())
    return f"0.{minor + 1}.0" if specification_changed else f"0.{minor}.{patch + 1}"


def _first_parent_commits(root: Path, base: str, target: str) -> list[str]:
    base_sha, target_sha = _commit(root, base), _commit(root, target)
    if not _is_ancestor(root, base_sha, target_sha):
        raise ReleaseError(f"release boundary {base_sha} is not an ancestor of {target_sha}")
    commits = str(_git(root, "rev-list", "--first-parent", "--reverse", f"{base_sha}..{target_sha}"))
    return commits.splitlines() if commits else []


def _new_archive_roots(root: Path, commit: str) -> list[str]:
    """Find archive roots whose marker was introduced by this first-parent commit."""
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
    boundary_sha, target_sha = _commit(root, boundary), _commit(root, target)
    commits = _first_parent_commits(root, boundary_sha, target_sha)
    archives: list[dict[str, str]] = []
    for commit in commits:
        for change_id in _new_archive_roots(root, commit):
            archives.append({"id": change_id, "acceptance_commit": commit})

    before, after = _spec_inventory(root, boundary_sha), _spec_inventory(root, target_sha)
    changed_paths = sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))
    previous = version_at(root, boundary_sha)
    return {
        "boundary": boundary_sha,
        "target": target_sha,
        "previous_version": previous,
        "version": next_version(previous, bool(changed_paths)) if archives else None,
        "archives": archives,
        "specification_changed": bool(changed_paths),
        "changed_specifications": changed_paths,
        "has_release": bool(archives),
    }


def _replace_declared_version(text: str, version: str) -> str:
    if not _VERSION.fullmatch(version):
        raise ReleaseError(f"invalid release version {version!r}")
    pattern = re.compile(r'(?m)^(version\s*=\s*)"[^"]+"$')
    updated, count = pattern.subn(lambda match: f'{match.group(1)}"{version}"', text, count=1)
    if count != 1:
        raise ReleaseError("could not locate a unique project version in pyproject.toml")
    return updated


def update_version_files(root: Path, version: str) -> None:
    """Update only the root project version in source metadata and uv.lock."""
    project = root / "pyproject.toml"
    lock = root / "uv.lock"
    original_project, original_lock = project.read_text(), lock.read_text()
    project_updated = _replace_declared_version(original_project, version)
    package_pattern = re.compile(
        r'(?ms)(\[\[package\]\]\nname = "humanmotionlib"\nversion = ")[^"]+("\nsource = \{ editable = "\." \})'
    )
    lock_updated, count = package_pattern.subn(lambda match: f"{match.group(1)}{version}{match.group(2)}",
                                               original_lock, count=1)
    if count != 1:
        raise ReleaseError("could not locate the editable humanmotionlib package entry in uv.lock")
    project.write_text(project_updated)
    lock.write_text(lock_updated)


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

    def release_for_tag(self, tag: str) -> dict[str, object] | None:
        _, release = self.request(f"/releases/tags/{quote(tag, safe='')}", allow_missing=True)
        return release if isinstance(release, dict) else None

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


def _latest_boundary(root: Path, client: GitHubClient) -> tuple[str, str]:
    bootstrap, bootstrap_version = bootstrap_boundary(root)
    latest = client.latest_release()
    if latest is None:
        return bootstrap, bootstrap_version
    if latest.get("draft") is not False:
        raise ReleaseError("latest release history is not a successfully published GitHub Release")
    tag = latest.get("tag_name")
    if not isinstance(tag, str) or not re.fullmatch(r"v0\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", tag):
        raise ReleaseError(f"latest published release has an unsupported automatic version tag: {tag!r}")
    boundary = _commit(root, f"refs/tags/{tag}")
    version = version_at(root, boundary)
    if tag != f"v{version}":
        raise ReleaseError(f"published tag {tag} and source version {version} disagree")
    if boundary == bootstrap:
        raise ReleaseError("the bootstrap snapshot is not a managed published release")
    if not _is_ancestor(root, bootstrap, boundary):
        raise ReleaseError("latest release tag is unrelated to the configured bootstrap history")
    record = _validate_reservation_chain(root, boundary, bootstrap, bootstrap_version)
    if record["version"] != version:
        raise ReleaseError("latest release tag and managed reservation versions disagree")
    plan = build_plan(root, str(record["boundary"]), str(record["input"]))

    assets = client.release_assets(latest)
    wheel_names = [name for name in assets if name.endswith(".whl")]
    if set(assets) != {*wheel_names, "SHA256SUMS"} or len(wheel_names) != 1:
        raise ReleaseError("latest managed release must contain exactly one wheel and SHA256SUMS")
    wheel_name = wheel_names[0]
    wheel_checksum = _asset_digest(client, assets[wheel_name])
    checksum_bytes = client.asset_bytes(assets["SHA256SUMS"])
    if checksum_bytes != f"{wheel_checksum}  {wheel_name}\n".encode("ascii"):
        raise ReleaseError("latest managed release checksum file does not match its wheel")
    _validate_release_evidence(latest, plan, tag, boundary, wheel_checksum)
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


def _pending_reservation(root: Path, boundary: str, target: str) -> dict[str, object] | None:
    commits = _first_parent_commits(root, boundary, target)
    reservations = [record for commit in commits if (record := _parse_reservation(root, commit))]
    if not reservations:
        return None
    if len(reservations) != 1:
        raise ReleaseError("multiple unpublished release reservations exist; refusing to skip or reorder them")
    reservation = reservations[0]
    if _commit(root, str(reservation["boundary"])) != _commit(root, boundary):
        raise ReleaseError("unfinished release reservation does not match the latest published boundary")
    if not _is_ancestor(root, str(reservation["input"]), str(reservation["candidate"])):
        raise ReleaseError("release candidate does not descend from its recorded input snapshot")
    return reservation


def reserve_release(root: Path, client: GitHubClient, target: str = "HEAD") -> dict[str, object]:
    """Resume an existing reservation or create and commit the next version."""
    root = root.resolve()
    boundary, _ = _latest_boundary(root, client)
    target_sha = _commit(root, target)
    if not _is_ancestor(root, boundary, target_sha):
        raise ReleaseError("latest release boundary is not an ancestor of the selected main snapshot")
    existing = _pending_reservation(root, boundary, target_sha)
    if existing:
        return {**existing, "resumed": True, "has_release": True}
    plan = build_plan(root, boundary, target_sha)
    if not plan["has_release"]:
        return {"has_release": False, "boundary": boundary, "target": target_sha, "candidate": None}
    update_version_files(root, str(plan["version"]))
    _git(root, "add", "pyproject.toml", "uv.lock")
    command = ["git", "commit", "-m", f"chore(release): {plan['version']}",
               "--trailer", f"HML-Release-Version: {plan['version']}",
               "--trailer", f"HML-Release-Boundary: {boundary}",
               "--trailer", f"HML-Release-Input: {target_sha}"]
    for item in plan["archives"]:
        command.extend(("--trailer", f"HML-Release-Change: {item['id']} {item['acceptance_commit']}"))
    subprocess.run(command, cwd=root, check=True, capture_output=True, text=True)
    candidate = _commit(root, "HEAD")
    return {
        "has_release": True,
        "resumed": False,
        "version": plan["version"],
        "boundary": boundary,
        "target": target_sha,
        "candidate": candidate,
        "archives": plan["archives"],
    }


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


def _validate_release_evidence(release: dict[str, object], plan: dict[str, object],
                               tag: str, candidate: str, wheel_checksum: str) -> None:
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
    required_lines = [
        "Release automation identity: humanmotionlib-versioned-release/v1",
        "Included accepted changes:",
        f"Previous release boundary: `{plan['boundary']}`",
        f"Release commit: `{candidate}`",
        f"Checked wheel SHA-256: `{wheel_checksum}`",
    ]
    required_lines.extend(
        f"- `{item['id']}` (acceptance `{item['acceptance_commit']}`)"
        for item in plan["archives"]
    )
    lines = set(body.splitlines())
    if any(line not in lines for line in required_lines):
        raise ReleaseError("existing release notes do not identify this reservation and checked wheel")
    if not any(line.startswith("Verification workflow: ") for line in lines):
        raise ReleaseError("existing release notes do not identify the verification workflow")


def publish_release(root: Path, client: GitHubClient, candidate: str, wheel_path: Path,
                    workflow_url: str, checksum_path: Path) -> dict[str, object]:
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
    plan = _load_reserved_candidate(root, candidate)
    candidate_sha = str(plan["candidate"])
    tag = f"v{plan['version']}"
    local_tag = subprocess.run(["git", "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"],
                               cwd=root, capture_output=True, text=True)
    if local_tag.returncode == 0 and local_tag.stdout.strip() != candidate_sha:
        raise ReleaseError(f"tag {tag} points to a conflicting commit")

    wheel_bytes = wheel_path.read_bytes()
    wheel_name = wheel_path.name
    checksum = hashlib.sha256(wheel_bytes).hexdigest()
    if checksum != expected_checksum:
        raise ReleaseError("downloaded wheel bytes differ from the package-check workflow checksum")
    with zipfile.ZipFile(wheel_path) as archive:
        metadata_names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(metadata_names) != 1:
            raise ReleaseError("checked wheel must contain exactly one distribution metadata file")
        metadata = archive.read(metadata_names[0]).decode("utf-8")
        if f"Name: humanmotionlib\n" not in metadata or f"Version: {plan['version']}\n" not in metadata:
            raise ReleaseError("checked wheel metadata does not match the reserved distribution identity")
        if archive.read("humanmotionlib/_version.py").decode("utf-8") != f'__version__ = "{plan["version"]}"\n':
            raise ReleaseError("checked wheel Python version does not match its metadata")
        manifest = json.loads(archive.read("humanmotionlib/resources/runtime-manifest.json"))
        if manifest.get("version") != plan["version"]:
            raise ReleaseError("checked wheel runtime manifest version does not match its metadata")
    checksum_bytes = f"{checksum}  {wheel_name}\n".encode("ascii")
    notes = format_release_notes(plan, candidate_sha, workflow_url)
    notes += f"Checked wheel SHA-256: `{checksum}`\n"
    release = _create_or_get_draft(client, tag, candidate_sha, f"HumanMotionLib {plan['version']}", notes)
    if release.get("tag_name") != tag:
        raise ReleaseError("release identity does not match reserved version")
    if release.get("draft") is False:
        assets = client.release_assets(release)
        if set(assets) != {wheel_name, "SHA256SUMS"}:
            raise ReleaseError("published release assets do not match the reserved wheel/checksum")
        if _asset_digest(client, assets[wheel_name]) != checksum:
            raise ReleaseError("published release wheel checksum conflicts with the checked artifact")
        if client.asset_bytes(assets["SHA256SUMS"]) != checksum_bytes:
            raise ReleaseError("published SHA256SUMS conflicts with the checked wheel")
        _validate_release_evidence(release, plan, tag, candidate_sha, checksum)
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
        _validate_release_evidence(release, plan, tag, candidate_sha, checksum)
    else:
        _validate_release_evidence(release, plan, tag, candidate_sha, checksum)
        release_id = release.get("id")
        if not isinstance(release_id, int):
            raise ReleaseError("GitHub release has no numeric identity")
        client.request(f"/releases/{release_id}", method="PATCH", payload={"body": notes})
        client.upload_asset(release, wheel_name, wheel_bytes)
    assets = client.release_assets(client.release_for_tag(tag) or release)
    if "SHA256SUMS" in assets:
        if client.asset_bytes(assets["SHA256SUMS"]) != checksum_bytes:
            raise ReleaseError("draft SHA256SUMS conflicts with its immutable wheel asset")
    else:
        client.upload_asset(release, "SHA256SUMS", checksum_bytes)

    release = client.release_for_tag(tag) or release
    assets = client.release_assets(release)
    if set(assets) != {wheel_name, "SHA256SUMS"}:
        raise ReleaseError("draft release asset set is incomplete or contains unexpected assets")
    if _asset_digest(client, assets[wheel_name]) != checksum:
        raise ReleaseError("draft wheel does not match its recorded checksum")
    if client.asset_bytes(assets["SHA256SUMS"]) != checksum_bytes:
        raise ReleaseError("draft checksum does not match its wheel")
    release_id = release.get("id")
    if not isinstance(release_id, int):
        raise ReleaseError("GitHub release has no numeric identity")
    _, result = client.request(f"/releases/{release_id}", method="PATCH", payload={"draft": False})
    if not isinstance(result, dict) or result.get("draft") is not False:
        raise ReleaseError("GitHub did not confirm publication")
    return {"published": True, "already_complete": False, "tag": tag,
            "candidate": candidate_sha, "wheel_sha256": checksum}


def pending_after_latest_release(root: Path, client: GitHubClient, target: str) -> dict[str, object]:
    boundary, _ = _latest_boundary(root, client)
    return build_plan(root, boundary, target)


def dispatch_pending(client: GitHubClient) -> None:
    client.request("/dispatches", method="POST", payload={"event_type": "hml-release-pending", "client_payload": {}})


def _client_from_args(args: argparse.Namespace) -> GitHubClient:
    return GitHubClient(args.repository, args.token or os.environ.get("GITHUB_TOKEN", ""))


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan_parser = subparsers.add_parser("plan", help="compute a pending release plan")
    plan_parser.add_argument("--boundary", default=None,
                             help="last published release commit (defaults to fixed bootstrap)")
    plan_parser.add_argument("--target", default="HEAD", help="main snapshot to evaluate")
    plan_parser.add_argument("--repo", type=Path, default=Path.cwd())
    reserve_parser = subparsers.add_parser("reserve", help="reserve the next release commit")
    reserve_parser.add_argument("--target", default="HEAD", help="main snapshot to evaluate")
    reserve_parser.add_argument("--repo", type=Path, default=Path.cwd())
    reserve_parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    reserve_parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    publish_parser = subparsers.add_parser("publish", help="publish a checked reserved wheel")
    publish_parser.add_argument("--repo", type=Path, default=Path.cwd())
    publish_parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    publish_parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    publish_parser.add_argument("--candidate", required=True)
    publish_parser.add_argument("--wheel", required=True, type=Path)
    publish_parser.add_argument("--checksum", required=True, type=Path)
    publish_parser.add_argument("--workflow-url", required=True)
    pending_parser = subparsers.add_parser("pending", help="find accepted changes after the latest release")
    pending_parser.add_argument("--target", default="HEAD")
    pending_parser.add_argument("--repo", type=Path, default=Path.cwd())
    pending_parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    pending_parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    dispatch_parser = subparsers.add_parser("dispatch-pending", help="wake the serialized release worker")
    dispatch_parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    dispatch_parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    set_parser = subparsers.add_parser("set-version", help="update pyproject.toml and uv.lock")
    set_parser.add_argument("version")
    set_parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        if args.command == "plan":
            print(json.dumps(build_plan(args.repo, args.boundary, args.target), sort_keys=True, indent=2))
        elif args.command == "set-version":
            update_version_files(args.repo, args.version)
        elif args.command == "reserve":
            print(json.dumps(reserve_release(args.repo, _client_from_args(args), args.target), sort_keys=True))
        elif args.command == "publish":
            result = publish_release(args.repo, _client_from_args(args), args.candidate, args.wheel,
                                     args.workflow_url, args.checksum)
            print(json.dumps(result, sort_keys=True))
        elif args.command == "pending":
            print(json.dumps(pending_after_latest_release(args.repo, _client_from_args(args), args.target),
                             sort_keys=True, indent=2))
        else:
            dispatch_pending(_client_from_args(args))
    except (ReleaseError, OSError, subprocess.CalledProcessError) as error:
        print(f"release helper: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
