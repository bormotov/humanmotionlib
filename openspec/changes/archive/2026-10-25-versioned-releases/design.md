# Design

## Context

See `proposal.md` for motivation and the two capability deltas for behavior. `pyproject.toml` declares `0.2.0`; `hml_build_backend.py` already derives generated runtime identity from it. Existing package CI builds wheel/sdist, checks payload parity and installs the exact wheel outside the checkout. Host CI provides locked tests. There are no local release tags or publication workflow; package CI still asserts literal `0.2.0`.

Design is needed because release reservation, concurrent main updates and partial GitHub publication cross repository and workflow boundaries.

## Goals / Non-Goals

**Goals:** one small release helper, one publication chain, reuse existing checks, and durable recovery without a queue service or extra credential.

**Non-Goals:** semantic interpretation of specification edits, arbitrary selection of commits, detached release branches, PyPI, automatic major releases, or renewed rendering/visual acceptance for version bookkeeping.

## Decisions

### 1. Acceptance and batching

Use `main` first-parent history and newly introduced archive roots containing `.openspec.yaml` under `openspec/changes/archive/` as acceptance markers. Existing archive edits and active changes are not markers. This is the machine-readable consequence of the existing ordered approval/review/archive process, not a second parser for natural-language approval. A `skip_specs` archive remains eligible.

Every acceptance triggers evaluation. A serialized worker discovers all pending archive identities since the last published boundary and may coalesce them into one release if main advanced before reservation. This concurrency default preserves simple automatic cadence while avoiding an artificial version for every closely spaced merge. Notes list every included change exactly once. All source content at the selected main snapshot is included; project governance must keep unaccepted behavioral implementation off main. Planning-only edits do not trigger publication, but any accumulated canonical spec difference contributes to the next triggered release.

### 2. Version and immutable bootstrap

Compare canonical specification path/byte inventories between the previous published release commit and selected main snapshot; any difference chooses minor, otherwise patch. Rename, deletion and editorial edits count. No classifier or commit-message convention is needed. `pyproject.toml` remains the sole authored version source; refresh only the root project version in `uv.lock`, without dependency upgrades. Generated `_version.py` remains build-owned.

Commit a fixed bootstrap SHA in the release configuration: the first-parent main commit immediately before introducing this automation, containing the existing `0.2.0` and historical archives. Resolve and record the concrete SHA during implementation; never infer it from moving main at execution time. It must be an ancestor, with the expected baseline version. Its old archives are excluded; this change's later archive is included, making the first managed release `0.3.0`. A bootstrap anchor conflicting with managed release history fails closed.

### 3. Reserve, check, publish in one workflow

Use a repository-wide concurrency group with running jobs not cancelled. Wakeups are hints; durable history is authoritative, so replacing a queued wakeup loses no changes. Support manual workflow rerun/dispatch for recovery without changing normal automatic cadence.

Fetch current main and published release metadata. Reconcile any unfinished managed reservation first. Otherwise select all pending accepted changes, compute the version and create a metadata-only release commit updating `pyproject.toml` and `uv.lock`. Its structured Git trailers record version, prior published/bootstrap boundary, selected input SHA and included archive identities/acceptance SHAs. Push only as a fast-forward compare-and-swap against that input SHA; if main moves, discard the unpushed candidate and recompute. No force push. The successful commit is the reserved immutable candidate.

In the same workflow, explicitly run reused host/package verification on that candidate SHA. A bot-authenticated push/tag must not be relied on to trigger follow-up workflows. Adapt check entry points to accept that ref and expected version; use the existing pinned actions/runtime. On success retain the wheel/checksum tied to candidate SHA and workflow attempt, create a matching tag and draft Release, upload exactly that wheel plus `SHA256SUMS`, then publish the Release. Notes contain the durable boundary and verification identity. Uploaded sdist remains unnecessary; its parity check remains required.

### 4. Recovery and permissions

The newest managed reservation in main history plus matching tag/draft/published Release identifies progress. Resume it before allocating a later version. Before a checked artifact is reserved, checks can run again on the same candidate; once tag/draft evidence binds a checksum, reuse that artifact or stop if evidence is unavailable. A matching completed release is a no-op; conflicting targets/assets fail without replacement. After success rescan current main for pending accepted work.

Use the existing ephemeral workflow token with scoped `contents: write` only where mutation is required; checks retain read access. Document required Actions settings and allowed bot version commits under branch rules. Do not bypass protection or silently introduce a PAT. A denied write leaves a failed, recoverable operation with no successful release.

## Risks / Trade-offs

- Byte-based spec comparison causes minor bumps for typos; this is the deliberately simple policy.
- Archive markers trust the existing human/reviewer process; publication does not certify missing acceptance.
- GitHub operations are not atomic; reservation trailers, draft state and checksum reconciliation make partial failure explicit.
- A failed reserved release temporarily advances main's declared version; later work waits for recovery rather than skipping the reserved version.
- Hosted verification covers the host/package contract only; notes explicitly retain that scope.

## Migration Plan

Generalize fixed current-version assertions while retaining historical migration documentation. Add and test helper/workflow/configuration without creating a historical tag or publishing during development. Document enablement and recovery commands in `tools/README.md` and version policy/installation from Release in `docs/usage.md`. Archive this change only after the existing review gate; its main integration is the first normal trigger.

Independent developer/reviewer runs use fresh roots such as `build/versioned-releases_r1_dev_try-1_checks/` and `build/versioned-releases_r1_reviewer_try-1_release/`. Their hand-offs inventory retained evidence and dependencies, remove obsolete owned runs, and record bytes/paths and pending cleanup. No scene/data/rendering change is planned, so no new contact sheet, GIF or onion-skin pack is required; the acceptance pack is the release dry-run report, candidate wheel identity, mocked publication/retry evidence and workflow audit. External tools/references actually used must be commercially cleared and registered before use; reuse existing cleared toolchain where possible.
