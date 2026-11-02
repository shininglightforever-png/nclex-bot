"""
Turns a day's questions into rendered media + a posting plan.

  python build_day.py questions.json 2026-11-03

Writes queue/<date>/ with images, videos and plan.json,
and bumps state/counter.json so numbering keeps going.
"""
import json, os, sys, shutil
from render import render_batch
from photo_card import photo_card
from kit import write_kit

HASHTAGS = "#nclex #nclexprep #nursingstudent #nursingschool #nclexrn #futurenurse #nursing"
# Spread through the day (local time)
POST_TIMES = ["08:15", "10:30", "12:45", "15:00", "17:15", "19:30", "21:15"]


def main(src, date, folder=None):
    data = json.load(open(src))
    os.makedirs("state", exist_ok=True)
    counter_path = "state/counter.json"
    start = json.load(open(counter_path))["next"] if os.path.exists(counter_path) else 154
    out = f"queue/{folder or date}"
    made, nxt = render_batch(data["questions"], out, start)
    for d in os.listdir(out):
        if d.startswith("_tmp"):
            shutil.rmtree(os.path.join(out, d))

    items = []
    vids = []
    for m in made:
        v = m.get("video")
        if v and v not in [x[0] for x in vids]:
            vids.append((v, m))
    for i, (v, m) in enumerate(vids):
        cap = (f"{m['q'].get('caption', '')}\n\nPause and lock in both answers before the reveal 🧠"
               f"\n\n{HASHTAGS}")
        items.append({
            "id": os.path.basename(v).replace("_video.mp4", ""),
            "time": f"{date}T{POST_TIMES[i % len(POST_TIMES)]}:00",
            "video": v,
            "caption": cap,
            "platforms": ["ig_reel", "fb_reel"],  # add "tiktok_inbox" once TikTok is linked
        })
    # photo kit for the personal Facebook profile (posted by hand)
    photos = []
    pc_path = "state/photo_counter.json"
    pnum = json.load(open(pc_path))["next"] if os.path.exists(pc_path) else 239
    os.makedirs(f"{out}/photos", exist_ok=True)
    for i, q in enumerate(data.get("photo_questions", [])):
        img = f"{out}/photos/{pnum:04d}.png"
        photo_card(q, pnum).save(img)
        photos.append({"num": pnum, "image": img, "topic": q.get("topic", ""),
                       "time": POST_TIMES[i % len(POST_TIMES)],
                       "question": q["question"],
                       "caption": q["fb_caption"].replace("{NUM}", str(pnum))})
        pnum += 1
    json.dump({"next": pnum}, open(pc_path, "w"))
    json.dump({"date": date, "items": items, "photos": photos}, open(f"{out}/plan.json", "w"), indent=2)
    write_kit()
    json.dump({"next": nxt}, open(counter_path, "w"))
    # running list of every question used, so new batches never repeat
    hist_path = "state/history.json"
    hist = json.load(open(hist_path)) if os.path.exists(hist_path) else []
    hist += [{"num": m["num"], "topic": m["q"].get("topic", ""), "question": m["q"]["question"]}
             for m in made]
    hist += [{"num": f"P{p['num']}", "topic": p["topic"], "question": p["question"]} for p in photos]
    json.dump(hist, open(hist_path, "w"), indent=1)
    print(f"{date}: {len(made)} questions, {len(items)} reels, next #{nxt}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
