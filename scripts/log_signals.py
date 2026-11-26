"""Daily signal log: every player the site flags today, plus an unflagged comparison group, with that day's market
prices and model odds.

Point-in-time prices can't be rebuilt later (ktc.json / data/fc/ are overwritten every day), so this keeps a dated
snapshot that a later backtest can join to what the players actually did over the next 6-12 months.

Flags logged, with the site's own rules (index.html):
  WR BUY, Y2 JUMPED, MISSED TIME   signals.json `sig` ('buy', 'jump', 'missed')
  CHEAP / PRICEY                   signalPlayers(): current rookie class, Weeks 1-4 odds rank vs KTC rank at the
                                   position; |rank gap| >= max(3, 20% of the pool) AND a real value gap
                                   (>= max(500, 15% of his KTC))
  SELL NOW / SELL WINDOW           sellInfo(): position, age and last season's PPG against data/age-curves.json
Market: KTC superflex (12-team, no TE premium) and 1QB, FantasyCalc superflex PPR (data/fc/fc-sf-ppr1-none.json).
The hub ranks on each league's own KTC values (TE premium, league size), so a flag near the cutoff can differ by
league; this log is the plain superflex baseline.

Writes data/signal-log/YYYY-MM-DD.json (UTC date; a rerun the same day overwrites). Never fails the workflow.
Usage: python3 scripts/log_signals.py [repo root]
"""
import datetime, json, os, re, sys, unicodedata

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
RULES = "v2 (2026-11-26): + FantasyCalc check on CHEAP/PRICEY"
# Log layout: 1 = flagged players only; 2 = + an unflagged comparison group (cohort "rookie" / "veteran", flags [])
LOG_SCHEMA = 2


def key(name):   # same matching key as check_names.py / the hub's value hand-off: letters only, suffixes dropped
    s = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b\.?", "", s)
    return re.sub(r"[^a-z]", "", s)


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return json.load(f)


