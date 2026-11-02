# Manual character build and check

The contributor matrix builds one character at one height. It covers the fixed
table of skeleton, male and female at H1.50, H1.70 and H1.90. Each selection
uses only neutral, rest and arm-raise at 120 BPM, with the existing render-only
API and authoritative views. This is a local preview and file check; it does
not grant visual approval or full character, package, or library acceptance,
and it does not resume the paused character change.

The normal Make route prepares the project-owned CPython 3.14 environment,
updates its locked dependencies, rebuilds and installs the current package,
then runs the selected pair. It requires GNU Make 3.81+, a POSIX shell and uv. The first
run may download CPython and Python dependencies into the configured project
tools root. Blender is needed only for `matrix-build` rendering; `matrix-check`
uses the existing project environment and never prepares or rebuilds it.
Host workflows are supported on macOS arm64 and Ubuntu 24.04 x64; native
Windows is unsupported and WSL is unverified. Rendering currently requires
macOS arm64 Blender 5.2.2 LTS build `d13f752e3b9c`.

```sh
make
make matrix-list
make matrix-build CHARACTER=male HEIGHT=1.70
make matrix-check CHARACTER=male HEIGHT=1.70
```

`make` and `make matrix-list` need no Python, uv or Blender. Help describes the
goals; `matrix-list` prints the nine fixed character/height pairs. Missing or unsupported choices
fail before the selected output is changed. The workspace defaults to the
checkout; `WORKSPACE=/absolute/path` is an optional override. Matrix check
compares the selected build's package identity with the package already in the
prepared environment and prints the selected rebuild command when they differ.
If the selected result root or `build.json` is absent, Make and the direct
runner return that command without creating the result root, log, or report.
Once an existing result is present and a check attempt starts, its log and
current report are retained even when the record or generated files are
malformed or incompatible.

The direct CLI remains available for advanced use with a separately prepared
offline environment:

```sh
HML_PYTHON="$PWD/build/<owned-run>/environment/bin/python"
"$HML_PYTHON" tools/matrix.py list --workspace "$PWD"
"$HML_PYTHON" tools/matrix.py build \
  --workspace "$PWD" --character male --height 1.70
"$HML_PYTHON" tools/matrix.py check \
  --workspace "$PWD" --character male --height 1.70
```

`list` prints all nine pairs and their fixed result paths without creating
files, invoking Blender or running checks. Direct build and check require both
`CHARACTER` and `HEIGHT`; unknown or missing values fail before output changes.
Each action affects only the selected pair. Repeating build runs preparation,
render and presentation again from the beginning. Repeating check reruns every
validator against the actual current output and does not generate or repair
files. If its result root or build record is absent, it reports the selected
`make matrix-build CHARACTER=... HEIGHT=...` remedy without writing anything;
checks that start against existing results retain their log and report on both
success and failure.

For male H1.70, the current result root is
`build/automate-build-and-verification-matrix_r1_dev_current_male-h170/`.
Replace the last component with `<character>-h150`, `<character>-h170` or
`<character>-h190`. Each root contains `prepared/input.json`, the `render/`
producer output and `render/frames/`, `presentation/` with its media and
inventory, small `build.json` and `check.json` results, and `logs/` with one
ordinary timestamp/PID log per build or check attempt. Each build replaces only
that pair's generated content and current result files. Past attempts remain
as logs; there are no plan, candidate, continuation or publication steps.

Male and female outputs contain 32 source PNGs (1024×1024): neutral and rest
each have one sample for front, side and rear, while arm-raise has 13 animation
samples over four beats for front and side. Skeleton has 44 source PNGs; its
neutral/rest views also include the three thorax views and their isolated
variants. Static count samples reuse the animation source frames. Presentation
contains 8 count sheets for male/female or 20 for skeleton, two arm-raise GIFs
with 12 frames and 2000 ms total duration, two onion skins, `index.html` and
`presentation-inventory.json`. Static neutral/rest do not have GIFs.

Package/distribution tests, host and installed acceptance, cross-stature
comparisons, baseline/determinism review packs and backend process hardening
remain separate workflows. A matrix check covers the selected local output
only. The known backend PGID safety finding remains separate and unresolved.

## Cleanup levels

| Target | Exact selected area | What stays |
|---|---|---|
| `make mostlyclean` | Every direct child of `build/` whose basename ends in `_stage` or `_check`, including all hidden/nested files and links, except the configured reusable tools root | Other build entries and the configured reusable tools root, even if its basename ends in `_stage` or `_check` |
| `make clean` | Every direct child of `build/` except the configured reusable tools root | That tools/cache/Python root |
| `make distclean` | The entire `build/` directory | Nothing under `build/` |

All files inside a selected area are disposable, including unknown files,
matrix attempt logs and local R6 or other historical results. There are no
producer markers, file inventories, legacy-reference scans or history
exemptions. Tracked sources and releases in `dist/` are outside these areas.
The cleanup checks process activity and real path containment, unlinks selected
symbolic-link entries without traversing their targets, and reports exact
removals or pending failures. It requires Make, a POSIX shell, `ps`, `lsof`,
`find`, `wc`, `awk`, `grep`, `basename` and `rm`, not Python, uv or Blender.
