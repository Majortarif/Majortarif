#!/usr/bin/env python3
"""Generate the animated SVGs used by the profile README.

    python tools/build_assets.py <path-to-portfolio>

The look follows the 2026 portfolio (css/base.css): near-black surfaces, a
cyan/blue accent, mono labels and an italic serif for emphasis. The three
project screenshots are read from the portfolio folder and embedded.

Every SVG is self-contained (no external fonts, scripts or images), so
GitHub's image proxy renders it as-is. CSS animations stop under
prefers-reduced-motion; SMIL-only decorations (typing, pulses, shimmer) are
hidden there and a static version is shown instead.
"""
import base64
import html
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
PORTFOLIO = Path(sys.argv[1]) if len(sys.argv) > 1 else None

# ---------------------------------------------------------------- tokens
D = dict(
    bg="#04060b", elev="#080c16", elev2="#0c1220",
    text="#e8eef8", text2="#a7b4c8", text3="#7f8ca2",
    acc="#3ee0ff", acc2="#4f8bff", ok="#4ade80", ink="#03141c",
    line="rgba(148,170,210,0.14)", line2="rgba(148,170,210,0.26)",
)
# Section headings sit on the page itself, so they also get a light variant.
L = dict(text="#0b1220", text2="#3f4c63", text3="#5b6880", acc="#0e7490", acc2="#1d4ed8")

SANS = "ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'Cascadia Mono','Segoe UI Mono',Menlo,Consolas,'Liberation Mono',monospace"
SERIF = "'Instrument Serif',Georgia,'Times New Roman',serif"

BASE_CSS = (
    ".sans{font-family:" + SANS + "}"
    ".mono{font-family:" + MONO + "}"
    ".serif{font-family:" + SERIF + ";font-style:italic}"
    ".static{display:none}"
)
REDUCED = "@media (prefers-reduced-motion:reduce){*{animation:none!important}.smil{display:none}.static{display:inline}}"
EASE = "cubic-bezier(.16,1,.3,1)"


def esc(s):
    return html.escape(s, quote=True)


def svg(w, h, label, body, css="", defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">'
        f"<title>{esc(label)}</title><style>{BASE_CSS}{css}{REDUCED}</style>"
        f"<defs>{defs}</defs>{body}</svg>\n"
    )


def write(name, content):
    (OUT / name).write_text(content, encoding="utf-8")
    print(f"  {name:34} {len(content.encode()) / 1024:6.1f} KB")


def mono(x, y, s, fs, fill, cls="", extra="", cw=0.6):
    """Monospace text with a fixed advance, so layout does not depend on the viewer's font."""
    return (
        f'<text class="mono {cls}" x="{x:.1f}" y="{y:.1f}" font-size="{fs}" fill="{fill}" '
        f'textLength="{len(s) * fs * cw:.1f}" lengthAdjust="spacing" xml:space="preserve" {extra}>{esc(s)}</text>'
    )


def mono_w(s, fs, cw=0.6):
    return len(s) * fs * cw


def wrap(text, width):
    lines, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > width:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}" if cur else word
    if cur:
        lines.append(cur)
    return lines


def card(w, h, rx=24, fill=None):
    return (
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{rx}" '
        f'fill="{fill or D["elev"]}" stroke="{D["line"]}"/>'
    )


def chip_layout(items, x0, y0, maxw, fs=13, h=30, gap=8, rowgap=10, pad=13):
    out, x, y = [], x0, y0
    for t in items:
        w = mono_w(t, fs) + 2 * pad
        if x > x0 and x + w > x0 + maxw:
            x, y = x0, y + h + rowgap
        out.append((x, y, w, t))
        x += w + gap
    return out, y + h


def chips_svg(layout, fs=13, h=30, pad=13, start=0, step=0.12):
    """Pill chips; a highlight runs across them in order (see chip_css)."""
    parts = []
    for i, (x, y, w, t) in enumerate(layout):
        parts.append(
            f'<g class="chip" style="animation-delay:{start + i * step:.2f}s">'
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="{h / 2}"/>'
            f'{mono(x + pad, y + h / 2 + fs * 0.36, t, fs, D["text2"])}</g>'
        )
    return "".join(parts)


def chip_css(cycle):
    c = f"{cycle:.2f}s"
    return (
        ".chip rect{fill:rgba(148,176,220,.04);stroke:rgba(148,170,210,.2);"
        f"animation:litr {c} ease-in-out infinite;animation-delay:inherit}}"
        f".chip text{{animation:litt {c} ease-in-out infinite;animation-delay:inherit}}"
        "@keyframes litr{0%,9%,100%{stroke:rgba(148,170,210,.2);fill:rgba(148,176,220,.04)}"
        "3%{stroke:rgba(62,224,255,.9);fill:rgba(62,224,255,.14)}}"
        "@keyframes litt{0%,9%,100%{fill:" + D["text2"] + "}3%{fill:#ffffff}}"
    )


# ---------------------------------------------------------------- icons (Lucide-style, ISC)
ICONS = {
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    "mail": '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    "linkedin": '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/><rect width="4" height="12" x="2" y="9"/><circle cx="4" cy="4" r="2"/>',
    "arrow": '<path d="M7 17 17 7"/><path d="M7 7h10v10"/>',
}


def icon(name, x, y, size, color, sw=2):
    s = size / 24
    return (
        f'<g transform="translate({x} {y}) scale({s:.3f})" fill="none" stroke="{color}" '
        f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</g>'
    )


