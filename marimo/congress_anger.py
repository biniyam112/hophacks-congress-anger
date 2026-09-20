import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium", app_title="What Makes Congress Angry?")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md(
        r"""
        # What Makes Congress Angry?

        **A field guide to Congressional anger, from 4.8 million tweets by 902 members of Congress, 2011–2026.**

        ## Executive summary

        We scored every tweet from every sitting member of the U.S. House and Senate for *anger* with a model trained on
        tweets, then asked when, who, and what for. Five findings, each one interactive below:

        1. **Anger belongs to the out-party.** Both parties were equally calm under Obama (0.18). Since 2017, whichever party
           just lost the White House is the angry one — and each hand-over ratchets the floor higher. 2025 is the angriest year on record.
        2. **Congress's most reliable source of anger is Congress.** Four of the five biggest weekly spikes are government shutdowns.
        3. **Anger keeps office hours.** Working hours sit on the average; after 9 pm is angrier in 13 of 16 years; August recess is the
           calm month; and the final four weeks before an election are *calmer*, not angrier.
        4. **You can forecast it.** Knowing the party tells you nothing; knowing the party *and the president* moves the odds from 29% to
           52%; knowing the person makes it near-certain (Chris Van Hollen, 9-to-5, 2025: 90%).
        5. **Nobody unites from opposition.** Civic-unity tweets belong to the party in power and polarizing tweets to the party out of it;
           the two parties' emotional profiles were closest in 2020 and have been far apart since 2021. 2025 is the most polarizing year on record.
        6. **Two networks, one Congress.** Only 2% of member retweets cross the aisle, and those are the calmest tweets we have.
           37% of `.@` call-outs cross the aisle, and those are the angriest — nearly all aimed at party leaders.

        This notebook reproduces every chart from our web story and adds what a notebook can do that a web page can't:
        every parameter is a live control, and the "anger forecast" is a function you can query.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Problem statement

        Political anger online is usually described anecdotally ("Twitter is a cesspool") or with a single trend line.
        Neither tells you the *mechanism*: is anger a property of people (temperament, age), of time (hours, seasons, elections),
        of position (in power vs. out), or of the medium (retweets vs. call-outs)? We treat anger as a **memetic phenomenon** —
        something that spreads and clusters — and try to locate where it actually lives.

        **Question:** given a tweet from a member of Congress, what predicts that it is angry — and how well?
        """
    )
    return


@app.cell
def _():
    # ---------- data loading: local files next to the notebook, else the GitHub raw copy (for molab) ----------
    import json
    from pathlib import Path
    from urllib.request import urlopen

    import pandas as pd

    GITHUB_RAW = "https://raw.githubusercontent.com/biniyam112/hophacks-congress-anger/main/marimo/data/"
    LOCAL = Path(__file__).parent / "data" if "__file__" in globals() else Path("data")

    def load_json(name: str) -> dict:
        """Read a JSON data file from disk if present, otherwise from the GitHub mirror."""
        p = LOCAL / f"{name}.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf8"))
        with urlopen(GITHUB_RAW + f"{name}.json") as r:
            return json.load(r)

    def load_csv(name: str) -> pd.DataFrame:
        p = LOCAL / f"{name}.csv"
        return pd.read_csv(p if p.exists() else GITHUB_RAW + f"{name}.csv")

    DATA_SOURCE = "local files" if (LOCAL / "meta.json").exists() else "GitHub"
    return DATA_SOURCE, load_csv, load_json, pd


@app.cell
def _(load_csv, load_json):
    META = load_json("meta")
    YEAR = load_json("year")
    OUTPARTY = load_json("outparty")
    SEISMO = load_json("seismograph")
    HOUR = load_json("hour")
    MONTH = load_json("month")
    CYCLE = load_json("cycle")
    FORECAST = load_json("forecast")
    STATEMENT = load_json("statement")
    LOUDEST = load_json("loudest")
    NETWORK = load_json("network")
    UNITY = load_json("unity")
    weekly = load_csv("seismograph_weekly")
    cells = load_csv("forecast_party_era_hour")
    member_cells = load_csv("forecast_member_era_hour")
    volume = load_csv("member_volume_vs_anger")
    return (
        CYCLE,
        FORECAST,
        HOUR,
        LOUDEST,
        META,
        MONTH,
        NETWORK,
        OUTPARTY,
        SEISMO,
        STATEMENT,
        UNITY,
        YEAR,
        cells,
        member_cells,
        volume,
        weekly,
    )


@app.cell
def _():
    # ---------- shared chart styling (matches the web story) ----------
    import plotly.graph_objects as go

    C = dict(
        ink="#0b0b0b", ink2="#52514e", muted="#898781", grid="#e1e0d9", axis="#c3c2b7",
        dem="#2a78d6", rep="#e34948", gold="#eda100", accent="#eb6834",
    )
    PARTY = {"Democrat": C["dem"], "Republican": C["rep"], "Independent": C["muted"]}

    def base_layout(**kw):
        """One consistent, recessive chart chrome for every figure."""
        lay = dict(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, system-ui, sans-serif", size=13, color=C["ink2"]),
            margin=dict(l=56, r=24, t=70, b=48), hovermode="x unified",
            title=dict(x=0, y=0.98, yanchor="top", font=dict(size=16, color=C["ink"])),
            hoverlabel=dict(bgcolor=C["ink"], bordercolor=C["ink"], font=dict(color="#fff", size=12.5)),
            legend=dict(orientation="h", x=0, y=1.0, yanchor="bottom", font=dict(size=12)),
            xaxis=dict(gridcolor=C["grid"], linecolor=C["axis"], zeroline=False, tickfont=dict(color=C["muted"])),
            yaxis=dict(gridcolor=C["grid"], linecolor=C["axis"], zeroline=False, tickfont=dict(color=C["muted"])),
        )
        for k, v in kw.items():
            if isinstance(v, dict) and isinstance(lay.get(k), dict):
                lay[k].update(v)
            else:
                lay[k] = v
        return lay

    def presidency_marks(xs=(2017, 2021, 2025), labels=("Trump", "Biden", "Trump II")):
        shapes = [dict(type="line", x0=x, x1=x, y0=0, y1=1, yref="paper", line=dict(color=C["grid"], width=1)) for x in xs]
        ann = [dict(x=x, y=1, yref="paper", text=t, showarrow=False, xanchor="left", yanchor="top", font=dict(size=11, color=C["muted"]))
               for x, t in zip(xs, labels)]
        return shapes, ann
    return C, PARTY, base_layout, go, presidency_marks


@app.cell
def _(DATA_SOURCE, META, mo):
    mo.md(
        rf"""
        ## Data overview

        The HopHacks `congress-tweets-unified` dataset holds 5.1M tweets from Congressional accounts. We kept tweets by members of the
        House and Senate **sent while they were in office**, from 2011 onward — dropping executive-branch accounts, pre-election personal
        tweets and a handful of pre-2011 rows. Every tweet was then scored by
        [`cardiffnlp/twitter-roberta-base-emotion-multilabel-latest`](https://huggingface.co/cardiffnlp/twitter-roberta-base-emotion-multilabel-latest),
        a RoBERTa model trained on tweets, which returns a probability of anger (and ten other emotions). Throughout, **mean anger** is the
        average probability and a tweet counts as **angry** above 0.5. Member ages and terms come from the open
        [`unitedstates/congress-legislators`](https://github.com/unitedstates/congress-legislators) dataset (100% of members matched).

        The 5M-row scored table is 650 MB, so this notebook loads the **aggregated results** (~2 MB, currently from *{DATA_SOURCE}*) that the
        analysis pipeline in the repository produces. The pipeline itself is reproducible with `python run_pipeline.py`.
        """
    )
    return


