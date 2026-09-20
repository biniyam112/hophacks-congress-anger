"""Two networks, one Congress: who retweets whom vs. who calls out whom (.@mentions).

Nodes: members of Congress (by handle). Edges: member -> member, from the tweet text.
  retweet:      tweet starts with 'RT @target'
  dot-mention:  '.@target' anywhere (the old convention for a *public* address — a call-out)
Each edge carries the count and the mean anger of the tweets that made it.

A single force layout is computed on the union graph so both panels share node positions;
the contrast in edge structure is then visible directly. Output: site/data/network.json,
results/network_edges_*.csv, results/network_bridges.csv.
"""
import json, re
import duckdb, networkx as nx, numpy as np, pandas as pd

MIN_EDGE = 3          # min tweets for an edge to be drawn
con = duckdb.connect()
con.execute("""
CREATE VIEW d AS
SELECT t.tweet_id, lower(t.author_handle) h, t.bioguide, t.author_name, t.party, t.state, t.year, t.text, e.anger
FROM 'tweets_enriched.parquet' t JOIN 'tweet_emotions.parquet' e USING (tweet_id)
WHERE t.in_office AND t.year BETWEEN 2011 AND 2026 AND t.party IN ('Democrat','Republican','Independent')""")
# one node per person (bioguide); a person may have used several handles
con.execute("""CREATE TABLE members AS
  SELECT bioguide AS h, ARG_MAX(author_name, year) AS name, ARG_MAX(party, year) AS party, ARG_MAX(state, year) AS state, COUNT(*) AS n_tweets
  FROM d GROUP BY 1""")
con.execute("CREATE TABLE handle2id AS SELECT DISTINCT h AS handle, bioguide FROM d")
# retweet edges (exclude 2023-24: those years were collected without retweets)
con.execute("""CREATE TABLE rt AS
  SELECT d.bioguide src, x.bioguide dst, COUNT(*) n, AVG(anger) anger
  FROM d JOIN handle2id x ON x.handle = lower(regexp_extract(text, '^RT @(\\w+)', 1))
  WHERE regexp_matches(text, '^RT @') AND year NOT IN (2023, 2024) GROUP BY 1,2""")
# dot-mention edges
con.execute("""CREATE TABLE dot AS
  SELECT u.src, x.bioguide dst, COUNT(*) n, AVG(anger) anger
  FROM (SELECT bioguide src, anger, lower(UNNEST(regexp_extract_all(text, '(?:^|\\s)\\.@(\\w+)', 1))) m FROM d WHERE NOT regexp_matches(text, '^RT @')) u
  JOIN handle2id x ON x.handle = u.m GROUP BY 1,2""")

def member_edges(tbl):
    return con.sql(f"""SELECT e.src, e.dst, e.n, e.anger, a.party sp, b.party dp FROM {tbl} e
                       JOIN members a ON a.h = e.src JOIN members b ON b.h = e.dst WHERE e.src <> e.dst AND e.n >= {MIN_EDGE}""").df()
rt_e, dot_e = member_edges("rt"), member_edges("dot")
for name, df in [("retweet", rt_e), ("dot_mention", dot_e)]:
    df["cross"] = (df.sp != df.dp) & df.sp.isin(["Democrat", "Republican"]) & df.dp.isin(["Democrat", "Republican"])
    df.to_csv(f"results/network_edges_{name}.csv", index=False)
    print(f"{name}: {len(df)} edges (>= {MIN_EDGE} tweets), {df.n.sum():,} tweets, cross-party share of edges {df.cross.mean():.1%}, "
          f"of tweets {df.n[df.cross].sum() / df.n.sum():.1%}; mean anger same {df[~df.cross].anger.mean():.3f} / cross {df[df.cross].anger.mean():.3f}")

# ---- shared layout on the union graph (undirected, weighted by tweets) ----
nodes = sorted(set(rt_e.src) | set(rt_e.dst) | set(dot_e.src) | set(dot_e.dst))
G = nx.Graph()
for df, w in [(rt_e, 1.0), (dot_e, 0.6)]:
    for r in df.itertuples():
        G.add_edge(r.src, r.dst, weight=G.get_edge_data(r.src, r.dst, {"weight": 0})["weight"] + w * np.log1p(r.n))
