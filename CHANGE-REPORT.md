# Dynasty Trade Calculator: Change Report (for review)

**Repo:** `calverrd/dynasty-trade-calc` (GitHub Pages: https://calverrd.github.io/dynasty-trade-calc/)
**Date:** Nov 23, 2026
**Status:** Part B is **live** (deployed Nov 23, 2026, ~10:25 AM CT). Netlify copy deleted. The first live workflow run succeeded: 500 KTC entries, 457/464 players with Sleeper IDs, `ktc-history.json` day 1 saved.

---

## Part A: Changes made Nov 22 (already live)

1. **Daily KTC data job**
   - `.github/workflows/update-ktc.yml` runs on a daily cron (11:17 UTC) and can be started manually from the Actions tab. It has `permissions: contents: write`.
   - It runs `scripts/update-ktc.mjs`, which:
     - fetches `https://keeptradecut.com/dynasty-rankings`, falling back to Playwright/Chromium if a plain fetch is blocked
     - extracts `playersArray` and writes `ktc.json` (`{ updatedAt, count, players[] }`, with `superflexValues` / `oneQBValues` and `tep` / `tepp` / `teppp` tiers)
     - fails without writing anything if fewer than 300 players are found
   - First run: 500 entries (464 players + 36 rookie picks).
2. **`index.html`: TE premium tier.** For TEs, the KTC value now uses the tier that matches the league's Sleeper `bonus_rec_te`: ≥1.5 uses `teppp`, ≥1.0 uses `tepp`, ≥0.5 uses `tep`.
3. **Profile Buckets tab**
   - `bucket-explorer.html` is embedded as a 6th tab in a same-origin iframe. The iframe's `src` is only set when the tab is first opened.
   - The calculator's theme is mirrored into the frame by toggling its `dark` class and sending a `postMessage`.
   - The frame's height follows its content (`ResizeObserver` plus a `postMessage` fallback).
   - When the explorer runs inside the calculator, it adds `html.embedded`. This removes `min-h-screen`, which otherwise caused a resize feedback loop, and hides the explorer's own theme toggle.
   - Its Range of Outcomes modal is repositioned to the part of the frame visible in the parent window, and the parent page's scrolling is locked while it is open.
4. **Bucket Explorer: TE is hit-or-bust at 12+ PPG**
   - Tuple column 2 (12+ seasons) is now the TE hit count, and the near-hit tier is removed for TE.
   - TE 2+ season and repeater % are recomputed from the named players. They match the calculator's existing TE table exactly.
   - Fixed the calculator's `Clogger Gifted` hit rate, which used the 14+ rate (4.65): it is now 8.14.
5. **Bucket Explorer: draft-class filter.** A year range filter (default 2006–2026) controls which player chips are shown. Bucket percentages stay based on the full sample.
6. **Bucket Explorer: "Hide pre-2019 busts" toggle** now applies to every bucket. It previously applied only to buckets whose names start with "Clogger", which affected 21 players.

---

## Part B: This build (Nov 23)

Files changed: `index.html`, `scripts/update-ktc.mjs`, `.github/workflows/update-ktc.yml`. New data file created by the job: `ktc-history.json`.

### B1. Data job (`scripts/update-ktc.mjs`, workflow)
- **Daily history:** `ktc-history.json` = `{ version, updatedAt, days: { 'YYYY-MM-DD': { 'Name|POS': [sf, 1qb] } } }`.
  - TE rows hold 8 numbers: `[sf, 1qb, sfTep, sfTepp, sfTeppp, 1qbTep, 1qbTepp, 1qbTeppp]`.
  - Rookie picks are stored under their KTC name, e.g. `2027 Early 1st|RDP`.
  - The last 120 days are kept, with one snapshot per UTC date (a rerun on the same day overwrites).
- **New fields in `ktc.json`:** `age` (if KTC provides it) and `sleeperId`.
  - `sleeperId` comes from `https://api.sleeper.app/v1/players/nfl`, matched on normalized name + position. A position-agnostic fallback is used only when the name is unique.
  - If the Sleeper call fails, the job continues without IDs.
- **Workflow:** now runs `git add ktc.json ktc-history.json`.
- **Limitation:** KTC does not expose past values in a form the job can download, so history starts accumulating from the first run after deployment. Nothing is backfilled.

### B2. Value accuracy (`index.html`, sync function)
1. **KTC matching**
   - Order: Sleeper ID first, then alias-normalized `name|pos`, then name alone (only if unambiguous).
   - `NAME_ALIASES` covers known spelling differences between FC/Sleeper and KTC.
   - KTC players FantasyCalc doesn't list are now **added** (flagged `ktcOnly`) instead of dropped. They join Sleeper rosters through `sleeperId`. Previously about 25% of KTC entries were unmatched.
2. **FC on KTC's scale**
   - `buildScaleMap()` quantile-matches FC values to KTC values, using only players both sources value. It needs at least 25 pairs, otherwise it returns identity.
   - `p.f` is FC on KTC's scale (used for blending). `p.fRaw` is FC as published (used in FC-only mode and the chart's KTC / FC column).
   - FC mode falls back to `FC_SCALE.toFc(k)` for KTC-only players.
