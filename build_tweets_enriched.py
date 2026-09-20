"""Join authors.parquet onto the tweets and add the 'What makes US angrier' features.

Output: tweets_enriched.parquet (Congress members only, deduplicated by tweet_id)
  age_at_tweet      years, fractional
  hour_et           hour of day in US Eastern (created_at is assumed UTC, as Twitter's API returns)
  hour_local        hour of day in the member's home-state time zone
  season            Winter/Spring/Summer/Fall (meteorological, Northern Hemisphere)
  is_election_year  even year (all House seats + 1/3 Senate)
  is_presidential   year % 4 == 0
  days_to_election  days until the next general election (Tue after 1st Mon of Nov)
  cycle_phase       position within the 2-year cycle: 0 = just after an election, 1 = election day
"""
import duckdb

con = duckdb.connect()
con.execute("SET TimeZone='America/New_York'")

# dominant IANA zone per state, for hour_local (split-zone states use the zone with most population)
STATE_TZ = {
    **{s: "America/New_York" for s in "CT DE DC FL GA IN KY ME MD MA MI NH NJ NY NC OH PA RI SC VT VA WV PR VI".split()},
    **{s: "America/Chicago" for s in "AL AR IL IA KS LA MN MS MO NE ND OK SD TN TX WI".split()},
    **{s: "America/Denver" for s in "CO ID MT NM UT WY".split()},
    "AZ": "America/Phoenix",
    **{s: "America/Los_Angeles" for s in "CA NV OR WA".split()},
    "AK": "America/Anchorage", "HI": "Pacific/Honolulu",
    "GU": "Pacific/Guam", "MP": "Pacific/Guam", "AS": "Pacific/Pago_Pago",
}
con.execute("CREATE TABLE state_tz (state VARCHAR, tz VARCHAR)")
con.executemany("INSERT INTO state_tz VALUES (?, ?)", list(STATE_TZ.items()))

con.execute("""
CREATE OR REPLACE TABLE tweets AS
WITH t AS (
  SELECT *,
         CASE WHEN chamber IN ('Senate','senator') THEN 'Senate'
              WHEN chamber IN ('House','representative') THEN 'House' END AS chamber_norm,
         CASE WHEN state IN ('MARIANA') THEN 'MP' WHEN state='GUAM' THEN 'GU' ELSE state END AS state_norm,
         ROW_NUMBER() OVER (PARTITION BY tweet_id ORDER BY source_corpus) AS rn
  FROM 'congress-tweets-unified.parquet'
),
e AS (
  SELECT
    t.tweet_id, t.author_handle, a.bioguide, t.author_name, t.party, t.chamber_norm AS chamber,
    t.state_norm AS state, t.created_at, t.text, t.topic, t.source_corpus,
    a.birthday, a.gender,
    date_diff('day', a.birthday::DATE, t.created_at::DATE) / 365.25          AS age_at_tweet,
    (t.created_at AT TIME ZONE 'UTC' AT TIME ZONE 'America/New_York')       AS created_at_et,
    EXTRACT(hour FROM (t.created_at AT TIME ZONE 'UTC' AT TIME ZONE COALESCE(z.tz, 'America/New_York')))::INT AS hour_local,
    EXTRACT(year FROM t.created_at)::INT                                     AS year
  FROM t
  JOIN 'authors.parquet' a USING (author_handle)
  LEFT JOIN state_tz z ON z.state = t.state_norm
  WHERE t.rn = 1 AND a.is_congress AND a.birthday IS NOT NULL
    AND t.created_at >= '2006-03-21'          -- Twitter's launch; earlier timestamps are corrupt
),
f AS (
  SELECT *,
    EXTRACT(hour FROM created_at_et)::INT      AS hour_et,
    EXTRACT(dow  FROM created_at_et)::INT      AS dow_et,      -- 0 = Sunday
    EXTRACT(month FROM created_at_et)::INT     AS month,
    CASE EXTRACT(month FROM created_at_et)::INT
      WHEN 12 THEN 'Winter' WHEN 1 THEN 'Winter' WHEN 2 THEN 'Winter'
      WHEN 3 THEN 'Spring' WHEN 4 THEN 'Spring' WHEN 5 THEN 'Spring'
      WHEN 6 THEN 'Summer' WHEN 7 THEN 'Summer' WHEN 8 THEN 'Summer'
      ELSE 'Fall' END                          AS season,
    year % 2 = 0                               AS is_election_year,
    year % 4 = 0                               AS is_presidential,
    -- general election: Tuesday after the first Monday in November of the next even year
    (SELECT d FROM (
       SELECT make_date(y, 11, 1) + ((8 - EXTRACT(dow FROM make_date(y,11,1))::INT) % 7) + 1 AS d
       FROM (SELECT (year + (year % 2)) AS y)
     ))                                        AS next_election_naive
  FROM e
),
g AS (
  SELECT *,
    -- if we've already passed this cycle's election day, the next one is two years later
    CASE WHEN created_at::DATE > next_election_naive
         THEN make_date(EXTRACT(year FROM next_election_naive)::INT + 2, 11, 1)
              + ((8 - EXTRACT(dow FROM make_date(EXTRACT(year FROM next_election_naive)::INT + 2, 11, 1))::INT) % 7) + 1
         ELSE next_election_naive END          AS next_election
  FROM f
)
SELECT g.* EXCLUDE (next_election_naive),
  date_diff('day', created_at::DATE, next_election)          AS days_to_election,
  1 - date_diff('day', created_at::DATE, next_election)/730.5 AS cycle_phase,
  EXISTS (SELECT 1 FROM 'terms.parquet' tm
          WHERE tm.bioguide = g.bioguide
            AND g.created_at::DATE BETWEEN tm.term_start AND tm.term_end) AS in_office
FROM g
""")

con.execute("COPY tweets TO 'tweets_enriched.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)")

print(con.sql("SELECT COUNT(*) n_rows, COUNT(DISTINCT bioguide) members, MIN(created_at) first_tweet, MAX(created_at) last_tweet FROM tweets"))
print(con.sql("SELECT COUNT(*) - COUNT(DISTINCT tweet_id) AS dup_ids_in_source FROM 'congress-tweets-unified.parquet'"))
print(con.sql("""SELECT quantile_cont(age_at_tweet, [0, .05, .25, .5, .75, .95, 1]) AS age_quantiles FROM tweets"""))
print(con.sql("SELECT season, COUNT(*) n FROM tweets GROUP BY 1 ORDER BY 1"))
print(con.sql("SELECT is_election_year, COUNT(*) n FROM tweets GROUP BY 1"))
print(con.sql("SELECT in_office, COUNT(*) n, ROUND(AVG(age_at_tweet),1) mean_age FROM tweets GROUP BY 1"))
print(con.sql("SELECT tweet_id, author_name, created_at, created_at_et, hour_et, age_at_tweet, days_to_election, cycle_phase FROM tweets USING SAMPLE 5"))
