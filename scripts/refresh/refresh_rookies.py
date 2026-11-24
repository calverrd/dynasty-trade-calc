#!/usr/bin/env python3
"""Refresh the Rookie WR / RB / TE tabs from nflverse data.

Usage: python refresh_rookies.py RAW_DIR SITE_DIR

RAW_DIR holds nflverse files (see fetch_nflverse.py). SITE_DIR holds rookie-wr-tracker.html,
rookie-rb-tracker.html and rookie-te-tracker.html; each page's `const DATA = [...];` line and its
"as of" date are rewritten in place.

What it does
- RB and TE: rebuilds every row (cells, usage, tiers, tags, comps) from nflverse alone.
- WR: rows carry profile buckets and Senior Bowl flags from outside nflverse, so existing rows are
  kept; rows for the last two classes get fresh cells/usage/tags, tiers are re-checked against
  completed seasons, and a new draft class is added with an empty bucket.
- All three: Year 2 fields (the player's team games 1-4 in his second season).

Rules match the validated models documented on each tab. A season counts toward tiers only once its
regular season is complete.
"""
import json
import math
import re
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

RAW, SITE = sys.argv[1], sys.argv[2]
TEAM = {"OAK": "LV", "LVR": "LV", "SD": "LAC", "SDG": "LAC", "STL": "LA", "LAR": "LA", "JAC": "JAX",
        "SFO": "SF", "TAM": "TB", "KAN": "KC", "NWE": "NE", "GNB": "GB", "NOR": "NO"}
FIRST = 2015

# ---------------------------------------------------------------- load
gm = pd.read_csv(f"{RAW}/games.csv", low_memory=False)
gm = gm[(gm.game_type == "REG") & (gm.season >= FIRST)].copy()
for c in ("home_team", "away_team"):
    gm[c] = gm[c].replace(TEAM)
played = gm[gm.home_score.notna()]
CUR = int(played.season.max())
done_by_season = gm.groupby("season").home_score.apply(lambda s: s.notna().all())
LAST_DONE = int(max(s for s, ok in done_by_season.items() if ok))
S = range(FIRST, CUR + 1)
print(f"current season {CUR}, last completed {LAST_DONE}")

wk = pd.concat([pd.read_csv(f"{RAW}/stats_player_week_{y}.csv", low_memory=False) for y in S])
wk = wk[wk.season_type == "REG"].copy()
wk["team"] = wk.team.replace(TEAM)
num = ["targets", "receptions", "receiving_yards", "receiving_tds", "carries", "rushing_yards",
       "rushing_tds", "fantasy_points_ppr", "receiving_first_downs", "receiving_air_yards"]
for c in num:
    if c in wk:
        wk[c] = wk[c].fillna(0)
sn = pd.concat([pd.read_csv(f"{RAW}/snap_counts_{y}.csv") for y in S])
sn = sn[sn.game_type == "REG"].copy()
sn["team"] = sn.team.replace(TEAM)
dp = pd.read_csv(f"{RAW}/draft_picks.csv", low_memory=False)
dp["team"] = dp.team.replace(TEAM)
pl = pd.read_csv(f"{RAW}/players.csv", low_memory=False)
pfr2gsis = pl[["pfr_id", "gsis_id"]].dropna()
sn = sn.merge(pfr2gsis, left_on="pfr_player_id", right_on="pfr_id", how="left")

# team game order (byes skipped)
g2 = pd.concat(ignore_index=True, objs=[
    gm[["season", "week", "home_team", "home_score"]].rename(columns={"home_team": "team", "home_score": "sc"}),
    gm[["season", "week", "away_team", "away_score"]].rename(columns={"away_team": "team", "away_score": "sc"})])
g2 = g2.sort_values(["season", "team", "week"])
g2["tg"] = g2.groupby(["season", "team"]).cumcount() + 1
g2["done"] = g2.sc.notna()

# completed-season PPG (8+ games), PPR and PPR + 0.5 TE premium
ss = wk[wk.season <= LAST_DONE].assign(tep=lambda x: x.fantasy_points_ppr + 0.5 * x.receptions)
ss = ss.groupby(["player_id", "season"]).agg(gp=("week", "count"), ppr=("fantasy_points_ppr", "sum"),
                                            tep=("tep", "sum")).reset_index()
ss = ss[ss.gp >= 8]
ss["ppr"] /= ss.gp
ss["tep"] /= ss.gp
BEST_PPR = ss.groupby("player_id").ppr.max().to_dict()
BEST_TEP = ss.groupby("player_id").tep.max().to_dict()

