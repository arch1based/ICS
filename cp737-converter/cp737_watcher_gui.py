"""
CP737 → UTF-8 Auto Converter  (GUI version για standalone EXE)
Τρέχει στο system tray — ο πελάτης το ξεκινά και ξεχνά.
"""

import sys
import time
import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime


# ── Ρυθμίσεις ──────────────────────────────────────────────────────────────
DEFAULT_WATCH    = r"C:\ERP_Export"
FILE_EXTENSIONS  = {".txt", ".csv", ".dat", ".asc"}
SOURCE_ENCODING  = "cp737"
TARGET_ENCODING  = "utf-8-sig"
CHECK_INTERVAL   = 3
CONVERTED_TAG    = ".utf8_done"
# ───────────────────────────────────────────────────────────────────────────


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CP737 → UTF-8 Converter")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        self.watch_var  = tk.StringVar(value=DEFAULT_WATCH)
        self.status_var = tk.StringVar(value="Σταματημένο")
        self.running    = False
        self._thread    = None
        self._converted = 0

        self._build_ui()
        self.center()

    def _build_ui(self):
        pad = dict(padx=10, pady=5)

        # Φάκελος
        frm = ttk.LabelFrame(self, text="Φάκελος παρακολούθησης")
        frm.pack(fill="x", **pad)
        ttk.Entry(frm, textvariable=self.watch_var, width=42).pack(side="left", padx=5, pady=5)
        ttk.Button(frm, text="...", width=3, command=self.browse).pack(side="left", pady=5)

        # Κουμπιά
        btn_frm = ttk.Frame(self)
        btn_frm.pack(**pad)
        self.btn_start = ttk.Button(btn_frm, text="▶  Εκκίνηση", command=self.start, width=16)
        self.btn_start.pack(side="left", padx=5)
        self.btn_stop = ttk.Button(btn_frm, text="■  Διακοπή", command=self.stop, width=16, state="disabled")
        self.btn_stop.pack(side="left", padx=5)

        # Log
        log_frm = ttk.LabelFrame(self, text="Αρχεία που μετατράπηκαν")
        log_frm.pack(fill="both", expand=True, **pad)
        self.log = tk.Text(log_frm, height=10, width=54, state="disabled", font=("Consolas", 9))
        sb = ttk.Scrollbar(log_frm, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        self.log.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Status bar
        ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w").pack(
            fill="x", side="bottom", ipady=2)

    def center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    def browse(self):
        d = filedialog.askdirectory(initialdir=self.watch_var.get())
        if d:
            self.watch_var.set(d)

    def log_line(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.configure(state="normal")
        self.log.insert("end", f"[{ts}] {msg}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def start(self):
        folder = Path(self.watch_var.get())
        if not folder.exists():
            try:
                folder.mkdir(parents=True)
            except Exception as e:
                messagebox.showerror("Σφάλμα", f"Αδύνατη δημιουργία φακέλου:\n{e}")
                return

        self.running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.status_var.set(f"Παρακολούθηση: {folder}")
        self._thread = threading.Thread(target=self._watch_loop, args=(folder,), daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.status_var.set("Σταματημένο")
        self.log_line("── Διακοπή παρακολούθησης ──")

    def minimize_to_tray(self):
        self.withdraw()
        # Απλό minimize — επαναφορά με διπλό κλικ στη γραμμή εργασιών
        self.iconify()

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
