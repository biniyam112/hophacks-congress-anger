"""The anger seismograph: weekly anger 2011-2026 with spikes detected and auto-described.

Outputs
  results/seismograph_weekly.csv   week, n, anger, share_angry, anger_dem, anger_rep, baseline, spike_score
  results/seismograph_spikes.csv   top spikes with the words/hashtags that distinguish that week,
                                   which party drove it, and the angriest example tweet
  figures/seismograph.png
"""
import re, math
from collections import Counter
import duckdb, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

TOP_SPIKES = 40
BASELINE_WEEKS = 13          # centred rolling median window for "normal" anger
MIN_GAP_WEEKS = 3            # spikes closer than this are merged into the higher one

con = duckdb.connect()
con.execute("""
CREATE VIEW d AS
SELECT t.tweet_id, t.party, t.author_name, t.created_at, t.text, e.anger, e.disgust, e.fear, e.sadness, e.joy,
       date_trunc('week', t.created_at)::DATE AS wk
FROM 'tweets_enriched.parquet' t JOIN 'tweet_emotions.parquet' e USING (tweet_id)
WHERE t.in_office AND t.year BETWEEN 2011 AND 2026""")

# ---------- weekly series ----------
w = con.sql("""
SELECT wk, COUNT(*) n, AVG(anger) anger, AVG((anger > 0.5)::INT) share_angry,
       AVG(CASE WHEN party='Democrat' THEN anger END) anger_dem, AVG(CASE WHEN party='Republican' THEN anger END) anger_rep,
       SUM(CASE WHEN party='Democrat' THEN 1 ELSE 0 END) n_dem, SUM(CASE WHEN party='Republican' THEN 1 ELSE 0 END) n_rep,
       AVG(disgust) disgust, AVG(fear) fear, AVG(sadness) sadness, AVG(joy) joy
FROM d GROUP BY 1 ORDER BY 1""").df()
w = w[w.n >= 500].reset_index(drop=True)
w["baseline"] = w.anger.rolling(BASELINE_WEEKS, center=True, min_periods=5).median()
w["excess"] = w.anger - w.baseline
resid_sd = w.excess.rolling(52, center=True, min_periods=20).std()
w["spike_score"] = w.excess / resid_sd
w["dem_excess"] = w.anger_dem - w.anger_dem.rolling(BASELINE_WEEKS, center=True, min_periods=5).median()
w["rep_excess"] = w.anger_rep - w.anger_rep.rolling(BASELINE_WEEKS, center=True, min_periods=5).median()
w.to_csv("results/seismograph_weekly.csv", index=False)

# ---------- spike detection: local maxima of excess anger, greedy with a minimum gap ----------
cand = w.dropna(subset=["excess"]).sort_values("excess", ascending=False)
spikes = []
for _, r in cand.iterrows():
    if any(abs((r.wk - s.wk).days) < MIN_GAP_WEEKS * 7 for s in spikes):
        continue
    spikes.append(r)
    if len(spikes) == TOP_SPIKES:
        break
spikes = pd.DataFrame(spikes).sort_values("wk").reset_index(drop=True)

# ---------- describe each spike ----------
STOP = set("""the a an and or of to in on for with is are was were be been this that these those it its at by from as we our
us you your they their he she his her i my me not no but if so than then there here who what when which will would can could
should has have had do does did just about into over more most all any some very out up down off also only new one two today
rt amp http https user via re s t m ve ll d don doesn didn isn aren won wouldn couldn shouldn get got make made like
""".split())

def tokens(text):
    text = re.sub(r"https?://\S+|@\w+", " ", text.lower())
    return [t for t in re.findall(r"#?[a-z][a-z'’\-]{2,}", text) if t.lstrip("#") not in STOP]

def describe(week):
    lo, hi = week - pd.Timedelta(weeks=6), week + pd.Timedelta(weeks=7)
    df = con.sql(f"""SELECT wk, party, author_name, text, anger FROM d
                     WHERE wk BETWEEN '{lo.date()}' AND '{hi.date()}'""").df()
    df["wk"] = pd.to_datetime(df.wk)
    inwk = df[df.wk == week]
    base = df[df.wk != week]
    # log-odds of each token in the spike week vs surrounding weeks, among angry tweets
    cw = Counter(t for txt in inwk[inwk.anger > 0.5].text for t in set(tokens(txt)))
    cb = Counter(t for txt in base[base.anger > 0.5].text for t in set(tokens(txt)))
    nw, nb = max(1, len(inwk[inwk.anger > 0.5])), max(1, len(base[base.anger > 0.5]))
    scores = {t: math.log((cw[t] + 1) / nw) - math.log((cb[t] + 1) / nb) for t in cw if cw[t] >= 15}
    top = sorted(scores, key=scores.get, reverse=True)
    words = [t for t in top if not t.startswith("#")][:10]
    tags = [t for t in top if t.startswith("#")][:5]
    # which party drove it: excess anger by party this week vs their own baseline
    dem = inwk[inwk.party == "Democrat"].anger.mean() - base[base.party == "Democrat"].anger.mean()
    rep = inwk[inwk.party == "Republican"].anger.mean() - base[base.party == "Republican"].anger.mean()
    ex = inwk.sort_values("anger", ascending=False).iloc[0]
    return dict(keywords=" ".join(words), hashtags=" ".join(tags), dem_excess=round(dem, 3), rep_excess=round(rep, 3),
                driven_by=("Dem" if dem > rep + 0.03 else "Rep" if rep > dem + 0.03 else "both"),
                example_author=ex.author_name, example=ex.text.replace("\n", " ")[:220])

