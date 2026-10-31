"""Strumento per sviluppatori: salva screenshot delle scene (senza aprire finestre).

    python tools/screenshots.py CARTELLA_DI_USCITA
"""

import os
import sys
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("FUGAISOLA_DATA_DIR", os.path.join(tempfile.gettempdir(), "fugaisola_screens"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import pygame  # noqa: E402

from game.app import App  # noqa: E402
from game.scenes import stage_classes  # noqa: E402


def run(app, frames=30):
    for _ in range(frames):
        app.frame(1 / 60)


def shot(app, out, name, frames=30):
    run(app, frames)
    pygame.image.save(app.canvas, os.path.join(out, name + ".png"))
    print("salvato", name)


def advance_dialog(scene, app):
    while scene.in_dialog:
        scene._next_line()
        run(app, 2)


def main(out):
    os.makedirs(out, exist_ok=True)
    app = App(fullscreen=False)
    shot(app, out, "00_menu")
    app.go_options()
    shot(app, out, "01_opzioni")
    app.go_team()
    shot(app, out, "02_squadra")
    app.new_game("Delfini")
    shot(app, out, "03_intro_a")
    for _ in range(3):
        app.scene._next()
    shot(app, out, "03_intro_b", 80)
    app.go_map(3)
    shot(app, out, "04_mappa", 120)
    S = stage_classes()
    for n, cls in S.items():
        app.state.prepare_stage(n)
        app.go_stage(n)
        shot(app, out, f"1{n}_tappa_a", 40)
        scene = app.scene
        advance_dialog(scene, app)
        shot(app, out, f"1{n}_tappa_b", 200)
    app.go_victory()
    shot(app, out, "20_vittoria", 90)
    app.shutdown()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "screenshots")
