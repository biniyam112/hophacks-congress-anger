/* Gone with the Wind, as told by tweets — the parties' emotional distance, month by month, as a romance.
   Driven by data/unity.json: distance_month (the gap) and distance (per-year largest-gap emotion and which side has it). */

const NS = "http://www.w3.org/2000/svg";
const $ = (id) => document.getElementById(id);
const el = (tag, attrs = {}, parent) => { const n = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v); if (parent) parent.appendChild(n); return n; };
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const lerp = (a, b, t) => a + (b - a) * t;
const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
const mix = (a, b, t) => { const A = hex(a), B = hex(b); return `rgb(${A.map((v, i) => Math.round(lerp(v, B[i], clamp(t, 0, 1)))).join(",")})`; };

// ---------- the five acts (year ranges) ----------
const ACTS = [
  { n: "Act I", t: "The ball", y: [2011, 2016], sub: "They were never closer. The gap: a little optimism, mostly Democratic.", mood: "warm" },
  { n: "Act II", t: "The quarrel", y: [2017, 2018], sub: "Distance triples in a year. The gap is anger.", mood: "storm" },
  { n: "Act III", t: "Bonnie", y: [2019, 2020], sub: "A shared catastrophe. For a year they hold each other. The gap is joy — and it's Republican.", mood: "candle" },
  { n: "Act IV", t: "Separate bedrooms", y: [2021, 2024], sub: "“Tomorrow is another day.” Only one side says it. The gap is optimism.", mood: "cold" },
  { n: "Act V", t: "“Frankly, my dear…”", y: [2025, 2026], sub: "The gap is disgust. The last word, and it isn't a word.", mood: "night" },
];
const MOODS = {  // wall, window top/bottom, chandelier brightness
  warm:   { wallA: "#3a2a22", wallB: "#1c1410", winA: "#f7d9a0", winB: "#e9a86a", glow: 1.0, rain: 0 },
  storm:  { wallA: "#2b2624", wallB: "#141110", winA: "#6b7280", winB: "#374151", glow: 0.55, rain: 1 },
  candle: { wallA: "#2e221c", wallB: "#120d0a", winA: "#1f2a44", winB: "#0b1a3a", glow: 0.85, rain: 0 },
  cold:   { wallA: "#26292e", wallB: "#101214", winA: "#c8d3e0", winB: "#8fa3b8", glow: 0.45, rain: 0 },
  night:  { wallA: "#1b1a1f", wallB: "#0a0a0c", winA: "#20242c", winB: "#0b0d12", glow: 0.35, rain: 0 },
};
// how each emotion shapes a face: brow tilt (deg, + = angry inward), mouth curve (+ = smile), extra effect
const FACES = {
  optimism: { brow: -8, mouth: 0.6, fx: "glowing" },
  joy: { brow: -10, mouth: 1.0, fx: "glowing" },
  anger: { brow: 18, mouth: -0.8, fx: "fuming" },
  disgust: { brow: 8, mouth: -0.6, fx: "disgusted" },
  sadness: { brow: -14, mouth: -0.6, fx: "weeping" },
  fear: { brow: -12, mouth: -0.3, fx: "" },
  neutral: { brow: 0, mouth: 0.15, fx: "" },
};

let D, months, years, playing = false, i = 0, pos = 0, lastTs = null, raf = null;
let smooth = [];                       // 3-month centred mean of the distance, so the figures glide instead of twitch
const MASK_FROM = "2020-03", MASK_TO = "2021-05";   // pandemic months: both figures wear masks
let cur = null;                        // current (tweened) room colours
let halfCur = null;                    // damped position of the figures (they glide toward the target)

async function main() {
  D = await (await fetch("data/unity.json")).json();
  months = D.distance_month.mo.map((m, k) => ({ mo: m, year: +m.slice(0, 4), d: D.distance_month.d[k] }));
  years = Object.fromEntries(D.distance.year.map((y, k) => [y, { gap: D.distance.gap[k], demHigher: D.distance.sign[k].startsWith("Democrats"), d: D.distance.d[k] }]));
  smooth = months.map((m, k) => { const w = months.slice(Math.max(0, k - 2), k + 3); return w.reduce((a, x) => a + x.d, 0) / w.length; });   // 5-month centred mean
  buildRoom(); buildFigure("dem", "#2a78d6", "Democrats"); buildFigure("rep", "#e34948", "Republicans"); buildControls(); buildActs();
  render(0);
}