desc = pd.DataFrame([describe(pd.Timestamp(wk)) for wk in spikes.wk])
spikes = pd.concat([spikes[["wk", "n", "anger", "baseline", "excess", "spike_score"]].round(3), desc], axis=1)

# Hand-labelled from the auto-extracted keywords/hashtags + the dates. Keyed by week start (Monday).
EVENTS = {
    "2011-02-14": "H.R.1 spending-cut fight (FY2011 budget)",
    "2011-04-04": "Near-shutdown, Apr 8 deadline",
    "2011-07-25": "Debt-ceiling standoff",
    "2011-12-19": "Payroll-tax-cut extension fight",
    "2012-01-16": "SOPA/PIPA blackout; Keystone XL rejected",
    "2012-02-13": "Obama FY2013 budget; stimulus anniversary",
    "2012-07-30": "Bush tax-cut extension votes",
    "2013-02-25": "Sequester takes effect (Mar 1)",
    "2013-05-13": "IRS targeting + DOJ/AP + Benghazi scandals",
    "2013-07-08": "Farm bill splits off SNAP; student-loan rates double",
    "2013-09-30": "GOVERNMENT SHUTDOWN begins (Oct 1)",
    "2014-11-17": "Obama immigration executive action",
    "2015-02-23": "DHS shutdown deadline; net-neutrality vote; Keystone veto",
    "2016-01-04": "Obama gun executive actions; ACA/PP repeal veto",
    "2016-06-20": "Orlando aftermath: House Democrats' gun sit-in",
    "2016-07-11": "Dallas & Baton Rouge police shootings; Nice attack",
    "2017-01-02": "New Congress: ethics-office gutting attempt; ACA repeal starts",
    "2017-01-30": "Travel ban; Sally Yates fired; Gorsuch nominated",
    "2017-03-20": "AHCA 'Trumpcare' pulled; Comey hearing",
    "2017-07-24": "'Skinny repeal' fails; trans military ban",
    "2017-08-14": "Charlottesville aftermath; Bannon out",
    "2017-11-27": "Flynn pleads guilty; Senate passes tax bill",
    "2017-12-18": "Tax Cuts and Jobs Act signed; DREAM Act push",
    "2018-01-15": "GOVERNMENT SHUTDOWN (Jan 20–22)",
    "2018-06-18": "Family separation at the border",
    "2018-07-16": "Helsinki: Trump sides with Putin",
    "2018-12-17": "Mattis resigns; GOVERNMENT SHUTDOWN begins (Dec 22)",
    "2019-01-07": "35-day shutdown peak; Trump Oval Office address",
    "2019-09-23": "Whistleblower complaint; impeachment inquiry opens",
    "2020-06-01": "George Floyd protests; Lafayette Square photo-op",
    "2021-01-04": "JANUARY 6 Capitol attack",
    "2021-05-17": "Israel–Gaza war / ceasefire; Equality Act",
    "2022-02-21": "Russia invades Ukraine",
    "2023-01-09": "New GOP House: Born-Alive Act; Biden garage documents",
    "2023-09-25": "Shutdown deadline (averted); Menendez indicted",
    "2024-04-15": "Iran strikes Israel; Mayorkas impeachment; Ukraine aid",
    "2024-11-18": "Laken Riley verdict; ICC warrants; Capitol restroom fight",
    "2024-12-16": "CR collapses, near-shutdown (Dec 20)",
    "2025-09-29": "GOVERNMENT SHUTDOWN begins (Oct 1) — angriest week on record",
    "2025-10-20": "Shutdown wk 4; East Wing demolition; No Kings rallies",
}
spikes["event"] = spikes.wk.map(lambda d: EVENTS.get(str(pd.Timestamp(d).date()), ""))
spikes.to_csv("results/seismograph_spikes.csv", index=False)

# ---------- figure ----------
fig, (ax, ax2) = plt.subplots(2, 1, figsize=(18, 8), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
ax.fill_between(w.wk, w.baseline, w.anger, where=w.anger > w.baseline, color="tab:red", alpha=0.35, lw=0)
ax.plot(w.wk, w.anger, color="k", lw=0.8, label="all members")
ax.plot(w.wk, w.baseline, color="grey", lw=0.8, ls="--", label=f"{BASELINE_WEEKS}-week baseline")
ax.plot(w.wk, w.anger_dem, color="tab:blue", lw=0.5, alpha=0.7, label="Democrats")
ax.plot(w.wk, w.anger_rep, color="tab:red", lw=0.5, alpha=0.7, label="Republicans")
for _, s in spikes.sort_values("excess", ascending=False).head(16).iterrows():
    lab = s.event.split(";")[0].split(":")[0][:34] if s.event else str(pd.Timestamp(s.wk).date())
    ax.annotate(lab, (s.wk, s.anger), textcoords="offset points", xytext=(0, 5), ha="left", va="bottom",
                fontsize=6.5, rotation=60)
for d, lab in [("2017-01-20", "Trump"), ("2021-01-20", "Biden"), ("2025-01-20", "Trump II")]:
    ax.axvline(pd.Timestamp(d), color="grey", lw=0.6); ax.text(pd.Timestamp(d), 0.66, " " + lab, fontsize=8, color="grey")
ax.set(ylim=(0.05, 0.72), ylabel="mean P(anger), weekly", title="The Congressional anger seismograph, 2011–2026"); ax.legend(loc="upper left", fontsize=8)
ax2.bar(w.wk, w.n, width=7, color="lightgrey"); ax2.set(ylabel="tweets / week")
fig.tight_layout(); fig.savefig("figures/seismograph.png", dpi=130)

pd.set_option("display.width", 250, "display.max_colwidth", 70)
print(spikes[["wk", "n", "anger", "excess", "driven_by", "keywords", "hashtags"]].to_string(index=False))
