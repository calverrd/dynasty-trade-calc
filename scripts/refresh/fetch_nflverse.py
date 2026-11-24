#!/usr/bin/env python3
"""Download the nflverse files refresh_rookies.py needs. Usage: python fetch_nflverse.py OUT_DIR"""
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
REL = "https://github.com/nflverse/nflverse-data/releases/download"
now = datetime.now(timezone.utc)
cur = now.year if now.month >= 8 else now.year - 1   # NFL season label

files = {
    "games.csv": "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv",
    "players.csv": f"{REL}/players/players.csv",
    "draft_picks.csv": f"{REL}/draft_picks/draft_picks.csv",
}
for y in range(2015, cur + 1):
    files[f"stats_player_week_{y}.csv"] = f"{REL}/stats_player/stats_player_week_{y}.csv"
    files[f"snap_counts_{y}.csv"] = f"{REL}/snap_counts/snap_counts_{y}.csv"


def get(url, path):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "dynasty-trade-calc-refresh"})
            with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
                f.write(r.read())
            return
        except Exception as e:  # noqa: BLE001
            if attempt == 3:
                raise
            print(f"retry {url}: {e}")
            time.sleep(5 * (attempt + 1))


for name, url in files.items():
    get(url, os.path.join(OUT, name))
    print("ok", name)
