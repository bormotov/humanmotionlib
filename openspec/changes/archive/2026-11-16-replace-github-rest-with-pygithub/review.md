# Independent review

Verdict: **PASS WITH NOTES** — controlled integration passed; actual GitHub publication and recovery of existing drafts were not exercised.

## Candidate and environment

- Source snapshot `3a8eb8b01a1e8fb0ae22c4741d057fb4d1b5a8b9`, clean developer snapshot; current tracked worktree matched it when review began.
- Independently rebuilt `humanmotionlib-0.3.3-py3-none-any.whl`, SHA-256 `3cf2ba3b1a90aa46929c4c0ec2d9c82054e2b972924c2990ad45a0e8bfa6e1b7`. Wheel bytes may differ from the developer build; no claim of reproducible wheel hashes is made.
- Fresh uv CPython 3.14.6 environment in reviewer run, locked release dependencies, PyGithub 2.10.0 and the independently built wheel installed. Imports of the package, PyGithub, PyYAML, jsonschema, Pillow, referencing and requests resolved to that environment; `_virtualenv.pth` was the only `.pth`; `uv pip check` passed. Python standard library came from the uv-managed interpreter. The wheel metadata has no PyGithub runtime dependency.
- Independent run: `build/replace-github-rest-with-pygithub_r1_reviewer_try-1_review/`. An initial relative `UV_PROJECT_ENVIRONMENT` accidentally created a subordinate environment inside the reviewer source copy; it was not used for testing. Corrected with an absolute environment path. A first build from that source copy was rejected by the backend due to source/output containment; the successful build used the clean, disjoint developer snapshot as read-only input with bytecode writes disabled.

## Findings

No product defects found in the reviewed scope. Actual GitHub publication was not attempted, so server-side draft behavior and production release completion remain unverified. This does not establish that PyGithub fixes the `untagged-*` response.

## Requirement and scenario checks

| Requirement/scenario | Method and result |
|---|---|
| Locked host setup and release client | Fresh locked release-group setup and imports passed; `uv pip check` passed. Wheel metadata contains only PyYAML, jsonschema, Pillow and referencing runtime dependencies. |
| Release identity/retries, tag conflicts, missing/denied and artifact bytes | 63 release and workflow unit/integration tests passed under the installed wheel, including controlled failed publication and successful retry with exact wheel/checksum. The controlled test patched Git tag and GitHub operations; it is not a live publication. |
| Same release ID with an `untagged-*` tag and positive controls | Automated suite passed; mismatch prevents publication and reports expected/actual tag and release ID. |
| PyGithub operations and failures | Controlled actual SDK transport checks cover lazy 404, paginated 500, asset upload/download bytes and interrupted stream. Tracked project source search found no direct GitHub API HTTP transport. |
| Permissions, evidence and licensing | Workflow and release tests passed. Locked installed package metadata agrees with documented release dependency licenses where metadata declares an SPDX expression or license; PyGithub wheel includes LGPL texts and classifier. The release-only dependency is not bundled in the project wheel. Final legal interpretation is outside this technical review. |
| OpenSpec and scope | `openspec validate replace-github-rest-with-pygithub --strict` and `git diff --check` passed. Visual gate not applicable: release tooling and CI only. |

## Cleanup

Removed the reviewer run after `lsof +D` returned no open files and the resolved path was confirmed under the project build directory. `du -sk` before removal reported 149432 KiB (153018368 bytes, allocated). Removal was confirmed; no reviewer cleanup failures are pending.
