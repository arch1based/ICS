"""
CP1253/CP737 → UTF-8 Converter  (GUI - Standalone EXE)
Ζυγαριά ILS1100 — μετατροπή αρχείων ελληνικής κωδικοσελίδας σε UTF-8.
"""

import sys
import shutil
import json
import os
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime

try:
    import pystray
    from PIL import Image, ImageDraw
    _TRAY_OK = True
except ImportError:
    _TRAY_OK = False

if sys.platform == "win32":
    import winreg

# ── Ρυθμίσεις ──────────────────────────────────────────────────────────────
TARGET_ENCODING  = "utf-8-sig"
CHECK_INTERVAL   = 2           # δευτερόλεπτα μεταξύ ελέγχων
CONFIG_PATH      = Path(os.environ.get("APPDATA", ".")) / "ICS" / "cp737_converter.json"
_AUTOSTART_KEY   = r"Software\Microsoft\Windows\CurrentVersion\Run"
_AUTOSTART_NAME  = "ILS1100_Converter"
# ───────────────────────────────────────────────────────────────────────────


def decode_greek_auto(raw_bytes: bytes) -> str:
    lines = raw_bytes.split(b'\n')
    decoded = []
    for line in lines:
        try:
            decoded.append(line.decode('cp1253'))
        except (UnicodeDecodeError, ValueError):
            decoded.append(line.decode('cp737', errors='replace'))
    return '\n'.join(decoded)


def is_already_utf8(raw: bytes) -> bool:
    if raw.startswith(b'\xef\xbb\xbf'):
        return True
    try:
        raw.decode('utf-8')
        return True
    except (UnicodeDecodeError, ValueError):
        return False


def get_autostart() -> bool:
    if sys.platform != "win32":
        return False
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _AUTOSTART_KEY, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, _AUTOSTART_NAME)
        winreg.CloseKey(key)
        return True
    except (FileNotFoundError, OSError):
        return False


