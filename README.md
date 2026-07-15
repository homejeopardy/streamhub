# StreamHub

A unified browsing UI that combines **YouTube** and **Nebula** into one feed — your subscriptions from both platforms in a single, consistent interface.

![StreamHub](https://img.shields.io/badge/no%20API%20key-required-brightgreen)

## Features

- **Unified feed** — YouTube videos and Nebula content interleaved, newest-first
- **Real recent videos** — pulled live from each channel's public YouTube RSS feed (no API key)
- **Inline playback** — YouTube videos play in an embedded player; Nebula deep-links out
- **Tabs** — Home, **Shorts** (auto-detected), **Live** (channels streaming now), Subscriptions
- **Live functionality** — red LIVE badges, a live count, auto-refresh, and a manual refresh button
- **Unified search** — filters your library instantly; Enter searches both YouTube and Nebula on the web
- **Source & creator filters**, collapsible sidebar, responsive + dark UI

## How it works

Neither `youtube.com` nor `nebula.tv` can be embedded in an `<iframe>` (both block framing), and Nebula has no public API. So StreamHub is a **unified hub**: one UI where both platforms live together, YouTube plays inline via `youtube-nocookie.com/embed`, and Nebula deep-links out.

The YouTube side is powered by each channel's **public RSS feed** (`youtube.com/feeds/videos.xml`) — no API key, no login.

## Setup

Just open `index.html` — or serve it locally:

```bash
python3 -m http.server 8777
# then open http://localhost:8777
```

## Refreshing the feed

`build_feeds.py` resolves your subscribed channels to their IDs, fetches each channel's latest videos (and detects Shorts + live streams), and writes `feeds.json`, which the app loads.

```bash
python3 build_feeds.py
```

Edit the `YT_SUBS` / `NEBULA_SUBS` lists in both `build_feeds.py` and `index.html` to change which channels appear. Use the `OVERRIDES` dict in `build_feeds.py` to pin a channel that auto-resolves to the wrong ID.

## Files

| File | Purpose |
|------|---------|
| `index.html` | The entire app (self-contained HTML/CSS/JS) |
| `build_feeds.py` | Fetches real videos/shorts/live status → `feeds.json` |
| `feeds.json` | Generated feed data the app reads |
