"""Tappa 5 - La notte stellata (premio: Stella Polare).

Le stelle del Grande Carro e la Polare sono nelle posizioni vere (logic/stars.py).
"""

import math
import random

import pygame

from .. import config as C
from .. import testi as T
from ..gfx import draw as G
from ..logic import stars as ST
from ..ui import fonts
from ..ui.widgets import DragGroup, Draggable
from .base import StageScene

N_HOME = (1170, 548)
EXTEND_TO = 6.6   # la linea arriva un po' oltre la Polare (5 volte dopo Dubhe = fattore 6)


def make_background_stars(stars, n=110, seed=None):
    rnd = random.Random(seed)
    a = stars["Merak"]
    b = ST.pointer_point(stars, EXTEND_TO)
    out = []
    tries = 0
    while len(out) < n and tries < 5000:
        tries += 1
        p = (rnd.uniform(0, C.WIDTH), rnd.uniform(4, ST.HORIZON_Y - 30))
        if any(math.hypot(p[0] - s[0], p[1] - s[1]) < 34 for s in stars.values()):
            continue
        # niente stelline vicino alla linea dei puntatori, per non confondere
        ax, ay = a
        bx, by = b
        L2 = (bx - ax) ** 2 + (by - ay) ** 2
        u = max(0.0, min(1.0, ((p[0] - ax) * (bx - ax) + (p[1] - ay) * (by - ay)) / L2))
        if math.hypot(p[0] - (ax + u * (bx - ax)), p[1] - (ay + u * (by - ay))) < 22:
            continue
        out.append((p, rnd.uniform(0.8, 1.8), rnd.uniform(0, 6.28), rnd.uniform(1.0, 3.0), rnd.randint(90, 170)))
    return out


