# -*- coding: utf-8 -*-
"""固定投稿3本（改訂版・朝焼けテーマ）
  投稿1: あなたのルナは何番？（1枚）
  投稿2: 27のルナ早見表 → あなたはこんな人（2ルナ/枚 ×14）→ ルナは、どう決まる？（計16枚）
  投稿3: 会員になると（表紙）→ 届くものを1枚ずつ（計7枚）
  ・左上のブランド表記、中央下の@表記はすべて無し
  python3 render_fixed2.py --out out/fixed_v2
"""
import argparse, os, sys, json, math
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import luna_style as L
import luna_video as V

f = L.f
W, H = 1080, 1350
INK, SOFT, GOLD_D = (255, 252, 246), (255, 242, 222), (255, 236, 196)
LINE = (255, 246, 230); SHADOW = (70, 40, 100); GOLD = L.GOLD
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMES = json.load(open(os.path.join(ROOT, "content", "luna_names.json"), encoding="utf-8"))
ORDER = [n for n in range(1, 29) if n != 20]

# ---------------------------------------------------------------- 基本部品
ZOD_SPOTS = [(5, 80, 66, 1.35, 0.55), (10, 790, 390, 1.25, 0.5), (3, 90, 1130, 1.2, 0.5)]
def zodiac_layer(n, color=(255, 240, 210), alpha=0.5, scale=1.3):
    """ユーザー提供の星座線画（content/zodiac_NN.png）を薄い生成り色で"""
    m = Image.open(os.path.join(ROOT, "content", f"zodiac_{n:02d}.png")).convert("L")
    m = m.resize((max(1, int(m.width * scale)), max(1, int(m.height * scale))), Image.LANCZOS)
    lay = Image.new("RGBA", m.size, color + (255,)); lay.putalpha(m.point(lambda a: int(a * alpha)))
    return lay

def paper(seed=4, horizon=0.80, spots=None):
    img = V.dawn_sky(W, H, horizon=horizon, seed=seed).convert("RGBA")
    for n, x, y, sc, al in (ZOD_SPOTS if spots is None else spots):
        img.alpha_composite(zodiac_layer(n, alpha=al, scale=sc), (int(x), int(y)))
    return img.convert("RGB")

def frame(img, inset=48):
    ImageDraw.Draw(img).rectangle([inset, inset, W - inset, H - inset], outline=LINE, width=2)

def panel(img, box, alpha=120, radius=26, outline=True):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle(box, radius=radius, fill=(60, 36, 96, alpha), outline=(255, 240, 210, 110) if outline else None, width=1)
    return Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")

def band(img, y0, y1, amax=0.40):
    yy = np.arange(H, dtype=np.float32); c0, c1 = y0 + (y1 - y0) * 0.3, y1 - (y1 - y0) * 0.3
    a = np.where(yy < y0, 0, np.where(yy < c0, (yy - y0) / (c0 - y0), np.where(yy < c1, 1, np.where(yy < y1, (y1 - yy) / (y1 - c1), 0))))
    lay = Image.new("RGBA", (W, H), (60, 36, 96, 0)); lay.putalpha(Image.fromarray((np.repeat(a[:, None], W, axis=1) * 255 * amax).astype(np.uint8)))
    return Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")

def text(d, xy, s, font, fill):
    d.text((xy[0] + 3, xy[1] + 3), s, font=font, fill=SHADOW); d.text(xy, s, font=font, fill=fill)

def ctext(d, s, cx, y, font, fill):
    b = d.textbbox((0, 0), s, font=font); text(d, (cx - (b[2] - b[0]) / 2, y), s, font, fill)

def gold_c(img, s, cx, y, font):
    d = ImageDraw.Draw(img); b = d.textbbox((0, 0), s, font=font); L.gold_text(img, (int(cx - (b[2] - b[0]) / 2), int(y)), s, font)

def rule(d, cx, y, half=200):
    d.line([(cx - half, y), (cx + half, y)], fill=GOLD, width=1); L.diamond(d, cx, y, 7, GOLD)

def moon(img, size, cx, cy, alpha=1.0):
    mo = L.moon(size)
    if alpha < 1: mo.putalpha(mo.split()[3].point(lambda a: int(a * alpha)))
    base = img.convert("RGBA"); base.alpha_composite(mo, (int(cx - size / 2), int(cy - size / 2))); return base.convert("RGB")

