# -*- coding: utf-8 -*-
"""
Instagram 公式API（Instagram API with Instagram Login）で投稿する
  - ストーリーズ（画像/動画）、リール、カルーセル、単画像
  - メディアは公開URLに置いてから container を作り、FINISHED を待って publish
ドキュメント: https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/content-publishing
"""
import os, time, requests

def host_for(token):
    """トークンの種類でAPIホストを選ぶ:
       EAA… = Facebook Graph（Metaの「統合ログイン／システムユーザー」トークン、無期限）→ graph.facebook.com
       IG…  = Instagram Login の長期トークン（60日）→ graph.instagram.com"""
    env = os.environ.get("IG_API_HOST")
    if env: return env
    return "https://graph.facebook.com" if str(token).startswith("EAA") else "https://graph.instagram.com"
API_VER = "v26.0"

class InstagramError(Exception):
    pass

class Instagram:
    def __init__(self, ig_user_id, access_token):
        self.uid = str(ig_user_id); self.token = access_token
        self.host = host_for(access_token); self.api = f"{self.host}/{API_VER}"
        self.is_fb = self.host.endswith("facebook.com")

    # ---- 低レベル
    @staticmethod
    def _parse(r):
        try: j = r.json()
        except ValueError: raise InstagramError(f"HTTP {r.status_code}: {r.text[:200]}")
        if "error" in j: raise InstagramError(j["error"].get("message", str(j)))
        return j

    def _post(self, path, **params):
        params["access_token"] = self.token
        return self._parse(requests.post(f"{self.api}/{path}", data=params, timeout=60))

    def _get(self, path, **params):
        params["access_token"] = self.token
        return self._parse(requests.get(f"{self.api}/{path}", params=params, timeout=60))

    def wait_ready(self, container_id, timeout=600):
        """動画の処理が終わるまで待つ（FINISHED / ERROR / EXPIRED）"""
        t0 = time.time()
        while time.time() - t0 < timeout:
            j = self._get(container_id, fields="status_code,status")
            s = j.get("status_code")
            if s == "FINISHED": return True
            if s in ("ERROR", "EXPIRED"): raise InstagramError(f"container {container_id}: {j}")
            time.sleep(20)
        raise InstagramError(f"container {container_id}: timeout")

    def publish_only(self, container_id):
        """公開だけ行い media_id を返す（この後の失敗は投稿失敗ではない）"""
        return self._post(f"{self.uid}/media_publish", creation_id=container_id)["id"]

    def permalink(self, media_id):
        return self._get(media_id, fields="permalink").get("permalink", "")

    def publish(self, container_id):
        media_id = self.publish_only(container_id)
        return media_id, self.permalink(media_id)

    # ---- コンテナ作成（投稿はまだしない）
    def container_story(self, media_url, is_video):
        key = "video_url" if is_video else "image_url"
        return self._post(f"{self.uid}/media", media_type="STORIES", **{key: media_url})["id"]

    def container_reel(self, video_url, caption, cover_url=None, share_to_feed=True):
        p = dict(media_type="REELS", video_url=video_url, caption=caption, share_to_feed="true" if share_to_feed else "false")
        if cover_url: p["cover_url"] = cover_url
        return self._post(f"{self.uid}/media", **p)["id"]

    def container_image(self, image_url, caption):
        return self._post(f"{self.uid}/media", image_url=image_url, caption=caption)["id"]

    def container_carousel(self, image_urls, caption):
        children = []
        for u in image_urls:
            children.append(self._post(f"{self.uid}/media", image_url=u, is_carousel_item="true")["id"])
        for c in children: self.wait_ready(c, timeout=180)
        return self._post(f"{self.uid}/media", media_type="CAROUSEL", children=",".join(children), caption=caption)["id"]

    # ---- 便利
    def quota(self):
        j = self._get(f"{self.uid}/content_publishing_limit", fields="quota_usage,config")
        return j.get("data", [{}])[0]

    def needs_refresh(self):
        """Facebook Graph のシステムユーザートークンは無期限なので延長不要"""
        return not self.is_fb

    def refresh_token(self):
        """長期トークン（60日）を延長。24時間以上経ったトークンなら何度でも可"""
        if self.is_fb: return self.token, None
        r = self._parse(requests.get(f"{self.host}/refresh_access_token", params={"grant_type": "ig_refresh_token", "access_token": self.token}, timeout=60))
        if "access_token" not in r: raise InstagramError(str(r))
        self.token = r["access_token"]; return r["access_token"], r.get("expires_in")

    def me(self):
        """{'user_id': IGアカウントID, 'username': ...} を返す（ホストの違いを吸収）"""
        if self.is_fb:
            j = self._get(self.uid, fields="id,username,name")
            return {"user_id": j.get("id"), "username": j.get("username"), "name": j.get("name")}
        return self._get("me", fields="user_id,username,account_type")
