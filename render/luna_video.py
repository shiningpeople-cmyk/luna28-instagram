# -*- coding: utf-8 -*-
"""
LUNA28 動画エンジン（Instagram ストーリーズ／リール用）
- 画像は Pillow と numpy だけで描画（AI画像生成なし、C2PA等のメタデータなし）
- 音源も numpy で合成（著作権フリー・自前）
- 出力: 1080x1920 / 24fps / H.264 + AAC / faststart / メタデータなし
"""
import math, os, random, subprocess, struct, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import luna_style as L

W, H, FPS = 1080, 1920, 24
GOLD, GOLD_L, GOLD_D, CHAMP = L.GOLD, L.GOLD_L, L.GOLD_D, L.CHAMP
VIOLET, PLUM, DUSK = L.VIOLET, L.PLUM, L.DUSK
CREAM = (250, 244, 255)
f = L.f

# ---------------------------------------------------------------- static layers
def purple_bg(w, h, light_bottom=0.35, seed=11):
    """紫のグラデーション＋星（numpyで高速描画）"""
    t = np.linspace(0, 1, h, dtype=np.float32)
    stops = [(0.0, VIOLET), (0.45, PLUM), (0.8, DUSK), (1.0, L.lerp(DUSK, (236, 214, 240), light_bottom))]
    col = np.zeros((h, 3), np.float32)
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        m = (t >= t0) & (t <= t1); k = (t - t0) / (t1 - t0)
        for i in range(3):
            col[:, i] = np.where(m, c0[i] * (1 - k) + c1[i] * k, col[:, i])
    arr = np.repeat(col[:, None, :], w, axis=1)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    rnd = random.Random(seed)
    for _ in range(int(w * h / 6000)):
        x, y = rnd.randint(0, w), rnd.randint(0, int(h * .8)); r = rnd.choice([1, 1, 2, 2, 3]); a = rnd.randint(150, 255)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(a, a - 8, min(255, a + 5)))
    for _ in range(int(w * h / 40000)):
        x, y = rnd.randint(0, w), rnd.randint(0, int(h * .8)); r = rnd.randint(2, 4)
        d.ellipse([x - r, y - r, x + r, y + r], fill=GOLD_L)
    return im

def frame_layer(inset=60, radius=30):
    """金の二重フレーム＋四隅の飾り（透明レイヤー）"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rgb = Image.new("RGB", (W, H), (0, 0, 0))
    L.gold_rounded_frame(rgb, (inset, inset, W - inset, H - inset), radius, width=3)
    d = ImageDraw.Draw(rgb)
    d.rounded_rectangle([inset + 14, inset + 14, W - inset - 14, H - inset - 14], radius=radius - 8, outline=L.lerp(GOLD, VIOLET, .5), width=1)
    for sx, sy, px, py in ((1, 1, inset + 36, inset + 36), (-1, 1, W - inset - 36, inset + 36), (1, -1, inset + 36, H - inset - 36), (-1, -1, W - inset - 36, H - inset - 36)):
        L.corner_flourish(d, px, py, sx, sy, size=90)
    mask = rgb.convert("L").point(lambda v: 255 if v > 8 else 0)
    lay.paste(rgb, (0, 0), mask)
    return lay

def text_layer(draw_fn):
    """draw_fn(img_rgba) で描いた内容を透明レイヤーとして返す"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(lay)
    return lay

def ctext(d, text, cx, y, font, fill, shadow=None):
    b = d.textbbox((0, 0), text, font=font); x = cx - (b[2] - b[0]) / 2
    if shadow: d.text((x + 3, y + 4), text, font=font, fill=shadow)
    d.text((x, y), text, font=font, fill=fill)

def gold_text_c(lay, text, cx, y, font):
    """金グラデ文字（透明レイヤー上）"""
    d = ImageDraw.Draw(lay); b = d.textbbox((0, 0), text, font=font)
    xy = (int(cx - (b[2] - b[0]) / 2), int(y))
    tmp = Image.new("RGB", (W, H), (0, 0, 0)); L.gold_text(tmp, xy, text, font)
    mask = Image.new("L", (W, H), 0); md = ImageDraw.Draw(mask)
    md.text((xy[0] + 4, xy[1] + 6), text, font=font, fill=255); md.text(xy, text, font=font, fill=255)
    lay.paste(tmp, (0, 0), mask)

def pill_layer(box, text, font):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    tmp = Image.new("RGB", (W, H), (0, 0, 0)); L.gold_pill(tmp, box, text, font)
    x0, y0, x1, y1 = [int(v) for v in box]; radius = (y1 - y0) // 2
    mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=255)
    lay.paste(tmp, (0, 0), mask)
    return lay

