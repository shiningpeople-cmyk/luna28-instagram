# -*- coding: utf-8 -*-
"""
LUNA28 リール（朝焼けの空と海・動く背景）エンジン
- 1080x1920 / 30fps / H.264 + AAC。画像は Pillow と numpy だけで描画（AI画像生成なし、メタデータなし）
- 背景：紫から桃色の空、水平線の光、きらめく海、またたく星、金箔の月
- 要素：時刻つきのレイヤー（フェード・少し上へ・左から現れる）
使い方は render_reel2.py を参照
"""
import math, os, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import luna_style as L

W, H, FPS = 1080, 1920, 30
HORIZON = 1250
CREAM = (252, 247, 255)
SHADOW = (46, 24, 92)
f = L.f
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ------------------------------------------------------------ 背景（静止部分）
def _vgrad(stops, h):
    y = np.arange(h, dtype=np.float32); col = np.zeros((h, 3), np.float32)
    for (y0, c0), (y1, c1) in zip(stops, stops[1:]):
        m = (y >= y0) & (y <= y1); k = (y - y0) / max(1, (y1 - y0)); k = k * k * (3 - 2 * k)
        for i in range(3):
            col[:, i] = np.where(m, c0[i] * (1 - k) + c1[i] * k, col[:, i])
    return col


def base_background(seed=7):
    stops = [(0, (40, 25, 94)), (40, (44, 28, 99)), (300, (94, 67, 144)), (600, (144, 103, 173)), (900, (149, 100, 156)),
             (1120, (178, 128, 157)), (1240, (216, 176, 164)), (1280, (208, 155, 185)), (1320, (189, 141, 191)),
             (1400, (138, 100, 177)), (1600, (69, 51, 135)), (1880, (38, 28, 91)), (1920, (36, 26, 88))]
    col = _vgrad(stops, H)
    arr = np.repeat(col[:, None, :], W, axis=1)
    # 薄い雲（空の中ほどに横長の帯）
    cl = np.asarray(L.fractal(1200, seed).resize((W, 520), Image.BILINEAR), np.float32) / 255.0
    yy = np.linspace(0, 1, 520, dtype=np.float32)[:, None]
    band = np.clip(np.sin(yy * math.pi), 0, 1) ** 1.4
    cloud = np.clip((cl - 0.5) * 2.4, 0, 1) * band * 0.30
    tint = np.array([236, 196, 214], np.float32)
    seg = arr[690:1210]
    arr[690:1210] = seg * (1 - cloud[..., None]) + tint[None, None, :] * cloud[..., None]
    # 水平線の光（中央がやや明るい）
    xx = np.linspace(-1, 1, W, dtype=np.float32)[None, :]
    yy = np.arange(H, dtype=np.float32)[:, None]
    glow = np.exp(-((yy - (HORIZON - 6)) / 46.0) ** 2) * (0.55 + 0.45 * np.exp(-(xx / 0.75) ** 2))
    warm = np.array([255, 226, 190], np.float32)
    arr = arr * (1 - glow[..., None] * 0.42) + warm[None, None, :] * glow[..., None] * 0.42
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGB")
    return img


def frame_layer(inset=60):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle([inset, inset, W - inset, H - inset], outline=(255, 244, 226, 150), width=2)
    return lay


# ------------------------------------------------------------ 文字・部品（透明レイヤーを返す）
def _blank():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def _shadowed(lay, blur=10, alpha=0.75, col=SHADOW, dy=4):
    """文字の背面にやわらかい影を敷く"""
    a = lay.split()[3]
    sh = Image.new("RGBA", (W, H), col + (0,))
    sh.putalpha(a.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(min(255, v * 1.6) * alpha)))
    out = _blank(); out.alpha_composite(sh, (0, dy)); out.alpha_composite(lay)
    return out


def white_text(text, cy, size, font=None, cx=W / 2, fill=CREAM, tracking=0):
    lay = _blank(); d = ImageDraw.Draw(lay); ft = f(font or L.SERIF, size)
    b = d.textbbox((0, 0), text, font=ft)
    d.text((cx - (b[2] - b[0]) / 2 - b[0], cy - (b[3] - b[1]) / 2 - b[1]), text, font=ft, fill=fill)
    return _shadowed(lay)


