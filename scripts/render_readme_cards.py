#!/usr/bin/env python3
"""Render Aazim's GitHub profile cards as animated SVGs into cards/.

Method (per Avi Vashishta's write-up): a GitHub README cannot run JS or CSS,
but an SVG shown via <img> runs its own <style> keyframes and SMIL. So every
visual lives inside the SVGs: embedded subset fonts, CSS entrance animations
staggered top-to-bottom, SMIL count-ups and a shine sweep, all disabled under
prefers-reduced-motion.

Data: data/contributions.json (scripts/fetch_contributions.py) and
assets/portrait.txt (scripts/make_portrait.py).

STATIC=1 renders the final frame only (no animations / SMIL) for screenshots.
"""
import base64
import json
import math
import os
from datetime import date, timedelta
from xml.sax.saxutils import escape as esc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.environ.get("STATIC") == "1"

PAPER = "#FAF6EF"
CARD = "#FFFFFF"
INK = "#191D23"
BODY = "#3A4150"
MUTED = "#6E7683"
LINE = "#E5DDCE"
BLUE = "#2456C8"
RED = "#B3372B"
GOLD = "#B97A0F"
HEAT = ["#E9EDF5", "#B9C8EE", "#7E97E0", "#4668C9", "#23439A"]


def font_css() -> str:
    def b64(name):
        with open(os.path.join(ROOT, "fonts", name), "rb") as f:
            return base64.b64encode(f.read()).decode()
    return (
        f"@font-face{{font-family:'PSerif';src:url(data:font/woff;base64,{b64('serif.woff')})}}"
        f"@font-face{{font-family:'PSans';font-weight:400;src:url(data:font/woff;base64,{b64('sans.woff')})}}"
        f"@font-face{{font-family:'PSans';font-weight:700;src:url(data:font/woff;base64,{b64('sans-bold.woff')})}}"
        f"@font-face{{font-family:'PMono';src:url(data:font/woff;base64,{b64('mono.woff')})}}"
        ".serif{font-family:'PSerif',Georgia,serif}"
        ".sans{font-family:'PSans',Arial,sans-serif}"
        ".mono{font-family:'PMono','Courier New',monospace}"
    )


ANIM_CSS = (
    "@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}"
    ".rise{animation:rise .8s cubic-bezier(.2,.7,.3,1) both}"
    "@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}"
    ".grow{transform-box:fill-box;transform-origin:50% 100%;animation:grow .9s cubic-bezier(.2,.7,.3,1) both}"
    "@keyframes growx{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
    ".growx{transform-box:fill-box;transform-origin:0 50%;animation:growx .8s cubic-bezier(.2,.7,.3,1) both}"
    "@keyframes pop{from{opacity:0;transform:scale(.2)}to{opacity:1;transform:scale(1)}}"
    ".pop{transform-box:fill-box;transform-origin:center;animation:pop .45s ease-out both}"
    "@keyframes swing{0%{opacity:0;transform:translateY(52px) rotate(2.6deg)}"
    "55%{opacity:1;transform:translateY(-7px) rotate(-.7deg)}"
    "75%{transform:translateY(3px) rotate(.3deg)}100%{opacity:1;transform:translateY(0) rotate(0deg)}}"
    ".swing{transform-box:fill-box;transform-origin:50% 100%;animation:swing 1s cubic-bezier(.2,.7,.3,1) both}"
    "@keyframes fadein{from{opacity:0}to{opacity:1}}"
    ".fade{animation:fadein .45s ease both}"
    "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.2}}"
    ".pulse{animation:pulse 2.2s ease-in-out 3s infinite}"
    "@keyframes nudge{from{transform:translateX(0)}to{transform:translateX(5px)}}"
    ".nudge{animation:nudge .9s ease-in-out 3.4s infinite alternate}"
    "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"
)


def style(extra: str = "") -> str:
    css = font_css() + ("" if STATIC else ANIM_CSS) + extra
    return f"<style>{css}</style>"


def svg_open(w: int, h: int, extra_style: str = "") -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img">{style(extra_style)}')


