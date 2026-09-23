// Builds deck/whats_making_us_angry.pptx from the site's data files. No em dashes anywhere in the copy.
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const J = (n) => JSON.parse(fs.readFileSync(path.join(ROOT, "site/data", n + ".json"), "utf8"));
const YEAR = J("year"), OUT = J("outparty"), SEIS = J("seismograph"), FC = J("forecast"), UN = J("unity"), NET = J("network"), LOUD = J("loudest"), META = J("meta");

const C = { page: "6F7B98", ink: "0B0B0B", ink2: "52514E", muted: "898781", grid: "E1E0D9", dem: "2A78D6", rep: "E34948", gold: "EDA100", accent: "EB6834", card: "FFFFFF", tint: "F1F0EC" };
const HEAD = "Cambria", BODY = "Calibri", MONO = "Courier New";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";            // 13.33 x 7.5
pres.title = "What's making US angry?";
const W = 13.33, H = 7.5, M = 0.6;

// ---------- helpers ----------
function dark(slide) { slide.background = { color: C.page }; }
function light(slide) { slide.background = { color: C.card }; }
function title(slide, text, opts = {}) {
  slide.addText(text, { x: M, y: 0.45, w: W - 2 * M, h: 0.9, fontFace: HEAD, fontSize: 34, bold: true, color: opts.color || C.ink, isTextBox: true, margin: 0, valign: "middle" });
}
function kicker(slide, text, color = C.muted) {
  slide.addText(text, { x: M, y: 0.18, w: W - 2 * M, h: 0.3, fontFace: BODY, fontSize: 11, color, charSpacing: 2, isTextBox: true, margin: 0 });
}
function body(slide, items, x, y, w, h, size = 14, color = C.ink2) {
  slide.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 6 } })),
    { x, y, w, h, fontFace: BODY, fontSize: size, color, isTextBox: true, margin: 0, valign: "top" });
}
function para(slide, text, x, y, w, h, size = 14, color = C.ink2, extra = {}) {
  slide.addText(text, Object.assign({ x, y, w, h, fontFace: BODY, fontSize: size, color, isTextBox: true, margin: 0, valign: "top" }, extra));
}
function stat(slide, x, y, w, value, label, color = C.ink) {
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h: 1.55, fill: { color: C.tint }, line: { color: C.tint }, rectRadius: 0.08 });
  slide.addText(value, { x: x + 0.15, y: y + 0.12, w: w - 0.3, h: 0.8, fontFace: BODY, fontSize: 30, bold: true, color, isTextBox: true, margin: 0, valign: "middle" });
  slide.addText(label, { x: x + 0.15, y: y + 0.92, w: w - 0.3, h: 0.55, fontFace: BODY, fontSize: 11.5, color: C.ink2, isTextBox: true, margin: 0, valign: "top" });
}
const chartFrame = {
  catAxisLabelColor: C.muted, valAxisLabelColor: C.muted, catAxisLabelFontFace: BODY, valAxisLabelFontFace: BODY, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10,
  valGridLine: { color: C.grid, size: 0.5 }, catGridLine: { style: "none" }, legendFontFace: BODY, legendFontSize: 10, legendColor: C.ink2,
};
function footer(slide, n) {
  slide.addText(`What's making US angry?  ·  HopHacks 2026  ·  ${n}`, { x: M, y: H - 0.45, w: W - 2 * M, h: 0.3, fontFace: BODY, fontSize: 9, color: C.muted, isTextBox: true, margin: 0, align: "right" });
}
const pc = (v) => Math.round(v * 100) + "%";

