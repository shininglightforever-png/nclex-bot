"""
NCLEX post renderer for @ryan__glass
Makes question cards, answer cards and a 90 second two-question video
in the dark violet glow style.

Usage:
  python render.py questions.json out/
"""
import json, math, os, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HANDLE = "@ryan__glass"

# Colors
BG_TOP = (14, 8, 28)
BG_BOT = (6, 4, 14)
VIOLET = (168, 110, 255)
VIOLET_SOFT = (120, 70, 220)
PANEL = (22, 14, 40)
TEXT = (240, 236, 255)
MUTED = (170, 160, 200)
GREEN = (80, 230, 160)

FONT_DIR = "/usr/share/fonts"
def font(name, size):
    paths = {
        "bold": ["truetype/google-fonts/Poppins-Bold.ttf", "opentype/inter/Inter-Bold.otf"],
        "semi": ["truetype/google-fonts/Poppins-SemiBold.ttf", "opentype/inter/Inter-SemiBold.otf"],
        "reg": ["opentype/inter/Inter-Regular.otf", "truetype/google-fonts/Poppins-Regular.ttf"],
        "med": ["opentype/inter/Inter-Medium.otf", "truetype/google-fonts/Poppins-Medium.ttf"],
    }[name]
    for p in paths:
        fp = os.path.join(FONT_DIR, p)
        if os.path.exists(fp):
            return ImageFont.truetype(fp, size)
    return ImageFont.truetype(os.path.join(FONT_DIR, "truetype/dejavu/DejaVuSans.ttf"), size)


