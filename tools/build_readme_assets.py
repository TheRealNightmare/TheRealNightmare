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
    b.append(mono(x, 118, "$ whoami", 14, P["lime"], 500))

    name, nsize, ntrack = "MIRAZUL ISLAM NAHID", 38, 1.5
    check_clear(x, name, nsize, gutter, "hero/name", ntrack)
    b.append(mono(x, 170, name, nsize, P["text"], 700, tracking=ntrack))

    role = "full-stack developer · machine learning · always shipping"
    check_clear(x, role, 14, gutter, "hero/role")
    b.append(mono(x, 200, role, 14, P["muted"]))

    meta = "Dhaka, Bangladesh · @Moner-Bondhu · github.com/TheRealNightmare"
    check_clear(x, meta, 12, gutter, "hero/meta")
    b.append(mono(x, 236, meta, 12, P["muted"]))

    # prompt + cursor
    b.append(mono(x, 262, "$", 14, P["lime"], 500))
    b.append(f'<rect x="{x + 16}" y="{262 - 11}" width="9" height="14" fill="{P["lime"]}"/>')
    return svg("hero.svg", h, b)


def build_about():
    h = 308
    b = section_head(1, "whoami")
    top, ph = 60, h - 60 - 24
    b += panel(MARGIN, top, INNER, ph, accent=P["lime"])

    x, y = MARGIN + 26, top + 38
    lines = [
        ("Full-stack developer based in Dhaka, Bangladesh.", P["text"]),
        ("Currently building at @Moner-Bondhu.", P["text"]),
        ("", None),
        ("I build web platforms end to end — Laravel and React", P["muted"]),
        ("on the front, Python and PyTorch when a problem needs", P["muted"]),
        ("a model instead of an if-statement.", P["muted"]),
        ("", None),
        ("Always exploring, always learning, building things as I grow.", P["lime"]),
    ]
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
    for k, v in [("location", "Dhaka, BD"), ("company", "@Moner-Bondhu"),
                 ("focus", "web + ML"), ("since", "2021"), ("status", "always learning")]:
        b.append(mono(kx, ky, k, 12, P["muted"]))
        b.append(mono(kx + 78, ky, v, 12, P["lime"], 500))
        check_text(kx + 78, v, 12, W - MARGIN - 12, "about/kv")
        ky += 26
    check_bottom(max(y, ky) - 22 + 12, top + ph, "about")
    return svg("about.svg", h, b)


def build_now():
    h = 208
    b = section_head(2, "currently")
    top, ph = 60, h - 60 - 24
    b += panel(MARGIN, top, INNER, ph, accent=P["yellow"])
    x, y = MARGIN + 26, top + 40
    rows = [
        ("learning", "built micrograd from scratch — autograd, backprop, the lot"),
        ("training", "working through PyTorch and transformer fine-tuning"),
        ("next", "shipping models into the apps I already build"),
    ]
    for k, v in rows:
        b.append(mono(x, y, "$", 13, P["lime"], 500))
        b.append(mono(x + 18, y, k, 13, P["yellow"], 500))
        b.append(mono(x + 18 + 84, y, v, 13, P["muted"]))
        check_text(x + 18 + 84, v, 13, W - MARGIN - 20, "now/row")
        y += 30
    check_bottom(y - 30 + 12, top + ph, "now")
    return svg("now.svg", h, b)


GROUPS = [
    ("LANGUAGES",    ["C", "C++", "PHP", "Java", "Python", "JavaScript", "TypeScript", "Bash"]),
    ("AI / ML",      ["PyTorch", "NumPy", "Pandas", "scikit-learn", "Jupyter"]),
    ("FRONTEND",     ["React", "Vue", "Nuxt", "Next.js", "Tailwind"]),
    ("BACKEND",      ["Laravel", "Django", "Flask", "FastAPI"]),
    ("MOBILE / EMBED", ["Android", "Arduino"]),
    ("DEVOPS / CLOUD", ["AWS", "Docker", "K8s", "Actions", "Git", "Linux"]),
]


def build_skills():
    b = section_head(3, "toolbox")
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
        parts, _ = draw_chips(px + pad, py + 40, items, maxw)
        b += parts
    return svg("skills.svg", h, b)


PROJECTS = [
    {
        "name": "Verso 2.0",
        "repo": "github.com/TheRealNightmare/Verso2.0",
        "desc": ["Online book-reading and digital library platform. Read EPUB and PDF in the",
                 "browser, read together in collaborative rooms, get AI-powered recommendations."],
        "tech": ["React 19", "Laravel 13", "PHP 8.3", "Filament", "Vite", "Tailwind"],
    },
    {
        "name": "ScrollSense",
        "repo": "github.com/TheRealNightmare/ScrollSense",
        "desc": ["Reads the sentiment of your social feed. A browser extension captures the posts",
                 "you scroll past, a fine-tuned transformer scores each one, a dashboard charts it."],
        "tech": ["JavaScript", "Transformers", "JWT", "Extension", "Dashboard"],
    },
]


def build_projects():
    b = section_head(4, "featured")
    y = 60
    pad = 24
    maxw = INNER - pad * 2
    for pr in PROJECTS:
        rows = len(chip_rows(pr["tech"], maxw))
        ph = 34 + len(pr["desc"]) * 21 + 14 + rows * 31 + 18
        b += panel(MARGIN, y, INNER, ph, accent=P["lime"])
        x = MARGIN + pad
        b.append(mono(x, y + 30, pr["name"], 16, P["lime"], 700, tracking=0.6))
        rx = MARGIN + INNER - pad
        b.append(mono(rx, y + 30, pr["repo"], 11, P["muted"], anchor="end"))
        ty = y + 56
        for line in pr["desc"]:
            check_text(x, line, 12.5, MARGIN + INNER - pad, "projects/desc")
            b.append(mono(x, ty, line, 12.5, P["text"]))
            ty += 21
        parts, _ = draw_chips(x, ty + 6, pr["tech"], maxw, color=P["muted"])
        b += parts
        y += ph + GUTTER
    return svg("projects.svg", int(y - GUTTER + 24), b)


def build_contact():
    h = 264
    b = section_head(7, "get in touch")
    top, ph = 60, h - 60 - 24
    b += panel(MARGIN, top, INNER, ph, accent=P["lime"])
    x, y = MARGIN + 26, top + 40
    for k, v in [("email", "nnahid929@gmail.com"),
                 ("site", "mirazulislamnahid.com"),
                 ("blog", "therealnightmare.github.io"),
                 ("where", "Dhaka, Bangladesh")]:
        b.append(mono(x, y, "$", 13, P["lime"], 500))
        b.append(mono(x + 18, y, k, 13, P["yellow"], 500))
        b.append(mono(x + 18 + 68, y, v, 13, P["text"]))
        check_text(x + 18 + 68, v, 13, W - MARGIN - 20, "contact/row")
        y += 28
    b.append(mono(x, y + 10, "// open to collaboration and interesting problems", 12, P["muted"]))
    check_bottom(y + 10 + 10, top + ph, "contact")
    return svg("contact.svg", h, b)


def build_rule():
    h = 16
    b = [f'<rect x="{MARGIN}" y="8" width="{INNER}" height="1" fill="{P["border"]}"/>',
         f'<rect x="{MARGIN}" y="8" width="90" height="1" fill="{P["lime"]}"/>']
    return svg("rule.svg", h, b)


def build_blog_head():
    b = section_head(5, "latest writing")
    return svg("blog.svg", 60, b)


def build_stats_head():
    b = section_head(6, "the numbers")
    return svg("stats.svg", 60, b)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print("building assets:")
    build_hero()
    build_about()
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