def delay(cls: str, seconds: float, extra: str = "") -> str:
    """class + animation-delay attributes. `extra` is a non-animation class
    (e.g. a font class) that must survive in STATIC mode too."""
    if STATIC:
        return f' class="{extra}"' if extra else ""
    classes = f"{cls} {extra}".strip()
    return f' class="{classes}" style="animation-delay:{seconds:.2f}s"'


def count_up(value: int, suffix: str, x: float, y: float, size: int,
             fill: str, start: float) -> str:
    """SMIL count-up: eased steps, final frame freezes. STATIC: plain text."""
    attrs = f'x="{x}" y="{y}" font-size="{size}" fill="{fill}"'
    if STATIC:
        return f'<text {attrs} class="serif">{value}{esc(suffix)}</text>'
    frames, seen = [], []
    n = 16
    for i in range(1, n + 1):
        p = i / n
        v = round(value * (1 - (1 - p) ** 3))
        if not seen or seen[-1] != v:
            seen.append(v)
    step = 1.0 / len(seen)
    for i, v in enumerate(seen):
        t = start + i * step
        if i == len(seen) - 1:
            s = f'<set attributeName="visibility" to="visible" begin="{t:.2f}s" fill="freeze"/>'
        else:
            s = (f'<set attributeName="visibility" to="visible" begin="{t:.2f}s" '
                 f'dur="{step:.2f}s" fill="remove"/>')
        frames.append(f'<text {attrs} class="serif" visibility="hidden">{v}{esc(suffix)}{s}</text>')
    return "".join(frames)


# ---------------------------------------------------------------- data ----
def load_data():
    with open(os.path.join(ROOT, "data", "contributions.json")) as f:
        return json.load(f)


def stats(days: dict):
    total = sum(days.values())
    active = sum(1 for v in days.values() if v > 0)
    items = sorted(days.items())
    best = cur = 0
    for _d, v in items:
        cur = cur + 1 if v > 0 else 0
        best = max(best, cur)
    busiest_d, busiest_c = max(days.items(), key=lambda kv: kv[1])
    return total, active, best, busiest_d, busiest_c


# ---------------------------------------------------------------- hero ----
def hero(data) -> str:
    with open(os.path.join(ROOT, "assets", "portrait.txt")) as f:
        rows = [ln for ln in f.read().split("\n") if ln.strip()]
    shine_anim = "" if STATIC else (
        '<animateTransform attributeName="gradientTransform" type="translate" '
        'values="-1.1 0;1.1 0" begin="1.4s" dur="5.5s" repeatCount="indefinite"/>')
    shine_pos = ' gradientTransform="translate(-1.1 0)"' if STATIC else ""
    out = [svg_open(880, 330)]
    out.append(f'<rect width="880" height="330" rx="18" fill="{PAPER}"/>')
    out.append(f'<rect x="0.5" y="0.5" width="879" height="329" rx="18" fill="none" stroke="{LINE}"/>')
    # portrait, prints in row by row
    for i, row in enumerate(rows):
        out.append(
            f'<text x="586" y="{52 + i * 12.4:.0f}" font-size="10.5" fill="#2A2F38" '
            f'xml:space="preserve"{delay("fade", 0.25 + i * 0.05, "mono")}>{esc(row)}</text>')
    out.append(
        f'<text x="48" y="54" font-size="13" font-weight="700" letter-spacing="3" '
        f'fill="{MUTED}"{delay("rise", 0.05, "sans")}>PAMPORE · KASHMIR · IST (UTC +5:30)</text>')
    out.append(
        f'<defs><linearGradient id="shine" x1="0" y1="0" x2="1" y2="0"{shine_pos}>'
        f'<stop offset="0" stop-color="{INK}"/><stop offset="0.42" stop-color="{INK}"/>'
        f'<stop offset="0.5" stop-color="{BLUE}"/><stop offset="0.58" stop-color="{INK}"/>'
        f'<stop offset="1" stop-color="{INK}"/>{shine_anim}</linearGradient></defs>')
    out.append(
        f'<text x="46" y="132" font-size="67" fill="{INK}"{delay("rise", 0.15, "serif")}>'
        f'Aazim <tspan fill="url(#shine)">Ameen</tspan></text>')
    out.append(
        f'<text x="48" y="180" font-size="20" fill="{BODY}"{delay("rise", 0.4, "sans")}>'
        f'I build Android &amp; AI tools, photograph</text>')
    out.append(
        f'<text x="48" y="208" font-size="20" fill="{BODY}"{delay("rise", 0.52, "sans")}>'
        f'Kashmir\u2019s heritage, and archive its</text>')
    out.append(
        f'<text x="48" y="236" font-size="20" fill="{BODY}"{delay("rise", 0.64, "sans")}>'
        f'endangered languages.</text>')
    out.append(f'<circle cx="56" cy="278" r="5" fill="#2F9E44"{delay("pulse", 0)}/>')
    out.append(
        f'<text x="72" y="284" font-size="15.5" fill="{MUTED}"{delay("rise", 0.8, "sans")}>'
        f'DYOD student at IUST, Awantipora — building in public</text>')
    out.append("</svg>")
    return "".join(out)


