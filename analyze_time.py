"""Anger vs time-of-day, season, and election cycle — each year / cycle kept separate.

Reads tweets_enriched.parquet + whatever emotion chunks exist in emotions/ (or tweet_emotions.parquet).
Writes tidy aggregates to results/ (for the website) and quick-look PNGs to figures/.

Anger metric: mean P(anger) from the emotion model. Within-year curves are shown as
deviation from that year's mean, so the shape isn't swamped by the secular trend.
"""
import os, sys
import duckdb, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.makedirs("results", exist_ok=True); os.makedirs("figures", exist_ok=True)
EMO = (sys.argv[1] if len(sys.argv) > 1 else
       "tweet_emotions.parquet" if os.path.exists("tweet_emotions.parquet") else "emotions/chunk_*.parquet")
IS_SAMPLE = "sample" in EMO
MIN_N = 30 if IS_SAMPLE else 300   # min tweets per cell to report
print("labels:", EMO)

con = duckdb.connect()
con.execute(f"""
CREATE VIEW d AS
SELECT t.*, e.anger, e.disgust, e.joy, e.optimism, e.fear, e.sadness, e.negative, e.positive,
       (e.anger > 0.5)::INT AS is_angry
FROM 'tweets_enriched.parquet' t JOIN '{EMO}' e USING (tweet_id)
WHERE t.in_office AND t.year BETWEEN 2011 AND 2026
""")
n = con.sql("SELECT COUNT(*) FROM d").fetchone()[0]
print(f"labeled in-office tweets: {n:,}")

def agg(group_cols, where="TRUE"):
    cols = ", ".join(group_cols)
    return con.sql(f"""
        SELECT {cols}, COUNT(*) n, AVG(anger) anger, AVG(is_angry) share_angry, AVG(negative) negative,
               AVG(disgust) disgust, AVG(joy) joy, AVG(optimism) optimism, AVG(fear) fear, AVG(sadness) sadness,
               STDDEV(anger)/SQRT(COUNT(*)) anger_se
        FROM d WHERE {where} GROUP BY {cols} HAVING COUNT(*) >= {MIN_N} ORDER BY {cols}""").df()

def add_deviation(df, within, col="anger"):
    """anger minus the tweet-weighted mean of the same `within` group."""
    within = [within] if isinstance(within, str) else list(within)
    base = (df.groupby(within).apply(lambda g: np.average(g[col], weights=g.n), include_groups=False)
              .rename("_base").reset_index())
    df = df.merge(base, on=within, how="left")
    df[f"{col}_dev"] = df[col] - df["_base"]
    return df.drop(columns="_base")

# ---------- 0. baseline: anger by year (the secular trend the other panels are normalised against) ----------
by_year = agg(["year"]); by_year_party = agg(["year", "party"], "party IN ('Democrat','Republican')")
by_year.to_csv("results/anger_by_year.csv", index=False); by_year_party.to_csv("results/anger_by_year_party.csv", index=False)

# ---------- 1. time of day, one curve per year ----------
hod = add_deviation(agg(["year", "hour_local"]), "year")
hod.to_csv("results/anger_by_hour_year.csv", index=False)
hod_party = add_deviation(agg(["year", "party", "hour_local"], "party IN ('Democrat','Republican')"), ["year", "party"])
hod_party.to_csv("results/anger_by_hour_year_party.csv", index=False)
dow = add_deviation(agg(["year", "dow_et"]), "year"); dow.to_csv("results/anger_by_dow_year.csv", index=False)

# ---------- 2. season / month, one curve per year ----------
mon = add_deviation(agg(["year", "month"]), "year"); mon.to_csv("results/anger_by_month_year.csv", index=False)
sea = add_deviation(agg(["year", "season"]), "year"); sea.to_csv("results/anger_by_season_year.csv", index=False)

# ---------- 3. election cycle: weekly anger vs days-to-election, one curve per cycle ----------
cyc = con.sql(f"""
    SELECT EXTRACT(year FROM next_election)::INT AS cycle, (days_to_election // 7)::INT AS weeks_to_election,
           COUNT(*) n, AVG(anger) anger, AVG(is_angry) share_angry, AVG(negative) negative
    FROM d GROUP BY 1,2 HAVING COUNT(*) >= {MIN_N} ORDER BY 1,2""").df()
