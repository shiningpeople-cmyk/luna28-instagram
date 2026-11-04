# -*- coding: utf-8 -*-
"""固定投稿3本（テーマC：生成り×墨×金） 1080x1350
  python3 render_pins.py --out out/pins [--month 11 --top3 1 18 9]
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw
import luna_style as L
import luna_video as V
import render_carousel as C

W, H = 1080, 1350
f = L.f
INK, SOFT, GOLD = C.CREAM, C.SOFT, L.GOLD

def brand(d):
    d.text((C.M, 92), "LUNA28　宿曜占星術", font=f(L.SERIFM, 28), fill=L.GOLD_D)

def foot(d):
    C.ctext(d, "@luna28.japan", W / 2, 1250, f(L.SERIFM, 26), L.GOLD_D)

def pin1():
    img = C.bg(); img = C.moon_at(img, 620, W / 2, 400); C.hairline_frame(img)
    d = ImageDraw.Draw(img); brand(d)
    C.ctext(d, "生年月日だけで決まる", W / 2, 745, f(L.SERIFM, 48), INK)
    C.gold_c(img, "あなたのルナは何番？", W / 2, 815, f(L.SERIF, 92)); d = ImageDraw.Draw(img)
    C.rule(d, W / 2 - 220, W / 2 + 220, 960)
    C.ctext(d, "27のルナが教える、本当のあなたと今日の運気", W / 2, 990, f(L.SERIFM, 34), SOFT)
    L.gold_pill(img, (W / 2 - 340, 1080, W / 2 + 340, 1180), "無料で30秒・プロフィールのリンクから", f(L.SANSB, 32))
    foot(ImageDraw.Draw(img)); return img

def pin2():
    img = C.bg(); img = C.moon_at(img, 440, W / 2, 330); C.hairline_frame(img)
    d = ImageDraw.Draw(img); brand(d)
    C.ctext(d, "気になるあの人と", W / 2, 600, f(L.SERIFM, 48), INK)
    C.gold_c(img, "相性は何点？", W / 2, 670, f(L.SERIF, 104)); d = ImageDraw.Draw(img)
    C.rule(d, W / 2 - 220, W / 2 + 220, 830)
    for i, ln in enumerate(["ふたりのルナ番号でわかる", "恋人・友人・仕事相手、関係別に", "27×27＝729通り"]):
        C.ctext(d, ln, W / 2, 870 + i * 60, f(L.SERIFM, 36), INK if i < 2 else SOFT)
    L.gold_pill(img, (W / 2 - 320, 1080, W / 2 + 320, 1180), "まず自分のルナを調べる ▶", f(L.SANSB, 34))
    foot(ImageDraw.Draw(img)); return img

def pin3(month, top3):
    img = C.bg(); img = C.moon_at(img, 300, W - 190, 190, alpha=0.9); C.hairline_frame(img)
    d = ImageDraw.Draw(img); brand(d)
    d.text((C.M, 180), f"{month}月の", font=f(L.SERIFM, 52), fill=INK)
    L.gold_text(img, (C.M, 250), "ラッキールナ", f(L.SERIF, 104)); L.gold_text(img, (C.M, 370), "ランキング", f(L.SERIF, 104)); d = ImageDraw.Draw(img)
    d.line([(C.M, 520), (W - C.M, 520)], fill=GOLD, width=1)
    y = 570
    for i, nm in enumerate(top3):
        d.rounded_rectangle([C.M, y, W - C.M, y + 118], radius=20, outline=GOLD, width=2)
        L.diamond(d, C.M + 54, y + 59, 14)
        d.text((C.M + 100, y + 24), f"{i + 1}位", font=f(L.SERIF, 60), fill=L.GOLD_D)
        d.text((C.M + 290, y + 26), f"{nm}のルナ", font=f(L.SERIF, 58), fill=INK); y += 146
    C.ctext(d, "4位以下と、あなたのルナの今月の運勢はプロフィールのリンクから", W / 2, 1050, f(L.SERIFM, 30), SOFT)
    L.gold_pill(img, (W / 2 - 300, 1110, W / 2 + 300, 1205), "自分のルナを調べる ▶", f(L.SANSB, 34))
    foot(ImageDraw.Draw(img)); return img

def render(out_dir, month=None, top3=None):
    os.makedirs(out_dir, exist_ok=True)
    pin1().save(os.path.join(out_dir, "pin1_ルナ判定.jpg"), quality=92)
    pin2().save(os.path.join(out_dir, "pin2_相性.jpg"), quality=92)
    pin3(month or "○", top3 or ["○", "○", "○"]).save(os.path.join(out_dir, "pin3_月間ランキング.jpg"), quality=92)
    return sorted(os.listdir(out_dir))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--month"); ap.add_argument("--top3", nargs=3)
    a = ap.parse_args(); print(render(a.out, a.month, a.top3))
