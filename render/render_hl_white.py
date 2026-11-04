# -*- coding: utf-8 -*-
"""ハイライト5本（白テーマ）：カバー＋ストーリーズ画像 1080x1920
  python3 render_hl_white.py --out out/hl_white
"""
import argparse, os, sys, json, math
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import luna_style as L
import luna_video as V

f = L.f
SW, SH = 1080, 1920
PAPER = (253, 251, 247)            # 白（わずかに温かみ）
INK = (64, 44, 92)                 # 深い紫
SOFT = (126, 104, 150)
GOLD, GOLD_D, GOLD_L = L.GOLD, (168, 128, 56), L.GOLD_L
LINE = (222, 206, 164)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMES = json.load(open(os.path.join(ROOT, "content", "luna_names.json"), encoding="utf-8"))
ORDER = [n for n in range(1, 29) if n != 20]

def paper(seed=4):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (SH // 4, SW // 4)).astype(np.float32)
    n = np.asarray(Image.fromarray(np.clip(n * 40 + 128, 0, 255).astype(np.uint8)).resize((SW, SH), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.4)), np.float32)
    arr = np.zeros((SH, SW, 3), np.float32)
    for i in range(3): arr[..., i] = PAPER[i] + (n - 128) * (0.0 if os.environ.get("HL_FLAT") else 0.05)
    # 上からごく薄い金のかすみ
    t = np.linspace(1, 0, SH, dtype=np.float32)[:, None]
    arr[..., 0] += t * 1.5; arr[..., 2] -= t * 4
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    # 金の小さな星
    d = ImageDraw.Draw(img); r2 = np.random.default_rng(seed + 100)
    for _ in range(70):
        x, y = int(r2.integers(60, SW - 60)), int(r2.integers(60, SH * 0.55)); r = int(r2.integers(1, 3))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(232, 212, 160))
    return img

def frame(img, inset=56):
    d = ImageDraw.Draw(img)
    d.rectangle([inset, inset, SW - inset, SH - inset], outline=GOLD, width=2)
    d.rectangle([inset + 12, inset + 12, SW - inset - 12, SH - inset - 12], outline=LINE, width=1)

def moon(img, size, cx, cy, alpha=1.0):
    mo = L.moon(size)
    # 白地に沈まないよう、柔らかい金の影
    glow = Image.new("RGBA", img.size, (236, 206, 140, 0)); gd = ImageDraw.Draw(glow)
    gd.ellipse([cx - size * .62, cy - size * .62, cx + size * .62, cy + size * .62], fill=(236, 206, 140, 90))
    glow = glow.filter(ImageFilter.GaussianBlur(size * 0.12))
    base = Image.alpha_composite(img.convert("RGBA"), glow)
    if alpha < 1: mo.putalpha(mo.split()[3].point(lambda a: int(a * alpha)))
    base.alpha_composite(mo, (int(cx - size / 2), int(cy - size / 2))); return base.convert("RGB")

def bright_moon(img, dia, cx, cy, crescent=False, bite=(0.40, -0.28), inner=0.94):
    """明るい月色の円盤（L.moon の中心円盤だけ使う）。crescent=True で右上が欠けた三日月"""
    size = int(dia / 0.48); mo = L.moon(size); r = size * 0.24; c = size / 2
    m = Image.new("L", mo.size, 0); md = ImageDraw.Draw(m)
    md.ellipse([c - r, c - r, c + r, c + r], fill=255)
    if crescent:
        bx, by, br = c + bite[0] * 2 * r, c + bite[1] * 2 * r, r * inner
        md.ellipse([bx - br, by - br, bx + br, by + br], fill=0)
    m = m.filter(ImageFilter.GaussianBlur(1.2))
    mo.putalpha(Image.fromarray((np.asarray(mo.split()[3], np.float32) * np.asarray(m, np.float32) / 255).astype(np.uint8)))
    ring = Image.new("RGBA", mo.size, (0, 0, 0, 0)); ImageDraw.Draw(ring).ellipse([c - r - 3, c - r - 3, c + r + 3, c + r + 3], outline=(212, 172, 92, 200), width=3)
    if crescent: ring.putalpha(Image.fromarray((np.asarray(ring.split()[3], np.float32) * np.asarray(m.filter(ImageFilter.MaxFilter(9)), np.float32) / 255).astype(np.uint8)))
    glow = Image.new("RGBA", img.size, (236, 206, 140, 0)); gd = ImageDraw.Draw(glow)
    gd.ellipse([cx - r * 1.35, cy - r * 1.35, cx + r * 1.35, cy + r * 1.35], fill=(236, 206, 140, 90))
    base = Image.alpha_composite(img.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(r * 0.25)))
    base.alpha_composite(ring, (int(cx - c), int(cy - c))); base.alpha_composite(mo, (int(cx - c), int(cy - c)))
    return base.convert("RGB")

