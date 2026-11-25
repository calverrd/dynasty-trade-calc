"""Pre-draft prospect model v1: dataset + validation report.

Pool: every WR / RB / TE drafted or invited to the Combine, draft classes 2015-2026.
Outcomes (settled classes 2015-2024): Devon's Hit Rates sheet tiers (scripts/refresh/sheet_tiers.json),
falling back to nflverse: best 8+ game season PPG (full PPR; TE + 0.5 / catch).
  Safe   = 12+ PPG (all three positions)
  Upside = 14+ WR, 15+ RB, 17+ TE
College data: SportsDataverse espn_cfb_usage_players / espn_cfb_usage_teams (seasons before the draft).
Validation: leave-one-draft-class-out logistic regression, AUC on pooled out-of-fold predictions,
paired bootstrap (3,000) vs both anchors (log draft pick, log class rank), 5-bin calibration + Brier.
Writes data/predraft_dataset.csv, data/predraft_report.md, data/predraft_models.json.
"""
import io, json, math, os, re, sys, unicodedata, urllib.request
from collections import defaultdict
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss

OUT = "data"
os.makedirs(OUT, exist_ok=True)
REPORT = []
def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    REPORT.append(s)

NFLV = "https://github.com/nflverse/nflverse-data/releases/download"
SDV = "https://github.com/sportsdataverse/sportsdataverse-data/releases/download"
FIRST, LAST_SETTLED, LAST = 2015, 2024, 2026
POSS = ("WR", "RB", "TE")
UP = {"WR": 14, "RB": 15, "TE": 17}


def get(url, kind="csv"):
    data = urllib.request.urlopen(url, timeout=180).read()
    if kind == "parquet":
        return pd.read_parquet(io.BytesIO(data))
    return pd.read_csv(io.BytesIO(data), low_memory=False)


def norm(x):
    x = unicodedata.normalize("NFKD", str(x or "")).encode("ascii", "ignore").decode().lower()
    x = re.sub(r"['’.]", "", x)
    x = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", x)
    return re.sub(r"[^a-z0-9]+", " ", x).strip()


def school_key(s):
    s = norm(s).replace(" st", " state") if s else ""
    s = re.sub(r"\b(fl|oh)\b", "", s)
    s = {"ole miss": "mississippi", "pitt": "pittsburgh", "lsu": "louisiana state", "smu": "southern methodist",
         "tcu": "texas christian", "ucf": "central florida", "usc": "southern california", "byu": "brigham young",
         "uab": "alabama birmingham", "utsa": "texas san antonio", "utep": "texas el paso", "unlv": "nevada las vegas"}.get(s.strip(), s)
    return s.strip()


# ------------------------------------------------------------------ pool: drafted + combine
say("# Pre-draft prospect model v1: build + validation report\n")
dp = get(f"{NFLV}/draft_picks/draft_picks.csv")
dp = dp[dp.season.between(FIRST, LAST) & dp.position.isin(POSS)]
cb = get(f"{NFLV}/combine/combine.csv")
cb = cb[cb.draft_year.fillna(cb.season).between(FIRST, LAST) & cb.pos.isin(POSS)].copy()
cb["yr"] = cb.draft_year.fillna(cb.season).astype(int)
pl = get(f"{NFLV}/players/players.csv")
birth = dict(zip(pl.gsis_id, pl.birth_date))
pfr_birth = {}
if "pfr_id" in pl.columns:
    pfr_birth = dict(zip(pl.pfr_id, pl.birth_date))

rows = {}
for r in dp.itertuples():
    k = r.pfr_player_id if isinstance(r.pfr_player_id, str) else f"{norm(r.pfr_player_name)}|{r.season}"
    rows[k] = dict(name=r.pfr_player_name, pos=r.position, yr=int(r.season), pick=int(r.pick), rd=int(r.round),
                   school=r.college, gsis=r.gsis_id, pfr=r.pfr_player_id if isinstance(r.pfr_player_id, str) else None,
                   birth=birth.get(r.gsis_id) or pfr_birth.get(r.pfr_player_id))
