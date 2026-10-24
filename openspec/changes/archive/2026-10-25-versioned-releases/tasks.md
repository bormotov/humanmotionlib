# Tasks

## 1. Release selection and version consistency

- [x] 1.1 Add a contributor release helper with fixed bootstrap configuration, first-parent archive discovery (including `skip_specs`), pending-change selection and canonical spec inventory comparison. Verify synthetic histories cover historical exclusion, this change's first `0.3.0`, patch/minor/editorial/delete/rename cases, no-op and invalid boundaries/versions; document policy and helper commands in `tools/README.md`.
- [x] 1.2 Generalize current-version assertions in package CI and affected runtime tests; preserve intentional historical/fixture `0.2.0` references and generated runtime identity. Verify two declared-version builds report matching wheel metadata/Python/CLI/runtime manifest and unchanged canonical resources; update current-version usage text in `docs/usage.md`.

## 2. Reservation and checked publication

- [x] 2.1 Implement main reservation through version/lock-only commits with durable trailers and fast-forward compare-and-swap; reconcile reservations before later work. Verify interleaved main advancement, queued-wakeup replacement, coalesced changes, pending-after-reservation and interrupted reservation fixtures prove no overwrite or lost accepted change; document trailer/recovery behavior.
- [x] 2.2 Add one serialized release workflow reusing locked host/package verification on the exact reserved SHA and carrying the checked wheel/checksum into publication. Verify workflow/ref/permission audit and failure cases prevent publication after failed checks; document required branch/Actions settings and no permanent token assumption.
- [x] 2.3 Implement immutable tag/draft/assets/final Release reconciliation with wheel plus `SHA256SUMS` and notes naming all covered changes and verification scope. Verify mocked GitHub/local-Git fault tests at each publication boundary, matching reruns, conflicting tags/assets, unavailable evidence and denied writes; document retry and failure commands without publishing a development release.
- [x] 2.4 Check commercial/derivative clearance for every new external reference, action or tool actually used and update `docs/used-materials.md` when necessary. Verify exact source/license/conditions/date/output entries against the source-use inventory; no uncleared material or new runtime dependency enters the change.

## 3. Independent integration review and hand-off

- [x] 3.1 Developer runs the integrated host/package suite and synthetic release dry run in fresh `build/versioned-releases_r1_dev_try-1_checks/` (new attempt on retry). Verify full scenario coverage, exact checked-wheel checksum and source-to-release identities; record results and dependency-aware cleanup in `developer-handoff.md`, including removed paths/bytes, retained reasons and pending work.
- [x] 3.2 Reviewer independently checks every delta scenario from clean sources in fresh `build/versioned-releases_r1_reviewer_try-1_release/`, builds/installs a candidate wheel and audits workflow publication boundaries, source clearance and unchanged generation scope. Deliver `review.md` and a review pack with dry-run histories, checksum/version evidence, fault outcomes and documented permissions; record cleanup/dependencies and any findings against named requirements. No live release or new visual pack is required for this tooling-only review.

## Workflow follow-up

- After implementation and independent review are accepted, archive through the existing OpenSpec process and integrate the accepted archive on `main`; publication requires no additional manual release approval.
- Observe the first normal release and verify `v0.3.0`, checked wheel, `SHA256SUMS` and notes identify this change and its release commit. Repository permission failures remain explicit operational blockers rather than bypasses.
