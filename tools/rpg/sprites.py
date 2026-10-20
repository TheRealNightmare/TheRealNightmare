"""ASCII sprites. '.' is transparent; every other char maps to a palette key.

Keep grids rectangular; `pixel.sprite` refuses ragged rows.
"""

# --------------------------------------------------------------------------
# the hooded mage: a face lost in shadow, two lime eyes, a staff with a gem
# --------------------------------------------------------------------------
MAGE_KEYS = {
    "o": "outline", "c": "cloak", "h": "cloak_hi", "d": "cloak_lo",
    "f": "face", "e": "glow", "g": "glow", "G": "glow_hi",
    "s": "wood", "w": "wood_lo", "t": "trim",
}

MAGE = [
    "..........oo............",
    ".........ohco.......oo..",
    "........ohccdo.....oggo.",
    "........ohcccdo...ogGGgo",
    ".......ohccccdo...ogGGgo",
    ".......ohcccccdo...oggo.",
    "......ohcffffcdo....so..",
    "......ohffffffdo....so..",
    ".....ohffeffeffdo...so..",
    ".....ohffffffffdo...so..",
    ".....ohcffffffcdo...so..",
    "....ohhccffffccddo..so..",
    "...ohhcccccccccddo..so..",
    "..ohhccccctccccddoooso..",
    "..ohcccccctcchhhhhhdsd..",
    ".ohhcccccctcdddddddoso..",
    ".ohccccccctccccddo..so..",
    ".ohccccccctcccccddo.so..",
    "ohhccccccctccccccddoso..",
    "ohcccccccctccccccddoso..",
    "ohhccccccctcccccdddoso..",
    "ohcccccccctcccccdddoso..",
    "ohhccccccctccccddddoso..",
    "ohcccccccctcccccdddoso..",
    "ohtttttttttttttttddoso..",
    ".oooooooooooooooooo.so..",
    "....................ww..",
]

# second idle frame: eyes half-closed (a blink) — swapped in briefly
MAGE_BLINK = [row if i != 8 else ".....ohffffffffdo...so.." for i, row in enumerate(MAGE)]

# --------------------------------------------------------------------------
# inventory item icons, 12x12 — one item type per skill group
# --------------------------------------------------------------------------
ICON_KEYS = {
    "o": "outline", "p": "paper", "P": "paper_lo", "k": "ink",
    "v": "rare_fill", "G": "glow_hi", "g": "accent_fill", "w": "wood",
    "m": "metal", "M": "metal_lo", "t": "trim", "K": "metal_lo", "e": "glow",
    "W": "cloud", "L": "mp_fill",
}

SCROLL = [
    "............",
    ".oooooooooo.",
    "oPPPPPPPPPPo",
    ".oppppppppo.",
    ".opkkkkkkpo.",
    ".oppppppppo.",
    ".opkkkkpppo.",
    ".oppppppppo.",
    ".opkkkkkkpo.",
    "oPPPPPPPPPPo",
    ".oooooooooo.",
    "............",
]

POTION = [
    "....oooo....",
    "....owwo....",
    "....oooo....",
    "....oGvo....",
    "...oGvvvo...",
    "..oGvvvvvo..",
    ".oGvGvvvvvo.",
    ".ovvvvvvvvo.",
    ".ovvvvGvvvo.",
    ".ovvvvvvvvo.",
    "..ovvvvvvo..",
    "...oooooo...",
]

GEM = [
    "............",
    "...oooooo...",
    "..oGggggGo..",
    ".oGggggggGo.",
    "oggggggggggo",
    ".oggggggggo.",
    "..oggggggo..",
    "...oggggo...",
    "....oggo....",
    ".....oo.....",
    "............",
    "............",
]

SWORD = [
    "..........oo",
    ".........oGo",
    "........oGmo",
    ".......oGmo.",
    "......oGmo..",
    ".....oGmo...",
    "..o.oGmo....",
    "..otomo.....",
    "...otto.....",
    "..owotto....",
    ".owo..oo....",
    ".oo.........",
]

CHIP = [
    "..m.m..m.m..",
    ".oooooooooo.",
    "moKKKKKKKKom",
    ".oKKKKKKKKo.",
    "moKKmmmmKKom",
    ".oKKmemmKKo.",
    ".oKKmmmmKKo.",
    "moKKmmmmKKom",
    ".oKKKKKKKKo.",
    "moKKKKKKKKom",
    ".oooooooooo.",
    "..m.m..m.m..",
]

CLOUD = [
    "............",
    "............",
    "....oooo....",
    "...oWWWWo...",
    ".oooWWWWWoo.",
    "oWWWWWWWWWWo",
    "oWWWWWWWWWWo",
    "oWWWWWWWWWLo",
    ".oLLLLLLLLo.",
    "..oooooooo..",
    "............",
    "............",
]

# --------------------------------------------------------------------------
# legendary items, 16x16
# --------------------------------------------------------------------------
ITEM_KEYS = dict(ICON_KEYS, **{"W": "piece", "L": "piece_lo", "b": "accent_fill",
                                "B": "cloak_lo", "r": "rare_fill", "h": "hp_fill"})

PAWN = [
    "................",
    "......oooo......",
    ".....oWWWLo.....",
    ".....oWWWLo.....",
    "......oWLo......",
    "....oWWWWWLo....",
    ".....oooooo.....",
    "......oWLo......",
    "......oWLo......",
    ".....oWWWLo.....",
    ".....oWWWLo.....",
    "....oWWWWWLo....",
    "...oWWWWWWWLo...",
    "..oooooooooooo..",
    "..oWWWWWWWWWLo..",
    "..oooooooooooo..",
]

EYE = [
    "................",
    "................",
    "................",
    "................",
    ".....oooooo.....",
    "...ooWWWWWWoo...",
    "..oWWWWooWWWWo..",
    ".oWWWWoggoWWWWo.",
    "oWWWWogGGgoWWWWo",
    "oWWWWoggggoWWWWo",
    ".oWWWWooooWWWWo.",
    "..oWWWWWWWWWWo..",
    "...ooWWWWWWoo...",
    ".....oooooo.....",
    "................",
    "................",
]

BOOK = [
    "................",
    "...ooooooooooo..",
    "..orrrrrrrrrrro.",
    "..orttttttttrro.",
    "..ortrrrrrrtrro.",
    "..ortrrGrrrtrro.",
    "..ortrrrrrrtrro.",
    "..orttttttttrro.",
    "..orrrrrrrrrrro.",
    "..orrrrrrrrrrro.",
    "..orrrrrrrrrrro.",
    "..oBBBBBBBBBBBo.",
    "..oppppppppppppo",
    "..oPPPPPPPPPPPPo",
    "...oooooooooooo.",
    "................",
]

# --------------------------------------------------------------------------
# small decorations
# --------------------------------------------------------------------------
HEART = [
    ".oo.oo.",
    "ohhohho",
    "ohhhhho",
    ".ohhho.",
    "..oho..",
    "...o...",
]

CRYSTAL = [
    "...oo...",
    "..oGgo..",
    ".oGggbo.",
    "oGgggbbo",
    "oggggbbo",
    ".oggbbo.",
    "..ogbo..",
    "...oo...",
]
CRYSTAL_KEYS = {"o": "outline", "G": "glow_hi", "g": "accent_fill", "b": "frame_dim"}

COIN = [
    ".oooo.",
    "ottGto",
    "otGtto",
    "otttto",
    "otttto",
    ".oooo.",
]
COIN_KEYS = {"o": "outline", "t": "gold_fill", "G": "glow_hi"}
HEART_KEYS = {"o": "outline", "h": "hp_fill"}
