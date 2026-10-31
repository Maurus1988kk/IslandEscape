"""Mappa del tesoro della tappa 4: luoghi su una griglia logica e indovinelli.

Regola usata (e verificata dai test): "X è a Nord di Y" vuol dire che X sta
nella stessa colonna di Y, più in alto. Est/Ovest: stessa riga, a destra/sinistra.
Ogni indovinello deve avere UNA sola risposta.
"""

MAP_COLS = 4
MAP_ROWS = 4

PLACES = {
    "cascata": (1, 0),
    "grotta": (1, 1),
    "faro": (2, 1),
    "lago": (0, 2),
    "palma": (1, 2),
    "tartaruga": (3, 2),
    "relitto": (1, 3),
    "capanna": (3, 3),
}

PLACE_NAMES = {
    "cascata": "Cascata",
    "grotta": "Grotta",
    "faro": "Faro",
    "lago": "Lago",
    "palma": "Palma gigante",
    "tartaruga": "Roccia tartaruga",
    "relitto": "Relitto",
    "capanna": "Capanna",
}

RIDDLES = (
    {
        "text": "La corda per la vela è a Nord della capanna. Toccate il posto giusto!",
        "clues": (("N", "capanna"),),
        "answer": "tartaruga",
        "piece": "corda",
        "hint": "Trovate la capanna. Il Nord è in alto: guardate sopra la capanna!",
        "hint2": "Partite dalla capanna e seguite la freccia gialla verso l'alto!",
    },
    {
        "text": "La tela della vela è a Ovest del faro. Dov'è?",
        "clues": (("O", "faro"),),
        "answer": "grotta",
        "piece": "tela",
        "hint": "Trovate il faro. Sulle mappe l'Ovest è a sinistra!",
        "hint2": "Partite dal faro e seguite la freccia gialla verso sinistra!",
    },
    {
        "text": "L'albero per la vela è a Est del lago e a Sud della cascata.",
        "clues": (("E", "lago"), ("S", "cascata")),
        "answer": "palma",
        "piece": "albero",
        "hint": "Dal lago andate verso destra. Dalla cascata andate verso il basso.",
        "hint2": "Seguite le due frecce gialle: il posto giusto è dove si incontrano!",
    },
)

_DIR_TEST = {
    "N": lambda ref, p: p[0] == ref[0] and p[1] < ref[1],
    "S": lambda ref, p: p[0] == ref[0] and p[1] > ref[1],
    "E": lambda ref, p: p[1] == ref[1] and p[0] > ref[0],
    "O": lambda ref, p: p[1] == ref[1] and p[0] < ref[0],
}


def in_direction(ref_id, direction, places=PLACES):
    ref = places[ref_id]
    test = _DIR_TEST[direction]
    return {pid for pid, pos in places.items() if pid != ref_id and test(ref, pos)}


def nearest_in_direction(ref_id, direction, places=PLACES):
    cands = in_direction(ref_id, direction, places)
    if not cands:
        return None
    ref = places[ref_id]
    return min(cands, key=lambda pid: abs(places[pid][0] - ref[0]) + abs(places[pid][1] - ref[1]))


def solve(clues, places=PLACES):
    result = None
    for direction, ref_id in clues:
        cands = in_direction(ref_id, direction, places)
        result = cands if result is None else result & cands
    return result or set()


def place_at(cell, places=PLACES):
    for pid, pos in places.items():
        if pos == tuple(cell):
            return pid
    return None
