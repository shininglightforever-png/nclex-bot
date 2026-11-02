"""
Auto-poster for @ryan__glass. Runs hourly on GitHub Actions.

Reads queue/<date>/plan.json and posts every item whose time has come:
  - Instagram: question+answer carousel, plus Reels for videos
  - Facebook Page: two-photo post, plus Reels for videos
  - TikTok: videos go to your TikTok inbox (tap Post in the app)

Anything with "skip": true in plan.json is left alone.
Results are written to state/posted.json so nothing posts twice.
"""
import datetime as dt, json, os, sys, time, glob
import requests
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Indiana/Indianapolis")
GRAPH = "https://graph.facebook.com/v21.0"
REPO = os.environ.get("GITHUB_REPOSITORY", "")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"

PAGE_ID = os.environ.get("FB_PAGE_ID")
PAGE_TOKEN = os.environ.get("FB_PAGE_TOKEN")
IG_ID = os.environ.get("IG_USER_ID")
TT_KEY = os.environ.get("TIKTOK_CLIENT_KEY")
TT_SECRET = os.environ.get("TIKTOK_CLIENT_SECRET")
TT_REFRESH = os.environ.get("TIKTOK_REFRESH_TOKEN")
DRY = os.environ.get("DRY_RUN") == "1"

STATE = "state/posted.json"


def log(*a):
    print(*a, flush=True)


def url(path):
    return f"{RAW}/{path}"


_page_token = None


def page_token():
    """Works whether the secret holds a Page token or a user token."""
    global _page_token
    if _page_token is None:
        r = requests.get(f"{GRAPH}/{PAGE_ID}", params={"fields": "access_token",
                                                      "access_token": PAGE_TOKEN}, timeout=60)
        _page_token = r.json().get("access_token") or PAGE_TOKEN
    return _page_token


def graph(method, path, **data):
    data["access_token"] = page_token()
    if method == "GET":
        r = requests.get(f"{GRAPH}/{path}", params=data, timeout=120)
    else:
        r = requests.request(method, f"{GRAPH}/{path}", data=data, timeout=120)
    if r.status_code >= 400:
        raise RuntimeError(f"{path}: {r.text}")
    return r.json()


# ---------- Instagram ----------
def ig_wait(container):
    for _ in range(60):
        s = graph("GET", f"{container}?fields=status_code").get("status_code")
        if s == "FINISHED":
            return
        if s == "ERROR":
            raise RuntimeError(f"IG container {container} failed")
        time.sleep(10)
    raise RuntimeError("IG processing timed out")


def ig_carousel(images, caption):
    kids = [graph("POST", f"{IG_ID}/media", image_url=url(p), is_carousel_item="true")["id"]
            for p in images]
    c = graph("POST", f"{IG_ID}/media", media_type="CAROUSEL",
              children=",".join(kids), caption=caption)["id"]
    ig_wait(c)
    return graph("POST", f"{IG_ID}/media_publish", creation_id=c)["id"]


def ig_reel(video, caption):
    c = graph("POST", f"{IG_ID}/media", media_type="REELS", video_url=url(video),
              caption=caption, share_to_feed="true")["id"]
    ig_wait(c)
    return graph("POST", f"{IG_ID}/media_publish", creation_id=c)["id"]


# ---------- Facebook Page ----------
def fb_photos(images, caption):
    ids = [graph("POST", f"{PAGE_ID}/photos", url=url(p), published="false")["id"] for p in images]
    attached = json.dumps([{"media_fbid": i} for i in ids])
    return graph("POST", f"{PAGE_ID}/feed", message=caption, attached_media=attached)["id"]


def fb_reel(video, caption):
    start = graph("POST", f"{PAGE_ID}/video_reels", upload_phase="start")
    vid = start["video_id"]
    r = requests.post(f"https://rupload.facebook.com/video-upload/v21.0/{vid}",
                      headers={"Authorization": f"OAuth {page_token()}", "file_url": url(video)},
                      timeout=300)
    if r.status_code >= 400:
        raise RuntimeError(f"FB reel upload: {r.text}")
    graph("POST", f"{PAGE_ID}/video_reels", upload_phase="finish", video_id=vid,
          video_state="PUBLISHED", description=caption)
    return vid


# ---------- TikTok (inbox upload, works without app audit) ----------
def tt_token():
    r = requests.post("https://open.tiktokapis.com/v2/oauth/token/", data={
        "client_key": TT_KEY, "client_secret": TT_SECRET,
        "grant_type": "refresh_token", "refresh_token": TT_REFRESH}, timeout=60)
    j = r.json()
    if "access_token" not in j:
        raise RuntimeError(f"TikTok token refresh failed: {j}")
    return j["access_token"]


def tt_inbox(video):
    size = os.path.getsize(video)
    tok = tt_token()
    init = requests.post("https://open.tiktokapis.com/v2/post/publish/inbox/video/init/",
                         headers={"Authorization": f"Bearer {tok}",
                                  "Content-Type": "application/json; charset=UTF-8"},
                         json={"source_info": {"source": "FILE_UPLOAD", "video_size": size,
                                               "chunk_size": size, "total_chunk_count": 1}},
                         timeout=60).json()
    if init.get("error", {}).get("code") not in (None, "ok"):
        raise RuntimeError(f"TikTok init: {init}")
    up = init["data"]["upload_url"]
    with open(video, "rb") as f:
        r = requests.put(up, data=f.read(), headers={
            "Content-Type": "video/mp4", "Content-Length": str(size),
            "Content-Range": f"bytes 0-{size - 1}/{size}"}, timeout=300)
    if r.status_code >= 400:
        raise RuntimeError(f"TikTok upload: {r.text}")
    return init["data"]["publish_id"]


# ---------- main loop ----------
def load(path, default):
    try:
        return json.load(open(path))
    except FileNotFoundError:
        return default


def main():
    now = dt.datetime.now(TZ)
    state = load(STATE, {})
    plans = sorted(glob.glob("queue/*/plan.json"))
    did = 0
    for plan_path in plans:
        plan = json.load(open(plan_path))
        for item in plan["items"]:
            when = dt.datetime.fromisoformat(item["time"]).replace(tzinfo=TZ)
            if item.get("skip") or when > now:
                continue
            # only catch up on items from the last 12 hours
            if now - when > dt.timedelta(hours=12):
                continue
            for platform in item["platforms"]:
                key = f"{item['id']}:{platform}"
                if key in state:
                    continue
                cap = item["caption"]
                try:
                    if DRY:
                        res = "dry-run"
                    elif platform == "ig_carousel":
                        res = ig_carousel(item["images"], cap)
                    elif platform == "ig_reel":
                        res = ig_reel(item["video"], cap)
                    elif platform == "fb_photos":
                        res = fb_photos(item["images"], cap)
                    elif platform == "fb_reel":
                        res = fb_reel(item["video"], cap)
                    elif platform == "tiktok_inbox":
                        res = tt_inbox(item["video"])
                    else:
                        continue
                    state[key] = {"at": now.isoformat(), "result": str(res)}
                    log(f"posted {key}: {res}")
                    did += 1
                except Exception as e:
                    log(f"FAILED {key}: {e}")
                    state.setdefault("_errors", []).append(
                        {"key": key, "at": now.isoformat(), "error": str(e)[:500]})
                    state["_errors"] = state["_errors"][-50:]
                json.dump(state, open(STATE, "w"), indent=2)
    log(f"done, {did} posted")


if __name__ == "__main__":
    os.makedirs("state", exist_ok=True)
    main()
