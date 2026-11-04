from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import random, math

W, H = 2500, 1686
SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
SERIFM = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Medium.ttc"
SANSB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
f = lambda path, s: ImageFont.truetype(path, s, index=0)

VIOLET = (52, 26, 92); PLUM = (104, 58, 140); DUSK = (176, 120, 184); PINKSKY = (236, 190, 220)
LILAC_BG = (238, 230, 246); CARD_TOP = (255, 255, 255); CARD_BOT = (247, 241, 252)
INK = (74, 46, 112); SUB = (134, 106, 168)
GOLD = (212, 172, 92); GOLD_D = (168, 128, 56); GOLD_L = (248, 226, 168); CHAMP = (255, 243, 210)
PINK = (236, 150, 186); LAV = (196, 172, 232)

def lerp(a, b, t): return tuple(int(a[i]*(1-t)+b[i]*t) for i in range(3))

# ---------- gold helpers ----------
def gold_grad(w, h, horizontal=True):
    g = Image.new("RGB", (w, h)); gd = ImageDraw.Draw(g)
    n = w if horizontal else h
    for i in range(n):
        t = i/max(1, n-1); k = 0.5+0.5*math.sin(t*math.pi*2-math.pi/2)
        c = lerp(lerp(GOLD_D, GOLD, min(1, k*1.6)), GOLD_L, max(0, k-0.4)*1.6)
        if horizontal: gd.line([(i, 0), (i, h)], fill=c)
        else: gd.line([(0, i), (w, i)], fill=c)
    return g