@app.cell
def _(META, YEAR, mo):
    mo.hstack(
        [
            mo.stat(value=f"{META['tweets']/1e6:.2f}M", label="tweets scored", caption="sitting members only", bordered=True),
            mo.stat(value=str(META["members"]), label="members of Congress", caption=f"{META['from'][:4]} – {META['to'][:7]}", bordered=True),
            mo.stat(value=f"{YEAR['anger'][0]:.2f} → {max(YEAR['anger']):.2f}", label="mean anger, 2011 → peak", caption="2025 is the angriest year", bordered=True),
            mo.stat(value=f"{YEAR['share_angry'][-1]*100:.0f}%", label="of 2026 tweets are angry", caption="vs 17% in 2011", bordered=True),
        ],
        widths="equal", gap=1,
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Core visualization

        ### Chapter 1 · It's not you. It's the White House.
        """
    )
    return


@app.cell
def _(mo):
    show_party = mo.ui.switch(value=True, label="split by party")
    show_ci = mo.ui.switch(value=False, label="show 95% confidence intervals")
    mo.hstack([show_party, show_ci], justify="start", gap=2)
    return show_ci, show_party


@app.cell
def _(C, YEAR, base_layout, go, mo, presidency_marks, show_ci, show_party):
    _fig = go.Figure()
    _shapes, _ann = presidency_marks()
    if show_party.value:
        _fig.add_scatter(x=YEAR["year"], y=YEAR["dem"], name="Democrats", mode="lines+markers", line=dict(color=C["dem"], width=2), hovertemplate="%{y:.3f}")
        _fig.add_scatter(x=YEAR["year"], y=YEAR["rep"], name="Republicans", mode="lines+markers", line=dict(color=C["rep"], width=2), hovertemplate="%{y:.3f}")
        _fig.add_scatter(x=YEAR["year"], y=YEAR["anger"], name="All", mode="lines", line=dict(color=C["muted"], width=1.5, dash="dot"), hovertemplate="%{y:.3f}")
    else:
        _fig.add_scatter(
            x=YEAR["year"], y=YEAR["anger"], name="All members", mode="lines+markers", line=dict(color=C["ink"], width=2),
            error_y=dict(type="data", array=[1.96 * s for s in YEAR["se"]], visible=show_ci.value, color=C["muted"]),
            hovertemplate="%{y:.3f}",
        )
    _fig.update_layout(base_layout(
        title=dict(text="Mean anger by year" + (" — the X" if show_party.value else " — doubled, in two steps"), font=dict(size=16, color=C["ink"])),
        shapes=_shapes, annotations=_ann, yaxis=dict(title="mean anger score", range=[0.1, 0.55]), xaxis=dict(dtick=1), height=380,
    ))
    mo.vstack([
        mo.ui.plotly(_fig),
        mo.md(
            "Anger sat below 0.21 through the Obama years, jumped to 0.29 in 2017 and hit 0.44 in 2025. Split by party the trend becomes an **X**: "
            "Democrats spike when Trump takes office (2017, 2025), Republicans spike under Biden. The lines cross at every inauguration."
        ),
    ])
    return


@app.cell
def _(C, OUTPARTY, base_layout, go, mo):
    _lab = [f"{p} ({q})" for p, q in zip(OUTPARTY["president"], OUTPARTY["president_party"])]
    _fig = go.Figure()
    _fig.add_bar(x=_lab, y=OUTPARTY["dem"], name="Democrats", marker_color=C["dem"], text=[f"{v:.2f}" for v in OUTPARTY["dem"]], textposition="outside")
    _fig.add_bar(x=_lab, y=OUTPARTY["rep"], name="Republicans", marker_color=C["rep"], text=[f"{v:.2f}" for v in OUTPARTY["rep"]], textposition="outside")
    _fig.update_layout(base_layout(barmode="group", bargap=0.35, height=360, title=dict(text="Same rule, four presidencies", font=dict(size=16, color=C["ink"])),
                                   yaxis=dict(title="mean anger score", range=[0, 0.58]), xaxis=dict(title="who holds the White House")))
    mo.vstack([
        mo.ui.plotly(_fig),
        mo.callout(
            mo.md("Under Obama both parties were equally calm (0.18 vs 0.19). Since then the out-party has been 0.12–0.17 angrier than the in-party — "
                  "and today's *in*-party (0.35) is angrier than 2017's *out*-party (0.34). **The floor never resets.**"),
            kind="info",
        ),
    ])
    return


@app.cell
def _(mo):
    mo.md(r"""### Chapter 2 · The seismograph""")
    return


@app.cell
def _(mo, weekly):
    emotion = mo.ui.dropdown(
        options={"anger": "anger", "disgust": "disgust", "fear": "fear", "sadness": "sadness", "joy": "joy"},
        value="anger", label="emotion",
    )
    _years = sorted({int(w[:4]) for w in weekly.wk})
    year_range = mo.ui.range_slider(start=min(_years), stop=max(_years), step=1, value=[min(_years), max(_years)], label="years")
    mo.hstack([emotion, year_range], justify="start", gap=2)
    return emotion, year_range


@app.cell
def _(C, SEISMO, base_layout, emotion, go, mo, pd, weekly, year_range):
    _w = weekly[(weekly.wk.str[:4].astype(int) >= year_range.value[0]) & (weekly.wk.str[:4].astype(int) <= year_range.value[1])].copy()
    _col = emotion.value
    _w["base"] = _w[_col].rolling(13, center=True, min_periods=5).median()
    _fig = go.Figure()
    _fig.add_scatter(x=_w.wk, y=_w.base, name="13-week baseline", line=dict(color=C["axis"], width=1), hoverinfo="skip")
    _fig.add_scatter(x=_w.wk, y=[max(a, b) for a, b in zip(_w[_col], _w.base)], line=dict(width=0), fill="tonexty", fillcolor="rgba(227,73,72,0.28)", hoverinfo="skip", showlegend=False)
    if _col == "anger":
        _fig.add_scatter(x=_w.wk, y=_w.anger_dem, name="Democrats", line=dict(color=C["dem"], width=1), opacity=0.75, hovertemplate="%{y:.3f}")
        _fig.add_scatter(x=_w.wk, y=_w.anger_rep, name="Republicans", line=dict(color=C["rep"], width=1), opacity=0.75, hovertemplate="%{y:.3f}")
    _fig.add_scatter(x=_w.wk, y=_w[_col], name="All members", line=dict(color=C["ink"], width=1.4), hovertemplate="%{y:.3f}")
    if _col == "anger":
        _sp = [s for s in SEISMO["spikes"] if year_range.value[0] <= int(s["week"][:4]) <= year_range.value[1]]
        _fig.add_scatter(
            x=[s["week"] for s in _sp], y=[s["anger"] + 0.02 for s in _sp], name="spike (hover)", mode="markers",
            marker=dict(symbol="diamond", size=9, color=C["rep"], line=dict(color="#fff", width=1.5)),
            text=[f"<b>{s['event']}</b><br>+{s['excess']:.2f} vs baseline · driven by {s['driven_by']}" for s in _sp],
            hovertemplate="%{x|%b %d, %Y}<br>%{text}<extra></extra>",
        )
    _fig.update_layout(base_layout(hovermode="closest", height=440, title=dict(text=f"Weekly mean {_col}, {year_range.value[0]}–{year_range.value[1]}", font=dict(size=16, color=C["ink"])),
                                   yaxis=dict(title=f"mean {_col} score, weekly")))
    seismo_chart = mo.ui.plotly(_fig)
    seismo_chart
    return (seismo_chart,)


@app.cell
def _(SEISMO, mo, pd):
    _sp = pd.DataFrame(SEISMO["spikes"])[["week", "event", "excess", "driven_by", "hashtags"]].head(15)
    mo.vstack([
        mo.md(
            "Anger in each week relative to the surrounding three months. **Four of the top five spikes are government shutdowns**; "
            "January 6 is the only external event in that tier. Before 2017 the blue and red lines are braided together — the parties got angry "
            "*together*. From 2017 on they split into two bands and swap places at each inauguration."
        ),
        mo.accordion({"The 15 biggest spikes (hand-labelled from that week's over-represented words and hashtags)": mo.ui.table(_sp, selection=None, page_size=15)}),
    ])
    return


@app.cell
def _(mo):
    mo.md(r"""### Chapter 3 · Anger keeps office hours""")
    return


@app.cell
def _(mo):
    highlight_year = mo.ui.slider(start=2011, stop=2026, step=1, value=2025, label="highlight a year")
    highlight_year
    return (highlight_year,)


@app.cell
def _(C, HOUR, MONTH, base_layout, go, highlight_year, mo):
    def _curves(d, title, xlab, tickvals, ticktext, band, band_label):
        fig = go.Figure()
        for yr, ys in d["years"].items():
            hl = int(yr) == highlight_year.value
            fig.add_scatter(x=d["x"], y=ys, name=yr, mode="lines", line=dict(color=C["accent"] if hl else C["muted"], width=2.5 if hl else 1),
                            opacity=1 if hl else 0.3, hovertemplate=f"{yr}: %{{y:+.3f}}<extra></extra>", showlegend=False)
        fig.add_scatter(x=d["x"], y=d["mean"], name="all years", mode="lines", line=dict(color=C["ink"], width=2.5), hovertemplate="mean: %{y:+.3f}<extra></extra>", showlegend=False)
        fig.update_layout(base_layout(
            hovermode="closest", height=340, title=dict(text=title, font=dict(size=15, color=C["ink"])),
            yaxis=dict(title="Δ vs. that year's mean", zeroline=True, zerolinecolor=C["axis"]),
            xaxis=dict(title=xlab, tickvals=tickvals, ticktext=ticktext),
            shapes=[dict(type="rect", x0=b[0], x1=b[1], y0=0, y1=1, yref="paper", fillcolor="rgba(235,104,52,0.10)", line=dict(width=0)) for b in band],
            annotations=[dict(x=(band[0][0] + band[0][1]) / 2, y=1, yref="paper", text=band_label, showarrow=False, yanchor="top", font=dict(size=11, color=C["accent"]))],
        ))
        return mo.ui.plotly(fig)

    _hour = _curves(HOUR, "By hour of day (home-state time)", "hour", [0, 3, 6, 9, 12, 15, 18, 21, 23],
                    ["12am", "3am", "6am", "9am", "noon", "3pm", "6pm", "9pm", "11pm"], [[20.5, 23.5], [-0.5, 4.5]], "after dark")
    _month = _curves(MONTH, "By month", "month", list(range(1, 13)), ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                     [[7.5, 8.5]], "August recess")
    mo.vstack([
        mo.md(f"**Δ anger vs. each year's own mean — {highlight_year.value} in orange**"),
        mo.hstack([_hour, _month], widths="equal"),
        mo.md(
            f"Grey lines are individual years, **orange is {highlight_year.value}**, black is the tweet-weighted mean; every curve is measured against its own "
            "year so the 2011→2026 trend can't masquerade as a daily pattern. Working hours sit exactly on the average; 9 pm–4 am is above it in 13 of 16 years "
            "(but only 4% of tweets are sent then). August is below average in 14 of 16 years."
        ),
    ])
    return


@app.cell
def _(C, CYCLE, base_layout, go, mo):
    from plotly.subplots import make_subplots

    _cycles = sorted(int(k) for k in CYCLE["cycles"])
    _fig = make_subplots(rows=2, cols=4, subplot_titles=[f"{c} {'presidential' if c % 4 == 0 else 'midterm'}" for c in _cycles], vertical_spacing=0.16, horizontal_spacing=0.05)
    for _i, _c in enumerate(_cycles):
        _d = CYCLE["cycles"][str(_c)]
        _r, _col = _i // 4 + 1, _i % 4 + 1
        _xs = [-w for w in _d["weeks"]]
        _fig.add_scatter(x=_xs, y=_d["dem"], line=dict(color=C["dem"], width=0.9), opacity=0.8, showlegend=False, hovertemplate="D %{y:.3f}<extra></extra>", row=_r, col=_col)
        _fig.add_scatter(x=_xs, y=_d["rep"], line=dict(color=C["rep"], width=0.9), opacity=0.8, showlegend=False, hovertemplate="R %{y:.3f}<extra></extra>", row=_r, col=_col)
        _fig.add_scatter(x=_xs, y=_d["anger"], line=dict(color=C["ink"], width=1.3), showlegend=False, hovertemplate="%{x} wk: %{y:.3f}<extra></extra>", row=_r, col=_col)
        _fig.add_vline(x=0, line=dict(color=C["axis"], width=1, dash="dot"), row=_r, col=_col)
    _fig.update_layout(base_layout(hovermode="closest", height=500, margin=dict(l=40, r=12, t=60, b=40),
                                   title=dict(text="Eight election cycles, no build-up (weeks before election day →)", font=dict(size=15, color=C["ink"]))))
    _fig.update_xaxes(gridcolor=C["grid"], tickfont=dict(size=10, color=C["muted"]), range=[-105, 2])
    _fig.update_yaxes(gridcolor=C["grid"], tickfont=dict(size=10, color=C["muted"]), range=[0.05, 0.65])
    _fin = CYCLE["final"]
    _bar = go.Figure()
    _bar.add_bar(x=_fin["year"], y=_fin["rest"], name="rest of the year", marker_color=C["axis"], hovertemplate="%{y:.3f}")
    _bar.add_bar(x=_fin["year"], y=_fin["last4"], name="final 4 weeks", marker_color=C["ink"], hovertemplate="%{y:.3f}")
    _bar.update_layout(base_layout(barmode="group", height=300, title=dict(text="The final stretch is calmer", font=dict(size=15, color=C["ink"])),
                                   yaxis=dict(title="mean anger"), xaxis=dict(dtick=2)))
    mo.vstack([
        mo.ui.plotly(_fig),
        mo.hstack([mo.ui.plotly(_bar), mo.md(
            "There is no ramp into November in any cycle; the spikes are events, not the calendar. In **six of seven elections the closing four weeks are "
            "calmer** than the rest of the year — members switch to hopeful campaign messaging. Only 2020 broke the pattern, barely."
        )], widths=[3, 2], align="center"),
    ])
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ### Chapter 4 · The anger forecast

        This is the part a notebook does better than a web page: the forecast is a *function*. Pick what you know about a tweet
        and read off the probability that it's angry. Every "%" is the share of tweets in that cell with P(anger) > 0.5.
        """
    )
    return


@app.cell
def _(cells, member_cells, mo):
    party_pick = mo.ui.dropdown(options=["(unknown)", "Democrat", "Republican"], value="(unknown)", label="party")
    era_pick = mo.ui.dropdown(options=["(unknown)", "Obama", "Trump", "Biden", "Trump II"], value="(unknown)", label="who's president")
    band_pick = mo.ui.dropdown(options=["(unknown)"] + sorted(cells.band.unique()), value="(unknown)", label="hour band")
    _members = sorted(member_cells.name.unique())
    member_pick = mo.ui.dropdown(options=["(unknown)"] + _members, value="(unknown)", label="specific member", searchable=True)
    mo.hstack([party_pick, era_pick, band_pick, member_pick], justify="start", gap=1.5, wrap=True)
    return band_pick, era_pick, member_pick, party_pick


@app.cell
def _(FORECAST, band_pick, cells, era_pick, member_cells, member_pick, mo, party_pick):
    def forecast(party, era, band, member):
        """Return (probability, n tweets, description) for the most specific cell the inputs describe."""
        if member != "(unknown)":
            m = member_cells[member_cells.name == member]
            if era != "(unknown)":
                m = m[m.era == era]
            if band != "(unknown)":
                m = m[m.band == band]
            if len(m):
                p = (m.share_angry * m.n).sum() / m.n.sum()
                return p, int(m.n.sum()), f"{member}" + (f" during {era}" if era != "(unknown)" else "") + (f", {band}" if band != "(unknown)" else "")
        c = cells.copy()
        parts = []
        if party != "(unknown)":
            c = c[c.party == party]; parts.append(f"a {party}")
        if era != "(unknown)":
            c = c[c.era == era]; parts.append(f"during {era}")
        if band != "(unknown)":
            c = c[c.band == band]; parts.append(f"at {band}")
        if not len(c):
            return None, 0, "no data for that combination"
        p = (c.share_angry * c.n).sum() / c.n.sum()
        return p, int(c.n.sum()), ", ".join(parts) if parts else "nothing known"

    _p, _n, _desc = forecast(party_pick.value, era_pick.value, band_pick.value, member_pick.value)
    _base = FORECAST["baseline"]
    if _p is None:
        _card = mo.callout(mo.md(f"No tweets match **{_desc}** — try fewer constraints."), kind="warn")
    else:
        _verdict = "it's an angry tweet." if _p >= 0.75 else "it's probably angry." if _p >= 0.5 else "it's probably not angry." if _p < 0.25 else "it's a coin flip."
        _card = mo.Html(
            f"""
            <div style="text-align:center;padding:18px 8px 6px">
              <div style="font-family:Georgia,serif;font-style:italic;font-size:26px;line-height:1.3;color:#0b0b0b">
                If we know <b>{_desc}</b>,<br>{_verdict}</div>
              <div style="font-family:ui-monospace,monospace;font-size:13px;color:#e34948;margin-top:10px">
                — {_p*100:.0f}% of {_n:,} tweets were angry &nbsp;·&nbsp; Congress average {_base*100:.0f}%</div>
              <div style="margin:16px auto 0;max-width:520px;height:14px;background:#f1f0ec;border-radius:7px;position:relative">
                <div style="width:{_p*100:.1f}%;height:100%;background:{'#e34948' if _p >= 0.5 else '#0b0b0b'};border-radius:7px"></div>
                <div style="position:absolute;left:{_base*100:.1f}%;top:-4px;bottom:-4px;border-left:1px dashed #898781"></div>
              </div>
            </div>"""
        )
    _card
    return (forecast,)


@app.cell
def _(FORECAST, mo, pd):
    _L = pd.DataFrame(FORECAST["ladder"])
    _labels = {
        "nothing": "Nothing", "party = Democrat": "It's a Democrat", "hour band = 00-04": "It's 12–4 am",
        "party = Democrat, era = Trump II": "A Democrat, Trump's 2nd term", "party = Democrat, era = Trump II, 09-17": "…and it's working hours",
        "Chris Van Hollen, era = Trump II, 09-17": "…and it's Chris Van Hollen", "party = Democrat, era = Obama, 00-04": "A Democrat at 2 am, Obama era",
    }
    _L["label"] = _L.known.map(_labels)
    _L = pd.concat([_L.iloc[[0]], _L.iloc[1:].sort_values("p")])
    mo.accordion({
        "The forecast ladder — how each thing you learn moves the odds": mo.ui.table(
            _L[["label", "p"]].rename(columns={"label": "what you know", "p": "P(angry)"}).assign(**{"P(angry)": lambda d: (d["P(angry)"] * 100).round(0).astype(int).astype(str) + "%"}),
            selection=None,
        )
    })
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        #### A forecast you can set your watch by — custom widget

        The strip below is a **custom `anywidget`**: every dot is one of Patty Murray's 418 tweets sent between midnight and 5 am on her
        home-state clock during Trump's second term (she's usually in Washington, where it's breakfast). Red is angry, grey is not.
        Press **play** to watch them land; **click any dot** and the tweet is sent back to Python and shown underneath — the selection is a
        real Python value other cells can react to.
        """
    )
    return


