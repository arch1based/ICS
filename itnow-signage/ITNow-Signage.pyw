"""
ITNow Signage - εκκίνηση εφαρμογής (itnow.gr).

  ITNow-Signage.exe              -> 1η φορά: εγκατάσταση στο C:\\ITNow-Signage, μετά: Πίνακας Ελέγχου
  ITNow-Signage.exe --autostart  -> (εκκίνηση Windows) ξεκινά τον server στο παρασκήνιο και την προβολή

Ο server μένει να τρέχει στο παρασκήνιο· κλείνοντας τον Πίνακα Ελέγχου η προβολή συνεχίζει.
"""
import json
import os
import shutil
import subprocess
import sys
import threading
import time

import server

INSTALL_DIR = r"C:\ITNow-Signage"
EXE_NAME = "ITNow-Signage.exe"


def message(text, error=False, yesno=False):
    """Παράθυρο μηνύματος Windows. Με yesno=True επιστρέφει True για «Ναι»."""
    if os.name != "nt":
        return True
    import ctypes
    flags = 0x10 if error else (0x24 if yesno else 0x40)
    return ctypes.windll.user32.MessageBoxW(None, text, "ITNow Signage", flags) == 6


def open_firewall():
    """Ο κεντρικός πρέπει να δέχεται συνδέσεις από τις οθόνες (ζητά άδεια διαχειριστή μία φορά)."""
    exe = os.path.join(INSTALL_DIR, EXE_NAME)
    script = os.path.join(INSTALL_DIR, "firewall.cmd")
    with open(script, "w", encoding="ascii") as f:
        f.write('netsh advfirewall firewall delete rule name="ITNow Signage"\r\n'
                f'netsh advfirewall firewall add rule name="ITNow Signage" dir=in action=allow '
                f'program="{exe}" enable=yes profile=any\r\n')
    powershell(f"Start-Process '{script}' -Verb RunAs -WindowStyle Hidden -Wait")


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
    cfg_path = os.path.join(INSTALL_DIR, "schedule.json")
    first_time = not os.path.exists(cfg_path)
    if first_time:
        central = message("Τι θα είναι αυτός ο υπολογιστής;\n\n"
                          "ΝΑΙ  =  Κεντρικός υπολογιστής\n"
                          "          (εδώ μπαίνουν οι φάκελοι και δίνονται οι εντολές)\n\n"
                          "ΟΧΙ  =  Οθόνη προβολής\n"
                          "          (παίζει ό,τι ορίζει ο κεντρικός υπολογιστής)", yesno=True)
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump({"mode": "central" if central else "client"}, f)
    with open(cfg_path, encoding="utf-8") as f:
        central = json.load(f).get("mode", "central") == "central"
    # αν τρέχει ήδη παλιά εγκατάσταση, την κλείνουμε για να αντικατασταθεί
    subprocess.run(["taskkill", "/f", "/im", EXE_NAME, "/fi", f"PID ne {os.getpid()}"],
                   capture_output=True, creationflags=server.NO_WINDOW)
    time.sleep(1)
    shutil.copy2(me, dest)
    if central:
        for g in server.GROUPS:
            os.makedirs(os.path.join(INSTALL_DIR, g), exist_ok=True)
        if first_time:
            open_firewall()
    desktop = powershell("[Environment]::GetFolderPath('Desktop')")
    startup = powershell("[Environment]::GetFolderPath('Startup')")
    shortcut(os.path.join(desktop, "ITNow Signage.lnk"), dest)
    if central:
        shortcut(os.path.join(desktop, "ITNow Signage - Φάκελος Προσφορών.lnk"), INSTALL_DIR)
    shortcut(os.path.join(startup, "ITNow Signage.lnk"), dest, "--autostart")
    message("Η εγκατάσταση ολοκληρώθηκε!\n\n"
            f"Φάκελος: {INSTALL_DIR}\n"
            "Στην επιφάνεια εργασίας θα βρείτε το «ITNow Signage».\n"
            "Η προβολή θα ξεκινά αυτόματα με το άνοιγμα του υπολογιστή."
            + ("" if central else "\n\nΗ οθόνη θα βρει μόνη της τον κεντρικό υπολογιστή στο δίκτυο."))
    subprocess.Popen([dest] + ([] if central else ["--autostart"]), cwd=INSTALL_DIR)


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
        # Με τα Windows ξεκινά πάντα ο server· η προβολή ξεκινά στις οθόνες και στον κεντρικό
        # μόνο αν την είχαν αφήσει να παίζει (ή αν έπαιζε πριν από αναβάθμιση).
        if "--after-update" in sys.argv or server.play_on_boot():
            threading.Thread(target=lambda: (time.sleep(3), server.start_show()), daemon=True).start()
    elif "--after-update" not in sys.argv:
        server.open_panel()
    if srv:
        srv.serve_forever()
    else:
        time.sleep(5)  # τρέχει ήδη στο παρασκήνιο· αφήνουμε το thread εκκίνησης να ολοκληρωθεί


if __name__ == "__main__":
    main()
