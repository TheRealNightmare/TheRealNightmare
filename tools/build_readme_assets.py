#!/usr/bin/env python3
"""Build every SVG for the profile README, in two themes, then write README.md.

The README is a retro RPG: a title screen, an NPC dialogue, a world map, a quest
list, an inventory, legendary items, a quest log, a character sheet and a
CONTINUE? screen. Sprites are pixel grids (tools/rpg/sprites.py) set inside clean
vector windows (tools/rpg/pixel.py).

Each panel is built once per theme into assets/dark/ and assets/light/, and the
README picks between them with <picture> + prefers-color-scheme, which follows
the viewer's GitHub theme. Nothing here is hand-tweaked: edit this file and
re-run it. The build fails loudly if any text would overflow its window.

    python3 tools/fetch_stats.py        # optional: refresh tools/stats.json
    python3 tools/build_readme_assets.py
"""
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rpg import sprites as S                    # noqa: E402
from rpg.palette import THEMES                  # noqa: E402
from rpg.pixel import (B, blink, bar, notched, ptext, sprite, sprite_size,  # noqa: E402
                       text_h, text_w, window)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
ASSETS = os.path.join(ROOT, "assets")

# --------------------------------------------------------------------------
# grid
# --------------------------------------------------------------------------
W = 880          # canvas width, matches GitHub's readable column
X0 = 14          # window left edge
WW = 848         # window width; the 4px hard shadow ends at 866
PAD = 24         # window inner padding
L = X0 + PAD     # content left
R = X0 + WW - PAD  # content right
TOP = 22         # window top, leaving room for the title tab above it

MONO = "'JetBrains Mono','Fira Code','SFMono-Regular',Consolas,'Courier New',monospace"
ADVANCE = 0.6    # mono advance as a fraction of font-size

P = THEMES[0]    # the theme being built; rebound for each pass in main()
_errors = []


def fail(msg):
    if msg not in _errors:
        _errors.append(msg)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tw(text, size, tracking=0.0):
    """Estimated rendered width of a mono string."""
    return len(text) * (size * ADVANCE + tracking)


def mono(x, y, text, size=13, color=None, weight=400, anchor="start", tracking=0.0, extra=""):
    if "  " in text:
        # SVG collapses runs of whitespace; position columns with x, never spaces
        fail(f"run of spaces will collapse when rendered: {text!r}")
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    t = f' letter-spacing="{tracking}"' if tracking else ""
    return (f'<text x="{x:g}" y="{y:g}"{a} font-family="{MONO}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color or P["text"]}"{t}{extra}>{esc(text)}</text>')


def check_text(x, text, size, limit, where, tracking=0.0):
    end = x + tw(text, size, tracking)
    if end > limit + 0.5:
        fail(f"{where}: text overflows ({end:.0f} > {limit:g}): {text!r}")


def check_px(x, text, scale, limit, where):
    end = x + text_w(text.upper(), scale)
    if end > limit + 0.5:
        fail(f"{where}: pixel text overflows ({end:.0f} > {limit:g}): {text!r}")


def check_bottom(y, limit, where):
    if y > limit + 0.5:
        fail(f"{where}: content runs past the window bottom ({y:.0f} > {limit:g})")


def fit(text, size, maxw, floor=11):
    """Largest size (down to `floor`, in 0.5 steps) at which text fits maxw."""
    while size > floor and tw(text, size) > maxw:
        size -= 0.5
    return size


def wrap(text, size, maxw):
    """Greedy word wrap on estimated mono widths."""
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}" if cur else word
        if tw(trial, size) <= maxw:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def svg(name, h, body, w=W, defs=None):
    """Write one theme's copy. The canvas stays transparent: windows carry their
    own fill and the GitHub page shows through around them."""
    doc = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}" width="{w:g}" '
           f'height="{h:g}" shape-rendering="crispEdges">']
    if defs:
        doc += ["  <defs>"] + ["    " + d for d in defs] + ["  </defs>"]
    doc += ["  " + line for line in body if line]
    doc.append("</svg>")
    path = os.path.join(ASSETS, P["name"], name)
    with open(path, "w") as f:
        f.write("\n".join(doc) + "\n")
    if P is THEMES[0]:
        print(f"  {name:<22} {w:g}x{h:g}")


def inset(x, y, w, h, fill=None, stroke=None):
    """A sunken well inside a window: slots, map, portrait frames."""
    return (f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{fill or P["inset"]}" '
            f'stroke="{stroke or P["frame_dim"]}" stroke-width="2"/>')


def tag(x, y, label, color, size=10.5, pad=7, h=20, anchor="start"):
    """Outlined status tag. Returns (width, parts)."""
    w = tw(label, size, 0.8) + pad * 2
    if anchor == "end":
        x -= w
    return w, [f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h}" fill="none" '
               f'stroke="{color}" stroke-width="1.5"/>',
               mono(x + w / 2, y + h / 2 + 3.8, label, size, color, 700, anchor="middle", tracking=0.8)]


def stars(x, y, w, h, n, seed, color=None):
    """Twinkling 2px stars scattered (deterministically) over a sky region."""
    out = []
    for i in range(n):
        sx = x + (seed * 37 + i * 53) % int(w)
        sy = y + (seed * 17 + i * 29) % int(h)
        dur = 2 + (i % 4) * 0.7
        out.append(f'<rect x="{sx}" y="{sy}" width="2" height="2" fill="{color or P["muted"]}">'
                   f'<animate attributeName="opacity" values="1;0.2;1" dur="{dur:g}s" '
                   f'begin="{(i * 0.37) % 2:.2f}s" repeatCount="indefinite"/></rect>')
    return out


# --------------------------------------------------------------------------
# content
# --------------------------------------------------------------------------
NAME = "MIRAZUL ISLAM NAHID"

DIALOGUE = [
    "always exploring, always learning",
    "reading papers, writing my first one",
    "laravel + vue by day",
    "pytorch when curiosity wins",
    "building things as I grow",
    "open to collab: projects to research papers",
]