# per-game player lines with snaps
lines = wk[["player_id", "season", "week", "team"] + [c for c in num if c in wk]].rename(columns={"player_id": "gsis_id"})
snaps = sn[["gsis_id", "season", "week", "offense_pct"]].dropna(subset=["gsis_id"]).drop_duplicates(["gsis_id", "season", "week"])


def universe(pos):
    d = dp[(dp.position == pos) & dp.season.isin(S)][["season", "round", "pick", "team", "gsis_id", "pfr_player_id", "pfr_player_name"]]
    d = d.merge(pfr2gsis.rename(columns={"gsis_id": "g2", "pfr_id": "p2"}), left_on="pfr_player_id", right_on="p2", how="left")
    d["gsis_id"] = d.gsis_id.fillna(d.g2)
    d = d.drop(columns=["g2", "p2"]).drop_duplicates(["season", "pick"])
    u = pl[(pl.position == pos) & pl.draft_pick.isna() & pl.rookie_season.isin(S)][["rookie_season", "gsis_id", "pfr_id", "display_name"]]
    u = u.rename(columns={"rookie_season": "season", "pfr_id": "pfr_player_id", "display_name": "pfr_player_name"}).assign(round=np.nan, pick=np.nan, team=np.nan)
    uni = pd.concat([d, u], ignore_index=True).dropna(subset=["gsis_id"]).drop_duplicates("gsis_id")
    uni = uni.rename(columns={"season": "yr", "pfr_player_name": "name"})
    uni["name"] = uni.gsis_id.map(pl.set_index("gsis_id").display_name).fillna(uni.name)
    return uni


def season_team(ids_years, offset=0):
    """Most common team in season yr+offset for each player."""
    q = ids_years.assign(season=ids_years.yr + offset)[["gsis_id", "season"]]
    rw = lines.merge(q, on=["gsis_id", "season"])
    return rw.groupby("gsis_id").team.agg(lambda s: s.value_counts().index[0])


def team_games(uni, offset=0, team_col="tm"):
    q = uni[["gsis_id", "yr", team_col]].assign(season=uni.yr + offset).rename(columns={team_col: "team"})
    L = q.merge(g2, on=["season", "team"])
    L = L.merge(lines.drop(columns="team").assign(line=True), on=["gsis_id", "season", "week"], how="left")
    L["line"] = L.line.fillna(False).astype(bool)
    L = L.merge(snaps, on=["gsis_id", "season", "week"], how="left")
    for c in num:
        if c in L:
            L[c] = L[c].fillna(0)
    L["snap"] = L.offense_pct.fillna(0) > 0
    L["snp"] = L.offense_pct.fillna(0)
    return L.sort_values(["gsis_id", "tg"])


def comps(rows, pairs):
    lp = np.array([math.log(o["pk"] or 262) for o in rows])
    yr = np.array([o["yr"] for o in rows])
    settled = np.array([o["tier"] != "tbd" for o in rows])
    for out_key, ukey, gkey in pairs:
        u = np.array([o[ukey] if o[ukey] is not None else np.nan for o in rows], dtype=float)
        g = np.array([o[gkey] or 0 for o in rows])
        pool = settled & (g >= 2) & ~np.isnan(u)
        su, sp = np.nanstd(u[pool]), lp[pool].std()
        for i, o in enumerate(rows):
            if np.isnan(u[i]) or g[i] < 1:
                o[out_key] = []
                continue
            d = np.sqrt(2 * ((u - u[i]) / su) ** 2 + ((lp - lp[i]) / sp) ** 2)
            d[~pool | (yr == yr[i])] = np.inf
            d[np.isnan(d)] = np.inf
            o[out_key] = [int(j) for j in np.argsort(d)[:5] if np.isfinite(d[j])]


# ---------------------------------------------------------------- Year 2 (all positions)
Y2 = {  # usage formula per game, and tag cut-offs: low rookie < lo, Year-2 jump >= hi, rising >= rise
    "WR": dict(lo=15, hi=15, rise=12),
    "RB": dict(lo=14, hi=20, rise=17),
    "TE": dict(lo=6, hi=9, rise=7.5),
}


