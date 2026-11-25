// Saves a daily snapshot of FantasyCalc dynasty values to ./fc-history.json
// (last 120 days), so we can later test which source best predicts value changes.
// Format: { version, updatedAt, formats:["sf12","sf16"], days: { "YYYY-MM-DD": { key: [sf12, sf16] } } }
// key = "sid:<Sleeper ID>" when FantasyCalc gives one (stable), else "<normalized name>|POS" (picks etc.)
// Non-fatal by design: the workflow runs this with continue-on-error.

import { readFileSync, writeFileSync, existsSync, renameSync } from "node:fs";
import { mergeHistory, normName } from "./update-ktc.mjs";

const HISTORY = "fc-history.json";
const BASE = "https://api.fantasycalc.com/values/current?isDynasty=true&numQbs=2&ppr=1&numTeams=";
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

async function getFormat(n) {
  const res = await fetch(BASE + n, { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const rows = await res.json();
  if (!Array.isArray(rows)) throw new Error("not a list");
  // Each format is checked on its own: enough rows with real, positive values
  const good = rows.filter((r) => r && r.player && Number.isFinite(Number(r.value)) && Number(r.value) > 0);
  if (good.length < MIN_ROWS) throw new Error(`numTeams=${n}: only ${good.length} valid rows`);
  return good;
}

async function main() {
  const lists = [];
  for (const [, n] of FORMATS) lists.push(await getFormat(n));
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