def gold_line(img, x0, y0, x1, y1, width=3):
    """draw a gradient gold line (axis-aligned) """
    if y0 == y1:
        seg = gold_grad(int(abs(x1-x0)), width); img.paste(seg, (int(min(x0, x1)), int(y0-width//2)))
    else:
        seg = gold_grad(width, int(abs(y1-y0)), horizontal=False); img.paste(seg, (int(x0-width//2), int(min(y0, y1))))

def gold_rounded_frame(img, box, radius, width=4):
    x0, y0, x1, y1 = [int(v) for v in box]
    g = gold_grad(x1-x0, y1-y0)
    mask = Image.new("L", (x1-x0, y1-y0), 0); md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, x1-x0-1, y1-y0-1], radius=radius, outline=255, width=width)
    img.paste(g, (x0, y0), mask)

def diamond(d, cx, cy, r, fill=GOLD):
    d.polygon([(cx, cy-r), (cx+r*.6, cy), (cx, cy+r), (cx-r*.6, cy)], fill=fill)

def sparkle4(d, cx, cy, r, col=GOLD_L):
    d.polygon([(cx, cy-r), (cx+r*.18, cy-r*.18), (cx+r, cy), (cx+r*.18, cy+r*.18), (cx, cy+r), (cx-r*.18, cy+r*.18), (cx-r, cy), (cx-r*.18, cy-r*.18)], fill=col)

def corner_flourish(d, x, y, sx, sy, size=90, col=GOLD):
    """art-deco corner: two arcs + dots. sx,sy = direction (+1/-1)"""
    w = 4
    d.line([(x, y+sy*size), (x, y), (x+sx*size, y)], fill=col, width=w)
    d.line([(x+sx*14, y+sy*(size*.7)), (x+sx*14, y+sy*14), (x+sx*(size*.7), y+sy*14)], fill=col, width=2)
    d.arc([x+sx*10-30, y+sy*10-30, x+sx*10+30, y+sy*10+30], 0, 360, fill=col, width=2)
    d.ellipse([x+sx*10-6, y+sy*10-6, x+sx*10+6, y+sy*10+6], fill=col)
    d.ellipse([x-4, y+sy*size-4, x+4, y+sy*size+4], fill=col)
    d.ellipse([x+sx*size-4, y-4, x+sx*size+4, y+4], fill=col)

def ornament_divider(d, cx, y, half=260, col=GOLD):
    d.line([(cx-half, y), (cx-40, y)], fill=col, width=2)
    d.line([(cx+40, y), (cx+half, y)], fill=col, width=2)
    diamond(d, cx, y, 14, col); diamond(d, cx-24, y, 7, col); diamond(d, cx+24, y, 7, col)
    d.ellipse([cx-half-5, y-5, cx-half+5, y+5], fill=col); d.ellipse([cx+half-5, y-5, cx+half+5, y+5], fill=col)

# ---------- smooth moon ----------
def value_noise(S, cells, seed):
    rnd = random.Random(seed)
    g = Image.new("L", (cells, cells))
    g.putdata([rnd.randint(0, 255) for _ in range(cells*cells)])
    return g.resize((S, S), Image.BICUBIC)

def fractal(S, seed):
    import numpy as np
    acc = np.zeros((S, S), dtype=np.float32); amp, tot = 1.0, 0.0
    for i, cells in enumerate((4, 8, 16, 32, 64)):
        n = value_noise(S, cells, seed+i).filter(ImageFilter.GaussianBlur(S/cells*0.35))
        acc += np.asarray(n, dtype=np.float32)*amp; tot += amp; amp *= 0.5
    return Image.fromarray((acc/tot).astype(np.uint8))

def moon(size):
    import numpy as np
    S = size*2; cx = cy = S/2; r = S*0.24
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    dx, dy = (xx-cx)/r, (yy-cy)/r; d2 = dx*dx+dy*dy
    inside = d2 <= 1.0
    z = np.sqrt(np.clip(1-d2, 0, 1))
    # --- noise octaves ---
    def noise(cells, seed):
        return np.asarray(value_noise(S, cells, seed), dtype=np.float32)/255.0
    low  = 0.45*noise(6, 41)+0.30*noise(12, 42)+0.25*noise(24, 43)       # maria patches
    low  = (low-low[inside].mean())/ (low[inside].std()+1e-6)               # normalize over disk
    mid  = 0.5*noise(48, 44)+0.3*noise(96, 45)+0.2*noise(192, 46)           # mottling / flakes
    mid  = (mid-mid.mean())/(mid.std()+1e-6)
    rng = np.random.default_rng(7)
    grain = rng.random((S, S)).astype(np.float32)                           # fine speckle
    grain = (grain*0.6+np.asarray(Image.fromarray((grain*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), dtype=np.float32)/255*0.4)
    # patches mask: where low noise is high -> orange gold leaf, softened edges, broken up by mid
    patch = np.clip(low*0.9+0.35+mid*0.35, 0, 1)**1.6          # ~45% coverage, broken by flakes
    flakes = np.clip(mid*0.6+0.5, 0, 1)
    patch = np.clip(patch*(0.45+0.55*flakes)*(0.7+0.3*grain), 0, 1)
    # speckles everywhere (gold dust), stronger near patches
    speck = np.clip((grain-0.80)*5.0, 0, 1)*(0.35+0.65*patch)
    # limb darkening + slight light from upper-left
    light = np.clip(0.70+0.30*z-0.06*dx-0.05*dy, 0, 1)
    pale   = np.array([255, 246, 190], np.float32)   # bright cream-yellow
    yellow = np.array([252, 222, 110], np.float32)
    orange = np.array([236, 152, 30], np.float32)
    deep   = np.array([196, 102, 14], np.float32)
    base = pale[None, None, :]*light[..., None]+yellow[None, None, :]*(1-light[..., None])
    col = base*(1-patch[..., None])+(orange[None, None, :]*(1-speck[..., None])+deep[None, None, :]*speck[..., None])*patch[..., None]
    # golden dust speckles on pale area too
    col = col*(1-speck[..., None]*0.6)+orange[None, None, :]*speck[..., None]*0.6
    # glitter: tiny bright gold-dust specks
    glit = np.clip((rng.random((S, S)).astype(np.float32)-0.986)*70, 0, 1)
    col = col*(1-glit[..., None])+np.array([255, 252, 225], np.float32)[None, None, :]*glit[..., None]
    # edge: slightly deeper ring near limb
    rim = np.clip((d2-0.80)/0.20, 0, 1)
    col = col*(1-rim[..., None]*0.25)+yellow[None, None, :]*rim[..., None]*0.25
    img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8))
    disk = Image.new("L", (S, S), 0); ImageDraw.Draw(disk).ellipse([cx-r, cy-r, cx+r, cy+r], fill=255)
    disk = disk.filter(ImageFilter.GaussianBlur(1.6))
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0)); out.paste(img, (0, 0), disk)
    # warm bloom
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    for k, a in ((2.0, 40), (1.6, 70), (1.3, 120), (1.12, 190)):
        gd.ellipse([cx-r*k, cy-r*k, cx+r*k, cy+r*k], fill=(255, 214, 120, a))
    glow = glow.filter(ImageFilter.GaussianBlur(S*0.045))
    glow2 = Image.new("RGBA", (S, S), (0, 0, 0, 0)); ImageDraw.Draw(glow2).ellipse([cx-r*1.03, cy-r*1.03, cx+r*1.03, cy+r*1.03], fill=(255, 240, 180, 235))
    glow2 = glow2.filter(ImageFilter.GaussianBlur(S*0.012))
    out = Image.alpha_composite(Image.alpha_composite(glow, glow2), out)
    return out.resize((size, size), Image.LANCZOS)

def sky(w, h):
    img = Image.new("RGB", (w, h), VIOLET); d = ImageDraw.Draw(img)
    stops = [(0.0, VIOLET), (0.28, PLUM), (0.50, DUSK), (0.70, (226, 200, 232)), (1.0, LILAC_BG)]
    for y in range(h):
        t = y/h
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            if t0 <= t <= t1: c = lerp(c0, c1, (t-t0)/(t1-t0)); break
        d.line([(0, y), (w, y)], fill=c)
    haze = Image.new("RGBA", (w, h), (0, 0, 0, 0)); hd = ImageDraw.Draw(haze)
    hd.ellipse([-w*.2, h*.36, w*1.2, h*.95], fill=PINKSKY+(120,))
    haze = haze.filter(ImageFilter.GaussianBlur(160))
    img = Image.alpha_composite(img.convert("RGBA"), haze).convert("RGB")
    d = ImageDraw.Draw(img); rnd = random.Random(11)
    for _ in range(380):
        x, y = rnd.randint(0, w), rnd.randint(0, int(h*.48)); r = rnd.choice([1, 1, 1, 2, 2, 3]); a = rnd.randint(150, 255)
        d.ellipse([x-r, y-r, x+r, y+r], fill=(a, a-8, min(255, a+5)))
    for _ in range(40):
        x, y = rnd.randint(0, w), rnd.randint(0, int(h*.46)); r = rnd.randint(2, 4)
        d.ellipse([x-r, y-r, x+r, y+r], fill=GOLD_L)
    return img

def ctext(d, text, cx, y, font, fill, shadow=None):
    b = d.textbbox((0, 0), text, font=font); x = cx-(b[2]-b[0])/2
    if shadow: d.text((x+3, y+4), text, font=font, fill=shadow)
    d.text((x, y), text, font=font, fill=fill)

def gold_text(img, xy, text, font, shadow=(50, 20, 70)):
    """gradient gold text via mask"""
    d = ImageDraw.Draw(img)
    b = d.textbbox(xy, text, font=font)
    d.text((xy[0]+4, xy[1]+6), text, font=font, fill=shadow)
    w, h = b[2]-b[0]+10, b[3]-b[1]+14
    g = Image.new("RGB", (w, h)); gd = ImageDraw.Draw(g)
    for i in range(h):
        t = i/max(1, h-1); k = 0.5+0.5*math.sin(t*math.pi*2-math.pi/2)
        gd.line([(0, i), (w, i)], fill=lerp(lerp(GOLD, GOLD_L, k), CHAMP, max(0, k-.5)*1.2))
    mask = Image.new("L", img.size, 0); ImageDraw.Draw(mask).text(xy, text, font=font, fill=255)
    gfull = Image.new("RGB", img.size); gfull.paste(g, (b[0]-5, b[1]-7))
    img.paste(gfull, (0, 0), mask)

def gold_pill(img, box, text, font):
    x0, y0, x1, y1 = [int(v) for v in box]; radius = (y1-y0)//2
    pill = gold_grad(x1-x0, y1-y0)
    pd = ImageDraw.Draw(pill)
    # top highlight
    pd.rounded_rectangle([18, 8, x1-x0-18, (y1-y0)*0.42], radius=radius, fill=None, outline=None)
    hl = Image.new("RGBA", pill.size, (0, 0, 0, 0)); hd = ImageDraw.Draw(hl)
    hd.rounded_rectangle([22, 10, x1-x0-22, (y1-y0)*0.45], radius=radius, fill=(255, 255, 255, 70))
    hl = hl.filter(ImageFilter.GaussianBlur(6)); pill = Image.alpha_composite(pill.convert("RGBA"), hl).convert("RGB")
    mask = Image.new("L", pill.size, 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, pill.width-1, pill.height-1], radius=radius, fill=255)
    sh = Image.new("RGBA", (pill.width+80, pill.height+80), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([40, 52, pill.width+40, pill.height+52], radius=radius, fill=(40, 10, 60, 140))
    sh = sh.filter(ImageFilter.GaussianBlur(22)); img.paste(sh, (x0-40, y0-40), sh)
    img.paste(pill, (x0, y0), mask)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0+8, y0+8, x1-8, y1-8], radius=radius-8, outline=CHAMP, width=2)
    ctext(d, text, (x0+x1)/2, y0+(y1-y0)/2-font.size*.62, font, (72, 40, 16))

