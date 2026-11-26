"""SUPERSEDED by scripts/build_buckets.py (builds the matrix AND the bucket cards from one source). Kept for reference.

Build the Profile Bucket matrix dataset from the owner's Hit Rates spreadsheet (the bucket summary rows).

Usage: python scripts/build_matrix.py "Updated Hit Rates.xlsx" > /tmp/matrix.json
Then paste the JSON into `const BUCKET_MATRIX = ...` in bucket-explorer.html (one line).
Sections: QB, RB, WR (raw), WR (size-adjusted; the one the bucket cards use), TE. Errors such as #DIV/0! become null.
"""
import json, sys
import openpyxl

SECTIONS = [  # header text in column A -> key, marks (PPG columns H..), hit mark index, notes
    ("QB", "QB", ["16+", "20+", "24+"], 1),
    ("RB", "RB", ["12+", "15+", "18+"], 1),
    ("WR", "WR_RAW", ["12+", "14+", "16+", "18+"], 1),
    ("WR (Size-Adjusted)", "WR", ["12+", "14+", "16+", "18+"], 1),
    ("TE", "TE", ["12+", "14+", "17+"], 0),
]

def num(v):
    return round(float(v), 4) if isinstance(v, (int, float)) else None

def main(path):
    ws = openpyxl.load_workbook(path, data_only=True)["Updated Hit Rates"]
    starts = {}
    for r in range(1, ws.max_row + 1):
        if ws.cell(r, 2).value == "Year":
            starts[str(ws.cell(r, 1).value).strip()] = r
    order = sorted(starts.values())
    out = {}
    for head, key, marks, hit_i in SECTIONS:
        st = starts[head]
        en = next((x for x in order if x > st), ws.max_row + 1)
        rows, tier_overall = [], {}
        for r in range(st + 1, en):
            a, b, tot = ws.cell(r, 1).value, ws.cell(r, 2).value, ws.cell(r, 5).value
            if not a or b is not None or not isinstance(tot, (int, float)):
                continue
            name = str(a).strip()
            tier = name.split(" ")[0]
            if num(ws.cell(r, 6).value) is not None:
                tier_overall[tier] = num(ws.cell(r, 6).value)
            rates = [num(ws.cell(r, 8 + i).value) for i in range(len(marks))]
            rows.append({
                "name": name, "tier": tier,
                "hitRate": num(ws.cell(r, 3).value), "hits": int(num(ws.cell(r, 4).value) or 0), "n": int(tot),
                "rates": rates,
                "low2": num(ws.cell(r, 13).value), "low3": num(ws.cell(r, 14).value), "lowRep": num(ws.cell(r, 15).value),
                "hit2": num(ws.cell(r, 16).value), "hitRep": num(ws.cell(r, 17).value),
            })
        for x in rows:
            x["tierOverall"] = tier_overall.get(x["tier"])
        lowMark = marks[0]
        hitMark = marks[hit_i] if key != "TE" else "14+"
        out[key] = {"marks": marks, "lowMark": lowMark, "hitMark": marks[hit_i], "rep2Mark": marks[1] if key == "TE" else marks[hit_i], "rows": rows}
    json.dump(out, sys.stdout, separators=(",", ":"))

if __name__ == "__main__":
    main(sys.argv[1])
