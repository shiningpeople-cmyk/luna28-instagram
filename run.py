# -*- coding: utf-8 -*-
"""
LUNA28 Instagram 自動投稿ランナー
  A. 準備：7日以内の未処理行の動画・画像を生成 → 公開用ブランチ media に push → 予定表にプレビューURLを書き「確認待ち」にする
  B. 投稿：「確認待ち」かつ 承認列が OK の行を、予定時刻（2時間前〜40分後の窓）に Instagram へ投稿 → 予定表に URL と状態を書き戻す
     承認が無い行は予定時刻を過ぎても投稿せず「見送り」にする（内容はプレビューで確認してから OK を書く）
環境変数: GOOGLE_SA_JSON, SHEET_ID, GITHUB_TOKEN, GITHUB_REPOSITORY（Actionsが自動で入れる）, MEDIA_BASE_URL（任意）, DRY_RUN（任意 "1"）
"""
import os, sys, json, time, shutil, subprocess, datetime, traceback, unicodedata, re, tempfile, requests
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "render"))
from sheet import Sheet, now_jst
from publish import Instagram, InstagramError
import captions

ROOT = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(ROOT, "media")
WINDOW_AFTER = int(os.environ.get("WINDOW_MIN", "40"))     # 予定の何分前から拾うか
WINDOW_BEFORE = 120                                          # 予定を過ぎていても何分までなら投稿するか（起動遅れ対策）
KEEP_DAYS = 12                                               # 公開ブランチに残す日数（7日前に準備＋投稿後も少し残す）
PREP_DAYS = 7                                                # 何日先まで事前に生成するか
DRY = os.environ.get("DRY_RUN") == "1"
JST = datetime.timezone(datetime.timedelta(hours=9))
FAILS = []

def log(*a):
    print(now_jst().strftime("%H:%M:%S"), *a, flush=True)

def fail(sh, row, msg, status="失敗"):
    try: sh.set(row, status=status, log=f"{now_jst():%m/%d %H:%M} {msg}")
    except Exception as e: log("書き戻し失敗", row, e)
    FAILS.append(f"行{row}: {msg}"); log(f"行{row}: {msg}")

def weekday_jp(d):
    return "月火水木金土日"[d.weekday()]

def parse_when(r):
    ds = unicodedata.normalize("NFKC", r["date"]).strip(); ts = unicodedata.normalize("NFKC", r["time"]).strip()
    m = re.match(r"^(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})", ds)
    if not m: raise ValueError(f"日付の形式が読めません: {r['date']}（2026/12/01 のように）")
    y, mo, d = (int(x) for x in m.groups())
    hm = ts.split(":")
    if len(hm) < 2 or not hm[0].isdigit() or not hm[1].isdigit(): raise ValueError(f"時刻の形式が読めません: {r['time']}（12:00 のように）")
    return datetime.datetime(y, mo, d, int(hm[0]), int(hm[1]), tzinfo=JST)

# ------------------------------------------------------------ メディア生成
def build(r, stamp):
    kind = r["kind"].strip(); key = r["key"].strip()
    when = parse_when(r)
    date_label = f"{when.month}月{when.day}日({weekday_jp(when)})"
    out_dir = os.path.join(MEDIA_DIR, when.strftime("%Y%m%d")); os.makedirs(out_dir, exist_ok=True)
    if kind == "ストーリーズ":
        import render_story
        if not (r["r1"] and r["r2"] and r["r3"] and r["hitokoto"]): raise ValueError("1位・2位・3位・ひとことが未記入")
        out = os.path.join(out_dir, f"story_{stamp}.mp4")
        render_story.render(date_label, [r["r1"], r["r2"], r["r3"]], r["hitokoto"], out)
        return [out], "", True
    jp = os.path.join(ROOT, "content", f"{key}.json")
    if not key or not os.path.exists(jp): raise ValueError(f"原稿キー「{key}」のJSONが content/ にありません")
    spec = json.load(open(jp, encoding="utf-8"))
    txt = json.dumps(spec, ensure_ascii=False)
    if "【要原稿】" in txt or "【○】" in txt: raise ValueError(f"原稿 {key}.json に未確定の印（【要原稿】/【○】）があります")
    if kind == "リール":
        import render_reel
        out = os.path.join(out_dir, f"reel_{stamp}.mp4"); render_reel.render(spec, out)
        return [out], r["caption"] or captions.reel(spec), True
    if kind == "カルーセル":
        import render_carousel
        files = render_carousel.render(spec, os.path.join(out_dir, f"carousel_{stamp}"))
        return files, r["caption"] or captions.carousel(spec), False
    raise ValueError(f"種類が不明: {kind}（ストーリーズ／リール／カルーセル）")

