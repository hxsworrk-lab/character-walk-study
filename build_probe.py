"""Self-initiated source/alpha probe; not a commissioned or pixel-art asset.
Run: python preparation/demos/editable-sprite-probe-20261016/build_probe.py
Pillow is the only external dependency. No network, fonts, customer files or server.
"""
from pathlib import Path
import math, json, hashlib, xml.etree.ElementTree as ET
from collections import deque
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
SIZE, SCALE, COUNT = 128, 4, 12
PAL = {'ink':'#223747','suit':'#e9c866','suit_light':'#f7df8a','suit_dark':'#b99147',
       'white':'#f1eee1','visor':'#254f68','visor_light':'#60b5b9','accent':'#d66e43',
       'pack':'#587b79','pack_dark':'#3e5c60','sole':'#354550'}
def project(u,v,z): return (64+.82*u+.58*v, 105+.52*u-.35*v-.82*z)
def rounded(points): return [[round(x,3),round(y,3)] for x,y in points]
def ellipse_points(cx,cy,rx,ry,angle=0):
    a=math.radians(angle); ca,sa=math.cos(a),math.sin(a)
    return [(cx+rx*math.cos(t)*ca-ry*math.sin(t)*sa,
             cy+rx*math.cos(t)*sa+ry*math.sin(t)*ca) for t in [i*math.tau/64 for i in range(64)]]
def scene(frame):
    phase=math.tau*frame/COUNT
    bob=1.2*(1-math.cos(2*phase))
    groups=[]
    def group(name):
        g={'id':name,'shapes':[]};groups.append(g);return g
    def poly(g,name,pts,fill,stroke='ink',width=1.7):
        g['shapes'].append({'id':name,'points':rounded(pts),'fill':PAL.get(fill,fill),
                            'stroke':PAL.get(stroke,stroke) if stroke else None,'strokeWidth':width})
    def ell(g,name,x,y,rx,ry,fill,angle=0,stroke='ink',width=1.7):
        poly(g,name,ellipse_points(x,y,rx,ry,angle),fill,stroke,width)
    def limb(g,name,a,b,r,fill):
        x1,y1=project(*a);x2,y2=project(*b)
        ang=math.atan2(y2-y1,x2-x1); nx,ny=-math.sin(ang)*r,math.cos(ang)*r
        pts=[(x1+nx,y1+ny),(x2+nx,y2+ny),(x2-nx,y2-ny),(x1-nx,y1-ny)]
        poly(g,name+'-shaft',pts,fill)
        ell(g,name+'-joint-a',x1,y1,r,r,fill,stroke=None)
        ell(g,name+'-joint-b',x2,y2,r,r,fill,stroke=None)
    def leg(name,v,p):
        g=group(name); u=17*math.cos(p); lift=max(0,-math.sin(p))*8
        hip=(0,v,35+bob); foot=(u,v,3+lift)
        du,dz=foot[0]-hip[0],foot[2]-hip[2];dist=math.hypot(du,dz)
        h=math.sqrt(max(0,21**2-(dist/2)**2))
        knee=((hip[0]+foot[0])/2-dz/dist*h,v,(hip[2]+foot[2])/2+du/dist*h)
        limb(g,'upper-leg',hip,knee,5.1,'suit_dark' if v>0 else 'suit')
        limb(g,'lower-leg',knee,foot,4.7,'suit_dark' if v>0 else 'suit')
        kx,ky=project(*knee);ell(g,'knee-pad',kx,ky,4.1,3.6,'accent',angle=25)
        boot=[project(u+uu,v+vv,3+lift) for uu,vv in [(-6,-4),(9,-4),(12,0),(9,4),(-6,4)]]
        poly(g,'boot',boot,'accent')
        a,b=project(u-4,v-4,2+lift),project(u+10,v-4,2+lift)
        limb(g,'sole-stripe',(u-4,v-4,2+lift),(u+10,v-4,2+lift),1.15,'sole')
        g['joints3d']={'hip':hip,'knee':knee,'ankle':foot,'phaseRadians':round(p%math.tau,6)}
    def arm(name,v,p):
        g=group(name); swing=-12*math.cos(p)
        shoulder=(0,v,56+bob); elbow=(swing*.45,v*1.15,44+bob);hand=(swing,v*1.15,36+bob+max(0,math.sin(p))*2)
        limb(g,'upper-arm',shoulder,elbow,4.8,'suit_dark' if v>0 else 'suit')
        limb(g,'forearm',elbow,hand,4.1,'suit_dark' if v>0 else 'suit')
        x,y=project(*hand);ell(g,'glove',x,y,4.8,4.0,'white',angle=30)
        g['joints3d']={'shoulder':shoulder,'elbow':elbow,'hand':hand}
    leg('far-leg',8,phase+math.pi)
    arm('far-arm',14,phase+math.pi)
    g=group('survey-pack')
    cx,cy=project(-11,4,52+bob)
    poly(g,'pack-shell',[(cx-12,cy-12),(cx+6,cy-14),(cx+13,cy-4),(cx+10,cy+14),(cx-9,cy+12)],'pack')
    poly(g,'pack-top',[(cx-12,cy-12),(cx-4,cy-19),(cx+12,cy-16),(cx+6,cy-14)],'pack_dark')
    poly(g,'antenna',[(cx-6,cy-15),(cx-5,cy-29),(cx-3,cy-29),(cx-3,cy-15)],'ink',None)
    ell(g,'antenna-tip',cx-4,cy-30,2.5,2.5,'accent')
    leg('near-leg',-8,phase)
    g=group('torso')
    shl=project(-2,14,57+bob);shr=project(-2,-14,57+bob)
    br=project(6,-12,35+bob);bl=project(6,12,35+bob)
    poly(g,'suit-body',[shl,shr,br,bl],'suit')
    topback=project(-9,0,60+bob)
    poly(g,'shoulder-top',[shl,topback,shr,project(5,0,55+bob)],'suit_light')
    poly(g,'front-panel',[project(6,-9,50+bob),project(6,8,50+bob),project(7,8,39+bob),project(7,-9,39+bob)],'white')
    px,py=project(8,-2,46+bob);ell(g,'panel-button',px,py,2.3,2.0,'visor_light',stroke=None)
    poly(g,'belt',[project(5,-12,38+bob),project(5,12,38+bob),project(7,12,34+bob),project(7,-12,34+bob)],'pack_dark')
    arm('near-arm',-14,phase)
    g=group('helmet')
    cx,cy=project(0,0,79+bob)
    ell(g,'shell',cx,cy,23,21,'white',angle=8,width=2)
    ell(g,'upper-dome',cx-3,cy-7,17,9,'suit_light',angle=8,stroke=None)
    ell(g,'front-visor',cx+6,cy+6,16,10.6,'visor',angle=29,width=2)
    ell(g,'visor-reflection',cx+5,cy+2,8.8,2,'visor_light',angle=29,stroke=None)
    ell(g,'side-coupler',cx-14,cy+6,5,5.4,'pack',angle=10,width=1.6)
    ell(g,'coupler-center',cx-14,cy+6,2,2.2,'suit_light',stroke=None)
    poly(g,'dome-registration',[(cx-6,cy-17),(cx-1,cy-17),(cx+2,cy-14),(cx-4,cy-14)],'accent',None)
    return {'frame':frame,'phase':phase,'groups':groups}

