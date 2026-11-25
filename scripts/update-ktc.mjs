// Scrapes KeepTradeCut dynasty rankings and writes:
//   ./ktc.json          – today's values (what index.html loads)
//   ./ktc-history.json  – one compact snapshot per day (last 120 days) for the trend graphs
// Step 1: KTC's JSON endpoint (/dynasty-rankings/player-pool). Since Nov 2026 the
//         rankings page ships `playersArray = []` and loads players from this URL.
// Step 2: plain fetch() of the HTML + parse `playersArray` (the old page format).
// Step 3 (fallback): headless Chromium via Playwright, wait for window.playersArray to fill.
// Each step counts as failed if it returns fewer than MIN_PLAYERS, so the next one is tried.
// Also attaches Sleeper player IDs (so KTC-only players can be matched to Sleeper rosters)
// and writes depth.json (RB depth charts + injury status from Sleeper's players file).
// Fails (non-zero exit) if every step comes up short, so a bad scrape
// never overwrites good data.

import { readFileSync, writeFileSync, existsSync } from "node:fs";

const URL = "https://keeptradecut.com/dynasty-rankings";
const POOL_URL = "https://keeptradecut.com/dynasty-rankings/player-pool";
const SLEEPER_PLAYERS = "https://api.sleeper.app/v1/players/nfl";
const OUT = "ktc.json";
const HISTORY = "ktc-history.json";
const DEPTH = "depth.json";
const HISTORY_DAYS = 120;
const MIN_PLAYERS = 300;
const UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

