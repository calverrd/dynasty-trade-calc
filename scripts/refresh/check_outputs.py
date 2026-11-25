"""Sanity gate for the Tuesday rookie refresh. Runs after refresh_rookies.py and build_context.py, before the commit.

Checks every file the workflow commits:
  - rookie-wr/rb/te-tracker.html: the `const DATA = [...]` line parses, has 100+ rows, and every row has a name,
    a class year and a tier
  - ppg.json: parses, has a season, 200+ players, and every PPG is a number from -10 to 70
  - signals.json / bf.json: parse, have a season and a non-empty players list
  - data/player-context.json: parses, WR/RB/TE rows match the tracker pages, 100+ veteran ages
And against the last committed version (git HEAD): no file may lose more than 15% of its rows, and the season
may not go backwards. A bad nflverse download or a parsing change then fails the run instead of publishing
half-empty tabs.

Usage: python scripts/refresh/check_outputs.py [repo_dir]
Exits 1 with a list of problems; the workflow then restores the committed files and fails.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
PAGES = {"WR": "rookie-wr-tracker.html", "RB": "rookie-rb-tracker.html", "TE": "rookie-te-tracker.html"}
MAX_DROP = 0.15
DATA_RE = re.compile(r"const DATA = (\[.*?\]);\s*\n", re.S)
problems = []


def head(rel):
    """Text of the committed version, or None if the file is new / git isn't available."""
    try:
        return subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], capture_output=True, text=True, check=True).stdout
    except Exception:
        return None


def page_rows(text):
    m = DATA_RE.search(text or "")
    return json.loads(m.group(1)) if m else None


def json_text(text):
    try:
        return json.loads(text) if text else None
    except ValueError:
        return None


def shrink(label, new_n, old_n):
    if old_n and new_n < (1 - MAX_DROP) * old_n:
        problems.append(f"{label}: {new_n} rows, down from {old_n} (more than {int(MAX_DROP * 100)}%)")


def season_check(label, new, old):
    if old and new and isinstance(new.get("season"), int) and isinstance(old.get("season"), int) and new["season"] < old["season"]:
        problems.append(f"{label}: season went backwards ({old['season']} -> {new['season']})")


# Tracker pages
page_n = {}
for pos, rel in PAGES.items():
    try:
        rows = page_rows((ROOT / rel).read_text(encoding="utf-8"))
    except Exception as e:
        problems.append(f"{rel}: unreadable ({e})")
        continue
    if rows is None:
        problems.append(f"{rel}: DATA line missing or not valid JSON")
        continue
    page_n[pos] = len(rows)
    if len(rows) < 100:
        problems.append(f"{rel}: only {len(rows)} rows")
    bad = [r for r in rows if not r.get("n") or not isinstance(r.get("yr"), int) or not r.get("tier")]
    if bad:
        problems.append(f"{rel}: {len(bad)} rows missing name / class / tier (first: {bad[0].get('n')!r})")
    try:
        old = page_rows(head(rel))
    except ValueError:
        old = None
    shrink(rel, len(rows), len(old) if old else 0)


def load(rel):
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception as e:
        problems.append(f"{rel}: not valid JSON ({e})")
        return None


# ppg.json
ppg = load("ppg.json")
if ppg is not None:
    pl = ppg.get("players") or {}
    if not isinstance(ppg.get("season"), int):
        problems.append("ppg.json: no season")
    if len(pl) < 200:
        problems.append(f"ppg.json: only {len(pl)} players")
    badp = [k for k, v in pl.items() if not isinstance(v, dict) or not isinstance(v.get("ppg"), (int, float)) or not -10 <= v["ppg"] <= 70 or v.get("pos") not in ("QB", "RB", "WR", "TE")]
    if badp:
        problems.append(f"ppg.json: {len(badp)} bad rows (first: {badp[0]!r})")
    old = json_text(head("ppg.json"))
    season_check("ppg.json", ppg, old)
    # A new season starts small (Week 1); only compare counts within the same season
    if old and old.get("season") == ppg.get("season"):
        shrink("ppg.json", len(pl), len(old.get("players") or {}))

# signals.json, bf.json
for rel in ("signals.json", "bf.json"):
    d = load(rel)
    if d is None:
        continue
    pl = d.get("players")
    if not isinstance(d.get("season"), int):
        problems.append(f"{rel}: no season")
    if not pl:
        problems.append(f"{rel}: players list empty")
    old = json_text(head(rel))
    season_check(rel, d, old)
    if old and old.get("season") == d.get("season") and pl:
        shrink(rel, len(pl), len(old.get("players") or []))

# data/player-context.json
ctx = load("data/player-context.json")
if ctx is not None:
    for pos, n in page_n.items():
        got = len((ctx.get("rows") or {}).get(pos) or [])
        if got != n:
            problems.append(f"data/player-context.json: {pos} has {got} rows, page has {n}")
    if len(ctx.get("vets") or {}) < 100:
        problems.append(f"data/player-context.json: only {len(ctx.get('vets') or {})} veteran ages")

if problems:
    print("Sanity gate FAILED:")
    for p in problems:
        print("  -", p)
    sys.exit(1)
print(f"Sanity gate passed: pages {page_n}, ppg {len((ppg or {}).get('players') or {})} players, season {(ppg or {}).get('season')}")
