#!/usr/bin/env python3
"""Generate the Android launcher icons from the company logo (tools/logo.png).

Usage:  python3 tools/make_icons.py
Needs:  pip install pillow
"""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "app/src/main/res"
LOGO = ROOT / "tools/logo.png"

CENTER = (31, 77, 45)   # #1f4d2d  forest (lighter)
EDGE = (13, 36, 21)     # #0d2415  forest (darker)
GOLD_TOP = (232, 218, 160)
GOLD_BOTTOM = (181, 163, 92)
SS = 4                  # supersampling factor

DENSITIES = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}


def mark_alpha():
    """Alpha mask of the roof mark only (without the AL-BENAA CO. text)."""
    logo = Image.open(LOGO).convert("RGBA")
    top = logo.crop((0, 0, logo.width, 200))      # text starts below y=200
    a = top.getchannel("A")
    return a.crop(a.getbbox())


MARK = mark_alpha()


def background(size):
    g = Image.radial_gradient("L").resize((size, size), Image.LANCZOS)
    center = Image.new("RGB", (size, size), CENTER)
    edge = Image.new("RGB", (size, size), EDGE)
    return Image.composite(edge, center, g).convert("RGBA")


def mark_layer(size, width_frac, mode="gold"):
    """Transparent square canvas with the mark centred."""
    w = int(size * width_frac)
    h = round(w * MARK.height / MARK.width)
    m = MARK.resize((w, h), Image.LANCZOS)
    if mode == "mono":
        fill = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    else:
        grad = Image.linear_gradient("L").resize((w, h))        # black top -> white bottom
        fill = Image.composite(
            Image.new("RGB", (w, h), GOLD_BOTTOM),
            Image.new("RGB", (w, h), GOLD_TOP), grad).convert("RGBA")
    fill.putalpha(m)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(fill, ((size - w) // 2, (size - h) // 2), fill)
    return canvas


def shaped(size, width_frac, shape):
    """Full icon (background + mark) clipped to a rounded square / circle."""
    big = size * SS
    img = Image.alpha_composite(background(big), mark_layer(big, width_frac))
    mask = Image.new("L", (big, big), 0)
    d = ImageDraw.Draw(mask)
    if shape == "circle":
        d.ellipse((0, 0, big - 1, big - 1), fill=255)
    elif shape == "square":
        d.rectangle((0, 0, big, big), fill=255)
    else:
        d.rounded_rectangle((0, 0, big - 1, big - 1), radius=int(big * 0.22), fill=255)
    img.putalpha(mask)
    return img.resize((size, size), Image.LANCZOS)


def save(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)


def main():
    for name, k in DENSITIES.items():
        legacy = round(48 * k)
        adaptive = round(108 * k)
        d = RES / f"mipmap-{name}"
        # Legacy launcher icons (Android < 8)
        save(shaped(legacy, 0.70, "rounded"), d / "ic_launcher.png")
        save(shaped(legacy, 0.70, "circle"), d / "ic_launcher_round.png")
        # Adaptive icon layers (Android 8+). Mark stays inside the 66dp safe zone.
        big = adaptive * SS
        save(background(big).resize((adaptive, adaptive), Image.LANCZOS).convert("RGB"),
             d / "ic_launcher_background.png")
        save(mark_layer(big, 0.58).resize((adaptive, adaptive), Image.LANCZOS),
             d / "ic_launcher_foreground.png")
        # Themed (monochrome) icon, Android 13+
        save(mark_layer(big, 0.58, "mono").resize((adaptive, adaptive), Image.LANCZOS),
             d / "ic_launcher_monochrome.png")
    # Store / README icon
    save(shaped(512, 0.70, "square").convert("RGB"), ROOT / "icon-512.png")
    print("icons generated")


if __name__ == "__main__":
    main()
