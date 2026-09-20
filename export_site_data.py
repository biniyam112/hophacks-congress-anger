"""Export the analysis results as compact JSON for the static site (site/data/)."""
import json, os
import duckdb, pandas as pd

os.makedirs("site/data", exist_ok=True)
R = lambda f: pd.read_csv(f"results/{f}")
def _default(o):
    import numpy as np
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return None if np.isnan(o) else float(o)
    raise TypeError(type(o))
def dump(name, obj):
    with open(f"site/data/{name}.json", "w", encoding="utf8") as fh:
        json.dump(obj, fh, separators=(",", ":"), ensure_ascii=False, default=_default)
    print(f"site/data/{name}.json  {os.path.getsize(f'site/data/{name}.json')//1024} KB")
r3 = lambda s: [round(float(x), 4) for x in s]

# ---- 1. year trend ----
y = R("anger_by_year.csv"); yp = R("anger_by_year_party.csv")
dump("year", {
    "year": y.year.tolist(), "anger": r3(y.anger), "se": r3(y.anger_se), "share_angry": r3(y.share_angry), "n": y.n.tolist(),
    "dem": r3(yp[yp.party == "Democrat"].set_index("year").reindex(y.year).anger),
    "rep": r3(yp[yp.party == "Republican"].set_index("year").reindex(y.year).anger),
})

# ---- out-party grid (recomputed from the parquet) ----
con = duckdb.connect()
con.execute("""CREATE VIEW d AS SELECT t.*, e.anger FROM 'tweets_enriched.parquet' t JOIN 'tweet_emotions.parquet' e USING (tweet_id)
               WHERE t.in_office AND t.year BETWEEN 2011 AND 2026""")
op = con.sql("""
SELECT party, CASE WHEN created_at < '2017-01-20' THEN 'Obama' WHEN created_at < '2021-01-20' THEN 'Trump'
                   WHEN created_at < '2025-01-20' THEN 'Biden' ELSE 'Trump II' END AS president,
       COUNT(*) n, AVG(anger) anger FROM d WHERE party IN ('Democrat','Republican') GROUP BY 1,2""").df()
pres = ["Obama", "Trump", "Biden", "Trump II"]
dump("outparty", {"president": pres, "president_party": ["D", "R", "D", "R"],
                  "dem": r3(op[op.party == "Democrat"].set_index("president").reindex(pres).anger),
                  "rep": r3(op[op.party == "Republican"].set_index("president").reindex(pres).anger)})

# ---- 2. seismograph ----
w = R("seismograph_weekly.csv"); s = R("seismograph_spikes.csv")
dump("seismograph", {
    "week": w.wk.tolist(), "anger": r3(w.anger), "dem": r3(w.anger_dem.fillna(0)), "rep": r3(w.anger_rep.fillna(0)),
    "baseline": r3(w.baseline.fillna(0)), "n": w.n.tolist(),
    "spikes": [{"week": r.wk, "anger": round(r.anger, 3), "excess": round(r.excess, 3), "event": r.event, "driven_by": r.driven_by,
                "hashtags": r.hashtags if isinstance(r.hashtags, str) else "", "example": r.example, "author": r.example_author}
               for r in s.sort_values("excess", ascending=False).itertuples()],
})

# ---- 3. time of day / month: per-year deviation curves + tweet-weighted mean ----
def curves(df, xcol, years=None):
    years = years or sorted(df.year.unique())
    xs = sorted(df[xcol].unique())
    per_year = {int(yv): [None] * len(xs) for yv in years}
    for r in df.itertuples():
        per_year[int(r.year)][xs.index(getattr(r, xcol))] = round(float(r.anger_dev), 4)
    g = df.groupby(xcol).apply(lambda t: (t.anger_dev * t.n).sum() / t.n.sum(), include_groups=False)
    return {"x": [int(v) for v in xs], "mean": r3(g.reindex(xs)), "years": per_year}
dump("hour", curves(R("anger_by_hour_year.csv"), "hour_local"))
dump("month", curves(R("anger_by_month_year.csv"), "month"))

# ---- election cycles ----
c = R("anger_by_cycle_week.csv"); cp = R("anger_by_cycle_week_party.csv")
cycles = {}
for cy, g in c.groupby("cycle"):
    g = g.sort_values("weeks_to_election")
    d = cp[(cp.cycle == cy) & (cp.party == "Democrat")].set_index("weeks_to_election").reindex(g.weeks_to_election)
    rr = cp[(cp.cycle == cy) & (cp.party == "Republican")].set_index("weeks_to_election").reindex(g.weeks_to_election)
    cycles[int(cy)] = {"weeks": g.weeks_to_election.tolist(), "anger": r3(g.anger),
                       "dem": [None if pd.isna(v) else round(float(v), 4) for v in d.anger],
                       "rep": [None if pd.isna(v) else round(float(v), 4) for v in rr.anger]}
