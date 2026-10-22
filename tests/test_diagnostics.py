# SPDX-License-Identifier: Apache-2.0
from copy import deepcopy
from fractions import Fraction
import math
import unittest

from tools import math3d as m
from tools.actions import ActionError
from tools.contacts import attachments,contact_checks,solve_contacts
from tools.diagnostics import DiagnosticEvaluator
from tools.measurements import measure_pose
from tools.mirror import mirror_pose
from tools.sampling import sampling
from tools.validate import load_sources,validate_bundle


class DiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources,_=load_sources('adult-reference-v1');cls.evaluator=DiagnosticEvaluator(cls.sources)

    def test_squat_seven_independent_audit_rows_and_support(self):
        evaluator=self.evaluator
        for k,i,hip,y,z in [(0, 4.336808689942018e-18, (1.2980823435802104e-18, -3.0580903601574798e-18, 2.7876468914756417e-18), -1.0183786980436785e-20, 0.4895), (15, -0.7142798145318074, (15.58915829173155, -0.44922754418693106, 3.5148761452294), -0.03224756525938123, 0.4846247616951816), (30, -2.6883777071153503, (30.661728344426873, -1.5743407120396005, 6.076282431707224), -0.059423334726462496, 0.47063379845585157), (45, -3.801628496102256, (46.11634455025933, -2.0572622617115184, 5.157890039632266), -0.08606898584430603, 0.4474068603019031), (60, -4.783206031070607, (61.636011802099716, -2.3665172340515257, 4.28670268265114), -0.10858381409464903, 0.4157010850618596), (75, -5.644182671808673, (77.21081000234639, -2.522124977115177, 3.476078337180324), -0.12549884196496053, 0.3764433246434558), (90, -6.392846611224364, (92.8327718980059, -2.543428129379284, 2.738335387932881), -0.13549659670895722, 0.3308744098065181)]:
            measured,angles,v=evaluator.flat_leg(k,20*k/90,25*k/90)
            self.assertAlmostEqual(measured,i,delta=.00001)
            for a,b in zip(angles,hip):self.assertAlmostEqual(a,b,delta=.00001)
            self.assertAlmostEqual(-v[1]/1.7,y,delta=1e-6)
            self.assertAlmostEqual(.04-v[2]/1.7,z,delta=1e-6)
        bottom=evaluator.evaluate('squat',2)
        self.assertAlmostEqual(bottom['actions']['knee.R.flexion'],90)
        self.assertAlmostEqual(bottom['actions']['lumbar.flexion'],10)
        self.assertAlmostEqual(bottom['actions']['pelvis.pitch'],25)

    def test_all_count_samples_bounds_pins_mirror_and_loops(self):
        e=self.evaluator
        for id in ('squat','arm-raise','walking-in-place','forefoot-rocker'):
            fixture=e.fixtures[id];history={}
            for beat in range(fixture['duration_beats']+1):
                solved=e.evaluate(id,beat)
                report=measure_pose(e.sources['profile'],e.sources['mobility'],solved['frames'],beat,solved['actions'],solved['world_root'])
                self.assertEqual(report['status'],'pass',id)
                checks=contact_checks(e.model.profile,solved['contacts'],attachments(e.model.profile,solved['frames']),beat,history)
                self.assertTrue(all(c['status']=='pass' for c in checks),id)
            first,last=e.evaluate(id,0)['frames'],e.evaluate(id,fixture['duration_beats'])['frames']
            for body in first:
                self.assertLess(m.norm(m.sub(first[body]['position_m'],last[body]['position_m'])),1e-4*1.7)
                self.assertLess(m.angle_error(first[body]['rotation'],last[body]['rotation']),.1)
        right=e.evaluate('walking-in-place',5)['frames'];left=e.evaluate('walking-in-place',1)['frames']
        for id,frame in mirror_pose(left).items():
            self.assertLess(m.norm(m.sub(frame['position_m'],right[id]['position_m'])),1e-4*1.7)
            self.assertLess(m.angle_error(frame['rotation'],right[id]['rotation']),.1)

    def test_half_open_events_and_rocker_terminal_state(self):
        e=self.evaluator
        for beat,feet in [(0,{'R'}),(2,{'L','R'}),(4,{'L'}),(6,{'L','R'}),(8,{'L','R'})]:
            self.assertEqual({c['foot'] for c in e.evaluate('walking-in-place',beat)['contacts']},feet)
        self.assertEqual({c['state'] for c in e.evaluate('forefoot-rocker',3.99)['contacts']},{'ball'})
        self.assertEqual({c['state'] for c in e.evaluate('forefoot-rocker',4)['contacts']},{'flat'})

    def test_rest_policies_masks_and_conflicting_layers(self):
        s=deepcopy(self.sources);f=next(f for f in s['diagnostics'] if f['id']=='arm-raise')
        f['rest_policy']['policy']='hold';e=DiagnosticEvaluator(s)
        with self.assertRaisesRegex(ValueError,'previous'):e.evaluate('arm-raise',1)
        values=deepcopy(e.model.evaluator.defaults);values['cervical.rotation']=10
        self.assertEqual(e.evaluate('arm-raise',1,previous=values)['actions']['cervical.rotation'],10)
        with self.assertRaisesRegex(ValueError,'Conflicting'):e.evaluate('arm-raise',1,previous=values,layers=[{'controls':['arm_R'],'actions':{}}])
        f['rest_policy']['policy']='free';e=DiagnosticEvaluator(s)
        with self.assertRaisesRegex(ValueError,'Unassigned'):e.evaluate('arm-raise',1)
        f['controls'].remove('arm_R');e=DiagnosticEvaluator(s)
        with self.assertRaisesRegex(ValueError,'unowned'):e.evaluate('arm-raise',1,layers=[{'controls':['pelvis','torso','head_neck','arm_R','leg_L','leg_R'],'actions':{}}])

    def test_exact_sampling_contract(self):
        for duration in (4,8):
            for bpm,expected in [(60,5*duration+1),(120,3*duration+1),(180,3*duration+1)]:
                plan=sampling(duration,bpm)
                self.assertEqual(len(plan['static']),duration+1);self.assertEqual(len(plan['animation']),expected)
                times=[Fraction(s['seconds']['numerator'],s['seconds']['denominator']) for s in plan['animation']]
                self.assertEqual(len(times),len(set(times)))
                self.assertTrue(all(b-a<=Fraction(1,5) for a,b in zip(times,times[1:])))
                self.assertGreaterEqual(plan['intervals_per_beat'],3)

    def test_bounded_contact_solver_seed_order_and_unreachable_target(self):
        e=self.evaluator;model=e.model
        start=e.evaluate('neutral',0);points=attachments(model.profile,start['frames'])
        pin={'anchor':'contact.heel.R','target_m':m.add(points['contact.heel.R']['position_m'],[0,.005,0])}
        kwargs=dict(model=model,requested={},pins=[pin],free_channels=['pelvis.y'],owners=e.owners,controls=['pelvis'],beat=1)
        a=solve_contacts(**kwargs);b=solve_contacts(**kwargs)
        self.assertEqual(a,b);self.assertEqual(a['state'],'valid')
        self.assertLess(a['normalized_residual'],1e-5)
        original=deepcopy(pin);pin['target_m']=[0,50,0]
        failed=solve_contacts(**kwargs)
        self.assertEqual(failed['state'],'unsatisfied-constraint')
        self.assertEqual(failed['requested_targets'],[pin]);self.assertNotIn('solution',failed)
        self.assertIn('limits',failed['errors'][0]['joint_residuals'])
        with self.assertRaisesRegex(ValueError,'outside controls'):solve_contacts(**(kwargs|{'controls':['leg_R']}))

    def test_contact_solver_rejects_intent_before_seed_substitution(self):
        e=self.evaluator
        neutral=e.evaluate('neutral',0)
        point=attachments(e.model.profile,neutral['frames'])['contact.heel.R']['position_m']
        kwargs=dict(model=e.model,pins=[{'anchor':'contact.heel.R','target_m':point}],
                    free_channels=['pelvis.y'],owners=e.owners,controls=['pelvis'],beat=1)
        with self.assertRaises(ActionError) as caught:
            solve_contacts(**kwargs,requested={'pelvis.y':50},previous={'pelvis.y':0})
        error=caught.exception.report['errors'][0]
        self.assertEqual((error['action'],error['measured'],error['beat']),('pelvis.y',50,1))
        self.assertEqual(caught.exception.report['state'],'out-of-range')
        # At sequence start, a valid free-channel hint cannot replace the
        # prescribed neutral seed; a neutral target is already satisfied.
        result=solve_contacts(**kwargs,requested={'pelvis.y':.01})
        self.assertEqual(result['state'],'valid')
        self.assertEqual(result['iterations'],0)
        self.assertEqual(result['actions']['pelvis.y'],0)
        shifted=m.add(point,[0,.01,0])
        result=solve_contacts(**(kwargs|{'pins':[{'anchor':'contact.heel.R','target_m':shifted}]}),
                              requested={},previous={'pelvis.y':.01})
        self.assertEqual(result['iterations'],0)
        self.assertEqual(result['actions']['pelvis.y'],.01)

    def test_three_statures_scale_contact_targets_and_analytic_frames(self):
        from tools.poses import scaled_profile,scale_meter_fields
        for height in (1.5,1.7,1.9):
            sources=deepcopy(self.sources)
            sources['profile']=scaled_profile(sources['profile'],height)
            sources['mobility']=scale_meter_fields(sources['mobility'],height/1.7)
            sources['diagnostics']=scale_meter_fields(sources['diagnostics'],height/1.7)
            evaluator=DiagnosticEvaluator(sources)
            for id in ('squat','forefoot-rocker','arm-raise','walking-in-place'):
                for beat in (0,1,2,4):
                    solved=evaluator.evaluate(id,beat)
                    checks=contact_checks(sources['profile'],solved['contacts'],attachments(sources['profile'],solved['frames']),beat)
                    self.assertTrue(all(c['status']=='pass' for c in checks))
                    reference=self.evaluator.evaluate(id,beat)
                    for body,frame in solved['frames'].items():
                        self.assertLess(m.norm(m.sub(frame['position_m'],m.scale(reference['frames'][body]['position_m'],height/1.7))),1e-6*height)
                        self.assertLess(m.angle_error(frame['rotation'],reference['frames'][body]['rotation']),.1)

    def test_prepared_modes_refer_to_one_animation_and_exact_events(self):
        from tools.prepare_skeleton import prepare
        prepared=prepare('adult-reference-v1',fixtures=['arm-raise','walking-in-place'])
        lookup={s['id']:s for s in prepared['samples']}
        for id,plans in prepared['sampling'].items():
            common={}
            for plan in plans:
                animation={Fraction(s['beat']['numerator'],s['beat']['denominator']):s for s in plan['animation']}
                for static in plan['static']:
                    beat=Fraction(static['beat']['numerator'],static['beat']['denominator'])
                    self.assertEqual(animation[beat]['sample_id'],static['sample_id'])
                    if beat in common:self.assertEqual(common[beat],static['sample_id'])
                    common[beat]=static['sample_id']
                    solved=self.evaluator.evaluate(id,float(beat))
                    self.assertEqual(lookup[static['sample_id']]['frames'],solved['frames'])