def ctext(d, s, cx, y, font, fill):
    b = d.textbbox((0, 0), s, font=font); d.text((cx - (b[2] - b[0]) / 2, y), s, font=font, fill=fill)

def gold_c(img, s, cx, y, font):
    d = ImageDraw.Draw(img); b = d.textbbox((0, 0), s, font=font)
    L.gold_text(img, (int(cx - (b[2] - b[0]) / 2), int(y)), s, font, shadow=(150, 118, 60))

def rule(d, cx, y, half=200):
    d.line([(cx - half, y), (cx + half, y)], fill=GOLD, width=1); L.diamond(d, cx, y, 7, GOLD)

# ---------------------------------------------------------------- カバー（丸く切り抜かれる：中央700pxに収める）
EMBLEM = os.path.join(ROOT, "content", "sunmoon_emblem.png")
def emblem_layer(size, alpha=0.55, color=(190, 150, 70)):
    """「太陽と月の円」を金の線画に（濃い円盤は落とし、輪・星座・太陽・月・星だけ）"""
    em = Image.open(EMBLEM).convert("RGBA")
    em = em.resize((size, int(em.height * size / em.width)), Image.LANCZOS)
    a = np.asarray(em).astype(np.float32)
    lum = a[..., :3].mean(axis=2); al = a[..., 3] / 255
    bright = np.clip((lum - 60) / 120, 0, 1) * al
    lay = Image.new("RGBA", em.size, color + (255,)); lay.putalpha(Image.fromarray((bright * 255 * alpha).astype(np.uint8)))
    return lay

def zodiac_layer(n, color=(196, 160, 80), alpha=0.8, scale=1.9):
    m = Image.open(os.path.join(ROOT, "content", f"zodiac_{n:02d}.png")).convert("L")
    m = m.resize((max(1, int(m.width * scale)), max(1, int(m.height * scale))), Image.LANCZOS)
    lay = Image.new("RGBA", m.size, color + (255,)); lay.putalpha(m.point(lambda a: int(a * alpha)))
    return lay

def constellations(img, spots):
    """spots: [(星座番号, x, y, scale, alpha), ...] 薄い金の線画を散らす"""
    base = img.convert("RGBA")
    for n, x, y, sc, al in spots:
        base.alpha_composite(zodiac_layer(n, alpha=al, scale=sc), (int(x), int(y)))
    return base.convert("RGB")

STORY_SPOTS = [(5, 80, 140, 1.9, 0.85), (10, 600, 230, 1.9, 0.8), (12, 70, 1380, 1.9, 0.8), (3, 660, 1470, 1.9, 0.85)]

# ---------------------------------------------------------------- カバー（Instagramで丸く切り抜かれる：中央の直径1080の円に収める）
def hl_cover(label):
    """太陽と月の円（星座の輪）を中央に大きく。輪は切り抜き円のすぐ外側に置き、二重丸に見えないようにする"""
    img = paper(seed=7)
    cx, cy = SW / 2, SH / 2
    em = emblem_layer(1340, alpha=0.65)
    # 外側の輪は切り抜き円（直径1080）の外に出し、円の外側は消す（カバーとして丸く切られたとき二重丸にならない）
    cut = Image.new("L", em.size, 0); r = 522
    ImageDraw.Draw(cut).ellipse([em.width / 2 - r, em.height / 2 - r, em.width / 2 + r, em.height / 2 + r], fill=255)
    cut = cut.filter(ImageFilter.GaussianBlur(6))
    # 元の平らな太陽・月の円盤は消す（下で明るい月色に描き直す）
    sc0 = em.width / 460.0; cd = ImageDraw.Draw(cut)
    for (ex, ey, er) in [(226.5, 89, 50), (229.5, 302, 48)]:
        cd.ellipse([ex * sc0 - er * sc0, ey * sc0 - er * sc0, ex * sc0 + er * sc0, ey * sc0 + er * sc0], fill=0)
    em.putalpha(Image.fromarray((np.asarray(em.split()[3], np.float32) * np.asarray(cut, np.float32) / 255).astype(np.uint8)))
    base = img.convert("RGBA"); base.alpha_composite(em, (int(cx - em.width / 2), int(cy - em.height / 2))); img = base.convert("RGB")
    # 満月と三日月は明るい月色（ストーリーズと同じ月の質感）で上描き
    sc = em.width / 460.0; ox, oy = cx - em.width / 2, cy - em.height / 2
    sun_c = (ox + 226.5 * sc, oy + 89 * sc); mo_c = (ox + 229.5 * sc, oy + 302 * sc)
    img = bright_moon(img, int(2 * 46 * sc), sun_c[0], sun_c[1])
    img = bright_moon(img, int(2 * 42 * sc), mo_c[0], mo_c[1], crescent=True)
    d = ImageDraw.Draw(img)
    fs = 96 if len(label) <= 4 else (84 if len(label) <= 5 else 68)
    ctext(d, label, cx, cy - fs * 0.55, f(L.SERIF, fs), INK)
    rule(d, cx, cy + fs * 0.75, 130)
    return img

