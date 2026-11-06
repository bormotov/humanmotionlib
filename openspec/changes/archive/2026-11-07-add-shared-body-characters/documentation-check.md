# Documentation check: character API and distribution

Snapshot checked: try196, wheel SHA-256
`cff54359a150cc91f5cb46e5712b6631424366461b7866c3a5eb5fe0d3694b8b`,
runtime manifest SHA-256
`63351e7294bf3820c7209fc19076024b891cb95204ad2fa9cad4b93773e53048`.

## Task 6.4

The character sections in `docs/usage.md` and `tools/README.md` describe the
additive typed result fields, `character-render-request/v1`,
`character-render-manifest/v1`, package-identity regeneration, and the absence
of new runtime dependencies or downloaded meshes. The packaged
`docs/usage.md` and `docs/character-models.md` are byte-identical to checkout
sources in try196:

- `docs/usage.md`: `36b11bfa7b32839e9119e80ec00bbcb43565f5d7d2bb3fb6d8631df709b1b58c`
- `docs/character-models.md`: `2a3a9c26de36f415635f08774179b9cfd02eeb3c5b0dc1fa8240fd71d3b3c064`
- `tools/README.md`: `0eee199200aad94e803113c4ebc0215ab14416f61d3a8a3ec04d4fa841a48c88`

Task 6.4 documentation criteria are satisfied for this snapshot.

## Task 4.5

The batch examples show one shared preparation, registry-ordered character
selection, `character_provenance` attribution union, and image joins keyed by
`(character_id, sample_id, view)`. CLI and Python API examples are present.
The documents also establish absolute workspace/fresh disjoint run paths and
describe timeout options and stable cancellation/backend error handling.

The API/CLI regression report
`build/add-shared-body-characters_r1_dev_try-198_api-cli-regressions/test-report.json`
passed 28/28 tests against the exact try196 wheel. It covers console/API
parity, finite timeout rejection, cancellation propagation, and workspace/path
preflight. This is focused API/CLI regression evidence, not the complete host
suite or native acceptance.

`docs/usage.md` now includes a runnable single-female render using the same
prepared result and a fresh `library-use_r1_app_try-2_single-render` output,
with a character-keyed image join and selected-character attribution check.
This docs-only resource edit is not part of try196; its wheel identity remains
the one recorded above. A new unified candidate must package this documentation
before task 4.5 is closed. The docs-inclusive try199 wheel was built offline
and the API/render examples were bound against its installed `prepare` and
`render` signatures. Installed documentation bytes match checkout bytes as
listed above. R2 integration regressions on that same runtime snapshot passed
41/41 in
`build/add-shared-body-characters_r1_dev_try-204_r2-regressions/test-report.json`;
these tests do not replace the complete host suite or native review.