3. **TE premium for FC:** each TE's FC value is multiplied by that player's own KTC tier/base ratio, or the median ratio for unmatched TEs. This replaces a guessed `×(1+tep×0.14)`.
4. **Draft picks** (the biggest change)
   - **Sources:** real pick values from KTC (`RDP`, e.g. "2027 Early 1st") and FantasyCalc (`PICK`, e.g. "2027 1st (Early)" or "2027 1st"), parsed by `parsePickName()`.
   - **Anchors:** Early / Mid / Late sit at fractions 1/6, 1/2 and 5/6 of a round. Values are linearly interpolated between anchors, and extrapolation is clamped to ≤ first anchor × 1.15 and ≥ last anchor × 0.85.
   - **Next draft:** every slot gets its own asset (`2027 1.03`). An owner's pick uses the projected slot of the original team (worst record first, then lowest points-for).
   - **Later two drafts:** generic mid-round assets (`2028 1st`).
   - **Leagues bigger than 12 teams:** the overall pick number is mapped onto the 12-team curve. Example: 24-team 1.24 = overall #24 = 12-team 2.12. Rounds past the last anchored round decay ×0.6 per round.
   - **Draft years** come from the Sleeper league's `season + 1` (no longer hard-coded to 2027–2029).
   - The old hand-made curve (`overallPickValue12T`) is used only if neither source has the pick.
5. **Stale data warning:** the header pill turns amber ("KTC stale (date)") when `ktc.json` is more than 48 hours old.
6. **FantasyCalc 16-team cap:** in leagues over 16 teams, the pill tooltip and sync status say FC values are 16-team values. The FC request itself was already capped at 16.

