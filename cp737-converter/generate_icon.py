"""
Δημιουργεί το icon.ico για το CP737_Converter.exe
Τρέχει αυτόματα από το build_exe.bat
"""
from PIL import Image, ImageDraw


def make_icon():
    sizes = [16, 32, 48, 256]
    images = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 86, 179, 255))
        draw = ImageDraw.Draw(img)
        s = size
        cx = s // 2
        p = max(2, s // 8)

        # Κεντρικό στύλο
        draw.rectangle([cx - max(1, s//20), s//4, cx + max(1, s//20), s - p - 1], fill="white")
        # Βραχίονας
        draw.rectangle([p, s//4, s - p, s//4 + max(1, s//16)], fill="white")
        # Αριστερό πιάτο
        draw.ellipse([p - s//10, s//4 - s//10, p + s//5, s//4 + s//5], outline="white", width=max(1, s//24))
        # Δεξί πιάτο
        draw.ellipse([s - p - s//5, s//4 - s//10, s - p + s//10, s//4 + s//5], outline="white", width=max(1, s//24))
        # Βάση
        draw.rectangle([cx - s//5, s - p - max(1, s//16), cx + s//5, s - p], fill="white")

        images.append(img)

    images[0].save(
        "icon.ico", format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    print("icon.ico δημιουργήθηκε.")


if __name__ == "__main__":
    make_icon()