# ------------------------------------------------------------- heatmap ----
def heat_level(c: int) -> int:
    if c == 0:
        return 0
    if c <= 2:
        return 1
    if c <= 5:
        return 2
    if c <= 11:
        return 3
    return 4


def heatmap(data) -> str:
    days = data["days"]
    last = max(days)
    last_d = date.fromisoformat(last)
    first_d = last_d - timedelta(days=364)
    first_d -= timedelta(days=(first_d.weekday() + 1) % 7)  # back to Sunday
    out = [svg_open(880, 196)]
    out.append(f'<rect width="880" height="196" rx="18" fill="{CARD}"/>')
    out.append(f'<rect x="0.5" y="0.5" width="879" height="195" rx="18" fill="none" stroke="{LINE}"/>')
    out.append(
        f'<text x="48" y="44" font-size="15" font-weight="700" letter-spacing="2.5" '
        f'fill="{INK}"{delay("rise", 1.15, "sans")}>THE YEAR IN BLUE</text>')
    out.append(
        f'<text x="832" y="44" text-anchor="end" font-size="13" fill="{MUTED}"'
        f'{delay("fade", 1.3, "sans")}>both accounts combined</text>')
    x0, y0, pitch, cell = 48, 64, 14.5, 11
    d = first_d
    col = 0
    last_month = None
    while d <= last_d:
        if d.month != last_month and d.day <= 7:
            out.append(
                f'<text x="{x0 + col * pitch:.0f}" y="58" font-size="11" fill="{MUTED}" '
                f'class="sans">{d.strftime("%b")}</text>')
            last_month = d.month
        for row in range(7):
            cur = d + timedelta(days=row)
            if cur > last_d:
                continue
            c = days.get(cur.isoformat(), 0)
            out.append(
                f'<rect x="{x0 + col * pitch:.1f}" y="{y0 + row * pitch:.1f}" width="{cell}" '
                f'height="{cell}" rx="2.5" fill="{HEAT[heat_level(c)]}"'
                f'{delay("pop", 1.2 + col * 0.045 + row * 0.008)}/>')
        d += timedelta(days=7)
        col += 1
    out.append("</svg>")
    return "".join(out)