function buildRoom() {
  const fb = $("floorboards");
  for (let x = 0; x <= 1200; x += 60) el("line", { x1: x, y1: 480, x2: x + (x - 600) * 0.35, y2: 640 }, fb);
  const cl = $("chandelier-lights");
  for (let k = -3; k <= 3; k++) el("circle", { cx: 600 + k * 20, cy: 46 - Math.abs(k) * 2, r: 3.5, class: "bulb" }, cl);
  const rain = $("rain");
  for (let k = 0; k < 40; k++) el("line", { x1: 505 + Math.random() * 190, y1: 75 + Math.random() * 280, x2: 0, y2: 0, stroke: "#dbe4ee", "stroke-width": 1.2, opacity: 0.6, class: "drop" }, rain);
  rain.querySelectorAll(".drop").forEach((l) => { const x = +l.getAttribute("x1"), y = +l.getAttribute("y1"); l.setAttribute("x2", x - 3); l.setAttribute("y2", y + 14); });
}

function buildFigure(id, color, name) {
  const g = $(id);
  g.innerHTML = "";
  // body
  el("path", { d: "M-46 200 C-46 120 -30 80 0 80 C30 80 46 120 46 200 Z", fill: color, class: "body" }, g);
  el("path", { d: "M-16 84 L16 84 L14 110 L-14 110 Z", fill: "#fff", opacity: 0.85 }, g);
  const head = el("g", { class: "head" }, g);
  el("circle", { cx: 0, cy: 40, r: 40, fill: "#f3d5b5", stroke: "#3a2a22", "stroke-width": 2 }, head);
  el("path", { d: "M-40 30 C-38 -2 38 -2 40 30 C30 18 -30 18 -40 30 Z", fill: id === "dem" ? "#3b2a1a" : "#1a1a1a" }, head);
  el("circle", { cx: -14, cy: 38, r: 3.5, class: "eye" }, head); el("circle", { cx: 14, cy: 38, r: 3.5, class: "eye" }, head);
  el("path", { class: "brow bl", d: "M-24 26 L-6 26" }, head); el("path", { class: "brow br", d: "M6 26 L24 26" }, head);
  el("path", { class: "mouth", d: "M-14 56 Q0 62 14 56" }, head);
  const mask = el("g", { class: "mask" }, head);
  el("path", { d: "M-24 44 Q-30 50 -26 56 L-40 34", fill: "none", stroke: "#b9d2ea", "stroke-width": 2 }, mask);   // ear loops
  el("path", { d: "M24 44 Q30 50 26 56 L40 34", fill: "none", stroke: "#b9d2ea", "stroke-width": 2 }, mask);
  el("rect", { x: -24, y: 44, width: 48, height: 24, rx: 7, fill: "#dbe9f7", stroke: "#9fbddc", "stroke-width": 1.5 }, mask);
  el("path", { d: "M-18 52 L18 52 M-18 58 L18 58", stroke: "#b9d2ea", "stroke-width": 1.2 }, mask);
  // effects
  el("circle", { class: "tear", cx: -14, cy: 48, r: 3 }, head);
  el("path", { class: "heart", d: "M0 -8 C-8 -20 -26 -6 0 12 C26 -6 8 -20 0 -8 Z", transform: "translate(34,-6) scale(0.8)" }, head);
  el("path", { class: "stink s1", d: "M30 10 q6 -10 0 -20 q-6 -10 0 -20" }, head); el("path", { class: "stink s2", d: "M42 14 q6 -10 0 -20 q-6 -10 0 -20" }, head);
  el("text", { class: "name", x: 0, y: 232 }, g).textContent = name;
  el("text", { class: "mood", x: 0, y: 250 }, g);
}

function setFace(id, emo, on) {
  const g = $(id), f = on ? FACES[emo] || FACES.neutral : FACES.neutral;
  const s = id === "rep" ? -1 : 1;   // mirror brows so the figures face each other
  const tilt = f.brow;
  g.querySelector(".bl").setAttribute("d", `M-24 ${26 - s * tilt * 0.25} L-6 ${26 + s * tilt * 0.25}`);
  g.querySelector(".br").setAttribute("d", `M6 ${26 + s * tilt * 0.25} L24 ${26 - s * tilt * 0.25}`);
  g.querySelector(".mouth").setAttribute("d", `M-14 56 Q0 ${56 + 14 * f.mouth} 14 56`);
  g.classList.remove("fuming", "weeping", "glowing", "disgusted"); if (on && f.fx) g.classList.add(f.fx);
  g.querySelector(".mood").textContent = on ? emo : "";
}

function actFor(year) { return ACTS.find((a) => year >= a.y[0] && year <= a.y[1]) || ACTS[ACTS.length - 1]; }

