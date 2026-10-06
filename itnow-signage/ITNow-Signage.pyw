"""
ITNow Signage - εκκίνηση εφαρμογής (itnow.gr).

  ITNow-Signage.pyw              -> ανοίγει τον Πίνακα Ελέγχου
  ITNow-Signage.pyw --autostart  -> (εκκίνηση Windows) ξεκινά κατευθείαν την προβολή

Ο server μένει να τρέχει στο παρασκήνιο· κλείνοντας τον Πίνακα Ελέγχου η προβολή συνεχίζει.
"""
import sys
import threading
import time

import server


def main():
    try:
        srv = server.make_server()
    except OSError:
        srv = None  # τρέχει ήδη στο παρασκήνιο
    if "--autostart" in sys.argv:
        # η προβολή ανοίγει μόλις ο server είναι έτοιμος
        threading.Thread(target=lambda: (time.sleep(2), server.start_show()), daemon=True).start()
    else:
        server.open_panel()
    if srv:
        srv.serve_forever()
    else:
        time.sleep(5)  # αφήνουμε το thread εκκίνησης να ολοκληρωθεί


if __name__ == "__main__":
    main()