def pager(d, n, total):
    ctext(d, f"{n} / {total}", W / 2, 1262, f(L.SERIFM, 24), SOFT)

# ================================================================ 投稿1
def pin1():
    img = paper(seed=4, horizon=0.78); img = moon(img, 560, W / 2, 400); img = band(img, 700, 1250, 0.40); frame(img)
    d = ImageDraw.Draw(img)
    ctext(d, "生年月日で決まる、27のルナ", W / 2, 760, f(L.SERIFM, 46), INK)
    gold_c(img, "あなたのルナは何番？", W / 2, 835, f(L.SERIF, 92)); d = ImageDraw.Draw(img)
    rule(d, W / 2, 960, 220)
    ctext(d, "性格・相性・宿命・今日の運勢もすべて網羅。", W / 2, 995, f(L.SERIFM, 38), INK)
    L.gold_pill(img, (W / 2 - 340, 1085, W / 2 + 340, 1190), "無料・30秒・プロフィールのリンクから", f(L.SANSB, 34))
    ctext(d, "番号がわかったら、2つ目の固定投稿で自分のルナを見てみてください", W / 2, 1222, f(L.SERIFM, 28), SOFT)
    return img

# ================================================================ 投稿2
def p2_table(total):
    img = paper(seed=4); img = moon(img, 220, W - 170, 170, 0.9); img = panel(img, (72, 300, W - 72, 1180)); frame(img)
    d = ImageDraw.Draw(img)
    L.gold_text(img, (96, 160), "27のルナ 早見表", f(L.SERIF, 80)); d = ImageDraw.Draw(img)
    text(d, (100, 262), "※ 20番はありません。1〜28で27のルナです", f(L.SERIFM, 26), SOFT)
    cols, cw, ch, x0, y0 = 3, 296, 92, 96, 330
    for i, n in enumerate(ORDER):
        r, c = divmod(i, cols); x, y = x0 + c * cw, y0 + r * ch
        text(d, (x, y + 14), f"{n:>2}", f(L.SERIF, 40), GOLD_D)
        text(d, (x + 64, y + 22), NAMES[str(n)], f(L.SERIFM, 34), INK)
        d.line([(x, y + ch - 6), (x + cw - 30, y + ch - 6)], fill=LINE, width=1)
    ctext(d, "番号がわかったら、次のページから自分のルナを探してください", W / 2, 1195, f(L.SERIFM, 30), SOFT)
    pager(d, 1, total); return img

