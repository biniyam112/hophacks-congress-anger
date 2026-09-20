"""Anger vs representative age — compared only within the same year, never across years.

Design
  * age bracket x year cells (5-year brackets, in-office tweets only).
  * Within each year, anger for a bracket is reported both raw and as deviation from
    that year's mean, so brackets are only ever compared to their contemporaries.
  * Per-year slope: OLS of anger on age within each year -> is the sign stable year to year?
  * Generations x year (Silent / Boomer / Gen X / Millennial / Gen Z) for the website copy.
  * Within-person: for members with >= 6 years of tweets, does their own anger rise with age,
    after removing the year effect? (separates "older = angrier" from "angry members stay longer")
  * Party x age within year.

Reads tweets_enriched.parquet + emotion labels (sample file if that's all we have).
"""
import os, sys
import duckdb, numpy as np, pandas as pd
import statsmodels.formula.api as smf
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

EMO = (sys.argv[1] if len(sys.argv) > 1 else
       "tweet_emotions.parquet" if os.path.exists("tweet_emotions.parquet") else "tweet_emotions_sample.parquet")
MIN_N = 200 if "sample" not in EMO else 30
os.makedirs("results", exist_ok=True); os.makedirs("figures", exist_ok=True)

con = duckdb.connect()
con.execute(f"""
CREATE VIEW d AS
SELECT t.tweet_id, t.bioguide, t.author_name, t.party, t.chamber, t.year, t.age_at_tweet, t.birthday,
       (FLOOR(t.age_at_tweet / 5) * 5)::INT AS age_bracket,
       CASE WHEN EXTRACT(year FROM t.birthday) <= 1945 THEN 'Silent'
            WHEN EXTRACT(year FROM t.birthday) <= 1964 THEN 'Boomer'
            WHEN EXTRACT(year FROM t.birthday) <= 1980 THEN 'Gen X'
            WHEN EXTRACT(year FROM t.birthday) <= 1996 THEN 'Millennial' ELSE 'Gen Z' END AS generation,
       e.anger, e.disgust, e.joy, e.optimism, e.negative, (e.anger > 0.5)::INT AS is_angry
FROM 'tweets_enriched.parquet' t JOIN '{EMO}' e USING (tweet_id)
WHERE t.in_office AND t.year BETWEEN 2011 AND 2026 AND t.age_at_tweet BETWEEN 25 AND 95
""")
print(f"using {EMO}: {con.sql('SELECT COUNT(*) FROM d').fetchone()[0]:,} in-office labeled tweets")

def dev_within(df, within, col="anger"):
    """anger minus the tweet-weighted mean of the same `within` group."""
    within = [within] if isinstance(within, str) else list(within)
    base = (df.groupby(within).apply(lambda g: np.average(g[col], weights=g.n), include_groups=False)
              .rename("_base").reset_index())
    df = df.merge(base, on=within, how="left")
    df[f"{col}_dev"] = df[col] - df["_base"]
    return df.drop(columns="_base")

# ---------- 1. age bracket x year ----------
ab = con.sql(f"""
    SELECT year, age_bracket, COUNT(*) n, COUNT(DISTINCT bioguide) members,
           AVG(anger) anger, AVG(is_angry) share_angry, AVG(negative) negative, AVG(joy) joy,
           STDDEV(anger)/SQRT(COUNT(*)) anger_se
    FROM d GROUP BY 1,2 HAVING COUNT(*) >= {MIN_N} ORDER BY 1,2""").df()
ab = dev_within(ab, "year"); ab.to_csv("results/anger_by_age_year.csv", index=False)

gen = con.sql(f"""
    SELECT year, generation, COUNT(*) n, COUNT(DISTINCT bioguide) members, AVG(anger) anger, AVG(is_angry) share_angry
    FROM d GROUP BY 1,2 HAVING COUNT(*) >= {MIN_N} ORDER BY 1,2""").df()
gen = dev_within(gen, "year"); gen.to_csv("results/anger_by_generation_year.csv", index=False)

abp = con.sql(f"""
    SELECT year, party, age_bracket, COUNT(*) n, AVG(anger) anger
    FROM d WHERE party IN ('Democrat','Republican') GROUP BY 1,2,3 HAVING COUNT(*) >= {MIN_N} ORDER BY 1,2,3""").df()
abp = dev_within(abp, ["year", "party"]); abp.to_csv("results/anger_by_age_year_party.csv", index=False)

