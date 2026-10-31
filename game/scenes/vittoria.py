"""Festa finale e diploma."""

import math

import pygame

from .. import config as C
from .. import testi as T
from ..gfx import draw as G
from ..ui import fonts
from ..ui.parrot import Parrot
from ..ui.widgets import Button
from .base import Scene
from .common import Confetti, draw_clouds


def format_time(seconds):
    m, s = divmod(int(seconds), 60)
    mm = "1 minuto" if m == 1 else f"{m} minuti"
    ss = "1 secondo" if s == 1 else f"{s} secondi"
    return f"{mm} e {ss}"


class VictoryScene(Scene):
    ambient = "waves"

    def __init__(self, app):
        super().__init__(app)
        self.parrot = Parrot((190, 650), 0.8, perch=False)
        self.parrot.flying = True
        self.confetti = Confetti(110)
        self.buttons = [
            Button((420, 626, 330, 84), T.VICTORY_AGAIN, app.go_team, C.BTN_GREEN, icon="restart"),
            Button((770, 626, 250, 84), T.VICTORY_MENU, app.go_menu, C.BTN_BLUE, icon="home"),
        ]
        self.timer_used = app.options.timer_minutes > 0
        self.elapsed = app.state.elapsed
        self.team = app.state.team_name

    def enter(self):
        self.app.audio.play("victory")
        text = T.VICTORY_TITLE
        if self.team:
            text = f"Bravissima, squadra {self.team}! " + text
        self.app.speak(text)

    def handle_event(self, ev):
        for b in self.buttons:
            if b.handle_event(ev):
                return

    def update(self, dt):
        super().update(dt)
        self.parrot.update(dt)
        a = self.t * 0.9
        self.parrot.x = 200 + math.sin(a) * 120
        self.parrot.y = 660 + math.sin(2 * a) * 22
        self.parrot.flip = math.cos(a) < 0
        self.confetti.update(dt)
        for b in self.buttons:
            b.update(dt)

    def draw(self, surf):
        t = self.t
        G.draw_sky(surf, (0, 0, C.WIDTH, 470))
        G.draw_sun(surf, (1180, 90), 46, t)
        draw_clouds(surf, t, y_max=300)
        G.draw_sea(surf, (0, 470, C.WIDTH, 250), t, rows=4)
        G.aa_polygon(surf, (110, 180, 90), [(0, 380), (300, 360), (700, 380), (1280, 350), (1280, 520), (0, 520)])
        G.aa_polygon(surf, C.SAND, [(0, 500), (1280, 490), (1280, 560), (0, 570)])
        for i, x in enumerate((60, 150, 250, 1150, 1230)):
            G.draw_house(surf, (x, 380 - (i % 2) * 8), 1.2)
        G.draw_raft(surf, (200, 560), 0.55)
        self.confetti.draw(surf)
        fonts.draw_outlined(surf, T.VICTORY_TITLE, (800, 46), 42, (255, 214, 60), (90, 40, 10), True, width=3)
        # diploma
        d = pygame.Rect(30, 90, 1220, 524)
        G.panel(surf, d, (253, 246, 222), 18, border=(176, 130, 60))
        G.rounded_rect(surf, (210, 170, 100), d.inflate(-20, -20), 12, 3)
        for sx in (d.x + 70, d.right - 70):
            G.aa_circle(surf, (200, 60, 50), (sx, d.y + 62), 40)
            G.aa_circle(surf, (226, 90, 70), (sx, d.y + 62), 33)
            G.draw_compass_rose(surf, (sx, d.y + 62), 22, labels=False)
        fonts.draw(surf, T.DIPLOMA_TITLE, (d.centerx, d.y + 46), 36, (140, 70, 20), True, anchor="center")
        info = []
        if self.team:
            info.append(f"Squadra: {self.team}")
        if self.timer_used:
            info.append(f"Tempo impiegato: {format_time(self.elapsed)}")
        y = d.y + 78
        if info:
            fonts.draw(surf, "   -   ".join(info), (d.centerx, y), 30, (30, 90, 180), True, anchor="midtop")
            y += 44
        y += 8
        row_h = (d.bottom - 26 - y) / len(T.DIPLOMA_RULES)
        for i, rule in enumerate(T.DIPLOMA_RULES):
            cy = y + row_h * (i + 0.5)
            G.draw_star(surf, (d.x + 56, cy), 18, (250, 200, 50), outline=(150, 100, 20))
            fonts.draw(surf, str(i + 1), (d.x + 56, cy + 1), 20, (120, 70, 10), True, anchor="center", transform=False)
            fonts.draw_wrapped(surf, rule, (d.x + 90, cy - row_h / 2, d.w - 120, row_h), (30, 28, 26, 24),
                               C.TEXT_DARK, False, "left", "center")
        self.parrot.draw(surf)
        for b in self.buttons:
            b.draw(surf)
