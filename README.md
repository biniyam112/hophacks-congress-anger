# What's making US angry?

**A study of emotional tone in 4.8 million tweets by 902 members of the U.S. Congress, 2011 to 2026.**

Every tweet is scored for eleven emotions with a transformer model, then aggregated to ask a measurement question:
what actually predicts the emotional tone of a political message? Timing, tenure, volume, audience, or position?

[**Read the story**](https://biniyam112.github.io/hophacks-tweet-sentiment/) · HopHacks 2026

This is a descriptive data project. It reports aggregate patterns in public messages and does not evaluate any
party, member or policy. Findings are stated symmetrically: where one group shows an effect, the mirror case is
reported alongside it.

## What the data shows

| | Finding |
|---|---|
| **Tone tracks position, not party** | Both major parties score about the same on anger when their party holds the presidency, and about the same as each other when it does not. The pattern repeats across four presidencies and reverses at each transition, so the effect follows who is in power rather than which party it is. The overall baseline has risen steadily across the whole period. |
| **Legislative deadlines drive the peaks** | Four of the five largest weekly peaks coincide with funding lapses. Across the 40 largest, roughly a third are budget and debt deadlines, about a quarter follow executive action, and the rest follow national tragedies, the only weeks when both parties move in the same direction at once. |
| **Tone follows the working calendar** | Tweets sent during office hours sit on the yearly average. The small share sent between 9 pm and 4 am scores higher in 13 of 16 years. The August recess is calmer in 14 of 16. In 6 of 7 elections the final four weeks are calmer than the rest of the year, not more heated. |
| **Predictability is mostly individual** | 29% of tweets cross the anger threshold. Party alone tells you nothing (still 29%). Party plus the current presidency moves it to 52%. Adding the identity of the individual account moves it to about 90%, so most of the signal is personal style rather than party. |
| **Posting volume correlates with tone** | Across 902 members, posting rate and anger share correlate at Spearman 0.31. High-volume accounts are generally more negative, with clear exceptions. |
| **The channel matters** | Only 2% of member-to-member retweets cross party lines, and those are the calmest messages in the data. 37% of public `.@` mentions cross party lines, and those are the most negative, and are concentrated on a small number of leadership accounts. |

## Contents

| Path | What it is |
|---|---|
| `site/` | The web story: six chapters plus two animated interludes ([a day on the Hill](https://biniyam112.github.io/hophacks-tweet-sentiment/timelapse.html), [emotional distance over time](https://biniyam112.github.io/hophacks-tweet-sentiment/romance.html)). Static HTML, CSS and Plotly, no build step. Deployed to GitHub Pages on every push. |
| `marimo/` | The interactive [marimo](https://marimo.io) notebook for the DSAI x marimo track: reactive charts, the forecast as a live function, a custom `anywidget`. See [`marimo/README.md`](marimo/README.md). |
| `deck/` | Generators for the 13-slide presentation (`build_deck.js`) and the 90-second animated explainer (`make_video.py`). |
| `results/`, `figures/` | Aggregated CSVs and static charts produced by the pipeline. |
| `score_text.py` | Score any text with the same models the project uses. |

## The pipeline

```bash
pip install -r requirements.txt
python run_pipeline.py          # everything; add --skip-labels to re-run only the analyses
python export_site_data.py      # refresh the JSON the site and notebook read
```

`run_pipeline.py` runs, in order:

1. `build_author_ages.py` matches 1,156 Twitter handles to bioguide IDs, birthdays and terms (handles first, including 14 yearly snapshots of the social-media file so former members are covered, then name plus state as a fallback).
2. `build_tweets_enriched.py` keeps in-office tweets and adds age at tweet, local hour, month and position in the election cycle.
3. `label_emotions.py` scores all 4.97M tweets with two RoBERTa models. Resumable in 50k chunks. About two hours on a laptop RTX 4050, roughly a day on CPU.
4. `analyze_time.py`, `analyze_age.py`, `analyze_seismograph.py`, `analyze_forecast.py`, `analyze_unity.py`, `analyze_network.py` write `results/*.csv`.
5. `export_site_data.py` and `export_romance_tweets.py` write the small JSON files the site and notebook read.

## Scoring your own text

```bash
python score_text.py "This is the third time the deadline has slipped and nobody will give me a straight answer."
```

```
  ANGRY  (anger 0.87, threshold 0.5)
  emotions:  disgust 0.90  anger 0.87  sadness 0.77  pessimism 0.29  fear 0.14
  sentiment: negative 0.92  neutral 0.08  positive 0.01
```

Also takes `--file` (one text per line), stdin, and `--json`. Importable as `from score_text import score, score_many`.

## Data and method

- **Tweets**: the HopHacks `congress-tweets-unified.parquet` (5.1M rows, not committed, 420 MB). We keep tweets by members of the House and Senate sent while in office from 2011 onward: 4.83M tweets by 902 members. Executive-branch accounts, pre-election personal tweets and a few corrupt pre-2011 rows are dropped.
- **Members**: the open [`unitedstates/congress-legislators`](https://github.com/unitedstates/congress-legislators) dataset for birthdays, terms and handles. 100% of members matched.
- **Scores**: [`cardiffnlp/twitter-roberta-base-emotion-multilabel-latest`](https://huggingface.co/cardiffnlp/twitter-roberta-base-emotion-multilabel-latest) gives 11 independent emotion probabilities; [`cardiffnlp/twitter-roberta-base-sentiment-latest`](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest) gives negative, neutral and positive. **Mean anger** is the average probability; a tweet is **angry** when P(anger) > 0.5.
- **Comparisons**: hour, month and age effects are computed within a single year and shown as deviation from that year's mean, so the long-run trend cannot masquerade as a daily or seasonal pattern. Election cycles are always shown separately, never pooled. Every party comparison is reported for both parties.
- **Limits**: scores are model estimates, spot-checked by hand, and a model's reading of tone is not a reader's. Sarcasm, quotation and reported speech are scored as written. Hours use each member's home-state clock, which is wrong whenever they are in Washington. The 2023 to 2024 part of the collection contains almost no retweets, so the retweet network excludes those years. We see explicit public mentions only, not replies or quote tweets. Accounts are often staff-operated, so this measures the tone of an office's output rather than a person's mood.

The full method note is the appendix of the [web story](https://biniyam112.github.io/hophacks-tweet-sentiment/#methods).

## License

Code is MIT. The tweet dataset belongs to its publisher; member data from `unitedstates/congress-legislators` is public domain.