# ================================================================ hero
def hero():
    W, H = 1200, 460
    rnd = random.Random(2026)
    css = f"""
.rise{{animation:rise 1.1s {EASE} both}}
.d1{{animation-delay:.1s}}.d2{{animation-delay:.3s}}.d3{{animation-delay:.55s}}.d4{{animation-delay:.8s}}.d5{{animation-delay:1s}}.d6{{animation-delay:1.3s}}
@keyframes rise{{from{{opacity:0;transform:translateY(26px)}}to{{opacity:1;transform:none}}}}
.fade{{animation:fade 2s ease both .2s}}@keyframes fade{{from{{opacity:0}}}}
.drift{{animation:drift 140s linear infinite}}@keyframes drift{{to{{transform:translateX({W}px)}}}}
.tw{{animation:tw 4s ease-in-out infinite alternate}}@keyframes tw{{from{{opacity:.06}}to{{opacity:.6}}}}
.breathe{{animation:breathe 9s ease-in-out infinite alternate;transform-box:fill-box;transform-origin:center}}
@keyframes breathe{{from{{opacity:.5;transform:scale(1)}}to{{opacity:1;transform:scale(1.1)}}}}
.float{{animation:float 11s ease-in-out infinite alternate}}
@keyframes float{{from{{transform:translate(-4px,-7px)}}to{{transform:translate(4px,7px)}}}}
.flow{{stroke-dasharray:12 100;animation:flow 3.4s linear infinite}}
@keyframes flow{{from{{stroke-dashoffset:112}}to{{stroke-dashoffset:0}}}}
.ping{{animation:ping 2.4s cubic-bezier(0,0,.2,1) infinite;transform-box:fill-box;transform-origin:center}}
@keyframes ping{{0%{{transform:scale(1);opacity:.75}}80%,100%{{transform:scale(3.2);opacity:0}}}}
.node{{animation:node 3.6s ease-in-out infinite;transform-box:fill-box;transform-origin:center}}
@keyframes node{{0%,100%{{opacity:.7;transform:scale(1)}}50%{{opacity:1;transform:scale(1.45)}}}}
.blink{{animation:blink 1.05s steps(1) infinite}}@keyframes blink{{50%{{opacity:0}}}}
"""
    defs = f"""
<clipPath id="frame"><rect width="{W}" height="{H}" rx="22"/></clipPath>
<pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse"><path d="M48 0H0V48" fill="none" stroke="#94aad2" stroke-opacity=".09"/></pattern>
<radialGradient id="gridFade" cx=".74" cy=".42" r=".62"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
<mask id="gridMask"><rect width="{W}" height="{H}" fill="url(#gridFade)"/></mask>
<radialGradient id="glowA"><stop offset="0" stop-color="{D['acc']}" stop-opacity=".2"/><stop offset="1" stop-color="{D['acc']}" stop-opacity="0"/></radialGradient>
<radialGradient id="glowB"><stop offset="0" stop-color="{D['acc2']}" stop-opacity=".17"/><stop offset="1" stop-color="{D['acc2']}" stop-opacity="0"/></radialGradient>
<radialGradient id="nodeGlow"><stop offset="0" stop-color="{D['acc']}" stop-opacity=".5"/><stop offset="1" stop-color="{D['acc']}" stop-opacity="0"/></radialGradient>
<linearGradient id="ink" x1="60" y1="0" x2="390" y2="0" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{D['acc']}"/><stop offset="1" stop-color="{D['acc2']}"/></linearGradient>
<linearGradient id="shine" x1="0" y1="0" x2="150" y2="0" gradientUnits="userSpaceOnUse" gradientTransform="translate(-300 0)">
  <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".85"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
  <animateTransform attributeName="gradientTransform" type="translate" values="-220 0;520 0;520 0" keyTimes="0;.38;1" dur="6.5s" begin="1.8s" repeatCount="indefinite"/>
</linearGradient>
<filter id="soft" x="-30%" y="-60%" width="160%" height="220%"><feGaussianBlur stdDeviation="16"/></filter>
"""
    b = [f'<g clip-path="url(#frame)">', f'<rect width="{W}" height="{H}" fill="{D["bg"]}"/>']
    b.append(f'<rect width="{W}" height="{H}" fill="url(#grid)" mask="url(#gridMask)"/>')
    b.append('<ellipse class="breathe" cx="930" cy="140" rx="440" ry="300" fill="url(#glowA)"/>')
    b.append('<ellipse class="breathe" style="animation-delay:-4.5s" cx="170" cy="470" rx="440" ry="250" fill="url(#glowB)"/>')

    # ultrasonic sonar behind the network: rings ping outwards while a radar beam turns
    sx, sy, R = 955, 215, 300
    css += f"""
.sonar{{animation:sonar 4.8s cubic-bezier(.2,.6,.3,1) infinite;transform-box:fill-box;transform-origin:center}}
@keyframes sonar{{0%{{transform:scale(.1);opacity:0}}10%{{opacity:.6}}100%{{transform:scale(1);opacity:0}}}}
.beam{{animation:beam 7s linear infinite;transform-origin:{sx}px {sy}px}}@keyframes beam{{to{{transform:rotate(360deg)}}}}
.scan{{animation:scan 7.5s linear infinite}}@keyframes scan{{from{{transform:translateY(-60px)}}to{{transform:translateY({H + 60}px)}}}}
"""
    a = math.radians(-48)
    ex, ey = sx + R * math.cos(a), sy + R * math.sin(a)
    defs += (
        f'<linearGradient id="beamG" gradientUnits="userSpaceOnUse" x1="{sx + 160}" y1="{sy}" '
        f'x2="{sx + 160 * math.cos(a):.0f}" y2="{sy + 160 * math.sin(a):.0f}">'
        f'<stop offset="0" stop-color="{D["acc"]}" stop-opacity=".26"/><stop offset="1" stop-color="{D["acc"]}" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="scanG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{D["acc"]}" stop-opacity="0"/>'
        f'<stop offset=".85" stop-color="{D["acc"]}" stop-opacity=".07"/><stop offset="1" stop-color="{D["acc"]}" stop-opacity=".22"/></linearGradient>'
    )
    sonar = [f'<g opacity=".9">']
    for r in (75, 150, 225, 300):
        sonar.append(f'<circle cx="{sx}" cy="{sy}" r="{r}" fill="none" stroke="#94aad2" stroke-opacity=".08" stroke-dasharray="2 6"/>')
    sonar.append(f'<path d="M{sx - R} {sy}H{sx + R}M{sx} {sy - R}V{sy + R}" stroke="#94aad2" stroke-opacity=".07"/>')
    for k in range(3):
        sonar.append(f'<circle class="sonar" style="animation-delay:{-k * 1.6:.1f}s" cx="{sx}" cy="{sy}" r="{R}" fill="none" stroke="{D["acc"]}" stroke-width="1.4"/>')
    sonar.append(
        f'<g class="beam"><path d="M{sx} {sy}L{sx + R} {sy}A{R} {R} 0 0 0 {ex:.0f} {ey:.0f}Z" fill="url(#beamG)"/>'
        f'<path d="M{sx} {sy}H{sx + R}" stroke="{D["acc"]}" stroke-opacity=".55" stroke-width="1.5"/></g>'
    )
    sonar.append(f'<circle cx="{sx}" cy="{sy}" r="4" fill="{D["acc"]}"/><circle class="ping" cx="{sx}" cy="{sy}" r="4" fill="{D["acc"]}"/></g>')
    b.append("".join(sonar))
    b.append(f'<g class="scan"><rect y="0" width="{W}" height="60" fill="url(#scanG)"/><path d="M0 60H{W}" stroke="{D["acc"]}" stroke-opacity=".3"/></g>')

    # drifting dust; two copies side by side make the loop seamless
    dust = []
    for _ in range(70):
        x, y = rnd.uniform(0, W), rnd.uniform(8, H - 8)
        r = rnd.choice([0.6, 0.8, 1.0, 1.2, 1.5, 1.8])
        dust.append(
            f'<circle class="tw" cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#a9dcff" opacity=".35" '
            f'style="animation-duration:{rnd.uniform(2.5, 6):.1f}s;animation-delay:{-rnd.uniform(0, 6):.1f}s"/>'
        )
    dust = "".join(dust)
    b.append(f'<g class="drift"><g>{dust}</g><g transform="translate(-{W} 0)">{dust}</g></g>')

    # the eight model inputs as a softly linked network
    labelled = [
        ("PM2.5", 790, 104), ("PM10", 948, 76), ("CO", 1098, 120), ("CO₂", 872, 200),
        ("NO₂", 1030, 222), ("O₃", 1140, 292), ("Temp", 812, 304), ("Humidity", 970, 334),
    ]
    small = []
    while len(small) < 14:
        x, y = rnd.uniform(730, 1170), rnd.uniform(60, 380)
        if all(math.dist((x, y), (lx, ly)) > 58 for _, lx, ly in labelled) and all(
            math.dist((x, y), s) > 50 for s in small
        ):
            small.append((x, y))
    pts = [(lx, ly) for _, lx, ly in labelled] + small
    net = []
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            d = math.dist(pts[i], pts[j])
            if d < 128 or (i < 8 and j < 8 and d < 180):
                (x1, y1), (x2, y2) = pts[i], pts[j]
                net.append(
                    f'<path d="M{x1:.0f} {y1:.0f}L{x2:.0f} {y2:.0f}" stroke="#94aad2" stroke-opacity=".17"/>'
                    f'<path class="flow" pathLength="100" d="M{x1:.0f} {y1:.0f}L{x2:.0f} {y2:.0f}" '
                    f'stroke="{D["acc"]}" stroke-opacity=".75" stroke-width="1.4" stroke-linecap="round" '
                    f'style="animation-duration:{rnd.uniform(2.6, 5):.1f}s;animation-delay:{-rnd.uniform(0, 5):.1f}s"/>'
                )
    for x, y in small:
        net.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="1.8" fill="#a9dcff" opacity=".55"/>')
    for k, (name, x, y) in enumerate(labelled):
        net.append(
            f'<circle cx="{x}" cy="{y}" r="16" fill="url(#nodeGlow)"/>'
            f'<circle class="node" style="animation-delay:{-k * 0.45:.2f}s" cx="{x}" cy="{y}" r="3.6" fill="{D["acc"]}"/>'
            + mono(x + 10, y - 10, name, 12, D["text3"])
        )
    wander = (
        '<circle class="smil" r="70" fill="url(#nodeGlow)" opacity=".35">'
        '<animateMotion dur="22s" repeatCount="indefinite" '
        'path="M880 160C980 80 1120 120 1110 230S960 360 860 300 780 220 880 160Z"/></circle>'
    )
    b.append(f'<g class="fade"><g class="float">{wander}{"".join(net)}</g></g>')

    # legend, as on the portfolio hero
    b.append(
        f'<g class="rise d6">{mono(768, 414, "// background.field", 12, D["acc"])}'
        f'<text class="sans" x="768" y="436" font-size="13.5" fill="{D["text3"]}">'
        "Particles carry the 8 input features of my air-quality model.</text></g>"
    )

    # status pill
    s1, s2 = "Open to AI/ML roles", "/  Dhaka, Bangladesh"
    w1, w2 = mono_w(s1, 13), mono_w(s2, 13)
    pw = 44 + w1 + 12 + w2 + 18
    b.append(
        f'<g class="rise d1"><rect x="64" y="44" width="{pw:.0f}" height="36" rx="18" fill="{D["elev2"]}" '
        f'fill-opacity=".85" stroke="{D["line2"]}"/>'
        f'<circle class="ping" cx="88" cy="62" r="4" fill="{D["ok"]}"/><circle cx="88" cy="62" r="4" fill="{D["ok"]}"/>'
        + mono(104, 66.5, s1, 13, D["text"])
        + mono(104 + w1 + 12, 66.5, s2, 13, D["text3"])
        + "</g>"
    )

    # name
    b.append(
        f'<g class="rise d2"><text class="sans" x="58" y="196" font-size="106" font-weight="600" '
        f'letter-spacing="-3" fill="{D["text"]}">Tariful</text></g>'
    )
    hq = 'x="62" y="298" font-size="118"'
    b.append(
        f'<g class="rise d3"><text class="serif" {hq} fill="{D["acc"]}" opacity=".32" filter="url(#soft)">Hoque</text>'
        f'<text class="serif" {hq} fill="url(#ink)">Hoque</text>'
        f'<text class="serif smil" {hq} fill="url(#shine)">Hoque</text></g>'
    )

    # role line
    roles = ["Computer Science", "Machine Learning", "Explainable AI", "Data"]
    spans = []
    for k, r in enumerate(roles):
        if k:
            spans.append(f'<tspan dx="11" fill="{D["acc"]}">·</tspan>')
        spans.append(f'<tspan dx="{11 if k else 0}">{esc(r)}</tspan>')
    b.append(
        f'<g class="rise d4"><text class="sans" x="64" y="354" font-size="21" fill="{D["text2"]}">'
        f'{"".join(spans)}</text></g>'
    )

    # typing line (SMIL, so it runs in GitHub's <img>)
    phrases = [
        "I build ML models that can explain their decisions",
        "Explainable AI · data analysis · UI/UX design",
        "Recently shipped: a grounded RAG service",
        "From raw data to interpretable predictions",
    ]
    fs, cw, x0, y = 17, 10.2, 92, 405
    t_type, t_del, hold, gap = 0.055, 0.022, 2.6, 0.5
    T = sum(len(p) * (t_type + t_del) + hold + gap for p in phrases)
    cursor_events = [(0.0, 0)]
    typed = []
    t = 0.0
    for i, p in enumerate(phrases):
        n = len(p)
        ev = [(t + k * t_type, k) for k in range(1, n + 1)]
        t_end = t + n * t_type + hold
        ev += [(t_end + (n - k) * t_del, k) for k in range(n - 1, -1, -1)]
        cursor_events += ev
        ev = [(0.0, 0)] + ev
        times = ";".join(f"{e[0] / T:.4f}" for e in ev)
        vals = ";".join(f"{e[1] * cw:.1f}" for e in ev)
        typed.append(
            f'<clipPath id="type{i}"><rect x="{x0}" y="{y - 20}" height="28" width="0">'
            f'<animate attributeName="width" calcMode="discrete" dur="{T:.2f}s" repeatCount="indefinite" '
            f'keyTimes="{times}" values="{vals}"/></rect></clipPath>'
            f'<text class="mono" x="{x0}" y="{y}" font-size="{fs}" fill="{D["text"]}" '
            f'textLength="{n * cw:.1f}" lengthAdjust="spacingAndGlyphs" clip-path="url(#type{i})">{esc(p)}</text>'
        )
        t = t_end + n * t_del + gap
    ctimes = ";".join(f"{e[0] / T:.4f}" for e in cursor_events)
    cvals = ";".join(f"{x0 + 2 + e[1] * cw:.1f}" for e in cursor_events)
    b.append(
        f'<g class="rise d5">{mono(64, y, ">", fs, D["acc"])}'
        f'<g class="smil">{"".join(typed)}'
        f'<rect class="blink" x="{x0 + 2}" y="{y - 15}" width="9" height="19" rx="1.5" fill="{D["acc"]}">'
        f'<animate attributeName="x" calcMode="discrete" dur="{T:.2f}s" repeatCount="indefinite" '
        f'keyTimes="{ctimes}" values="{cvals}"/></rect></g>'
        f'<g class="static"><text class="mono" x="{x0}" y="{y}" font-size="{fs}" fill="{D["text"]}" '
        f'textLength="{len(phrases[0]) * cw:.1f}" lengthAdjust="spacingAndGlyphs">{esc(phrases[0])}</text></g></g>'
    )

    b.append("</g>")
    b.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" fill="none" stroke="{D["line2"]}"/>')
    label = (
        "Tariful Hoque. Computer Science graduate working on machine learning, Explainable AI and data. "
        "Open to AI/ML roles, Dhaka, Bangladesh."
    )
    write("hero.svg", svg(W, H, label, "".join(b), css, defs))


