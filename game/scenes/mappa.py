"""Mappa di avanzamento tra una tappa e l'altra."""

import math

import pygame

from .. import config as C
from .. import testi as T
from ..gfx import draw as G
from ..ui import fonts
from ..ui.parrot import Parrot
from ..ui.widgets import Button, InventoryBar, SpeechBubble
from .base import Scene, draw_timer

# posizioni delle tappe sull'isola (Nord in alto)
MARKERS = {
    1: (770, 560),
    2: (1110, 420),
    3: (800, 395),
    4: (455, 425),
    5: (630, 270),
    6: (930, 232),
    7: (930, 128),  # casa, sulla terraferma
}


def path_points(a, b, n=16):
    (x0, y0), (x1, y1) = MARKERS[a], MARKERS[b]
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    cx, cy = mx - dy * 0.15, my + dx * 0.15
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append(((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1,
                    (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1))
    return pts


class MapScene(Scene):
    in_game = True
    ambient = "waves"

    def __init__(self, app, next_stage):
        super().__init__(app)
        self.next_stage = max(1, min(6, int(next_stage)))
        self.parrot = Parrot((110, 296), 0.9)
        self.bubble = SpeechBubble((14, 372, 320, 168), (140, 360))
        self.btn_go = Button((40, 550, 260, 86), "Andiamo!", self._go, C.BTN_GREEN, icon="play")
        self.btn_go.pulse = True
        self.btn_pause = Button(C.PAUSE_BTN_RECT, "", app.open_pause, C.BTN_GRAY, icon="pause")
        self.inventory = InventoryBar(app.state)
        self.move_t = 0.0

    def enter(self):
        n = self.next_stage
        if n == 1:
            text = T.MAP_START
        elif n == 6:
            text = T.MAP_HOME
        else:
            text = f"{T.MAP_NEXT} {T.STAGE_TITLES[n]}!"
        self.bubble.set_text(text)
        self.parrot.talk(2.0)
        self.app.speak(text)

    def restart(self):
        return MapScene(self.app, self.next_stage)

    def _go(self):
        self.app.go_stage(self.next_stage)

    def handle_event(self, ev):
        if self.btn_pause.handle_event(ev):
            return
        self.btn_go.handle_event(ev)

    def update(self, dt):
        super().update(dt)
        self.move_t = min(1.0, self.move_t + dt / 1.6)
        self.parrot.update(dt)
        self.bubble.update(dt)
        self.btn_go.update(dt)
        self.btn_pause.update(dt)
        self.inventory.update(dt)

    def draw(self, surf):
        t = self.t
        G.draw_sea(surf, (0, 0, C.WIDTH, C.HEIGHT), t, rows=9)
        # terraferma a Nord
        pts = [(0, 92)] + [(x, 150 + 10 * math.sin(x * 0.02)) for x in range(0, 1300, 40)] + [(1280, 92)]
        G.aa_polygon(surf, C.SAND, [(x, y + 8) for x, y in pts])
        G.aa_polygon(surf, (110, 180, 90), pts)
        for i, x in enumerate((820, 880, 990, 1050)):
            G.draw_house(surf, (x, 124 - (i % 2) * 6), 0.7)
        fonts.draw_outlined(surf, "CASA (terraferma)", (560, 122), 30, C.WHITE, (40, 60, 40), True)
        # isola
        G.draw_island(surf, (790, 410), 420, 205, seed=8)
        for p in ((560, 330), (1000, 330), (700, 480), (980, 500), (520, 520)):
            G.draw_tree_top(surf, p, 22)
        for p in ((870, 300), (650, 400)):
            G.draw_palm_top(surf, p, 28, t)
        G.draw_compass_rose(surf, (1185, 600 - 30), 34, label_size=22)
        # percorso
        done = self.next_stage - 1
        for a in range(1, 7):
            pts = path_points(a, a + 1)
            if a < done:
                G.polyline(surf, (250, 200, 40), pts, 9)
            elif a == done:
                k = G.ease_in_out(self.move_t)
                n = max(1, int(len(pts) * k))
                for i in range(0, len(pts) - 1, 2):
                    G.thick_line(surf, (255, 255, 255), pts[i], pts[i + 1], 5)
                G.polyline(surf, (250, 200, 40), pts[:n + 1], 9)
            else:
                for i in range(0, len(pts) - 1, 2):
                    G.thick_line(surf, (255, 255, 255), pts[i], pts[i + 1], 5)
        for n in range(1, 7):
            p = MARKERS[n]
            if n <= done:
                G.badge(surf, p, 24, True)
            elif n == self.next_stage:
                k = 0.5 + 0.5 * math.sin(t * 5)
                G.aa_circle(surf, (255, 230, 60), p, 30 + 6 * k)
                G.aa_circle(surf, (214, 46, 46), p, 26)
                fonts.draw(surf, str(n), p, 32, C.WHITE, True, anchor="center", transform=False)
            else:
                G.aa_circle(surf, (60, 70, 100), p, 22)
                G.aa_circle(surf, (230, 230, 240), p, 18)
                fonts.draw(surf, str(n), p, 26, (60, 70, 100), True, anchor="center", transform=False)
        # esploratore
        if done >= 1:
            pts = path_points(done, done + 1)
            k = G.ease_in_out(self.move_t)
            idx = min(len(pts) - 1, int((len(pts) - 1) * k))
            pos = pts[idx]
        else:
            pos = MARKERS[1]
        G.draw_explorer_top(surf, (pos[0] + 30, pos[1] - 30), 1.1)
        # barra superiore e colonna di Bussolino
        G.alpha_rect(surf, pygame.Rect(0, 0, C.WIDTH, C.TOPBAR_H), (16, 26, 56, 165), 0)
        fonts.draw(surf, "Mappa dell'isola", (20, 22), 40, C.WHITE, True, shadow=(0, 0, 0))
        draw_timer(surf, self.app, (955, 46))
        if "rosa" in self.app.state.inventory:
            G.draw_compass_rose(surf, (1118, 46), 23, labels=True, label_size=19)
        self.btn_pause.draw(surf)
        self.parrot.draw(surf)
        self.bubble.draw(surf)
        self.btn_go.draw(surf)
        self.inventory.draw(surf)
