"""
ITNow Signage - προβολή προσφορών σε οθόνες καταστήματος (itnow.gr).

Δύο ρόλοι (ίδιο πρόγραμμα):
  * Κεντρικός: κρατά τους φακέλους & το πρόγραμμα ημερών, έχει τον Πίνακα Ελέγχου
               και δίνει εντολές στις οθόνες του δικτύου.
  * Οθόνη:     βρίσκει μόνη της τον κεντρικό στο δίκτυο, κατεβάζει ό,τι πρέπει να παίξει
               και το παίζει — συνεχίζει να παίζει ακόμα κι αν ο κεντρικός κλείσει.

Μόνο Python standard library (χωρίς εγκαταστάσεις).
"""
import datetime
import hashlib
import json
import mimetypes
import os
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "1.2.0"
CENTRAL_PORT = 8765       # HTTP (Πίνακας Ελέγχου, προβολή, συγχρονισμός)
PORT = int(os.environ.get("ITNOW_PORT", CENTRAL_PORT))  # αλλάζει μόνο για δοκιμές σε ίδιο PC
DISCOVERY_PORT = 8766     # UDP: οι οθόνες βρίσκουν τον κεντρικό
FROZEN = getattr(sys, "frozen", False)  # True όταν τρέχει ως ITNow-Signage.exe
BASE = os.path.dirname(os.path.abspath(sys.executable if FROZEN else __file__))
WEB = os.path.join(getattr(sys, "_MEIPASS", BASE), "web")
TECH_PIN = "1995"  # κωδικός τεχνικού
MEDIA = BASE       # οι φάκελοι προσφορών βρίσκονται δίπλα στο πρόγραμμα (C:\ITNow-Signage\...)
CACHE = os.path.join(BASE, "cache")  # οθόνη: τοπικό αντίγραφο αρχείων από τον κεντρικό
CONFIG = os.path.join(BASE, "schedule.json")
ONLINE_SECS = 60   # μια οθόνη θεωρείται online αν επικοινώνησε μέσα σε τόσα δευτερόλεπτα
SYNC_SECS = 15

# Οι δύο βασικοί φάκελοι: πρώτα παίζουν της εβδομάδας, μετά (έξτρα) της ημέρας
GROUPS = ["Προσφορές Εβδομάδας", "Προσφορές Ημέρας"]
SETTING_KEYS = ("image_seconds", "transition", "transition_ms", "video_sound")

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
VIDEO_EXT = {".mp4", ".webm", ".ogg", ".m4v", ".mov"}

DEFAULT_CONFIG = {
    "mode": "central",        # central | client
    "screen_name": "",        # όνομα αυτής της οθόνης (προεπιλογή: όνομα υπολογιστή)
    "central_host": "",       # οθόνη: IP του κεντρικού (κενό = αυτόματη αναζήτηση)
    "image_seconds": 8,
    "transition": "random",   # fade | slide | zoom | flip | blur | random
    "transition_ms": 1200,
    "video_sound": False,
    "update_url": "",         # σύνδεσμος Google Drive προς το version.json
    "known_screens": [],      # κεντρικός: οθόνες που έχουν συνδεθεί ποτέ
    "campaigns": {},          # "Ομάδα/Φάκελος": {"enabled", "days": [0..6], "from", "to", "screens": []}
}

_cfg_lock = threading.Lock()


def load_config():
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    try:
        with open(CONFIG, encoding="utf-8") as f:
            cfg.update(json.load(f))
    except (OSError, ValueError):
        pass
    if not cfg["screen_name"]:
        cfg["screen_name"] = socket.gethostname()
    return cfg


def save_config(cfg):
    with _cfg_lock:
        tmp = CONFIG + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        os.replace(tmp, CONFIG)


def is_client():
    return load_config()["mode"] == "client"