def gold_text(text, cy, size, cx=W / 2, font=None):
    ft = f(font or L.SERIF, size)
    d = ImageDraw.Draw(Image.new("RGB", (8, 8))); b = d.textbbox((0, 0), text, font=ft)
    x = int(cx - (b[2] - b[0]) / 2 - b[0]); y = int(cy - (b[3] - b[1]) / 2 - b[1])
    # 縦の金グラデーション（上が明るい）
    tw, th = b[2] - b[0] + 12, b[3] - b[1] + 12
    g = np.zeros((th, tw, 3), np.float32); t = np.linspace(0, 1, th, dtype=np.float32)[:, None]
    top, mid, bot = np.array([255, 240, 200], np.float32), np.array([240, 204, 128], np.float32), np.array([206, 160, 84], np.float32)
    k = np.clip(t * 2, 0, 1); k2 = np.clip(t * 2 - 1, 0, 1)
    colrow = top[None, :] * (1 - k) + mid[None, :] * k
    colrow = colrow * (1 - k2) + bot[None, :] * k2
    g = np.repeat(colrow[:, None, :], tw, axis=1)
    grad = Image.fromarray(g.astype(np.uint8)).convert("RGBA")
    mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).text((x, y), text, font=ft, fill=255)
    lay = _blank(); gfull = _blank(); gfull.paste(grad, (x + b[0] - 6, y + b[1] - 6))
    lay.paste(gfull, (0, 0), mask)
    return _shadowed(lay, blur=9, alpha=0.8, col=(54, 26, 84), dy=5)


def foot_text(text, cy, size=34):
    """海の上に置く小さな文字。背面にぼかした濃い帯を敷いて、きらめきと重なっても読めるようにする"""
    t = white_text(text, cy, size, font=L.SERIFM)
    bb = t.getbbox(); lay = _blank(); m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle([bb[0] - 40, bb[1] - 14, bb[2] + 40, bb[3] + 14], radius=34, fill=120)
    sc = Image.new("RGBA", (W, H), (44, 28, 100, 0)); sc.putalpha(m.filter(ImageFilter.GaussianBlur(24)))
    lay.alpha_composite(sc); lay.alpha_composite(t); return lay


def divider(cy, half=150, cx=W / 2):
    lay = _blank(); d = ImageDraw.Draw(lay); col = (240, 208, 140, 230)
    d.line([(cx - half, cy), (cx - 22, cy)], fill=col, width=2); d.line([(cx + 22, cy), (cx + half, cy)], fill=col, width=2)
    r = 9; d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=(248, 222, 160, 255))
    return lay


def glass_box(box, radius=26, fill=(255, 255, 255, 34), outline=(255, 255, 255, 120)):
    lay = _blank(); d = ImageDraw.Draw(lay)
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=2)
    return lay


def date_pill(text, cy, size=58):
    ft = f(L.SERIF, size); d = ImageDraw.Draw(Image.new("RGB", (8, 8))); b = d.textbbox((0, 0), text, font=ft)
    tw = b[2] - b[0]; hw = tw / 2 + 46; hh = size * 0.92
    lay = glass_box([W / 2 - hw, cy - hh, W / 2 + hw, cy + hh], radius=22)
    lay.alpha_composite(white_text(text, cy, size))
    return lay


_med_cache = {}
def medallion(no, cx, cy, d, ring=True):
    """キャラクターのメダリオン（金の細い輪とやわらかい光つき）"""
    key = (no, d)
    if key not in _med_cache:
        src = Image.open(os.path.join(ROOT, "content", "chars", f"{int(no):02d}_med.png")).convert("RGBA")
        _med_cache[key] = src.resize((d, d), Image.LANCZOS)
    im = _med_cache[key]; lay = _blank()
    gl = Image.new("RGBA", (d * 2, d * 2), (0, 0, 0, 0)); gd = ImageDraw.Draw(gl)
    gd.ellipse([d * 0.42, d * 0.42, d * 1.58, d * 1.58], fill=(255, 232, 190, 90))
    gl = gl.filter(ImageFilter.GaussianBlur(d * 0.09))
    lay.alpha_composite(gl, (int(cx - d), int(cy - d)))
    lay.alpha_composite(im, (int(cx - d / 2), int(cy - d / 2)))
    if ring:
        dd = ImageDraw.Draw(lay); r = d / 2 + 6
        dd.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(244, 214, 150, 235), width=3)
    return lay


def gold_button(text, cy, hw=330, hh=54, size=40):
    lay = _blank(); tmp = Image.new("RGB", (W, H), (0, 0, 0))
    box = (W / 2 - hw, cy - hh, W / 2 + hw, cy + hh)
    L.gold_pill(tmp, box, text, f(L.SANSB, size))
    x0, y0, x1, y1 = [int(v) for v in box]
    sh = Image.new("RGBA", (W, H), (40, 16, 70, 0)); m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle([x0, y0 + 12, x1, y1 + 12], radius=hh, fill=150)
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(16))); lay.alpha_composite(sh)
    mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).rounded_rectangle([x0, y0, x1, y1], radius=hh, fill=255)
    lay.paste(tmp, (0, 0), mask)
    return lay


def merge(*layers):
    out = _blank()
    for l in layers: out.alpha_composite(l)
    return out