ABOUT = [
    ("Software developer based in Dhaka, Bangladesh.", "text"),
    ("Building web products at @Moner-Bondhu.", "text"),
    ("", None),
    ("Most of what I know came from building the thing", "muted"),
    ("badly first, then figuring out why it was bad.", "muted"),
    ("My time splits between full-stack web and Python.", "muted"),
    ("When something feels like magic, I rebuild it by", "muted"),
    ("hand until it doesn't. Autograd engines included.", "muted"),
    ("", None),
    ("Ship small things that work > plan big things that don't.", "accent"),
]
ABOUT_KV = [("location", "Dhaka, BD"), ("role", "software dev"), ("company", "@Moner-Bondhu"),
            ("study", "CSE @ UIU"), ("focus", "web + ML"), ("status", "open to collab")]

JOURNEY = [
    {"when": "2023", "title": "BSc, Computer Science & Engineering",
     "org": "@ United International University",
     "desc": "9th trimester. Player Koi and ScrollSense both started as lab projects here.",
     "color": "accent2", "state": "visited"},
    {"when": "JUN 2025", "title": "Software Developer", "org": "@ Moner Bondhu",
     "desc": "Laravel + Vue product work, and the Docker/Linux plumbing that ships it.",
     "color": "accent", "state": "here"},
    {"when": "NEXT", "title": "First research paper", "org": "@ ???",
     "desc": "The next area on the map. Not drawn yet, but the path is already heading there.",
     "color": "muted", "state": "fog"},
]

QUESTS = [
    ("MAIN", "accent2", "Write my first research paper", "reading, experimenting, drafting", False),
    ("SIDE", "mp", "Read research papers", "one at a time, notes on everything", False),
    ("DAILY", "accent", "Build web products at Moner Bondhu", "Laravel + Vue, plus the plumbing that ships it", False),
    ("CLEAR", "muted", "Ship Player Koi + ScrollSense", "both written up on the blog", True),
]

GROUPS = [
    ("LANGUAGES", "scroll", ["Python", "TypeScript", "JavaScript", "PHP", "C", "C++", "Java", "SQL", "Bash"]),
    ("AI / ML", "potion", ["PyTorch", "Transformers", "NumPy", "Pandas", "scikit-learn", "OpenCV", "Jupyter"]),
    ("FRONTEND", "gem", ["SvelteKit", "React", "Vue", "Nuxt", "Next.js", "Tailwind"]),
    ("BACKEND", "sword", ["Laravel", "Filament", "FastAPI", "Django", "Flask", "Node.js"]),
    ("HARDWARE", "chip", ["Raspberry Pi", "Arduino", "ESP32", "Android"]),
    ("DEVOPS / CLOUD", "cloud", ["Docker", "AWS", "Cloudflare", "Kubernetes", "Actions", "Linux", "Git"]),
]
ICONS = {"scroll": S.SCROLL, "potion": S.POTION, "gem": S.GEM, "sword": S.SWORD,
         "chip": S.CHIP, "cloud": S.CLOUD}

PROJECTS = [
    {"name": "Player Koi", "rarity": "LEGENDARY", "color": "accent2", "fill": "gold_fill",
     "kind": "MICROCONTROLLERS LAB", "icon": S.PAWN,
     "repo": "github.com/TheRealNightmare/PlayerKoi",
     "desc": "A chessboard that sees, thinks and moves its own pieces. A camera on a Raspberry "
             "Pi 5 reads your move, Stockfish answers, a magnet under the board slides the reply.",
     "tech": ["Raspberry Pi 5", "Computer vision", "YOLOv8", "python-chess", "Stockfish", "Arduino"]},
    {"name": "ScrollSense", "rarity": "EPIC", "color": "rare", "fill": "rare_fill",
     "kind": "AI LAB", "icon": S.EYE,
     "repo": "github.com/TheRealNightmare/ScrollSense",
     "desc": "Scores the mood of your feed. A Chrome extension captures what you scroll past, "
             "a fine-tuned XLM-RoBERTa reads code-mixed Bengali-English, a dashboard charts it.",
     "tech": ["PyTorch", "XLM-RoBERTa", "Chrome extension", "JWT", "Dashboard"]},
    {"name": "Verso 2.0", "rarity": "RARE", "color": "mp", "fill": "mp_fill",
     "kind": "FULL-STACK", "icon": S.BOOK,
     "repo": "github.com/TheRealNightmare/Verso2.0",
     "desc": "A digital library. Read EPUB and PDF in the browser, join collaborative reading "
             "rooms, get AI recommendations, and moderate it all from a Filament admin panel.",
     "tech": ["React 19", "Laravel 13", "PHP 8.3", "Filament", "Tailwind"]},
]
STASH = ["Ray Tracing · C + SDL2", "micrograd · autograd by hand", "Laravel Microservices"]

CONTACT = [("EMAIL", "nnahid929@gmail.com"), ("SITE", "mirazulislamnahid.com"),
           ("BLOG", "mirazulislamnahid.com/blog"), ("LINKEDIN", "in/therealnightmare"),
           ("X", "@nightMARE496"), ("REALM", "Dhaka, BD · UTC+6")]

# small pixel buttons: (file, label, style)
BUTTONS = [
    ("btn-website", "WEBSITE", "accent"), ("btn-blog", "BLOG", "accent"),
    ("btn-resume", "RESUME", "accent"), ("btn-linkedin", "LINKEDIN", "gold"),
    ("btn-x", "X", "gold"), ("btn-email", "EMAIL", "gold"),
    ("btn-playerkoi", "PLAYER KOI", "gold"), ("btn-scrollsense", "SCROLLSENSE", "rare"),
    ("btn-verso", "VERSO 2.0", "mp"), ("btn-writeup", "WRITE-UP", "plain"),
    ("btn-projects", "ALL PROJECTS ▶", "plain"), ("btn-readmore", "READ MORE ▶", "accent"),
]

DEFAULT_STATS = {"contributions_year": 0, "contributions_total": 0, "streak_current": 0,
                 "streak_longest": 0, "stars": 0, "repos": 0, "followers": 0, "since": 2021,
                 "languages": []}


