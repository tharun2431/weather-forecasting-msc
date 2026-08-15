"""Redraw the PWA icons to match the brand mark.

The old icons were left from an earlier identity, so an installed copy of the
app showed one thing on the home screen and another in the header.

Drawn with PIL rather than rasterised from the SVG so there is no extra
toolchain to install. The curve is stroked by stamping a filled circle at every
sampled point: PIL's line(joint='curve') beads visibly at this weight, whereas a
circle brush gives exact round caps and joins for free. Everything is drawn at
8x and downsampled, which is cheaper than antialiasing by hand.
"""
from PIL import Image, ImageDraw

ACCENT = (90, 70, 214)      # --accent  #5A46D6
SUN    = (255, 216, 107)    # #FFD86B
WHITE  = (255, 255, 255)
SS     = 8                  # supersample factor

# the header path: M3.6 17.3 c2.7 0 3.5-4.6 6.2-4.6 s3.5 3.3 6.2 3.3 s3-1.7 4.5-1.7
SEGMENTS = [
    ((3.6, 17.3), (6.3, 17.3), (6.3, 12.7), (9.8, 12.7)),
    ((9.8, 12.7), (13.3, 12.7), (13.3, 16.0), (16.0, 16.0)),
    ((16.0, 16.0), (18.7, 16.0), (19.0, 14.3), (20.5, 14.3)),
]


def sample(u, per_seg=260):
    pts = []
    for p0, p1, p2, p3 in SEGMENTS:
        for i in range(per_seg + 1):
            t = i / per_seg
            m = 1 - t
            x = m**3 * p0[0] + 3 * m * m * t * p1[0] + 3 * m * t * t * p2[0] + t**3 * p3[0]
            y = m**3 * p0[1] + 3 * m * m * t * p1[1] + 3 * m * t * t * p2[1] + t**3 * p3[1]
            pts.append((x * u, y * u))
    return pts


def build(size):
    S = size * SS
    u = S / 24.0
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, S - 1, S - 1], int(7 * u), fill=ACCENT)

    cx, cy, r = 15.8 * u, 8.2 * u, 3.9 * u
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SUN)

    # optically thinner than the 2.1 used at 24px: a stroke that reads right
    # in the header looks heavy blown up to 512
    rad = 1.85 * u / 2
    for x, y in sample(u):
        d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=WHITE)

    return im.resize((size, size), Image.LANCZOS)


if __name__ == '__main__':
    for n in (192, 512):
        out = f'icon-{n}.png'
        build(n).save(out, optimize=True)
        print(f'wrote {out}')
