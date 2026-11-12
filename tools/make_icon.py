"""
Pravi ikonicu programa: assets/icon.ico (Windows, više veličina) i assets/icon.png.

Pokretanje:  python tools/make_icon.py

Ako želite svoju ikonicu, ovaj skript nije potreban – samo zamenite
assets/icon.ico i assets/icon.png svojim fajlovima (ista imena).
"""

from pathlib import Path

from PIL import Image, ImageDraw

S = 1024  # crta se veliko pa se smanjuje, radi glatkih ivica
OUT = Path(__file__).resolve().parent.parent / "assets"


def draw():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Pozadina: zaobljeni kvadrat
    d.rounded_rectangle((32, 32, S - 32, S - 32), radius=200, fill=(22, 105, 210, 255))

    # Monitor
    d.rounded_rectangle((170, 230, 854, 690), radius=48, fill=(255, 255, 255, 255))
    d.rounded_rectangle((215, 275, 809, 645), radius=20, fill=(205, 228, 252, 255))
    d.rectangle((462, 690, 562, 780), fill=(255, 255, 255, 255))
    d.rounded_rectangle((350, 770, 674, 820), radius=25, fill=(255, 255, 255, 255))

    # Okvir označenog dela (uglovi za isecanje)
    c, w, L = (255, 140, 0, 255), 34, 85
    x0, y0, x1, y1 = 300, 340, 724, 580
    for (x, y, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.rectangle(sorted_box(x, y, x + dx * L, y + dy * w), fill=c)
        d.rectangle(sorted_box(x, y, x + dx * w, y + dy * L), fill=c)
    return img


def sorted_box(xa, ya, xb, yb):
    return (min(xa, xb), min(ya, yb), max(xa, xb), max(ya, yb))


def main():
    OUT.mkdir(exist_ok=True)
    big = draw().resize((256, 256), Image.LANCZOS)
    big.save(OUT / "icon.png")
    big.save(OUT / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                                     (64, 64), (128, 128), (256, 256)])
    print("Sačuvano:", OUT / "icon.ico", "i", OUT / "icon.png")


if __name__ == "__main__":
    main()
