"""
Turns a day's questions into rendered media + a posting plan.

  python build_day.py questions.json 2026-11-03

Writes queue/<date>/ with images, videos and plan.json,
and bumps state/counter.json so numbering keeps going.
"""
import json, os, sys, shutil
from render import render_batch

HASHTAGS = "#nclex #nclexprep #nursingstudent #nursingschool #nclexrn #futurenurse #nursing"
# Spread through the day (local time)
POST_TIMES = ["08:15", "10:30", "12:45", "15:00", "17:15", "19:30", "21:15"]


def main(src, date):
    data = json.load(open(src))
    os.makedirs("state", exist_ok=True)
    counter_path = "state/counter.json"
    start = json.load(open(counter_path))["next"] if os.path.exists(counter_path) else 154
    out = f"queue/{date}"
    made, nxt = render_batch(data["questions"], out, start)
    for d in os.listdir(out):
        if d.startswith("_tmp"):
            shutil.rmtree(os.path.join(out, d))

    items = []
    used_videos = set()
    for i, m in enumerate(made):
        cap = f"{m['q'].get('caption', '')}\n\nAnswer on slide 2 👉\n\n{HASHTAGS}"
        item = {
            "id": f"{m['num']:04d}",
            "time": f"{date}T{POST_TIMES[i % len(POST_TIMES)]}:00",
            "images": m["feed"],
            "caption": cap,
            "platforms": ["ig_carousel", "fb_photos"],
            "topic": m["q"].get("topic", ""),
            "question": m["q"]["question"],
        }
        items.append(item)
        v = m.get("video")
        if v and v not in used_videos:
            used_videos.add(v)
            vcap = (f"Can you get both? Pause and lock in your answers 🧠\n\n{HASHTAGS}")
            items.append({
                "id": os.path.basename(v).replace("_video.mp4", "") + "v",
                "time": f"{date}T{POST_TIMES[i % len(POST_TIMES)]}:00",
                "video": v,
                "caption": vcap,
                "platforms": ["tiktok_inbox", "ig_reel", "fb_reel"],
            })
    json.dump({"date": date, "items": items}, open(f"{out}/plan.json", "w"), indent=2)
    json.dump({"next": nxt}, open(counter_path, "w"))
    # running list of every question used, so new batches never repeat
    hist_path = "state/history.json"
    hist = json.load(open(hist_path)) if os.path.exists(hist_path) else []
    hist += [{"num": m["num"], "topic": m["q"].get("topic", ""), "question": m["q"]["question"]}
             for m in made]
    json.dump(hist, open(hist_path, "w"), indent=1)
    print(f"{date}: {len(made)} questions, {len(used_videos)} videos, next #{nxt}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
