"""
Ryan's original reel format: 3 questions per reel, 66 seconds.
Per question: 15 s question with shrinking bar + countdown, 2 s answer highlight, 5 s rationale.

Question fields: qtype ("Signs + Treatment"), topic ("GI"), question, options[4], answer ("A"-"D"),
answer_label (short, e.g. "NPO + NG tube"), bullets (3 to 4 short lines).
"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FPS = 30
Q_SECS, A_SECS, R_SECS = 15, 2, 5

BG = (9, 7, 15)
VIOLET = (168, 104, 252)
BORDER = (112, 72, 220)
PANEL = (21, 14, 38)
TEXT = (238, 234, 252)
GREY = (168, 162, 186)
DIM = (120, 114, 140)
GREEN = (74, 222, 150)
GREEN_FILL = (14, 52, 38)
TRACK = (34, 24, 52)

FONTS = "/usr/share/fonts/"
def poppins(size):
    return ImageFont.truetype(FONTS + "truetype/google-fonts/Poppins-Bold.ttf", size)
def inter(size, weight="SemiBold"):
    return ImageFont.truetype(FONTS + f"opentype/inter/Inter-{weight}.otf", size)


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


_bg = None
def background():
    global _bg
    if _bg is None:
        img = Image.new("RGB", (W, H), BG)
        glow = Image.new("RGB", (W, H), (0, 0, 0))
        ImageDraw.Draw(glow).ellipse((W * 0.05, H * 0.2, W * 0.95, H * 0.7), fill=(42, 22, 74))
        glow = glow.filter(ImageFilter.GaussianBlur(220))
        _bg = Image.blend(img, glow, 0.5)
    return _bg.copy()


def glow_text(img, xy, text, fnt, fill, radius=14, anchor="mm"):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(xy, text, font=fnt, fill=fill + (150,), anchor=anchor)
    layer = layer.filter(ImageFilter.GaussianBlur(radius))
    img.paste(layer, (0, 0), layer)
    ImageDraw.Draw(img).text(xy, text, font=fnt, fill=fill, anchor=anchor)


def header(img, idx, total, sub):
    glow_text(img, (W // 2, 160), f"NCLEX QUESTION {idx} OF {total}", poppins(64), VIOLET, 10)
    ImageDraw.Draw(img).text((W // 2, 237), sub, font=inter(38), fill=GREY, anchor="mm")


def footer(img):
    d = ImageDraw.Draw(img)
    d.text((W // 2, 1640), "@ryan__glass", font=poppins(50), fill=VIOLET, anchor="mm")
    d.text((W // 2, 1695), "Follow for daily NCLEX practice", font=inter(32, "Regular"), fill=GREY, anchor="mm")


def layout(q):
    """Pick text sizes so question + options end above the countdown bar (y 1360)."""
    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    for qs, os_ in ((56, 48), (52, 46), (48, 44), (44, 40), (40, 36), (36, 33)):
        fq, fo = inter(qs), inter(os_)
        ql = wrap(d, q["question"], fq, W - 2 * 58 - 88)
        qlh = int(qs * 1.29)
        qh = 52 * 2 + len(ql) * qlh - (qlh - qs)
        ol = [wrap(d, t, fo, W - 2 * 58 - 190) for t in q["options"]]
        olh = int(os_ * 1.3)
        oh = [max(122, 40 + len(l) * olh) for l in ol]
        if 285 + qh + 38 + sum(oh) + 24 * 3 <= 1350:
            return fq, fo, ql, qlh, qh, ol, olh, oh
    return fq, fo, ql, qlh, qh, ol, olh, oh


def question_base(q, idx, total, reveal=False):
    img = background()
    header(img, idx, total, "Answer" if reveal else f'{q.get("qtype", "Practice")}  |  {q.get("topic", "")}')
    d = ImageDraw.Draw(img)
    fq, fo, ql, qlh, qh, ol, olh, oh = layout(q)
    top = 285
    d.rounded_rectangle((58, top, W - 58, top + qh), 32, fill=PANEL, outline=BORDER, width=3)
    y = top + 52
    for ln in ql:
        d.text((101, y), ln, font=fq, fill=TEXT)
        y += qlh
    y = top + qh + 38
    for letter, lines, bh in zip("ABCD", ol, oh):
        right = reveal and letter == q["answer"].upper()
        dim = reveal and not right
        d.rounded_rectangle((58, y, W - 58, y + bh), 30,
                            fill=GREEN_FILL if right else PANEL,
                            outline=GREEN if right else (BORDER if not dim else (70, 50, 120)), width=3)
        cy = y + bh / 2
        col = GREEN if right else (DIM if dim else TEXT)
        d.text((126, cy), letter, font=poppins(50), fill=col, anchor="mm")
        ty = cy - (len(lines) - 1) * olh / 2
        for ln in lines:
            d.text((197, ty), ln, font=fo, fill=col, anchor="lm")
            ty += olh
        y += bh + 24
    footer(img)
    return img


def rationale_card(q, idx, total):
    img = background()
    header(img, idx, total, "Rationale")
    d = ImageDraw.Draw(img)
    glow_text(img, (W // 2, 540), f'Answer: {q["answer"].upper()}', poppins(100), GREEN, 16)
    label = q.get("answer_label") or q["options"]["ABCD".index(q["answer"].upper())]
    d.text((W // 2, 640), label, font=inter(50), fill=TEXT, anchor="mm")
    bullets = q.get("bullets") or [s.strip() for s in q.get("rationale", "").split(". ") if s.strip()]
    fb = inter(50)
    lines = [wrap(d, b.rstrip("."), fb, W - 2 * 58 - 140) for b in bullets[:4]]
    lh = 63
    ph = 50 * 2 + sum(len(l) * lh for l in lines) + 28 * (len(lines) - 1) - (lh - 50)
    top = 710
    d.rounded_rectangle((58, top, W - 58, top + ph), 32, fill=PANEL, outline=BORDER, width=3)
    y = top + 50
    for ls in lines:
        d.ellipse((99, y + 14, 121, y + 36), fill=VIOLET)
        for ln in ls:
            d.text((147, y), ln, font=fb, fill=TEXT)
            y += lh
        y += 28
    msg = "Next question coming up" if idx < total else "How many did you get? Comment below"
    d.text((W // 2, top + ph + 62), msg, font=inter(38, "Regular"), fill=GREY, anchor="mm")
    footer(img)
    return img


_numbers = {}
def number_layer(n):
    if n not in _numbers:
        layer = Image.new("RGBA", (360, 220), (0, 0, 0, 0))
        g = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).text((180, 110), str(n), font=poppins(116), fill=VIOLET + (150,), anchor="mm")
        g = g.filter(ImageFilter.GaussianBlur(12))
        layer.paste(g, (0, 0), g)
        ImageDraw.Draw(layer).text((180, 110), str(n), font=poppins(116), fill=VIOLET, anchor="mm")
        _numbers[n] = layer
    return _numbers[n]


def render_reel(questions, out_mp4):
    """questions: list of 3 question dicts."""
    total = len(questions)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-f", "lavfi", "-t", str(total * (Q_SECS + A_SECS + R_SECS)), "-i", "anullsrc=r=44100:cl=stereo",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-shortest", "-movflags", "+faststart", out_mp4],
        stdin=subprocess.PIPE)
    x0, x1, by, bh = 110, 970, 1388, 24
    for i, q in enumerate(questions, 1):
        base = question_base(q, i, total)
        bd = ImageDraw.Draw(base)
        bd.rounded_rectangle((x0, by, x1, by + bh), bh // 2, fill=TRACK)
        for f in range(Q_SECS * FPS):
            t = f / FPS
            fr = base.copy()
            d = ImageDraw.Draw(fr)
            frac = max(0.0, 1 - t / Q_SECS)
            if frac > 0.02:
                d.rounded_rectangle((x0, by, x0 + (x1 - x0) * frac, by + bh), bh // 2, fill=VIOLET)
            n = max(1, Q_SECS - int(t))
            lay = number_layer(n)
            fr.paste(lay, (W // 2 - 180, 1505 - 110), lay)
            ff.stdin.write(fr.tobytes())
        ans = question_base(q, i, total, reveal=True).tobytes()
        for _ in range(A_SECS * FPS):
            ff.stdin.write(ans)
        rat = rationale_card(q, i, total).tobytes()
        for _ in range(R_SECS * FPS):
            ff.stdin.write(rat)
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg failed")
