# SPDX-License-Identifier: Apache-2.0
"""Measure supplied body transforms independently; missing backend evidence fails."""

import argparse
import json
from pathlib import Path
import sys

from humanmotionlib import math3d as m
from humanmotionlib.measurements import Measurements, measure_pose
from humanmotionlib.prepared import read_prepared, write_json
from humanmotionlib.poses import neutral_pose, rest_pose


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


def main():
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
    args = parser.parse_args()
    try:
        path = args.input/"input.json" if args.input.is_dir() else args.input
        prepared = read_prepared(path)
        if args.transforms_only:
            result = verify_transforms(prepared)
        else:
            from humanmotionlib.backend_measurements import verify_backend
            from humanmotionlib.finite import require_finite
            evaluated = json.loads((args.input/'evaluated.json').read_text())
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
                result = verify_collection(prepared,evaluated,args.output,verify_transforms)
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
            geometry=json.loads((args.input/'geometry-reference.json').read_text())
            result['dense_floor']=audit_dense_floor(prepared,geometry,lambda row:print(f"Dense floor {row['fixture']}: {row['status']} ({row['samples']} samples)",flush=True))
            if result['dense_floor']['status']!='pass':result['status']='fail'
        if args.stature_builds:
            from humanmotionlib.stature_comparison import compare_statures
            result['stature_comparison']=compare_statures(args.stature_builds)
            if result['stature_comparison']['status']!='pass':result['status']='fail'
            from humanmotionlib.dense_verification import audit_squat_balance
            result['stature_balance']=[]
            for directory in args.stature_builds:
                source=read_prepared(directory/'input.json')['sources']
                audit=audit_squat_balance(source);result['stature_balance'].append(audit)
                print(f"Dense squat balance H={audit['stature_m']}: {audit['status']} ({audit['samples']} samples)",flush=True)
                if audit['status']!='pass':result['status']='fail'
        write_json(args.output,result)
        print(f"{result['status']}: {result['scope']} ({len(result['samples'])} samples)")
        return 0 if result["status"]=="pass" else 1
    except (ValueError,OSError,KeyError) as error:
        print(str(error),file=sys.stderr)
        return 1


if __name__ == "__main__": raise SystemExit(main())