# ------------------------------------------------------------ タイムライン
class El:
    def __init__(self, layer, t0, t1=None, fade=0.6, out=0.45, slide=26, wipe=0.0):
        bb = layer.getbbox() or (0, 0, 1, 1)
        pad = 4; bb = (max(0, bb[0] - pad), max(0, bb[1] - pad), min(W, bb[2] + pad), min(H, bb[3] + pad))
        self.img = layer.crop(bb); self.xy = (bb[0], bb[1])
        self.alpha = np.asarray(self.img.split()[3], np.float32)
        self.t0, self.t1, self.fade, self.out, self.slide, self.wipe = t0, t1, fade, out, slide, wipe


def ease(k):
    k = min(1.0, max(0.0, k)); return 1 - (1 - k) ** 3


def smooth(k):
    k = min(1.0, max(0.0, k)); return k * k * (3 - 2 * k)


class Reel:
    def __init__(self, duration, seed=5):
        self.T = duration; self.els = []; self.moon_keys = []   # (t, cx, cy, d, dark)
        self.seed = seed

    def add(self, layer, t0, t1=None, **kw):
        self.els.append(El(layer, t0, t1, **kw)); return self

    def moon(self, t, cx, cy, d, dark=0.0):
        self.moon_keys.append((t, cx, cy, d, dark)); return self

    # --- 月の位置（キー間を1.1秒でなめらかに移動）
    def _moon_at(self, t):
        ks = self.moon_keys; cur = ks[0][1:]
        for i in range(1, len(ks)):
            tk = ks[i][0]
            if t >= tk + 0.55: cur = ks[i][1:]
            elif t > tk - 0.55:
                k = smooth((t - (tk - 0.55)) / 1.1); a, b = ks[i - 1][1:], ks[i][1:]
                cur = tuple(a[j] * (1 - k) + b[j] * k for j in range(4)); break
        return cur

    def render(self, out_mp4, audio=None, preview_times=None):
        rnd = random.Random(self.seed)
        bg = base_background(); frame = frame_layer()
        stars = [(rnd.uniform(20, W - 20), rnd.uniform(20, 760) ** 1.0, rnd.choice([1, 1, 1, 2, 2]), rnd.uniform(0, 6.28), rnd.uniform(0.5, 1.8), rnd.randint(120, 235)) for _ in range(210)]
        sparks = [(rnd.uniform(90, W - 90), rnd.uniform(110, 1150), rnd.uniform(0, 6.28), rnd.uniform(0.7, 1.6), rnd.choice([6, 7, 9, 11])) for _ in range(16)]
        streaks = []
        for _ in range(300):
            k = rnd.random() ** 0.8; y = HORIZON + 40 + k * (H - HORIZON - 60)
            spread = 60 + 300 * k; x = W / 2 + rnd.gauss(0, spread * 0.5)
            ln = rnd.uniform(30, 70 + 170 * k); a = rnd.uniform(150, 255) * (1 - 0.35 * k)
            streaks.append((x, y, ln, a, rnd.uniform(0, 6.28), rnd.uniform(0.9, 2.4), rnd.uniform(-9, 9), rnd.choice([2, 2, 3, 4])))
        moon_src = L.moon(1200); moon_cache = {}; glow_cache = {}

        def moon_img(d, dark):
            # L.moon は光の余白つき（円の直径は画像の約0.495倍）なので、円が d になる大きさに直す
            key = (int(d), round(dark, 2))
            if key not in moon_cache:
                S = int(key[0] / 0.495); m = moon_src.resize((S, S), Image.LANCZOS)
                if dark > 0.01:
                    r = key[0] / 2 + 1; c = S / 2
                    dk = Image.new("RGBA", (S, S), (0, 0, 0, 0)); dd = ImageDraw.Draw(dk)
                    dd.ellipse([c - r, c - r, c + r, c + r], fill=(34, 24, 86, int(255 * min(0.94, dark))))
                    dd.ellipse([c - r, c - r, c + r, c + r], outline=(246, 220, 168, int(235 * dark)), width=max(2, key[0] // 110))
                    al = m.split()[3].point(lambda v, kk=1 - 0.75 * dark: int(v * kk)); m.putalpha(al)
                    m = Image.alpha_composite(m, dk)
                if len(moon_cache) > 60: moon_cache.clear()
                moon_cache[key] = m
            return moon_cache[key]

        def glow_img(d):
            key = int(d / 6) * 6 + 6
            if key not in glow_cache:
                S = int(key * 3.4); g = np.zeros((S, S), np.float32)
                yy, xx = np.mgrid[0:S, 0:S].astype(np.float32); r = np.hypot(xx - S / 2, yy - S / 2) / (key / 2)
                g = np.clip(1.0 * np.exp(-((r - 0.9) / 0.55) ** 2) * (r > 0.9) + (r <= 0.9) * 1.0, 0, 1) * 0.50 + np.exp(-(r / 2.0) ** 2) * 0.30
                im = Image.new("RGBA", (S, S), (255, 222, 150, 0)); im.putalpha(Image.fromarray(np.clip(g * 255, 0, 255).astype(np.uint8)))
                if len(glow_cache) > 40: glow_cache.clear()
                glow_cache[key] = im
            return glow_cache[key]

        def frame_at(t):
            fr = bg.copy().convert("RGBA")
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
            for x, y, r, ph, spd, a in stars:
                k = 0.55 + 0.45 * math.sin(t * spd + ph); aa = int(a * k * max(0.0, 1 - y / 900))
                if aa > 12: d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 250, 255, aa))
            for x, y, ph, spd, r in sparks:
                a = math.sin(t * spd + ph)
                if a < 0.35: continue
                a = (a - 0.35) / 0.65; rr = r * (0.6 + 0.4 * a); c = (255, 244, 214, int(215 * a))
                d.line([(x - rr, y), (x + rr, y)], fill=c, width=2); d.line([(x, y - rr), (x, y + rr)], fill=c, width=2)
            sea = Image.new("RGBA", (W, H - HORIZON), (0, 0, 0, 0)); sd = ImageDraw.Draw(sea)
            for x, y, ln, a, ph, spd, drift, wd in streaks:
                k = 0.5 + 0.5 * math.sin(t * spd + ph); k = k * k
                k = 0.25 + 0.75 * k
                xx = x + drift * math.sin(t * 0.5 + ph); yy = y - HORIZON
                sd.line([(xx - ln / 2, yy), (xx + ln / 2, yy)], fill=(255, 236, 216, int(a * k)), width=wd)
            sea = sea.filter(ImageFilter.GaussianBlur(1.1))
            fr.alpha_composite(ov); fr.alpha_composite(sea, (0, HORIZON))
            cx, cy, md, dark = self._moon_at(t)
            md = md * (1.0 + 0.012 * math.sin(t * 0.9))
            gl = glow_img(md); ga = (0.80 + 0.20 * math.sin(t * 1.3)) * (1 - 0.6 * dark)
            g2 = gl.copy(); g2.putalpha(gl.split()[3].point(lambda v, kk=ga * 0.7: int(v * kk)))
            fr.alpha_composite(g2, (int(cx - g2.width / 2), int(cy - g2.height / 2)))
            mo = moon_img(md, dark); fr.alpha_composite(mo, (int(cx - mo.width / 2), int(cy - mo.height / 2)))
            fr.alpha_composite(frame)
            for e in self.els:
                if t < e.t0: continue
                if e.t1 is not None and t > e.t1 + e.out: continue
                k = ease((t - e.t0) / max(0.01, e.fade)); a = k; dy = int(e.slide * (1 - k))
                if e.t1 is not None and t > e.t1: a *= 1 - smooth((t - e.t1) / e.out)
                if a <= 0.004: continue
                if e.wipe > 0 and t < e.t0 + e.wipe + 0.3:
                    p = (t - e.t0) / e.wipe; w = e.img.width; soft = 140.0
                    xs = np.arange(w, dtype=np.float32)[None, :]
                    m = np.clip((p * (w + soft) - xs) / soft, 0, 1)
                    al = (e.alpha * m * (a if e.t1 is not None and t > e.t1 else 1.0)).astype(np.uint8)
                    im = e.img.copy(); im.putalpha(Image.fromarray(al)); fr.alpha_composite(im, (e.xy[0], e.xy[1]))
                elif a >= 0.996:
                    fr.alpha_composite(e.img, (e.xy[0], e.xy[1] + dy))
                else:
                    im = e.img.copy(); im.putalpha(Image.fromarray((e.alpha * a).astype(np.uint8))); fr.alpha_composite(im, (e.xy[0], e.xy[1] + dy))
            # 冒頭と末尾のフェード
            fd = min(1.0, t / 0.5) * min(1.0, (self.T - t) / 0.6)
            out = fr.convert("RGB")
            if fd < 0.999: out = Image.blend(Image.new("RGB", (W, H), (30, 20, 78)), out, max(0.0, fd))
            return out

        if preview_times is not None:
            return [frame_at(t) for t in preview_times]
        n = int(round(self.T * FPS)); tmp = out_mp4 + ".part.mp4"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
        if audio: cmd += ["-i", audio]
        cmd += ["-map", "0:v"] + (["-map", "1:a"] if audio else []) + ["-map_metadata", "-1", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1", "-r", str(FPS), "-movflags", "+faststart"]
        if audio: cmd += ["-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2", "-t", f"{self.T:.3f}"]
        cmd += [tmp]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(n): p.stdin.write(frame_at(i / FPS).tobytes())
        p.stdin.close(); p.wait()
        if p.returncode != 0: raise RuntimeError("ffmpeg failed")
        os.replace(tmp, out_mp4); return out_mp4
