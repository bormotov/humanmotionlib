# Proposal

## Why

A contributor needs to build one character at one height, check its files and repeat either command after an error. The existing matrix design combines that small job with package preparation, generic execution plans, comparison workflows and process management, making both implementation and manual use unnecessarily complex.

## What Changes

- Provide only `matrix-list`, `matrix-build CHARACTER=... HEIGHT=...` and `matrix-check CHARACTER=... HEIGHT=...`. The fixed table is skeleton/male/female × H1.50/H1.70/H1.90; every row generates neutral, rest and arm-raise at 120 BPM in existing render-only mode, with static PNGs and assembled presentation. This is the human-selected short set, not full character acceptance.
- Use one predetermined result directory per character and height. Each build runs preparation, generation and required presentation in order through existing APIs. Each check reads and checks that current result through existing validators.
- **BREAKING:** Remove the matrix plan/candidate/action/recipe protocol, selective continuation, custom status command, UUID work trees, publication copies, latest pointers and generic report/allocation machinery. One installed offline environment is a prerequisite, not something a matrix action constructs or repairs.
- Repeat an action completely at the same paths. Preserve only one ordinary log file per past attempt; replace current data and small build/check results, and remove temporary or failed generated data.
- Treat accidental overlapping commands as operator errors. Add no concurrency support, owner discovery, locks, or successful-overlap requirement.
- Keep existing backend supervision and generation/validation assertions. Package testing, host/installed acceptance, cross-stature comparisons, baseline/determinism review packs and backend hardening remain separate existing tools and work, rather than matrix actions.

## Capabilities

### New Capabilities

- `build-verification-matrix`: a fixed character/height table with complete manual build and check commands, stable current data and log-only attempt history.

### Modified Capabilities

- `build-artifact-lifecycle`: allow stable matrix result roots using the existing five-component outer names, with replacement of current content and retention of log files.
- `public-generation-api`: retain the narrow explicit destination binding already agreed for generation inside stable matrix roots; standalone fresh-run defaults remain unchanged.

## Impact

The contributor runner, Make aliases and guide become thin adapters around existing APIs and validators. They no longer own package installation or another process supervisor. No new dependency, canonical pose/motion, scene, character geometry, numerical tolerance or renderer setting is introduced.

Existing package and domain acceptance commands retain their requirements outside this change. Removing them from the matrix does not declare them unnecessary or passed. The paused character change, accepted R6 and historical evidence remain untouched. The known backend PGID safety finding remains unresolved separate work; this change neither weakens backend safety requirements nor claims to fix it. Implementation must inventory old generated data before any cleanup.
