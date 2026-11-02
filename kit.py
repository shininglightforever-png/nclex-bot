"""Builds index.html: a phone page with each day's profile photos and captions."""
import glob, html, json

DAYS_SHOWN = 4


def write_kit(path="index.html"):
    days = {}
    for p in sorted(glob.glob("queue/*/plan.json")):
        d = json.load(open(p))
        day = days.setdefault(d["date"], {"reels": [], "photos": []})
        day["photos"] += d.get("photos", [])
        day["reels"] += [it for it in d.get("items", []) if it.get("video") and not it.get("skip")]
    blocks = []
    for date in sorted(days, reverse=True)[:DAYS_SHOWN]:
        day = days[date]
        day["reels"].sort(key=lambda it: it["time"])
        out = [f'<h2>{date}</h2>']
        if day["reels"]:
            out.append('<h3>Reels for TikTok</h3>')
            for it in day["reels"]:
                cap = html.escape(it["caption"])
                out.append(f'''
<article class="post">
  <div class="meta"><span class="num">#{it["id"]}</span><span>post around {it["time"][11:16]}</span></div>
  <video src="{it["video"]}" controls playsinline preload="metadata"></video>
  <div class="row">
    <button class="btn ghost" onclick="saveMedia(this,'{it["video"]}')">Save to Photos</button>
    <button class="btn" onclick="copyCap(this)">Copy caption</button>
  </div>
  <details><summary>Show caption</summary><pre>{cap}</pre></details>
  <textarea hidden>{cap}</textarea>
</article>''')
        if day["photos"]:
            out.append('<h3>Photos for your Facebook profile</h3>')
            for ph in day["photos"]:
                cap = html.escape(ph["caption"])
                out.append(f'''
<article class="post">
  <div class="meta"><span class="num">#{ph["num"]}</span><span>{html.escape(ph["topic"])} · post around {ph["time"]}</span></div>
  <img src="{ph["image"]}" alt="NCLEX question {ph["num"]}" loading="lazy">
  <div class="row">
    <button class="btn ghost" onclick="saveMedia(this,'{ph["image"]}')">Save to Photos</button>
    <button class="btn" onclick="copyCap(this)">Copy caption</button>
  </div>
  <details><summary>Show caption</summary><pre>{cap}</pre></details>
  <textarea hidden>{cap}</textarea>
</article>''')
        blocks.append("".join(out))
    body = "".join(blocks) or "<p>Nothing queued yet.</p>"
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
img,video{{width:100%;border-radius:12px;display:block;background:#000}}\nh3{{font-size:14px;color:var(--muted);margin:18px 0 10px}}
.row{{display:flex;gap:10px;margin-top:12px}}
.btn{{flex:1;border:0;border-radius:12px;padding:13px;font:600 15px system-ui;background:var(--teal);color:#06101e;text-align:center;text-decoration:none;cursor:pointer}}
.btn.ghost{{background:transparent;color:var(--teal);border:1px solid var(--teal)}}
details{{margin-top:10px;color:var(--muted)}}pre{{white-space:pre-wrap;font:13px/1.4 system-ui;color:var(--text)}}
</style></head><body><main>
<h1>Daily NCLEX Posts</h1>
<p class="sub">Reels for TikTok, photos for your Facebook profile and groups. On iPhone: press and hold an image to save it. Tap Save to Photos, then choose Save Image or Save Video in the share menu.</p>
{body}
</main>
<script>
async function saveMedia(b,url){{const old=b.textContent;b.textContent='Loading…';
try{{const r=await fetch(url);const blob=await r.blob();
const name=url.split('/').pop();const file=new File([blob],name,{{type:blob.type||(name.endsWith('.mp4')?'video/mp4':'image/png')}});
if(navigator.canShare&&navigator.canShare({{files:[file]}})){{await navigator.share({{files:[file]}})}}
else{{const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click()}}}}
catch(e){{}} b.textContent=old}}
function copyCap(b){{const t=b.closest('.post').querySelector('textarea').value;
const done=()=>{{b.textContent='Copied ✓';setTimeout(()=>b.textContent='Copy caption',1500)}};
if(navigator.clipboard){{navigator.clipboard.writeText(t).then(done)}}else{{const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove();done()}}}}
</script></body></html>'''
    open(path, "w").write(page)
