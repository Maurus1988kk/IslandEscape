"""Tappa 3 - Il bastone di mezzogiorno (premio: Tronchi).

Parte A: l'ombra di un bastone (modello del sole in logic/sun.py).
Parte B: caccia ai tronchi su una griglia 6x6 con i pulsanti N, E, S, O.
"""

import math
import random

import pygame

from .. import config as C
from .. import testi as T
from ..gfx import draw as G
from ..logic import grid as GR
from ..logic import sun as SUN
from ..ui import fonts
from ..ui.widgets import Button, Slider
from .base import StageScene
from .tappa1_spiaggia import choice_list

DISC_C = (845, 316)
DISC_R = 190
SUN_DIST = 212
SLIDER_RECT = (575, 572, 540, 48)
INSET = pygame.Rect(1066, 104, 196, 120)

CELL = 78
GX, GY = 440, 128
DPAD_C = (1095, 394)


def cell_center(cell):
    return (GX + (cell[0] + 0.5) * CELL, GY + (cell[1] + 0.5) * CELL)


def make_dpad(callback, center=DPAD_C, w=104, h=88, gap=10):
    cx, cy = center
    rects = {
        "N": (cx - w // 2, cy - h // 2 - h - gap, w, h),
        "S": (cx - w // 2, cy + h // 2 + gap, w, h),
        "O": (cx - w // 2 - w - 4, cy - h // 2, w, h),
        "E": (cx + w // 2 + 4, cy - h // 2, w, h),
    }
    buttons = {}
    for d, r in rects.items():
        b = DirButton(r, d, (lambda v=d: callback(v)))
        buttons[d] = b
    return buttons


class DirButton(Button):
    """Pulsante-freccia con la lettera del punto cardinale."""

    def __init__(self, rect, direction, on_click):
        super().__init__(rect, "", on_click, C.DIR_COLORS[direction], sound="click")
        self.direction = direction

    def draw(self, surf):
        if not self.visible:
            return
        icon, self.icon = self.icon, None
        super().draw(surf)
        self.icon = icon
        face = self.rect.move(0, 4 if self.press_t > 0 else 0)
        sgn = -1 if self.direction == "O" else 1
        arrow_c = (face.centerx + sgn * 22, face.centery)
        letter_c = (face.centerx - sgn * 24, face.centery)
        G.icon_arrow_dir(surf, arrow_c, 40, (255, 255, 255), self.direction)
        fonts.draw_outlined(surf, self.direction, letter_c, 36, C.WHITE, G.shade(self.color, 0.5), True, width=2)


class Tappa3(StageScene):
    stage = 3

    def __init__(self, app):
        super().__init__(app)
        self.phase = "intro"
        self.slider = Slider(SLIDER_RECT, 0.12, on_change=self._sun_changed)
        self.slider.label_mode = "sides"
        self.slider.enabled = False
        self.btn_done = Button(C.NEXT_BTN_RECT, "Fatto!", self._check_short, C.BTN_GREEN, icon="check")
        self.btn_done.visible = False
        self.n_mark = 0.0
        self.tip_glow = False
        # parte B
        self.grid_mode = False
        self.route_idx = 0
        self.cell = GR.GRID3_START
        self.draw_pos = list(cell_center(self.cell))
        self.facing = 0
        self.steps = 0
        self.trail = []
        self.found = []
        self.stuck = False
        self.show_path = False
        self.bump_t = 0.0
        self.dpad = make_dpad(self._move)
        for b in self.dpad.values():
            b.visible = False
        self.btn_restart = Button((930, 548, 330, 84), T.T3_RESTART, self._restart_route, C.BTN_TEAL, icon="restart")
        self.btn_restart.visible = False
        self.buttons = [self.btn_done, self.btn_restart] + list(self.dpad.values())
        rnd = random.Random(9)
        self.tufts = [(rnd.uniform(430, 1260), rnd.uniform(110, 630)) for _ in range(40)]

    def start(self):
        self.say(T.T3_INTRO, self._task_short)

    # ------------------------------------------------ parte A
    def _sun_changed(self, value):
        pass

    def _task_short(self):
        self.phase = "short"
        self.slider.enabled = True
        self.btn_done.visible = True
        self.task(T.T3_TASK_SHORT, T.T3_SHORT_HINT, T.T3_SHORT_HINT2)
        self.btn_done.visible = True

    def _check_short(self):
        if self.phase != "short":
            return
        if SUN.is_noon(self.slider.value):
            self.slider.value = SUN.NOON
            self.slider.enabled = False
            self.slider.marker = None
            self.btn_done.visible = False
            self.btn_done.flash(True)
            self.right(T.T3_SHORT_OK)
            self.phase = "wait"
            self.after(2.4, self._task_tip)
        else:
            self.btn_done.flash(False)
            self.wrong(T.T3_SHORT_WRONG)

    def _task_tip(self):
        self.phase = "tip"
        self.task(T.T3_TASK_TIP, T.T3_TIP_HINT, T.T3_TIP_HINT2)

    def shadow_tip(self, t=None):
        vx, vy = SUN.shadow_vector(self.slider.value if t is None else t)
        return (DISC_C[0] + vx, DISC_C[1] + vy)

    def _tap_tip(self, pos):
        tip = self.shadow_tip(SUN.NOON)
        d_tip = math.hypot(pos[0] - tip[0], pos[1] - tip[1])
        d_base = math.hypot(pos[0] - DISC_C[0], pos[1] - DISC_C[1])
        if d_tip <= 42 and d_tip <= d_base + 4:
            self.phase = "wait"
            self.n_mark = 0.01
            self.tip_glow = False
            self.right(T.T3_TIP_OK)
            self.after(2.6, self._task_bonus)
        else:
            self.wrong(T.T3_TIP_WRONG)

    def _task_bonus(self):
        self.phase = "bonus"
        self.slider.enabled = True
        self.task(T.T3_BONUS, T.T3_BONUS_HINT, T.T3_BONUS_HINT2, choices=choice_list(), on_choice=self._bonus)

    def _bonus(self, value, btn):
        if value == "O":
            btn.flash(True)
            self.clear_choices()
            self.slider.enabled = False
            self.right(T.T3_BONUS_OK)
            self.phase = "wait"
            self.after(3.2, self._start_grid)
        else:
            btn.flash(False)
            self.wrong()

    def on_hint(self, level):
        if self.phase == "short" and level >= 2:
            self.slider.marker = SUN.NOON
        if self.phase == "tip" and level >= 2:
            self.tip_glow = True
        if self.phase == "grid" and level >= 2:
            self.show_path = True

    # ------------------------------------------------ parte B
    def _start_grid(self):
        self.phase = "grid_intro"
        self.grid_mode = True
        self.slider.visible = False
        self.btn_done.visible = False
        self.say(T.T3_GRID_INTRO, lambda: self._start_route(0))

    def route_start(self, i=None):
        return GR.grid3_route_starts()[self.route_idx if i is None else i]

    def route_target(self):
        return GR.grid3_targets()[self.route_idx]

    def _start_route(self, i):
        self.route_idx = i
        self.cell = self.route_start(i)
        self.draw_pos = list(cell_center(self.cell))
        self.steps = 0
        self.trail = [self.cell]
        self.stuck = False
        self.show_path = False
        self.phase = "grid"
        for b in self.dpad.values():
            b.visible = True
            b.enabled = True
        self.btn_restart.visible = True
        self.btn_restart.pulse = False
        route = GR.GRID3_ROUTES[i]
        text = f"Percorso {i + 1}: " + GR.route_text(route)
        self.task(text, T.T3_GRID_HINT, T.T3_GRID_HINT2)

    def _restart_route(self):
        if self.phase != "grid":
            return
        self.cell = self.route_start()
        self.draw_pos = list(cell_center(self.cell))
        self.steps = 0
        self.trail = [self.cell]
        self.stuck = False
        self.btn_restart.pulse = False

    def _move(self, direction):
        if self.phase != "grid" or self.in_dialog or self.card is not None:
            return
        self.facing = {"N": 0, "E": 90, "S": 180, "O": 270}[direction]
        if self.stuck:
            self.btn_restart.pulse = True
            self.info(T.T3_GRID_WRONG)
            return
        nxt = GR.step(self.cell, direction)
        if not GR.in_bounds(nxt, GR.GRID3_COLS, GR.GRID3_ROWS):
            self.bump_t = 0.3
            self.info(T.T3_GRID_SEA)
            return
        if nxt in GR.GRID3_ROCKS:
            self.bump_t = 0.3
            self.info(T.T3_GRID_ROCK)
            return
        self.cell = nxt
        self.steps += 1
        self.trail.append(nxt)
        self.app.audio.play("step")
        route = GR.GRID3_ROUTES[self.route_idx]
        if self.steps >= GR.route_steps(route):
            if self.cell == self.route_target():
                self.found.append(self.cell)
                self.phase = "wait"
                for b in self.dpad.values():
                    b.enabled = False
                self.btn_restart.visible = False
                self.right(f"{T.T3_GRID_FOUND} ({len(self.found)} di 3)")
                if len(self.found) >= len(GR.GRID3_ROUTES):
                    self.complete(delay=2.2)
                else:
                    self.after(2.2, lambda: self._start_route(self.route_idx + 1))
            else:
                self.stuck = True
                self.btn_restart.pulse = True
                self.wrong(T.T3_GRID_WRONG)

    # ------------------------------------------------ ciclo
    def on_event(self, ev):
        if self.phase in ("short", "bonus"):
            self.slider.handle_event(ev)
        elif self.phase == "tip" and ev.type == pygame.MOUSEBUTTONDOWN and self.in_play(ev.pos):
            self._tap_tip(ev.pos)

    def on_update(self, dt):
        self.slider.update(dt)
        if self.n_mark:
            self.n_mark = min(1.0, self.n_mark + dt * 3)
        target = cell_center(self.cell)
        self.draw_pos[0] += (target[0] - self.draw_pos[0]) * min(1.0, dt * 14)
        self.draw_pos[1] += (target[1] - self.draw_pos[1]) * min(1.0, dt * 14)
        self.bump_t = max(0.0, self.bump_t - dt)

    def draw_background(self, surf):
        surf.blit(G.vgradient((C.WIDTH, C.HEIGHT), (232, 206, 140), (214, 182, 112)), (0, 0))
        for x, y in self.tufts:
            for k in range(3):
                G.thick_line(surf, (120, 160, 70), (x + k * 4, y), (x + k * 4 - 4 + k * 4, y - 12), 3)

    def draw_play(self, surf):
        if self.grid_mode:
            self.draw_grid(surf)
        else:
            self.draw_stick(surf)

    def draw_stick(self, surf):
        t = self.slider.value
        G.aa_circle(surf, (242, 222, 168), DISC_C, DISC_R)
        G.aa_ring(surf, (200, 170, 110), DISC_C, DISC_R, 4)
        for d, lab in ((0, "N"), (90, "E"), (180, "S"), (270, "O")):
            vx, vy = SUN.azimuth_to_vector(d)
            p0 = (DISC_C[0] + vx * (DISC_R - 22), DISC_C[1] + vy * (DISC_R - 22))
            p1 = (DISC_C[0] + vx * (DISC_R - 6), DISC_C[1] + vy * (DISC_R - 6))
            G.thick_line(surf, (190, 160, 100), p0, p1, 4)
        G.draw_compass_rose(surf, (488, 162), 36, label_size=22)
        # sole sul bordo
        az = SUN.sun_azimuth(t)
        elev = SUN.sun_elevation(t)
        vx, vy = SUN.azimuth_to_vector(az)
        sun_pos = (DISC_C[0] + vx * SUN_DIST, DISC_C[1] + vy * SUN_DIST)
        col = G.lerp_color((255, 120, 50), (255, 214, 60), (elev - 5) / 60)
        G.draw_sun(surf, sun_pos, 24, self.t, col)
        # ombra
        shadow = SUN.shadow_vector(t)
        G.draw_shadow(surf, DISC_C, shadow, 20)
        G.draw_stick_top(surf, DISC_C, 10)
        tip = self.shadow_tip(t)
        if self.tip_glow:
            k = 0.5 + 0.5 * math.sin(self.t * 6)
            G.aa_ring(surf, (255, 220, 40), tip, 30 + 6 * k, 6)
        if self.n_mark:
            k = G.ease_out_back(self.n_mark)
            ntip = self.shadow_tip(SUN.NOON)
            p = (ntip[0], ntip[1] - 40 * k)
            G.aa_circle(surf, (120, 20, 20), (p[0], p[1] + 3), 26 * k)
            G.aa_circle(surf, C.NORTH_RED, p, 26 * k)
            if k > 0.5:
                fonts.draw(surf, "N", p, 34, C.WHITE, True, anchor="center", transform=False)
        # il sole nel cielo (vista di lato, guardando verso Sud)
        G.rounded_rect(surf, (40, 30, 20), INSET.move(0, 4), 14)
        surf.blit(G.vgradient(INSET.size, (110, 180, 245), (200, 230, 255)), INSET.topleft)
        hy = INSET.bottom - 22
        pygame.draw.rect(surf, (130, 180, 90), (INSET.x, hy, INSET.w, INSET.bottom - hy))
        pts = [(INSET.x + 14 + (INSET.w - 28) * k, hy - (SUN.sun_elevation(k) - 5) / 60 * 70) for k in [i / 20 for i in range(21)]]
        for a, b in zip(pts[::2], pts[1::2]):
            G.thick_line(surf, (255, 255, 255), a, b, 2)
        sp = (INSET.x + 14 + (INSET.w - 28) * t, hy - (elev - 5) / 60 * 70)
        G.draw_sun(surf, sp, 11, 0, col, rays=False)
        stick_x = INSET.centerx
        G.thick_line(surf, C.WOOD_DARK, (stick_x, hy + 6), (stick_x, hy - 18), 4)
        fonts.draw(surf, "E", (INSET.x + 12, hy + 11), 20, C.TEXT_DARK, True, anchor="center", transform=False)
        fonts.draw(surf, "S", (INSET.centerx + 14, hy + 11), 20, C.TEXT_DARK, True, anchor="center", transform=False)
        fonts.draw(surf, "O", (INSET.right - 12, hy + 11), 20, C.TEXT_DARK, True, anchor="center", transform=False)
        fonts.draw(surf, "Il sole nel cielo", (INSET.centerx, INSET.y + 4), 20, C.TEXT_DARK, True, anchor="midtop")
        fonts.draw(surf, SUN.time_label(t), (INSET.centerx, INSET.bottom + 8), 24, C.TEXT_DARK, True, anchor="midtop")
        self.slider.draw(surf)

    def draw_grid(self, surf):
        area = pygame.Rect(GX - 14, GY - 14, CELL * GR.GRID3_COLS + 28, CELL * GR.GRID3_ROWS + 28)
        G.rounded_rect(surf, C.SEA_LIGHT, area.inflate(16, 16), 30)
        G.rounded_rect(surf, (240, 216, 150), area, 26)
        for c in range(GR.GRID3_COLS):
            for r in range(GR.GRID3_ROWS):
                rect = pygame.Rect(GX + c * CELL + 2, GY + r * CELL + 2, CELL - 4, CELL - 4)
                col = (126, 190, 96) if (c + r) % 2 == 0 else (114, 178, 88)
                G.rounded_rect(surf, col, rect, 10)
        for cell in GR.GRID3_ROCKS:
            G.draw_rock(surf, cell_center(cell), 28, seed=cell[0] * 7 + cell[1])
        G.draw_tent(surf, cell_center(GR.GRID3_START), 1.1)
        for cell in self.found:
            G.draw_logs(surf, cell_center(cell), 1.0)
        if self.show_path and self.phase == "grid":
            cells = GR.route_cells(self.route_start(), GR.GRID3_ROUTES[self.route_idx])
            k = 0.5 + 0.5 * math.sin(self.t * 5)
            for cell in cells:
                G.aa_circle(surf, (140, 100, 10), cell_center(cell), 11)
                G.aa_circle(surf, (255, 224, 50), cell_center(cell), 8 + 2 * k)
        for cell in self.trail[1:]:
            x, y = cell_center(cell)
            G.aa_ellipse(surf, (90, 120, 60), (x - 7, y + 4), 5, 8)
            G.aa_ellipse(surf, (90, 120, 60), (x + 7, y - 4), 5, 8)
        dx = math.sin(self.bump_t * 40) * 6 if self.bump_t > 0 else 0
        G.draw_explorer_top(surf, (self.draw_pos[0] + dx, self.draw_pos[1]), 1.15, self.facing)
        # pannello a destra
        route = GR.GRID3_ROUTES[self.route_idx]
        if self.phase in ("grid", "wait"):
            fonts.draw(surf, f"Passi: {self.steps} di {GR.route_steps(route)}", (1095, 128), 32, C.TEXT_DARK, True,
                       anchor="center")
        fonts.draw(surf, "Tronchi:", (985, 182), 28, C.TEXT_DARK, True, anchor="center")
        for i in range(3):
            p = (1080 + i * 64, 182)
            if i < len(self.found):
                G.draw_logs(surf, p, 0.6)
            else:
                G.aa_ring(surf, (150, 130, 90), p, 18, 3)
        G.aa_circle(surf, (250, 246, 230), DPAD_C, 30)
        G.draw_compass_rose(surf, DPAD_C, 26, labels=False)
