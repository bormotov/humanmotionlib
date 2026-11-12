# Tasks

## 1. Candidate build and artifact handoff

- [x] 1.1 Create the build job for push, pull request and reusable calls. Verify that a clean build uploads one candidate wheel and one sdist with the checksum and reports the actual checkout SHA and artifact name.
- [x] 1.2 Make both verification jobs depend on successful build and upload. Remove duplicate standalone push and pull-request triggers. Verify the job graph and use controlled build and upload failures to confirm both checks are skipped and the workflow fails.

## 2. Verify the supplied wheel

- [x] 2.1 Install the downloaded wheel with the locked dependencies in the Host Python job's fresh external environment. Verify package import origin, interpreter, preflight, source validation and host-only discovery. Check that a missing or mismatched artifact or a checkout import fails before discovery.
- [x] 2.2 Fix installed acceptance ownership and scratch allocation. Verify that the CI and existing matrix layouts pass and that escaping, symlinked and occupied run locations fail before generation.
- [x] 2.3 Run installed CLI/API and character installation checks against the downloaded wheel in a fresh external environment. Verify scoped logs, sdist parity, the second-version control and existing workspace, decoy and tamper cases. Update the workflow guidance for the new job and artifact layout and verify any changed documented commands.

## 3. Release handoff and candidate review

- [x] 3.1 Call the shared chain for the reserved release commit and download the artifact reported by its build only after both checks succeed. Verify a reserved SHA different from the event SHA, a downstream retry using the original upload, and blocked publication on either failed check or missing artifact. Use a controlled case without publishing a release.
- [x] 3.2 Complete the joint pre-freeze audit and record source/package identity, unresolved findings and why visual gates are inapplicable. Confirm clearance for any newly used external material and update register entries where action usage changes.
- [x] 3.3 Verify the frozen candidate on GitHub with CPython 3.14 on Ubuntu 24.04, including the complete host-only suite and installed package checks. Inspect the pull-request trigger and record the run, checkout SHA, matching wheel checksum, job results and logs. Keep unavailable hosted evidence pending and separate from local results.
- [x] 3.4 Independently review both specs against the frozen candidate and deliver `review.md` with evidence and a verdict. Use fresh direct `build/` children named `fix-github-actions-failures_<revision>_<role>_<attempt>_<kind>/` in the applicable workspace and audited `uv venv` installs where needed. Record role-owned cleanup, removed paths and bytes, and pending failures.