# 性格（シート「性質」原文）／宿命（シート「天運」原文）からの抜粋
PERSON = {
 1: ["品がよくお洒落な交際上手。会話もうまく聞き上手", "知的な分野に高い関心を持つ生まれ", "財より名誉に憧れ、学問や芸術を好む"],
 2: ["善良で聡明。正義感や責任感も強い", "物事に動じず、孤独にも強い精神力の持ち主", "高い理想を努力により実現する底力がある"],
 3: ["礼儀正しく正直。感情も豊かで飾り気がない", "本質的に数に強く、お金に関して先を読む能力", "見かけはおだやかでも、心の中には激しい闘争心"],
 4: ["陽気な目立ちたがり屋。根が正直で人気者になる", "常に新しいものを追い求めていく活動家", "誰も思いつかないアイデアを発想する創造力"],
 5: ["弱い立場の人に手を差し伸べる優しさがある", "人の役に立ちたい気持ちと、直感力を備える", "生真面目さと完璧主義で独自の世界を築く"],
 6: ["明るく陽気で楽しい会話もできる社交家", "好奇心旺盛な勉強家で、知識や知恵を身につける", "アイデア力の持ち主。働き者ではトップクラス"],
 7: ["損得ぬきで人のお世話をする、涙もろく心優しい人", "我が道を貫く生まれ", "生涯を通じてある種の強運に恵まれる"],
 8: ["明るく話し好きで気取ったところがない", "真面目で義理堅いが、本心を表現するのは苦手", "信念や目標を持ち続ける力。土地と縁が深い"],
 9: ["気位が高く負けず嫌い。自信ありげに振舞う", "自分を演出でき、有力者に自分を売り込める", "周囲の力を自分のために活かすことができる"],
 10: ["人と争うことが嫌いな平和主義者", "徳が高く実力もあり、恵まれた人生はトップクラス", "ご先祖にも見守られている"],
 11: ["心根の優しい人。相手の気持ちを素早く察する", "精神的に大変純粋な面を持つ生まれ", "物事の本質を見抜く知恵者"],
 12: ["物腰が柔らかで気配りも大変よくできる", "内面は意外と頑固で一本気", "手先の器用さは、まさにトップ中のトップ"],
 13: ["何事も一度は反対しないと気が済まない", "裏表のないまっすぐな性格", "信念を貫き通す意志の力はトップクラス"],
 14: ["話題が豊富で話し上手。年齢を問わず好かれる", "信念を貫き通す強さはトップクラス", "世の人々に喜ばれる物を創造したいという志"],
 15: ["常識もあり気配りもでき、人あたりも柔らか", "本当はワンマンで苦労知らず", "頭が切れて学問好き。遊びにも仕事にも大胆"],
 16: ["気さくで愛嬌があり、頼られ好かれる", "多くの人に愛される生まれ", "遊び好きで多芸多才"],
 17: ["自分の世界を大切にする繊細な感情の持ち主", "好きな事柄には驚くほどの力を発揮する", "努力家で仕事熱心。緻密さもある"],
 18: ["心根が優しく、見栄は張らないが派手に見られがち", "自立を好む生まれ。商売の勘が大変鋭い", "他人のために働くことで財を生む"],
 19: ["穏やかな印象と違い、自尊心が強く大変な負けず嫌い", "人生の幸運度が高い生まれ", "鋭い直感力や洞察力、美的感覚や器用さ"],
 21: ["身近な人を大切にし、きめ細かい心配りができる", "自分にも他人にも大変厳しい", "誰も思いつかないようなアイデア力がある"],
 22: ["何事もじっくりと考えた上で行動に移す", "プライドは高め。同じくらい臆病な面も", "一種独特の精神世界を備えた生まれ"],
 23: ["陽気でさっぱりした性格と理性的な雰囲気", "頼られると損をしてでも親切にする優しさ", "つきあいの良さは誰にも負けない。アイデアマン"],
 24: ["明るく陽気で社交的。派手好きな目立ちたがり屋", "活動的で高級志向", "エネルギッシュな働き者で度胸も備わる"],
 25: ["目立つことを好まない真面目な人", "人物や物事を冷静に観察する能力がある", "有力者に引き立てられ、片腕や相談役として活躍"],
 26: ["楽しいことが大好きで話題も豊富", "知的なことに対する好奇心が旺盛", "趣味と仕事がうまくリンクしやすい"],
 27: ["周囲を楽しくできる人。内面は大変複雑", "アイデアマンで多芸多才", "独自の世界を築くことができる天運を持つ"],
 28: ["少々短気でせっかちだが、陽気でユーモアも備わる", "干渉するのもされるのも大嫌い", "これだと思った事柄だけを猛烈に追求する"],
}
CATCH = {int(k): v["catch"] for k, v in json.load(open(os.path.join(ROOT, "content", "luna_data.json"), encoding="utf-8")).items()}
# キャッチの改行位置（意味の切れ目で割る）
CATCH_BREAK = {
 1: ["生涯天から恵みを受けられる", "気位の高い人"], 2: ["体力・精神力全てにおいて", "最強を誇る人"],
 3: ["数に強く、自力で財を築く", "ことができる粘り強い人"], 4: ["先取り精神で常に", "新しいものを追い求める人"],
 5: ["素晴らしい頭脳を持っている", "真面目な仕事人"], 6: ["何をするにも誰よりも早くと", "考える即行動の人"],
 7: ["備わった運の磨き方によって", "人生が決まる人"], 8: ["不思議な魅力の持ち主で", "土地にも縁がある人"],
 9: ["会話で人を引き付ける", "才能を持つ魅力的な人"], 10: ["海外や乗り物に縁が深く", "旅行も好きな人"],
 11: ["精神的にとても純粋な面がある", "心優しい人"], 12: ["手先が器用で", "おつきあいもとても上手な人"],
 13: ["何かにつけて逆らうことが多い", "正義の人"], 14: ["愛嬌の良さと", "信念を貫く力を持っている人"],
 15: ["自然に財が集まる", "豊かな財運を持っている人"], 16: ["笑顔を絶やさず", "誰とでも気軽につき合える人"],
 17: ["目標に対する粘り強さは、", "まさに獲物を狙う狩人"], 18: ["派手なことは好まないのに", "なぜか目立ってしまう人"],
 19: ["理想が高いほど開運となる", "不屈の精神の持ち主"], 21: ["心の底に燃えるような", "野心を抱いている人"],
 22: ["独特の精神世界を持ち、", "心を見抜く感も鋭い人"], 23: ["常に今より新しいものを", "追い求め続ける人"],
 24: ["生きることに貪欲で、", "豪快かつ度胸もある人"], 25: ["人のお世話をすることで", "大きな開運となる人"],
 26: ["多彩な趣味に生きる", "根っからの自由人"], 27: ["数字に強く、", "何事も手際よくこなせる人"],
 28: ["全ての判断基準は自分にある", "好奇心旺盛な人"],
}

