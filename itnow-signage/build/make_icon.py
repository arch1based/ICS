"""Φτιάχνει το icon.ico του ITNow Signage (οθόνη σε μωβ gradient)."""
from PIL import Image, ImageDraw

S = 256
img = Image.new("RGBA", (S, S))
grad = Image.new("RGBA", (S, S))
for y in range(S):
    for x in range(S):
        t = (x + y) / (2 * S)
        grad.putpixel((x, y), (int(79 + (124 - 79) * t), int(70 + (58 - 70) * t), int(229 + (237 - 229) * t), 255))
mask = Image.new("L", (S, S))
ImageDraw.Draw(mask).rounded_rectangle((8, 8, S - 8, S - 8), radius=56, fill=255)
img.paste(grad, (0, 0), mask)
d = ImageDraw.Draw(img)
d.rounded_rectangle((56, 64, 200, 160), radius=14, outline="white", width=16)
d.line((128, 160, 128, 194), fill="white", width=16)
d.line((88, 198, 168, 198), fill="white", width=16)
img.save("icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