pos = nx.spring_layout(G, k=1.6 / np.sqrt(G.number_of_nodes()), weight="weight", iterations=300, seed=7)
# rotate so Democrats are on the left, Republicans on the right (cosmetic)
M = con.sql("SELECT * FROM members").df().set_index("h")
xy = np.array([pos[n] for n in nodes]); party = M.loc[nodes, "party"].values
dem_c = xy[party == "Democrat"].mean(0); rep_c = xy[party == "Republican"].mean(0)
ang = -np.arctan2(*(rep_c - dem_c)[::-1])
R = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]]); xy = xy @ R.T
xy = (xy - xy.min(0)) / (xy.max(0) - xy.min(0)) * 2 - 1
pos = {n: xy[i] for i, n in enumerate(nodes)}

# ---- node stats ----
def deg(df, col): return df.groupby(col).n.sum()
rt_in, rt_out, dot_in, dot_out = deg(rt_e, "dst"), deg(rt_e, "src"), deg(dot_e, "dst"), deg(dot_e, "src")
cross_rt_in = rt_e[rt_e.cross].groupby("dst").n.sum(); cross_dot_in = dot_e[dot_e.cross].groupby("dst").n.sum()
cross_dot_anger = dot_e[dot_e.cross].groupby("dst").apply(lambda g: np.average(g.anger, weights=g.n), include_groups=False)
clean = lambda s: re.sub(r"\s+[DRI]-[A-Z]{2}$", "", s)
node_rows = []
for h in nodes:
    m = M.loc[h]
    node_rows.append({"id": h, "name": clean(m["name"]), "party": m["party"], "state": m["state"], "x": round(float(pos[h][0]), 4), "y": round(float(pos[h][1]), 4),
                      "rt_in": int(rt_in.get(h, 0)), "rt_out": int(rt_out.get(h, 0)), "dot_in": int(dot_in.get(h, 0)), "dot_out": int(dot_out.get(h, 0)),
                      "cross_rt_in": int(cross_rt_in.get(h, 0)), "cross_dot_in": int(cross_dot_in.get(h, 0)),
                      "cross_dot_anger": (None if h not in cross_dot_anger else round(float(cross_dot_anger[h]), 3))})
N = pd.DataFrame(node_rows)
# the bridges: most retweeted by the other party; the lightning rods: most called out by the other party
bridges = N.sort_values("cross_rt_in", ascending=False).head(12)
rods = N.sort_values("cross_dot_in", ascending=False).head(12)
N.to_csv("results/network_nodes.csv", index=False)
bridges.to_csv("results/network_bridges.csv", index=False)
pd.set_option("display.width", 200)
print("\nBRIDGES — most retweeted across the aisle:\n", bridges[["name", "party", "cross_rt_in", "rt_in"]].to_string(index=False))
print("\nLIGHTNING RODS — most .@-called-out by the other party:\n", rods[["name", "party", "cross_dot_in", "cross_dot_anger"]].to_string(index=False))

def edges_json(df):
    return [[r.src, r.dst, int(r.n), round(float(r.anger), 3)] for r in df.itertuples()]
summary = {name: {"edges": len(df), "tweets": int(df.n.sum()), "cross_edge_share": round(float(df.cross.mean()), 3),
                  "cross_tweet_share": round(float(df.n[df.cross].sum() / df.n.sum()), 3),
                  "anger_same": round(float(np.average(df[~df.cross].anger, weights=df[~df.cross].n)), 3),
                  "anger_cross": round(float(np.average(df[df.cross].anger, weights=df[df.cross].n)), 3)}
           for name, df in [("retweet", rt_e), ("dot", dot_e)]}
json.dump({"nodes": node_rows, "retweet": edges_json(rt_e), "dot": edges_json(dot_e), "summary": summary,
           "bridges": bridges[["name", "party", "cross_rt_in"]].to_dict(orient="records"),
           "rods": rods[["name", "party", "cross_dot_in", "cross_dot_anger"]].to_dict(orient="records")},
          open("site/data/network.json", "w", encoding="utf8"), separators=(",", ":"), ensure_ascii=False)
print("\nsummary:", json.dumps(summary, indent=1))
print("nodes:", len(node_rows), " site/data/network.json written")
