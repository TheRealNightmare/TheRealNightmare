#!/usr/bin/env python3
"""Build every SVG panel for the profile README.

All assets share one grid and one palette so the README reads as a single
designed surface rather than a stack of unrelated images. Nothing here is
hand-tweaked: edit this file and re-run it.

Every panel is measured before it is written, and the build fails loudly if any
text or chip row would overflow its container.
"""
import math
import os
import sys

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

# --------------------------------------------------------------------------
# palette — the only place colors are written
# --------------------------------------------------------------------------
P = {
    "bg":     "#0D0D0D",
    "panel":  "#161616",
    "border": "#2A2A2A",
    "lime":   "#A3E636",
    "yellow": "#FFDC58",
    "text":   "#E6E6E6",
    "muted":  "#8B8B8B",
    "red":    "#FF6B6B",
}

# --------------------------------------------------------------------------
# grid
# --------------------------------------------------------------------------
W = 880          # canvas width, matches GitHub's readable column
MARGIN = 24      # outer margin
UNIT = 8         # baseline unit; every y is a multiple of this
GUTTER = 16
INNER = W - 2 * MARGIN          # 832
COL = (INNER - 11 * GUTTER) / 12  # 12-column grid

MONO = "'JetBrains Mono','Fira Code','SFMono-Regular',Consolas,'Courier New',monospace"
ADVANCE = 0.6    # mono advance as a fraction of font-size (validated last pass)

_errors = []


def fail(msg):
    _errors.append(msg)


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def tw(text, size, tracking=0.0):
    """Estimated rendered width of a mono string."""
    return len(text) * (size * ADVANCE + tracking)


# --------------------------------------------------------------------------
# primitives
# --------------------------------------------------------------------------
def mono(x, y, text, size=13, color=None, weight=400, anchor="start", tracking=0.0, opacity=None):
    color = color or P["text"]
    if "  " in text:
        # SVG collapses runs of whitespace, so padded strings silently lose their
        # alignment. Columns must be positioned with x, never with spaces.
        fail(f"run of spaces will collapse when rendered: {text!r}")
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    t = f' letter-spacing="{tracking}"' if tracking else ""
    o = f' opacity="{opacity}"' if opacity is not None else ""
    return (f'<text x="{x:g}" y="{y:g}"{a} font-family="{MONO}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}"{t}{o}>{esc(text)}</text>')


def panel(x, y, w, h, accent=None, fill=None):
    """Raised panel: border + fill, optional accent rule on the left edge.

    On a dark ground a drop shadow is invisible, so depth comes from the
    1.5px border against the darker page behind it.
    """
    out = [f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{fill or P["panel"]}" '
           f'stroke="{P["border"]}" stroke-width="1.5"/>']
    if accent:
        out.append(f'<rect x="{x:g}" y="{y:g}" width="2" height="{h:g}" fill="{accent}"/>')
    return out


ORBIT_R = 88     # outer ring radius
ORBIT_TICK = 9   # radial ticks sit outside the outer ring
ORBIT_EXT = ORBIT_R + 4 + ORBIT_TICK   # full extent, ticks included