# ---------- icons (gold) ----------
def icon_pair(d, cx, cy, r):
    d.ellipse([cx-r-r*.45, cy-r, cx+r-r*.45, cy+r], outline=GOLD, width=12)
    d.ellipse([cx-r+r*.45, cy-r, cx+r+r*.45, cy+r], outline=GOLD_L, width=12)
    hr = r*.3; hx, hy = cx, cy+hr*.15
    d.ellipse([hx-hr, hy-hr*.9, hx, hy+hr*.1], fill=PINK); d.ellipse([hx, hy-hr*.9, hx+hr, hy+hr*.1], fill=PINK)
    d.polygon([(hx-hr, hy-hr*.3), (hx+hr, hy-hr*.3), (hx, hy+hr)], fill=PINK)
    sparkle4(d, cx+r*1.25, cy-r*.9, 18, GOLD)
def icon_sun(d, cx, cy, r):
    d.ellipse([cx-r*.52, cy-r*.52, cx+r*.52, cy+r*.52], fill=GOLD)
    d.ellipse([cx-r*.36, cy-r*.36, cx+r*.36, cy+r*.36], fill=GOLD_L)
    for k in range(16):
        a = k*math.pi/8; L = r if k % 2 == 0 else r*.85
        d.line([(cx+math.cos(a)*r*.68, cy+math.sin(a)*r*.68), (cx+math.cos(a)*L, cy+math.sin(a)*L)], fill=GOLD if k % 2 == 0 else PINK, width=8)
