"""Test della logica pura: rosa dei venti, sole, indovinelli, percorsi, stelle."""

import math

import pytest

from game import config as C
from game.logic import grid as GR
from game.logic import places as PL
from game.logic import rose
from game.logic import stars as ST
from game.logic import sun as SUN


# ------------------------------------------------------------ rosa dei venti (tappa 1 e 2)
@pytest.mark.parametrize("east, expected", [
    ("right", {"top": "N", "right": "E", "bottom": "S", "left": "O"}),
    ("bottom", {"bottom": "E", "left": "S", "top": "O", "right": "N"}),   # esempio del testo
    ("left", {"left": "E", "top": "S", "right": "O", "bottom": "N"}),
    ("top", {"top": "E", "right": "S", "bottom": "O", "left": "N"}),
])
def test_rotated_rose_all_orientations(east, expected):
    assert rose.expected_layout(east) == expected
    assert rose.validate(expected, east)
    for side, d in expected.items():
        assert rose.is_correct(d, side, east)
        for other in rose.SIDES:
            if other != side:
                assert not rose.is_correct(d, other, east)


@pytest.mark.parametrize("east", rose.SIDES)
def test_rotated_rose_rules(east):
    """S a 90 gradi in senso orario dall'Est, O a 180, N a 90 in senso antiorario."""
    i = rose.SIDES.index(east)
    assert rose.side_for("E", east) == east
    assert rose.side_for("S", east) == rose.SIDES[(i + 1) % 4]
    assert rose.side_for("O", east) == rose.SIDES[(i + 2) % 4]
    assert rose.side_for("N", east) == rose.SIDES[(i - 1) % 4]


def test_rose_validate_rejects_wrong_or_incomplete():
    good = rose.expected_layout("right")
    swapped = dict(good, top="S", bottom="N")
    assert not rose.validate(swapped, "right")
    incomplete = {k: v for k, v in good.items() if k != "left"}
    assert not rose.validate(incomplete, "right")


def test_clockwise_order():
    assert [rose.next_clockwise(d) for d in "NESO"] == ["E", "S", "O", "N"]


# ------------------------------------------------------------ sole e ombra (tappa 3)
def test_noon_shadow_points_north_and_is_shortest():
    assert SUN.shadow_azimuth(0.5) == pytest.approx(0.0)
    assert SUN.azimuth_to_dir(SUN.shadow_azimuth(0.5)) == "N"
    noon = SUN.shadow_length(0.5)
    for i in range(101):
        t = i / 100
        if t != 0.5:
            assert SUN.shadow_length(t) >= noon
    vx, vy = SUN.shadow_vector(0.5)
    assert abs(vx) < 1e-6 and vy < 0  # verso l'alto dello schermo = Nord


def test_shadow_morning_west_evening_east():
    assert SUN.shadow_azimuth(0.0) == pytest.approx(270.0)
    assert SUN.azimuth_to_dir(SUN.shadow_azimuth(0.0)) == "O"
    assert SUN.shadow_azimuth(1.0) == pytest.approx(90.0)
    assert SUN.azimuth_to_dir(SUN.shadow_azimuth(1.0)) == "E"
    assert SUN.azimuth_to_dir(SUN.shadow_azimuth(0.25)) in ("O", "N")  # mattina: verso Nord-Ovest
    assert SUN.shadow_vector(0.25)[0] < 0                              # comunque verso Ovest


def test_sun_positions():
    assert SUN.sun_azimuth(0.0) == pytest.approx(90.0)    # sorge a Est
    assert SUN.sun_azimuth(0.5) == pytest.approx(180.0)   # mezzogiorno a Sud
    assert SUN.sun_azimuth(1.0) == pytest.approx(270.0)   # tramonta a Ovest
    assert SUN.sun_elevation(0.5) == pytest.approx(65.0)
    assert SUN.sun_elevation(0.0) == pytest.approx(5.0)


def test_shadow_is_clamped_and_noon_tolerance():
    assert SUN.shadow_length(0.0) <= SUN.MAX_SHADOW
    assert SUN.is_noon(0.5) and SUN.is_noon(0.55) and SUN.is_noon(0.45)
    assert not SUN.is_noon(0.3) and not SUN.is_noon(0.7)


# ------------------------------------------------------------ indovinelli (tappa 4)
def test_places_are_on_distinct_cells_inside_grid():
    cells = list(PL.PLACES.values())
    assert len(cells) == len(set(cells))
    assert 6 <= len(cells) <= 8
    for c, r in cells:
        assert 0 <= c < PL.MAP_COLS and 0 <= r < PL.MAP_ROWS


@pytest.mark.parametrize("riddle", PL.RIDDLES, ids=lambda r: r["answer"])
def test_each_riddle_has_exactly_one_answer(riddle):
    assert PL.solve(riddle["clues"]) == {riddle["answer"]}
    # anche leggendo "il posto più vicino in quella direzione" la risposta è la stessa
    for direction, ref in riddle["clues"]:
        if len(riddle["clues"]) == 1:
            assert PL.nearest_in_direction(ref, direction) == riddle["answer"]
        assert riddle["answer"] in PL.in_direction(ref, direction)


def test_last_riddle_needs_both_clues():
    last = PL.RIDDLES[-1]
    for clue in last["clues"]:
        assert len(PL.solve((clue,))) > 1


