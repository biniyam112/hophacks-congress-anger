"""Uniting vs. dividing: which party tweets civic unity, which tweets at the other side, and how far apart
the parties *feel* (distance between their 11-emotion profiles) — by year and by month.

Definitions (a tweet can be several of these):
  civic unity   positive tone (joy/optimism/love/trust > 0.5, no anger/disgust > 0.5) AND explicit cross-party language
                (bipartisan, across the aisle, both parties/sides, common ground, work/come together, unity/unite, reach across)
  gratitude     positive tone AND thanks/proud/honored/grateful language (the ribbon-cutting register; reported separately)
  polarizing    negative tone (anger or disgust > 0.5) AND a reference to the other party or its leaders
Outputs results/unity_*.csv and site/data/unity.json.
"""
import json
import duckdb, numpy as np, pandas as pd

CIVIC = r"(bipartisan|across the aisle|both parties|both sides of the aisle|common ground|work(ing|ed)? together|come together|came together|\bunity\b|\bunite[ds]?\b|reach(ing|ed)? across)"
GRATITUDE = r"(thank you|thanks to|proud to|honored to|honoured to|grateful)"
DEM_OUT = r"(republican|\bgop\b|\bmaga\b|trump|mcconnell|speaker johnson|boehner|paul ryan|the right\b|far-right|extremist)"
REP_OUT = r"(democrat|\bdems?\b|\bdnc\b|biden|obama|pelosi|schumer|kamala|harris|the left\b|far-left|socialist|radical|liberal)"
EMOTIONS = ["anger", "disgust", "fear", "sadness", "joy", "optimism", "love", "trust", "anticipation", "pessimism", "surprise"]

con = duckdb.connect()
con.execute(f"""
CREATE VIEW d AS
SELECT t.party, t.year, date_trunc('month', t.created_at)::DATE AS mo, lower(t.text) AS txt, {", ".join("e." + c for c in EMOTIONS)},
       (e.joy > 0.5 OR e.optimism > 0.5 OR e.love > 0.5 OR e.trust > 0.5) AND e.anger <= 0.5 AND e.disgust <= 0.5 AS positive,
       (e.anger > 0.5 OR e.disgust > 0.5) AS negative,
       regexp_matches(lower(t.text), '{CIVIC}') AS civic_lang,
       regexp_matches(lower(t.text), '{GRATITUDE}') AS grat_lang,
       CASE WHEN t.party = 'Democrat' THEN regexp_matches(lower(t.text), '{DEM_OUT}')
            WHEN t.party = 'Republican' THEN regexp_matches(lower(t.text), '{REP_OUT}') ELSE FALSE END AS outgroup
FROM 'tweets_enriched.parquet' t JOIN 'tweet_emotions.parquet' e USING (tweet_id)
WHERE t.in_office AND t.year BETWEEN 2011 AND 2026 AND t.party IN ('Democrat','Republican')""")

SHARES = """COUNT(*) n, AVG((positive AND civic_lang)::INT) civic, AVG((positive AND grat_lang)::INT) gratitude,
            AVG((negative AND outgroup)::INT) polarizing, AVG(civic_lang::INT) any_civic_lang, AVG(outgroup::INT) any_outgroup"""
by_year = con.sql(f"SELECT year, party, {SHARES} FROM d GROUP BY 1,2 ORDER BY 1,2").df()
by_month = con.sql(f"SELECT mo, party, {SHARES} FROM d GROUP BY 1,2 ORDER BY 1,2").df()
by_year.to_csv("results/unity_by_year_party.csv", index=False); by_month.to_csv("results/unity_by_month_party.csv", index=False)

# ---- emotional distance between the parties' mean-emotion profiles ----
def distance(df, key):
    rows = []
    for k, g in df.groupby(key):
        if set(g.party) != {"Democrat", "Republican"}:
            continue
        a = g[g.party == "Democrat"][EMOTIONS].values[0]; b = g[g.party == "Republican"][EMOTIONS].values[0]
        gap = a - b
        rows.append({key: k, "distance": float(np.linalg.norm(gap)), "biggest_gap": EMOTIONS[int(np.argmax(np.abs(gap)))],
                     "gap_sign": "Democrats higher" if gap[int(np.argmax(np.abs(gap)))] > 0 else "Republicans higher",
                     **{f"gap_{e}": float(v) for e, v in zip(EMOTIONS, gap)}})
    return pd.DataFrame(rows)
