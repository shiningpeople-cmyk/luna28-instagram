# -*- coding: utf-8 -*-
"""固定投稿3本・ハイライト5本（テーマC：生成り×墨×金）
  python3 render_fixed.py --out out/fixed
  27のルナの呼び名は content/luna_names.json（番号→名前）。未確定は「？」で描く
"""
import argparse, os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import luna_style as L
import luna_video as V
import render_carousel as C

f = L.f
THEME = os.environ.get("FIXED_THEME", "dawn")            # dawn（朝焼けの空と海）/ purple（紫×金）/ washi（生成り×墨×金）
GOLD = L.GOLD
SH = None
if THEME == "dawn":
    INK, SOFT, GOLD_D = (255, 252, 246), (255, 242, 222), (255, 236, 196)
    LINE = (255, 246, 230); SH = (70, 40, 100)
elif THEME == "purple":
    INK, SOFT, GOLD_D = (250, 244, 255), (226, 212, 236), L.GOLD_L
    LINE = L.lerp(L.GOLD, L.VIOLET, .6)
else:
    INK, SOFT, GOLD_D = C.CREAM, C.SOFT, L.GOLD_D
    LINE = (222, 206, 160)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMES = json.load(open(os.path.join(ROOT, "content", "luna_names.json"), encoding="utf-8")) if os.path.exists(os.path.join(ROOT, "content", "luna_names.json")) else {}
ORDER = [n for n in range(1, 29) if n != 20]

def paper(W, H, seed=4):
    if THEME == "dawn":
        return V.dawn_sky(W, H, horizon=0.76 if H > W * 1.5 else 0.80, seed=seed)
    if THEME == "purple":
        img = V.purple_bg(W, H, light_bottom=0.30, seed=seed)
        veil = Image.new("RGBA", (W, H), (60, 30, 100, 50))
        return Image.alpha_composite(img.convert("RGBA"), veil).convert("RGB")
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (H // 4, W // 4)).astype(np.float32)
    n = np.asarray(Image.fromarray(np.clip(n * 40 + 128, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.2)), np.float32)
    arr = np.zeros((H, W, 3), np.float32)
    for i in range(3): arr[..., i] = C.PAPER[i] + (n - 128) * 0.10
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]; arr[..., 0] += t * 4; arr[..., 2] -= t * 6
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def frame(img, inset=48):
    W, H = img.size; d = ImageDraw.Draw(img)
    if THEME == "dawn":
        d.rectangle([inset, inset, W - inset, H - inset], outline=LINE + (230,) if False else LINE, width=2); return
    d.rectangle([inset, inset, W - inset, H - inset], outline=GOLD, width=2)
    d.rectangle([inset + 10, inset + 10, W - inset - 10, H - inset - 10], outline=LINE, width=1)

def panel(img, box, alpha=120, radius=26):
    """文字の背面に敷く半透明の紫パネル（明るい空の上で白文字を読ませる）"""
    if THEME != "dawn": return img
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle(box, radius=radius, fill=(60, 36, 96, alpha), outline=(255, 240, 210, 110), width=1)
    return Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")

def band(img, y0, y1, amax=0.40):
    """上下がぼける帯（短い見出し向け）"""
    if THEME != "dawn": return img
    Wi, Hi = img.size
    yy = np.arange(Hi, dtype=np.float32); c0, c1 = y0 + (y1 - y0) * 0.3, y1 - (y1 - y0) * 0.3
    a = np.where(yy < y0, 0, np.where(yy < c0, (yy - y0) / (c0 - y0), np.where(yy < c1, 1, np.where(yy < y1, (y1 - yy) / (y1 - c1), 0))))
    lay = Image.new("RGBA", (Wi, Hi), (60, 36, 96, 0)); lay.putalpha(Image.fromarray((np.repeat(a[:, None], Wi, axis=1) * 255 * amax).astype(np.uint8)))
    return Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")

def text(d, xy, s, font, fill):
    if SH: d.text((xy[0] + 3, xy[1] + 3), s, font=font, fill=SH)
    d.text(xy, s, font=font, fill=fill)

def moon(img, size, cx, cy, alpha=1.0):
    if THEME == "washi": return C.moon_at(img, size, cx, cy, alpha)
    mo = L.moon(size)
    if alpha < 1: mo.putalpha(mo.split()[3].point(lambda a: int(a * alpha)))
    base = img.convert("RGBA"); base.alpha_composite(mo, (int(cx - size / 2), int(cy - size / 2))); return base.convert("RGB")

def ctext(d, s_, cx, y, font, fill):
    b = d.textbbox((0, 0), s_, font=font); text(d, (cx - (b[2] - b[0]) / 2, y), s_, font, fill)

