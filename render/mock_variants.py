# -*- coding: utf-8 -*-
"""ブランド配色3案の比較モック（リールの「それ、○のルナかも」画面 ＋ 図鑑カルーセル表紙）"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import luna_style as L
import luna_video as V

f = L.f
OUT = "/home/claude/ig_auto/out/variants"; os.makedirs(OUT, exist_ok=True)

def vgrad(w, h, stops):
    t = np.linspace(0, 1, h, dtype=np.float32); col = np.zeros((h, 3), np.float32)
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        m = (t >= t0) & (t <= t1); k = (t - t0) / (t1 - t0)
        for i in range(3): col[:, i] = np.where(m, c0[i] * (1 - k) + c1[i] * k, col[:, i])
    return Image.fromarray(np.clip(np.repeat(col[:, None, :], w, axis=1), 0, 255).astype(np.uint8))

def stars(img, n, seed=3, col=(255, 250, 235)):
    d = ImageDraw.Draw(img); rnd = random.Random(seed); W, H = img.size
    for _ in range(n):
        x, y = rnd.randint(0, W), rnd.randint(0, int(H * .6)); r = rnd.choice([1, 1, 2]); a = rnd.randint(120, 255)
        d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(c * a / 255) for c in col))

def moon(img, size, cx, cy, silver=False, alpha=1.0, flat=False):
    mo = L.moon(size)
    if flat:   # 明るい背景用：にじみを外して円盤だけ＋細い金の縁
        m = Image.new("L", mo.size, 0); r = size * 0.24
        ImageDraw.Draw(m).ellipse([size/2-r, size/2-r, size/2+r, size/2+r], fill=255); m = m.filter(ImageFilter.GaussianBlur(1.2))
        mo.putalpha(m)
        ring = Image.new("RGBA", mo.size, (0,0,0,0)); ImageDraw.Draw(ring).ellipse([size/2-r-3, size/2-r-3, size/2+r+3, size/2+r+3], outline=(212,172,92,200), width=3)
        mo = Image.alpha_composite(ring, mo)
    if silver:
        g = mo.convert("L"); rgb = Image.merge("RGB", (g, g, g)).convert("RGBA"); rgb.putalpha(mo.split()[3])
        tint = Image.new("RGBA", mo.size, (236, 240, 255, 0)); mo = Image.blend(rgb, tint, 0.0)
        mo = Image.eval(mo, lambda v: min(255, int(v * 1.08)))
    if alpha < 1: mo.putalpha(mo.split()[3].point(lambda a: int(a * alpha)))
    base = img.convert("RGBA"); base.alpha_composite(mo, (int(cx - size / 2), int(cy - size / 2))); return base.convert("RGB")

def ctext(d, text, cx, y, font, fill):
    b = d.textbbox((0, 0), text, font=font); d.text((cx - (b[2] - b[0]) / 2, y), text, font=font, fill=fill)

def gold_c(img, text, cx, y, font):
    d = ImageDraw.Draw(img); b = d.textbbox((0, 0), text, font=font); L.gold_text(img, (int(cx - (b[2] - b[0]) / 2), int(y)), text, font)

def washi(w, h, base=(247, 242, 232), seed=4):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (h // 4, w // 4)).astype(np.float32)
    n = np.asarray(Image.fromarray(np.clip(n * 40 + 128, 0, 255).astype(np.uint8)).resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.2)), np.float32)
    arr = np.zeros((h, w, 3), np.float32)
    for i in range(3): arr[..., i] = base[i] + (n - 128) * 0.10
    # 下にいくほど少し暖かく
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    arr[..., 0] += t * 4; arr[..., 2] -= t * 6
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

# ---------------------------------------------------------------- 3案
def reel_A(no, name):   # 現行：紫×金・金箔の月
    W, H = 1080, 1920
    img = V.purple_bg(W, H, light_bottom=0.35); img = moon(img, 760, W / 2, 520)
    img = img.convert("RGBA"); img.alpha_composite(V.frame_layer()); img = img.convert("RGB")
    d = ImageDraw.Draw(img)
    ctext(d, "LUNA28　宿曜占星術", W / 2, 150, f(L.SERIFM, 36), L.GOLD_L)
    ctext(d, "それ、", W / 2, 900, f(L.SERIFM, 60), V.CREAM)
    gold_c(img, f"{no}のルナ", W / 2, 990, f(L.SERIF, 150)); d = ImageDraw.Draw(img)
    ctext(d, "かも", W / 2, 1190, f(L.SERIFM, 60), V.CREAM)
    L.ornament_divider(d, W / 2, 1320, half=240); ctext(d, f"「{name}」", W / 2, 1360, f(L.SERIFM, 56), L.GOLD_L)
    return img

def cover_A(no, name, catch):
    import render_carousel as R
    return R.page_cover({"no": no, "name": name, "catch": catch}, 6)

def reel_B(no, name):   # 朝焼けの空と海（飯田さんの動画の世界観）
    W, H = 1080, 1920
    sky = vgrad(W, int(H * 0.74), [(0, (74, 58, 128)), (0.35, (168, 120, 170)), (0.7, (244, 178, 160)), (1.0, (255, 226, 178))])
    sea = vgrad(W, H - sky.height, [(0, (255, 214, 168)), (0.25, (214, 160, 160)), (1.0, (92, 70, 130))])
    img = Image.new("RGB", (W, H)); img.paste(sky, (0, 0)); img.paste(sea, (0, sky.height))
    # 海の反射（横に伸ばした光）
    ref = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rd = ImageDraw.Draw(ref); rng = random.Random(2)
    for y in range(sky.height, H, 6):
        k = (y - sky.height) / (H - sky.height); w = 120 + 260 * k; a = int(90 * (1 - k))
        x0 = W / 2 - w / 2 + rng.uniform(-40, 40)
        rd.line([(x0, y), (x0 + w, y)], fill=(255, 240, 205, a), width=2)
    ref = ref.filter(ImageFilter.GaussianBlur(5)); img = Image.alpha_composite(img.convert("RGBA"), ref).convert("RGB")
    stars(img, 160, seed=5)
    img = moon(img, 620, W / 2, 600)
    d = ImageDraw.Draw(img)
    d.rectangle([60, 60, W - 60, H - 60], outline=(255, 248, 230), width=2)
    ctext(d, "LUNA28　宿曜占星術", W / 2, 150, f(L.SERIFM, 36), (255, 250, 240))
    ctext(d, "それ、", W / 2, 960, f(L.SERIFM, 60), (255, 252, 246))
    gold_c(img, f"{no}のルナ", W / 2, 1050, f(L.SERIF, 150)); d = ImageDraw.Draw(img)
    ctext(d, "かも", W / 2, 1250, f(L.SERIFM, 60), (255, 252, 246))
    d.line([(W / 2 - 200, 1380), (W / 2 + 200, 1380)], fill=(255, 240, 210), width=1)
    ctext(d, f"「{name}」", W / 2, 1410, f(L.SERIFM, 56), (255, 246, 226))
    return img

def cover_B(no, name, catch):
    W, H = 1080, 1350
    sky = vgrad(W, int(H * 0.6), [(0, (74, 58, 128)), (0.35, (168, 120, 170)), (0.7, (244, 178, 160)), (1.0, (255, 226, 178))])
    sea = vgrad(W, H - sky.height, [(0, (255, 214, 168)), (0.3, (214, 160, 160)), (1.0, (92, 70, 130))])
    img = Image.new("RGB", (W, H)); img.paste(sky, (0, 0)); img.paste(sea, (0, sky.height))
    stars(img, 100, seed=6); img = moon(img, 420, W / 2, 330)
    d = ImageDraw.Draw(img); d.rectangle([48, 48, W - 48, H - 48], outline=(255, 248, 230), width=2)
    ctext(d, "27 の ル ナ 図 鑑", W / 2, 92, f(L.SERIFM, 28), (255, 250, 240))
    gold_c(img, str(no), W / 2 - 40, 600, f(L.SERIF, 220)); d = ImageDraw.Draw(img)
    d.text((W / 2 + 40, 760), "のルナ", font=f(L.SERIFM, 44), fill=(255, 252, 246))
    ctext(d, f"『{name}』", W / 2, 880, f(L.SERIFM, 60), (255, 246, 226))
    d.line([(W / 2 - 200, 985), (W / 2 + 200, 985)], fill=(255, 240, 210), width=1)
    for i, ln in enumerate(V.wrap(catch, 22)): ctext(d, ln, W / 2, 1020 + i * 52, f(L.SERIFM, 34), (255, 252, 246))
    ctext(d, "LUNA28　宿曜占星術", W / 2, 1238, f(L.SERIFM, 26), (255, 246, 226))
    return img

INK = (58, 48, 56); INK_L = (120, 104, 112)
def reel_C(no, name):   # 生成り×墨×金の和モダン
    W, H = 1080, 1920
    img = washi(W, H); img = moon(img, 700, W / 2, 560, flat=True)
    d = ImageDraw.Draw(img)
    d.rectangle([60, 60, W - 60, H - 60], outline=L.GOLD, width=2); d.rectangle([72, 72, W - 72, H - 72], outline=(222, 206, 160), width=1)
    ctext(d, "LUNA28　宿曜占星術", W / 2, 150, f(L.SERIFM, 36), L.GOLD_D)
    ctext(d, "それ、", W / 2, 960, f(L.SERIFM, 60), INK)
    gold_c(img, f"{no}のルナ", W / 2, 1050, f(L.SERIF, 150)); d = ImageDraw.Draw(img)
    ctext(d, "かも", W / 2, 1250, f(L.SERIFM, 60), INK)
    d.line([(W / 2 - 200, 1380), (W / 2 + 200, 1380)], fill=L.GOLD, width=1); L.diamond(d, W / 2, 1380, 7, L.GOLD)
    ctext(d, f"「{name}」", W / 2, 1410, f(L.SERIFM, 56), INK)
    return img

def cover_C(no, name, catch):
    W, H = 1080, 1350
    img = washi(W, H); img = moon(img, 520, W / 2, 330, flat=True)
    d = ImageDraw.Draw(img)
    d.rectangle([48, 48, W - 48, H - 48], outline=L.GOLD, width=2); d.rectangle([58, 58, W - 58, H - 58], outline=(222, 206, 160), width=1)
    ctext(d, "27 の ル ナ 図 鑑", W / 2, 92, f(L.SERIFM, 28), L.GOLD_D)
    gold_c(img, str(no), W / 2 - 40, 600, f(L.SERIF, 220)); d = ImageDraw.Draw(img)
    d.text((W / 2 + 40, 760), "のルナ", font=f(L.SERIFM, 44), fill=INK)
    ctext(d, f"『{name}』", W / 2, 880, f(L.SERIFM, 60), INK)
    d.line([(W / 2 - 200, 985), (W / 2 + 200, 985)], fill=L.GOLD, width=1); L.diamond(d, W / 2, 985, 7, L.GOLD)
    for i, ln in enumerate(V.wrap(catch, 22)): ctext(d, ln, W / 2, 1020 + i * 52, f(L.SERIFM, 34), INK_L)
    ctext(d, "LUNA28　宿曜占星術", W / 2, 1238, f(L.SERIFM, 26), L.GOLD_D)
    return img

if __name__ == "__main__":
    no, name, catch = 1, "王の人", "恵まれた天運に導かれ、品格と知性を持って生きる星"
    sets = [("A", reel_A, cover_A), ("B", reel_B, cover_B), ("C", reel_C, cover_C)]
    tiles = []
    for tag, rf, cf in sets:
        r = rf(no, name); c = cf(no, name, catch)
        r.save(f"{OUT}/reel_{tag}.jpg", quality=90); c.save(f"{OUT}/cover_{tag}.jpg", quality=90)
        tiles.append((r.resize((405, 720)), c.resize((405, 506))))
    board = Image.new("RGB", (3 * 405 + 2 * 40 + 80, 720 + 506 + 120), (250, 250, 250)); bd = ImageDraw.Draw(board)
    labels = ["A　紫×金（現行）", "B　朝焼けの空と海", "C　生成り×墨×金"]
    for i, (r, c) in enumerate(tiles):
        x = 40 + i * (405 + 40)
        bd.text((x, 20), labels[i], font=f(L.SANSB, 30), fill=(40, 40, 40))
        board.paste(r, (x, 70)); board.paste(c, (x, 70 + 720 + 20))
    board.save(f"{OUT}/compare.png"); print("ok")
