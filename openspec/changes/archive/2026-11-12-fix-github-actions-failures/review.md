# Independent review

Verdict: **PASS WITH NOTES**. The frozen candidate and the release handoff are supported by the combined hosted and local evidence below. The controlled release consumer itself failed because of a test-only path error; production release execution and actual publication were deliberately not performed. Reviewer-owned cleanup is complete as recorded below.

## Candidate and evidence

- Base commit: `99b7dd10cb45f3221fc696a581bf6abffe7c45fe`; the implementation remains uncommitted. Candidate identity and subsequent package re-freeze are recorded in `handoff.md`.
- Exact reviewed wheel: SHA-256 `463772923b3c0d0081cb792d0402d4471220533a057121bc34e769ca1b90a8dd`, from `build/package-humanmotionlib_r1_dev_run-20261107t181850384988-87576_package/direct/`.
- Independent non-editable uv installations used CPython 3.14.6 on macOS, locked dependencies, writable reviewer-owned caches and fresh environments. Pre-test import origins, versions, `.pth` contents, paths, wheel hash and `uv pip check` are in the respective `preflight.json` files. Process inspection was verified with `ps` under the same elevated privileges used for supervised checks.
- Installed acceptance passed with exit 0, including selected workspace, source and integrity, misleading neighbors, write escape, symlink and presentation controls: `build/fix-github-actions-failures_99b7dd1_reviewer_try-4_review/installed.log` and its structured result. This is host-only; no Blender was launched.
- Installed character acceptance passed 7/7: `build/fix-github-actions-failures_99b7dd1_reviewer_try-6_review/character.log`.
- Focused workflow, acceptance ownership and release tests passed 38/38: `build/fix-github-actions-failures_99b7dd1_reviewer_try-7_review/focused.log`. Workflow tests inspect structure; they do not execute the GitHub job graph.
- An independently built earlier wheel `99f03cb41bcf3d733efd134dc486d9db57800263d28476eba841b4a218f4eb99` and the reviewed wheel contain identical bytes for all 124 ZIP members, including resources and RECORD; `build/fix-github-actions-failures_99b7dd1_reviewer_try-4_review/payload-comparison.json`. Different wheel hashes and their execution evidence remain distinct.
- The earlier full host suite completed against the earlier wheel in reviewer `try-3`: 526 tests, exit 0, seven expected installed-character skips; the latter ran separately on the reviewed wheel. Its results are not relabelled as the current wheel's result. An earlier `try-1` was interrupted because temporary paths were not constrained; `try-2` finished with 35 setup errors caused by an incorrectly selected reviewer test root. Character attempts `try-4` and `try-5` lacked, respectively, the poison file and `pyproject.toml` in the reviewer-created decoy; `try-6` supplies both and passes. These are review setup failures, not product findings.

## Requirements and scenarios

| Requirement / scenario | Method and result |
| --- | --- |
| Host environment contract: clean host job and uploaded wheel | Hosted Ubuntu job passed with 527 discovered, 519 passed and 8 explicitly reported skips; wrong-interpreter, stale-lock and failed-test controls are not established by that run. |
| Artifact build and dependent verification jobs | Hosted build/upload and both dependent checks passed. Controlled build and upload failures each caused both dependent checks to skip, as detailed below. |
| Exact installed wheel and package closure | Hosted installed job passed including sdist rebuild parity and its seven character tests; logs identify the same wheel hash as host evidence. |
| Installed wheel independent of checkout | Hosted installed acceptance passed, alongside the earlier independent local API/CLI, character, workspace and tamper checks. |
| Acceptance ownership and rejected layouts | Hosted installed acceptance and local positive, escape, symlink and occupied-location tests pass. |
| Reusable caller and exact reserved revision | Hosted reusable caller used a different event SHA, and a rerun host job downloaded the original producer artifact; a later dry consumer also downloaded it but failed its test-only wheel glob. A local audit of that artifact using the production recursive guard passed. Publication-blocking controls exercised surrogate jobs; production release workflow was not executed. Details below. |

## Findings

| ID | Severity | Requirement / scenario | Evidence and direction |
| --- | --- | --- | --- |
| — | — | No unresolved product defect identified | The controlled run failure and evidence boundaries are recorded below. |

The used-materials register records the pinned GitHub actions and their MIT licenses, including the expanded artifact-transfer usage. No new visual asset, motion, scene or render behavior was introduced; visual review and both visual gates are not applicable. Real Blender acceptance is outside this review.

## Cleanup and open work

Reviewer-owned runs `try-1` through `try-9` were cleaned after the checks; paths cited above identify historical local evidence that is no longer retained. See the cleanup record below. Later sections contain the hosted control evidence and its limitations.

## Subsequent host fixture corrections

