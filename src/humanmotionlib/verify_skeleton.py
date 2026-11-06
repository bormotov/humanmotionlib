# SPDX-License-Identifier: Apache-2.0
"""Measure supplied body transforms independently; missing backend evidence fails."""

import argparse
import json
from fractions import Fraction
from pathlib import Path
import sys

from humanmotionlib import math3d as m
from humanmotionlib.measurements import Measurements, measure_pose
from humanmotionlib.prepared import read_prepared, write_json
from humanmotionlib.runtime import resolve_workspace_path, validate_run_content_path, workspace_root
from humanmotionlib.poses import neutral_pose, rest_pose


_DIAGONAL_PAIRS = {"skeleton": 1.50, "male": 1.70, "female": 1.90}


def _parse_diagonal_builds(values):
    """Parse CHARACTER=RUN operands without normalizing away duplicate IDs."""
    parsed = []
    for value in values or ():
        if not isinstance(value, str) or "=" not in value:
            raise ValueError("--diagonal-build must use CHARACTER=RUN form")
        identifier, run = value.split("=", 1)
        if not identifier or not run:
            raise ValueError("--diagonal-build must use nonempty CHARACTER=RUN values")
        parsed.append((identifier, Path(run)))
    identifiers = [identifier for identifier, _ in parsed]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("--diagonal-build contains a duplicate character")
    if len(parsed) != len(_DIAGONAL_PAIRS) or set(identifiers) != set(_DIAGONAL_PAIRS):
        raise ValueError("--diagonal-build requires exactly skeleton, male and female")
    return parsed


def _diagonal_numeric_coverage_failures(prepared):
    """Require the complete packaged diagnostic set and default BPM plans."""
    from humanmotionlib.sampling import delivered_beats, sampling
    from humanmotionlib.validate import load_sources, validate_sources

    failures = []
    try:
        profile_id = prepared["sources"]["profile"]["id"]
        validate_sources(profile_id)
        canonical, _ = load_sources(profile_id)
        failures.extend(_matrix_definition_failures([prepared], canonical))
        diagnostics = canonical["diagnostics"]
        if len(diagnostics) != 32:
            failures.append(f"canonical diagnostic set has {len(diagnostics)} fixtures; expected 32")
        fixture_ids = [row["id"] for row in diagnostics]
        if len(set(fixture_ids)) != 32:
            failures.append("canonical diagnostic fixture IDs are not 32 unique entries")

        expected_sampling = {}
        expected_samples = {}
        stature = prepared["sources"]["profile"]["stature_m"]
        scaled_diagnostics = _scale_diagonal_diagnostics(diagnostics, stature,
                                                         canonical["profile"]["stature_m"])
        for fixture in sorted(scaled_diagnostics, key=lambda row: row["id"]):
            fixture_id = fixture["id"]
            beats = delivered_beats(fixture["duration_beats"], (60, 120, 180))
            ids = {beat: fixture_id + f"/{index:05d}" for index, beat in enumerate(beats)}
            expected_sampling[fixture_id] = []
            for bpm in (60, 120, 180):
                plan = sampling(fixture["duration_beats"], bpm)
                for mode in ("static", "animation"):
                    for record in plan[mode]:
                        beat = Fraction(record["beat"]["numerator"], record["beat"]["denominator"])
                        record["sample_id"] = ids[beat]
                expected_sampling[fixture_id].append(plan)
                for beat, sample_id in ids.items():
                    expected_samples[sample_id] = (fixture_id, beat.numerator, beat.denominator)
        if prepared.get("sampling") != expected_sampling:
            failures.append("prepared sampling does not cover all 32 canonical diagnostics at BPM 60, 120 and 180")
        observed_samples = {}
        for row in prepared.get("samples", []):
            try:
                beat = row["beat"]
                observed_samples[row["id"]] = (row["fixture"], beat["numerator"], beat["denominator"])
            except (KeyError, TypeError):
                failures.append("prepared sample inventory contains a malformed fixture/beat row")
        if observed_samples != expected_samples:
            failures.append("prepared sample inventory does not cover the complete canonical diagnostic/BPM plan")
    except (KeyError, TypeError, ValueError, OSError) as error:
        failures.append(f"canonical diagonal numeric coverage could not be verified: {error}")
    return failures


def _scale_diagonal_diagnostics(diagnostics, stature, reference_height):
    from humanmotionlib.poses import scale_meter_fields
    return scale_meter_fields(diagnostics, stature / reference_height)