# ================================================================ section heads
SCRAMBLE = "!<>-_/[]{}=+*^?#ABCDEFGHJKLMNPQRSTUVWXYZ0123456789"


def heading(slug, index, label, lines, theme):
    """Eyebrow (index, drawn rule, scrambling label) plus a title; emphasis in italic serif."""
    P = D if theme == "dark" else {**D, **L}
    rnd = random.Random(slug)
    W = 1200
    H = 132 + 62 * (len(lines) - 1)
    cycle, frame = 9.0, 0.055
    label_u = label.upper()
    frames = 8
    css = [
        f".rise{{animation:rise 1s {EASE} both .15s}}",
        "@keyframes rise{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}",
        f".rule{{stroke-dasharray:64;animation:draw {cycle}s {EASE} infinite}}",
        "@keyframes draw{0%{stroke-dashoffset:64}9%,100%{stroke-dashoffset:0}}",
        ".fr{opacity:0}",
    ]
    end = frames * frame / cycle * 100
    css.append(f".fin{{animation:fin {cycle}s steps(1) infinite}}@keyframes fin{{0%{{opacity:0}}{end:.2f}%,100%{{opacity:1}}}}")
    b = []
    lx = 118
    b.append(mono(0, 34, index, 14, P["acc"]))
    b.append(f'<path class="rule" d="M38 29.5H102" stroke="{P["acc"]}" stroke-opacity=".7" stroke-width="1.5"/>')
    for k in range(frames):
        reveal = int(len(label_u) * k / frames)
        s = "".join(
            ch if (i < reveal or ch == " ") else rnd.choice(SCRAMBLE) for i, ch in enumerate(label_u)
        )
        a, z = k * frame / cycle * 100, (k + 1) * frame / cycle * 100
        css.append(
            f".f{k}{{animation:f{k} {cycle}s steps(1) infinite}}"
            f"@keyframes f{k}{{0%{{opacity:0}}{a:.2f}%{{opacity:1}}{z:.2f}%,100%{{opacity:0}}}}"
        )
        b.append(mono(lx, 34, s, 14, P["acc"], cls=f"fr f{k}", cw=0.78))
    b.append(mono(lx, 34, label_u, 14, P["text3"], cls="fin", cw=0.78))

    grad = f'<linearGradient id="em" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{P["acc"]}"/><stop offset="1" stop-color="{P["acc2"]}"/></linearGradient>'
    for n, parts in enumerate(lines):
        spans = []
        for text, emph in parts:
            if emph:
                spans.append(f'<tspan class="serif" font-size="58" font-weight="400" fill="url(#em)">{esc(text)}</tspan>')
            else:
                spans.append(f"<tspan>{esc(text)}</tspan>")
        b.append(
            f'<g class="rise" style="animation-delay:{0.15 + n * 0.15:.2f}s"><text class="sans" x="-2" y="{104 + n * 62}" '
            f'font-size="48" font-weight="600" letter-spacing="-1.4" fill="{P["text"]}" xml:space="preserve">'
            f'{"".join(spans)}</text></g>'
        )
    title = " ".join(t for parts in lines for t, _ in parts)
    write(f"head-{slug}-{theme}.svg", svg(W, H, f"{index} · {label}: {title}", "".join(b), "".join(css), grad))


def headings():
    heads = [
        ("about", "01", "About", [[("I care about what a model predicts, ", False), ("and why.", True)]]),
        ("featured", "02", "Featured research", [[("Predicting air quality, ", False), ("and explaining why.", True)]]),
        ("work", "03", "Selected work", [[("Things I have trained, designed ", False), ("and shipped.", True)]]),
        ("skills", "04", "Skills", [[("A toolkit backed by ", False), ("evidence.", True)]]),
        ("experience", "05", "Experience", [[("Research, product building ", False), ("and leadership.", True)]]),
        ("activity", "06", "Activity", [[("Building in public, ", False), ("one commit at a time.", True)]]),
        ("contact", "07", "Contact", [[("Let's turn data into decisions", False)], [("people can trust.", True)]]),
    ]
    for slug, idx, label, lines in heads:
        for theme in ("dark", "light"):
            heading(slug, idx, label, lines, theme)


# ================================================================ buttons
def button(name, label, ico, primary):
    fs, h = 17, 52
    tw = len(label) * fs * 0.5
    w = 22 + 22 + 12 + tw + 14 + 16 + 24
    fg = D["ink"] if primary else D["text"]
    css = (
        f".sh{{animation:sh 5.5s {EASE} infinite 1s}}"
        "@keyframes sh{0%{transform:translateX(-120px)}30%,100%{transform:translateX(" + f"{w + 60:.0f}" + "px)}}"
    )
    defs = (
        f'<clipPath id="b"><rect width="{w:.0f}" height="{h}" rx="{h / 2}"/></clipPath>'
        '<linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset=".5" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="fill" x1="0" x2="1"><stop offset="0" stop-color="{D["acc"]}"/><stop offset="1" stop-color="#5fe8ff"/></linearGradient>'
    )
    bg = (
        f'<rect width="{w:.0f}" height="{h}" rx="{h / 2}" fill="url(#fill)"/>'
        if primary
        else f'<rect x=".75" y=".75" width="{w - 1.5:.0f}" height="{h - 1.5}" rx="{(h - 1.5) / 2}" fill="{D["elev2"]}" stroke="{D["line2"]}" stroke-width="1.5"/>'
    )
    shine = (
        f'<g clip-path="url(#b)"><g class="sh"><rect x="0" y="0" width="70" height="{h}" fill="url(#g)" '
        f'transform="skewX(-20)" opacity="{0.9 if primary else 0.25}"/></g></g>'
    )
    body = (
        bg
        + shine
        + icon(ico, 22, 15, 22, fg)
        + f'<text class="sans" x="56" y="32.5" font-size="{fs}" font-weight="600" fill="{fg}">{esc(label)}</text>'
        + icon("arrow", w - 40, 18, 16, fg, 2.4)
    )
    write(f"btn-{name}.svg", svg(round(w), h, label, body, css, defs))


def buttons():
    button("portfolio", "Visit portfolio", "globe", True)
    button("linkedin", "LinkedIn", "linkedin", False)
    button("email", "Email me", "mail", False)