# ---------- 2. per-year slope of anger on age (tweet-level OLS, SE clustered by member) ----------
rows = []
for y in sorted(ab.year.unique()):
    dy = con.sql(f"SELECT anger, age_at_tweet, party, bioguide FROM d WHERE year = {y} AND party IS NOT NULL").df()
    if len(dy) < 1000: continue
    m = smf.ols("anger ~ age_at_tweet", dy).fit(cov_type="cluster", cov_kwds={"groups": dy.bioguide})
    mp = smf.ols("anger ~ age_at_tweet + C(party)", dy).fit(cov_type="cluster", cov_kwds={"groups": dy.bioguide})
    rows.append({"year": y, "n": len(dy), "members": dy.bioguide.nunique(),
                 "slope_per_decade": 10 * m.params["age_at_tweet"], "se": 10 * m.bse["age_at_tweet"], "p": m.pvalues["age_at_tweet"],
                 "slope_per_decade_party_adj": 10 * mp.params["age_at_tweet"], "p_party_adj": mp.pvalues["age_at_tweet"]})
slopes = pd.DataFrame(rows); slopes.to_csv("results/anger_age_slope_by_year.csv", index=False)

# ---------- 3. within-person: same member, does anger rise with age net of the year effect? ----------
# Outcome is anger relative to that year's mean (so the common year trend is removed non-parametrically),
# with member fixed effects, so the age coefficient comes only from the same member getting older.
# NB: member FE + year FE + age would be unidentified (age = year - birth year); this design is the
# identifiable version. Within a member, age and seniority accrue together and cannot be separated.
wp = con.sql(f"""
    WITH y AS (SELECT year, AVG(anger) ymean FROM d GROUP BY 1)
    SELECT bioguide, d.year, AVG(anger - ymean) anger_dev, AVG(age_at_tweet) age, COUNT(*) n, ANY_VALUE(party) party
    FROM d JOIN y USING (year) GROUP BY 1,2 HAVING COUNT(*) >= {MIN_N // 4}""").df()
span = wp.groupby("bioguide").year.agg(["min", "max", "count"])
keep = span[(span["max"] - span["min"] >= 5) & (span["count"] >= 6)].index
wp = wp[wp.bioguide.isin(keep)]
within = {"members": len(keep), "member_years": len(wp), "slope_per_decade": np.nan, "se": np.nan, "p": np.nan}
if len(keep) >= 20:
    fe = smf.wls("anger_dev ~ age + C(bioguide)", wp, weights=wp.n).fit(
        cov_type="cluster", cov_kwds={"groups": wp.bioguide})
    within.update(slope_per_decade=10 * fe.params["age"], se=10 * fe.bse["age"], p=fe.pvalues["age"])
pd.DataFrame([within]).to_csv("results/anger_age_within_person.csv", index=False)

# ---------- figures ----------
years = sorted(ab.year.unique()); cmap = plt.get_cmap("viridis")
colr = {y: cmap(i / max(1, len(years) - 1)) for i, y in enumerate(years)}

fig, axes = plt.subplots(1, 3, figsize=(17, 4.6))
for y in years:
    s = ab[ab.year == y]; axes[0].plot(s.age_bracket + 2.5, s.anger_dev, color=colr[y], marker=".", lw=1.2, label=str(y))
axes[0].axhline(0, color="grey", lw=0.8); axes[0].legend(ncol=2, fontsize=7)
axes[0].set(title="Anger by age bracket, deviation from same-year mean", xlabel="age at tweet", ylabel="Δ anger")

axes[1].errorbar(slopes.year, slopes.slope_per_decade, yerr=1.96 * slopes.se, marker="o", color="k", label="raw")
axes[1].plot(slopes.year, slopes.slope_per_decade_party_adj, marker="s", ls="--", color="tab:purple", label="party-adjusted")
axes[1].axhline(0, color="grey", lw=0.8); axes[1].legend()
axes[1].set(title="Within-year slope: Δ anger per +10 years of age", xlabel="year")

gens = ["Silent", "Boomer", "Gen X", "Millennial", "Gen Z"]
for g, c in zip(gens, ["tab:gray", "tab:brown", "tab:green", "tab:orange", "tab:pink"]):
    s = gen[gen.generation == g]
    if len(s): axes[2].plot(s.year, s.anger_dev, marker=".", color=c, label=g)
axes[2].axhline(0, color="grey", lw=0.8); axes[2].legend()
axes[2].set(title="Generations, deviation from same-year mean", xlabel="year")
fig.tight_layout(); fig.savefig("figures/anger_by_age.png", dpi=130)

# ---------- console ----------
pd.set_option("display.width", 200)
print("\nage bracket x year (Δ from year mean):")
print(ab.pivot(index="age_bracket", columns="year", values="anger_dev").round(3).to_string())
print("\nper-year slope (Δ anger per decade of age):\n", slopes.round(4).to_string(index=False))
print(f"\nwithin-person (member FE, outcome = deviation from year mean): {within}")
print("\ngenerations (Δ from year mean):")
print(gen.pivot(index="generation", columns="year", values="anger_dev").reindex(gens).round(3).to_string())
