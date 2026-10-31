"""Schermata mostrata se succede un errore imprevisto: il gioco non si chiude da solo."""

from .. import config as C
from .. import save
from ..gfx import draw as G
from ..ui import fonts
from ..ui.parrot import Parrot
from ..ui.widgets import Button
from .base import Scene


class ErrorScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.parrot = Parrot((250, 380), 1.6)
        self.parrot.think(5)
        self.buttons = [
            Button((480, 470, 360, 90), "Torna al menu", app.go_menu, C.BTN_GREEN, icon="home"),
            Button((860, 470, 240, 90), "Esci", app.quit, C.BTN_RED, icon="exit"),
        ]

    def handle_event(self, ev):
        for b in self.buttons:
            if b.handle_event(ev):
                return

    def update(self, dt):
        super().update(dt)
        self.parrot.update(dt)
        for b in self.buttons:
            b.update(dt)

    def draw(self, surf):
        surf.fill((40, 70, 120))
        G.panel(surf, (420, 150, 760, 440), (255, 252, 240), 30, border=C.BTN_ORANGE)
        fonts.draw(surf, "Ops! Qualcosa non ha funzionato.", (800, 210), 38, C.TEXT_DARK, True, anchor="center")
        fonts.draw_wrapped(surf, "Niente paura: potete tornare al menu e continuare a giocare. "
                                 "Per l'adulto: i dettagli sono nel file log.txt.",
                           (460, 250, 680, 150), (30, 28), C.TEXT_DARK)
        fonts.draw(surf, str(save.log_path()), (800, 420), 20, C.TEXT_SOFT, anchor="center", transform=False)
        self.parrot.draw(surf)
        for b in self.buttons:
            b.draw(surf)
