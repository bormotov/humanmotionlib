# SPDX-License-Identifier: Apache-2.0
from copy import deepcopy
import math
import unittest
from unittest.mock import patch
from humanmotionlib import math3d as m
from humanmotionlib.balance import (validate_mass_model, mass_observations, static_balance,
                           measure_balance, mirror_mass_segment)
from humanmotionlib.contacts import attachments, contact_checks
from humanmotionlib.diagnostics import DiagnosticEvaluator
from humanmotionlib.poses import scaled_profile, scale_meter_fields
from humanmotionlib.validate import load_sources, validate_bundle
from humanmotionlib.source_validation import SourceValidationError
from humanmotionlib.dense_verification import audit_squat_balance, audit_dense


class BalanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources,_=load_sources('adult-reference-v1')

    def evidence(self,sources,beat):
        e=DiagnosticEvaluator(sources);p=e.evaluate('squat',beat)
        observed={'frames':p['frames'],'mass_points':mass_observations(sources['profile'],p['frames']),
                  'attachments':attachments(sources['profile'],p['frames'])}
        return p,observed

    def test_dense_statures_native_units_and_reference_bottom(self):
        for height in (1.5,1.7,1.9):
            sources=deepcopy(self.sources);sources['profile']=scaled_profile(sources['profile'],height)
            sources['mobility']=scale_meter_fields(sources['mobility'],height/1.7)
            sources['diagnostics']=scale_meter_fields(sources['diagnostics'],height/1.7)
            e=DiagnosticEvaluator(sources)
            for n in range(401):
                beat=n/100;p=e.evaluate('squat',beat)
                sample={'frames':p['frames'],'mass_points':mass_observations(sources['profile'],p['frames']),
                        'attachments':attachments(sources['profile'],p['frames'])}
                result=measure_balance(sources['profile'],sample,p['contacts'],beat,True)
                self.assertEqual(result['status'],'pass',(height,beat,result['checks']))
                a=result['assessment']
                self.assertGreaterEqual(a['variants']['reference']['margin_h'],.010)
                self.assertGreaterEqual(a['perturbation_lower_bound_h'],.005)
                for variant in a['variants'].values():self.assertAlmostEqual(sum(variant['fractions'].values()),1,delta=1e-12)
            p,sample=self.evidence(sources,2);a=static_balance(sources['profile'],sample['mass_points'],sample['attachments'],p['contacts'])
            self.assertAlmostEqual(a['variants']['reference']['com_m'][1]/height,-.00792753253808,delta=1e-10)
            self.assertAlmostEqual(p['frames']['knee.R']['position_m'][1]/height,.0807945981124,delta=1e-10)

    def test_original_squat_fails_balance_while_contacts_pass(self):
        sources=deepcopy(self.sources)
        f=next(f for f in sources['diagnostics'] if f['id']=='squat')
        for track in f['tracks']:
            peak=25 if track['channel']=='pelvis.pitch' else 20 if track['channel'].startswith('ankle.') else None
            if peak:
                for key in track['keys']:key['value']*=12/peak
        p,observed=self.evidence(sources,2)
        self.assertTrue(all(c['status']=='pass' for c in contact_checks(sources['profile'],p['contacts'],observed['attachments'])))
        r=measure_balance(sources['profile'],observed,p['contacts'],2,True)
        self.assertEqual(r['status'],'fail')
        self.assertTrue(any(c['id']=='balance.reference_margin' and c['status']=='fail' for c in r['checks']))
        self.assertAlmostEqual(r['assessment']['variants']['reference']['com_m'][1]/1.7,-.0650806008562,delta=1e-10)

    def test_dense_squat_audit_retains_each_complete_observation_and_context_link(self):
        with patch('humanmotionlib.dense_verification.dense_beats',return_value=[0.,2.25,4.]):
            report=audit_squat_balance(self.sources)
        self.assertEqual(report['status'],'pass')
        self.assertEqual(len(report['observations']),3)
        middle=report['observations'][1]
        self.assertEqual(middle['beat'],2.25)
        self.assertEqual(set(middle['mass_points']),{r['id'] for r in self.sources['profile']['mass_model']['segments']})
        self.assertEqual(len(middle['measured_support_points']),6)
        self.assertEqual(len(middle['assessment']['support_xy_m']),4)
        self.assertEqual(set(middle['assessment']['variants']),{'reference','male_weights','female_weights'})
        self.assertEqual(len(middle['assessment']['variants']['reference']['edge_margins_m']),4)
        self.assertIn('perturbation_lower_bound_h',middle['assessment'])
        self.assertEqual(middle['units']['edge_margins'],'m')
        self.assertFalse(middle['image_reference']['exact_match'])
        self.assertEqual(middle['image_reference']['relationship'],'nearest-delivered-render-context')
        self.assertEqual(report['extrema']['perturbation_lower_bound_h']['minimum']['sample_id'],report['minimum'] and min(report['observations'],key=lambda s:s['assessment']['perturbation_lower_bound_h'])['sample_id'])

    def test_dense_squat_audit_retains_failed_sample_evidence(self):
        sources=deepcopy(self.sources);fixture=next(f for f in sources['diagnostics'] if f['id']=='squat')
        for track in fixture['tracks']:
            peak=25 if track['channel']=='pelvis.pitch' else 20 if track['channel'].startswith('ankle.') else None
            if peak:
                for key in track['keys']:key['value']*=12/peak
        with patch('humanmotionlib.dense_verification.dense_beats',return_value=[2.]):
            report=audit_squat_balance(sources)
        self.assertEqual(report['status'],'fail')
        sample=report['observations'][0]
        self.assertEqual(sample['status'],'fail')
        self.assertIsNotNone(sample['assessment'])
        self.assertTrue(any(c['id']=='balance.reference_margin' and c['status']=='fail' for c in sample['checks']))
        self.assertEqual(len(report['failures']),sum(c['status']!='pass' for c in sample['checks']))

    def test_dense_combined_report_retains_squat_assessments(self):
        def sample_grid(fixture):
            return [0.,2.,4.] if fixture['id']=='squat' else [0.,fixture['duration_beats']]
        with patch('humanmotionlib.dense_verification.dense_beats',side_effect=sample_grid):
            report=audit_dense(self.sources)
        squat=next(row for row in report['fixtures'] if row['fixture']=='squat')
        retained=squat['static_balance']
        self.assertEqual(len(retained['observations']),3)
        self.assertEqual(retained['samples'],squat['samples'])
        self.assertEqual(squat['static_balance_minimum']['beat'],retained['extrema']['perturbation_lower_bound_h']['minimum']['beat'])
        self.assertEqual(len(retained['observations'][1]['assessment']['mass_points']),16)

    def test_missing_forged_mass_and_observed_support(self):
        p,observed=self.evidence(self.sources,2);profile=self.sources['profile']
        for mutation in ('missing','forged','posterior','support','degenerate'):
            sample=deepcopy(observed)
            if mutation=='missing':sample['mass_points'].pop('head')
            if mutation=='forged':sample['mass_points']['head']['position_m'][1]+=.1
            if mutation=='posterior':
                for id in ('head','upper_trunk','abdomen','pelvis'):sample['mass_points'][id]['position_m'][1]-=.3
            if mutation=='support':
                # Intact declared targets cannot conceal shifted observations.
                for a in sample['attachments'].values():a['position_m'][1]+=.5
            if mutation=='degenerate':
                for a in sample['attachments'].values():a['position_m']=[0,0,0]
            with self.subTest(mutation=mutation):self.assertEqual(measure_balance(profile,sample,p['contacts'],2,True)['status'],'fail')
        r=measure_balance(profile,observed,[],2,True)
        self.assertEqual(r['status'],'fail')

    def test_closed_mass_contract_and_frozen_coefficients(self):
        for mutation in ('missing','extra','duplicate','zero','negative','nan','carrier','offset','equal','unknown','id'):
            sources=deepcopy(self.sources);model=sources['profile']['mass_model'];r=model['segments'][0]
            if mutation=='missing':model['segments'].pop()
            if mutation=='extra':model['segments'].append(deepcopy(r)|{'id':'extra'})
            if mutation=='duplicate':model['segments'][-1]=deepcopy(r)
            if mutation in ('zero','negative','nan','equal'):r['weight_kg']={'zero':0,'negative':-1,'nan':float('nan'),'equal':1}[mutation]
            if mutation=='carrier':r['body']='absent'
            if mutation=='offset':r['position_m'][0]+=.1
            if mutation=='unknown':r['unknown']=1
            if mutation=='id':model['id']='other'
            with self.subTest(mutation=mutation):
                with self.assertRaises(SourceValidationError):validate_bundle(sources)

    def test_mirror_and_scaling_preserve_mass_budget(self):
        profile=self.sources['profile'];index=validate_mass_model(profile)
        for id,r in index.items():
            self.assertEqual(mirror_mass_segment(mirror_mass_segment(r)),r)
            if id.endswith('.R'):
                left=index[id[:-1]+'L'];mirrored=mirror_mass_segment(r)
                self.assertEqual(left['body'],mirrored['body'])
                self.assertLess(m.norm(m.sub(left['position_m'],mirrored['position_m'])),1e-12)
        scaled=scaled_profile(profile,1.9);validate_mass_model(scaled)
        for a,b in zip(profile['mass_model']['segments'],scaled['mass_model']['segments']):
            self.assertEqual(a['weight_kg'],b['weight_kg'])
            self.assertLess(m.norm(m.sub(b['position_m'],[v*1.9/1.7 for v in a['position_m']])),1e-12)

    def test_ankle_twenty_bound_and_unchanged_reference_observations(self):
        e=DiagnosticEvaluator(self.sources)
        for side in ('L','R'):
            action='ankle.'+side+'.dorsiflexion'
            self.assertEqual(e.model.evaluator.actions[action]['bounds_deg'],[-40,20])
            e.model.solve({action:20})
            with self.assertRaises(ValueError):e.model.solve({action:20.5})
        r=next(r for r in self.sources['mobility']['reference_observations'] if r['action']=='ankle.dorsiflexion')
        self.assertEqual((r['female_deg'],r['male_deg']),(13.8,12.7))

    def test_nonuniform_mass_arithmetic_and_signed_polygon_edges(self):
        p,observed=self.evidence(self.sources,2);profile=self.sources['profile']
        # Independent hand-calculable case: only the head mass has X=1 m.
        for point in observed['mass_points'].values():point['position_m']=[0,0,1]
        observed['mass_points']['head']['position_m'][0]=1
        for i,id in enumerate(sorted({id for c in p['contacts'] for id in c['anchors']})):
            observed['attachments'][id]['position_m']=[(-1,1)[i%2],(-1,1)[(i//2)%2],0]
        a=static_balance(profile,observed['mass_points'],observed['attachments'],p['contacts'])
        expected=5.45/74.15
        self.assertAlmostEqual(a['variants']['reference']['com_m'][0],expected,delta=1e-12)
        self.assertAlmostEqual(a['variants']['reference']['margin_h'],(1-expected)/1.7,delta=1e-12)
        for point in observed['mass_points'].values():point['position_m'][0]=2
        a=static_balance(profile,observed['mass_points'],observed['attachments'],p['contacts'])
        self.assertAlmostEqual(a['variants']['reference']['margin_h'],-1/1.7,delta=1e-12)

    def test_independent_scalar_squat_closure(self):
        # Independent test arithmetic; no production FK/articulation/flat-leg
        # solver is used to derive these expected leg matrices and positions.
        from test_walking_dossier import multiply,transform,rx,rz,transpose,axis_rotation
        evaluator=DiagnosticEvaluator(self.sources)
        axis=[-math.sin(math.radians(23))*math.cos(math.radians(40)),
              math.cos(math.radians(23))*math.cos(math.radians(40)),math.sin(math.radians(40))]
        for knee in range(0,91,3):
            t=min(1,knee/30);K=multiply(rx(-knee),rz(8*(3*t*t-2*t*t*t)))
            shift=[0,-.003*math.sin(math.radians(knee)),-.001*(1-math.cos(math.radians(knee)))]
            shank=transform(K,[0,0,-.2155]);vector=[shank[j]+shift[j]+[0,0,-.234][j] for j in range(3)]
            P=rx(-25*knee/90)
            def trial(i):
                U=multiply(transpose(P),transpose(multiply(K,multiply(rx(20*knee/90),axis_rotation(axis,i)))))
                return U,transform(multiply(P,U),vector)
            lo,hi=-10,20
            for _ in range(60):
                mid=(lo+hi)/2
                if trial(lo)[1][0]*trial(mid)[1][0]<=0:hi=mid
                else:lo=mid
            i=(lo+hi)/2;U,v=trial(i)
            angles=[math.degrees(math.atan2(-U[1][2],U[2][2])),math.degrees(math.asin(U[0][2])),-math.degrees(math.atan2(-U[0][1],U[0][0]))]
            actual,hip,measured=evaluator.flat_leg(knee,20*knee/90,25*knee/90)
            self.assertAlmostEqual(actual,i,delta=1e-10)
            for x,y in zip(hip,angles):self.assertAlmostEqual(x,y,delta=1e-10)
            for x,y in zip(measured,v):self.assertAlmostEqual(x/1.7,y,delta=1e-12)
