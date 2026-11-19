# -*- coding: utf-8 -*-
"""
LUNA28 リール（朝焼けの空と海）: 恋愛の相性／星座と月／新月／診断の実演／満月／年間ランキング
使い方:
  python3 render/render_reel2.py --key aite_luna16 --out out/aite_luna16.mp4 --audio audio19.m4a
  python3 render/render_reel2.py --key aite_luna16 --preview out/prev   （代表コマだけ書き出す）
数字とルナの呼び名は content/luna_data.json（ルナシート由来）と、確認済みの生年月日だけを使う
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import luna_style as L
import reel2 as R

W, H = R.W, R.H
ROOT = R.ROOT
DATA = json.load(open(os.path.join(ROOT, "content", "luna_data.json"), encoding="utf-8"))
NAME = {k: v["name"] for k, v in DATA.items()}
BIG = (540, 445, 216, 0.0); SMALL = (837, 283, 108, 0.0)

# 生年月日→ルナは、ルナツールと早見表で確認済みのものだけ（2026年11月の制作時に照合）
VERIFIED = {"1988-04-05": 16, "1989-04-05": 27, "1990-04-05": 9, "1988-08-15": 12, "1989-08-15": 23, "1990-08-15": 3, "1985-12-24": 4}

def luna_of(y, m, d):
    return VERIFIED[f"{y:04d}-{m:02d}-{d:02d}"]

def title(r, t0, t1, white, gold, wsize=74, gsize=92, y=878, gap=148, div=True):
    r.add(R.white_text(white, y, wsize), t0 + 0.35, t1, wipe=0.9, slide=0)
    r.add(R.gold_text(gold, y + gap, gsize), t0 + 1.25, t1, wipe=0.9, slide=0)
    if div: r.add(R.divider(y + gap + 112), t0 + 2.0, t1, fade=0.8, slide=0)

def cta(r, t0, headline, foot, hsize=72):
    r.add(R.gold_text(headline, 888, hsize), t0, None, wipe=0.9, slide=0)
    r.add(R.divider(1000), t0 + 0.9, None, fade=0.7, slide=0)
    r.add(R.white_text("生年月日だけで、30秒", 1072, 44, font=L.SERIFM), t0 + 1.1, None)
    r.add(R.white_text("登録不要・無料", 1150, 44, font=L.SERIFM), t0 + 1.3, None)
    r.add(R.gold_button("プロフィールのリンクから ▶", 1332), t0 + 1.7, None, fade=0.8)
    r.add(R.foot_text(foot, 1484), t0 + 2.0, None, fade=0.8)

def reveal(r, t0, t1, lead, date_text, no, catch_lines=None):
    r.add(R.white_text(lead, 308, 44, font=L.SERIFM), t0 + 0.1, t1)
    r.add(R.date_pill(date_text, 460), t0 + 0.45, t1)
    r.add(R.medallion(no, 540, 830, 420), t0 + 1.2, t1, fade=0.9, slide=18)
    r.add(R.gold_text(f"{no}のルナ", 1092, 84), t0 + 1.9, t1)
    r.add(R.white_text(f"「{NAME[str(no)]}」", 1184, 46, font=L.SERIFM), t0 + 2.1, t1)
    for i, ln in enumerate(catch_lines or []):
        r.add(R.white_text(ln, 1338 + i * 66, 42, font=L.SERIFM), t0 + 3.0 + i * 0.35, t1)

# ------------------------------------------------------------ 恋愛の相性（金曜）
def aite(y, m, d):
    no = luna_of(y, m, d); a, b = DATA[str(no)]["aishou"]["ideal1"]
    r = R.Reel(19.4)
    r.moon(0, *BIG).moon(3.7, *SMALL).moon(13.3, *BIG)
    title(r, 0.0, 3.4, "気になる人の誕生日、", "覚えていますか")
    reveal(r, 3.8, 7.3, "たとえば、あの人が", f"{y}年 {m}月 {d}日生まれ", no)
    t0, t1 = 7.7, 12.9
    r.add(R.medallion(no, 540, 324, 216), t0, t1, fade=0.7, slide=14)
    r.add(R.white_text(f"{no}のルナが理想とする相手", 494, 50), t0 + 0.35, t1)
    for i, (x, n) in enumerate(((297, a), (783, b))):
        ts = t0 + 1.1 + i * 0.75
        r.add(R.medallion(n, x, 810, 400), ts, t1, fade=0.9, slide=18)
        r.add(R.gold_text(f"{n}のルナ", 1090, 72, cx=x), ts + 0.35, t1)
        r.add(R.white_text(f"「{NAME[str(n)]}」", 1176, 40, font=L.SERIFM, cx=x), ts + 0.5, t1)
    r.add(R.white_text("あなたは、このどちらか？", 1342, 46, font=L.SERIFM), t0 + 3.2, t1)
    title(r, 13.3, 15.5, "あなたは、あの人の", "理想の相手？", gsize=98)
    cta(r, 15.8, "ふたりは、何番と何番？", "誕生日がわかれば、ふたりのルナがわかる", hsize=70)
    return r

# ------------------------------------------------------------ 星座が太陽なら、ルナは月
def sun_moon():
    r = R.Reel(17.0)
    r.moon(0, *BIG).moon(3.6, *SMALL).moon(8.6, *BIG)
    title(r, 0.0, 3.3, "星座が太陽なら、", "ルナは月", gsize=116, gap=156)
    t1 = 8.2
    for i, (lab, txt, y0) in enumerate((("星座", "生まれた日の太陽の位置", 430), ("ルナ", "生まれた日の月の位置", 760))):
        ts = 3.9 + i * 1.5
        r.add(R.merge(R.glass_box([110, y0, 970, y0 + 280], radius=30)), ts, t1)
        r.add(R.gold_text(lab, y0 + 86, 64), ts + 0.2, t1)
        r.add(R.white_text(txt, y0 + 192, 56), ts + 0.45, t1)
    title(r, 8.6, 12.3, "月は毎日、位置を変える", "だから、ルナは27通り", wsize=64, gsize=80)
    cta(r, 12.7, "あなたは、何のルナ？", "星座は同じでも、ルナは違うかもしれない")
    return r

# ------------------------------------------------------------ 新月
def shingetsu(month, day):
    r = R.Reel(17.0)
    r.moon(0, 540, 520, 420, 0.84).moon(8.2, 540, 445, 216, 0.0)
    r.add(R.white_text(f"{month}月{day}日は", 900, 66), 0.4, 3.5, wipe=0.8, slide=0)
    r.add(R.gold_text("新月", 1056, 140), 1.2, 3.5, wipe=0.7, slide=0)
    r.add(R.white_text("月が見えない夜。", 900, 64), 4.0, 7.7, wipe=0.8, slide=0)
    r.add(R.white_text("ここからまた、月は満ちていく", 1012, 58), 5.1, 7.7, wipe=1.0, slide=0)
    title(r, 8.1, 12.0, "その月の位置から導くのが", "27のルナ", wsize=56, gsize=124, gap=156)
    cta(r, 12.4, "あなたのルナは何番？", "新しい月のはじまりに、自分のルナを知る")
    return r

# ------------------------------------------------------------ 診断の実演
def jitsuen(y, m, d, hook_white, hook_gold):
    no = luna_of(y, m, d); c = DATA[str(no)]["catch"]
    cut = c.find("新しい") if no == 4 else len(c) // 2
    r = R.Reel(17.0)
    r.moon(0, *BIG).moon(3.7, *SMALL).moon(10.0, *BIG)
    title(r, 0.0, 3.4, hook_white, hook_gold, wsize=68, gsize=82)
    reveal(r, 3.8, 9.6, "たとえば", f"{y}年 {m}月 {d}日生まれ", no, [c[:cut], c[cut:]])
    title(r, 10.0, 12.6, "生年月日を入れるだけ。", "気になる人の誕生日でも", wsize=66, gsize=76, div=False)
    cta(r, 13.0, "あなたは、何のルナ？", "あの人の誕生日でも調べられます")
    return r

# ------------------------------------------------------------ 満月
def mangetsu(lead, line_w, line_g):
    r = R.Reel(17.0)
    r.moon(0, 540, 720, 400, 0.0).moon(3.9, 540, 500, 480, 0.0).moon(12.4, 540, 420, 300, 0.0)
    r.add(R.white_text(lead, 1010, 64), 0.5, 3.5, wipe=0.8, slide=0)
    r.add(R.gold_text("満月", 1160, 140), 1.3, 3.5, wipe=0.7, slide=0)
    r.add(R.white_text(line_w, 880, 60), 4.2, 8.0, wipe=0.9, slide=0)
    r.add(R.gold_text(line_g, 1000, 62), 5.2, 8.0, wipe=1.0, slide=0)
    r.add(R.white_text("その月の位置から導くのが", 880, 56), 8.5, 12.0, wipe=0.9, slide=0)
    r.add(R.gold_text("27のルナ", 1030, 124), 9.4, 12.0, wipe=0.8, slide=0)
    cta(r, 12.5, "あなたのルナは何番？", "満月の夜に、自分のルナを知る")
    return r

# ------------------------------------------------------------ 毎月の満月（2027年）。日時は国立天文台の暦要項（令和9年）の「望」による
def mangetsu2(lead, fact_w, fact_g, msg_w, msg_g, cta_head, foot):
    r = R.Reel(17.0)
    r.moon(0, 540, 720, 400, 0.0).moon(3.9, 540, 500, 480, 0.0).moon(12.4, 540, 420, 300, 0.0)
    r.add(R.white_text(lead, 1010, 64), 0.5, 3.5, wipe=0.8, slide=0)
    r.add(R.gold_text("満月", 1160, 140), 1.3, 3.5, wipe=0.7, slide=0)
    r.add(R.white_text(fact_w, 880, 58), 4.2, 8.0, wipe=0.9, slide=0)
    r.add(R.gold_text(fact_g, 1000, 68), 5.2, 8.0, wipe=1.0, slide=0)
    r.add(R.white_text(msg_w, 880, 58), 8.5, 12.0, wipe=0.9, slide=0)
    r.add(R.gold_text(msg_g, 1010, 84), 9.4, 12.0, wipe=0.9, slide=0)
    cta(r, 12.5, cta_head, foot)
    return r

FULLMOON_2027 = {
    "mangetsu_270122": ("今夜21時17分、", "2027年、最初の満月は", "今年いちばん大きく見える", "生まれた日の月の位置で決まる", "27のルナ", "あなたのルナは何番？", "今年の運勢は、ルナ番号から"),
    "mangetsu_270221": ("今日、2月21日は", "満月の瞬間は、朝8時24分", "今夜も、まるい月がのぼる", "気になる人が生まれた日、", "月はどこにいただろう", "あの人は、何のルナ？", "誕生日がわかれば、ルナがわかる"),
    "mangetsu_270322": ("今日、3月22日は", "春分をすぎて、最初の満月", "19時44分、月が満ちた", "新しい季節のはじまりに", "自分のルナを知る", "あなたは、何のルナ？", "生年月日だけで調べられます"),
    "mangetsu_270421": ("今日、4月21日は", "満月の瞬間は、朝7時27分", "春の夜に、まるい月", "星座は太陽、", "ルナは月で決まる", "あなたのルナは何番？", "星座は同じでも、ルナは違うかもしれない"),
    "mangetsu_270520": ("今夜、5月20日は", "満月の瞬間は、19時59分", "いま、月がいちばんまるい", "同じ誕生日でも、生まれ年で", "ルナは変わる", "あなたは、何のルナ？", "月の位置は、毎年ちがう"),
    "mangetsu_270619": ("今日、6月19日は", "夏至の2日前の満月", "一年でいちばん夜が短いころ", "短い夜にも、月はのぼる", "その月から導く27のルナ", "あなたのルナは何番？", "生年月日を入れるだけ"),
    "mangetsu_270719": ("今日、7月19日は", "満月の瞬間は、深夜0時45分", "今夜も、まるい月がのぼる", "あなたが生まれた夜、", "月はどこにいただろう", "あなたは、何のルナ？", "生まれた日の月の位置でわかる"),
    "mangetsu_270817": ("今日、8月17日は", "満月の瞬間は、16時29分", "夏の夜空に、まるい月", "ふたりの誕生日がわかれば", "ふたりのルナがわかる", "ふたりは、何番と何番？", "気になる人の誕生日でも調べられます"),
    "mangetsu_270916": ("今日、9月16日は", "中秋の名月は、きのう15日", "満月は、その翌日の今日", "お月見の季節に", "自分のルナを知る", "あなたのルナは何番？", "月で占う、27のルナ"),
    "mangetsu_271015": ("今夜22時47分、", "あと少しで、", "月がいちばん満ちる", "月の位置から導く", "27のルナ", "あなたは、何のルナ？", "満月の夜に、自分のルナを知る"),
    "mangetsu_271114": ("今日12時26分、", "ちょうど今ごろ、", "月が満ちている", "今夜の月を見上げたら", "あの人のルナも調べてみる", "あの人は、何のルナ？", "誕生日がわかれば、ルナがわかる"),
    "mangetsu_271214": ("今日、12月14日は", "2027年、最後の満月", "満月の瞬間は、深夜1時9分", "一年のしめくくりに", "自分のルナを知る", "あなたのルナは何番？", "来年の運勢は、ルナ番号から"),
}

# ------------------------------------------------------------ 2027年 年間ランキング
def ranking(year, top3, label, note):
    r = R.Reel(17.0)
    r.moon(0, *BIG).moon(3.6, 908, 205, 92, 0.0).moon(9.8, *BIG)
    title(r, 0.0, 3.3, f"{year}年、", "運のいいルナは？", wsize=84, gsize=90, gap=152)
    t1 = 9.4
    r.add(R.white_text(f"{year}年 年間ランキング", 345, 54), 3.8, t1)
    for i, no in enumerate(top3):
        y0 = 430 + i * 276; ts = 4.5 + (2 - i) * 0.95
        r.add(R.glass_box([100, y0, 980, y0 + 246], radius=28), ts, t1)
        r.add(R.gold_text(f"{i + 1}位", y0 + 123, 78, cx=222), ts + 0.15, t1)
        r.add(R.medallion(no, 468, y0 + 123, 196), ts + 0.15, t1, slide=12)
        r.add(R.gold_text(f"{no}のルナ", y0 + 96, 66, cx=768), ts + 0.3, t1)
        r.add(R.white_text(f"「{NAME[str(no)]}」", y0 + 176, 40, font=L.SERIFM, cx=768), ts + 0.45, t1)
    r.add(R.white_text(f"1位は{top3[0]}のルナ", 860, 70), 10.0, 12.6, wipe=0.8, slide=0)
    r.add(R.gold_text(f"『{label}』", 1010, 104), 10.8, 12.6, wipe=0.8, slide=0)
    r.add(R.white_text(note, 1136, 42, font=L.SERIFM), 11.5, 12.6)
    cta(r, 13.0, f"あなたのルナの{year}年は？", "生年月日だけで、ルナ番号がわかります", hsize=64)
    return r

REELS = {
    "sunmoon_1202":  lambda: sun_moon(),
    "aite_luna16":   lambda: aite(1988, 4, 5),
    "shingetsu_1209": lambda: shingetsu(12, 9),
    "aite_luna27":   lambda: aite(1989, 4, 5),
    "jitsuen_luna04": lambda: jitsuen(1985, 12, 24, "クリスマスイブ生まれの", "あの人は、何のルナ？"),
    "aite_luna23":   lambda: aite(1989, 8, 15),
    "mangetsu_1224": lambda: mangetsu("明日、12月24日は", "クリスマスイブの夜空に", "今年いちばん大きく見える満月"),
    "aite_luna03":   lambda: aite(1990, 8, 15),
    "rank_2027":     lambda: ranking(2027, [19, 2, 11], "大幸運年", "想像を超える喜びが訪れる年回り"),
}

for _k, _v in FULLMOON_2027.items():
    REELS[_k] = (lambda v=_v: mangetsu2(*v))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", required=True); ap.add_argument("--out"); ap.add_argument("--audio"); ap.add_argument("--preview"); ap.add_argument("--times", default="")
    a = ap.parse_args(); r = REELS[a.key]()
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        ts = [float(x) for x in a.times.split(",")] if a.times else [2.9, 6.9, 11.8, 15.5, r.T - 1.0]
        for t, im in zip(ts, r.render(None, preview_times=ts)):
            im.save(os.path.join(a.preview, f"{a.key}_{t:05.1f}.jpg"), quality=90)
    else:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        print(r.render(a.out, audio=a.audio))