@app.cell
def _(STATEMENT, mo):
    import anywidget
    import traitlets

    class TweetStrip(anywidget.AnyWidget):
        """A time-strip of tweets with an animated 'play' and a click-to-select dot. `selected` syncs back to Python."""

        _esm = r"""
        function render({ model, el }) {
          const T = model.get("tweets"), t0 = model.get("t0"), t1 = model.get("t1");
          el.innerHTML = "";
          const wrap = document.createElement("div"); wrap.className = "ts-wrap"; el.appendChild(wrap);
          const W = Math.max(320, el.clientWidth || 700), H = 120, padL = 16, padR = 16, y0 = 52;
          const ns = "http://www.w3.org/2000/svg";
          const svg = document.createElementNS(ns, "svg"); svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.setAttribute("width", "100%");
          const mk = (tag, a) => { const e = document.createElementNS(ns, tag); for (const k in a) e.setAttribute(k, a[k]); svg.appendChild(e); return e; };
          const xs = (t) => padL + ((t - t0) / (t1 - t0)) * (W - padL - padR);
          mk("line", { x1: padL, x2: W - padR, y1: y0, y2: y0, class: "ts-axis" });
          for (let d = new Date(2025, 0, 1); d.getTime() <= t1; d.setMonth(d.getMonth() + 3)) {
            const x = xs(d.getTime()); if (x < padL) continue;
            const lab = mk("text", { x, y: y0 + 44, "text-anchor": "middle", class: "ts-tick" });
            lab.textContent = d.getMonth() === 0 ? String(d.getFullYear()) : ["Jan", "Apr", "Jul", "Oct"][d.getMonth() / 3];
          }
          const dots = T.map((tw, i) => {
            const angry = tw.a > 0.5, jit = ((i * 7919) % 23) - 11;
            const c = mk("circle", { cx: xs(Date.parse(tw.t.replace(" ", "T"))), cy: y0 + (angry ? -14 : 14) + jit * 0.9, r: 4, class: "ts-dot " + (angry ? "angry" : "calm") });
            c.addEventListener("click", () => { model.set("selected", i); model.save_changes(); dots.forEach(d => d.classList.remove("sel")); c.classList.add("sel"); });
            return c;
          });
          wrap.appendChild(svg);
          const ui = document.createElement("div"); ui.className = "ts-ui"; wrap.appendChild(ui);
          const play = document.createElement("button"); play.textContent = "▶ Play"; ui.appendChild(play);
          const reset = document.createElement("button"); reset.textContent = "↻ Reset"; ui.appendChild(reset);
          const tally = document.createElement("span"); tally.className = "ts-tally"; ui.appendChild(tally);
          let k = 0, angryN = 0, timer = null;
          const showAll = () => { dots.forEach(d => d.classList.add("on")); k = T.length; angryN = T.filter(t => t.a > 0.5).length; tally.textContent = `${angryN} angry of ${k} (${Math.round(100 * angryN / k)}%)`; };
          const doReset = () => { clearInterval(timer); timer = null; dots.forEach(d => d.classList.remove("on")); k = 0; angryN = 0; tally.textContent = ""; play.textContent = "▶ Play"; };
          play.addEventListener("click", () => {
            if (timer) { clearInterval(timer); timer = null; play.textContent = "▶ Play"; return; }
            if (k >= T.length) doReset();
            play.textContent = "❚❚ Pause";
            timer = setInterval(() => {
              if (k >= T.length) { clearInterval(timer); timer = null; play.textContent = "▶ Play"; return; }
              dots[k].classList.add("on"); if (T[k].a > 0.5) angryN++; k++;
              tally.textContent = `${angryN} angry of ${k} shown (${Math.round(100 * angryN / k)}%)`;
            }, 28);
          });
          reset.addEventListener("click", doReset);
          showAll();
        }
        export default { render };
        """
        _css = r"""
        .ts-wrap { font-family: Inter, system-ui, sans-serif; }
        .ts-axis { stroke: #c3c2b7; } .ts-tick { font-size: 11px; fill: #898781; }
        .ts-dot { cursor: pointer; opacity: 0; transition: opacity .15s; } .ts-dot.on { opacity: 1; }
        .ts-dot.angry { fill: #e34948; } .ts-dot.calm { fill: #fff; stroke: #898781; stroke-width: 1.5; }
        .ts-dot.sel, .ts-dot:hover { stroke: #0b0b0b; stroke-width: 2.5; }
        .ts-ui { display: flex; gap: 10px; align-items: center; justify-content: center; margin-top: 4px; }
        .ts-ui button { font-family: ui-monospace, monospace; font-size: 13px; padding: 5px 12px; border: 1px solid #c3c2b7; background: #fff; border-radius: 4px; cursor: pointer; }
        .ts-tally { font-family: ui-monospace, monospace; font-size: 13px; color: #52514e; }
        """
        tweets = traitlets.List([]).tag(sync=True)
        t0 = traitlets.Float(0).tag(sync=True)
        t1 = traitlets.Float(0).tag(sync=True)
        selected = traitlets.Int(-1).tag(sync=True)

    from datetime import datetime as _dt

    _tw = STATEMENT["tweets"]
    strip = mo.ui.anywidget(TweetStrip(
        tweets=_tw,
        t0=_dt.fromisoformat(STATEMENT["from"]).timestamp() * 1000,
        t1=_dt.fromisoformat(STATEMENT["to"]).timestamp() * 1000,
    ))
    mo.vstack([
        mo.Html(
            f"""<div style="text-align:center;font-family:Georgia,serif;font-style:italic;font-size:24px;line-height:1.3">
            If Patty Murray tweets before sunrise during Trump's second term,<br>it's an angry tweet.</div>
            <div style="text-align:center;font-family:ui-monospace,monospace;font-size:13px;color:#e34948;margin:8px 0 14px">
            — {STATEMENT['p']*100:.0f}% of {STATEMENT['n']} tweets, {STATEMENT['band']} Pacific, {STATEMENT['from'][:7]} – {STATEMENT['to'][:7]}</div>"""
        ),
        strip,
    ])
    return (strip,)


