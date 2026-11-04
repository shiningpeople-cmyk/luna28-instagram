# -*- coding: utf-8 -*-
"""
リール動画（質問型・約16秒）: ①問いかけ → ②「それ、○のルナかも」 → ③特徴3つ → ④あなたは何番？
使い方:
  python3 render_reel.py --json reel.json --out out/reel.mp4
reel.json:
  {"hook": ["周りから", "「しっかり者」と", "言われるあなた"],
   "no": 1, "name": "王の人",
   "traits": ["品格と知性で人を惹きつける", "天からの恵みに守られる", "頼られるほど運が開く"],
   "cta": "あなたのルナは何番？"}
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw, ImageFilter
import luna_style as L
import luna_video as V

W, H = V.W, V.H
f = L.f
WHITE = (255, 252, 246)      # テーマB：朝焼けの空に白文字
SH = (70, 40, 100)
SOFT = (255, 244, 224)

def brand(lay):
    d = ImageDraw.Draw(lay)
    V.ctext(d, "LUNA28　宿曜占星術", W / 2, 150, f(L.SERIFM, 36), SOFT)

def scene_hook(hook):
    s = V.Scene(4.0, 520, W / 2, 430)
    s.add(V.scrim_layer(700, 1500), 0, 0.01, 0); s.add(V.text_layer(brand), 0, 0.5)
    y0 = 800
    for i, ln in enumerate(hook):
        s.add(V.text_layer(lambda l, ln=ln, i=i: V.gold_text_c(l, ln, W / 2, y0 + i * 130, f(L.SERIF, 92 if len(ln) <= 8 else (74 if len(ln) <= 11 else 60)))), 0.15 + i * 0.35, 0.5, 36)
    s.add(V.text_layer(lambda l: V.ctext(ImageDraw.Draw(l), "▼", W / 2, 1320, f(L.SANSB, 60), SOFT)), 1.6, 0.6, 0)
    return s

CHARS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "content", "chars")
def medallion_layer(no, cx, cy, dia):
    pth = os.path.join(CHARS, f"{int(no):02d}_med.png")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if not os.path.exists(pth): return lay
    med = Image.open(pth).convert("RGBA").resize((dia, dia), Image.LANCZOS)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse([cx - dia / 2 + 4, cy - dia / 2 + 12, cx + dia / 2 + 4, cy + dia / 2 + 12], fill=(40, 20, 70, 110))
    lay = Image.alpha_composite(lay, sh.filter(ImageFilter.GaussianBlur(12)))
    lay.alpha_composite(med, (int(cx - dia / 2), int(cy - dia / 2)))
    d = ImageDraw.Draw(lay); d.ellipse([cx - dia / 2, cy - dia / 2, cx + dia / 2, cy + dia / 2], outline=L.GOLD, width=4)
    d.ellipse([cx - dia / 2 - 8, cy - dia / 2 - 8, cx + dia / 2 + 8, cy + dia / 2 + 8], outline=(255, 240, 210), width=1)
    return lay

def scene_reveal(no, name):
    has_char = os.path.exists(os.path.join(CHARS, f"{int(no):02d}_med.png"))
    s = V.Scene(4.2, 200 if has_char else 760, (W - 180) if has_char else W / 2, 300 if has_char else 520)
    s.add(V.scrim_layer(820, 1520), 0, 0.01, 0); s.add(V.text_layer(brand), 0, 0.5)
    if has_char: s.add(medallion_layer(no, W / 2, 500, 520), 0.1, 0.7, 20)
    s.add(V.text_layer(lambda l: V.ctext(ImageDraw.Draw(l), "それ、", W / 2, 900, f(L.SERIFM, 60), WHITE, shadow=SH)), 0.1, 0.5)
    def big(l):
        V.gold_text_c(l, f"{no}のルナ", W / 2, 990, f(L.SERIF, 150))
        V.ctext(ImageDraw.Draw(l), "かも", W / 2, 1190, f(L.SERIFM, 60), WHITE, shadow=SH)
    s.add(V.text_layer(big), 0.6, 0.6, 50)
    s.add(V.text_layer(lambda l: [L.ornament_divider(ImageDraw.Draw(l), W / 2, 1320, half=240), V.ctext(ImageDraw.Draw(l), f"「{name}」", W / 2, 1360, f(L.SERIFM, 56), SOFT)]), 1.4, 0.7, 20)
    return s

def scene_traits(no, name, traits):
    s = V.Scene(6.5, 460, W / 2, 380)
    s.add(V.scrim_layer(620, 1640), 0, 0.01, 0); s.add(V.text_layer(brand), 0, 0.5)
    s.add(V.text_layer(lambda l: [V.gold_text_c(l, f"{no}のルナの人は", W / 2, 680, f(L.SERIF, 76)), L.ornament_divider(ImageDraw.Draw(l), W / 2, 800, half=260)]), 0.0, 0.6)
    for i, tr in enumerate(traits):
        def mk(l, tr=tr, i=i):
            d = ImageDraw.Draw(l); y = 880 + i * 190
            L.diamond(d, 150, y + 36, 16)
            lines = V.wrap(tr, 16)
            for j, ln in enumerate(lines):
                d.text((203, y + j * 66 + 3), ln, font=f(L.SERIFM, 46), fill=SH); d.text((200, y + j * 66), ln, font=f(L.SERIFM, 46), fill=WHITE)
        s.add(V.text_layer(mk), 0.6 + i * 1.3, 0.6, 30)
    s.add(V.text_layer(lambda l: V.ctext(ImageDraw.Draw(l), "当てはまる人、周りにいませんか？", W / 2, 1520, f(L.SERIFM, 40), SOFT)), 4.6, 0.7, 12)
    return s

def scene_cta(cta):
    s = V.Scene(4.6, 560, W / 2, 400)
    s.add(V.scrim_layer(720, 1520), 0, 0.01, 0); s.add(V.text_layer(brand), 0, 0.5)
    def big(l):
        V.gold_text_c(l, cta, W / 2, 800, f(L.SERIF, 84 if len(cta) <= 9 else 70))
        L.ornament_divider(ImageDraw.Draw(l), W / 2, 950, half=240)
    s.add(V.text_layer(big), 0.2, 0.7)
    s.add(V.text_layer(lambda l: [V.ctext(ImageDraw.Draw(l), ln, W / 2, 1000 + i * 80, f(L.SERIFM, 46), WHITE, shadow=SH) for i, ln in enumerate(["生年月日だけで、30秒", "登録不要・無料"])]), 0.8, 0.7)
    s.add(V.pill_layer((W / 2 - 360, 1210, W / 2 + 360, 1330), "プロフィールのリンクから ▶", f(L.SANSB, 44)), 1.3, 0.7, 30)
    s.add(V.text_layer(lambda l: [V.ctext(ImageDraw.Draw(l), "毎朝7時、今日のラッキールナをストーリーズで", W / 2, 1420, f(L.SERIFM, 32), SOFT), V.ctext(ImageDraw.Draw(l), "@luna28.japan", W / 2, 1755, f(L.SERIFM, 30), SOFT)]), 1.9, 0.8, 10)
    return s

def render(spec, out_mp4, with_audio=True):
    os.makedirs(os.path.dirname(out_mp4) or ".", exist_ok=True)
    scenes = [scene_hook(spec["hook"]), scene_reveal(spec["no"], spec["name"]), scene_traits(spec["no"], spec["name"], spec["traits"]), scene_cta(spec.get("cta", "あなたのルナは何番？"))]
    xfade = 0.6
    total = sum(s.duration for s in scenes) - xfade * (len(scenes) - 1)
    wav = None
    if with_audio:
        ts = [0.0]
        for s in scenes[:-1]: ts.append(ts[-1] + s.duration - xfade)
        chords = [(ts[0], ["E3", "B3", "G#4", "B4", "F#5"]), (ts[1], ["C#3", "G#3", "E4", "B4", "D#5"]), (ts[2], ["A2", "E3", "C#4", "G#4", "B4"]), (ts[3], ["B2", "F#3", "D#4", "A4", "C#5"])]
        bells = [(ts[1] + 0.3, "B5"), (ts[3] + 0.1, "E6")]
        audio, sr = V.ambient(total, chords, bells, seed=9)
        wav = out_mp4.rsplit(".", 1)[0] + ".wav"; V.write_wav(wav, audio, sr)
    bg = V.dawn_sky(int(W * 1.06), int(H * 1.06), photo=spec.get("bg"))
    V.Renderer(seed=5, frame=V.thin_frame_layer(), bg=bg).render(scenes, out_mp4, wav, xfade=xfade)
    if wav: os.remove(wav)
    return out_mp4, total

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True); ap.add_argument("--out", required=True); ap.add_argument("--no-audio", action="store_true")
    a = ap.parse_args()
    spec = json.load(open(a.json, encoding="utf-8"))
    print(*render(spec, a.out, not a.no_audio))