def _diagonal_numeric_aggregate(rows, prepared_rows):
    """Aggregate the three approved leaves without claiming a full matrix."""
    required_pairs = [{"character_id": identifier, "stature_m": height}
                      for identifier, height in _DIAGONAL_PAIRS.items()]
    failures = []
    observed_pairs = []
    for (identifier, expected_height), prepared, leaf in zip(_DIAGONAL_PAIRS.items(), prepared_rows, rows):
        observed_height = float(prepared["sources"]["profile"]["stature_m"])
        pair = {"character_id": identifier, "stature_m": observed_height}
        observed_pairs.append(pair)
        if abs(observed_height - expected_height) > 1e-9:
            failures.append(f"{identifier} has H={observed_height:.9g}; expected H={expected_height:.2f}")
        failures.extend(_diagonal_numeric_coverage_failures(prepared))
        if leaf.get("numeric_status") != "pass":
            failures.append(f"{identifier} H={expected_height:.2f} numeric leaf did not pass")
        if (leaf.get("verification_scope") != "selected-character-numeric-leaf"
                or leaf.get("checked_character_ids") != [identifier]
                or not isinstance(leaf.get("render_identity"), str)):
            failures.append(f"{identifier} leaf is missing its selected-character/render identity")
        if identifier == "skeleton":
            if (leaf.get("native_midpoints", {}).get("status") != "not-applicable-skeleton"
                    or leaf.get("dense", {}).get("status") != "not-applicable-skeleton"):
                failures.append("skeleton leaf does not explicitly scope surface midpoint/dense checks as not applicable")
        elif any(leaf.get(key, {}).get("status") != "pass"
                 for key in ("native_midpoints", "dense")):
            failures.append(f"{identifier} leaf native midpoint/dense checks did not pass")
    failures.extend(_matrix_shared_identity_failures(prepared_rows))
    try:
        from humanmotionlib.validate import load_sources, validate_sources
        profile_id = prepared_rows[0]["sources"]["profile"]["id"]
        validate_sources(profile_id)
        canonical, _ = load_sources(profile_id)
        failures.extend(_matrix_definition_failures(prepared_rows, canonical))
    except (KeyError, TypeError, ValueError, OSError) as error:
        failures.append(f"canonical diagonal source validation failed: {error}")
    unassessed = [{"character_id": identifier, "stature_m": height}
                  for identifier, height in (("skeleton", 1.70), ("skeleton", 1.90),
                                             ("male", 1.50), ("male", 1.90),
                                             ("female", 1.50), ("female", 1.70))]
    status = "pass" if not failures and len(rows) == 3 else "fail"
    return {
        "format": "hml-character-diagonal-numeric/v1",
        "verification_scope": "diagonal-v1",
        "scope": "exactly skeleton H=1.50, male H=1.70, female H=1.90",
        "status": status,
        "numeric_status": status,
        "matrix_complete": False,
        "required_pairs": required_pairs,
        "observed_pairs": observed_pairs,
        "unassessed_pairs": unassessed,
        "failures": failures,
        "rendering": "not-run",
        "repeatability": "not-assessed",
        "visual": "not-assessed",
        "full_change_acceptance": "not-assessed",
        "leaves": rows,
    }


def _matrix_definition_failures(matrix_inputs, canonical_sources,
                                consumer_resolver=None):
    """Check each prepared definition against the canonical stature-scaled sources."""
    from humanmotionlib.poses import scale_meter_fields, scaled_profile

    failures = []
    reference_height = canonical_sources["profile"]["stature_m"]
    for index, current in enumerate(matrix_inputs):
        profile = current["sources"]["profile"]
        stature = profile["stature_m"]
        factor = stature / reference_height
        expected_profile = scaled_profile(canonical_sources["profile"], stature)
        if profile != expected_profile:
            failures.append(f"run {index} profile definition differs from stature-scaled canonical profile")
        expected_mobility = scale_meter_fields(canonical_sources["mobility"], factor)
        if current["sources"].get("mobility") != expected_mobility:
            failures.append(f"run {index} mobility definition differs from stature-scaled canonical source")
        expected_diagnostics = list(canonical_sources["diagnostics"])
        snapshot = current.get("consumer_motion")
        if snapshot is not None:
            if consumer_resolver is None:
                failures.append(f"run {index} consumer diagnostic has no canonical lineage resolver")
            else:
                try:
                    bpms = tuple(plan["bpm"] for plans in current["sampling"].values()
                                 for plan in plans)
                    resolved = consumer_resolver(snapshot, canonical_sources,
                                                 current["source_hashes"], profile["id"], bpms,
                                                 stature)
                    expected_diagnostics.append(resolved)
                except (KeyError, TypeError, ValueError, OSError) as error:
                    failures.append(f"run {index} consumer diagnostic lineage invalid: {error}")
        expected_diagnostics = scale_meter_fields(expected_diagnostics, factor)
        if current["sources"].get("diagnostics") != expected_diagnostics:
            failures.append(f"run {index} diagnostics differ from stature-scaled canonical definitions")
        if current["sources"].get("review-scene") != canonical_sources["review-scene"]:
            failures.append(f"run {index} review-scene definition differs")
    return failures