// ---------- 1. title ----------
{
  const s = pres.addSlide(); dark(s);
  s.addText("HOPHACKS 2026  ·  CONGRESS ON TWITTER, 2011 TO 2026", { x: M, y: 0.9, w: 8, h: 0.4, fontFace: BODY, fontSize: 12, color: "DFE3EC", charSpacing: 2, isTextBox: true, margin: 0 });
  s.addText("What's making\nUS angry?", { x: M, y: 1.5, w: 7.2, h: 2.6, fontFace: HEAD, fontSize: 60, bold: true, color: "FFFFFF", isTextBox: true, margin: 0, valign: "middle", lineSpacingMultiple: 0.95 });
  s.addText("4.8 million tweets, one finding: anger in Congress isn't an opinion. It's a jersey you put on when your side loses the White House.",
    { x: M, y: 4.3, w: 6.6, h: 1.4, fontFace: BODY, fontSize: 17, color: "EEF1F7", isTextBox: true, margin: 0, valign: "top" });
  s.addText("github.com/biniyam112/hophacks-tweet-sentiment", { x: M, y: 6.5, w: 7, h: 0.4, fontFace: MONO, fontSize: 11, color: "CFD5E3", isTextBox: true, margin: 0 });
  s.addChart(pres.ChartType.line, [
    { name: "Democrats", labels: YEAR.year.map(String), values: YEAR.dem }, { name: "Republicans", labels: YEAR.year.map(String), values: YEAR.rep },
  ], { x: 7.5, y: 1.3, w: 5.3, h: 3.4, chartColors: ["8FC0FF", "FF8A86"], lineSize: 3, lineDataSymbol: "circle", lineDataSymbolSize: 6, showLegend: true, legendPos: "t", legendColor: "FFFFFF", legendFontFace: BODY, legendFontSize: 10,
    valAxisMinVal: 0.1, valAxisMaxVal: 0.55, valAxisMajorUnit: 0.1, valAxisLabelFormatCode: "0.0", catAxisLabelColor: "DFE3EC", valAxisLabelColor: "DFE3EC", catAxisLabelFontSize: 9, valAxisLabelFontSize: 9, catAxisLabelFontFace: BODY, valAxisLabelFontFace: BODY,
    valGridLine: { color: "8C97B3", size: 0.5 }, catGridLine: { style: "none" }, showTitle: true, title: "Whoever is out of power is angry", titleColor: "FFFFFF", titleFontFace: HEAD, titleFontSize: 13 });
  s.addText("Mean anger score by party, 2011 to 2026. The lines cross at every inauguration.", { x: 7.5, y: 4.75, w: 5.3, h: 0.5, fontFace: BODY, fontSize: 10.5, color: "DFE3EC", isTextBox: true, margin: 0, italic: true });
}

// ---------- 2. the question ----------
{
  const s = pres.addSlide(); light(s); kicker(s, "THE QUESTION"); title(s, "Where does political anger actually live?");
  para(s, "Political anger online is usually described with an anecdote or a single trend line. Neither tells you the mechanism. Is anger a property of people (temperament, age), of time (hours, seasons, elections), of position (in power or out of it), or of the medium (a retweet or a call-out)?",
    M, 1.6, 6.3, 2.4, 15);
  para(s, "We treat anger as a memetic phenomenon, something that spreads and clusters, and try to locate it.", M, 4.05, 6.3, 0.9, 15, C.ink, { bold: true });
  para(s, "Given a tweet from a member of Congress, what predicts that it is angry, and how well?", M, 5.0, 6.3, 0.9, 15, C.accent, { italic: true, fontFace: HEAD, fontSize: 18 });
  // right: the five questions as cards
  const qs = [["When", "hour, month, election cycle"], ["Who", "party, person, age, volume"], ["What for", "shutdowns, presidents, tragedies"], ["To whom", "retweets vs call-outs"], ["Together or apart", "uniting vs dividing tweets"]];
  qs.forEach(([h, d], i) => {
    const y = 1.6 + i * 1.0;
    s.addShape(pres.ShapeType.roundRect, { x: 7.4, y, w: 5.3, h: 0.85, fill: { color: C.tint }, line: { color: C.tint }, rectRadius: 0.08 });
    s.addText(h, { x: 7.6, y: y + 0.1, w: 1.9, h: 0.65, fontFace: HEAD, fontSize: 16, bold: true, color: C.ink, isTextBox: true, margin: 0, valign: "middle" });
    s.addText(d, { x: 9.5, y: y + 0.1, w: 3.1, h: 0.65, fontFace: BODY, fontSize: 12.5, color: C.ink2, isTextBox: true, margin: 0, valign: "middle" });
  });
  footer(s, 2);
}

