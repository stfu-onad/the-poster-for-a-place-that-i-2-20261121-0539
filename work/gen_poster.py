"""Generator artwork poster travel fiktif 'VELDORIA' (prosedural, PIL+numpy).
Output: work/entry.png 1024x1024. Dijalankan sekali di sesi ini; main.py
nantinya menulis ulang byte PNG yang sama secara deterministik.
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1024, 1024
HORIZON = 620
rng = random.Random(20261121)

# ---------- helpers ----------
def vgrad(stops, height, width):
    """Vertical gradient from [(pos0..1, (r,g,b)), ...]."""
    ys = np.linspace(0.0, 1.0, height)
    cols = np.zeros((height, 3), dtype=np.float64)
    pos = [s[0] for s in stops]
    for ch in range(3):
        vals = [s[1][ch] for s in stops]
        cols[:, ch] = np.interp(ys, pos, vals)
    return np.repeat(cols[:, None, :], width, axis=1).astype(np.uint8)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------- base: sky + sea ----------
sky = vgrad([
    (0.00, (16, 22, 58)),
    (0.30, (52, 40, 92)),
    (0.52, (122, 62, 102)),
    (0.72, (214, 110, 82)),
    (0.88, (255, 158, 92)),
    (1.00, (255, 190, 110)),
], HORIZON, W)
sea = vgrad([
    (0.00, (46, 122, 138)),
    (0.35, (24, 84, 112)),
    (1.00, (8, 34, 66)),
], H - HORIZON, W)
img = Image.new("RGB", (W, H))
img.paste(Image.fromarray(sky), (0, 0))
img.paste(Image.fromarray(sea), (0, HORIZON))
d = ImageDraw.Draw(img, "RGBA")

# ---------- stars (upper sky, subtle) ----------
for _ in range(90):
    x = rng.randint(0, W - 1)
    y = rng.randint(0, 300)
    r = rng.choice([1, 1, 2])
    a = rng.randint(40, 130)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 240, 210, a))

# ---------- sun + glow ----------
SUN = (668, 548)
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
for r, a in [(260, 26), (210, 40), (160, 60), (120, 90)]:
    gd.ellipse([SUN[0] - r, SUN[1] - r, SUN[0] + r, SUN[1] + r],
               fill=(255, 176, 92, a))
img = Image.alpha_composite(img.convert("RGBA"), glow)
d = ImageDraw.Draw(img, "RGBA")
d.ellipse([SUN[0] - 82, SUN[1] - 82, SUN[0] + 82, SUN[1] + 82],
          fill=(255, 238, 186, 255))
d.ellipse([SUN[0] - 62, SUN[1] - 62, SUN[0] + 62, SUN[1] + 62],
          fill=(255, 246, 214, 255))

# ---------- clouds (soft, blurred layer) ----------
clouds = Image.new("RGBA", (W, H), (0, 0, 0, 0))
cd = ImageDraw.Draw(clouds)
def cloud(cx, cy, w, h, col, alpha):
    cd.ellipse([cx - w, cy - h, cx + w, cy + h], fill=col + (alpha,))
    cd.ellipse([cx - w * 0.55, cy - h * 1.5, cx + w * 0.45, cy + h * 0.4],
               fill=col + (alpha,))
cloud(210, 250, 190, 26, (255, 178, 140), 90)
cloud(830, 180, 150, 20, (255, 190, 160), 80)
cloud(880, 330, 210, 24, (244, 130, 110), 70)
cloud(140, 420, 170, 20, (255, 160, 120), 60)
cloud(520, 120, 130, 16, (200, 160, 210), 55)
clouds = clouds.filter(ImageFilter.GaussianBlur(14))
img = Image.alpha_composite(img, clouds)
d = ImageDraw.Draw(img, "RGBA")

# ---------- sun reflection on the sea ----------
for i in range(22):
    y = HORIZON + 16 + i * 14
    cx = SUN[0] + rng.uniform(-16, 16)
    wdt = rng.uniform(16, 58) * (1 - i / 60.0) + 10
    alpha = max(0, int(88 - i * 3.6))
    d.rounded_rectangle([cx - wdt, y, cx + wdt, y + 4], radius=2,
                        fill=(255, 196, 120, alpha))
# gentle wave lines
for i in range(26):
    y = HORIZON + 30 + i * 14
    x0 = rng.randint(0, 300)
    ln = rng.randint(60, 260)
    d.line([x0, y, x0 + ln, y], fill=(140, 200, 215, 46), width=2)
    x1 = rng.randint(500, 900)
    d.line([x1, y + 6, x1 + rng.randint(40, 160), y + 6],
           fill=(140, 200, 215, 36), width=2)

# ---------- twin crystal spires (the landmark) ----------
def spire(cx, base_y, tip_y, half_w, palette, lean=0.0):
    """Faceted crystal obelisk: wide hexagonal silhouette, 3 lit facets."""
    h = base_y - tip_y
    tip = (cx + lean, tip_y)
    sh_l = (cx - half_w * 0.78, tip_y + h * 0.34)
    sh_r = (cx + half_w * 0.60, tip_y + h * 0.44)
    bl = (cx - half_w, base_y)
    br = (cx + half_w, base_y)
    ridge = (cx + half_w * 0.08, base_y)
    # left facet (bright, catches the sun)
    d.polygon([tip, sh_l, bl, ridge], fill=palette["lit"])
    # centre facet
    d.polygon([tip, ridge, br, sh_r], fill=palette["mid"])
    # right facet (shadow)
    d.polygon([tip, sh_r, br, ridge], fill=palette["dark"])
    # facet seam highlights
    d.line([tip, sh_l], fill=(255, 240, 200, 170), width=3)
    d.line([tip, ridge], fill=(255, 230, 180, 130), width=2)
    d.line([tip, sh_r], fill=(255, 220, 170, 110), width=2)
    # glowing windows along the ridge
    for t in (0.30, 0.48, 0.66, 0.82):
        y = base_y - h * t
        d.ellipse([ridge[0] - 4, y - 4, ridge[0] + 4, y + 4],
                  fill=(255, 244, 190, 230))
    return tip

# back spire (smaller, hazier, to the right)
spire(782, 742, 392, 62,
       {"lit": (226, 150, 110), "mid": (196, 110, 96), "dark": (110, 58, 84)},
       lean=14)
# main spire
spire(560, 788, 268, 96,
       {"lit": (255, 214, 150), "mid": (238, 158, 92), "dark": (122, 58, 88)},
       lean=-10)
# small third shard
spire(448, 760, 470, 36,
       {"lit": (240, 180, 120), "mid": (210, 130, 96), "dark": (104, 56, 82)},
       lean=-6)
# rock islets at the spires' feet
d.polygon([(470, 788), (520, 756), (620, 756), (656, 788)],
          fill=(28, 26, 52))
d.polygon([(742, 742), (772, 722), (816, 722), (842, 742)],
          fill=(34, 30, 56))
d.polygon([(408, 760), (442, 744), (478, 744), (496, 760)],
          fill=(30, 28, 54))

# ---------- sailboat (scale + life) ----------
bx, by = 318, 812
d.polygon([(bx, by - 66), (bx, by - 6), (bx + 52, by - 6)], fill=(255, 246, 228))
d.polygon([(bx - 6, by - 52), (bx - 6, by - 6), (bx - 40, by - 6)],
          fill=(232, 214, 190))
d.line([bx, by - 70, bx, by - 4], fill=(40, 30, 50), width=3)
d.polygon([(bx - 52, by - 4), (bx + 62, by - 4), (bx + 48, by + 12),
           (bx - 40, by + 12)], fill=(38, 28, 48))
d.line([bx - 46, by + 18, bx + 56, by + 18], fill=(255, 200, 130, 90), width=2)

# ---------- foreground headland (bottom-left, frames the scene) ----------
d.polygon([(0, 1024), (0, 872), (96, 836), (210, 872), (300, 928),
           (330, 1024)], fill=(18, 16, 40))
# pine silhouettes on the headland
for px, ph in [(52, 74), (96, 96), (140, 62), (186, 84)]:
    py = 872 - (px - 52) * 0.12
    d.polygon([(px, py - ph), (px - 16, py), (px + 16, py)], fill=(14, 12, 32))
    d.polygon([(px, py - ph * 0.72), (px - 12, py - ph * 0.28),
               (px + 12, py - ph * 0.28)], fill=(14, 12, 32))
    d.rectangle([px - 3, py, px + 3, py + 12], fill=(14, 12, 32))

# ---------- birds ----------
for bx2, by2, s in [(830, 250, 14), (872, 282, 11), (792, 300, 9)]:
    d.arc([bx2 - s, by2 - s // 2, bx2, by2 + s // 2], 200, 340,
          fill=(40, 28, 52, 220), width=3)
    d.arc([bx2, by2 - s // 2, bx2 + s, by2 + s // 2], 200, 340,
          fill=(40, 28, 52, 220), width=3)

# ---------- title: VELDORIA ----------
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
NAME = "VELDORIA"
size = 118
font = ImageFont.truetype(FONT, size)
# letterspaced width
spacing = 26
widths = [d.textlength(ch, font=font) for ch in NAME]
total_w = sum(widths) + spacing * (len(NAME) - 1)
x = (W - total_w) // 2
y = 88
# soft shadow + outline for legibility
for dx, dy, col in [(0, 6, (20, 16, 48, 170)), (3, 3, (20, 16, 48, 120))]:
    xx = x
    for ch, wch in zip(NAME, widths):
        d.text((xx + dx, y + dy), ch, font=font, fill=col)
        xx += wch + spacing
xx = x
for ch, wch in zip(NAME, widths):
    d.text((xx, y), ch, font=font, fill=(255, 242, 210, 255),
           stroke_width=2, stroke_fill=(64, 32, 66, 255))
    xx += wch + spacing
# thin rule under the name
rule_y = y + size + 34
d.line([x + 40, rule_y, x + total_w - 40, rule_y],
       fill=(255, 242, 210, 200), width=3)

img.convert("RGB").save("work/entry.png", optimize=True)
print("saved work/entry.png")
