# SPDX-License-Identifier: Apache-2.0
"""Review cards must not change anatomical angles through unequal XY scaling."""
from fractions import Fraction
from pathlib import Path
import tempfile
import unittest
from PIL import Image,ImageDraw
from humanmotionlib.review_graphics import sheet,gif


class ReviewAspectTests(unittest.TestCase):
    def test_circle_remains_round_in_rectangular_review_card_previews(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source.png'
            image=Image.new('RGB',(600,300),'white');draw=ImageDraw.Draw(image)
            draw.ellipse((250,100,350,200),fill='black');image.save(source)
            sheet([source],[''],root/'sheet.png',columns=1)
            report=gif([source]*3,Fraction(1,5),root/'preview.gif')
            self.assertEqual(report['status'],'pass')
            for name in ('sheet.png','preview.gif'):
                with self.subTest(name=name),Image.open(root/name) as result:
                    rgb=result.convert('RGB');dark=[(x,y) for y in range(rgb.height) for x in range(rgb.width) if max(rgb.getpixel((x,y)))<30]
                    self.assertTrue(dark)
                    width=max(x for x,y in dark)-min(x for x,y in dark)
                    height=max(y for x,y in dark)-min(y for x,y in dark)
                    self.assertLessEqual(abs(width-height),2)