def icon_crown(d, cx, cy, r):
    pts = [(cx-r, cy+r*.55), (cx-r, cy-r*.3), (cx-r*.5, cy+r*.1), (cx, cy-r*.75), (cx+r*.5, cy+r*.1), (cx+r, cy-r*.3), (cx+r, cy+r*.55)]
    d.polygon(pts, fill=GOLD); d.rectangle([cx-r, cy+r*.55, cx+r, cy+r*.85], fill=GOLD_D)
    d.rectangle([cx-r, cy+r*.62, cx+r, cy+r*.7], fill=GOLD_L)
    for px, py in ((cx-r, cy-r*.3), (cx, cy-r*.75), (cx+r, cy-r*.3)): d.ellipse([px-15, py-15, px+15, py+15], fill=PINK)
    diamond(d, cx, cy+r*.3, 16, CHAMP)

def card(img, box, title, sub, icon, badge=None, hl=False):
    x0, y0, x1, y1 = [int(v) for v in box]
    sh = Image.new("RGBA", (x1-x0+100, y1-y0+100), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([50, 66, sh.width-50, sh.height-34], radius=46, fill=(110, 70, 150, 80))
    sh = sh.filter(ImageFilter.GaussianBlur(26)); img.paste(sh, (x0-50, y0-50), sh)
    body = Image.new("RGB", (x1-x0, y1-y0)); bd = ImageDraw.Draw(body)
    ct, cb = ((255, 250, 236), (248, 232, 196)) if hl else (CARD_TOP, CARD_BOT)
    for y in range(body.height): bd.line([(0, y), (body.width, y)], fill=lerp(ct, cb, y/body.height))
    mask = Image.new("L", body.size, 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, body.width-1, body.height-1], radius=46, fill=255)
    img.paste(body, (x0, y0), mask)
    gold_rounded_frame(img, (x0, y0, x1, y1), 46, width=9 if hl else 4)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0+14, y0+14, x1-14, y1-14], radius=34, outline=lerp(GOLD_L, (255, 255, 255), .4), width=2)
    # corner ticks
    for sx, sy, px, py in ((1, 1, x0+30, y0+30), (-1, 1, x1-30, y0+30), (1, -1, x0+30, y1-30), (-1, -1, x1-30, y1-30)):
        d.line([(px, py+sy*34), (px, py), (px+sx*34, py)], fill=GOLD, width=3); d.ellipse([px-4, py-4, px+4, py+4], fill=GOLD)
    cx = (x0+x1)/2; cy = (y0+y1)/2
    icon(d, cx, cy-150, 100)
    ctext(d, title, cx, cy+35, f(SERIF, 70), INK)
    ornament_divider(d, cx, cy+135, half=150)
    ctext(d, sub, cx, cy+160, f(SERIFM, 36), SUB)
    if badge:
        bf = f(SANSB, 36 if hl else 32); b = d.textbbox((0, 0), badge, font=bf); bw = b[2]-b[0]+60
        bx0 = x1-bw-36; by0 = y0+34
        bp = gold_grad(bw, 64); bm = Image.new("L", bp.size, 0); ImageDraw.Draw(bm).rounded_rectangle([0, 0, bw-1, 63], radius=32, fill=255)
        img.paste(bp, (bx0, by0), bm); d = ImageDraw.Draw(img)
        d.text((bx0+30, by0+8), badge, font=bf, fill=(72, 40, 16))

