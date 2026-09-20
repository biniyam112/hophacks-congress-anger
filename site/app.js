/* What Makes Congress Angry? — charts (Plotly) + carousel */
const C = {
  ink: "#0b0b0b", ink2: "#52514e", muted: "#898781", grid: "#e1e0d9", axis: "#c3c2b7", surface: "#fcfcfb",
  dem: "#2a78d6", rep: "#e34948", accent: "#eb6834",
  // ordinal blue ramp (validated steps 700→250) for generations, oldest → youngest
  ordinal: ["#0d366b", "#1c5cab", "#2a78d6", "#5598e7", "#86b6ef"],
};
const FONT = { family: '"Inter", system-ui, -apple-system, "Segoe UI", sans-serif', size: 13, color: C.ink2 };
const CONFIG = { displayModeBar: false, responsive: true };
function layout(extra) {
  return Object.assign({
    paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)", font: FONT,
    margin: { l: 56, r: 24, t: 16, b: 48 }, hovermode: "x unified",
    // same dark tooltip as the icon ladder: ink background, white Inter text, no border
    hoverlabel: { bgcolor: C.ink, bordercolor: C.ink, font: { family: FONT.family, color: "#fff", size: 12.5 }, align: "left", namelength: -1 },
    legend: { orientation: "h", x: 0, y: 1.12, font: { size: 12 } },
    xaxis: { gridcolor: C.grid, linecolor: C.axis, zeroline: false, tickfont: { color: C.muted } },
    yaxis: { gridcolor: C.grid, linecolor: C.axis, zeroline: false, tickfont: { color: C.muted } },
  }, extra || {});
}
const ax = (o) => Object.assign({ gridcolor: C.grid, linecolor: C.axis, zeroline: false, tickfont: { color: C.muted } }, o || {});
const line = (x, y, name, color, extra) => Object.assign({ x, y, name, type: "scatter", mode: "lines", line: { color, width: 2 } }, extra || {});

const D = {};
const loaded = new Set();
const renderers = {};

async function main() {
  const names = ["meta", "year", "outparty", "seismograph", "hour", "month", "cycle", "forecast", "statement", "loudest", "network", "unity"];
  await Promise.all(names.map(async (n) => { D[n] = await (await fetch(`data/${n}.json`)).json(); }));
  fillMeta();
  setupCarousels();
  renderSeismograph();
  renderNetworks();
  renderUnityCalendar();
  // render whichever slides are active now
  document.querySelectorAll(".slide.active .chart, .slide.active .stat, .slide.active .statement").forEach((el) => renderIfNeeded(el.id));
  window.addEventListener("resize", () => document.querySelectorAll(".slide.active .chart, .chart.tall").forEach((el) => {
    if (el._fullLayout) Plotly.Plots.resize(el);
  }));
}

function fillMeta() {
  const m = D.meta;
  const fmt = (n) => (n / 1e6).toFixed(1) + " million";
  document.getElementById("meta-tweets").textContent = fmt(m.tweets);
  document.getElementById("meta-tweets-2").textContent = (m.tweets / 1e6).toFixed(2) + "M";
  document.getElementById("meta-members").textContent = m.members;
  document.getElementById("meta-members-2").textContent = m.members;
  document.getElementById("meta-from").textContent = m.from.slice(0, 4);
  document.getElementById("meta-to").textContent = m.to.slice(0, 7);
  document.getElementById("fc-base").textContent = Math.round(D.forecast.baseline * 100) + "%";
  document.getElementById("ld-base").textContent = Math.round(D.loudest.baseline * 100) + "%";
  document.getElementById("ld-median").textContent = D.loudest.median_per_day.toFixed(1);
}

/* ---------- carousel ---------- */
function setupCarousels() {
  document.querySelectorAll("[data-carousel]").forEach((car) => {
    const slides = [...car.querySelectorAll(".slide")];
    const count = car.querySelector(".count");
    let i = 0;
    const show = (k) => {
      i = (k + slides.length) % slides.length;
      slides.forEach((s, j) => s.classList.toggle("active", j === i));
      count.textContent = `${i + 1} / ${slides.length}`;
      slides[i].querySelectorAll(".chart, .stat, .statement, .ladder").forEach((el) => {
        if (loaded.has(el.id) && el._fullLayout) Plotly.Plots.resize(el); else renderIfNeeded(el.id);
      });
    };
    car.querySelector(".prev").addEventListener("click", () => show(i - 1));
    car.querySelector(".next").addEventListener("click", () => show(i + 1));
    car._show = show;
    show(0);
  });
  // in-page links that jump to a specific slide of the carousel they live in
  document.querySelectorAll("[data-goto-slide]").forEach((a) => a.addEventListener("click", (e) => {
    e.preventDefault();
    const car = a.closest("[data-carousel]"); if (!car) return;
    car._show(+a.dataset.gotoSlide);
    car.querySelector(".slide.active").scrollIntoView({ behavior: "smooth", block: "start" });
  }));
}
function renderIfNeeded(id) {
  if (!id || loaded.has(id) || !renderers[id]) return;
  loaded.add(id);
  renderers[id]();
}