def _matrix_shared_identity_failures(matrix_inputs):
    """Require cross-stature package/source/sampling/sample-join identity."""
    failures = []
    if not matrix_inputs:
        return failures
    reference = matrix_inputs[0]
    reference_profile = reference["sources"]["profile"]
    def membership(value):
        return [(row.get("id"), row.get("fixture"), row.get("beat"))
                for row in value.get("samples", [])]
    for index, current in enumerate(matrix_inputs[1:], start=1):
        if current.get("package_identity") != reference.get("package_identity"):
            failures.append(f"run {index} candidate package identity differs")
        if current.get("source_hashes") != reference.get("source_hashes"):
            failures.append(f"run {index} canonical source hash closure differs")
        if current["sources"]["profile"].get("id") != reference_profile.get("id"):
            failures.append(f"run {index} skeletal profile identity differs")
        if current.get("sampling") != reference.get("sampling"):
            failures.append(f"run {index} diagnostic sampling coverage differs")
        if membership(current) != membership(reference):
            failures.append(f"run {index} prepared sample membership differs")
    return failures


def verify_transforms(prepared,evaluated_samples=None):
    profile,mobility = prepared["sources"]["profile"],prepared["sources"]["mobility"]
    fixtures = {f["id"]:f for f in prepared["sources"]["diagnostics"]}
    supplied = evaluated_samples if evaluated_samples is not None else prepared["samples"]
    observed = {s["id"]:s for s in supplied}
    if len(observed) != len(supplied): raise ValueError("Duplicate evaluated sample ID")
    if set(observed) != {s["id"] for s in prepared["samples"]}: raise ValueError("Missing/extra evaluated samples")
    reports = []
    for expected in prepared["samples"]:
        sample = observed[expected["id"]]
        beat = expected["beat"]["numerator"]/expected["beat"]["denominator"]
        report = measure_pose(profile,mobility,sample["frames"],beat,expected["expected_actions"],expected["world_root"])
        kind = fixtures[expected["fixture"]]["construction"]["type"]
        if expected["fixture"] in ("neutral","rest") and not report.get("missing"):
            # Literal stored dossier frames, independently of action-solving routines.
            frozen = (neutral_pose if kind=="neutral" else rest_pose)(profile)
            checks = Measurements(beat)
            for id in sorted(frozen):
                if id not in sample["frames"]: continue
                checks.position(id+".frozen_origin",sample["frames"][id]["position_m"],frozen[id]["position_m"],1e-4*profile["stature_m"])
                checks.rotation(id+".frozen_frame",sample["frames"][id]["rotation"],frozen[id]["rotation"])
            report["checks"].extend(checks.checks)
        report["id"],report["fixture"] = sample["id"],expected["fixture"]
        report["status"] = "pass" if report["checks"] and all(c["status"]=="pass" for c in report["checks"]) else "fail"
        reports.append(report)
    return {"status":"pass" if reports and all(r["status"]=="pass" for r in reports) else "fail",
            "scope":"evaluated-body-transforms" if evaluated_samples is not None else "prepared-body-transforms",
            "source_hashes":prepared["source_hashes"],"samples":reports,
            "acceptance":"incomplete: mesh/contact/render/timing/independent visual evidence must be verified separately"}


