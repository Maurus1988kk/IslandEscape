"""Test di integrazione: si gioca ogni tappa dall'inizio alla fine simulando i tocchi."""

import pygame
import pytest

from game import save
from game import testi as T
from game.logic import grid as GR
from game.logic import places as PL
from game.logic import rose
from game.logic import stars as ST
from game.logic import sun as SUN
from game.scenes import stage_classes
from game.scenes.errore import ErrorScene
from game.scenes.mappa import MapScene
from game.scenes.menu import MenuScene
from game.scenes.pausa import PauseOverlay, TimerOverlay
from game.scenes.vittoria import VictoryScene
from game.ui.widgets import Button, CompleteCard, HintCard

DT = 1 / 30


def run(app, seconds):
    for _ in range(int(seconds / DT) + 1):
        app.frame(DT)


def tap(app, pos):
    Button.reset_cooldown()
    app.target().handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(int(pos[0]), int(pos[1])), button=1))
    app.target().handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=(int(pos[0]), int(pos[1])), button=1))
    run(app, 0.05)


def press(app, button):
    assert button.visible and button.enabled, f"pulsante non attivo: {button.text!r}"
    tap(app, button.rect.center)


def drag(app, start, end):
    Button.reset_cooldown()
    t = app.target()
    t.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(int(start[0]), int(start[1])), button=1))
    mid = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
    for p in (mid, end):
        t.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(int(p[0]), int(p[1])), rel=(0, 0), buttons=(1, 0, 0)))
    t.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=(int(end[0]), int(end[1])), button=1))
    run(app, 0.6)


def advance(app):
    scene = app.scene
    guard = 0
    while scene.in_dialog:
        press(app, scene.btn_next)
        guard += 1
        assert guard < 20
    run(app, 0.1)


def choose(app, label):
    for b in app.scene.choices:
        if b.text == label:
            press(app, b)
            return
    raise AssertionError(f"scelta {label!r} non trovata tra {[b.text for b in app.scene.choices]}")


def finish_stage(app, stage):
    scene = app.scene
    for _ in range(200):
        if isinstance(scene.card, CompleteCard):
            break
        run(app, 0.1)
    assert isinstance(scene.card, CompleteCard), "manca la schermata Tappa superata"
    run(app, 0.8)
    press(app, scene.card.btn)
    run(app, 2.0)
    assert isinstance(app.scene, MapScene), type(app.scene)
    assert app.scene.next_stage == stage + 1
    st = save.load_game()
    assert st is not None and st.last_completed == stage


def start_stage(app, n):
    app.state.prepare_stage(n)
    app.go_stage(n)
    run(app, 0.2)
    advance(app)
    return app.scene


# ------------------------------------------------------------ tappe
def play_stage1(app, make_errors=False):
    scene = start_stage(app, 1)
    layout = rose.expected_layout("right")
    if make_errors:
        n = next(d for d in scene.group.items if d.text == "N")
        for _ in range(4):
            drag(app, n.pos, scene.slots["bottom"].rect.center)
        assert scene.btn_hint.visible
        press(app, scene.btn_hint)
        assert isinstance(scene.card, HintCard) and scene.card.explicit
        assert scene.slots["top"].ghost == "N"
        press(app, scene.card.btn)
        assert scene.card is None
    for side, letter in layout.items():
        d = next(x for x in scene.group.items if x.text == letter)
        drag(app, d.pos, scene.slots[side].rect.center)
        assert scene.slots[side].content is d
    run(app, 2.2)
    advance(app)
    for _, ans in T.T1_ORDER_Q:
        choose(app, {"E": "Est", "S": "Sud", "O": "Ovest"}[ans])
        run(app, 1.5)
    finish_stage(app, 1)


def play_stage2(app, east):
    app.state.prepare_stage(2)
    app.change_scene(stage_classes()[2](app, east_side=east))
    run(app, 0.2)
    advance(app)
    scene = app.scene
    run(app, 3.5)
    choose(app, "Nord")
    assert scene.q_errors == 1
    choose(app, "Est")
    run(app, 2.8)
    assert scene.slots[east].content is scene.e_label
    for side, letter in rose.expected_layout(east).items():
        if letter == "E":
            continue
        d = next(x for x in scene.group.items if x.text == letter)
        drag(app, d.pos, scene.slots[side].rect.center)
        assert scene.slots[side].content is d, (east, side, letter)
    finish_stage(app, 2)