def svg_document(s):
    ns='http://www.w3.org/2000/svg';ET.register_namespace('',ns)
    root=ET.Element('{'+ns+'}svg',{'viewBox':'0 0 128 128','width':'128','height':'128','role':'img'})
    ET.SubElement(root,'{'+ns+'}title').text='Survey courier — self-initiated high-three-quarter walk source, frame %02d'%s['frame']
    ET.SubElement(root,'{'+ns+'}desc').text='Original geometric prototype; not a client asset, pixel-art example or rights guarantee.'
    for g in s['groups']:
        node=ET.SubElement(root,'{'+ns+'}g',{'id':g['id'],'data-editable-layer':'true'})
        for sh in g['shapes']:
            pts=sh['points'];d='M '+' L '.join(f'{x:g},{y:g}' for x,y in pts)+' Z'
            attrs={'id':g['id']+'--'+sh['id'],'d':d,'fill':sh['fill']}
            if sh['stroke']:attrs.update({'stroke':sh['stroke'],'stroke-width':str(sh['strokeWidth']),'stroke-linejoin':'round'})
            ET.SubElement(node,'{'+ns+'}path',attrs)
    return ET.tostring(root,encoding='unicode')+'\n'
def render(s):
    im=Image.new('RGBA',(SIZE*SCALE,SIZE*SCALE),(0,0,0,0));draw=ImageDraw.Draw(im)
    for g in s['groups']:
        for sh in g['shapes']:
            pts=[(round(x*SCALE),round(y*SCALE)) for x,y in sh['points']]
            draw.polygon(pts,fill=sh['fill'])
            if sh['stroke']:draw.line(pts+[pts[0]],fill=sh['stroke'],width=round(sh['strokeWidth']*SCALE),joint='curve')
    im=im.resize((SIZE,SIZE),Image.Resampling.LANCZOS)
    # LANCZOS can leave alpha=1 pixels a few pixels from the silhouette. Strip
    # only near-zero edge residue, then clear invisible RGB. Normal edge AA stays.
    px=im.load()
    for y in range(SIZE):
        for x in range(SIZE):
            r,g,b,a=px[x,y]
            px[x,y]=(0,0,0,0) if a<=3 else (r,g,b,a)
    # This authored character is one connected object. Remove detached 1–5 px
    # LANCZOS ringing islands, verified in the first export's alpha audit.
    # Keep all partial-alpha pixels connected to the main visible silhouette.
    seen=set();components=[]
    for y in range(SIZE):
        for x in range(SIZE):
            if px[x,y][3]==0 or (x,y) in seen:continue
            q=deque([(x,y)]);seen.add((x,y));component=[]
            while q:
                u,v=q.popleft();component.append((u,v))
                for du,dv in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
                    k=(u+du,v+dv)
                    if 0<=k[0]<SIZE and 0<=k[1]<SIZE and k not in seen and px[k][3]>0:
                        seen.add(k);q.append(k)
            components.append(component)
    for component in sorted(components,key=len,reverse=True)[1:]:
        for point in component:px[point]=(0,0,0,0)
    return im
