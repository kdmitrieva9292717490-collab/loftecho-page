#!/usr/bin/env python3
"""Encode Figma source images into a CSS block of base64 WebP custom properties."""
import base64, io, os, sys
from PIL import Image

RAW = os.path.join(os.path.dirname(__file__), "assets", "raw")
OUT = os.path.join(os.path.dirname(__file__), "images.css")

# name, source file, target width, quality, keep-alpha
M = [
    # --- rooms (also hero Ken Burns slides + modal backdrops) ---
    ("kosmos",   "room1_1.jpg", 1600, 72, False),
    ("lava",     "room2_1.jpg", 1600, 72, False),
    ("tropiki",  "room3_1.jpg", 1600, 72, False),
    ("laguna",   "room4_1.jpg", 1600, 72, False),
    ("euphoria", "room5_1.jpg", 1600, 72, False),

    # --- about / features sticky images ---
    ("feat1", "about_1.jpg", 1280, 74, False),
    ("feat2", "food_1.jpg",  1520, 72, False),

    # --- combos 3x3 ---
    ("c1", "combo_10.png", 700, 70, False),   # день рождения / кино-комбо
    ("c2", "combo_5.jpg",  700, 70, False),   # романтическое свидание
    ("c3", "combo_1.jpg",  700, 70, False),   # караоке для друзей
    ("c4", "combo_13.png", 700, 70, False),   # девичник
    ("c5", "combo_3.png",  700, 70, False),   # корпоратив
    ("c6", "combo_12.jpg", 700, 70, False),   # лаундж-комбо
    ("c8", "combo_14.jpg", 700, 70, False),   # последний звонок
    ("c9", "combo_6.jpg",  700, 70, False),   # детский день рождения

    # --- special offers illustrations (alpha) ---
    ("o1", "offer_1.png", 760, 78, True),     # луна и облака
    ("o2", "offer_7.png", 760, 78, True),     # гора
    ("o3", "offer_5.png", 760, 78, True),     # тропики
    ("o4", "offer_8.png", 760, 78, True),     # лагуна

    # --- gallery marquee ---
    ("g1",  "gal_1.jpg",  480, 70, False),
    ("g2",  "gal_8.png",  480, 70, False),
    ("g3",  "gal_12.jpg", 480, 70, False),
    ("g4",  "gal_16.jpg", 480, 70, False),
    ("g5",  "gal_18.png", 480, 70, False),
    ("g6",  "gal_4.png",  480, 70, False),
    ("g7",  "gal_11.jpg", 480, 70, False),
    ("g8",  "gal_15.jpg", 480, 70, False),
    ("g9",  "gal_13.jpg", 480, 70, False),
    ("g10", "gal_2.jpg",  480, 70, False),
    ("g11", "gal_14.png", 480, 70, False),
    ("g12", "gal_3.jpg",  480, 70, False),
    ("g13", "gal_20.jpg", 480, 70, False),
    ("g14", "gal_7.png",  480, 70, False),
    ("g15", "gal_9.jpg",  480, 70, False),
    ("g16", "combo_9.png", 480, 70, False),

    # --- reviews ---
    ("rev1", "review_5.jpg", 900, 72, False),
    ("rev2", "review_4.jpg", 900, 72, False),
    ("rev3", "review_1.jpg", 900, 72, False),
    ("av1",  "review_2.png", 140, 82, False),
    ("av2",  "review_8.png", 140, 82, False),

    # --- footer ---
    ("map",  "bottom_1.png", 1400, 72, False),
    ("neon", "bottom_5.png",  900, 82, True),
]


def encode(name, src, width, q, alpha):
    p = os.path.join(RAW, src)
    im = Image.open(p)
    im = im.convert("RGBA" if alpha else "RGB")
    if im.width > width:
        h = round(im.height * width / im.width)
        im = im.resize((width, h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=q, method=6)
    data = buf.getvalue()
    b64 = base64.b64encode(data).decode()
    return name, im.size, len(data), b64


def main():
    lines = [":root{"]
    total = 0
    report = []
    for name, src, w, q, a in M:
        n, size, nbytes, b64 = encode(name, src, w, q, a)
        total += nbytes
        report.append((n, src, f"{size[0]}x{size[1]}", f"{nbytes/1024:.0f}K"))
        lines.append(f'--i-{n}:url("data:image/webp;base64,{b64}");')
    lines.append("}")
    css = "\n".join(lines)
    with open(OUT, "w") as f:
        f.write(css)
    for r in report:
        print(f"  {r[0]:<9} {r[1]:<16} {r[2]:>11} {r[3]:>7}")
    print(f"\n  raw webp total : {total/1024/1024:.2f} MB")
    print(f"  css file size  : {len(css)/1024/1024:.2f} MB")


if __name__ == "__main__":
    main()
