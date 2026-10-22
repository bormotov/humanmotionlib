# Proposal: Align project instructions with agreed workflow

## Why

The project instructions leave timing and licensing decisions open and contain an ambiguous reviewer cleanup rule. Codex configuration comments also imply that the work pipeline is sequential at the subagent runtime level, although only the OpenSpec change lifecycle needs to remain ordered.

## What changes

- Define one beat as the timing unit, static sampling at each beat, and animation sampling intervals from the beat duration.
- Set Apache-2.0 for project code and CC-BY-4.0 for library data/assets, and require provenance for motions as well as poses and segments.
- Require explicit commercial-use and derivative clearance for all external source material, and maintain a register of every source actually used, including CC0 and no-attribution sources.
- Keep IK target representation open until a concrete contact task is specified.
- Clarify that independent implementation tasks may run in parallel inside an approved OpenSpec change, while architect approval, implementation, review, and archive remain ordered.
- Let reviewers clean only their own review output; broader build cleanup is requested from the developer.

## Impact

Updates `AGENTS.md`, Codex role instructions, and `docs/used-materials.md`. No runtime code or source-data schema is introduced by this change.
