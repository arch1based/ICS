"""Εγκατάσταση ITNow Signage στο C:\\ITNow-Signage + συντομεύσεις επιφάνειας εργασίας & αυτόματης εκκίνησης."""
import os
import shutil
import subprocess
import sys

import server

SRC = os.path.dirname(os.path.abspath(__file__))
DEST = r"C:\ITNow-Signage"
FILES = ["server.py", "ITNow-Signage.pyw", "README.md"]


def shortcut(lnk, target, args="", workdir="", icon=""):
    q = lambda s: s.replace("'", "''")
    ps = (f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{q(lnk)}');"
          f"$s.TargetPath='{q(target)}';$s.Arguments='{q(args)}';$s.WorkingDirectory='{q(workdir)}';"
          + (f"$s.IconLocation='{q(icon)}';" if icon else "") + "$s.Save()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)


def special(name):
    r = subprocess.run(["powershell", "-NoProfile", "-Command", f"[Environment]::GetFolderPath('{name}')"],
                       capture_output=True, text=True)
    return r.stdout.strip()


def main():
    print("Αντιγραφή αρχείων στο", DEST)
    os.makedirs(os.path.join(DEST, "web"), exist_ok=True)
    for f in FILES:
        shutil.copy2(os.path.join(SRC, f), os.path.join(DEST, f))
    for f in os.listdir(os.path.join(SRC, "web")):
        shutil.copy2(os.path.join(SRC, "web", f), os.path.join(DEST, "web", f))
    for g in server.GROUPS:  # φάκελοι προσφορών + παραδείγματα (αν δεν υπάρχουν ήδη)
        os.makedirs(os.path.join(DEST, g), exist_ok=True)

    pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    app = os.path.join(DEST, "ITNow-Signage.pyw")
    desktop, startup = special("Desktop"), special("Startup")
    print("Δημιουργία συντομεύσεων...")
    shortcut(os.path.join(desktop, "ITNow Signage - Πίνακας Ελέγχου.lnk"), pyw, f'"{app}"', DEST,
             r"%SystemRoot%\System32\imageres.dll,186")
    shortcut(os.path.join(desktop, "ITNow Signage - Φάκελος Προσφορών.lnk"), DEST, "", DEST)
    shortcut(os.path.join(startup, "ITNow Signage.lnk"), pyw, f'"{app}" --autostart', DEST)
    print("\nΗ εγκατάσταση ολοκληρώθηκε!")
    subprocess.Popen([pyw, app], cwd=DEST)


if __name__ == "__main__":
    main()
