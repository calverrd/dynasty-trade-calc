"""Write data/bucket-stats.json from the Profile Buckets data in bucket-explorer.html (RAW_BUCKETS), so the hub's
player popup shows the same Hit / Starter / Bust bar as the bucket detail, from one source.

Same arithmetic as bucket-explorer.html (bucket detail): hit = hit, starter only = nearTotal - hit (none for TE),
bust = 100 - nearTotal. Every TE bucket is built at 12+ by scripts/build_buckets.py (te12), so no recompute is needed.
Run by `scripts/build_buckets.py ... --write`; safe to run on its own: python3 scripts/export_bucket_stats.py [repo root]
"""
import json, os, re, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..")
LBL = {"QB": ("16+", "20+", "24+"), "RB": ("12+", "15+", "18+"), "WR": ("12+", "14+", "16+"), "TE": (None, "12+", "17+")}
NUM = r"(-?[\d.]+|null)"
HEAD = re.compile(r"pos: '(\w+)', name: (\"[^\"]+\"), n: (\d+), hit: " + NUM + r", nearTotal: " + NUM + r", elite: " + NUM
                  + r", twoPlus: " + NUM + r", rep: " + NUM + r"(, te12: true)?")


def main():
    s = open(os.path.join(ROOT, "bucket-explorer.html"), encoding="utf-8").read()
    i = s.index("const RAW_BUCKETS = ["); j = s.index("\n    ];", i)
    f = lambda v: None if v == "null" else float(v)
    out = {}
    for pos, name, n, hit, near, elite, two, rep, te12 in HEAD.findall(s[i:j]):
        name = json.loads(name)
        hit, near = f(hit) or 0.0, f(near) or 0.0
        if pos == "TE" and not te12:
            raise SystemExit(f"TE bucket {name} isn't built at 12+; run scripts/build_buckets.py first")
        no_near = LBL[pos][0] is None
        out[f"{pos}|{name}"] = {
            "n": int(n), "hit": hit, "starter": 0.0 if no_near else max(0.0, round(near - hit, 1)),
            "bust": max(0.0, round(100 - near, 1)), "elite": f(elite), "rep": f(rep), "twoPlus": f(two),
            "hitLbl": LBL[pos][1], "starterLbl": LBL[pos][0], "eliteLbl": LBL[pos][2],
        }
    path = os.path.join(ROOT, "data", "bucket-stats.json")
    json.dump({"source": "bucket-explorer.html RAW_BUCKETS", "buckets": out}, open(path, "w"), separators=(",", ":"))
    print(f"wrote {path}: {len(out)} buckets", file=sys.stderr)


if __name__ == "__main__":
    main()
