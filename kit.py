"""Builds index.html: a phone page with each day's profile photos and captions."""
import glob, html, json

DAYS_SHOWN = 3  # newest days shown open; older days go in a collapsed archive

# Facebook profile photos: most reach comes from groups, and many groups ban links,
# so the caption points people to Ryan's profile (link in his intro and featured post).
# The link comment is only for posts on his own profile, never in groups.
FOLLOW_LINE = "❤️ Follow @ryan__glass for daily NCLEX practice questions!"
FB_CTA = "📚 Want 150 more practice questions with rationales? The full question bank is linked on my profile 👤"
# TikTok photo posts on the 2 small accounts that can't have a bio link
TT_CTA = "📚 Want 150 more practice questions with rationales? The full question bank is linked on @ryan__glass 👤"
FB_LINK_COMMENT = ("📚 150 NCLEX practice questions with full rationales 👉 "
                   "https://shinelight37.gumroad.com/l/ryan_glass")


def fb_photo_caption(cap):
    if FB_CTA in cap:
        return cap
    if FOLLOW_LINE in cap:
        return cap.replace(FOLLOW_LINE, f"{FB_CTA}\n\n{FOLLOW_LINE}", 1)
    return f"{cap}\n\n{FB_CTA}"


def write_kit(path="index.html"):
    days = {}
    for p in sorted(glob.glob("queue/*/plan.json")):
        d = json.load(open(p))
        day = days.setdefault(d["date"], {"reels": [], "photos": []})
        day["photos"] += d.get("photos", [])
        day["reels"] += [it for it in d.get("items", []) if it.get("video") and not it.get("skip")]
    allp = sorted((ph for d in days.values() for ph in d["photos"]), key=lambda ph: ph["num"])
    upnext_data = json.dumps({str(ph["num"]): {
        "img": ph["image"], "topic": ph["topic"],
        "cap": fb_photo_caption(ph["caption"]),
        "tt": fb_photo_caption(ph["caption"]).replace(FB_CTA, TT_CTA)} for ph in allp}).replace("</", "<\\/")
    blocks, archive = [], []
    for idx, date in enumerate(sorted(days, reverse=True)):
        recent = idx < DAYS_SHOWN
        preload = "metadata" if recent else "none"
        day = days[date]
        day["reels"].sort(key=lambda it: it["time"])
        out = [f'<h2>{date}</h2>'] if recent else []
        if day["reels"]:
            out.append('<h3>Reels for TikTok</h3>')
            for it in day["reels"]:
                cap = html.escape(it["caption"])
                out.append(f'''
<article class="post">
  <div class="meta"><span class="num">#{it["id"]}</span><span>post around {it["time"][11:16]}</span></div>
  <video src="{it["video"]}" controls playsinline preload="{preload}"></video>
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
                cap = html.escape(fb_photo_caption(ph["caption"]))
                link = html.escape(FB_LINK_COMMENT)
                tt = html.escape(fb_photo_caption(ph["caption"]).replace(FB_CTA, TT_CTA))
                out.append(f'''
<article class="post">
  <div class="meta"><span class="num">#{ph["num"]}</span><span>{html.escape(ph["topic"])} · post around {ph["time"]}</span></div>
  <img src="{ph["image"]}" alt="NCLEX question {ph["num"]}" loading="lazy">
  <div class="row">
    <button class="btn ghost" onclick="saveMedia(this,'{ph["image"]}')">Save to Photos</button>
    <button class="btn" onclick="copyCap(this)">Copy caption</button>
  </div>
  <div class="row">
    <button class="btn ghost" onclick="copyCap(this,'.tt')">Copy TikTok caption (no-link accounts)</button>
  </div>
  <div class="row">
    <button class="btn ghost" data-label="Copy link comment (own profile only)" onclick="copyText(this,'{link}')">Copy link comment (own profile only)</button>
  </div>
  <details><summary>Show caption</summary><pre>{cap}</pre></details>
  <textarea hidden>{cap}</textarea>
  <textarea hidden class="tt">{tt}</textarea>
</article>''')
        if recent:
            blocks.append("".join(out))
        else:
            nr, npn = len(day["reels"]), len(day["photos"])
            nums = [p["num"] for p in day["photos"]]
            label = f"{nr} reels" + (f", photos #{min(nums)} to #{max(nums)}" if nums else "")
            archive.append(f'<details class="day"><summary>{date} <span>{label}</span></summary>{"".join(out)}</details>')
    body = "".join(blocks) or "<p>Nothing queued yet.</p>"
    if archive:
        body += '<h2>Older posts</h2>' + "".join(archive)
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
details{{margin-top:10px;color:var(--muted)}}
.tabs{{display:flex;gap:8px;margin-bottom:12px}}.tab{{flex:1;border:1px solid var(--line);background:var(--panel);color:var(--muted);border-radius:12px;padding:10px 4px;font:600 14px system-ui}}.tab.on{{border-color:var(--teal);color:var(--teal)}}.tab small{{font-weight:400}}
.day{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin:0 0 10px}}
.day>summary{{color:var(--text);font-weight:600;cursor:pointer}}.day>summary span{{color:var(--muted);font-weight:400;font-size:13px;margin-left:6px}}pre{{white-space:pre-wrap;font:13px/1.4 system-ui;color:var(--text)}}
</style></head><body><main>
<h1>Daily NCLEX Posts</h1>
<p class="sub">Reels for TikTok, photos for your Facebook profile and groups. For Facebook photos: the caption sends people to your profile. Only paste the link comment on posts on your own profile, not in groups. Use Copy TikTok caption on the 2 TikTok accounts without a bio link. On iPhone: press and hold an image to save it. Tap Save to Photos, then choose Save Image or Save Video in the share menu.</p>
{body}
</main>
<script>
const PHOTOS={upnext_data};
const CH=[{{id:"tt",name:"TikTok",start:306,tt:true}},{{id:"fb1",name:"Facebook 1",start:318}},{{id:"fb2",name:"Facebook 2",start:296}}];
const PER=3;
function getPos(c){{try{{const v=localStorage.getItem("pos_"+c.id);if(v)return +v}}catch(e){{}}return c.start}}
function setPos(c,v){{try{{localStorage.setItem("pos_"+c.id,v)}}catch(e){{}}}}
let cur=CH[0];
function esc(t){{return t.replace(/[&<>"']/g,m=>({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}}[m]))}}
function render(){{
 document.getElementById("tabs").innerHTML=CH.map(c=>`<button class="tab${{c===cur?" on":""}}" onclick="pick('${{c.id}}')">${{c.name}}<br><small>#${{getPos(c)}}</small></button>`).join("");
 const start=getPos(cur);let html="";
 for(let n=start;n<start+PER;n++){{const p=PHOTOS[n];
  if(!p){{html+=`<p class="sub">#${{n}} is not made yet.</p>`;continue}}
  const btns=cur.tt
   ?`<button class="btn" onclick="copyText(this,PHOTOS[${{n}}].cap)" data-label="Copy caption (link accounts)">Copy caption (link accounts)</button></div><div class="row"><button class="btn ghost" onclick="copyText(this,PHOTOS[${{n}}].tt)" data-label="Copy caption (no-link accounts)">Copy caption (no-link accounts)</button>`
   :`<button class="btn" onclick="copyText(this,PHOTOS[${{n}}].cap)" data-label="Copy caption">Copy caption</button>`;
  html+=`<article class="post"><div class="meta"><span class="num">#${{n}}</span><span>${{esc(p.topic)}}</span></div>
  <img src="${{p.img}}" loading="lazy"><div class="row"><button class="btn ghost" onclick="saveMedia(this,'${{p.img}}')">Save to Photos</button>${{btns}}</div></article>`}}
 html+=`<div class="row"><button class="btn ghost" onclick="move(-PER)">Back 3</button><button class="btn" onclick="move(PER)">Done, next 3</button></div>
 <div class="row"><button class="btn ghost" onclick="jump()">Jump to #</button></div>`;
 document.getElementById("upnext").innerHTML=html}}
function pick(id){{cur=CH.find(c=>c.id===id);render()}}
function move(d){{setPos(cur,getPos(cur)+d);render();window.scrollTo(0,0)}}
function jump(){{const v=prompt("Start at photo #",getPos(cur));if(v&&!isNaN(+v)){{setPos(cur,+v);render()}}}}
document.addEventListener("DOMContentLoaded",render);
async function saveMedia(b,url){{const old=b.textContent;b.textContent='Loading…';
try{{const r=await fetch(url);const blob=await r.blob();
const name=url.split('/').pop();const file=new File([blob],name,{{type:blob.type||(name.endsWith('.mp4')?'video/mp4':'image/png')}});
if(navigator.canShare&&navigator.canShare({{files:[file]}})){{await navigator.share({{files:[file]}})}}
else{{const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click()}}}}
catch(e){{}} b.textContent=old}}
function copyText(b,t){{const old=b.dataset.label||b.textContent;
const done=()=>{{b.textContent='Copied ✓';setTimeout(()=>b.textContent=old,1500)}};
if(navigator.clipboard){{navigator.clipboard.writeText(t).then(done)}}else{{const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove();done()}}}}
function copyCap(b,sel){{const t=b.closest('.post').querySelector(sel||'textarea').value;const old=b.textContent;
const done=()=>{{b.textContent='Copied ✓';setTimeout(()=>b.textContent=old,1500)}};
if(navigator.clipboard){{navigator.clipboard.writeText(t).then(done)}}else{{const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove();done()}}}}
</script></body></html>'''
    open(path, "w").write(page)