# ================================================================ numbers (odometer)
def numbers():
    W, H = 1200, 214
    stats = [
        ("20", "K+", "records in the capstone", "air-quality dataset"),
        ("8", "", "environmental input", "features modelled"),
        ("5", "", "classifiers compared:", "RF, DT, LR, SVM, KNN"),
        ("3", "", "live product prototypes", "deployed"),
    ]
    cycle, Lh, fs = 12.0, 76, 66
    css = [
        f".cyc{{animation:cyc {cycle}s ease infinite}}@keyframes cyc{{0%{{opacity:0}}3%,93%{{opacity:1}}98%,100%{{opacity:0}}}}",
        ".bar{animation:bar " + f"{cycle}s {EASE}" + " infinite;transform-box:fill-box;transform-origin:left}"
        "@keyframes bar{0%{transform:scaleX(0)}20%,100%{transform:scaleX(1)}}",
    ]
    defs, b = [], [card(W, H)]
    b.append(mono(36, 40, "// by the numbers", 12, D["acc"]))
    b.append(mono(W - 36 - mono_w("real figures from my projects", 12), 40, "real figures from my projects", 12, D["text3"]))
    cw = (W - 72) / 4
    dig_w = fs * 0.6
    for c, (num, suf, l1, l2) in enumerate(stats):
        x0 = 36 + c * cw
        if c:
            b.append(f'<path d="M{x0 - 0.5:.1f} 62V{H - 28}" stroke="{D["line"]}"/>')
        px = x0 + (24 if c else 0)
        b.append(f'<rect class="bar" style="animation-delay:{c * 0.15:.2f}s" x="{px:.1f}" y="62" width="40" height="2" fill="{D["acc"]}"/>')
        g = [f'<g class="cyc">']
        for k, ch in enumerate(num):
            d = int(ch)
            seq = list(range(10)) + list(range(d + 1))
            dist = (len(seq) - 1) * Lh
            cid = f"c{c}{k}"
            dx = px + k * dig_w
            defs.append(f'<clipPath id="{cid}"><rect x="{dx - 2:.1f}" y="{142 - fs:.0f}" width="{dig_w + 4:.1f}" height="{Lh}"/></clipPath>')
            css.append(
                f"@keyframes r{cid}{{0%{{transform:translateY(0)}}{18 + c * 2 + k * 2}%,100%{{transform:translateY(-{dist}px)}}}}"
                f".r{cid}{{animation:r{cid} {cycle}s cubic-bezier(.2,.9,.25,1) infinite}}"
            )
            col = "".join(
                f'<text class="sans" x="{dx:.1f}" y="{134 + i * Lh}" font-size="{fs}" font-weight="600" fill="{D["text"]}">{v}</text>'
                for i, v in enumerate(seq)
            )
            g.append(f'<g clip-path="url(#{cid})"><g class="r{cid}" transform="translate(0 -{dist})">{col}</g></g>')
        if suf:
            g.append(
                f'<text class="sans" x="{px + len(num) * dig_w + 2:.1f}" y="134" font-size="{fs}" font-weight="600" fill="{D["acc"]}">{esc(suf)}</text>'
            )
        g.append("</g>")
        b.append("".join(g))
        b.append(f'<text class="sans" x="{px:.1f}" y="168" font-size="16" fill="{D["text2"]}">{esc(l1)}</text>')
        b.append(f'<text class="sans" x="{px:.1f}" y="190" font-size="16" fill="{D["text2"]}">{esc(l2)}</text>')
    label = "By the numbers: 20K+ records in the capstone dataset, 8 input features, 5 classifiers compared, 3 live product prototypes."
    write("numbers.svg", svg(W, H, label, "".join(b), "".join(css), "".join(defs)))


# ================================================================ capstone pipeline
def pipeline():
    W, H = 1200, 480
    cycle = 5.2
    inputs = ["PM2.5", "PM10", "CO", "CO₂", "NO₂", "O₃", "Temperature", "Humidity"]
    models = ["Random Forest", "Decision Tree", "Logistic Regression", "SVM", "KNN"]
    css = [
        ".base{fill:none;stroke:#94aad2;stroke-opacity:.2;stroke-width:1.2}",
        ".dash{fill:none;stroke:" + D["acc"] + ";stroke-opacity:.45;stroke-width:1.3;stroke-dasharray:3 9;animation:dash 1.1s linear infinite}",
        "@keyframes dash{to{stroke-dashoffset:-24}}",
        ".box{fill:" + D["elev2"] + ";stroke:rgba(148,170,210,.24)}",
    ]
    # stage windows inside one cycle: inputs->prep, prep->models, models->xai, xai->insight
    stages = [(0.00, 0.22), (0.24, 0.44), (0.46, 0.66), (0.68, 0.80)]
    for k, (s, e) in enumerate(stages):
        hit = e * 100
        css.append(
            f".glow{k}{{animation:glow{k} {cycle}s ease-out infinite}}"
            f"@keyframes glow{k}{{0%,{hit:.0f}%{{stroke:rgba(148,170,210,.24)}}{hit + 3:.0f}%{{stroke:{D['acc']};filter:drop-shadow(0 0 8px rgba(62,224,255,.6))}}{hit + 16:.0f}%,100%{{stroke:rgba(148,170,210,.24)}}}}"
        )
    b = [card(W, H)]
    heads = [("INPUTS · 8", 48), ("PREP", 300), ("MODELS · 5", 584), ("EXPLAIN", 880), ("OUTPUT", 1048)]
    for t, x in heads:
        b.append(mono(x, 48, t, 12, D["text3"], cw=0.72))
    paths, pulses = [], []

    def edge(pid, d, stage, delay=0.0):
        paths.append(f'<path id="{pid}" class="base" d="{d}"/><path class="dash" d="{d}"/>')
        s, e = stages[stage]
        s = min(s + delay, e - 0.05)
        pulses.append(
            f'<g opacity="0"><circle r="9" fill="{D["acc"]}" fill-opacity=".22"/><circle r="3.4" fill="{D["acc"]}"/>'
            f'<animate attributeName="opacity" calcMode="discrete" dur="{cycle}s" repeatCount="indefinite" '
            f'keyTimes="0;{s:.3f};{e:.3f}" values="0;1;0"/>'
            f'<animateMotion dur="{cycle}s" repeatCount="indefinite" calcMode="linear" keyPoints="0;0;1;1" '
            f'keyTimes="0;{s:.3f};{e:.3f};1"><mpath xlink:href="#{pid}"/></animateMotion></g>'
        )

    cy = 240
    for i, t in enumerate(inputs):
        y = 74 + i * 44
        edge(f"i{i}", f"M200 {y + 16}C250 {y + 16} 250 {cy} 300 {cy}", 0, i * 0.008)
        b.append(f'<rect class="box" x="48" y="{y}" width="152" height="32" rx="9"/>')
        b.append(f'<circle cx="66" cy="{y + 16}" r="3" fill="{D["acc"]}" opacity=".8"/>')
        b.append(f'<text class="mono" x="80" y="{y + 21}" font-size="13.5" fill="{D["text2"]}">{esc(t)}</text>')
    b.append(f'<rect class="box glow0" x="300" y="{cy - 40}" width="184" height="80" rx="14"/>')
    b.append(f'<text class="sans" x="392" y="{cy - 4}" text-anchor="middle" font-size="19" font-weight="600" fill="{D["text"]}">Preprocess</text>')
    b.append(f'<text class="mono" x="392" y="{cy + 20}" text-anchor="middle" font-size="12.5" fill="{D["text3"]}">+ feature engineering</text>')
    my0 = cy - (5 * 40 + 4 * 16) / 2
    for j, t in enumerate(models):
        y = my0 + j * 56
        edge(f"m{j}", f"M484 {cy}C534 {cy} 534 {y + 20} 584 {y + 20}", 1, j * 0.01)
        edge(f"x{j}", f"M790 {y + 20}C836 {y + 20} 836 {cy} 880 {cy}", 2, j * 0.01)
        b.append(f'<rect class="box glow1" x="584" y="{y}" width="206" height="40" rx="10"/>')
        b.append(f'<text class="sans" x="604" y="{y + 26}" font-size="15.5" font-weight="500" fill="{D["text"]}">{esc(t)}</text>')
    edge("o0", f"M1004 {cy}H1048", 3)
    b.append(f'<rect class="box glow2" x="880" y="{cy - 40}" width="124" height="80" rx="14"/>')
    b.append(f'<text class="sans" x="942" y="{cy - 2}" text-anchor="middle" font-size="22" font-weight="600" fill="{D["acc"]}">XAI</text>')
    b.append(f'<text class="mono" x="942" y="{cy + 20}" text-anchor="middle" font-size="12.5" fill="{D["text3"]}">why?</text>')
    b.append(f'<rect class="box glow3" x="1048" y="{cy - 40}" width="114" height="80" rx="14"/>')
    b.append(f'<text class="sans" x="1105" y="{cy - 2}" text-anchor="middle" font-size="18" font-weight="600" fill="{D["text"]}">Insight</text>')
    b.append(f'<text class="mono" x="1105" y="{cy + 20}" text-anchor="middle" font-size="12.5" fill="{D["text3"]}">for people</text>')
    cap = "// capstone.pipeline   20,000+ records · 8 features · 5 classifiers · feature-level impact via XAI"
    b.append(mono(48, H - 30, cap, 12, D["text3"]))
    body = b[0] + "".join(paths) + "".join(b[1:]) + f'<g class="smil">{"".join(pulses)}</g>'
    label = (
        "Capstone pipeline: 8 inputs (PM2.5, PM10, CO, CO2, NO2, O3, temperature, humidity) go through "
        "preprocessing and feature engineering into 5 classifiers (Random Forest, Decision Tree, Logistic "
        "Regression, SVM, KNN), then Explainable AI turns predictions into insight."
    )
    write("featured-pipeline.svg", svg(W, H, label, body, "".join(css)))


# ================================================================ project cards
def media_frame(x, y, w, h, url, live):
    """Browser chrome around a screenshot slot. Returns (svg, content_y)."""
    p = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{D["bg"]}" stroke="{D["line2"]}"/>',
        f'<path d="M{x} {y + 36}H{x + w}" stroke="{D["line"]}"/>',
    ]
    for k, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        p.append(f'<circle cx="{x + 20 + k * 16}" cy="{y + 18}" r="5" fill="{c}" opacity=".85"/>')
    if url:
        uw = min(w - 200, mono_w(url, 12) + 36)
        ux = x + (w - uw) / 2
        p.append(f'<rect x="{ux:.0f}" y="{y + 8}" width="{uw:.0f}" height="20" rx="10" fill="{D["elev2"]}"/>')
        p.append(mono(ux + 18, y + 22, url, 12, D["text3"]))
    if live:
        lx = x + w - 66
        p.append(
            f'<circle class="ping" cx="{lx}" cy="{y + 18}" r="3.5" fill="{D["ok"]}"/>'
            f'<circle cx="{lx}" cy="{y + 18}" r="3.5" fill="{D["ok"]}"/>' + mono(lx + 10, y + 22.5, "LIVE", 11, D["ok"], cw=0.7)
        )
    return "".join(p), y + 36