// ---------- 3. the data ----------
{
  const s = pres.addSlide(); light(s); kicker(s, "THE DATA"); title(s, "5.1 million tweets, filtered to sitting members");
  stat(s, M, 1.6, 2.9, "5.1M", "raw tweets in the HopHacks congress-tweets-unified dataset (two merged corpora, 1999 to 2026)");
  stat(s, M + 3.1, 1.6, 2.9, "4.83M", "tweets kept: members of the House and Senate, sent while in office, 2011 onward");
  stat(s, M + 6.2, 1.6, 2.9, "902", "members of Congress, 100% matched to birthdays, terms and handles");
  stat(s, M + 9.3, 1.6, 2.9, "14", "scores per tweet: 11 emotions and 3 sentiment classes");
  body(s, [
    "Source 1: the HopHacks parquet (tweet text, author, party, state, timestamp, topic).",
    "Source 2: the open unitedstates/congress-legislators dataset for birthdays, terms and Twitter handles. Handles were matched first (including 14 yearly snapshots of the social-media file, so former members are covered), then names plus state as a fallback.",
    "Dropped: executive-branch accounts (cabinet secretaries, the President), tweets members posted before they were elected, and a few corrupt pre-2011 rows.",
    "Added per tweet: age of the member that day, hour of day in the member's home-state time zone, month, and position in the two-year election cycle.",
  ], M, 3.5, 12.1, 3.3, 13.5);
  footer(s, 3);
}

// ---------- 4. processing pipeline ----------
{
  const s = pres.addSlide(); light(s); kicker(s, "HOW WE PROCESSED IT"); title(s, "From raw tweets to an anger score for each one");
  const steps = [
    ["1", "Match", "1,156 handles to bioguide IDs and birthdays; keep only in-office tweets"],
    ["2", "Enrich", "age at tweet, local hour, month, days to the next election"],
    ["3", "Score", "cardiffnlp twitter-roberta emotion model (11 emotions) and a sentiment model (3 classes)"],
    ["4", "Label", "all 4.97M tweets on a laptop RTX 4050 in under two hours (about 630 tweets per second)"],
    ["5", "Analyze", "year, party, hour, month, cycle, age, volume, spikes, networks, uniting vs dividing"],
    ["6", "Publish", "a web story, an animated interlude or two, and a marimo notebook"],
  ];
  steps.forEach(([n, h, d], i) => {
    const col = i % 3, row = Math.floor(i / 3), x = M + col * 4.1, y = 1.6 + row * 1.75;
    s.addShape(pres.ShapeType.roundRect, { x, y, w: 3.9, h: 1.55, fill: { color: C.tint }, line: { color: C.tint }, rectRadius: 0.08 });
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.18, y: y + 0.2, w: 0.5, h: 0.5, fill: { color: C.ink }, line: { color: C.ink } });
    s.addText(n, { x: x + 0.18, y: y + 0.2, w: 0.5, h: 0.5, fontFace: BODY, fontSize: 14, bold: true, color: "FFFFFF", align: "center", valign: "middle", isTextBox: true, margin: 0 });
    s.addText(h, { x: x + 0.82, y: y + 0.18, w: 2.9, h: 0.5, fontFace: HEAD, fontSize: 17, bold: true, color: C.ink, isTextBox: true, margin: 0, valign: "middle" });
    s.addText(d, { x: x + 0.18, y: y + 0.78, w: 3.55, h: 0.72, fontFace: BODY, fontSize: 11.5, color: C.ink2, isTextBox: true, margin: 0, valign: "top" });
  });
  para(s, "Choosing the model: we benchmarked three on a sample. The 4-class TweetEval model rated \"when we fight, we win!\" as rage, so it was out. The multilabel model's top-scored tweets were genuinely angry, and a separate sentiment model's negative score correlates 0.80 with it. A tweet counts as angry when P(anger) is above 0.5.",
    M, 5.2, 12.1, 1.2, 12.5, C.ink2);
  footer(s, 4);
}

