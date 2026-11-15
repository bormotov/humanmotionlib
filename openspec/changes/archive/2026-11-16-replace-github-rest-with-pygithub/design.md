# Design

## Context

The tracked-source inventory found the project-authored GitHub HTTP transport in `tools/release.py`. It handles release history and lookups, draft creation and updates, and release asset uploads and reads. The production entry points are the `intent` and `publish-push` commands in `.github/workflows/package.yml`. The release tests currently combine a fake HTTP opener with controlled Git repositories and release fixtures.

Run [43755323246](https://github.com/bormotov/humanmotionlib/actions/runs/43755323246/job/132978544768) recorded the expected tag `v0.3.3` in the create request and response. A subsequent read of release ID `446407418` returned `untagged-a7f579fc9948c034f15f`. Draft updates and asset operations occur between creation and the final validation, so the logs establish the response difference without identifying the cause.

## Goals / Non-Goals

**Goals**

- Replace the custom transport with PyGithub while retaining the local Git and checked-wheel publication contracts.
- Run release commands on a clean Python 3.14 runner using one reproducibly installed client.
- Preserve actionable evidence for API failures and disagreements between draft reads.

**Non-Goals**

- Changing release eligibility, Git tag creation or Actions artifact handoff.
- Repairing existing production drafts or attributing the observed server response to a specific cause without evidence.

## Decisions

1. Replace URL construction, request headers, JSON handling and binary HTTP requests with repository-scoped PyGithub objects. Use the existing token with `Auth.Token`. Use `Repository.get_releases()` for paginated history and draft lookup, `Repository.get_release(int)` for read-back, and `Repository.create_git_release()` for creation. The SDK also provides `Repository.get_latest_release()` for the legacy latest-only lookup. Use `GitRelease.update_release()` for release updates, `get_assets()` for pagination, `upload_asset_from_memory()` or `upload_asset()` for uploads, and `GitReleaseAsset.download_asset()` for binary reads. Preserve existing release-policy orchestration and its test seam. Keep the Git CLI for local tags and pushes. Using public SDK methods avoids keeping the custom HTTP transport or adding a second transport for assets. [Repository API](https://pygithub.readthedocs.io/en/v2.10.0/github_objects/Repository.html), [release API](https://pygithub.readthedocs.io/en/v2.10.0/github_objects/GitRelease.html), [release asset API](https://pygithub.readthedocs.io/en/v2.10.0/github_objects/GitReleaseAsset.html).
2. Use the numeric ID for read-back and an explicit expected tag for validation. Preserve name, notes and draft state as appropriate when invoking SDK updates with required fields. Stop before publication when the draft returned by ID differs in tag or other required evidence. Keep INFO records for requested and returned release identities and ERROR records for safe inputs and the failing operation or status. Treat a 404 as absence only at lookups where absence already has defined meaning. Map access failures, transient errors and incomplete reads to the existing failure path. Log neither token values nor raw request, response or asset bodies. A cached SDK object would hide the response difference, so read back from GitHub by ID.
3. Declare PyGithub in a dedicated locked uv dependency group. PyGithub 2.10.0 is the baseline to verify because its public asset download method covers binary reads and the release declares Python 3.14 support. Provision that group in an isolated environment before the publication job evaluates intent. Use the same interpreter for both commands. Keep imports for SDK access inside the release integration path so purely local commands and existing wheel-only checks can load the helper. Run SDK-specific tests in the locked release tooling environment with a controlled repository/response fixture and retain the host suite's existing release policy coverage. Adding PyGithub to runtime wheel metadata would install publisher tooling for applications that only use the generation API. [Package metadata](https://pypi.org/project/PyGithub/2.10.0/), [upstream license](https://github.com/PyGithub/PyGithub/blob/v2.10.0/COPYING.LESSER).
4. Preserve tested artifact identity and existing retry semantics. Reconcile incomplete releases using fresh release and asset reads. Reuse matching assets, reject conflicts, and retain the existing digest comparison or binary verification where required. Exercise SDK success, pagination, missing results, denied writes, binary reads and partial failures in controlled fixtures, including a create response followed by an `untagged-*` read-back. Verify a positive control with the same accepted tag and bytes. Production publication and existing draft recovery are separate operations.

## Risks / Trade-offs

- PyGithub uses the same GitHub API. A server-side tag discrepancy can recur, so verify and report each relevant identity and retain the existing stop condition.
- SDK method defaults and lazy reads can differ from the custom client's semantics. Verify the selected package's method signatures and exercise fresh reads, explicit update fields, missing-resource handling and actual binary responses in the release test environment.
- Locking a release-only dependency adds provisioning to the publication job. Verify CPython 3.14 installation, unchanged wheel dependencies, and compatible licenses for the selected PyGithub release and newly used dependencies. Record cleared materials in `docs/used-materials.md` and add notices where required.

## Migration Plan

Land the lock change, SDK migration, workflow provisioning and contributor instructions together. Validate the lock and recreate a clean release tooling environment. Exercise the release commands and publication sequence against controlled Git and SDK fixtures before rollout. An ordinary main push can confirm the general workflow without introducing a version increase for the test. Roll back configuration and tooling together if necessary, preserving all existing tags, drafts and published assets. Early visual and final visual gates are not applicable because the change affects contributor release tooling only.
