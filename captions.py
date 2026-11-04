# -*- coding: utf-8 -*-
"""キャプションの型。予定表のI列が空のときに使う。ハッシュタグは5個まで（2025年12月〜のInstagram仕様）"""
TAGS = "#宿曜占星術 #ルナ28 #LUNA28 #今日の運勢 #相性占い"

def reel(spec):
    return (f"宿曜占星術 {spec['no']}のルナ（{spec['name']}）の性格\n\n"
            + "\n".join("・" + t for t in spec["traits"]) + "\n\n"
            "当てはまる人、周りにいませんか？\n"
            "自分のルナはプロフィールのリンクから30秒で調べられます。\n\n" + TAGS)

def carousel(spec):
    return (f"宿曜占星術 {spec['no']}のルナ（{spec['name']}）の性格と相性\n\n"
            f"{spec['catch']}\n\n"
            "保存して、気になるあの人のルナと見くらべてみてください。\n"
            "自分のルナはプロフィールのリンクから30秒で調べられます。\n\n" + TAGS)

def image(text):
    return text + "\n\n" + TAGS