def screenshot(x, y, w, h, path, uid):
    data = base64.b64encode(path.read_bytes()).decode()
    return (
        f'<clipPath id="shot{uid}"><path d="M{x} {y}H{x + w}V{y + h - 16}a16 16 0 0 1-16 16H{x + 16}a16 16 0 0 1-16-16Z"/></clipPath>'
        f'<g clip-path="url(#shot{uid})"><image x="{x}" y="{y}" width="{w}" height="{h}" '
        f'preserveAspectRatio="xMidYMin slice" href="data:image/webp;base64,{data}" xlink:href="data:image/webp;base64,{data}"/>'
        f'<g class="sweep"><rect x="{x - 160}" y="{y - 40}" width="110" height="{h + 80}" fill="url(#sweep)" transform="skewX(-14)"/></g></g>'
    )


def terminal(x, y, w, lines, uid, cycle=14.0, fs=12.5, lh=18.5):
    """Lines appear one by one (CSS); each line is a list of (text, color) runs."""
    css, out = [], []
    n = len(lines)
    for i, runs in enumerate(lines):
        a = (0.35 + i * 0.22) / cycle * 100
        css.append(
            f".ln{uid}{i}{{animation:ln{uid}{i} {cycle}s ease infinite}}"
            f"@keyframes ln{uid}{i}{{0%,{a:.2f}%{{opacity:0;transform:translateX(-6px)}}{a + 2:.2f}%,94%{{opacity:1;transform:none}}99%,100%{{opacity:0}}}}"
        )
        tx = x
        segs = []
        for text, color in runs:
            segs.append(mono(tx, y + i * lh, text, fs, color))
            tx += mono_w(text, fs)
        out.append(f'<g class="ln{uid}{i}">{"".join(segs)}</g>')
        last_x = tx
    return "".join(out), "".join(css), (last_x, y + (n - 1) * lh)


def project(slug, idx, kicker, title, summary, points, tags, media_right, media, alt):
    W, H = 1200, 400
    css = [
        ".ping{animation:ping 2.4s cubic-bezier(0,0,.2,1) infinite;transform-box:fill-box;transform-origin:center}",
        "@keyframes ping{0%{transform:scale(1);opacity:.75}80%,100%{transform:scale(3.2);opacity:0}}",
        f".sweep{{animation:sweep 7s {EASE} infinite 1.2s}}@keyframes sweep{{0%{{transform:translateX(0)}}35%,100%{{transform:translateX(860px)}}}}",
        ".blink{animation:blink 1.05s steps(1) infinite}@keyframes blink{50%{opacity:0}}",
        f".flowd{{stroke-dasharray:4 8;animation:fd 1.2s linear infinite}}@keyframes fd{{to{{stroke-dashoffset:-24}}}}",
    ]
    defs = (
        f'<linearGradient id="sweep" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="#fff" stop-opacity=".16"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1" gradientTransform="rotate(0 .5 .5)">'
        f'<stop offset="0" stop-color="{D["acc"]}" stop-opacity=".9"/><stop offset=".35" stop-color="{D["acc2"]}" stop-opacity="0"/>'
        f'<stop offset=".65" stop-color="{D["acc2"]}" stop-opacity="0"/><stop offset="1" stop-color="{D["acc2"]}" stop-opacity=".7"/>'
        f'<animateTransform attributeName="gradientTransform" type="rotate" values="0 .5 .5;360 .5 .5" dur="9s" repeatCount="indefinite"/>'
        f"</linearGradient>"
        f'<radialGradient id="halo"><stop offset="0" stop-color="{D["acc"]}" stop-opacity=".09"/><stop offset="1" stop-color="{D["acc"]}" stop-opacity="0"/></radialGradient>'
    )
    mx = 576 if media_right else 24
    tx = 44 if media_right else 668
    b = [card(W, H)]
    b.append(f'<ellipse cx="{tx + 240}" cy="80" rx="380" ry="220" fill="url(#halo)"/>')
    b.append(f'<rect class="smil" x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="23.5" fill="none" stroke="url(#edge)" stroke-width="1.5"/>')
    m_svg, m_css = media(mx, 24, 600, 352)
    b.append(m_svg)
    css.append(m_css)

    # text column, laid out from y=0 and then centred vertically in the card
    col = []
    k = f"{idx}  /  {kicker}".upper()
    col.append(mono(tx, 0, k, 12.5, D["acc"], cw=0.68))
    col.append(f'<text class="sans" x="{tx - 2}" y="50" font-size="38" font-weight="600" letter-spacing="-1" fill="{D["text"]}">{esc(title)}</text>')
    yy = 90
    lines = wrap(summary, 52)
    assert len(lines) <= 3, f"{slug}: summary longer than 3 lines"
    for line in lines:
        col.append(f'<text class="sans" x="{tx}" y="{yy}" font-size="18" fill="{D["text2"]}">{esc(line)}</text>')
        yy += 27
    yy += 14
    for pt in points:
        assert len(pt) <= 56, f"{slug}: bullet too long: {pt}"
        col.append(f'<path d="M{tx} {yy - 5}h12m-4-4 4 4-4 4" fill="none" stroke="{D["acc"]}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>')
        col.append(f'<text class="sans" x="{tx + 22}" y="{yy}" font-size="15.5" fill="{D["text3"]}">{esc(pt)}</text>')
        yy += 27
    lay, bottom = chip_layout(tags, tx, yy + 4, 488)
    assert bottom <= yy + 4 + 30, f"{slug}: tags need more than one row"
    cycle = 1.5 + len(tags) * 0.14 + 5
    css.append(chip_css(cycle))
    col.append(chips_svg(lay, start=1.5, step=0.14))
    top = -13  # cap height of the kicker line
    dy = (H - (bottom - top)) / 2 - top
    b.append(f'<g transform="translate(0 {dy:.1f})">{"".join(col)}</g>')
    write(f"project-{slug}.svg", svg(W, H, alt, "".join(b), "".join(css), defs))


def shot_media(name, url, live, path=None):
    """Screenshot slot; reads the portfolio's project image unless an explicit path is given."""
    def media(x, y, w, h):
        frame, cy = media_frame(x, y, w, h, url, live)
        src = path or PORTFOLIO / "assets/img/projects" / f"{name}.webp"
        return frame + screenshot(x, cy, w, h - 36, src, name), ""
    return media


def docusense_media(x, y, w, h):
    frame, cy = media_frame(x, y, w, h, "", False)
    t = D["text2"]
    k, s, n, p, c = D["acc"], "#c3d3ea", D["acc2"], D["ok"], D["text3"]
    lines = [
        [("$ ", p), ("curl -s -X POST localhost:8000/api/query \\", t)],
        [("    -H ", t), ('"Content-Type: application/json"', s), (" \\", t)],
        [("    -d ", t), ("'{\"question\": \"What is the policy on database", s)],
        [("          backup retention periods?\"}'", s)],
        [("{", t)],
        [('  "answer"', k), (": ", t), ('"All primary database backups are retained', s)],
        [('             for a rolling period of 30 calendar days. ..."', s), (",", t)],
        [('  "sources"', k), (": [{ ", t), ('"chunk_id"', k), (": ", t), ('"chunk_04"', s), (", ", t), ('"similarity_score"', k), (": ", t), ("0.87", n), (" }],", t)],
        [('  "tokens_used"', k), (": ", t), ("0", n)],
        [("}", t)],
        [("", t)],
        [("# not in the docs? one fixed fallback sentence, no guessing", c)],
    ]
    body, css, (lx, ly) = terminal(x + 20, cy + 30, w - 40, lines, "d", fs=12, lh=21)
    title = mono(x + w / 2 - mono_w("bash  —  docusense-rag", 12) / 2, y + 22, "bash  —  docusense-rag", 12, D["text3"])
    cur = f'<rect class="blink" x="{x + 20}" y="{ly + 21 - 11:.0f}" width="8" height="15" fill="{D["acc"]}"/>'
    return frame + title + body + cur, css


def phonebook_media(x, y, w, h):
    frame, cy = media_frame(x, y, w, h, "", False)
    # Real menu output of phonebook.c (blank lines dropped to fit the card).
    banner = [
        "=================================================",
        "      DIGITAL PHONEBOOK -- 2026 EDITION",
        "=================================================",
    ]
    options = [
        "Create new contact", "View all contacts", "Edit contact", "Find contact",
        "Remove contact", "Block contact", "View blocked contacts", "Mark / unmark favorite",
        "View favorite contacts", "Contact statistics", "Export contacts to file", "Exit",
    ]
    lines = [[(m, D["acc"])] for m in banner]
    lines += [[(f"{i + 1:2d}. ", D["acc"]), (o, D["text2"])] for i, o in enumerate(options)]
    lines.append([("Select your option: ", D["text"])])
    body, css, (lx, ly) = terminal(x + 28, cy + 30, w - 56, lines, "p", fs=12.5, lh=17.4)
    title = mono(x + w / 2 - mono_w("phonebook.c  —  MinGW GCC", 12) / 2, y + 22, "phonebook.c  —  MinGW GCC", 12, D["text3"])
    cur = f'<rect class="blink" x="{lx + 2:.0f}" y="{ly - 12:.0f}" width="8" height="15" fill="{D["acc"]}"/>'
    return frame + title + body + cur, css