def main():
    sig = load("signals.json")
    ktc = load("ktc.json")
    fc = load("data/fc/fc-sf-ppr1-none.json")
    ppg = load("ppg.json").get("players", {})
    sell = load("data/age-curves.json")["sell"]["table"]

    K = {}
    for p in ktc.get("players", []):
        K[f"{p.get('position')}|{key(p.get('playerName'))}"] = {
            "name": p.get("playerName"), "pos": p.get("position"), "team": p.get("team"), "age": p.get("age"),
            "sid": p.get("sleeperId"),
            "ktc_sf": (p.get("superflexValues") or {}).get("value"), "ktc_1qb": (p.get("oneQBValues") or {}).get("value"),
        }
    ci = {x: i for i, x in enumerate(fc["fields"])}
    F = {f"{r[ci['pos']]}|{key(r[ci['name']])}": r for r in fc["players"]}

    rows = {}   # pos|key -> logged row

    def row(pos, name):
        k = f"{pos}|{key(name)}"
        if k not in rows:
            m, f = K.get(k, {}), F.get(k)
            rows[k] = {
                "name": m.get("name") or name, "pos": pos, "team": m.get("team") or (f[ci["team"]] if f else None),
                "sid": m.get("sid") or (f[ci["sleeperId"]] if f else None),
                "age": m.get("age") or (f[ci["age"]] if f else None),
                "ktc_sf": m.get("ktc_sf"), "ktc_1qb": m.get("ktc_1qb"),
                "fc_sf": f[ci["val"]] if f else None, "fc_redraft": f[ci["rval"]] if f else None,
                "flags": [],
            }
        return rows[k]

    # ---- rookie signals (signals.json) ----
    season = sig.get("season")
    players = sig.get("players", [])
    names = {"buy": "WR BUY", "jump": "Y2 JUMPED", "missed": "MISSED TIME"}
    for s in players:
        tags = [names[t] for t in s.get("sig", []) if t in names]
        if tags:
            r = row(s["pos"], s["n"])
            r["flags"] += tags

    # CHEAP / PRICEY: the hub's signalPlayers() rule on KTC superflex
    # FantasyCalc on the KTC scale (same rank, KTC's value at that rank), so the 500-point / 15% gap reads the same
    kv_all = sorted((v["ktc_sf"] or 0 for v in K.values()), reverse=True)
    fv_all = sorted((r[ci["val"]] or 0 for r in fc["players"]), reverse=True)
    def fc_on_ktc(v):
        i = sum(1 for x in fv_all if x > v)
        return kv_all[min(len(kv_all) - 1, int(i * len(kv_all) / max(1, len(fv_all))))]
    fc_flags = {}
    for pos in ("WR", "RB", "TE"):
        fpool = []
        for s in players:
            if s["pos"] != pos or s.get("yr") != season or (s.get("hp") or {}).get("4") is None:
                continue
            f = F.get(f"{pos}|{key(s['n'])}")
            if (K.get(f"{pos}|{key(s['n'])}") or {}).get("ktc_sf") and f and f[ci["val"]]:
                fpool.append((s, fc_on_ktc(f[ci["val"]])))
        if len(fpool) < 6:
            continue
        th = max(3, round(len(fpool) * 0.2))
        by_f = sorted(fpool, key=lambda x: -x[1])
        for i, (s, fv) in enumerate(sorted(fpool, key=lambda x: (-x[0]["hp"]["4"], -x[1]))):
            fr = next(j for j, x in enumerate(by_f) if x[0] is s) + 1
            gap = fr - (i + 1)
            big = abs(fv - by_f[i][1]) >= max(500, 0.15 * fv)
            fc_flags[s["n"]] = ("CHEAP" if gap >= th else "PRICEY" if gap <= -th else "") if big else ""
    for pos in ("WR", "RB", "TE"):
        pool = []
        for s in players:
            if s["pos"] != pos or s.get("yr") != season or (s.get("hp") or {}).get("4") is None:
                continue
            kv = (K.get(f"{pos}|{key(s['n'])}") or {}).get("ktc_sf") or 0
            if kv > 0:
                pool.append((s, kv))
        n = len(pool)
        if n < 6:
            continue
        th = max(3, round(n * 0.2))
        by_k = sorted(pool, key=lambda x: -x[1])
        by_odds = sorted(pool, key=lambda x: (-x[0]["hp"]["4"], -x[1]))
        for i, (s, kv) in enumerate(by_odds):
            kr = next(j for j, x in enumerate(by_k) if x[0] is s) + 1
            gap = kr - (i + 1)
            big = abs(kv - by_k[i][1]) >= max(500, 0.15 * kv)
            flag = ("CHEAP" if gap >= th else "PRICEY" if gap <= -th else None) if big else None
            # every pool member is logged (flagged or not), so a later test can compare flagged players with
            # unflagged peers priced on the same day
            r = row(pos, s["n"])
            if flag:
                r["flags"].append(flag)
            r["mv"] = {"odds_rank": i + 1, "ktc_rank": kr, "pool": n, "fc_flag": fc_flags.get(s["n"], "")}

    # comparison group: every rookie on the rookie tabs this season and last (the WR BUY / JUMP / MISSED classes)
    for s in players:
        row(s["pos"], s["n"])

    # odds and draft info for every logged rookie
    by_key = {f"{s['pos']}|{key(s['n'])}": s for s in players}
    for k, r in rows.items():
        s = by_key.get(k)
        if s:
            r.update({"class": s.get("yr"), "rd": s.get("rd"), "pk": s.get("pk"), "nfl": s.get("tm"),
                      "hp": s.get("hp"), "he": s.get("he"), "usage4": s.get("u"), "usage8": s.get("u8")})

    # ---- veteran sells (sellInfo) ----
    for k, m in K.items():
        pos, age = m["pos"], m.get("age")
        p = ppg.get(re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "",
                    re.sub(r"['’.]", "", unicodedata.normalize("NFKD", m["name"] or "").encode("ascii", "ignore").decode().lower())))).strip())
        cfg = sell.get(pos)
        if not p or not cfg or not age or p.get("pos") != pos or p.get("ppg", 0) < 12:
            continue
        i = len([a for a in cfg["ages"] if age >= a])
        kk, nn = (cfg["top"] if p["ppg"] >= cfg["med"] else cfg["bot"])[i]
        flag = None
        if pos == "RB":
            flag = "SELL NOW" if age >= 28 else "SELL WINDOW" if age >= 27 else None
        elif pos == "WR":
            flag = "SELL NOW" if age >= 31 else "SELL WINDOW" if (age >= 29 and p["ppg"] < cfg["med"]) else None
        elif pos == "TE" and p["ppg"] < cfg["med"]:
            flag = "SELL NOW" if age >= 32 else "SELL WINDOW" if age >= 31 else None
        # every 12+ PPG veteran the sell table covers is logged, flagged or not (the veteran comparison group)
        r = row(pos, m["name"])
        if flag:
            r["flags"].append(flag)
        r["sell"] = {"repeat12_odds": round(100 * kk / nn), "k": kk, "n": nn, "ppg": p["ppg"], "season": p.get("s"), "gp": p.get("gp")}

    for k, r in rows.items():   # rookie = on the rookie tabs (this class or last); veteran = the sell table's group
        r["cohort"] = "rookie" if k in by_key else "veteran"

    out = {
        "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
        "rules": RULES,
        "log_schema": LOG_SCHEMA,
        "sources": {"ktc_updated": ktc.get("updatedAt"), "fc_updated": fc.get("updated"), "signals_season": season},
        "count": len(rows),
        "flagged": sum(1 for r in rows.values() if r["flags"]),
        "players": sorted(rows.values(), key=lambda r: (r["pos"], -(r.get("ktc_sf") or 0))),
    }
    os.makedirs(os.path.join(ROOT, "data/signal-log"), exist_ok=True)
    path = os.path.join(ROOT, "data/signal-log", f"{out['date']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))
    tally = {}
    for r in rows.values():
        for t in r["flags"]:
            tally[t] = tally.get(t, 0) + 1
    print(f"signal log {out['date']}: {len(rows)} players · " + " · ".join(f"{k} {v}" for k, v in sorted(tally.items())))
    nomkt = [r["name"] for r in rows.values() if r["ktc_sf"] is None and r["fc_sf"] is None]
    if nomkt:
        print(f"  no market value found for {len(nomkt)} (mostly deep rookies): {', '.join(nomkt[:12])}{' …' if len(nomkt) > 12 else ''}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:   # a log, never a blocker
        print("signal log skipped:", e)