def load_stats():
    try:
        with open(os.path.join(TOOLS, "stats.json")) as f:
            return {**DEFAULT_STATS, **json.load(f)}
    except FileNotFoundError:
        print("  (no tools/stats.json; character sheet uses zeros)")
        return dict(DEFAULT_STATS)


def level(total):
    """LV from lifetime contributions: each level costs a little more than the last."""
    lv = int(math.sqrt(max(total, 0) / 5))
    lo, hi = 5 * lv * lv, 5 * (lv + 1) ** 2
    return max(lv, 1), (total - lo) / (hi - lo), hi


# --------------------------------------------------------------------------
# panels
# --------------------------------------------------------------------------
def mage(x, y, scale, bob=True, eyes=True):
    """The player sprite, with a stepped idle bob, blinking eyes and a pulsing gem."""
    out = sprite(S.MAGE, x, y, scale, S.MAGE_KEYS, P)
    if eyes:
        # cover each eye with face color for a few frames every 4s
        for col in (9, 12):
            out.append(f'<rect x="{x + col * scale}" y="{y + 8 * scale}" width="{scale}" height="{scale}" '
                       f'fill="{P["face"]}" opacity="0"><animate attributeName="opacity" values="0;1;0" '
                       f'keyTimes="0;0.92;0.96" dur="4s" calcMode="discrete" repeatCount="indefinite"/></rect>')
    # gem halo: a pixel cross around the gem that breathes
    gx, gy = x + 20 * scale, y + 3 * scale
    halo = (f'M{gx - 2 * scale} {gy}h{6 * scale}v{2 * scale}h{-6 * scale}z'
            f'M{gx} {gy - 2 * scale}h{2 * scale}v{6 * scale}h{-2 * scale}z')
    out.insert(0, f'<path d="{halo}" fill="{P["glow"]}" opacity="0.15">'
                  f'<animate attributeName="opacity" values="0.05;0.35;0.05" dur="2.4s" '
                  f'repeatCount="indefinite"/></path>')
    if bob:
        out = ([f'<g><animateTransform attributeName="transform" type="translate" '
                f'values="0 0;0 {-scale}" dur="1.6s" calcMode="discrete" repeatCount="indefinite"/>']
               + out + ["</g>"])
    return out


def sparks(cx, cy, n=4, rise=46):
    """Pixel motes floating up from (cx, cy) and fading out."""
    out = []
    for i in range(n):
        dx = (-10, 6, -3, 11, -7)[i % 5]
        size = 3 if i % 2 else 4
        out.append(f'<rect x="{cx + dx}" y="{cy}" width="{size}" height="{size}" fill="{P["glow"]}" opacity="0">'
                   f'<animate attributeName="y" values="{cy};{cy - rise}" dur="2.6s" begin="{i * 0.65:g}s" '
                   f'repeatCount="indefinite"/>'
                   f'<animate attributeName="opacity" values="0;0.9;0" dur="2.6s" begin="{i * 0.65:g}s" '
                   f'repeatCount="indefinite"/></rect>')
    return out


def typewriter(x, y, lines, size, color, slot=3.6, cps=22):
    """Rotate through `lines`, typing each one out, the way NPC dialogue appears."""
    total = slot * len(lines)
    defs, body = [], []
    for i, line in enumerate(lines):
        cid = f"tw{i}-{P['name']}"
        start = i * slot
        full = tw(line, size) + 4
        n = len(line)
        times, widths = [0.0], [0]
        for k in range(1, n + 1):
            times.append((start + k / cps) / total)
            widths.append(round(full * k / n, 1))
        times.append((start + slot) / total)
        widths.append(0)
        if times[1] == 0:
            times[1] = 0.0001
        kt = ";".join(f"{t:.4f}" for t in times)
        vals = ";".join(f"{w:g}" for w in widths)
        defs.append(f'<clipPath id="{cid}"><rect x="{x}" y="{y - size}" height="{size * 1.5:g}" width="0">'
                    f'<animate attributeName="width" values="{vals}" keyTimes="{kt}" dur="{total:g}s" '
                    f'calcMode="discrete" repeatCount="indefinite"/></rect></clipPath>')
        body.append(f'<g clip-path="url(#{cid})">{mono(x, y, line, size, color, 500)}</g>')
    return defs, body


def build_hero(st):
    h = 318
    b = window(X0, 14, WW, h - 22, P)
    # left: night scene with the mage
    sx, sy, sw, shh = L - 4, 34, 244, h - 22 - 40
    b.append(inset(sx, sy, sw, shh, P["sky"], P["frame_dim"]))
    b += stars(sx + 8, sy + 8, sw - 16, 90, 14, 3, P["star"])
    # crescent moon
    mx, my = sx + 26, sy + 22
    b.append(f'<path d="M{mx} {my}h12v4h4v12h-4v4h-12v-4h4v-4h4v-4h-4v-4h-4z" fill="{P["gold_fill"]}"/>')
    # ground: a grass edge over dirt
    gy = sy + shh - 22
    b.append(f'<rect x="{sx + 1}" y="{gy}" width="{sw - 2}" height="21" fill="{P["dirt"]}"/>')
    b.append(f'<rect x="{sx + 1}" y="{gy}" width="{sw - 2}" height="4" fill="{P["accent_fill"]}"/>')
    for gx in range(sx + 6, sx + sw - 6, 14):
        b.append(f'<rect x="{gx}" y="{gy - 4}" width="4" height="4" fill="{P["accent_fill"]}"/>')
    scale = 7
    mw, mh = sprite_size(S.MAGE, scale)
    mx0 = sx + (sw - mw) // 2
    b += mage(mx0, gy - mh + scale, scale)
    b += sparks(mx0 + 20 * scale, sy + 50)

    # right: the title card
    x = sx + sw + 30
    b.append(ptext(x, 38, "PLAYER 1", 2, P["accent2"]))
    status = "★ OPEN FOR COLLABORATION"
    b.append(f'<g>{ptext(R, 38, status, 2, P["accent"], anchor="end")}'
             f'<animate attributeName="opacity" values="1;1;0.35;1" keyTimes="0;0.6;0.8;1" dur="2s" '
             f'repeatCount="indefinite"/></g>')
    check_px(x, NAME, 4, R, "hero/name")
    b.append(ptext(x, 66, NAME, 4, P["text"]))
    lv, _, _ = level(st["contributions_total"])
    rows = [("CLASS", "Software Developer · web + ML"),
            ("GUILD", "@Moner-Bondhu · CSE @ UIU"),
            ("REALM", "Dhaka, Bangladesh"),
            ("LEVEL", f"LV {lv} · playing since {st['since']}")]
    y = 118
    for k, v in rows:
        b.append(ptext(x, y - 10, k, 1.5, P["muted"]))
        b.append(mono(x + 64, y, v, 13, P["text"]))
        check_text(x + 64, v, 13, R, "hero/row")
        y += 24
    # dialogue box with the rotating lines
    dy, dh = 210, 50
    b.append(inset(x, dy, R - x, dh, P["window"], P["frame"]))
    b.append(ptext(x + 14, dy + 19, "▶", 2, P["accent"]))
    defs, lines = typewriter(x + 36, dy + 31, DIALOGUE, 14, P["accent"])
    for line in DIALOGUE:
        check_text(x + 36, line, 14, R - 30, "hero/dialogue")
    b += lines
    b.append(f'<g>{ptext(R - 20, dy + dh - 16, "▼", 1.5, P["text"])}{blink(0.9)}</g>')
    b.append(f'<g>{ptext((x + R) / 2, dy + dh + 18, "PRESS START", 2, P["accent2"], anchor="middle")}'
             f'{blink(1.2, 0.6)}</g>')
    check_bottom(dy + dh + 18 + 14, 14 + h - 22 - 12, "hero")
    return svg("hero.svg", h, b, defs=defs)