def ads_media(x, y, w, h):
    frame, cy = media_frame(x, y, w, h, "", False)
    steps = [("01", "CONCEPT", "Creative ad concepts"), ("02", "GENERATE", "AI-based generative content tools"), ("03", "DELIVER", "Short-form promotional ads")]
    p = [frame, mono(x + w / 2 - mono_w("ad-workflow", 12) / 2, y + 22, "ad-workflow", 12, D["text3"])]
    css = []
    bx, bw, bh = x + 70, w - 140, 70
    for i, (n, tag, text) in enumerate(steps):
        by = cy + 22 + i * 98
        css.append(
            f".st{i}{{animation:st{i} 6s ease infinite}}"
            f"@keyframes st{i}{{0%,{i * 22}%,{i * 22 + 30}%,100%{{stroke:rgba(148,170,210,.24)}}{i * 22 + 8}%{{stroke:{D['acc']}}}}}"
        )
        p.append(f'<rect class="st{i}" x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="14" fill="{D["elev2"]}" stroke="rgba(148,170,210,.24)"/>')
        p.append(mono(bx + 22, by + 28, f"{n} · {tag}", 12, D["acc"], cw=0.7))
        p.append(f'<text class="sans" x="{bx + 22}" y="{by + 52}" font-size="17" font-weight="500" fill="{D["text"]}">{esc(text)}</text>')
        if i < 2:
            ax = x + w / 2
            p.append(f'<path class="flowd" d="M{ax} {by + bh + 4}V{by + 94}" stroke="{D["acc"]}" stroke-opacity=".7" stroke-width="1.6"/>')
    # a play glyph: the outputs are short video ads
    px, py = bx + bw - 46, cy + 22 + 2 * 98 + 35
    p.append(f'<circle cx="{px}" cy="{py}" r="17" fill="none" stroke="{D["acc"]}" stroke-opacity=".6"/><path d="M{px - 5} {py - 8}l13 8-13 8z" fill="{D["acc"]}"/>')
    return "".join(p), "".join(css)


def projects():
    project(
        "docusense", "01", "Applied AI · Grounded RAG service · 2026", "DocuSense RAG",
        "A FastAPI microservice that answers questions only from internal documentation, and returns one fixed fallback sentence when the answer is not there.",
        ["Injection screen, similarity gate and citation checks", "106 tests, golden-set evaluation, Docker CI"],
        ["Python", "FastAPI", "FAISS", "Claude API", "Docker"],
        False, docusense_media,
        "DocuSense RAG: a FastAPI service that answers only from internal documentation (FAISS retrieval, Claude or extractive answers, guardrails, 106 tests, Docker CI).",
    )
    project(
        "agricycle", "02", "AgriTech · Offline Bangla PWA · CSE495", "AgriCycle",
        "A mobile-first app for smallholder farmers in Bangladesh: sell without middlemen, earn from crop waste, get rewarded for green farming.",
        ["Farmer–buyer market, waste matcher, green rewards", "Bangla advisor with voice, offline PWA, 64 districts"],
        ["JavaScript", "PWA", "Chart.js", "Web Speech API"],
        True, shot_media("agricycle", "github.com/Majortarif/AgriCycle", False, Path(__file__).parent / "shots" / "agricycle.webp"),
        "AgriCycle: offline-first Bangla PWA for smallholder farmers with a farmer–buyer marketplace, crop-waste recycling matcher, green rewards and a Bangla farming advisor.",
    )
    project(
        "careerpilot", "03", "Career intelligence · Frontend prototype · 2026", "CareerPilot AI",
        "A career and skill workspace: analyse a CV and job descriptions, see skill gaps, follow a 12-week roadmap and track applications.",
        ["Required vs. preferred skill detection, gap scoring", "Rule-based AI, deterministic and labelled as simulated"],
        ["JavaScript", "Tailwind CSS", "Chart.js", "LocalStorage"],
        False, shot_media("careerpilot", "majortarif.github.io/CareerPilot-AI", True),
        "CareerPilot AI: career and skill intelligence prototype with CV and job analysis, skill gaps, a 12-week roadmap and an application tracker.",
    )
    project(
        "ecobin", "04", "Smart waste management · Concept + dashboard", "EcoBin 2.0",
        "An AI-powered smart waste bin concept I led from problem definition to prototype, with an operations dashboard for bins and routes.",
        ["48 simulated bins: fill level, battery, waste type", "Collection routes with a rule-based route optimizer"],
        ["Product design", "JavaScript", "Tailwind CSS", "Cloudflare"],
        True, shot_media("ecobin", "icy-leaf-c41a.tariful-ewu.workers.dev", True),
        "EcoBin 2.0: smart waste bin concept and operations dashboard with 48 simulated bins, waste analytics and route optimization.",
    )
    project(
        "pulse", "05", "Productivity · Task & habit tracker · 2026", "Pulse",
        "An AI-assisted task and habit tracker: organise tasks, build streaks, read your own analytics and ask a coach what to do next.",
        ["Habit streaks calculated from real completion dates", "Rule-based AI Coach that answers from your own data"],
        ["JavaScript", "Tailwind CSS", "LocalStorage", "Netlify"],
        False, shot_media("pulse", "ai-task-habit-tracker.netlify.app", True),
        "Pulse: task and habit tracker with streaks, productivity analytics and a rule-based AI coach.",
    )
    project(
        "phonebook", "06", "C · Console application · 2022 → 2026", "Digital Phonebook",
        "My 2022 C console project, rebuilt in 2026 with proper fixes and a colourised UI.",
        ["CRUD, search across six fields, blocking, favourites", "Statistics and export to a readable text file"],
        ["C", "File I/O", "Code::Blocks", "MinGW GCC"],
        True, phonebook_media,
        "Digital Phonebook 2026: C console app with contact CRUD, search, blocking, favourites, statistics and export.",
    )
    project(
        "ai-ads", "07", "Generative AI · Digital marketing", "AI-Powered Short Ads",
        "Short-form promotional ads and creative ad concepts made with AI-based generative content tools.",
        ["How AI-assisted workflows make advertising faster", "From creative concept to finished short-form ad"],
        ["Generative AI", "Advertising", "Creative content"],
        False, ads_media,
        "AI-Powered Short Advertisement Creation: creative ad concepts turned into short-form promotional ads with generative AI tools.",
    )


# ================================================================ skills
SKILLS = [
    ("AI & Machine Learning", "modelling and interpretation", ["Machine Learning", "Explainable AI (XAI)", "Random Forest", "Decision Tree", "Logistic Regression", "SVM", "KNN", "Feature engineering", "Model evaluation"]),
    ("Applied AI & LLMs", "grounded answers, not guesses", ["RAG", "Vector search (FAISS)", "Embeddings", "Claude API", "Structured output", "Prompt-injection guardrails", "Rule-based logic"]),
    ("Data", "analysis and visualization", ["Data analysis", "Data visualization", "Data preprocessing", "SQL", "MS Excel", "Chart.js"]),
    ("Programming & Web", "building working software", ["Python", "FastAPI", "pytest", "JavaScript (ES6+)", "HTML5 & CSS3", "Tailwind CSS", "C", "Responsive, accessible UI"]),
    ("Design & Product", "from idea to interface", ["UI/UX design", "Figma", "Product prototyping", "AI-assisted content", "Ad & campaign concepts", "Digital communication"]),
    ("Tools & Delivery", "shipping and version control", ["Git & GitHub", "GitHub Actions", "Docker", "GitHub Pages", "Netlify", "Cloudflare", "Code::Blocks"]),
]


def skills():
    W, pad, gap = 1200, 24, 16
    pw = (W - 2 * pad - 2 * gap) / 3
    inner = pw - 44
    rows, layouts = [], []
    for r in range(2):
        hs = []
        for c in range(3):
            _, _, items = SKILLS[r * 3 + c]
            lay, bottom = chip_layout(items, 0, 0, inner)
            layouts.append(lay)
            hs.append(bottom)
        rows.append(98 + max(hs) + 24)
    H = pad + rows[0] + gap + rows[1] + pad
    total = sum(len(s[2]) for s in SKILLS)
    cycle = total * 0.09 + 4
    css = [chip_css(cycle), f".rise{{animation:rise .9s {EASE} both}}@keyframes rise{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}"]
    b = [card(W, H)]
    k = 0
    for i, (title, note, items) in enumerate(SKILLS):
        r, c = divmod(i, 3)
        x = pad + c * (pw + gap)
        y = pad + (0 if r == 0 else rows[0] + gap)
        h = rows[r]
        b.append(f'<g class="rise" style="animation-delay:{0.1 + i * 0.08:.2f}s">')
        b.append(f'<rect x="{x:.1f}" y="{y}" width="{pw:.1f}" height="{h}" rx="16" fill="{D["elev2"]}" stroke="{D["line"]}"/>')
        b.append(mono(x + 22, y + 34, f"{i + 1:02d}", 12, D["acc"]))
        b.append(f'<path d="M{x + 48:.1f} {y + 30}H{x + 72:.1f}" stroke="{D["acc"]}" stroke-opacity=".6"/>')
        b.append(mono(x + 82, y + 34, note, 12, D["text3"]))
        b.append(f'<text class="sans" x="{x + 22:.1f}" y="{y + 70}" font-size="21" font-weight="600" fill="{D["text"]}">{esc(title)}</text>')
        lay = [(x + 22 + cx, y + 92 + cy, w, t) for cx, cy, w, t in layouts[i]]
        b.append(chips_svg(lay, start=k * 0.09, step=0.09))
        b.append("</g>")
        k += len(items)
    label = "Skills. " + " ".join(f"{t}: {', '.join(items)}." for t, _, items in SKILLS)
    write("skills.svg", svg(W, H, label, "".join(b), "".join(css)))