@app.cell
def _(STATEMENT, mo, strip):
    _i = strip.selected
    if _i is None or _i < 0:
        mo.md("*Click a dot to read that tweet.*")
    else:
        _t = STATEMENT["tweets"][_i]
        mo.callout(mo.md(f"**{_t['t']}** · anger {_t['a']:.2f}\n\n{_t['x']}"), kind="danger" if _t["a"] > 0.5 else "neutral")
    return


@app.cell
def _(C, FORECAST, PARTY, base_layout, go, mo):
    _O = FORECAST["owls"] + FORECAST["larks"]
    _gap = 1.6
    _y = [i if i < len(FORECAST["owls"]) else i + _gap for i in range(len(_O))]
    _fig = go.Figure()
    for _r, _yy in zip(_O, _y):
        _fig.add_scatter(x=[_r["day"], _r["night"]], y=[_yy, _yy], mode="lines", line=dict(color=PARTY[_r["party"]], width=4), opacity=0.5, hoverinfo="skip", showlegend=False)
        _fig.add_annotation(x=_r["night"], y=_yy, ax=_r["day"], ay=_yy, axref="x", ayref="y", showarrow=True, arrowhead=2, arrowwidth=1.5, arrowcolor=PARTY[_r["party"]], standoff=9, startstandoff=9, text="")
        _fig.add_annotation(x=min(_r["day"], _r["night"]), y=_yy, text=f"{min(_r['day'], _r['night'])*100:.0f}%", showarrow=False, xanchor="right", xshift=-12, font=dict(size=11))
        _fig.add_annotation(x=max(_r["day"], _r["night"]), y=_yy, text=f"{max(_r['day'], _r['night'])*100:.0f}%", showarrow=False, xanchor="left", xshift=12, font=dict(size=11))
    _fig.add_scatter(x=[r["day"] for r in _O], y=_y, mode="markers", name="☀ daytime, 9–5", marker=dict(color=C["gold"], size=14, line=dict(color="#fff", width=2)), text=[r["name"] for r in _O], hovertemplate="%{text}<br>daytime: %{x:.0%} angry<extra></extra>")
    _fig.add_scatter(x=[r["night"] for r in _O], y=_y, mode="markers", name="☾ late night, 9 pm – 4 am", marker=dict(color="#0d366b", size=14, line=dict(color="#fff", width=2)), text=[r["name"] for r in _O], hovertemplate="%{text}<br>late night: %{x:.0%} angry<extra></extra>")
    _div = len(FORECAST["owls"]) - 1 + (_gap + 1) / 2
    _fig.add_annotation(x=0.5, xref="paper", y=-0.85, text="NIGHT OWLS — angrier after dark", showarrow=False, font=dict(size=11, color=C["muted"]))
    _fig.add_annotation(x=0.5, xref="paper", y=_div, text="MORNING PEOPLE — angrier by day", showarrow=False, font=dict(size=11, color=C["muted"]))
    _fig.update_layout(base_layout(
        hovermode="closest", height=440, margin=dict(l=10, r=24, t=70, b=44),
        title=dict(text="Night owls and morning people", font=dict(size=16, color=C["ink"])),
        xaxis=dict(range=[0, 0.82], tickformat=".0%", title="share of tweets that are angry"),
        yaxis=dict(showgrid=False, range=[_y[-1] + 0.7, -1.2], tickvals=_y, ticktext=[r["name"] for r in _O], tickfont=dict(size=13, color=C["ink"])),
    ))
    mo.vstack([
        mo.ui.plotly(_fig),
        mo.md("Members whose late-night tweets are far angrier than their daytime ones — and the reverse. Mike Levin is a mild 25% by day and 56% after dark; "
              "Bill Hagerty is the opposite. *Do not tweet at Mazie Hirono after midnight.*"),
    ])
    return