def gold_c(img, text, cx, y, font):
    d = ImageDraw.Draw(img); b = d.textbbox((0, 0), text, font=font); L.gold_text(img, (int(cx - (b[2] - b[0]) / 2), int(y)), text, font)

def rule(d, cx, y, half=200):
    d.line([(cx - half, y), (cx + half, y)], fill=GOLD, width=1); L.diamond(d, cx, y, 7, GOLD)

# ============================================================ 固定投稿（1080x1350）
W, H = 1080, 1350
def brand(d): text(d, (96, 92), "LUNA28　宿曜占星術", font=f(L.SERIFM, 28), fill=GOLD_D)
def foot(d, n=None, total=None):
    ctext(d, "@luna28.japan", W / 2, 1250, f(L.SERIFM, 26), GOLD_D)
    if total:
        for i in range(total):
            cx = W / 2 - (total - 1) * 13 + i * 26
            d.ellipse([cx - 4, 1292 - 4, cx + 4, 1292 + 4], fill=GOLD if i == n else LINE)

def pin2_p1():
    """27のルナ早見表"""
    img = paper(W, H); img = moon(img, 220, W - 170, 170, 0.9); img = panel(img, (72, 300, W - 72, 1180)); frame(img)
    d = ImageDraw.Draw(img); brand(d)
    L.gold_text(img, (96, 150), "27のルナ 早見表", f(L.SERIF, 76)); d = ImageDraw.Draw(img)
    text(d, (96, 250), "生年月日で決まる、あなたの星の名前", font=f(L.SERIFM, 32), fill=SOFT)
    cols, cw, ch, x0, y0 = 3, 296, 92, 96, 330
    for i, n in enumerate(ORDER):
        r, c = divmod(i, cols); x, y = x0 + c * cw, y0 + r * ch
        name = NAMES.get(str(n), "？")
        text(d, (x, y + 14), f"{n:>2}", font=f(L.SERIF, 40), fill=GOLD_D)
        text(d, (x + 64, y + 22), name, font=f(L.SERIFM, 34), fill=INK if name != "？" else SOFT)
        d.line([(x, y + ch - 6), (x + cw - 30, y + ch - 6)], fill=LINE, width=1)
    ctext(d, "次のページ → ルナは、どう決まる？", W / 2, 1195, f(L.SERIFM, 30), SOFT)
    foot(d, 0, 2); return img

def pin2_p2():
    """ルナは、どう決まる？"""
    img = paper(W, H); img = moon(img, 560, W / 2, 340); img = band(img, 620, 1260, 0.42); frame(img)
    d = ImageDraw.Draw(img); brand(d)
    gold_c(img, "ルナは、どう決まる？", W / 2, 690, f(L.SERIF, 84)); d = ImageDraw.Draw(img)
    rule(d, W / 2, 820, 220)
    ctext(d, "生まれた日の、月の位置で決まります。", W / 2, 860, f(L.SERIFM, 40), INK)
    for i, ln in enumerate(["生年月日を昔の暦（旧暦）に直して、", "その日に月がいた場所が、あなたのルナ。", "だから同じ星座の人でも、ルナは違います。"]):
        ctext(d, ln, W / 2, 940 + i * 64, f(L.SERIFM, 34), SOFT)
    L.gold_pill(img, (W / 2 - 320, 1160, W / 2 + 320, 1250), "自分のルナを調べる ▶", f(L.SANSB, 34))
    foot(ImageDraw.Draw(img), 1, 2); return img

def pin3():
    """会員になると届くもの（永久固定）"""
    img = paper(W, H); img = moon(img, 300, W - 190, 190, 0.85); img = panel(img, (72, 375, W - 72, 955)); img = band(img, 950, 1250, 0.42); frame(img)
    d = ImageDraw.Draw(img); brand(d)
    text(d, (96, 170), "会員になると", font=f(L.SERIFM, 44), fill=INK)
    L.gold_text(img, (96, 230), "毎日、運勢が届く", f(L.SERIF, 84)); d = ImageDraw.Draw(img)
    d.line([(96, 350), (W - 96, 350)], fill=GOLD, width=1)
    items = [("今日の運勢", "365日、毎日"), ("今月の運勢・今年の運勢", "月ごと、年ごとの流れ"), ("相性診断", "ふたりのルナ番号で、何度でも"), ("吉凶カレンダー", "1か月の吉凶が一目で"), ("宿命・天運／才能・適職／恋愛・結婚／金運・健康", "自分のルナを、くわしく")]
    y = 395
    for t, s in items:
        L.diamond(d, 120, y + 26, 10)
        text(d, (150, y), t, font=f(L.SERIFM, 38), fill=INK); text(d, (150, y + 50), s, font=f(L.SERIFM, 28), fill=SOFT); y += 112
    rule(d, W / 2, 975, 300)
    ctext(d, "プレミアム会員　月550円から", W / 2, 1000, f(L.SERIFM, 40), GOLD_D)
    ctext(d, "2007年から続く宿曜占星術　一冊であなたも占い師『新占星術LUNA28』", W / 2, 1060, f(L.SERIFM, 26), SOFT)
    L.gold_pill(img, (W / 2 - 300, 1115, W / 2 + 300, 1205), "会員になる ▶ プロフィールのリンク", f(L.SANSB, 30))
    foot(ImageDraw.Draw(img)); return img

