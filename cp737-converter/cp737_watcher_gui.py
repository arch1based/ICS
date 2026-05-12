"""
CP1253 → UTF-8 Auto Converter  (GUI - Standalone EXE)
Ζυγαριά ILS1100 — αυτόματη μετατροπή αρχείων Windows Greek σε UTF-8.
"""

import sys
import time
import shutil
import threading
import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    import winreg

# ── Ρυθμίσεις ──────────────────────────────────────────────────────────────
FILE_EXTENSIONS = {".txt", ".csv", ".dat", ".asc"}
TARGET_ENCODING = "utf-8-sig"
CHECK_INTERVAL  = 3
CONVERTED_TAG   = ".utf8_done"
CONFIG_PATH     = Path(os.environ.get("APPDATA", ".")) / "ICS" / "cp737_converter.json"
# ───────────────────────────────────────────────────────────────────────────


def decode_greek_auto(raw_bytes: bytes) -> str:
    """Αποκωδικοποιεί αρχείο ζυγαριάς που μπορεί να αναμιγνύει CP1253 και CP737."""
    lines = raw_bytes.split(b'\n')
    decoded = []
    for line in lines:
        try:
            decoded.append(line.decode('cp1253'))
        except (UnicodeDecodeError, ValueError):
            decoded.append(line.decode('cp737', errors='replace'))
    return '\n'.join(decoded)