def _ring(cx, cy, r, color, width=1, dash=None, opacity=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    o = f' opacity="{opacity}"' if opacity is not None else ""
    return (f'<circle cx="{cx:g}" cy="{cy:g}" r="{r:g}" fill="none" stroke="{color}" '
            f'stroke-width="{width:g}"{d}{o}/>')


def _node(cx, cy, r, angle, size, color):
    """A dot parked on a ring at `angle` degrees, measured from 12 o'clock."""
    a = math.radians(angle - 90)
    return (f'<circle cx="{cx + r * math.cos(a):.1f}" cy="{cy + r * math.sin(a):.1f}" '
            f'r="{size:g}" fill="{color}"/>')


def _spin(parts, cx, cy, dur, reverse=False):
    """Wrap parts in a group that rotates about (cx, cy) forever."""
    f, t = (360, 0) if reverse else (0, 360)
    return ([f'<g>'] + parts +
            [f'<animateTransform attributeName="transform" attributeType="XML" type="rotate" '
             f'from="{f} {cx:g} {cy:g}" to="{t} {cx:g} {cy:g}" dur="{dur}s" '
             f'repeatCount="indefinite"/>', '</g>'])


def orbital(cx, cy):
    """Ambient orbital figure — concentric rings turning at unrelated speeds.

    Purely geometric: no labels, nothing to decode. It fills the empty right half
    of the hero so the panel reads as composed rather than half-finished.

    The root <svg> sets shape-rendering="crispEdges", which is right for the
    rectangles and text everywhere else but would make these arcs visibly jagged,
    so the whole figure overrides it.
    """
    b = [f'<g shape-rendering="geometricPrecision">']

    # fixed instrumentation — the frame the mechanism turns inside
    for i in range(12):
        a = math.radians(i * 30 - 90)
        r0, r1 = ORBIT_R + 4, ORBIT_EXT
        b.append(f'<line x1="{cx + r0 * math.cos(a):.1f}" y1="{cy + r0 * math.sin(a):.1f}" '
                 f'x2="{cx + r1 * math.cos(a):.1f}" y2="{cy + r1 * math.sin(a):.1f}" '
                 f'stroke="{P["border"]}" stroke-width="1"/>')
    b.append(f'<line x1="{cx - ORBIT_R:g}" y1="{cy:g}" x2="{cx + ORBIT_R:g}" y2="{cy:g}" '
             f'stroke="{P["border"]}" stroke-width="1" opacity="0.5"/>')
    b.append(f'<line x1="{cx:g}" y1="{cy - ORBIT_R:g}" x2="{cx:g}" y2="{cy + ORBIT_R:g}" '
             f'stroke="{P["border"]}" stroke-width="1" opacity="0.5"/>')

    # three rings, each carrying its own nodes, at non-harmonic periods so the
    # composition never visibly repeats
    b += _spin([_ring(cx, cy, ORBIT_R, P["border"], 1, dash="3 7"),
                _node(cx, cy, ORBIT_R, 34, 3, P["yellow"]),
                _node(cx, cy, ORBIT_R, 208, 3, P["yellow"])],
               cx, cy, 48)
    b += _spin([_ring(cx, cy, 64, P["lime"], 1.2, opacity=0.35),
                _node(cx, cy, 64, 0, 4, P["lime"]),
                _node(cx, cy, 64, 130, 4, P["lime"]),
                _node(cx, cy, 64, 245, 4, P["lime"])],
               cx, cy, 32, reverse=True)
    b += _spin([_ring(cx, cy, 40, P["border"], 1),
                _node(cx, cy, 40, 160, 3, P["yellow"])],
               cx, cy, 20)

    # core — breathes rather than turns, so the centre reads as still
    b.append(_ring(cx, cy, 18, P["lime"], 1, opacity=0.25))
    b.append(f'<circle cx="{cx:g}" cy="{cy:g}" r="10" fill="{P["lime"]}">'
             f'<animate attributeName="opacity" values="0.55;1;0.55" dur="4s" '
             f'repeatCount="indefinite"/></circle>')

    b.append('</g>')
    return b


def check_clear(x, text, size, figure_left, where, tracking=0.0):
    """Text must not run into the orbital figure to its right."""
    end = x + tw(text, size, tracking)
    if end > figure_left - 0.5:
        fail(f"{where}: text runs into the figure ({end:.0f} > {figure_left:g}): {text!r}")


def section_head(n, title, x=MARGIN, y=40):
    """`01 // WHOAMI` — the shared section header."""
    num = f"{n:02d}"
    out = [mono(x, y, num, 15, P["yellow"], 700, tracking=1)]
    nx = x + tw(num, 15, 1) + 10
    out.append(mono(nx, y, "//", 15, P["border"], 700))
    out.append(mono(nx + 28, y, title.upper(), 15, P["text"], 700, tracking=2.4))
    return out


def chip(x, y, label, size=12, pad=11, h=24, color=None):
    w = tw(label, size) + pad * 2
    return w, [
        f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h}" fill="{P["bg"]}" '
        f'stroke="{P["border"]}" stroke-width="1"/>',
        mono(x + w / 2, y + h / 2 + 4.2, label, size, color or P["text"], 500, anchor="middle"),
    ]