def set_autostart(enabled: bool):
    if sys.platform != "win32":
        return
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _AUTOSTART_KEY, 0, winreg.KEY_SET_VALUE)
        if enabled:
            winreg.SetValueEx(key, _AUTOSTART_NAME, 0, winreg.REG_SZ, f'"{sys.executable}"')
        else:
            try:
                winreg.DeleteValue(key, _AUTOSTART_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except OSError:
        pass


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_config(data: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def resource_path(filename: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / filename
    return Path(__file__).parent / filename


def _make_tray_image() -> "Image.Image":
    """Δημιουργεί το εικονίδιο του tray (μπλε τετράγωνο με λευκό 'I')."""
    logo_file = resource_path("logo.png")
    if logo_file.exists():
        try:
            return Image.open(str(logo_file)).convert("RGBA").resize((64, 64))
        except Exception:
            pass
    img = Image.new("RGB", (64, 64), "#0077c8")
    d = ImageDraw.Draw(img)
    d.rectangle([30, 10, 34, 54], fill="#ffffff")
    d.rectangle([14, 10, 50, 18], fill="#ffffff")
    d.rectangle([14, 46, 50, 54], fill="#ffffff")
    return img


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ILS1100 — Μετατροπή Αρχείων")
        self.resizable(False, False)

        self.status_var    = tk.StringVar(value="Έτοιμο")
        self.autostart_var = tk.BooleanVar(value=get_autostart())
        self._last_dir     = load_config().get("last_dir", "C:\\")
        self._watch_path   = None
        self._watch_mtime  = None
        self._watching     = False
        self._thread       = None
        self._tray         = None
        self._tray_thread  = None

        self._build_ui()
        self._set_icon()
        self._center()
        self._setup_tray()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Εικονίδιο παραθύρου ──────────────────────────────────────────────
    def _set_icon(self):
        logo_file = resource_path("logo.png")
        if logo_file.exists():
            try:
                img = tk.PhotoImage(file=str(logo_file))
                factor = max(1, max(img.width(), img.height()) // 64)
                if factor > 1:
                    img = img.subsample(factor, factor)
                self.iconphoto(True, img)
                self._ico_ref = img
                return
            except Exception:
                pass
        ico = tk.PhotoImage(width=64, height=64)
        ico.put("#0077c8", to=(0, 0, 64, 64))
        ico.put("#ffffff", to=(30, 10, 34, 48))
        ico.put("#ffffff", to=(14, 18, 50, 21))
        ico.put("#ffffff", to=(10, 21, 26, 32))
        ico.put("#ffffff", to=(38, 21, 54, 32))
        ico.put("#ffffff", to=(22, 48, 42, 52))
        self.iconphoto(True, ico)
        self._ico_ref = ico

    # ── System Tray ───────────────────────────────────────────────────────
    def _setup_tray(self):
        if not _TRAY_OK:
            return
        menu = pystray.Menu(
            pystray.MenuItem("Άνοιγμα", self._tray_show, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Έξοδος", self._tray_quit),
        )
        self._tray = pystray.Icon(
            "ILS1100_Converter",
            _make_tray_image(),
            "ILS1100 Converter",
            menu,
        )
        self._tray_thread = threading.Thread(target=self._tray.run, daemon=True)
        self._tray_thread.start()

    def _tray_show(self, icon=None, item=None):
        self.after(0, self._show_window)

    def _tray_quit(self, icon=None, item=None):
        self.after(0, self._quit_app)

    def _show_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def _on_close(self):
        if _TRAY_OK and self._tray:
            self.withdraw()   # κρύψε το παράθυρο, μείνε στο tray
        else:
            self._quit_app()

    def _quit_app(self):
        self._watching = False
        if _TRAY_OK and self._tray:
            try:
                self._tray.stop()
            except Exception:
                pass
        self.destroy()

    # ── UI ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        pad = dict(padx=12, pady=6)

        # Header
        hdr = tk.Frame(self, bg="#ffffff", pady=8)
        hdr.pack(fill="x")
        logo_file = resource_path("logo.png")
        if logo_file.exists():
            try:
                raw = tk.PhotoImage(file=str(logo_file))
                factor = max(1, raw.height() // 50)
                if factor > 1:
                    raw = raw.subsample(factor, factor)
                lbl = tk.Label(hdr, image=raw, bg="#ffffff")
                lbl.image = raw
                lbl.pack(side="left", padx=12)
            except Exception:
                self._header_fallback(hdr)
        else:
            self._header_fallback(hdr)

        tk.Label(
            hdr, text="Μετατροπή Αρχείων\nΖυγαριάς ILS1100",
            bg="#ffffff", fg="#0077c8",
            font=("Segoe UI", 10, "bold"), justify="left"
        ).pack(side="left", padx=6)

        ttk.Separator(self, orient="horizontal").pack(fill="x")

        # Κουμπιά
        bf = ttk.Frame(self)
        bf.pack(**pad)
        self.btn_pick = ttk.Button(
            bf, text="📂   Επιλογή αρχείου & Μετατροπή",
            command=self.convert_file, width=36
        )
        self.btn_pick.pack(ipady=6)

        self.btn_stop = ttk.Button(
            bf, text="■   Διακοπή παρακολούθησης",
            command=self.stop_watch, width=36, state="disabled"
        )
        self.btn_stop.pack(ipady=4, pady=(4, 0))

        # Αυτόματη εκκίνηση
        af = ttk.Frame(self)
        af.pack(fill="x", padx=12, pady=(0, 4))
        ttk.Checkbutton(
            af, text="Εκκίνηση αυτόματα με τα Windows",
            variable=self.autostart_var, command=self._toggle_autostart
        ).pack(side="left")

        # Υπόδειξη tray
        if _TRAY_OK:
            tk.Label(
                af, text="  (το X το στέλνει στο tray)",
                fg="#888888", font=("Segoe UI", 8)
            ).pack(side="left")

        # Log
        lf = ttk.LabelFrame(self, text="Ιστορικό μετατροπών")
        lf.pack(fill="both", expand=True, **pad)
        self.log = tk.Text(lf, height=10, width=56, state="disabled", font=("Consolas", 9))
        sb = ttk.Scrollbar(lf, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        self.log.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Status bar
        ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w").pack(
            fill="x", side="bottom", ipady=2)

    def _header_fallback(self, parent):
        tk.Label(parent, text="ICS", bg="#ffffff", fg="#0077c8",
                 font=("Segoe UI", 22, "bold")).pack(side="left", padx=12)

    def _center(self):
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    # ── Ενέργειες ────────────────────────────────────────────────────────
    def _toggle_autostart(self):
        set_autostart(self.autostart_var.get())

    def log_line(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.configure(state="normal")
        self.log.insert("end", f"[{ts}] {msg}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _do_convert(self, path: Path) -> bool:
        raw = path.read_bytes()
        if is_already_utf8(raw):
            return False
        backup = path.with_suffix(".bak" + path.suffix)
        shutil.copy2(path, backup)
        text = decode_greek_auto(raw)
        path.write_bytes(text.encode(TARGET_ENCODING))
        return True

    def convert_file(self):
        fp = filedialog.askopenfilename(
            initialdir=self._last_dir,
            title="Επιλογή αρχείου για μετατροπή",
            filetypes=[
                ("Αρχεία ζυγαριάς", "*.txt *.csv *.dat *.asc"),
                ("Όλα τα αρχεία", "*.*"),
            ]
        )
        if not fp:
            return

        path = Path(fp)
        self._last_dir = str(path.parent)
        save_config({"last_dir": self._last_dir})

        self.stop_watch()

        try:
            converted = self._do_convert(path)
            if converted:
                self.log_line(f"✓  {path.name}")
            else:
                self.log_line(f"⚠  {path.name} — ήδη UTF-8")
        except Exception as e:
            messagebox.showerror("Σφάλμα", f"Αποτυχία μετατροπής:\n{e}")
            self.log_line(f"✗  {path.name}: {e}")
            return

        self._watch_path  = path
        self._watch_mtime = path.stat().st_mtime
        self._watching    = True
        self.btn_stop.configure(state="normal")
        self.status_var.set(f"⟳ Παρακολούθηση: {path.name}  (κάθε {CHECK_INTERVAL}s)")
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()

    def stop_watch(self):
        self._watching = False
        self._watch_path = None
        self.btn_stop.configure(state="disabled")
        self.status_var.set("Έτοιμο")

    # ── Loop παρακολούθησης (background thread) ───────────────────────
    def _watch_loop(self):
        while self._watching:
            time.sleep(CHECK_INTERVAL)
            if not self._watching:
                break
            path = self._watch_path
            if not path or not path.exists():
                break
            try:
                mtime = path.stat().st_mtime
                if mtime != self._watch_mtime:
                    converted = self._do_convert(path)
                    self._watch_mtime = path.stat().st_mtime
                    if converted:
                        self.after(0, self.log_line, f"✓  {path.name}  (αλλαγή εντοπίστηκε)")
                    else:
                        self.after(0, self.log_line, f"⚠  {path.name}  (αλλαγή χωρίς μετατροπή — ήδη UTF-8)")
            except Exception as e:
                self.after(0, self.log_line, f"✗  {path.name}: {e}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