/* ---------- Chapter 1 ---------- */
renderers["c-year"] = () => {
  const y = D.year;
  Plotly.newPlot("c-year", [
    Object.assign(line(y.year, y.anger, "All members", C.ink), {
      mode: "lines+markers", marker: { size: 8, color: C.ink },
      error_y: { type: "data", array: y.se.map((s) => 1.96 * s), color: C.muted, thickness: 1, width: 3 },
      hovertemplate: "%{y:.3f}<extra>mean anger</extra>",
    }),
  ], layout({ showlegend: false, yaxis: ax({ title: { text: "mean anger score", font: { size: 12 } }, range: [0.1, 0.5] }),
    xaxis: ax({ dtick: 1, tickangle: 0 }),
    shapes: ["2017-01-20", "2021-01-20", "2025-01-20"].map((d) => ({ type: "line", x0: +d.slice(0, 4), x1: +d.slice(0, 4), y0: 0, y1: 1, yref: "paper", line: { color: C.grid, width: 1 } })),
    annotations: [["2017", "Trump"], ["2021", "Biden"], ["2025", "Trump II"]].map(([x, t]) => ({ x: +x, y: 1, yref: "paper", text: t, showarrow: false, xanchor: "left", yanchor: "top", font: { size: 11, color: C.muted } })),
  }), CONFIG);
};

renderers["c-year-party"] = () => {
  const y = D.year;
  Plotly.newPlot("c-year-party", [
    line(y.year, y.dem, "Democrats", C.dem, { mode: "lines+markers", marker: { size: 6 }, hovertemplate: "%{y:.3f}" }),
    line(y.year, y.rep, "Republicans", C.rep, { mode: "lines+markers", marker: { size: 6 }, hovertemplate: "%{y:.3f}" }),
    line(y.year, y.anger, "All", C.muted, { line: { color: C.muted, width: 1.5, dash: "dot" }, hovertemplate: "%{y:.3f}" }),
  ], layout({ yaxis: ax({ title: { text: "mean anger score", font: { size: 12 } }, range: [0.1, 0.55] }), xaxis: ax({ dtick: 1 }),
    shapes: [2017, 2021, 2025].map((x) => ({ type: "line", x0: x, x1: x, y0: 0, y1: 1, yref: "paper", line: { color: C.grid, width: 1 } })),
    annotations: [[2017, "Trump"], [2021, "Biden"], [2025, "Trump II"]].map(([x, t]) => ({ x, y: 1, yref: "paper", text: t, showarrow: false, xanchor: "left", yanchor: "top", font: { size: 11, color: C.muted } })),
  }), CONFIG);
};

renderers["c-outparty"] = () => {
  const o = D.outparty;
  const lab = o.president.map((p, i) => `${p} (${o.president_party[i]})`);
  Plotly.newPlot("c-outparty", [
    { x: lab, y: o.dem, name: "Democrats", type: "bar", marker: { color: C.dem }, text: o.dem.map((v) => v.toFixed(2)), textposition: "outside", textfont: { color: C.ink2 }, hovertemplate: "%{y:.3f}" },
    { x: lab, y: o.rep, name: "Republicans", type: "bar", marker: { color: C.rep }, text: o.rep.map((v) => v.toFixed(2)), textposition: "outside", textfont: { color: C.ink2 }, hovertemplate: "%{y:.3f}" },
  ], layout({ barmode: "group", bargap: 0.35, bargroupgap: 0.06, hovermode: "x unified",
    yaxis: ax({ title: { text: "mean anger score", font: { size: 12 } }, range: [0, 0.58] }), xaxis: ax({ title: { text: "who holds the White House", font: { size: 12 } } }) }), CONFIG);
};

/* ---------- Chapter 2: seismograph ---------- */
function renderSeismograph() {
  const s = D.seismograph;
  const spikeIdx = new Map(s.spikes.map((sp) => [sp.week, sp]));
  const above = s.anger.map((a, i) => Math.max(a, s.baseline[i]));
  const traces = [
    { x: s.week, y: s.baseline, name: "13-week baseline", type: "scatter", mode: "lines", line: { color: C.axis, width: 1 }, hoverinfo: "skip", showlegend: true },
    { x: s.week, y: above, type: "scatter", mode: "lines", line: { width: 0 }, fill: "tonexty", fillcolor: "rgba(227,73,72,0.28)", hoverinfo: "skip", showlegend: false },
    line(s.week, s.dem, "Democrats", C.dem, { line: { color: C.dem, width: 1 }, opacity: 0.75, hovertemplate: "%{y:.3f}" }),
    line(s.week, s.rep, "Republicans", C.rep, { line: { color: C.rep, width: 1 }, opacity: 0.75, hovertemplate: "%{y:.3f}" }),
    line(s.week, s.anger, "All members", C.ink, { line: { color: C.ink, width: 1.4 }, hovertemplate: "%{y:.3f}" }),
    { x: s.spikes.map((p) => p.week), y: s.spikes.map((p) => p.anger + 0.02), name: "Spike (hover)", type: "scatter", mode: "markers",
      marker: { symbol: "diamond", size: 9, color: C.rep, line: { color: "#fff", width: 1.5 } },
      text: s.spikes.map((p) => `<b>${p.event}</b><br>+${p.excess.toFixed(2)} vs baseline · driven by ${p.driven_by}` + (p.hashtags ? `<br><i>${p.hashtags}</i>` : "")),
      hovertemplate: "%{x|%b %d, %Y}<br>%{text}<extra></extra>" },
  ];
  const lay = layout({
    hovermode: "closest", margin: { l: 56, r: 16, t: 24, b: 40 },
    yaxis: ax({ title: { text: "mean anger score, weekly", font: { size: 12 } }, range: [0.05, 0.68] }),
    xaxis: ax({ type: "date", range: ["2010-12-01", "2026-09-15"] }),
    legend: { orientation: "h", x: 0, y: 1.08, font: { size: 12 }, traceorder: "normal" },
    shapes: ["2017-01-20", "2021-01-20", "2025-01-20"].map((d) => ({ type: "line", x0: d, x1: d, y0: 0, y1: 1, yref: "paper", line: { color: C.grid, width: 1 } })),
    annotations: [["2017-01-20", "Trump"], ["2021-01-20", "Biden"], ["2025-01-20", "Trump II"]].map(([x, t]) => ({ x, y: 1, yref: "paper", text: t, showarrow: false, xanchor: "left", yanchor: "top", font: { size: 11, color: C.muted } })),
  });
  Plotly.newPlot("c-seismo", traces, lay, CONFIG);

  // spike list (top 12) + a pull-quote from the angriest week
  const ol = document.getElementById("spike-list");
  s.spikes.slice(0, 12).forEach((p) => {
    const li = document.createElement("li");
    li.innerHTML = `<span class="wk">${p.week}</span><span class="ev">${p.event}</span><span class="ex">+${p.excess.toFixed(2)}</span><span class="who ${p.driven_by}">${p.driven_by}</span>`;
    ol.appendChild(li);
  });
  const q = s.spikes.find((p) => p.week === "2021-01-04") || s.spikes[0];
  document.getElementById("spike-quote").innerHTML = `“${q.example}”<span class="by">— ${q.author}, week of ${q.week}</span>`;
}

