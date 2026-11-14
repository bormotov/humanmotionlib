# Design

## Context

The production publisher can select a commit from an earlier release reservation. The control branch at `83eff17` completed build, fresh wheel installation, host and character installation tests, and tested-wheel artifact upload in GitHub Actions run `43491819554`. Earlier controls showed that a failed test prevents the final upload. These runs establish the exercised build, test and artifact handoff. GitHub Release creation is a separate path to verify.

## Decisions

### Build and test the triggering revision

Use the package workflow as the entry point for pushes and pull requests. Check out the pushed SHA for a push and use the existing selected revision for a pull request. Build one wheel and expose the producer artifact name, wheel filename and SHA-256 as build outputs. Job dependencies ensure a successful upload precedes tests and successful tests precede publication. A later push uses its own build and test results.

Install the received wheel non-editably in a fresh supported CPython environment outside the checkout. Check its filename and SHA-256 before installation and before publication. Log the name and checksum at each handoff. Reuse the build job's artifact output on downstream reruns, including when the runner increments the attempt number. A missing artifact fails the consumer. Tests share the installed wheel and retain their existing product assertions and named backend exclusions. Test success is the verification result for publication. The dedicated version, package inventory, source validation, environment report and source-distribution parity steps are removed from this workflow. The local `make package` checks remain governed by their existing specification.

Carry over the control branch's creation of `build/` for test fixtures and run the installed character suite from a caller directory disjoint from the virtual environment. Carry over the fixture restoration in `test_character_review_pack.py`. Adapt the workflow and package version assertions that conflict with the new CI contract. Keep coverage of version reporting, resources, imports and test integrity under the applicable product requirements. Reconcile overlapping changes in the existing implementation worktree before electing which edits to keep.

### Gate GitHub Release creation

Evaluate publication after successful verification and only for a fast-forward push to `refs/heads/main`. Compare `project.version` from the original push's `before` and pushed revisions as numeric `0.MINOR.PATCH` values. Use the event range for a push with multiple commits. A same-version push, downgrade or missing usable predecessor cannot request publication. An eligible rerun uses the original event and artifact. The contributor chooses the version and updates the committed lock. Build and test jobs do not depend on the publication decision.

Use a single write-capable job, serialized with other publication attempts. After it receives the slot, use the current published boundary for archive attribution and skip versions that are already published or lower than the latest published version. Keep the existing `0.2.0` bootstrap when no managed release exists. An archived change belongs to a release if it is within that release's checked snapshot and after the preceding published or bootstrap boundary. A historic reservation without a public release cannot serve as a boundary. Reuse existing archive discovery and release formatting where they satisfy this contract.

Tag the tested commit and publish the original wheel with `SHA256SUMS`. Use the existing release notes format to identify the checked commit, verification run and included archives. Existing public releases and conflicting tags are immutable. On retry, use the original eligible run and tested artifact. Reuse a tag only if it already points to that exact commit. Resume or reject an incomplete publication without touching an unrelated draft or replacing different existing bytes. Use the GitHub release lifecycle directly and keep only the collision handling needed for those guarantees.

### Cut over the publisher

Remove the separate release workflow triggers and the reservation and automatic version-writing paths. Retain historical commits and public releases, and update contributor instructions for choosing a version, pushing to `main` and retrying the original qualifying run. At deployment, confirm the retired publisher has stopped and that its old triggers will not run alongside the replacement. This is a one-time migration check. The deployment itself can use the version already on `main`.

## Verification

Exercise version and publication decisions using disposable Git histories and controlled release state. Reuse applicable evidence from the control branch with its original identity. Verify the revised workflow locally and in a controlled hosted run. Record what the hosted run verifies and what remains covered by simulation. Only an authorized production version bump can establish actual public publication.

Use fresh, disjoint run roots following `build/publish-releases-from-version-bumps_<revision>_<role>_<attempt>_<kind>/` for independent build, check and review work. Keep role cleanup and source clearance under the project rules. The early and final visual gates are not applicable to this CI and release change.
