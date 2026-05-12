"""
Εφάπαξ μετατροπή: μετατρέπει ένα συγκεκριμένο αρχείο από CP1253/CP737 σε UTF-8.
Χρήση:  python convert_once.py "C:\path\to\file.txt"
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime


TARGET_ENCODING = "utf-8-sig"


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


def convert(src: Path):
    backup = src.with_suffix(".bak" + src.suffix)
    shutil.copy2(src, backup)
    print(f"Αντίγραφο ασφαλείας: {backup}")

    text = decode_greek_auto(src.read_bytes())
    src.write_bytes(text.encode(TARGET_ENCODING))
    print(f"Έτοιμο: {src}  (CP1253/CP737 → {TARGET_ENCODING})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Χρήση: python convert_once.py <αρχείο>")
        sys.exit(1)
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"Δεν βρέθηκε αρχείο: {path}")
        sys.exit(1)
    convert(path)
