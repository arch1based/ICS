"""
ICS Signage - Πίνακας Ελέγχου (γραφικό περιβάλλον).

Ανοίγει παράθυρο όπου ο χρήστης:
  - ξεκινά / σταματά την προβολή σε πλήρη οθόνη
  - ανοίγει τους φακέλους για να βάλει εικόνες / βίντεο
  - διαλέγει ποιες ημέρες παίζει κάθε ομάδα προσφορών

Με το όρισμα --autostart (συντόμευση εκκίνησης Windows) ξεκινά κατευθείαν την προβολή.
"""
import datetime
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import server

DAYS = ["Δευ", "Τρί", "Τετ", "Πέμ", "Παρ", "Σάβ", "Κυρ"]
EFFECTS = [("Τυχαίο", "random"), ("Σβήσιμο", "fade"), ("Σύρσιμο", "slide"),
           ("Zoom", "zoom"), ("Γύρισμα", "flip"), ("Θόλωμα", "blur")]
URL = f"http://localhost:{server.PORT}/"
PROFILE = os.path.join(os.environ.get("LOCALAPPDATA", server.BASE), "ICS-Signage-Browser")
NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def find_browser():
    pf = [os.environ.get(k, "") for k in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA")]
    for base in pf:
        for rel in (r"Microsoft\Edge\Application\msedge.exe", r"Google\Chrome\Application\chrome.exe"):
            p = os.path.join(base, rel)
            if base and os.path.isfile(p):
                return p
    return None


def start_show():
    exe = find_browser()
    if not exe:
        messagebox.showerror("ICS Signage", "Δεν βρέθηκε Microsoft Edge ή Google Chrome.")
        return
    subprocess.Popen([exe, "--kiosk", URL, "--edge-kiosk-type=fullscreen",
                      "--autoplay-policy=no-user-gesture-required", "--no-first-run",
                      "--disable-features=Translate", "--disable-session-crashed-bubble",
                      f"--user-data-dir={PROFILE}"])


def stop_show():
    if os.name != "nt":
        return
    ps = ("Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*ICS-Signage-Browser*' } "
          "| ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], creationflags=NO_WINDOW)


def open_folder(path):
    os.makedirs(path, exist_ok=True)
    if os.name == "nt":
        os.startfile(path)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ICS Signage — Προβολή Προσφορών")
        self.geometry("1120x660")
        self.minsize(820, 500)
        style = ttk.Style(self)
        style.configure("Big.TButton", font=("Segoe UI", 12, "bold"), padding=10)
        style.configure("TLabel", font=("Segoe UI", 10))
        self.rows = []

        # --- Πάνω: μεγάλα κουμπιά ---
        top = ttk.Frame(self, padding=12)
        top.pack(fill="x")
        ttk.Button(top, text="▶  ΕΝΑΡΞΗ ΠΡΟΒΟΛΗΣ", style="Big.TButton", command=start_show).pack(side="left", padx=4)
        ttk.Button(top, text="■  ΔΙΑΚΟΠΗ ΠΡΟΒΟΛΗΣ", style="Big.TButton", command=stop_show).pack(side="left", padx=4)
        ttk.Button(top, text="📁 Φάκελος Εβδομάδας", style="Big.TButton",
                   command=lambda: open_folder(os.path.join(server.MEDIA, server.GROUPS[0]))).pack(side="left", padx=4)
        ttk.Button(top, text="📁 Φάκελος Ημέρας", style="Big.TButton",
                   command=lambda: open_folder(os.path.join(server.MEDIA, server.GROUPS[1]))).pack(side="left", padx=4)

        help_txt = ("Βήμα 1: Πατήστε «Φάκελος Εβδομάδας» ή «Φάκελος Ημέρας» και βάλτε μέσα σε υποφακέλους τις εικόνες/βίντεο.\n"
                    "Βήμα 2: Πατήστε «Ανανέωση», τσεκάρετε τις ημέρες που θα παίζει κάθε ομάδα και πατήστε «Αποθήκευση».\n"
                    "Βήμα 3: Πατήστε «Έναρξη προβολής». Παίζουν πρώτα οι προσφορές εβδομάδας και μετά οι προσφορές ημέρας.")
        ttk.Label(self, text=help_txt, foreground="#444", padding=(14, 0)).pack(anchor="w")

        # --- Λίστα ομάδων ---
        box = ttk.LabelFrame(self, text=" Ομάδες προσφορών & ημέρες προβολής ", padding=8)
        box.pack(fill="both", expand=True, padx=12, pady=8)
        canvas = tk.Canvas(box, highlightthickness=0)
        sb = ttk.Scrollbar(box, orient="vertical", command=canvas.yview)
        self.inner = ttk.Frame(canvas)
        self.inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

        # --- Κάτω: ρυθμίσεις + αποθήκευση ---
        bottom = ttk.Frame(self, padding=12)
        bottom.pack(fill="x")
        cfg = server.load_config()
        ttk.Label(bottom, text="Δευτερόλεπτα ανά εικόνα:").pack(side="left")
        self.secs = tk.IntVar(value=cfg["image_seconds"])
        ttk.Spinbox(bottom, from_=2, to=300, width=5, textvariable=self.secs).pack(side="left", padx=(4, 16))
        ttk.Label(bottom, text="Εφέ:").pack(side="left")
        self.effect = tk.StringVar(value=dict((v, k) for k, v in EFFECTS).get(cfg["transition"], "Τυχαίο"))
        ttk.Combobox(bottom, values=[k for k, _ in EFFECTS], textvariable=self.effect,
                     state="readonly", width=10).pack(side="left", padx=(4, 16))
        self.sound = tk.BooleanVar(value=cfg["video_sound"])
        ttk.Checkbutton(bottom, text="Ήχος στα βίντεο", variable=self.sound).pack(side="left")
        ttk.Button(bottom, text="💾 Αποθήκευση", style="Big.TButton", command=self.save).pack(side="right", padx=4)
        ttk.Button(bottom, text="🔄 Ανανέωση", command=self.refresh).pack(side="right", padx=4)
        ttk.Button(bottom, text="➕ Νέα ομάδα", command=self.new_group).pack(side="right", padx=4)

        self.refresh()

    def refresh(self):
        for w in self.inner.winfo_children():
            w.destroy()
        self.rows = []
        _, info = server.campaigns_info(datetime.date.today())
        heads = ["Ενεργή", "Ομάδα", "Αρχεία"] + DAYS + ["Από (ΕΕΕΕ-ΜΜ-ΗΗ)", "Έως", "Σήμερα", ""]
        r = 0
        last = None
        for c in info:
            if c["group"] != last:
                last = c["group"]
                ttk.Label(self.inner, text=last, font=("Segoe UI", 11, "bold"), foreground="#1e3a8a")\
                    .grid(row=r, column=0, columnspan=len(heads), sticky="w", pady=(10, 2))
                r += 1
                for i, h in enumerate(heads):
                    ttk.Label(self.inner, text=h, foreground="#666").grid(row=r, column=i, padx=4)
                r += 1
            en = tk.BooleanVar(value=c["enabled"])
            days = [tk.BooleanVar(value=d in c["days"]) for d in range(7)]
            fr, to = tk.StringVar(value=c["from"]), tk.StringVar(value=c["to"])
            ttk.Checkbutton(self.inner, variable=en).grid(row=r, column=0)
            ttk.Label(self.inner, text=c["name"], width=22).grid(row=r, column=1, sticky="w")
            ttk.Label(self.inner, text=str(c["count"])).grid(row=r, column=2)
            for d in range(7):
                ttk.Checkbutton(self.inner, variable=days[d]).grid(row=r, column=3 + d)
            ttk.Entry(self.inner, textvariable=fr, width=12).grid(row=r, column=10, padx=2)
            ttk.Entry(self.inner, textvariable=to, width=12).grid(row=r, column=11, padx=2)
            ttk.Label(self.inner, text="✔ Παίζει" if c["active"] else "—",
                      foreground="#15803d" if c["active"] else "#999").grid(row=r, column=12, padx=6)
            path = os.path.join(server.MEDIA, *c["key"].split("/"))
            ttk.Button(self.inner, text="Άνοιγμα", command=lambda p=path: open_folder(p)).grid(row=r, column=13)
            self.rows.append((c["key"], en, days, fr, to))
            r += 1
        if not info:
            ttk.Label(self.inner, text="Δεν υπάρχουν ομάδες. Πατήστε «➕ Νέα ομάδα».").grid(row=0, column=0)

    def new_group(self):
        which = messagebox.askyesnocancel("Νέα ομάδα", "Ναι = Προσφορές Εβδομάδας\nΌχι = Προσφορές Ημέρας")
        if which is None:
            return
        name = simpledialog.askstring("Νέα ομάδα", "Όνομα ομάδας (π.χ. Δευτέρα-Τετάρτη):", parent=self)
        if not name or any(ch in name for ch in '\\/:*?"<>|'):
            return
        path = os.path.join(server.MEDIA, server.GROUPS[0 if which else 1], name.strip())
        os.makedirs(path, exist_ok=True)
        open_folder(path)
        self.refresh()

    def save(self):
        for _, _, _, fr, to in self.rows:
            for v in (fr, to):
                if v.get().strip():
                    try:
                        datetime.date.fromisoformat(v.get().strip())
                    except ValueError:
                        messagebox.showerror("ICS Signage", f"Λάθος ημερομηνία: {v.get()}\nΓράψτε π.χ. 2026-10-31")
                        return
        cfg = server.load_config()
        cfg["image_seconds"] = max(2, int(self.secs.get() or 8))
        cfg["transition"] = dict(EFFECTS).get(self.effect.get(), "random")
        cfg["video_sound"] = bool(self.sound.get())
        for key, en, days, fr, to in self.rows:
            cfg["campaigns"][key] = {"enabled": en.get(), "days": [d for d in range(7) if days[d].get()],
                                     "from": fr.get().strip(), "to": to.get().strip()}
        server.save_config(cfg)
        self.refresh()
        messagebox.showinfo("ICS Signage", "Αποθηκεύτηκε! Οι αλλαγές ισχύουν από τον επόμενο γύρο της προβολής.")


def main():
    try:
        srv = server.make_server()
    except OSError:
        srv = None  # τρέχει ήδη (άλλο παράθυρο ή αυτόματη εκκίνηση)
    if srv:
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    if "--autostart" in sys.argv:
        start_show()
    app = App()
    if "--autostart" in sys.argv:
        app.iconify()

    def on_close():
        if messagebox.askyesno("ICS Signage", "Αν κλείσει αυτό το παράθυρο θα σταματήσει και η προβολή.\nΚλείσιμο;"):
            stop_show()
            app.destroy()
    if srv:
        app.protocol("WM_DELETE_WINDOW", on_close)
    app.mainloop()


if __name__ == "__main__":
    main()