# ================================================================ experience timeline
def experience():
    W, H = 1200, 396
    cols = [
        ("2026", "Self-directed", "Product builder", "Independent projects",
         "Designed and shipped browser-based product prototypes and a grounded RAG service end to end, from problem framing and UI to deployment.",
         ["CareerPilot AI · EcoBin · Pulse", "DocuSense RAG (FastAPI, FAISS, Claude)"]),
        ("2025", "Academic research", "Capstone research", "East West University · CSE400C",
         "Three-person capstone on air-quality prediction, supervised by Dr. Tania Sultana. Data preparation, model training, evaluation and XAI.",
         ["8 environmental parameters", "Plain-language insight on what drives air quality"]),
        ("2 yrs each", "Volunteering", "Club volunteer", "Three campus clubs",
         "Organising technical events, supporting workshops and managing communication-based outreach.",
         ["EWU Robotics Club", "Science Club · Telecommunication Club"]),
    ]
    css = [
        f".line{{stroke-dasharray:1120;animation:draw 10s {EASE} infinite}}@keyframes draw{{0%{{stroke-dashoffset:1120}}22%,100%{{stroke-dashoffset:0}}}}",
        ".ping{animation:ping 2.6s cubic-bezier(0,0,.2,1) infinite;transform-box:fill-box;transform-origin:center}",
        "@keyframes ping{0%{transform:scale(1);opacity:.7}80%,100%{transform:scale(3.4);opacity:0}}",
        f".rise{{animation:rise .9s {EASE} both}}@keyframes rise{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}",
    ]
    defs = (
        f'<linearGradient id="tl" x1="0" x2="1"><stop offset="0" stop-color="{D["acc"]}"/>'
        f'<stop offset=".6" stop-color="{D["acc2"]}"/><stop offset="1" stop-color="{D["acc2"]}" stop-opacity=".15"/></linearGradient>'
    )
    b = [card(W, H)]
    b.append(f'<path d="M40 70H1160" stroke="{D["line2"]}"/>')
    b.append('<path class="line" d="M40 70H1160" stroke="url(#tl)" stroke-width="2"/>')
    cw = 1120 / 3
    for i, (period, kind, title, org, text, pts) in enumerate(cols):
        x = 40 + i * cw
        b.append(
            f'<circle class="ping" style="animation-delay:{i * 0.6:.1f}s" cx="{x + 8:.1f}" cy="70" r="6" fill="{D["acc"]}"/>'
            f'<circle cx="{x + 8:.1f}" cy="70" r="6" fill="{D["bg"]}" stroke="{D["acc"]}" stroke-width="2.5"/>'
        )
        b.append(f'<g class="rise" style="animation-delay:{0.2 + i * 0.15:.2f}s">')
        b.append(mono(x, 118, period, 15, D["acc"]))
        kw = mono_w(kind.upper(), 11, 0.7) + 20
        kx = x + mono_w(period, 15) + 14
        b.append(f'<rect x="{kx:.1f}" y="102" width="{kw:.1f}" height="22" rx="11" fill="rgba(62,224,255,.08)" stroke="rgba(62,224,255,.3)"/>')
        b.append(mono(kx + 10, 117, kind.upper(), 11, D["acc"], cw=0.7))
        b.append(f'<text class="sans" x="{x:.1f}" y="160" font-size="25" font-weight="600" letter-spacing="-.5" fill="{D["text"]}">{esc(title)}</text>')
        b.append(f'<text class="sans" x="{x:.1f}" y="186" font-size="15.5" fill="{D["text3"]}">{esc(org)}</text>')
        y = 224
        for line in wrap(text, 41):
            b.append(f'<text class="sans" x="{x:.1f}" y="{y}" font-size="16" fill="{D["text2"]}">{esc(line)}</text>')
            y += 24
        y += 12
        for pt in pts:
            b.append(f'<circle cx="{x + 4:.1f}" cy="{y - 5}" r="2.5" fill="{D["acc"]}"/>')
            b.append(f'<text class="sans" x="{x + 16:.1f}" y="{y}" font-size="14.5" fill="{D["text3"]}">{esc(pt)}</text>')
            y += 23
        b.append("</g>")
    label = "Experience. " + " ".join(f"{p}, {k}: {t}, {o}. {x}" for p, k, t, o, x, _ in cols)
    write("experience.svg", svg(W, H, label, "".join(b), "".join(css), defs))


# ================================================================ ultrasonic extras
def wave_divider():
    """Section divider: three phase-shifting ultrasonic waves and a travelling signal packet."""
    W, H = 1200, 72
    mid = H / 2
    layers = [  # wavelength, amplitude, colour, opacity, stroke width, seconds per wavelength
        (300, 15, D["acc2"], 0.5, 1.6, 9),
        (150, 9, D["acc"], 0.8, 1.8, 4.5),
        (40, 4, D["acc"], 0.45, 1.1, 1.6),
    ]
    defs = (
        '<linearGradient id="fade" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset=".2" stop-color="#fff"/><stop offset=".8" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<mask id="m" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>'
        f'<radialGradient id="pulse"><stop offset="0" stop-color="{D["acc"]}" stop-opacity=".9"/><stop offset="1" stop-color="{D["acc"]}" stop-opacity="0"/></radialGradient>'
    )
    css, b = [], []
    for k, (lam, amp, col, op, sw, sec) in enumerate(layers):
        step = 4 if lam < 100 else 8
        pts = [f"{x},{mid + amp * math.sin(2 * math.pi * x / lam):.1f}" for x in range(0, W + lam + 1, step)]
        css.append(f".w{k}{{animation:w{k} {sec}s linear infinite}}@keyframes w{k}{{to{{transform:translateX(-{lam}px)}}}}")
        b.append(f'<path class="w{k}" d="M{pts[0]}L{" ".join(pts[1:])}" fill="none" stroke="{col}" stroke-opacity="{op}" stroke-width="{sw}" stroke-linecap="round"/>')
    css.append(f".pk{{animation:pk 3.8s linear infinite}}@keyframes pk{{from{{transform:translateX(-90px)}}to{{transform:translateX({W + 90}px)}}}}")
    b.append(f'<g class="pk"><ellipse cx="0" cy="{mid}" rx="70" ry="16" fill="url(#pulse)" opacity=".5"/><circle cx="0" cy="{mid}" r="3" fill="#fff"/></g>')
    write("divider-wave.svg", svg(W, H, "Animated ultrasonic wave divider", f'<g mask="url(#m)">{"".join(b)}</g>', "".join(css), defs))


TICKER = ["Machine Learning", "Explainable AI", "Python", "FastAPI", "RAG", "FAISS", "Claude API",
          "Data Analysis", "Data Visualization", "JavaScript", "PWA", "Chart.js", "Figma", "UI/UX", "Docker", "GitHub Actions"]


def ticker():
    """An endless, edge-faded ribbon of the stack, with a pinging SCAN badge."""
    W, H, fs, cw, gap = 1200, 60, 14, 0.66, 46
    y = H / 2 + fs * 0.36
    row, x = [], 0.0
    for t in TICKER:
        s = t.upper()
        row.append(mono(x, y, s, fs, D["text2"], cw=cw))
        x += mono_w(s, fs, cw) + gap
        dx = x - gap / 2
        row.append(f'<path d="M{dx:.1f} {H / 2 - 5}l5 5-5 5-5-5z" fill="{D["acc"]}" opacity=".85"/>')
    seq = x
    row = "".join(row)
    css = [
        f".tk{{animation:tk {seq / 48:.1f}s linear infinite}}@keyframes tk{{to{{transform:translateX(-{seq:.1f}px)}}}}",
        ".ping{animation:ping 2s cubic-bezier(0,0,.2,1) infinite;transform-box:fill-box;transform-origin:center}",
        "@keyframes ping{0%{transform:scale(1);opacity:.8}80%,100%{transform:scale(3);opacity:0}}",
    ]
    defs = (
        f'<clipPath id="c"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="{H / 2 - 1}"/></clipPath>'
        '<linearGradient id="edge" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset=".2" stop-color="#fff"/><stop offset=".93" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<mask id="m" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="url(#edge)"/></mask>'
    )
    badge_w = 128
    b = [
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="{H / 2}" fill="{D["elev"]}" stroke="{D["line2"]}"/>',
        f'<g clip-path="url(#c)"><g mask="url(#m)"><g transform="translate({badge_w + 30} 0)"><g class="tk"><g>{row}</g><g transform="translate({seq:.1f} 0)">{row}</g></g></g></g></g>',
        f'<rect x="8" y="8" width="{badge_w}" height="{H - 16}" rx="{(H - 16) / 2}" fill="{D["elev2"]}" stroke="{D["acc"]}" stroke-opacity=".45"/>',
        f'<circle cx="30" cy="{H / 2}" r="4" fill="{D["ok"]}"/><circle class="ping" cx="30" cy="{H / 2}" r="4" fill="{D["ok"]}"/>',
        mono(44, y - 0.5, "NOW SCANNING", 11.5, D["acc"], cw=0.62),
    ]
    write("ticker.svg", svg(W, H, "Stack: " + ", ".join(TICKER) + ".", "".join(b), "".join(css), defs))


