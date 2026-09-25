import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'examples/generated/presentation.json').read_text())
img=Image.new('RGB',(1600,900),'#040810')
d=ImageDraw.Draw(img)
font='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
small=ImageFont.truetype(font,19)
medium=ImageFont.truetype(font,26)
large=ImageFont.truetype(font,52)
for j,scene in enumerate([data['scenes'][0],data['scenes'][2]]):
    x0=30+j*790
    d.rounded_rectangle((x0,45,x0+760,850),radius=18,fill='#071522',outline='#264159',width=2)
    for gx in range(x0+24,x0+735,40):d.line((gx,72,gx,822),fill='#0e2434')
    for gy in range(72,823,40):d.line((x0+24,gy,x0+735,gy),fill='#0e2434')
    accent=scene['accent']
    d.text((x0+40,88),scene['eyebrow'],font=small,fill=accent)
    cols,rows=scene['columns'],scene['rows']
    cw=min(6.4,690/cols,470/rows)
    f=ImageFont.truetype(font,max(6,int(cw*1.55)))
    aw,ah=cols*cw,rows*cw*1.23
    ox=x0+(760-aw)/2;oy=165+(520-ah)/2
    for x,y,g,r,green,b,a in scene['cells']:
        if a<30:continue
        rgb=tuple(int(v*a/255+base*(255-a)/255) for v,base in zip((r,green,b),(7,21,34)))
        d.text((int(ox+x*cw),int(oy+y*cw*1.23)),g,font=f,fill=rgb)
    title=scene['title'].split('\n')
    for i,line in enumerate(title):d.text((x0+40,715+i*54),line,font=large,fill='#f3f7fc')
    d.rectangle((x0+38,830,x0+95,834),fill=accent)
img.save(root/'examples/generated/poster.png',optimize=True)