class Tappa5(StageScene):
    stage = 5
    night = True
    topbar_alpha = 70
    panel_color = (0, 0, 20, 100)

    def __init__(self, app):
        super().__init__(app)
        self.stars = ST.projected()
        self.bg = make_background_stars(self.stars)
        self.phase = "intro"
        self.dipper_k = 0.0
        self.drawing = False
        self.selected = []
        self.line_k = 1.0
        self.extending = False
        self.polaris_found = False
        self.ruler = False
        self.pulse = set()
        self.target_glow = False
        self.n_label = Draggable(N_HOME, (92, 92), "N", C.NORTH_RED)
        self.n_label.visible = False
        self.n_label.on_drop = self._drop_n
        self.group = DragGroup([self.n_label])
        self.drag_groups = [self.group]
        self.n_placed = False
        self.palms = [(380, 150, 0.2), (455, 120, -0.15), (800, 160, -0.2), (1010, 130, 0.15), (1215, 170, -0.1)]

    def start(self):
        self.say(T.T5_INTRO, self._ask_find)

    def _nearest(self, pos, names, tol):
        best = None
        for n in names:
            x, y = self.stars[n]
            d = math.hypot(pos[0] - x, pos[1] - y)
            if d <= tol and (best is None or d < best[0]):
                best = (d, n)
        return best[1] if best else None

    # ------------------------------------------------ passo 1: il carro
    def _ask_find(self):
        self.phase = "find"
        self.task(T.T5_FIND, T.T5_FIND_HINT, T.T5_FIND_HINT2)

    def _tap_find(self, pos):
        if self._nearest(pos, ST.DIPPER, 36):
            self.phase = "wait"
            self.pulse = set()
            self.drawing = True
            self.btn_hint.visible = False
            self.right(T.T5_FIND_OK)
            self.after(3.6, self._ask_pointers)
        else:
            self.wrong(T.T5_FIND_WRONG)

    # ------------------------------------------------ passo 2: le due stelle
    def _ask_pointers(self):
        self.phase = "pointers"
        self.task(T.T5_POINTERS, T.T5_POINTERS_HINT, T.T5_POINTERS_HINT2)

    def _tap_pointers(self, pos):
        n = self._nearest(pos, ST.DIPPER, 26)
        if n in ST.POINTERS:
            if n in self.selected:
                return
            self.selected.append(n)
            self.pulse.discard(n)
            if len(self.selected) == 2:
                self.phase = "wait"
                self.pulse = set()
                self.btn_hint.visible = False
                self.right(T.T5_POINTERS_OK)
                self.after(2.2, self._start_line)
            else:
                self.right(T.T5_POINTERS_ONE, sound="pop")
        else:
            self.wrong(T.T5_POINTERS_WRONG)

    # ------------------------------------------------ passo 3: la linea
    def _start_line(self):
        self.phase = "line"
        self.extending = True
        self.task(T.T5_LINE, T.T5_LINE_HINT, T.T5_LINE_HINT2)

    def _tap_line(self, pos):
        x, y = self.stars["Polaris"]
        if math.hypot(pos[0] - x, pos[1] - y) <= 54:
            self.phase = "wait"
            self.polaris_found = True
            self.pulse = set()
            self.ruler = False
            self.btn_hint.visible = False
            self.right(T.T5_LINE_OK)
            self.after(2.4, self._ask_north)
        else:
            self.wrong(T.T5_LINE_WRONG)

    # ------------------------------------------------ passo 4: la N
    def _ask_north(self):
        self.phase = "north"
        self.n_label.visible = True
        self.n_label.glow = True
        self.task(T.T5_NORTH, T.T5_NORTH_HINT, T.T5_NORTH_HINT2)

    def north_target(self):
        x, _ = ST.north_point(self.stars)
        return (x, ST.HORIZON_Y - 24)

    def _drop_n(self, drag, pos):
        tx, ty = self.north_target()
        if abs(pos[0] - tx) <= 75 and pos[1] >= ST.HORIZON_Y - 130:
            drag.snap((tx, ty))
            drag.glow = False
            self.n_placed = True
            self.target_glow = False
            self.phase = "done"
            self.btn_hint.visible = False
            self.right(T.T5_NORTH_OK)
            self.complete(delay=2.4)
            return True
        if drag.moved > 30:
            self.wrong(T.T5_NORTH_WRONG)
        return False

    def on_hint(self, level):
        if self.phase == "find" and level >= 2:
            self.pulse = set(ST.DIPPER)
        elif self.phase == "pointers" and level >= 2:
            self.pulse = set(ST.POINTERS) - set(self.selected)
        elif self.phase == "line":
            self.ruler = True
            if level >= 2:
                self.pulse = {"Polaris"}
        elif self.phase == "north" and level >= 2:
            self.target_glow = True

    # ------------------------------------------------ ciclo
    @staticmethod
    def in_sky(pos):
        """Il cielo arriva fino al bordo alto: le stelle del carro sono sotto la barra del titolo."""
        return pos[0] > C.PANEL_W and pos[1] < C.INV_Y

    def on_event(self, ev):
        if self.phase == "north":
            self.group.handle_event(ev)
            return
        if ev.type != pygame.MOUSEBUTTONDOWN or not self.in_sky(ev.pos):
            return
        if self.phase == "find":
            self._tap_find(ev.pos)
        elif self.phase == "pointers":
            self._tap_pointers(ev.pos)
        elif self.phase == "line":
            self._tap_line(ev.pos)

    def on_update(self, dt):
        if self.drawing:
            self.dipper_k = min(len(ST.DIPPER_LINES), self.dipper_k + dt * 3.0)
        if self.extending:
            self.line_k = min(EXTEND_TO, self.line_k + dt * 2.2)
        self.group.update(dt)

    # ------------------------------------------------ disegno
    def draw_background(self, surf):
        surf.blit(G.vgradient((C.WIDTH, C.HEIGHT), C.NIGHT_TOP, C.NIGHT_BOTTOM), (0, 0))
        for p, r, ph, sp, base in self.bg:
            a = base + 50 * math.sin(self.t * sp + ph)
            c = int(max(40, min(230, a)))
            G.aa_circle(surf, (c, c, min(255, c + 30)), p, r)

    def draw_play(self, surf):
        st = self.stars
        # linee del carro
        n_full = int(self.dipper_k)
        for i, (a, b) in enumerate(ST.DIPPER_LINES):
            if i < n_full:
                G.thick_line(surf, (120, 170, 255), st[a], st[b], 3)
            elif i == n_full and self.dipper_k < len(ST.DIPPER_LINES):
                k = self.dipper_k - n_full
                end = (G.lerp(st[a][0], st[b][0], k), G.lerp(st[a][1], st[b][1], k))
                G.thick_line(surf, (120, 170, 255), st[a], end, 3)
        # linea dei puntatori
        if self.extending:
            end = ST.pointer_point(st, self.line_k)
            G.dashed_line(surf, (255, 230, 120), st["Merak"], end, 4, 14, 10, -self.t * 30)
        if self.ruler:
            self._draw_ruler(surf)
        # stelle
        for name in ST.DIPPER + ("Polaris",):
            x, y = st[name]
            tw = 0.85 + 0.15 * math.sin(self.t * 2.3 + x * 0.05)
            G.blit_glow(surf, (x, y), 32, (150, 160, 200), tw)
            G.draw_star(surf, (x, y), 12 * tw, (255, 250, 220))
            G.aa_circle(surf, (255, 255, 255), (x, y), 4.5)
            if name in self.pulse:
                k = 0.5 + 0.5 * math.sin(self.t * 6)
                G.aa_ring(surf, (255, 220, 60), (x, y), 22 + 8 * k, 4)
            if name in self.selected:
                G.aa_ring(surf, (120, 255, 140), (x, y), 22, 4)
        if self.dipper_k >= len(ST.DIPPER_LINES):
            mx, my = st["Mizar"]
            fonts.draw(surf, "Grande Carro", (mx + 10, my + 44), 24, (170, 200, 255), True, anchor="center")
        if self.polaris_found:
            x, y = st["Polaris"]
            G.aa_ring(surf, (255, 230, 120), (x, y), 26, 3)
            fonts.draw(surf, "Stella Polare", (x, y + 44), 26, (255, 236, 150), True, anchor="center")
        # orizzonte con le palme
        sil = (8, 10, 20)
        pts = [(0, ST.HORIZON_Y)] + [(x, ST.HORIZON_Y - 6 * math.sin(x * 0.01)) for x in range(0, 1300, 40)] + [(1280, 640), (0, 640)]
        for x, h, lean in self.palms:
            G.draw_palm(surf, (x, ST.HORIZON_Y + 4), h, self.t, lean, silhouette=sil)
        G.aa_polygon(surf, sil, pts)
        if self.target_glow:
            tx, ty = self.north_target()
            k = 0.5 + 0.5 * math.sin(self.t * 5)
            G.aa_ring(surf, (255, 220, 60), (tx, ty), 52 + 6 * k, 6)
        if self.n_placed or self.target_glow:
            tx, ty = self.north_target()
            px, py = st["Polaris"]
            G.dashed_line(surf, (255, 236, 150), (px, py + 18), (tx, ty - 50), 3, 10, 8)
        self.group.draw(surf)

    def _draw_ruler(self, surf):
        st = self.stars
        mx, my = st["Merak"]
        dx, dy = st["Dubhe"]
        vx, vy = dx - mx, dy - my
        L = math.hypot(vx, vy)
        nx, ny = -vy / L, vx / L
        G.thick_line(surf, (120, 255, 140), (mx, my), (dx, dy), 6)
        for i in range(1, 6):
            a = (dx + vx * (i - 1), dy + vy * (i - 1))
            b = (dx + vx * i, dy + vy * i)
            col = (255, 214, 60) if i % 2 else (255, 255, 255)
            G.thick_line(surf, col, (a[0] + nx * 12, a[1] + ny * 12), (b[0] + nx * 12, b[1] + ny * 12), 6)
            G.thick_line(surf, col, (b[0] + nx * 4, b[1] + ny * 4), (b[0] + nx * 22, b[1] + ny * 22), 3)
            mid = ((a[0] + b[0]) / 2 + nx * 32, (a[1] + b[1]) / 2 + ny * 32)
            fonts.draw_outlined(surf, str(i), mid, 24, col, (20, 20, 40), True, width=2)
