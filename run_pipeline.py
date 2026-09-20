"""One command for the whole 'What makes US angrier' pipeline.

  python run_pipeline.py            # full: label all tweets (GPU) -> analyses -> figures
  python run_pipeline.py --sample   # quick: 20K-tweet sample labels -> analyses (for testing)
  python run_pipeline.py --skip-labels   # just re-run the analyses on existing labels

Each step is idempotent (labeling resumes from finished chunks; the data build is skipped
if its outputs exist) so it's safe to re-run after an interruption.
"""
import argparse, os, subprocess, sys, time

ap = argparse.ArgumentParser()
ap.add_argument("--sample", action="store_true")
ap.add_argument("--skip-labels", action="store_true")
ap.add_argument("--rebuild", action="store_true", help="rebuild authors/terms/tweets_enriched even if present")
args = ap.parse_args()

def run(cmd):
    print(f"\n$ {' '.join(cmd)}", flush=True)
    t0 = time.time()
    r = subprocess.run(cmd, env={**os.environ, "PYTHONIOENCODING": "utf8"})
    print(f"  [{'ok' if r.returncode == 0 else 'FAILED'} in {(time.time()-t0)/60:.1f} min]", flush=True)
    if r.returncode:
        sys.exit(r.returncode)

py = [sys.executable]
if args.rebuild or not os.path.exists("authors.parquet"):
    run(py + ["build_author_ages.py"])
if args.rebuild or not os.path.exists("tweets_enriched.parquet"):
    run(py + ["build_tweets_enriched.py"])

if not args.skip_labels:
    run(py + ["label_emotions.py"] + (["--sample", "20000", "--batch", "64"] if args.sample else []))

labels = "tweet_emotions_sample.parquet" if args.sample else "tweet_emotions.parquet"
run(py + ["analyze_time.py", labels])
run(py + ["analyze_age.py", labels])
print("\nresults/  figures/  are up to date")
