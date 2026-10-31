"""Tappa 2 - L'alba sulla scogliera (premio: Corda).

Il sole sorge da un lato dello schermo scelto a caso: il Nord non è sempre in alto.
"""

import math
import random

import pygame

from .. import config as C
from .. import testi as T
from ..gfx import draw as G
from ..logic import rose
from ..ui import fonts
from ..ui.widgets import DragGroup, Draggable, DropSlot
from .base import StageScene
from .tappa1_spiaggia import choice_list

CENTER = (845, 365)
SLOT_DIST = {"h": 178, "v": 152}
SUN_DIST = {"h": 385, "v": 250}
CORNERS = [(510, 165), (1180, 165), (1180, 565), (510, 565)]


def side_point(side, dist):
    vx, vy = rose.SIDE_VECTORS[side]
    d = dist["h"] if vx else dist["v"]
    return (CENTER[0] + vx * d, CENTER[1] + vy * d)


def draw_arms_hint(surf, rect, t):
    """Disegno per l'indizio: bambino visto da dietro con le braccia aperte."""
    r = pygame.Rect(rect)
    G.rounded_rect(surf, (200, 230, 255), r, 18)
    G.rounded_rect(surf, (150, 210, 120), (r.x, r.y + r.h * 0.62, r.w, r.h * 0.38), 18)
    sun = (r.right - 40, r.y + 70)
    G.draw_sun(surf, sun, 24, t)
    kid = (r.centerx - 10, r.y + r.h * 0.6)
    G.draw_explorer_back(surf, kid, 0.95)
    fonts.draw_outlined(surf, "NORD", (kid[0], r.y + 24), 28, C.NORTH_RED, C.WHITE, True)
    G.arrow(surf, C.NORTH_RED, (kid[0], r.y + 92), (kid[0], r.y + 46), 6, 18)
    fonts.draw_outlined(surf, "EST", (r.right - 40, r.y + 116), 26, C.BTN_ORANGE, C.WHITE, True)
    fonts.draw_outlined(surf, "OVEST", (r.x + 50, r.y + 116), 26, C.BTN_PURPLE, C.WHITE, True)
    fonts.draw_outlined(surf, "SUD", (kid[0], r.bottom - 18), 26, C.BTN_BLUE, C.WHITE, True)