CHARS = os.path.join(ROOT, "content", "chars")
def medallion(img, n, cx, cy, dia):
    """キャラ（白い丸）＋金の縁。content/chars/NN_med.png"""
    p = os.path.join(CHARS, f"{n:02d}_med.png")
    if not os.path.exists(p): return img
    med = Image.open(p).convert("RGBA").resize((dia, dia), Image.LANCZOS)
    base = img.convert("RGBA")
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse([cx - dia / 2 + 4, cy - dia / 2 + 10, cx + dia / 2 + 4, cy + dia / 2 + 10], fill=(40, 20, 70, 90))
    base = Image.alpha_composite(base, sh.filter(ImageFilter.GaussianBlur(10)))
    base.alpha_composite(med, (int(cx - dia / 2), int(cy - dia / 2)))
    d = ImageDraw.Draw(base); d.ellipse([cx - dia / 2, cy - dia / 2, cx + dia / 2, cy + dia / 2], outline=GOLD, width=3)
    d.ellipse([cx - dia / 2 - 6, cy - dia / 2 - 6, cx + dia / 2 + 6, cy + dia / 2 + 6], outline=(255, 240, 210), width=1)
    return base.convert("RGB")

def luna_block(img, y0, n):
    """1ルナ分（右上にキャラの丸）。描いた高さを返す"""
    DIA = 220
    catch = CATCH[n].rstrip("。"); cl = CATCH_BREAK.get(n) or V.wrap(catch, 15)
    body = [V.wrap(ln, 24) for ln in PERSON[n]]
    head = max(150 + 50 * len(cl), DIA + 40)
    h = head + 20 + 22 + sum(48 * len(b) + 14 for b in body) + 20
    img = panel(img, (72, y0, W - 72, y0 + h), alpha=118)
    img = medallion(img, n, W - 72 - 24 - DIA / 2, y0 + 24 + DIA / 2, DIA)
    d = ImageDraw.Draw(img)
    L.gold_text(img, (104, y0 + 22), f"{n}", f(L.SERIF, 96)); d = ImageDraw.Draw(img)
    nx = 104 + (120 if n >= 10 else 70)
    text(d, (nx, y0 + 58), "のルナ", f(L.SERIFM, 34), GOLD_D)
    text(d, (nx + 128, y0 + 34), NAMES[str(n)], f(L.SERIF, 64), INK)
    for j, ln in enumerate(cl):
        text(d, (104, y0 + 150 + j * 50), ln, f(L.SERIFM, 34), GOLD_D)
    y = y0 + head + 20
    d.line([(104, y), (W - 104, y)], fill=LINE, width=1); y += 22
    for subs in body:
        L.diamond(d, 118, y + 24, 8)
        for k, s_ in enumerate(subs):
            text(d, (146, y + k * 48), s_, f(L.SERIFM, 34), INK)
        y += 48 * len(subs) + 14
    return img, h

def p2_person(pair, idx, total):
    img = paper(seed=5 + idx); frame(img)
    d = ImageDraw.Draw(img); ctext(d, "27のルナ　あなたはこんな人", W / 2, 96, f(L.SERIFM, 34), GOLD_D)
    img, h1 = luna_block(img, 160, pair[0])
    if len(pair) > 1:
        img, h2 = luna_block(img, 160 + h1 + 36, pair[1])
    else:
        y = 160 + h1 + 36
        img = moon(img, 220, W / 2, y + 130, 0.95); img = band(img, 940, 1250, 0.42)
        gold_c(img, "あなたのルナは何番？", W / 2, 975, f(L.SERIF, 72))
        L.gold_pill(img, (W / 2 - 320, 1090, W / 2 + 320, 1180), "無料で調べる ▶ プロフィールのリンク", f(L.SANSB, 30))
    pager(ImageDraw.Draw(img), idx, total); return img

