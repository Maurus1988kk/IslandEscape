"""Griglie della tappa 3 (caccia ai tronchi) e della tappa 6 (navigazione).

Coordinate (colonna, riga). La riga 0 è a Nord (in alto).
"""

from collections import deque

DELTAS = {"N": (0, -1), "E": (1, 0), "S": (0, 1), "O": (-1, 0)}
DIR_WORDS = {"N": "Nord", "E": "Est", "S": "Sud", "O": "Ovest"}


def step(pos, direction):
    dx, dy = DELTAS[direction]
    return (pos[0] + dx, pos[1] + dy)


def in_bounds(pos, cols, rows):
    return 0 <= pos[0] < cols and 0 <= pos[1] < rows


def route_cells(start, route):
    """Tutte le caselle visitate (esclusa la partenza) seguendo `route` = [(dir, passi), ...]."""
    cells = []
    pos = start
    for direction, count in route:
        for _ in range(count):
            pos = step(pos, direction)
            cells.append(pos)
    return cells


def route_end(start, route):
    cells = route_cells(start, route)
    return cells[-1] if cells else start


def route_steps(route):
    return sum(count for _, count in route)


def route_text(route):
    parts = []
    for direction, count in route:
        word = "passo" if count == 1 else "passi"
        parts.append(f"{count} {word} a {DIR_WORDS[direction]}")
    if len(parts) == 1:
        return parts[0] + "."
    return ", poi ".join(parts) + "."


def bfs(cols, rows, start, is_free, is_goal):
    """Percorso più breve (lista di caselle, partenza inclusa) oppure None."""
    queue = deque([start])
    prev = {start: None}
    while queue:
        cur = queue.popleft()
        if is_goal(cur):
            path = []
            while cur is not None:
                path.append(cur)
                cur = prev[cur]
            return path[::-1]
        for d in ("N", "E", "S", "O"):
            nxt = step(cur, d)
            if nxt in prev or not in_bounds(nxt, cols, rows):
                continue
            if not (is_free(nxt) or is_goal(nxt)):
                continue
            prev[nxt] = cur
            queue.append(nxt)
    return None


# ------------------------------------------------------------ tappa 3
GRID3_COLS = 6
GRID3_ROWS = 6
GRID3_START = (1, 5)
GRID3_ROCKS = frozenset({(0, 0), (2, 2), (5, 1), (3, 4), (4, 5)})
# Tre percorsi di difficoltà crescente. Ognuno parte dove finisce il precedente.
GRID3_ROUTES = (
    (("N", 2), ("E", 3)),
    (("N", 2), ("O", 3), ("S", 1)),
    (("O", 1), ("S", 3), ("E", 2), ("N", 1)),
)


def grid3_route_starts():
    starts = [GRID3_START]
    for route in GRID3_ROUTES[:-1]:
        starts.append(route_end(starts[-1], route))
    return starts


def grid3_targets():
    return [route_end(s, r) for s, r in zip(grid3_route_starts(), GRID3_ROUTES)]


def grid3_can_enter(pos):
    return in_bounds(pos, GRID3_COLS, GRID3_ROWS) and pos not in GRID3_ROCKS


# ------------------------------------------------------------ tappa 6
# L = terraferma (casa), I = isola, R = scoglio, W = mulinello, . = mare libero
SEA_MAP = (
    "LLLLLLLL",
    "..R...W.",
    ".W..R...",
    "...R..R.",
    "R....W..",
    "..W....R",
    ".R..R...",
    "...W..R.",
    "........",
    "IIIIIIII",
)
SEA_COLS = len(SEA_MAP[0])
SEA_ROWS = len(SEA_MAP)
SEA_START = (3, 8)
DAY_EVENT_ROW = 6     # l'evento del mattino scatta quando la zattera arriva alla riga 6
NIGHT_EVENT_ROW = 3   # l'evento della notte scatta alla riga 3


def sea_cell(pos):
    if not in_bounds(pos, SEA_COLS, SEA_ROWS):
        return "X"
    return SEA_MAP[pos[1]][pos[0]]


def sea_is_free(pos):
    return sea_cell(pos) == "."


def sea_is_goal(pos):
    return sea_cell(pos) == "L"


def sea_path(start=SEA_START):
    return bfs(SEA_COLS, SEA_ROWS, start, sea_is_free, sea_is_goal)