# ---------------------------------------------------------------- ストーリーズ
def hl_story(title, lines, cta=None, moon_size=520, url=None):
    img = constellations(paper(seed=9), STORY_SPOTS); img = moon(img, moon_size, SW / 2, 540); frame(img)
    gold_c(img, title, SW / 2, 900, f(L.SERIF, 84 if len(title) <= 8 else (66 if len(title) <= 12 else 58))); d = ImageDraw.Draw(img)
    rule(d, SW / 2, 1040, 220)
    y = 1090
    for ln in lines:
        for sub in V.wrap(ln, 18): ctext(d, sub, SW / 2, y, f(L.SERIFM, 44), INK); y += 76
        if not ln.endswith(("、", "を")): y += 24
    if cta: L.gold_pill(img, (SW / 2 - 360, 1560, SW / 2 + 360, 1670), cta, f(L.SANSB, 40))
    return img

BOOK_PHOTO = os.path.join(ROOT, "content", "book_photo.jpg")
def hl_story_book(url=None):
    """書籍『新占星術ルナ28』：content/book_photo.jpg（実物の写真）を中央に配置"""
    img = constellations(paper(seed=13), [(5, 70, 300, 1.9, 0.85), (10, 760, 330, 1.7, 0.8), (12, 70, 1380, 1.9, 0.8), (3, 660, 1470, 1.9, 0.85)]); frame(img)
    bh = 620
    if os.path.exists(BOOK_PHOTO):
        ph = Image.open(BOOK_PHOTO).convert("RGB")
        ph = ph.resize((int(ph.width * bh / ph.height), bh), Image.LANCZOS)
        bx, by = int(SW / 2 - ph.width / 2), 250
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([bx + 16, by + 28, bx + ph.width + 16, by + bh + 28], fill=(120, 90, 140, 80))
        img = Image.alpha_composite(img.convert("RGBA"), sh.filter(ImageFilter.GaussianBlur(18))).convert("RGB")
        img.paste(ph, (bx, by))
        ImageDraw.Draw(img).rectangle([bx - 1, by - 1, bx + ph.width, by + bh], outline=GOLD, width=2)
    gold_c(img, "書籍『新占星術ルナ28』", SW / 2, 960, f(L.SERIF, 66)); d = ImageDraw.Draw(img)
    rule(d, SW / 2, 1070, 220)
    y = 1120
    for ln in ["LUNA28のもとになった一冊。", "27のルナの性格・相性・運勢を、", "自分で読み解けるようになります。", "", "Amazonで探せます。"]:
        if ln: ctext(d, ln, SW / 2, y, f(L.SERIFM, 44), INK)
        y += 76
    L.gold_pill(img, (SW / 2 - 360, 1560, SW / 2 + 360, 1670), "書籍を見る ▶", f(L.SANSB, 40))
    return img

CHARS = os.path.join(ROOT, "content", "chars")
def medallion(img, n, cx, cy, dia):
    pth = os.path.join(CHARS, f"{n:02d}_med.png")
    if not os.path.exists(pth): return img
    med = Image.open(pth).convert("RGBA").resize((dia, dia), Image.LANCZOS)
    base = img.convert("RGBA")
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse([cx - dia / 2 + 3, cy - dia / 2 + 8, cx + dia / 2 + 3, cy + dia / 2 + 8], fill=(120, 90, 140, 70))
    base = Image.alpha_composite(base, sh.filter(ImageFilter.GaussianBlur(8)))
    base.alpha_composite(med, (int(cx - dia / 2), int(cy - dia / 2)))
    ImageDraw.Draw(base).ellipse([cx - dia / 2, cy - dia / 2, cx + dia / 2, cy + dia / 2], outline=GOLD, width=3)
    return base.convert("RGB")