def p2_how(total):
    img = paper(seed=4); img = moon(img, 560, W / 2, 340); img = band(img, 620, 1260, 0.42); frame(img)
    gold_c(img, "ルナは、どう決まる？", W / 2, 690, f(L.SERIF, 84)); d = ImageDraw.Draw(img)
    rule(d, W / 2, 820, 220)
    ctext(d, "生まれた日の、月の位置で決まります。", W / 2, 860, f(L.SERIFM, 40), INK)
    for i, ln in enumerate(["生年月日を昔の暦（旧暦）に直して、", "その日に月がいた場所が、あなたのルナ。", "だから同じ星座の人でも、ルナは違います。"]):
        ctext(d, ln, W / 2, 940 + i * 64, f(L.SERIFM, 34), SOFT)
    L.gold_pill(img, (W / 2 - 320, 1150, W / 2 + 320, 1240), "自分のルナを調べる ▶", f(L.SANSB, 34))
    pager(ImageDraw.Draw(img), total, total); return img

def post2():
    pairs = [ORDER[i:i + 2] for i in range(0, len(ORDER), 2)]      # 14枚（最後は27・28）
    total = 1 + len(pairs) + 1
    pages = [p2_table(total)] + [p2_person(p, i + 2, total) for i, p in enumerate(pairs)] + [p2_how(total)]
    return pages

# ================================================================ 投稿3
def p3_cover(total):
    img = paper(seed=4); img = moon(img, 300, W - 190, 190, 0.85); img = panel(img, (72, 375, W - 72, 955)); img = band(img, 950, 1250, 0.42); frame(img)
    d = ImageDraw.Draw(img)
    text(d, (96, 170), "会員になると", f(L.SERIFM, 44), INK)
    L.gold_text(img, (96, 230), "毎日、運勢が届く", f(L.SERIF, 84)); d = ImageDraw.Draw(img)
    d.line([(96, 350), (W - 96, 350)], fill=GOLD, width=1)
    items = [("今日の運勢", "毎朝、メールで"), ("今月の運勢・今年の運勢", "月ごと、年ごとの流れ"), ("相性診断", "ふたりのルナ番号で、何度でも"), ("吉凶カレンダー", "1か月の吉凶が一目で"), ("自分のルナを、くわしく", "宿命・天運・才能・適職・恋愛・結婚・金運・健康")]
    y = 395
    for t, s in items:
        L.diamond(d, 120, y + 26, 10)
        text(d, (150, y), t, f(L.SERIFM, 38), INK); text(d, (150, y + 50), s, f(L.SERIFM, 28), SOFT); y += 112
    rule(d, W / 2, 975, 300)
    ctext(d, "プレミアム会員　月550円から", W / 2, 1000, f(L.SERIFM, 40), GOLD_D)
    ctext(d, "2007年から続く宿曜占星術 LUNA28", W / 2, 1060, f(L.SERIFM, 28), SOFT)
    L.gold_pill(img, (W / 2 - 300, 1115, W / 2 + 300, 1205), "次のページで、くわしく ▶", f(L.SANSB, 30))
    pager(ImageDraw.Draw(img), 1, total); return img

def p3_base(title, sub, lines, idx, total, seed):
    img = paper(seed=seed, horizon=0.82); img = band(img, 60, 420, 0.40); img = band(img, 880, 1300, 0.46); frame(img)
    d = ImageDraw.Draw(img)
    ctext(d, sub, W / 2, 120, f(L.SERIFM, 32), GOLD_D)
    gold_c(img, title, W / 2, 170, f(L.SERIF, 84 if len(title) <= 8 else 64)); d = ImageDraw.Draw(img)
    rule(d, W / 2, 310, 240)
    y = 930
    for ln in lines:
        for s in V.wrap(ln, 22):
            ctext(d, s, W / 2, y, f(L.SERIFM, 36), INK); y += 58
        y += 12
    return img

def phone_card(img, box, title):
    """画面イメージ：角丸カード＋見出し＋文章を示す横線"""
    x0, y0, x1, y1 = box
    img = panel(img, box, alpha=150, radius=36)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0 + 6, y0 + 6, x1 - 6, y1 - 6], radius=32, outline=(255, 236, 196), width=1)
    text(d, (x0 + 44, y0 + 36), title, f(L.SERIFM, 34), GOLD_D)
    d.line([(x0 + 44, y0 + 96), (x1 - 44, y0 + 96)], fill=LINE, width=1)
    return img, d

