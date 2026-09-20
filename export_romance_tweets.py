"""For the romance interlude: one exemplary tweet per party per month.

For each month, each party gets the emotion in which it exceeds the other party most that month (from the
per-month gap vector), and the tweet by that party in that month with the highest score on that emotion —
excluding retweets, very short tweets and link-only tweets. Output: site/data/romance_tweets.json
"""
import json, re
import duckdb, pandas as pd

EMOTIONS = ["anger", "disgust", "fear", "sadness", "joy", "optimism", "love", "trust", "anticipation", "pessimism", "surprise"]
gaps = pd.read_csv("results/unity_distance_by_month.csv")
con = duckdb.connect()
con.execute("""
CREATE VIEW d AS
SELECT t.party, date_trunc('month', t.created_at)::DATE AS mo, t.author_name, t.text, e.*
FROM 'tweets_enriched.parquet' t JOIN 'tweet_emotions.parquet' e USING (tweet_id)
WHERE t.in_office AND t.year BETWEEN 2011 AND 2026 AND t.party IN ('Democrat','Republican')
  AND NOT regexp_matches(t.text, '^RT @') AND length(t.text) BETWEEN 70 AND 280
  AND length(regexp_replace(t.text, 'https?://\\S+', '', 'g')) >= 60""")

clean_name = lambda s: re.sub(r"\s+[DRI]-[A-Z]{2}$", "", s)
def tidy(text):
    text = re.sub(r"https?://\S+", "", text).replace("&amp;", "&").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= 220 else text[:217].rsplit(" ", 1)[0] + "…"

out = {}
for r in gaps.itertuples():
    mo = str(r.mo)
    gap = {e: getattr(r, f"gap_{e}") for e in EMOTIONS}          # Democrats minus Republicans
    picks = {"Democrat": max(gap, key=gap.get), "Republican": min(gap, key=gap.get)}
    entry = {}
    for party, emo in picks.items():
        row = con.sql(f"""SELECT author_name, text, {emo} AS score FROM d WHERE party = '{party}' AND mo = '{mo}'
                          ORDER BY {emo} DESC LIMIT 1""").fetchone()
        if row:
            entry["dem" if party == "Democrat" else "rep"] = {"emo": emo, "who": clean_name(row[0]), "text": tidy(row[1]), "score": round(float(row[2]), 2)}
    out[mo[:7]] = entry
json.dump(out, open("site/data/romance_tweets.json", "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
print(len(out), "months;", sum(len(v) for v in out.values()), "tweets")
for k in ["2013-06", "2017-10", "2020-06", "2022-03", "2025-10"]:
    print(k, json.dumps(out.get(k), ensure_ascii=False)[:400])
