# What Makes Congress Angry?

A HopHacks 2026 project: 4.8 million tweets by 902 members of Congress (2011–2026), each scored for anger, and a
field guide to what predicts it — the presidency, the clock, the person, and the medium.

- **`site/`** — the web story (static HTML + Plotly). Serve the folder and open `index.html`.
- **`marimo/`** — the interactive marimo notebook for the DSAI × marimo track (see `marimo/README.md`).
- **Pipeline** — `run_pipeline.py` runs `build_author_ages.py` → `build_tweets_enriched.py` → `label_emotions.py` (GPU)
  → `analyze_time.py`, `analyze_age.py`, `analyze_seismograph.py`, `analyze_forecast.py`, `analyze_unity.py`, `analyze_network.py`; then
  `export_site_data.py` writes the small JSON/CSV the site and notebook read. `results/` and `figures/` hold the outputs.

Data: the HopHacks `congress-tweets-unified.parquet` (not committed) and the open `unitedstates/congress-legislators` dataset.
Anger scores come from `cardiffnlp/twitter-roberta-base-emotion-multilabel-latest`.