for r in cb.itertuples():
    k = r.pfr_id if isinstance(r.pfr_id, str) and r.pfr_id in rows else (r.pfr_id if isinstance(r.pfr_id, str) else f"{norm(r.player_name)}|{r.yr}")
    if k not in rows:
        # try name + year match with a drafted row
        hit = [kk for kk, v in rows.items() if v["yr"] == r.yr and norm(v["name"]) == norm(r.player_name) and v["pos"] == r.pos]
        k = hit[0] if hit else k
    o = rows.setdefault(k, dict(name=r.player_name, pos=r.pos, yr=int(r.yr), pick=None, rd=None, school=r.school,
                                gsis=None, pfr=r.pfr_id if isinstance(r.pfr_id, str) else None, birth=pfr_birth.get(r.pfr_id)))
    ht = r.ht
    if isinstance(ht, str) and "-" in ht:
        a, b = ht.split("-")[:2]
        ht = int(a) * 12 + int(b)
    o.update(ht=float(ht) if ht == ht and ht is not None else None, wt=r.wt, forty=r.forty, combine=1)
df = pd.DataFrame(rows.values())
for c in ("ht", "wt", "forty", "combine"):
    if c not in df:
        df[c] = np.nan
df["combine"] = df["combine"].fillna(0)
say(f"Pool: {len(df)} players ({(df.pick.notna()).sum()} drafted, {int(df["combine"].sum())} at the Combine), classes {FIRST}-{LAST}")
say(df.groupby(["pos"]).size().to_string())

# ------------------------------------------------------------------ outcomes: sheet tiers, nflverse fallback
sheet = json.load(open("scripts/refresh/sheet_tiers.json"))
weeks = []
for y in range(FIRST, LAST_SETTLED + 2):
    try:
        w = get(f"{NFLV}/stats_player/stats_player_week_{y}.csv")
        weeks.append(w[w.season_type == "REG"][["player_id", "player_display_name", "position", "season", "week", "fantasy_points_ppr", "receptions"]])
    except Exception as e:
        say(f"stats {y} failed: {e}")
wk = pd.concat(weeks)
wk["pts"] = np.where(wk.position == "TE", wk.fantasy_points_ppr + 0.5 * wk.receptions.fillna(0), wk.fantasy_points_ppr)
ss = wk.groupby(["player_id", "season"]).agg(gp=("week", "count"), pts=("pts", "sum")).reset_index()
ss = ss[ss.gp >= 8]
ss["ppg"] = ss.pts / ss.gp
best = ss.groupby("player_id").ppg.max().to_dict()
safe, up, src = [], [], []
for r in df.itertuples():
    if r.yr > LAST_SETTLED:
        safe.append(np.nan); up.append(np.nan); src.append("tbd"); continue
    h = sheet.get(f"{r.pos}|{norm(r.name)}|{r.yr}")
    if h:
        safe.append(1 if h[0] else 0); up.append(1 if h[2] else 0); src.append("sheet")
    else:
        b = best.get(r.gsis, 0) if isinstance(r.gsis, str) else 0
        safe.append(1 if b >= 12 else 0); up.append(1 if b >= UP[r.pos] else 0); src.append("nflverse")
df["safe"], df["up"], df["outcome_src"] = safe, up, src
st = df[df.yr <= LAST_SETTLED]
say(f"\nOutcomes 2015-{LAST_SETTLED}: {len(st)} players; source: {st.outcome_src.value_counts().to_dict()}; "
    f"safe rate {st.safe.mean():.1%}, upside rate {st.up.mean():.1%}")

# ------------------------------------------------------------------ college stats
pc, tc = [], []
for y in range(FIRST - 5, LAST):
    try:
        p = get(f"{SDV}/espn_cfb_usage_players/usage_players_{y}.parquet", "parquet")
        pc.append(p)
    except Exception as e:
        say(f"college players {y}: {e}")
