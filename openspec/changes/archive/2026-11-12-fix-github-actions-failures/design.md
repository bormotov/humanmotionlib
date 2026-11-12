# Design

## Context

Versioned release currently calls Host Python and Python package independently for a reserved source SHA. The installed harness expects the caller layout covered by `tests/test_matrix_test_outcomes.py`, including a nested `.tmp` harness directory.

## Goals / Non-Goals

- Make build and upload the only first stage. Show Host Python and installed CLI/API results separately on Ubuntu 24.04 with the existing CPython and uv pins.
- Preserve checkout rejection, filesystem containment, test failures and artifact identity for both direct and reusable invocations.
- Scope the repair to CI setup, evidence and contributor checks and guidance. Generation, Blender and release policy are outside the repair. Both visual gates are not applicable because no visible source, character, scene, pose, motion or rendering behavior is changed. A correction that affects any of those returns to planning for the applicable visual gates.

## Decisions

1. **Use jobs within one CI run.** Make the package workflow the shared entry point for push, pull request and reusable calls. It runs the build job first. The build job checks out the selected ref, builds one candidate wheel and sdist, then uploads them with the wheel checksum. It reports the resolved checkout SHA and the uploaded artifact name as outputs. Host Python and installed package verification each depend on successful build completion via `needs` and can run in parallel. Remove the independent push and pull-request triggers from Host Python. Keeping the jobs in one run gives both consumers a direct dependency and a same-run artifact.
2. **Install the supplied wheel in each verification job.** Check out the build job's resolved SHA for the tests, lock and fixtures. Download its artifact by name, check the wheel checksum, and install that local file non-editably in a fresh external `uv venv` with the committed lock for host verification. Use `uv pip` and record the repository-required environment preflight before the first test. The external environment allows Host Python to use its existing checkout import guard. `make dev` remains the local contributor command. Retain the sdist rebuild and second-version build as test controls. Both verify separate build behaviors and have distinct outputs from the candidate. Log each job's checkout SHA, artifact and wheel hash, install identity and scoped results.
3. **Use disjoint external paths for package acceptance.** Place the external installation, invocation directory and caller workspace in disjoint locations. Allocate a fresh five-component element under the caller workspace's `build/` and put the harness in that element's `.tmp/installed-acceptance`, with fixture scratch under the same element's `.tmp`. Resolve role and scratch from the validated owning element. Keep real-directory, symlink, freshness and containment checks. Give the character installation check its own caller workspace.
4. **Reuse the checked candidate for Versioned release.** Call the chain once for the reserved commit. The publish job depends on successful completion of the chain and downloads the wheel using the artifact name reported by the successful build. Use the producer's actual upload name on retries, including when downstream jobs run in a later attempt. The publish job verifies the reserved commit and wheel checksum before using the existing release procedure.

## Risks / Trade-offs

- An absent or changed candidate artifact blocks the downstream check before test discovery or installed execution. Match the commit and wheel checksum from the successful build and retain the import origin in evidence.
- The installed harness may fail after its initial path check → Exercise it through its final structured outcome with its generated roots and existing negative cases. Test escaped and occupied locations with a positive control in the actual CI layout.
- The reusable caller's event SHA can differ from the selected commit, and reruns can reuse an earlier build. Verify both cases with the producer's output and the consumer's actual checkout and download.
- GitHub runner evidence needs a run for the candidate → Record any missing hosted evidence as pending. Local controls can establish the tested behavior and do not establish a hosted job result.

## Migration Plan

Land the CI and release wiring together with the harness fix. Verify the push route and audit the pull-request and reusable routes, including any repository settings that refer to named checks. Revert the repair as one change if its workflow contract regresses.
