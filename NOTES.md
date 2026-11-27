# NOTES — read this first

Single source of truth for every chat that works on this repo. **Read it before changing anything, and update it when you finish.**
Last updated: Nov 25, 2026 (afternoon).

> This repo is **public**. Keep league strategy, trade plans and notes about other managers out of it. Those live in the owner's private doc.

---

## 0. Hard rules (learned the hard way)

1. **Work from the live files.** Several chats push to this repo, often on the same day. Before editing, get the current version from GitHub (see section 1), check `git log` / the commit history for recent work, and edit *that*.
   - Nov 25: a chat uploaded a stale `index.html` and workflow and wiped two days of features. It was restored with a 3-way merge.
2. **Upload only the files you changed**, and before pushing, diff them against live `main`. The diff should contain only your change.
3. After pushing **any rookie page**, run the `rookie-refresh` workflow so its embedded `DATA` is current again.
4. After pushing, confirm on the live site and check the browser console for errors.
5. Update this file (sections 3–8) in the same push when you add a feature, file or workflow.

## 1. How to read and push

- **Repo:** `calverrd/dynasty-trade-calc`
- **Live site:** https://calverrd.github.io/dynasty-trade-calc/ (GitHub Pages; deploys about 1–2 minutes after a push)
- **Reading live files**, by session type:
  - Some sessions can reach GitHub from the shell. Test with `git ls-remote https://github.com/calverrd/dynasty-trade-calc`. If it works, `git clone` and `git diff origin/main`.
  - If the shell has no network, fetch `raw.githubusercontent.com/calverrd/dynasty-trade-calc/main/<file>` from a github.com tab with Claude in Chrome's javascript tool.
- **Pushing** (no git credentials in the sandbox), through Claude in Chrome on GitHub's upload page:
  1. Go to `github.com/calverrd/dynasty-trade-calc/upload/main[/subfolder]`. Use `/scripts` and `/.github/workflows` for files in those folders; each folder is a separate commit.
  2. Find the file input, then use `file_upload`. Only paths inside the session's working folder are allowed, not `/tmp`.
  3. Type a commit message and **click** "Commit changes". Pressing Enter doesn't submit.
- **Running a workflow:** open Actions, pick the workflow, click "Run workflow" (sometimes it takes two clicks), then the green Run button.
- **Chrome:** it disconnects when the owner is on his phone. Stage the files and ask him to come back to the computer. Two browsers may be connected; use whichever `list_connected_browsers` shows.

## 2. Leagues (both on Sleeper)

