"""
CP737 → UTF-8 Auto Converter  (GUI - Standalone EXE)
Ζυγαριά ILS1100 — αυτόματη μετατροπή αρχείων DOS Greek σε UTF-8.
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

# ── Ρυθμίσεις ──────────────────────────────────────────────────────────────
FILE_EXTENSIONS = {".txt", ".csv", ".dat", ".asc"}
SOURCE_ENCODING = "cp737"
TARGET_ENCODING = "utf-8-sig"
CHECK_INTERVAL  = 3
CONVERTED_TAG   = ".utf8_done"
CONFIG_PATH     = Path(os.environ.get("APPDATA", ".")) / "ICS" / "cp737_converter.json"
# ───────────────────────────────────────────────────────────────────────────


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

        self.watch_var  = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Σταματημένο")
        self.running    = False
        self._thread    = None
        self._converted = 0

        self._build_ui()
        self._set_icon()
        self._center()

        # Φόρτωση αποθηκευμένου φακέλου + αυτόματη εκκίνηση
        cfg = load_config()
        if cfg.get("folder"):
            self.watch_var.set(cfg["folder"])
            self.after(600, self.start)

    # ── Εικονίδιο ────────────────────────────────────────────────────────
    def _set_icon(self):
        ico = tk.PhotoImage(width=64, height=64)
        ico.put("#0056b3", to=(0, 0, 64, 64))          # μπλε φόντο
        # Ζυγαριά ⚖
        ico.put("#ffffff", to=(30, 10, 34, 48))         # κεντρικό στύλο
        ico.put("#ffffff", to=(14, 18, 50, 21))         # οριζόντιος βραχίονας
        ico.put("#ffffff", to=(14, 18, 22, 22))         # αριστερό άκρο
        ico.put("#ffffff", to=(42, 18, 50, 22))         # δεξί άκρο
        ico.put("#ffffff", to=(10, 21, 26, 32))         # αριστερό πιάτο
        ico.put("#ffffff", to=(38, 21, 54, 32))         # δεξί πιάτο
        ico.put("#ffffff", to=(22, 48, 42, 52))         # βάση
        self.iconphoto(True, ico)
        self._ico_ref = ico                             # αποφυγή garbage collection

    # ── UI ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        pad = dict(padx=12, pady=6)

        # Header με χρώμα
        hdr = tk.Frame(self, bg="#0056b3")
        hdr.pack(fill="x")
        tk.Label(
            hdr, text="  ⚖  ILS1100 Converter  —  CP737 → UTF-8",
            bg="#0056b3", fg="white",
            font=("Segoe UI", 11, "bold"), pady=10
        ).pack(side="left")

        # Φάκελος
        frm = ttk.LabelFrame(self, text="Φάκελος εξαγωγής ζυγαριάς")
        frm.pack(fill="x", **pad)
        self._entry = ttk.Entry(frm, textvariable=self.watch_var, width=44)
        self._entry.pack(side="left", padx=5, pady=6)
        ttk.Button(frm, text="...", width=3, command=self.browse).pack(side="left", pady=6)

        # Κουμπιά
        bf = ttk.Frame(self)
        bf.pack(**pad)
        self.btn_start = ttk.Button(bf, text="▶  Εκκίνηση", command=self.start, width=18)
        self.btn_start.pack(side="left", padx=5)
        self.btn_stop = ttk.Button(bf, text="■  Διακοπή", command=self.stop, width=18, state="disabled")
        self.btn_stop.pack(side="left", padx=5)

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

    def _center(self):
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    # ── Ενέργειες ────────────────────────────────────────────────────────
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
        backup_dir = watch_dir / "backup_cp737"
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
                        text = fp.read_bytes().decode(SOURCE_ENCODING)
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