def status_card():
    """A terminal that types who I am, next to a radar that sweeps across my core skills."""
    W, H = 1200, 330
    T = 6.0  # radar revolution, seconds
    b = [card(W, H)]
    fx, fy, fw, fh = 24, 24, 760, 282
    frame, cy = media_frame(fx, fy, fw, fh, "", False)
    tt = "zsh  —  tariful@dhaka"
    b.append(frame + mono(fx + fw / 2 - mono_w(tt, 12) / 2, fy + 22, tt, 12, D["text3"]))
    t1, t2, t3, ok, a1, a2 = D["text"], D["text2"], D["text3"], D["ok"], D["acc"], D["acc2"]

    def prompt(cmd):
        return [("tariful@dhaka", ok), (":", t3), ("~", a2), ("$ ", t3), (cmd, t1)]

    lines = [
        prompt("whoami"),
        [("  Tariful Hoque  ·  CSE graduate, East West University", t2)],
        prompt("cat focus.txt"),
        [("  machine learning · explainable AI · grounded LLMs · UI/UX", t2)],
        prompt("ls ~/shipped"),
        [("  docusense-rag/  agricycle/  careerpilot-ai/  ecobin/  pulse/", a1)],
        prompt("./status --live"),
        [("  ● open to AI/ML roles    ● building in public    ● UTC+6", ok)],
    ]
    body, tcss, (lx, ly) = terminal(fx + 24, cy + 34, fw - 48, lines, "s", cycle=15.0, fs=13, lh=26)
    b.append(body)
    b.append(f'<rect class="blink" x="{fx + 24}" y="{ly + 26 - 12:.0f}" width="8" height="16" fill="{a1}"/>')

    # radar
    rx, ry, R = 994, 160, 118
    a = math.radians(-50)
    css = [
        tcss,
        ".blink{animation:blink 1.05s steps(1) infinite}@keyframes blink{50%{opacity:0}}",
        f".sweep{{animation:sweep {T}s linear infinite;transform-origin:{rx}px {ry}px}}@keyframes sweep{{to{{transform:rotate(360deg)}}}}",
        f".blip{{opacity:.22;animation:blip {T}s ease-out infinite}}",
        "@keyframes blip{0%{opacity:1}35%,100%{opacity:.22}}",
        f".ring{{animation:ring {T / 2}s cubic-bezier(.2,.6,.3,1) infinite;transform-box:fill-box;transform-origin:center}}",
        "@keyframes ring{0%{transform:scale(.1);opacity:0}15%{opacity:.5}100%{transform:scale(1);opacity:0}}",
    ]
    defs = (
        f'<linearGradient id="beam" gradientUnits="userSpaceOnUse" x1="{rx + 70}" y1="{ry}" x2="{rx + 70 * math.cos(a):.0f}" y2="{ry + 70 * math.sin(a):.0f}">'
        f'<stop offset="0" stop-color="{a1}" stop-opacity=".38"/><stop offset="1" stop-color="{a1}" stop-opacity="0"/></linearGradient>'
        f'<radialGradient id="disc"><stop offset="0" stop-color="{a1}" stop-opacity=".08"/><stop offset="1" stop-color="{a1}" stop-opacity="0"/></radialGradient>'
    )
    b.append(f'<circle cx="{rx}" cy="{ry}" r="{R}" fill="url(#disc)" stroke="{D["line2"]}"/>')
    for r in (R / 3, 2 * R / 3):
        b.append(f'<circle cx="{rx}" cy="{ry}" r="{r:.0f}" fill="none" stroke="{D["line"]}" stroke-dasharray="2 5"/>')
    b.append(f'<path d="M{rx - R} {ry}H{rx + R}M{rx} {ry - R}V{ry + R}" stroke="{D["line"]}"/>')
    b.append(f'<circle class="ring" cx="{rx}" cy="{ry}" r="{R}" fill="none" stroke="{a1}" stroke-width="1.2"/>')
    ex, ey = rx + R * math.cos(a), ry + R * math.sin(a)
    b.append(
        f'<g class="sweep"><path d="M{rx} {ry}L{rx + R} {ry}A{R} {R} 0 0 0 {ex:.1f} {ey:.1f}Z" fill="url(#beam)"/>'
        f'<path d="M{rx} {ry}H{rx + R}" stroke="{a1}" stroke-width="1.6" stroke-opacity=".8"/></g>'
    )
    blips = [("ML", 300, 72), ("XAI", 25, 92), ("RAG", 120, 64), ("UI/UX", 205, 96), ("DATA", 250, 40)]
    for name, deg, dist in blips:
        bx = rx + dist * math.cos(math.radians(deg))
        by = ry + dist * math.sin(math.radians(deg))
        delay = deg / 360 * T
        lw = mono_w(name, 11)
        tx = bx + 9 if bx < rx + 40 else bx - 9 - lw
        b.append(
            f'<g class="blip" style="animation-delay:{delay:.2f}s"><circle cx="{bx:.1f}" cy="{by:.1f}" r="9" fill="{a1}" fill-opacity=".18"/>'
            f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="3.4" fill="{a1}"/>{mono(tx, by + 4, name, 11, t1)}</g>'
        )
    b.append(f'<circle cx="{rx}" cy="{ry}" r="3.5" fill="{a1}"/>')
    cap = "// skills.scan  ·  ultrasonic sweep"
    b.append(mono(rx - mono_w(cap, 11.5) / 2, H - 22, cap, 11.5, t3))
    label = (
        "Terminal: whoami, Tariful Hoque, CSE graduate from East West University. Focus: machine learning, "
        "explainable AI, grounded LLMs and UI/UX. Shipped: DocuSense RAG, AgriCycle, CareerPilot AI, EcoBin, Pulse. "
        "Status: open to AI/ML roles. A radar sweeps across ML, XAI, RAG, UI/UX and data."
    )
    write("status.svg", svg(W, H, label, "".join(b), "".join(css), defs))


# ================================================================ footer
def footer():
    W, H = 1200, 250
    css = [
        ".w1{animation:wave 16s linear infinite}.w2{animation:wave 24s linear infinite reverse}.w3{animation:wave 34s linear infinite}",
        f"@keyframes wave{{from{{transform:translateX(0)}}to{{transform:translateX(-{W}px)}}}}",
        f".rise{{animation:rise 1s {EASE} both .2s}}@keyframes rise{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}",
        ".tw{animation:tw 4s ease-in-out infinite alternate}@keyframes tw{from{opacity:.08}to{opacity:.7}}",
    ]

    def wave(amp, base, periods, phase):
        pts = []
        for i in range(0, 2 * W + 1, 12):
            y = base + amp * math.sin(2 * math.pi * periods * i / W + phase)
            pts.append(f"{i},{y:.1f}")
        return f'M{pts[0]}L{" ".join(pts[1:])}V{H}H0Z'

    defs = (
        f'<clipPath id="f"><rect width="{W}" height="{H}" rx="22"/></clipPath>'
        f'<linearGradient id="em" x1="0" x2="1"><stop offset="0" stop-color="{D["acc"]}"/><stop offset="1" stop-color="{D["acc2"]}"/></linearGradient>'
        f'<linearGradient id="fadeUp" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{D["acc"]}" stop-opacity=".16"/><stop offset="1" stop-color="{D["acc"]}" stop-opacity="0"/></linearGradient>'
    )
    rnd = random.Random(7)
    b = [f'<g clip-path="url(#f)"><rect width="{W}" height="{H}" fill="{D["bg"]}"/>']
    for _ in range(40):
        b.append(
            f'<circle class="tw" cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(10, 160):.0f}" r="{rnd.choice([0.7, 1, 1.3])}" fill="#a9dcff" '
            f'style="animation-delay:{-rnd.uniform(0, 4):.1f}s;animation-duration:{rnd.uniform(2.5, 6):.1f}s"/>'
        )
    b.append(f'<path class="w3" d="{wave(10, 196, 2, 0.6)}" fill="{D["acc2"]}" fill-opacity=".06"/>')
    b.append(f'<path class="w2" d="{wave(14, 206, 1, 2.0)}" fill="url(#fadeUp)"/>')
    b.append(f'<path class="w1" d="{wave(8, 218, 3, 1.1)}" fill="{D["acc"]}" fill-opacity=".07"/>')
    b.append(
        f'<g class="rise"><text class="sans" x="600" y="96" text-anchor="middle" font-size="40" font-weight="600" '
        f'letter-spacing="-1" fill="{D["text"]}" xml:space="preserve">Thanks for <tspan class="serif" font-size="46" '
        f'font-weight="400" fill="url(#em)">stopping by.</tspan></text>'
    )
    line = "Machine Learning  ·  Explainable AI  ·  Data  ·  UI/UX"
    b.append(mono(600 - mono_w(line, 13) / 2, 134, line, 13, D["text3"]))
    cr = "© 2026 Tariful Hoque  ·  Dhaka, Bangladesh"
    b.append(mono(600 - mono_w(cr, 12) / 2, 228, cr, 12, D["text2"]))
    b.append("</g></g>")
    b.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" fill="none" stroke="{D["line2"]}"/>')
    write("footer.svg", svg(W, H, "Thanks for stopping by. © 2026 Tariful Hoque, Dhaka, Bangladesh.", "".join(b), "".join(css), defs))


if __name__ == "__main__":
    if not PORTFOLIO or not (PORTFOLIO / "assets/img/projects").is_dir():
        sys.exit("usage: build_assets.py <path-to-tariful-portfolio-2026>")
    OUT.mkdir(exist_ok=True)
    hero()
    headings()
    buttons()
    numbers()
    pipeline()
    projects()
    skills()
    experience()
    wave_divider()
    ticker()
    status_card()
    footer()