def main(workspace=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--transforms-only",action="store_true",help="Explicitly check prepared frames; does not establish backend acceptance")
    parser.add_argument('--thorax-preview',action='store_true',help='Verify evaluated neutral/rest preview only; no full diagnostic acceptance')
    parser.add_argument('--squat-preview',action='store_true',help='Verify evaluated squat-only preview; no full diagnostic acceptance')
    parser.add_argument("--action-coverage",action="store_true")
    parser.add_argument("--dense",action="store_true",help="Also audit data-side dense diagnostic continuity and couplings")
    parser.add_argument("--dense-floor",action="store_true",help="Audit dense floor bounds from evaluated local mesh vertices")
    parser.add_argument("--stature-builds",nargs=3,type=Path,help="Compare actual 1.50/1.70/1.90 m evaluated builds")
    parser.add_argument("--character-output",type=Path,help="Audit selected surface evidence from a character render run")
    parser.add_argument("--numeric-only",action="store_true",
                        help="Verify complete no-images character construction evidence; requires --character-output")
    parser.add_argument("--selected-character", help="Opt into a scoped numeric comparison for one registered character")
    parser.add_argument("--acceptance-scope", choices=("diagonal-v1",),
                        help="Use the approved three-pair diagonal numeric acceptance scope")
    parser.add_argument("--diagonal-build", action="append", default=[], metavar="CHARACTER=RUN",
                        help="One diagonal numeric build; repeat for skeleton, male and female")
    args = parser.parse_args()
    try:
        if args.acceptance_scope == "diagonal-v1":
            if (not args.numeric_only or args.character_output is None or args.transforms_only
                    or args.thorax_preview or args.squat_preview or args.dense or args.dense_floor
                    or args.action_coverage or args.stature_builds):
                raise ValueError("diagonal-v1 cannot mix numeric, preview, transform, action-coverage or stature modes")
            if args.selected_character:
                if args.diagonal_build:
                    raise ValueError("diagonal leaf mode cannot include --diagonal-build operands")
                from humanmotionlib.characters import validate_character_sources
                known_ids = {row["id"] for row in validate_character_sources()}
                if args.selected_character not in _DIAGONAL_PAIRS or args.selected_character not in known_ids:
                    raise ValueError("diagonal leaf requires one approved character ID")
                diagonal_specs = None
            else:
                diagonal_specs = _parse_diagonal_builds(args.diagonal_build)
        elif args.diagonal_build:
            raise ValueError("--diagonal-build requires --acceptance-scope diagonal-v1")
        else:
            diagonal_specs = None
        if args.numeric_only and args.character_output is None:
            raise ValueError("--numeric-only requires --character-output")
        if args.selected_character is not None and args.acceptance_scope != "diagonal-v1":
            if (not args.numeric_only or args.character_output is None or not args.stature_builds
                    or args.transforms_only or args.thorax_preview or args.squat_preview
                    or args.dense or args.dense_floor):
                raise ValueError("--selected-character requires only numeric-only --character-output and three --stature-builds")
            from humanmotionlib.characters import validate_character_sources
            registered_character_ids = [row["id"] for row in validate_character_sources()]
            if args.selected_character not in registered_character_ids:
                raise ValueError(f"unknown selected character {args.selected_character!r}")
        elif args.selected_character is None:
            registered_character_ids = None
        else:
            registered_character_ids = None
        workspace = workspace_root(workspace)
        input_operand = resolve_workspace_path(args.input, workspace)
        output, output_run = validate_run_content_path(args.output, workspace)
        input_root = input_operand if input_operand.is_dir() else input_operand.parent
        path = input_operand/"input.json" if input_operand.is_dir() else input_operand
        if (input_root == output_run or input_root.is_relative_to(output_run)
                or output_run.is_relative_to(input_root)):
            raise ValueError("verification input and report output runs must be disjoint")
        stature_builds = ([resolve_workspace_path(item, workspace) for item in args.stature_builds]
                          if args.stature_builds else None)
        if args.selected_character is not None and args.acceptance_scope != "diagonal-v1":
            if len({path.resolve(strict=False) for path in stature_builds}) != 3:
                raise ValueError("--selected-character requires three distinct stature builds")
            if input_root.resolve(strict=False) != stature_builds[0].resolve(strict=False):
                raise ValueError("selected numeric --input must be the H1.50 generated run")
            if resolve_workspace_path(args.character_output, workspace).resolve(strict=False) != stature_builds[0].resolve(strict=False):
                raise ValueError("selected numeric --character-output must be the H1.50 generated run")
        if output.exists():
            raise ValueError(f"verification report already exists: {output}")
        if not args.transforms_only:
            evaluated_path = input_operand/"evaluated.json"
        if stature_builds:
            for build in stature_builds:
                if build == output_run or build.is_relative_to(output_run) or output_run.is_relative_to(build):
                    raise ValueError("stature comparison inputs must be disjoint from report output run")
        prepared = read_prepared(path)
        if diagonal_specs is not None:
            from humanmotionlib.characters import validate_character_sources
            from humanmotionlib.character_verification import verify_character_output
            from humanmotionlib.runtime import validate_existing_run_root
            registry_ids = [row["id"] for row in validate_character_sources()]
            diagonal_runs = {identifier: resolve_workspace_path(run, workspace)
                             for identifier, run in diagonal_specs}
            if set(diagonal_runs) != set(_DIAGONAL_PAIRS):
                raise ValueError("diagonal-v1 requires exactly skeleton, male and female")
            diagonal_paths = [path.resolve(strict=False) for path in diagonal_runs.values()]
            for index, left in enumerate(diagonal_paths):
                for right in diagonal_paths[index + 1:]:
                    if left == right or left.is_relative_to(right) or right.is_relative_to(left):
                        raise ValueError("diagonal input runs must be distinct and disjoint")
            skeleton_run = validate_existing_run_root(diagonal_runs["skeleton"], workspace)
            if (input_root.resolve(strict=False) != skeleton_run.resolve(strict=False)
                    or resolve_workspace_path(args.character_output, workspace).resolve(strict=False)
                    != skeleton_run.resolve(strict=False)):
                raise ValueError("diagonal-v1 --input and --character-output must name the skeleton H1.50 run")
            resolved_runs = {}
            diagonal_prepared = {}
            diagonal_backend = {}
            for identifier, height in _DIAGONAL_PAIRS.items():
                run = validate_existing_run_root(diagonal_runs[identifier], workspace)
                if run == output_run or run.is_relative_to(output_run) or output_run.is_relative_to(run):
                    raise ValueError(f"diagonal-v1 {identifier} input and output must be disjoint")
                if run / "input.json" != (input_operand / "input.json" if input_operand.is_dir() else input_operand) and identifier == "skeleton":
                    raise ValueError("diagonal-v1 skeleton input must be the --input run")
                run_prepared = read_prepared(run / "input.json")
                observed_height = float(run_prepared["sources"]["profile"]["stature_m"])
                if abs(observed_height - height) > 1e-9:
                    raise ValueError(f"diagonal-v1 {identifier} input must be H={height:.2f} m")
                if run_prepared.get("consumer_motion") is not None:
                    raise ValueError("diagonal-v1 numeric leaf must use canonical packaged diagnostics, not consumer input")
                metadata_path = run / "build-metadata.json"
                if metadata_path.is_symlink() or not metadata_path.is_file():
                    raise ValueError(f"diagonal {identifier} build metadata is missing or unsafe")
                metadata = json.loads(metadata_path.read_text())
                from humanmotionlib.runtime import check_blender_version
                backend = check_blender_version(metadata.get("blender_version"),
                                                 metadata.get("blender_build"))
                diagonal_backend[identifier] = {"version": metadata["blender_version"],
                                                "build_hash": metadata["blender_build"]}
                resolved_runs[identifier] = run
                diagonal_prepared[identifier] = run_prepared
            if len({(row["version"], row["build_hash"]) for row in diagonal_backend.values()}) != 1:
                raise ValueError("diagonal candidate backend identities differ")
            if output.exists():
                raise ValueError(f"verification report already exists: {output}")
            rows = []
            for identifier, _height in _DIAGONAL_PAIRS.items():
                leaf = verify_character_output(diagonal_prepared[identifier], resolved_runs[identifier],
                    registry_ids, numeric_only=True, selected_character_id=identifier,
                    require_complete_diagnostic_coverage=True)
                rows.append({"character_id": identifier, "stature_m": _DIAGONAL_PAIRS[identifier],
                             "prepared_sha256": diagonal_prepared[identifier].get("content_sha256"),
                             "run": str(resolved_runs[identifier]), "report": leaf})
            aggregate = _diagonal_numeric_aggregate(
                [row["report"] for row in rows],
                [diagonal_prepared[identifier] for identifier in _DIAGONAL_PAIRS])
            aggregate["leaves"] = rows
            aggregate["backend_identity"] = diagonal_backend
            result = {"status": aggregate["status"], "numeric_status": aggregate["numeric_status"],
                      "verification_scope": "diagonal-v1", "scope": aggregate["scope"],
                      "acceptance": ("diagonal numeric acceptance only; excluded pairs and visual evidence remain unassessed"
                                     if aggregate["status"] == "pass" else "diagonal numeric acceptance failed or incomplete"),
                      "character_verification": aggregate}
            output.parent.mkdir(parents=True, exist_ok=True)
            write_json(output, result)
            print(f"{result['status']}: {result['scope']} (3 diagonal leaves)")
            return 0 if result["status"] == "pass" else 1
        if args.acceptance_scope == "diagonal-v1":
            from humanmotionlib.characters import validate_character_sources
            from humanmotionlib.character_verification import verify_character_output
            from humanmotionlib.runtime import validate_existing_run_root
            identifier = args.selected_character
            required_height = _DIAGONAL_PAIRS[identifier]
            run = validate_existing_run_root(resolve_workspace_path(args.character_output, workspace), workspace)
            if input_root.resolve(strict=False) != run.resolve(strict=False):
                raise ValueError("diagonal leaf --input and --character-output must name the same run")
            if run == output_run or run.is_relative_to(output_run) or output_run.is_relative_to(run):
                raise ValueError("diagonal leaf input and report output runs must be disjoint")
            actual_height = float(prepared["sources"]["profile"]["stature_m"])
            if abs(actual_height-required_height) > 1e-9:
                raise ValueError(f"diagonal leaf {identifier} requires H={required_height:.2f} m")
            if prepared.get("consumer_motion") is not None:
                raise ValueError("diagonal numeric leaf requires canonical packaged diagnostics")
            ids = [row["id"] for row in validate_character_sources()]
            leaf = verify_character_output(prepared, run, ids, numeric_only=True,
                                           selected_character_id=identifier,
                                           require_complete_diagnostic_coverage=True)
            status = "pass" if leaf.get("numeric_status") == "pass" else "fail"
            report = {"status": status, "numeric_status": status,
                      "verification_scope": "diagonal-v1",
                      "scope": f"{identifier} H={required_height:.2f} numeric leaf",
                      "matrix_complete": False,
                      "required_pairs": [{"character_id": key, "stature_m": height}
                                         for key, height in _DIAGONAL_PAIRS.items()],
                      "observed_pairs": [{"character_id": identifier, "stature_m": actual_height}],
                      "unassessed_pairs": [{"character_id": key, "stature_m": height}
                                            for key, height in _DIAGONAL_PAIRS.items() if key != identifier],
                      "rendering": "not-run", "repeatability": "not-assessed",
                      "visual": "not-assessed", "full_change_acceptance": "not-assessed",
                      "leaf": leaf}
            output.parent.mkdir(parents=True, exist_ok=True)
            write_json(output, report)
            print(f"{status}: {report['scope']}")
            return 0 if status == "pass" else 1
        if args.selected_character is not None:
            observed_heights = [float(read_prepared(directory / "input.json")["sources"]["profile"]["stature_m"])
                                for directory in stature_builds]
            if observed_heights != [1.5, 1.7, 1.9]:
                raise ValueError("--selected-character requires H1.50, H1.70 and H1.90 builds in canonical order")
            if Path(path).resolve(strict=True) != (stature_builds[0] / "input.json").resolve(strict=True):
                raise ValueError("selected numeric --input must name generated H1.50 input.json")
        character_run = None
        if args.character_output is not None:
            from humanmotionlib.runtime import validate_existing_run_root
            character_run = validate_existing_run_root(args.character_output, workspace)
            if character_run == output_run or character_run.is_relative_to(output_run) or output_run.is_relative_to(character_run):
                raise ValueError("character evidence and verification report runs must be disjoint")
        if args.transforms_only:
            result = verify_transforms(prepared)
        else:
            from humanmotionlib.backend_measurements import verify_backend
            from humanmotionlib.finite import require_finite
            evaluated = json.loads(evaluated_path.read_text())
            require_finite(evaluated)
            from humanmotionlib.verification_run import verify_collection
            if args.thorax_preview or args.squat_preview:
                if args.thorax_preview and args.squat_preview:raise ValueError('Select one preview scope')
                required={'squat'} if args.squat_preview else {'neutral','rest'}
                if {s['fixture'] for s in prepared['samples']} != required:
                    raise ValueError('Preview requires exactly '+str(sorted(required)))
                result=verify_backend(prepared,evaluated,verify_transforms(prepared,evaluated['samples']))
                result['scope']=('evaluated-squat-preview' if args.squat_preview else 'evaluated-thorax-preview')+'; full diagnostics and independent review pending'
            else:
                result = verify_collection(prepared,evaluated,output,verify_transforms,workspace=workspace)
        if args.action_coverage or (not args.transforms_only and not args.thorax_preview and not args.squat_preview):
            from humanmotionlib.coverage import audit_action_cases
            result["action_coverage"] = audit_action_cases(prepared["sources"]["profile"],prepared["sources"]["mobility"])
            if result["action_coverage"]["status"] != "pass": result["status"] = "fail"
            for channel,row in result['action_coverage']['actions'].items():
                family=channel.replace('.L.','.bilateral.').replace('.R.','.bilateral.')
                fixture='sweep-'+family.replace('.','-')
                if fixture not in prepared['sampling']:
                    if channel.startswith(('patella.','knee.')):fixture='sweep-knee-bilateral-flexion'
                    elif channel.startswith(('glenohumeral.','scapula.','clavicle.')):fixture='sweep-shoulder-bilateral-elevation'
                    else:fixture='neutral'
                row['visual']={'status':'pending human judgement','page':fixture+'.html','image':f'clean-a/frames/{fixture}/front/00000.png'}
        if args.dense:
            from humanmotionlib.dense_verification import audit_dense
            result['dense']=audit_dense(prepared['sources'],lambda row:print(f"Dense {row['fixture']}: {row['status']} ({row['samples']} samples)",flush=True))
            if result['dense']['status']!='pass':result['status']='fail'
        if args.dense_floor:
            from humanmotionlib.dense_floor import audit_dense_floor
            geometry=json.loads((input_operand/'geometry-reference.json').read_text())
            result['dense_floor']=audit_dense_floor(prepared,geometry,lambda row:print(f"Dense floor {row['fixture']}: {row['status']} ({row['samples']} samples)",flush=True))
            if result['dense_floor']['status']!='pass':result['status']='fail'
        if args.stature_builds:
            from humanmotionlib.stature_comparison import compare_statures
            result['stature_comparison']=compare_statures(stature_builds)
            if result['stature_comparison']['status']!='pass':result['status']='fail'
            from humanmotionlib.dense_verification import audit_squat_balance
            result['stature_balance']=[]
            for directory in stature_builds:
                source=read_prepared(directory/'input.json')['sources']
                audit=audit_squat_balance(source);result['stature_balance'].append(audit)
                print(f"Dense squat balance H={audit['stature_m']}: {audit['status']} ({audit['samples']} samples)",flush=True)
                if audit['status']!='pass':result['status']='fail'
        if character_run is not None:
            from humanmotionlib.characters import validate_character_sources
            from humanmotionlib.character_verification import verify_character_output
            ids=registered_character_ids or [row['id'] for row in validate_character_sources()]
            if args.numeric_only:
                numeric_runs = [character_run]
                if stature_builds:
                    if character_run not in stature_builds:
                        raise ValueError("--character-output must be one of the --stature-builds numeric runs")
                    numeric_runs = stature_builds
                run_reports=[]
                observed_heights=[]
                matrix_inputs=[]
                for numeric_run in numeric_runs:
                    run_input = numeric_run / "input.json"
                    if not run_input.is_file():
                        raise ValueError(f"Numeric character run has no prepared input: {run_input}")
                    run_prepared = read_prepared(run_input)
                    matrix_inputs.append(run_prepared)
                    observed_heights.append(float(run_prepared["sources"]["profile"]["stature_m"]))
                    run_report = verify_character_output(run_prepared,numeric_run,ids,numeric_only=True,
                        selected_character_id=args.selected_character)
                    run_reports.append({
                        "run": str(numeric_run),
                        "prepared_sha256": run_prepared.get("content_sha256"),
                        "report": run_report,
                    })
                matrix_complete = False
                matrix_failures=[]
                if stature_builds:
                    required_heights=[1.5,1.7,1.9]
                    if len(set(observed_heights)) != len(observed_heights):
                        matrix_failures.append("duplicate stature input")
                    if len(observed_heights)!=3 or any(
                            sum(abs(height-required)<1e-9 for height in observed_heights)!=1
                            for required in required_heights):
                        matrix_failures.append("numeric matrix must contain exactly H=1.50, 1.70 and 1.90 m")
                    if matrix_inputs:
                        reference=matrix_inputs[0]
                        reference_profile=reference["sources"]["profile"]
                        matrix_failures.extend(_matrix_shared_identity_failures(matrix_inputs))
                        try:
                            from humanmotionlib.validate import load_sources, validate_sources
                            profile_id = reference_profile["id"]
                            validate_sources(profile_id)
                            canonical_sources, _ = load_sources(profile_id)
                            consumer_resolver = None
                            if any(item.get("consumer_motion") is not None for item in matrix_inputs):
                                from humanmotionlib.consumer_motion import verify_consumer_snapshot
                                consumer_resolver = verify_consumer_snapshot
                            matrix_failures.extend(_matrix_definition_failures(
                                matrix_inputs, canonical_sources, consumer_resolver))
                        except (KeyError, TypeError, ValueError, OSError) as error:
                            matrix_failures.append(f"canonical matrix source validation failed: {error}")
                    if result.get("stature_comparison",{}).get("status") != "pass":
                        matrix_failures.append("evaluated cross-stature comparison did not pass")
                    generation_identities=[item["report"].get("package_identity",{}).get("generation")
                                           for item in run_reports]
                    if generation_identities and any(value!=generation_identities[0]
                                                     for value in generation_identities[1:]):
                        matrix_failures.append("numeric build receipt package identities differ")
                    matrix_complete=(len(observed_heights)==3 and not matrix_failures and
                        all(sum(abs(height-required)<1e-9 for height in observed_heights)==1
                            for required in required_heights) and
                        all(item["report"].get("numeric_status")=="pass" for item in run_reports))
                scoped_pass = all(item["report"].get("numeric_status")=="pass" for item in run_reports)
                selected_scope = args.selected_character is not None and bool(stature_builds)
                if selected_scope:
                    if any(item["report"].get("verification_scope") != "selected-character-numeric-leaf"
                           or item["report"].get("checked_character_ids") != [args.selected_character]
                           for item in run_reports):
                        matrix_failures.append("selected numeric leaf scope or character membership differs")
                    comparison_complete = (len(observed_heights) == 3 and observed_heights == [1.5, 1.7, 1.9]
                        and not matrix_failures and scoped_pass)
                else:
                    comparison_complete = False
                character_report={
                    "format":"hml-character-numeric-matrix/v1",
                    "status":"incomplete" if scoped_pass else "fail",
                    "numeric_status":"pass" if ((selected_scope and comparison_complete)
                                     or (scoped_pass and (not stature_builds or matrix_complete)))
                                     else ("incomplete" if scoped_pass else "fail"),
                    "scope":("selected-character numeric evidence across exactly three statures; full registry acceptance remains incomplete"
                             if args.selected_character is not None else
                             "per-stature full character numeric evidence; images and visual judgment not assessed"),
                    "rendering":"not-run","visual":"not-assessed",
                    "required_statures_m":[1.5,1.7,1.9],
                    "observed_statures_m":observed_heights,
                    "missing_statures_m":[value for value in (1.5,1.7,1.9)
                        if not any(abs(value-height)<1e-9 for height in observed_heights)],
                    "matrix_complete":False if selected_scope else matrix_complete,
                    "matrix_failures":matrix_failures,"runs":run_reports,
                }
                if selected_scope:
                    character_report.update({"verification_scope":"selected-character-three-stature-numeric",
                        "all_registry_ids":list(ids), "checked_character_ids":[args.selected_character],
                        "unassessed_character_ids":[identifier for identifier in ids
                                                     if identifier != args.selected_character],
                        "comparison_complete":comparison_complete})
            else:
                character_report=verify_character_output(prepared,character_run,ids)
            result['character_verification']=character_report
            if args.selected_character is not None:
                result["verification_scope"]="selected-character-three-stature-numeric"
                result["checked_character_ids"]=[args.selected_character]
                result["unassessed_character_ids"]=[identifier for identifier in ids
                                                    if identifier != args.selected_character]
            if args.numeric_only:
                if character_report["numeric_status"] == "pass":
                    result["numeric_status"]="pass"
                    result["acceptance"]=("selected-character three-stature numeric comparison passed; full registry acceptance remains incomplete"
                        if args.selected_character is not None else
                        "numeric-only pass; rendering, repeatability and human visual acceptance remain pending")
                else:
                    result["status"]="fail" if character_report["numeric_status"]=="fail" else "incomplete"
                    result["numeric_status"]=character_report["numeric_status"]
            elif character_report['status']!='pass':
                result['status']='fail' if character_report['status']=='fail' else 'incomplete'
        # Output and all shards are now known to be inside the selected run.
        output.parent.mkdir(parents=True, exist_ok=True)
        write_json(output,result)
        if args.numeric_only and result.get("numeric_status")=="pass" and result.get("status")=="pass":
            result["status"]="pass"
        print(f"{result['status']}: {result['scope']} ({len(result['samples'])} samples)")
        return 0 if result["status"]=="pass" else 1
    except (ValueError,OSError,KeyError) as error:
        print(str(error),file=sys.stderr)
        return 1


if __name__ == "__main__": raise SystemExit(main())