def wrap(text, n):
    """n文字で折り返し（均等割り＋禁則：行頭に 、。」）を置かない）"""
    if len(text) <= n: return [text]
    k = math.ceil(len(text) / n); m = math.ceil(len(text) / k)
    lines = [text[i:i + m] for i in range(0, len(text), m)]
    out = []
    for ln in lines:
        while ln and ln[0] in "、。」）】" and out:
            out[-1] += ln[0]; ln = ln[1:]
        if ln: out.append(ln)
    return out

# ---------------------------------------------------------------- scene
class Scene:
    """1シーン = 背景＋月＋テキスト要素（出現タイミング付き）"""
    def __init__(self, duration, moon_size, moon_cx, moon_cy, bg=None):
        self.duration = duration
        self.moon_size, self.moon_cx, self.moon_cy = moon_size, moon_cx, moon_cy
        self.bg = bg
        self.elements = []   # (layer RGBA, t_in, fade_dur, slide_px)
        self._moon_cache = {}
    def add(self, layer, t_in=0.0, fade=0.6, slide=28):
        self.elements.append((layer, t_in, fade, slide))

# ---------------------------------------------------------------- renderer
class Renderer:
    def __init__(self, seed=3, frame=None, bg=None):
        self.bg_big = bg            # 背景（W*1.06 × H*1.06 の画像）。None なら紫
        self.frame = frame if frame is not None else frame_layer()
        rnd = random.Random(seed)
        self.sparks = [(rnd.uniform(90, W - 90), rnd.uniform(90, H * 0.78), rnd.uniform(0, 6.28), rnd.uniform(0.6, 1.6), rnd.choice([5, 6, 8, 10])) for _ in range(46)]
        self.moon_src = {}
        self.glow = {}

    def _bg(self, scene):
        if scene.bg is None:
            if self.bg_big is None:
                self.bg_big = purple_bg(int(W * 1.06), int(H * 1.06))
            return self.bg_big
        return scene.bg

    def _moon(self, size):
        key = int(size)
        if key not in self.moon_src:
            base = self.moon_src.get("base")
            if base is None:
                base = L.moon(1200); self.moon_src["base"] = base
            self.moon_src[key] = base.resize((key, key), Image.LANCZOS)
        return self.moon_src[key]

    def _glow(self, size):
        key = int(size)
        if key not in self.glow:
            S = key * 2; g = Image.new("RGBA", (S, S), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
            r = key * 0.24
            for k, a in ((3.0, 22), (2.3, 40), (1.7, 64)):
                gd.ellipse([S / 2 - r * k, S / 2 - r * k, S / 2 + r * k, S / 2 + r * k], fill=(255, 214, 130, a))
            self.glow[key] = g.filter(ImageFilter.GaussianBlur(S * 0.06))
        return self.glow[key]

    def frame_at(self, scene, t):
        T = scene.duration; u = t / T
        # 背景：ゆっくりパン
        big = self._bg(scene)
        ox = int((big.width - W) * (0.5 + 0.5 * math.sin(u * math.pi * 0.9 - 1.2)))
        oy = int((big.height - H) * (0.2 + 0.6 * u))
        fr = big.crop((ox, oy, ox + W, oy + H)).convert("RGBA")
        # 月：呼吸（1.00→1.025）＋光のゆらぎ
        ms = scene.moon_size * (1.0 + 0.025 * (0.5 - 0.5 * math.cos(u * math.pi * 2)))
        mo = self._moon(ms); gl = self._glow(scene.moon_size)
        ga = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(t * 1.4))
        gla = gl.copy(); gla.putalpha(gl.split()[3].point(lambda a, k=ga: int(a * k)))
        fr.alpha_composite(gla, (int(scene.moon_cx - gla.width / 2), int(scene.moon_cy - gla.height / 2)))
        fr.alpha_composite(mo, (int(scene.moon_cx - mo.width / 2), int(scene.moon_cy - mo.height / 2)))
        # きらめき
        sp = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sp)
        for x, y, ph, spd, r in self.sparks:
            a = max(0.0, math.sin(t * spd * 1.3 + ph))
            if a < 0.15: continue
            rr = r * (0.6 + 0.4 * a); col = (255, 240, 190, int(230 * a))
            sd.polygon([(x, y - rr), (x + rr * .28, y - rr * .28), (x + rr, y), (x + rr * .28, y + rr * .28), (x, y + rr), (x - rr * .28, y + rr * .28), (x - rr, y), (x - rr * .28, y - rr * .28)], fill=col)
        fr.alpha_composite(sp)
        # フレーム
        fr.alpha_composite(self.frame)
        # テキスト要素（フェードイン＋少し上へ）
        for lay, t_in, fade, slide in scene.elements:
            if t < t_in: continue
            k = min(1.0, (t - t_in) / max(0.01, fade)); e = 1 - (1 - k) ** 3
            dy = int(slide * (1 - e))
            if e >= 0.999:
                fr.alpha_composite(lay, (0, dy))
            else:
                tmp = lay.copy(); tmp.putalpha(lay.split()[3].point(lambda a, kk=e: int(a * kk)))
                fr.alpha_composite(tmp, (0, dy))
        return fr.convert("RGB")

    def render(self, scenes, out_mp4, audio_wav=None, xfade=0.6, end_fade=0.5):
        total = sum(s.duration for s in scenes) - xfade * (len(scenes) - 1)
        n = int(round(total * FPS))
        starts = []; acc = 0.0
        for s in scenes:
            starts.append(acc); acc += s.duration - xfade
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
        if audio_wav: cmd += ["-i", audio_wav]
        cmd += ["-map_metadata", "-1", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1", "-r", str(FPS), "-movflags", "+faststart"]
        if audio_wav: cmd += ["-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-shortest"]
        cmd += [out_mp4]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(n):
            t = i / FPS
            # どのシーンか
            idx = 0
            for j, st in enumerate(starts):
                if t >= st: idx = j
            s = scenes[idx]; ts = t - starts[idx]
            img = self.frame_at(s, min(ts, s.duration - 0.001))
            # クロスフェード
            if idx + 1 < len(scenes) and ts > s.duration - xfade:
                k = (ts - (s.duration - xfade)) / xfade
                nxt = self.frame_at(scenes[idx + 1], k * xfade)
                img = Image.blend(img, nxt, k)
            # 終了フェード
            if t > total - end_fade:
                k = (t - (total - end_fade)) / end_fade
                img = Image.blend(img, Image.new("RGB", (W, H), VIOLET), k * 0.6)
            p.stdin.write(img.tobytes())
        p.stdin.close(); p.wait()
        if p.returncode != 0: raise RuntimeError("ffmpeg failed")
        return out_mp4, total

# ---------------------------------------------------------------- audio (自前合成)
NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
def hz(name):
    n, o = name[:-1], int(name[-1]); semi = NOTE[n[0]] + (1 if "#" in n else 0) - (1 if "b" in n else 0)
    return 440.0 * 2 ** ((semi - 9) / 12 + (o - 4))

def ambient(duration, chord_times, bells, sr=44100, seed=5):
    """静かなパッド＋シーン切替のベル。chord_times=[(t0, [notes]), ...]"""
    n = int(duration * sr); t = np.arange(n) / sr
    out = np.zeros(n, np.float32)
    rng = np.random.default_rng(seed)
    for i, (t0, notes) in enumerate(chord_times):
        t1 = chord_times[i + 1][0] if i + 1 < len(chord_times) else duration + 2
        env = np.clip((t - t0) / 2.2, 0, 1) * np.clip((t1 + 1.2 - t) / 2.0, 0, 1)   # ゆっくり出てゆっくり消える
        env = env ** 1.5
        for nm in notes:
            fq = hz(nm)
            for det, amp in ((-0.35, 0.5), (0.0, 1.0), (0.35, 0.5)):
                ph = rng.uniform(0, 6.28)
                out += amp * 0.045 * env * np.sin(2 * np.pi * (fq + det) * t + ph) * (1 + 0.08 * np.sin(2 * np.pi * 0.17 * t + ph))
                out += amp * 0.012 * env * np.sin(2 * np.pi * (fq * 2 + det) * t + ph)
    # ベル（シーン切替）
    for tb, nm in bells:
        fq = hz(nm); i0 = int(tb * sr); tt = np.arange(n - i0) / sr
        bell = np.exp(-tt * 1.6) * (np.sin(2 * np.pi * fq * tt) + 0.35 * np.sin(2 * np.pi * fq * 2.0 * tt) * np.exp(-tt * 2.5) + 0.12 * np.sin(2 * np.pi * fq * 3.0 * tt) * np.exp(-tt * 4))
        out[i0:] += 0.16 * bell.astype(np.float32)
    # ごく薄い「空気」ノイズ（ローパス）
    noise = rng.normal(0, 1, n).astype(np.float32)
    k = 0.002; lp = np.zeros(n, np.float32); acc = 0.0
    for i in range(0, n, 64):   # ブロック単位の簡易ローパス
        acc = acc * (1 - k * 64) + noise[i:i + 64].mean() * k * 64
        lp[i:i + 64] = acc
    out += lp * 0.4
    # フェードアウト・正規化
    fade = np.clip((duration - t) / 1.2, 0, 1); out *= fade
    out = out / (np.max(np.abs(out)) + 1e-6) * 0.55
    # わずかなステレオ感
    left = out; right = np.roll(out, 220) * 0.97
    return np.stack([left, right], axis=1), sr

def write_wav(path, data, sr):
    pcm = (np.clip(data, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())
    return path

# ---------------------------------------------------------------- テーマB：朝焼けの空と海（実写が無いときの描画背景）
def dawn_sky(w, h, horizon=0.74, seed=7, photo=None):
    """朝焼けのグラデーション＋薄い雲＋海。photo にファイルパスを渡すとその写真をカバー配置して返す"""
    if photo and os.path.exists(photo):
        im = Image.open(photo).convert("RGB"); k = max(w / im.width, h / im.height)
        im = im.resize((int(im.width * k) + 1, int(im.height * k) + 1), Image.LANCZOS)
        x0, y0 = (im.width - w) // 2, (im.height - h) // 2
        return im.crop((x0, y0, x0 + w, y0 + h))
    hz = int(h * horizon)
    def vgrad(ww, hh, stops):
        t = np.linspace(0, 1, hh, dtype=np.float32); col = np.zeros((hh, 3), np.float32)
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            m = (t >= t0) & (t <= t1); k = (t - t0) / (t1 - t0)
            for i in range(3): col[:, i] = np.where(m, c0[i] * (1 - k) + c1[i] * k, col[:, i])
        return np.repeat(col[:, None, :], ww, axis=1)
    sky = vgrad(w, hz, [(0, (70, 56, 126)), (0.3, (150, 110, 168)), (0.62, (236, 170, 162)), (0.86, (255, 214, 172)), (1.0, (255, 236, 196))])
    sea = vgrad(w, h - hz, [(0, (255, 226, 182)), (0.2, (226, 170, 160)), (0.6, (150, 110, 160)), (1.0, (80, 62, 128))])
    # 薄い雲（横に流れる帯）
    cl = np.asarray(L.fractal(max(w, hz), seed).resize((w, hz), Image.BILINEAR), np.float32) / 255.0
    band = np.clip((np.linspace(0, 1, hz, dtype=np.float32)[:, None] - 0.35) / 0.45, 0, 1) * (1 - np.linspace(0, 1, hz, dtype=np.float32)[:, None]) * 2.2
    cloud = np.clip((cl - 0.52) * 3.0, 0, 1) * band
    tint = np.array([255, 232, 214], np.float32)
    sky = sky * (1 - cloud[..., None] * 0.55) + tint[None, None, :] * cloud[..., None] * 0.55
    arr = np.concatenate([sky, sea], axis=0)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    # 海面のきらめき（水平線近くの光の道）
    ref = Image.new("RGBA", (w, h), (255, 240, 205, 0)); rd = ImageDraw.Draw(ref); rnd = random.Random(seed)
    for y in range(hz, h, 5):
        k = (y - hz) / (h - hz); ww = 110 + 240 * k; a = int(95 * (1 - k))
        x0 = w / 2 - ww / 2 + rnd.uniform(-40, 40)
        rd.line([(x0, y), (x0 + ww, y)], fill=(255, 240, 205, a), width=2)
    ref = ref.filter(ImageFilter.GaussianBlur(5))
    img = Image.alpha_composite(img.convert("RGBA"), ref).convert("RGB")
    # 上空の星（薄く）
    d = ImageDraw.Draw(img)
    for _ in range(int(w * h / 14000)):
        x, y = rnd.randint(0, w), rnd.randint(0, int(hz * .45)); r = rnd.choice([1, 1, 2]); a = rnd.randint(110, 230)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(a, a - 6, a))
    return img

def thin_frame_layer(col=(255, 248, 232), inset=60):
    """テーマB/C用の細い一重フレーム"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle([inset, inset, W - inset, H - inset], outline=col + (230,), width=2)
    return lay

def scrim_layer(y0=720, y1=1560, col=(60, 36, 96), amax=0.36):
    """文字の背面に置く、上下がぼける半透明の帯（明るい背景で白文字を読ませる）"""
    lay = Image.new("RGBA", (W, H), col + (0,))
    a = np.zeros((H, 1), np.float32); yy = np.arange(H, dtype=np.float32)
    core0, core1 = y0 + (y1 - y0) * 0.32, y1 - (y1 - y0) * 0.32
    a[:, 0] = np.where(yy < y0, 0, np.where(yy < core0, (yy - y0) / (core0 - y0), np.where(yy < core1, 1, np.where(yy < y1, (y1 - yy) / (y1 - core1), 0))))
    alpha = Image.fromarray((np.repeat(a, W, axis=1) * 255 * amax).astype(np.uint8))
    lay.putalpha(alpha); return lay
