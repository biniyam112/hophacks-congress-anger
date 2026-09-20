"""Compare candidate sentiment/emotion models on a random sample of Congress tweets.
Prints throughput, label distributions, and the top 'angry' tweets per model so we can
judge which definition of anger fits the data."""
import re, time, sys
import duckdb, numpy as np, pandas as pd, torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

N = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
torch.set_num_threads(16)

df = duckdb.sql(f"""SELECT tweet_id, author_name, party, year, text
                    FROM 'tweets_enriched.parquet' WHERE in_office USING SAMPLE {N} (reservoir, 42)""").df()

def preprocess(t):  # what the Cardiff models were trained on
    t = re.sub(r"@\w+", "@user", t)
    t = re.sub(r"https?://\S+", "http", t)
    return t

MODELS = {
    "emotion4":   "cardiffnlp/twitter-roberta-base-emotion",                   # anger joy optimism sadness (softmax)
    "emotion11":  "cardiffnlp/twitter-roberta-base-emotion-multilabel-latest", # 11 labels (sigmoid)
    "sentiment3": "cardiffnlp/twitter-roberta-base-sentiment-latest",          # negative neutral positive
}

texts = [preprocess(t) for t in df.text]
results = {}
for key, name in MODELS.items():
    tok = AutoTokenizer.from_pretrained(name)
    model = AutoModelForSequenceClassification.from_pretrained(name).eval()
    labels = [model.config.id2label[i] for i in range(model.config.num_labels)]
    multilabel = model.config.problem_type == "multi_label_classification" or "multilabel" in name
    out = []
    t0 = time.time()
    with torch.inference_mode():
        for i in range(0, len(texts), 64):
            enc = tok(texts[i:i+64], padding=True, truncation=True, max_length=128, return_tensors="pt")
            logits = model(**enc).logits
            probs = torch.sigmoid(logits) if multilabel else torch.softmax(logits, -1)
            out.append(probs.numpy())
    dt = time.time() - t0
    probs = np.vstack(out)
    res = pd.DataFrame(probs, columns=labels)
    results[key] = res
    print(f"\n=== {key} ({name}) — {len(texts)/dt:.0f} tweets/s, {dt:.0f}s ===")
    print("mean prob per label:", res.mean().round(3).to_dict())
    if not multilabel:
        print("argmax share:", res.idxmax(axis=1).value_counts(normalize=True).round(3).to_dict())

# ---- show what each model thinks the angriest tweets are ----
pd.set_option("display.width", 250, "display.max_colwidth", 160)
for key, col in [("emotion4", "anger"), ("emotion11", "anger"), ("sentiment3", "negative")]:
    s = results[key][col]
    print(f"\n#### top {col} by {key}")
    top = df.assign(score=s.values).sort_values("score", ascending=False).head(12)
    print(top[["score", "party", "year", "text"]].to_string(index=False))

# ---- agreement between models ----
m = pd.DataFrame({"anger4": results["emotion4"]["anger"], "anger11": results["emotion11"]["anger"],
                  "neg3": results["sentiment3"]["negative"]})
print("\ncorrelations:\n", m.corr().round(2))

# save for inspection
df.join(m).to_parquet("bench_sample.parquet", index=False)
