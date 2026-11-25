"""List SportsDataverse / nflverse release assets and print the columns of a sample file from each
college-football release, so the pre-draft pipeline can be written against the real schemas."""
import io, json, os, sys, urllib.request
import pandas as pd

TOKEN = os.environ.get("GITHUB_TOKEN", "")


def gh(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})})
    return json.load(urllib.request.urlopen(req, timeout=60))


def releases(repo):
    out, page = [], 1
    while True:
        r = gh(f"https://api.github.com/repos/{repo}/releases?per_page=100&page={page}")
        if not r:
            return out
        out += r
        page += 1


def sample(url):
    data = urllib.request.urlopen(url, timeout=120).read()
    if url.endswith(".parquet"):
        df = pd.read_parquet(io.BytesIO(data))
    elif url.endswith(".csv") or url.endswith(".csv.gz"):
        df = pd.read_csv(io.BytesIO(data), compression="gzip" if url.endswith(".gz") else None, low_memory=False)
    else:
        return None
    return df


for repo in ("sportsdataverse/sportsdataverse-data", "sportsdataverse/cfbfastR-data"):
    try:
        rs = releases(repo)
    except Exception as e:
        print(f"## {repo}: {e}")
        continue
    print(f"## {repo}: {len(rs)} releases")
    for r in rs:
        names = [a["name"] for a in r.get("assets", [])]
        print(f"- {r['tag_name']}: {len(names)} assets, e.g. {names[:4]} ... {names[-3:]}")
        tag = r["tag_name"].lower()
        if any(k in tag for k in ("cfb", "college", "ncaaf")) and any(k in tag for k in ("player", "team", "box", "rating", "roster", "stat")):
            pq = [a for a in r["assets"] if a["name"].endswith((".parquet", ".csv", ".csv.gz")) and "2019" in a["name"]] or \
                 [a for a in r["assets"] if a["name"].endswith((".parquet", ".csv", ".csv.gz"))]
            if pq:
                try:
                    df = sample(pq[0]["browser_download_url"])
                    print(f"    sample {pq[0]['name']}: {df.shape} cols={list(df.columns)[:80]}")
                    print("    head:", df.head(2).to_dict("records"))
                except Exception as e:
                    print(f"    sample failed: {e}")

print("## nflverse combine")
r = gh("https://api.github.com/repos/nflverse/nflverse-data/releases/tags/combine")
for a in r["assets"][:6]:
    print("-", a["name"])
csv = [a for a in r["assets"] if a["name"].endswith(".csv")]
if csv:
    df = sample(csv[0]["browser_download_url"])
    print("combine", df.shape, list(df.columns))