final = con.sql("""SELECT year, AVG(CASE WHEN days_to_election <= 28 THEN anger END) last4, AVG(CASE WHEN days_to_election > 28 THEN anger END) rest
                   FROM d WHERE is_election_year AND year < 2026 GROUP BY 1 ORDER BY 1""").df()
dump("cycle", {"cycles": cycles, "final": {"year": final.year.tolist(), "last4": r3(final.last4), "rest": r3(final.rest)}})

# ---- 4. age ----
sl = R("anger_age_slope_by_year.csv"); gen = R("anger_by_generation_year.csv"); wp = R("anger_age_within_person.csv").iloc[0]
ab = R("anger_by_age_year.csv")
gens = ["Silent", "Boomer", "Gen X", "Millennial", "Gen Z"]
dump("age", {
    "slope": {"year": sl.year.tolist(), "raw": r3(sl.slope_per_decade), "se": r3(sl.se), "adj": r3(sl.slope_per_decade_party_adj), "p": r3(sl.p)},
    "generation": {"year": sorted(gen.year.unique()),
                   **{g: [None if pd.isna(v) else round(float(v), 4) for v in gen[gen.generation == g].set_index("year").reindex(sorted(gen.year.unique())).anger_dev] for g in gens}},
    "within_person": {k: (None if pd.isna(v) else round(float(v), 4)) for k, v in wp.items()},
    "brackets": {"year": sorted(ab.year.unique()), "age": sorted(ab.age_bracket.unique()),
                 "dev": [[None if pd.isna(v) else round(float(v), 4) for v in ab.pivot(index="age_bracket", columns="year", values="anger_dev").reindex(sorted(ab.age_bracket.unique())).loc[a]] for a in sorted(ab.age_bracket.unique())]},
    "party_age": con.sql("""SELECT year, AVG(CASE WHEN party='Democrat' THEN age_at_tweet END) dem, AVG(CASE WHEN party='Republican' THEN age_at_tweet END) rep
                            FROM d GROUP BY 1 ORDER BY 1""").df().round(1).to_dict(orient="list"),
})

# ---- headline numbers ----
tot = con.sql("SELECT COUNT(*) n, COUNT(DISTINCT bioguide) members, MIN(created_at)::DATE a, MAX(created_at)::DATE b FROM d").fetchone()
dump("meta", {"tweets": tot[0], "members": tot[1], "from": str(tot[2]), "to": str(tot[3])})

# ---- 5. the anger forecast ----
lad = R("forecast_ladder.csv"); mem = R("forecast_members.csv"); meh = R("forecast_member_era_hour.csv"); owl = R("forecast_night_owls.csv")
clean = lambda n: __import__("re").sub(r"\s+[DRI]-[A-Z]{2}$", "", n)
dump("forecast", {
    "baseline": round(float(lad.p.iloc[0]), 4),
    "ladder": [{"known": k, "p": round(float(p), 4)} for k, p in zip(lad.known, lad.p)],
    "angriest": [{"name": clean(r.name), "party": r.party, "state": r.state, "n": int(r.n), "p": round(float(r.share_angry), 3)} for r in mem.head(10).itertuples()],
    "calmest": [{"name": clean(r.name), "party": r.party, "state": r.state, "n": int(r.n), "p": round(float(r.share_angry), 3)} for r in mem.tail(8).iloc[::-1].itertuples()],
    "predictable": [{"name": clean(r.name), "party": r.party, "era": r.era, "band": r.band, "n": int(r.n), "p": round(float(r.share_angry), 3)} for r in meh.head(10).itertuples()],
    "owls": [{"name": clean(r.name), "party": r.party, "day": round(float(r.daytime), 3), "night": round(float(r.nighttime), 3)} for r in owl.head(6).itertuples()],
    "larks": [{"name": clean(r.name), "party": r.party, "day": round(float(r.daytime), 3), "night": round(float(r.nighttime), 3)} for r in owl.tail(4).iloc[::-1].itertuples()],
})

# ---- 6. the loudest people in Congress (prolific tweeters and their anger share) ----
mv = R("member_volume_vs_anger.csv")
nm = con.sql("SELECT bioguide, ARG_MAX(author_name, created_at) AS nm, ARG_MAX(state, created_at) AS st FROM 'tweets_enriched.parquet' WHERE in_office GROUP BY 1").df()
mv = mv.merge(nm, on="bioguide"); mv["nm"] = mv.nm.str.replace(r"\s+[DRI]-[A-Z]{2}$", "", regex=True)
top = mv[mv.n >= 2000].sort_values("tweets_per_year", ascending=False).head(12)
base_share = float(con.sql("SELECT AVG((anger > 0.5)::INT) FROM d").fetchone()[0])
dump("loudest", {"baseline": round(base_share, 3), "median_per_day": round(float(mv.tweets_per_day.median()), 2),
    "members": [{"name": r.nm, "party": r.party, "state": r.st, "per_day": round(float(r.tweets_per_day), 2), "per_year": int(round(r.tweets_per_year)),
                 "n": int(r.n), "p": round(float(r.share_angry), 3)} for r in top.itertuples()]})