class Tappa2(StageScene):
    stage = 2

    def __init__(self, app, east_side=None):
        super().__init__(app)
        self.east_side = east_side or random.choice(rose.SIDES)
        self.phase = "intro"
        self.slots = {}
        for side in rose.SIDES:
            r = pygame.Rect(0, 0, 104, 104)
            r.center = tuple(int(v) for v in side_point(side, SLOT_DIST))
            self.slots[side] = DropSlot(r, side)
        self.sun_k = 0.0
        self.rising = False
        corners = random.sample(CORNERS, 3)
        self.group = DragGroup()
        for letter, home in zip(("N", "S", "O"), corners):
            d = Draggable(home, (96, 96), letter, C.DIR_COLORS[letter])
            d.on_drop = self._drop
            d.visible = False
            self.group.add(d)
        self.e_label = Draggable(side_point(self.east_side, SUN_DIST), (96, 96), "E", C.DIR_COLORS["E"])
        self.e_label.visible = False
        self.e_label.locked = True
        self.drag_groups = [self.group]
        rnd = random.Random(21)
        self.trees = []
        while len(self.trees) < 26:
            p = (rnd.uniform(430, 1260), rnd.uniform(110, 625))
            if math.hypot((p[0] - CENTER[0]) / 1.35, p[1] - CENTER[1]) > 210 and all(
                    math.hypot(p[0] - c[0], p[1] - c[1]) > 75 for c in CORNERS):
                self.trees.append((p, rnd.uniform(22, 34)))
        self.explorer_facing = {"top": 0, "right": 90, "bottom": 180, "left": 270}[self.east_side]
        self.show_arms = False

    def restart(self):
        self.app.state.prepare_stage(self.stage)
        return Tappa2(self.app)

    def start(self):
        self.say(T.T2_INTRO, self._sunrise)

    def _sunrise(self):
        self.phase = "sunrise"
        self.rising = True
        self.locked = True
        self.bubble.set_text(T.T2_SUNRISE)
        self.speak(T.T2_SUNRISE)
        self.after(3.2, self._ask_east)

    def _ask_east(self):
        self.locked = False
        self.phase = "q1"
        self.task(T.T2_Q1, T.T2_Q1_HINT, T.T2_Q1_HINT2, choices=choice_list(), on_choice=self._answer_east)

    def _answer_east(self, value, btn):
        if value != "E":
            btn.flash(False)
            self.wrong()
            return
        btn.flash(True)
        self.clear_choices()
        self.right(T.T2_Q1_OK)
        self.e_label.visible = True
        self.e_label.place(side_point(self.east_side, SUN_DIST))
        self.e_label.snap(self.slots[self.east_side].rect.center)
        self.slots[self.east_side].content = self.e_label
        self.after(2.6, self._ask_others)

    def _ask_others(self):
        self.phase = "drag"
        for d in self.group.items:
            d.visible = True
            d.glow = True
        self.task(T.T2_Q2, T.T2_Q2_HINT, T.T2_Q2_HINT2, drawer=draw_arms_hint)

    def _drop(self, drag, pos):
        best = None
        for slot in self.slots.values():
            if slot.content is None and slot.accepts_point(pos):
                d = math.hypot(pos[0] - slot.rect.centerx, pos[1] - slot.rect.centery)
                if best is None or d < best[0]:
                    best = (d, slot)
        if best is None:
            return False
        slot = best[1]
        if rose.is_correct(drag.text, slot.key, self.east_side):
            slot.content = drag
            drag.snap(slot.rect.center)
            drag.glow = False
            self.app.audio.play("pop")
            if all(s.content for s in self.slots.values()):
                self.phase = "done"
                self.btn_hint.visible = False
                for s in self.slots.values():
                    s.glow = False
                self.right(T.T2_DONE)
                self.complete(delay=2.4)
            return True
        self.wrong(center=(845, 150) if self.east_side != "top" else (845, 290))
        return False

    def on_hint(self, level):
        if self.phase != "drag":
            return
        self.show_arms = True
        if level >= 2:
            layout = rose.expected_layout(self.east_side)
            for side, slot in self.slots.items():
                slot.ghost = layout[side]
                slot.glow = slot.content is None

    def on_event(self, ev):
        if self.phase == "drag":
            self.group.handle_event(ev)

    def on_update(self, dt):
        if self.rising:
            self.sun_k = min(1.0, self.sun_k + dt / 3.0)
        self.group.update(dt)
        self.e_label.update(dt)
        active = self.group.active()
        for s in self.slots.values():
            s.update(dt, active)
        if self.show_arms:
            target = {"top": 270, "right": 0, "bottom": 90, "left": 180}[self.east_side]
            diff = (target - self.explorer_facing + 540) % 360 - 180
            self.explorer_facing += diff * min(1.0, dt * 3)

    def draw_background(self, surf):
        surf.blit(G.vgradient((C.WIDTH, C.HEIGHT), (70, 140, 70), (50, 120, 60)), (0, 0))

    def draw_play(self, surf):
        play = pygame.Rect(C.PLAY_RECT)
        clip = surf.get_clip()
        surf.set_clip(play)
        G.aa_ellipse(surf, (120, 190, 100), CENTER, 300, 225)
        G.aa_ellipse(surf, (226, 206, 150), CENTER, 255, 190)
        G.aa_ellipse(surf, (236, 218, 166), CENTER, 200, 150)
        for p, r in self.trees:
            G.draw_tree_top(surf, p, r)
        # luce dell'alba dal lato Est
        k = G.ease_out(self.sun_k)
        if k > 0:
            glow_pos = side_point(self.east_side, {"h": 470, "v": 330})
            G.blit_glow(surf, glow_pos, 360, (150, 90, 20), round(k * 4) / 4 * 0.75)
            start = side_point(self.east_side, {"h": 470, "v": 320})
            end = side_point(self.east_side, SUN_DIST)
            sun = (G.lerp(start[0], end[0], k), G.lerp(start[1], end[1], k))
            G.draw_sun(surf, sun, 40, self.t, G.lerp_color((255, 130, 60), (255, 210, 70), k))
        veil = int(150 * (1 - k))
        if veil > 0:
            G.alpha_rect(surf, play, (20, 30, 80, veil), 0)
        surf.set_clip(clip)
        for s in self.slots.values():
            if s.content is None:
                s.draw(surf)
        G.draw_explorer_top(surf, CENTER, 1.5, self.explorer_facing, arms=self.show_arms)
        if self.show_arms:
            a = math.radians(self.explorer_facing - 90)
            front = (CENTER[0] + math.cos(a) * 95, CENTER[1] + math.sin(a) * 95)
            G.arrow(surf, (255, 255, 255), (CENTER[0] + math.cos(a) * 40, CENTER[1] + math.sin(a) * 40), front, 6, 20)
        self.e_label.draw(surf)
        self.group.draw(surf)
