"""Label every tweet in tweets_enriched.parquet with 11 emotion + 3 sentiment probabilities.

Models: cardiffnlp/twitter-roberta-base-emotion-multilabel-latest  (sigmoid, 11 labels)
        cardiffnlp/twitter-roberta-base-sentiment-latest           (softmax, 3 labels)

Resumable: writes one parquet chunk per CHUNK tweets to emotions/, skips chunks already done.
Final merge -> tweet_emotions.parquet (tweet_id + 14 scores), join on tweet_id.

Usage: python label_emotions.py                 # everything -> tweet_emotions.parquet
       python label_emotions.py --sample 20000  # random sample -> tweet_emotions_sample.parquet
"""
import argparse, os, re, time
import duckdb, numpy as np, pandas as pd, torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

ap = argparse.ArgumentParser()
ap.add_argument("--sample", type=int, default=None, help="label a random sample of N in-office tweets instead of all")
ap.add_argument("--batch", type=int, default=256)
args = ap.parse_args()

CHUNK = 50_000 if not args.sample else 5_000
BATCH = args.batch
OUT = "emotions" if not args.sample else "emotions_sample"
FINAL = "tweet_emotions.parquet" if not args.sample else "tweet_emotions_sample.parquet"
os.makedirs(OUT, exist_ok=True)

dev = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if dev == "cuda" else torch.float32
print("device:", dev, torch.cuda.get_device_name(0) if dev == "cuda" else "")
if dev == "cpu":
    torch.set_num_threads(os.cpu_count())

MODELS = {
    "emo": "cardiffnlp/twitter-roberta-base-emotion-multilabel-latest",
    "sent": "cardiffnlp/twitter-roberta-base-sentiment-latest",
}
loaded = {}
for k, name in MODELS.items():
    tok = AutoTokenizer.from_pretrained(name)
    m = AutoModelForSequenceClassification.from_pretrained(name, dtype=dtype).to(dev).eval()
    loaded[k] = (tok, m, [m.config.id2label[i] for i in range(m.config.num_labels)])

def preprocess(t):
    t = re.sub(r"@\w+", "@user", t)
    t = re.sub(r"https?://\S+", "http", t)
    return t

def score(texts, key):
    tok, m, labels = loaded[key]
    out = []
    with torch.inference_mode():
        for i in range(0, len(texts), BATCH):
            enc = tok(texts[i:i+BATCH], padding=True, truncation=True, max_length=128, return_tensors="pt").to(dev)
            logits = m(**enc).logits.float()
            p = torch.sigmoid(logits) if key == "emo" else torch.softmax(logits, -1)
            out.append(p.cpu().numpy())
    return pd.DataFrame(np.vstack(out), columns=labels)

con = duckdb.connect()
if args.sample:
    # fixed-seed sample materialised once so chunks are stable across resumed runs
    con.execute(f"""CREATE TABLE t AS SELECT tweet_id, text FROM 'tweets_enriched.parquet'
                    WHERE in_office USING SAMPLE {args.sample} (reservoir, 7) ORDER BY tweet_id""")
else:
    # stable order so chunk boundaries are reproducible across runs
    con.execute("CREATE VIEW t AS SELECT tweet_id, text FROM 'tweets_enriched.parquet' ORDER BY tweet_id")
n_total = con.sql("SELECT COUNT(*) FROM t").fetchone()[0]
print(f"tweets to label: {n_total:,}")

t_start = time.time()
for start in range(0, n_total, CHUNK):
    path = f"{OUT}/chunk_{start:09d}.parquet"
    if os.path.exists(path):
        continue
    df = con.sql(f"SELECT * FROM t LIMIT {min(CHUNK, n_total - start)} OFFSET {start}").df()
    # sort by length within the chunk so padding is minimal -> big speedup
    df["_len"] = df.text.str.len()
    df = df.sort_values("_len").reset_index(drop=True)
    texts = [preprocess(x) for x in df.text]
    t0 = time.time()
    emo = score(texts, "emo")
    sent = score(texts, "sent")
    res = pd.concat([df[["tweet_id"]], emo, sent], axis=1)
    res.to_parquet(path + ".tmp", index=False)
    os.replace(path + ".tmp", path)
    done = start + len(df)
    rate = len(df) / (time.time() - t0)
    eta = (n_total - done) / rate / 60
    print(f"{done:>10,}/{n_total:,}  {rate:,.0f} tweets/s  ETA {eta:.0f} min", flush=True)

con.sql(f"COPY (SELECT * FROM '{OUT}/chunk_*.parquet') TO '{FINAL}' (FORMAT PARQUET, COMPRESSION ZSTD)")
print(f"done in {(time.time()-t_start)/60:.1f} min ->  {FINAL}")
print(con.sql(f"SELECT COUNT(*) n, ROUND(AVG(anger),3) mean_anger, ROUND(AVG((anger > 0.5)::INT),3) share_angry FROM '{FINAL}'"))
