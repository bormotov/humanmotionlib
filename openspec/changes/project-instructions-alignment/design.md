# Design

## Decisions

- `T_beat` means the duration of one beat, derived from BPM as `60 / BPM` seconds. For each full beat, animation sampling uses `max(3, ceil(T_beat / 0.2 seconds))` intervals. Static samples are placed at every beat boundary. Fractional-beat segment boundary allocation remains for the timing implementation change to define.
- Apache-2.0 covers project code. CC-BY-4.0 covers library-authored data and distributable authored assets, including poses, segments, motions, baked clips, and renders. Third-party character and scene assets retain their own licenses and must be checked separately.
- Every motion records provenance. A composed motion records its source segment identifiers or external references; its distribution license remains CC-BY-4.0 when all included material is compatible with that license.
- External references and inputs are gated before use: their specific license must explicitly permit commercial use of the resulting work and be compatible with CC-BY-4.0 distribution. When that cannot be established, the source is not used. Every external material actually used is recorded in `docs/used-materials.md`, even where attribution is not required; provenance links to that register.
- IK target coordinate space, normalization, and units remain open. A contact-focused change must settle them with a concrete use case.
- Subagent concurrency is a scheduling capability, not workflow order. Independent tasks may run concurrently; the OpenSpec approval, implementation, review, and archive gates remain in sequence.
- Reviewer cleanup is limited to `build/review/<change-id>/`. If unrelated or broader build outputs prevent a clean verification, the reviewer asks the developer to remove them rather than exceeding its write scope.

## Codex configuration

Use the supported `max_concurrent_threads_per_session` key for the subagent concurrency cap. Keep comments accurate about host/runtime feature enablement and the V1-only `max_depth` behavior; do not imply that these settings enforce the OpenSpec lifecycle.
