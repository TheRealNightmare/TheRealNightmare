"""Two themes with identical keys, so every panel can be built for either.

DARK sits on GitHub's dark canvas (#0d1117), LIGHT on its light canvas (#ffffff).
The canvas itself is never painted: windows carry their own fill, and the space
between them is the page showing through. That way each SVG blends into
whichever GitHub theme picks it.

Text colors pass WCAG AA (4.5:1) against `window` in their own theme. The
`*_fill` colors are for bars and sprite pixels only, never for text.
"""

DARK = {
    "name":        "dark",
    "window":      "#161b22",   # window body
    "inset":       "#0d1117",   # wells, slots, bar troughs
    "frame":       "#c9d1d9",   # outer pixel border: the classic light-on-dark RPG frame
    "frame_dim":   "#30363d",   # inner rule, dividers
    "shadow":      "#010409",   # hard 4px drop shadow
    "text":        "#e6edf3",
    "muted":       "#9198a1",
    "accent":      "#a3e636",   # lime: the brand
    "accent2":     "#ffdc58",   # gold
    "hp":          "#ff7b72",
    "mp":          "#79c0ff",
    "rare":        "#d2a8ff",   # purple, for legendary items
    "accent_fill": "#a3e636",
    "gold_fill":   "#ffdc58",
    "hp_fill":     "#f85149",
    "mp_fill":     "#388bfd",
    "rare_fill":   "#a371f7",
    # sprite-only colors
    "outline":     "#010409",
    "cloak":       "#3b2a6b",
    "cloak_hi":    "#5b45a0",
    "cloak_lo":    "#24184a",
    "face":        "#0a0612",
    "glow":        "#a3e636",
    "glow_hi":     "#e9ffc2",
    "wood":        "#8a5a2b",
    "wood_lo":     "#5c3a1a",
    "trim":        "#ffdc58",
    "screen":      "#0d1117",
    "metal":       "#8b949e",
    "metal_lo":    "#484f58",
    "paper":       "#f2e2b8",
    "paper_lo":    "#c9a96e",
    "ink":         "#6b4f2a",
    "cloud":       "#e6edf3",
    "piece":       "#e6edf3",
    "piece_lo":    "#9198a1",
    "sky":         "#0b1020",
    "star":        "#c9d1d9",
    "dirt":        "#30363d",
}

LIGHT = {
    "name":        "light",
    "window":      "#ffffff",
    "inset":       "#f6f8fa",
    "frame":       "#1f2328",
    "frame_dim":   "#d1d9e0",
    "shadow":      "#d1d9e0",
    "text":        "#1f2328",
    "muted":       "#59636e",
    "accent":      "#3f6212",   # lime, deepened until it reads on white
    "accent2":     "#9a6700",   # gold, likewise
    "hp":          "#cf222e",
    "mp":          "#0969da",
    "rare":        "#8250df",
    "accent_fill": "#84cc16",
    "gold_fill":   "#f5c518",
    "hp_fill":     "#ff6b6b",
    "mp_fill":     "#54aeff",
    "rare_fill":   "#a371f7",
    "outline":     "#1f2328",
    "cloak":       "#4c3a8c",
    "cloak_hi":    "#6f5bc0",
    "cloak_lo":    "#2e2160",
    "face":        "#120c22",
    "glow":        "#a3e636",
    "glow_hi":     "#e9ffc2",
    "wood":        "#9a6634",
    "wood_lo":     "#6b4220",
    "trim":        "#e0a800",
    "screen":      "#1f2328",
    "metal":       "#8c959f",
    "metal_lo":    "#59636e",
    "paper":       "#f2e2b8",
    "paper_lo":    "#c9a96e",
    "ink":         "#6b4f2a",
    "cloud":       "#ffffff",
    "piece":       "#ffffff",
    "piece_lo":    "#afb8c1",
    "sky":         "#1b1f3b",
    "star":        "#e6edf3",
    "dirt":        "#4a3a2a",
}

THEMES = [DARK, LIGHT]