_AUTOSTART_KEY  = r"Software\Microsoft\Windows\CurrentVersion\Run"
_AUTOSTART_NAME = "ILS1100_Converter"


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
            exe = sys.executable
            winreg.SetValueEx(key, _AUTOSTART_NAME, 0, winreg.REG_SZ, f'"{exe}"')
        else:
            try:
                winreg.DeleteValue(key, _AUTOSTART_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except OSError:
        pass


def resource_path(filename: str) -> Path:
    """Βρίσκει αρχείο είτε σε development είτε μέσα στο PyInstaller exe."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / filename
    return Path(__file__).parent / filename


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


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ILS1100 — Μετατροπή Αρχείων")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.iconify)

        self.watch_var     = tk.StringVar(value="")
        self.status_var    = tk.StringVar(value="Σταματημένο")
        self.autostart_var = tk.BooleanVar(value=get_autostart())
        self.running       = False
        self._thread       = None
        self._converted    = 0

        self._build_ui()
        self._set_icon()
        self._center()

        # Φόρτωση αποθηκευμένου φακέλου + αυτόματη εκκίνηση
        cfg = load_config()
        if cfg.get("folder"):
            self.watch_var.set(cfg["folder"])
            self.after(600, self.start)

    # ── Εικονίδιο παραθύρου ──────────────────────────────────────────────
    def _set_icon(self):
        logo_file = resource_path("logo.png")
        if logo_file.exists():
            try:
                img = tk.PhotoImage(file=str(logo_file))
                # Σμίκρυνση ανάλογα με το μέγεθος
                w, h = img.width(), img.height()
                factor = max(1, max(w, h) // 64)
                if factor > 1:
                    img = img.subsample(factor, factor)
                self.iconphoto(True, img)
                self._ico_ref = img
                return
            except Exception:
                pass
        # Fallback: ζυγαριά με pixels αν δεν βρεθεί το logo.png
        ico = tk.PhotoImage(width=64, height=64)
        ico.put("#0077c8", to=(0, 0, 64, 64))
        ico.put("#ffffff", to=(30, 10, 34, 48))
        ico.put("#ffffff", to=(14, 18, 50, 21))
        ico.put("#ffffff", to=(10, 21, 26, 32))
        ico.put("#ffffff", to=(38, 21, 54, 32))
        ico.put("#ffffff", to=(22, 48, 42, 52))
        self.iconphoto(True, ico)
        self._ico_ref = ico

    # ── UI ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        pad = dict(padx=12, pady=6)

        # Header με logo
        hdr = tk.Frame(self, bg="#ffffff", pady=8)
        hdr.pack(fill="x")

        logo_file = resource_path("logo.png")
        if logo_file.exists():
            try:
                raw = tk.PhotoImage(file=str(logo_file))
                # Κλιμάκωση ώστε το ύψος να είναι ~50px
                factor = max(1, raw.height() // 50)
                if factor > 1:
                    raw = raw.subsample(factor, factor)
                lbl_logo = tk.Label(hdr, image=raw, bg="#ffffff")
                lbl_logo.image = raw          # αποφυγή GC
                lbl_logo.pack(side="left", padx=12)
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

        # Φάκελος
        frm = ttk.LabelFrame(self, text="Φάκελος εξαγωγής ζυγαριάς")
        frm.pack(fill="x", **pad)
        ttk.Entry(frm, textvariable=self.watch_var, width=44).pack(side="left", padx=5, pady=6)
        ttk.Button(frm, text="...", width=3, command=self.browse).pack(side="left", pady=6)

        # Κουμπιά
        bf = ttk.Frame(self)
        bf.pack(**pad)
        self.btn_start = ttk.Button(bf, text="▶  Εκκίνηση", command=self.start, width=18)
        self.btn_start.pack(side="left", padx=5)
        self.btn_stop = ttk.Button(bf, text="■  Διακοπή", command=self.stop, width=18, state="disabled")
        self.btn_stop.pack(side="left", padx=5)

        # Εφάπαξ μετατροπή αρχείου
        sf = ttk.LabelFrame(self, text="Εφάπαξ μετατροπή αρχείου")
        sf.pack(fill="x", **pad)
        ttk.Button(sf, text="📂  Επιλογή αρχείου & Μετατροπή",
                   command=self.convert_single_file).pack(padx=5, pady=6)

        # Αυτόματη εκκίνηση με Windows
        af = ttk.Frame(self)
        af.pack(fill="x", padx=12, pady=(0, 4))
        ttk.Checkbutton(
            af, text="Εκκίνηση αυτόματα με τα Windows",
            variable=self.autostart_var, command=self._toggle_autostart
        ).pack(side="left")

        # Log
        lf = ttk.LabelFrame(self, text="Αρχεία που μετατράπηκαν")
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

    def convert_single_file(self):
        fp = filedialog.askopenfilename(
            title="Επιλογή αρχείου για μετατροπή",
            filetypes=[
                ("Αρχεία ζυγαριάς", "*.txt *.csv *.dat *.asc"),
                ("Όλα τα αρχεία", "*.*"),
            ]
        )
        if not fp:
            return
        path = Path(fp)
        try:
            backup = path.with_suffix(".bak" + path.suffix)
            shutil.copy2(path, backup)
            text = decode_greek_auto(path.read_bytes())
            path.write_bytes(text.encode(TARGET_ENCODING))
            self.log_line(f"OK  {path.name}  (αντίγραφο: {backup.name})")
            self.status_var.set(f"Μετατράπηκε: {path.name}")
        except Exception as e:
            messagebox.showerror("Σφάλμα", f"Αποτυχία μετατροπής:\n{e}")

    def browse(self):
        d = filedialog.askdirectory(initialdir=self.watch_var.get() or "C:\\")
        if d:
            self.watch_var.set(d)
            save_config({"folder": d})

    def log_line(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.configure(state="normal")
        self.log.insert("end", f"[{ts}] {msg}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def start(self):
        folder = self.watch_var.get().strip()
        if not folder:
            messagebox.showwarning("Προσοχή", "Επιλέξτε φάκελο πρώτα.")
            return
        path = Path(folder)
        if not path.exists():
            try:
                path.mkdir(parents=True)
            except Exception as e:
                messagebox.showerror("Σφάλμα", f"Αδύνατη δημιουργία φακέλου:\n{e}")
                return
        save_config({"folder": folder})
        self.running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.status_var.set(f"Παρακολούθηση: {folder}")
        self.log_line(f"── Έναρξη: {folder} ──")
        self._thread = threading.Thread(target=self._watch_loop, args=(path,), daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.status_var.set("Σταματημένο")
        self.log_line("── Διακοπή ──")

    # ── Loop παρακολούθησης (background thread) ───────────────────────
    def _watch_loop(self, watch_dir: Path):
        backup_dir = watch_dir / "backup_greek"
        backup_dir.mkdir(exist_ok=True)

        while self.running:
            for ext in FILE_EXTENSIONS:
                for fp in watch_dir.glob(f"*{ext}"):
                    if not fp.is_file():
                        continue
                    tag = fp.with_suffix(fp.suffix + CONVERTED_TAG)
                    if tag.exists():
                        continue
                    try:
                        shutil.copy2(fp, backup_dir / fp.name)
                        text = decode_greek_auto(fp.read_bytes())
                        fp.write_bytes(text.encode(TARGET_ENCODING))
                        tag.touch()
                        self._converted += 1
                        self.after(0, self.log_line, f"OK  {fp.name}")
                        self.after(0, self.status_var.set,
                                   f"Παρακολούθηση: {watch_dir}  |  Μετατράπηκαν: {self._converted}")
                    except Exception as e:
                        self.after(0, self.log_line, f"ΣΦΑΛΜΑ {fp.name}: {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    app = App()
    app.mainloop()