cp = pd.concat(pc, ignore_index=True)
cp = cp[cp.position_group.isin(["WR", "RB", "TE", "QB", "ATH", "FB"]) | cp.position_group.isna()]
cp["nk"] = cp.player_name.map(norm)
cp["sk"] = cp.pos_team.map(lambda s: norm(s))
# team totals from the player file itself
tot = cp.groupby(["season", "pos_team_id"]).agg(t_rec=("receiving_yards", "sum"), t_rush=("rushes", "sum"), t_rushyd=("rush_yards", "sum")).reset_index()
cp = cp.merge(tot, on=["season", "pos_team_id"], how="left")
say(f"\nCollege rows: {len(cp)} player-seasons {cp.season.min()}-{cp.season.max()}; columns ok: "
    f"{all(c in cp.columns for c in ['targets','receptions','receiving_yards','rushes','rush_yards','team_targets','games'])}")
by_name = defaultdict(list)
for r in cp.itertuples():
    by_name[r.nk].append(r)


def college_rows(o):
    cands = [r for r in by_name.get(norm(o["name"]), []) if o["yr"] - 6 <= r.season <= o["yr"] - 1]
    if not cands:
        return [], "none"
    teams = {r.pos_team_id for r in cands}
    if len(teams) == 1:
        return cands, "name"
    sk = school_key(o.get("school") or "")
    if sk:
        m = [r for r in cands if sk and (sk in school_key(r.pos_team) or school_key(r.pos_team).startswith(sk.split(" ")[0]))]
        if m:
            # keep the matched school plus any transfer seasons that follow the same name in adjacent years
            return [r for r in cands if r.season >= min(x.season for x in m) - 3], "school"
    # ambiguous: take the team with the most recent season
    last = max(cands, key=lambda r: r.season).pos_team_id
    return [r for r in cands if r.pos_team_id == last], "recent"


def age_at(birth, season):
    try:
        b = pd.Timestamp(birth)
        return (pd.Timestamp(f"{season}-09-01") - b).days / 365.25
    except Exception:
        return None


feat = []
match_kind = []
for o in df.to_dict("records"):
    cr, how = college_rows(o)
    match_kind.append(how)
    f = {}
    seasons = [r for r in cr if (r.games or 0) >= 6]
    if seasons:
        def yshare(r): return (r.receiving_yards or 0) / r.t_rec if r.t_rec else 0
        def ypta(r): return (r.receiving_yards or 0) / r.team_targets if r.team_targets else 0
        def rshare(r): return (r.rushes or 0) / r.t_rush if r.t_rush else 0
        def tshare(r): return r.target_share or 0
        def scrim(r): return ((r.receiving_yards or 0) + (r.rush_yards or 0)) / max(1, r.games)
        f["best_yard_share"] = max(map(yshare, seasons))
        f["best_ypta"] = max(map(ypta, seasons))
        f["best_target_share"] = max(map(tshare, seasons))
        f["best_rush_share"] = max(map(rshare, seasons))
        f["best_scrim_pg"] = max(map(scrim, seasons))
        last = max(seasons, key=lambda r: r.season)
        f["final_yard_share"] = yshare(last)
        f["final_ypta"] = ypta(last)
        f["college_seasons"] = len({r.season for r in seasons})
        # breakout age: age (Sep 1) of the first season with a 20%+ share of team receiving yards (RB: 15% of carries or yards)
        ages = []
        for r in sorted(seasons, key=lambda r: r.season):
            hit = yshare(r) >= (0.15 if o["pos"] == "TE" else 0.20) if o["pos"] != "RB" else (rshare(r) >= 0.30 or yshare(r) >= 0.10)
            if hit:
                a = age_at(o.get("birth"), r.season)
                ages.append(a if a else 20.5 + (r.season - (o["yr"] - 4)))
                break
        f["breakout_age"] = ages[0] if ages else 24.0
        f["college_rush_capped"] = min(250.0, sum((r.rush_yards or 0) for r in seasons)) if o["pos"] == "WR" else None
    feat.append(f)
