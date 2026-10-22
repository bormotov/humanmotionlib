# SPDX-License-Identifier: Apache-2.0
"""Repository-authored bitmap lettering and deterministic review composites."""

from fractions import Fraction
from PIL import Image,ImageDraw,ImageOps

# Original simple 5x7 glyphs for image labels; no imported font asset.
PATTERNS={
'A':['01110','10001','10001','11111','10001','10001','10001'],
'B':['11110','10001','10001','11110','10001','10001','11110'],
'C':['01111','10000','10000','10000','10000','10000','01111'],
'D':['11110','10001','10001','10001','10001','10001','11110'],
'E':['11111','10000','10000','11110','10000','10000','11111'],
'F':['11111','10000','10000','11110','10000','10000','10000'],
'G':['01111','10000','10000','10111','10001','10001','01111'],
'H':['10001','10001','10001','11111','10001','10001','10001'],
'I':['11111','00100','00100','00100','00100','00100','11111'],
'J':['00111','00010','00010','00010','10010','10010','01100'],
'K':['10001','10010','10100','11000','10100','10010','10001'],
'L':['10000','10000','10000','10000','10000','10000','11111'],
'M':['10001','11011','10101','10101','10001','10001','10001'],
'N':['10001','11001','11001','10101','10011','10011','10001'],
'O':['01110','10001','10001','10001','10001','10001','01110'],
'P':['11110','10001','10001','11110','10000','10000','10000'],
'Q':['01110','10001','10001','10001','10101','10010','01101'],
'R':['11110','10001','10001','11110','10100','10010','10001'],
'S':['01111','10000','10000','01110','00001','00001','11110'],
'T':['11111','00100','00100','00100','00100','00100','00100'],
'U':['10001','10001','10001','10001','10001','10001','01110'],
'V':['10001','10001','10001','10001','10001','01010','00100'],
'W':['10001','10001','10001','10101','10101','10101','01010'],
'X':['10001','10001','01010','00100','01010','10001','10001'],
'Y':['10001','10001','01010','00100','00100','00100','00100'],
'Z':['11111','00001','00010','00100','01000','10000','11111'],
'0':['01110','10001','10011','10101','11001','10001','01110'],
'1':['00100','01100','00100','00100','00100','00100','01110'],
'2':['01110','10001','00001','00010','00100','01000','11111'],
'3':['11110','00001','00001','01110','00001','00001','11110'],
'4':['00010','00110','01010','10010','11111','00010','00010'],
'5':['11111','10000','10000','11110','00001','00001','11110'],
'6':['01110','10000','10000','11110','10001','10001','01110'],
'7':['11111','00001','00010','00100','01000','01000','01000'],
'8':['01110','10001','10001','01110','10001','10001','01110'],
'9':['01110','10001','10001','01111','00001','00001','01110'],
'-':['00000','00000','00000','11111','00000','00000','00000'],
'_':['00000','00000','00000','00000','00000','00000','11111'],
'.':['00000','00000','00000','00000','00000','01100','01100'],
'/':['00001','00010','00010','00100','01000','01000','10000'],
':':['00000','01100','01100','00000','01100','01100','00000'],
' ':['00000']*7,
}


def label(image,text,xy=(8,8),scale=2,color=(20,20,20)):
    draw=ImageDraw.Draw(image);x,y=xy
    for char in text.upper():
        pattern=PATTERNS.get(char,PATTERNS[' '])
        for row,line in enumerate(pattern):
            for col,pixel in enumerate(line):
                if pixel=='1':draw.rectangle((x+col*scale,y+row*scale,x+(col+1)*scale-1,y+(row+1)*scale-1),fill=color)
        x+=6*scale
    return image


def sheet(paths,captions,output,columns=5):
    width,height=320,346;rows=(len(paths)+columns-1)//columns
    canvas=Image.new('RGB',(columns*width,rows*height),(245,247,248))
    for index,(path,caption) in enumerate(zip(paths,captions)):
        with Image.open(path) as image:
            tile=ImageOps.pad(image.convert('RGB'),(width,width),method=Image.Resampling.LANCZOS,color=(245,247,248))
        canvas.paste(tile,((index%columns)*width,(index//columns)*height))
        label(canvas,caption,((index%columns)*width+8,(index//columns)*height+width+5),scale=1)
    canvas.save(output)


def gif(paths,interval_seconds,output,crop_box=None):
    # The terminal duplicate of a closed loop is represented by the next
    # cycle's first frame. Endpoint PNGs and count sheets retain it explicitly.
    count=len(paths)-1
    if count<1:return {'status':'not-applicable','reason':'static reference'}
    frames=[];durations=[];previous=0
    for index,path in enumerate(paths[:-1]):
        with Image.open(path) as image:
            image=image.convert('RGB')
            if crop_box is not None:image=image.crop(crop_box)
            frames.append(ImageOps.pad(image,(512,512),method=Image.Resampling.LANCZOS,color=(245,247,248)))
        rounded=round(Fraction(index+1)*interval_seconds*100)*10
        durations.append(rounded-previous);previous=rounded
    frames[0].save(output,save_all=True,append_images=frames[1:],duration=durations,loop=0,disposal=2,optimize=False)
    with Image.open(output) as image:
        decoded=0
        for index in range(image.n_frames):image.seek(index);decoded+=image.info.get('duration',0)
    expected=interval_seconds*count*1000
    error=abs(Fraction(decoded)-expected)
    return {'status':'pass' if error<10 else 'fail','expected_duration_ms':float(expected),'decoded_duration_ms':decoded,
            'error_ms':float(error),'upper_bound_ms':10,'terminal_duplicate':'coalesced with loop start; retained in PNG/static samples'}


def onion(paths,output):
    with Image.open(paths[0]) as first:result=first.convert('RGB')
    for index,path in enumerate(paths[1:],start=2):
        with Image.open(path) as image:result=Image.blend(result,image.convert('RGB'),1/index)
    result.save(output)
