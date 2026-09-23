"""Animated explainer for "What's making US angry?" (silent, captions on screen, ~90 s, 1920x1080, 30 fps).

Every scene is drawn frame by frame from the site's data files (site/data/*.json) with PIL, plus matplotlib
for the chart scenes. Output: deck/whats_making_us_angry_demo.mp4
"""
import json, math, os, random
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

ROOT = os.path.join(os.path.dirname(__file__), "..")
D = lambda n: json.load(open(os.path.join(ROOT, "site/data", n + ".json"), encoding="utf8"))
YEAR, OUT, SEIS, HOUR, MONTH, FC, UN, NET, ST = D("year"), D("outparty"), D("seismograph"), D("hour"), D("month"), D("forecast"), D("unity"), D("network"), D("statement")

W, H, FPS = 1920, 1080, 30
PAGE, CARD, INK, INK2, MUTED, GRID = (111, 123, 152), (255, 255, 255), (11, 11, 11), (82, 81, 78), (137, 135, 129), (225, 224, 217)
DEM, REP, GOLD, ACCENT = (42, 120, 214), (227, 73, 72), (237, 161, 0), (235, 104, 52)
FONTS = "C:/Windows/Fonts/"
def font(name, size):
    for f in [name, "georgia.ttf"]:
        try: return ImageFont.truetype(FONTS + f, size)
        except OSError: pass
    return ImageFont.load_default()
SERIF, SERIF_I, SERIF_B = "georgia.ttf", "georgiai.ttf", "georgiab.ttf"
SANS, SANS_B, MONO = "segoeui.ttf", "segoeuib.ttf", "consola.ttf"
ease = lambda t: 0.5 - 0.5 * math.cos(math.pi * min(1, max(0, t)))
lerp = lambda a, b, t: a + (b - a) * t
mixc = lambda a, b, t: tuple(int(lerp(x, y, t)) for x, y in zip(a, b))

# ---------------- frame helpers ----------------
def base():
    return Image.new("RGB", (W, H), PAGE)
def card(im, x0=120, y0=150, x1=W - 120, y1=H - 210):
    ImageDraw.Draw(im).rounded_rectangle([x0, y0, x1, y1], radius=14, fill=CARD)
def caption(im, text, y=H - 150, color=(255, 255, 255), size=44, italic=True):
    d = ImageDraw.Draw(im); f = font(SERIF_I if italic else SERIF, size)
    w = d.textlength(text, font=f); d.text(((W - w) / 2, y), text, font=f, fill=color)
def kicker(im, text, y=95, color=(223, 227, 236)):
    d = ImageDraw.Draw(im); f = font(SANS, 24); w = d.textlength(text, font=f); d.text(((W - w) / 2, y), text, font=f, fill=color)
def text(im, s, xy, f, fill, anchor="la"):
    ImageDraw.Draw(im).text(xy, s, font=f, fill=fill, anchor=anchor)
def fig_to_image(fig):
    canvas = FigureCanvasAgg(fig); canvas.draw()
    return Image.frombuffer("RGBA", canvas.get_width_height(), canvas.buffer_rgba(), "raw", "RGBA", 0, 1).convert("RGB")
def chart_fig(w_in, h_in):
    fig = plt.figure(figsize=(w_in, h_in), dpi=100, facecolor="white")
    ax = fig.add_axes([0.07, 0.12, 0.9, 0.78]); ax.set_facecolor("white")
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.grid(True, color="#e1e0d9", lw=1); ax.set_axisbelow(True); ax.tick_params(colors="#898781", labelsize=15, length=0)
    return fig, ax
def paste_chart(im, fig, x, y):
    im.paste(fig_to_image(fig), (x, y)); plt.close(fig)