function render(p, dt = 0) {
  pos = clamp(p, 0, months.length - 1);
  i = Math.round(pos);
  const lo = Math.floor(pos), hi = Math.min(lo + 1, months.length - 1), f = pos - lo;
  const m = months[i], yr = years[m.year], act = actFor(m.year);
  const d = lerp(smooth[lo], smooth[hi], f);
  // the gap: 0.05 (touching) -> 0.60 (opposite walls)
  const halfTarget = lerp(70, 470, clamp((d - 0.05) / 0.55, 0, 1));
  if (halfCur === null || !dt) halfCur = halfTarget; else halfCur = lerp(halfCur, halfTarget, 1 - Math.exp(-dt / 0.45));
  const half = halfCur;
  const y = 300;
  $("dem").setAttribute("transform", `translate(${(600 - half).toFixed(1)}, ${y})`);
  $("rep").setAttribute("transform", `translate(${(600 + half).toFixed(1)}, ${y})`);
  $("gap-line").setAttribute("x1", 600 - half + 46); $("gap-line").setAttribute("x2", 600 + half - 46);
  $("gap-label").textContent = `distance ${m.d.toFixed(2)}`;
  // faces: whoever is higher on this year's largest-gap emotion wears it; masks during the pandemic
  setFace("dem", yr.gap, yr.demHigher); setFace("rep", yr.gap, !yr.demHigher);
  const masked = m.mo.slice(0, 7) >= MASK_FROM && m.mo.slice(0, 7) <= MASK_TO;
  $("dem").classList.toggle("masked", masked); $("rep").classList.toggle("masked", masked);
  // room mood, cross-faded toward the act's palette (~0.8 s time constant)
  const T = MOODS[act.mood];
  if (!cur) cur = { ...T };
  const a = dt ? 1 - Math.exp(-dt / 0.8) : 1;
  for (const k of ["wallA", "wallB", "winA", "winB"]) cur[k] = mix(cur[k].startsWith("rgb") ? rgbToHex(cur[k]) : cur[k], T[k], a);
  cur.glow = lerp(cur.glow, T.glow, a); cur.rain = lerp(cur.rain, T.rain, a);
  $("wall-a").setAttribute("stop-color", cur.wallA); $("wall-b").setAttribute("stop-color", cur.wallB);
  $("win-a").setAttribute("stop-color", cur.winA); $("win-b").setAttribute("stop-color", cur.winB);
  $("candle-glow").setAttribute("opacity", cur.glow); $("rain").setAttribute("opacity", cur.rain);
  $("chandelier-lights").querySelectorAll(".bulb").forEach((b) => b.setAttribute("opacity", 0.4 + 0.6 * cur.glow));
  // HUD + intertitle (fades in over the first months of an act, out after a few) + programme
  $("hud-date").textContent = new Date(m.mo + "T00:00:00").toLocaleDateString("en-US", { month: "short", year: "numeric" });
  $("hud-act").textContent = `${act.n} · ${act.t}`;
  $("hud-dist").textContent = m.d.toFixed(2);
  $("card-title").textContent = `${act.n} — ${act.t}`; $("card-sub").textContent = act.sub;
  const first = months.findIndex((x) => x.year === act.y[0]), since = pos - first;
  $("card").setAttribute("opacity", clamp(Math.min(since / 1.5, (14 - since) / 3), 0, 1));
  document.querySelectorAll(".act").forEach((el2, k) => el2.classList.toggle("on", ACTS[k] === act));
  $("scrub").value = i;
}
function rgbToHex(rgb) { const v = rgb.match(/\d+/g).map(Number); return "#" + v.map((x) => x.toString(16).padStart(2, "0")).join(""); }

function buildControls() {
  const scrub = $("scrub"); scrub.max = months.length - 1;
  const marks = $("marks");
  [2011, 2014, 2017, 2020, 2023, 2026].forEach((y) => { const k = months.findIndex((m) => m.year === y); if (k < 0) return; const s = document.createElement("span"); s.style.left = `${(100 * k) / (months.length - 1)}%`; s.textContent = y; marks.appendChild(s); });
  scrub.addEventListener("input", () => { pause(); render(+scrub.value); });
  $("play").addEventListener("click", () => (playing ? pause() : play()));
}
function play() {
  if (pos >= months.length - 1) render(0);
  playing = true; $("play").textContent = "❚❚ Pause"; lastTs = null;
  // clock-driven tween (~60 fps); dt comes from the clock so a throttled tab just catches up smoothly
  const frame = () => {
    if (!playing) return;
    const ts = performance.now();
    const dt = lastTs ? Math.min(0.1, (ts - lastTs) / 1000) : 0; lastTs = ts;
    const monthsPerSecond = 2.2 * +$("speed").value;          // 1x: the whole story in ~85 s
    if (pos >= months.length - 1) { pause(); return; }
    render(pos + dt * monthsPerSecond, dt);
    raf = setTimeout(frame, 16);
  };
  frame();
}
function pause() { playing = false; clearTimeout(raf); $("play").textContent = "▶ Play"; }

function buildActs() {
  const box = $("acts");
  ACTS.forEach((a, k) => {
    const d = document.createElement("div"); d.className = "act";
    d.innerHTML = `<div class="n">${a.n}</div><div class="t">${a.t}</div><div class="y">${a.y[0]}–${a.y[1]}</div>`;
    d.addEventListener("click", () => { pause(); render(months.findIndex((m) => m.year === a.y[0])); });
    box.appendChild(d);
  });
}

main();