// Same normalisation index.html uses
export function normName(s) {
  return String(s || "").toLowerCase()
    .replace(/['’.]/g, "")
    .replace(/\b(jr|sr|ii|iii|iv|v)\b/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

// Pull the array literal that follows `playersArray =` using bracket matching
// (safer than a regex if a player name ever contains "];").
export function extractPlayersArray(html) {
  const m = html.match(/playersArray\s*=\s*\[/);
  if (!m) return null;
  let i = m.index + m[0].length - 1; // at "["
  const start = i;
  let depth = 0, inStr = false, quote = "", esc = false;
  for (; i < html.length; i++) {
    const c = html[i];
    if (inStr) {
      if (esc) esc = false;
      else if (c === "\\") esc = true;
      else if (c === quote) inStr = false;
      continue;
    }
    if (c === '"' || c === "'") { inStr = true; quote = c; }
    else if (c === "[") depth++;
    else if (c === "]" && --depth === 0) {
      return JSON.parse(html.slice(start, i + 1));
    }
  }
  return null;
}

function valueBlock(v) {
  if (!v || typeof v !== "object") return { value: 0 };
  const out = { value: Number(v.value) || 0 };
  // KTC TE-premium tiers: tep (+0.5), tepp (+1.0), teppp (+1.5)
  for (const k of ["tep", "tepp", "teppp"]) {
    if (v[k] && v[k].value != null) out[k] = { value: Number(v[k].value) || 0 };
  }
  return out;
}

export function normalize(raw, sleeperIndex) {
  return raw
    .filter((p) => p && p.playerName)
    .map((p) => {
      const out = {
        playerName: p.playerName,
        position: p.position,
        team: p.team ?? null,
        superflexValues: valueBlock(p.superflexValues),
        oneQBValues: valueBlock(p.oneQBValues),
      };
      const age = Number(p.age);
      if (Number.isFinite(age) && age > 15 && age < 50) out.age = Math.round(age * 10) / 10;
      if (sleeperIndex && p.position !== "RDP") {
        const sid = sleeperIndex.get(`${normName(p.playerName)}|${p.position}`) || sleeperIndex.get(`${normName(p.playerName)}|*`);
        if (sid) out.sleeperId = sid;
      }
      return out;
    });
}

// Compact daily snapshot: "Name|POS" -> [sf, 1qb]  (TEs: [sf, 1qb, sfTep, sfTepp, sfTeppp, 1qbTep, 1qbTepp, 1qbTeppp])
export function snapshot(players) {
  const snap = {};
  for (const p of players) {
    const sf = p.superflexValues, oq = p.oneQBValues;
    const row = [sf.value, oq.value];
    if (p.position === "TE") {
      row.push(sf.tep?.value ?? sf.value, sf.tepp?.value ?? sf.value, sf.teppp?.value ?? sf.value,
               oq.tep?.value ?? oq.value, oq.tepp?.value ?? oq.value, oq.teppp?.value ?? oq.value);
    }
    snap[`${p.playerName}|${p.position}`] = row;
  }
  return snap;
}

export function mergeHistory(prev, dateKey, snap, keepDays = HISTORY_DAYS) {
  const days = { ...(prev && prev.days ? prev.days : {}) };
  days[dateKey] = snap;
  const keys = Object.keys(days).sort();
  for (const k of keys.slice(0, Math.max(0, keys.length - keepDays))) delete days[k];
  return { version: 1, updatedAt: new Date().toISOString(), days };
}

async function sleeperPlayers() {
  try {
    const res = await fetch(SLEEPER_PLAYERS, { headers: { "User-Agent": UA } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    console.warn(`Sleeper players download failed (${e.message})`);
    return null;
  }
}

// depth.json: every NFL team's RBs in Sleeper depth-chart order, with injury status, for the hub's
// handcuff and stash cards. Small (about 30 KB) so the browser never needs Sleeper's 5 MB players file.
export function buildDepth(all) {
  const teams = {};
  for (const [id, p] of Object.entries(all || {})) {
    if (p.position !== "RB" || !p.team || !p.active) continue;
    const order = Number(p.depth_chart_order);
    const inj = p.injury_status || (/injured reserve|physically unable/i.test(p.status || "") ? "IR" : null);
    (teams[p.team] = teams[p.team] || []).push({
      sid: id,
      n: p.full_name || `${p.first_name || ""} ${p.last_name || ""}`.trim(),
      o: p.depth_chart_position === "RB" && Number.isFinite(order) ? order : 99,
      inj,
      age: p.age ?? null,
    });
  }
  for (const t of Object.keys(teams)) {
    teams[t].sort((a, b) => a.o - b.o || a.n.localeCompare(b.n));
    teams[t] = teams[t].slice(0, 5);
  }
  return { updatedAt: new Date().toISOString(), teams };
}

function sleeperIndex(all) {
  try {
    if (!all) throw new Error("no players file");
    const idx = new Map();
    const byName = new Map();
    for (const [id, p] of Object.entries(all)) {
      const pos = p.position;
      if (!["QB", "RB", "WR", "TE"].includes(pos)) continue;
      const name = p.full_name || `${p.first_name || ""} ${p.last_name || ""}`;
      const key = normName(name);
      if (!key) continue;
      const k = `${key}|${pos}`;
      // Prefer players currently on a team / active when names collide
      const score = (p.team ? 2 : 0) + (p.active ? 1 : 0);
      const prev = idx.get(k);
      if (!prev || score > prev.score) idx.set(k, { id, score });
      byName.set(key, (byName.get(key) || 0) + 1);
    }
    const out = new Map();
    for (const [k, v] of idx) out.set(k, v.id);
    for (const [k, v] of idx) {
      const nm = k.split("|")[0];
      if (byName.get(nm) === 1) out.set(`${nm}|*`, v.id); // unique name: position-agnostic fallback
    }
    console.log(`Sleeper index: ${out.size} keys`);
    return out;
  } catch (e) {
    console.warn(`Sleeper players lookup failed (${e.message}); continuing without sleeperIds`);
    return null;
  }
}

function requireEnough(arr, label) {
  if (!Array.isArray(arr)) throw new Error(`${label}: no player array`);
  if (arr.length < MIN_PLAYERS) throw new Error(`${label}: only ${arr.length} entries`);
  return arr;
}

async function viaPool() {
  const res = await fetch(POOL_URL, {
    headers: {
      "User-Agent": UA,
      Accept: "application/json,text/plain,*/*",
      "Accept-Language": "en-US,en;q=0.9",
      Referer: URL,
    },
  });
  if (!res.ok) throw new Error(`player-pool HTTP ${res.status}`);
  const j = await res.json();
  const arr = Array.isArray(j) ? j : (j && (j.players || j.data));
  return requireEnough(arr, "player-pool");
}

async function viaFetch() {
  const res = await fetch(URL, {
    headers: {
      "User-Agent": UA,
      Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "en-US,en;q=0.9",
    },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const arr = extractPlayersArray(await res.text());
  if (!arr) throw new Error("playersArray not found in HTML (likely bot protection)");
  return requireEnough(arr, "HTML playersArray");
}

async function viaPlaywright() {
  const { chromium } = await import("playwright");
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await (await browser.newContext({ userAgent: UA, locale: "en-US" })).newPage();
    await page.goto(URL, { waitUntil: "domcontentloaded", timeout: 60000 });
    const read = () =>
      typeof playersArray !== "undefined" ? playersArray : window.playersArray; // eslint-disable-line no-undef
    await page.waitForFunction(
      (min) => {
        const a = typeof playersArray !== "undefined" ? playersArray : window.playersArray; // eslint-disable-line no-undef
        return Array.isArray(a) && a.length >= min;
      },
      MIN_PLAYERS,
      { timeout: 60000 }
    );
    let arr = await page.evaluate(read);
    if (!Array.isArray(arr)) arr = extractPlayersArray(await page.content());
    return requireEnough(arr, "Playwright");
  } finally {
    await browser.close();
  }
}

async function main() {
  let raw = null;
  const errors = [];
  for (const [label, fn] of [["player-pool", viaPool], ["fetch()", viaFetch], ["Playwright", viaPlaywright]]) {
    try {
      raw = await fn();
      console.log(`${label}: found ${raw.length} entries`);
      break;
    } catch (e) {
      console.warn(`${label} failed: ${e.message}`);
      errors.push(e.message);
    }
  }
  if (!raw) throw new Error(`All KTC sources failed (${errors.join("; ")}). Not writing ${OUT}.`);

  const all = await sleeperPlayers();
  if (all) {
    const depth = buildDepth(all);
    writeFileSync(DEPTH, JSON.stringify(depth) + "\n");
    console.log(`Wrote ${DEPTH}: ${Object.keys(depth.teams).length} teams`);
  }
  const players = normalize(raw, sleeperIndex(all));
  if (players.length < MIN_PLAYERS) {
    throw new Error(`Only ${players.length} players parsed (need ${MIN_PLAYERS}+). Not writing ${OUT}.`);
  }

  const now = new Date();
  const data = { updatedAt: now.toISOString(), count: players.length, players };
  writeFileSync(OUT, JSON.stringify(data, null, 2) + "\n");
  console.log(`Wrote ${OUT} with ${players.length} players (${players.filter((p) => p.sleeperId).length} with Sleeper IDs). Top: ${players[0].playerName}`);

  let prev = null;
  if (existsSync(HISTORY)) {
    try { prev = JSON.parse(readFileSync(HISTORY, "utf8")); } catch { prev = null; }
  }
  const dateKey = now.toISOString().slice(0, 10);
  const hist = mergeHistory(prev, dateKey, snapshot(players));
  writeFileSync(HISTORY, JSON.stringify(hist) + "\n");
  console.log(`Wrote ${HISTORY}: ${Object.keys(hist.days).length} day(s) of history`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}