# ------------------------------------------------------------ 公開ブランチ media へ push
def git(args, cwd, check=True):
    p = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    if check and p.returncode != 0: raise RuntimeError(f"git {' '.join(args[:2])}: {p.stderr.strip()[:300]}")
    return p

def publish_media(files, remote_url=None):
    """media/ 以下の新しいファイルを、履歴を持たない公開ブランチ media に force push（古い日付のものは消す）"""
    if DRY: return
    if remote_url is None:
        repo = os.environ.get("GITHUB_REPOSITORY"); token = os.environ.get("GITHUB_TOKEN")
        if not (repo and token): raise RuntimeError("GITHUB_REPOSITORY / GITHUB_TOKEN がありません（Actions 以外から実行？）")
        remote_url = f"https://x-access-token:{token}@github.com/{repo}.git"
    url = remote_url
    tmp = tempfile.mkdtemp(prefix="media_")
    try:
        p = subprocess.run(["git", "clone", "-q", "--depth", "1", "--branch", "media", url, tmp], capture_output=True, text=True)
        if p.returncode != 0:
            shutil.rmtree(tmp); os.makedirs(tmp); git(["init", "-q"], tmp)
        git(["config", "user.name", "luna28-bot"], tmp); git(["config", "user.email", "bot@luna28.jp"], tmp)
        cutoff = (now_jst() - datetime.timedelta(days=KEEP_DAYS)).strftime("%Y%m%d")
        mdir = os.path.join(tmp, "media")
        if os.path.isdir(mdir):
            for d in os.listdir(mdir):
                if re.fullmatch(r"\d{8}", d) and d < cutoff: shutil.rmtree(os.path.join(mdir, d), ignore_errors=True)
        for f in files:
            dst = os.path.join(tmp, os.path.relpath(f, ROOT)); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(f, dst)
        # 履歴を持たせない：毎回「このファイル一式」だけの1コミットにして force push
        git(["checkout", "-q", "--orphan", "flat"], tmp); git(["add", "-A"], tmp)
        git(["commit", "-q", "--allow-empty", "-m", f"media {now_jst():%Y-%m-%d %H:%M}"], tmp)
        last = None
        for i in range(3):
            p = subprocess.run(["git", "push", "-q", "--force", url, "HEAD:media"], cwd=tmp, capture_output=True, text=True)
            if p.returncode == 0: return
            last = p.stderr.strip()[:300]; time.sleep(8)
        raise RuntimeError(f"git push に失敗: {last}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def public_url(path, base):
    return base.rstrip("/") + "/" + os.path.relpath(path, ROOT).replace(os.sep, "/")

def wait_url(url, timeout=600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            r = requests.head(url, timeout=20, allow_redirects=True)
            if r.status_code == 200: return True
        except Exception: pass
        time.sleep(15)
    raise RuntimeError(f"公開URLが開けません: {url}")

def default_base():
    repo = os.environ.get("GITHUB_REPOSITORY")
    return f"https://raw.githubusercontent.com/{repo}/media" if repo else ""

# ------------------------------------------------------------ メイン
def main():
    sh = Sheet(os.environ["GOOGLE_SA_JSON"], os.environ["SHEET_ID"])
    st = sh.settings()
    base = os.environ.get("MEDIA_BASE_URL") or st.get("media_base_url") or default_base()
    ig = None
    if not DRY:
        ig = Instagram(st.get("ig_user_id", ""), st.get("access_token", ""))
        me = ig.me(); uid = str(me.get("user_id", "")).strip()        # シートの表示値（1.78E+16 等）に頼らない
        if uid:
            ig.uid = uid
            if uid != st.get("ig_user_id", "").strip():
                try: sh.set_setting("ig_user_id", uid)
                except Exception: pass
        log("Instagram:", me.get("username"), uid)
        try:
            upd = datetime.date.fromisoformat(st.get("token_updated", "").strip()) if st.get("token_updated", "").strip() else None
        except ValueError:
            upd = None
        if ig.needs_refresh() and (upd is None or (now_jst().date() - upd).days >= 7):
            try:
                tok, exp = ig.refresh_token(); sh.set_setting("access_token", tok); sh.set_setting("token_updated", now_jst().date().isoformat())
                log("token refreshed, expires_in", exp)
            except Exception as e:
                log("token refresh failed:", e)
    now = now_jst()
    rows = sh.rows()
    # ---------- A. 準備（生成してプレビューURLを書く）
    prep = []
    for r in rows:
        if r["status"].strip() != "": continue
        try: when = parse_when(r)
        except Exception as e:
            fail(sh, r["row"], str(e)); continue
        if -WINDOW_BEFORE <= (when - now).total_seconds() / 60 <= PREP_DAYS * 1440: prep.append((when, r))
    prep.sort(key=lambda x: x[0]); log(f"準備 {len(prep)} 件")
    jobs = []
    for when, r in prep:
        try:
            files, caption, is_video = build(r, when.strftime("%Y%m%d_%H%M"))
            jobs.append((when, r, files, caption, is_video)); log(f"生成OK 行{r['row']} {r['kind']} {len(files)}ファイル")
        except Exception as e:
            fail(sh, r["row"], f"生成エラー: {e}")
    if jobs:
        try:
            publish_media([f for j in jobs for f in j[2]])
            for when, r, files, caption, is_video in jobs:
                urls = [public_url(f, base) for f in files]
                r["media"] = urls[0]; r["caption"] = caption; r["status"] = "確認待ち"; r["preview"] = "\n".join(urls)
                sh.set(r["row"], status="確認待ち", media=urls[0], preview="\n".join(urls), caption=caption,
                       log=f"{now_jst():%m/%d %H:%M} 生成済み。プレビューを見て承認列に OK を書いてください")
        except Exception as e:
            for when, r, *_ in jobs: fail(sh, r["row"], f"公開用ブランチへの保存に失敗: {e}")
    if DRY:
        for when, r, files, caption, is_video in jobs: log("DRY", r["row"], [os.path.basename(f) for f in files], caption[:40])
        return
    # ---------- B. 投稿（確認待ち ＋ 承認OK ＋ 時間窓）
    due = []
    for r in rows:
        if r["status"].strip() not in ("確認待ち", "予約"): continue
        try: when = parse_when(r)
        except Exception: continue
        delta = (when - now).total_seconds() / 60
        if delta > WINDOW_AFTER: continue
        if r["ok"].strip().upper() != "OK":
            if delta < -WINDOW_BEFORE: fail(sh, r["row"], f"見送り（承認がないまま予定 {when:%m/%d %H:%M} を過ぎたため未投稿。投稿するなら日時を直して承認に OK）", status="見送り")
            continue
        if delta < -WINDOW_BEFORE:
            fail(sh, r["row"], f"時間切れ（予定 {when:%m/%d %H:%M} を2時間以上過ぎていたため未投稿。投稿するなら日時を直して状態を「確認待ち」に）"); continue
        due.append((when, r))
    due.sort(key=lambda x: x[0]); log(f"投稿対象 {len(due)} 件")
    if not due: return
    ready = []
    for when, r in due:
        try:
            urls = [u.strip() for u in r["preview"].split("\n") if u.strip()]
            caption = r["caption"]; is_video = urls[0].lower().endswith(".mp4") if urls else False
            if not urls:
                files, caption, is_video = build(r, when.strftime("%Y%m%d_%H%M")); publish_media(files); urls = [public_url(f, base) for f in files]; time.sleep(15)
            for u in urls: wait_url(u)
            kind = r["kind"].strip()
            if kind == "ストーリーズ": cid = ig.container_story(urls[0], is_video)
            elif kind == "リール": cid = ig.container_reel(urls[0], caption)
            else: cid = ig.container_carousel(urls, caption)
            ig.wait_ready(cid)
            ready.append((when, r, cid, urls[0]))
            sh.set(r["row"], status="予約", media=urls[0], log=f"{now_jst():%m/%d %H:%M} コンテナ作成 {cid}")
            log("コンテナOK", r["row"], cid)
        except Exception as e:
            fail(sh, r["row"], f"API: {e}")
    for when, r, cid, url in sorted(ready, key=lambda x: x[0]):
        wait = (when - now_jst()).total_seconds()
        if wait > 0: log(f"{wait:.0f}秒待機 → 行{r['row']}"); time.sleep(wait)
        try:
            mid = ig.publish_only(cid)
        except Exception as e:
            fail(sh, r["row"], f"publish: {e}"); continue
        # 投稿は成功。ここから先の失敗で「失敗」にはしない（二重投稿を防ぐ）
        try: sh.set(r["row"], status="投稿済み", log=f"{now_jst():%m/%d %H:%M:%S} 投稿 {mid}")
        except Exception as e: log("書き戻し失敗（投稿は成功）", r["row"], e); FAILS.append(f"行{r['row']}: 投稿は成功したがシートに書けず {e}")
        try:
            link = ig.permalink(mid); sh.set(r["row"], url=link); log("投稿OK", r["row"], link)
        except Exception as e: log("URL取得失敗（投稿は成功）", r["row"], e)

def summary(lines):
    p = os.environ.get("GITHUB_STEP_SUMMARY")
    if p:
        with open(p, "a", encoding="utf-8") as fp: fp.write("\n".join(lines) + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        traceback.print_exc(); summary(["## LUNA28 自動投稿: 異常終了", f"```\n{e}\n```"]); sys.exit(1)
    if FAILS:
        summary(["## LUNA28 自動投稿: 失敗あり"] + ["- " + x for x in FAILS]); sys.exit(1)
    summary(["## LUNA28 自動投稿: 正常終了"])
