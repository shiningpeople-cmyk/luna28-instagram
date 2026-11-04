# -*- coding: utf-8 -*-
"""
毎朝のストーリーズ動画（約15秒）: ①今日のラッキールナ1〜3位 → ②今日のひとこと → ③プロフィールへ
使い方:
  python3 render_story.py --date "11月3日(火)" --top3 1 18 9 --hitokoto "気になっていた本や映画に…" --out out/story_1103.mp4
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from PIL import ImageDraw
import luna_style as L
import luna_video as V

W, H = V.W, V.H
f = L.f

def header(lay, date_label):
    d = ImageDraw.Draw(lay)
    V.ctext(d, "LUNA28　宿曜占星術", W / 2, 150, f(L.SERIFM, 36), L.GOLD_L)
    V.ctext(d, date_label, W / 2, 205, f(L.SERIFM, 44), V.CREAM)

def footer(lay, text="自分のルナは、プロフィールのリンクから"):
    d = ImageDraw.Draw(lay)
    if text: V.ctext(d, text, W / 2, 1700, f(L.SERIFM, 34), V.CREAM)
    V.ctext(d, "@luna28.japan", W / 2, 1755, f(L.SERIFM, 30), L.GOLD_L)

def scene_ranking(date_label, top3):
    s = V.Scene(6.2, 900, W / 2, 520)
    s.add(V.text_layer(lambda l: header(l, date_label)), 0.0, 0.8)
    def title(l):
        V.gold_text_c(l, "今日のラッキールナ", W / 2, 880, f(L.SERIF, 88))
        L.ornament_divider(ImageDraw.Draw(l), W / 2, 1010, half=260)
    s.add(V.text_layer(title), 0.3, 0.8)
    cols = [(W / 2, 1060, 1, 230, 64, 0.9), (W / 2 - 330, 1120, 2, 170, 48, 1.6), (W / 2 + 330, 1120, 3, 170, 48, 2.1)]
    for cx, cy, rank, big, small, t_in in cols:
        def mk(l, cx=cx, cy=cy, rank=rank, big=big, small=small):
            d = ImageDraw.Draw(l)
            V.ctext(d, f"{rank}位", cx, cy, f(L.SERIFM, 40), L.GOLD_L)
            V.gold_text_c(l, str(top3[rank - 1]), cx, cy + 50, f(L.SERIF, big))
            d = ImageDraw.Draw(l)
            V.ctext(d, "のルナ", cx, cy + 50 + int(big * 1.18) + 16, f(L.SERIFM, small - 10), V.CREAM)
        s.add(V.text_layer(mk), t_in, 0.7, 40)
    s.add(V.text_layer(footer), 2.8, 0.8, 16)
    return s

def scene_hitokoto(date_label, hitokoto):
    s = V.Scene(5.8, 620, W / 2, 430)
    s.add(V.text_layer(lambda l: header(l, date_label)), 0.0, 0.6)
    def title(l):
        V.gold_text_c(l, "今日のひとこと", W / 2, 790, f(L.SERIF, 84))
        L.ornament_divider(ImageDraw.Draw(l), W / 2, 920, half=240)
    s.add(V.text_layer(title), 0.2, 0.8)
    lines = V.wrap(hitokoto, 14)
    for i, ln in enumerate(lines):
        s.add(V.text_layer(lambda l, ln=ln, i=i: V.ctext(ImageDraw.Draw(l), ln, W / 2, 1000 + i * 92, f(L.SERIFM, 54), V.CREAM)), 0.8 + i * 0.45, 0.7, 24)
    s.add(V.text_layer(footer), 1.2 + len(lines) * 0.45, 0.8, 16)
    return s

def scene_cta(top3):
    s = V.Scene(4.8, 560, W / 2, 400)
    s.add(V.text_layer(lambda l: V.ctext(ImageDraw.Draw(l), f"今日の1位は {top3[0]}のルナ", W / 2, 740, f(L.SERIFM, 48), V.CREAM)), 0.0, 0.6)
    def big(l):
        V.gold_text_c(l, "あなたのルナは", W / 2, 820, f(L.SERIF, 84)); V.gold_text_c(l, "何番？", W / 2, 930, f(L.SERIF, 84))
        L.ornament_divider(ImageDraw.Draw(l), W / 2, 1070, half=240)
    s.add(V.text_layer(big), 0.3, 0.8)
    s.add(V.text_layer(lambda l: [V.ctext(ImageDraw.Draw(l), ln, W / 2, 1110 + i * 80, f(L.SERIFM, 46), V.CREAM) for i, ln in enumerate(["生年月日だけで、30秒", "登録不要・無料"])]), 0.9, 0.7)
    s.add(V.pill_layer((W / 2 - 360, 1320, W / 2 + 360, 1440), "プロフィールのリンクから ▶", f(L.SANSB, 44)), 1.4, 0.7, 30)
    s.add(V.text_layer(lambda l: V.ctext(ImageDraw.Draw(l), "ルナ番号がわかる方は、LINEで番号を送ると性格が届きます", W / 2, 1520, f(L.SERIFM, 30), L.GOLD_L)), 2.0, 0.8, 12)
    s.add(V.text_layer(lambda l: footer(l, "")), 2.0, 0.8, 0)
    return s

def render(date_label, top3, hitokoto, out_mp4, with_audio=True):
    os.makedirs(os.path.dirname(out_mp4) or ".", exist_ok=True)
    scenes = [scene_ranking(date_label, top3), scene_hitokoto(date_label, hitokoto), scene_cta(top3)]
    xfade = 0.6
    total = sum(s.duration for s in scenes) - xfade * 2
    wav = None
    if with_audio:
        t2 = scenes[0].duration - xfade; t3 = t2 + scenes[1].duration - xfade
        audio, sr = V.ambient(total, [(0.0, ["D3", "A3", "F#4", "A4", "E5"]), (t2, ["B2", "F#3", "D4", "A4", "C#5"]), (t3, ["G2", "D3", "B3", "F#4", "A4"])],
                              [(0.15, "A5"), (t2 + 0.1, "F#5"), (t3 + 0.1, "D6")])
        wav = out_mp4.rsplit(".", 1)[0] + ".wav"; V.write_wav(wav, audio, sr)
    V.Renderer().render(scenes, out_mp4, wav, xfade=xfade)
    if wav: os.remove(wav)
    return out_mp4, total

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True); ap.add_argument("--top3", nargs=3, required=True)
    ap.add_argument("--hitokoto", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--no-audio", action="store_true")
    a = ap.parse_args()
    out, total = render(a.date, a.top3, a.hitokoto, a.out, not a.no_audio)
    print(out, f"{total:.1f}s")