@app.cell
def _(mo, volume):
    min_tweets = mo.ui.slider(start=500, stop=10000, step=500, value=2000, label="minimum tweets per member", show_value=True)
    top_n = mo.ui.slider(start=8, stop=25, step=1, value=12, label="how many of the loudest", show_value=True)
    mo.hstack([min_tweets, top_n], justify="start", gap=2)
    return min_tweets, top_n


@app.cell
def _(C, LOUDEST, PARTY, base_layout, go, min_tweets, mo, top_n, volume):
    _v = volume[volume.n >= min_tweets.value].sort_values("tweets_per_day", ascending=False).head(top_n.value)
    _labels = [f"{r.name} ({r.party[0]}-{r.state})" for r in _v.itertuples()]
    _isB = [("Booker" in r.name) for r in _v.itertuples()]
    _fig = go.Figure()
    _fig.add_bar(y=_labels, x=_v.tweets_per_day * _v.share_angry, orientation="h", name="angry", marker_color=C["rep"],
                 customdata=list(zip(_v.tweets_per_day.round(1), (_v.share_angry * 100).round(0), _v.n)), hovertemplate="%{y}<br>%{customdata[0]} tweets/day, %{customdata[1]}% angry (%{customdata[2]} tweets)<extra></extra>")
    _fig.add_bar(y=_labels, x=_v.tweets_per_day * (1 - _v.share_angry), orientation="h", name="not angry",
                 marker_color=[C["dem"] if b else C["grid"] for b in _isB],
                 text=[f"{p*100:.0f}% angry" + (" — the prolific optimist" if b else "") for p, b in zip(_v.share_angry, _isB)], textposition="outside", cliponaxis=False,
                 textfont=dict(color=[C["dem"] if b else C["ink2"] for b in _isB]),
                 customdata=list(zip(_v.tweets_per_day.round(1), (_v.share_angry * 100).round(0), _v.n)), hovertemplate="%{y}<br>%{customdata[0]} tweets/day, %{customdata[1]}% angry (%{customdata[2]} tweets)<extra></extra>")
    _fig.add_vline(x=LOUDEST["median_per_day"], line=dict(color=C["axis"], width=1, dash="dot"), annotation_text="typical member", annotation_position="top")
    _fig.update_layout(base_layout(barmode="stack", hovermode="closest", height=30 * len(_v) + 120, margin=dict(l=10, r=200, t=70, b=48), legend=dict(x=1, xanchor="right", y=1.0, yanchor="bottom"),
                                   title=dict(text="The loudest people in Congress", font=dict(size=16, color=C["ink"])),
                                   xaxis=dict(title="tweets per day"), yaxis=dict(autorange="reversed", showgrid=False, automargin=True)))
    mo.vstack([
        mo.ui.plotly(_fig),
        mo.md("Volume and anger rise together — Spearman ρ = 0.31 across all 902 members; you cannot post ten times a day about ribbon-cuttings. "
              "**Everyone who tweets more than seven times a day is angrier than average. Except Cory Booker.**"),
    ])
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ### Chapter 5 · Nobody unites from opposition

        Anger is one emotion; we scored eleven. Sorting tweets into two registers — **civic unity** (positive tone *and* explicit
        cross-party language: bipartisan, across the aisle, common ground, work together) and **polarizing** (anger or disgust *and* a
        reference to the other party or its leaders) — shows the Chapter 1 flip in both directions at once. Gratitude tweets
        ("thank you", "proud to") are counted separately, not as unity.
        """
    )
    return


@app.cell
def _(mo):
    unity_view = mo.ui.radio(options={"civic unity": "civic", "gratitude": "gratitude"}, value="civic unity", label="positive register")
    unity_view
    return (unity_view,)


@app.cell
def _(C, UNITY, base_layout, go, mo, unity_view):
    from plotly.subplots import make_subplots as _mk

    _U = UNITY
    _pos = _U[unity_view.value]
    _fig = _mk(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12, subplot_titles=["Polarizing — angry or disgusted, aimed at the other party", f"{unity_view.value.title()} — positive, " + ("explicitly cross-party" if unity_view.value == "civic" else "thanks / proud / honored")])
    _fig.add_scatter(x=_U["year"], y=_U["polarizing"]["dem"], name="Democrats", mode="lines+markers", line=dict(color=C["dem"], width=2), hovertemplate="%{y:.1%}", row=1, col=1)
    _fig.add_scatter(x=_U["year"], y=_U["polarizing"]["rep"], name="Republicans", mode="lines+markers", line=dict(color=C["rep"], width=2), hovertemplate="%{y:.1%}", row=1, col=1)
    _fig.add_scatter(x=_U["year"], y=_pos["dem"], name="Democrats", mode="lines+markers", line=dict(color=C["dem"], width=2, dash="dot"), marker=dict(symbol="diamond"), showlegend=False, hovertemplate="%{y:.1%}", row=2, col=1)
    _fig.add_scatter(x=_U["year"], y=_pos["rep"], name="Republicans", mode="lines+markers", line=dict(color=C["rep"], width=2, dash="dot"), marker=dict(symbol="diamond"), showlegend=False, hovertemplate="%{y:.1%}", row=2, col=1)
    for _x, _t in [(2017, "Trump"), (2021, "Biden"), (2025, "Trump II")]:
        _fig.add_vline(x=_x, line=dict(color=C["grid"], width=1), annotation_text=_t, annotation_position="top left", annotation_font=dict(size=11, color=C["muted"]))
    _fig.update_layout(base_layout(height=560, title=dict(text="The mirror: share of each party's tweets per year", font=dict(size=16, color=C["ink"])), legend=dict(y=1.0)))
    _fig.update_xaxes(dtick=1, gridcolor=C["grid"]); _fig.update_yaxes(tickformat=".0%", rangemode="tozero", gridcolor=C["grid"])
    mo.vstack([
        mo.ui.plotly(_fig),
        mo.md(
            "Polarizing tweets belong to the out-party — Democrats 17% in 2017, Republicans 25% in 2022, Democrats **35% in 2025**, the record. "
            "Civic unity belongs to the in-party: Republicans' peak (4.2%) is 2018, Democrats' (5.6%) is 2024; in 2025 both fall to 2.6%. "
            "Switch to *gratitude* and the same flip appears in the ribbon-cutting register."
        ),
    ])
    return


@app.cell
def _(C, UNITY, base_layout, go, mo):
    _D = UNITY["distance"]
    _notes = {2017: "anger", 2020: "COVID: closest since 2011", 2021: "optimism", 2025: "disgust"}
    _fig = go.Figure()
    _fig.add_scatter(x=_D["year"], y=_D["d"], mode="lines+markers", line=dict(color=C["ink"], width=2.2), marker=dict(size=8), fill="tozeroy", fillcolor="rgba(11,11,11,0.06)",
                     text=[f"biggest gap: <b>{g}</b> ({s})" for g, s in zip(_D["gap"], _D["sign"])], hovertemplate="%{x}: distance %{y:.2f}<br>%{text}<extra></extra>", showlegend=False)
    for _x, _t in _notes.items():
        _i = _D["year"].index(_x)
        _fig.add_annotation(x=_x, y=_D["d"][_i], text=_t, showarrow=True, arrowhead=0, arrowcolor=C["muted"], ax=0, ay=40 if _x == 2020 else -26, font=dict(size=11, color=C["dem"] if _x == 2020 else C["ink"]))
    _fig.update_layout(base_layout(hovermode="closest", height=380, title=dict(text="How far apart the parties feel", font=dict(size=16, color=C["ink"])),
                                   xaxis=dict(dtick=1), yaxis=dict(title="distance between party emotion profiles", rangemode="tozero")))
    mo.vstack([
        mo.ui.plotly(_fig),
        mo.md(
            "Each year, the mean of all eleven emotions for each party; the line is the Euclidean distance between the two profiles. The parties felt "
            "roughly the same things through 2016, split in 2017 (the gap was *anger*), **came back together in 2019–20** — the pandemic year is the "
            "last time Congress was emotionally close — and split again in 2021. Since then the biggest gap isn't anger but *optimism*; in 2025 it's *disgust*."
        ),
    ])
    return


@app.cell
def _(UNITY, mo, pd):
    _fmt = lambda df, col: (pd.DataFrame(df).assign(month=lambda d: pd.to_datetime(d.mo).dt.strftime("%b %Y"), share=lambda d: (d[col] * 100).round(1).astype(str) + "%")[["month", "event", "share"]])
    mo.vstack([
        mo.md("**The calendar of unity** — civic-unity share vs polarizing share, both parties pooled, months with 5,000+ tweets."),
        mo.hstack([
            mo.vstack([mo.md("*Most uniting months*"), mo.ui.table(_fmt(UNITY["calendar"]["uniting"], "civic"), selection=None)]),
            mo.vstack([mo.md("*Most polarizing months*"), mo.ui.table(_fmt(UNITY["calendar"]["polarizing"], "polarizing"), selection=None)]),
        ], widths="equal", gap=1.5),
        mo.md("Unity peaks on things that actually passed — infrastructure, COVID relief, the Ukraine response. The eight most polarizing months in the dataset are all in 2025."),
    ])
    return


@app.cell
def _(mo):
    mo.md(r"""### Chapter 6 · Two networks, one Congress""")
    return


