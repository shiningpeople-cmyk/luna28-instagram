# -*- coding: utf-8 -*-
"""Instagram Graph API のモック（テスト用）: python3 tests/mock_graph.py 8765"""
import json, sys, time, re
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

STATE = {"containers": {}, "published": [], "n": 100}

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _json(self, obj, code=200):
        b = json.dumps(obj).encode(); self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        u = urlparse(self.path); q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if "access_token" not in q: return self._json({"error": {"message": "no token"}}, 400)
        if u.path == "/refresh_access_token": return self._json({"access_token": "REFRESHED_" + q["access_token"][:6], "token_type": "bearer", "expires_in": 5183944})
        m = re.match(r"^/v\d+\.\d+/(.+)$", u.path)
        if not m: return self._json({"error": {"message": "bad path"}}, 404)
        p = m.group(1)
        if p == "me": return self._json({"user_id": "17841400000000000", "username": "luna28.japan", "account_type": "BUSINESS", "id": "1"})
        if p.endswith("/content_publishing_limit"): return self._json({"data": [{"quota_usage": len(STATE["published"]), "config": {"quota_total": 100, "quota_duration": 86400}}]})
        if p in STATE["containers"]:
            c = STATE["containers"][p]
            # 動画は作成から2秒後にFINISHED
            st = "FINISHED" if (time.time() - c["t"] > (2 if c.get("video") else 0)) else "IN_PROGRESS"
            return self._json({"id": p, "status_code": st, "status": st})
        if p in STATE["published"]: return self._json({"id": p, "permalink": f"https://www.instagram.com/p/MOCK{p}/", "media_type": "IMAGE", "timestamp": "2026-12-01T11:00:00+0000"})
        return self._json({"error": {"message": f"unknown {p}"}}, 400)
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0)); body = parse_qs(self.rfile.read(n).decode()); b = {k: v[0] for k, v in body.items()}
        u = urlparse(self.path); m = re.match(r"^/v\d+\.\d+/(\d+)/(media|media_publish)$", u.path)
        if not m: return self._json({"error": {"message": "bad path " + u.path}}, 404)
        if "access_token" not in b: return self._json({"error": {"message": "no token"}}, 400)
        STATE["n"] += 1; cid = str(STATE["n"])
        if m.group(2) == "media":
            mt = b.get("media_type", "IMAGE")
            if mt == "CAROUSEL":
                kids = b.get("children", "").split(",")
                if not (2 <= len(kids) <= 20) or any(k not in STATE["containers"] for k in kids): return self._json({"error": {"message": "invalid children"}}, 400)
            elif mt in ("REELS", "STORIES") and not (b.get("video_url") or b.get("image_url")): return self._json({"error": {"message": "video_url required"}}, 400)
            elif mt == "IMAGE" and not b.get("image_url"): return self._json({"error": {"message": "image_url required"}}, 400)
            for key in ("image_url", "video_url"):
                if b.get(key) and not b[key].startswith("https://"): return self._json({"error": {"message": "url must be https"}}, 400)
            STATE["containers"][cid] = {"t": time.time(), "video": bool(b.get("video_url")), "params": b}
            return self._json({"id": cid})
        else:
            c = STATE["containers"].get(b.get("creation_id"))
            if not c: return self._json({"error": {"message": "unknown creation_id"}}, 400)
            if c.get("video") and time.time() - c["t"] < 2: return self._json({"error": {"message": "Media ID is not available"}}, 400)
            STATE["published"].append(cid); return self._json({"id": cid})

if __name__ == "__main__":
    HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