def pack(labels, maxw, size=12, pad=11, gap=7):
    """Greedily pack chips into rows no wider than maxw. None if one can't fit."""
    rows, cur, curw = [], [], 0.0
    for l in labels:
        w = tw(l, size) + pad * 2
        if w > maxw:
            return None
        add = w if not cur else w + gap
        if cur and curw + add > maxw:
            rows.append(cur)
            cur, curw = [l], w
        else:
            cur.append(l)
            curw += add
    if cur:
        rows.append(cur)
    return rows


def chip_rows(labels, maxw, size=12, pad=11, gap=7):
    """Fewest rows, then even them out so no orphan chip sits alone on the last row."""
    best = pack(labels, maxw, size, pad, gap)
    if best is None:
        fail(f"chip too wide for {maxw:g}px: {labels}")
        return [labels]
    n = len(best)
    w = maxw
    while w > 40:
        w -= 4
        trial = pack(labels, w, size, pad, gap)
        if trial is None or len(trial) != n:
            break
        best = trial
    return best


def draw_chips(x, y, labels, maxw, size=12, pad=11, gap=7, h=24, rowgap=7, color=None):
    """Render chip rows from (x, y) downward. Returns (svg_parts, total_height)."""
    parts, cy = [], y
    for row in chip_rows(labels, maxw, size, pad, gap):
        cx = x
        for l in row:
            w, p = chip(cx, cy, l, size, pad, h, color)
            parts += p
            cx += w + gap
        if cx - gap - x > maxw + 0.5:
            fail(f"chip row overflows ({cx - gap - x:.0f} > {maxw:g}): {row}")
        cy += h + rowgap
    return parts, cy - y - rowgap


def check_text(x, text, size, limit, where, tracking=0.0):
    end = x + tw(text, size, tracking)
    if end > limit + 0.5:
        fail(f"{where}: text overflows ({end:.0f} > {limit:g}): {text!r}")


def check_bottom(y, limit, where):
    """Content must stay inside its panel vertically, not just horizontally."""
    if y > limit + 0.5:
        fail(f"{where}: content runs past panel bottom ({y:.0f} > {limit:g})")


def svg(name, h, body):
    doc = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" '
           f'height="{h}" shape-rendering="crispEdges">',
           f'  <rect x="0" y="0" width="{W}" height="{h}" fill="{P["bg"]}"/>']
    doc += ["  " + line for line in body]
    doc.append("</svg>")
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        f.write("\n".join(doc) + "\n")
    print(f"  {name:<16} {W}x{h}")


# --------------------------------------------------------------------------
# panels
# --------------------------------------------------------------------------
def cursor(x, y, size=14, color=None):
    """Blinking block cursor: a hard on/off step, like a real terminal."""
    return (f'<rect x="{x:g}" y="{y - size * 0.8:g}" width="{size * 0.62:g}" height="{size:g}" '
            f'fill="{color or P["lime"]}"><animate attributeName="opacity" values="1;1;0;0" '
            f'keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/></rect>')


def pill(x, y, label, color, size=10.5, pad=8, h=20, anchor="start"):
    """Outlined status tag. Returns (width, parts)."""
    w = tw(label, size, 0.8) + pad * 2
    if anchor == "end":
        x -= w
    return w, [
        f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h}" fill="none" '
        f'stroke="{color}" stroke-width="1"/>',
        mono(x + w / 2, y + h / 2 + 3.8, label, size, color, 700, anchor="middle", tracking=0.8),
    ]