// ---------- 5. result: the X ----------
{
  const s = pres.addSlide(); light(s); kicker(s, "RESULT 1"); title(s, "It's not you. It's the White House.");
  s.addChart(pres.ChartType.line, [
    { name: "Democrats", labels: YEAR.year.map(String), values: YEAR.dem },
    { name: "Republicans", labels: YEAR.year.map(String), values: YEAR.rep },
    { name: "All members", labels: YEAR.year.map(String), values: YEAR.anger },
  ], Object.assign({ x: M, y: 1.5, w: 8.0, h: 5.2, chartColors: [C.dem, C.rep, C.muted], lineSize: 2.5, lineDataSymbol: "circle", lineDataSymbolSize: 6,
    showLegend: true, legendPos: "t", valAxisMinVal: 0.1, valAxisMaxVal: 0.55, valAxisMajorUnit: 0.1, valAxisLabelFormatCode: "0.0", showTitle: true, title: "Mean anger score per tweet, by year", titleFontFace: BODY, titleFontSize: 12, titleColor: C.ink2 }, chartFrame));
  body(s, [
    "Anger sat below 0.21 through the Obama years, jumped to 0.29 in 2017 and reached 0.44 in 2025, the angriest year on record.",
    "Split by party it is an X. Democrats spike when Trump takes office (2017, 2025). Republicans spike under Biden. The lines cross at every inauguration.",
    "Each hand-over ratchets the floor higher: today's in-party (0.35) is angrier than 2017's out-party (0.34).",
  ], 9.0, 1.6, 3.75, 5.0, 13);
  footer(s, 5);
}

// ---------- 6. result: four presidencies ----------
{
  const s = pres.addSlide(); light(s); kicker(s, "RESULT 1, CONTINUED"); title(s, "Same rule, four presidencies");
  const lab = OUT.president.map((p, i) => `${p} (${OUT.president_party[i]})`);
  s.addChart(pres.ChartType.bar, [
    { name: "Democrats", labels: lab, values: OUT.dem }, { name: "Republicans", labels: lab, values: OUT.rep },
  ], Object.assign({ x: M, y: 1.5, w: 7.6, h: 5.2, barDir: "col", barGrouping: "clustered", barGapWidthPct: 60, chartColors: [C.dem, C.rep], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", dataLabelFontSize: 10, dataLabelColor: C.ink2,
    showLegend: true, legendPos: "t", valAxisMinVal: 0, valAxisMaxVal: 0.6, valAxisMajorUnit: 0.1, valAxisLabelFormatCode: "0.0", showTitle: true, title: "Mean anger by party and who holds the White House", titleFontFace: BODY, titleFontSize: 12, titleColor: C.ink2 }, chartFrame));
  stat(s, 8.6, 1.6, 4.1, "0.18 vs 0.19", "Democrats and Republicans under Obama. Equal, and calm.");
  stat(s, 8.6, 3.35, 4.1, "0.12 to 0.17", "how much angrier the out-party has been than the in-party in every presidency since");
  stat(s, 8.6, 5.1, 4.1, "0.50", "Democrats in Trump's second term, the angriest any group has ever been", C.rep);
  footer(s, 6);
}

