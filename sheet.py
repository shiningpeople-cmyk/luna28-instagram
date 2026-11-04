# -*- coding: utf-8 -*-
"""
Googleスプレッドシート「LUNA28_Instagram自動投稿」の読み書き（サービスアカウント）
タブ:
  予定表  A日付 B時刻 C種類 D1位 E2位 F3位 Gひとこと H原稿キー Iキャプション J状態 K投稿URL L処理ログ MメディアURL N承認(OK) Oプレビュー
  設定    A項目 B値   （ig_user_id / access_token / token_updated / media_base_url）
"""
import json, datetime, re, unicodedata
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
COLS = ["date", "time", "kind", "r1", "r2", "r3", "hitokoto", "key", "caption", "status", "url", "log", "media", "ok", "preview"]

class Sheet:
    def __init__(self, sa_json: str, sheet_id: str):
        info = json.loads(sa_json)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        self.gc = gspread.authorize(creds)
        self.ss = self.gc.open_by_key(sheet_id)
        self.ws = self.ss.worksheet("予定表")

    def rows(self):
        vals = self.ws.get_all_values()
        out = []
        for i, r in enumerate(vals[1:], start=2):       # 1行目は見出し
            r = (r + [""] * len(COLS))[:len(COLS)]
            d = dict(zip(COLS, r)); d["row"] = i
            if d["date"] and d["time"] and d["kind"]: out.append(d)
        return out

    def set(self, row, **kv):
        """列名→値 をまとめて書く"""
        cells = []
        for k, v in kv.items():
            col = COLS.index(k) + 1
            cells.append(gspread.Cell(row, col, v))
        if cells: self.ws.update_cells(cells, value_input_option="RAW")

    def approved_months(self):
        ws = self.ss.worksheet("承認"); out = set()
        for r in ws.get_all_values()[1:]:
            if len(r) >= 3 and r[1].strip().upper() == "OK" and r[2].strip():
                m = re.match(r"^\s*(\d{4})\D+(\d{1,2})", unicodedata.normalize("NFKC", r[0]))
                if m: out.add(f"{int(m.group(1)):04d}-{int(m.group(2)):02d}")
        return out

    def settings(self):
        ws = self.ss.worksheet("設定")
        return {r[0].strip(): (r[1].strip() if len(r) > 1 else "") for r in ws.get_all_values() if r and r[0].strip()}

    def set_setting(self, key, value):
        ws = self.ss.worksheet("設定")
        for i, r in enumerate(ws.get_all_values(), start=1):
            if r and r[0].strip() == key:
                ws.update(f"B{i}", [[str(value)]], value_input_option="RAW"); return   # RAW＝文字列のまま（数値に変換されない）
        ws.append_row([key, str(value)], value_input_option="RAW")

def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