cyc = add_deviation(cyc, "cycle"); cyc.to_csv("results/anger_by_cycle_week.csv", index=False)
cyc_party = con.sql(f"""
    SELECT EXTRACT(year FROM next_election)::INT AS cycle, party, (days_to_election // 7)::INT AS weeks_to_election,
           COUNT(*) n, AVG(anger) anger FROM d WHERE party IN ('Democrat','Republican')
    GROUP BY 1,2,3 HAVING COUNT(*) >= {MIN_N} ORDER BY 1,2,3""").df()
cyc_party.to_csv("results/anger_by_cycle_week_party.csv", index=False)
ey = agg(["year", "is_election_year", "is_presidential"]); ey.to_csv("results/anger_election_vs_off_year.csv", index=False)

# ================= quick-look figures =================
years = sorted(hod.year.unique()); cmap = plt.get_cmap("viridis")
colr = {y: cmap(i / max(1, len(years) - 1)) for i, y in enumerate(years)}

fig, ax = plt.subplots(figsize=(9, 4))
ax.errorbar(by_year.year, by_year.anger, yerr=1.96 * by_year.anger_se, marker="o", color="k", label="all")
for p, c in [("Democrat", "tab:blue"), ("Republican", "tab:red")]:
    s = by_year_party[by_year_party.party == p]; ax.plot(s.year, s.anger, marker=".", color=c, label=p)
ax.set(title="Mean P(anger) by year", xlabel="year", ylabel="mean anger"); ax.legend(); fig.tight_layout()
fig.savefig("figures/anger_by_year.png", dpi=130)

fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))
for y in years:
    s = hod[hod.year == y]; axes[0].plot(s.hour_local, s.anger_dev, color=colr[y], label=str(y), lw=1.3)
    s = mon[mon.year == y]; axes[1].plot(s.month, s.anger_dev, color=colr[y], label=str(y), lw=1.3, marker=".")
axes[0].set(title="Anger by hour (local time), deviation from year mean", xlabel="hour", ylabel="Δ anger", xticks=range(0, 24, 2))
axes[1].set(title="Anger by month, deviation from year mean", xlabel="month", xticks=range(1, 13))
for a in axes: a.axhline(0, color="grey", lw=0.8)
axes[1].legend(ncol=2, fontsize=7); fig.tight_layout(); fig.savefig("figures/anger_hour_month_by_year.png", dpi=130)

cycles = sorted(cyc.cycle.unique())
fig, axes = plt.subplots(2, 4, figsize=(16, 6.5), sharey=True)
for ax, c in zip(axes.flat, cycles):
    s = cyc[cyc.cycle == c]; ax.plot(-s.weeks_to_election, s.anger, color="k", lw=1)
    for p, col in [("Democrat", "tab:blue"), ("Republican", "tab:red")]:
        sp = cyc_party[(cyc_party.cycle == c) & (cyc_party.party == p)]; ax.plot(-sp.weeks_to_election, sp.anger, color=col, lw=0.8, alpha=0.8)
    ax.axvline(0, color="grey", ls="--", lw=0.8); ax.set_title(f"{c} {'presidential' if c % 4 == 0 else 'midterm'}")
    ax.set_xlabel("weeks to election")
for ax in axes.flat[len(cycles):]: ax.axis("off")
axes[0, 0].set_ylabel("mean anger"); fig.suptitle("Anger across each election cycle (black = all, blue/red = party)")
fig.tight_layout(); fig.savefig("figures/anger_by_cycle.png", dpi=130)

# ---------- console summary ----------
pd.set_option("display.width", 200)
print("\nanger by year:\n", by_year[["year", "n", "anger", "share_angry"]].round(3).to_string(index=False))
print("\nelection vs off years:\n", ey.groupby(["is_election_year", "is_presidential"]).apply(
    lambda g: pd.Series({"years": len(g), "anger": np.average(g.anger, weights=g.n)}), include_groups=False).round(3))
peak = hod.loc[hod.groupby("year").anger_dev.idxmax(), ["year", "hour_local", "anger_dev"]]
print("\nangriest hour per year:\n", peak.round(3).to_string(index=False))
peak = mon.loc[mon.groupby("year").anger_dev.idxmax(), ["year", "month", "anger_dev"]]
print("\nangriest month per year:\n", peak.round(3).to_string(index=False))
print("\nfigures/ and results/ written")