def build_about():
    top = TOP
    lh = 22
    ph = 40 + (len(ABOUT) - 1) * lh + 42
    h = top + ph + 8
    b = window(X0, top, WW, ph, P, title="WHOAMI")
    # NPC portrait: the hood and face, cropped from the full sprite
    px, py, pw = L, top + 30, 110
    b.append(inset(px, py, pw, pw))
    crop = [row[2:18] for row in S.MAGE[:13]]
    cs = 6
    cw, chh = sprite_size(crop, cs)
    b += sprite(crop, px + (pw - cw) / 2, py + pw - chh - 2, cs, S.MAGE_KEYS, P)
    b.append(f'<rect x="{px + (pw - cw) / 2 + 7 * cs:g}" y="{py + pw - chh - 2 + 8 * cs:g}" width="{4 * cs}" '
             f'height="{cs}" fill="{P["face"]}" opacity="0"><animate attributeName="opacity" '
             f'values="0;1;0" keyTimes="0;0.9;0.95" dur="5s" calcMode="discrete" repeatCount="indefinite"/></rect>')
    b.append(ptext(px + pw / 2, py + pw + 12, "NAHID", 2, P["accent"], anchor="middle"))

    kx = R - 190
    x, y = px + pw + 26, top + 44
    for text, color in ABOUT:
        if text:
            check_text(x, text, 13, kx - 26, "about/copy")
            b.append(mono(x, y, text, 13, P[color]))
        y += lh
    b.append(f'<g>{ptext(kx - 36, top + ph - 22, "▼", 1.5, P["text"])}{blink(0.9)}</g>')
    b.append(f'<rect x="{kx - 18}" y="{top + 26}" width="2" height="{ph - 52}" fill="{P["frame_dim"]}"/>')
    ky = top + 44
    for k, v in ABOUT_KV:
        b.append(ptext(kx, ky - 9, k, 1.5, P["muted"]))
        b.append(mono(kx + 80, ky, v, 12, P["accent"], 600))
        check_text(kx + 80, v, 12, R, "about/kv")
        ky += 28
    check_bottom(max(y - lh, ky - 28) + 12, top + ph - 8, "about")
    return svg("about.svg", h, b)


TREE = [".ooo.", "oggGo", "ogggo", ".ooo.", "..w..", ".www."]


def build_journey():
    top = TOP
    mh = 132               # map strip
    cols = len(JOURNEY)
    cw = (R - L - (cols - 1) * 16) / cols
    pad = 12
    # measure cards first
    wrapped = [wrap(e["desc"], 12, cw - pad * 2) for e in JOURNEY]
    ch = 22 + 22 + 20 + max(len(w) for w in wrapped) * 18 + 10
    ph = 30 + mh + 16 + ch + 26
    h = top + ph + 8
    b = window(X0, top, WW, ph, P, title="WORLD MAP")

    my = top + 28
    b.append(inset(L, my, R - L, mh))
    # scenery: trees and grass tufts at fixed, hand-picked spots
    for i, (tx, ty) in enumerate([(70, 16), (96, 92), (310, 20), (338, 100), (560, 14), (604, 96),
                                  (752, 22), (770, 92)]):
        b += sprite(TREE, L + tx, my + ty, 3, {"o": "outline", "g": "accent_fill", "G": "glow_hi",
                                               "w": "wood"}, P)
    # the path: a dotted trail through every node, fogged after the last visited one
    nodes = [L + cw / 2 + i * (cw + 16) for i in range(cols)]
    py = my + mh / 2 + 10
    for i, nx in enumerate(nodes[:-1]):
        fog = JOURNEY[i + 1]["state"] == "fog"
        for dx in range(int(nx + 22), int(nodes[i + 1] - 22), 12):
            b.append(f'<rect x="{dx}" y="{py:g}" width="6" height="6" fill="{P["muted" if fog else "accent2"]}"'
                     f'{" opacity=\"0.45\"" if fog else ""}/>')
    for e, nx in zip(JOURNEY, nodes):
        c = P[e["color"]]
        b.append(ptext(nx, my + 12, e["when"], 2, c, anchor="middle"))
        if e["state"] == "fog":
            b.append(f'<g opacity="0.6">{ptext(nx, py - 8, "?", 3, P["muted"], anchor="middle")}'
                     f'<animate attributeName="opacity" values="0.6;0.25;0.6" dur="3s" repeatCount="indefinite"/></g>')
            continue
        cs = 4
        b += sprite(S.CRYSTAL, nx - 16, py - 13, cs, S.CRYSTAL_KEYS, P)
        if e["state"] == "here":
            # save-point ring + the player standing beside it
            b.append(f'<rect x="{nx - 22:g}" y="{py - 19:g}" width="44" height="44" fill="none" stroke="{c}" '
                     f'stroke-width="2"><animate attributeName="opacity" values="0.9;0" dur="1.8s" '
                     f'repeatCount="indefinite"/></rect>')
            ms = 2
            mw, mhh = sprite_size(S.MAGE, ms)
            b += mage(nx + 26, py + 22 - mhh, ms, eyes=False)
            b.append(ptext(nx, py + 32, "YOU ARE HERE", 1, c, anchor="middle"))
    # cards
    cy = my + mh + 16
    for e, nx, lines in zip(JOURNEY, nodes, wrapped):
        cx = nx - cw / 2
        c = P[e["color"]]
        b.append(inset(cx, cy, cw, ch, P["window"]))
        b.append(f'<rect x="{cx + 2:g}" y="{cy + 2:g}" width="{cw - 4:g}" height="4" fill="{c}"/>')
        tsize = fit(e["title"], 13.5, cw - pad * 2)
        check_text(cx + pad, e["title"], tsize, cx + cw - pad, "journey/title")
        b.append(mono(cx + pad, cy + 30, e["title"], tsize, P["text"], 700))
        osize = fit(e["org"], 12, cw - pad * 2)
        check_text(cx + pad, e["org"], osize, cx + cw - pad, "journey/org")
        b.append(mono(cx + pad, cy + 50, e["org"], osize, c, 600))
        yy = cy + 74
        for line in lines:
            b.append(mono(cx + pad, yy, line, 12, P["muted"]))
            yy += 18
        check_bottom(yy - 18 + 6, cy + ch, "journey/card")
    return svg("journey.svg", h, b)