def test_riddle_answers_are_different():
    answers = [r["answer"] for r in PL.RIDDLES]
    assert len(set(answers)) == len(answers)


# ------------------------------------------------------------ percorsi (tappa 3)
def test_grid3_routes_are_solvable():
    starts = GR.grid3_route_starts()
    targets = GR.grid3_targets()
    assert len(GR.GRID3_ROUTES) == 3
    for start, route, target in zip(starts, GR.GRID3_ROUTES, targets):
        cells = GR.route_cells(start, route)
        assert cells, "percorso vuoto"
        for cell in cells:
            assert GR.grid3_can_enter(cell), f"il percorso passa per {cell}"
        assert cells[-1] == target
        assert target != start
        path = GR.bfs(GR.GRID3_COLS, GR.GRID3_ROWS, start, GR.grid3_can_enter, lambda p, t=target: p == t)
        assert path is not None
    assert len(set(targets)) == 3
    assert GR.GRID3_START not in GR.GRID3_ROCKS


def test_grid3_routes_get_harder():
    lengths = [len(r) for r in GR.GRID3_ROUTES]
    assert lengths == sorted(lengths) and lengths[0] < lengths[-1]
    steps = [GR.route_steps(r) for r in GR.GRID3_ROUTES]
    assert steps == sorted(steps)


def test_route_text():
    assert GR.route_text((("N", 2), ("E", 3))) == "2 passi a Nord, poi 3 passi a Est."
    assert GR.route_text((("S", 1),)) == "1 passo a Sud."


# ------------------------------------------------------------ mare (tappa 6)
def test_sea_map_shape():
    assert all(len(row) == GR.SEA_COLS for row in GR.SEA_MAP)
    assert GR.SEA_COLS == 8 and GR.SEA_ROWS == 10
    assert set(GR.SEA_MAP[0]) == {"L"}
    assert set(GR.SEA_MAP[-1]) == {"I"}
    assert GR.sea_is_free(GR.SEA_START)
    assert any("R" in row for row in GR.SEA_MAP) and any("W" in row for row in GR.SEA_MAP)


def test_sea_map_is_solvable_and_events_are_on_the_way():
    path = GR.sea_path()
    assert path is not None
    assert GR.sea_is_goal(path[-1])
    rows = [p[1] for p in path]
    assert GR.DAY_EVENT_ROW in rows and GR.NIGHT_EVENT_ROW in rows
    assert GR.DAY_EVENT_ROW > GR.NIGHT_EVENT_ROW
    # da ogni casella libera si può sempre arrivare a casa (nessun vicolo cieco)
    for r in range(GR.SEA_ROWS):
        for c in range(GR.SEA_COLS):
            if GR.sea_is_free((c, r)):
                assert GR.sea_path((c, r)) is not None, (c, r)


def test_straight_north_is_blocked():
    """La strada dritta verso Nord è bloccata: bisogna usare anche Est e Ovest."""
    c, r = GR.SEA_START
    blocked = any(not GR.sea_is_free((c, rr)) for rr in range(1, r))
    assert blocked


# ------------------------------------------------------------ stelle (tappa 5)
def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def test_polaris_is_about_five_times_the_pointer_distance():
    st = ST.projected()
    d_pointers = dist(st["Merak"], st["Dubhe"])
    d_polaris = dist(st["Dubhe"], st["Polaris"])
    assert 4.5 <= d_polaris / d_pointers <= 6.0


def test_polaris_lies_on_the_pointer_line():
    st = ST.projected()
    a, b, p = st["Merak"], st["Dubhe"], st["Polaris"]
    # oltre Dubhe, nella stessa direzione
    v = (b[0] - a[0], b[1] - a[1])
    w = (p[0] - b[0], p[1] - b[1])
    assert v[0] * w[0] + v[1] * w[1] > 0
    angle = math.degrees(abs(math.atan2(v[0] * w[1] - v[1] * w[0], v[0] * w[0] + v[1] * w[1])))
    assert angle < 6.0
    assert ST.distance_to_line(p, a, b) / dist(b, p) < 0.1
    # il prolungamento di 5 volte arriva vicino alla Polare
    assert dist(ST.pointer_point(st, 6.0), p) < 0.15 * dist(b, p)


def test_star_layout_on_screen():
    st = ST.projected()
    px, py = st["Polaris"]
    assert dist((px, py), ST.POLE_CENTER) < 10          # la Polare è quasi al centro della proiezione
    frac = (ST.HORIZON_Y - py) / ST.HORIZON_Y
    assert 0.35 <= frac <= 0.6                             # circa a metà altezza sopra l'orizzonte
    for name in ST.DIPPER:
        x, y = st[name]
        assert y < py, f"{name} deve stare sopra la Polare"
        assert C.PANEL_W + 20 < x < C.WIDTH - 20 and 20 < y < ST.HORIZON_Y - 40
    names = list(st)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            assert dist(st[a], st[b]) >= 38, (a, b)       # stelle abbastanza distanti per il tocco
    nx, ny = ST.north_point(st)
    assert nx == pytest.approx(px) and ny == ST.HORIZON_Y


def test_star_catalog_values():
    assert ST.STARS["Polaris"] == (2.53, 89.26)
    assert ST.STARS["Dubhe"] == (11.06, 61.75)
    assert ST.STARS["Merak"] == (11.03, 56.38)
    assert ST.STARS["Alkaid"] == (13.79, 49.31)