# ---- 吉凶カレンダーの実際のマーク（luna28.jp/lucky_calendar の icon01〜09 の形状を再現）
MARK_OUT = (180, 143, 109)      # サイト: #b48f6d（枠線のマーク）
MARK_FILL = (28, 22, 36)        # サイト: 黒（塗りのマーク）
MARKS = [("star_o", "最大級のラッキーday"), ("dcircle", "ラッキーday"), ("square_o", "良い日"), ("tri_o", "やや良い日"),
         ("bracket", "平穏な日"), ("tri_f", "やや悪い日"), ("square_f", "悪い日"), ("circle_f", "小さなアンラッキーday"), ("star_f", "アンラッキーday")]
# サイト掲載サンプル（2019年1月）の実データ：日→マーク番号
SAMPLE_201901 = [6,5,7,3,9,4,4,8,2,6,5,7,3,9,4,4,1,2,6,5,7,3,9,4,4,8,2,6,5,3,9]

def star_pts(cx, cy, r):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5; rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    return pts

def mark(d, kind, cx, cy, s, out=MARK_OUT, fill=MARK_FILL, lw=3):
    if kind == "star_o": d.polygon(star_pts(cx, cy, s), outline=out, width=lw)
    elif kind == "star_f": d.polygon(star_pts(cx, cy, s), fill=fill)
    elif kind == "dcircle":
        d.ellipse([cx - s, cy - s, cx + s, cy + s], outline=out, width=lw - 1); r2 = s * 0.56
        d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], outline=out, width=lw - 1)
    elif kind == "square_o": d.rectangle([cx - s * .85, cy - s * .85, cx + s * .85, cy + s * .85], outline=out, width=lw)
    elif kind == "square_f": d.rectangle([cx - s * .85, cy - s * .85, cx + s * .85, cy + s * .85], fill=fill)
    elif kind == "tri_o": d.polygon([(cx, cy - s), (cx + s * 1.1, cy + s * .85), (cx - s * 1.1, cy + s * .85)], outline=out, width=lw)
    elif kind == "tri_f": d.polygon([(cx, cy + s), (cx + s * 1.1, cy - s * .85), (cx - s * 1.1, cy - s * .85)], fill=fill)
    elif kind == "circle_f": d.ellipse([cx - s, cy - s, cx + s, cy + s], fill=fill)
    elif kind == "bracket":
        t = max(2, int(s * .18)); L_ = s * 1.5; h = s * .9
        d.rectangle([cx - L_, cy - h, cx - L_ + t, cy + h], fill=fill); d.rectangle([cx - L_, cy - h, cx - L_ + s * .5, cy - h + t], fill=fill); d.rectangle([cx - L_, cy + h - t, cx - L_ + s * .5, cy + h], fill=fill)
        d.rectangle([cx + L_ - t, cy - h, cx + L_, cy + h], fill=fill); d.rectangle([cx + L_ - s * .5, cy - h, cx + L_, cy - h + t], fill=fill); d.rectangle([cx + L_ - s * .5, cy + h - t, cx + L_, cy + h], fill=fill)
        d.rectangle([cx - s * .65, cy - t / 2, cx + s * .65, cy + t / 2], fill=fill)

def cream_card(img, box, radius=32):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
    dd.rounded_rectangle(box, radius=radius, fill=(250, 245, 238, 238), outline=(255, 236, 196, 255), width=2)
    img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB"); return img, ImageDraw.Draw(img)

DARK = (60, 40, 80); DARK2 = (120, 96, 140)
TODAY_TEXT = {
  "date": "1月1日（火）", "luna": "1のルナ", "rank": "最大級のラッキーday",
  "sections": [
    ("今日の幸運度", ["年に十数日しかない、最上級の吉日。新しい着手、買い物、贈り物に吉。"]),
    ("注意点", ["思い通りにならない時、攻撃的で感情的な言動にならないように。"]),
    ("開運のための心がけ", ["今の自分があるのは周囲のおかげ、という謙虚な気持ちを感謝の言動に。"]),
  ]
}