/* ---------- Chapter 3 ---------- */
function yearCurves(id, d, xlab, tickvals, ticktext, highlight) {
  const traces = Object.entries(d.years).map(([yr, ys]) => ({
    x: d.x, y: ys, name: yr, type: "scatter", mode: "lines", line: { color: C.muted, width: 1 }, opacity: 0.35,
    hovertemplate: `${yr}: %{y:+.3f}<extra></extra>`, showlegend: false,
  }));
  traces.push(line(d.x, d.mean, "All years (weighted)", C.ink, { line: { color: C.ink, width: 2.5 }, hovertemplate: "mean: %{y:+.3f}<extra></extra>" }));
  Plotly.newPlot(id, traces, layout({
    hovermode: "closest", showlegend: false,
    yaxis: ax({ title: { text: "Δ anger vs. that year's mean", font: { size: 12 } }, zeroline: true, zerolinecolor: C.axis }),
    xaxis: ax({ title: { text: xlab, font: { size: 12 } }, tickvals, ticktext }),
    shapes: (highlight || []).map((h) => ({ type: "rect", x0: h[0], x1: h[1], y0: 0, y1: 1, yref: "paper", fillcolor: "rgba(235,104,52,0.10)", line: { width: 0 } })),
    annotations: (highlight || []).filter((h) => h[2]).map((h) => ({ x: (h[0] + h[1]) / 2, y: 1, yref: "paper", text: h[2], showarrow: false, yanchor: "top", font: { size: 11, color: C.accent } })),
  }), CONFIG);
}
renderers["c-hour"] = () => yearCurves("c-hour", D.hour, "hour of day (member's local time)",
  [0, 3, 6, 9, 12, 15, 18, 21, 23], ["12 am", "3 am", "6 am", "9 am", "noon", "3 pm", "6 pm", "9 pm", "11 pm"], [[20.5, 23.5, "after dark"], [-0.5, 4.5, "small hours"]]);
renderers["c-month"] = () => yearCurves("c-month", D.month, "month", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
  ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], [[7.5, 8.5, "August recess"]]);

renderers["c-cycle"] = () => {
  const cyc = D.cycle.cycles; const keys = Object.keys(cyc).map(Number).sort();
  const cols = 4, rows = 2, traces = [], lay = layout({ hovermode: "closest", showlegend: false, margin: { l: 44, r: 12, t: 28, b: 40 }, annotations: [], shapes: [] });
  keys.forEach((cy, k) => {
    const c = cyc[cy], n = k + 1, sfx = n === 1 ? "" : String(n);
    const xs = c.weeks.map((w) => -w);
    traces.push({ x: xs, y: c.dem, xaxis: "x" + sfx, yaxis: "y" + sfx, type: "scatter", mode: "lines", line: { color: C.dem, width: 0.9 }, opacity: 0.8, hovertemplate: `${cy} D: %{y:.3f}<extra></extra>` });
    traces.push({ x: xs, y: c.rep, xaxis: "x" + sfx, yaxis: "y" + sfx, type: "scatter", mode: "lines", line: { color: C.rep, width: 0.9 }, opacity: 0.8, hovertemplate: `${cy} R: %{y:.3f}<extra></extra>` });
    traces.push({ x: xs, y: c.anger, xaxis: "x" + sfx, yaxis: "y" + sfx, type: "scatter", mode: "lines", line: { color: C.ink, width: 1.3 }, hovertemplate: `${cy}, %{x} wk: %{y:.3f}<extra></extra>` });
    const col = k % cols, row = Math.floor(k / cols);
    const xd = [col / cols + 0.012, (col + 1) / cols - 0.012], yd = [1 - (row + 1) / rows + 0.09, 1 - row / rows - 0.06];
    lay["xaxis" + sfx] = ax({ domain: xd, anchor: "y" + sfx, range: [-105, 2], tickvals: [-100, -50, 0], tickfont: { size: 10, color: C.muted } });
    lay["yaxis" + sfx] = ax({ domain: yd, anchor: "x" + sfx, range: [0.05, 0.65], tickvals: [0.2, 0.4, 0.6], tickfont: { size: 10, color: C.muted } });
    lay.annotations.push({ x: (xd[0] + xd[1]) / 2, y: yd[1] + 0.005, xref: "paper", yref: "paper", text: `<b>${cy}</b> ${cy % 4 === 0 ? "presidential" : "midterm"}`, showarrow: false, yanchor: "bottom", font: { size: 12, color: C.ink } });
    lay.shapes.push({ type: "line", xref: "x" + sfx, yref: "y" + sfx, x0: 0, x1: 0, y0: 0.05, y1: 0.65, line: { color: C.axis, width: 1, dash: "dot" } });
  });
  lay.annotations.push({ x: 0.5, y: -0.06, xref: "paper", yref: "paper", text: "weeks before election day", showarrow: false, font: { size: 12, color: C.ink2 } });
  Plotly.newPlot("c-cycle", traces, lay, CONFIG);
};