def build_hero():
    h = 300
    b = []
    bar = 34
    b += panel(MARGIN, 24, INNER, h - 48)
    # title bar
    b.append(f'<rect x="{MARGIN}" y="24" width="{INNER}" height="{bar}" fill="#101010"/>')
    b.append(f'<rect x="{MARGIN}" y="{24 + bar}" width="{INNER}" height="1" fill="{P["border"]}"/>')
    for i, c in enumerate([P["red"], P["yellow"], P["lime"]]):
        b.append(f'<circle cx="{MARGIN + 20 + i * 18}" cy="{24 + bar / 2:g}" r="5" fill="{c}"/>')
    b.append(mono(MARGIN + 88, 24 + bar / 2 + 4, "mirazul@nightmare: ~", 12, P["muted"]))

    # live status, top right — a pulsing dot so the panel never looks like a screenshot
    sx = MARGIN + INNER - 20
    label = "open to work"
    b.append(mono(sx, 24 + bar / 2 + 4, label, 12, P["lime"], 500, anchor="end"))
    dx = sx - tw(label, 12) - 12
    b.append(f'<circle cx="{dx:g}" cy="{24 + bar / 2:g}" r="4" fill="{P["lime"]}">'
             f'<animate attributeName="opacity" values="1;0.25;1" dur="2s" repeatCount="indefinite"/>'
             f'</circle>')

    # the figure paints first so text always wins any overlap
    body_top, body_bot = 24 + bar, h - 24
    ocx, ocy = 716, int((body_top + body_bot) / 2)
    b += orbital(ocx, ocy)
    if ocy - ORBIT_EXT < body_top or ocy + ORBIT_EXT > body_bot:
        fail(f"hero/figure: orbital escapes the panel body vertically "
             f"({ocy - ORBIT_EXT} .. {ocy + ORBIT_EXT} outside {body_top} .. {body_bot})")
    if ocx + ORBIT_EXT > MARGIN + INNER:
        fail(f"hero/figure: orbital overruns the panel's right edge "
             f"({ocx + ORBIT_EXT} > {MARGIN + INNER:g})")
    gutter = ocx - ORBIT_EXT - 24   # 24px of breathing room beside the text

    x = MARGIN + 32
    b.append(mono(x, 112, "$ whoami", 14, P["lime"], 500))

    name, nsize, ntrack = "MIRAZUL ISLAM NAHID", 38, 1.5
    check_clear(x, name, nsize, gutter, "hero/name", ntrack)
    b.append(mono(x, 162, name, nsize, P["text"], 700, tracking=ntrack))

    role = "software developer · full-stack web · ML"
    check_clear(x, role, 14, gutter, "hero/role")
    b.append(mono(x, 192, role, 14, P["yellow"], 500))

    meta = "Dhaka, BD · @Moner-Bondhu · CSE @ UIU"
    check_clear(x, meta, 12, gutter, "hero/meta")
    b.append(mono(x, 220, meta, 12, P["muted"]))

    # prompt + cursor
    b.append(mono(x, 258, "$", 14, P["lime"], 500))
    cmd = "open mirazulislamnahid.com"
    b.append(mono(x + 16, 258, cmd, 14, P["text"]))
    check_clear(x + 16, cmd, 14, gutter, "hero/cmd")
    b.append(cursor(x + 16 + tw(cmd, 14) + 6, 258))
    return svg("hero.svg", h, b)


def build_about():
    b = section_head(1, "whoami")
    top = 60
    x, y = MARGIN + 26, top + 38
    lines = [
        ("Software developer based in Dhaka, Bangladesh.", P["text"]),
        ("Building web products at @Moner-Bondhu.", P["text"]),
        ("", None),
        ("Most of what I know came from building the thing", P["muted"]),
        ("badly first, then figuring out why it was bad.", P["muted"]),
        ("My time splits between full-stack web and Python.", P["muted"]),
        ("When something feels like magic, I rebuild it by", P["muted"]),
        ("hand until it doesn't. Autograd engines included.", P["muted"]),
        ("", None),
        ("Ship small things that work > plan big things that don't.", P["lime"]),
    ]
    ph = 38 + (len(lines) - 1) * 22 + 28
    h = top + ph + 24
    b += panel(MARGIN, top, INNER, ph, accent=P["lime"])
    colw = INNER - 26 - 250
    for text, color in lines:
        if text:
            check_text(x, text, 13, MARGIN + 26 + colw, "about/copy")
            b.append(mono(x, y, text, 13, color))
        y += 22

    # key/value column on the right
    kx = MARGIN + INNER - 250
    b.append(f'<rect x="{kx - 26}" y="{top + 20}" width="1" height="{ph - 40}" fill="{P["border"]}"/>')
    ky = top + 38
    for k, v in [("location", "Dhaka, BD"), ("role", "software dev"), ("company", "@Moner-Bondhu"),
                 ("study", "CSE @ UIU"), ("focus", "web + ML"), ("status", "open to work")]:
        b.append(mono(kx, ky, k, 12, P["muted"]))
        b.append(mono(kx + 78, ky, v, 12, P["lime"], 500))
        check_text(kx + 78, v, 12, W - MARGIN - 12, "about/kv")
        ky += 26
    check_bottom(max(y, ky) - 22 + 12, top + ph, "about")
    return svg("about.svg", h, b)