def susuki(d, x, y, h, lean, col, seed):
    rnd = random.Random(seed)
    # gently curved stem
    pts = []
    for i in range(13):
        t = i/12
        pts.append((x+lean*h*t*t*1.6+lean*h*t*0.2, y-h*t))
    d.line(pts, fill=col, width=3)
    tip = pts[-1]
    # soft plume: dense fine strokes drooping from the upper 30%
    for i in range(170):
        t = rnd.uniform(0.0, 0.34)**0.8
        bx, by = tip[0]-(tip[0]-pts[-5][0])*t*2.4, tip[1]+h*t
        base_ang = math.atan2(pts[-1][1]-pts[-5][1], pts[-1][0]-pts[-5][0])
        ang = base_ang + rnd.uniform(-1.25, 0.55) + 0.5
        L = rnd.uniform(h*0.03, h*0.11)*(1.0-t*0.8+0.3)
        ex, ey = bx+math.cos(ang)*L, by+math.sin(ang)*L
        d.line([(bx, by), (ex, ey)], fill=col, width=rnd.choice([1, 1, 2, 2]))
        if rnd.random() < 0.5: d.ellipse([ex-2, ey-2, ex+2, ey+2], fill=col)

def _ellipse_pts(cx, cy, rx, ry, rot=0.0, n=60):
    out = []
    for i in range(n):
        a = i*math.tau/n; px, py = math.cos(a)*rx, math.sin(a)*ry
        out.append((cx+px*math.cos(rot)-py*math.sin(rot), cy+px*math.sin(rot)+py*math.cos(rot)))
    return out

