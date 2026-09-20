# What Makes Congress Angry? — marimo notebook

[![Open in molab](https://marimo.io/molab-shield.svg)](https://molab.marimo.io/notebooks)

An interactive marimo notebook that reproduces every chart of the *What Makes Congress Angry?* story and turns the
"anger forecast" into a live function: 4.8M tweets by 902 members of Congress (2011–2026), each scored for anger.

## Run it

**In molab (no install):** *New notebook → Mirror from GitHub* and paste the URL of `marimo/congress_anger.py` in this repository.
The notebook loads its data from this repository's `marimo/data/` folder over HTTPS, so nothing else is needed.

**Locally:**

```bash
pip install marimo plotly pandas anywidget
marimo edit marimo/congress_anger.py      # editor
marimo run  marimo/congress_anger.py      # app mode
```

## What's inside

| Section | Interactive |
|---|---|
| Executive summary · Problem statement · Data overview | `mo.stat` tiles |
| Ch. 1 — It's not you, it's the White House | party split / confidence-interval switches |
| Ch. 2 — The seismograph | emotion dropdown (anger, disgust, fear, sadness, joy), year range, 40 hover-labelled spikes |
| Ch. 3 — Anger keeps office hours | highlight-a-year slider over hour-of-day and month curves; 8 election cycles |
| Ch. 4 — The anger forecast | party / president / hour / member dropdowns → probability card; **custom `anywidget`** tweet strip with play + click-to-select; night owls; loudest members with thresholds |
| Ch. 5 — Two networks, one Congress | retweet vs `.@` call-out network on a shared "aisle" layout, edge threshold slider |
| Insight synthesis · Discussion & future work · Notes on marimo · Agentic tool usage | |

## Data

`marimo/data/` holds the aggregated results (~2 MB) produced by the analysis pipeline in the repository root
(`run_pipeline.py` → `analyze_*.py` → `export_site_data.py`). The 5M-row scored tweet table (650 MB) is not committed;
the pipeline rebuilds it from the HopHacks `congress-tweets-unified.parquet` plus `unitedstates/congress-legislators`.

`__marimo__/session/congress_anger.py.json` is the exported session so GitHub-mirrored previews render without running.
Regenerate it with `marimo export session marimo/congress_anger.py` after changing the notebook.
