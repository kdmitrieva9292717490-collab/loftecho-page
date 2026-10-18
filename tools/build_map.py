#!/usr/bin/env python3
"""ЛофтЭхо map: real OpenStreetMap tiles for Колокольников пер., 22 с5,
recoloured into the gold-on-olive palette of the Figma design.
Data (c) OpenStreetMap contributors, ODbL."""
import math, io, os, json, time, urllib.request
from PIL import Image, ImageFilter, ImageChops

LAT, LON = 55.7679082, 37.6293007
UA  = "LoftEcho-design-prototype/1.0 (+orshakss@gmail.com)"
OUT = os.path.join(os.path.dirname(__file__), "map")
os.makedirs(OUT, exist_ok=True)

RAMP = [(0,(38,30,12)),(150,(52,41,18)),(200,(74,59,27)),(222,(86,68,30)),
        (236,(91,72,32)),(246,(150,124,62)),(251,(205,180,120)),(255,(236,220,180))]
def _lut():
    o=[]
    for v in range(256):
        for i in range(len(RAMP)-1):
            a,ca=RAMP[i]; b,cb=RAMP[i+1]
            if a<=v<=b:
                t=(v-a)/(b-a) if b>a else 0
                o.append(tuple(round(ca[k]+(cb[k]-ca[k])*t) for k in range(3))); break
        else: o.append(RAMP[-1][1])
    return o
LUT=_lut()

def deg2num(lat, lon, z):
    n = 2.0**z
    return ((lon+180)/360*n, (1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n)

def tile(z,x,y):
    req = urllib.request.Request(f"https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                                 headers={"User-Agent": UA})
    return Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=30).read())).convert("RGB")

def style(c):
    l = c.convert("L")
    base = Image.merge("RGB", (l.point([k[0] for k in LUT]),
                               l.point([k[1] for k in LUT]),
                               l.point([k[2] for k in LUT])))
    dark = l.point(lambda v: 255 if v < 100 else 0)              # ink
    halo = l.filter(ImageFilter.MaxFilter(5)).point(lambda v: 255 if v > 246 else 0)
    txt  = ImageChops.multiply(dark, halo).filter(ImageFilter.MaxFilter(3))
    base.paste(Image.new("RGB", c.size, (238,226,192)), (0,0), txt)
    return base

def build(z, cols, rows):
    cx, cy = deg2num(LAT, LON, z)
    tx0, ty0 = int(cx)-cols//2, int(cy)-rows//2
    T = 256
    canvas = Image.new("RGB", (cols*T, rows*T), (91,72,32))
    for i in range(cols):
        for j in range(rows):
            try:
                canvas.paste(style(tile(z, tx0+i, ty0+j)), (i*T, j*T))
            except Exception as e:
                print("   miss", z, tx0+i, ty0+j, e)
            time.sleep(0.12)
    return canvas, (cx-tx0)*T/(cols*T), (cy-ty0)*T/(rows*T)

meta={}
for key, z, cols, rows in (("z15",15,8,5), ("z17",17,8,5)):
    print("building", key)
    im, fx, fy = build(z, cols, rows)
    p = os.path.join(OUT, key+".webp")
    im.save(p, "WEBP", quality=72, method=6)
    meta[key] = {"w":im.size[0], "h":im.size[1], "fx":round(fx,6), "fy":round(fy,6),
                 "kb":round(os.path.getsize(p)/1024)}
    print("  ", meta[key])
json.dump(meta, open(os.path.join(OUT,"meta.json"),"w"), indent=1)
