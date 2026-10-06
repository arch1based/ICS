"""
ITNow Signage - τοπικός server για προβολή προσφορών σε οθόνη καταστήματος.

Μόνο Python standard library (χωρίς εγκαταστάσεις).
  Προβολή:   http://localhost:8765/
  Ρυθμίσεις: http://localhost:8765/admin
"""
import datetime
import json
import mimetypes
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8765
BASE = os.path.dirname(os.path.abspath(sys.argv[0] if getattr(sys, "frozen", False) else __file__))
MEDIA = BASE  # οι φάκελοι προσφορών βρίσκονται δίπλα στο πρόγραμμα (C:\ITNow-Signage\...)
CONFIG = os.path.join(BASE, "schedule.json")

# Οι δύο βασικοί φάκελοι: πρώτα παίζουν της εβδομάδας, μετά (έξτρα) της ημέρας
GROUPS = ["Προσφορές Εβδομάδας", "Προσφορές Ημέρας"]

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
VIDEO_EXT = {".mp4", ".webm", ".ogg", ".m4v", ".mov"}

DEFAULT_CONFIG = {
    "image_seconds": 8,
    "transition": "random",   # fade | slide | zoom | flip | blur | random
    "transition_ms": 1200,
    "video_sound": False,
    "campaigns": {},          # "Ομάδα/Φάκελος": {"enabled", "days": [0..6], "from", "to"}
}


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG, encoding="utf-8") as f:
            cfg.update(json.load(f))
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg):
    tmp = CONFIG + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CONFIG)


def media_files(folder):
    out = []
    for name in sorted(os.listdir(folder), key=str.lower):
        ext = os.path.splitext(name)[1].lower()
        if ext in IMAGE_EXT or ext in VIDEO_EXT:
            out.append((name, "video" if ext in VIDEO_EXT else "image"))
    return out


def list_campaigns():
    """Κάθε υποφάκελος μέσα στις ομάδες = μία καμπάνια. Αρχεία απευθείας στην ομάδα = καμπάνια '(γενικά)'."""
    result = []
    for group in GROUPS:
        gdir = os.path.join(MEDIA, group)
        os.makedirs(gdir, exist_ok=True)
        if media_files(gdir):
            result.append((group, "", gdir))
        for sub in sorted(os.listdir(gdir), key=str.lower):
            p = os.path.join(gdir, sub)
            if os.path.isdir(p):
                result.append((group, sub, p))
    return result


def is_active(rule, today):
    if not rule.get("enabled", True):
        return False
    days = rule.get("days", list(range(7)))
    if today.weekday() not in days:
        return False
    try:
        if rule.get("from") and today < datetime.date.fromisoformat(rule["from"]):
            return False
        if rule.get("to") and today > datetime.date.fromisoformat(rule["to"]):
            return False
    except ValueError:
        pass
    return True


def campaigns_info(today):
    cfg = load_config()
    info = []
    for group, sub, path in list_campaigns():
        key = f"{group}/{sub}" if sub else group
        rule = cfg["campaigns"].get(key, {})
        files = media_files(path)
        info.append({
            "key": key, "group": group, "name": sub or "(αρχεία απευθείας στον φάκελο)",
            "enabled": rule.get("enabled", True),
            "days": rule.get("days", list(range(7))),
            "from": rule.get("from", ""), "to": rule.get("to", ""),
            "count": len(files), "active": is_active(rule, today) and bool(files),
            "files": [{"url": "/media/" + urllib.parse.quote(f"{key}/{n}"), "type": t, "name": n} for n, t in files],
        })
    return cfg, info


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send_json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_file(self, path, ctype=None):
        if not os.path.isfile(path):
            self.send_error(404)
            return
        size = os.path.getsize(path)
        ctype = ctype or mimetypes.guess_type(path)[0] or "application/octet-stream"
        start, end = 0, size - 1
        rng = self.headers.get("Range")
        if rng and rng.startswith("bytes="):
            s, _, e = rng[6:].split(",")[0].partition("-")
            try:
                if s:
                    start = int(s)
                    end = int(e) if e else size - 1
                else:
                    start = max(0, size - int(e))
                end = min(end, size - 1)
            except ValueError:
                start, end = 0, size - 1
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        else:
            self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        try:
            with open(path, "rb") as f:
                f.seek(start)
                left = end - start + 1
                while left > 0:
                    chunk = f.read(min(1 << 20, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
        except (ConnectionError, OSError):
            pass

    def do_GET(self):
        path = urllib.parse.unquote(urllib.parse.urlparse(self.path).path)
        if path in ("/", "/player"):
            return self.send_file(os.path.join(BASE, "web", "player.html"), "text/html; charset=utf-8")
        if path == "/admin":
            return self.send_file(os.path.join(BASE, "web", "admin.html"), "text/html; charset=utf-8")
        if path == "/api/playlist":
            today = datetime.date.today()
            cfg, info = campaigns_info(today)
            items = []
            for group in GROUPS:  # πρώτα εβδομάδας, μετά ημέρας
                for c in info:
                    if c["group"] == group and c["active"]:
                        items.extend(c["files"])
            return self.send_json({k: cfg[k] for k in ("image_seconds", "transition", "transition_ms", "video_sound")}
                                  | {"date": today.isoformat(), "items": items})
        if path == "/api/config":
            cfg, info = campaigns_info(datetime.date.today())
            cfg = {k: v for k, v in cfg.items() if k != "campaigns"}
            return self.send_json({"settings": cfg, "campaigns": info, "media_dir": MEDIA})
        if path.startswith("/media/"):
            full = os.path.realpath(os.path.join(MEDIA, path[len("/media/"):]))
            if not any(full.startswith(os.path.realpath(os.path.join(MEDIA, g)) + os.sep) for g in GROUPS):
                return self.send_error(403)
            return self.send_file(full)
        self.send_error(404)

    def do_POST(self):
        if urllib.parse.urlparse(self.path).path != "/api/config":
            return self.send_error(404)
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))).decode("utf-8"))
        except ValueError:
            return self.send_json({"ok": False}, 400)
        cfg = load_config()
        for k in ("image_seconds", "transition", "transition_ms", "video_sound"):
            if k in body.get("settings", {}):
                cfg[k] = body["settings"][k]
        for c in body.get("campaigns", []):
            cfg["campaigns"][c["key"]] = {
                "enabled": bool(c.get("enabled", True)),
                "days": sorted(int(d) for d in c.get("days", []) if 0 <= int(d) <= 6),
                "from": c.get("from", ""), "to": c.get("to", ""),
            }
        save_config(cfg)
        self.send_json({"ok": True})


def make_server():
    for g in GROUPS:
        os.makedirs(os.path.join(MEDIA, g), exist_ok=True)
    return ThreadingHTTPServer(("127.0.0.1", PORT), Handler)


def main():
    srv = make_server()
    print(f"ITNow Signage τρέχει στο http://localhost:{PORT}/  (ρυθμίσεις: /admin)")
    print(f"Φάκελος αρχείων: {MEDIA}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