F = pd.DataFrame(feat)
df = pd.concat([df.reset_index(drop=True), F], axis=1)
df["match"] = match_kind
drafted_fbs = df[(df.pick.notna())]
say(f"College match rate: {(df.match != 'none').mean():.1%} of pool, {(drafted_fbs.match != 'none').mean():.1%} of drafted players "
    f"(by name only {(df.match=='name').mean():.0%}, school-disambiguated {(df.match=='school').mean():.0%}, most-recent-team {(df.match=='recent').mean():.0%})")
for pos in POSS:
    x = df[(df.pos == pos) & df.pick.notna()]
    say(f"  {pos}: drafted matched {(x.match != 'none').mean():.1%} (n={len(x)}); 6+ game season found {x.best_yard_share.notna().mean():.1%}")

# ------------------------------------------------------------------ derived features
df["draft_age"] = [age_at(b, y) for b, y in zip(df.birth, df.yr)]
df["draft_age"] = df.draft_age - (9 - 4.8) / 12  # Sep 1 -> late April
df["log_pick"] = np.log(df.pick.fillna(262))
df["class_rank"] = np.nan
for (pos, yr), g in df.groupby(["pos", "yr"]):
    dr = g[g.pick.notna()].sort_values("pick")
    df.loc[dr.index, "class_rank"] = np.arange(1, len(dr) + 1)
    df.loc[g[g.pick.isna()].index, "class_rank"] = len(dr) + 6
df["log_rank"] = np.log(df.class_rank + 2)
df["speed_score"] = np.where(df.forty > 0, df.wt * 200 / df.forty.pow(4), np.nan)
df["bmi"] = np.where((df.ht > 0) & (df.wt > 0), df.wt / df.ht.pow(2) * 703, np.nan)
df["no_forty"] = df.forty.isna().astype(int)
df.to_csv(f"{OUT}/predraft_dataset.csv", index=False)
say(f"\nWrote {OUT}/predraft_dataset.csv ({len(df)} rows)")

# ------------------------------------------------------------------ validation
CANDS = {
    "WR": ["best_yard_share", "best_ypta", "final_ypta", "best_target_share", "breakout_age", "draft_age", "college_rush_capped", "wt", "speed_score"],
    "RB": ["best_yard_share", "best_target_share", "best_rush_share", "best_scrim_pg", "draft_age", "wt", "speed_score", "breakout_age"],
    "TE": ["best_yard_share", "best_ypta", "breakout_age", "draft_age", "wt", "speed_score", "ht"],
}
RNG = np.random.default_rng(7)


def prep(x, cols):
    X = x[cols].astype(float).copy()
    for c in cols:
        X[c] = X[c].fillna(X[c].median())
    return X.values


def loso(x, cols, y):
    p = np.zeros(len(x))
    yrs = x.yr.values
    for yr in sorted(set(yrs)):
        tr = yrs != yr
        X = prep(x, cols)
        mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-9
        if len(set(x[y].values[tr])) < 2:
            p[~tr] = x[y].values[tr].mean(); continue
        m = LogisticRegression(C=1.0, max_iter=2000).fit((X[tr] - mu) / sd, x[y].values[tr])
        p[~tr] = m.predict_proba((X[~tr] - mu) / sd)[:, 1]
    return p


def boot(y, pa, pb, n=3000):
    ds = []
    for _ in range(n):
        i = RNG.integers(0, len(y), len(y))
        if y[i].min() == y[i].max():
            continue
        ds.append(roc_auc_score(y[i], pb[i]) - roc_auc_score(y[i], pa[i]))
    lo, hi = np.percentile(ds, [2.5, 97.5])
    return float(np.mean(ds)), float(lo), float(hi)