### B3. Value adjustment: matched to KeepTradeCut (replaces the per-asset stud exponent)
- **Old method:** every asset was transformed as `10000·(v/10000)^1.35` before summing. This also distorted 1-for-1 trades.
- **Interim version** (`v·(v/top)^adj`, in the first draft of this report): replaced because it was far milder than KTC. It called Chase 8,200 vs Lamb 5,500 + Mixon 4,900 fair; KTC says the Lamb side must add about 2,700.
- **Current method:** KTC's own structure.
  - **Per-asset "raw adjustment":** `raw(p) = p · (d + a·(p/t)^1.3 + b·(p/v)^8 + c·(p/(v+2000))^1.28)`, where `p` = asset value, `t` = best asset in the trade and `v` = best asset overall (the max value in the current value mode).
  - **Where the formula comes from:** the exponents and structure were read from KTC's client-side code by Javelin Fantasy Football ("How the KeepTradeCut Value Adjustment Works", 2022). That article didn't publish the constants, so they were fitted with non-negative least squares.
  - **Fitted to today's KTC:** the first fit used only the 2022 published numbers, and it ran about 10% too harsh against KTC's live calculator. The constants were refitted to three live KTC trades from Nov 23, 2026, with the 2022 numbers as a soft constraint: `d = 0.09356, a = 0.27519, b = 0, c = 0.07029`.
    - The third (mid-range) trade showed that the `(p/t)^1.3` term carries most of the weight.
    - An intermediate fit using only the two top-player trades was about 13% too gentle mid-range: it predicted 1,874 where KTC says 2,159.
  - **Reference trades** (KTC Nov 23, 2026, Gibbs 9999 = top overall):
    - Gibbs 9,999 vs Bowers 8,804: KTC says add 4,501; ours adds **4,501**.
    - Gibbs 9,999 vs Carnell Tate 5,624 + Jonah Coleman 5,101: KTC gives Value Adjustment +6,863 and add 6,138; ours gives **+6,863 / 6,138**.
    - Carnell Tate 5,624 vs Jonah Coleman 5,101: KTC says add 2,159; ours adds **2,159**.
    - These are recorded in a code comment next to the constants.
  - **2022 numbers** still within about 2–6% (9999 → 4,244 vs 4,169; 5000 → 1,141 vs 1,077; 1000 → 110 vs 115).
  - **Verdict:** the side with the larger raw total is giving up the better piece. The other side would need an extra asset `X` with `raw(X) = |rawA − rawB|` (found by bisection). The value adjustment `max(0, other + X − own)` is credited to the first side.
  - **Slider:** **Value adj.** (0–1.5, default ×1.00 = KTC; 0 = off) scales the adjustment.
  - **Saved settings:** settings saved by the interim version are reset to ×1.00.
- **Behavior to be aware of (this is how KTC works):** strongly favors the single best piece.
  - Uneven 1-for-1s get an adjustment too: 9,999 vs 8,804 needs a 4,501 player added, in both KTC and ours.
  - 2-for-1: 9,999 vs 5,624 + 5,101 gives the 9,999 side +6,863.
  - Equal 1-for-1 → no adjustment.