q = ", ".join(f"AVG({c}) {c}" for c in EMOTIONS)
dist_year = distance(con.sql(f"SELECT year, party, {q} FROM d GROUP BY 1,2").df(), "year").sort_values("year")
dist_month = distance(con.sql(f"SELECT mo, party, {q} FROM d GROUP BY 1,2 HAVING COUNT(*) >= 2000").df(), "mo").sort_values("mo")
dist_year.to_csv("results/unity_distance_by_year.csv", index=False); dist_month.to_csv("results/unity_distance_by_month.csv", index=False)

# ---- calendar: most uniting / most polarizing months (both parties pooled) ----
cal = con.sql(f"SELECT mo, {SHARES} FROM d GROUP BY 1 HAVING COUNT(*) >= 5000").df()
EVENTS = {  # hand labels for the extremes, from the news of the month
    "2021-11-01": "Bipartisan infrastructure bill signed", "2024-11-01": "Post-election; Thanksgiving",
    "2019-05-01": "Memorial Day; disaster-aid deal", "2019-08-01": "August recess",
    "2024-05-01": "Memorial Day; FAA & farm bills", "2022-08-01": "CHIPS Act; PACT Act for veterans",
    "2024-10-01": "Hurricanes Helene & Milton", "2013-04-01": "Boston Marathon bombing",
    "2025-10-01": "Government shutdown (Oct 1)", "2025-11-01": "Shutdown ends after 43 days",
    "2025-03-01": "DOGE cuts; CR fight", "2025-09-01": "Shutdown looms; Kirk assassination",
    "2025-07-01": "'One Big Beautiful Bill' passes", "2025-04-01": "Tariffs; market crash",
    "2017-01-01": "Inauguration; travel ban", "2021-01-01": "January 6",
    "2021-12-01": "Debt-ceiling deal; NDAA passes", "2023-10-01": "Speaker Johnson elected; Israel resolutions",
    "2020-12-01": "COVID relief deal after months of stalemate", "2022-02-01": "Russia invades Ukraine — bipartisan support",
    "2019-02-01": "35-day shutdown ends; border deal", "2022-01-01": "Jan 6 anniversary; Ukraine build-up",
    "2025-02-01": "DOGE; funding fights begin", "2025-05-01": "'Big Beautiful Bill' in the House",
}
cal["event"] = cal.mo.astype(str).map(EVENTS).fillna("")
cal.to_csv("results/unity_calendar.csv", index=False)

pd.set_option("display.width", 220)
print(by_year.pivot(index="year", columns="party", values=["civic", "gratitude", "polarizing"]).round(3).to_string())
print("\n", dist_year[["year", "distance", "biggest_gap", "gap_sign"]].round(3).to_string(index=False))
print("\nmost civic months:\n", cal.sort_values("civic", ascending=False).head(8)[["mo", "civic", "polarizing", "event"]].round(3).to_string(index=False))
print("most polarizing months:\n", cal.sort_values("polarizing", ascending=False).head(8)[["mo", "civic", "polarizing", "event"]].round(3).to_string(index=False))

# ---- site export ----
years = sorted(by_year.year.unique())
def series(df, party, col): return [round(float(v), 4) for v in df[df.party == party].set_index("year").reindex(years)[col]]
json.dump({
    "year": [int(y) for y in years],
    "civic": {"dem": series(by_year, "Democrat", "civic"), "rep": series(by_year, "Republican", "civic")},
    "gratitude": {"dem": series(by_year, "Democrat", "gratitude"), "rep": series(by_year, "Republican", "gratitude")},
    "polarizing": {"dem": series(by_year, "Democrat", "polarizing"), "rep": series(by_year, "Republican", "polarizing")},
    "distance": {"year": [int(y) for y in dist_year.year], "d": [round(float(v), 4) for v in dist_year.distance],
                 "gap": dist_year.biggest_gap.tolist(), "sign": dist_year.gap_sign.tolist()},
    "distance_month": {"mo": dist_month.mo.astype(str).tolist(), "d": [round(float(v), 4) for v in dist_month.distance]},
    "calendar": {"uniting": cal.sort_values("civic", ascending=False).head(8)[["mo", "civic", "polarizing", "event"]].assign(mo=lambda x: x.mo.astype(str)).round(4).to_dict(orient="records"),
                 "polarizing": cal.sort_values("polarizing", ascending=False).head(8)[["mo", "civic", "polarizing", "event"]].assign(mo=lambda x: x.mo.astype(str)).round(4).to_dict(orient="records")},
}, open("site/data/unity.json", "w", encoding="utf8"), separators=(",", ":"))
print("\nsite/data/unity.json written")
