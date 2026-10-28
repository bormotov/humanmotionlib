# Proposal

## Why

A visually unsuitable character, pose or motion can currently reach full diagnostic matrices and repeated renders before the human sees a reviewable result. A bounded early visual decision will reject an unsuitable visual direction before those costly checks, while retaining complete independent verification of the accepted direction.

## What Changes

- Add an explicit early human visual gate for changes affecting poses, motions, visible characters, scenes or rendering.
- Require a small reproducible preview and the checks necessary to create it safely before that gate; defer full regression matrices, dense audits and repeated render comparisons until the human explicitly accepts the preview.
- Record preview scope, source/package identity, artifacts, limitations and the human's decision; regenerate and resubmit after relevant visual changes or rejection.
- Preserve OpenSpec Gate 1, source clearance before use, the pre-freeze audit, independent final verification, final Human Gate 2 and cleanup obligations.
- Apply the new ordering prospectively to unfinished work without relabeling existing evidence or inferring a past visual decision.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project-governance`: Add the early visual gate and its workload boundary to the ordered development lifecycle.

## Impact

The implementation updates `AGENTS.md`, the architect/dev/reviewer instructions and contributor workflow guidance. It changes process order, not runtime APIs, sampling, schemas, model geometry, numerical tolerances, dependencies or package-identity rules. This governance-only change requires no Blender render or new external reference material; its verification uses instruction audits and workflow scenarios.
