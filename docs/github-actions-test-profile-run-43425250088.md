# GitHub Actions test profile: run 43425250088

## Source and outcome

- Workflow run: [43425250088](https://github.com/bormotov/humanmotionlib/actions/runs/43425250088)
- Test job: [131885105172](https://github.com/bormotov/humanmotionlib/actions/runs/43425250088/job/131885105172)
- Source: the job log and its `TEST_PROFILE` lines, retrieved on 2026-11-13.
- Host-only suite: 525 tests in 13,225.383 seconds (3 h 40 min 25 s); 8 skipped.
- The host-only suite passed. The later installed-wheel acceptance step ran 7 tests in 102.200 seconds and failed one test, `test_origin_registry_closure_is_from_noneditable_site_install`; see the workflow log for that separate failure.
- The artifact publication step was skipped after the acceptance failure.

## Profile results

The test instrumentation reports elapsed seconds. The slow dense surface audit dominates the selected surface checks.

| Profiled work | Case | Total | Main measured phases |
|---|---|---:|---|
| `test_selected_male_and_female_accept_complete_host_oracle_numeric_evidence` | male | 2,116.18 s (35.3 min) | dense surface audit 1,962.22 s; native midpoints 15.09 s; build evidence 60.38 s |
| same test | female | 2,111.13 s (35.2 min) | dense surface audit 1,955.77 s; native midpoints 15.21 s; build evidence 61.31 s |
| `test_selected_surface_rejects_tampered_and_missing_dense_midpoint_evidence` | tampered dense | 2,148.21 s (35.8 min) | dense surface audit 1,990.21 s; native midpoints 15.26 s; build evidence 61.51 s |
| same test | missing dense | 2,134.27 s (35.6 min) | dense surface audit 1,977.54 s; native midpoints 14.94 s; build evidence 63.10 s |
| `test_actual_diagonal_preflight_runs_focused_dense_once_and_rejects_coherent_dq_fault` | skeleton + male + female | 1,626.31 s (27.1 min) | diagonal preflight 1,514.81 s; prepare 56.01 s; evidence building 55.48 s; verify calls: skeleton 2.61 s, male 740.96 s, female 748.51 s |

Other `TEST_PROFILE _make_surface_run` records show evidence-build totals between about 60 and 63 seconds in the selected surface tests. Inside those records, key-row generation and surface-pose calculations are the largest reported pieces; file writing/receipt is also material. In the focused preflight, evidence generation was about 54 seconds for surface data plus about 2 seconds for skeleton data.

## What this suggests

For the profiled selected surface checks, almost all elapsed time is in `_run_dense_surface_audit`, not preparation, midpoint checks, or evidence writing. The positive male/female check and the two negative male scenarios each repeat a dense audit taking roughly 32–33 minutes. The focused diagonal preflight spends about 12.4 minutes on each male/female verification call, about 25 minutes combined.

This makes the dense surface audit the first optimization target. Before changing it, profile its internal operations (for example, vertex transforms, skinning, and contact-distance calculations) while preserving the independent expected-value checks. Parallel jobs could reduce wall-clock time for independent cases, but would increase concurrent runner usage and would not reduce total compute.

## Limits

- Timings describe this single GitHub-hosted run and will vary with runner performance and load.
- `TEST_PROFILE` phase values can be nested or overlapping; do not add phase values to derive a total. Use each explicit `total_s` field for the case total.
- The log does not reveal how much of `_run_dense_surface_audit` is Python arithmetic versus file handling without additional profiling.
- This report records measurements only; it does not establish a speedup target or authorize reducing test coverage.