// ---------- 7. result: seismograph ----------
{
  const s = pres.addSlide(); light(s); kicker(s, "RESULT 2"); title(s, "Congress's most reliable source of anger is Congress");
  const wk = SEIS.week.map((w) => w.slice(0, 4)), every = (arr) => arr;
  s.addChart(pres.ChartType.line, [
    { name: "Democrats", labels: wk, values: SEIS.dem }, { name: "Republicans", labels: wk, values: SEIS.rep }, { name: "All members", labels: wk, values: SEIS.anger },
  ], Object.assign({ x: M, y: 1.45, w: 7.7, h: 4.3, chartColors: [C.dem, C.rep, C.ink], lineSize: 1, lineDataSymbol: "none", showLegend: true, legendPos: "t",
    valAxisMinVal: 0, valAxisMaxVal: 0.7, valAxisMajorUnit: 0.1, valAxisLabelFormatCode: "0.0", catAxisLabelFrequency: 52, showTitle: true, title: "Weekly mean anger, 2011 to 2026", titleFontFace: BODY, titleFontSize: 12, titleColor: C.ink2 }, chartFrame));
  para(s, "Blue and red are braided together until 2017, then split into two bands and swap places at each inauguration.", M, 5.85, 7.7, 0.5, 11, C.muted, { italic: true });
  const top = SEIS.spikes.slice(0, 7);
  const rows = [[{ text: "Week", options: { bold: true } }, { text: "Event", options: { bold: true } }, { text: "Excess", options: { bold: true } }]]
    .concat(top.map((sp) => [sp.week, sp.event.replace(/—/g, ",").replace(/ ,/g, ",").replace(/–/g, " to "), "+" + sp.excess.toFixed(2)]));
  s.addTable(rows, { x: 8.55, y: 1.5, w: 4.2, colW: [1.0, 2.5, 0.7], fontFace: BODY, fontSize: 9.5, color: C.ink2, border: { type: "solid", pt: 0.5, color: C.grid }, fill: { color: "FFFFFF" }, rowH: 0.42, valign: "middle" });
  para(s, "Four of the top five spikes are government shutdowns. January 6 is the only external event in that tier. Of the 40 biggest spikes, 13 are fiscal brinkmanship, about 10 are presidential actions, and 6 are violence or tragedy, the only weeks when the two party lines converge.",
    8.55, 5.0, 4.2, 1.8, 11.5);
  footer(s, 7);
}

// ---------- 8. result: office hours ----------
{
  const s = pres.addSlide(); light(s); kicker(s, "RESULT 3"); title(s, "Anger keeps office hours");
  stat(s, M, 1.6, 3.9, "13 of 16", "years in which 9 pm to 4 am (home-state time) is angrier than that year's average. Working hours sit exactly on the average.");
  stat(s, M + 4.1, 1.6, 3.9, "14 of 16", "years in which August, the recess month, is calmer than the year's average");
  stat(s, M + 8.2, 1.6, 3.9, "6 of 7", "elections where the final four weeks were calmer than the rest of the year. There is no ramp into November in any of eight cycles.");
  para(s, "Every curve is measured against its own year, so the steep 2011 to 2026 trend cannot masquerade as a daily or seasonal pattern.", M, 3.45, 12.1, 0.5, 12, C.muted, { italic: true });
  // night owls table
  const owls = FC.owls.slice(0, 4).map((r) => [r.name, "night owl", pc(r.day), pc(r.night)]);
  const larks = FC.larks.slice(0, 3).map((r) => [r.name, "morning person", pc(r.day), pc(r.night)]);
  const rows = [[{ text: "Member", options: { bold: true } }, { text: "Type", options: { bold: true } }, { text: "Angry by day", options: { bold: true } }, { text: "Angry at night", options: { bold: true } }]].concat(owls, larks);
  s.addTable(rows, { x: M, y: 4.1, w: 7.0, colW: [2.4, 1.6, 1.5, 1.5], fontFace: BODY, fontSize: 11, color: C.ink2, border: { type: "solid", pt: 0.5, color: C.grid }, rowH: 0.32, valign: "middle" });
  para(s, "Some members run on their own clock. Mike Levin is a mild 25% angry by day and 56% after dark. Bill Hagerty is the opposite. The web story turns these nine into an animated day on the Hill, sunrise to sunset, with faces driven by the hourly numbers.",
    8.0, 4.1, 4.7, 2.5, 12.5);
  footer(s, 8);
}