renderers["c-final"] = () => {
  const f = D.cycle.final;
  Plotly.newPlot("c-final", [
    { x: f.year, y: f.rest, name: "Rest of the year", type: "bar", marker: { color: C.axis }, hovertemplate: "%{y:.3f}" },
    { x: f.year, y: f.last4, name: "Final 4 weeks", type: "bar", marker: { color: C.ink }, hovertemplate: "%{y:.3f}" },
  ], layout({ barmode: "group", bargap: 0.35, bargroupgap: 0.06, hovermode: "x unified",
    yaxis: ax({ title: { text: "mean anger score", font: { size: 12 } } }), xaxis: ax({ dtick: 2, title: { text: "election year", font: { size: 12 } } }) }), CONFIG);
};





/* ---------- Chapter 4: forecast ---------- */
const pc = (v) => Math.round(v * 100) + "%";
const partyColor = (p) => (p === "Democrat" ? C.dem : p === "Republican" ? C.rep : C.muted);
const hbar = (extra) => layout(Object.assign({ hovermode: "closest", showlegend: false, margin: { l: 10, r: 60, t: 8, b: 40 },
  xaxis: ax({ range: [0, 1], tickformat: ".0%", title: { text: "share of tweets that are angry", font: { size: 12 } } }),
  yaxis: ax({ automargin: true, showgrid: false, autorange: "reversed" }), bargap: 0.3 }, extra || {}));

renderers["c-ladder"] = () => {
  const I = window.ICONS, L = D.forecast.ladder, base = D.forecast.baseline;
  const tip = (html, text) => `<span class="tip" data-tip="${text}">${html}</span>`;
  const nothing = tip(I.nothing, "We know nothing about the tweet");
  const dem = tip(I.dem, "It's a Democrat");
  const night = tip(I.clock(2, 0, true), "It's between midnight and 4 am");
  const work = tip(I.clock(9), "It's working hours, 9 to 5");
  const trump = tip(I.portrait("img/trump.jpg", "Donald Trump"), "It's Trump's second term");
  const cvh = tip(I.portrait("img/vanhollen.jpg", "Chris Van Hollen"), "It's Chris Van Hollen");
  const spec = {
    "nothing": [nothing],
    "party = Democrat": [dem],
    "hour band = 00-04": [night],
    "party = Democrat, era = Trump II": [dem, trump],
    "party = Democrat, era = Trump II, 09-17": [dem, trump, work],
    "Chris Van Hollen, era = Trump II, 09-17": [cvh, trump, work],
  };
  const rows = [L[0], ...L.slice(1).filter((r) => spec[r.known] && !r.known.includes("Obama")).sort((a, b) => a.p - b.p)];
  const el = document.getElementById("c-ladder");
  el.innerHTML = rows.map((r) => `
    <div class="lrow${r.known.includes("Van Hollen") ? " hot" : ""}">
      <div class="licons">${spec[r.known].join('<span class="plus">+</span>')}</div>
      <div class="lbar"><div class="lfill" style="width:${(r.p * 100).toFixed(1)}%"></div><div class="lbase" style="left:${(base * 100).toFixed(1)}%"></div></div>
      <div class="lpct">${Math.round(r.p * 100)}%</div>
    </div>`).join("") + `<div class="lfoot"><span class="lbase-key">┆ Congress average, ${Math.round(base * 100)}%</span> · share of tweets that are angry</div>`;
};