JOURNEY = [
    {
        "period": ["JUN 2025", "now"],
        "title": "Software Developer",
        "org": "@ Moner Bondhu",
        "desc": "Laravel + Vue product work, and the Docker/Linux plumbing that ships it.",
        "color": P["lime"],
        "live": True,
    },
    {
        "period": ["2023", "now"],
        "title": "BSc, Computer Science & Engineering",
        "org": "@ United International University",
        "desc": "9th trimester. Player Koi and ScrollSense both started as lab projects here.",
        "color": P["yellow"],
        "live": True,
    },
]


def build_journey():
    b = section_head(2, "journey")
    top, step = 60, 92
    ph = 24 + len(JOURNEY) * step
    h = top + ph + 24
    b += panel(MARGIN, top, INNER, ph, accent=P["yellow"])

    px = MARGIN + 26                 # period column
    lx = MARGIN + 150                # the timeline rail
    cx = lx + 28                     # content column
    limit = MARGIN + INNER - 24
    b.append(f'<rect x="{lx}" y="{top + 30}" width="1" height="{ph - 60}" fill="{P["border"]}"/>')

    y = top + 40
    for e in JOURNEY:
        b.append(mono(px, y, e["period"][0], 12, e["color"], 700, tracking=1))
        b.append(mono(px, y + 20, "→ " + e["period"][1], 12, P["muted"]))
        # node on the rail; a live entry gets a slow ping ring
        b.append(f'<g shape-rendering="geometricPrecision">'
                 f'<circle cx="{lx + 0.5}" cy="{y - 5}" r="5" fill="{P["panel"]}" stroke="{e["color"]}" stroke-width="2"/>')
        if e["live"]:
            b.append(f'<circle cx="{lx + 0.5}" cy="{y - 5}" r="5" fill="none" stroke="{e["color"]}" stroke-width="1">'
                     f'<animate attributeName="r" values="5;13" dur="2.4s" repeatCount="indefinite"/>'
                     f'<animate attributeName="opacity" values="0.8;0" dur="2.4s" repeatCount="indefinite"/></circle>')
        b.append('</g>')
        b.append(mono(cx, y, e["title"], 15, P["text"], 700))
        check_text(cx, e["title"], 15, limit, "journey/title")
        b.append(mono(cx, y + 22, e["org"], 13, e["color"], 500))
        check_text(cx, e["org"], 13, limit, "journey/org")
        b.append(mono(cx, y + 44, e["desc"], 12, P["muted"]))
        check_text(cx, e["desc"], 12, limit, "journey/desc")
        y += step
    check_bottom(y - step + 44 + 12, top + ph, "journey")
    return svg("journey.svg", h, b)


def build_now():
    b = section_head(3, "currently")
    rows = [
        ("reading", "ML research papers, one at a time, notes on everything"),
        ("writing", "working toward my first ML research paper"),
        ("shipped", "Player Koi + ScrollSense, both written up on the blog"),
        ("building", "web products at Moner Bondhu, Laravel + Vue"),
    ]
    top = 60
    ph = 40 + (len(rows) - 1) * 30 + 28
    h = top + ph + 24
    b += panel(MARGIN, top, INNER, ph, accent=P["yellow"])
    x, y = MARGIN + 26, top + 40
    for k, v in rows:
        b.append(mono(x, y, "$", 13, P["lime"], 500))
        b.append(mono(x + 18, y, k, 13, P["yellow"], 500))
        b.append(mono(x + 18 + 84, y, v, 13, P["text"] if k == "writing" else P["muted"]))
        check_text(x + 18 + 84, v, 13, W - MARGIN - 20, "now/row")
        if k == "writing":
            # the thing in progress gets the live cursor
            b.append(cursor(x + 18 + 84 + tw(v, 13) + 6, y, 13))
        y += 30
    check_bottom(y - 30 + 12, top + ph, "now")
    return svg("now.svg", h, b)