def play_stage3(app):
    from game.scenes import tappa3_mezzogiorno as M
    scene = start_stage(app, 3)
    press(app, scene.btn_done)              # troppo presto: errore gentile
    assert scene.q_errors == 1
    s = scene.slider
    drag(app, s.knob_center(), (s.rect.x + s.rect.w * 0.5, s.rect.centery))
    assert SUN.is_noon(s.value)
    press(app, scene.btn_done)
    run(app, 2.6)
    tap(app, (M.DISC_C[0] + 150, M.DISC_C[1]))   # lontano dalla punta
    assert scene.q_errors == 1
    tip = scene.shadow_tip(SUN.NOON)
    tap(app, tip)
    run(app, 2.8)
    choose(app, "Ovest")
    run(app, 3.4)
    advance(app)
    # percorso sbagliato (5 passi a Nord), poi "Ricomincia percorso"
    route = GR.GRID3_ROUTES[0]
    for _ in range(GR.route_steps(route)):
        press(app, scene.dpad["N"])
    assert scene.stuck and scene.q_errors == 1
    press(app, scene.dpad["E"])                  # bloccato finché non si ricomincia
    assert scene.cell == (GR.GRID3_START[0], GR.GRID3_START[1] - 5)
    press(app, scene.btn_restart)
    assert scene.cell == GR.GRID3_START and scene.steps == 0 and not scene.stuck
    for i, route in enumerate(GR.GRID3_ROUTES):
        assert scene.route_idx == i
        for direction, count in route:
            for _ in range(count):
                press(app, scene.dpad[direction])
        run(app, 2.6)
    assert len(scene.found) == 3
    finish_stage(app, 3)


def play_stage4(app):
    from game.scenes import tappa4_tramonto as M
    scene = start_stage(app, 4)
    choose(app, "Ovest")
    run(app, 2.8)
    advance(app)
    for i, riddle in enumerate(PL.RIDDLES):
        wrong = next(p for p in PL.PLACES if p != riddle["answer"] and p not in scene.found)
        tap(app, M.cell_center(PL.PLACES[wrong]))
        tap(app, M.cell_center(PL.PLACES[riddle["answer"]]))
        assert riddle["answer"] in scene.found
        run(app, 2.4)
    finish_stage(app, 4)


def play_stage5(app):
    scene = start_stage(app, 5)
    st = scene.stars
    tap(app, (1000, 400))                  # cielo vuoto
    assert scene.q_errors == 1
    tap(app, st["Mizar"])
    run(app, 3.8)
    tap(app, st["Alkaid"])                 # stella del manico: sbagliata
    tap(app, st["Merak"])
    tap(app, st["Dubhe"])
    run(app, 2.4)
    tap(app, st["Polaris"])
    run(app, 2.6)
    tx, ty = scene.north_target()
    drag(app, scene.n_label.pos, (tx + 300, ty))   # troppo lontano
    assert not scene.n_placed
    drag(app, scene.n_label.pos, (tx + 10, ty - 10))
    assert scene.n_placed
    finish_stage(app, 5)


def play_stage6(app):
    from game.scenes import tappa6_zattera as M
    scene = start_stage(app, 6)
    cards = {d.data: d for d in scene.group.items}
    drag(app, cards["vela"].pos, M.RAFT_C)    # ordine sbagliato
    assert scene.parts == []
    for item in ("tronchi", "corda", "vela"):
        drag(app, cards[item].pos, M.RAFT_C)
    assert scene.parts == ["tronchi", "corda", "vela"]
    run(app, 2.6)
    advance(app)
    # uno scoglio o un mulinello: si torna indietro senza perdere
    guard = 0
    while not isinstance(app.scene, VictoryScene):
        guard += 1
        assert guard < 60, "la zattera non arriva a casa"
        if scene.phase == "day":
            choose(app, T.T6_DAY_LEFT)
            choose(app, T.T6_DAY_RIGHT)
            run(app, 2.8)
            continue
        if scene.in_dialog:
            advance(app)
            continue
        if scene.phase == "night_q":
            stars, _ = scene.card_stars
            tap(app, stars["Vega"])
            tap(app, stars["Stella Polare"])
            run(app, 2.8)
            continue
        if scene.phase == "landed":
            run(app, 3.2)
            continue
        if scene.phase != "nav":
            run(app, 0.3)
            continue
        path = GR.sea_path(scene.cell)
        nxt = path[1]
        d = {(0, -1): "N", (1, 0): "E", (0, 1): "S", (-1, 0): "O"}[(nxt[0] - scene.cell[0], nxt[1] - scene.cell[1])]
        press(app, scene.dpad[d])
        run(app, 0.6)
    assert {"day", "night"} <= scene.events_done
    assert save.load_game() is None   # a fine gioco il salvataggio viene cancellato