// ---------- 9. result: the forecast ----------
{
  const s = pres.addSlide(); light(s); kicker(s, "RESULT 4"); title(s, "The anger forecast");
  const labels = { "nothing": "Nothing", "party = Democrat": "It's a Democrat", "hour band = 00-04": "It's 12 to 4 am", "party = Democrat, era = Trump II": "A Democrat, Trump's 2nd term",
    "party = Democrat, era = Trump II, 09-17": "and it's working hours", "Chris Van Hollen, era = Trump II, 09-17": "and it's Chris Van Hollen" };
  const L = [FC.ladder[0]].concat(FC.ladder.slice(1).filter((r) => labels[r.known]).sort((a, b) => a.p - b.p));
  s.addChart(pres.ChartType.bar, [{ name: "P(angry)", labels: L.map((r) => labels[r.known]), values: L.map((r) => +(r.p * 100).toFixed(1)) }],
    Object.assign({ x: M, y: 1.5, w: 7.4, h: 4.6, barDir: "bar", chartColors: [C.ink], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0\"%\"", dataLabelFontSize: 10, dataLabelColor: C.ink2, showLegend: false,
      valAxisMinVal: 0, valAxisMaxVal: 100, catAxisOrientation: "maxMin", showTitle: true, title: "Share of tweets that are angry, given what you know", titleFontFace: BODY, titleFontSize: 12, titleColor: C.ink2 }, chartFrame));
  body(s, [
    "Overall, 29% of tweets are angry. Knowing the party tells you nothing (29%).",
    "Knowing the party and the president moves it to 52%. The hour adds nothing on top.",
    "Knowing the person makes it nearly certain: Chris Van Hollen, 9 to 5, in Trump's second term, is a 90% forecast. If Patty Murray tweets before sunrise in that period, 84% of the time it's angry.",
    "Volume predicts anger too (Spearman 0.31). Everyone who tweets more than seven times a day is angrier than average. Except Cory Booker: 8.5 tweets a day, 18% angry.",
  ], 8.3, 1.6, 4.4, 5.0, 12.5);
  footer(s, 9);
}

// ---------- 10. result: uniting vs dividing ----------
{
  const s = pres.addSlide(); light(s); kicker(s, "RESULT 5"); title(s, "Nobody unites from opposition");
  s.addChart(pres.ChartType.line, [
    { name: "Democrats, polarizing", labels: UN.year.map(String), values: UN.polarizing.dem.map((v) => +(v * 100).toFixed(1)) },
    { name: "Republicans, polarizing", labels: UN.year.map(String), values: UN.polarizing.rep.map((v) => +(v * 100).toFixed(1)) },
  ], Object.assign({ x: M, y: 1.5, w: 6.2, h: 2.75, chartColors: [C.dem, C.rep], lineSize: 2.5, lineDataSymbol: "circle", lineDataSymbolSize: 5, showLegend: true, legendPos: "t",
    valAxisLabelFormatCode: "0\"%\"", valAxisMinVal: 0, valAxisMajorUnit: 10, showTitle: true, title: "Polarizing tweets: angry or disgusted, aimed at the other party", titleFontFace: BODY, titleFontSize: 11, titleColor: C.ink2 }, chartFrame));
  s.addChart(pres.ChartType.line, [
    { name: "Democrats, civic unity", labels: UN.year.map(String), values: UN.civic.dem.map((v) => +(v * 100).toFixed(1)) },
    { name: "Republicans, civic unity", labels: UN.year.map(String), values: UN.civic.rep.map((v) => +(v * 100).toFixed(1)) },
  ], Object.assign({ x: M, y: 4.3, w: 6.2, h: 2.6, chartColors: [C.dem, C.rep], lineSize: 2.5, lineDataSymbol: "diamond", lineDataSymbolSize: 5, showLegend: true, legendPos: "t",
    valAxisLabelFormatCode: "0.0\"%\"", valAxisMinVal: 0, valAxisMajorUnit: 2, showTitle: true, title: "Civic unity tweets: positive, and explicitly cross-party", titleFontFace: BODY, titleFontSize: 11, titleColor: C.ink2 }, chartFrame));
  s.addChart(pres.ChartType.line, [{ name: "distance", labels: UN.distance.year.map(String), values: UN.distance.d }],
    Object.assign({ x: 7.1, y: 1.5, w: 5.65, h: 2.75, chartColors: [C.ink], lineSize: 2.5, lineDataSymbol: "circle", lineDataSymbolSize: 5, showLegend: false, valAxisMinVal: 0, valAxisMaxVal: 0.5, valAxisMajorUnit: 0.1, valAxisLabelFormatCode: "0.0",
      showTitle: true, title: "How far apart the parties feel (distance between 11-emotion profiles)", titleFontFace: BODY, titleFontSize: 11, titleColor: C.ink2 }, chartFrame));
  body(s, [
    "Polarizing tweets belong to the out-party: Democrats 17% in 2017, Republicans 25% in 2022, Democrats 35% in 2025, the record.",
    "Civic unity belongs to the in-party. Republicans' peak is 2018, Democrats' is 2024. In 2025 both fall to 2.6%.",
    "The parties felt roughly the same things until 2016, split in 2017 (anger), came back together in 2020 (the pandemic year), and have been apart since 2021, where the gap is optimism, and in 2025, disgust.",
  ], 7.1, 4.35, 5.65, 2.6, 11.5);
  footer(s, 10);
}

