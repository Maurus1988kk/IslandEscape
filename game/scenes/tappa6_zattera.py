"""Tappa 6 - La zattera e il viaggio verso casa (vittoria)."""

import math
import random

import pygame

from .. import config as C
from .. import testi as T
from ..gfx import draw as G
from ..logic import grid as GR
from ..logic import stars as ST
from ..ui import fonts
from ..ui.widgets import DragGroup, Draggable, dash_rect
from .base import StageScene
from .tappa3_mezzogiorno import make_dpad

ORDER = ("tronchi", "corda", "vela")
RAFT_C = (790, 500)
BUILD_ZONE = pygame.Rect(560, 250, 470, 330)
CARD_HOMES = [(1168, 210), (1168, 352), (1168, 494)]

CELL = 50
GX, GY = 445, 114
DPAD_C = (1096, 400)
SKY_CARD = pygame.Rect(452, 112, 812, 500)


def cell_center(cell):
    return (GX + (cell[0] + 0.5) * CELL, GY + (cell[1] + 0.5) * CELL)


def draw_card(surf, rect, drag):
    G.rounded_rect(surf, (120, 90, 60), rect.move(0, 5), 18)
    G.rounded_rect(surf, (255, 250, 236), rect, 18)
    G.rounded_rect(surf, (200, 160, 90), rect, 18, 4)
    G.blit_item(surf, drag.data, (rect.centerx, rect.y + 46), 1.15)
    fonts.draw(surf, C.ITEM_NAMES[drag.data], (rect.centerx, rect.bottom - 22), 26, C.TEXT_DARK, True, anchor="center")


