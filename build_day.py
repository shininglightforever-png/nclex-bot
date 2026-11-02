"""
Turns a day's questions into rendered media + a posting plan.

  python build_day.py questions.json 2026-11-03

Writes queue/<date>/ with images, videos and plan.json,
and bumps state/counter.json so numbering keeps going.
"""
import json, os, sys, shutil
from reel3 import render_reel
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
    os.makedirs(out, exist_ok=True)
    qs = data["questions"]
    made = [{"num": start + i, "q": q} for i, q in enumerate(qs)]
    nxt = start + len(qs)
    items = []
    # Ryan's original format: 3 questions per 66 second reel
    for i in range(0, len(made) - 2, 3):
        group = made[i:i + 3]
        rid = f"{group[0]['num']:04d}-{group[-1]['num']:04d}"
        v = f"{out}/{rid}_reel.mp4"
        render_reel([g["q"] for g in group], v)
        hook = group[0]["q"].get("caption", "3 NCLEX questions. How many can you get?")
        cap = (f"{hook}\n\n🧠 3 NCLEX questions. Answer before the timer runs out!"
               f"\n\n👇 How many did you get? Comment below\n\n❤️ Follow @ryan__glass for daily NCLEX practice"
               f"\n\n{HASHTAGS}")
        items.append({
            "id": rid,
            "time": f"{date}T{POST_TIMES[len(items) % len(POST_TIMES)]}:00",
            "video": v,
            "caption": cap,
            "platforms": ["ig_reel", "fb_reel"],  # add "tiktok_inbox" once TikTok is linked
        })
    # photo kit for the personal Facebook profile (posted by hand)
    photos = []
    pc_path = "state/photo_counter.json"
    pnum = json.load(open(pc_path))["next"] if os.path.exists(pc_path) else 238
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