GROUPS = [
    ("LANGUAGES",      ["Python", "TypeScript", "JavaScript", "PHP", "C", "C++", "Java", "SQL", "Bash"]),
    ("AI / ML",        ["PyTorch", "Transformers", "NumPy", "Pandas", "scikit-learn", "OpenCV", "Jupyter"]),
    ("FRONTEND",       ["SvelteKit", "React", "Vue", "Nuxt", "Next.js", "Tailwind"]),
    ("BACKEND",        ["Laravel", "Filament", "FastAPI", "Django", "Flask"]),
    ("HARDWARE",       ["Raspberry Pi", "Arduino", "Android"]),
    ("DEVOPS / CLOUD", ["Docker", "AWS", "Cloudflare", "Actions", "Linux", "Git"]),
]


def build_skills():
    b = section_head(4, "toolbox")
    top = 60
    cw = (INNER - GUTTER) / 2          # two columns
    pad = 20
    maxw = cw - pad * 2

    # measure every group first so both columns can share a row height
    heights = []
    for _, items in GROUPS:
        rows = len(chip_rows(items, maxw))
        heights.append(38 + rows * 31 + 12)

    y, i, ys = top, 0, []
    while i < len(GROUPS):
        rh = max(heights[i], heights[i + 1]) if i + 1 < len(GROUPS) else heights[i]
        ys.append((y, rh))
        y += rh + GUTTER
        i += 2

    h = int(y - GUTTER + 24)
    for idx, (title, items) in enumerate(GROUPS):
        col, row = idx % 2, idx // 2
        px = MARGIN + col * (cw + GUTTER)
        py, ph = ys[row]
        accent = P["lime"] if idx % 2 == 0 else P["yellow"]
        b += panel(px, py, cw, ph, accent=accent)
        b.append(mono(px + pad, py + 26, title, 12, accent, 700, tracking=1.6))
        b.append(mono(px + cw - pad, py + 26, f"{len(items):02d}", 12, P["border"], 700, anchor="end"))
        parts, _ = draw_chips(px + pad, py + 40, items, maxw)
        b += parts
    return svg("skills.svg", h, b)


PROJECTS = [
    {
        "name": "Player Koi",
        "tag": "MICROCONTROLLERS LAB",
        "repo": "github.com/TheRealNightmare/PlayerKoi",
        "desc": ["A chessboard that sees, thinks and moves its own pieces. A camera on a Raspberry",
                 "Pi 5 reads your move, Stockfish answers, a magnet under the board slides the reply."],
        "tech": ["Raspberry Pi 5", "Computer vision", "YOLOv8", "python-chess", "Stockfish", "Arduino"],
        "accent": P["lime"],
    },
    {
        "name": "ScrollSense",
        "tag": "AI LAB",
        "repo": "github.com/TheRealNightmare/ScrollSense",
        "desc": ["Scores the mood of your feed. A Chrome extension captures what you scroll past,",
                 "a fine-tuned XLM-RoBERTa reads code-mixed Bengali-English, a dashboard charts it."],
        "tech": ["PyTorch", "XLM-RoBERTa", "Chrome extension", "JWT", "Dashboard"],
        "accent": P["yellow"],
    },
    {
        "name": "Verso 2.0",
        "tag": "FULL-STACK",
        "repo": "github.com/TheRealNightmare/Verso2.0",
        "desc": ["A digital library. Read EPUB and PDF in the browser, join collaborative reading",
                 "rooms, get AI recommendations, and moderate it all from a Filament admin panel."],
        "tech": ["React 19", "Laravel 13", "PHP 8.3", "Filament", "Tailwind"],
        "accent": P["lime"],
    },
]

ALSO_BUILT = ["Ray Tracing · C + SDL2", "micrograd · autograd by hand", "Laravel Microservices"]


