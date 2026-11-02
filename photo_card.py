"""Navy + teal question card for the personal Facebook profile (question only, no answer)."""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1350
TEAL = (45, 212, 191)
BG = (6, 10, 24)
PANEL = (17, 28, 60)
PANEL_LINE = (36, 54, 110)
WHITE = (238, 242, 255)
SOFT_BLUE = (140, 170, 245)
DARK = (8, 14, 30)
HANDLE = "@ryan__glass"

FD = "/usr/share/fonts/truetype/dejavu/"


def f(size, bold=True):
    return ImageFont.truetype(FD + ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), size)


def wrap(d, text, fnt, maxw):
    out, line = [], ""
    for w in text.split():
        t = (line + " " + w).strip()
        if d.textlength(t, font=fnt) <= maxw:
            line = t
        else:
            out.append(line)
            line = w
    if line:
        out.append(line)
    return out


def background():
    img = Image.new("RGB", (W, H), BG)
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse((W * 0.45, -H * 0.25, W * 1.35, H * 0.35), fill=(25, 110, 100))
    g.ellipse((-W * 0.45, H * 0.65, W * 0.45, H * 1.35), fill=(35, 55, 140))
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    return Image.blend(img, glow, 0.55)


def spaced(d, xy, text, fnt, fill, gap):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=fnt, fill=fill, anchor="lm")
        x += d.textlength(ch, font=fnt) + gap


def photo_card(q, num):
    img = background()
    d = ImageDraw.Draw(img)
    M = 70
    # header
    spaced(d, (M, 98), "NCLEX PRACTICE QUESTION", f(27), TEAL, 6.5)
    pill = f"#{num}"
    fp = f(40)
    pw = d.textlength(pill, font=fp) + 56
    d.rounded_rectangle((W - M - pw, 62, W - M, 126), 32, fill=TEAL)
    d.text((W - M - pw / 2, 95), pill, font=fp, fill=DARK, anchor="mm")

    # pick the largest text sizes that fit above the call-to-action bar
    cta_top = 1072
    for qs, os_ in ((46, 38), (42, 36), (40, 34), (36, 32), (33, 30), (30, 28)):
        fq, fo = f(qs), f(os_)
        ql = wrap(d, q["question"], fq, W - 2 * M - 90)
        lh = int(qs * 1.28)
        olh = int(os_ * 1.26)
        qh = 60 * 2 + len(ql) * lh - (lh - qs)
        opts = [(c, wrap(d, t, fo, W - 2 * M - 160)) for c, t in zip("ABCD", q["options"])]
        oh = [max(100, 52 + len(l) * olh) for _, l in opts]
        if 176 + qh + 36 + sum(oh) + 18 * 3 <= cta_top - 30:
            break
    qtop = 176
    d.rounded_rectangle((M, qtop, W - M, qtop + qh), 34, fill=PANEL, outline=PANEL_LINE, width=2)
    y = qtop + 60
    for ln in ql:
        d.text((M + 45, y), ln, font=fq, fill=WHITE)
        y += lh
    # spread options evenly in the space left
    y = qtop + qh + 36
    spare = (cta_top - 30) - y - sum(oh) - 18 * 3
    pad = min(18, max(0, spare // 8))
    for (c, lines), bh in zip(opts, oh):
        bh += pad * 2
        d.rounded_rectangle((M, y, W - M, y + bh), 30, fill=(18, 32, 68), outline=PANEL_LINE, width=2)
        cy = y + bh / 2
        d.ellipse((M + 20, cy - 38, M + 96, cy + 38), fill=TEAL)
        d.text((M + 58, cy), c, font=f(40), fill=DARK, anchor="mm")
        ty = cy - (len(lines) - 1) * olh / 2
        for ln in lines:
            d.text((M + 127, ty), ln, font=fo, fill=WHITE, anchor="lm")
            ty += olh
        y += bh + 18

    # call to action
    d.rounded_rectangle((M, cta_top, W - M, cta_top + 112), 56, fill=(14, 26, 58), outline=TEAL, width=2)
    d.text((M + 48, cta_top + 40), "COMMENT YOUR ANSWER", font=f(33), fill=WHITE, anchor="lm")
    d.text((M + 48, cta_top + 79), "BEFORE EXPANDING THE CAPTION", font=f(23), fill=SOFT_BLUE, anchor="lm")
    cx, cy = W - M - 66, cta_top + 56
    d.ellipse((cx - 35, cy - 35, cx + 35, cy + 35), fill=TEAL)
    d.line((cx, cy - 15, cx, cy + 14), fill=DARK, width=4)
    d.polygon([(cx - 10, cy + 5), (cx + 10, cy + 5), (cx, cy + 17)], fill=DARK)

    d.text((W / 2, 1246), HANDLE, font=f(30), fill=TEAL, anchor="mm")
    return img