@app.cell
def _(mo):
    net_kind = mo.ui.radio(options={"Who retweets whom": "retweet", "Who calls out whom (.@)": "dot"}, value="Who retweets whom", label="network")
    min_edge = mo.ui.slider(start=3, stop=30, step=1, value=3, label="minimum tweets per edge", show_value=True)
    mo.hstack([net_kind, min_edge], justify="start", gap=2)
    return min_edge, net_kind


@app.cell
def _(C, NETWORK, PARTY, base_layout, go, min_edge, mo, net_kind):
    import math

    _nodes = NETWORK["nodes"]
    _key = "rt_in" if net_kind.value == "retweet" else "dot_in"
    _score = lambda n: n["rt_in"] + 4 * n["dot_in"]
    _left = sorted([n for n in _nodes if n["party"] != "Republican"], key=_score, reverse=True)
    _right = sorted([n for n in _nodes if n["party"] == "Republican"], key=_score, reverse=True)

    def _place(arr, side):
        # two arcs facing each other across "the aisle"; biggest hubs nearest the centre line
        for i, n in enumerate(arr):
            t = ((1 if i % 2 else -1) * math.ceil(i / 2)) / len(arr)
            ang = t * math.pi * 150 / 180
            n["x"] = side * (0.42 + (1 - math.cos(ang)) * 0.9)
            n["y"] = math.sin(ang) * 1.05

    _place(_left, -1); _place(_right, 1)
    _by = {n["id"]: n for n in _nodes}
    _edges = [e for e in NETWORK[net_kind.value] if e[2] >= min_edge.value]
    _isDR = lambda p: p in ("Democrat", "Republican")
    _bins = [(3, 6, 0.5), (6, 15, 1.1), (15, 50, 2.2), (50, 10**9, 4)]
    _same = [dict(x=[], y=[]) for _ in _bins]; _cross = [dict(x=[], y=[]) for _ in _bins]
    _n_cross_tweets = _n_tweets = 0
    for _a, _b, _n, _ang in _edges:
        _u, _v = _by.get(_a), _by.get(_b)
        if not _u or not _v:
            continue
        _k = next(i for i, (lo, hi, _w) in enumerate(_bins) if lo <= _n < hi)
        _x = _isDR(_u["party"]) and _isDR(_v["party"]) and _u["party"] != _v["party"]
        (_cross if _x else _same)[_k]["x"] += [_u["x"], _v["x"], None]; (_cross if _x else _same)[_k]["y"] += [_u["y"], _v["y"], None]
        _n_tweets += _n; _n_cross_tweets += _n if _x else 0
    _fig = go.Figure()
    for _k, (_, _, _w) in enumerate(_bins):
        _fig.add_scatter(x=_same[_k]["x"], y=_same[_k]["y"], mode="lines", name="same party", legendgroup="same", showlegend=_k == 1, line=dict(color="rgba(11,11,11,0.14)", width=_w), hoverinfo="skip")
    _cc = C["gold"] if net_kind.value == "retweet" else C["rep"]
    for _k, (_, _, _w) in enumerate(_bins):
        _fig.add_scatter(x=_cross[_k]["x"], y=_cross[_k]["y"], mode="lines", name="across the aisle", legendgroup="cross", showlegend=_k == 1, line=dict(color=_cc, width=_w), opacity=0.7, hoverinfo="skip")
    _max = max(n[_key] for n in _nodes) or 1
    _fig.add_scatter(
        x=[n["x"] for n in _nodes], y=[n["y"] for n in _nodes], mode="markers", showlegend=False,
        marker=dict(size=[3.5 + 14 * math.sqrt(n[_key] / _max) for n in _nodes], color=[PARTY.get(n["party"], C["muted"]) for n in _nodes], line=dict(color="#fff", width=0.8)),
        text=[f"<b>{n['name']}</b> ({n['party'][0]}-{n['state']})<br>retweeted by members: {n['rt_in']} ({n['cross_rt_in']} across the aisle)<br>called out by members: {n['dot_in']} ({n['cross_dot_in']} across the aisle)" for n in _nodes],
        hovertemplate="%{text}<extra></extra>",
    )
    _hubs = lambda arr: sorted(arr, key=lambda n: -n[_key])[:3]
    _ann = [dict(x=0, y=1.12, text="the aisle", showarrow=False, font=dict(size=10.5, color=C["muted"]))]
    for _side, _arr in [(-1, _hubs(_left)), (1, _hubs(_right))]:
        for _i, _n2 in enumerate(_arr):
            _ann.append(dict(x=_n2["x"], y=_n2["y"], text=_n2["name"].split(",")[0].split(" ")[-1] if "," not in _n2["name"] else _n2["name"].split(",")[0], showarrow=True, arrowhead=0, arrowwidth=0.7, arrowcolor=C["muted"], ax=_side * -46, ay=(_i - 1) * 16, xanchor="right" if _side < 0 else "left", font=dict(size=11, color=C["ink"])))
    _fig.update_layout(base_layout(
        hovermode="closest", height=540, margin=dict(l=4, r=4, t=50, b=4), legend=dict(x=0.5, xanchor="center", y=-0.02, yanchor="top"),
        title=dict(text=("Who retweets whom" if net_kind.value == "retweet" else "Who calls out whom (.@)"), font=dict(size=16, color=C["ink"])),
        xaxis=dict(visible=False, range=[-1.5, 1.5], fixedrange=True), yaxis=dict(visible=False, range=[-1.2, 1.2], fixedrange=True),
        annotations=_ann, shapes=[dict(type="line", x0=0, x1=0, y0=-1.05, y1=1.05, line=dict(color=C["grid"], width=1, dash="dot"))],
    ))
    _S = NETWORK["summary"]["retweet" if net_kind.value == "retweet" else "dot"]
    mo.vstack([
        mo.ui.plotly(_fig),
        mo.md(
            f"{len(_edges):,} edges carrying {_n_tweets:,} tweets at this threshold; **{100*_n_cross_tweets/max(1,_n_tweets):.0f}% cross the aisle**. "
            f"Across the full network, cross-aisle {'retweets' if net_kind.value == 'retweet' else 'call-outs'} have mean anger {_S['anger_cross']:.2f} "
            f"vs {_S['anger_same']:.2f} within a party. Every tweet that begins `RT @` is an endorsement; a tweet that begins `.@` addresses someone in front "
            "of everyone — within a party that's usually praise, across the aisle it's a call-out (53% angry vs 27% for an ordinary mention)."
        ),
    ])
    return


