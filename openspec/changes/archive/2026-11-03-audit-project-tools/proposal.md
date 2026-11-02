# Proposal

## Why

After cloning the repository, a contributor should be able to choose a goal and follow a short, reliable command sequence. Today even help can fail because Python has not been prepared, and the setup guidance leaves the contributor to assemble working commands, cache settings and output paths.

## What Changes

- Make becomes the starting point for repository work. Running `make` shows the system requirements, available goals and required choices without preparing anything.
- `make package` prepares its tools, builds the distributable library and checks the resulting package. It needs no extra arguments or Blender.
- `make dev` prepares the tools, rebuilds the library from current sources and checks that the sources are ready for development. It reports the available ways to build and inspect development results.
- `make matrix-build CHARACTER=male HEIGHT=1.70` prepares everything needed and builds that selected preview. Matrix keeps its explicit character/height choice and remains one specialized development operation.
- `make matrix-check CHARACTER=male HEIGHT=1.70` checks existing results without rebuilding them. It reports when a new build is needed and preserves the information about how the old results were produced.
- Store default paths, cache settings, versions and recipes in project configuration. Contributors need not activate an environment, run setup commands manually or choose internal output directories.
- Rebuild and install the current library package before every operation that must use changed sources. Reuse already prepared development tools; check distributable packages independently in a clean setup.
- Audit existing tools, instructions and CI together. Fix reasonable coordination problems and document concrete gaps instead of presenting the short matrix preview as the whole development process.
- Provide argument-free mostlyclean, clean and distclean targets with fixed generated-file areas and progressively wider removal. Remove all contents selected by a level, including unknown files and local history, without producer inventories or reference scans; preserve active work and containment, and restore tools/results through normal builds.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `build-verification-matrix`: automatic preparation for a selected build, clear choice guidance and checking existing results without changing them.
- `host-python-runtime`: simple routes from a clean checkout, project-owned defaults and an executable audit of supported tools.
- `python-distribution`: a complete package-building route and reliable use of current sources during development.
- `project-governance`: clear purposes for development preparation and independent checks, consistent instructions and preservation of paused work.
- `build-artifact-lifecycle`: fixed cleanup areas, complete removal inside each selected area, activity/containment checks and ordinary rebuilding afterwards.

## Impact

Implementation is expected in Makefile, repository workflow tools, project configuration, package-building integration, guides and focused CI checks. Existing installed HML commands keep their input/output rules; Make supplies the ordinary repository defaults. No new runtime dependency is planned.

Development readiness, preview results, checked packages and full change acceptance remain distinct outcomes. Package creation does not publish a release; publication continues through the existing checked CI process. This change preserves character/movement/scene behavior, existing numerical limits and the pause on `add-shared-body-characters`. The R6 visual decision and separately recorded process-safety/determinism findings keep their status. Local files under build are disposable even when historical; durable results belong in external artifact storage. Updating cleanup rules does not execute cleanup or resume character verification.
