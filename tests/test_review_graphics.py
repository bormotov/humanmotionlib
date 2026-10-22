# SPDX-License-Identifier: Apache-2.0
from fractions import Fraction
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from tools.review_graphics import gif,label,onion,sheet
from tools.review_pack import decoded_digest


class ReviewGraphicsTests(unittest.TestCase):
    def test_gif_decoded_duration_error_and_endpoint_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);paths=[]
            for i in range(25):
                path=root/f'{i}.png';Image.new('RGB',(32,32),((i*7)%255,50,100)).save(path);paths.append(path)
            for bpm,n in ((60,5),(120,3),(180,3)):
                selected=paths[:4*n+1]
                result=gif(selected,Fraction(60,bpm*n),root/f'{bpm}.gif')
                self.assertEqual(result['status'],'pass');self.assertLess(result['error_ms'],10)
                self.assertEqual(result['expected_duration_ms'],float(Fraction(4*60*1000,bpm)))

    def test_composites_and_decoded_pixel_comparison(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);paths=[]
            for i,color in enumerate(('white','black','red')):
                path=root/f'{i}.png';Image.new('RGB',(64,64),color).save(path);paths.append(path)
            sheet(paths,['BEAT 0','BEAT 1','BEAT 2'],root/'sheet.png')
            onion(paths,root/'onion.png')
            self.assertTrue((root/'sheet.png').is_file());self.assertTrue((root/'onion.png').is_file())
            self.assertNotEqual(decoded_digest(paths[0]),decoded_digest(paths[1]))
            first=Image.new('RGB',(100,30),'white');label(first,'TEST 1/2')
            second=Image.new('RGB',(100,30),'white');label(second,'TEST 1/2')
            self.assertEqual(first.tobytes(),second.tobytes())
