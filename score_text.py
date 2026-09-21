"""Score any text for emotion and sentiment with the same RoBERTa models used in the project.

Models (Cardiff NLP, trained on tweets):
  cardiffnlp/twitter-roberta-base-emotion-multilabel-latest   11 emotions, independent probabilities (sigmoid)
  cardiffnlp/twitter-roberta-base-sentiment-latest            negative / neutral / positive (softmax, sums to 1)
A text counts as "angry" when P(anger) > 0.5, the same rule the analysis uses.

Usage
  python score_text.py "It's downright criminal. They're slashing Medicare to cut taxes for billionaires." "Happy birthday!"
  python score_text.py --file tweets.txt            # one text per line
  echo "Happy birthday, Senator!" | python score_text.py
  python score_text.py --json "text"                # machine-readable output

As a library
  from score_text import score, score_many
  score("some text")             -> {"anger": 0.94, ..., "negative": 0.9, "neutral": 0.08, "positive": 0.02, "angry": True}
  score_many(["a", "b"])         -> list of the same dicts
"""
import argparse, json, re, sys
from functools import lru_cache

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

EMOTION_MODEL = "cardiffnlp/twitter-roberta-base-emotion-multilabel-latest"
SENTIMENT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
ANGRY_THRESHOLD = 0.5
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def preprocess(text: str) -> str:
    """The normalisation the Cardiff models were trained with: mask handles and links."""
    text = re.sub(r"@\w+", "@user", text)
    text = re.sub(r"https?://\S+", "http", text)
    return text.strip()


@lru_cache(maxsize=None)
def _load(name: str):
    tokenizer = AutoTokenizer.from_pretrained(name)
    model = AutoModelForSequenceClassification.from_pretrained(name).to(DEVICE).eval()
    labels = [model.config.id2label[i] for i in range(model.config.num_labels)]
    return tokenizer, model, labels


def _run(name: str, texts: list[str], multilabel: bool, batch_size: int = 64) -> list[dict]:
    tokenizer, model, labels = _load(name)
    out = []
    with torch.inference_mode():
        for i in range(0, len(texts), batch_size):
            enc = tokenizer(texts[i:i + batch_size], padding=True, truncation=True, max_length=128, return_tensors="pt").to(DEVICE)
            logits = model(**enc).logits.float()
            probs = torch.sigmoid(logits) if multilabel else torch.softmax(logits, dim=-1)
            out.extend({lab: round(float(p), 4) for lab, p in zip(labels, row)} for row in probs.cpu())
    return out


def score_many(texts: list[str]) -> list[dict]:
    """Score a list of texts. Returns one dict per text with 11 emotions, 3 sentiments, and an `angry` flag."""
    clean = [preprocess(t) for t in texts]
    emotions = _run(EMOTION_MODEL, clean, multilabel=True)
    sentiments = _run(SENTIMENT_MODEL, clean, multilabel=False)
    return [{**e, **s, "angry": e["anger"] > ANGRY_THRESHOLD} for e, s in zip(emotions, sentiments)]


def score(text: str) -> dict:
    """Score a single text."""
    return score_many([text])[0]


def _print_report(text: str, r: dict) -> None:
    emo = {k: v for k, v in r.items() if k not in ("negative", "neutral", "positive", "angry")}
    top = sorted(emo.items(), key=lambda kv: -kv[1])
    print(f"\n\"{text}\"")
    print(f"  {'ANGRY' if r['angry'] else 'not angry'}  (anger {r['anger']:.2f}, threshold {ANGRY_THRESHOLD})")
    print("  emotions:  " + "  ".join(f"{k} {v:.2f}" for k, v in top if v >= 0.1))
    print(f"  sentiment: negative {r['negative']:.2f}  neutral {r['neutral']:.2f}  positive {r['positive']:.2f}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Score text for emotion and sentiment with the project's RoBERTa models.")
    ap.add_argument("text", nargs="*", help="one or more texts to score (quote each); omit to read from --file or stdin")
    ap.add_argument("--file", help="file with one text per line")
    ap.add_argument("--json", action="store_true", help="print JSON instead of a report")
    args = ap.parse_args()

    if args.file:
        texts = [line.rstrip("\n") for line in open(args.file, encoding="utf8") if line.strip()]
    elif args.text:
        texts = args.text
    else:
        texts = [line.rstrip("\n") for line in sys.stdin if line.strip()]
    if not texts:
        ap.error("no text given")

    print(f"device: {DEVICE}", file=sys.stderr)
    results = score_many(texts)
    if args.json:
        print(json.dumps([{"text": t, **r} for t, r in zip(texts, results)], ensure_ascii=False, indent=2))
    else:
        for t, r in zip(texts, results):
            _print_report(t, r)


if __name__ == "__main__":
    main()
