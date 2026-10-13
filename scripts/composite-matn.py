#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
composite-matn.py - put REAL Arabic onto a blank FLUX page.

WHY THIS EXISTS (P218's shape, closed). FLUX cannot write Arabic: three
`b5027-page` variants came back as convincing gibberish, which matters most
exactly where the text IS the subject. A near-correct ayah is worse than an
obviously decorative one, so scripture is never rendered by the model. The
method was worked out on 2026-10-11 for Bukhari #5027, recorded in prose in
self_upskilling.md and the changelog - and left unscripted, so the next reel
that needed it would have rebuilt it from a paragraph.

THE METHOD
  1. FLUX a BLANK page. Describe the emptiness as a STATE, per R026.
  2. Render the real text with Pillow's RAQM layout engine. HarfBuzz gives
     correct joining and tashkeel; direction='rtl' and language='ar' are both
     required - without them the glyphs come out isolated and backwards.
  3. Perspective-warp the rendered text onto the page quad.
  4. MULTIPLY it into the parchment so the ink absorbs into the fibre instead
     of sitting on top of it like a sticker.

KEEP THE CATEGORIES STRAIGHT. A page carrying a HADITH matn is a hadith
manuscript, not a mushaf. Putting a matn on something that reads as a Quran
conflates the two, and that is the one confusion this channel cannot afford.

USAGE
  python composite-matn.py --image in.jpg --out out.jpg \
      --text "لا إله إلا الله" --font amiri-arabic-400.ttf \
      --quad "62,196 520,186 528,856 70,846" [--size 150] [--ink 40,32,24]

The quad is the page's four corners in the SOURCE image, clockwise from
top-left. --probe draws the quad outline instead of text, to check the corners
before committing to a render.
"""
import argparse
import sys

from PIL import Image, ImageDraw, ImageFont, ImageChops


def solve_coeffs(src_quad, dst_quad):
    """Coefficients for Image.transform(PERSPECTIVE).

    Pillow maps OUTPUT -> INPUT, so the quads go in the order (dst, src).
    Getting this backwards yields a plausible-looking but wrong warp, which is
    why it is spelled out here rather than inlined.
    """
    matrix = []
    for (x, y), (u, v) in zip(dst_quad, src_quad):
        matrix.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        matrix.append([0, 0, 0, x, y, 1, -v * x, -v * y])
    try:
        import numpy as np
    except ImportError:
        sys.exit("numpy required: pip install numpy")
    A = np.matrix(matrix, dtype=float)
    B = np.array(src_quad, dtype=float).reshape(8)
    return np.array(np.dot(np.linalg.inv(A.T * A) * A.T, B)).reshape(8)


def parse_quad(s):
    pts = []
    for pair in s.split():
        x, y = pair.split(",")
        pts.append((float(x), float(y)))
    if len(pts) != 4:
        sys.exit("--quad needs exactly 4 'x,y' points, clockwise from top-left")
    return pts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", required=True)
    ap.add_argument("--font", required=True)
    ap.add_argument("--quad", required=True,
                    help="page corners in the source image, clockwise from top-left")
    ap.add_argument("--size", type=int, default=0,
                    help="point size on the FLAT canvas; 0 = fit to width")
    ap.add_argument("--ink", default="38,30,22", help="r,g,b of the ink")
    ap.add_argument("--opacity", type=float, default=0.92)
    ap.add_argument("--probe", action="store_true",
                    help="outline the quad instead of rendering text")
    args = ap.parse_args()

    base = Image.open(args.image).convert("RGB")
    quad = parse_quad(args.quad)

    if args.probe:
        probe = base.copy()
        d = ImageDraw.Draw(probe)
        d.line(quad + [quad[0]], fill=(255, 0, 0), width=4)
        for i, p in enumerate(quad):
            d.ellipse([p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7], fill=(0, 160, 255))
            d.text((p[0] + 10, p[1] - 6), str(i), fill=(0, 160, 255))
        probe.save(args.out, quality=95)
        print(f"probe -> {args.out}")
        return

    # Flat canvas the size of the page quad's bounding box, so the text is laid
    # out square and only then warped. Laying out directly on the skewed page
    # would shape the glyphs against a distorted baseline.
    xs = [p[0] for p in quad]
    ys = [p[1] for p in quad]
    cw, ch = int(max(xs) - min(xs)), int(max(ys) - min(ys))
    flat = Image.new("L", (cw, ch), 255)
    draw = ImageDraw.Draw(flat)

    size = args.size or 10
    if not args.size:                       # fit to ~72% of the page width
        target = cw * 0.72
        while size < 400:
            f = ImageFont.truetype(args.font, size + 2)
            w = f.getbbox(args.text, direction="rtl", language="ar")[2]
            if w > target:
                break
            size += 2
    font = ImageFont.truetype(args.font, size)

    bbox = font.getbbox(args.text, direction="rtl", language="ar")
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((cw - tw) / 2 - bbox[0], (ch - th) / 2 - bbox[1]),
              args.text, font=font, fill=0,
              direction="rtl", language="ar")

    # Warp the flat canvas onto the page quad.
    src = [(0, 0), (cw, 0), (cw, ch), (0, ch)]
    coeffs = solve_coeffs(src, quad)
    warped = flat.transform(base.size, Image.PERSPECTIVE, coeffs,
                            Image.BICUBIC, fillcolor=255)

    # MULTIPLY: ink darkens the fibre it lies on and keeps the paper's grain
    # and lighting. Pasting instead gives a flat sticker that Kling then
    # animates as a separate surface.
    ink = tuple(int(v) for v in args.ink.split(","))
    ink_layer = Image.new("RGB", base.size, ink)
    mask = warped.point(lambda v: int((255 - v) * args.opacity))
    inked = Image.composite(ink_layer, base, mask)
    out = ImageChops.multiply(base, Image.composite(
        ink_layer, Image.new("RGB", base.size, (255, 255, 255)), mask))
    out = Image.blend(inked, out, 0.5)
    out.save(args.out, quality=95)
    print(f"wrote {args.out}  (font {size}px, text {tw}x{th} on {cw}x{ch} page)")


if __name__ == "__main__":
    main()
