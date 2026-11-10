#!/usr/bin/env python3
"""Turn Aazim's GitHub avatar into an ASCII portrait (assets/portrait.txt).

The portrait is drawn from the avatar of the FIRST username in
PROFILE_USERNAMES (default aazimameen1-dotcom). Needs Pillow.
In the GitHub Action it runs daily, so a new avatar refreshes the portrait.
"""
import io
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "portrait.txt")

COLS = 44
RAMP = " .:-=+*#%@"  # light -> dark is inverted below (ink on paper)


def main() -> None:
    from PIL import Image, ImageEnhance, ImageOps

    users = os.environ.get("PROFILE_USERNAMES", "aazimameen1-dotcom").split(",")
    username = users[0].strip()
    req = urllib.request.Request(
        f"https://github.com/{username}.png?size=460",
        headers={"User-Agent": "Mozilla/5.0 (profile-card-renderer)"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        img = Image.open(io.BytesIO(r.read())).convert("L")
    # Crop to head & shoulders so the ASCII reads as a portrait, not a scene.
    w, h = img.size
    img = img.crop((int(w * 0.10), int(h * 0.10), int(w * 0.62), int(h * 0.62)))
    img = ImageOps.autocontrast(img, cutoff=1)
    img = ImageEnhance.Contrast(img).enhance(1.15)
    rows = max(1, int(COLS * img.height / img.width * 0.52))  # char cells are ~2x tall
    img = img.resize((COLS, rows))
    px = img.load()
    lines = []
    for y in range(rows):
        line = ""
        for x in range(COLS):
            v = px[x, y] / 255.0  # 0 black .. 1 white
            idx = int((1.0 - v) * (len(RAMP) - 1))
            line += RAMP[idx]
        lines.append(line.rstrip())
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {OUT}: {COLS}x{rows} from @{username} avatar")


if __name__ == "__main__":
    sys.exit(main())
