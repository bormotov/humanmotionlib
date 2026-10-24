# Review: versioned-releases

## Verdict

**PASS WITH NOTES** — no open findings. Independent checks cover all eight requirements and fourteen scenarios in the two deltas. No live release was published and no visual correctness is approved by this review.

## Candidate and reproduction

- Base commit: `35aa4bb8aa8c196dc3da2d5f7653ec5e817aa23e`.
- Reviewer run: `build/versioned-releases_35aa4bb_reviewer_try-1_release/`.
- Final 228-file snapshot inventory SHA-256: `841a0eaa8a4f4a8b315b080493c75e0a7b95555e5604d9f811efefbc195f44a9`.
- Candidate copied from tracked and nonignored untracked sources into the owned `source/` fixture. Tests, temporary files, environments and synthetic Git repositories stayed under this run. No developer/shared build state was modified.
- `docs/used-materials.md` related-output completeness was corrected during review. That single bundled-resource update was copied into the final snapshot and both actual wheel builds/installations, parity and installed acceptance were rerun. Other functional source hashes remained unchanged.

## Results

| Check | Independent result |
|---|---|
| Locked host suite | 226 passed in 184.450 s; zero skipped; seven explicitly excluded real-Blender tests |
| Release/version suite | 22 passed in 14.785 s, covering selector, bootstrap, CAS, pending work, identity conflicts and partial publication |
| Distribution matrix | Actual wheels 0.2.0 and 0.91.7 built and installed noneditably outside the checkout; metadata/Python/CLI/runtime manifest agree |
| Resource invariance | Same 51 resource-file hashes for the two versions |
| Source distribution | Rebuilt wheel matches all 94 logical package-file hashes |
| Installed acceptance | Pass: two invocation directories, 900 prepared samples, public API, numeric verification, presentation-only modes and integrity/write-containment failures |
| Source schemas | 180 structures, 67 actions, 3 placements, 32 fixtures valid |
| Workflow audit | 20 Bash blocks and four Python heredocs syntax-valid; exact candidate/artifact identity, required checks, serialization and bounded permissions verified |
| Production REST adapter | 29 in-memory REST requests using actual client serialization and list-shaped API assets; two sequential versions 0.2.1/0.2.2, safe no-op retries and real nonancestor Git boundary rejection |
| Fixture isolation | Backend ambiguity/sentinel, queued signals, abandoned receipt and two-caller serialization assertions remain in place and pass; runtime implementation unchanged |
| Licensing/scope | New pinned download-artifact action has verified MIT permission and register entry; reused cleared action outputs updated. No runtime dependency, source data, scene or generation algorithm change |

Full requirement/scenario evidence is in [scenario-checklist.json](../../../../build/versioned-releases_35aa4bb_reviewer_try-1_release/scenario-checklist.json). The reviewer-owned [pack index](../../../../build/versioned-releases_35aa4bb_reviewer_try-1_release/index.md) links every retained proof artifact.

## Findings

| ID | Severity | Violated requirement/scenario | Evidence | Suggested direction |
|---|---|---|---|---|
| — | — | None open | All listed checks pass | — |

The early unrelated-draft/unmanaged-boundary/checksum-diagnostic observations were fixed before this frozen review; their regression cases pass. The register-related-output note was resolved and its affected packaging checks repeated.

## Scope limits and human decision

Live GitHub execution and actual branch/Actions permission settings were not exercised; local Git histories, realistic REST fixtures and static workflow dependency/permission checks satisfy this change's nonpublishing review plan. First normal publication is the documented follow-up after acceptance/archive. Real Blender rendering, frame metrics and visual packs are not applicable because runtime/data/scene/rendering behavior is unchanged. No human visual question is pending for this tooling-only change; existing visual gates for future motion changes remain required.

## Cleanup

Removed **1,729,417,320 bytes** of obsolete candidate copies, disposable environments/cache, raw test inputs/reports and redundant install fixtures only within the owned reviewer run. Exact paths/bytes and reasons are in [cleanup-receipt.json](../../../../build/versioned-releases_35aa4bb_reviewer_try-1_release/cleanup-receipt.json). Retained: frozen sources, checked wheels/sdist, compact installed evidence/receipt/HTML dependency closure, source/checksum inventories, scenario/workflow/license reports, command transcripts and local fault fixtures for reproduction. Dependency checks after cleanup all pass; no external symlink was followed and no other agent's run was touched. **Pending reviewer cleanup: none.**

## Accepted developer cleanup metadata deviation

On 2026-10-25 the human explicitly accepted the developer's cleanup metadata deviation for the removed `build/versioned-releases_r1_dev_try-10_host/` run: its exact removed byte count is irrecoverable and is recorded as **bytes unknown** in the developer hand-off. This exception concerns that developer-owned run only. The reviewer-owned cleanup above is complete, with exact removed paths/bytes and no exception; the verdict and absence of open code findings are unchanged.