# ============================================================ ハイライト（1080x1920）
SW, SH = 1080, 1920
def hl_cover(label):
    """丸く切り抜かれる前提：中央 700px に収める"""
    img = paper(SW, SH, seed=7); img = band(img, SH / 2 - 60, SH / 2 + 260, 0.35); img = moon(img, 300, SW / 2, SH / 2 - 190)
    d = ImageDraw.Draw(img)
    d.ellipse([SW / 2 - 400, SH / 2 - 400, SW / 2 + 400, SH / 2 + 400], outline=GOLD, width=3)
    d.ellipse([SW / 2 - 386, SH / 2 - 386, SW / 2 + 386, SH / 2 + 386], outline=LINE, width=1)
    ctext(d, label, SW / 2, SH / 2 + 20, f(L.SERIF, 72 if len(label) <= 5 else 60), INK)
    rule(d, SW / 2, SH / 2 + 140, 120)
    ctext(d, "LUNA28", SW / 2, SH / 2 + 165, f(L.SERIFM, 30), GOLD_D)
    return img

def hl_story(title, lines, cta=None, moon_size=560):
    img = paper(SW, SH, seed=9); img = moon(img, moon_size, SW / 2, 520); img = band(img, 820, 1720, 0.5); frame(img, 60)
    d = ImageDraw.Draw(img)
    ctext(d, "LUNA28　宿曜占星術", SW / 2, 150, f(L.SERIFM, 34), GOLD_D)
    gold_c(img, title, SW / 2, 880, f(L.SERIF, 84 if len(title) <= 8 else 68)); d = ImageDraw.Draw(img)
    rule(d, SW / 2, 1020, 220)
    y = 1070
    for ln in lines:
        for sub in V.wrap(ln, 18): ctext(d, sub, SW / 2, y, f(L.SERIFM, 44), INK); y += 76
        y += 24
    if cta: L.gold_pill(img, (SW / 2 - 360, 1540, SW / 2 + 360, 1650), cta, f(L.SANSB, 40))
    ctext(ImageDraw.Draw(img), "@luna28.japan", SW / 2, 1760, f(L.SERIFM, 30), GOLD_D)
    return img

HIGHLIGHTS = [
    ("01", "ルナ28とは", [("月の位置で決まる27のルナ", ["生まれた日の月の位置から、あなたのルナが決まります。", "全部で27種類あります。"], "自分のルナを調べる ▶"),
                         ("2007年から、毎日", ["宿曜経をもとに、毎日の運勢・相性・月運・年運を届けています。", "一冊であなたも占い師『新占星術LUNA28』"], None)]),
    ("02", "無料で調べる", [("調べ方は、これだけ", ["① プロフィールのリンクを開く", "② 生年月日を選ぶ", "③ 番号と性格が出ます"], "30秒・登録不要 ▶")]),
    ("03", "27のルナ", []),
    ("04", "相性", [("ふたりのルナ番号でわかる相性", ["27×27＝729通り。", "恋人でも、友だちでも、職場の人でも。"], "LINEで「相性」と送る ▶")]),
    ("05", "会員になる", [("会員になると届くもの", ["毎日の運勢がメールで届く", "今月・今年の運勢、相性診断", "吉凶カレンダー、宿命・才能・恋愛・金運・健康"], "月550円から ▶")]),
]

def render(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    pin2_p1().save(os.path.join(out_dir, "pin2_早見表_1.jpg"), quality=92)
    pin2_p2().save(os.path.join(out_dir, "pin2_早見表_2_どう決まる.jpg"), quality=92)
    pin3().save(os.path.join(out_dir, "pin3_会員になると.jpg"), quality=92)
    for n, label, stories in HIGHLIGHTS:
        hl_cover(label).save(os.path.join(out_dir, f"hl{n}_cover_{label}.jpg"), quality=92)
        for i, (t, lines, cta) in enumerate(stories, 1):
            hl_story(t, lines, cta).save(os.path.join(out_dir, f"hl{n}_story{i}_{label}.jpg"), quality=92)
    return sorted(os.listdir(out_dir))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True)
    print(render(ap.parse_args().out))