The two host fixture tests corrected after hosted run `42435197451` were independently rerun from a source copy of commit `76cc160a59c211414a57c28817dbe1b0e30e6238`, using a fresh uv environment and the wheel identified above. Both passed (2 tests, 3.176 s): `build/fix-github-actions-failures_1bf07d7_reviewer_try-8_review/focused.log`. The cleanup test selects a hermetic PATH with no Python or uv, proves populated cleanup and repeated empty cleanup; the release test starts with a bare repository initialized using `master`, sets its HEAD to `main`, and checks the clone's commit and bootstrap file before its existing compare-and-swap scenarios. The environment preflight was in the same reviewer root, since removed as recorded below. This local evidence does not replace the controlled hosted scenarios.

## Hosted push evidence

Independently inspected run [42473535328](https://github.com/bormotov/humanmotionlib/actions/runs/42473535328), attempt 1: checkout `76cc160a59c211414a57c28817dbe1b0e30e6238`; build, host and installed jobs succeeded. Both downstream logs identify artifact `humanmotionlib-76cc160a59c211414a57c28817dbe1b0e30e6238-42473535328-1` and wheel SHA-256 `3f9742ebe7770ee0d3f8728287a9166bbc6299da96cc734b0320bd3dd66c0704`. The host evidence archive was independently downloaded to `build/fix-github-actions-failures_76cc160_reviewer_try-9_hosted/host-evidence`; it contains the 16 allowed diagnostic files, no generated `cases/` or `build/`, and a matching candidate checksum. `host-checks.json` records 527 discovered, 519 passed, zero failures/errors, eight named skips, and seven excluded real-backend tests. Seven skips are installed-character cases executed by the installed job; the eighth, real process cwd/open-file cleanup, was skipped because the opt-in variable was not set. Hosted `ps` preflight succeeded, but the skipped test is not hosted proof of real process-inspection permissions or cleanup behavior. Earlier local opt-in reviewer evidence applies to its own identified environment. The hosted candidate wheel archive itself was not independently downloaded; the hash is corroborated by the host evidence and both job logs. Reviewer `try-9` was removed as recorded below.

## Controlled build and upload failures

Independently inspected [run 43057432689](https://github.com/bormotov/humanmotionlib/actions/runs/43057432689), push fixture `76e9e3658a99ea10afb382c7d5ea72ba01719537`. The caller invokes candidate `package.yml` at immutable `76cc160a59c211414a57c28817dbe1b0e30e6238` with fixture source. Compared with the candidate, the fixture adds a branch-only caller, suppresses duplicate direct push for control branches and deliberately invalidates `uv.lock`. Checkout, Python, uv and allocation passed; `uv lock --check` failed on the malformed TOML, upload was skipped, both downstream jobs were skipped, and the run failed. The failure is the intended fixture, not a defect asserted against the candidate.

Independently inspected [run 43064239805](https://github.com/bormotov/humanmotionlib/actions/runs/43064239805), push fixture `7732d04cc9b8f96231ed6698d5089704439d2d41`. Its only candidate diff limits its push trigger to the control branch and changes upload to a deliberately absent file; the real job graph and `if-no-files-found: error` remain unchanged. Lock validation and actual wheel/sdist build succeeded. Upload failed specifically because `control-missing-upload.bin` did not exist; both verification jobs were skipped and the run failed. The successful candidate run above supplies the positive control. These tests establish task 1.2's failure-gating behavior, not the release-handoff/retry cases.

## Surrogate release gate controls

Independently inspected [run 43070584010](https://github.com/bormotov/humanmotionlib/actions/runs/43070584010), commit `c21ce9d55f9a7d3ccefed827e1e347cb2b949ea5`. The host-failure fixture failed while its installed-check counterpart passed; the installed-failure fixture failed while its host-check counterpart passed. Both respective aggregate and publication jobs were skipped. In the missing-artifact fixture, the download failed, the simulated publication receipt was skipped, and its assertion passed. The positive fixture uploaded and downloaded a marker and wrote its simulated receipt. The final observer passed. The overall run conclusion was the expected failure from deliberately failing fixtures.

These are surrogate jobs exercising GitHub scheduling and artifact download behavior; they do not execute the production release workflow or publish a release. They do not by themselves establish the actual release handoff or retry scenarios; see the combined audit below.

## Release handoff artifact inspection (pending hosted log audit)

The orchestrator supplied an extracted artifact at `/private/tmp/hml-release-artifact-43065111067`. Its `summary.txt` records source `76cc160a59c211414a57c28817dbe1b0e30e6238`; one wheel is present under `distributions/` and one `wheel.sha256` at the artifact root. An independent local check followed the production publish guard's recursive `find`, single-file counts and digest comparisons, substituting macOS `shasum -a 256` for the runner's `sha256sum`: both the wheel and sidecar report `873c3cefd8af7ceb333d16d4df6f530d80fdea682ed7664c9dba80e77c7fe23c`. The source equality check used the value recorded in the supplied summary; its linkage to GitHub job outputs and the identity of the downloaded artifact require the hosted logs. This check did not execute the production release workflow or publish a release.

The test consumer's top-level wheel glob differs from the production guard's recursive `find`; its failure on the `distributions/` layout cannot be reported as a successful consumer run.

## Hosted retry and combined handoff audit

Independently examined the orchestrator's exported job logs and job lists in `/private/tmp/hml-evidence-43065111067/`. Run [43065111067](https://github.com/bormotov/humanmotionlib/actions/runs/43065111067) used event SHA `b20dd1e6f1ddb08956523f1b1804136169190e3e` and selected source `76cc160a59c211414a57c28817dbe1b0e30e6238`. The producer log records upload of artifact `humanmotionlib-76cc160a59c211414a57c28817dbe1b0e30e6238-43065111067-1`, ID `13874867873`. Attempt 1 built and passed installed checks; its host job failed while uploading evidence and the consumer was skipped. The attempt 2 job listing repeats the original build and installed start/end times, while the host and consumer have later times. Although GitHub assigns different job IDs in the two attempt listings, their matching original timestamps and artifact `-1` show that the original producer output was reused rather than a fresh build being reported.

The successful attempt 2 host log and the successful attempt 1 installed log each identify the same source, expected wheel SHA-256 `873c3cefd8af7ceb333d16d4df6f530d80fdea682ed7664c9dba80e77c7fe23c`, and downloaded artifact ID `13874867873`. The host suite reports 527 tests, zero failures and eight skips. The dry consumer, starting after those checks, recorded the distinct event/source SHAs and successfully downloaded that same artifact ID. It then failed its own nonrecursive root-level wheel glob: the wheel is in `distributions/`. Thus the workflow run itself concluded failure and no dry success receipt was produced. The local production-equivalent recursive guard check above independently verified the actual extracted wheel and checksum against the producer output; it is a separate audit, not a successful hosted execution of the guard. Along with the earlier surrogate negative controls and production graph inspection, this supports the bounded artifact handoff assessment without asserting production release execution, reservation, or publication.

The temporary downloaded artifact and exported logs are orchestrator-owned and were not included in reviewer cleanup.

## Reviewer cleanup

After the evidence audit, process visibility was checked using `ps` and `lsof` with elevated access. No matching active process or open file was found. Each selected direct child was checked to be a real directory with resolved parent `build/`; traversal and size accounting did not follow symlinks. All nine reviewer-owned roots were removed; sizes are summed `lstat` byte sizes of their contents and are not claims about disk blocks reclaimed:

| Removed direct child of `build/` | Bytes |
| --- | ---: |
| `fix-github-actions-failures_1bf07d7_reviewer_try-8_review` | 56,346,344 |
| `fix-github-actions-failures_76cc160_reviewer_try-9_hosted` | 206,334 |
| `fix-github-actions-failures_99b7dd1_reviewer_try-1_review` | 53,050,781 |
| `fix-github-actions-failures_99b7dd1_reviewer_try-2_review` | 55,260,105 |
| `fix-github-actions-failures_99b7dd1_reviewer_try-3_review` | 5,427,072,463 |
| `fix-github-actions-failures_99b7dd1_reviewer_try-4_review` | 1,001,487,357 |
| `fix-github-actions-failures_99b7dd1_reviewer_try-5_review` | 196,451,784 |
| `fix-github-actions-failures_99b7dd1_reviewer_try-6_review` | 196,452,055 |
| `fix-github-actions-failures_99b7dd1_reviewer_try-7_review` | 57,098,274 |

Pending reviewer cleanup failures: none. No other role's paths were removed.

The developer reports completing cleanup of all 35 assigned roots after an earlier partial failure in `try-31_checks`; the retry removed its remaining 834 bytes and the root. The bytes already removed in that interrupted first pass were not recorded and cannot be reconstructed from the remaining files. This accounting limitation remains open: the reported 4,756,642,985 bytes covers only the completed pass and is not the total across both passes. The failed removal itself was resolved by the completed retry, so this limitation does not prevent completing the independent review task; it must remain visible in the hand-off and must not be reported as a fully measured total.

The retained hosted evidence at `evidence/hosted-42473535328/` contains 16 files totalling 205,758 bytes, as recorded before developer cleanup. Its candidate checksum is `3f9742ebe7770ee0d3f8728287a9166bbc6299da96cc734b0320bd3dd66c0704`, matching the independently reviewed hosted candidate. This checks the retained inventory and identity; it does not reconstruct the unavailable partial-cleanup byte count.