- **Fair range:** **Fair ±** slider (2–15%, default 5% of the larger side). KTC's own default is reportedly 5% of the *combined* value, which is about twice as lenient, so ours is intentionally stricter. "Slight edge" is any gap up to 2.4× the fair range; anything above is "Lopsided".
- **Balance suggestions:** picks are chosen by re-evaluating the trade with each candidate pick added.
- **Check against league trades** (League tab): for 2-team trades in the last 120 days where every asset is still valued, it computes the median gap between sides for strengths 0–1.5. It reports the gap at KTC ×1.00, with no adjustment, and the best fit, and offers a "Use ×N" button. It needs at least 4 trades. Labeled as a sanity check, because accepted trades aren't all fair and the values used are today's.
- **Caveats:**
  - The fit uses three live trades plus the 2022 numbers. Low-value-only trades (e.g. 2,000 vs 1,500) and 3-for-1s aren't directly verified yet. If KTC changes its formula, re-check the reference trades.
  - The formula is applied to blended / FC values too (`v` adapts to the current mode's top value).

### B4. Player value trends
- **Opening the pop-up:** click any player name (Trade chart, trade sides, waivers, risers/fallers, trade history).
- **Pop-up contents:**
  - calculator value, KTC / FC as published, KTC 7-day and 30-day change, and FC `trend30Day`
  - two SVG line charts (no library): KTC value, and positional rank among KTC players at that position in the league's format and TE tier (rank axis inverted)
  - a 7D / 30D / All toggle
- **Short history:** when there is less history than the window, the change is shown "since <first date>". With only one snapshot, the pop-up says the graphs will fill in.
- **Trend arrows** appear next to names: KTC 7-day change when available, otherwise FC 30-day change.
- **Risers & Fallers** card (Scout tab): rostered players, 7 or 30 days. It falls back to FC 30-day data, clearly labeled, until KTC history exists.

### B5. League tab: graded trade history
- Fetches Sleeper `transactions/0..18` for the current league and `previous_league_id` (one season back). It keeps `type=trade`, `status=complete`, de-duplicated.
- Each side's received assets (players via `adds`, picks via `draft_picks.owner_id`, FAAB shown at 0) are valued at **today's** values with the same value adjustment and fair range.
- **Valuing picks:** picks from drafts that already happened show as "(already drafted)" with value 0. Next-draft picks use the original team's projected slot.
- **Manager summary:** trades, won/lost, and net value (adjusted value received − average adjusted value of the other sides). Click a manager to filter.
- Loaded lazily the first time the League tab opens; reset when the league changes.
- **Limitation:** last season's roster IDs are mapped to current team names (normal in Sleeper dynasty leagues, since roster IDs persist).

### B6. Trade calculator additions
- **League rank before → after**
  - For both teams: QB / RB / WR / TE, Starting lineup, Draft capital, Total value, ranked among all teams before and after the trade.
  - Position strength = value of the players who start at that position in each team's optimal lineup (existing `solveLineup`). A TE or QB filling a FLEX / SUPER_FLEX spot counts for his own position. *(Revised after review: this replaced a fixed 50/50 RB/WR flex split, which ignored TEs in FLEX.)*
- **Quick facts per side:** average player age, pick count, and an "est. in 2 yrs" value.
  - The estimate is a rough age-curve multiplier per year (`ageMult`): RBs fade from about 25, WRs about 28, TEs about 30, QBs about 32.
  - Next-draft picks are held flat. Later-year picks rise to today's value of a mid-round pick in the next draft for the same round, since they appreciate as their draft approaches. *(Revised after review.)*
  - It is labeled as an estimate in the UI.
- **Trade Idea Finder**
  - New **2-for-1 Upgrade** idea type: the target is worth 8–120% more than the base player, and the best second asset from the user's roster or picks is chosen by minimum adjusted gap.
  - Existing idea types now use the value adjustment and the fair range.
- **Waiver scanner:** Sleeper trending adds (`/players/nfl/trending/add?lookback_hours=24&limit=100`) shown as "🔥 N adds (24h)", plus a 🔥 Trending sort toggle.

### B7. Consensus check (trade calculator)
- Every trade is graded under all three value sources at once: **KTC** (`k`, falling back to FC on KTC's scale), **FantasyCalc** (as published) and **Blend** (current weight).
  - Each source uses its own top overall value for the KTC-matched adjustment (`evalValues(..., vmax)`) and the same Fair ± range.
  - Values per source come from `valueFor(p, mode)`; `recompute()` uses the same function for the active source, so they can't drift apart. Results are cached per recompute.
- **When your team is Side A or B:**
  - a red banner if any source says you lose ("⚠ 2 of 3 value sources say you lose this trade (FantasyCalc, Blend)")
  - otherwise a green "No value source says you lose", plus how many say you win
- **When neither side is your team:** an amber "Sources disagree" banner if their verdicts differ.
- One chip per source (Fair / who wins and by how much). "Copy summary" includes the consensus line.
- Tested in headless Chrome: lose case (3 of 3 flagged), win case, neutral teams, cleared trade (hidden). No errors.

### B8. Other
- Header layout: the value-source controls stack under the tabs below 1,536px (`2xl`) so the six tabs and three sliders don't collide (fix made after deploy).
- The "How it works" tab explains the value adjustment, blending, picks and trends.
- The iframe's `loading="lazy"` attribute is removed when the tab is opened. The `src` is already deferred, and native lazy-loading could leave the frame blank in headless Chrome.

---

## Testing done
- Syntax check: `node --check` on all inline JavaScript and the scraper; YAML parsed with PyYAML.
- Scraper helpers unit-tested: normalize, Sleeper ID attach, snapshot, history trimming to 120 days.
- **Headless Chrome (Playwright) with mock data:** a 12-team superflex 0.5 TEP league with rosters, traded picks, 7 trades across 2 seasons, trending adds, FC data (different scale, picks, trend30Day), `ktc.json` (255 players + 15 KTC-only + 36 picks) and 35 days of history. Results:
  - no console errors or page errors
  - pick values decrease steadily by slot (1.01 > … > 1.12 > 2.01)
  - KTC-only players are added and appear on rosters
  - KTC-matched adjustment unit-tested against three live KTC trades (all matched exactly, see B3); equal 1-for-1 gives 0 adjustment
  - league check computes with 6 mock recent trades
  - the rank table, trade history grading, modal charts (7D shows 8 points), risers/fallers and trending sort all render
  - the Profile Buckets frame loads and resizes; all 6 tabs switch
  - consensus check: lose / win / neutral / cleared cases (see B7)
- **24-team test:** 1.12 = 12-team 1.12; 1.24 is priced as 12-team 2.12; values decrease through round 4; FC request uses `numTeams=16`; cap note shown.

## Not tested / please double-check
- **Real data:** the test workspace has no internet access, so real KTC, FantasyCalc and Sleeper responses weren't used. Check after deploy:
  - real KTC pick names parse (check the Trade chart → Pick filter)
  - the Sleeper `players/nfl` match rate in the Action log
  - trade history with real transactions
- **Styling:** Tailwind couldn't load offline, so layout was checked structurally only. Look over the new cards and the pop-up on desktop and phone.
- **Review notes (Nov 23):** an external review flagged the interim `evalValues` formula as a possible bug (it read the subtracted amount as the kept amount). That formula has since been replaced by the KTC-matched one in B3. Pick clamp: 1.01 is extrapolated along the Early→Mid slope; the ×1.15 cap only applies if that slope is very steep (in testing, 1.01 came out at 1.05× the Early anchor).
- **Judgment calls worth reviewing:** the fitted KTC constants (three live reference trades + 2022 data), the age-curve multipliers, lineup-based position strength for the rank table, and the ±15% / 0.6 extrapolation limits for picks.

## Deploy steps
0. Delete the Netlify copy of the site (it rebuilds on every commit, including the daily KTC commit, which would use up the free plan's credits). GitHub Pages is the only host.
1. Commit `index.html`, `scripts/update-ktc.mjs` and `.github/workflows/update-ktc.yml` to `main`.
2. Actions → "Update KeepTradeCut Values Daily" → Run workflow. Confirm `ktc-history.json` appears and the log shows Sleeper IDs attached.
3. Hard-refresh the site and check the pill, Trade chart → Pick, a player pop-up, the League tab trade history, and Scout → Risers & Fallers.

---

## Update — Nov 25, 2026: accuracy safeguards (not yet deployed)

### 1. FantasyCalc history saved daily (`scripts/update-fc.mjs`, new)
- Fetches FC dynasty values (superflex, PPR) for 12-team and 16-team formats and saves one compact snapshot per day to `fc-history.json`: `{version, formats:["sf12","sf16"], days:{date:{"Name|POS":[sf12, sf16]}}}`. Keeps 120 days (reuses `mergeHistory` from update-ktc.mjs). Needs at least 200 rows or it writes nothing.
- Workflow: a new step runs *before* the KTC scrape with `continue-on-error: true`, so an FC outage never blocks KTC. The commit step now has `if: always()`; that's safe because the KTC script never writes when its scrape fails. `fc-history.json` is added to the commit when present. An empty placeholder `fc-history.json` is shipped so the site doesn't log a 404 before the first save.

### 2. Offer check in the consensus box (`renderConsensus`)
When you've picked your team, the banner now has four states, checked in this order:
- **Red — you lose:** at least one source says the other side wins (unchanged).
- **Green — Safe to send:** every source calls the trade fair (gap within the Fair ± setting).
- **Amber — Likely rejected:** every source says *you* win by more than 2.4× the fair range (12%+ at the default ±5%). The banner shows the smallest of those gaps.
- **Green — no source says you lose:** anything else; shows how many sources say you win.

New **"Less reliable"** line, listing any asset that:
- has only one source's value (the other sources fall back to a converted copy of that number, so they aren't independent checks); or
- has no source value at all (a pick priced by the estimated fallback curve). New `est` flag on pick objects.

### 3. Which source fits your league (`calibrateAdj` / `renderTradeHistory`)
- On the same usable recent trades (two-team, last 120 days, every asset valued), it computes the median gap and the share graded fair under KTC, FC and Blend, at the current Value adj. setting.
- Sources are ranked, with the best one starred. A "Use X" button switches the calculator source; it reuses the existing source buttons through a `data-usesrc` handler.
- If the top two sources are within 2 points, it says no source clearly fits better.

### 4. Trend graphs follow the calculator's source
Previously the player-popup graphs, 7/30-day changes, chart badges and League Movers used KTC history only, even with Blend or FC selected. Now:
- FC players carry `fcKey` ("Name|POS") and `fcTeMult` (the KTC TE-premium lift applied to their FC value today).
- `srcHistVal(p, date, mode)` rebuilds a past value the same way `valueFor()` builds today's:
  - FC uses the 12- or 16-team column (16 when the league has 14+ teams), with the TE lift applied.
  - Blend = w·KTC + (1−w)·FC mapped to KTC's scale with `FC_SCALE.toKtc`, falling back like `valueFor`.
- Positional rank under FC/Blend is the rank among the calculator's players at that position on that date (cached).
- `listMode()` uses the selected source once FC history has 2+ days, otherwise KTC. `graphMode(p)` falls back to KTC for picks or players lacking points. All labels (graph title, change cards, Movers subtitle, notes) name the source actually graphed.

### Testing (headless Chrome with mock data)
- Full UI run passes with no console errors, with and without an FC history fixture.
- The "you lose" and "likely rejected" banners trigger as expected. With FC removed for one player, the "Less reliable" note names him.
- With the FC history fixture loaded, the popup, change cards and Movers show "Blend". Without it, they show KTC plus a note that FC history is still building.
- The KTC reference trades still match exactly (add 4501 / VA +6863, add 6138 / add 2159).
- `fcSnapshot` unit test passes. The live FC fetch could not be tested here (no network); it will run on GitHub's runner.

### Known limits
- Blend history uses today's FC→KTC scale map for past dates (not each day's own map), which is a close approximation.
- League fit uses today's values on past trades, so it measures fit to the current market, not the market when the trade happened.
- In about 30 days of saved history, the next step is a backtest of which source best predicted later value moves.

### Gemini review fixes (Nov 25)
- "Likely rejected" threshold is now max(12%, 2 × Fair ±) instead of 2.4 × Fair ± (fixes Fair 0% / 2% / 10% edge cases).
- New amber "Might be rejected" when ANY source says you win past that threshold (and none says you lose).
- "Safe to send" downgrades to "Looks fair… but some values come from only one source" whenever the Less-reliable list isn't empty.
- fc-history keys are now "sid:<Sleeper ID>" (normalized "name|POS" fallback), so name changes don't break history.
- League sizes between 12 and 16 interpolate between the sf12 and sf16 values (14 teams = average).
- No source-switch cliffs: if a source prices a player today, past dates without that source are skipped instead of spliced in from the other source.
- Workflow: commit step uses `!cancelled()` (not `always()`); fc-history.json is only staged if it parses; update-fc.mjs writes to a temp file, verifies it, then renames; each FC format is validated on its own (200+ rows with finite positive values); a final step fails the run (sending GitHub's failure email) if FantasyCalc failed, after KTC data is already committed.
- Known limit added: today's KTC TE-premium lift (fcTeMult) is applied to past FC values for TEs.

### Deployment note
The first Nov 25 upload accidentally overwrote index.html and the workflow with an older base, dropping the Nov 23–24 work (Hub, Trade Finder, rookie tabs, sell windows, depth.json/draft_latest.json commits). Both were restored with a 3-way merge the same morning; nothing was lost.
