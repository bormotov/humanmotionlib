# SPDX-License-Identifier: Apache-2.0
"""Anatomical action validation with explicit failure states and no correction."""

from copy import deepcopy
import math

from tools.articulation import linear_sample, shoulder, swing_twist


class ActionError(ValueError):
    def __init__(self, report):
        self.report = report
        super().__init__(str(report["errors"]))


def error_record(state, joint, action, measured, bounds, beat, condition):
    if isinstance(measured,float) and not math.isfinite(measured): measured = repr(measured)
    return {"state":state,"joint":joint,"action":action,"measured":deepcopy(measured),
            "bounds":deepcopy(bounds),"beat":beat,"condition":condition}


def constraint_failure(joint, action, residual, allowed, beat, target, joint_residuals):
    error = error_record("unsatisfied-constraint",joint,action,residual,[0,allowed],beat,
                         "Requested contact cannot be satisfied inside the declared rigid/mobility bounds")
    error["requested_target"] = deepcopy(target)
    error["joint_residuals"] = deepcopy(joint_residuals)
    return {"state":"unsatisfied-constraint","errors":[error]}


def require_valid(report):
    if report["state"] != "valid": raise ActionError(report)
    return report["values"]


class ActionEvaluator:
    def __init__(self, mobility):
        self.mobility = mobility
        self.actions = {a["id"]:a for a in mobility["actions"]+mobility["placements"]}
        self.couplings = {c["id"]:c for c in mobility["couplings"]}
        self.defaults = {id:a["neutral_deg" if "neutral_deg" in a else "neutral_m"]
                         for id,a in self.actions.items() if a.get("mode","independent") == "independent"}

    def evaluate(self, requested=None, beat=0):
        requested = {} if requested is None else requested
        if not isinstance(requested,dict):raise ValueError('Action intent must be a mapping')
        values, errors, measurements = deepcopy(self.defaults), [], {}
        for id in sorted(requested):
            value = requested[id]
            action = self.actions.get(id)
            if action is None or action.get("mode","independent") != "independent":
                errors.append(error_record("unsupported",action["joint"] if action else id.rsplit(".",1)[0],
                                           id,value,None,beat,"No independent action is supported for this channel"))
                continue
            suffix = "deg" if "bounds_deg" in action else "m"
            bounds = action["bounds_"+suffix]
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
                errors.append(error_record("out-of-range",action["joint"],id,value,bounds,beat,"Expected a finite numeric action value"))
                continue
            values[id] = value
            if not bounds[0]-1e-9 <= value <= bounds[1]+1e-9:
                errors.append(error_record("out-of-range",action["joint"],id,value,bounds,beat,"Outside operating bounds ("+suffix+")"))
        if errors:
            state = "unsupported" if any(e["state"] == "unsupported" for e in errors) else "out-of-range"
            return {"state":state,"errors":errors,"values":values,"measurements":measurements}
        for id,coupling in sorted(self.couplings.items()):
            p = coupling["parameters"]
            if coupling["type"] == "multiaxis_envelope":
                score = 0
                for name in p["action_ids"]:
                    value = values[name]
                    bounds = self.actions[name]["bounds_deg"]
                    denominator = bounds[1] if value >= 0 else -bounds[0]
                    score += (value/denominator)**p["exponent"]
                measurements[id] = {"score":score,"allowed":1}
                if score > 1+1e-9:
                    errors.append(error_record("out-of-range",id,"combined",score,[0,1],beat,"Sign-specific multiaxis envelope exceeded"))
            elif coupling["type"] == "spine_budget":
                total = sum(values[name] for name in p["action_ids"])
                if not p["bounds_deg"][0]-1e-9 <= total <= p["bounds_deg"][1]+1e-9:
                    errors.append(error_record("out-of-range",id,"combined",total,p["bounds_deg"],beat,"Thoracic/lumbar combined budget exceeded"))
            elif coupling["type"] == "shoulder_sector":
                side = id.split(".")[1]
                e,psi,tau = [values[f"shoulder.{side}.{name}"] for name in ("elevation","plane","external_twist")]
                if abs(e) < 1e-12 and abs(psi) > 1e-12:
                    errors.append(error_record("out-of-range","humerus."+side,"plane",psi,[0,0],beat,"Azimuth must be canonical zero at zero elevation"))
                    continue
                maximum = linear_sample(p["azimuth_deg"],p["elevation_deg"],psi)
                twist_bounds = self.actions[f"shoulder.{side}.external_twist"]["bounds_deg"]
                twist_max = twist_bounds[1] if tau >= 0 else -twist_bounds[0]
                score = (e/maximum)**2+(tau/twist_max)**2
                if score > 1+1e-9:
                    errors.append(error_record("out-of-range","humerus."+side,"elevation/twist",score,[0,1],beat,"Shoulder sector/twist envelope exceeded"))
                girdle = self.couplings[f"shoulder.{side}.girdle"]["parameters"]
                solved = shoulder(girdle,e,psi,tau,side)
                swing,twist = swing_twist(solved["glenohumeral"],self.actions[f"glenohumeral.{side}.twist"]["axis"])
                measurements["shoulder."+side] = {"total_elevation_deg":e,"plane_deg":psi,
                    "total_twist_deg":tau,"glenohumeral_swing_deg":swing,"glenohumeral_twist_deg":twist,
                    "sector_max_deg":maximum,"envelope_score":score}
                if swing > p["gh_swing_max_deg"]+1e-9 or abs(twist) > p["gh_twist_max_deg"]+1e-9:
                    errors.append(error_record("out-of-range","humerus."+side,"glenohumeral",
                        {"swing_deg":swing,"twist_deg":twist},
                        {"swing_max_deg":p["gh_swing_max_deg"],"twist_abs_max_deg":p["gh_twist_max_deg"]},beat,
                        "Dependent glenohumeral guard exceeded"))
        return {"state":"out-of-range" if errors else "valid","errors":errors,
                "values":values,"measurements":measurements}
