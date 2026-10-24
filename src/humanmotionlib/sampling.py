# SPDX-License-Identifier: Apache-2.0
"""Beat geometry is independent of BPM; exact rationals describe delivered times."""

from fractions import Fraction
import math


def rational(value):
    value=Fraction(value)
    return {'numerator':value.numerator,'denominator':value.denominator}


def sampling(duration,bpm):
    if isinstance(duration,bool) or not isinstance(duration,int) or duration<0:raise ValueError('Integer non-negative beat duration required')
    if bpm<=0 or not math.isfinite(bpm):raise ValueError('Positive finite BPM required')
    beat_seconds=Fraction(60)/Fraction(str(bpm))
    intervals=max(3,math.ceil(beat_seconds/Fraction(1,5)))
    animation=[Fraction(i,intervals) for i in range(duration*intervals+1)]
    return {'bpm':bpm,'intervals_per_beat':intervals,
            'animation':[{'beat':rational(b),'seconds':rational(b*beat_seconds),'frame_id':i} for i,b in enumerate(animation)],
            'static':[{'beat':rational(Fraction(b)),'seconds':rational(b*beat_seconds),'frame_id':b*intervals} for b in range(duration+1)]}


def delivered_beats(duration,bpms=(60,120,180)):
    return sorted({Fraction(s['beat']['numerator'],s['beat']['denominator']) for bpm in bpms for s in sampling(duration,bpm)['animation']})