def veil(img, box, blur=14, label="続きは、毎朝のメールで"):
    """カードの下半分をぼかして隠す（メールの続きの見せ方）"""
    x0, y0, x1, y1 = [int(v) for v in box]
    region = img.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(blur))
    img.paste(region, (x0, y0))
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
    dd.rectangle([x0, y0, x1, y1], fill=(250, 245, 238, 110))
    img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB"); d = ImageDraw.Draw(img)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    # 鍵マーク
    d.rounded_rectangle([cx - 18, cy - 30, cx + 18, cy - 2], radius=6, fill=MARK_OUT)
    d.arc([cx - 12, cy - 50, cx + 12, cy - 22], 180, 360, fill=MARK_OUT, width=4)
    b_ = d.textbbox((0, 0), label, font=f(L.SERIFM, 28)); d.text((cx - (b_[2] - b_[0]) / 2, cy + 8), label, font=f(L.SERIFM, 28), fill=DARK)
    return img, d

def p3_today(idx, total):
    img = p3_base("今日の運勢", "会員になると届くもの ①", ["毎日あなたの今日の運勢が", "メールで届きます。"], idx, total, 11)
    T = TODAY_TEXT
    img, d = cream_card(img, (120, 360, W - 120, 900))
    d.text((160, 392), T["date"], font=f(L.SERIFM, 26), fill=DARK2)
    d.text((160, 428), f'{T["luna"]}　今日の運勢', font=f(L.SERIF, 40), fill=DARK)
    mark(d, "star_o", 182, 502, 20, lw=4)
    d.text((214, 486), T["rank"], font=f(L.SERIFM, 28), fill=MARK_OUT)
    d.line([(160, 536), (W - 160, 536)], fill=(214, 196, 170), width=1)
    y = 554
    for title, lines in T["sections"]:
        d.text((160, y), title, font=f(L.SERIFM, 28), fill=MARK_OUT); y += 40
        for ln in lines:
            for sub in V.wrap(ln, 30): d.text((160, y), sub, font=f(L.SERIFM, 24), fill=DARK); y += 36
        y += 14
    img, d = veil(img, (124, 680, W - 124, 896))
    pager(d, idx, total); return img

def p3_month(idx, total):
    img = p3_base("今月・今年の運勢", "会員になると届くもの ②", ["月ごと、年ごとの運気の流れがわかります。", "引っ越しや転職など、大きな決断の時期選びに。"], idx, total, 12)
    img, d = phone_card(img, (120, 400, W - 120, 860), "今月の運勢　／　今年の運勢")
    # 流れを示す曲線
    pts = []
    for i in range(0, 721):
        x = 180 + i; t = i / 720
        y = 690 - 110 * math.sin(t * math.pi * 2.2 + 0.4) - 30 * math.sin(t * math.pi * 7)
        pts.append((x, y))
    d.line(pts, fill=(255, 236, 196), width=5)
    for i, m in enumerate(["1月", "3月", "5月", "7月", "9月", "11月"]):
        x = 180 + i * 144; d.line([(x, 560), (x, 800)], fill=(255, 246, 230, 80), width=1)
        ctext(d, m, x, 806, f(L.SERIFM, 24), SOFT)
    pager(d, idx, total); return img

def p3_aishou(idx, total):
    img = p3_base("相性診断", "会員になると届くもの ③", ["ふたりのルナ番号で、何度でも。", "恋人でも、友だちでも、職場の人でも。", "27×27＝729通り。"], idx, total, 13)
    img = moon(img, 300, W / 2 - 200, 560); img = moon(img, 300, W / 2 + 200, 560, 0.9)
    d = ImageDraw.Draw(img)
    d.arc([W / 2 - 300, 440, W / 2 + 300, 760], 205, 335, fill=(255, 236, 196), width=6)
    L.diamond(d, W / 2, 440, 16, (255, 236, 196))
    ctext(d, "あなた", W / 2 - 200, 740, f(L.SERIFM, 32), INK); ctext(d, "気になる人", W / 2 + 200, 740, f(L.SERIFM, 32), INK)
    ctext(d, "理想の相手　／　避けたい相手", W / 2, 820, f(L.SERIFM, 30), GOLD_D)
    pager(d, idx, total); return img

# 2030年1月（1日は火曜）：☆多めの並び
SAMPLE_203001 = [1,2,4,3,1,5,2,1,4,6,3,1,2,8,5,1,4,2,3,7,1,2,4,9,3,1,5,2,6,1,4]