# ---------------- Φάκελοι & πρόγραμμα (κεντρικός) ----------------
def media_files(folder):
    out = []
    for name in sorted(os.listdir(folder), key=str.lower):
        ext = os.path.splitext(name)[1].lower()
        if ext in IMAGE_EXT or ext in VIDEO_EXT:
            st = os.stat(os.path.join(folder, name))
            out.append({"name": name, "type": "video" if ext in VIDEO_EXT else "image",
                        "size": st.st_size, "mtime": int(st.st_mtime)})
    return out


def list_campaigns():
    """Κάθε υποφάκελος μέσα στις ομάδες = μία καμπάνια. Αρχεία απευθείας στην ομάδα = ξεχωριστή καμπάνια."""
    result = []
    for group in GROUPS:
        gdir = os.path.join(MEDIA, group)
        if not os.path.isdir(gdir):
            continue
        if media_files(gdir):
            result.append((group, "", gdir))
        for sub in sorted(os.listdir(gdir), key=str.lower):
            p = os.path.join(gdir, sub)
            if os.path.isdir(p):
                result.append((group, sub, p))
    return result


def rule_of(cfg, key):
    r = cfg["campaigns"].get(key, {})
    return {"enabled": r.get("enabled", True), "days": r.get("days", list(range(7))),
            "from": r.get("from", ""), "to": r.get("to", ""), "screens": r.get("screens", [])}


def is_active(rule, today):
    if not rule.get("enabled", True) or today.weekday() not in rule.get("days", list(range(7))):
        return False
    try:
        if rule.get("from") and today < datetime.date.fromisoformat(rule["from"]):
            return False
        if rule.get("to") and today > datetime.date.fromisoformat(rule["to"]):
            return False
    except ValueError:
        pass
    return True


def for_screen(rule, screen):
    return not rule.get("screens") or screen in rule["screens"]


def campaigns_info(today, cfg=None):
    cfg = cfg or load_config()
    info = []
    for group, sub, path in list_campaigns():
        key = f"{group}/{sub}" if sub else group
        rule = rule_of(cfg, key)
        files = media_files(path)
        for f in files:
            f["url"] = "/media/" + urllib.parse.quote(f"{key}/{f['name']}")
        info.append({"key": key, "group": group, "name": sub or "(αρχεία απευθείας στον φάκελο)",
                     **rule, "count": len(files), "active": is_active(rule, today) and bool(files),
                     "files": files})
    return cfg, info


def build_playlist(campaigns, today):
    """Λίστα αναπαραγωγής: πρώτα όλες οι ενεργές της εβδομάδας, μετά οι ενεργές της ημέρας."""
    items = []
    for group in GROUPS:
        for c in campaigns:
            if c["group"] == group and is_active(c, today):
                items.extend({"url": f["url"], "type": f["type"], "name": f["name"]} for f in c["files"])
    return items


# ---------------- Οθόνες δικτύου (κεντρικός) ----------------
SCREENS = {}    # όνομα -> {"ip", "last_seen", "version", "running", "local"}
COMMANDS = {}   # όνομα -> "start" | "stop" | "restart"


def screens_status():
    cfg = load_config()
    me = cfg["screen_name"]
    now = time.time()
    names = [me] + [n for n in cfg["known_screens"] if n != me]
    out = []
    for n in names:
        s = SCREENS.get(n, {})
        local = n == me
        out.append({"name": n, "local": local, "ip": "" if local else s.get("ip", ""),
                    "online": local or now - s.get("last_seen", 0) < ONLINE_SECS,
                    "running": show_running if local else bool(s.get("running")),
                    "version": VERSION if local else s.get("version", ""),
                    "last_seen": s.get("last_seen", 0), "pending": COMMANDS.get(n, "")})
    return out


def register_screen(name, ip, version, running):
    SCREENS[name] = {"ip": ip, "last_seen": time.time(), "version": version, "running": running}
    cfg = load_config()
    if name not in cfg["known_screens"] and name != cfg["screen_name"]:
        cfg["known_screens"].append(name)
        save_config(cfg)