def usage_cols(L, pos):
    if pos == "WR":
        L["u"] = 2.2 * L.targets + L.receptions + 0.12 * L.receiving_yards + 0.5 * L.receiving_tds
        L["cnt"] = L.snap | (L.targets > 0) | (L.carries > 0) | (L.fantasy_points_ppr != 0)
    elif pos == "RB":
        L["u"] = L.carries + 2.5 * L.targets
        L["cnt"] = L.snap | ((L.carries + L.targets) > 0)
    else:
        L["u"] = L.targets + 10 * L.snp
        L["cnt"] = L.snap | (L.targets > 0)
    return L


def y2_cell(r, pos):
    if not r.done:
        return {"s": "TBD"}
    if not r.cnt:
        return {"s": "DNP"}
    p = float(r.fantasy_points_ppr) + (0.5 * float(r.receptions) if pos == "TE" else 0)
    if pos == "RB":
        return {"p": round(p, 1), "c": int(r.carries), "t": int(r.targets), "ry": int(r.rushing_yards), "ey": int(r.receiving_yards), "td": int(r.rushing_tds + r.receiving_tds), "g": int(r.tg)}
    if pos == "TE":
        return {"p": round(p, 1), "t": int(r.targets), "r": int(r.receptions), "y": int(r.receiving_yards), "td": int(r.receiving_tds), "sn": int(round(100 * r.snp)), "g": int(r.tg)}
    return {"p": round(p, 1), "t": int(r.targets), "r": int(r.receptions), "y": int(r.receiving_yards), "td": int(r.receiving_tds), "g": int(r.tg)}


def add_year2(rows, pos):
    q = pd.DataFrame([{"gsis_id": o["id"], "yr": o["yr"]} for o in rows if o.get("id") and o["yr"] + 1 <= CUR])
    for o in rows:
        o.update(y2w=None, u2=None, g2=0, y2t=[])
    if q.empty:
        return
    q["tm2"] = q.gsis_id.map(season_team(q, 1))
    q = q.dropna(subset=["tm2"])
    L = usage_cols(team_games(q, 1, "tm2"), pos)
    L = L[L.tg <= 4]
    by = {k: v for k, v in L.groupby("gsis_id")}
    cut = Y2[pos]
    for o in rows:
        g = by.get(o.get("id"))
        if g is None or o["yr"] + 1 > CUR:
            continue
        c = g[g.done & g.cnt]
        o["y2w"] = [y2_cell(r, pos) for r in g.itertuples()]
        o["g2"] = int(len(c))
        o["u2"] = round(float(c.u.mean()), 2) if len(c) else None
        u1, u2 = o.get("u") or 0.0, o["u2"]   # no early rookie games counts as 0 usage
        if u2 is None or o["g2"] < 2:
            continue
        t = []
        if u1 < cut["lo"] and u2 >= cut["hi"]:
            t.append("jump")
        elif u1 < cut["lo"] and u2 >= cut["rise"]:
            t.append("rise")
        if u1 >= cut["hi"] and u2 < cut["hi"]:
            t.append("fade")
        o["y2t"] = t