def p3_calendar(idx, total, ym="2030年1月", data=None):
    img = p3_base("吉凶カレンダー", "会員になると届くもの ④", ["1か月の吉凶が、9つのマークで一目で。", "結婚・旅行・仕事・デートの日にち選びに。"], idx, total, 14)
    data = data or SAMPLE_203001
    img, d = cream_card(img, (100, 350, W - 100, 910))
    d.text((140, 378), ym, font=f(L.SERIF, 36), fill=DARK)
    d.text((140 + 36 * len(ym) + 20, 390), "吉凶カレンダー", font=f(L.SERIFM, 24), fill=DARK2)
    x0, y0, cw, ch = 140, 470, 114, 64
    for i, wd in enumerate(["日", "月", "火", "水", "木", "金", "土"]):
        b_ = d.textbbox((0, 0), wd, font=f(L.SERIFM, 22)); d.text((x0 + i * cw + cw / 2 - (b_[2] - b_[0]) / 2, y0 - 36), wd, font=f(L.SERIFM, 22), fill=(200, 60, 60) if i == 0 else ((60, 90, 180) if i == 6 else DARK2))
    first_wd = 2   # 2019年1月1日は火曜
    for day, k in enumerate(data, 1):
        pos = first_wd + day - 1; r, c = divmod(pos, 7)
        cx, cy = x0 + c * cw + cw / 2, y0 + r * ch + ch / 2
        b_ = d.textbbox((0, 0), str(day), font=f(L.SERIFM, 22)); d.text((cx - 36, cy - 14), str(day), font=f(L.SERIFM, 22), fill=DARK)
        mark(d, MARKS[k - 1][0], cx + 18, cy, 11, lw=2)
    # 凡例（実際のマーク名）3列×3行
    for i, (kind, name) in enumerate(MARKS):
        r, c = divmod(i, 3); x, y = 150 + c * 290, 812 + r * 30
        mark(d, kind, x, y, 10, lw=2); d.text((x + 20, y - 13), name, font=f(L.SERIFM, 19), fill=DARK)
    img, d = veil(img, (104, y0 + ch * 2 + 4, W - 104, 790), label="残りは、会員ページで")
    pager(d, idx, total); return img

def p3_profile(idx, total):
    img = p3_base("自分のルナを、くわしく", "会員になると届くもの ⑤", ["宿命・天運・才能・適職・恋愛・結婚・金運・健康。", "あなたのルナの、本当のところ。"], idx, total, 15)
    img = moon(img, 260, W / 2, 620, 0.95)
    d = ImageDraw.Draw(img)
    tags = ["宿命", "天運", "才能", "適職", "恋愛", "結婚", "金運", "健康"]
    for i, t in enumerate(tags):
        a = -math.pi / 2 + i * 2 * math.pi / len(tags)
        cx, cy = W / 2 + 330 * math.cos(a), 620 + 230 * math.sin(a)
        d.rounded_rectangle([cx - 72, cy - 30, cx + 72, cy + 30], radius=30, fill=(60, 36, 96, 255), outline=GOLD, width=1)
        ctext(d, t, cx, cy - 18, f(L.SERIFM, 30), INK)
    pager(d, idx, total); return img

def p3_close(idx, total):
    img = paper(seed=16); img = moon(img, 420, W / 2, 360); img = band(img, 640, 1280, 0.44); frame(img)
    gold_c(img, "プレミアム会員", W / 2, 700, f(L.SERIF, 84)); d = ImageDraw.Draw(img)
    ctext(d, "月550円から", W / 2, 830, f(L.SERIF, 64), INK)
    rule(d, W / 2, 930, 240)
    for i, ln in enumerate(["まずは無料で、自分のルナを調べてみてください。", "2007年から続く宿曜占星術 LUNA28"]):
        ctext(d, ln, W / 2, 965 + i * 60, f(L.SERIFM, 32), SOFT)
    L.gold_pill(img, (W / 2 - 320, 1110, W / 2 + 320, 1205), "会員になる ▶ プロフィールのリンク", f(L.SANSB, 32))
    pager(ImageDraw.Draw(img), idx, total); return img

def post3():
    total = 7
    return [p3_cover(total), p3_today(2, total), p3_month(3, total), p3_aishou(4, total), p3_calendar(5, total), p3_profile(6, total), p3_close(7, total)]

def render(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    pin1().save(os.path.join(out_dir, "post1_あなたのルナは何番.jpg"), quality=92)
    for i, im in enumerate(post2(), 1): im.save(os.path.join(out_dir, f"post2_{i:02d}.jpg"), quality=92)
    for i, im in enumerate(post3(), 1): im.save(os.path.join(out_dir, f"post3_{i:02d}.jpg"), quality=92)
    return sorted(os.listdir(out_dir))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True)
    print(render(ap.parse_args().out))