| League | ID | Format | Notes |
|---|---|---|---|
| Planet of the DynastyIM Apes | 1334642025076621312 | 12 teams, superflex, TE +0.5/rec; 6-team playoffs (2 byes, re-seeded), one-week rounds, no trade deadline | Default league in `index.html`. **Rookie draft order: lowest Max PF first** (owner, Nov 25; `draftOrder: 'maxpf'`). |
| Dirty Double Dozen | 1312492943805779968 | 24 teams, 1 QB, TE +0.5/rec; starts QB, RB, 2 WR, TE, 2 FLEX; 6 bench + 3 taxi, no IR | Valued as **superflex**: 24 starting QBs is the same QB demand as a 12-team superflex league. Picks are mapped onto the 12-team curve by overall pick number. Two 12-team divisions with promotion/relegation (Sleeper division 2 = "Top Division", 1 = "Bottom Division"; 2 move each way every year). **Playoffs (rules sheet): 8 teams = top 6 of the Top Division + top 2 of the Bottom Division, seeded in that order** (`LEAGUE_RULES` in `index.html`; reproduces Sleeper's 2025 first round exactly), re-seeded, one-week rounds, consolation losers bracket (`playoff_type` 1). Weekly median game (two results a week). Trade deadline Week 12; 24-hour counteroffer rule. **Rookie draft order: the bottom 10 go into a weighted lottery for the top 10 picks** (owner, Nov 25): slots are projected by standings, with teams outside the current quota playoff field first (1.01–1.16) and the field last (1.17–1.24), each worst-first (`draftLottery: true`), and the playoff card's last column is "Last place", not the 1.01. |
| LFFL | 1312070951269076992 (2025: 1181014173902921728) | 12 teams, 1 QB, full PPR, no TE premium; starts QB, 2 RB, 2 WR, TE, FLEX, K, DEF; 5-round draft; trade deadline Week 13 | Built into `DEFAULT_LEAGUES` (Nov 25) so it shows on every device; the owner's phone kept losing it when added with + League (browser storage). **Playoffs:** 4 divisions of 3 (1–2 = Big Ten East, 3–4 = Big Ten West); the top 2 of each make it; round 1 is each division winner vs its sister division's runner-up, then the East and West winners meet, final East vs West; fixed bracket (`LEAGUE_RULES.bracket`; reproduces Sleeper's 2025 bracket exactly). **Draft:** the 4 non-playoff teams play a Toilet Bowl for picks 1–4 (winner 1.01); playoff teams eliminated before the final pick 5–10 worst record first (lower points break ties); runner-up 11, champion 12. In-season projection: Toilet Bowl teams best-first at 1–4, then the field worst-first; the playoff card hides the 1.01 column. |

## 3. Site map

Every page has `<meta name="robots" content="noindex, nofollow">` in its `<head>` (added Nov 25), so search engines leave the site out and it stays a link-only tool. Keep it on any new page. (A project site can't use robots.txt; that would have to sit at the root of calverrd.github.io.)

**`index.html` — hub and trade calculator.** One file. Tabs:
- Trade chart
- Trade calculator
- League
- Scout & Waivers
- Profile Buckets
- Rookies (one tab; a WR / RB / TE switcher, `#rookiePosBar`, over the three tracker iframes. Internal tab ids stay `rookies` / `rbs` / `tes`, so those hashes still open the right position; the Rookies tab reopens the last one, `dtv_rookie_pos`.)
- Prospects
- How it works

The embedded tabs are iframes. They talk to the hub with `postMessage`: `dtc-league` (teams with fit/send/recv/arch, plus players), `dtc-theme`, `dtc-height`.

**Player popup bucket bar (Nov 26):** the hub's player popup shows the Hit / Starter / Bust bar plus Hit, Elite, Repeater and n for the player's profile bucket, from `data/bucket-stats.json`. That file is written by `scripts/export_bucket_stats.py` from bucket-explorer.html's RAW_BUCKETS (run automatically by `build_buckets.py --write`; same arithmetic as the bucket detail), so the two can't drift. No bar for players without a named bucket (the hub's value-based guess). `getBucket` also tries the FantasyCalc→KTC nickname list (Kenny Gainwell → Kenneth Gainwell). Tapping the bar opens that bucket's detail on the Profile Buckets tab (`dtc-open-bucket`, sent once the frame posts `dtc-ready`). Note: the hub's own BUCKET_STATS / BUCKET_PLAYER_LISTS copies still drive the badge; they matched the explorer on Nov 26.

**Signal log comparison group (Nov 26, log_schema 2):** the daily log also records every rookie on the rookie tabs (this class and last) and every 12+ PPG veteran the sell table covers, flagged or not (`cohort` rookie / veteran, `flags` []), with the CHEAP/PRICEY ranks for the whole pool. Flag rules unchanged (rules v2). About 200 players / 55 KB a day. Offseason audit: flagged vs unflagged peers at the same position and price tier, 6 and 12 months on, and KTC + FC agree vs KTC only.

**CHEAP / PRICEY run Weeks 5–8 only (Nov 26, `mvExpired` in the hub and rookie tabs, `mv_expired` in log_signals.py):** off from the Tuesday after Week 8 (Week 1 = the Thursday after Labor Day; calendar, not games played). Why: the backtest set flags at Week 5 against Week 5 prices; the site kept recomputing Weeks 1–4 odds against each day's prices all season. Week 12 check: 5 of 6 showing flags were contradicted by Weeks 5–11 usage (Emmett Johnson PRICEY with usage 7.1 → 18.3; Lance / Meyers CHEAP with roles shrinking; Thompson CHEAP with no games since Week 4); only Cyrus Allen's PRICEY held. The log keeps the would-be flag in `mv.flag` with `mv.stale: true` (not in `flags`).

**Offseason test queue:** (1) missed games in the rookie odds model (rookies who missed early time hit 14% in the tracker backtest, but the odds model only sees usage per game played, e.g. Caleb Douglas 56%). Unlike the rejected role shares, games missed isn't already inside usage per game. **Read-only test (Nov 26, `research/usage_swaps.py`, not in the repo; same harness as the role-feature test, test classes 2019–23, train on classes ≤ Y−3, usage swapped as the single input):** baselines WR 0.1212 (G1–4) / 0.0887 (G1–8), RB 0.0951 / 0.0920. WR: dividing usage by games played + 2 instead of games played improved Brier in both windows (−0.0074, 95% −0.0138 to −0.0005; −0.0118, −0.0209 to −0.0030); + 1 also better (−0.0053 / −0.0087); team games (missed = 0) −0.0103 (crosses 0) / −0.0162. RB: none of these helped (per team game slightly worse); recency ramp (weights 1..N) and ffopportunity xFP per game were flat for both positions; RB target weight 2.0× / 3.0× flat vs the live 2.5×. Candidate: WR usage = sum / (games played + 2). 2026 effect (G1–8 live → +2 → team games): Caleb Douglas 56% → 47% → 24%, Omar Cooper 47% → 37% → 17%, healthy WRs up (Denzel Boston 76% → 86% → 91%). Before shipping, re-run with the 2024 class settled and check top-end calibration (do WRs pushed into 75–90% hit at that rate?), comparing + 2 vs team games. (2) A late-season market signal: rolling last-4-games usage and second-half trajectory (last 4 minus first 4, with a volume floor), backtested at Week 13 against DynastyProcess values like the Week 5 test; only goes live if it clears the same 95% bar. (3) Profile Bucket × live tag, using coarse buckets instead of the 48 small ones (2–3 players per cell would overfit): (a) 3 broad hit-rate tiers (High / Mid / Low), (b) an out-of-fold `Bucket Hit %` numeric prior (target-encoded inside each walk-forward fold so there's no leakage), (c) broad archetype groups (WR Alpha vs Beta, Hog vs Runt; RB Bellcow vs Committee). Test whether each improves 2015–2025 walk-forward Brier score on top of usage + draft pick, or clearly separates PPG outcomes when paired with WR BUY / Y2 JUMPED / PRICEY. Only goes live if it beats the existing baseline. (4) Continuous odds-vs-price score to replace the CHEAP / PRICEY rank cutoffs (diagnostic Nov 26, `research/flag_variants.py` + `sens.py`, not in the repo; 2020–2025 DynastyProcess rows). Gemini's tighter filters failed: a 20% gap + value ≥ 1000 left 0 CHEAP and 4 PRICEY flags; CHEAP limited to Rounds 1–2 fires once at Week 5 in six seasons (Round 3+ CHEAP, n = 41: +39% at 12m, 95% −12% to +120%). Continuous check, all players, class × position fixed effects: at the same starting price, +1 logit of model odds → log value change at 12m of +0.38 at Week 5 (95% +0.20 to +0.60), holding under a 3-knot spline on log(start value) (+0.40), value terciles (+0.24, +0.08 to +0.40) and v0 ≥ 200 (+0.43 to +0.50). Week 9 looked significant (+0.26) but drops to about +0.02–0.09 (CIs cross 0) once v0 < 200 rows are excluded, so the Week 9 result was floor-level mean reversion, not signal; Week 9 stays off. Offseason spec: show model-implied value vs market price (or an Overpriced ↔ Undervalued bar) for Weeks 5–8, no outcome-tuned cutoffs; if badges stay, use fixed bands set in advance (e.g. |z| ≥ 1.0 on the log residual, ≥ 1.5 strong) with KTC + FC agreement as the confirmation; log the score in the daily signal log from the 2027 class. Show the score only above a minimum market value (cutoff to test in the offseason, somewhere around 500–1,000 KTC / FC): below it, low-value rookies are the same floor noise that faked the Week 9 result (e.g. Dohnte Meyers, Reggie Virgil, Bryce Lance topping the Nov 26 gap list at 3–15% odds and 170–360 FC). Rules v2, the odds model and log_signals.py stay frozen until then.

**Tried and rejected, Nov 26 (don't re-run without new data):** (1) Role shares in the rookie odds model: snap share, target share, air-yards share / WOPR, carry share added to [usage, log pick], walk-forward 2019–2023 (TE 2019–2024), nflverse 2015–2026. No candidate's Brier 95% range sat below zero (best: WR + snap share −0.0014, −0.0037 to +0.0009); WR target share / WOPR at G1–8 and RB carry share made it worse. Usage per game already carries the volume. Route data (nflverse participation, `route` column) exists 2016–2025 only, not in-season. (2) TD regression for veteran sells: TD share of points, TDs above expected per game (league TDs per scrimmage yard), and a TD / non-TD PPG split added to [age, age², PPG], 12+ PPG seasons 2015–2024, walk-forward 2018–2024. No improvement at any position; RB TD share made it worse (+0.0055, +0.0004 to +0.0107): high-PPG RBs with a high TD share repeated 83% vs 74% low (lead-back role, not luck). In-sample, +10 points of TD share ≈ −0.45 (WR) / −0.82 (RB) PPG next season among those who played. `sellInfo` unchanged. (3) QB rushing vs passing aging: QB seasons 2015–2024 (8+ games), walk-forward 2018–2024, baseline [age, age², PPG], candidates rushing share, rushing share × age, passing/rushing PPG split. 18+ PPG (n 60): rushing share helped (Brier −0.027, −0.055 to +0.003; AUC 0.61→0.72) but the range crosses zero, and rushing QBs repeated MORE (≤26: 73% vs 29% pocket); × age added nothing; no 30+ rushing-heavy QB1 seasons in the data. 15+ PPG (n 148): no gain; rushing-heavy QBs 27–29 / 30+ repeated 47% (n 15) / 43% (n 7) vs pocket 67% / 60%, too few to act on. No QB sell flag. Revisit the 18+ rushing-share effect when more seasons exist. Earlier rejections: usage shrinkage, efficiency feature.

**CHEAP / PRICEY rerun + consensus + ask price + window tilt (Nov 26):** `backtest_market.py` 2020–2025 (DynastyProcess). Live rule at Week 5: 5 CHEAP, 5 PRICEY; all 5 PRICEY lost value vs matched peers (median −60% at 12m). Looser cutoff (min_gap 0): PRICEY 17, −48% at 6m / −56% at 12m (95% −72% to −31%); CHEAP 18, +54% / +53% (95% −29% to +253%). Week 9: neither flag works. 17 of 18 CHEAP flags were round 3+, so no round-based caution. Changes: CHEAP worded as "worth a look", PRICEY as the strongest sell signal; `signalPlayers` reruns the rule on FantasyCalc (`p.f`, KTC scale) → `mv.both` ("KTC + FC agree" vs "KTC only"), consensus ranked slightly higher; SELL rows show the higher of FC/KTC as the asking price (FC priced 12 of 15 flagged veterans above KTC on Nov 26); Buys & sells reorders by your team's `teamArchetype` (rebuild: SELL rows +1; contender: SELL WINDOW −1, buys + up to 0.3 by redraft value). signal log rules v2 adds `mv.fc_flag`. Rookie tabs still flag on KTC only.

**Daily signal log (Nov 26, `scripts/log_signals.py`, workflow step "Log today's signals"):** each run writes data/signal-log/YYYY-MM-DD.json: every player with WR BUY, Y2 JUMPED, MISSED TIME, CHEAP, PRICEY, SELL NOW or SELL WINDOW, with that day's KTC (SF + 1QB), FantasyCalc (SF dynasty + redraft), model odds (hp/he by window), usage, draft slot, the CHEAP/PRICEY ranks and the sell table's repeat odds. Rules copy the hub's (`signalPlayers`, `sellInfo`) on plain KTC superflex, so a flag near a cutoff can differ from a league's own view. Purpose: point-in-time prices for a forward test (6- and 12-month value and PPG after each flag). About 16 KB a day. Nothing on the site reads it.

**DDD lottery pricing (Nov 26, `lotteryDist`, `LEAGUE_RULES[DDD].lottery`):** the 10 worst teams get chips 1,2,3,4,5,7,9,11,13,15 (70); chips are drawn for 1.10 first, a drawn team's other chips leave the bucket, the last team left gets 1.01 (owner's league note). The lottery sets the whole draft order (owner, Nov 26), so the next draft's projected .01–.10 in every round (1–4) are valued at the exact lottery expectation of each source's slot values (KTC and FC separately), so each round's 10 picks keep about the same total: 1.01 −4%, 1.10 +8%. The pick card shows the odds ("lottery: 53% at 2.01, expected slot 2.4") and mixes the rookie outcome odds over the lottery. Uses today's projected order, not the playoff sim's finish distribution. Future years and leagues without the rule are unchanged.

**Card view retired (Nov 26, bucket-explorer.html):** the matrix now carries what only the cards had. Draft-class filter: `mxRecompute` rebuilds every matrix rate from the bucket player rows for the chosen classes (same rules as build_buckets.py, Rule A included; with no range it reproduces BUCKET_MATRIX exactly, checked for all 4 positions), and a bucket opened from the filtered matrix lists only those classes (`bm.years`). WR (Raw) has no player list on the page, so the filter and player search are off there. Player search: the matrix search box matches bucket names or, from 3 letters, player names (including the rookie tabs' names via CMP_ALIAS) and lists the matched players under the bucket row with owner + Offer. Owner + Offer also show in the player detail header. Removed: the card HTML, renderBucketsGrid, outcome pills, pre-2019 bust toggle.

**Buys & sells — one list (Nov 26, Scout & Waivers tab, `renderBuySell`):** combines only the backtested signals: WR BUY and Y2 JUMPED (signals.json `sig`), CHEAP / PRICEY (Weeks 1–4 odds vs KTC rank, the rookie tabs' exact rule), SELL NOW / SELL WINDOW (`sellInfo`). Each row shows 12+ and elite odds (rookies: `hp` / `he`, Games 1–8 when available; veterans: next-season 12+ from the sell table, k of n) and the class average. Ranked by the player's own odds first, signal second. A player with a buy and a sell signal shows in both with a MIXED tag. The older Sell-High / Buy-Low radars (untested heuristics) stay below it. Rookie Buy Targets now uses the same Weeks 1–4 CHEAP flag (was Games 1–8, which the backtest didn't support); both read `signalPlayers().mv`.

**24+ team pick discount (Nov 26, `lgPickMult` in the pick builder):** in leagues with 24+ teams (DDD), every pick is priced at the 12-team-mapped value × round (1st ×0.90, 2nd ×0.80, 3rd+ ×0.70) × year (next draft ×1.00, +1 ×0.95, +2 ×0.90). 12-team leagues are untouched. Evidence: DDD's five pick-for-player trades since Oct 2026 all had the pick side worth more on paper (picks would have needed ×0.33–0.74 to balance), and the hub's own DDD fit prefers a ×0.45 value adjustment; the multipliers are deliberately milder for the small sample. Pick history gets the same multiplier (`srcHistVal`), so trend arrows don't show a fake drop. Pick cards say "24-team pick discount ×0.81". **Rule: refit when DDD has 15+ pick-for-player trades** (pull trades from the Sleeper API, value both sides at that day's values, fit the multiplier that balances the median trade).

**One market value everywhere (Nov 26):** the hub also sends `dtc-values` (`sendValuesToFrames`, on every recompute and frame load): the calculator's own value for every player under the active source (Blend by default), in the active league's SF/1QB and TE format, keyed `POS|letters-only name` (suffixes dropped — the same key the rookie tabs, Compare and `scripts/check_names.py` use), as `[value, KTC, FantasyCalc, position rank, KTC only]`. The rookie tabs show it as the market column (header follows the source; KTC / FC on hover; a "KTC only" tag when FantasyCalc doesn't list him); CHEAP / PRICEY still compare odds with the KTC rank (`p.kFlag`), the price that rule was backtested on. Compare ranks the market by that one value (standalone: a 50/50 Blend built the hub's way from ktc.json + the FC cache). Opened outside the hub, the rookie tabs fall back to KTC superflex. Trend arrows were already Blend-to-Blend (`srcHistVal` skips dates without FC). The daily workflow logs current rookies KTC / FC can't match by name (`scripts/check_names.py`).

Main features and where they live:

| Feature | Code |
|---|---|
| Value sources and blend | `valueFor`, `modeValues` (cached), `recompute`, `buildScaleMap` (maps FC onto KTC's scale) |
| KTC-matched value adjustment | `ktcRaw`, `evalValues`, `evalTrade` |
| Consensus / offer check | `renderConsensus` |
| League-trade calibration | `loadTradeHistory`, `gradeTrade`, `calibrateAdj`, `renderTradeHistory` |
| Picks | `parsePickName`, `buildPickTable`, `anchorValue`, `pickValueFrom`, `pickOddsHtml` |
| Value history and trend graphs | `loadHistory`, `srcHistVal`, `histSeries`, `trendWindow`, `graphMode` / `listMode`, `openPlayerModal` |
| Lineups and rank impact | `solveLineup`, `teamStrength`, `tradeRankImpact` |
| Hub cards | playoff odds (`#playoffCard`, 2,000 seeded simulations of the rest of the regular season and the playoff bracket: Playoffs / Bye / Title / 1.01); team timeline (AGE_R curves); pick-ownership grid; handcuffs and stash alerts (DEPTH/BFSH, `SID_OWNER`); rookie targets (`signalPlayers`); sell windows (`sellBadge`) |
| Trading tools | Fit score (`computeFit`); Copy DM Pitch (`buildPitch`); acquire flow (`data-acquire` → `startAcquire`); Trade ideas section (`#tradeIdeasSection`) with three modes: shop one player (`renderTradeIdeas`), Trade Finder for one target (`acquireIdeas`), and **ideas with one team** (`#ideaPartnerSel` or the League tab's Ideas button → `partnerIdeas`) |
| Saved settings (localStorage) | adj, adjModel, fair, src, w, theme |

**Other pages:**
- `bucket-explorer.html` — Profile Buckets. TE hit = 12+ PPG with no near-hit tier; filter by draft class.
  - **Bucket matrix** section (`BUCKET_MATRIX`, `renderMatrix` / `wireMatrix`) and the bucket cards (`RAW_BUCKETS`) are both written by `python3 scripts/build_buckets.py <Updated Hit Rates.xlsx> --last-done <newest completed season> --write`, from the player rows of the sheet's "Updated Hit Rates" tab (one source; the sheet's own summary rows are ignored, they had drifted). Every player is named on the cards. Repeater % uses Audit 4 Rule A: the newest completed class's one-season hitters are left out of the denominator. Hit-mark repeaters: QB 20+, RB 15+, WR 14+; TE cards use 12+ (the TE hit mark; `te12` on TE buckets). Colors: one red → yellow → green scale (0% / 50% / 100%). Compact toggle on by default under 640 px. `scripts/build_matrix.py` is superseded.
- `rookie-wr-tracker.html`, `rookie-rb-tracker.html`, `rookie-te-tracker.html` — data embedded as `const DATA = [...]` and regenerated by the refresh workflow. Edit both the page and its template in `scripts/`.
- `prospects.html` — 2027 Prospects (draft-capital odds).
- `keeper.html` — keeper trade calculator for Sleeper keeper leagues, with a draft board tab.

## 4. Data files and workflows

| File | Written by | What it holds |
|---|---|---|
| `ktc.json`, `ktc-history.json` | `update-ktc.yml`, daily at 11:17 UTC | KTC values (Playwright fallback, since a plain fetch gets bot-blocked); 120 days of history |
| `data/fc/*.json` + `data/fc/manifest.json` | same workflow, via `scripts/fetch-fc-cache.mjs` (runs first) | The site's only FantasyCalc source: pages never call `api.fantasycalc.com` (FC terms: cache and reuse across users). 18 files `fc-{1qb|sf}-ppr{0|05|1}-{none|tep1|tep2}.json`, all at 12 teams, overwritten daily. Each: `updated`, `params`, `fields` (`sleeperId, name, pos, team, age, val, rval, t30`), `players`, `pickFields` (`name, val, fcId`), `picks`. `val` = dynasty value; `rval` = the `isDynasty=false` value (TE premium included), else the dynasty payload's `redraftValue`. 36 GETs a day, 0.75 s apart. A failed format keeps yesterday's file (marked `stale` in the manifest) and fails the run. ~22 KB per file (~5 KB gzipped). |
| `fc-history.json` | same workflow, via `scripts/update-fc.mjs` (reads `data/fc/fc-sf-ppr1-none.json`, no API call) | FantasyCalc dynasty SF values for 12 and 16 teams, keyed `sid:<SleeperID>`, 120 days. First day saved Nov 25. FC currently returns identical values for 12 and 16 teams. |
| `depth.json`, `draft_latest.json` | same workflow | RB depth charts and injuries; nflverse draft picks |
| `ppg.json`, `signals.json`, `bf.json`, rookie-tab `DATA` | `rookie-refresh.yml` (Tuesdays in Sep–Jan, plus manual), via `scripts/refresh/refresh_rookies.py` | Veteran PPG, rookie signals, buckets |
| `data/player-context.json` | `scripts/build_context.py`: after the Tuesday rookie refresh, and daily in `update-ktc.yml` (after the FC cache and KTC) | Slim copy of the three rookie tabs' `DATA` (`fields` + one array per row) plus veteran ages (`vets`, `"POS|normname": age`). Ages use the hub's order: FantasyCalc `maybeAge` (from `data/fc/fc-sf-ppr1-none.json`) first, then `ktc.json`, so both pages put a player in the same age band (Nov 25: 306 FC, 43 KTC). ~100 KB, 29 KB gzipped. Read by the comparison tool instead of the rookie pages (~1.4 MB). |
| `data/age-curves.json` | by hand (static; rebuild only if the nflverse study is rerun) | `sell.table` (next-season 12+ odds by position / age band / above-median PPG, cells `[hits, players]`) and `ageCurves.table` (next-season PPG retention by age). One copy, read by `index.html` (SELL badges, team timeline) and `bucket-explorer.html` (comparison). |
| `data/predraft_*` | `build-predraft-data.yml` (manual; discover or build mode) | Pre-draft prospect dataset |
| (run summary only) | `backtest-market.yml` (manual; inputs first_class, last_class, min_gap, min_value) | CHEAP/PRICEY backtest against DynastyProcess history. Never commits. |

Daily workflow safety:
- If FC fails (cache or history), KTC still runs (`continue-on-error`).
- `data/fc/*.json` files are committed only if they parse.
- The commit step uses `!cancelled()`.
- `fc-history.json` is committed only if it parses.
- A final step fails the run, so GitHub emails the owner, if FC failed.

Rookie refresh safety (`scripts/refresh/check_outputs.py`, runs before the commit):
- Every committed file must parse: the three pages' `DATA` (100+ rows, each with name, class and tier), `ppg.json` (200+ players, PPG −10 to 70, a season), `signals.json` / `bf.json` (season, non-empty players), `data/player-context.json` (row counts equal the pages', 100+ ages).
- Against the last commit: no file loses more than 15% of its rows (ppg/signals/bf compared only within the same season), and the season can't go backwards.
- On failure the workflow restores the committed files and fails the run (GitHub emails the owner). `build_context.py` also exits non-zero on missing or tiny `DATA`.

## 5. Value math (calculator)

- **Sources:** KTC, FantasyCalc (FC) or Blend (`w`% KTC).
  - FC is mapped onto KTC's scale with a quantile map.
  - FC TEs are raised by KTC's TE-premium ratio.
  - The KTC TE tier is chosen from the league's `bonus_rec_te`.
- **Value adjustment** (the "stud premium") matches KTC's calculator exactly on reference trades:
  - Formula: `ktcRaw(p,t,v) = p·(0.09356 + 0.27519(p/t)^1.3 + 0.07029(p/(v+2000))^1.28)`.
  - It's solved with bisection and added to the side with the bigger raw total.
  - The slider runs 0–1.5×, default 1.00 = KTC.
  - Reference checks: 9999 vs 8804 → add 4501; 9999 vs 5624+5101 → VA +6863, add 6138; 5624 vs 5101 → add 2159.
- **Fair:** within ±5% of the bigger side by default (slider).
- **Offer check:** grades the trade under KTC, FC and Blend at once.
  - Red: any source says you lose.
  - Green "Safe to send": every source says fair. It's downgraded when an asset is priced by only one source.
  - Amber "Likely rejected": every source says you win by more than max(12%, 2 × Fair).
  - Amber "Might be rejected": any one source says so.
- **League check:** grades the league's recent Sleeper trades (last 120 days, at today's values). It shows which adjustment setting and which source fit what leaguemates actually accept.
- **Picks:**
  - The next draft has per-slot values, from KTC/FC early/mid/late anchors interpolated by projected slot.
  - Later drafts use generic values.
  - Rounds 5+ (LFFL only; Nov 25): neither source prices them, so they're deep-dart estimates: 4% of that year's 1.01 at the top of round 5, sliding to 2% at its end, halved each later round, on each source's own scale (`est: true`). Before this, stretching the round-4 curve put a 5th near 1,700 in Blend.
  - Why LFFL's 4ths run above KTC's own (e.g. 4.03 = 2,611 Blend vs 2,383 KTC): FantasyCalc is translated onto KTC's scale by player rank, and FC's 4.03 (870) ranks with its ~200th player, which KTC values at ~2,840. Below ~#200 FC's values fall off fast while KTC's stay above 2,000, so FC's small pick values land high on KTC's scale. That's a real difference in how the two sources price late picks against fringe players, not a bug, so rounds 1–4 are unchanged.
  - Leagues over 12 teams map each overall pick onto the 12-team curve.
- **League rules by ID** (`LEAGUE_RULES`, `DEFAULT_LEAGUES`): Dirty Double Dozen's division playoff quotas, LFFL's division bracket, and the leagues' draft order are keyed by Sleeper league ID. **At each season rollover** (Sleeper issues a new league ID every year), add the new ID to `LEAGUE_RULES` and `DEFAULT_LEAGUES`. Quotas only apply when Sleeper reports roster divisions. When adding the new ID, also check the new league's `metadata.division_1` / `division_2` names: the quota assumes division 2 = "Top Division" and division 1 = "Bottom Division". For LFFL, add the new ID to both `DEFAULT_LEAGUES` and `LEAGUE_RULES` and confirm divisions 1–2 are still the East and 3–4 the West.
- **Trade playoff odds** (Nov 25): the calculator shows Playoffs / Bye / Title before → after for both teams (`tradeOddsStrip`), and one-team idea cards get a badge when any of them moves 1+ point for either team (`fillIdeaOdds`, filled a card at a time).
    - Engine: `playoffModel()` builds once per league data (cached by records, Win Now and PF): per-team scoring means, the remaining Sleeper schedule, and pre-drawn standard normals from a seeded PRNG (mulberry32, seed = league + weeks played). `runPlayoffSim(m, mu)` replays those same 2,000 seasons (about 2 ms), so baseline and "after" differ only through the two teams' means. A bench-only or picks-only trade gives exactly 0 for all teams.
    - Points per Win Now: only above-replacement scoring moves with lineup value. The slope is fit per league (team PPG on Win Now) and clamped to 30–50% of mean / average Win Now; it's used in both the baseline lineup term and the trade change. Apes, Nov 25: 47% (r = 0.90), about 2.2 points a week per 1,000 Win Now (the first version used 100%, 4.8 points, which was too steep).
    - A trade moves a team's mean by that slope × the change in its best this-season lineup (FantasyCalc redraft values, picks 0). Past points per game were scored by the old roster, so mu' = w·(PPG + Δ) + (1 − w)·(lineup term + Δ) = mu + Δ.
    - Bracket: standard seeding with byes for the top seeds (6 teams → 2 byes, 12 → 4); `playoff_seed_type` 1 re-seeds each round (confirmed on Apes' 2025 bracket: seed 1 played seed 6 in round 2); round length is `playoff_round_type` (`playoff_type` is the losers-bracket style): 0 = one week (both leagues; DDD's 2025 bracket ran 3 one-week rounds), 1 = two-week final and 2 = two-week rounds are assumptions; each week of a two-week round gets its own draw; higher seed wins ties. Hidden once the regular season is over (live bracket odds are a separate item).
- **FantasyCalc input:** `fcFromCache` turns `data/fc/fc-{1qb|sf}-ppr{0|05|1}-none.json` back into FC's row shape for the sync code. The sync pill's tooltip shows the cache time.
- **Trend graphs:** follow the selected source once FC history has 2+ days; until then they show KTC. Blend history reuses today's FC→KTC map (an approximation).

## 6. Rookie-tab model (validated)

- **Usage per game:**
  - RB: carries + 2.5 × targets
  - WR: 2.2 × targets + receptions + 0.12 × yards + 0.5 × TDs
  - TE: targets + 10 × snap share
- **Hit / elite:**
  - Hit = a completed season of 8+ games at 12+ PPG (PPR, TEs +0.5 per catch).
  - Elite = WR 14+, RB 15+, TE 17+.
  - Tiers come from the owner's Hit Rates sheet (`scripts/refresh/sheet_tiers.json`), with an nflverse fallback.
- **Odds:** logistic regression on log(draft pick) + usage. Leave-one-class-out AUC is about 0.85–0.90.
- **Views:**
  - WR: Weeks 1–4, 1–8
  - RB: Games 1–4, 1–8, Last 4
  - TE: Games 1–8, Season to date
  - Year 2: Games 1–4 by default, plus a 1–8 toggle
- **Presets:** click-to-load. Hidden range syntax: `ge:N`, `lt:N`, `rng:A:B`; draft groups `r12`, `r13`, `r3p`, `d3u`.
- **CHEAP/PRICEY flags** show only in the Games 1–4 view (WR/RB), per the market backtest:
  - Week 5 PRICEY (2020–2025 rerun, Nov 26): live rule n = 5, −59% at 6 months and −65% at 12 months vs matched FAIR rookies, all 5 below the FAIR median at 12 months; looser 15%-only gap n = 17, −48% / −56% (95% −73% to −31%).
  - Week 9 flags didn't help.
  - Rerun the backtest each season.
- **Refresh fields:** `tdn`, `b3` (typical best PPG in Years 1–3), `y2w8`, `u28`, `g28`.

## 7. Testing

- **Playwright:** `/opt/npm-tools/node_modules/playwright` or `/opt/node-tools/node_modules/playwright/index.mjs`, depending on the session; Chrome at `/usr/bin/google-chrome`.
- **Tailwind CDN** is blocked in tests: stub it with `addInitScript(() => { window.tailwind = { config: {} } })`.
- **Mocks:** mock Sleeper, FC and the data files with `page.route`, or serve the repo with `python3 -m http.server`.
- Unmocked Sleeper calls (matchups, `state/nfl`) show up as `ERR_FAILED` in tests. That's expected; real page errors show as `pageerror`.
- **Before pushing,** check the KTC reference trades in section 5 still match.

## 8. Open items

- **League tab team detail** (Nov 25): a Value / Position toggle (`st.rosterSort`) sorts the opened team's players (QB, RB, WR, TE, then value, with position labels) and picks (by year, round, slot, with year labels).
    - The opened detail is pinned (`position: sticky`, width = the table's visible width, refit on resize) so on phones the value column is on screen even though the League table itself scrolls sideways.

- **FantasyCalc API terms** (https://fantasycalc.com/terms-of-usage, https://fantasycalc.com/api-docs, effective Oct 10, 2026; free under 1,000 monthly users with attribution):
    - A visible "FantasyCalc" link to https://fantasycalc.com near the data on every page using it, with at least one in the static HTML. Done: `index.html` header next to the Blend/KTC/FC toggle (Nov 25); `keeper.html` footer already had one.
    - Only `GET /values/current`. Responses must be cached and reused across users; each unique query may be refreshed at most once every 3 hours. Done Nov 25: `index.html` and `keeper.html` read `data/fc/` (see section 4); neither calls the API.
        - Pre-flight (Nov 25): the dynasty payload's `redraftValue` covers the same 194 players as `isDynasty=false` and matches it exactly in SF / 1 PPR, but ignores the TE premium (25 TEs, up to +29%) and drifts 1–3% in 1QB formats. So each file also takes the `isDynasty=false` call.
        - League size: every league maps to 12 teams. FC's 8/10/14-team values differ from 12 by a median ~0.6–1% (max ~3% among the top 150); 16 is identical to 12; TE premium changes only TEs.
        - `index.html` uses the `none` files (it applies KTC's TE lift itself). `keeper.html` uses the league's TE-premium file, falling back to `none`.
    - Use restriction 1b: FC data or derivatives may not be used to replicate or substitute for FC's trade calculator or other key features. **Owner decision (Nov 25): keep using FantasyCalc values for the time being.** Revisit if FantasyCalc objects or the terms change; the options were written permission, FC as a secondary signal only, or KTC-only trade grades.

- **Fixed Nov 25 — Blend outside KTC and FC.** There were two causes:
    1. `evalValues` gave the value adjustment to whichever side led on the raw curve. When that lead flipped, the stud side's premium dropped from about +3,000 to 0, so a near-even stud-for-package verdict could swing about 30 points. Now the side with the best player always gets the adjustment, sized continuously. KTC reference trades are unchanged.
    2. Blend mixed asset values with FC rescaled onto KTC's curve, which changes how players compare to each other. Now `evalIds(aIds, bIds, mode)` grades Blend from KTC's and FC's own results: `mixEvals` mixes each side's SHARE of the trade by the blend weight. That's a convex mix, so Blend always lies between them (0 of 3,941 random test trades fall outside) and each source gets exactly its weight. Normalizing by each source's top value instead had tilted the mix toward KTC's flatter curve.
    3. The adjustment is signed: it's credited to the stud side, or to the other side when that side is the more consolidated package, so |effA − effB| = X everywhere. On blowouts, the inverse search widens instead of capping at 2× the top value.
    - The verdict is steep near even (about 0.12 points per value point against a 3,000 + 2,900 package) but has no jumps. That steepness is KTC's own model, the same one that matches the reference trades.
    - Calibration now shows how many trades are uneven (only those move with the setting) and the best fit for KTC and FC separately.
    - Every trade grade now goes through `evalIds`: calculator, offer check, league trades, calibration, Trade ideas. Asset-level Blend values (`valueFor`) are still used for the chart, totals and "add X" suggestions.
- **Built Nov 25 — player comparison** (`bucket-explorer.html`, "Compare players" section; `wireCompare` / `renderCompare`). Value-free by default: no KTC, no FC, no CHEAP/PRICEY.
  - **Elite odds (Option 3, Nov 25):** `hp` = 12+ odds, `he` = elite odds (WR 14+ / RB 15+, tier green) per window, written by `add_odds` in `scripts/refresh/refresh_rookies.py` (also into `signals.json`). `he` is the 12+ model rescaled (a 1-input logistic of elite on the 12+ score), clamped to ≤ `hp`; the UI shows "<5%" when `hp` < 5. Walk-forward backtest (2019–23): a separate elite model ranked the same (Spearman 0.94–1.00) with no AUC gain; the rescaled version had the best Brier / log-loss in all four WR/RB windows. So no Safe/Upside re-rank: Compare shows elite odds as a second number. TEs (6 hits at 17+) and veterans stay 12+ only.
  - **Model B for WR/RB odds (Nov 26):** `add_odds` trains WR/RB on a 12+ PPG season in Years 1–3 (`b3 >= 12`; elite `b3 >= 14` WR / `>= 15` RB) using only classes with three completed seasons (`yr <= LAST_DONE - 2`), the same target and window as the ladder. Backtest 2019–23 vs the old "12+ ever, through LAST_DONE − 1" model: Brier/AUC a wash (CIs cross 0), WR odds-vs-ladder clashes 13 → 1 (G1–8) and 19 → 1 (G1–4), and the old model ran high (WR G1–8 predicted 29%, actual 24%). TEs stay on the old target (12+ in any season); the stricter window was worse for TEs. `data/player-context.json` now carries `he` too (`scripts/build_context.py`).
  - **Projected best season (Nov 25):** Compare players' "Projected best season, Years 1–3" row. WR/RB use `ladderBest`: logistic fits of P(b3 ≥ t) for t = 2…30 (step 0.5) on standardized usage + log pick (pk fallback 300), 2-game floor, settled classes through newest−3; monotone in t; median = where P crosses 50%; middle half = median + training-pool residual 25th/75th percentiles. Cached per position/window (~90 ms first fit). TEs keep the 15-NN median. Walk-forward backtest (2019–23): best MAE/RMSE for WR and RB (WR G1–8 3.12/3.99 → 2.89/3.62), fewer clashes with the 12+ odds (WR G1–8 18 → 11 of 39 high-odds rookies with a sub-12 median; RB G1–8 9 → 1), middle-half coverage 49–54%. The rookie tracker tabs' own "typ. best" column is still 15-NN.
    - **2–4 players + ranked summary** (Nov 25, `rankSummary` / `rankOdds`). Rule from a walk-forward backtest (to predict class Y, only classes ≤ Y−3; test classes 2018–2023; Brier / log-loss):
        - (These numbers are from this older Compare-players backtest, run before Model B changed the target; they aren't comparable with Model B's walk-forward baselines, WR 0.1212 / 0.0887 and RB 0.0951 / 0.0920.) WR: usage model 0.0701 (Games 1–8 view 0.0675); bucket alone 0.0931; draft round 0.1063; equal 3-way blend 0.0740; weights chosen year by year from earlier years 0.0765. RB: model 0.1278 (Games 1–8 0.1171); nested blend 0.1286. Draft round's best weight is 0% for WR and RB (the model already has draft slot). Buckets can't be tested fairly: bucket lists name most hits but count many busts only as a total, so named members skew to hits (47 of 82 WRs).
        - TE (64 players, 8 hits): model 0.150, draft round 0.128, 50/50 model + draft round 0.121.
        - Typical best season in the comparison uses the same view as the ranking (Games 1–8 when he has 2+ of those games), so it matches the rookie tab's Games 1–8 view (Bernard 12.9 on both).
        - So: WR/RB rookies ranked by the usage model alone (Games 1–8 when he has 2+ of those games, else Weeks 1–4); TE rookies by 50/50 model + draft-round 12+ rate, tagged "TE small sample"; a player whose 12+ season is already on the books shows "already hit". Each row shows a sample tag (e.g. "8g", "4g · thin" under 6 games, "rookie yr" for sophomores). Buckets and draft history stay as context rows.
        - Veterans ranked by next-season 12+ odds (`sellOdds`). Rookies and veterans are never ranked together; a mixed group gets two labeled lists. Players without odds are listed as not ranked, with the reason.
    - **Market line** (opt-in, off by default): loads `ktc.json` and `data/fc/fc-{sf|1qb}-ppr1-none.json` only when switched on; SF / 1QB switch; shows KTC / FC and a market rank (average of the two ranks in the group) and flags "cheap for his odds" / "priced above his odds" when market and odds ranks differ by 2+ (1+ for two players).
    - Name variants between the bucket sheet and the rookie tabs (Kevin vs KC Concepcion) are matched by class + last name + first initial when unique.
    - Any positions. Two search boxes (datalist of every bucket player), Swap, and a Safe / Upside toggle that sets which odds line comes first.
    - Safe = 12+ PPG (QB 16+) from bucket `nearTotal` (TE: hit). Upside = WR 14+ / RB 15+ / TE 17+ / QB 20+ from bucket `hit` (TE: `elite`).
    - Odds and comps always come from the player's own bucket. The type (e.g. Konami vs Pocket) is the point of a bucket, so the owner decided against pooling other types at the same tier (Nov 25).
    - When a bucket has fewer than 5 players: a "Small sample — treat as a lean" note, a faint tier-average reference line (`tierWide`, labeled "different play styles mixed"), and no lead pills.
    - Also shown: Repeat %, the top 4 hits and the 3 most recent busts from the bucket.
    - Lazy-loads `signals.json`, `ppg.json`, `data/player-context.json` and `data/age-curves.json` the first time it's used (about 40 KB gzipped; was about 1.4 MB when it read the rookie pages).
        - Draft-slot history: same round group, settled classes, % hitting 12+ and % reaching the tab's elite tier (Hit Rates sheet tiers: WR/RB `green` = 14+/15+, TE `g17` = 17+).
        - Early usage (WR/RB Games 1–4, TE Games 1–8), model odds (`hp`), flags (BUY / MISSED TIME / JUMPED), BF%, Year 2 usage.
        - Typical best season: `typBestCmp` uses the same 15-nearest method as the rookie tabs, and matches them exactly (Love 17.7, Coleman 6.3).
        - Career: season counts by PPG tier (bucket data), this season's PPG (`ppg.json`), and next-season odds to repeat 12+ (`sellOdds`, the same table and SELL NOW / SELL WINDOW rule as the hub's `sellInfo`; RB/WR/TE at 12+ PPG; shows the age band and n).
    - Each Safe/Upside cell prints that player's PPG bar. The "+N" lead pill shows only on same-position pairs.
    - WR header shows within-class rank (WR1 = first WR drafted that year). Odds for older unsettled players are labeled "Rookie-yr odds"; each view needs 2+ games.
- **Fixed Nov 25 — Year 2 preset counts:** a Year 2 bullet's % covers settled classes only (through the newest class − 3; 2023 now), but the filter also lists newer sophomores. The preset bar now says how many settled players the % is based on and how many newer ones are in the list (TE "9+ both years": 7 + 4 = the 11 rows). It doesn't print its own hit rate: the bullets count 12+ seasons in Year 2 or later, which needs season-level data the pages don't carry. Year 1 bars are unchanged.
    - **Maintenance:** the Year 2 cutoff is pinned (`Y2_BULLET_CUTOFF = 2023` in all three rookie pages) to match the static Year 2 bullet text. When the Year 2 bullets are regenerated with newer classes, update that constant in the same push. Otherwise the bar's settled count won't match the bullets.
- **Fixed Nov 25 — dead-looking presets:** four "best filter combination" bullets had no `data-preset`, so tapping did nothing: WR "Usage 8–15 · Day 3 or undrafted"; TE "Games 1–8 · Usage 9+ · Round 4 or later", "MISSED TIME · Round 1–3" and "Round 4 or later · Games 1–8 usage under 6". All 39 presets now load, and their settled-class numbers match the text.
- **Done Nov 25 — ideas with one team** (`partnerIdeas`): owner asked for trade ideas with one chosen team, based on what each team needs.
    - **Focus player** (Nov 25, `#ideaFocusSel`, shown in one-team mode): "Any player" (default) is the unchanged generator. Picking one of your assets ("Move from") or one of theirs ("Target from") builds only packages containing it (same shapes and sweeteners, same offer-check window), skips the need-fit gates (they still rank), ignores Target Pos when the focus is what you get, lets the focus asset repeat across cards, and requires it to be the most valuable piece on its side (so a deep stash isn't shopped as filler). Empty state names the player. Resets to Any when he's on neither roster.
    - Uses both full rosters (assets worth 700+): 1-for-1, 2-for-1 / player + pick, and 1-for-2 / get player + pick.
    - Keeps a deal only if, on the selected source, you don't lose by more than Fair and don't win by more than max(12%, 2 × Fair).
    - It must help you (need score ≥ 0), cost them at most a little (≥ −4), and help overall. Picks-only swaps are dropped.
    - Need fit = filling positions below the league average without opening a hole on the other side, plus timeline (rebuild teams like early picks and youth; contenders don't want picks).
    - Shows up to 12, each with a reason for each side. Ideas passing the offer check under all three sources come first, marked ✓; the rest show which source disagrees.
    - Each asset appears at most twice.
    - The Goal box reshapes the ranking (`goalBonus`):
        - Hit & Repeater: favors receiving higher bucket hit/repeat rates.
        - Rebuild: favors receiving picks (early more) and players ≤ 24.5; penalizes receiving players 28+.
        - Win-Now: favors receiving starters (value ≥ 3,500); penalizes receiving picks.
        - Closest: weights the value gap 4× instead of 1.2×.
    - Near-miss deals get one sweetener from the short side, picked to bring all three sources closest to the window.
    - First live result (before the Blend fix and loosening): 4 of 11 teams got only 1 idea. Sweeteners can now be added to 2-player packages too, up to 4 pieces.
- **About Dec 25:** backtest which source (KTC, FC, Blend) best predicted later value moves, using `ktc-history.json` and `fc-history.json`.
- **Unresolved method differences** (decide, don't silently pick):
  - An older 24-team chat used a stud premium of `Σ 10000·(v/10000)^1.5`, calibrated to both sites' calculators. The site now uses the KTC-matched adjustment above. Compare the two on 24-team trades.
  - That chat pulled FC with `numTeams=14&tep=te+` (FC's real TE-premium setting). The site uses 12/16 teams and scales FC TEs by KTC's TE ratio. Check whether `tep=te+` should replace the scaling.
- **Known limits:**
  - League-trade grading uses today's values, not values at trade time.
  - Today's TE lift is applied to past FC values for TEs.