// ---------- 11. result: two networks ----------
{
  const s = pres.addSlide(); light(s); kicker(s, "RESULT 6"); title(s, "Two networks, one Congress");
  s.addImage({ path: path.join(ROOT, "figures/network_preview.png"), x: M, y: 1.45, w: 7.9, h: 3.95 });
  para(s, "Left: who retweets whom. Right: who addresses whom in public with .@ (a call-out when it crosses the aisle). Democrats on the left arc, Republicans on the right, hubs nearest the centre, line width by tweet count.", M, 5.45, 7.9, 0.7, 10.5, C.muted, { italic: true });
  const S = NET.summary;
  stat(s, 8.8, 1.5, 3.9, pc(S.retweet.cross_tweet_share) + " cross the aisle", `of ${S.retweet.tweets.toLocaleString()} retweets of fellow members. Their anger: ${S.retweet.anger_cross.toFixed(2)}, the calmest tweets in Congress (${S.retweet.anger_same.toFixed(2)} within a party).`, C.gold);
  stat(s, 8.8, 3.25, 3.9, pc(S.dot.cross_tweet_share) + " cross the aisle", `of ${S.dot.tweets.toLocaleString()} public call-outs. Their anger: ${S.dot.anger_cross.toFixed(2)}, the angriest (${S.dot.anger_same.toFixed(2)} within a party).`, C.rep);
  para(s, "Lightning rods: Pelosi (514 call-outs, anger 0.76), McConnell (338, 0.63), Schumer (136, 0.82). Bridges: Massie, DeGette, McCain. Massie and McCain are on both lists, the only people both sides retweet and yell at.",
    8.8, 5.0, 3.9, 1.7, 11.5);
  footer(s, 11);
}

// ---------- 12. patterns ----------
{
  const s = pres.addSlide(); light(s); kicker(s, "THE PATTERNS"); title(s, "Five things the data keeps saying");
  const P = [
    ["Anger is positional, not personal", "The same people are calm in power and furious out of it. Age adds nothing once you know the party: the within-person slope is a tight zero."],
    ["Events beat the calendar", "No ramp into elections in eight cycles. Shutdowns, Jan 6 and presidential actions make the spikes. The month before an election is the calm one."],
    ["Volume predicts anger", "The prolific are angry, because anger is the high-volume genre. The one exception, Cory Booker, is the kind of thing a reader remembers."],
    ["The medium is the mood", "Retweets across the aisle are the calmest tweets we have. Call-outs across the aisle are the angriest, and they go straight to party leaders."],
    ["The floor ratchets", "Every hand-over of the White House leaves the baseline higher than it found it. The in-party of 2025 is angrier than the out-party of 2017."],
  ];
  P.forEach(([h, d], i) => {
    const y = 1.5 + i * 1.08;
    s.addShape(pres.ShapeType.ellipse, { x: M, y: y + 0.12, w: 0.55, h: 0.55, fill: { color: i === 4 ? C.rep : C.ink }, line: { color: i === 4 ? C.rep : C.ink } });
    s.addText(String(i + 1), { x: M, y: y + 0.12, w: 0.55, h: 0.55, fontFace: BODY, fontSize: 15, bold: true, color: "FFFFFF", align: "center", valign: "middle", isTextBox: true, margin: 0 });
    s.addText(h, { x: M + 0.8, y, w: 4.2, h: 0.85, fontFace: HEAD, fontSize: 17, bold: true, color: C.ink, isTextBox: true, margin: 0, valign: "middle" });
    s.addText(d, { x: 5.7, y, w: 7.0, h: 0.95, fontFace: BODY, fontSize: 12.5, color: C.ink2, isTextBox: true, margin: 0, valign: "middle" });
  });
  footer(s, 12);
}

