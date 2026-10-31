"""Bussolino: pappagallo esploratore disegnato con forme semplici."""

import math
import random

from ..gfx import draw as G

GREEN = (52, 176, 84)
GREEN_DARK = (30, 128, 60)
YELLOW = (255, 214, 64)
RED = (230, 64, 56)
BLUE = (40, 120, 220)
BEAK = (255, 170, 40)
BEAK_DARK = (200, 110, 20)
GOLD = (236, 186, 52)


class Parrot:
    def __init__(self, pos, scale=1.0, flip=False, perch=True):
        self.x, self.y = pos
        self.scale = scale
        self.flip = flip
        self.perch = perch
        self.t = random.uniform(0, 3)
        self.talk_time = 0.0
        self.happy_time = 0.0
        self.think_time = 0.0
        self.flying = False
        self.blink = 0.0
        self.next_blink = random.uniform(2, 4)

    @property
    def pos(self):
        return (self.x, self.y)

    def talk(self, seconds=1.6):
        self.talk_time = max(self.talk_time, seconds)

    def happy(self, seconds=1.2):
        self.happy_time = seconds
        self.think_time = 0.0

    def think(self, seconds=1.2):
        self.think_time = seconds

    def update(self, dt):
        self.t += dt
        self.talk_time = max(0.0, self.talk_time - dt)
        self.happy_time = max(0.0, self.happy_time - dt)
        self.think_time = max(0.0, self.think_time - dt)
        self.next_blink -= dt
        if self.next_blink <= 0:
            self.blink = 0.15
            self.next_blink = random.uniform(2.5, 5.0)
        self.blink = max(0.0, self.blink - dt)

    def draw(self, surf):
        s = self.scale
        sx = -1 if self.flip else 1
        bob = math.sin(self.t * 2.2) * 3 * s
        jump = 0.0
        if self.happy_time > 0:
            jump = -abs(math.sin(self.happy_time * 9)) * 16 * s
        cx, cy = self.x, self.y + bob + jump
        tilt = 0.0
        if self.think_time > 0:
            tilt = -0.22 * min(1.0, self.think_time * 2)
        elif self.talk_time > 0:
            tilt = 0.05 * math.sin(self.t * 5)

        def P(x, y):
            return (cx + sx * x * s, cy + y * s)

        if self.flying:
            flap = math.sin(self.t * 12) * 0.9
        elif self.happy_time > 0:
            flap = math.sin(self.t * 16) * 0.6
        elif self.talk_time > 0:
            flap = math.sin(self.t * 8) * 0.18
        else:
            flap = math.sin(self.t * 1.5) * 0.05

        # ramo
        if self.perch and not self.flying:
            G.thick_line(surf, G.shade((120, 80, 40), 0.8), P(-60, 66), P(60, 70), 12 * s)
            G.thick_line(surf, (140, 94, 48), P(-60, 63), P(60, 67), 9 * s)
            G.aa_ellipse(surf, (60, 150, 70), P(52, 58), 14 * s, 6 * s, -0.4 * sx)

        # coda
        for k, col in enumerate((BLUE, RED, BLUE)):
            a = math.radians(110 + k * 12)
            tip = P(-8 + math.cos(a) * 40 - 14, 44 + math.sin(a) * 56)
            G.aa_polygon(surf, col, [P(-16, 40), tip, P(4, 44)])

        # zampe
        if not self.flying:
            for dx in (-6, 12):
                G.thick_line(surf, (120, 120, 130), P(dx, 52), P(dx, 66), 4 * s)
                G.thick_line(surf, (120, 120, 130), P(dx - 6, 68), P(dx + 7, 68), 4 * s)

        # corpo
        G.aa_ellipse(surf, GREEN_DARK, P(0, 14), 34 * s, 46 * s, 0.15 * sx)
        G.aa_ellipse(surf, GREEN, P(0, 12), 32 * s, 44 * s, 0.15 * sx)
        G.aa_ellipse(surf, YELLOW, P(9, 20), 18 * s, 30 * s, 0.12 * sx)

        # medaglione-bussola
        G.thick_line(surf, (120, 70, 30), P(2, -14), P(10, 2), 2.5 * s)
        G.thick_line(surf, (120, 70, 30), P(22, -16), P(10, 2), 2.5 * s)
        G.aa_circle(surf, G.shade(GOLD, 0.7), P(10, 8), 10 * s)
        G.aa_circle(surf, GOLD, P(10, 8), 8.5 * s)
        G.aa_circle(surf, (250, 248, 236), P(10, 8), 6 * s)
        G.aa_polygon(surf, RED, [P(10, 2.5), P(12.5, 8), P(7.5, 8)])
        G.aa_polygon(surf, (60, 70, 100), [P(10, 13.5), P(12.5, 8), P(7.5, 8)])

        # ala (si muove)
        shoulder = P(-10, -8)
        wing_ang = (0.25 + flap) * sx
        pts = [(-10, -8), (-34, 6), (-38, 30), (-28, 46), (-14, 36), (-4, 12)]
        wing = [G.rot_point(P(x, y), shoulder, wing_ang) for x, y in pts]
        G.aa_polygon(surf, GREEN_DARK, wing)
        tips = [(-34, 26), (-38, 30), (-28, 46), (-20, 40)]
        G.aa_polygon(surf, BLUE, [G.rot_point(P(x, y), shoulder, wing_ang) for x, y in tips])
        G.aa_polygon(surf, RED, [G.rot_point(P(x, y), shoulder, wing_ang) for x, y in ((-30, 14), (-36, 22), (-24, 24))])

        # testa (con inclinazione)
        neck = P(6, -20)

        def H(x, y):
            return G.rot_point(P(x, y), neck, tilt * sx)

        for k, col in enumerate((RED, (255, 120, 50), RED)):
            a = math.radians(-120 + k * 22)
            G.aa_polygon(surf, col, [H(-2 + k * 6, -62), H(-2 + k * 6 + math.cos(a) * 26, -66 + math.sin(a) * 22), H(8 + k * 6, -62)])
        G.aa_circle(surf, GREEN_DARK, H(8, -40), 31 * s)
        G.aa_circle(surf, GREEN, H(8, -42), 29 * s)
        G.aa_circle(surf, (255, 150, 150), H(24, -30), 7 * s)  # guancia

        # occhio
        eye = H(18, -48)
        G.aa_circle(surf, (255, 255, 255), eye, 11 * s)
        if self.blink > 0:
            G.thick_line(surf, GREEN_DARK, H(9, -48), H(28, -48), 4 * s)
        else:
            px = 3 * s * sx
            G.aa_circle(surf, (20, 22, 30), (eye[0] + px, eye[1] + 1), 6.5 * s)
            G.aa_circle(surf, (255, 255, 255), (eye[0] + px - 2 * s * sx, eye[1] - 2 * s), 2.2 * s)

        # becco
        open_amt = abs(math.sin(self.t * 14)) * 8 if self.talk_time > 0 else (4 if self.happy_time > 0 else 0)
        G.aa_polygon(surf, BEAK_DARK, [H(30, -36 + open_amt * 0.3), H(46, -34 + open_amt), H(42, -26 + open_amt), H(30, -28 + open_amt * 0.5)])
        G.aa_polygon(surf, BEAK, [H(28, -48), H(44, -46), H(52, -38), H(48, -30), H(40, -36), H(30, -36)])
        G.aa_polygon(surf, (255, 210, 120), [H(30, -46), H(42, -44), H(46, -40), H(32, -42)])