def main():
    (ROOT/'frames').mkdir(parents=True,exist_ok=True);(ROOT/'svg-frames').mkdir(exist_ok=True)
    scenes=[scene(i) for i in range(COUNT)];frames=[];metrics=[]
    for i,s in enumerate(scenes):
        svg=svg_document(s);(ROOT/'svg-frames'/f'walk-{i:02}.svg').write_text(svg,encoding='utf-8')
        im=render(s);frames.append(im);path=ROOT/'frames'/f'walk-{i:02}.png';im.save(path)
        alpha=im.getchannel('A');hist=alpha.histogram()
        metrics.append({'frame':i,'size':list(im.size),'mode':im.mode,'alphaBounds':list(alpha.getbbox()),
                        'transparentPixels':hist[0],'opaquePixels':hist[255],'antialiasedPixels':sum(hist[1:255]),
                        'alpha1to3Pixels':sum(hist[1:4]),'cornerAlpha':[im.getpixel(p)[3] for p in [(0,0),(127,0),(0,127),(127,127)]],
                        'invisibleNonzeroRGBPixels':sum(1 for r,g,b,a in im.get_flattened_data() if a==0 and (r or g or b)),
                        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    sheet=Image.new('RGBA',(SIZE*4,SIZE*3),(0,0,0,0))
    for i,im in enumerate(frames):sheet.alpha_composite(im,((i%4)*SIZE,(i//4)*SIZE))
    sheet.save(ROOT/'walk-sheet.png')
    comparison=Image.new('RGB',(512,512),'#f1e9d8')
    for j,(bg,size) in enumerate([('#f1e9d8',128),('#21313c',128),('#f1e9d8',64),('#21313c',64)]):
        x=(j%2)*256;y=(j//2)*256
        ImageDraw.Draw(comparison).rectangle([x,y,x+255,y+255],fill=bg)
        sample=frames[1].resize((size,size),Image.Resampling.LANCZOS)
        comparison.paste(sample,(x+(256-size)//2,y+(256-size)//2),sample)
    comparison.save(ROOT/'background-size-contact.png')
    (ROOT/'scene-frames.json').write_text(json.dumps({'palette':PAL,'camera':{'forward':[.82,.52],'lateral':[.58,-.35],'height':[0,-.82]},'frameCount':COUNT,'frames':scenes},indent=2)+'\n',encoding='utf-8')
    (ROOT/'metrics.json').write_text(json.dumps({'renderer':'Pillow '+Image.__version__,'frameCount':COUNT,'fps':12,'durationSeconds':1,
        'groupsPerFrame':len(scenes[0]['groups']),'pathsPerFrame':sum(len(g['shapes']) for g in scenes[0]['groups']),
        'loopClosureImageEqual':render(scene(0)).tobytes()==render(scene(12)).tobytes(),'frames':metrics,
        'svgRasterEquivalence':'NOT independently verified; SVG paths and Pillow use the same scene coordinates.'},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'frames':COUNT,'groups':len(scenes[0]['groups']),'paths':sum(len(g['shapes']) for g in scenes[0]['groups']),'loopClosureEqual':render(scene(0)).tobytes()==render(scene(12)).tobytes(),'root':str(ROOT)},indent=2))
if __name__=='__main__':main()
