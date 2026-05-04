"""
Εφάπαξ μετατροπή: μετατρέπει ένα συγκεκριμένο αρχείο από CP737 σε UTF-8.
Χρήση:  python convert_once.py "C:\path\to\file.txt"
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime


SOURCE_ENCODING = "cp737"
TARGET_ENCODING = "utf-8-sig"


def convert(src: Path):
    backup = src.with_suffix(".bak" + src.suffix)
    shutil.copy2(src, backup)
    print(f"Αντίγραφο ασφαλείας: {backup}")

    text = src.read_bytes().decode(SOURCE_ENCODING)
    src.write_bytes(text.encode(TARGET_ENCODING))
    print(f"Έτοιμο: {src}  ({SOURCE_ENCODING} → {TARGET_ENCODING})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Χρήση: python convert_once.py <αρχείο>")
        sys.exit(1)
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"Δεν βρέθηκε αρχείο: {path}")
        sys.exit(1)
    convert(path)