// ---------- 13. conclusion ----------
{
  const s = pres.addSlide(); dark(s);
  s.addText("CONCLUSION", { x: M, y: 0.7, w: 8, h: 0.35, fontFace: BODY, fontSize: 12, color: "DFE3EC", charSpacing: 2, isTextBox: true, margin: 0 });
  s.addText("Anger in Congress is a jersey.", { x: M, y: 1.15, w: 12, h: 1.2, fontFace: HEAD, fontSize: 44, bold: true, color: "FFFFFF", isTextBox: true, margin: 0, valign: "middle" });
  s.addText("You put it on when your side loses the White House and take it off when you win. It does not spread evenly. It jumps to the losing party, concentrates on a handful of lightning rods, ratchets the baseline up each cycle, and it is loudest at 2 am, in October, during a shutdown.",
    { x: M, y: 2.45, w: 7.4, h: 2.0, fontFace: BODY, fontSize: 16, color: "EEF1F7", isTextBox: true, margin: 0, valign: "top" });
  s.addText([
    { text: "Limits. ", options: { bold: true } }, { text: "Scores are model estimates, spot-checked by hand. Hours use home-state time, which is wrong when a member is in Washington. The 2023 to 2024 collection has almost no retweets. We see explicit public call-outs only, not replies or quote tweets.", options: { breakLine: true } },
    { text: "Next. ", options: { bold: true } }, { text: "The other ten emotions are already scored: fear should spike on shootings and COVID where anger spikes on shutdowns. Per-member change points (\"the day X stopped being nice\"). A weekday vs weekend split, which is probably a staff vs member split." },
  ], { x: M, y: 4.6, w: 7.4, h: 2.3, fontFace: BODY, fontSize: 11.5, color: "DFE3EC", isTextBox: true, margin: 0, valign: "top", paraSpaceAfter: 8 });
  // right column: what we built
  const built = [["Web story", "six chapters, two animated interludes: a day on the Hill, and the parties' emotional distance as Gone with the Wind"], ["marimo notebook", "every chart interactive, the forecast as a function, a custom anywidget, on molab"], ["Pipeline", "reproducible from the raw parquet: match, enrich, label on GPU, analyze, export"]];
  built.forEach(([h, d], i) => {
    const y = 2.45 + i * 1.35;
    s.addShape(pres.ShapeType.roundRect, { x: 8.6, y, w: 4.1, h: 1.2, fill: { color: "5C6885" }, line: { color: "5C6885" }, rectRadius: 0.08 });
    s.addText(h, { x: 8.8, y: y + 0.1, w: 3.7, h: 0.4, fontFace: HEAD, fontSize: 15, bold: true, color: "FFFFFF", isTextBox: true, margin: 0 });
    s.addText(d, { x: 8.8, y: y + 0.5, w: 3.7, h: 0.65, fontFace: BODY, fontSize: 10.5, color: "EEF1F7", isTextBox: true, margin: 0, valign: "top" });
  });
  s.addText("github.com/biniyam112/hophacks-tweet-sentiment", { x: M, y: 6.85, w: 8, h: 0.35, fontFace: MONO, fontSize: 11, color: "CFD5E3", isTextBox: true, margin: 0 });
}

pres.writeFile({ fileName: path.join(__dirname, "whats_making_us_angry.pptx") }).then((f) => console.log("wrote", f));