@pytest.mark.parametrize("east", rose.SIDES)
def test_stage2_all_orientations(app, east):
    play_stage2(app, east)


def test_stage1_with_errors_and_hints(app):
    play_stage1(app, make_errors=True)


def test_stage3(app):
    play_stage3(app)


def test_stage4(app):
    play_stage4(app)


def test_stage5(app):
    play_stage5(app)


def test_stage6_and_victory(app):
    play_stage6(app)
    run(app, 1.0)
    assert isinstance(app.scene, VictoryScene)


def test_rock_bump_in_stage6(app):
    scene = start_stage(app, 6)
    scene.parts = ["tronchi", "corda", "vela"]
    scene._start_nav()
    advance(app)
    start = scene.cell
    press(app, scene.dpad["N"])            # (3,7) è un mulinello
    run(app, 1.0)
    assert scene.cell == start and scene.q_errors == 1
    press(app, scene.dpad["S"])            # c'è l'isola: avviso, non errore
    assert scene.cell == start and scene.q_errors == 1


# ------------------------------------------------------------ flussi generali
def test_full_new_game_flow(app):
    from game.scenes.intro import IntroScene
    app.go_menu()
    press(app, app.scene.buttons[0])                 # Nuova partita
    app.scene.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="Delfini"))
    press(app, app.scene.btn_start)
    assert isinstance(app.scene, IntroScene)
    assert app.state.team_name == "Delfini"
    for _ in range(len(app.scene.lines)):
        press(app, app.scene.btn)
    assert isinstance(app.scene, MapScene) and app.scene.next_stage == 1
    press(app, app.scene.btn_go)
    assert type(app.scene).__name__ == "Tappa1"


def test_continue_after_stage(app):
    play_stage1(app)
    app.go_menu()
    assert app.scene.has_save
    cont = next(b for b in app.scene.buttons if b.text == "Continua")
    press(app, cont)
    assert isinstance(app.scene, MapScene) and app.scene.next_stage == 2
    assert app.state.inventory == ["rosa"]


def test_pause_menu(app):
    scene = start_stage(app, 3)
    app.process_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, scancode=41, unicode=""))
    assert isinstance(app.overlay, PauseOverlay)
    press(app, app.overlay.buttons[1])               # Ricomincia tappa
    assert app.overlay is None and app.scene is not scene and type(app.scene) is type(scene)
    app.open_pause()
    press(app, app.overlay.buttons[3])               # Esci -> conferma
    assert app.overlay.confirm
    press(app, app.overlay.confirm_buttons[1])       # No
    assert app.running and not app.overlay.confirm
    press(app, app.overlay.buttons[2])               # Menu principale
    assert isinstance(app.scene, MenuScene)


def test_timer_expires_without_losing(app):
    app.options.timer_minutes = 30
    start_stage(app, 2)
    app.state.elapsed = 30 * 60 - 0.05
    run(app, 0.2)
    assert isinstance(app.overlay, TimerOverlay)
    press(app, app.overlay.btn)
    assert app.overlay is None and app.state.timer_expired_ack
    run(app, 0.5)
    assert app.overlay is None


@pytest.mark.parametrize("key, expected", [(pygame.K_1, "Tappa1"), (pygame.K_4, "Tappa4"), (pygame.K_6, "Tappa6"),
                                           (pygame.K_v, "VictoryScene")])
def test_teacher_shortcuts(app, key, expected):
    mods = pygame.KMOD_LCTRL | pygame.KMOD_LSHIFT
    app.process_event(pygame.event.Event(pygame.KEYDOWN, key=key, mod=mods, scancode=0, unicode=""))
    assert type(app.scene).__name__ == expected
    if expected == "Tappa6":
        assert app.state.inventory == ["rosa", "corda", "tronchi", "vela", "stella"]


def test_unexpected_error_shows_error_scene_and_log(app, data_dir):
    import logging
    import logging.handlers
    handler = logging.FileHandler(save.log_path(), encoding="utf-8")
    logging.getLogger("fuga").addHandler(handler)
    try:
        start_stage(app, 1)

        def broken(surf):
            raise RuntimeError("errore di prova")
        app.scene.draw = broken
        try:
            app.frame(DT)
        except RuntimeError:
            app.on_crash()
        assert isinstance(app.scene, ErrorScene)
        run(app, 0.2)
        handler.flush()
        assert "errore di prova" in save.log_path().read_text(encoding="utf-8")
        press(app, app.scene.buttons[0])
        assert isinstance(app.scene, MenuScene)
    finally:
        logging.getLogger("fuga").removeHandler(handler)
        handler.close()
