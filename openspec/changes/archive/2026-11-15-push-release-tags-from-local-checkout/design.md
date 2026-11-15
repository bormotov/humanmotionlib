# Design

## Context

The publish job already checks out the tested commit with full history and has `contents: write`. The helper currently creates the draft and uploads its assets before using the GitHub Git references API to create the tag. On run [43634934284](https://github.com/bormotov/humanmotionlib/actions/runs/43634934284), draft lookup failed before that Git write. GitHub returned draft `445697550` with an `untagged-…` name and both assets.

## Goals / Non-Goals

Use the existing checkout and job credential for Git writes, and use the GitHub Releases API for release records and assets. The publish job remains serialized and runs only after successful build and installed tests for an eligible version increase on `main`. This change covers publication tooling, so neither visual gate applies.

## Decisions

1. Keep the existing eligibility and artifact checks ahead of writes. Inspect any existing publication state using the current identity checks. For an absent remote tag, create a lightweight tag locally at the checked commit, or reuse an existing local tag at that commit, and push only `refs/tags/vX.Y.Z:refs/tags/vX.Y.Z` to `origin`. Use the checkout's job credential, disable follow-tags, and let a non-forced push reject conflicts. Remove the GitHub API tag writer. For an already-present remote tag, compare its resolved commit and reuse it only on a match. A failed or rejected push stops publication. No Git writes update a branch. [GitHub Docs on pushing tags](https://docs.github.com/en/get-started/using-git/pushing-commits-to-a-remote-repository)
2. With the remote tag available, create or resume a draft against that tag. Once the draft ID is known, read it by ID during verification and publish it by that ID. Keep the existing checks that identify the draft and its assets, using the confirmed Git tag for commit identity. The Releases API ignores `target_commitish` if the named tag already exists. [GitHub REST API for releases](https://docs.github.com/en/rest/releases/releases)
3. A tag can remain after an interrupted publication. A retry for the same checked commit can reuse it and resume the existing release sequence. Continue to compare published history before starting publication and retain the existing checks for conflicting drafts and assets. A tag without a published release is not a published boundary.

## Migration Plan

Deploy the helper and workflow together. The first normal qualifying run with the new helper will use the local tag and push sequence.

For `0.3.1`, first inspect the current tag and draft read-only and verify the original successful build and test steps from run `43634934284`, the tested commit `a13ae579002344908c3c0c59446ab9a1d44c864b`, and the wheel identity `humanmotionlib-0.3.1-py3-none-any.whl` with SHA-256 `de789b7fc594cf03925173e20a6e4e23f1ba360c4b6037bd1c2f1adb9d28859a`. Confirm the original artifact is available and that the draft assets and notes agree with the run before proposing a one-off recovery. If evidence or the current publication state does not match, leave the draft intact and use a later intentional version increase for the first normal release. A rerun of the failed job uses the old checked commit and helper. A same-version push of the fix gives ordinary CI only. Treat any actual repair and publication of this draft as a separate operator action using the verified evidence. [GitHub Docs on rerun identity](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs)

## Risks / Trade-offs

A remote tag can appear while the release is still a draft. The public GitHub Release is the completion marker. The retry path reuses a same-commit tag and preserves existing release evidence when publication stops.
