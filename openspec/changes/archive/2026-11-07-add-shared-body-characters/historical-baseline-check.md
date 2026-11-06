# Historical BPM90 skeleton baseline

## Result

The protected HumanMotionLib 0.2.0 wheel was run through its own installed
package and supervised Blender entry point to produce a supplementary H=1.70 m
skeleton baseline at BPM90. This baseline covers the shared core set
`neutral`, `rest`, `arm-raise`, `squat`, and `walking-in-place`. It does not
claim rocker or joint-sweep coverage. The older protected try2 baseline was
read-only and was not modified.

The generation uses the exact original wheel
`build/portable-installed-runtime_c3e9007_dev_try-6_candidate/artifacts/humanmotionlib-0.2.0-py3-none-any.whl`
(SHA-256 `6171a6ea8e833095dcf0246a9eb0447b1aae422fdbc49c001d776e64454d227a`)
and runtime manifest SHA-256
`3a980bb5e242e846fe438b493f0cd375e3c0332aa4db6b18277b170136b62869`. The
installed old package's 40 implementation hashes were checked against the
protected try2 metadata by the package-install owner before this run. The old
package version, manifest identity and Blender version/build are independently
confirmed by both the prepared input and render outputs.

The supervised `render-pass` receipt succeeded on Blender 5.2.2 LTS,
`d13f752e3b9c` (Darwin-arm64). The prepared input has 69 delivered samples:
1 neutral, 1 rest, 17 arm-raise, 17 squat, and 33 walking-in-place. The render
manifest contains the same sample IDs in the same order. Every declared image
path was checked against the expected view inventory, and all 152 PNGs were
decoded successfully and SHA-256 inventoried.

| Evidence | Identity |
|---|---|
| Prepared content seal | `75f0e6749c1f75714ada4813e274c2542dbd0305ba554d4310a69bbe6468049a` |
| Prepared file SHA-256 | `5d0da50ec148a0a3663b48c8e2bccfbb68e9061e78047c3b0c083f326d3047f1` |
| Render manifest SHA-256 | `ebc58fe7fc591eefe2d4ca41f4b835deb9761bd736b730d2a16c02ed11f65f60` |
| Saved `.blend` SHA-256 | `f13952d39330ee32fd071a9b578822237d25630bbdc13f7c630ad22a0d347dbe` |
| Old wheel scene source SHA-256 | `69a3060ebfc75951563f2c811b7224b5004303fd038953ac8fb1cbc79b1e6a9e` |
| Successful supervisor receipt | `build/add-shared-body-characters_r1_character-final-packaging_try-1_historical-render/processes/1961c21b25be4f74b797dbf2224dfdba/stdout.log` |

The full machine-readable record contains every exact sample ID, rational
beat/second, frame ID, view, image path, image SHA-256 and byte length:
`build/add-shared-body-characters_r1_character-final-packaging_try-1_historical-render/historical-baseline-record.json`.
The prepared input and the script that produced it are retained in
`build/add-shared-body-characters_r1_character-final-packaging_try-1_historical-input/`;
rendered scene, numeric outputs, receipt, manifest and images are in the
disjoint sibling `..._try-1_historical-render/` run.

## Commands and retained runs

The saved harness inserts the read-only try163 installation before the first
HML import, asserts wheel/manifest identity, prepares with the 0.2.0
`prepare_skeleton.prepare(..., bpms=(90,))`, writes the prepared input, and
calls the old public `run_blender.run` supervisor with the render directory.
It does not load or reseal the current 0.3.0 sources. The independent audit
re-reads the input with the old package's validator and verifies render,
sample, image, backend and package identities. Source files were not changed.

The fresh input and rendered output are retained as dependencies of the
baseline record. Both are direct child run roots under `build/`; their roots
are disjoint and have zero symlinks. No generated asset or external material
was used. This baseline is historical comparison evidence and does not attest
current-candidate deformation, rocker/sweep behavior, or human visual
acceptance.