# ---------------- scenes (each yields PIL frames) ----------------
def scene_open(sec=6):
    n = sec * FPS; random.seed(3)
    cards = [dict(x=random.randint(140, W - 260), t0=random.random() * 0.75, v=random.uniform(320, 520), angry=random.random() < 0.293, w=random.randint(110, 190)) for _ in range(140)]
    for k in range(n):
        t = k / n; im = base(); d = ImageDraw.Draw(im)
        for c in cards:
            tt = (t - c["t0"]) * sec
            if tt < 0: continue
            y = -60 + c["v"] * tt
            if y > H: continue
            scored = y > 420
            col = (REP if c["angry"] else (200, 203, 214)) if scored else (170, 178, 200)
            d.rounded_rectangle([c["x"], y, c["x"] + c["w"], y + 34], radius=8, fill=col)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        od.rounded_rectangle([420, 360, W - 420, 640], radius=24, fill=(111, 123, 152, 215)); od.rectangle([0, H - 175, W, H - 80], fill=(111, 123, 152, 215))
        im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
        cnt = int(4832639 * ease(min(1, t / 0.75)))
        text(im, f"{cnt:,}", (W / 2, 470), font(SANS_B, 150), (255, 255, 255), "mm")
        text(im, "tweets by 902 members of Congress, 2011 to 2026, scored for anger", (W / 2, 580), font(SANS, 34), (238, 241, 247), "mm")
        kicker(im, "WHAT'S MAKING US ANGRY?  ·  HOPHACKS 2026")
        caption(im, "We scored every tweet from every sitting member of Congress.")
        yield im

def scene_x(sec=14):
    n = sec * FPS; yrs = YEAR["year"]; N = len(yrs)
    for k in range(n):
        t = k / n; im = base(); card(im); kicker(im, "RESULT 1", color=(223, 227, 236))
        fig, ax = chart_fig(16.8, 6.8)
        ax.set_xlim(2010.5, 2026.5); ax.set_ylim(0.1, 0.56); ax.set_xticks(yrs); ax.set_yticks([0.2, 0.3, 0.4, 0.5])
        for x, lab in [(2017, "Trump"), (2021, "Biden"), (2025, "Trump II")]:
            if t > 0.42 + (x - 2017) / 9 * 0.5:
                ax.axvline(x, color="#e1e0d9", lw=1.5); ax.text(x + 0.1, 0.545, lab, color="#898781", fontsize=15, va="top")
        p1 = ease(min(1, t / 0.4)) * (N - 1)                       # phase 1: the single line draws
        i1 = int(p1); frac = p1 - i1
        xs = yrs[: i1 + 1] + ([yrs[i1] + frac] if i1 < N - 1 else []); ys = YEAR["anger"][: i1 + 1] + ([lerp(YEAR["anger"][i1], YEAR["anger"][i1 + 1], frac)] if i1 < N - 1 else [])
        ax.plot(xs, ys, color="#0b0b0b" if t < 0.42 else "#898781", lw=3.5 if t < 0.42 else 2, ls="-" if t < 0.42 else ":", marker="o" if t < 0.42 else None, ms=8)
        if t > 0.42:                                                 # phase 2: split into parties
            p2 = ease(min(1, (t - 0.42) / 0.5)) * (N - 1); i2 = int(p2); fr = p2 - i2
            for key, col in [("dem", DEM), ("rep", REP)]:
                v = YEAR[key]; xs = yrs[: i2 + 1] + ([yrs[i2] + fr] if i2 < N - 1 else []); ys = v[: i2 + 1] + ([lerp(v[i2], v[i2 + 1], fr)] if i2 < N - 1 else [])
                ax.plot(xs, ys, color="#%02x%02x%02x" % col, lw=4, marker="o", ms=8, markevery=list(range(i2 + 1)))
        ax.set_ylabel("mean anger score", color="#52514e", fontsize=15)
        paste_chart(im, fig, 120, 160)
        text(im, "Mean anger score per tweet, by year" if t < 0.42 else "Split by party, it is an X. The lines cross at every inauguration.", (W / 2, 190), font(SERIF_B, 34), INK, "mm")
        caption(im, "Anger doubled since 2011." if t < 0.42 else "Whoever is out of power is angry.")
        yield im

