"""Daily name check: current-class rookies on the rookie tabs that KTC or FantasyCalc can't be matched to by name.

A missed match silently drops that source (the player falls back to KTC only, or shows no value). Uses the same key
as every page: position + the name with only letters left, suffixes (Jr, Sr, II, III, IV, V) dropped.
Prints the misses to the workflow log; never fails the run.  Usage: python3 scripts/check_names.py [repo root]
"""
import json, re, sys, unicodedata
ROOT = sys.argv[1] if len(sys.argv) > 1 else "."

def key(name):
    s = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b\.?", "", s)
    return re.sub(r"[^a-z]", "", s)

def main():
    ktc = json.load(open(f"{ROOT}/ktc.json"))
    knames = [(p.get("position"), p.get("playerName")) for p in ktc.get("players", [])]
    kset = {f"{pos}|{key(n)}" for pos, n in knames}
    fc = json.load(open(f"{ROOT}/data/fc/fc-sf-ppr1-none.json"))
    c = {x: i for i, x in enumerate(fc["fields"])}
    fnames = [(r[c["pos"]], r[c["name"]]) for r in fc["players"]]
    fset = {f"{pos}|{key(n)}" for pos, n in fnames}
    last = lambda n: key(re.sub(r"\b(jr|sr|ii|iii|iv|v)\b\.?", "", str(n), flags=re.I).split()[-1] if str(n).split() else "")
    def hint(pos, n, names):   # same position, last name and first initial = probably a nickname / spelling difference
        m = [x for p_, x in names if p_ == pos and last(x) == last(n) and key(x)[:1] == key(n)[:1] and key(x) != key(n)]
        return f" (maybe {', '.join(m)})" if m else ""
    for pos, f in (("WR", "rookie-wr-tracker.html"), ("RB", "rookie-rb-tracker.html"), ("TE", "rookie-te-tracker.html")):
        rows = json.loads(re.search(r"const DATA = (\[.*?\]);\n", open(f"{ROOT}/{f}", encoding="utf-8").read(), re.S).group(1))
        cls = max(r["yr"] for r in rows)
        cur = [r for r in rows if r["yr"] == cls]
        no_k = [r["n"] for r in cur if f"{pos}|{key(r['n'])}" not in kset]
        no_f = [r["n"] for r in cur if f"{pos}|{key(r['n'])}" not in fset]
        both = [n for n in no_k if n in no_f]
        print(f"{pos} {cls}: {len(cur)} rookies · not in KTC {len(no_k)} · not in FantasyCalc {len(no_f)} (KTC only) · in neither {len(both)}")
        if no_k: print(f"  not in KTC: {', '.join(n + hint(pos, n, knames) for n in no_k)}")
        if no_f: print(f"  not in FantasyCalc: {', '.join(n + hint(pos, n, fnames) for n in no_f if n not in both)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:   # a report, never a blocker
        print("name check skipped:", e)