# ---------------------------------------------------------------- RB / TE full rebuild
def build_rb_te(pos):
    uni = universe(pos)
    if pos == "TE":
        uni = uni[uni.name != "Taysom Hill"]  # converted QB; his points aren't TE production
    uni["tm"] = uni.gsis_id.map(season_team(uni)).fillna(uni.team)
    uni = uni.dropna(subset=["tm"])
    L = usage_cols(team_games(uni), pos)
    if pos == "RB":
        rbw = wk[wk.position == "RB"]
        tt = rbw.assign(o=rbw.carries + 2.5 * rbw.targets).groupby(["season", "week", "team"]).o.sum().rename("team_o").reset_index()
        L = L.merge(tt, on=["season", "week", "team"], how="left")
    G = {k: v for k, v in L.groupby("gsis_id")}

    def summ(rows_):
        c = rows_[rows_.done & rows_.cnt]
        return (round(float(c.u.mean()), 2), int(len(c))) if len(c) else (None, 0)

    def bfs(rows_):
        c = rows_[rows_.done & rows_.cnt]
        t = c.team_o.sum()
        return round(float(c.u.sum() / t), 3) if len(c) and t > 0 else None

    def cellof(r):
        return y2_cell(r, pos)

    out = []
    for p in uni.itertuples():
        g = G.get(p.gsis_id)
        if g is None or len(g[g.tg <= 4]) < 4:
            continue
        u4, g4 = summ(g[g.tg <= 4])
        u8, g8 = summ(g[g.tg <= 8])
        cg = g[g.done & g.cnt].tail(4)
        td4, td8 = int(g[g.tg <= 4].done.sum()), int(g[g.tg <= 8].done.sum())
        drafted = not pd.isna(p.round)
        if pos == "RB":
            t4 = int(g[(g.tg <= 4) & g.done & ((g.carries + g.targets) > 0)].shape[0])
            t8 = int(g[(g.tg <= 8) & g.done & ((g.carries + g.targets) > 0)].shape[0])
            uL, gL = summ(cg)
            best = BEST_PPR.get(p.gsis_id)
            tier = "green" if best and best >= 15 else "yellow" if best and best >= 12 else ("tbd" if p.yr >= LAST_DONE else "red")
            n12 = int(((ss.player_id == p.gsis_id) & (ss.ppr >= 12)).sum())
            n2 = int(((ss.player_id == p.gsis_id) & (ss.ppr >= 15)).sum())
        else:
            t4, t8 = g4, g8
            uL, gL = summ(g)  # season to date
            best = BEST_TEP.get(p.gsis_id)
            tier = ("g17" if best >= 17 else "g14" if best >= 14 else "g12") if best and best >= 12 else ("tbd" if p.yr >= LAST_DONE else "red")
            n12 = int(((ss.player_id == p.gsis_id) & (ss.tep >= 12)).sum())
            n2 = int(bool(best and best >= 17))
        tags = ["missed"] if drafted and td4 >= 4 and t4 <= 2 else []
        tags8 = ["missed"] if drafted and td8 >= 7 and t8 <= 4 else []
        o = dict(n=p.name, id=p.gsis_id, yr=int(p.yr), rd=int(p.round) if drafted else None,
                 pk=None if pd.isna(p.pick) else int(p.pick), tm=p.tm if isinstance(p.tm, str) else "",
                 tier=tier, best=None if best is None else round(float(best), 1), n12=n12,
                 w=[cellof(r) for r in g[g.tg <= 4].itertuples()], w8=[cellof(r) for r in g[g.tg <= 8].itertuples()],
                 wL=[cellof(r) for r in cg.itertuples()], u=u4, g=g4, u8=u8, g8=g8, uL=uL, gL=gL, td8=td8,
                 tags=tags, tags8=tags8)
        if pos == "RB":
            o.update(n15=n2, bf=bfs(g[g.tg <= 4]), bf8=bfs(g[g.tg <= 8]), bfL=bfs(cg))
        else:
            o.update(n14=n2)
        out.append(o)
    comps(out, (("c4", "u", "g"), ("c8", "u8", "g8"), ("cL", "uL", "gL")))
    add_year2(out, pos)
    return out


