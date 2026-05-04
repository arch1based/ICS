"""
Δημιουργεί το icon.ico από το logo.png για το CP737_Converter.exe
Τρέχει αυτόματα από το build_exe.bat
"""
from PIL import Image
from pathlib import Path


def make_icon():
    logo = Path("logo.png")
    sizes = [16, 32, 48, 256]

    if logo.exists():
        src = Image.open(logo).convert("RGBA")
        images = []
        for s in sizes:
            img = src.copy()
            img.thumbnail((s, s), Image.LANCZOS)
            # Κεντράρισμα σε τετράγωνο καμβά
            canvas = Image.new("RGBA", (s, s), (0, 0, 0, 0))
            offset = ((s - img.width) // 2, (s - img.height) // 2)
            canvas.paste(img, offset)
            images.append(canvas)
        images[0].save(
            "icon.ico", format="ICO",
            sizes=[(s, s) for s in sizes],
            append_images=images[1:]
        )
        print("icon.ico δημιουργήθηκε από logo.png")
    else:
        # Fallback: μπλε εικονίδιο αν δεν υπάρχει logo.png
        from PIL import ImageDraw
        images = []
        for s in sizes:
            img = Image.new("RGBA", (s, s), (0, 119, 200, 255))
            draw = ImageDraw.Draw(img)
            cx, p = s // 2, max(2, s // 8)
            draw.rectangle([cx-max(1,s//20), s//4, cx+max(1,s//20), s-p], fill="white")
            draw.rectangle([p, s//4, s-p, s//4+max(1,s//16)], fill="white")
            draw.rectangle([cx-s//5, s-p-max(1,s//16), cx+s//5, s-p], fill="white")
            images.append(img)
        images[0].save("icon.ico", format="ICO",
                       sizes=[(s,s) for s in sizes], append_images=images[1:])
        print("icon.ico δημιουργήθηκε (fallback — logo.png δεν βρέθηκε)")


if __name__ == "__main__":
    make_icon()
