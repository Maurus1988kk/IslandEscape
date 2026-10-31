"""Introduzione: la tempesta e il naufragio."""

import math
import random

import pygame

from .. import config as C
from .. import testi as T
from ..gfx import draw as G
from ..ui import fonts
from ..ui.parrot import Parrot
from ..ui.widgets import Button, SpeechBubble
from .base import Scene
from .common import draw_clouds


class IntroScene(Scene):
    in_game = True
    ambient = "waves"

    def __init__(self, app):
        super().__init__(app)
        self.lines = T.intro_lines(app.state.team_name)
        self.idx = 0
        self.parrot = Parrot((215, 520), 1.45)
        self.bubble = SpeechBubble((380, 462, 880, 150), (300, 470))
        self.btn = Button((1000, 626, 260, 86), "Avanti", self._next, C.BTN_GREEN, icon="play")
        self.btn_pause = Button(C.PAUSE_BTN_RECT, "", app.open_pause, C.BTN_GRAY, icon="pause")
        self.rng = random.Random(5)
        self.rain = [[self.rng.uniform(0, 1280), self.rng.uniform(0, 720), self.rng.uniform(500, 800)] for _ in range(120)]
        self.flash = 0.0
        self.next_flash = 1.0
        self.calm = 0.0

    def enter(self):
        self._show()

    def restart(self):
        return IntroScene(self.app)

    def _show(self):
        text = self.lines[self.idx]
        self.bubble.set_text(text)
        self.parrot.talk(min(3.0, 0.5 + len(text) * 0.035))
        self.app.speak(text)
        last = self.idx == len(self.lines) - 1
        self.btn.text = T.INTRO_READY if last else "Avanti"
        self.btn.pulse = last

    def _next(self):
        if self.idx < len(self.lines) - 1:
            self.idx += 1
            self._show()
        else:
            self.app.go_map(1)

    def handle_event(self, ev):
        if self.btn_pause.handle_event(ev):
            return
        self.btn.handle_event(ev)

    @property
    def stormy(self):
        return self.idx <= 1

    def update(self, dt):
        super().update(dt)
        self.parrot.update(dt)
        self.bubble.update(dt)
        self.btn.update(dt)
        self.btn_pause.update(dt)
        target = 0.0 if self.stormy else 1.0
        self.calm += (target - self.calm) * min(1.0, dt * 1.5)
        if self.stormy:
            self.next_flash -= dt
            if self.next_flash <= 0:
                self.flash = 0.25
                self.next_flash = self.rng.uniform(1.5, 3.5)
        self.flash = max(0.0, self.flash - dt)
        for d in self.rain:
            d[1] += d[2] * dt
            d[0] -= d[2] * 0.25 * dt
            if d[1] > 720:
                d[1] = -10
                d[0] = self.rng.uniform(0, 1400)

    def draw(self, surf):
        k = self.calm
        top = G.lerp_color((40, 44, 70), C.SKY_TOP, k)
        bottom = G.lerp_color((90, 96, 120), C.SKY_BOTTOM, k)
        horizon = 300
        G.vgradient_live(surf, (0, 0, C.WIDTH, horizon), top, bottom)
        if k > 0.3:
            G.draw_sun(surf, (1100, 100), 50, self.t)
        draw_clouds(surf, self.t * (3 - 2 * k), G.lerp_color((70, 74, 96), (255, 255, 255), k), y_max=260)
        sea_top = G.lerp_color((40, 70, 100), C.SEA_LIGHT, k)
        sea_bot = G.lerp_color((20, 40, 70), C.SEA_DEEP, k)
        amp = 12 - 7 * k
        G.draw_sea(surf, (0, horizon, C.WIDTH, C.HEIGHT - horizon), self.t * (2 - k), sea_top, sea_bot, rows=7, amp=amp)
        if self.stormy:
            for i, x in enumerate((640, 860)):
                y = 390 + math.sin(self.t * 3 + i) * 14
                G.draw_broken_canoe(surf, (x, y), 1.3, math.sin(self.t * 2.5 + i) * 0.25, (196, 92, 52))
            for x, y, _ in self.rain:
                pygame.draw.line(surf, (190, 200, 230), (int(x), int(y)), (int(x - 6), int(y + 18)), 2)
            if self.flash > 0:
                veil = pygame.Surface((C.WIDTH, C.HEIGHT))
                veil.fill((255, 255, 255))
                veil.set_alpha(int(160 * self.flash / 0.25))
                surf.blit(veil, (0, 0))
        else:
            G.draw_island(surf, (800, 350), 330, 90, seed=3)
            G.draw_palm(surf, (700, 340), 150, self.t, 0.2)
            G.draw_palm(surf, (900, 330), 120, self.t, -0.1)
            G.draw_broken_canoe(surf, (600, 392), 0.9, 0.2)
            G.draw_broken_canoe(surf, (1010, 388), 0.8, -0.3, (60, 140, 200))
            if self.idx >= 3:
                # casa a Nord: freccia verso l'alto e la terraferma lontana
                G.aa_ellipse(surf, (110, 170, 90), (800, horizon + 4), 260, 14)
                for x in (720, 780, 850):
                    G.draw_house(surf, (x, horizon - 6), 0.5)
                G.arrow(surf, (214, 46, 46), (520, 250), (520, 150), 12, 34)
                fonts.draw_outlined(surf, "NORD", (520, 120), 40, (214, 46, 46), C.WHITE, True)
                fonts.draw_outlined(surf, "Casa", (800, horizon - 50), 32, C.WHITE, (40, 40, 60), True)
        self.parrot.draw(surf)
        self.bubble.draw(surf)
        self.btn.draw(surf)
        self.btn_pause.draw(surf)