def wrap(draw, text, fnt, max_w):
    words, lines, line = text.split(), [], ""
    for w in words:
        test = (line + " " + w).strip()
        if draw.textlength(test, font=fnt) <= max_w:
            line = test
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def background(W, H, seed=0):
    mask = Image.linear_gradient("L").resize((W, H))
    img = Image.composite(Image.new("RGB", (W, H), BG_BOT), Image.new("RGB", (W, H), BG_TOP), mask)
    # radial violet glows
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse([-W * 0.3, -H * 0.15, W * 0.8, H * 0.45], fill=(90, 40, 170))
    g.ellipse([W * 0.4, H * 0.6, W * 1.4, H * 1.2], fill=(60, 25, 130))
    glow = glow.filter(ImageFilter.GaussianBlur(W // 4))
    img = Image.blend(img, Image.eval(glow, lambda v: v), 0.35)
    # dot grid
    d = ImageDraw.Draw(img)
    step = 36
    for y in range(step // 2, H, step):
        for x in range(step // 2, W, step):
            d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=(48, 36, 78))
    return img


def glow_rect(img, box, radius, color, blur=28, strength=1):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(box, radius, outline=color + (255,), width=6)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    for _ in range(strength):
        img.paste(layer, (0, 0), layer)


def panel(img, box, radius=36, accent=VIOLET):
    glow_rect(img, box, radius, accent, blur=30, strength=2)
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (box[0] + 8, box[1] + 14, box[2] + 8, box[3] + 14), radius, fill=(0, 0, 0, 160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    img.paste(shadow, (0, 0), shadow)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, radius, fill=PANEL, outline=accent, width=3)


def header(img, W, top, num, topic):
    d = ImageDraw.Draw(img)
    f = font("bold", 40)
    label = f"NCLEX PRACTICE  #{num}"
    d.text((W // 2, top), label, font=f, fill=VIOLET, anchor="mm")
    if topic:
        ft = font("med", 30)
        tw = d.textlength(topic.upper(), font=ft) + 48
        x0 = (W - tw) / 2
        d.rounded_rectangle((x0, top + 40, x0 + tw, top + 90), 25, outline=VIOLET_SOFT, width=2)
        d.text((W // 2, top + 65), topic.upper(), font=ft, fill=MUTED, anchor="mm")


def footer(img, W, H):
    d = ImageDraw.Draw(img)
    f = font("semi", 38)
    # neon text: blurred copy under sharp copy
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((W // 2, H - 90), HANDLE, font=f, fill=VIOLET + (255,), anchor="mm")
    layer = layer.filter(ImageFilter.GaussianBlur(10))
    img.paste(layer, (0, 0), layer)
    d.text((W // 2, H - 90), HANDLE, font=f, fill=TEXT, anchor="mm")


def card(q, num, W=1080, H=1920, reveal=False):
    """One question card. reveal=True highlights the answer and shows rationale."""
    img = background(W, H).convert("RGBA")
    margin = 70
    top = 170 if H > 1500 else 90
    header(img, W, top, num, q.get("topic", ""))

    d = ImageDraw.Draw(img)
    inner_w = W - 2 * margin - 100
    fq = font("semi", 46 if H > 1500 else 40)
    fo = font("med", 38 if H > 1500 else 34)
    fr = font("reg", 32 if H > 1500 else 28)
    lh_q, lh_o, lh_r = int(fq.size * 1.35), int(fo.size * 1.35), int(fr.size * 1.4)

    q_lines = wrap(d, q["question"], fq, inner_w)
    opt_blocks = []
    for i, opt in enumerate(q["options"]):
        letter = "ABCDEF"[i]
        opt_blocks.append((letter, wrap(d, opt, fo, inner_w - 90)))
    r_lines = wrap(d, q.get("rationale", ""), fr, inner_w) if reveal else []

    # measure
    h = 60 + len(q_lines) * lh_q + 40
    for _, ls in opt_blocks:
        h += max(1, len(ls)) * lh_o + 50
    if reveal:
        h += 30 + 50 + len(r_lines) * lh_r
    h += 40
    y0 = max(top + 130, (H - h) // 2)
    box = (margin, y0, W - margin, y0 + h)
    panel(img, box)
    d = ImageDraw.Draw(img)

    x = margin + 50
    y = y0 + 60
    for ln in q_lines:
        d.text((x, y), ln, font=fq, fill=TEXT)
        y += lh_q
    y += 40
    correct = q["answer"].upper()
    for letter, ls in opt_blocks:
        bh = max(1, len(ls)) * lh_o + 26
        is_right = reveal and letter == correct
        oc = GREEN if is_right else VIOLET_SOFT
        fill = (20, 60, 46) if is_right else (32, 22, 58)
        if reveal and not is_right:
            fill = (26, 18, 44)
        d.rounded_rectangle((x - 10, y - 13, W - margin - 40, y + bh - 13), 22, fill=fill,
                            outline=oc, width=3 if is_right else 2)
        d.ellipse((x + 6, y + 2, x + 56, y + 52), outline=oc, width=3)
        d.text((x + 31, y + 27), letter, font=font("bold", 30), fill=oc, anchor="mm")
        ty = y
        tc = TEXT if (not reveal or is_right) else MUTED
        for ln in ls:
            d.text((x + 80, ty), ln, font=fo, fill=tc)
            ty += lh_o
        y += bh + 24
    if reveal:
        y += 20
        d.text((x, y), "WHY", font=font("bold", 32), fill=GREEN)
        y += 50
        for ln in r_lines:
            d.text((x, y), ln, font=fr, fill=MUTED)
            y += lh_r
    footer(img, W, H)
    return img.convert("RGB")


def progress_bar(W, path):
    bar = Image.new("RGBA", (W, 14), (0, 0, 0, 0))
    d = ImageDraw.Draw(bar)
    d.rounded_rectangle((0, 0, W, 14), 7, fill=VIOLET + (255,))
    bar.save(path)


def video(q1, q2, n1, n2, out_mp4, tmp, hold=35, ans=10):
    """90 s video: Q1 hold, Q1 answer, Q2 hold, Q2 answer. Countdown bar during holds."""
    os.makedirs(tmp, exist_ok=True)
    W, H = 1080, 1920
    segs = []
    for q, n, tag in ((q1, n1, "a"), (q2, n2, "b")):
        qp, ap = f"{tmp}/{tag}_q.png", f"{tmp}/{tag}_a.png"
        card(q, n, W, H).save(qp)
        card(q, n, W, H, reveal=True).save(ap)
        segs += [(qp, hold, True), (ap, ans, False)]
    bar = f"{tmp}/bar.png"
    progress_bar(W, bar)
    parts = []
    for i, (img, dur, timed) in enumerate(segs):
        p = f"{tmp}/seg{i}.mp4"
        if timed:
            vf = (f"[0:v][1:v]overlay=x='-W+W*t/{dur}':y=H-32:shortest=1,"
                  "format=yuv420p[v]")
            cmd = ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-t", str(dur), "-i", img,
                   "-loop", "1", "-t", str(dur), "-i", bar,
                   "-filter_complex", vf, "-map", "[v]", "-r", "30",
                   "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", p]
        else:
            cmd = ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-t", str(dur), "-i", img,
                   "-vf", "format=yuv420p", "-r", "30",
                   "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", p]
        subprocess.run(cmd, check=True)
        parts.append(p)
    lst = f"{tmp}/list.txt"
    with open(lst, "w") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
    total = 2 * (hold + ans)
    # silent audio track so every platform accepts it; add a trending sound in-app if you like
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-f", "lavfi", "-t", str(total), "-i", "anullsrc=r=44100:cl=stereo",
                    "-c:v", "copy", "-c:a", "aac", "-shortest", "-movflags", "+faststart", out_mp4],
                   check=True)


def render_batch(questions, out_dir, start_num):
    """questions: list of dicts {topic, question, options[4], answer 'A'-'D', rationale, caption}"""
    os.makedirs(out_dir, exist_ok=True)
    made = []
    num = start_num
    for q in questions:
        base = f"{out_dir}/{num:04d}"
        # feed carousel: question slide + answer slide (1080x1350)
        card(q, num, 1080, 1350).save(f"{base}_feed_q.png")
        card(q, num, 1080, 1350, reveal=True).save(f"{base}_feed_a.png")
        made.append({"num": num, "q": q,
                     "feed": [f"{base}_feed_q.png", f"{base}_feed_a.png"]})
        num += 1
    # one 90 s video per pair of questions
    for i in range(0, len(made) - 1, 2):
        a, b = made[i], made[i + 1]
        mp4 = f"{out_dir}/{a['num']:04d}-{b['num']:04d}_video.mp4"
        video(a["q"], b["q"], a["num"], b["num"], mp4, f"{out_dir}/_tmp{i}")
        a["video"] = b["video"] = mp4
    return made, num


if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    data = json.load(open(src))
    made, nxt = render_batch(data["questions"], out, data.get("start_num", 154))
    json.dump({"posts": made, "next_num": nxt}, open(f"{out}/manifest.json", "w"), indent=2)
    print(f"Rendered {len(made)} posts, next number {nxt}")
