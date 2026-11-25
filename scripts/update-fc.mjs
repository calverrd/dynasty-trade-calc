// Saves a daily snapshot of FantasyCalc dynasty values to ./fc-history.json, from the daily cache in data/fc/
// (last 120 days), so we can later test which source best predicts value changes.
// Format: { version, updatedAt, formats:["sf12","sf16"], days: { "YYYY-MM-DD": { key: [sf12, sf16] } } }
// key = "sid:<Sleeper ID>" when FantasyCalc gives one (stable), else "<normalized name>|POS" (picks etc.)
// Non-fatal by design: the workflow runs this with continue-on-error.

import { readFileSync, writeFileSync, existsSync, renameSync } from "node:fs";
import { mergeHistory, normName } from "./update-ktc.mjs";

const HISTORY = "fc-history.json";
const FORMATS = [["sf12", 12], ["sf16", 16]];
const MIN_ROWS = 200;

export function fcSnapshot(lists) {
  // lists: array (one per format) of FC rows
  const snap = {};
  lists.forEach((rows, i) => {
    for (const r of rows || []) {
      const pl = r.player || {};
      if (!pl.name || !pl.position) continue;
      const key = pl.sleeperId ? `sid:${pl.sleeperId}` : `${normName(pl.name)}|${pl.position}`;
      if (!snap[key]) snap[key] = new Array(lists.length).fill(null);
      snap[key][i] = Math.round(r.value);
    }
  });
  return snap;
}

// Reads today's FantasyCalc cache (data/fc/, written just before by fetch-fc-cache.mjs) instead of calling the
// API again: the terms allow one refresh per unique query, and the cache already holds SF / 1 PPR at 12 teams.
// FantasyCalc returns the same values for 16 teams as for 12 (checked Nov 25), so sf16 reuses it.
const CACHE = "data/fc/fc-sf-ppr1-none.json";
function getFormat() {
  const f = JSON.parse(readFileSync(CACHE, "utf8"));
  if (!f.updated || !(Date.now() - Date.parse(f.updated) < 12 * 3600 * 1000)) throw new Error(`${CACHE} is more than 12 hours old (${f.updated})`);
  const P = f.fields, K = f.pickFields || ["name", "val", "fcId"];
  const rows = f.players.map((r) => ({ player: { sleeperId: r[P.indexOf("sleeperId")], name: r[P.indexOf("name")], position: r[P.indexOf("pos")] }, value: r[P.indexOf("val")] }))
    .concat(f.picks.map((r) => ({ player: { sleeperId: r[K.indexOf("fcId")] || "", name: r[K.indexOf("name")], position: "PICK" }, value: r[K.indexOf("val")] })));
  const good = rows.filter((r) => r && r.player && Number.isFinite(Number(r.value)) && Number(r.value) > 0);
  if (good.length < MIN_ROWS) throw new Error(`only ${good.length} valid rows`);
  return good;
}

async function main() {
  const lists = [];
  const today = getFormat();
  for (const f of FORMATS) lists.push(today);   // sf12, sf16 (identical at FantasyCalc)
  const snap = fcSnapshot(lists);
  let prev = null;
  if (existsSync(HISTORY)) {
    try { prev = JSON.parse(readFileSync(HISTORY, "utf8")); } catch { prev = null; }
  }
  const dateKey = new Date().toISOString().slice(0, 10);
  const hist = { ...mergeHistory(prev, dateKey, snap), formats: FORMATS.map((f) => f[0]) };
  // Write to a temp file, check it parses, then swap it in (never leaves a half-written file)
  const tmp = HISTORY + ".tmp";
  writeFileSync(tmp, JSON.stringify(hist) + "\n");
  JSON.parse(readFileSync(tmp, "utf8"));
  renameSync(tmp, HISTORY);
  console.log(`Wrote ${HISTORY}: ${Object.keys(snap).length} assets, ${Object.keys(hist.days).length} day(s)`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((e) => {
    console.error(`FantasyCalc snapshot failed: ${e.message}`);
    process.exit(1);
  });
}
