"""Build authors.parquet: one row per author_handle with bioguide id + birthday.

Sources: unitedstates/congress-legislators (current + historical + yearly
snapshots of the social-media file, so former members' handles are covered).

Matching order:
  1. Twitter handle  -> bioguide (any snapshot of legislators-social-media.yaml)
  2. Normalized name -> bioguide, disambiguated by state (fallback)
"""
import glob, json, os, re, unicodedata
import pandas as pd
import pyarrow.parquet as pq
import yaml

SCRATCH = r"C:\Users\user\AppData\Local\Temp\claude\C--Users-user-Documents-Projects-HopHacks\78bf86ba-c937-4f2a-8841-c0f5f0cc8f1d\scratchpad"

# ---------- legislators: bioguide -> birthday, names, states ----------
cur = json.load(open(f"{SCRATCH}/legislators-current.json", encoding="utf8"))
hist = json.load(open(f"{SCRATCH}/legislators-historical.json", encoding="utf8"))
legs = {}
for l in cur + hist:
    bg = l["id"]["bioguide"]
    legs[bg] = {
        "bioguide": bg,
        "birthday": l.get("bio", {}).get("birthday"),
        "gender": l.get("bio", {}).get("gender"),
        "first": l["name"].get("first", ""),
        "last": l["name"].get("last", ""),
        "nick": l["name"].get("nickname", ""),
        "official": l["name"].get("official_full", ""),
        "states": {t["state"] for t in l["terms"]},
        "last_term_end": l["terms"][-1]["end"],
    }

# ---------- handle -> bioguide from all social-media snapshots ----------
handle2bg = {}
for f in glob.glob(f"{SCRATCH}/social-*.yaml") + [f"{SCRATCH}/legislators-social-media.json"]:
    data = yaml.safe_load(open(f, encoding="utf8")) if f.endswith(".yaml") else json.load(open(f, encoding="utf8"))
    for e in data:
        tw = (e.get("social") or {}).get("twitter")
        if tw:
            handle2bg.setdefault(tw.lower(), e["id"]["bioguide"])
print("handles known from social snapshots:", len(handle2bg))

# ---------- name normalization ----------
def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z ]", "", s.lower()).strip()

def name_keys(rec):
    """Candidate (first,last) keys for a legislator, incl. nickname."""
    keys = set()
    for fn in {rec["first"], rec["nick"], rec["official"].split(" ")[0] if rec["official"] else ""}:
        if fn:
            keys.add((norm(fn).split(" ")[0], norm(rec["last"])))
    return keys

name_index = {}
for rec in legs.values():
    for k in name_keys(rec):
        name_index.setdefault(k, []).append(rec)

SUFFIXES = {"jr", "sr", "ii", "iii", "iv"}

def parse_author_name(n):
    """Return (first, [last candidates]) from the assorted formats in the tweet data.
    Last-name candidates go from longest ('van orden') to shortest ('orden')."""
    n = re.sub(r"\s+[DRI]-[A-Z]{2}$", "", n or "").strip()   # 'Joe Barton R-TX'
    n = re.sub(r",?\s+(Jr|Sr|II|III|IV)\.?$", "", n, flags=re.I)  # 'Kean, Jr.'
    if "," in n:                                               # 'Sánchez, Linda'
        last, first = [p.strip() for p in n.split(",", 1)]
        last_parts = last.split()
    else:                                                      # 'Daniel S. Goldman'
        parts = n.split()
        if len(parts) < 2:
            return None, []
        first, last_parts = parts[0], parts[1:]
    first = norm(first).split(" ")[0] if norm(first) else None
    lasts = [norm(" ".join(last_parts[i:])) for i in range(len(last_parts))]
    return first, [l for l in lasts if l]

# ---------- authors from the tweet data ----------
t = pq.read_table("congress-tweets-unified.parquet",
                  columns=["author_handle", "author_name", "state", "chamber"]).to_pandas()
congress_chambers = {"Senate", "House", "representative", "senator"}
def mode_or_none(s):
    m = s.dropna().mode()
    return m.iloc[0] if len(m) else None

authors = (t.groupby("author_handle")
             .agg(author_name=("author_name", mode_or_none),
                  state=("state", mode_or_none),
                  is_congress=("chamber", lambda s: s.isin(congress_chambers).mean() > 0.5),
                  n_tweets=("author_name", "size"))
             .reset_index())

def match(row):
    h = row.author_handle.lower()
    if h in handle2bg:
        return handle2bg[h], "handle"
    first, lasts = parse_author_name(row.author_name)
    for last in lasts:
        cands = name_index.get((first, last), [])
        if row.state:
            cands = [c for c in cands if row.state in c["states"]]
        if len(cands) > 1:   # prefer recent members
            cands = sorted(cands, key=lambda c: c["last_term_end"], reverse=True)[:1]
        if len(cands) == 1:
            return cands[0]["bioguide"], "name"
    # last-name-only fallback within state (first-name variants like Thomas/Tom)
    for last in lasts:
        if row.state:
            cands = [c for c in legs.values() if norm(c["last"]) == last and row.state in c["states"]
                     and c["last_term_end"] >= "2005"]
            if len(cands) == 1:
                return cands[0]["bioguide"], "lastname+state"
    return None, None

authors[["bioguide", "match_method"]] = authors.apply(lambda r: pd.Series(match(r)), axis=1)
authors["birthday"] = authors.bioguide.map(lambda b: legs[b]["birthday"] if b else None)
authors["gender"] = authors.bioguide.map(lambda b: legs[b]["gender"] if b else None)
authors["birthday"] = pd.to_datetime(authors.birthday)

authors.to_parquet("authors.parquet", index=False)

# one row per term, for an "in office at tweet time" flag downstream
terms = pd.DataFrame([
    {"bioguide": l["id"]["bioguide"], "term_type": t["type"], "term_start": t["start"],
     "term_end": t["end"], "term_state": t["state"], "term_party": t.get("party")}
    for l in cur + hist for t in l["terms"]
])
terms["term_start"] = pd.to_datetime(terms.term_start); terms["term_end"] = pd.to_datetime(terms.term_end)
terms.to_parquet("terms.parquet", index=False)

c = authors[authors.is_congress]
print(f"\nCongress authors: {len(c)}  matched: {c.bioguide.notna().sum()}  "
      f"with birthday: {c.birthday.notna().sum()}")
print(c.match_method.value_counts(dropna=False))
w = c.n_tweets.sum()
print(f"tweet coverage (congress rows with birthday): {c[c.birthday.notna()].n_tweets.sum()/w:.1%}")
print("\nUnmatched congress authors (top by tweets):")
print(c[c.bioguide.isna()].sort_values("n_tweets", ascending=False)
       [["author_handle", "author_name", "state", "n_tweets"]].head(30).to_string())
