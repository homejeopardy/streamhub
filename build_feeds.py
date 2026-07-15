#!/usr/bin/env python3
"""
StreamHub feed builder.

Resolves each YouTube subscription (by display name) to its channel ID, then
pulls the channel's public RSS feed (youtube.com/feeds/videos.xml) for the
latest videos. Writes feeds.json, which index.html loads to show real recent
videos with real thumbnails and inline playback.

No API key required — uses only public search + RSS. Re-run any time to refresh:
    python3 build_feeds.py
"""
import json, re, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# --- Your YouTube subscriptions (must match YT_SUBS in index.html) -----------
YT_SUBS = [
    "2 Much ColinFurze","Aaron Rheins","BocaBola","Brandon Y Lee","Bud n' Pal",
    "Chaz Draycott Media","colinfurze","Dallas Taylor","DIY Perks","Engwerda Studios",
    "Hamfrags","Ivan Miranda","Izzie Norwood","JackSucksAtLife","JackSucksAtStuff",
    "Jon Youshaei","Linus Tech Tips","Luke Lafreniere","Man Made","Mark Rober",
    "Morley Kert","Mr Beardstone","MrBeast","MrBeast 2","Mrwhosetheboss",
    "Mrwhosetheboss Plus","Mumbo Jumbo","Nick DiGiovanni","Ryan Trahan","Sage Ellenwood",
    "Sam from Wendover","Schoolhouse Homestead","Shiloh & Bros","ShortCircuit",
    "Silver Creek Audio","Solidarity","Stam1o","Sticks","Swami 3","Taskmaster",
    "WAN Show","Wendover Productions","Zip Tie Tech","Zip Tie Tuning",
]

# Optional manual overrides for ambiguous names -> exact channel IDs.
# Fill these in if the auto-resolver picks the wrong channel.
OVERRIDES = {
    # "WAN Show": "UCXuqSBlHAE6Xw-yeJA0Tunw",
}

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")
NS = {"a": "http://www.w3.org/2005/Atom",
      "yt": "http://www.youtube.com/xml/schemas/2015",
      "media": "http://search.yahoo.com/mrss/"}
MAX_VIDEOS = 6


def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def resolve_channel_id(name):
    """Scrape the search results page for the first channelId. Prefer a channel
    result whose byline matches the query when possible."""
    q = urllib.parse.quote(name)
    html = get(f"https://www.youtube.com/results?search_query={q}")
    # channelRenderer blocks are actual channels (not videos); prefer those.
    m = re.search(r'"channelRenderer":\{"channelId":"(UC[\w-]{22})"', html)
    if m:
        return m.group(1)
    ids = re.findall(r'"channelId":"(UC[\w-]{22})"', html)
    return ids[0] if ids else None


def fetch_feed(channel_id):
    xml = get(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
    root = ET.fromstring(xml)
    feed_title = (root.findtext("a:title", default="", namespaces=NS) or "").strip()
    videos = []
    for entry in root.findall("a:entry", NS):
        vid = entry.findtext("yt:videoId", default="", namespaces=NS)
        title = (entry.findtext("a:title", default="", namespaces=NS) or "").strip()
        published = entry.findtext("a:published", default="", namespaces=NS)
        grp = entry.find("media:group", NS)
        views = ""
        if grp is not None:
            stats = grp.find("media:community/media:statistics", NS)
            if stats is not None:
                views = stats.get("views", "")
        # Shorts vs long-form: YouTube points the alternate link at /shorts/<id>.
        link = entry.find("a:link[@rel='alternate']", NS)
        href = link.get("href", "") if link is not None else ""
        is_short = "/shorts/" in href
        if vid:
            videos.append({"videoId": vid, "title": title, "published": published,
                           "views": views, "short": is_short})
        if len(videos) >= MAX_VIDEOS:
            break
    return feed_title, videos


def detect_live(channel_id):
    """Check the channel's /live page. If it's streaming right now, return the
    live video's {videoId, title}; otherwise None."""
    try:
        html = get(f"https://www.youtube.com/channel/{channel_id}/live", timeout=15)
    except Exception:
        return None
    if '"isLive":true' not in html:
        return None
    m = re.search(r'<link rel="canonical" href="https://www\.youtube\.com/watch\?v=([\w-]{11})">', html)
    if not m:
        m = re.search(r'"videoId":"([\w-]{11})"', html)
    if not m:
        return None
    tm = re.search(r'<meta name="title" content="([^"]*)">', html)
    title = (tm.group(1) if tm else "").strip() or "Live now"
    return {"videoId": m.group(1), "title": title}


def main():
    out = {"generated": datetime.now(timezone.utc).isoformat(), "channels": []}
    for i, name in enumerate(YT_SUBS, 1):
        cid = OVERRIDES.get(name)
        try:
            if not cid:
                cid = resolve_channel_id(name)
            if not cid:
                print(f"[{i:2}/{len(YT_SUBS)}] {name:28} -> NOT FOUND", file=sys.stderr)
                out["channels"].append({"name": name, "channelId": None,
                                        "resolvedTitle": None, "videos": []})
                continue
            feed_title, videos = fetch_feed(cid)
            live = detect_live(cid)
            n_short = sum(1 for v in videos if v.get("short"))
            match = "OK " if feed_title.lower() == name.lower() else "~? "
            flag = "  🔴LIVE" if live else ""
            print(f"[{i:2}/{len(YT_SUBS)}] {name:28} -> {cid}  "
                  f"{match}({feed_title}) {len(videos)} vids, {n_short} shorts{flag}",
                  file=sys.stderr)
            out["channels"].append({"name": name, "channelId": cid,
                                    "resolvedTitle": feed_title, "videos": videos,
                                    "live": live})
        except Exception as e:
            print(f"[{i:2}/{len(YT_SUBS)}] {name:28} -> ERROR {e}", file=sys.stderr)
            out["channels"].append({"name": name, "channelId": cid,
                                    "resolvedTitle": None, "videos": []})
        time.sleep(0.4)  # be polite

    with open("feeds.json", "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    got = sum(1 for c in out["channels"] if c["videos"])
    print(f"\nWrote feeds.json — {got}/{len(YT_SUBS)} channels with videos.",
          file=sys.stderr)


if __name__ == "__main__":
    main()