def build_now():
    top = TOP
    rh = 58
    ph = 30 + len(QUESTS) * rh + 18
    h = top + ph + 8
    b = window(X0, top, WW, ph, P, title="ACTIVE QUESTS")
    y = top + 30
    bw = 150
    bx = R - bw
    for i, (kind, color, title, desc, done) in enumerate(QUESTS):
        c = P[color]
        if i:
            b.append(f'<rect x="{L}" y="{y - 6}" width="{R - L}" height="2" fill="{P["frame_dim"]}"/>')
        # marker: ! for open quests, ✓ for cleared ones
        b.append(inset(L, y + 4, 36, 36))
        mark = "✓" if done else "!"
        g = ptext(L + 18, y + 12, mark, 3, c, anchor="middle")
        b.append(g if done else f'<g>{g}{blink(1.4, 0.75)}</g>')
        tx = L + 52
        tagw, parts = tag(tx, y + 4, kind, c)
        b += parts
        b.append(mono(tx + tagw + 12, y + 19, title, 14, P["muted"] if done else P["text"], 700,
                      extra=' text-decoration="line-through"' if done else ""))
        check_text(tx + tagw + 12, title, 14, bx - 16, "now/title")
        b.append(mono(tx, y + 40, desc, 12, P["muted"]))
        check_text(tx, desc, 12, bx - 16, "now/desc")
        # progress: cleared quests are full; open ones show a busy marquee, not a fake %
        by = y + 14
        b.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="16" fill="{P["frame"]}"/>')
        b.append(f'<rect x="{bx + 2}" y="{by + 2}" width="{bw - 4}" height="12" fill="{P["inset"]}"/>')
        if done:
            b.append(f'<rect x="{bx + 2}" y="{by + 2}" width="{bw - 4}" height="12" fill="{P["accent_fill"]}"/>')
            b.append(ptext(bx + bw / 2, by + 24, "QUEST CLEAR", 1, P["accent"], anchor="middle"))
        else:
            fill = P[{"accent2": "gold_fill", "mp": "mp_fill", "accent": "accent_fill"}[color]]
            xs = ";".join(str(bx + 2 + k * 8) for k in range((bw - 4 - 32) // 8 + 1))
            b.append(f'<rect x="{bx + 2}" y="{by + 2}" width="32" height="12" fill="{fill}">'
                     f'<animate attributeName="x" values="{xs}" dur="{1.8 + i * 0.3:g}s" calcMode="discrete" '
                     f'repeatCount="indefinite"/></rect>')
            b.append(ptext(bx + bw / 2, by + 24, "IN PROGRESS", 1, P["muted"], anchor="middle"))
        y += rh
    check_bottom(y - rh + 44, top + ph - 8, "now")
    return svg("now.svg", h, b)


ICON = 2           # icon scale inside a slot
SLOT = 12 * ICON + 6
CHIP_H = SLOT


def chip_w(label, size=12):
    return SLOT + 8 + tw(label, size) + 10


def pack(labels, maxw, gap=8):
    rows, cur, curw = [], [], 0.0
    for l in labels:
        w = chip_w(l)
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


def chip_rows(labels, maxw, gap=8):
    """Fewest rows, then even them out so no orphan chip sits alone on the last row."""
    best = pack(labels, maxw, gap)
    if best is None:
        fail(f"chip too wide for {maxw:g}px: {labels}")
        return [labels]
    n, w = len(best), maxw
    while w > 40:
        w -= 4
        trial = pack(labels, w, gap)
        if trial is None or len(trial) != n:
            break
        best = trial
    return best


def item_chips(x, y, labels, maxw, icon_id, color=None, gap=8, rowgap=8):
    """Inventory items: an icon slot plus the item's name. Returns (parts, height)."""
    parts, cy = [], y
    for row in chip_rows(labels, maxw, gap):
        cx = x
        for l in row:
            w = chip_w(l)
            parts.append(f'<rect x="{cx:g}" y="{cy:g}" width="{w:g}" height="{CHIP_H}" fill="{P["window"]}" '
                         f'stroke="{P["frame_dim"]}" stroke-width="2"/>')
            parts.append(f'<rect x="{cx + 1:g}" y="{cy + 1:g}" width="{SLOT - 2}" height="{SLOT - 2}" '
                         f'fill="{P["inset"]}"/>')
            parts.append(f'<use href="#{icon_id}" x="{cx + 3:g}" y="{cy + 3:g}"/>')
            parts.append(mono(cx + SLOT + 8, cy + CHIP_H / 2 + 4.3, l, 12, color or P["text"], 500))
            cx += w + gap
        if cx - gap - x > maxw + 0.5:
            fail(f"chip row overflows ({cx - gap - x:.0f} > {maxw:g}): {row}")
        cy += CHIP_H + rowgap
    return parts, cy - y - rowgap


def icon_defs(names):
    keys = dict(S.ICON_KEYS, **{"W": "cloud"})
    return [f'<g id="i-{n}">' + "".join(sprite(ICONS[n], 0, 0, ICON, keys, P)) + "</g>" for n in names]


def build_skills():
    top = TOP
    gap = 16
    cw = (R - L - gap) / 2
    pad = 16
    maxw = cw - pad * 2
    heights = [44 + len(chip_rows(items, maxw)) * (CHIP_H + 8) - 8 + 16 for _, _, items in GROUPS]
    ys, y = [], top + 30
    for i in range(0, len(GROUPS), 2):
        rh = max(heights[i:i + 2])
        ys.append((y, rh))
        y += rh + gap
    ph = y - gap - top + 18
    h = top + ph + 8
    total = sum(len(items) for _, _, items in GROUPS)
    b = window(X0, top, WW, ph, P, title="INVENTORY")
    b.append(ptext(R, top + 12, f"{len(GROUPS)} BAGS · {total} ITEMS".replace("·", "-"), 1.5,
                   P["muted"], anchor="end"))
    for idx, (title, icon, items) in enumerate(GROUPS):
        col, row = idx % 2, idx // 2
        gx = L + col * (cw + gap)
        gy, gh = ys[row]
        b.append(inset(gx, gy, cw, gh))
        b.append(f'<use href="#i-{icon}" x="{gx + pad:g}" y="{gy + 10:g}"/>')
        c = P["accent"] if idx % 2 == 0 else P["accent2"]
        b.append(ptext(gx + pad + 32, gy + 16, title, 2, c))
        b.append(ptext(gx + cw - pad, gy + 18, f"x{len(items)}", 1.5, P["muted"], anchor="end"))
        parts, _ = item_chips(gx + pad, gy + 44, items, maxw, f"i-{icon}")
        b += parts
    return svg("skills.svg", h, b, defs=icon_defs([g[1] for g in GROUPS]))


def shimmer(x, y, w, h, cid):
    """A diagonal glint that sweeps across an item slot every few seconds."""
    return ([f'<clipPath id="{cid}"><rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}"/></clipPath>'],
            [f'<g clip-path="url(#{cid})"><path d="M{x - 40:g} {y + h:g}l{h:g} {-h:g}h14l{-h:g} {h:g}z" '
             f'fill="#ffffff" opacity="0.35"><animateTransform attributeName="transform" type="translate" '
             f'values="0 0;{w + 60:g} 0;{w + 60:g} 0" keyTimes="0;0.25;1" dur="4s" repeatCount="indefinite"/>'
             f'</path></g>'])


def build_projects():
    top = TOP
    slot = 96
    tx_off = slot + 24
    pad = 18
    textw = R - L - pad * 2 - tx_off
    cards = []
    for pr in PROJECTS:
        lines = wrap(pr["desc"], 12.5, textw)
        rows = len(chip_rows(pr["tech"], textw))
        body = 44 + len(lines) * 20 + 10 + rows * 32
        cards.append((pr, lines, max(body, slot + 16) + pad))
    ph = 30 + sum(c[2] + 16 for c in cards) + 56 + 18
    h = top + ph + 8
    defs = icon_defs(["gem"])
    b = window(X0, top, WW, ph, P, title="LEGENDARY ITEMS")
    y = top + 30
    for i, (pr, lines, chh) in enumerate(cards):
        c, fill = P[pr["color"]], P[pr["fill"]]
        b.append(inset(L, y, R - L, chh, P["window"]))
        sx, sy = L + pad, y + pad
        b.append(f'<rect x="{sx}" y="{sy}" width="{slot}" height="{slot}" fill="{P["inset"]}" '
                 f'stroke="{fill}" stroke-width="3"/>')
        isz = 16 * 5
        b += sprite(pr["icon"], sx + (slot - isz) / 2, sy + (slot - isz) / 2, 5, S.ITEM_KEYS, P)
        d, s = shimmer(sx, sy, slot, slot, f"sh{i}-{P['name']}")
        defs += d
        b += s
        x = sx + tx_off
        b.append(ptext(x, y + pad + 2, pr["name"], 3, c))
        nw = text_w(pr["name"].upper(), 3)
        tagw, parts = tag(x + nw + 14, y + pad, f"★ {pr['rarity']}", c)
        b += parts
        b.append(mono(x + nw + 14 + tagw + 10, y + pad + 14, pr["kind"], 11, P["muted"], 600, tracking=0.8))
        check_text(x + nw + 14 + tagw + 10, pr["kind"], 11, R - pad, "projects/kind", 0.8)
        b.append(mono(x, y + pad + 40, pr["repo"], 11.5, P["muted"]))
        ty = y + pad + 64
        for line in lines:
            b.append(mono(x, ty, line, 12.5, P["text"]))
            ty += 20
        parts, _ = plain_chips(x, ty - 6, ["+ " + t for t in pr["tech"]], textw, c)
        b += parts
        y += chh + 16
    # the stash: smaller things, on one strip
    b.append(inset(L, y, R - L, 56, P["window"]))
    b.append(ptext(L + pad, y + 21, "STASH", 2, P["accent2"]))
    sx = L + pad + text_w("STASH", 2) + 18
    parts, _ = item_chips(sx, y + 13, STASH, R - pad - sx, "i-gem")
    if len(chip_rows(STASH, R - pad - sx)) > 1:
        fail("projects/stash: chips wrap onto a second row")
    b += parts
    return svg("projects.svg", h, b, defs=defs)


def plain_chips(x, y, labels, maxw, color, size=11.5, h=24, gap=8, rowgap=8):
    rows, cur, curw = [], [], 0.0
    for l in labels:
        w = tw(l, size) + 18
        if cur and curw + gap + w > maxw:
            rows.append(cur)
            cur, curw = [], 0.0
        curw += (gap if cur else 0) + w
        cur.append(l)
    rows.append(cur)
    parts, cy = [], y
    for row in rows:
        cx = x
        for l in row:
            w = tw(l, size) + 18
            parts.append(f'<rect x="{cx:g}" y="{cy:g}" width="{w:g}" height="{h}" fill="{P["inset"]}" '
                         f'stroke="{P["frame_dim"]}" stroke-width="1.5"/>')
            parts.append(mono(cx + 9, cy + h / 2 + 4, l, size, color, 600))
            cx += w + gap
        if cx - gap - x > maxw + 0.5:
            fail(f"tech row overflows: {row}")
        cy += h + rowgap
    return parts, cy - y - rowgap


def build_blog_head():
    h = 78
    b = window(X0, 10, WW, 58, P)
    b += sprite(S.BOOK, L, 21, 2, S.ITEM_KEYS, P)
    b.append(ptext(L + 46, 28, "QUEST LOG", 3, P["accent"]))
    sub = "latest entries from the blog"
    b.append(mono(R, 44, sub, 12, P["muted"], anchor="end"))
    return svg("blog.svg", h, b)


def build_stats(st):
    top = TOP
    ph = 236
    h = top + ph + 8
    b = window(X0, top, WW, ph, P, title="CHARACTER")
    lv, frac, nxt = level(st["contributions_total"])
    # left: portrait + level
    pw = 132
    b.append(inset(L, top + 30, pw, 132))
    ms = 4
    mw, mh = sprite_size(S.MAGE, ms)
    b += mage(L + (pw - mw) / 2, top + 30 + 132 - mh - 4, ms, bob=False)
    b.append(ptext(L + pw / 2, top + 176, f"LV {lv}", 3, P["accent"], anchor="middle"))
    b.append(ptext(L + pw / 2, top + 206, "CODE MAGE", 1.5, P["muted"], anchor="middle"))

    # middle: bars + attributes
    mx = L + pw + 28
    mwid = 300
    cur, longest = st["streak_current"], max(st["streak_longest"], 1)
    rows = [("HP", "hp", "hp_fill", cur / longest, f"{cur}/{st['streak_longest']} day streak"),
            ("XP", "accent", "accent_fill", frac, f"{st['contributions_total']:,} / {nxt:,} to LV {lv + 1}")]
    y = top + 34
    for i, (k, tc, fc, f, label) in enumerate(rows):
        b.append(ptext(mx, y + 3, k, 2, P[tc]))
        b += bar(mx + 34, y, mwid - 34, 20, f, P[fc], P, delay=0.2 + i * 0.3)
        b.append(mono(mx + 34, y + 38, label, 11.5, P["muted"]))
        check_text(mx + 34, label, 11.5, mx + mwid, "stats/bar")
        y += 54
    attrs = [("STR", "stars", st["stars"]), ("INT", "repos", st["repos"]),
             ("CHA", "followers", st["followers"]), ("WIS", "this year", st["contributions_year"])]
    aw = (mwid - 3 * 8) / 4
    ay = y + 4
    for i, (k, sub, v) in enumerate(attrs):
        axx = mx + i * (aw + 8)
        b.append(inset(axx, ay, aw, 66, P["window"]))
        b.append(ptext(axx + aw / 2, ay + 9, k, 1.5, P["accent2"], anchor="middle"))
        val = f"{v:,}" if v < 10000 else f"{v / 1000:.1f}K"
        b.append(ptext(axx + aw / 2, ay + 26, val, 2, P["text"], anchor="middle"))
        check_px(axx + aw / 2 - text_w(val, 2) / 2, val, 2, axx + aw - 4, "stats/attr")
        b.append(mono(axx + aw / 2, ay + 58, sub, 10, P["muted"], anchor="middle"))
    check_bottom(ay + 66, top + ph - 8, "stats/attrs")

    # right: language affinity
    rx = mx + mwid + 28
    b.append(f'<rect x="{rx - 16}" y="{top + 30}" width="2" height="{ph - 54}" fill="{P["frame_dim"]}"/>')
    b.append(ptext(rx, top + 32, "AFFINITY", 2, P["accent2"]))
    fills = ["accent_fill", "gold_fill", "mp_fill", "rare_fill", "hp_fill", "accent_fill"]
    ly = top + 60
    nw = 112
    langs = st["languages"][:6]
    top_pct = max([l["pct"] for l in langs] + [1])
    for i, lng in enumerate(langs):
        name = lng["name"].replace("Jupyter Notebook", "Jupyter")
        b.append(mono(rx, ly + 12, name, 12, P["text"], 500))
        check_text(rx, name, 12, rx + nw - 6, "stats/lang")
        pct = f"{lng['pct']:.0f}%"
        b += bar(rx + nw, ly, R - rx - nw - 44, 16, lng["pct"] / top_pct, P[fills[i]], P, delay=0.4 + i * 0.12)
        b.append(mono(R, ly + 12, pct, 12, P["muted"], anchor="end"))
        ly += 26
    if st.get("updated"):
        b.append(ptext(R, top + ph - 20, f"SAVED {st['updated']}", 1, P["muted"], anchor="end"))
    return svg("stats.svg", h, b)


def build_contact():
    top = TOP
    ph = 236
    h = top + ph + 8
    b = window(X0, top, WW, ph, P, title="CONTACT")
    # CONTINUE? + a countdown that ticks 9..0 and loops
    word = "CONTINUE?"
    s = 4
    ww_ = text_w(word, s) + 18 + text_w("9", s)
    cx = (L + R) / 2 - ww_ / 2
    b.append(ptext(cx, top + 34, word, s, P["text"]))
    dx = cx + text_w(word, s) + 18
    for d in range(10):
        digit = str(9 - d)
        vals = ";".join("1" if k == d else "0" for k in range(10))
        b.append(f'<g opacity="{1 if d == 0 else 0}">{ptext(dx, top + 34, digit, s, P["accent2"])}'
                 f'<animate attributeName="opacity" values="{vals}" dur="10s" calcMode="discrete" '
                 f'repeatCount="indefinite"/></g>')
    # menu, two columns, cursor on the first entry
    colw = (R - L) / 2
    y0 = top + 92
    for i, (k, v) in enumerate(CONTACT):
        col, row = i // 3, i % 3
        x = L + 40 + col * colw
        y = y0 + row * 34
        if i == 0:
            b.append(f'<g>{ptext(x - 22, y - 11, "▶", 2, P["accent"])}{blink(0.8)}</g>')
        b.append(ptext(x, y - 10, k, 1.5, P["accent2"] if i else P["accent"]))
        b.append(mono(x + 84, y, v, 13, P["text"] if i == 0 else P["muted"], 600 if i == 0 else 400))
        check_text(x + 84, v, 13, x + colw - 40, "contact/row")
    fy = top + ph - 42
    b.append(f'<rect x="{L}" y="{fy - 14}" width="{R - L}" height="2" fill="{P["frame_dim"]}"/>')
    msg = "INSERT COIN TO COLLABORATE"
    mw = text_w(msg, 2)
    mx = (L + R) / 2 - mw / 2 + 14
    b += sprite(S.COIN, mx - 30, fy, 3, S.COIN_KEYS, P,
                extra='><animateTransform attributeName="transform" type="translate" values="0 0;0 -3" '
                      'dur="0.8s" calcMode="discrete" repeatCount="indefinite"/')
    b.append(f'<g>{ptext(mx, fy + 2, msg, 2, P["accent2"])}{blink(1.4, 0.7)}</g>')
    return svg("contact.svg", h, b)


def build_rule():
    h = 28
    cy = 12
    b = []
    hw, hh = sprite_size(S.HEART, 2)
    hx = W / 2 - hw / 2
    b += sprite(S.HEART, hx, cy - hh / 2 + 1, 2, S.HEART_KEYS, P)
    for side in (-1, 1):
        for k in range(1, 26):
            x = W / 2 + side * (hw / 2 + 4 + k * 12) - (6 if side < 0 else 0)
            op = max(0.15, 1 - k / 26)
            b.append(f'<rect x="{x:g}" y="{cy - 1}" width="6" height="4" fill="{P["frame_dim" if k > 3 else "accent2"]}" '
                     f'opacity="{op:.2f}"/>')
    return svg("rule.svg", h, b)


def build_button(name, label, style):
    s = 2
    pad = 14
    w = text_w(label, s) + pad * 2 + 2 * B
    h = 30 + 2 * B
    fill = {"accent": P["accent_fill"], "gold": P["gold_fill"], "rare": P["rare_fill"],
            "mp": P["mp_fill"], "plain": P["window"]}[style]
    ink = P["text"] if style == "plain" else "#0d1117"
    b = [notched(4, 4, w, h, P["shadow"]), notched(0, 0, w, h, P["frame"]),
         f'<rect x="{B}" y="{B}" width="{w - 2 * B:g}" height="{h - 2 * B}" fill="{fill}"/>',
         f'<rect x="{B}" y="{B}" width="{w - 2 * B:g}" height="2" fill="#ffffff" opacity="0.4"/>',
         f'<rect x="{B}" y="{h - B - 3}" width="{w - 2 * B:g}" height="3" fill="#000000" opacity="0.18"/>',
         ptext(w / 2, (h - text_h(s)) / 2 - 1, label, s, ink, anchor="middle")]
    return svg(f"{name}.svg", h + 4, b, w=w + 4)


# --------------------------------------------------------------------------
# README
# --------------------------------------------------------------------------
def picture(name, alt, width=None, href=None):
    wa = f' width="{width}"' if width else ""
    pic = (f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/dark/{name}.svg">'
           f'<source media="(prefers-color-scheme: light)" srcset="assets/light/{name}.svg">'
           f'<img src="assets/dark/{name}.svg"{wa} alt="{alt}"></picture>')
    return f'<a href="{href}">{pic}</a>' if href else pic


def write_readme():
    """Expand tools/README.template.md into README.md.

    {{pic:NAME|ALT}}        full-width panel
    {{btn:NAME|HREF|ALT}}   linked pixel button
    The BLOG-POST-LIST block is carried over from the current README so an
    external job that rewrites it is never clobbered.
    """
    with open(os.path.join(TOOLS, "README.template.md")) as f:
        out = f.read()
    out = re.sub(r"\{\{pic:([\w-]+)\|([^}]*)\}\}", lambda m: picture(m[1], m[2], 880), out)
    out = re.sub(r"\{\{btn:([\w-]+)\|([^|}]*)\|([^}]*)\}\}", lambda m: picture(m[1], m[3], href=m[2]), out)
    readme = os.path.join(ROOT, "README.md")
    block = re.compile(r"<!-- BLOG-POST-LIST:START -->.*?<!-- BLOG-POST-LIST:END -->", re.S)
    if os.path.exists(readme):
        with open(readme) as f:
            cur = block.search(f.read())
        if cur:
            out = block.sub(lambda _: cur[0], out)
    with open(readme, "w") as f:
        f.write(out)
    print("  README.md")


def main():
    global P
    st = load_stats()
    for theme in THEMES:
        P = theme
        os.makedirs(os.path.join(ASSETS, P["name"]), exist_ok=True)
        if P is THEMES[0]:
            print("building assets (dark + light):")
        build_hero(st)
        build_about()
        build_journey()
        build_now()
        build_skills()
        build_projects()
        build_blog_head()
        build_stats(st)
        build_contact()
        build_rule()
        for name, label, style in BUTTONS:
            build_button(name, label, style)
    if _errors:
        print("\nOVERFLOW ERRORS:", file=sys.stderr)
        for e in _errors:
            print("  -", e, file=sys.stderr)
        sys.exit(1)
    write_readme()
    print("\nall panels fit.")


if __name__ == "__main__":
    main()
