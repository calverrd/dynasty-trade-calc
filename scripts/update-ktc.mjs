// Scrapes KeepTradeCut dynasty rankings and writes ./ktc.json
// Step 1: plain fetch() + parse `playersArray` out of the HTML.
// Step 2 (fallback): headless Chromium via Playwright, read window.playersArray.
// Fails (non-zero exit) if fewer than MIN_PLAYERS are found, so a bad scrape
// never overwrites a good ktc.json.

import { writeFileSync } from "node:fs";

const URL = "https://keeptradecut.com/dynasty-rankings";
const OUT = "ktc.json";
const MIN_PLAYERS = 300;
const UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

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

export function normalize(raw) {
  return raw
    .filter((p) => p && p.playerName)
    .map((p) => ({
      playerName: p.playerName,
      position: p.position,
      team: p.team ?? null,
      superflexValues: valueBlock(p.superflexValues),
      oneQBValues: valueBlock(p.oneQBValues),
    }));
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
  return arr;
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
      () => {
        const a = typeof playersArray !== "undefined" ? playersArray : window.playersArray; // eslint-disable-line no-undef
        return Array.isArray(a) && a.length > 0;
      },
      null,
      { timeout: 45000 }
    );
    let arr = await page.evaluate(read);
    if (!Array.isArray(arr)) arr = extractPlayersArray(await page.content());
    if (!arr) throw new Error("playersArray not found after browser load");
    return arr;
  } finally {
    await browser.close();
  }
}

async function main() {
  let raw;
  try {
    raw = await viaFetch();
    console.log(`fetch(): found ${raw.length} entries`);
  } catch (e) {
    console.warn(`fetch() failed: ${e.message} -> trying Playwright`);
    raw = await viaPlaywright();
    console.log(`Playwright: found ${raw.length} entries`);
  }

  const players = normalize(raw);
  if (players.length < MIN_PLAYERS) {
    throw new Error(`Only ${players.length} players parsed (need ${MIN_PLAYERS}+). Not writing ${OUT}.`);
  }

  const data = { updatedAt: new Date().toISOString(), count: players.length, players };
  writeFileSync(OUT, JSON.stringify(data, null, 2) + "\n");
  console.log(`Wrote ${OUT} with ${players.length} players. Top: ${players[0].playerName}`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}