renderers["c-owls"] = () => {
  const owls = D.forecast.owls, larks = D.forecast.larks, O = [...owls, ...larks];
  const SUN = "#eda100", MOON = "#0d366b", GAP = 1.6;      // rows 0..k-1, a gap, then the morning people
  const ypos = O.map((r, i) => (i < owls.length ? i : i + GAP));
  const names = O.map((r) => r.name);
  const pc = (v) => Math.round(v * 100) + "%";
  const traces = [
    ...O.map((r, i) => ({ type: "scatter", mode: "lines", x: [r.day, r.night], y: [ypos[i], ypos[i]], line: { color: partyColor(r.party), width: 4 }, opacity: 0.5, hoverinfo: "skip", showlegend: false })),
    { type: "scatter", mode: "markers", x: O.map((r) => r.day), y: ypos, name: "☀ daytime, 9–5", marker: { color: SUN, size: 14, line: { color: "#fff", width: 2 } },
      text: names, hovertemplate: "%{text}<br>daytime: %{x:.0%} angry<extra></extra>" },
    { type: "scatter", mode: "markers", x: O.map((r) => r.night), y: ypos, name: "☾ late night, 9 pm – 4 am", marker: { color: MOON, size: 14, line: { color: "#fff", width: 2 } },
      text: names, hovertemplate: "%{text}<br>late night: %{x:.0%} angry<extra></extra>" },
  ];
  const annotations = [];
  O.forEach((r, i) => {
    const lo = Math.min(r.day, r.night), hi = Math.max(r.day, r.night), yy = ypos[i];
    annotations.push({ x: lo, y: yy, text: pc(lo), showarrow: false, xanchor: "right", xshift: -12, font: { size: 11.5, color: C.ink2 } });
    annotations.push({ x: hi, y: yy, text: pc(hi), showarrow: false, xanchor: "left", xshift: 12, font: { size: 11.5, color: C.ink2 } });
    annotations.push({ x: r.night, y: yy, ax: r.day, ay: yy, axref: "x", ayref: "y", showarrow: true, arrowhead: 2, arrowsize: 1.1, arrowwidth: 1.5, arrowcolor: partyColor(r.party), standoff: 9, startstandoff: 9, text: "" });
  });
  const gapMid = owls.length - 1 + (GAP + 1) / 2, top = -1, bottom = ypos[ypos.length - 1] + 0.7;
  annotations.push({ x: 0.5, y: top + 0.15, xref: "paper", text: "NIGHT OWLS — angrier after dark", showarrow: false, font: { size: 11, color: C.muted, family: FONT.family } });
  annotations.push({ x: 0.5, y: gapMid, xref: "paper", text: "MORNING PEOPLE — angrier by day", showarrow: false, font: { size: 11, color: C.muted, family: FONT.family } });
  Plotly.newPlot("c-owls", traces, layout({
    hovermode: "closest", margin: { l: 10, r: 24, t: 48, b: 44 },
    legend: { orientation: "h", x: 0, y: 1.14, font: { size: 12 } },
    xaxis: ax({ range: [0, 0.82], tickformat: ".0%", tickvals: [0, 0.2, 0.4, 0.6, 0.8], title: { text: "share of tweets that are angry", font: { size: 12 } }, gridcolor: "#f0efec" }),
    yaxis: ax({ automargin: true, showgrid: false, range: [bottom, top - 0.2], tickvals: ypos, ticktext: names, tickfont: { size: 13, color: C.ink } }),
    shapes: [
      { type: "rect", xref: "paper", x0: 0, x1: 1, y0: owls.length - 1 + GAP / 2 + 0.5, y1: bottom, fillcolor: "#faf9f6", line: { width: 0 }, layer: "below" },
      { type: "line", xref: "paper", x0: 0, x1: 1, y0: owls.length - 1 + GAP / 2 + 0.5, y1: owls.length - 1 + GAP / 2 + 0.5, line: { color: C.grid, width: 1 } },
    ],
    annotations,
  }), CONFIG);
};

/* ---------- the statement card: one claim, every tweet behind it ---------- */
renderers["c-statement"] = () => {
  const S = D.statement, T = S.tweets;
  const fmt = (d) => d.toLocaleDateString("en-US", { month: "short", year: "numeric" });
  document.getElementById("st-attrib").textContent =
    `— ${Math.round(S.p * 100)}% of ${S.n} tweets, ${S.band} Pacific, ${fmt(new Date(S.from))} – ${fmt(new Date(S.to))}`;

  const strip = document.getElementById("st-strip"), peek = document.getElementById("st-peek"), tally = document.getElementById("st-tally");
  strip.innerHTML = "";
  const W = Math.max(320, strip.clientWidth || 860), H = 130, padL = 16, padR = 16, y0 = 56;
  const t0 = new Date(S.from).getTime(), t1 = new Date(S.to).getTime();
  const xs = (t) => padL + ((t - t0) / (t1 - t0)) * (W - padL - padR);
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg"); svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const el = (tag, attrs, cls) => { const e = document.createElementNS(ns, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (cls) e.setAttribute("class", cls); svg.appendChild(e); return e; };
  el("line", { x1: padL, x2: W - padR, y1: y0, y2: y0 }, "axis");
  // quarter ticks
  for (let d = new Date(2025, 0, 1); d.getTime() <= t1; d.setMonth(d.getMonth() + 3)) {
    const x = xs(d.getTime()); if (x < padL) continue;
    el("line", { x1: x, x2: x, y1: y0 + 30, y2: y0 + 34 }, "tick");
    const lab = el("text", { x, y: y0 + 44, "text-anchor": "middle" }, "tick-label");
    lab.textContent = d.getMonth() === 0 ? String(d.getFullYear()) : ["Jan", "Apr", "Jul", "Oct"][d.getMonth() / 3];
  }
  // dots: jitter vertically so same-day tweets don't stack; angry above the axis, calm below
  const dots = T.map((tw, i) => {
    const angry = tw.a > 0.5, jit = ((i * 7919) % 23) - 11;
    const c = el("circle", { cx: xs(new Date(tw.t.replace(" ", "T")).getTime()), cy: y0 + (angry ? -14 : 14) + jit * 0.9, r: angry ? 4.2 : 4 }, "dot " + (angry ? "angry" : "calm"));
    c.addEventListener("mouseenter", () => { peek.innerHTML = `<span class="when">${tw.t} · anger ${tw.a.toFixed(2)}</span>${escapeHtml(tw.x)}`; });
    return c;
  });
  svg.setAttribute("preserveAspectRatio", "xMidYMid meet"); strip.appendChild(svg);

  let timer = null, k = 0, angryCount = 0;
  const setTally = () => { tally.textContent = k ? `${angryCount} angry of ${k} shown (${Math.round((100 * angryCount) / k)}%)` : ""; };
  const showAll = () => { dots.forEach((d) => d.classList.add("on")); k = T.length; angryCount = T.filter((t) => t.a > 0.5).length; setTally(); };
  const reset = () => { clearInterval(timer); timer = null; dots.forEach((d) => d.classList.remove("on")); k = 0; angryCount = 0; setTally(); document.getElementById("st-play").textContent = "▶ Play"; };
  const play = () => {
    if (timer) { clearInterval(timer); timer = null; document.getElementById("st-play").textContent = "▶ Play"; return; }
    if (k >= T.length) reset();
    document.getElementById("st-play").textContent = "❚❚ Pause";
    timer = setInterval(() => {
      if (k >= T.length) { clearInterval(timer); timer = null; document.getElementById("st-play").textContent = "▶ Play"; return; }
      dots[k].classList.add("on"); if (T[k].a > 0.5) angryCount++; k++; setTally();
    }, 28);
  };
  document.getElementById("st-play").onclick = play;     // assignment, not addEventListener: safe across re-renders
  document.getElementById("st-reset").onclick = reset;
  showAll();
  if (!renderers["c-statement"]._resize) {
    renderers["c-statement"]._resize = true;
    let t; window.addEventListener("resize", () => { clearTimeout(t); t = setTimeout(() => { loaded.delete("c-statement"); renderIfNeeded("c-statement"); }, 200); });
  }
};
function escapeHtml(s) { return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }

/* ---------- the loudest people in Congress ---------- */
renderers["c-loudest"] = () => {
  const M = D.loudest.members;
  const y = M.map((m) => `${m.name} (${m.party[0]}-${m.state})`);
  const angry = M.map((m) => m.per_day * m.p), calm = M.map((m) => m.per_day * (1 - m.p));
  const isB = M.map((m) => m.name.includes("Booker")); const bi = isB.indexOf(true);
  const cd = M.map((m) => [m.per_day, Math.round(m.p * 100), m.n]);
  const hover = "%{y}<br>%{customdata[0]} tweets/day, %{customdata[1]}% angry (%{customdata[2]} tweets)<extra></extra>";
  Plotly.newPlot("c-loudest", [
    { type: "bar", orientation: "h", y, x: angry, name: "angry", marker: { color: isB.map((b) => (b ? "#e34948" : C.rep)), opacity: isB.map((b) => (b ? 1 : 0.85)) },
      customdata: cd, hovertemplate: hover },
    { type: "bar", orientation: "h", y, x: calm, name: "not angry", marker: { color: isB.map((b) => (b ? C.dem : C.grid)) },
      text: M.map((m, i) => (isB[i] ? `<b>${Math.round(m.p * 100)}% angry — the prolific optimist</b>` : `${Math.round(m.p * 100)}% angry`)),
      textposition: "outside", textfont: { color: isB.map((b) => (b ? C.dem : C.ink2)), size: 12 }, cliponaxis: false,
      customdata: cd, hovertemplate: hover },
  ], layout({ barmode: "stack", bargap: 0.28, hovermode: "closest", margin: { l: 10, r: 170, t: 8, b: 52 },
    legend: { orientation: "h", x: 1, xanchor: "right", y: 1.08, font: { size: 12 } },
    xaxis: ax({ title: { text: "tweets per day", font: { size: 12 } }, range: [0, 15.5] }),
    yaxis: ax({ automargin: true, showgrid: false, autorange: "reversed", tickfont: { color: C.muted } }),
    shapes: [
      // highlight band behind Booker's row
      ...(bi >= 0 ? [{ type: "rect", xref: "paper", x0: 0, x1: 1, y0: bi - 0.5, y1: bi + 0.5, fillcolor: "rgba(42,120,214,0.09)", line: { width: 0 }, layer: "below" }] : []),
      { type: "line", x0: D.loudest.median_per_day, x1: D.loudest.median_per_day, y0: 0, y1: 1, yref: "paper", line: { color: C.axis, width: 1, dash: "dot" } },
    ],
    annotations: [
      { x: D.loudest.median_per_day, y: 1, yref: "paper", text: "typical member", showarrow: false, xanchor: "left", yanchor: "bottom", yshift: 14, font: { size: 10, color: C.muted } },
    ] }), CONFIG);
  // Booker's name in bold blue on the axis
  if (bi >= 0) {
    const ticktext = y.map((t, i) => (i === bi ? `<b><span style="color:${C.dem}">${t}</span></b>` : t));
    Plotly.relayout("c-loudest", { "yaxis.tickvals": y, "yaxis.ticktext": ticktext });
  }
};

