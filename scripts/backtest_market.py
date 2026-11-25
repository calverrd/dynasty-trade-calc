"""Backtest the rookie tabs' CHEAP / PRICEY flags against DynastyProcess market values.

Manual research job: reads the rookie tab pages and a blobless clone of dynastyprocess/data, and
writes a markdown report. It never touches the site's data files.

For each past class (default 2020-2025) and each decision date (Tuesday after Week 4 / after Week 8):
  1. Hit odds per rookie from a logistic fit on log(draft pick) + usage (Games 1-4 at Week 5,
     Games 1-8 at Week 9), fit only on classes already settled at that date (class <= season - 2),
     the same two inputs the live site uses.
  2. Market value = DynastyProcess value_2qb from the last snapshot on or before that date.
  3. Flags exactly as on the site: odds rank vs value rank within the class and position; CHEAP if
     the value rank is at least a fifth of the list below the odds rank and the value is at least
     max(500, 15%) below the value at his odds rank; PRICEY the reverse; else FAIR.
  4. Outcome: value change to +6 months (pre-NFL Draft) and +12 months, compared within the same
     position and starting-value tier so cheap-player mean reversion isn't counted as an edge.

Usage: python scripts/backtest_market.py <site_dir> <dp_repo_dir> <out.md> [first_class] [last_class]
"""
import datetime as dt
import json
import math
import re
import subprocess
import sys
import unicodedata
from io import StringIO

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

SITE, DP, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
FIRST = int(sys.argv[4]) if len(sys.argv) > 4 else 2020
LAST = int(sys.argv[5]) if len(sys.argv) > 5 else 2025
MIN_GAP = float(sys.argv[6]) if len(sys.argv) > 6 else 500  # the site's KTC-scale floor; 0 = rank gap + 15% only
DATA_RE = re.compile(r"^\s*const DATA = (.*);\s*$", re.M)
DP_FILE = "files/values-players.csv"
rng = np.random.default_rng(7)


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b\.?", "", s)
    return re.sub(r"[^a-z]", "", s)


def season_start(y):
    """Thursday after Labor Day (first Monday of September)."""
    d = dt.date(y, 9, 1)
    while d.weekday() != 0:
        d += dt.timedelta(days=1)
    return d + dt.timedelta(days=3)


def decision_date(y, wk):  # Tuesday after week `wk`
    return season_start(y) + dt.timedelta(days=7 * (wk - 1) + 5)


# ---------------------------------------------------------------- rookie data from the site
rows = []
for pos, fn in (("WR", "rookie-wr-tracker.html"), ("RB", "rookie-rb-tracker.html"), ("TE", "rookie-te-tracker.html")):
    s = open(f"{SITE}/{fn}", encoding="utf-8").read()
    for o in json.loads(DATA_RE.search(s).group(1)):
        rows.append(dict(pos=pos, n=o["n"], key=norm(o["n"]), yr=o["yr"], pk=o.get("pk") or 300,
                         tier=o["tier"], u4=o.get("u"), g4=o.get("g") or 0, u8=o.get("u8"), g8=o.get("g8") or 0))
R = pd.DataFrame(rows)
R["hit"] = (R.tier != "red") & (R.tier != "tbd")
R["lp"] = np.log(R.pk)

# ---------------------------------------------------------------- DynastyProcess snapshots from git history
_snap_cache = {}


def snapshot(date):
    """values-players.csv as of the last commit on or before `date`."""
    sha = subprocess.run(["git", "-C", DP, "rev-list", "-n", "1", f"--before={date.isoformat()} 23:59", "HEAD", "--", DP_FILE],
                         capture_output=True, text=True).stdout.strip()
    if not sha:
        return None, None
    if sha not in _snap_cache:
        txt = subprocess.run(["git", "-C", DP, "show", f"{sha}:{DP_FILE}"], capture_output=True, text=True).stdout
        df = pd.read_csv(StringIO(txt)) if txt else pd.DataFrame()
        if not df.empty and "value_2qb" in df:
            df["key"] = df.player.map(norm)
            df = df[df.pos.isin(["WR", "RB", "TE"])].sort_values("value_2qb", ascending=False).drop_duplicates(["key", "pos"])
        _snap_cache[sha] = df
    df = _snap_cache[sha]
    when = df.scrape_date.max() if not df.empty and "scrape_date" in df else None
    return df, when