def build_projects():
    b = section_head(5, "featured")
    y = 60
    pad = 24
    maxw = INNER - pad * 2
    for pr in PROJECTS:
        rows = len(chip_rows(pr["tech"], maxw))
        ph = 34 + len(pr["desc"]) * 21 + 14 + rows * 31 + 18
        b += panel(MARGIN, y, INNER, ph, accent=pr["accent"])
        x = MARGIN + pad
        b.append(mono(x, y + 30, pr["name"], 16, pr["accent"], 700, tracking=0.6))
        tx = x + tw(pr["name"], 16, 0.6) + 14
        tagw, parts = pill(tx, y + 15, pr["tag"], P["muted"])
        b += parts
        rx = MARGIN + INNER - pad
        b.append(mono(rx, y + 30, pr["repo"], 11, P["muted"], anchor="end"))
        if tx + tagw + 16 > rx - tw(pr["repo"], 11):
            fail(f"projects/head: tag runs into repo path for {pr['name']}")
        ty = y + 56
        for line in pr["desc"]:
            check_text(x, line, 12.5, MARGIN + INNER - pad, "projects/desc")
            b.append(mono(x, ty, line, 12.5, P["text"]))
            ty += 21
        parts, _ = draw_chips(x, ty + 6, pr["tech"], maxw, color=P["muted"])
        b += parts
        y += ph + GUTTER

    # smaller things worth knowing about, on one strip
    ph = 52
    b += panel(MARGIN, y, INNER, ph)
    x = MARGIN + pad
    b.append(mono(x, y + 31, "ALSO BUILT", 12, P["yellow"], 700, tracking=1.6))
    cx = x + tw("ALSO BUILT", 12, 1.6) + 18
    parts, _ = draw_chips(cx, y + 14, ALSO_BUILT, MARGIN + INNER - pad - cx, color=P["text"])
    if len(chip_rows(ALSO_BUILT, MARGIN + INNER - pad - cx)) > 1:
        fail("projects/also: chips wrap onto a second row")
    b += parts
    y += ph + GUTTER
    return svg("projects.svg", int(y - GUTTER + 24), b)


def build_contact():
    b = section_head(8, "get in touch")
    rows = [("email", "nnahid929@gmail.com"),
            ("site", "mirazulislamnahid.com"),
            ("blog", "mirazulislamnahid.com/blog"),
            ("linkedin", "linkedin.com/in/therealnightmare"),
            ("x", "x.com/nightMARE496"),
            ("where", "Dhaka, Bangladesh · UTC+6")]
    top = 60
    ph = 40 + len(rows) * 28 + 34
    h = top + ph + 24
    b += panel(MARGIN, top, INNER, ph, accent=P["lime"])
    x, y = MARGIN + 26, top + 40
    for k, v in rows:
        b.append(mono(x, y, "$", 13, P["lime"], 500))
        b.append(mono(x + 18, y, k, 13, P["yellow"], 500))
        b.append(mono(x + 18 + 84, y, v, 13, P["text"]))
        check_text(x + 18 + 84, v, 13, W - MARGIN - 20, "contact/row")
        y += 28
    note = "// open to work, collaboration and interesting problems"
    b.append(mono(x, y + 10, note, 12, P["muted"]))
    b.append(cursor(x + tw(note, 12) + 6, y + 10, 12))
    check_bottom(y + 10 + 10, top + ph, "contact")
    return svg("contact.svg", h, b)


def build_rule():
    h = 16
    b = [f'<rect x="{MARGIN}" y="8" width="{INNER}" height="1" fill="{P["border"]}"/>',
         f'<rect x="{MARGIN}" y="8" width="90" height="1" fill="{P["lime"]}"/>',
         f'<rect x="{MARGIN + 90}" y="8" width="24" height="1" fill="{P["yellow"]}"/>']
    return svg("rule.svg", h, b)


def build_blog_head():
    b = section_head(6, "latest writing")
    return svg("blog.svg", 60, b)


def build_stats_head():
    b = section_head(7, "the numbers")
    return svg("stats.svg", 60, b)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print("building assets:")
    build_hero()
    build_about()
    build_journey()
    build_now()
    build_skills()
    build_projects()
    build_blog_head()
    build_stats_head()
    build_contact()
    build_rule()
    if _errors:
        print("\nOVERFLOW ERRORS:", file=sys.stderr)
        for e in _errors:
            print("  -", e, file=sys.stderr)
        sys.exit(1)
    print("\nall panels fit.")
