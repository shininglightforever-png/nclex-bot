"""Builds index.html: a phone page with each day's profile photos and captions."""
import glob, html, json

DAYS_SHOWN = 4


def write_kit(path="index.html"):
    plans = []
    for p in sorted(glob.glob("queue/*/plan.json"), reverse=True):
        d = json.load(open(p))
        if d.get("photos"):
            plans.append(d)
    plans = plans[:DAYS_SHOWN]
    blocks = []
    for d in plans:
        cards = []
        for ph in d["photos"]:
            cap = html.escape(ph["caption"])
            cards.append(f'''
<article class="post">
  <div class="meta"><span class="num">#{ph["num"]}</span><span>{html.escape(ph["topic"])} · post around {ph["time"]}</span></div>
  <img src="{ph["image"]}" alt="NCLEX question {ph["num"]}" loading="lazy">
  <div class="row">
    <a class="btn ghost" href="{ph["image"]}" download>Save image</a>
    <button class="btn" onclick="copyCap(this)">Copy caption</button>
  </div>
  <details><summary>Show caption</summary><pre>{cap}</pre></details>
  <textarea hidden>{cap}</textarea>
</article>''')
        blocks.append(f'<h2>{d["date"]}</h2>' + "".join(cards))
    body = "".join(blocks) or "<p>No photo posts queued yet.</p>"
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Daily NCLEX Posts</title>
<style>
:root{{--bg:#060a18;--panel:#111c3c;--line:#24366e;--teal:#2dd4bf;--text:#eef2ff;--muted:#8ca2d8}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:16px/1.45 system-ui,-apple-system,sans-serif}}
main{{max-width:560px;margin:0 auto;padding:20px 16px 60px}}
h1{{font-size:22px;margin:4px 0 2px}}.sub{{color:var(--muted);margin:0 0 18px;font-size:14px}}
h2{{font-size:15px;color:var(--teal);letter-spacing:.08em;text-transform:uppercase;margin:28px 0 10px}}
.post{{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:14px;margin:0 0 16px}}
.meta{{display:flex;gap:10px;align-items:center;color:var(--muted);font-size:13px;margin-bottom:10px}}
.num{{background:var(--teal);color:#06101e;font-weight:700;border-radius:999px;padding:2px 10px}}
img{{width:100%;border-radius:12px;display:block}}
.row{{display:flex;gap:10px;margin-top:12px}}
.btn{{flex:1;border:0;border-radius:12px;padding:13px;font:600 15px system-ui;background:var(--teal);color:#06101e;text-align:center;text-decoration:none;cursor:pointer}}
.btn.ghost{{background:transparent;color:var(--teal);border:1px solid var(--teal)}}
details{{margin-top:10px;color:var(--muted)}}pre{{white-space:pre-wrap;font:13px/1.4 system-ui;color:var(--text)}}
</style></head><body><main>
<h1>Daily NCLEX Posts</h1>
<p class="sub">For your Facebook profile and groups. On iPhone, press and hold an image, then Save to Photos.</p>
{body}
</main>
<script>
function copyCap(b){{const t=b.closest('.post').querySelector('textarea').value;
const done=()=>{{b.textContent='Copied ✓';setTimeout(()=>b.textContent='Copy caption',1500)}};
if(navigator.clipboard){{navigator.clipboard.writeText(t).then(done)}}else{{const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove();done()}}}}
</script></body></html>'''
    open(path, "w").write(page)