@app.cell
def _(NETWORK, mo, pd):
    _rods = pd.DataFrame(NETWORK["rods"]).head(8).assign(cross_dot_anger=lambda d: d.cross_dot_anger.round(2)).rename(
        columns={"cross_dot_in": "call-outs from the other party", "cross_dot_anger": "mean anger of those"})
    _br = pd.DataFrame(NETWORK["bridges"]).head(8).rename(columns={"cross_rt_in": "retweets from the other party"})
    mo.ui.tabs({
        "The lightning rods": mo.vstack([mo.md("Most `.@`-addressed by the *other* party, with the mean anger of those tweets."), mo.ui.table(_rods, selection=None)]),
        "The bridges": mo.vstack([mo.md("Most retweeted by the *other* party. Massie and McCain are on both lists — the only people both sides retweet *and* yell at."), mo.ui.table(_br, selection=None)]),
    })
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Insight synthesis

        - **Anger is positional, not personal.** The same members are calm in power and furious out of it; we checked age, too — with member fixed
          effects the slope of anger on age is −0.011 ± 0.008 per decade (p = 0.17). Older members *look* angrier only in years when the older party
          (Democrats, by 2–4 years) is the out-party.
        - **The calendar barely matters; events do.** No ramp into elections in eight cycles; five of the eight biggest spikes are Congress's own
          shutdowns and debt-ceiling fights. The final month before an election is the *calm* month.
        - **Volume predicts anger.** The prolific are angry (ρ = 0.31), because anger is the high-volume genre. The exception — Cory Booker,
          8.5 tweets a day at 18% angry — is the kind of thing a reader remembers.
        - **The medium is the mood.** Retweets across the aisle are the calmest tweets in Congress (0.16); `.@` call-outs across the aisle are the
          angriest (0.61). The out-party doesn't argue with its counterparts — it addresses their leaders, in public.
        - **Memetically:** anger in Congress behaves like a contagion with a fixed reservoir — it doesn't spread evenly, it jumps to whichever
          party lost the presidency, concentrates on a handful of lightning rods, and each cycle leaves the baseline higher than it found it.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Discussion & future work

        **Limits.** Scores are model estimates (spot-checked, not human-labelled; a separate sentiment model's *negative* score correlates 0.80).
        Hours use each member's home-state clock, which is wrong whenever they're in Washington — Patty Murray's "before sunrise" is DC breakfast.
        The `.@` convention faded after Twitter changed reply visibility in 2017, and the 2023–24 collection contains almost no retweets, so both
        networks are weighted toward 2013–2022. We see explicit public call-outs only; replies-to and quote tweets are not in the data.

        **Next.** (1) The other ten emotions are already scored: *fear* should spike on shootings and COVID where *anger* spikes on shutdowns —
        a 2-D map of the 40 spike weeks would separate "threatened" from "aggrieved". (2) A per-member change-point ("the day Congressman X stopped
        being nice"). (3) A weekday-vs-weekend personality split, which is probably a staff-vs-member split. (4) A Baltimore cross-reference:
        the Maryland delegation's tweets that mention the city against Baltimore's own open data (311 requests, crime) on the same weeks.

        ## Notes on marimo

        *What worked.* Reactivity made the "forecast" natural: four dropdowns and a function, no callbacks. `mo.ui.plotly` inherits our styling
        unchanged. `mo.ui.anywidget` let us keep the one animation a web page did better (the tweet strip) and gain something back — the clicked
        dot is a Python value, so the tweet text is rendered by a *different cell*. `mo.stat`, `mo.callout`, `mo.accordion` and `mo.ui.table` did
        most of the layout work with no CSS. Because a notebook is a `.py` file, the whole thing lives in git next to the analysis pipeline.

        *What we'd want.* A first-class way to animate a chart over a variable (we used a JS timer inside the widget); a `mo.carousel` that
        remembers which slide a reader is on; and a lazy-load hint for expensive cells so a 5-minute reading pass doesn't wait on the network panel.

        ## Agentic tool usage

        This project was built in a pair with Claude Code over one long session. The division of labour that worked: the human chose the
        questions, the story beats and the taste calls ("this chart is not good", "make it a coin flip", "that's not what I meant by timelapse");
        the agent did the data engineering (matching 1,156 handles to birthdays, labelling 5M tweets on a GPU it first had to get working),
        wrote and re-ran the analyses, and drafted copy the human then cut. Two lessons. First, **make the agent validate its own claims**: asked
        "are we sure `.@` means a call-out?", it sampled tweets, found the convention was also used for praise, and narrowed the claim to what
        the data supported — that check is now the Methods note. Second, **the agent's statistics need the same scepticism as its prose**: the
        first "within-person age" model was perfectly collinear and reported a meaningless p = 0.82; it was caught only because the standard error
        was ten times larger than everything around it. The agent's best work came when it was asked to disagree, and its worst when it wasn't.
        """
    )
    return


if __name__ == "__main__":
    app.run()
