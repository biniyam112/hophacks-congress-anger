"""The Anger Forecast: how predictable is an angry tweet given party, era, hour — and the member?

Outputs results/forecast_*.csv (share of tweets with P(anger) > 0.5, i.e. "angry tweets").
"""
import duckdb, pandas as pd
pd.set_option("display.width", 240)

con = duckdb.connect()
con.execute("""
CREATE VIEW d AS
SELECT t.*, e.anger, (e.anger > 0.5)::INT AS angry,
  CASE WHEN hour_local BETWEEN 9 AND 17 THEN '09-17 work' WHEN hour_local BETWEEN 18 AND 20 THEN '18-20 evening'
       WHEN hour_local BETWEEN 21 AND 23 THEN '21-23 late' WHEN hour_local BETWEEN 0 AND 4 THEN '00-04 night' ELSE '05-08 morning' END AS band,
  CASE WHEN created_at < '2017-01-20' THEN 'Obama' WHEN created_at < '2021-01-20' THEN 'Trump'
       WHEN created_at < '2025-01-20' THEN 'Biden' ELSE 'Trump II' END AS era
FROM 'tweets_enriched.parquet' t JOIN 'tweet_emotions.parquet' e USING (tweet_id)
WHERE in_office AND year BETWEEN 2011 AND 2026""")
# one display name per member: the one used on their most recent tweet
con.execute("""CREATE VIEW nm AS SELECT bioguide, ARG_MAX(author_name, created_at) AS name, ARG_MAX(party, created_at) AS party,
               ARG_MAX(state, created_at) AS state FROM d GROUP BY 1""")

base = con.sql("SELECT AVG(angry) FROM d").fetchone()[0]
print(f"baseline: {base:.1%} of tweets are angry\n")

cells = con.sql("""SELECT era, party, band, COUNT(*) n, AVG(angry) share_angry FROM d WHERE party IN ('Democrat','Republican')
                   GROUP BY 1,2,3 HAVING n >= 2000 ORDER BY share_angry DESC""").df()
cells.to_csv("results/forecast_party_era_hour.csv", index=False)
print("party x era x hour — top and bottom:\n", pd.concat([cells.head(6), cells.tail(4)]).round(3).to_string(index=False))

members = con.sql("""SELECT nm.name, nm.party, nm.state, COUNT(*) n, AVG(angry) share_angry, AVG(anger) mean_anger
                     FROM d JOIN nm USING (bioguide) GROUP BY 1,2,3 HAVING n >= 2000 ORDER BY share_angry DESC""").df()
members.to_csv("results/forecast_members.csv", index=False)
print("\nangriest members (>=2000 tweets):\n", members.head(10).round(3).to_string(index=False))
print("\ncalmest members:\n", members.tail(6).round(3).to_string(index=False))

mb = con.sql("""SELECT nm.name, nm.party, era, band, COUNT(*) n, AVG(angry) share_angry FROM d JOIN nm USING (bioguide)
                GROUP BY 1,2,3,4 HAVING n >= 200 ORDER BY share_angry DESC""").df()
mb.to_csv("results/forecast_member_era_hour.csv", index=False)
print("\nmember x era x hour (>=200 tweets) — most predictable:\n", mb.head(10).round(3).to_string(index=False))

owls = con.sql("""WITH m AS (SELECT bioguide,
    AVG(CASE WHEN band = '09-17 work' THEN angry END) daytime,
    AVG(CASE WHEN band IN ('21-23 late','00-04 night') THEN angry END) nighttime,
    SUM(CASE WHEN band IN ('21-23 late','00-04 night') THEN 1 ELSE 0 END) n_night, COUNT(*) n FROM d GROUP BY 1)
  SELECT nm.name, nm.party, n, n_night, daytime, nighttime, nighttime - daytime AS night_minus_day
  FROM m JOIN nm USING (bioguide) WHERE n_night >= 300 ORDER BY night_minus_day DESC""").df()
owls.to_csv("results/forecast_night_owls.csv", index=False)
print("\nnight owls (late tweets much angrier than daytime):\n", owls.head(8).round(3).to_string(index=False))
print("\nreverse (calmer at night):\n", owls.tail(4).round(3).to_string(index=False))

# the "forecast ladder": how much does each piece of information move the probability?
ladder = con.sql("""
SELECT 'nothing' AS known, AVG(angry) p FROM d
UNION ALL SELECT 'hour band = 00-04', AVG(angry) FROM d WHERE band = '00-04 night'
UNION ALL SELECT 'party = Democrat', AVG(angry) FROM d WHERE party = 'Democrat'
UNION ALL SELECT 'party = Democrat, era = Trump II', AVG(angry) FROM d WHERE party = 'Democrat' AND era = 'Trump II'
UNION ALL SELECT 'party = Democrat, era = Trump II, 09-17', AVG(angry) FROM d WHERE party = 'Democrat' AND era = 'Trump II' AND band = '09-17 work'
UNION ALL SELECT 'Chris Van Hollen, era = Trump II, 09-17', AVG(angry) FROM d JOIN nm USING (bioguide) WHERE nm.name = 'Chris Van Hollen' AND era = 'Trump II' AND band = '09-17 work'
UNION ALL SELECT 'party = Democrat, era = Obama, 00-04', AVG(angry) FROM d WHERE party = 'Democrat' AND era = 'Obama' AND band = '00-04 night'
""").df()
ladder.to_csv("results/forecast_ladder.csv", index=False)
print("\nforecast ladder:\n", ladder.round(3).to_string(index=False))
