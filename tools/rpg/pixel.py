"""Pixel primitives: a 5x7 bitmap font, ASCII-grid sprites and RPG windows.

Everything renders as merged horizontal runs inside one <path> per color, so a
sprite costs a handful of elements rather than one <rect> per pixel. Images
that GitHub serves through <img> cannot load web fonts, which is why headings
are drawn from a built-in bitmap alphabet instead of a pixel typeface.
"""

# --------------------------------------------------------------------------
# 5x7 font. '#' is ink. Lowercase is folded to uppercase.
# --------------------------------------------------------------------------
_GLYPHS = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    " ": [".....", ".....", ".....", ".....", ".....", ".....", "....."],
    ".": [".....", ".....", ".....", ".....", ".....", ".##..", ".##.."],
    ",": [".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."],
    ":": [".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."],
    "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    "-": [".....", ".....", ".....", "#####", ".....", ".....", "....."],
    "+": [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
    "/": ["....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."],
    "'": ["..#..", "..#..", ".#...", ".....", ".....", ".....", "....."],
    "%": ["##..#", "##..#", "...#.", "..#..", ".#...", "#..##", "#..##"],
    "#": [".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."],
    "(": ["...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."],
    ")": [".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."],
    ">": [".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."],
    "<": ["...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."],
    "&": [".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"],
    "@": [".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."],
    "*": [".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."],
    "=": [".....", ".....", "#####", ".....", "#####", ".....", "....."],
    "_": [".....", ".....", ".....", ".....", ".....", ".....", "#####"],
    "[": [".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."],
    "]": [".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."],
    "|": ["..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "▶": [".#...", ".##..", ".###.", ".####", ".###.", ".##..", ".#..."],  # ▶ cursor
    "▼": [".....", "#####", ".###.", ".###.", "..#..", "..#..", "....."],  # ▼ next
    "♥": [".....", ".#.#.", "#####", "#####", ".###.", "..#..", "....."],  # ♥
    "✓": [".....", "....#", "...##", "#.##.", "###..", ".#...", "....."],  # ✓
    "★": ["..#..", "..#..", "#####", ".###.", ".###.", "##.##", "#...#"],  # ★
}
for _g in _GLYPHS.values():
    assert len(_g) == 7 and all(len(r) == 5 for r in _g)

GLYPH_W, GLYPH_H, GLYPH_GAP = 5, 7, 1


def _runs(rows, ink):
    """Yield (col, row, length) for each horizontal run of `ink` in a char grid."""
    for r, line in enumerate(rows):
        c = 0
        while c < len(line):
            if line[c] == ink:
                s = c
                while c < len(line) and line[c] == ink:
                    c += 1
                yield s, r, c - s
            else:
                c += 1


def _path(runs, x, y, s, color, extra=""):
    d = "".join(f"M{x + c * s:g} {y + r * s:g}h{n * s:g}v{s:g}h{-n * s:g}z" for c, r, n in runs)
    return f'<path d="{d}" fill="{color}"{extra}/>' if d else ""


def text_w(text, scale, tracking=1):
    """Rendered width of bitmap text: 5 px glyphs, `tracking` px between them."""
    n = len(text)
    return (n * GLYPH_W + max(n - 1, 0) * tracking) * scale


def text_h(scale):
    return GLYPH_H * scale


def ptext(x, y, text, scale, color, anchor="start", tracking=1, extra=""):
    """Bitmap text whose TOP-left sits at (x, y). One <path> for the whole string."""
    text = text.upper()
    w = text_w(text, scale, tracking)
    if anchor == "middle":
        x -= w / 2
    elif anchor == "end":
        x -= w
    runs = []
    for i, ch in enumerate(text):
        g = _GLYPHS.get(ch)
        if g is None:
            raise KeyError(f"no glyph for {ch!r} in {text!r}")
        off = i * (GLYPH_W + tracking)
        runs += [(off + c, r, n) for c, r, n in _runs(g, "#")]
    return _path(runs, x, y, scale, color, extra)


# --------------------------------------------------------------------------
# sprites: list of equal-length strings + char -> palette key ('.' = clear)
# --------------------------------------------------------------------------
def sprite(grid, x, y, scale, keymap, P, extra=""):
    """Render an ASCII sprite. Returns a list of <path>s, one per color."""
    w = len(grid[0])
    for row in grid:
        if len(row) != w:
            raise ValueError(f"ragged sprite row ({len(row)} != {w}): {row!r}")
    out = []
    for ch, key in keymap.items():
        p = _path(list(_runs(grid, ch)), x, y, scale, P[key])
        if p:
            out.append(p)
    used = set("".join(grid)) - {"."}
    missing = used - set(keymap)
    if missing:
        raise KeyError(f"sprite uses unmapped chars {sorted(missing)}")
    if extra:
        return [f"<g{extra}>"] + out + ["</g>"]
    return out


def sprite_size(grid, scale):
    return len(grid[0]) * scale, len(grid) * scale


# --------------------------------------------------------------------------
# windows
# --------------------------------------------------------------------------
B = 3        # frame thickness
NOTCH = 3    # corner cut, which is what makes a rectangle read as pixel art
SHADOW = 4


def notched(x, y, w, h, color, c=NOTCH):
    return (f'<path d="M{x + c:g} {y:g}h{w - 2 * c:g}v{c:g}h{c:g}v{h - 2 * c:g}h{-c:g}v{c:g}'
            f'h{-(w - 2 * c):g}v{-c:g}h{-c:g}v{-(h - 2 * c):g}h{c:g}z" fill="{color}"/>')


def window(x, y, w, h, P, fill=None, title=None, title_color=None, accent=None):
    """The classic RPG message window: hard shadow, light frame, inner rule.

    `title` hangs a small tab over the top edge, so leave ~14px above `y`.
    `accent` paints a thin colored strip just inside the left frame.
    """
    out = [notched(x + SHADOW, y + SHADOW, w, h, P["shadow"]),
           notched(x, y, w, h, P["frame"]),
           f'<rect x="{x + B:g}" y="{y + B:g}" width="{w - 2 * B:g}" height="{h - 2 * B:g}" '
           f'fill="{fill or P["window"]}"/>',
           f'<rect x="{x + B + 3:g}" y="{y + B + 3:g}" width="{w - 2 * B - 6:g}" '
           f'height="{h - 2 * B - 6:g}" fill="none" stroke="{P["frame_dim"]}" stroke-width="1"/>']
    if accent:
        out.append(f'<rect x="{x + B + 3:g}" y="{y + B + 3:g}" width="3" height="{h - 2 * B - 6:g}" '
                   f'fill="{accent}"/>')
    if title:
        out += title_tab(x + 20, y, title, P, title_color)
    return out


def title_tab(x, y_edge, title, P, color=None, scale=2):
    """A small framed label centred on a window's top edge."""
    tw_ = text_w(title.upper(), scale)
    th = text_h(scale)
    pad = 8
    w, h = tw_ + pad * 2 + 2 * B, th + 10 + 2 * B
    ty = y_edge - h / 2
    return [notched(x, ty, w, h, P["frame"]),
            f'<rect x="{x + B:g}" y="{ty + B:g}" width="{w - 2 * B:g}" height="{h - 2 * B:g}" '
            f'fill="{P["window"]}"/>',
            ptext(x + B + pad, ty + B + 5, title, scale, color or P["accent"])]


def blink(dur=1.0, on=0.5):
    """SMIL fragment for a hard on/off blink (no fade, like an old console)."""
    return (f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;{on};{on};1" '
            f'dur="{dur}s" repeatCount="indefinite"/>')


def bar(x, y, w, h, frac, fill, P, label_parts=None, delay=0.0, dur=1.2):
    """Segmented stat bar that fills once on load and then holds."""
    frac = max(0.0, min(1.0, frac))
    inner_w = w - 4
    target = round(inner_w * frac)
    # stepped, not smooth: the bar ticks up in 12 chunks like an old HUD
    steps = ";".join(str(round(target * i / 12)) for i in range(13))
    grow = (f'<animate attributeName="width" values="{steps}" begin="{delay}s" dur="{dur}s" '
            f'calcMode="discrete" fill="freeze"/>')
    out = [f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{P["frame"]}"/>',
           f'<rect x="{x + 2:g}" y="{y + 2:g}" width="{inner_w:g}" height="{h - 4:g}" fill="{P["inset"]}"/>',
           f'<rect x="{x + 2:g}" y="{y + 2:g}" width="{target}" height="{h - 4:g}" fill="{fill}">{grow}</rect>',
           # a 1px highlight along the top, the way 16-bit bars catch the light
           f'<rect x="{x + 2:g}" y="{y + 2:g}" width="{target}" height="1" fill="#ffffff" '
           f'opacity="0.35">{grow}</rect>']
    # segment ticks every 8px so the fill reads as blocks
    for tx in range(int(x + 2 + 8), int(x + 2 + inner_w), 8):
        out.append(f'<rect x="{tx}" y="{y + 2:g}" width="1" height="{h - 4:g}" fill="{P["inset"]}" opacity="0.6"/>')
    if label_parts:
        out += label_parts
    return out