# ---------------------------------------------------------------- build flags at each decision date
recs, notes = [], []
for y in range(FIRST, LAST + 1):
    for wk, ucol, gcol, label in ((5, "u4", "g4", "Week 5 (Games 1-4)"), (9, "u8", "g8", "Week 9 (Games 1-8)")):
        d0 = decision_date(y, wk)
        d6, d12 = d0 + dt.timedelta(days=182), d0 + dt.timedelta(days=365)
        v0, w0 = snapshot(d0)
        if v0 is None or v0.empty:
            notes.append(f"{y} {label}: no DynastyProcess snapshot on or before {d0}")
            continue
        v6, w6 = snapshot(d6)
        v12, w12 = snapshot(d12)
        for pos in ("WR", "RB", "TE"):
            if pos == "TE" and wk == 5:
                continue  # the TE tab only uses Games 1-8
            train = R[(R.pos == pos) & (R.yr <= y - 2) & R[ucol].notna() & (R[gcol] >= 2) & (R.tier != "tbd")]
            cls = R[(R.pos == pos) & (R.yr == y) & R[ucol].notna() & (R[gcol] >= 2)].copy()
            if len(train) < 40 or train.hit.nunique() < 2 or cls.empty:
                continue
            m = LogisticRegression(max_iter=1000).fit(train[["lp", ucol]], train.hit)
            cls["hp"] = m.predict_proba(cls[["lp", ucol]])[:, 1]
            mv = v0[v0.pos == pos][["key", "value_2qb"]].rename(columns={"value_2qb": "v0"})
            cls = cls.merge(mv, on="key", how="inner")
            if len(cls) < 6:
                continue
            for nm, vv in (("v6", v6), ("v12", v12)):
                if vv is not None and not vv.empty:
                    cls = cls.merge(vv[vv.pos == pos][["key", "value_2qb"]].rename(columns={"value_2qb": nm}), on="key", how="left")
                else:
                    cls[nm] = np.nan
            n = len(cls)
            by_hp = cls.sort_values(["hp", "v0"], ascending=False).reset_index(drop=True)
            by_v = cls.sort_values("v0", ascending=False).reset_index(drop=True)
            vrank = {k: i + 1 for i, k in enumerate(by_v.key)}
            th = max(3, round(n * 0.2))
            for i, r in by_hp.iterrows():
                hr, kr = i + 1, vrank[r.key]
                v_at = by_v.v0.iloc[hr - 1]
                big = abs(r.v0 - v_at) >= max(MIN_GAP, 0.15 * r.v0)
                gap = kr - hr
                flag = ("CHEAP" if gap >= th else "PRICEY" if gap <= -th else "FAIR") if big else "FAIR"
                recs.append(dict(cls=y, when=label, pos=pos, n=r.n, hp=round(float(r.hp), 3), v0=r.v0,
                                 v6=r.v6, v12=r.v12, flag=flag, snap0=w0, snap6=w6, snap12=w12))
        notes.append(f"{y} {label}: decision {d0} (snapshot {w0}), +6m {d6} ({w6}), +12m {d12} ({w12})")

B = pd.DataFrame(recs)
out = ["# CHEAP / PRICEY vs DynastyProcess market values", "",
       f"Classes {FIRST}-{LAST}. Value = DynastyProcess `value_2qb` (superflex). Minimum value gap {MIN_GAP:g} points (plus 15%). Run {dt.date.today()}.", ""]
if B.empty:
    out += ["**No players matched.** Snapshot notes:", ""] + [f"- {x}" for x in notes]
    open(OUT, "w").write("\n".join(out) + "\n")
    sys.exit(0)

# value-change outcomes: log ratio (symmetric; a 50% rise and a 33% fall cancel). Missing later value = left the list.
for h in ("6", "12"):
    B[f"lr{h}"] = np.log(B[f"v{h}"].clip(lower=1) / B.v0)
# starting-value tier within position (terciles over the whole sample)
B["tier"] = B.groupby("pos").v0.transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=["low", "mid", "high"]))


def pct(x):
    return f"{100 * (math.exp(x) - 1):+.0f}%" if pd.notna(x) else "—"


