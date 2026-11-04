# -*- coding: utf-8 -*-
"""
設定が正しいか1分で確かめる（投稿はしない）
  python3 check_setup.py
環境変数 GOOGLE_SA_JSON, SHEET_ID を使う。設定タブの access_token で Instagram に接続して username と投稿枠を表示する。
"""
import os, sys
from sheet import Sheet
from publish import Instagram

sh = Sheet(os.environ["GOOGLE_SA_JSON"], os.environ["SHEET_ID"])
st = sh.settings()
print("シート: OK  予定表", len(sh.rows()), "行 / 承認済みの月:", sorted(sh.approved_months()))
ig = Instagram(st.get("ig_user_id", ""), st.get("access_token", ""))
me = ig.me()
print("Instagram: OK ", me)
if str(me.get("user_id")) != str(st.get("ig_user_id")):
    print("※ 設定タブの ig_user_id を", me.get("user_id"), "にしてください")
    sh.set_setting("ig_user_id", str(me.get("user_id"))); print("   → 書き換えました")
print("本日の投稿枠:", ig.quota())
