"""
ITNow Signage - εκκίνηση εφαρμογής (itnow.gr).

  ITNow-Signage.exe              -> 1η φορά: εγκατάσταση στο C:\\ITNow-Signage, μετά: Πίνακας Ελέγχου
  ITNow-Signage.exe --autostart  -> (εκκίνηση Windows) ξεκινά κατευθείαν την προβολή

Ο server μένει να τρέχει στο παρασκήνιο· κλείνοντας τον Πίνακα Ελέγχου η προβολή συνεχίζει.
"""
import os
import shutil
import subprocess
import sys
import threading
import time

import server

INSTALL_DIR = r"C:\ITNow-Signage"
EXE_NAME = "ITNow-Signage.exe"


def message(text, error=False):
    if os.name == "nt":
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, text, "ITNow Signage", 0x10 if error else 0x40)


def powershell(cmd, capture=False):
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
                       capture_output=True, text=True, creationflags=server.NO_WINDOW)
    return r.stdout.strip()


def shortcut(lnk, target, args=""):
    q = lambda s: s.replace("'", "''")
    powershell(f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{q(lnk)}');"
               f"$s.TargetPath='{q(target)}';$s.Arguments='{q(args)}';"
               f"$s.WorkingDirectory='{q(INSTALL_DIR)}';$s.Save()")


def install():
    """Αντιγράφει το exe στο C:\\ITNow-Signage και φτιάχνει συντομεύσεις."""
    me = sys.executable
    dest = os.path.join(INSTALL_DIR, EXE_NAME)
    os.makedirs(INSTALL_DIR, exist_ok=True)
    # αν τρέχει ήδη παλιά εγκατάσταση, την κλείνουμε για να αντικατασταθεί
    subprocess.run(["taskkill", "/f", "/im", EXE_NAME, "/fi", f"PID ne {os.getpid()}"],
                   capture_output=True, creationflags=server.NO_WINDOW)
    time.sleep(1)
    shutil.copy2(me, dest)
    for g in server.GROUPS:
        os.makedirs(os.path.join(INSTALL_DIR, g), exist_ok=True)
    desktop = powershell("[Environment]::GetFolderPath('Desktop')")
    startup = powershell("[Environment]::GetFolderPath('Startup')")
    shortcut(os.path.join(desktop, "ITNow Signage.lnk"), dest)
    shortcut(os.path.join(desktop, "ITNow Signage - Φάκελος Προσφορών.lnk"), INSTALL_DIR)
    shortcut(os.path.join(startup, "ITNow Signage.lnk"), dest, "--autostart")
    message("Η εγκατάσταση ολοκληρώθηκε!\n\n"
            f"Φάκελος: {INSTALL_DIR}\n"
            "Στην επιφάνεια εργασίας θα βρείτε το «ITNow Signage».\n"
            "Η προβολή θα ξεκινά αυτόματα με το άνοιγμα του υπολογιστή.")
    subprocess.Popen([dest], cwd=INSTALL_DIR)


def main():
    if server.FROZEN and os.path.normcase(server.BASE) != os.path.normcase(INSTALL_DIR):
        try:
            install()
        except OSError as e:
            message(f"Η εγκατάσταση απέτυχε:\n{e}", error=True)
        return

    old = sys.executable + ".old"  # απομεινάρι προηγούμενης αναβάθμισης
    if os.path.exists(old):
        try:
            os.remove(old)
        except OSError:
            pass

    srv = None
    for _ in range(20 if "--after-update" in sys.argv else 1):  # μετά από αναβάθμιση περιμένουμε να κλείσει η παλιά
        try:
            srv = server.make_server()
            break
        except OSError:
            time.sleep(0.5)

    if "--autostart" in sys.argv:
        threading.Thread(target=lambda: (time.sleep(2), server.start_show()), daemon=True).start()
    elif "--after-update" not in sys.argv:
        server.open_panel()
    if srv:
        srv.serve_forever()
    else:
        time.sleep(5)  # τρέχει ήδη στο παρασκήνιο· αφήνουμε το thread εκκίνησης να ολοκληρωθεί


if __name__ == "__main__":
    main()
