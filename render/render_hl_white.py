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

def ctext(d, s, cx, y, font, fill):
    b = d.textbbox((0, 0), s, font=font); d.text((cx - (b[2] - b[0]) / 2, y), s, font=font, fill=fill)

def gold_c(img, s, cx, y, font):
    d = ImageDraw.Draw(img); b = d.textbbox((0, 0), s, font=font)
    L.gold_text(img, (int(cx - (b[2] - b[0]) / 2), int(y)), s, font, shadow=(150, 118, 60))

def rule(d, cx, y, half=200):
    d.line([(cx - half, y), (cx + half, y)], fill=GOLD, width=1); L.diamond(d, cx, y, 7, GOLD)

# ---------------------------------------------------------------- カバー（丸く切り抜かれる：中央700pxに収める）
def hl_cover(label):
    img = paper(seed=7); img = moon(img, 260, SW / 2, SH / 2 - 200)
    d = ImageDraw.Draw(img)
    d.ellipse([SW / 2 - 400, SH / 2 - 400, SW / 2 + 400, SH / 2 + 400], outline=GOLD, width=3)
    d.ellipse([SW / 2 - 386, SH / 2 - 386, SW / 2 + 386, SH / 2 + 386], outline=LINE, width=1)
    ctext(d, label, SW / 2, SH / 2 + 10, f(L.SERIF, 76 if len(label) <= 5 else 62), INK)
    rule(d, SW / 2, SH / 2 + 130, 120)
    return img

# ---------------------------------------------------------------- ストーリーズ
def hl_story(title, lines, cta=None, moon_size=520, url=None):
    img = paper(seed=9); img = moon(img, moon_size, SW / 2, 540); frame(img)
    gold_c(img, title, SW / 2, 900, f(L.SERIF, 84 if len(title) <= 8 else (66 if len(title) <= 12 else 58))); d = ImageDraw.Draw(img)
    rule(d, SW / 2, 1040, 220)
    y = 1090
    for ln in lines:
        for sub in V.wrap(ln, 18): ctext(d, sub, SW / 2, y, f(L.SERIFM, 44), INK); y += 76
        if not ln.endswith(("、", "を")): y += 24
    if cta: L.gold_pill(img, (SW / 2 - 360, 1560, SW / 2 + 360, 1670), cta, f(L.SANSB, 40))
    if url: ctext(ImageDraw.Draw(img), url, SW / 2, 1712, f(L.SERIFM, 30), SOFT)
    return img

def hl_story_book(url):
    """書籍『新占星術ルナ28』"""
    img = paper(seed=13); frame(img)
    # 本のイラスト（金の背・紫の表紙）
    d = ImageDraw.Draw(img)
    bx, by, bw, bh = SW / 2 - 210, 260, 420, 560
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([bx + 18, by + 30, bx + bw + 18, by + bh + 30], radius=12, fill=(120, 90, 140, 70))
    img = Image.alpha_composite(img.convert("RGBA"), sh.filter(ImageFilter.GaussianBlur(18))).convert("RGB"); d = ImageDraw.Draw(img)
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=10, fill=(78, 48, 120))
    d.rectangle([bx, by, bx + 26, by + bh], fill=GOLD)
    d.rounded_rectangle([bx + 50, by + 40, bx + bw - 30, by + bh - 40], radius=8, outline=GOLD, width=2)
    img = moon(img, 150, bx + bw / 2 + 12, by + 190, 0.95); d = ImageDraw.Draw(img)
    ctext(d, "新占星術", bx + bw / 2 + 12, by + 300, f(L.SERIF, 44), (255, 244, 220))
    ctext(d, "ルナ28", bx + bw / 2 + 12, by + 360, f(L.SERIF, 64), GOLD_L)
    ctext(d, "一冊であなたも占い師", bx + bw / 2 + 12, by + 460, f(L.SERIFM, 26), (226, 212, 236))
    gold_c(img, "書籍『新占星術ルナ28』", SW / 2, 920, f(L.SERIF, 66)); d = ImageDraw.Draw(img)
    rule(d, SW / 2, 1040, 220)
    y = 1090
    for ln in ["LUNA28のもとになった一冊。", "27のルナの性格・相性・運勢を、", "自分で読み解けるようになります。", "", "Amazon・楽天ブックスで探せます。"]:
        if ln: ctext(d, ln, SW / 2, y, f(L.SERIFM, 44), INK)
        y += 76
    L.gold_pill(img, (SW / 2 - 360, 1560, SW / 2 + 360, 1670), "書籍を見る ▶", f(L.SANSB, 40))
    ctext(ImageDraw.Draw(img), url, SW / 2, 1712, f(L.SERIFM, 30), SOFT)
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
    img = paper(seed=12); frame(img)
    for i, n in enumerate([1, 9, 15, 22, 28]):
        img = medallion(img, n, 170 + i * 185, 520, 160)
    gold_c(img, "番号が出たら", SW / 2, 740, f(L.SERIF, 84)); d = ImageDraw.Draw(img)
    rule(d, SW / 2, 880, 220)
    y = 930
    for ln in ["プロフィールの2つ目の固定投稿で、", "あなたのルナの性格と特徴を。", "", "1〜28のルナ（20はありません）、", "ひとりずつ載せています。"]:
        if ln: ctext(d, ln, SW / 2, y, f(L.SERIFM, 44), INK)
        y += 76
    L.gold_pill(img, (SW / 2 - 360, 1560, SW / 2 + 360, 1670), "固定投稿を見る ▶", f(L.SANSB, 40))
    if url: ctext(ImageDraw.Draw(img), url, SW / 2, 1712, f(L.SERIFM, 30), SOFT)
    return img

def hl_story_table(url=None):
    """27のルナ：早見表（白）"""
    img = paper(seed=11); img = moon(img, 200, SW - 200, 230, 0.95); frame(img)
    L.gold_text(img, (120, 190), "27のルナ 早見表", f(L.SERIF, 84), shadow=(150, 118, 60)); d = ImageDraw.Draw(img)
    cols, cw, ch, x0, y0 = 3, 296, 118, 120, 380
    for i, n in enumerate(ORDER):
        r, c = divmod(i, cols); x, y = x0 + c * cw, y0 + r * ch
        d.text((x, y + 20), f"{n:>2}", font=f(L.SERIF, 46), fill=GOLD_D)
        d.text((x + 70, y + 30), NAMES[str(n)], font=f(L.SERIFM, 38), fill=INK)
        d.line([(x, y + ch - 10), (x + cw - 30, y + ch - 10)], fill=LINE, width=1)
    L.gold_pill(img, (SW / 2 - 360, 1560, SW / 2 + 360, 1670), "自分のルナを調べる ▶", f(L.SANSB, 40))
    if url: ctext(ImageDraw.Draw(img), url, SW / 2, 1712, f(L.SERIFM, 30), SOFT)
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
    ("01", "ルナ28とは", [("月の位置で決まる27のルナ", ["生まれた日の月の位置から、あなたのルナが決まります。", "全部で27種類あります。"], "自分のルナを調べる ▶"),
                         ("2007年から、毎日", ["1200年以上前の経典をもとに、", "毎日の運勢・相性・月運・年運を", "届けています。"], None)]),
    ("02", "無料で調べる", [("調べ方は、これだけ", ["① プロフィールのリンクを開く", "② 生年月日を選ぶ", "③ 番号と性格が出る"], "30秒・登録不要 ▶")]),
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
