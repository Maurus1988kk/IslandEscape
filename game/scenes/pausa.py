"""Finestre sopra la scena: pausa e tempo scaduto."""

import pygame

from .. import config as C
from .. import testi as T
from ..gfx import draw as G
from ..ui import fonts
from ..ui.parrot import Parrot
from ..ui.widgets import Button, SpeechBubble


class PauseOverlay:
    def __init__(self, app):
        self.app = app
        self.t = 0.0
        self.confirm = False
        x, w, h = 640 - 230, 460, 86
        self.buttons = [
            Button((x, 200, w, h), "Riprendi", app.close_overlay, C.BTN_GREEN, icon="play"),
            Button((x, 302, w, h), "Ricomincia tappa", app.restart_current, C.BTN_BLUE, icon="restart"),
            Button((x, 404, w, h), "Menu principale", app.go_menu, C.BTN_ORANGE, icon="home"),
            Button((x, 506, w, h), "Esci", self._ask_exit, C.BTN_RED, icon="exit"),
        ]
        self.confirm_buttons = [
            Button((420, 400, 200, 86), "Sì", app.quit, C.BTN_RED),
            Button((660, 400, 200, 86), "No", self._cancel_exit, C.BTN_GREEN),
        ]

    def _ask_exit(self):
        self.confirm = True

    def _cancel_exit(self):
        self.confirm = False

    def on_escape(self):
        if self.confirm:
            self.confirm = False
        else:
            self.app.close_overlay()

    def handle_event(self, ev):
        for b in (self.confirm_buttons if self.confirm else self.buttons):
            if b.handle_event(ev):
                return

    def update(self, dt):
        self.t += dt
        for b in self.buttons + self.confirm_buttons:
            b.update(dt)

    def draw(self, surf):
        G.alpha_rect(surf, pygame.Rect(0, 0, C.WIDTH, C.HEIGHT), (10, 16, 36, 170), 0)
        if self.confirm:
            G.panel(surf, (340, 230, 600, 290), (255, 252, 240), 30, border=C.BTN_RED)
            fonts.draw_wrapped(surf, "Volete davvero uscire dal gioco?", (380, 260, 520, 120), (36, 34, 32), C.TEXT_DARK, True)
            for b in self.confirm_buttons:
                b.draw(surf)
            return
        G.panel(surf, (380, 90, 520, 530), (255, 252, 240), 30, border=(40, 110, 200))
        fonts.draw(surf, "Pausa", (640, 145), 52, (30, 90, 180), True, anchor="center")
        for b in self.buttons:
            b.draw(surf)


class TimerOverlay:
    """Il tempo è finito, ma non si perde: si continua a giocare."""

    def __init__(self, app):
        self.app = app
        self.t = 0.0
        self.parrot = Parrot((330, 400), 1.5)
        self.parrot.happy(1.0)
        self.bubble = SpeechBubble((460, 250, 600, 220), (400, 330))
        self.bubble.set_text(T.TIMER_EXPIRED)
        self.btn = Button((600, 500, 340, 90), "Continuiamo!", self._go, C.BTN_GREEN, icon="play")
        self.btn.pulse = True
        app.speak(T.TIMER_EXPIRED)
        app.audio.play("pop")

    def _go(self):
        self.app.state.timer_expired_ack = True
        self.app.close_overlay()

    def on_escape(self):
        self._go()

    def handle_event(self, ev):
        self.btn.handle_event(ev)

    def update(self, dt):
        self.t += dt
        self.parrot.update(dt)
        self.bubble.update(dt)
        self.btn.update(dt)

    def draw(self, surf):
        G.alpha_rect(surf, pygame.Rect(0, 0, C.WIDTH, C.HEIGHT), (10, 16, 36, 170), 0)
        G.icon_clock(surf, (760, 180), 46, C.WHITE, (self.t % 4) / 4)
        self.parrot.draw(surf)
        self.bubble.draw(surf)
        self.btn.draw(surf)
