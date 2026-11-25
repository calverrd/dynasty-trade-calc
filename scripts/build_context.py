"""Build data/player-context.json: a slim, value-free context file for the Profile Buckets comparison tool.

Reads the `const DATA = [...]` line of the three rookie pages (written by refresh_rookies.py), ages (no values)
from the FantasyCalc cache (data/fc/fc-sf-ppr1-none.json) with ktc.json as the fallback, and ppg.json, and writes
only the fields the comparison needs:

  rows[pos]: one entry per rookie-tab player
      [name, class, round, pick, team, tier, u, u8, g, g8, gL, hp, tags, bf8, b3]
  vets: {"POS|normname": age} for players in ppg.json, used for next-season retention odds. Age source order matches
        index.html's sync (FantasyCalc's maybeAge first, then KTC's age), so both pages put a player in the same age band.

Run after refresh_rookies.py:  python scripts/build_context.py .
Exits non-zero (writing nothing) if any page's DATA is missing or too small.
"""
import json, os, re, sys, unicodedata

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
PAGES = {"WR": "rookie-wr-tracker.html", "RB": "rookie-rb-tracker.html", "TE": "rookie-te-tracker.html"}
MIN_ROWS = 100
FIELDS = ["n", "yr", "rd", "pk", "tm", "tier", "u", "u8", "g", "g8", "gL", "hp", "tags", "bf8", "b3"]


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b\.?", "", s)
    return re.sub(r"[^a-z]", "", s)


def page_data(path):
    txt = open(path, encoding="utf-8").read()
    m = re.search(r"const DATA = (\[.*?\]);\s*\n", txt, re.S)
    if not m:
        raise SystemExit(f"{path}: no DATA line")
    return json.loads(m.group(1))


def rnd(v):
    return round(v, 2) if isinstance(v, float) else v


def main():
    rows = {}
    for pos, fname in PAGES.items():
        data = page_data(os.path.join(ROOT, fname))
        if len(data) < MIN_ROWS:
            raise SystemExit(f"{fname}: only {len(data)} rows")
        rows[pos] = [[rnd(r.get(f)) if f not in ("hp", "tags") else (r.get(f) or ([] if f == "tags" else None)) for f in FIELDS] for r in data]

    ages, src = {}, {"fc": 0, "ktc": 0}
    try:  # 1) FantasyCalc (the hub's first choice)
        f = json.load(open(os.path.join(ROOT, "data", "fc", "fc-sf-ppr1-none.json"), encoding="utf-8"))
        c = {k: i for i, k in enumerate(f["fields"])}
        for r in f["players"]:
            if r[c["age"]] and r[c["pos"]] in ("QB", "RB", "WR", "TE"):
                ages.setdefault(f"{r[c['pos']]}|{norm(r[c['name']])}", ("fc", r[c["age"]]))
    except Exception as e:
        print("FantasyCalc cache ages unavailable:", e)
    try:  # 2) KTC, for players FantasyCalc has no age for
        k = json.load(open(os.path.join(ROOT, "ktc.json"), encoding="utf-8"))
        for p in k.get("players", []):
            if p.get("age") and p.get("position") in ("QB", "RB", "WR", "TE"):
                ages.setdefault(f"{p['position']}|{norm(p.get('playerName'))}", ("ktc", p["age"]))
    except Exception as e:  # ages are optional; retention odds just won't show
        print("ktc.json ages unavailable:", e)
    vets = {}
    try:
        ppg = json.load(open(os.path.join(ROOT, "ppg.json"), encoding="utf-8"))
        for name, v in ppg.get("players", {}).items():
            key = f"{v.get('pos')}|{norm(name)}"
            if key in ages:
                s_, a_ = ages[key]
                vets[key] = a_
                src[s_] += 1
    except Exception as e:
        print("ppg.json unavailable:", e)

    out = {"version": 1, "fields": FIELDS, "rows": rows, "vets": vets}
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    dest = os.path.join(ROOT, "data", "player-context.json")
    tmp = dest + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))
    json.load(open(tmp, encoding="utf-8"))  # must read back
    os.replace(tmp, dest)
    print(f"Wrote {dest}: " + ", ".join(f"{p} {len(r)}" for p, r in rows.items()) + f", vets {len(vets)} (ages: {src['fc']} FantasyCalc, {src['ktc']} KTC), {os.path.getsize(dest) // 1024} KB")


if __name__ == "__main__":
    main()
