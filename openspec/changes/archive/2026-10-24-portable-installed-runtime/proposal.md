# Proposal

## Why

HML's installed resource inventory and integrity checks already support checkout-independent generation, but optional workspace selection and inconsistent path handling still make pipeline behavior depend on the invocation directory. A caller must be able to run the installed package outside HML with an explicit writable workspace and no neighboring checkout.

## What Changes

- **BREAKING**: Require an explicit absolute workspace for CLI and public API operations that create filesystem state; resolve relative workflow operands against that workspace rather than the current directory.
- Keep results, temporary files, logs, receipts and backend lock state in the selected workspace's existing `build/` layout, with fresh run identities and existing ownership protections.
- Read runtime resources exclusively from the installed package, preserving manifest, implementation, prepared-content and predecessor-evidence checks without checkout fallback.
- Make numeric report writing and HTML-only regeneration obey the same workspace and predecessor contracts as preparation, supervised generation and review creation.
- Prove portability using non-editable installations, unrelated invocation directories, misleading neighboring files, read-only package resources and real pinned-backend regression evidence.
- Preserve read-only command usage without a workspace and retain existing animation, numerical, rendering and licensing contracts.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `python-distribution`: Make workspace selection explicit, define path resolution and write containment, and strengthen installed workflow and artifact checks outside the checkout.
- `backend-execution`: Bind backend execution, temporary resources, lock ownership and diagnostic evidence to the explicit caller workspace independently of invocation location.
- `build-artifact-lifecycle`: Apply existing flat run, disjoint input/output and cleanup rules to explicit pipeline workspaces and protected external predecessor inputs.

## Impact

Affected areas are the installed CLI, workspace/path helpers, preparation and verification writers, review and HTML-only presentation, supervised backend resource handling, wheel smoke checks, CI and active command documentation. Existing pipeline callers must pass an absolute workspace; relative workflow operands become workspace-relative. No new dependency, source data format, animation convention or backend version is proposed. Implementation requires Gate 1 approval; reviewer evidence and the human visual gate remain required before archive.