/* ---------- Chapter 5: uniting vs dividing ---------- */
renderers["c-unity-mirror"] = () => {
  const U = D.unity, pc = ".0%";
  const ann = (y, t, dom) => ({ x: y, y: 1, yref: dom, xref: "x", text: t, showarrow: false, xanchor: "left", yanchor: "top", font: { size: 11, color: C.muted } });
  Plotly.newPlot("c-unity-mirror", [
    { x: U.year, y: U.polarizing.dem, name: "Democrats · polarizing", type: "scatter", mode: "lines+markers", line: { color: C.dem, width: 2 }, marker: { size: 6 }, yaxis: "y", hovertemplate: "%{y:.1%}" },
    { x: U.year, y: U.polarizing.rep, name: "Republicans · polarizing", type: "scatter", mode: "lines+markers", line: { color: C.rep, width: 2 }, marker: { size: 6 }, yaxis: "y", hovertemplate: "%{y:.1%}" },
    { x: U.year, y: U.civic.dem, name: "Democrats · civic unity", type: "scatter", mode: "lines+markers", line: { color: C.dem, width: 2, dash: "dot" }, marker: { size: 6, symbol: "diamond" }, yaxis: "y2", hovertemplate: "%{y:.1%}" },
    { x: U.year, y: U.civic.rep, name: "Republicans · civic unity", type: "scatter", mode: "lines+markers", line: { color: C.rep, width: 2, dash: "dot" }, marker: { size: 6, symbol: "diamond" }, yaxis: "y2", hovertemplate: "%{y:.1%}" },
  ], layout({
    margin: { l: 56, r: 16, t: 30, b: 40 }, legend: { orientation: "h", x: 0, y: 1.1, font: { size: 11.5 } },
    xaxis: ax({ dtick: 1, anchor: "y2" }),
    yaxis: ax({ domain: [0.56, 1], title: { text: "polarizing", font: { size: 12 } }, tickformat: pc, rangemode: "tozero" }),
    yaxis2: ax({ domain: [0, 0.44], title: { text: "civic unity", font: { size: 12 } }, tickformat: pc, rangemode: "tozero" }),
    shapes: [2017, 2021, 2025].flatMap((x) => [{ type: "line", x0: x, x1: x, y0: 0, y1: 1, yref: "paper", line: { color: C.grid, width: 1 } }]),
    annotations: [[2017, "Trump"], [2021, "Biden"], [2025, "Trump II"]].map(([x, t]) => ({ x, y: 1, yref: "paper", text: t, showarrow: false, xanchor: "left", yanchor: "top", font: { size: 11, color: C.muted } })),
  }), CONFIG);
};

renderers["c-unity-distance"] = () => {
  const U = D.unity.distance;
  const notes = { 2017: "anger", 2020: "COVID: closest since 2011", 2021: "optimism", 2025: "disgust" };
  Plotly.newPlot("c-unity-distance", [
    { x: U.year, y: U.d, type: "scatter", mode: "lines+markers", line: { color: C.ink, width: 2.2 }, marker: { size: 8, color: C.ink },
      fill: "tozeroy", fillcolor: "rgba(11,11,11,0.06)", text: U.gap.map((g, i) => `biggest gap: <b>${g}</b> (${U.sign[i]})`), hovertemplate: "%{x}: distance %{y:.2f}<br>%{text}<extra></extra>", showlegend: false },
  ], layout({
    hovermode: "closest", margin: { l: 56, r: 16, t: 24, b: 44 },
    xaxis: ax({ dtick: 1 }), yaxis: ax({ title: { text: "distance between party emotion profiles", font: { size: 12 } }, rangemode: "tozero" }),
    shapes: [2017, 2021, 2025].map((x) => ({ type: "line", x0: x, x1: x, y0: 0, y1: 1, yref: "paper", line: { color: C.grid, width: 1 } })),
    annotations: [
      ...[[2017, "Trump"], [2021, "Biden"], [2025, "Trump II"]].map(([x, t]) => ({ x, y: 1, yref: "paper", text: t, showarrow: false, xanchor: "left", yanchor: "top", font: { size: 11, color: C.muted } })),
      ...Object.entries(notes).map(([x, t]) => { const i = U.year.indexOf(+x); return { x: +x, y: U.d[i], text: t, showarrow: true, arrowhead: 0, arrowcolor: C.muted, ax: 0, ay: +x === 2020 ? 40 : -26, font: { size: 11, color: +x === 2020 ? C.dem : C.ink } }; }),
    ],
  }), CONFIG);
};

function renderUnityCalendar() {
  const U = D.unity.calendar, fmt = (m) => new Date(m).toLocaleDateString("en-US", { month: "short", year: "numeric" });
  const li = (r, key) => `<li><span class="mo">${fmt(r.mo)}</span><span>${r.event || "—"}</span><span class="n">${(r[key] * 100).toFixed(1)}%</span></li>`;
  document.getElementById("unity-top").innerHTML = U.uniting.map((r) => li(r, "civic")).join("");
  document.getElementById("unity-bottom").innerHTML = U.polarizing.map((r) => li(r, "polarizing")).join("");
}