def strat_diff(df, a, b, col):
    """Mean log-ratio difference a minus b, averaged over (pos, tier) cells with both groups, weighted by
    the smaller group's size. Bootstrap CI resamples players within cells."""
    cells = [(k, g) for k, g in df.groupby(["pos", "tier"], observed=True) if (g.flag == a).any() and (g.flag == b).any()]
    if not cells:
        return None

    def est(sample_fn):
        num = den = 0.0
        for _, g in cells:
            ga, gb = sample_fn(g[g.flag == a][col].dropna().values), sample_fn(g[g.flag == b][col].dropna().values)
            if len(ga) == 0 or len(gb) == 0:
                continue
            w = min(len(ga), len(gb))
            num += w * (ga.mean() - gb.mean())
            den += w
        return num / den if den else np.nan

    point = est(lambda v: v)
    boots = [est(lambda v: rng.choice(v, len(v)) if len(v) else v) for _ in range(1000)]
    boots = [x for x in boots if pd.notna(x)]
    return point, np.percentile(boots, 2.5), np.percentile(boots, 97.5), sum(min((g.flag == a).sum(), (g.flag == b).sum()) for _, g in cells)


out += ["## Sample", "", "| Decision point | Players | CHEAP | FAIR | PRICEY |", "|---|---|---|---|---|"]
for w, g in B.groupby("when"):
    c = g.flag.value_counts()
    out.append(f"| {w} | {len(g)} | {c.get('CHEAP', 0)} | {c.get('FAIR', 0)} | {c.get('PRICEY', 0)} |")
out += ["", "## Raw value change by flag (not stratified; mean reversion included)", "",
        "| Decision point | Flag | n | +6 months (median) | +12 months (median) | Still listed at +12m |", "|---|---|---|---|---|---|"]
for (w, f), g in B.groupby(["when", "flag"]):
    out.append(f"| {w} | {f} | {len(g)} | {pct(g.lr6.median())} | {pct(g.lr12.median())} | {g.v12.notna().mean():.0%} |")

out += ["", "## Stratified edge (same position and starting-value tier)", "",
        "Difference in mean log value change, shown as a percent. Positive for CHEAP vs FAIR, or negative for PRICEY vs FAIR, means the flag worked. 95% bootstrap interval.", "",
        "| Decision point | Comparison | Horizon | Edge | 95% CI | Matched n |", "|---|---|---|---|---|---|"]
for w, g in list(B.groupby("when")) + [("Both decision points", B)]:
    for a, b in (("CHEAP", "FAIR"), ("PRICEY", "FAIR"), ("CHEAP", "PRICEY")):
        for h in ("6", "12"):
            r = strat_diff(g, a, b, f"lr{h}")
            if r is None:
                continue
            p, lo, hi, nn = r
            out.append(f"| {w} | {a} vs {b} | +{h}m | {pct(p)} | {pct(lo)} to {pct(hi)} | {nn} |")

out += ["", "## By position (both decision points, +12 months, stratified CHEAP vs PRICEY)", "", "| Position | Edge | 95% CI | Matched n |", "|---|---|---|---|"]
for pos, g in B.groupby("pos"):
    r = strat_diff(g, "CHEAP", "PRICEY", "lr12")
    out.append(f"| {pos} | " + ("— | — | 0 |" if r is None else f"{pct(r[0])} | {pct(r[1])} to {pct(r[2])} | {r[3]} |"))

out += ["", "## Flagged players", "", "| Class | Decision | Pos | Player | Odds | Value | +6m | +12m | Flag |", "|---|---|---|---|---|---|---|---|---|"]
for r in B[B.flag != "FAIR"].sort_values(["cls", "when", "flag", "hp"], ascending=[True, True, True, False]).itertuples():
    fv = lambda v: "—" if pd.isna(v) else f"{v:,.0f}"
    out.append(f"| {r.cls} | {r.when.split(' (')[0]} | {r.pos} | {r.n} | {r.hp:.0%} | {fv(r.v0)} | {fv(r.v6)} | {fv(r.v12)} | {r.flag} |")

out += ["", "## Caveats", "",
        "- Odds are refit per season on classes settled by then, but usage tiers come from today's data (e.g. a later sheet correction), so this is close to, not exactly, point-in-time.",
        "- Decision dates are approximate (Tuesday after Week 4 / Week 8 from the season's opening Thursday); byes mean some teams had played one fewer game.",
        "- DynastyProcess values are not KTC values; the 500-point and 15% thresholds were set for KTC's scale, which is similar but not identical.",
        "- Players who drop off the DynastyProcess list have no later value and are left out of the edge, which flatters busts in both groups.",
        "- Name matching is by normalized name and position; unmatched rookies are skipped.",
        "", "## Snapshot log", ""] + [f"- {x}" for x in notes]
open(OUT, "w").write("\n".join(out) + "\n")
B.to_csv(OUT.replace(".md", ".csv"), index=False)
print("\n".join(out[:40]))