def hl_story_find(url=None):
    """番号が出たら → 固定投稿で自分のルナを"""
    img = constellations(paper(seed=12), [(5, 80, 120, 1.7, 0.85), (10, 640, 150, 1.7, 0.8), (12, 70, 1380, 1.9, 0.8), (3, 660, 1470, 1.9, 0.85)]); frame(img)
    for i, n in enumerate([1, 9, 15, 22, 28]):
        img = medallion(img, n, 170 + i * 185, 520, 160)
    gold_c(img, "本当のあなたに出会う", SW / 2, 740, f(L.SERIF, 76)); d = ImageDraw.Draw(img)
    rule(d, SW / 2, 880, 220)
    y = 930
    for ln in ["プロフィールの2つ目の固定投稿で、", "あなたのルナの性格と特徴を", "見てみてくださいね。"]:
        if ln: ctext(d, ln, SW / 2, y, f(L.SERIFM, 44), INK)
        y += 76
    L.gold_pill(img, (SW / 2 - 360, 1560, SW / 2 + 360, 1670), "固定投稿を見る ▶", f(L.SANSB, 40))
    return img

def hl_story_table(url=None):
    """27のルナ：早見表（白）"""
    img = constellations(paper(seed=11), [(1, 100, 1700, 1.4, 0.8), (3, 700, 1690, 1.3, 0.8)]); img = moon(img, 200, SW - 200, 230, 0.95); frame(img)
    L.gold_text(img, (120, 190), "27のルナ 早見表", f(L.SERIF, 84), shadow=(150, 118, 60)); d = ImageDraw.Draw(img)
    cols, cw, ch, x0, y0 = 3, 296, 118, 120, 380
    for i, n in enumerate(ORDER):
        r, c = divmod(i, cols); x, y = x0 + c * cw, y0 + r * ch
        d.text((x, y + 20), f"{n:>2}", font=f(L.SERIF, 46), fill=GOLD_D)
        d.text((x + 70, y + 30), NAMES[str(n)], font=f(L.SERIFM, 38), fill=INK)
        d.line([(x, y + ch - 10), (x + cw - 30, y + ch - 10)], fill=LINE, width=1)
    L.gold_pill(img, (SW / 2 - 360, 1560, SW / 2 + 360, 1670), "自分のルナを調べる ▶", f(L.SANSB, 40))
    return img

LINKS = {
    "01": "https://luna28.jp/about",
    "02": "https://luna28.jp/#trial",
    "03": "https://luna28.jp/about#about28",
    "03b": "https://www.instagram.com/luna28.japan/p/DfT0VErH797/",
    "04": "https://luna28.jp/about",
    "05": "https://luna28.jp/plan",
    "06": "https://www.amazon.co.jp/dp/4651781039",
}

HIGHLIGHTS = [
    ("01", "ルナ28とは", [("月の運行で決まるあなたの運勢", ["生まれた日の月の位置から、あなたのルナが決まります。", "全部で27種類あります。"], "自分のルナを調べる ▶")]),
    ("03", "27のルナ", "table"),
    ("04", "相性", [("ふたりのルナ番号でわかる相性", ["27×27＝729通り。", "恋人でも、友だちでも、職場の人でも。"], "まず自分のルナを調べる ▶")]),
    ("05", "会員になる", [("会員になると届くもの", ["毎日の運勢がメールで届く", "今月・今年の運勢、相性診断", "吉凶カレンダー", "宿命・才能・恋愛・金運・健康"], "月550円から ▶")]),
    ("06", "書籍", "book"),
]

def render(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for n, label, stories in HIGHLIGHTS:
        hl_cover(label).save(os.path.join(out_dir, f"hl{n}_cover_{label}.jpg"), quality=92)
        url = LINKS.get(n)
        if stories == "table":
            hl_story_table(url).save(os.path.join(out_dir, f"hl{n}_story1_{label}.jpg"), quality=92)
            hl_story_find(LINKS.get("03b")).save(os.path.join(out_dir, f"hl{n}_story2_{label}.jpg"), quality=92); continue
        if stories == "book":
            hl_story_book(url).save(os.path.join(out_dir, f"hl{n}_story1_{label}.jpg"), quality=92); continue
        for i, (t, lines, cta) in enumerate(stories, 1):
            hl_story(t, lines, cta, url=url).save(os.path.join(out_dir, f"hl{n}_story{i}_{label}.jpg"), quality=92)
    return sorted(os.listdir(out_dir))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True)
    print(render(ap.parse_args().out))
