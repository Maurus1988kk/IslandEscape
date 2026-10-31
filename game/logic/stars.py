"""Stelle del Grande Carro e Stella Polare (tappa 5).

Proiezione polare centrata sul polo nord celeste, come vista guardando verso Nord:
    r = 90 - declinazione
    angolo = ascensione retta in gradi (ore x 15)
    x = cx + k * r * sin(angolo + rotazione)
    y = cy - k * r * cos(angolo + rotazione)
"""

import math

# nome: (ascensione retta in ore, declinazione in gradi)
STARS = {
    "Dubhe": (11.06, 61.75),
    "Merak": (11.03, 56.38),
    "Phecda": (11.90, 53.69),
    "Megrez": (12.26, 57.03),
    "Alioth": (12.90, 55.96),
    "Mizar": (13.40, 54.93),
    "Alkaid": (13.79, 49.31),
    "Polaris": (2.53, 89.26),
}

DIPPER = ("Dubhe", "Merak", "Phecda", "Megrez", "Alioth", "Mizar", "Alkaid")
BOWL = ("Dubhe", "Merak", "Phecda", "Megrez")
HANDLE = ("Alioth", "Mizar", "Alkaid")
POINTERS = ("Merak", "Dubhe")  # la linea va da Merak verso Dubhe e prosegue
DIPPER_LINES = (
    ("Alkaid", "Mizar"),
    ("Mizar", "Alioth"),
    ("Alioth", "Megrez"),
    ("Megrez", "Dubhe"),
    ("Dubhe", "Merak"),
    ("Merak", "Phecda"),
    ("Phecda", "Megrez"),
)

# Parametri scelti per la scena: il carro sta in alto a destra sopra la Polare,
# la Polare è a circa metà altezza tra l'orizzonte e il bordo superiore.
ROTATION = -155.0
SCALE_K = 9.6
POLE_CENTER = (600.0, 355.0)
HORIZON_Y = 610


def project(ra_hours, dec_deg, cx=POLE_CENTER[0], cy=POLE_CENTER[1], k=SCALE_K, rot=ROTATION):
    r = 90.0 - dec_deg
    ang = math.radians(ra_hours * 15.0 + rot)
    return (cx + k * r * math.sin(ang), cy - k * r * math.cos(ang))


def projected(cx=POLE_CENTER[0], cy=POLE_CENTER[1], k=SCALE_K, rot=ROTATION):
    return {name: project(ra, dec, cx, cy, k, rot) for name, (ra, dec) in STARS.items()}


def pointer_point(stars, factor):
    """Punto sulla retta Merak -> Dubhe: factor=0 Merak, 1 Dubhe, 6 = 5 volte oltre Dubhe."""
    mx, my = stars["Merak"]
    dx, dy = stars["Dubhe"]
    return (mx + (dx - mx) * factor, my + (dy - my) * factor)


def north_point(stars, horizon_y=HORIZON_Y):
    """Punto dell'orizzonte esattamente sotto la Stella Polare."""
    return (stars["Polaris"][0], float(horizon_y))


def distance_to_line(p, a, b):
    """Distanza del punto p dalla retta per a e b."""
    ax, ay = a
    bx, by = b
    px, py = p
    num = abs((bx - ax) * (ay - py) - (ax - px) * (by - ay))
    den = math.hypot(bx - ax, by - ay)
    return num / den if den else math.hypot(px - ax, py - ay)
