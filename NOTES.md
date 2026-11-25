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
| Planet of the DynastyIM Apes | 1334642025076621312 | 12 teams, superflex, TE +0.5/rec | Default league in `index.html` |
| Dirty Double Dozen | 1312492943805779968 | 24 teams, 1 QB, TE +0.5/rec; starts QB, RB, 2 WR, TE, 2 FLEX; 6 bench + 3 taxi, no IR | Valued as **superflex**: 24 starting QBs is the same QB demand as a 12-team superflex league. Picks are mapped onto the 12-team curve by overall pick number. |

## 3. Site map

**`index.html` — hub and trade calculator.** One file. Tabs:
- Trade chart
- Trade calculator
- League
- Scout & Waivers
- Profile Buckets
- Rookie WRs, Rookie RBs, Rookie TEs
- Prospects
- How it works

The embedded tabs are iframes. They talk to the hub with `postMessage`: `dtc-league` (teams with fit/send/recv/arch, plus players), `dtc-theme`, `dtc-height`.

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
| Hub cards | playoff odds (`#playoffCard`, 2,000 simulations); team timeline (AGE_R curves); pick-ownership grid; handcuffs and stash alerts (DEPTH/BFSH, `SID_OWNER`); rookie targets (`signalPlayers`); sell windows (`sellBadge`) |
| Trading tools | Fit score (`computeFit`); Copy DM Pitch (`buildPitch`); acquire flow (`data-acquire` → `startAcquire`); Trade ideas section (`#tradeIdeasSection`) with three modes: shop one player (`renderTradeIdeas`), Trade Finder for one target (`acquireIdeas`), and **ideas with one team** (`#ideaPartnerSel` or the League tab's Ideas button → `partnerIdeas`) |
| Saved settings (localStorage) | adj, adjModel, fair, src, w, theme |

**Other pages:**
- `bucket-explorer.html` — Profile Buckets. TE hit = 12+ PPG with no near-hit tier; filter by draft class.
- `rookie-wr-tracker.html`, `rookie-rb-tracker.html`, `rookie-te-tracker.html` — data embedded as `const DATA = [...]` and regenerated by the refresh workflow. Edit both the page and its template in `scripts/`.
- `prospects.html` — 2027 Prospects (draft-capital odds).
- `keeper.html` — keeper trade calculator for Sleeper keeper leagues, with a draft board tab.

## 4. Data files and workflows

| File | Written by | What it holds |
|---|---|---|
| `ktc.json`, `ktc-history.json` | `update-ktc.yml`, daily at 11:17 UTC | KTC values (Playwright fallback, since a plain fetch gets bot-blocked); 120 days of history |
| `fc-history.json` | same workflow, via `scripts/update-fc.mjs` | FantasyCalc dynasty SF values for 12 and 16 teams, keyed `sid:<SleeperID>`, 120 days. First day saved Nov 25. FC currently returns identical values for 12 and 16 teams. |
| `depth.json`, `draft_latest.json` | same workflow | RB depth charts and injuries; nflverse draft picks |
| `ppg.json`, `signals.json`, `bf.json`, rookie-tab `DATA` | `rookie-refresh.yml` (Tuesdays in Sep–Jan, plus manual), via `scripts/refresh/refresh_rookies.py` | Veteran PPG, rookie signals, buckets |
| `data/predraft_*` | `build-predraft-data.yml` (manual; discover or build mode) | Pre-draft prospect dataset |
| (run summary only) | `backtest-market.yml` (manual; inputs first_class, last_class, min_gap, min_value) | CHEAP/PRICEY backtest against DynastyProcess history. Never commits. |

Daily workflow safety:
- If FC fails, KTC still runs (`continue-on-error`).
- The commit step uses `!cancelled()`.
- `fc-history.json` is committed only if it parses.
- A final step fails the run, so GitHub emails the owner, if FC failed.

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
  - Leagues over 12 teams map each overall pick onto the 12-team curve.
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
  - Week 5 PRICEY trailed similar FAIR rookies by 59% at 6 months and 70% at 12 months; 7 of 8 trailed.
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

- **Top priority — Blend can fall outside KTC and FC.** On real Apes data (Nov 25), one trade showed KTC and FantasyCalc both saying you win by more than 12%, while Blend said +5%. Blend should land between the two.
    - Likely cause: "FantasyCalc" mode grades on FC's own scale (`fRaw`), while Blend mixes in FC mapped onto KTC's scale (`fK`, via `buildScaleMap`). The value adjustment isn't linear, so the two FC versions can disagree.
    - Fix first, then re-check the offer check and Trade ideas: grade all three on one scale.
- **Done Nov 25 — ideas with one team** (`partnerIdeas`): owner asked for trade ideas with one chosen team, based on what each team needs.
    - Uses both full rosters (assets worth 700+): 1-for-1, 2-for-1 / player + pick, and 1-for-2 / get player + pick.
    - Keeps a deal only if, on the selected source, you don't lose by more than Fair and don't win by more than max(12%, 2 × Fair).
    - A deal must help at least one side and hurt neither; picks-only swaps are dropped.
    - Need fit = filling positions below the league average without opening a hole on the other side, plus timeline (rebuild teams like early picks and youth; contenders don't want picks).
    - Shows up to 12, each with a reason for each side. Ideas passing the offer check under all three sources come first, marked ✓; the rest show which source disagrees.
    - Each asset appears at most twice.
    - Near-miss deals get one sweetener from the short side, picked to bring all three sources closest to the window.
    - Live result in the Apes league (Nov 25): 7 of 11 teams get 6–12 ideas, but 4 get only 1, and almost none pass all three sources. Revisit after the Blend fix above. The "hurt neither side" rule may be too strict for a rebuilder trading with contenders (picks score negative for contenders).
- **About Dec 25:** backtest which source (KTC, FC, Blend) best predicted later value moves, using `ktc-history.json` and `fc-history.json`.
- **Unresolved method differences** (decide, don't silently pick):
  - An older 24-team chat used a stud premium of `Σ 10000·(v/10000)^1.5`, calibrated to both sites' calculators. The site now uses the KTC-matched adjustment above. Compare the two on 24-team trades.
  - That chat pulled FC with `numTeams=14&tep=te+` (FC's real TE-premium setting). The site uses 12/16 teams and scales FC TEs by KTC's TE ratio. Check whether `tep=te+` should replace the scaling.
- **Known limits:**
  - League-trade grading uses today's values, not values at trade time.
  - Today's TE lift is applied to past FC values for TEs.