# ------------------------------------------------------------- activity ---
def activity(data) -> str:
    days = data["days"]
    total, active, streak, busiest_d, busiest_c = stats(days)
    by_month = {}
    for dstr, c in days.items():
        by_month[dstr[:7]] = by_month.get(dstr[:7], 0) + c
    last_d = date.fromisoformat(max(days))
    months = []
    y, m = last_d.year, last_d.month
    for _ in range(12):
        months.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    months.reverse()
    vals = [(f"{yy}-{mm:02d}", by_month.get(f"{yy}-{mm:02d}", 0)) for yy, mm in months]
    labels = [date(yy, mm, 1).strftime("%b") for yy, mm in months]
    vmax = max(v for _k, v in vals) or 1
    base, top_h = 236, 148
    plot_x, plot_w = 64, 768
    slot = plot_w / 12
    bar_w = 38
    out = [svg_open(880, 322)]
    out.append(f'<rect width="880" height="322" rx="18" fill="{CARD}"/>')
    out.append(f'<rect x="0.5" y="0.5" width="879" height="321" rx="18" fill="none" stroke="{LINE}"/>')
    out.append(
        f'<text x="48" y="52" font-size="15" font-weight="700" letter-spacing="2.5" '
        f'fill="{INK}"{delay("rise", 1.85, "sans")}>CONTRIBUTIONS — LAST 12 MONTHS</text>')
    out.append(f'<line x1="{plot_x - 16}" y1="{base}" x2="{plot_x + plot_w + 16}" y2="{base}" stroke="{LINE}"/>')
    for i, ((_k, v), lab) in enumerate(zip(vals, labels)):
        h = max(3, round(v / vmax * top_h)) if v else 3
        x = plot_x + i * slot + (slot - bar_w) / 2
        is_best = v == vmax and v > 0
        fill = BLUE if is_best else "#D3DCEC"
        out.append(
            f'<rect x="{x:.0f}" y="{base - h}" width="{bar_w}" height="{h}" rx="6" '
            f'fill="{fill}"{delay("grow", 2.0 + i * 0.07)}/>')
        if v:
            out.append(
                f'<text x="{x + bar_w / 2:.0f}" y="{base - h - 10}" text-anchor="middle" '
                f'font-size="14" font-weight="700" fill="{BLUE if is_best else MUTED}"'
                f'{delay("fade", 2.55 + i * 0.07, "sans")}>{v}</text>')
        out.append(
            f'<text x="{x + bar_w / 2:.0f}" y="{base + 24}" text-anchor="middle" '
            f'font-size="12.5" fill="{MUTED}" class="sans">{lab}</text>')
    bd = date.fromisoformat(busiest_d).strftime("%d %b %Y")
    out.append(
        f'<text x="48" y="298" font-size="15" fill="{BODY}"{delay("rise", 2.9, "sans")}>'
        f'<tspan font-weight="700" fill="{INK}">{total}</tspan> contributions in the last year · '
        f'<tspan font-weight="700" fill="{INK}">{active}</tspan> active days · '
        f'best streak <tspan font-weight="700" fill="{INK}">{streak} days</tspan> · '
        f'busiest {bd} (<tspan font-weight="700" fill="{INK}">{busiest_c}</tspan>)</text>')
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- tiles ---
TILES = [
    dict(key="build", label="BUILD", accent=BLUE, suffix="",
         caption="public repositories",
         desc=["Android apps, AI tools and", "web projects — IUST App,"],
         desc2="Koshur Offline, SabConvert.",
         foot="github.com/aazimameen1122"),
    dict(key="lens", label="LENS", accent=RED, suffix="+",
         caption="years behind the camera",
         desc=["Photographing Kashmir's old", "city, shrines, orchards and"],
         desc2="vanishing heritage.",
         foot="@aazimameen1 on Instagram"),
    dict(key="language", label="LANGUAGE", accent=GOLD, suffix="+",
         caption="Burushaski words archived",
         desc=["Plus published Kashmiri", "speech-to-text and English →"],
         desc2="Kashmiri translation models.",
         foot="Burushaski Digital Archive"),
]


def tile(t, value, idx) -> str:
    start = 3.3 + idx * 0.18
    a = t["accent"]
    out = [svg_open(283, 308)]
    out.append(f'<g{delay("swing", 3.15 + idx * 0.18)}>')
    out.append(f'<rect width="283" height="308" rx="18" fill="{CARD}"/>')
    out.append(f'<rect x="0.5" y="0.5" width="282" height="307" rx="18" fill="none" stroke="{LINE}"/>')
    out.append(f'<rect width="283" height="9" rx="4.5" fill="{a}"/>')
    out.append(
        f'<text x="26" y="52" font-size="14" font-weight="700" letter-spacing="2.5" '
        f'fill="{a}" class="sans">{t["label"]}</text>')
    out.append(
        f'<text x="238" y="54" font-size="19" font-weight="700" fill="{a}"'
        f'{delay("nudge", 0, "sans")}>→</text>')
    out.append(count_up(value, t["suffix"], 24, 152, 82, INK, start))
    out.append(
        f'<text x="26" y="188" font-size="16" font-weight="700" fill="{INK}" class="sans">{t["caption"]}</text>')
    out.append(f'<text x="26" y="218" font-size="14.5" fill="{BODY}" class="sans">{t["desc"][0]}</text>')
    out.append(f'<text x="26" y="239" font-size="14.5" fill="{BODY}" class="sans">{t["desc"][1]}</text>')
    out.append(f'<text x="26" y="260" font-size="14.5" fill="{BODY}" class="sans">{t["desc2"]}</text>')
    out.append(f'<rect x="26" y="278" width="44" height="4" rx="2" fill="{a}"{delay("growx", start + 0.35)}/>')
    out.append(
        f'<text x="80" y="285" font-size="12.5" font-weight="700" fill="{a}" class="sans">{t["foot"]}</text>')
    out.append("</g></svg>")
    return "".join(out)


