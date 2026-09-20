/* A day on the Hill — sunrise-to-sunset time-lapse.
   Faces are driven by data/timelapse.json: per-member share of angry tweets by hour (home-state time),
   plus the whole-chamber hourly deviation from Chapter 3. */

const T0 = 5, T1 = 21;                 // scene runs 5:00 → 21:00
const SUNRISE = 6.2, SUNSET = 19.4;    // decimal hours
const PASS_SECONDS = 48;               // one full day at 1× speed
const NS = "http://www.w3.org/2000/svg";

const $ = id => document.getElementById(id);
const el = (tag, attrs = {}, parent) => {
  const n = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  if (parent) parent.appendChild(n);
  return n;
};
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const lerp = (a, b, t) => a + (b - a) * t;
const hex = h => h.startsWith("rgb") ? h.match(/\d+/g).map(Number) : [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
const rgb = c => `rgb(${c.map(Math.round).join(",")})`;
const mix = (h1, h2, t) => rgb(hex(h1).map((a, i) => lerp(a, hex(h2)[i], clamp(t, 0, 1))));
const mixN = (stops, t) => {            // stops: [[t, hex], ...] sorted
  if (t <= stops[0][0]) return stops[0][1];
  for (let i = 1; i < stops.length; i++)
    if (t <= stops[i][0]) return mix(stops[i - 1][1], stops[i][1], (t - stops[i - 1][0]) / (stops[i][0] - stops[i - 1][0]));
  return stops[stops.length - 1][1];
};
// seeded random so the stars don't reshuffle on every load
let seed = 7; const rand = () => (seed = (seed * 16807) % 2147483647) / 2147483647;

/* ---------- sky palette by hour ---------- */
const SKY_TOP = [[5, "#0b1a3a"], [6, "#2b3d78"], [7, "#4a7cc9"], [8.5, "#62a8ee"], [13, "#4f9ff0"], [17, "#5d9be6"], [18.5, "#6a6fb0"], [19.4, "#6b4a8f"], [20.2, "#1e2650"], [21, "#0b1a3a"]];
const SKY_MID = [[5, "#1c2a55"], [6, "#8a5a80"], [7, "#c9a9b8"], [8.5, "#9cc9f6"], [13, "#8fc2f7"], [17, "#a5c1e6"], [18.5, "#d9a0a0"], [19.4, "#c46a7a"], [20.2, "#4a3660"], [21, "#1c2a55"]];
const SKY_HOR = [[5, "#2a3a6a"], [6, "#f08a5d"], [7, "#ffc178"], [8.5, "#cfe8ff"], [13, "#d9efff"], [17, "#f7d9a8"], [18.5, "#ffb277"], [19.4, "#ff8c5a"], [20.2, "#b05a6a"], [21, "#2a3a6a"]];

/* ---------- sun geometry ---------- */
function sunState(T) {
  const p = (T - SUNRISE) / (SUNSET - SUNRISE);
  const elev = Math.sin(Math.PI * p);        // -ish below horizon outside [0,1]
  const x = 60 + p * 1080, y = 470 - elev * 410;
  const light = clamp((elev + 0.12) / 0.5, 0, 1);
  return { p, elev, x, y, light };
}

/* ---------- build static scenery ---------- */
function buildScenery() {
  const stars = $("stars");
  for (let i = 0; i < 80; i++)
    el("circle", { cx: rand() * 1200, cy: rand() * 380, r: 0.7 + rand() * 1.3, fill: "#fff", "data-ph": rand() * 6.28 }, stars);

  const rays = $("sun-rays");
  for (let i = 0; i < 12; i++)
    el("path", { d: "M0,-58 L6,-78 L-6,-78 Z", fill: "#ffd53d", opacity: 0.8, transform: `rotate(${i * 30})` }, rays);

  const clouds = $("clouds");
  const specs = [[120, 100, 1.0, 9], [430, 160, 0.8, 12], [720, 90, 1.2, 7], [980, 200, 0.7, 14], [300, 240, 0.6, 16]];
  specs.forEach(([x, y, s, v]) => {
    const g = el("g", { "data-x": x, "data-y": y, "data-v": v, "data-s": s, class: "cloud" }, clouds);
    [[0, 0, 46, 22], [-34, 6, 30, 16], [36, 6, 34, 18], [8, -10, 30, 18]].forEach(([cx, cy, rx, ry]) => el("ellipse", { cx, cy, rx, ry }, g));
  });

  const birds = $("birds");
  for (let i = 0; i < 4; i++)
    el("path", { class: "bird", d: "M-9,0 q4.5,-6 9,0 q4.5,-6 9,0", fill: "none", stroke: "#2a2a2a", "stroke-width": 2, "stroke-linecap": "round", "data-i": i }, birds);

  const win = $("cap-windows");
  for (let row = 0; row < 2; row++)
    for (let x = -312; x <= 300; x += 24) {
      if (x > -150 && x < 130) continue;
      el("rect", { x, y: -72 + row * 34, width: 12, height: 20, rx: 1 }, win);
    }
}

/* ---------- cast ---------- */
const SUITS = ["#2c2f3a", "#3b3a44", "#1f2a3d", "#3a2f2a"];
const members = [];

function buildCast(cast) {
  const owls = cast.filter(m => m.kind === "owl"), larks = cast.filter(m => m.kind === "lark");
  const place = (list, x0, step) => list.forEach((m, i) => members.push(makeMember(m, x0 + i * step, i)));
  place(owls, 185, 100);
  place(larks, 835, 100);
}

function makeMember(m, x, i) {
  const party = m.party === "Democrat" ? "#2a78d6" : "#e34948";
  const suit = SUITS[i % SUITS.length];
  const g = el("g", { class: "member", transform: `translate(${x},582) scale(0.92)` }, $("cast"));
  const shadow = el("ellipse", { cx: 0, cy: 0, rx: 30, ry: 9, fill: "#10251a", opacity: 0 }, g);
  const body = el("g", { class: "body-group" }, g);

  el("rect", { x: -17, y: -36, width: 13, height: 36, rx: 3, fill: "#1d1f2a" }, body);
  el("rect", { x: 4, y: -36, width: 13, height: 36, rx: 3, fill: "#1d1f2a" }, body);
  el("rect", { x: -22, y: -6, width: 20, height: 6, rx: 3, fill: "#0b0b0b" }, body);
  el("rect", { x: 2, y: -6, width: 20, height: 6, rx: 3, fill: "#0b0b0b" }, body);
  const armL = el("path", { d: "M-32,-94 L-42,-54", stroke: suit, "stroke-width": 13, "stroke-linecap": "round" }, body);
  const armR = el("path", { d: "M32,-94 L42,-54", stroke: suit, "stroke-width": 13, "stroke-linecap": "round" }, body);
  const fistL = el("circle", { cx: -42, cy: -54, r: 7, fill: "#ffd54a" }, body);
  const fistR = el("circle", { cx: 42, cy: -54, r: 7, fill: "#ffd54a" }, body);
  el("path", { d: "M-30,-34 L-34,-96 Q-34,-104 -26,-106 L26,-106 Q34,-104 34,-96 L30,-34 Z", fill: suit }, body);
  el("path", { d: "M-13,-106 L0,-72 L13,-106 Z", fill: "#fff" }, body);
  el("path", { d: "M-5,-105 L5,-105 L3,-97 L7,-68 L0,-60 L-7,-68 L-3,-97 Z", fill: party }, body);

  const face = el("circle", { cy: -138, r: 34, fill: "#ffd54a", stroke: "#c9931a", "stroke-width": 2 }, body);
  el("ellipse", { cx: -12, cy: -142, rx: 6, ry: 7, fill: "#fff" }, body);
  el("ellipse", { cx: 12, cy: -142, rx: 6, ry: 7, fill: "#fff" }, body);
  const pupilL = el("circle", { cx: -11, cy: -141, r: 3.2, fill: "#111" }, body);
  const pupilR = el("circle", { cx: 13, cy: -141, r: 3.2, fill: "#111" }, body);
  const browL = el("path", { d: "", fill: "none", stroke: "#3a2a10", "stroke-width": 3.5, "stroke-linecap": "round" }, body);
  const browR = el("path", { d: "", fill: "none", stroke: "#3a2a10", "stroke-width": 3.5, "stroke-linecap": "round" }, body);
  const shout = el("ellipse", { cx: 0, cy: -117, rx: 10, ry: 0, fill: "#5a1a1a" }, body);
  const tongue = el("ellipse", { cx: 0, cy: -112, rx: 6, ry: 0, fill: "#e0607a" }, body);
  const mouth = el("path", { d: "", fill: "none", stroke: "#3a2a10", "stroke-width": 3, "stroke-linecap": "round" }, body);
  const vein = el("g", { transform: "translate(24,-166)", opacity: 0 }, body);
  ["M-8,-3 L-3,-3 M3,-3 L8,-3 M-8,3 L-3,3 M3,3 L8,3 M-3,-8 L-3,-3 M3,-8 L3,-3 M-3,3 L-3,8 M3,3 L3,8"].forEach(d =>
    el("path", { d, stroke: "#b8262a", "stroke-width": 2.5, "stroke-linecap": "round", fill: "none" }, vein));
  [[-30, -172, "s1"], [30, -176, "s2"], [-18, -184, "s3"]].forEach(([cx, cy, cls]) => {
    const s = el("g", { class: `steam ${cls}`, style: `transform-origin:${cx}px ${cy}px` }, body);
    el("circle", { cx, cy, r: 6, fill: "#fff", opacity: 0.85 }, s);
    el("circle", { cx: cx + 6, cy: cy - 4, r: 4.5, fill: "#fff", opacity: 0.85 }, s);
  });

  const short = m.name.replace(/^(\w+)\s\w\.\s/, "$1 ").replace(/^(\w+)\s\w\s/, "$1 ");
  el("text", { class: "name", y: 20 }, g).textContent = short;
  el("text", { class: "state", y: 34 }, g).textContent = `${m.party[0]} · ${m.state}`;
  const pct = el("text", { class: "pct", y: 54 }, g);

  return { m, x, g, body, shadow, face, browL, browR, mouth, shout, tongue, vein, pupilL, pupilR, armL, armR, fistL, fistR, pct };
}

// anger share for this member at decimal hour T (hour bins are centred on h+0.5)
function shareAt(share, T) {
  const t = ((T - 0.5) % 24 + 24) % 24;
  const i = Math.floor(t), f = t - i;
  return lerp(share[i], share[(i + 1) % 24], f);
}

function renderMember(M, T, sun) {
  const a = shareAt(M.m.share, T);
  const e = clamp((a - 0.12) / 0.6, 0, 1);        // 0 = serene, 1 = furious

  // stays yellow through "mildly annoyed", then heats up fast
  const fill = e < 0.5 ? mix("#ffd54a", "#ffa63d", Math.pow(e * 2, 1.8)) : mix("#ffa63d", "#e34948", (e - 0.5) * 2);
  M.face.setAttribute("fill", fill);
  M.fistL.setAttribute("fill", fill); M.fistR.setAttribute("fill", fill);

  // brows: arched & high when calm, slanted inward when angry
  const s = clamp((e - 0.22) / 0.78, 0, 1);
  const outer = -160 - (1 - s) * 3, inner = -158 + s * 14;
  M.browL.setAttribute("d", `M-23,${outer} Q-14,${outer - 3 * (1 - s)} -5,${inner}`);
  M.browR.setAttribute("d", `M23,${outer} Q14,${outer - 3 * (1 - s)} 5,${inner}`);
  // pupils pinch toward the centre when angry
  M.pupilL.setAttribute("cx", -11 + e * 2); M.pupilR.setAttribute("cx", 13 - e * 2);
  M.pupilL.setAttribute("r", 3.4 - e); M.pupilR.setAttribute("r", 3.4 - e);
  // mouth: smile → flat → frown, then an open shout
  const y0 = -120, c = y0 + 18 * (1 - 2 * e);
  M.mouth.setAttribute("d", `M-14,${y0} Q0,${c} 14,${y0}`);
  const open = clamp((e - 0.72) / 0.28, 0, 1);
  M.shout.setAttribute("ry", 9 * open); M.tongue.setAttribute("ry", 4 * open);
  M.mouth.setAttribute("opacity", 1 - open);
  M.vein.setAttribute("opacity", clamp((e - 0.6) / 0.3, 0, 1));
  // arms hang until the member is properly worked up, then the fists come up beside the head
  const ang = clamp((e - 0.55) / 0.45, 0, 1) * 150;
  M.armL.setAttribute("transform", `rotate(${ang}, -32, -94)`); M.fistL.setAttribute("transform", `rotate(${ang}, -32, -94)`);
  M.armR.setAttribute("transform", `rotate(${-ang}, 32, -94)`); M.fistR.setAttribute("transform", `rotate(${-ang}, 32, -94)`);
  M.g.classList.toggle("fuming", e > 0.82);

  // shadow cast by the sun
  if (sun.elev > 0.02) {
    const tip = clamp((M.x - sun.x) / (582 - sun.y) * 165, -170, 170);
    M.shadow.setAttribute("cx", tip / 2); M.shadow.setAttribute("rx", Math.abs(tip) / 2 + 18);
    M.shadow.setAttribute("opacity", 0.38 * sun.light * clamp(sun.elev * 5, 0, 1));
  } else M.shadow.setAttribute("opacity", 0);

  M.pct.textContent = `${Math.round(a * 100)}% angry`;
  M.pct.setAttribute("fill", e > 0.6 ? "#ffb3a7" : e < 0.25 ? "#d8f5c8" : "#fff");
}

/* ---------- world ---------- */
let chamber = [];
function renderWorld(T) {
  const sun = sunState(T), L = sun.light;

  $("sky-top").setAttribute("stop-color", mixN(SKY_TOP, T));
  $("sky-mid").setAttribute("stop-color", mixN(SKY_MID, T));
  $("sky-hor").setAttribute("stop-color", mixN(SKY_HOR, T));

  // stars twinkle and fade with daylight
  const starOp = Math.pow(1 - L, 2);
  for (const s of $("stars").children) {
    const ph = +s.getAttribute("data-ph");
    s.setAttribute("opacity", starOp * (0.55 + 0.45 * Math.sin(T * 40 + ph)));
  }

  // sun
  const sunG = $("sun"), visible = sun.p > -0.08 && sun.p < 1.08;
  sunG.setAttribute("opacity", visible ? clamp((sun.elev + 0.25) / 0.25, 0, 1) : 0);
  sunG.setAttribute("transform", `translate(${sun.x},${sun.y})`);
  const warm = clamp(sun.elev / 0.35, 0, 1);
  $("sun-disc").setAttribute("fill", mix("#ff8c3a", "#ffd53d", warm));
  $("sun-disc").setAttribute("stroke", mix("#e8612c", "#ffb347", warm));
  $("sun-rays").setAttribute("transform", `rotate(${T * 18})`);
  $("sun-rays").setAttribute("fill", mix("#ff8c3a", "#ffd53d", warm));
  $("sun-face").setAttribute("opacity", warm);

  // moon lives on the far side of the sky from the sun
  const moon = $("moon");
  moon.setAttribute("opacity", clamp((0.35 - L) / 0.35, 0, 1));
  moon.setAttribute("transform", T < 12 ? "translate(-140,60)" : "translate(-700,80)");
  $("moon-bite").setAttribute("fill", mix(mixN(SKY_TOP, T), mixN(SKY_MID, T), 0.45));

  // clouds drift, and catch the colour of the light
  const glow = clamp(1 - Math.abs(sun.elev) / 0.3, 0, 1) * (visible ? 1 : 0);
  const cloudCol = mix(mix("#3a4470", "#ffffff", L), "#ffb98f", glow * 0.8);
  for (const c of $("clouds").children) {
    const x = ((+c.getAttribute("data-x") + (T - T0) * +c.getAttribute("data-v")) % 1400 + 1400) % 1400 - 100;
    c.setAttribute("transform", `translate(${x},${c.getAttribute("data-y")}) scale(${c.getAttribute("data-s")})`);
    c.setAttribute("fill", cloudCol);
    c.setAttribute("opacity", 0.55 + 0.45 * L);
  }
  // birds only fly by day
  for (const b of $("birds").children) {
    const i = +b.getAttribute("data-i");
    const x = ((T - T0) * 150 + i * 330) % 1500 - 150;
    const y = 140 + i * 28 + Math.sin(T * 3 + i) * 12;
    b.setAttribute("transform", `translate(${x},${y})`);
    b.setAttribute("opacity", clamp((L - 0.3) / 0.5, 0, 1));
  }

  // ground & building take the light
  $("lawn").setAttribute("fill", mix("#23412c", "#6fae5a", L));
  $("hill-far").setAttribute("fill", mix("#2d4a3a", "#8fbf7a", L));
  $("lawn-path").setAttribute("fill", mix("#4d4a42", "#d9c9a3", L));
  $("capitol").style.filter = `brightness(${0.35 + 0.65 * L})`;
  const sky = mixN(SKY_HOR, T);
  $("capitol").style.filter += ` drop-shadow(0 0 ${Math.round(18 * (1 - L))}px ${sky})`;
  $("sign-owls").style.filter = $("sign-larks").style.filter = `brightness(${0.45 + 0.55 * L})`;
  $("cast").style.filter = `brightness(${0.78 + 0.22 * L})`;

  // HUD
  const h = Math.floor(T), mnt = Math.floor((T - h) * 60);
  const h12 = ((h + 11) % 12) + 1;
  $("hud-time").textContent = `${h12}:${String(mnt).padStart(2, "0")} ${h < 12 ? "am" : "pm"}`;
  $("hud-phase").textContent = T < SUNRISE ? "before dawn" : T < 7.5 ? "sunrise" : T < 12 ? "morning" : T < 13 ? "noon"
    : T < 17 ? "afternoon" : T < 18.8 ? "evening" : T < SUNSET + 0.2 ? "sunset" : "dusk";

  const pts = shareAt(chamber, T) * 100;
  $("hud-chamber").textContent = `${pts >= 0 ? "+" : "−"}${Math.abs(pts).toFixed(1)} pts`;
  $("hud-chamber-sub").textContent = Math.abs(pts) < 0.05 ? "right at the day's average"
    : pts > 0 ? "angrier than the day's average" : "calmer than the day's average";
  const w = clamp(Math.abs(pts) / 6 * 100, 0, 100);
  $("hud-bar").setAttribute("width", w);
  $("hud-bar").setAttribute("x", pts >= 0 ? 1060 : 1060 - w);
  $("hud-bar").setAttribute("fill", pts >= 0 ? "#ff7a5a" : "#7ad0ff");

  for (const M of members) renderMember(M, T, sun);
}

/* ---------- playback ---------- */
let T = T0, playing = false, last = 0;
const scrub = $("scrub"), playBtn = $("play");

function setTime(t, fromScrub) {
  T = clamp(t, T0, T1);
  if (!fromScrub) scrub.value = T.toFixed(2);
  renderWorld(T);
}
function tick(now) {
  if (!playing) return;
  const dt = Math.min((now - last) / 1000, 0.1); last = now;   // cap: no jump after a hidden tab
  const speed = +$("speed").value;
  let t = T + dt * (T1 - T0) / PASS_SECONDS * speed;
  if (t >= T1) {
    if ($("loop").checked) t = T0 + (t - T1);
    else { setTime(T1); togglePlay(false); return; }
  }
  setTime(t);
  requestAnimationFrame(tick);
}
function togglePlay(on) {
  playing = on === undefined ? !playing : on;
  playBtn.textContent = playing ? "❚❚ Pause" : "▶ Play";
  playBtn.setAttribute("aria-label", playing ? "Pause" : "Play");
  if (playing) {
    if (T >= T1 - 0.01) T = T0;
    last = performance.now();
    requestAnimationFrame(tick);
  }
}
playBtn.addEventListener("click", () => togglePlay());
scrub.addEventListener("input", () => setTime(+scrub.value, true));
document.addEventListener("keydown", e => {
  if (e.code === "Space" && e.target === document.body) { e.preventDefault(); togglePlay(); }
});

/* ---------- boot ---------- */
buildScenery();
fetch("data/timelapse.json").then(r => r.json()).then(d => {
  chamber = d.chamber;
  buildCast(d.cast);
  setTime(T0);
  // start automatically once the page is visible
  const io = new IntersectionObserver(entries => {
    if (entries.some(en => en.isIntersecting)) { togglePlay(true); io.disconnect(); }
  }, { threshold: 0.4 });
  io.observe($("scene"));
});