def discovery_responder():
    """Απαντά στις οθόνες που ψάχνουν τον κεντρικό στο τοπικό δίκτυο."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", DISCOVERY_PORT))
    except OSError:
        return
    while True:
        try:
            data, addr = s.recvfrom(256)
            if data.startswith(b"ITNOW-SIGNAGE?") and not is_client():
                s.sendto(f"ITNOW-SIGNAGE!{CENTRAL_PORT}".encode(), addr)
        except OSError:
            time.sleep(1)


# ---------------- Οθόνη: συγχρονισμός με τον κεντρικό ----------------
client_state = {"connected": False, "last_sync": 0, "host": "", "error": "", "files": 0}


def discover_central(timeout=3):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.settimeout(timeout)
    try:
        s.sendto(b"ITNOW-SIGNAGE?", ("255.255.255.255", DISCOVERY_PORT))
        while True:
            data, addr = s.recvfrom(256)
            if data.startswith(b"ITNOW-SIGNAGE!"):
                return addr[0]
    except OSError:
        return ""
    finally:
        s.close()


def cache_name(f, key):
    h = hashlib.sha1(f"{key}/{f['name']}|{f['size']}|{f['mtime']}".encode("utf-8")).hexdigest()[:20]
    return h + os.path.splitext(f["name"])[1].lower()


def load_client_playlist():
    try:
        with open(os.path.join(CACHE, "playlist.json"), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"settings": {}, "campaigns": []}


def sync_once():
    cfg = load_config()
    host = cfg["central_host"] or discover_central()
    if not host:
        raise RuntimeError("Δεν βρέθηκε κεντρικός υπολογιστής στο δίκτυο")
    base = f"http://{host}:{CENTRAL_PORT}"
    q = urllib.parse.urlencode({"screen": cfg["screen_name"], "version": VERSION, "running": int(show_running)})
    with urllib.request.urlopen(f"{base}/api/sync?{q}", timeout=10) as r:
        data = json.loads(r.read().decode("utf-8"))
    client_state.update(host=host, connected=True, error="")

    # κατέβασμα όσων αρχείων λείπουν
    os.makedirs(CACHE, exist_ok=True)
    keep = {"playlist.json"}
    for c in data["campaigns"]:
        for f in c["files"]:
            local = cache_name(f, c["key"])
            keep.add(local)
            dest = os.path.join(CACHE, local)
            if not os.path.exists(dest):
                with urllib.request.urlopen(base + f["url"], timeout=600) as r, open(dest + ".part", "wb") as out:
                    while chunk := r.read(1 << 20):
                        out.write(chunk)
                os.replace(dest + ".part", dest)
            f["url"] = "/cache/" + local
    with open(os.path.join(CACHE, "playlist.json.tmp"), "w", encoding="utf-8") as fh:
        json.dump({"settings": data["settings"], "campaigns": data["campaigns"]}, fh, ensure_ascii=False)
    os.replace(os.path.join(CACHE, "playlist.json.tmp"), os.path.join(CACHE, "playlist.json"))
    for name in os.listdir(CACHE):  # σβήσιμο αρχείων που δεν χρειάζονται πια
        if name not in keep and not name.endswith(".tmp"):
            try:
                os.remove(os.path.join(CACHE, name))
            except OSError:
                pass
    client_state.update(last_sync=time.time(), files=len(keep) - 1)

    # εντολές από τον κεντρικό
    cmd = data.get("command")
    if cmd in ("start", "restart"):
        start_show()
        remember_show(True)
    elif cmd == "stop":
        stop_show()
        remember_show(False)
    # αυτόματη αναβάθμιση από τον κεντρικό
    if FROZEN and data.get("exe") and vtuple(data.get("version")) > vtuple(VERSION):
        apply_update(base + "/exe")


def client_loop():
    fails = 0
    while True:
        if is_client():
            try:
                sync_once()
                fails = 0
            except Exception as e:  # δίκτυο κ.λπ. — συνεχίζουμε να παίζουμε από το αντίγραφο
                fails += 1
                client_state.update(connected=False, error=str(e))
                if fails >= 3 and load_config()["central_host"]:
                    found = discover_central()  # ίσως άλλαξε IP ο κεντρικός
                    if found:
                        cfg = load_config()
                        cfg["central_host"] = found
                        save_config(cfg)
        time.sleep(SYNC_SECS)


# ---------------- Έλεγχος οθόνης προβολής (Edge/Chrome) ----------------
URL = f"http://localhost:{PORT}/"
PROFILE_ROOT = os.path.join(os.environ.get("LOCALAPPDATA", BASE), "ITNow-Signage")
NO_WINDOW = 0x08000000 if os.name == "nt" else 0
show_running = False


def find_browser():
    for env in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
        base = os.environ.get(env)
        for rel in (r"Microsoft\Edge\Application\msedge.exe", r"Google\Chrome\Application\chrome.exe"):
            if base and os.path.isfile(os.path.join(base, rel)):
                return os.path.join(base, rel)
    return None


def play_on_boot():
    """Ξεκινά η προβολή με τα Windows; Οθόνες: ναι. Κεντρικός: μόνο αν την άφησαν να παίζει."""
    cfg = load_config()
    v = cfg.get("play_on_boot")
    return (cfg["mode"] == "client") if v is None else bool(v)


def remember_show(on):
    cfg = load_config()
    cfg["play_on_boot"] = bool(on)
    save_config(cfg)


def start_show():
    global show_running
    exe = find_browser()
    if not exe:
        return False
    stop_show()
    subprocess.Popen([exe, "--kiosk", URL, "--edge-kiosk-type=fullscreen",
                      "--autoplay-policy=no-user-gesture-required", "--no-first-run",
                      "--disable-features=Translate", "--disable-session-crashed-bubble",
                      "--user-data-dir=" + os.path.join(PROFILE_ROOT, "show")])
    show_running = True
    return True


def stop_show():
    global show_running
    show_running = False
    if os.name == "nt":
        ps = ("Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*ITNow-Signage\\show*' } "
              "| ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }")
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], creationflags=NO_WINDOW)


def open_panel():
    """Ανοίγει τον Πίνακα Ελέγχου σαν ξεχωριστή εφαρμογή (παράθυρο χωρίς μπάρα browser)."""
    exe = find_browser()
    if exe:
        subprocess.Popen([exe, f"--app={URL}admin", "--window-size=1280,860", "--no-first-run",
                          "--user-data-dir=" + os.path.join(PROFILE_ROOT, "panel")])
    else:
        import webbrowser
        webbrowser.open(URL + "admin")


def open_folder(path):
    os.makedirs(path, exist_ok=True)
    if os.name == "nt":
        os.startfile(path)


def safe_folder(key):
    full = os.path.realpath(os.path.join(MEDIA, *key.split("/")))
    if any(full == os.path.realpath(os.path.join(MEDIA, g)) or
           full.startswith(os.path.realpath(os.path.join(MEDIA, g)) + os.sep) for g in GROUPS):
        return full
    return None


# ---------------- Αναβαθμίσεις & επανεκκίνηση ----------------
def drive_direct(url):
    """Μετατρέπει σύνδεσμο κοινής χρήσης Google Drive σε σύνδεσμο απευθείας λήψης."""
    m = re.search(r"/d/([\w-]{10,})", url) or re.search(r"[?&]id=([\w-]{10,})", url)
    if m and "google." in url:
        return f"https://drive.usercontent.google.com/download?id={m.group(1)}&export=download&confirm=t"
    return url


def fetch(url, timeout=60):
    req = urllib.request.Request(drive_direct(url), headers={"User-Agent": f"ITNow-Signage/{VERSION}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def vtuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", str(v))[:4])


def check_update(url):
    info = json.loads(fetch(url, 30).decode("utf-8-sig"))
    latest = str(info.get("version", ""))
    return {"current": VERSION, "latest": latest, "notes": info.get("notes", ""),
            "available": vtuple(latest) > vtuple(VERSION), "exe": info.get("exe", "")}


def restart_app(extra=()):
    """Ξεκινά ξανά το πρόγραμμα (π.χ. μετά από αναβάθμιση ή αλλαγή ρόλου)."""
    def go():
        time.sleep(1)
        args = [sys.executable] if FROZEN else [sys.executable, os.path.join(BASE, "ITNow-Signage.pyw")]
        args += ["--after-update"] + (["--autostart"] if show_running else []) + list(extra)
        subprocess.Popen(args, cwd=BASE)
        os._exit(0)
    threading.Thread(target=go, daemon=True).start()


def apply_update(exe_url):
    """Κατεβάζει το νέο exe, αντικαθιστά το τρέχον και κάνει επανεκκίνηση."""
    if not FROZEN:
        raise RuntimeError("Η αναβάθμιση λειτουργεί μόνο στην έκδοση .exe")
    data = fetch(exe_url, 600)
    if len(data) < 1_000_000 or data[:2] != b"MZ":
        raise RuntimeError("Το αρχείο που κατέβηκε δεν είναι έγκυρο .exe (ελέγξτε ότι ο σύνδεσμος είναι δημόσιος)")
    exe = sys.executable
    with open(exe + ".new", "wb") as f:
        f.write(data)
    if os.path.exists(exe + ".old"):
        os.remove(exe + ".old")
    os.replace(exe, exe + ".old")       # τα Windows επιτρέπουν μετονομασία του exe που τρέχει
    os.replace(exe + ".new", exe)
    restart_app()


# ---------------- HTTP ----------------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def is_local(self):
        return self.client_address[0] in ("127.0.0.1", "::1")

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

    # ---- GET ----
    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(url.path)
        qs = urllib.parse.parse_qs(url.query)

        # Από το δίκτυο (οθόνες) επιτρέπονται μόνο: συγχρονισμός, αρχεία, exe αναβάθμισης
        if path == "/api/sync":
            return self.api_sync(qs)
        if path.startswith("/media/"):
            full = os.path.realpath(os.path.join(MEDIA, path[len("/media/"):]))
            if not any(full.startswith(os.path.realpath(os.path.join(MEDIA, g)) + os.sep) for g in GROUPS):
                return self.send_error(403)
            return self.send_file(full)
        if path == "/exe":
            return self.send_file(sys.executable, "application/octet-stream") if FROZEN else self.send_error(404)
        if not self.is_local():
            return self.send_error(403)

        cfg = load_config()
        client = cfg["mode"] == "client"
        if path in ("/", "/player"):
            return self.send_file(os.path.join(WEB, "player.html"), "text/html; charset=utf-8")
        if path == "/admin":
            return self.send_file(os.path.join(WEB, "client.html" if client else "admin.html"), "text/html; charset=utf-8")
        if path.startswith("/cache/"):
            name = os.path.basename(path)
            return self.send_file(os.path.join(CACHE, name))
        if path == "/api/playlist":
            today = datetime.date.today()
            if client:
                pl = load_client_playlist()
                settings, campaigns = pl["settings"], pl["campaigns"]
            else:
                _, campaigns = campaigns_info(today, cfg)
                campaigns = [c for c in campaigns if for_screen(c, cfg["screen_name"])]
                settings = {k: cfg[k] for k in SETTING_KEYS}
            return self.send_json({**{k: cfg[k] for k in SETTING_KEYS}, **settings,
                                   "date": today.isoformat(), "items": build_playlist(campaigns, today)})
        if path == "/api/config":
            _, info = campaigns_info(datetime.date.today(), cfg)
            return self.send_json({"settings": {k: cfg[k] for k in SETTING_KEYS}, "campaigns": info,
                                   "media_dir": MEDIA, "groups": GROUPS, "show_running": show_running,
                                   "today": datetime.date.today().weekday(), "version": VERSION,
                                   "screens": screens_status(), "screen_name": cfg["screen_name"]})
        if path == "/api/client":
            pl = load_client_playlist()
            today = datetime.date.today()
            return self.send_json({**client_state, "screen_name": cfg["screen_name"], "central_host": cfg["central_host"],
                                   "version": VERSION, "show_running": show_running,
                                   "today_items": len(build_playlist(pl["campaigns"], today)),
                                   "ago": int(time.time() - client_state["last_sync"]) if client_state["last_sync"] else None})
        self.send_error(404)

    def api_sync(self, qs):
        cfg = load_config()
        if cfg["mode"] != "central":
            return self.send_json({"error": "not central"}, 409)
        name = (qs.get("screen") or [""])[0][:60] or self.client_address[0]
        register_screen(name, self.client_address[0], (qs.get("version") or [""])[0],
                        (qs.get("running") or ["0"])[0] == "1")
        _, info = campaigns_info(datetime.date.today(), cfg)
        campaigns = [{k: c[k] for k in ("key", "group", "enabled", "days", "from", "to", "files")}
                     for c in info if for_screen(c, name)]
        self.send_json({"settings": {k: cfg[k] for k in SETTING_KEYS}, "campaigns": campaigns,
                        "command": COMMANDS.pop(name, None), "version": VERSION, "exe": FROZEN})

    # ---- POST (μόνο από αυτόν τον υπολογιστή) ----
    def do_POST(self):
        if not self.is_local():
            return self.send_error(403)
        path = urllib.parse.urlparse(self.path).path
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))).decode("utf-8") or "{}")
        except ValueError:
            return self.send_json({"ok": False}, 400)
        cfg = load_config()

        if path == "/api/show":
            ok = start_show() if body.get("action") == "start" else (stop_show() or True)
            remember_show(show_running)
            return self.send_json({"ok": ok, "show_running": show_running})
        if path == "/api/screen":  # εντολή σε οθόνη του δικτύου
            name, action = body.get("name", ""), body.get("action", "")
            if name == cfg["screen_name"]:
                ok = start_show() if action in ("start", "restart") else (stop_show() or True)
                remember_show(show_running)
                return self.send_json({"ok": ok})
            if action == "forget":
                cfg["known_screens"] = [n for n in cfg["known_screens"] if n != name]
                save_config(cfg)
                SCREENS.pop(name, None)
            elif action in ("start", "stop", "restart"):
                COMMANDS[name] = action
            return self.send_json({"ok": True})
        if path == "/api/open":
            folder = safe_folder(body.get("key", ""))
            if folder:
                open_folder(folder)
            return self.send_json({"ok": bool(folder)})
        if path == "/api/folder":
            name = str(body.get("name", "")).strip()
            if body.get("group") not in GROUPS or not name or any(c in name for c in '\\/:*?"<>|') or name in (".", ".."):
                return self.send_json({"ok": False}, 400)
            os.makedirs(os.path.join(MEDIA, body["group"], name), exist_ok=True)
            return self.send_json({"ok": True})
        if path == "/api/client":  # ρυθμίσεις οθόνης: όνομα / IP κεντρικού / αναζήτηση
            if "screen_name" in body and str(body["screen_name"]).strip():
                cfg["screen_name"] = str(body["screen_name"]).strip()[:60]
            if "central_host" in body:
                cfg["central_host"] = str(body["central_host"]).strip()
            if body.get("discover"):
                cfg["central_host"] = discover_central() or cfg["central_host"]
            save_config(cfg)
            threading.Thread(target=lambda: _safe(sync_once), daemon=True).start()
            return self.send_json({"ok": True, "central_host": cfg["central_host"]})
        if path.startswith("/api/tech/"):
            return self.api_tech(path, body, cfg)
        if path != "/api/config":
            return self.send_error(404)
        for k in SETTING_KEYS:
            if k in body.get("settings", {}):
                cfg[k] = body["settings"][k]
        for c in body.get("campaigns", []):
            cfg["campaigns"][c["key"]] = {
                "enabled": bool(c.get("enabled", True)),
                "days": sorted(int(d) for d in c.get("days", []) if 0 <= int(d) <= 6),
                "from": c.get("from", ""), "to": c.get("to", ""),
                "screens": [str(s) for s in c.get("screens", [])],
            }
        save_config(cfg)
        self.send_json({"ok": True})

    def api_tech(self, path, body, cfg):
        if str(body.get("pin", "")) != TECH_PIN:
            return self.send_json({"ok": False, "error": "Λάθος κωδικός"}, 403)
        if "update_url" in body:
            cfg["update_url"] = str(body["update_url"]).strip()
            save_config(cfg)
        try:
            if path == "/api/tech/login":
                return self.send_json({"ok": True, "version": VERSION, "update_url": cfg["update_url"],
                                       "frozen": FROZEN, "mode": cfg["mode"]})
            if path == "/api/tech/mode":
                cfg["mode"] = "client" if body.get("mode") == "client" else "central"
                save_config(cfg)
                restart_app()
                return self.send_json({"ok": True})
            if not cfg["update_url"]:
                return self.send_json({"ok": False, "error": "Δεν έχει οριστεί σύνδεσμος ενημερώσεων"})
            info = check_update(cfg["update_url"])
            if path == "/api/tech/check":
                return self.send_json({"ok": True, **info})
            if path == "/api/tech/update":
                if not info["exe"]:
                    return self.send_json({"ok": False, "error": "Το version.json δεν έχει πεδίο \"exe\""})
                apply_update(info["exe"])
                return self.send_json({"ok": True, "version": info["latest"]})
        except Exception as e:  # δίκτυο, Drive, δικαιώματα αρχείων
            return self.send_json({"ok": False, "error": str(e)})
        return self.send_error(404)


def _safe(fn):
    try:
        fn()
    except Exception as e:
        client_state.update(connected=False, error=str(e))


DEMO_SRC = os.path.join(getattr(sys, "_MEIPASS", BASE), "demo")
DEMO_NAME = "Demo"


def install_demo(cfg):
    """Πρώτη εκκίνηση κεντρικού: φάκελος «Demo» με 5 εικόνες για έλεγχο ότι παίζουν οι οθόνες."""
    if cfg.get("demo_done") or not os.path.isdir(DEMO_SRC):
        return
    import shutil
    dest = os.path.join(MEDIA, GROUPS[0], DEMO_NAME)
    os.makedirs(dest, exist_ok=True)
    for name in sorted(os.listdir(DEMO_SRC)):
        shutil.copy2(os.path.join(DEMO_SRC, name), os.path.join(dest, name))
    cfg["demo_done"] = True
    save_config(cfg)


def make_server():
    """Κεντρικός: ακούει σε όλο το δίκτυο (για τις οθόνες). Οθόνη: μόνο τοπικά."""
    cfg = load_config()
    if cfg["mode"] == "central":
        for g in GROUPS:
            os.makedirs(os.path.join(MEDIA, g), exist_ok=True)
        install_demo(cfg)
    host = "127.0.0.1" if cfg["mode"] == "client" else "0.0.0.0"
    srv = ThreadingHTTPServer((host, PORT), Handler)
    threading.Thread(target=discovery_responder, daemon=True).start()
    threading.Thread(target=client_loop, daemon=True).start()
    return srv


def main():
    srv = make_server()
    print(f"ITNow Signage {VERSION} ({load_config()['mode']}) — http://localhost:{PORT}/admin")
    srv.serve_forever()


if __name__ == "__main__":
    main()
