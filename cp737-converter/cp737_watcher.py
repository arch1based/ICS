"""
CP1253/CP737 → UTF-8 Auto Converter
Παρακολουθεί φάκελο και μετατρέπει αυτόματα αρχεία ζυγαριάς (Windows/DOS Greek) σε UTF-8.
"""

import sys
import time
import os
import shutil
from pathlib import Path
from datetime import datetime

# ── Ρυθμίσεις ──────────────────────────────────────────────────────────────
WATCH_FOLDER   = r"C:\ERP_Export"      # Φάκελος που εξάγει το ERP
BACKUP_FOLDER  = r"C:\ERP_Export\backup_greek"  # Αντίγραφο πριν τη μετατροπή
FILE_EXTENSIONS = {".txt", ".csv", ".dat", ".asc"}  # Τύποι αρχείων
TARGET_ENCODING = "utf-8-sig"          # utf-8-sig = UTF-8 με BOM (ανοίγει σωστά στο Excel)
CHECK_INTERVAL  = 3                    # Δευτερόλεπτα μεταξύ ελέγχων
# ───────────────────────────────────────────────────────────────────────────

CONVERTED_TAG = ".utf8_done"  # Κρυφό αρχείο-σήμα για αρχεία που έχουν ήδη μετατραπεί


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


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def is_converted(path: Path) -> bool:
    return path.with_suffix(path.suffix + CONVERTED_TAG).exists()


def mark_converted(path: Path):
    path.with_suffix(path.suffix + CONVERTED_TAG).touch()


def convert_file(path: Path):
    backup_dir = Path(BACKUP_FOLDER)
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Αντίγραφο ασφαλείας
    backup_path = backup_dir / path.name
    shutil.copy2(path, backup_path)

    # Διαβάζουμε με αυτόματη ανίχνευση ελληνικής κωδικοσελίδας (CP1253/CP737)
    try:
        text = decode_greek_auto(path.read_bytes())
    except Exception as e:
        log(f"  ΣΦΑΛΜΑ αποκωδικοποίησης {path.name}: {e}")
        return False

    # Γράφουμε ως UTF-8
    path.write_bytes(text.encode(TARGET_ENCODING))
    mark_converted(path)
    log(f"  OK  {path.name}  (CP1253/CP737 → {TARGET_ENCODING})")
    return True


def scan_and_convert(watch_dir: Path):
    for ext in FILE_EXTENSIONS:
        for filepath in watch_dir.glob(f"*{ext}"):
            if filepath.is_file() and not is_converted(filepath):
                log(f"Βρέθηκε νέο αρχείο: {filepath.name}")
                convert_file(filepath)


def main():
    watch_dir = Path(WATCH_FOLDER)
    if not watch_dir.exists():
        log(f"ΣΦΑΛΜΑ: Ο φάκελος δεν υπάρχει: {WATCH_FOLDER}")
        log("Δημιουργία φακέλου...")
        watch_dir.mkdir(parents=True)

    log(f"Παρακολούθηση: {WATCH_FOLDER}")
    log(f"Τύποι αρχείων: {', '.join(FILE_EXTENSIONS)}")
    log(f"Κωδικοσελίδα: CP1253/CP737 → {TARGET_ENCODING}")
    log("Πατήστε Ctrl+C για τερματισμό.\n")

    try:
        while True:
            scan_and_convert(watch_dir)
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        log("Τερματισμός.")


if __name__ == "__main__":
    # Επιτρέπει override φακέλου από command line:
    # python cp737_watcher.py "C:\MyFolder"
    if len(sys.argv) > 1:
        WATCH_FOLDER = sys.argv[1]
    main()
