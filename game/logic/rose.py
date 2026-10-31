"""Logica della rosa dei venti (tappe 1 e 2), senza grafica.

Lati dello schermo e punti cardinali sono entrambi elencati in senso orario,
visti dall'alto: alto -> destra -> basso -> sinistra e N -> E -> S -> O.
"""

SIDES = ("top", "right", "bottom", "left")
DIRS = ("N", "E", "S", "O")


def next_clockwise(direction):
    """Punto cardinale che viene dopo, girando come le lancette."""
    return DIRS[(DIRS.index(direction) + 1) % 4]


def side_for(direction, east_side="right"):
    """Lato dello schermo in cui deve stare `direction` se l'Est è su `east_side`.

    Partendo dall'Est: S è a 90 gradi in senso orario, O a 180, N a 90 in senso antiorario.
    """
    if direction not in DIRS:
        raise ValueError(f"direzione sconosciuta: {direction}")
    if east_side not in SIDES:
        raise ValueError(f"lato sconosciuto: {east_side}")
    steps = (DIRS.index(direction) - DIRS.index("E")) % 4
    return SIDES[(SIDES.index(east_side) + steps) % 4]


def expected_layout(east_side="right"):
    """Dizionario lato -> direzione attesa."""
    return {side_for(d, east_side): d for d in DIRS}


def is_correct(direction, side, east_side="right"):
    return side_for(direction, east_side) == side


def validate(placement, east_side="right"):
    """`placement` è un dizionario lato -> direzione. Vero se completo e corretto."""
    if set(placement.keys()) != set(SIDES):
        return False
    return all(is_correct(d, s, east_side) for s, d in placement.items())


SIDE_VECTORS = {"top": (0, -1), "right": (1, 0), "bottom": (0, 1), "left": (-1, 0)}
