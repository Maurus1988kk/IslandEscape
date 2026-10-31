"""Smoke test senza finestra (SDL dummy): ogni scena si apre, si aggiorna e si disegna."""

import random

import pygame
import pytest

from game import audio as A
from game import config as C
from game.scenes import stage_classes
from game.scenes.errore import ErrorScene
from game.scenes.intro import IntroScene
from game.scenes.mappa import MapScene
from game.scenes.menu import MenuScene, TeamScene
from game.scenes.opzioni import OptionsScene
from game.scenes.pausa import PauseOverlay, TimerOverlay
from game.scenes.vittoria import VictoryScene
from game.ui import fonts
from game.ui.widgets import Button

SCENES = {
    "menu": lambda app: MenuScene(app),
    "squadra": lambda app: TeamScene(app),
    "opzioni": lambda app: OptionsScene(app),
    "intro": lambda app: IntroScene(app),
    "mappa": lambda app: MapScene(app, 4),
    "vittoria": lambda app: VictoryScene(app),
    "errore": lambda app: ErrorScene(app),
}
for _n, _cls in stage_classes().items():
    SCENES[f"tappa{_n}"] = (lambda app, c=_cls: c(app))


def frames(app, n=10, dt=1 / 60):
    for _ in range(n):
        app.frame(dt)


@pytest.mark.parametrize("name", list(SCENES))
def test_scene_runs(app, name):
    app.state.prepare_stage(6)
    app.change_scene(SCENES[name](app))
    frames(app, 30)
    assert app.running


@pytest.mark.parametrize("name", list(SCENES))
def test_scene_survives_random_taps(app, name):
    """Tocchi e trascinamenti a caso non devono mai causare errori."""
    rnd = random.Random(hash(name) & 0xFFFF)
    app.state.prepare_stage(6)
    app.change_scene(SCENES[name](app))
    for i in range(160):
        Button.reset_cooldown()
        scene_before = app.scene
        pos = (rnd.randrange(C.WIDTH), rnd.randrange(C.HEIGHT))
        kind = rnd.random()
        target = app.target()
        if kind < 0.6:
            target.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))
            target = app.target()
            target.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos, button=1))
        else:
            target.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))
            pos2 = (rnd.randrange(C.WIDTH), rnd.randrange(C.HEIGHT))
            app.target().handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=pos2, rel=(0, 0), buttons=(1, 0, 0)))
            app.target().handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos2, button=1))
        frames(app, 3, 1 / 20)
        if not app.running:  # "Esci" premuto: si riparte
            app.running = True
        if isinstance(app.scene, ErrorScene) and not isinstance(scene_before, ErrorScene):
            pytest.fail("schermata di errore raggiunta")


def test_overlays(app):
    app.state.prepare_stage(2)
    app.go_stage(2)
    app.open_pause()
    assert isinstance(app.overlay, PauseOverlay)
    frames(app, 10)
    app.overlay = TimerOverlay(app)
    frames(app, 10)
    app.overlay.btn.fire()
    assert app.overlay is None and app.state.timer_expired_ack


def test_accented_letters_render():
    pygame.init()
    for size in (28, 30, 44):
        font = fonts.get(size)
        metrics = font.metrics("àèéìòùÀÈÉÌÒÙ")
        assert metrics is not None and None not in metrics
    surf = fonts.render("Città, perché, più", 30, (0, 0, 0))
    assert surf.get_width() > 100


def test_uppercase_option():
    fonts.set_uppercase(True)
    try:
        assert fonts.tx("è già così") == "È GIÀ COSÌ"
    finally:
        fonts.set_uppercase(False)
    assert fonts.tx("Nord") == "Nord"


def test_sounds_are_generated(app):
    for name, gen in A.GENERATORS.items():
        samples = gen(8000)
        assert samples and max(abs(s) for s in samples) <= 1.0, name
    data = A.to_bytes([0.0, 0.5, -0.5], -16, 2)
    assert len(data) == 3 * 2 * 2
    if app.audio.ok:
        app.audio.wait_ready()
        assert len(app.audio.sounds) == len(A.GENERATORS)
        app.audio.play("correct")


def test_audio_failure_is_silent(monkeypatch):
    pygame.init()

    def boom(*a, **k):
        raise pygame.error("nessun dispositivo audio")

    monkeypatch.setattr(pygame.mixer, "get_init", lambda: None)
    monkeypatch.setattr(pygame.mixer, "init", boom)
    au = A.Audio(True)
    assert not au.ok
    au.play("correct")          # non deve sollevare errori
    au.set_ambient("waves")
    au.set_enabled(False)


def test_window_scaling_and_mouse_conversion(app):
    pygame.display.set_mode((1920, 1080))
    assert app.to_logical((960, 540)) == (640, 360)
    pygame.display.set_mode((1000, 1000))     # finestra quadrata: bande nere sopra e sotto
    scale, ox, oy, sw, sh = app._view()
    assert ox == 0 and oy > 0 and sw == 1000
    assert app.to_logical((500, 10)) is None  # tocco sulla banda nera
    assert app.to_logical((0, oy)) == (0, 0)
    frames(app, 2)