def scene_presidencies(sec=8):
    n = sec * FPS; labs = [f"{p} ({q})" for p, q in zip(OUT["president"], OUT["president_party"])]
    for k in range(n):
        t = k / n; im = base(); card(im); kicker(im, "RESULT 1, CONTINUED")
        fig, ax = chart_fig(16.8, 6.8); ax.set_ylim(0, 0.6); ax.set_xlim(-0.6, 3.6); ax.set_xticks(range(4)); ax.set_xticklabels(labs, fontsize=17, color="#52514e")
        for i in range(4):
            g = ease(min(1, max(0, (t * sec - i * 1.6) / 1.4)))
            for j, (key, col) in enumerate([("dem", DEM), ("rep", REP)]):
                v = OUT[key][i] * g; x = i + (j - 0.5) * 0.36
                ax.bar(x, v, width=0.34, color="#%02x%02x%02x" % col)
                if g > 0.95: ax.text(x, v + 0.012, f"{OUT[key][i]:.2f}", ha="center", fontsize=16, color="#52514e", fontweight="bold" if (i == 3 and key == "dem") else "normal")
        ax.set_ylabel("mean anger score", color="#52514e", fontsize=15)
        paste_chart(im, fig, 120, 160)
        text(im, "Same rule, four presidencies", (W / 2, 190), font(SERIF_B, 34), INK, "mm")
        caption(im, "Under Obama both parties were calm. Since then, the out-party is the angry one." if t < 0.8 else "Today's in-party is angrier than 2017's out-party. The floor never resets.")
        yield im