/* ---------- Chapter 6: two networks, one Congress — "the aisle" layout ---------- */
function renderNetworks() {
  const N = D.network;
  const isDR = (p) => p === "Democrat" || p === "Republican";
  const GOLD = "#eda100";
  const lastName = (name) => (name.includes(",") ? name.split(",")[0] : name.split(" ").slice(-1)[0]);
  const display = (name) => (name.includes(",") ? name.split(", ").reverse().join(" ") : name);

  // Positions: two arcs facing each other across the aisle. Members are ordered along each arc by how
  // much they are retweeted+called out overall, the biggest hubs nearest the centre line (y = 0).
  const score = (n) => n.rt_in + 4 * n.dot_in;
  const left = N.nodes.filter((n) => n.party !== "Republican").sort((a, b) => score(b) - score(a));   // D + Independents
  const right = N.nodes.filter((n) => n.party === "Republican").sort((a, b) => score(b) - score(a));
  const place = (arr, side) => {
    // alternate above/below the centre so the hubs sit in the middle of the arc; arc spans 150 degrees
    arr.forEach((n, i) => {
      const t = ((i % 2 ? 1 : -1) * Math.ceil(i / 2)) / arr.length;          // -0.5 .. 0.5
      const ang = t * Math.PI * (150 / 180);                                   // radians from the horizontal
      const R = 1;
      n.x = side * (0.42 + R * (1 - Math.cos(ang)) * 0.9);                     // arc bulges away from the aisle
      n.y = R * Math.sin(ang) * 1.05;
    });
  };
  place(left, -1); place(right, 1);
  const byId = new Map(N.nodes.map((n) => [n.id, n]));

  const panel = (id, edges, sizeKey, crossColor) => {
    // edges binned by tweet count so line width reflects volume (Plotly can't vary width within a trace)
    const bins = [[3, 6, 0.5], [6, 15, 1.1], [15, 50, 2.2], [50, Infinity, 4]];
    const mk = () => bins.map(() => ({ x: [], y: [] }));
    const same = mk(), cross = mk();
    edges.forEach(([a, b, n]) => {
      const u = byId.get(a), v = byId.get(b); if (!u || !v) return;
      const k = bins.findIndex(([lo, hi]) => n >= lo && n < hi);
      const t = (isDR(u.party) && isDR(v.party) && u.party !== v.party ? cross : same)[k];
      t.x.push(u.x, v.x, null); t.y.push(u.y, v.y, null);
    });
    const maxDeg = Math.max(...N.nodes.map((n) => n[sizeKey]));
    const size = N.nodes.map((n) => 3.5 + 14 * Math.sqrt(n[sizeKey] / maxDeg));
    const hubsL = N.nodes.filter((n) => n.x < 0).sort((a, b) => b[sizeKey] - a[sizeKey]).slice(0, 3);
    const hubsR = N.nodes.filter((n) => n.x > 0).sort((a, b) => b[sizeKey] - a[sizeKey]).slice(0, 3);
    const traces = [];
    bins.forEach(([, , w], k) => traces.push({ type: "scatter", mode: "lines", x: same[k].x, y: same[k].y, name: "same party", legendgroup: "same", showlegend: k === 1,
      line: { color: "rgba(11,11,11,0.14)", width: w }, hoverinfo: "skip" }));
    bins.forEach(([, , w], k) => traces.push({ type: "scatter", mode: "lines", x: cross[k].x, y: cross[k].y, name: "across the aisle", legendgroup: "cross", showlegend: k === 1,
      line: { color: crossColor, width: w }, opacity: 0.7, hoverinfo: "skip" }));
    traces.push({ type: "scatter", mode: "markers", x: N.nodes.map((n) => n.x), y: N.nodes.map((n) => n.y), showlegend: false,
      marker: { size, color: N.nodes.map((n) => partyColor(n.party)), line: { color: "#fff", width: 0.8 }, opacity: 0.92 },
      text: N.nodes.map((n) => `<b>${display(n.name)}</b> (${n.party[0]}-${n.state})<br>retweeted by members: ${n.rt_in} (${n.cross_rt_in} across the aisle)<br>called out by members: ${n.dot_in} (${n.cross_dot_in} across the aisle)`),
      hovertemplate: "%{text}<extra></extra>" });
    const lab = (arr, side) => arr.map((n, i) => ({ x: n.x, y: n.y, text: lastName(n.name), showarrow: true, arrowhead: 0, arrowwidth: 0.7, arrowcolor: C.muted,
      ax: side * -46, ay: (i - 1) * 16, xanchor: side < 0 ? "right" : "left", font: { size: 11, color: C.ink } }));
    Plotly.newPlot(id, traces, layout({
      hovermode: "closest", showlegend: true, margin: { l: 4, r: 4, t: 4, b: 4 },
      legend: { orientation: "h", x: 0.5, xanchor: "center", y: -0.02, font: { size: 11 } },
      xaxis: { visible: false, range: [-1.5, 1.5], fixedrange: true }, yaxis: { visible: false, range: [-1.2, 1.2], fixedrange: true },
      annotations: [{ x: 0, y: 1.12, text: "the aisle", showarrow: false, font: { size: 10.5, color: C.muted } }, ...lab(hubsL, -1), ...lab(hubsR, 1)],
      shapes: [{ type: "line", x0: 0, x1: 0, y0: -1.05, y1: 1.05, line: { color: C.grid, width: 1, dash: "dot" } }],
    }), CONFIG);
  };
  panel("c-net-rt", N.retweet, "rt_in", GOLD);
  panel("c-net-dot", N.dot, "dot_in", C.rep);

  const S = N.summary, pc = (v) => Math.round(v * 100) + "%";
  document.getElementById("net-rt-stats").textContent =
    `${S.retweet.tweets.toLocaleString()} retweets of fellow members; ${pc(S.retweet.cross_tweet_share)} cross the aisle, with anger ${S.retweet.anger_cross.toFixed(2)} vs ${S.retweet.anger_same.toFixed(2)} within a party.`;
  document.getElementById("net-dot-stats").textContent =
    `${S.dot.tweets.toLocaleString()} call-outs of fellow members; ${pc(S.dot.cross_tweet_share)} cross the aisle, with anger ${S.dot.anger_cross.toFixed(2)} vs ${S.dot.anger_same.toFixed(2)} within a party.`;
  const badge = (p) => `<span class="who ${p === "Democrat" ? "Dem" : p === "Republican" ? "Rep" : "both"}">${p[0]}</span>`;
  const li = (name, party, n, a) => `<li><span>${display(name)} ${badge(party)}</span><span class="n">${n}</span>` +
    (a == null ? "<span></span>" : `<span class="a${a < 0.35 ? " calm" : ""}">anger ${a.toFixed(2)}</span>`) + "</li>";
  document.getElementById("net-rods").innerHTML = N.rods.slice(0, 8).map((r) => li(r.name, r.party, r.cross_dot_in, r.cross_dot_anger)).join("");
  document.getElementById("net-bridges").innerHTML = N.bridges.slice(0, 8).map((r) => li(r.name, r.party, r.cross_rt_in, null)).join("");
}

main();
