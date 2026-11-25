// Daily FantasyCalc cache for the site: data/fc/*.json + data/fc/manifest.json.
// FantasyCalc's API terms (fantasycalc.com/terms-of-usage, effective Oct 10, 2026) require responses to be cached
// and reused across users, with each unique query refreshed at most once every 3 hours. So visitors' browsers never
// call api.fantasycalc.com: index.html and keeper.html read these files instead, and this script runs once a day.
//
// Formats, all at numTeams=12 (the pages map every league size to 12; other sizes differ by ~1%, at most ~3%):
//   numQbs 1 / 2  x  ppr 0 / 0.5 / 1  x  tep none / te+ / te++   = 18 files
// Each file costs two GETs on /values/current: isDynasty=true (dynasty value, trend) and isDynasty=false
// (redraft value). The dynasty payload's own redraftValue ignores the TE premium and drifts 1-3% in 1QB formats,
// so the redraft call's value wins when present (same rule keeper.html used: fcRed.value || redraftValue).
// 36 requests a day, 0.75 s apart.
//
// File: { updated, params, fields, players: [[sleeperId, name, pos, team, age, val, rval, t30], ...],
//         picks: [[name, val, fcId], ...] }   (picks have no Sleeper ID; fcId is FantasyCalc's own, e.g. FP_2027_early_0)
// Each file is overwritten in place. If a format fails validation, its previous file is kept and the run exits 1
// (the workflow flags it) after writing everything else.

import { readFileSync, writeFileSync, existsSync, renameSync, mkdirSync } from "node:fs";

const BASE = process.env.FC_BASE || "https://api.fantasycalc.com/values/current";
const DIR = process.env.FC_DIR || "data/fc";
const DELAY_MS = Number(process.env.FC_DELAY_MS ?? 750);
const MIN_PLAYERS = 200;
const QBS = [[1, "1qb"], [2, "sf"]];
const PPRS = [[0, "ppr0"], [0.5, "ppr05"], [1, "ppr1"]];
const TEPS = [["none", "none"], ["te+", "tep1"], ["te++", "tep2"]];
export const FIELDS = ["sleeperId", "name", "pos", "team", "age", "val", "rval", "t30"];
export const PICK_FIELDS = ["name", "val", "fcId"];

export const fileName = (qb, ppr, tep) =>
  `fc-${QBS.find((x) => x[0] === qb)[1]}-${PPRS.find((x) => x[0] === ppr)[1]}-${TEPS.find((x) => x[0] === tep)[1]}.json`;

const num = (v) => (Number.isFinite(Number(v)) ? Number(v) : 0);

// Pure: two raw FantasyCalc lists -> the slim file object. Throws if the result looks broken.
export function buildFile(dynRows, redRows, params, updated) {
  if (!Array.isArray(dynRows)) throw new Error("dynasty response is not a list");
  const red = new Map();
  for (const r of Array.isArray(redRows) ? redRows : []) {
    const pl = r && r.player;
    if (pl && pl.sleeperId && pl.position !== "PICK" && num(r.value) > 0) red.set(String(pl.sleeperId), num(r.value));
  }
  const players = [], picks = [], seen = new Set();
  for (const r of dynRows) {
    const pl = r && r.player;
    if (!pl || !pl.name || !pl.position) continue;
    if (pl.position === "PICK") { picks.push([pl.name, Math.round(num(r.value)), pl.sleeperId ? String(pl.sleeperId) : ""]); continue; }
    const sid = pl.sleeperId ? String(pl.sleeperId) : "";
    if (sid) seen.add(sid);
    const rval = (sid && red.get(sid)) || num(r.redraftValue);
    players.push([sid, pl.name, pl.position, pl.maybeTeam || "", pl.maybeAge == null ? null : num(pl.maybeAge),
      Math.round(num(r.value)), Math.round(rval), Math.round(num(r.trend30Day))]);
  }
  // Players only in the redraft list (none seen on Nov 25) are kept with no dynasty value
  for (const r of Array.isArray(redRows) ? redRows : []) {
    const pl = r && r.player;
    if (!pl || !pl.sleeperId || pl.position === "PICK" || seen.has(String(pl.sleeperId)) || !(num(r.value) > 0)) continue;
    players.push([String(pl.sleeperId), pl.name, pl.position, pl.maybeTeam || "", pl.maybeAge == null ? null : num(pl.maybeAge), 0, Math.round(num(r.value)), 0]);
  }
  const good = players.filter((p) => p[5] > 0).length;
  if (good < MIN_PLAYERS) throw new Error(`only ${good} players with a dynasty value`);
  if (!players.some((p) => p[6] > 0)) throw new Error("no redraft values");
  if (picks.length < 10) throw new Error(`only ${picks.length} picks`);
  const top = Math.max(0, ...players.map((p) => p[5]));
  if (!(top > 5000)) throw new Error(`top dynasty value is only ${top}`);
  return { updated, params, fields: FIELDS, pickFields: PICK_FIELDS, players, picks };
}

async function getList(query) {
  const res = await fetch(`${BASE}?${query}`, { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const rows = await res.json();
  if (!Array.isArray(rows)) throw new Error("not a list");
  return rows;
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function writeAtomic(path, obj) {
  const tmp = path + ".tmp";
  writeFileSync(tmp, JSON.stringify(obj) + "\n");
  JSON.parse(readFileSync(tmp, "utf8"));
  renameSync(tmp, path);
}

async function main() {
  mkdirSync(DIR, { recursive: true });
  const updated = new Date().toISOString();
  const manifestPath = `${DIR}/manifest.json`;
  let prev = null;
  try { prev = existsSync(manifestPath) ? JSON.parse(readFileSync(manifestPath, "utf8")) : null; } catch { prev = null; }
  const files = {}, failed = [];
  let first = true;
  for (const [qb] of QBS) for (const [ppr] of PPRS) for (const [tep] of TEPS) {
    const name = fileName(qb, ppr, tep);
    const params = { isDynasty: true, numQbs: qb, numTeams: 12, ppr, tep };
    const q = `numQbs=${qb}&numTeams=12&ppr=${ppr}&tep=${encodeURIComponent(tep)}`;
    try {
      if (!first) await sleep(DELAY_MS);
      first = false;
      const dyn = await getList(`isDynasty=true&${q}`);
      await sleep(DELAY_MS);
      const red = await getList(`isDynasty=false&${q}`);
      const file = buildFile(dyn, red, params, updated);
      writeAtomic(`${DIR}/${name}`, file);
      files[name] = { updated, numQbs: qb, ppr, tep, players: file.players.length, picks: file.picks.length };
      console.log(`${name}: ${file.players.length} players, ${file.picks.length} picks`);
    } catch (e) {
      failed.push(`${name}: ${e.message}`);
      console.error(`FAILED ${name}: ${e.message} (keeping the previous file)`);
      if (prev && prev.files && prev.files[name]) files[name] = { ...prev.files[name], stale: true };
    }
  }
  writeAtomic(manifestPath, {
    updated, source: "https://fantasycalc.com", endpoint: "GET /values/current", numTeams: 12,
    note: "Daily cache; pages map every league size to 12 teams. Rows: see each file's fields.", files, failed,
  });
  if (failed.length) { console.error(`${failed.length} format(s) failed`); process.exit(1); }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((e) => { console.error(`FantasyCalc cache failed: ${e.message}`); process.exit(1); });
}