# ---------------------------------------------------------------- WR update
def wr_update(rows):
    by_key = {(o.get("id"), o["yr"]) for o in rows}
    uni = universe("WR")
    new = uni[(uni.yr >= CUR) & ~uni.apply(lambda r: (r.gsis_id, r.yr) in by_key, axis=1)]
    for p in new.itertuples():
        if pd.isna(p.round):
            continue  # undrafted WRs are only added by the full build
        rows.append(dict(n=p.name, id=p.gsis_id, yr=int(p.yr), rd=int(p.round), pk=int(p.pick), tm=p.team if isinstance(p.team, str) else "",
                         tier="tbd", best=None, n12=None, n14=None, u=0.0, b=None, g=0, sb=0, tags=[], w=[],
                         w8=[], u8=0.0, g8=0, td8=0, tags8=[]))
    recent = [o for o in rows if o["yr"] >= CUR - 1 and o.get("id")]
    if recent:
        q = pd.DataFrame([{"gsis_id": o["id"], "yr": o["yr"]} for o in recent])
        q["tm"] = q.gsis_id.map(season_team(q))
        q["tm"] = q.tm.fillna(q.gsis_id.map({o["id"]: o["tm"] for o in recent}))
        L = usage_cols(team_games(q.dropna(subset=["tm"])), "WR")
        G = {k: v for k, v in L.groupby("gsis_id")}
        snap_set = set(zip(snaps.gsis_id, snaps.season, snaps.week))
        for o in recent:
            g = G.get(o["id"])
            if g is None:
                continue
            o["tm"] = g.team.iloc[0]
            # NFL-week cells (weeks 1-8, byes shown), as on the original tab
            wks = gm[((gm.home_team == o["tm"]) | (gm.away_team == o["tm"])) & (gm.season == o["yr"])].set_index("week")
            ln = {r.week: r for r in g.itertuples()}
            cells = []
            for w in range(1, 9):
                if w not in wks.index:
                    cells.append({"s": "BYE"}); continue
                if pd.isna(wks.loc[w, "home_score"]):
                    cells.append({"s": "TBD"}); continue
                r = ln.get(w)
                if r is None or not (r.snap or r.line):  # original tab: any stat line or offensive snap
                    cells.append({"s": "DNP"}); continue
                cells.append({"p": round(float(r.fantasy_points_ppr), 1), "t": int(r.targets), "r": int(r.receptions),
                              "y": int(r.receiving_yards), "td": int(r.receiving_tds)})
            o["w"], o["w8"] = cells[:4], cells
            w4 = g[(g.tg <= 4) & g.done & g.cnt]
            o["g"] = int(len(w4))
            o["u"] = round(float(w4.u.mean()), 2) if len(w4) else 0.0
            played8 = [c for c in cells if "p" in c]
            o["g8"] = len(played8)
            o["td8"] = sum(1 for c in cells if c.get("s") not in ("BYE", "TBD"))
            o["u8"] = round(sum(2.2 * c["t"] + c["r"] + .12 * c["y"] + .5 * c["td"] for c in played8) / len(played8), 2) if played8 else 0.0
            ppg4 = round(float(w4.fantasy_points_ppr.mean()), 2) if len(w4) else 0.0   # rounded as in the original build
            ppg8 = round(sum(c["p"] for c in played8) / len(played8), 2) if played8 else 0.0
            drafted = o.get("rd") is not None
            t = []
            if drafted and o["g"] <= 2 and int(g[g.tg <= 4].done.sum()) >= 4:
                t.append("missed")
            if o["g"] >= 2 and o["u"] >= 15 and ppg4 < 10 and ppg4 <= 0.477 * o["u"] - 0.26 - 0.875:
                t.append("buy")
            o["tags"] = t
            t8 = []
            if drafted and o["td8"] >= 7 and o["g8"] <= 4:
                t8.append("missed")
            if o["g8"] >= 4 and o["u8"] >= 15 and ppg8 < 10 and ppg8 <= 0.47 * o["u8"] - 0.146 - 0.64:
                t8.append("buy")
            o["tags8"] = t8
    # tiers: completed seasons can only raise a tier; unhit players become red once two seasons are done
    rank = {"red": 0, "tbd": 0, "yellow": 1, "green": 2}
    for o in rows:
        b = BEST_PPR.get(o.get("id"))
        t = max(rank.get(o["tier"], 0), 2 if b and b >= 14 else 1 if b and b >= 12 else 0)
        if b is not None:
            o["best"] = round(float(b), 1)
        o["tier"] = ["red", "yellow", "green"][t] if t or o["yr"] < LAST_DONE else "tbd"
    comps(rows, (("c4", "u", "g"), ("c8", "u8", "g8")))
    add_year2(rows, "WR")
    return rows


# ---------------------------------------------------------------- write pages
DATA_RE = re.compile(r"const DATA = \[.*?\];\n", re.S)
ASOF = datetime.now(timezone.utc).strftime("%b %-d, %Y")


def read_data(path):
    s = open(path, encoding="utf-8").read()
    m = DATA_RE.search(s)
    return s, json.loads(m.group(0)[len("const DATA = "):-2])


def write_data(path, s, rows, old):
    if json.dumps(rows, sort_keys=True) == json.dumps(old, sort_keys=True):
        print(path, "unchanged")
        return
    s = DATA_RE.sub(lambda _: "const DATA = " + json.dumps(rows, separators=(",", ":"), ensure_ascii=False) + ";\n", s, count=1)
    s = re.sub(r"as of [A-Z][a-z]{2} \d{1,2}, \d{4}", f"as of {ASOF}", s)
    open(path, "w", encoding="utf-8").write(s)


for pos, fname in (("RB", "rookie-rb-tracker.html"), ("TE", "rookie-te-tracker.html"), ("WR", "rookie-wr-tracker.html")):
    path = f"{SITE}/{fname}"
    s, rows = read_data(path)
    old = json.loads(json.dumps(rows))
    rows = wr_update(rows) if pos == "WR" else build_rb_te(pos)
    write_data(path, s, rows, old)
    print(pos, len(rows), "rows;", sum(1 for o in rows if o["y2t"]), "Year 2 tags")
