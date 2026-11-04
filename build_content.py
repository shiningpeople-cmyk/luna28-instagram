# -*- coding: utf-8 -*-
"""ルナシート（content/luna_data.json）から、図鑑カルーセル／リールの原稿JSONを27ルナ分つくる。
文章はシートの原文をそのまま切り出す（言い換えなし）。"""
import json, re, os
ROOT=os.path.dirname(os.path.abspath(__file__))
D=json.load(open(os.path.join(ROOT,'content','luna_data.json'),encoding='utf-8'))

def sents(t):
    t=t.replace('\n','')
    return [s+'。' for s in t.split('。') if s.strip()]

def short(s, n=30):
    s=re.sub(r'^(あなたは、?|あなたには、?|\d+のルナの(人|あなた)は、?)','',s).rstrip('。')
    s=re.sub(r'(です|ます|でしょう)$','',s)
    s=s.replace('※男性は配偶者運が大変良い生まれです','')
    if len(s)<=n: return s
    parts=s.split('、'); out=''
    for p in parts:
        if len(out)+len(p)+1>n: break
        out=(out+'、' if out else '')+p
    return out or s[:n]

def quotes(t):
    return [q for q in re.findall(r'「([^「」]{6,40})」',t) if any(k in q for k in ('天運','運','できる','受ける','高まる','恵まれる','得る','引き立て','救われ','乗り切れ','発揮','生む','つかめ','戻ってくる','解決','助け','開運','認められ'))]

os.makedirs(os.path.join(ROOT,'content'),exist_ok=True)
for k,v in D.items():
    n=int(k); a=v['aishou']
    se=sents(v['seishitsu']); lo=sents(v['love']); te=sents(v['tenun'])
    qs=quotes(v['tenun'])
    tenun_lines=[q if q.startswith('「') else f'「{q}」' for q in qs[:2]] or [te[0]]
    zukan={"no":n,"name":v['name'],"catch":v['catch'],
      "pages":[
        {"title":"性格","lines":se[:2]},
        {"title":"天運","lines":[te[0]]+tenun_lines[:1]},
        {"title":"恋愛","lines":([lo[0]] if not re.search('不倫|離婚|死別|危険|泥沼',lo[0]) else [])+[x for x in lo[1:] if '鍵' in x][:1]},
        {"title":"相性","good":[str(x) for x in a['ideal1']],"care":[str(x) for x in a['avoid1']],"note":f"※{a['avoid_f']}のルナは女性の場合のみ避けたい相手"},
        {"title":"ラッキー","lines":[f"ラッキーフラワー　{v['lucky_flower']}",f"ラッキーカラー　{v['lucky_color']}"]}],
      "cta":"あなたのルナは何番？","_source":"ルナシート2017（luna_%02d.pdf）原文"%n}
    json.dump(zukan,open(os.path.join(ROOT,'content',f'zukan_luna{n:02d}.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    hook_core=re.sub(r'(な人|の人|人)$','',short(se[0],16))
    reel={"no":n,"name":v['name'],
      "hook":["周りから",f"「{hook_core}」と","言われるあなた"],
      "traits":[short(se[0]), short(v['catch']), short(tenun_lines[0].strip('「」'))],
      "cta":"あなたのルナは何番？","_source":"ルナシート2017（luna_%02d.pdf）原文"%n}
    json.dump(reel,open(os.path.join(ROOT,'content',f'reel_luna{n:02d}.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('ok')
