"""Tappa 1 - La spiaggia del naufragio (premio: Rosa dei venti)."""

import math
import random

import pygame

from .. import config as C
from .. import testi as T
from ..gfx import draw as G
from ..logic import rose
from ..ui.widgets import DragGroup, Draggable, DropSlot
from .base import StageScene

CENTER = (800, 366)
SLOT_DIST = 166
SLOT_SIZE = 104


def slot_rects(center=CENTER, dist=(SLOT_DIST, SLOT_DIST)):
    rects = {}
    for side in rose.SIDES:
        vx, vy = rose.SIDE_VECTORS[side]
        d = dist[0] if vx else dist[1]
        r = pygame.Rect(0, 0, SLOT_SIZE, SLOT_SIZE)
        r.center = (int(center[0] + vx * d), int(center[1] + vy * d))
        rects[side] = r
    return rects


def choice_list():
    return [(C.DIR_NAMES[d], d, C.DIR_COLORS[d]) for d in rose.DIRS]


def draw_beach(surf, t):
    G.draw_sky(surf, (0, 0, C.WIDTH, 230))
    G.draw_sun(surf, (1010, 150), 40, t)
    G.draw_sea(surf, (0, 230, C.WIDTH, 180), t, rows=4)
    pts = [(0, 420)] + [(x, 408 + 10 * math.sin(x * 0.012 + t * 0.8)) for x in range(0, 1300, 40)] + [(1280, 720), (0, 720)]
    G.aa_polygon(surf, G.lerp_color(C.FOAM, C.SAND, 0.3), [(x, y - 8) for x, y in pts[:-2]] + [(1280, 720), (0, 720)])
    G.aa_polygon(surf, C.SAND, pts)
    rnd = random.Random(4)
    for _ in range(40):
        x, y = rnd.uniform(0, 1280), rnd.uniform(440, 640)
        G.aa_circle(surf, C.SAND_DARK, (x, y), rnd.uniform(2, 4))
    for x, y, c in ((470, 600, (255, 170, 170)), (1210, 610, (255, 230, 200)), (560, 470, (250, 200, 230))):
        G.aa_ellipse(surf, c, (x, y), 12, 8)


class Tappa1(StageScene):
    stage = 1

    def __init__(self, app):
        super().__init__(app)
        self.phase = "intro"
        self.slots = {side: DropSlot(r, side) for side, r in slot_rects().items()}
        letters = list(rose.DIRS)
        random.shuffle(letters)
        homes = [(1176, 190), (1176, 302), (1176, 414), (1176, 526)]
        self.group = DragGroup()
        for letter, home in zip(letters, homes):
            d = Draggable(home, (96, 96), letter, C.DIR_COLORS[letter])
            d.on_drop = self._drop
            self.group.add(d)
        self.drag_groups = [self.group]
        self.hand = 0.0
        self.hand_target = 0.0
        self.order_idx = -1
        self.show_hand = False

    def start(self):
        self.say(T.T1_INTRO, self._start_drag)

    # ------------------------------------------------ parte 1: etichette
    def _start_drag(self):
        self.phase = "drag"
        for d in self.group.items:
            d.glow = True
        self.task(T.T1_TASK, T.T1_HINT, T.T1_HINT2)

    def _slot_at(self, pos):
        best = None
        for slot in self.slots.values():
            if slot.content is None and slot.accepts_point(pos):
                dist = math.hypot(pos[0] - slot.rect.centerx, pos[1] - slot.rect.centery)
                if best is None or dist < best[0]:
                    best = (dist, slot)
        return best[1] if best else None

    def _drop(self, drag, pos):
        slot = self._slot_at(pos)
        if slot is None:
            return False
        if rose.is_correct(drag.text, slot.key, "right"):
            slot.content = drag
            drag.snap(slot.rect.center)
            drag.glow = False
            self.app.audio.play("pop")
            if all(s.content for s in self.slots.values()):
                self._all_placed()
            return True
        self.wrong(center=(800, 150))
        return False

    def on_hint(self, level):
        if level >= 2 and self.phase == "drag":
            for side, slot in self.slots.items():
                slot.ghost = rose.expected_layout("right")[side]
                slot.glow = True

    def _all_placed(self):
        self.phase = "done_drag"
        for s in self.slots.values():
            s.glow = False
        self.btn_hint.visible = False
        self.right(T.T1_DONE)
        self.after(2.0, self._start_order)

    # ------------------------------------------------ parte 2: senso orario
    def _start_order(self):
        self.phase = "order"
        self.show_hand = True
        self.say(T.T1_ORDER_INTRO, lambda: self._ask(0))

    def _ask(self, i):
        self.order_idx = i
        q, ans = T.T1_ORDER_Q[i]
        self.task(q, T.T1_ORDER_HINT, T.T1_ORDER_HINT2[ans], choices=choice_list(), on_choice=self._answer)

    def _answer(self, value, btn):
        _, ans = T.T1_ORDER_Q[self.order_idx]
        if value == ans:
            btn.flash(True)
            self.clear_choices()
            self.hand_target += 90
            if self.order_idx + 1 < len(T.T1_ORDER_Q):
                self.right()
                self.after(1.3, lambda: self._ask(self.order_idx + 1))
            else:
                self.right(T.T1_ORDER_DONE)
                self.hand_target += 90
                self.complete(delay=2.6)
        else:
            btn.flash(False)
            self.wrong()

    # ------------------------------------------------ ciclo
    def on_event(self, ev):
        if self.phase == "drag":
            self.group.handle_event(ev)

    def on_update(self, dt):
        self.group.update(dt)
        active = self.group.active()
        for s in self.slots.values():
            s.update(dt, active)
        self.hand += (self.hand_target - self.hand) * min(1.0, dt * 5)

    def draw_background(self, surf):
        draw_beach(surf, self.t)
        G.draw_palm(surf, (452, 470), 170, self.t, 0.25)
        G.draw_palm(surf, (1250, 460), 150, self.t, -0.2)
        G.draw_broken_canoe(surf, (520, 590), 1.0, 0.25)
        G.draw_broken_canoe(surf, (1080, 600), 0.9, -0.4, (60, 140, 200))

    def draw_play(self, surf):
        G.aa_circle(surf, (0, 0, 0, 50), (CENTER[0] + 6, CENTER[1] + 10), 120)
        G.draw_compass_rose(surf, CENTER, 112, labels=False)
        for s in self.slots.values():
            if s.content is None:
                s.draw(surf)
        if self.show_hand:
            a = math.radians(self.hand - 90)
            tip = (CENTER[0] + math.cos(a) * 96, CENTER[1] + math.sin(a) * 96)
            G.arrow(surf, (30, 30, 40), CENTER, tip, 12, 34)
            G.arrow(surf, (255, 214, 60), CENTER, tip, 7, 28)
            G.aa_circle(surf, (30, 30, 40), CENTER, 12)
        self.group.draw(surf)
