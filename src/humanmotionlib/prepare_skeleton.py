# SPDX-License-Identifier: Apache-2.0
"""Validate canonical sources and prepare solved, backend-independent JSON."""

import argparse
from copy import deepcopy
from pathlib import Path
import sys

from fractions import Fraction
from humanmotionlib.diagnostics import DiagnosticEvaluator
from humanmotionlib.sampling import delivered_beats, rational, sampling
from humanmotionlib.guides import solve_guides
from humanmotionlib.kinematics import KinematicModel
from humanmotionlib.poses import neutral_pose, rest_pose, scale_meter_fields, scaled_profile, to_deltas
from humanmotionlib.prepared import seal, write_json
from humanmotionlib.runtime import (backend_contract, ensure_workspace_build,
                                    resolve_workspace_path, validate_run_root, workspace_root)
from humanmotionlib.package_resources import manifest_sha256, runtime_manifest
from humanmotionlib.validate import load_sources, validate_sources


def prepare(profile_id,stature=None,fixtures=None,bpms=(60,120,180)):
    validation = validate_sources(profile_id)
    sources,_ = load_sources(profile_id)
    reference_height = sources["profile"]["stature_m"]
    height = reference_height if stature is None else stature
    sources = deepcopy(sources)
    sources["profile"] = scaled_profile(sources["profile"],height)
    # Placement bounds/neutral values are dimensioned; angles and H-ratios are not.
    sources["mobility"] = scale_meter_fields(sources["mobility"],height/reference_height)
    sources["diagnostics"] = scale_meter_fields(sources["diagnostics"],height/reference_height)
    evaluator = DiagnosticEvaluator(sources)
    samples,plans = [],{}
    fixture_ids = {f['id'] for f in sources['diagnostics']}
    if fixtures is not None and (not fixtures or set(fixtures)-fixture_ids):
        raise ValueError('Unknown/empty fixture subset')
    for fixture in sorted(sources['diagnostics'],key=lambda f:f['id']):
        if fixtures is not None and fixture['id'] not in fixtures:continue
        beats = delivered_beats(fixture['duration_beats'],bpms)
        ids = {beat:fixture['id']+f'/{index:05d}' for index,beat in enumerate(beats)}
        plans[fixture['id']] = []
        for bpm in bpms:
            plan = sampling(fixture['duration_beats'],bpm)
            for mode in ('static','animation'):
                for record in plan[mode]:
                    beat = Fraction(record['beat']['numerator'],record['beat']['denominator'])
                    record['sample_id'] = ids[beat]
            plans[fixture['id']].append(plan)
        for index,beat in enumerate(beats):
            solved = evaluator.evaluate(fixture['id'],float(beat))
            samples.append({'id':ids[beat],'fixture':fixture['id'],'beat':rational(beat),
                            'seconds':rational(beat*Fraction(1,2)),'frame_id':index,
                            'expected_actions':solved['actions'],'world_root':deepcopy(solved['world_root']),
                            'contacts':solved['contacts'],'frames':solved['frames'],'guides':solved['guides'],
                            'fk_deltas':to_deltas(sources['profile'],solved['frames']),
                            'static':beat.denominator==1,'animation':True})
    manifest=runtime_manifest()
    return seal({'format':'skeleton-prepared/v1','sources':sources,
                 'source_hashes':validation['source_hashes'],'backend_contract':backend_contract(),
                 'package_identity':{'version':manifest['version'],'manifest_sha256':manifest_sha256(),
                                     'implementation':manifest['implementation']},
                 'samples':samples,'sampling':plans,'primary_bpm':120,
                 'units':{'positions':'m','rotations':'active-right-handed-matrix3','quaternion':'wxyz'},
                 'limitations':['Kinematic animation approximation; no clinical validation.',
                                 'Prepared transforms do not establish evaluated-mesh, contact, render, or human acceptance.']})


def main(workspace=None, argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile",required=True)
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--stature",type=float)
    parser.add_argument("--fixtures",nargs="+",help="Explicit diagnostic subset for isolated builds")
    args = parser.parse_args(argv)
    try:
        from humanmotionlib.api import prepare as public_prepare
        result = public_prepare(workspace=workspace, output=args.output, profile=args.profile,
                                stature=args.stature, fixtures=args.fixtures)
        print(f"Prepared {len(result.poses)} samples: {result.prepared_path}")
        return 0
    except (ValueError, OSError) as error:
        print(str(error),file=sys.stderr)
        return 1
    except RuntimeError as error:
        print(str(error),file=sys.stderr)
        return 1


if __name__ == "__main__": raise SystemExit(main())
