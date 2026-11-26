"""One source of truth for Profile Buckets: build BOTH the bucket cards (RAW_BUCKETS) and the bucket matrix
(BUCKET_MATRIX) in bucket-explorer.html from the player rows of the owner's Hit Rates sheet ("Updated Hit Rates" tab:
a bucket summary row followed by one row per player with his season counts at each PPG mark).

Every number is recomputed from those player rows; the sheet's own summary rows are not used (they drifted from the
player rows in a few buckets). Every player is named on the cards (no unnamed "historical busts").

Repeater % (Audit 4, Rule A): players with only one completed NFL season can't have repeated yet, so hitters from the
newest completed class (LAST_DONE) are left out of the repeater denominator. Everything else counts them.

Usage:
  python3 scripts/build_buckets.py "Updated Hit Rates.xlsx" --last-done 2025            # dry run: prints a summary
  python3 scripts/build_buckets.py "Updated Hit Rates.xlsx" --last-done 2025 --write    # rewrites bucket-explorer.html
"""
import json, re, sys
import openpyxl

HTML = "bucket-explorer.html"
# section header in column A -> (key, marks, hit-mark index, cards?)
SECTIONS = [
    ("QB", "QB", ["16+", "20+", "24+"], 1, True),
    ("RB", "RB", ["12+", "15+", "18+"], 1, True),
    ("WR", "WR_RAW", ["12+", "14+", "16+", "18+"], 1, False),
    ("WR (Size-Adjusted)", "WR", ["12+", "14+", "16+", "18+"], 1, True),
    ("TE", "TE", ["12+", "14+", "17+"], 0, True),
]
# Names the cards disambiguate (two players share a name in the data)
RENAME = {("Steve Smith", 2007, "WR"): "Steve Smith NYG", ("Mike Williams", 2010, "WR"): "Mike Williams TB",
          ("Zach Miller", 2009, "TE"): "Zach Miller CHI"}
HEADERS = {"QB": "QB (near=16+, hit=20+, elite=24+)", "RB": "RB (near=12+, hit=15+, elite=18+)",
           "WR": "WR Size-Adjusted (near=12+, hit=14+, elite=16+, superElite=18+)",
           "TE": "TE 1.5 TEP (tuple: [name, year, 12+ seasons, 14+ seasons, 17+ seasons]; hit = 12+, no near tier)"}


def read_sheet(path):
    ws = openpyxl.load_workbook(path, data_only=True)["Updated Hit Rates"]
    starts = {str(ws.cell(r, 1).value).strip(): r for r in range(1, ws.max_row + 1) if ws.cell(r, 2).value == "Year"}
    order = sorted(starts.values())
    out = {}
    for head, key, marks, hit_i, _ in SECTIONS:
        st = starts[head]
        en = next((x for x in order if x > st), ws.max_row + 1)
        buckets, cur = [], None
        for r in range(st + 1, en):
            a, b = ws.cell(r, 1).value, ws.cell(r, 2).value
            if not a:
                continue
            if b is None:   # bucket summary row: only its name is used
                cur = {"name": str(a).strip(), "players": []}
                buckets.append(cur)
            elif cur is not None:
                c = [ws.cell(r, 8 + i).value for i in range(len(marks))]
                nm = RENAME.get((str(a).strip(), int(b), "WR" if key == "WR_RAW" else key), str(a).strip())
                rookie = all(x is None for x in c)
                cur["players"].append([nm, int(b)] + (["rookie"] if rookie else [int(x or 0) for x in c]))
        out[key] = (marks, hit_i, buckets)
    return out


def stats(players, hit_i, last_done):
    vets = [p for p in players if p[2] != "rookie"]
    n = len(vets)
    c = lambda p, i: p[2 + i]
    share = lambda k: (k / n) if n else None
    can_repeat = lambda p: last_done - p[1] + 1 >= 2          # Rule A
    def rep(i):
        hs = [p for p in vets if c(p, i) >= 1 and can_repeat(p)]
        return (sum(c(p, i) >= 2 for p in hs) / len(hs)) if hs else None
    k = len(vets[0]) - 2 if vets else 0
    return {
        "n": n, "hits": sum(c(p, hit_i) >= 1 for p in vets),
        "rates": [share(sum(c(p, i) >= 1 for p in vets)) for i in range(k)] if n else [],
        "low2": share(sum(c(p, 0) >= 2 for p in vets)), "low3": share(sum(c(p, 0) >= 3 for p in vets)),
        "lowRep": rep(0), "hit2": share(sum(c(p, 1) >= 2 for p in vets)), "hitRep": rep(1),
    }


