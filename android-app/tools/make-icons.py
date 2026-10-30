#!/usr/bin/env python3
"""Generate Android launcher icons + splash images from ../icon-512.png (the game icon at the repo root).

Usage (from android-app/):  python3 tools/make-icons.py [path/to/icon.png]
Re-run whenever the game icon changes. Needs Pillow (pip install pillow).
"""
import os
import sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.dirname(HERE)
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(APP, "..", "icon-512.png")
RES = os.path.join(APP, "android", "app", "src", "main", "res")
BG = (0x05, 0x07, 0x0D, 255)  # #05070d, the game background

DENSITIES = {"mdpi": 1.0, "hdpi": 1.5, "xhdpi": 2.0, "xxhdpi": 3.0, "xxxhdpi": 4.0}
SS = 4  # supersampling factor for smooth mask edges


def mask(size, kind):
    big = size * SS
    m = Image.new("L", (big, big), 0)
    d = ImageDraw.Draw(m)
    if kind == "circle":
        d.ellipse((0, 0, big - 1, big - 1), fill=255)
    else:  # rounded square, like Android's legacy icon grid
        d.rounded_rectangle((0, 0, big - 1, big - 1), radius=int(big * 0.18), fill=255)
    return m.resize((size, size), Image.LANCZOS)


def legacy(src, px, kind):
    # Legacy (pre-Android 8) icons: 48dp canvas, artwork inset ~4% so it is not clipped.
    canvas = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    inner = round(px * 0.92)
    art = src.resize((inner, inner), Image.LANCZOS)
    art.putalpha(mask(inner, kind))
    off = (px - inner) // 2
    canvas.alpha_composite(art, (off, off))
    return canvas


def main():
    global LOGO, GLOW
    src = Image.open(SRC).convert("RGBA")
    LOGO = Image.open(os.path.join(HERE, "icon-logo.png")).convert("RGBA")
    GLOW = Image.open(os.path.join(HERE, "icon-background.png")).convert("RGB")
    for name, scale in DENSITIES.items():
        d = os.path.join(RES, "mipmap-" + name)
        os.makedirs(d, exist_ok=True)
        px = round(48 * scale)
        legacy(src, px, "square").save(os.path.join(d, "ic_launcher.png"))
        legacy(src, px, "circle").save(os.path.join(d, "ic_launcher_round.png"))
        # Adaptive icon: 108dp layers, launcher shows the centre 72dp (safe circle 66dp).
        # Foreground = the logo on transparency, sized to the safe circle so no letters get cut;
        # background = the red/blue glow from the store icon.
        fg_px = round(108 * scale)
        fg = Image.new("RGBA", (fg_px, fg_px), (0, 0, 0, 0))
        logo = LOGO.copy()
        logo.thumbnail((round(fg_px * 0.56),) * 2, Image.LANCZOS)
        fg.alpha_composite(logo, ((fg_px - logo.width) // 2, (fg_px - logo.height) // 2))
        fg.save(os.path.join(d, "ic_launcher_foreground.png"))
        GLOW.resize((fg_px, fg_px), Image.LANCZOS).save(os.path.join(d, "ic_launcher_background.png"))

    # Splash screens (shown while the WebView boots): icon centred on the game background colour.
    for f in os.listdir(RES):
        p = os.path.join(RES, f, "splash.png")
        if f.startswith("drawable") and os.path.exists(p):
            w, h = Image.open(p).size
            img = Image.new("RGBA", (w, h), BG)
            s = round(min(w, h) * 0.35)
            art = src.resize((s, s), Image.LANCZOS)
            art.putalpha(mask(s, "square"))
            img.alpha_composite(art, ((w - s) // 2, (h - s) // 2))
            img.convert("RGB").save(p)
    print("icons written to", RES)


if __name__ == "__main__":
    main()