def scene_seismo(sec=12):
    n = sec * FPS; wk = SEIS["week"]; N = len(wk); xs = np.arange(N)
    top = sorted(SEIS["spikes"], key=lambda s: -s["excess"])[:5]; idx = {wk.index(s["week"]): s for s in top if s["week"] in wk}
    lift = {i: 26 + 38 * (r % 3) for r, i in enumerate(sorted(idx))}     # staggered label heights, in chronological order
    short = {"2013-09-30": "Shutdown", "2021-01-04": "January 6", "2025-09-29": "Shutdown", "2019-01-07": "Shutdown", "2018-01-15": "Shutdown"}
    ticks = [i for i, w in enumerate(wk) if w.endswith("-01-0") or (w[5:7] == "01" and (i == 0 or wk[i - 1][:4] != w[:4]))]
    for k in range(n):
        t = k / n; im = base(); card(im); kicker(im, "RESULT 2")
        upto = int(ease(min(1, t / 0.9)) * (N - 1))
        fig, ax = chart_fig(16.8, 6.8); ax.set_xlim(0, N); ax.set_ylim(0.05, 0.68)
        ax.set_xticks(ticks); ax.set_xticklabels([wk[i][:4] for i in ticks], fontsize=14)
        ax.plot(xs[:upto], SEIS["dem"][:upto], color="#2a78d6", lw=1, alpha=0.7); ax.plot(xs[:upto], SEIS["rep"][:upto], color="#e34948", lw=1, alpha=0.7)
        ax.plot(xs[:upto], SEIS["anger"][:upto], color="#0b0b0b", lw=1.6)
        for i, s in idx.items():
            if i <= upto:
                ax.plot([i], [s["anger"]], marker="D", ms=11, color="#e34948", mec="white", mew=1.5)
                ax.annotate(short.get(s["week"], s["event"]), (i, s["anger"]), xytext=(0, lift[i]), textcoords="offset points", ha="center", fontsize=15, fontweight="bold", color="#0b0b0b",
                            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#e1e0d9"), arrowprops=dict(arrowstyle="-", color="#c3c2b7", lw=1))
        ax.set_ylabel("mean anger, weekly", color="#52514e", fontsize=15)
        paste_chart(im, fig, 120, 160)
        text(im, "The seismograph: weekly anger, 2011 to 2026", (W / 2, 190), font(SERIF_B, 34), INK, "mm")
        caption(im, "Four of the five biggest spikes are government shutdowns." if t > 0.55 else "Week by week, with the biggest spikes labelled as the line reaches them.")
        yield im

def scene_hours(sec=8):
    n = sec * FPS; hm = HOUR["mean"]; mm = MONTH["mean"]; hmax = max(abs(v) for v in hm); mmax = max(abs(v) for v in mm)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for k in range(n):
        t = k / n; im = base(); card(im); kicker(im, "RESULT 3"); d = ImageDraw.Draw(im)
        text(im, "Anger keeps office hours", (W / 2, 190), font(SERIF_B, 34), INK, "mm")
        # clock: 24 sectors coloured by deviation; hand sweeps over the first 5 s
        cx, cy, r = 560, 560, 250; sweep = ease(min(1, t * sec / 5)) * 24
        for h in range(24):
            v = hm[h] / hmax; col = mixc((241, 240, 236), REP, max(0, v)) if v > 0 else mixc((241, 240, 236), (190, 205, 225), min(1, -v))
            if h <= sweep: d.pieslice([cx - r, cy - r, cx + r, cy + r], h * 15 - 90, (h + 1) * 15 - 90, fill=col, outline=CARD, width=2)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GRID, width=3)
        for h in [0, 6, 12, 18]:
            a = math.radians(h * 15 - 90); text(im, {0: "midnight", 6: "6 am", 12: "noon", 18: "6 pm"}[h], (cx + (r + 42) * math.cos(a), cy + (r + 42) * math.sin(a)), font(SANS, 20), INK2, "mm")
        a = math.radians(min(sweep, 24) * 15 - 90); d.line([cx, cy, cx + (r - 30) * math.cos(a), cy + (r - 30) * math.sin(a)], fill=INK, width=8); d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=INK)
        text(im, "hour of day, home-state time · red = angrier than that year's average", (cx, cy + r + 90), font(SANS, 20), MUTED, "mm")
        # calendar: months appear one by one from 3 s
        for m in range(12):
            g = ease(min(1, max(0, (t * sec - 3 - m * 0.25) / 0.5)))
            if g <= 0: continue
            v = mm[m] / mmax; col = mixc((241, 240, 236), REP, max(0, v) * 0.9) if v > 0 else mixc((241, 240, 236), (190, 205, 225), min(1, -v))
            x = 1000 + (m % 4) * 200; y = 330 + (m // 4) * 160
            d.rounded_rectangle([x, y, x + 180, y + 140], radius=10, fill=mixc(CARD, col, g))
            text(im, months[m], (x + 90, y + 55), font(SANS_B, 30), mixc(CARD, INK, g), "mm")
            text(im, f"{mm[m]:+.3f}", (x + 90, y + 100), font(MONO, 20), mixc(CARD, INK2, g), "mm")
        text(im, "month · deviation from the year's average", (1390, 820), font(SANS, 20), MUTED, "mm")
        caption(im, "Working hours sit on the average. After 9 pm is angrier in 13 of 16 years." if t < 0.5 else "August recess is the calm month, 14 years out of 16.")
        yield im

def scene_forecast(sec=11):
    n = sec * FPS
    labels = {"nothing": "Nothing", "party = Democrat": "It's a Democrat", "hour band = 00-04": "It's 12 to 4 am", "party = Democrat, era = Trump II": "A Democrat, Trump's 2nd term",
              "party = Democrat, era = Trump II, 09-17": "and it's working hours", "Chris Van Hollen, era = Trump II, 09-17": "and it's Chris Van Hollen"}
    L = [FC["ladder"][0]] + sorted([r for r in FC["ladder"][1:] if r["known"] in labels], key=lambda r: r["p"])
    icons = ["?", "D", "☾", "D+T", "D+T+9", "V+T+9"]
    for k in range(n):
        t = k / n; im = base(); card(im); kicker(im, "RESULT 4"); d = ImageDraw.Draw(im)
        text(im, "The anger forecast: each thing you learn moves the odds", (W / 2, 190), font(SERIF_B, 34), INK, "mm")
        x0, bw = 760, 900
        for i, r in enumerate(L):
            g = ease(min(1, max(0, (t * sec - 0.6 - i * 1.25) / 1.0)))
            y = 290 + i * 100
            text(im, labels[r["known"]], (x0 - 30, y + 30), font(SANS, 28), INK2, "rm")
            d.rounded_rectangle([x0, y, x0 + bw, y + 60], radius=8, fill=(241, 240, 236))
            if g > 0:
                col = REP if r["known"].startswith("Chris") else INK
                d.rounded_rectangle([x0, y, x0 + max(12, bw * r["p"] * g), y + 60], radius=8, fill=col)
                text(im, f"{r['p']*100:.0f}%", (x0 + bw * r["p"] * g + 18, y + 30), font(SANS_B, 30), col if g > 0.95 else MUTED, "lm")
        d.line([x0 + bw * FC["baseline"], 280, x0 + bw * FC["baseline"], 880], fill=MUTED, width=2)
        text(im, "Congress average 29%", (x0 + bw * FC["baseline"] + 10, 880), font(SANS, 20), MUTED, "lm")
        caption(im, "Knowing the party tells you nothing. Knowing the party and the president tells you a lot." if t < 0.7 else "Knowing the person makes it nearly certain.")
        yield im

def scene_romance(sec=16):
    n = sec * FPS; mo = UN["distance_month"]["mo"]; dist = UN["distance_month"]["d"]; N = len(mo)
    sm = [np.mean(dist[max(0, i - 2): i + 3]) for i in range(N)]
    yrs = {y: (g, s.startswith("Democrats")) for y, g, s in zip(UN["distance"]["year"], UN["distance"]["gap"], UN["distance"]["sign"])}
    acts = [(2011, "Act I: the ball"), (2017, "Act II: the quarrel"), (2019, "Act III: the pandemic, together"), (2021, "Act IV: separate bedrooms"), (2025, "Act V: the last word is disgust")]
    faces = {"optimism": (-8, 0.6), "joy": (-10, 1.0), "anger": (18, -0.8), "disgust": (8, -0.6), "sadness": (-14, -0.6), "fear": (-12, -0.3), "neutral": (0, 0.15)}
    moods = {2011: (58, 42, 34), 2017: (43, 38, 36), 2019: (46, 34, 28), 2021: (38, 41, 46), 2025: (27, 26, 31)}
    def figure(d, cx, cy, col, emo, on, masked, side):
        d.rounded_rectangle([cx - 70, cy + 40, cx + 70, cy + 260], radius=60, fill=col)
        d.ellipse([cx - 60, cy - 60, cx + 60, cy + 60], fill=(243, 213, 181), outline=(58, 42, 34), width=3)
        d.chord([cx - 60, cy - 60, cx + 60, cy + 60], 200, 340, fill=(59, 42, 26) if side < 0 else (26, 26, 26))
        b, m = faces.get(emo if on else "neutral", faces["neutral"]); s = side
        for ex in (-22, 22): d.ellipse([cx + ex - 6, cy - 8, cx + ex + 6, cy + 4], fill=INK)
        tilt = b * 0.35
        d.line([cx - 36, cy - 26 - s * tilt * 0.5, cx - 10, cy - 26 + s * tilt * 0.5], fill=INK, width=5); d.line([cx + 10, cy - 26 + s * tilt * 0.5, cx + 36, cy - 26 - s * tilt * 0.5], fill=INK, width=5)
        if masked:
            d.rounded_rectangle([cx - 36, cy + 6, cx + 36, cy + 42], radius=10, fill=(219, 233, 247), outline=(159, 189, 220), width=2)
        else:
            pts = [(cx - 20 + 40 * u / 10, cy + 22 + 22 * m * (1 - (2 * u / 10 - 1) ** 2)) for u in range(11)]; d.line(pts, fill=INK, width=5)
    for k in range(n):
        t = k / n; p = ease(min(1, t / 0.97)) * (N - 1); i = int(p); f = p - i
        d_ = lerp(sm[i], sm[min(i + 1, N - 1)], f); y = int(mo[i][:4]); gap, demH = yrs[y]
        act = [a for a in acts if y >= a[0]][-1]; mood = moods[act[0]]
        im = Image.new("RGB", (W, H), mood); d = ImageDraw.Draw(im)
        d.rectangle([0, 720, W, H - 100], fill=(48, 34, 24)); d.rectangle([0, H - 100, W, H], fill=PAGE)
        d.rounded_rectangle([860, 120, 1060, 460], radius=100, fill=mixc((247, 217, 160), (32, 36, 44), (act[0] - 2011) / 14), outline=(42, 28, 19), width=10)
        d.line([960, 130, 960, 450], fill=(42, 28, 19), width=6); d.line([870, 290, 1050, 290], fill=(42, 28, 19), width=6)
        d.line([600, 0, 600, 40], fill=(201, 162, 75), width=3); d.ellipse([W / 2 - 70, 30, W / 2 + 70, 60], outline=(201, 162, 75), width=4)
        half = lerp(120, 720, min(1, max(0, (d_ - 0.05) / 0.55)))
        masked = "2020-03" <= mo[i][:7] <= "2021-05"
        figure(d, int(W / 2 - half), 470, DEM, gap, demH, masked, 1); figure(d, int(W / 2 + half), 470, REP, gap, not demH, masked, -1)
        text(im, "Democrats", (W / 2 - half, 770), font(SANS_B, 22), (255, 255, 255), "mm"); text(im, "Republicans", (W / 2 + half, 770), font(SANS_B, 22), (255, 255, 255), "mm")
        text(im, mo[i][:7].replace("-", " / "), (60, 60), font(MONO, 48), (255, 255, 255)); text(im, f"distance {dist[i]:.2f}", (W - 60, 60), font(MONO, 48), (255, 255, 255), "ra")
        text(im, act[1], (W / 2, 640), font(SERIF_I, 40), (255, 230, 168), "mm")
        text(im, f"the gap is {gap}", (W / 2, 690), font(SANS, 24), (223, 227, 236), "mm")
        caption(im, "Two households, one Capitol: their distance apart is the measured emotional distance, month by month.", y=H - 72, size=30)
        yield im

def scene_network(sec=9):
    n = sec * FPS; nodes = NET["nodes"]
    score = lambda nd: nd["rt_in"] + 4 * nd["dot_in"]
    left = sorted([nd for nd in nodes if nd["party"] != "Republican"], key=score, reverse=True); right = sorted([nd for nd in nodes if nd["party"] == "Republican"], key=score, reverse=True)
    def place(arr, side):
        for j, nd in enumerate(arr):
            tt = ((1 if j % 2 else -1) * math.ceil(j / 2)) / len(arr); ang = tt * math.pi * 150 / 180
            nd["px"] = side * (0.42 + (1 - math.cos(ang)) * 0.9); nd["py"] = math.sin(ang) * 1.05
    place(left, -1); place(right, 1); by = {nd["id"]: nd for nd in nodes}
    def panel(im, edges, x0, w, crossc, frac, title, sub):
        d = ImageDraw.Draw(im); cx, cy, sx, sy = x0 + w / 2, 560, w / 3.2, 300
        E = edges[: int(len(edges) * frac)]
        for a, b, cnt, _ in E:
            u, v = by.get(a), by.get(b)
            if not u or not v: continue
            cross = u["party"] != v["party"] and "Independent" not in (u["party"], v["party"])
            d.line([cx + u["px"] * sx, cy + u["py"] * sy, cx + v["px"] * sx, cy + v["py"] * sy], fill=crossc if cross else (215, 214, 208), width=2 if cross else 1)
        for nd in nodes:
            r = 3 + 6 * math.sqrt(score(nd) / max(1, score(left[0])))
            d.ellipse([cx + nd["px"] * sx - r, cy + nd["py"] * sy - r, cx + nd["px"] * sx + r, cy + nd["py"] * sy + r], fill=DEM if nd["party"] == "Democrat" else REP if nd["party"] == "Republican" else MUTED)
        text(im, title, (cx, 240), font(SERIF_B, 30), INK, "mm"); text(im, sub, (cx, 880), font(SANS, 24), INK2, "mm")
    for k in range(n):
        t = k / n; im = base(); card(im); kicker(im, "RESULT 6")
        panel(im, NET["retweet"], 130, 830, GOLD, ease(min(1, t / 0.45)), "Who retweets whom", "2% cross the aisle, the calmest tweets in Congress")
        if t > 0.45: panel(im, NET["dot"], 960, 830, REP, ease(min(1, (t - 0.45) / 0.45)), "Who calls out whom", "37% cross the aisle, the angriest, aimed at party leaders")
        caption(im, "Two networks, one Congress." if t < 0.5 else "Retweets stay home. Call-outs cross the aisle.")
        yield im

def scene_close(sec=6):
    n = sec * FPS
    for k in range(n):
        t = k / n; im = base(); g = ease(min(1, t / 0.5))
        text(im, "What's making US angry?", (W / 2, 330), font(SERIF_B, 96), mixc(PAGE, (255, 255, 255), g), "mm")
        text(im, "Anger in Congress isn't an opinion. It's a jersey you put on when your side loses the White House.", (W / 2, 470), font(SANS, 36), mixc(PAGE, (238, 241, 247), g), "mm")
        g2 = ease(min(1, max(0, (t - 0.35) / 0.4)))
        text(im, "biniyam112.github.io/hophacks-tweet-sentiment", (W / 2, 640), font(MONO, 34), mixc(PAGE, (255, 255, 255), g2), "mm")
        text(im, "github.com/biniyam112/hophacks-tweet-sentiment   ·   marimo notebook on molab", (W / 2, 700), font(MONO, 24), mixc(PAGE, (207, 213, 227), g2), "mm")
        text(im, "HopHacks 2026", (W / 2, 900), font(SANS, 24), mixc(PAGE, (223, 227, 236), g2), "mm")
        yield im

# ---------------- assemble with crossfades ----------------
SCENES = [scene_open, scene_x, scene_presidencies, scene_seismo, scene_hours, scene_forecast, scene_romance, scene_network, scene_close]
XF = 12   # crossfade frames
out = os.path.join(os.path.dirname(__file__), "whats_making_us_angry_demo.mp4")
vw = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
prev_tail = []; total = 0
for si, sc in enumerate(SCENES):
    frames = list(sc())
    if prev_tail:
        for j in range(XF):
            a = ease((j + 1) / XF); mixed = Image.blend(prev_tail[j], frames[j], a)
            vw.write(cv2.cvtColor(np.array(mixed), cv2.COLOR_RGB2BGR)); total += 1
        frames = frames[XF:]
    body = frames[:-XF] if si < len(SCENES) - 1 else frames
    for fr in body: vw.write(cv2.cvtColor(np.array(fr), cv2.COLOR_RGB2BGR)); total += 1
    prev_tail = frames[-XF:]
    print(f"scene {si + 1}/{len(SCENES)} done, {total} frames", flush=True)
vw.release()
print(f"wrote {out}: {total} frames = {total / FPS:.1f} s")