def _taper(p0, p1, w0, w1, bend=0.0, n=24):
    """tapered strip along a quadratic curve from p0 to p1"""
    mx, my = (p0[0]+p1[0])/2+bend, (p0[1]+p1[1])/2
    left, right = [], []
    for i in range(n+1):
        t = i/n
        x = (1-t)**2*p0[0]+2*(1-t)*t*mx+t*t*p1[0]; y = (1-t)**2*p0[1]+2*(1-t)*t*my+t*t*p1[1]
        dx = 2*(1-t)*(mx-p0[0])+2*t*(p1[0]-mx); dy = 2*(1-t)*(my-p0[1])+2*t*(p1[1]-my)
        L = math.hypot(dx, dy) or 1; nx, ny = -dy/L, dx/L; w = w0*(1-t)+w1*t
        left.append((x+nx*w, y+ny*w)); right.append((x-nx*w, y-ny*w))
    return left+right[::-1]

def rabbit(d, x, y, s, col):
    """sitting rabbit, side profile, looking up toward the moon. (x,y)=ground, s=scale"""
    d.polygon(_ellipse_pts(x, y-0.5*s, 0.85*s, 0.48*s, rot=-0.25), fill=col)        # body
    d.polygon(_ellipse_pts(x-0.4*s, y-0.48*s, 0.48*s, 0.46*s), fill=col)             # haunch
    d.polygon(_ellipse_pts(x+0.55*s, y-0.9*s, 0.36*s, 0.3*s, rot=-0.6), fill=col)    # chest/neck
    d.polygon(_ellipse_pts(x+0.8*s, y-1.12*s, 0.33*s, 0.29*s, rot=-0.4), fill=col)   # head
    d.polygon(_ellipse_pts(x+1.07*s, y-1.2*s, 0.16*s, 0.11*s, rot=-0.5), fill=col)   # muzzle
    d.polygon(_taper((x+0.68*s, y-1.36*s), (x+0.38*s, y-2.5*s), 0.1*s, 0.03*s, bend=-0.16*s), fill=col)  # ear back
    d.polygon(_taper((x+0.86*s, y-1.38*s), (x+0.82*s, y-2.6*s), 0.1*s, 0.03*s, bend=0.1*s), fill=col)    # ear front
    d.polygon(_ellipse_pts(x-1.02*s, y-0.42*s, 0.2*s, 0.18*s), fill=col)             # tail
    d.polygon(_ellipse_pts(x+0.5*s, y-0.08*s, 0.34*s, 0.1*s), fill=col)              # front paws

def rays(img, cx, cy, r, n=20):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    for k in range(n):
        a = k*math.tau/n+math.pi/n; L = r*(2.3 if k % 2 == 0 else 1.75); wdt = 0.03 if k % 2 == 0 else 0.012
        p1 = (cx+math.cos(a)*r*1.12, cy+math.sin(a)*r*1.12); p2 = (cx+math.cos(a)*L, cy+math.sin(a)*L)
        ld.line([p1, p2], fill=(250, 222, 156, 150), width=max(3, int(r*wdt)))
    ld.ellipse([cx-r*1.3, cy-r*1.3, cx+r*1.3, cy+r*1.3], outline=(250, 222, 156, 150), width=3)
    layer = layer.filter(ImageFilter.GaussianBlur(7))
    img.alpha_composite(layer)