MODELS = {}
for pos in POSS:
    for pool_name, sel in (("Drafted + Combine", lambda d: d), ("Rounds 1-3", lambda d: d[d.rd <= 3])):
        x = sel(df[(df.pos == pos) & (df.yr <= LAST_SETTLED)]).reset_index(drop=True)
        if len(x) < 40:
            continue
        say(f"\n## {pos} · {pool_name} (n={len(x)}; safe {x.safe.mean():.0%}, upside {x.up.mean():.0%})")
        for tgt in ("safe", "up"):
            y = x[tgt].values.astype(int)
            if y.sum() < 8:
                say(f"- {tgt}: too few hits ({y.sum()})"); continue
            base = {}
            for nm, cols in (("log_pick", ["log_pick"]), ("log_rank", ["log_rank"]), ("pick+rank", ["log_pick", "log_rank"])):
                base[nm] = loso(x, cols, tgt)
            aucs = {k: roc_auc_score(y, v) for k, v in base.items()}
            anchor = max(("log_pick", "log_rank"), key=lambda k: aucs[k])
            say(f"- **{tgt}** anchors: log_pick {aucs['log_pick']:.3f} · log_rank {aucs['log_rank']:.3f} · both {aucs['pick+rank']:.3f} → anchor = {anchor}")
            kept = []
            cur = base[anchor]
            for c in CANDS[pos]:
                if x[c].notna().mean() < 0.5:
                    say(f"  - {c}: skipped ({x[c].notna().mean():.0%} coverage)"); continue
                p = loso(x, [anchor] + kept + [c], tgt)
                d, lo, hi = boot(y, cur, p)
                ok = lo > 0
                say(f"  - +{c}: AUC {roc_auc_score(y, p):.3f} (Δ {d:+.3f} [{lo:+.3f}, {hi:+.3f}]) {'KEEP' if ok else 'drop'}")
                if ok:
                    kept.append(c); cur = p
            final_cols = [anchor] + kept
            pf = cur
            d_pick = boot(y, base["log_pick"], pf); d_rank = boot(y, base["log_rank"], pf)
            say(f"  - FINAL {final_cols}: AUC {roc_auc_score(y, pf):.3f}; vs log_pick Δ {d_pick[0]:+.3f} [{d_pick[1]:+.3f}, {d_pick[2]:+.3f}]; "
                f"vs log_rank Δ {d_rank[0]:+.3f} [{d_rank[1]:+.3f}, {d_rank[2]:+.3f}]; Brier {brier_score_loss(y, pf):.3f} (base {brier_score_loss(y, np.full(len(y), y.mean())):.3f})")
            cal = []
            for lo_, hi_ in ((0, .15), (.15, .35), (.35, .6), (.6, .8), (.8, 1.01)):
                m = (pf >= lo_) & (pf < hi_)
                if m.sum():
                    cal.append(f"{int(lo_*100)}-{int(min(hi_,1)*100)}%: {pf[m].mean():.0%} pred / {y[m].mean():.0%} actual (n={m.sum()})")
            say("  - calibration: " + " · ".join(cal))
            if pool_name == "Drafted + Combine":
                X = prep(x, final_cols)
                mu, sd = X.mean(0), X.std(0) + 1e-9
                m = LogisticRegression(C=1.0, max_iter=2000).fit((X - mu) / sd, y)
                med = {c: float(x[c].astype(float).median()) for c in final_cols}
                MODELS[f"{pos}|{tgt}"] = dict(cols=final_cols, mu=mu.tolist(), sd=sd.tolist(), coef=m.coef_[0].tolist(),
                                              intercept=float(m.intercept_[0]), median=med, auc=float(roc_auc_score(y, pf)), n=int(len(x)))
json.dump(MODELS, open(f"{OUT}/predraft_models.json", "w"), indent=1)
open(f"{OUT}/predraft_report.md", "w").write("\n".join(REPORT) + "\n")
say("\nDone.")