# ---------------------------------------------------------------- repos ---
REPOS = [
    dict(key="repo-iust", name="IUST Student App", lang="Kotlin", langc="#7F52FF",
         tag="ANDROID", accent=BLUE,
         desc=["The student app for IUST Awantipora —", "notices, results, timetable and AMS."]),
    dict(key="repo-koshur", name="Koshur Tools", lang="HTML", langc="#E34C26",
         tag="AI · LANGUAGE", accent=GOLD,
         desc=["Kashmiri editor with speech-to-text and", "English → Kashmiri translation."]),
    dict(key="repo-burushaski", name="BurushaskiRAG", lang="Python", langc="#3572A5",
         tag="RAG", accent=BLUE,
         desc=["Ask the Burushaski Archive in plain", "English — answers from the corpus only."]),
    dict(key="repo-chinar", name="Chinar Clash", lang="JavaScript", langc="#D9B916",
         tag="GAME", accent=RED,
         desc=["A browser fighting game of Kashmiri", "political satire — the great kursi fight."]),
]


def repo_card(r, idx) -> str:
    d = 3.95 + idx * 0.13
    out = [svg_open(431, 176)]
    out.append(f'<g{delay("rise", d)}>')
    out.append(f'<rect width="431" height="176" rx="18" fill="{CARD}"/>')
    out.append(f'<rect x="0.5" y="0.5" width="430" height="175" rx="18" fill="none" stroke="{LINE}"/>')
    out.append(f'<text x="26" y="50" font-size="25" fill="{INK}" class="serif">{r["name"]}</text>')
    out.append(
        f'<text x="382" y="50" font-size="19" font-weight="700" fill="{r["accent"]}"'
        f'{delay("nudge", 0, "sans")}>→</text>')
    out.append(f'<text x="26" y="84" font-size="14.5" fill="{BODY}" class="sans">{r["desc"][0]}</text>')
    out.append(f'<text x="26" y="106" font-size="14.5" fill="{BODY}" class="sans">{r["desc"][1]}</text>')
    out.append(f'<circle cx="32" cy="140" r="5.5" fill="{r["langc"]}"/>')
    out.append(f'<text x="46" y="145" font-size="13" fill="{MUTED}" class="sans">{r["lang"]}</text>')
    out.append(
        f'<text x="405" y="145" text-anchor="end" font-size="12" font-weight="700" '
        f'letter-spacing="1.5" fill="{r["accent"]}" class="sans">{r["tag"]}</text>')
    out.append("</g></svg>")
    return "".join(out)


def main():
    data = load_data()
    cards = {
        "hero.svg": hero(data),
        "heatmap.svg": heatmap(data),
        "activity.svg": activity(data),
    }
    tile_values = {"build": int(data.get("public_repos_total") or 31), "lens": 6, "language": 63}
    for i, t in enumerate(TILES):
        cards[f'{t["key"]}.svg'] = tile(t, tile_values[t["key"]], i)
    for i, r in enumerate(REPOS):
        cards[f'{r["key"]}.svg'] = repo_card(r, i)
    outdir = os.path.join(ROOT, "cards")
    os.makedirs(outdir, exist_ok=True)
    for name, svg in cards.items():
        with open(os.path.join(outdir, name), "w") as f:
            f.write(svg)
        print(f"cards/{name}: {len(svg) // 1024} KB")


if __name__ == "__main__":
    main()
