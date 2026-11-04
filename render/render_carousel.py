# -*- coding: utf-8 -*-
"""
カルーセル（27のルナ）: 1080x1350 JPEG を6枚書き出す。上品・余白多め・金の細線。
使い方:
  python3 render_carousel.py --json content/zukan_luna01.json --out out/carousel_luna01
JSON:
  {"no": 1, "name": "王の人", "catch": "恵まれた天運に導かれ、品格と知性を持って生きる星",
   "pages": [{"title": "性格", "lines": ["…", "…"]}, {"title": "恋愛", "lines": ["…"]},
             {"title": "仕事", "lines": ["…"]}, {"title": "相性", "good": ["7", "16"], "care": ["9", "22"]}],
   "cta": "あなたのルナは何番？"}
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import luna_style as L
import luna_video as V

W, H = 1080, 1350
f = L.f
# テーマC：生成り（和紙）× 墨 × 金
CREAM = (58, 48, 56)        # 本文＝墨
SOFT = (120, 104, 112)      # 補足＝薄墨
GOLD, GOLD_L = L.GOLD, L.GOLD_D   # 見出し金／小見出しは濃い金
PAPER = (247, 242, 232)
M = 96                      # 左右マージン

def bg(stars=0.0, seed=4, spots=None):
    """和紙の質感（細かいむら）"""
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (H // 4, W // 4)).astype(np.float32)
    n = np.asarray(Image.fromarray(np.clip(n * 40 + 128, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.2)), np.float32)
    arr = np.zeros((H, W, 3), np.float32)
    for i in range(3): arr[..., i] = PAPER[i] + (n - 128) * 0.10
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]; arr[..., 0] += t * 4; arr[..., 2] -= t * 6
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return constellations(img, ZOD_SPOTS if spots is None else spots)

ZOD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "content")
ZOD_SPOTS = [(5, 60, 110, 1.4, 0.75), (1, 80, 1190, 1.0, 0.7), (3, 820, 1170, 0.9, 0.7)]          # 左上＋下の両脇
ZOD_COVER = [(5, 60, 120, 1.4, 0.75), (10, 790, 150, 1.3, 0.7), (1, 80, 1190, 1.0, 0.7), (3, 820, 1170, 0.9, 0.7)]
ZOD_CTA = [(5, 60, 110, 1.4, 0.75), (10, 790, 120, 1.3, 0.7), (12, 60, 1120, 1.3, 0.7), (3, 800, 1160, 1.1, 0.7)]
def zodiac_layer(n, color=(196, 160, 80), alpha=0.7, scale=1.3):
    """星座線画（content/zodiac_NN.png）を薄い金で"""
    pth = os.path.join(ZOD_DIR, f"zodiac_{n:02d}.png")
    if not os.path.exists(pth): return None
    m = Image.open(pth).convert("L")
    m = m.resize((max(1, int(m.width * scale)), max(1, int(m.height * scale))), Image.LANCZOS)
    lay = Image.new("RGBA", m.size, color + (255,)); lay.putalpha(m.point(lambda a: int(a * alpha)))
    return lay

def constellations(img, spots):
    base = img.convert("RGBA")
    for n, x, y, sc, al in spots:
        lay = zodiac_layer(n, alpha=al, scale=sc)
        if lay is not None: base.alpha_composite(lay, (int(x), int(y)))
    return base.convert("RGB")

def hairline_frame(img):
    d = ImageDraw.Draw(img)
    d.rectangle([48, 48, W - 48, H - 48], outline=GOLD, width=2)
    d.rectangle([58, 58, W - 58, H - 58], outline=(222, 206, 160), width=1)

def moon_at(img, size, cx, cy, alpha=1.0):
    """明るい紙の上なので、にじみを外した円盤＋細い金の縁"""
    mo = L.moon(size); r = size * 0.24
    m = Image.new("L", mo.size, 0); ImageDraw.Draw(m).ellipse([size / 2 - r, size / 2 - r, size / 2 + r, size / 2 + r], fill=255)
    mo.putalpha(m.filter(ImageFilter.GaussianBlur(1.2)))
    ring = Image.new("RGBA", mo.size, (0, 0, 0, 0)); ImageDraw.Draw(ring).ellipse([size / 2 - r - 3, size / 2 - r - 3, size / 2 + r + 3, size / 2 + r + 3], outline=(212, 172, 92, 210), width=3)
    mo = Image.alpha_composite(ring, mo)
    if alpha < 1: mo.putalpha(mo.split()[3].point(lambda a: int(a * alpha)))
    base = img.convert("RGBA"); base.alpha_composite(mo, (int(cx - size / 2), int(cy - size / 2)))
    return base.convert("RGB")

def ctext(d, text, cx, y, font, fill):
    b = d.textbbox((0, 0), text, font=font); d.text((cx - (b[2] - b[0]) / 2, y), text, font=font, fill=fill)

def gold_c(img, text, cx, y, font):
    d = ImageDraw.Draw(img); b = d.textbbox((0, 0), text, font=font)
    L.gold_text(img, (int(cx - (b[2] - b[0]) / 2), int(y)), text, font)

def rule(d, x0, x1, y, col=GOLD):
    d.line([(x0, y), (x1, y)], fill=col, width=1)
    L.diamond(d, (x0 + x1) / 2, y, 7, col)

def header(d, spec):
    ctext(d, f"27のルナ　｜　{spec['no']}のルナ　{spec['name']}", W / 2, 92, f(L.SERIFM, 28), GOLD_L)

CHARS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "content", "chars")
def medallion(img, n, cx, cy, dia):
    """キャラ（白い丸）＋金の縁。無ければ何もしない"""
    pth = os.path.join(CHARS, f"{int(n):02d}_med.png")
    if not os.path.exists(pth): return img
    med = Image.open(pth).convert("RGBA").resize((dia, dia), Image.LANCZOS)
    base = img.convert("RGBA")
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse([cx - dia / 2 + 3, cy - dia / 2 + 10, cx + dia / 2 + 3, cy + dia / 2 + 10], fill=(90, 70, 60, 70))
    base = Image.alpha_composite(base, sh.filter(ImageFilter.GaussianBlur(10)))
    base.alpha_composite(med, (int(cx - dia / 2), int(cy - dia / 2)))
    d = ImageDraw.Draw(base); d.ellipse([cx - dia / 2, cy - dia / 2, cx + dia / 2, cy + dia / 2], outline=GOLD, width=3)
    d.ellipse([cx - dia / 2 - 7, cy - dia / 2 - 7, cx + dia / 2 + 7, cy + dia / 2 + 7], outline=(222, 206, 160), width=1)
    return base.convert("RGB")

def footer(img, n, total):
    d = ImageDraw.Draw(img)
    for i in range(total):
        cx = W / 2 - (total - 1) * 13 + i * 26
        d.ellipse([cx - 4, 1288 - 4, cx + 4, 1288 + 4], fill=GOLD if i == n else (222, 206, 160))

def page_cover(spec, total):
    img = bg(spots=ZOD_COVER); hairline_frame(img)
    has_char = os.path.exists(os.path.join(CHARS, f"{int(spec['no']):02d}_med.png"))
    if has_char:
        img = medallion(img, spec["no"], W / 2, 400, 600)
    else:
        img = moon_at(img, 520, W / 2, 400)
    d = ImageDraw.Draw(img)
    ctext(d, "27 の ル ナ", W / 2, 92, f(L.SERIFM, 28), GOLD_L)
    num = str(spec["no"]); fn = f(L.SERIF, 190 if len(num) == 1 else 165); fs = f(L.SERIFM, 44)
    bw = d.textbbox((0, 0), num, font=fn)[2]; sw = d.textbbox((0, 0), "のルナ", font=fs)[2]
    x0 = W / 2 - (bw + 18 + sw) / 2
    gold_c(img, num, x0 + bw / 2, 720, fn); d = ImageDraw.Draw(img)
    d.text((x0 + bw + 18, 720 + fn.size * 0.72), "のルナ", font=fs, fill=CREAM)
    ctext(d, f"『{spec['name']}』", W / 2, 950, f(L.SERIFM, 60), GOLD_L)
    rule(d, W / 2 - 200, W / 2 + 200, 1055)
    for i, ln in enumerate(V.wrap(spec["catch"], 22)):
        ctext(d, ln, W / 2, 1085 + i * 52, f(L.SERIFM, 34), CREAM)
    footer(img, 0, total); return img

def title_block(img, title):
    """見出し（中央）＋飾り罫"""
    gold_c(img, title, W / 2, 190, f(L.SERIF, 100)); d = ImageDraw.Draw(img)
    rule(d, W / 2 - 220, W / 2 + 220, 335)

def page_text(spec, page, n, total):
    img = bg(); img = moon_at(img, 300, W - 190, 190, alpha=0.55); hairline_frame(img)
    d = ImageDraw.Draw(img); header(d, spec)
    title_block(img, page["title"]); d = ImageDraw.Draw(img)
    y = 400
    for ln in page["lines"]:
        for sub in V.wrap(ln, 21):
            ctext(d, sub, W / 2, y, f(L.SERIFM, 42), CREAM); y += 70
        y += 34
    footer(img, n, total); return img

def page_match(spec, page, n, total):
    img = bg(); img = moon_at(img, 300, W - 190, 190, alpha=0.55); hairline_frame(img)
    d = ImageDraw.Draw(img); header(d, spec)
    title_block(img, "相性"); d = ImageDraw.Draw(img)
    def block(y, title, nums, col):
        ctext(d, title, W / 2, y, f(L.SERIFM, 36), col)
        k = len(nums); sw = d.textbbox((0, 0), "のルナ", font=f(L.SERIFM, 32))[2]
        tot = k * 180 + (k - 1) * 30 + 14 + sw; x = W / 2 - tot / 2
        for nm in nums:
            d.rounded_rectangle([x, y + 70, x + 180, y + 200], radius=18, outline=GOLD, width=2)
            gold_c(img, str(nm), x + 90, y + 82, f(L.SERIF, 82)); x += 210
        ImageDraw.Draw(img).text((x - 30 + 14, y + 140), "のルナ", font=f(L.SERIFM, 32), fill=CREAM)
    block(400, "理想の異性　1位", page.get("good", []), GOLD_L)
    block(690, "避けたい異性　1位", page.get("care", []), SOFT)
    d = ImageDraw.Draw(img)
    lines = ([page["note"]] if page.get("note") else []) + ["2位以下と、ふたりの番号での相性診断は会員ページで。"]
    for i, ln in enumerate(lines):
        ctext(d, ln, W / 2, 970 + i * 56, f(L.SERIFM, 30), SOFT)
    footer(img, n, total); return img

def page_cta(spec, n, total):
    img = bg(spots=ZOD_CTA); img = moon_at(img, 640, W / 2, 360); hairline_frame(img)
    d = ImageDraw.Draw(img)
    ctext(d, "生年月日だけで決まる", W / 2, 720, f(L.SERIFM, 44), CREAM)
    gold_c(img, spec.get("cta", "あなたのルナは何番？"), W / 2, 785, f(L.SERIF, 88)); d = ImageDraw.Draw(img)
    rule(d, W / 2 - 200, W / 2 + 200, 925)
    ctext(d, "登録不要・無料・30秒", W / 2, 955, f(L.SERIFM, 36), CREAM)
    L.gold_pill(img, (W / 2 - 320, 1030, W / 2 + 320, 1130), "プロフィールのリンクから ▶", f(L.SANSB, 36))
    footer(img, n, total); return img

def render(spec, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    pages = spec["pages"]; total = len(pages) + 2
    imgs = [page_cover_photo(spec, total) if spec.get("cover_photo") else page_cover(spec, total)]
    for i, pg in enumerate(pages):
        if "photo" in pg: imgs.append(page_photo(spec, pg, i + 1, total))
        elif pg.get("title") == "相性": imgs.append(page_match(spec, pg, i + 1, total))
        else: imgs.append(page_text(spec, pg, i + 1, total))
    imgs.append(page_cta(spec, total - 1, total))
    files = []
    for i, im in enumerate(imgs):
        p = os.path.join(out_dir, f"{i + 1:02d}.jpg"); im.save(p, "JPEG", quality=92, optimize=True); files.append(p)
    return files


# ---------------------------------------------------------------- 実写を混ぜるページ
def _photo_fill(path, w, h):
    """写真をカバー配置（中央トリミング）。無ければ朝焼けの描画背景で代用"""
    if path and os.path.exists(path):
        im = Image.open(path).convert("RGB"); k = max(w / im.width, h / im.height)
        im = im.resize((int(im.width * k) + 1, int(im.height * k) + 1), Image.LANCZOS)
        x0, y0 = (im.width - w) // 2, (im.height - h) // 2
        return im.crop((x0, y0, x0 + w, y0 + h))
    return V.dawn_sky(w, h, horizon=0.78)

def page_cover_photo(spec, total):
    """表紙を実写に：写真の下1/3を生成りに溶かして、番号と名前を置く"""
    img = _photo_fill(spec.get("cover_photo"), W, H)
    paper = bg()
    a = np.zeros((H, 1), np.float32); yy = np.arange(H, dtype=np.float32)
    a[:, 0] = np.clip((yy - H * 0.52) / (H * 0.26), 0, 1)             # 0.52〜0.78 で紙に溶ける
    mask = Image.fromarray((np.repeat(a, W, axis=1) * 255).astype(np.uint8))
    img = Image.composite(paper, img, mask)
    d = ImageDraw.Draw(img)
    d.rectangle([48, 48, W - 48, H - 48], outline=(255, 250, 240), width=2)
    ctext(d, "27 の ル ナ", W / 2, 92, f(L.SERIFM, 28), (255, 250, 240))
    num = str(spec["no"]); fn = f(L.SERIF, 200); bw = d.textbbox((0, 0), num, font=fn)[2]
    gold_c(img, num, W / 2 - 40, 840, fn); d = ImageDraw.Draw(img)
    d.text((W / 2 - 40 + bw / 2 + 18, 840 + fn.size * 0.72), "のルナ", font=f(L.SERIFM, 44), fill=CREAM)
    ctext(d, f"『{spec['name']}』", W / 2, 1090, f(L.SERIFM, 56), GOLD_L)
    rule(d, W / 2 - 200, W / 2 + 200, 1180)
    footer(img, 0, total); return img

def page_photo(spec, page, n, total):
    """中ページの実写：写真の上に細い白枠、下に生成りの帯でひとこと"""
    img = _photo_fill(page.get("photo"), W, H)
    band_h = 330; paper = bg().crop((0, H - band_h, W, H))
    img.paste(paper, (0, H - band_h))
    d = ImageDraw.Draw(img)
    d.line([(0, H - band_h), (W, H - band_h)], fill=GOLD, width=2)
    d.rectangle([48, 48, W - 48, H - band_h - 30], outline=(255, 250, 240), width=2)
    if page.get("title"): d.text((M, H - band_h + 34), page["title"], font=f(L.SERIFM, 32), fill=L.GOLD_D)
    y = H - band_h + 84
    for ln in V.wrap(page.get("text", ""), 25)[:2]:
        d.text((M, y), ln, font=f(L.SERIFM, 34), fill=CREAM); y += 52
    footer(img, n, total); return img

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--json", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    print(render(json.load(open(a.json, encoding="utf-8")), a.out))