class Tappa6(StageScene):
    stage = 6

    def __init__(self, app):
        super().__init__(app)
        self.phase = "intro"
        # parte A
        self.parts = []
        self.anim = {}
        homes = CARD_HOMES[:]
        random.shuffle(homes)
        self.group = DragGroup()
        for item, home in zip(ORDER, homes):
            d = Draggable(home, (150, 122), "", data=item, drawer=draw_card)
            d.on_drop = self._drop
            d.visible = False
            self.group.add(d)
        self.drag_groups = [self.group]
        # parte B
        self.nav_mode = False
        self.cell = GR.SEA_START
        self.draw_pos = list(cell_center(self.cell))
        self.events_done = set()
        self.night = False
        self.night_k = 0.0
        self.sun_shown = False
        self.sky_card = False
        self.bump = None
        self.spin = 0.0
        self.show_path = False
        self.pulse_polaris = False
        self.dpad = make_dpad(self._move, DPAD_C)
        for b in self.dpad.values():
            b.visible = False
        self.buttons = list(self.dpad.values())
        rnd = random.Random(17)
        self.night_stars = [((rnd.uniform(430, 1270), rnd.uniform(100, 630)), rnd.uniform(0.8, 1.8), rnd.uniform(0, 6))
                            for _ in range(70)]
        self.card_stars = self._make_card_stars()

    def _make_card_stars(self):
        r = SKY_CARD
        polaris = (r.centerx + 30, r.y + 170)
        # piccolo Grande Carro che indica la Polare (stesse proporzioni della tappa 5)
        raw = ST.projected(0, 0, 3.6, ST.ROTATION)
        px, py = raw["Polaris"]
        dipper = {n: (polaris[0] + (x - px), polaris[1] + (y - py)) for n, (x, y) in raw.items() if n != "Polaris"}
        stars = {"Sirio": (r.x + 150, r.bottom - 140), "Stella Polare": polaris, "Vega": (r.right - 130, r.y + 270)}
        return stars, dipper

    def start(self):
        self.say(T.T6_INTRO, self._build_task)

    # ------------------------------------------------ parte A: costruzione
    def _build_task(self):
        self.phase = "build"
        for d in self.group.items:
            d.visible = True
        self._glow_next(False)
        self.task(T.T6_BUILD, T.T6_BUILD_HINT, T.T6_BUILD_HINT2)

    def _glow_next(self, only_next):
        nxt = ORDER[len(self.parts)] if len(self.parts) < 3 else None
        for d in self.group.items:
            d.glow = (d.data == nxt) if only_next else d.visible

    def _drop(self, drag, pos):
        if not BUILD_ZONE.collidepoint(pos):
            return False
        expected = ORDER[len(self.parts)]
        if drag.data == expected:
            self.parts.append(drag.data)
            self.anim[drag.data] = 0.0
            drag.visible = False
            drag.locked = True
            i = len(self.parts) - 1
            self.right(T.T6_BUILD_OK[i], sound="pop")
            self.app.audio.play("correct")
            if len(self.parts) == 3:
                self.phase = "wait"
                self.btn_hint.visible = False
                self.after(2.4, self._start_nav)
            elif self.hint_level >= 2:
                self._glow_next(True)
            return True
        if drag.data == "vela" and self.parts == ["tronchi"]:
            msg = T.T6_BUILD_WRONG_LATE
        else:
            msg = T.T6_BUILD_WRONG.get(drag.data, T.WRONG_DEFAULT)
        self.wrong(msg)
        return False

    # ------------------------------------------------ parte B: navigazione
    def _start_nav(self):
        self.nav_mode = True
        self.phase = "nav_intro"
        self.say(T.T6_SAIL_INTRO, self._resume_nav)

    def _resume_nav(self):
        self.phase = "nav"
        self.sky_card = False
        for b in self.dpad.values():
            b.visible = True
            b.enabled = True
        self.task(T.T6_NAV, T.T6_NAV_HINT, T.T6_NAV_HINT2)

    def _set_dpad(self, enabled):
        for b in self.dpad.values():
            b.enabled = enabled

    def _move(self, direction):
        if self.phase != "nav" or self.in_dialog or self.card is not None or self.bump is not None:
            return
        nxt = GR.step(self.cell, direction)
        kind = GR.sea_cell(nxt)
        if kind == "X":
            self.info(T.T6_EDGE)
            return
        if kind == "I":
            self.info(T.T6_ISLAND)
            return
        if kind in ("R", "W"):
            self.bump = [self.cell, nxt, 0.0, kind]
            self.wrong(T.T6_ROCK if kind == "R" else T.T6_WHIRL)
            return
        self.cell = nxt
        self.app.audio.play("step")
        if kind == "L":
            self.phase = "landed"
            self._set_dpad(False)
            self.btn_hint.visible = False
            self.right(T.T6_LAND, sound="victory")
            self.bubble.set_text(T.T6_LAND)
            self.after(2.8, self.app.go_victory)
            return
        row = nxt[1]
        if "day" not in self.events_done and row <= GR.DAY_EVENT_ROW:
            self.events_done.add("day")
            self.after(0.4, self._day_event)
            self.phase = "event"
        elif "night" not in self.events_done and row <= GR.NIGHT_EVENT_ROW:
            self.events_done.add("night")
            self.after(0.4, self._night_event)
            self.phase = "event"

    def _day_event(self):
        self.phase = "day"
        self._set_dpad(False)
        self.task(T.T6_DAY_Q, T.T6_DAY_HINT, T.T6_DAY_HINT2,
                  choices=[(T.T6_DAY_LEFT, "L", C.BTN_BLUE), (T.T6_DAY_RIGHT, "R", C.BTN_BLUE)],
                  on_choice=self._day_answer)

    def _day_answer(self, value, btn):
        if value == "R":
            btn.flash(True)
            self.clear_choices()
            self.sun_shown = True
            self.right(T.T6_DAY_OK)
            self.phase = "wait"
            self.after(2.6, self._resume_nav)
        else:
            btn.flash(False)
            self.wrong()

    def _night_event(self):
        self.phase = "wait"
        self._set_dpad(False)
        self.night = True
        self.sun_shown = False
        self.say([T.T6_NIGHT_INTRO], self._night_question)

    def _night_question(self):
        self.phase = "night_q"
        self.sky_card = True
        for b in self.dpad.values():
            b.visible = False
        self.task(T.T6_NIGHT_Q, T.T6_NIGHT_HINT, T.T6_NIGHT_HINT2)

    def _tap_star(self, pos):
        stars, _ = self.card_stars
        best = None
        for name, p in stars.items():
            d = math.hypot(pos[0] - p[0], pos[1] - p[1])
            if d <= 70 and (best is None or d < best[0]):
                best = (d, name)
        if best is None:
            return
        correct = dict(T.T6_STARS).get(best[1], False)
        if correct:
            self.phase = "wait"
            self.pulse_polaris = False
            self.btn_hint.visible = False
            self.right(T.T6_NIGHT_OK)
            self.after(2.6, self._resume_nav)
        else:
            self.wrong()

    def on_hint(self, level):
        if level < 2:
            return
        if self.phase == "build":
            self._glow_next(True)
        elif self.phase == "nav":
            self.show_path = True
        elif self.phase == "night_q":
            self.pulse_polaris = True

    # ------------------------------------------------ ciclo
    def on_event(self, ev):
        if self.phase == "build":
            self.group.handle_event(ev)
        elif self.phase == "night_q" and ev.type == pygame.MOUSEBUTTONDOWN and self.in_play(ev.pos):
            self._tap_star(ev.pos)

    def on_update(self, dt):
        self.group.update(dt)
        for k in self.anim:
            self.anim[k] = min(1.0, self.anim[k] + dt * 2.0)
        if self.night:
            self.night_k = min(1.0, self.night_k + dt / 2.0)
        if self.bump is not None:
            self.bump[2] += dt
            if self.bump[2] >= 0.7:
                self.bump = None
        target = cell_center(self.cell)
        self.draw_pos[0] += (target[0] - self.draw_pos[0]) * min(1.0, dt * 12)
        self.draw_pos[1] += (target[1] - self.draw_pos[1]) * min(1.0, dt * 12)

    # ------------------------------------------------ disegno
    def draw_background(self, surf):
        if not self.nav_mode:
            G.draw_sky(surf, (0, 0, C.WIDTH, 260))
            G.draw_sun(surf, (494, 150), 36, self.t)
            G.draw_sea(surf, (0, 260, C.WIDTH, 170), self.t, rows=3)
            pts = [(0, 440)] + [(x, 430 + 8 * math.sin(x * 0.013 + self.t)) for x in range(0, 1300, 40)] + [(1280, 720), (0, 720)]
            G.aa_polygon(surf, C.SAND, pts)
            G.draw_palm(surf, (470, 470), 160, self.t, 0.22)
            return
        G.draw_sea(surf, (0, 0, C.WIDTH, C.HEIGHT), self.t, rows=8)

    def draw_play(self, surf):
        if not self.nav_mode:
            self._draw_build(surf)
        else:
            self._draw_nav(surf)

    def _draw_build(self, surf):
        if len(self.parts) < 3:
            outline = pygame.Rect(0, 0, 240, 44)
            outline.center = (RAFT_C[0], RAFT_C[1])
            dash_rect(surf, outline.inflate(10, 10), (120, 90, 50), 3, 14, t=self.t)
            G.dashed_line(surf, (120, 90, 50), (RAFT_C[0], RAFT_C[1] - 30), (RAFT_C[0], RAFT_C[1] - 200), 3, 12, 10)
            fonts.draw(surf, "La zattera", (RAFT_C[0], RAFT_C[1] + 60), 30, (110, 80, 40), True, anchor="center")
        if self.parts:
            G.draw_raft(surf, RAFT_C, 1.0, tuple(self.parts), self.anim)
        for i, item in enumerate(ORDER):
            x = 640 + i * 150
            done = item in self.parts
            G.rounded_rect(surf, (255, 255, 255) if done else (240, 230, 210), (x - 62, 124, 124, 54), 14)
            fonts.draw(surf, f"{i + 1}.", (x - 40, 151), 26, C.TEXT_DARK, True, anchor="center", transform=False)
            if done:
                G.blit_item(surf, item, (x + 16, 151), 0.6)
                G.badge(surf, (x + 54, 128), 14, True)
            else:
                fonts.draw(surf, "?", (x + 16, 151), 30, (150, 140, 120), True, anchor="center", transform=False)
        self.group.draw(surf)

    def _draw_nav(self, surf):
        t = self.t
        area = pygame.Rect(GX, GY, CELL * GR.SEA_COLS, CELL * GR.SEA_ROWS)
        G.rounded_rect(surf, (20, 80, 150), area.inflate(12, 12), 14)
        for r, row in enumerate(GR.SEA_MAP):
            for c, ch in enumerate(row):
                rect = pygame.Rect(GX + c * CELL, GY + r * CELL, CELL, CELL)
                center = rect.center
                if ch == "L":
                    pygame.draw.rect(surf, (110, 180, 90), rect)
                    if c % 2 == 0:
                        G.draw_house(surf, (center[0], center[1] + 4), 0.55)
                    else:
                        G.draw_tree_top(surf, center, 14)
                elif ch == "I":
                    pygame.draw.rect(surf, C.SAND, rect)
                    if c % 3 == 1:
                        G.draw_palm_top(surf, center, 18, t)
                else:
                    col = (40, 140, 205) if (c + r) % 2 == 0 else (36, 130, 196)
                    pygame.draw.rect(surf, col, rect)
                    if ch == "R":
                        G.draw_rock(surf, center, 19, seed=c * 13 + r)
                    elif ch == "W":
                        G.draw_whirlpool(surf, center, 20, t)
        fonts.draw_outlined(surf, "CASA", (GX + area.w / 2, GY + 25), 28, C.WHITE, (40, 70, 40), True)
        if self.show_path and self.phase == "nav":
            path = GR.sea_path(self.cell) or []
            k = 0.5 + 0.5 * math.sin(t * 5)
            for cell in path[1:]:
                G.aa_circle(surf, (140, 100, 10), cell_center(cell), 8)
                G.aa_circle(surf, (255, 224, 50), cell_center(cell), 6 + 2 * k)
        # zattera
        pos = list(self.draw_pos)
        if self.bump is not None:
            a, b, bt, kind = self.bump
            ca, cb = cell_center(a), cell_center(b)
            k = math.sin(min(1.0, bt / 0.7) * math.pi) * 0.55
            pos = [G.lerp(ca[0], cb[0], k), G.lerp(ca[1], cb[1], k)]
        if self.night_k > 0:
            G.alpha_rect(surf, area, (5, 10, 40, int(150 * self.night_k)), 0)
            for p, r, ph in self.night_stars:
                if area.collidepoint(p):
                    continue
                c = int(140 + 80 * math.sin(t * 2 + ph))
                G.aa_circle(surf, (c, c, 255), p, r)
            G.blit_glow(surf, pos, 46, (110, 90, 30), self.night_k)
        G.draw_raft_top(surf, pos, CELL, t, self.night)
        if self.night_k > 0 and not self.sky_card:
            G.blit_glow(surf, (GX + area.w / 2, GY - 6), 26, (100, 100, 60), self.night_k)
            G.draw_star(surf, (GX + area.w / 2, GY - 6), 9, (255, 246, 200))
        if self.sun_shown:
            G.draw_sun(surf, (GX + area.w + 34, self.draw_pos[1]), 24, t)
            fonts.draw(surf, "Est", (GX + area.w + 34, self.draw_pos[1] + 44), 24, C.WHITE, True, anchor="center",
                       shadow=(0, 0, 0))
        G.aa_circle(surf, (250, 246, 230), DPAD_C, 30)
        G.draw_compass_rose(surf, DPAD_C, 26, labels=False)
        if self.sky_card:
            self._draw_sky_card(surf)

    def _draw_sky_card(self, surf):
        r = SKY_CARD
        G.panel(surf, r, (10, 16, 50), 26, border=(120, 150, 230))
        stars, dipper = self.card_stars
        for a, b in ST.DIPPER_LINES:
            G.thick_line(surf, (80, 110, 190), dipper[a], dipper[b], 2)
        for p in dipper.values():
            G.draw_star(surf, p, 6, (220, 230, 255))
        G.dashed_line(surf, (150, 160, 110), dipper["Merak"], ST.pointer_point({"Merak": dipper["Merak"], "Dubhe": dipper["Dubhe"]}, 5.6), 2, 8, 8)
        G.aa_polygon(surf, (6, 8, 20), [(r.x + 6, r.bottom - 60), (r.centerx, r.bottom - 76), (r.right - 6, r.bottom - 58),
                                         (r.right - 6, r.bottom - 6), (r.x + 6, r.bottom - 6)])
        for name, p in stars.items():
            tw = 0.85 + 0.15 * math.sin(self.t * 3 + p[0])
            G.blit_glow(surf, p, 52, (150, 150, 110), tw)
            G.draw_star(surf, p, 28 * tw, (255, 246, 200), outline=(140, 120, 60))
            if name == "Stella Polare" and self.pulse_polaris:
                k = 0.5 + 0.5 * math.sin(self.t * 6)
                G.aa_ring(surf, (255, 220, 60), p, 40 + 8 * k, 5)
            fonts.draw(surf, name, (p[0], p[1] + 54), 30, (230, 236, 255), True, anchor="center")