def r4(v):
    return None if v is None else round(v, 4)


def r1(v):
    return 0.0 if v is None else round(100 * v + 1e-9, 1)


def build(path, last_done):
    data = read_sheet(path)
    matrix, cards = {}, []
    for head, key, marks, hit_i, on_cards in SECTIONS:
        marks_, hit_i, buckets = data[key]
        rows, tier_tot = [], {}
        for b in buckets:
            s = stats(b["players"], hit_i, last_done)
            tier = b["name"].split(" ")[0]
            t = tier_tot.setdefault(tier, [0, 0]); t[0] += s["hits"]; t[1] += s["n"]
            rows.append({"name": b["name"], "tier": tier, "hitRate": r4(s["hits"] / s["n"]) if s["n"] else None, "hits": s["hits"], "n": s["n"],
                         "rates": [r4(x) for x in s["rates"]] or [None] * len(marks), "low2": r4(s["low2"]), "low3": r4(s["low3"]),
                         "lowRep": r4(s["lowRep"]), "hit2": r4(s["hit2"]), "hitRep": r4(s["hitRep"])})
            if on_cards and s["n"] + sum(1 for p in b["players"] if p[2] == "rookie") > 0:
                rate = lambda i: r1(s["rates"][i]) if s["rates"] else 0.0
                if key == "TE":   # TE cards: hit = 12+, 2+ seasons and repeater at 12+ (Rule A); te12 tells the page not to recompute
                    card = dict(hit=rate(0), nearTotal=rate(0), elite=rate(2), twoPlus=r1(s["low2"]), rep=r1(s["lowRep"]), te12=True)
                else:
                    card = dict(hit=rate(1), nearTotal=rate(0), elite=rate(2), twoPlus=r1(s["hit2"]), rep=r1(s["hitRep"]))
                cards.append(dict(pos=key, name=b["name"], n=s["n"], **card, extraHistoricalBusts=0, players=b["players"]))
        for r in rows:
            r["tierOverall"] = r4(tier_tot[r["tier"]][0] / tier_tot[r["tier"]][1]) if tier_tot[r["tier"]][1] else None
        matrix[key] = {"marks": marks, "lowMark": marks[0], "hitMark": marks[hit_i], "rep2Mark": marks[1], "rows": rows}
    return matrix, cards


def js_cards(cards):
    out, last = ["    const RAW_BUCKETS = ["], None
    fmt = lambda v: "null" if v is None else (f"{v:.1f}" if isinstance(v, float) else json.dumps(v))
    for c in cards:
        if c["pos"] != last:
            out.append(f"      // ---------------- {HEADERS[c['pos']]} ----------------"); last = c["pos"]
        te = ", te12: true" if c.get("te12") else ""
        out.append("      {")
        out.append(f"        pos: '{c['pos']}', name: {json.dumps(c['name'])}, n: {c['n']}, hit: {fmt(c['hit'])}, nearTotal: {fmt(c['nearTotal'])}, "
                   f"elite: {fmt(c['elite'])}, twoPlus: {fmt(c['twoPlus'])}, rep: {fmt(c['rep'])}{te}, extraHistoricalBusts: 0,")
        out.append("        players: [")
        out.append(",\n".join("          " + json.dumps(p, ensure_ascii=False) for p in c["players"]))
        out.append("        ]")
        out.append("      },")
    out[-1] = "      }"
    out.append("    ];")
    return "\n".join(out)


if __name__ == "__main__":
    args = sys.argv[1:]
    path = args[0]
    last_done = int(args[args.index("--last-done") + 1])
    matrix, cards = build(path, last_done)
    print(f"cards: {len(cards)} buckets, {sum(len(c['players']) for c in cards)} players; matrix: "
          + ", ".join(f"{k} {len(v['rows'])}" for k, v in matrix.items()), file=sys.stderr)
    if "--write" in args:
        s = open(HTML, encoding="utf-8").read()
        i = s.index("    const RAW_BUCKETS = ["); j = s.index("\n    ];", i) + len("\n    ];")
        s = s[:i] + js_cards(cards) + s[j:]
        s, k = re.subn(r"const BUCKET_MATRIX = \{.*?\};\n", lambda _: "const BUCKET_MATRIX = " + json.dumps(matrix, separators=(",", ":")) + ";\n", s, count=1)
        assert k == 1
        open(HTML, "w", encoding="utf-8").write(s)
        print("wrote", HTML, file=sys.stderr)
    else:
        print(json.dumps({"cards": [{k: v for k, v in c.items() if k != "players"} for c in cards]}, indent=0)[:3000])
