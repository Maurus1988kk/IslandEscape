"""Sfondi e pezzi grafici condivisi tra più scene."""

import math
import random

import pygame

from .. import config as C
from ..gfx import draw as G

_rng = random.Random(11)
CLOUDS = [(_rng.uniform(0, 1280), _rng.uniform(30, 200), _rng.uniform(0.7, 1.3), _rng.uniform(6, 14)) for _ in range(5)]


def draw_clouds(surf, t, color=(255, 255, 255), y_max=None):
    for x0, y, s, speed in CLOUDS:
        if y_max is not None and y > y_max:
            continue
        x = (x0 + t * speed) % 1500 - 110
        G.draw_cloud(surf, (x, y), s, color)


def beach_background(surf, t, horizon=300):
    """Cielo, mare e un'isoletta: usato dal menu e da altre schermate."""
    G.draw_sky(surf, (0, 0, C.WIDTH, horizon))
    G.draw_sun(surf, (1110, 110), 52, t)
    draw_clouds(surf, t, y_max=horizon - 40)
    G.draw_sea(surf, (0, horizon, C.WIDTH, C.HEIGHT - horizon), t, rows=7)
    G.aa_ellipse(surf, G.lerp_color(C.FOAM, C.SEA_LIGHT, 0.3), (1060, 690), 380, 120)
    G.aa_ellipse(surf, C.SAND, (1060, 700), 360, 105)
    G.draw_palm(surf, (930, 640), 210, t, 0.2)
    G.draw_palm(surf, (1150, 650), 170, t, -0.15)
    G.draw_palm(surf, (1030, 620), 130, t, 0.05)


class Confetti:
    COLORS = [(240, 80, 80), (250, 200, 60), (70, 170, 240), (90, 200, 100), (190, 110, 220), (255, 150, 60)]

    def __init__(self, n=90, area=(0, 0, C.WIDTH, C.HEIGHT)):
        self.area = pygame.Rect(area)
        self.rng = random.Random()
        self.parts = [self._new(initial=True) for _ in range(n)]

    def _new(self, initial=False):
        a = self.area
        return [self.rng.uniform(a.x, a.right), self.rng.uniform(a.y - a.h if initial else a.y - 40, a.y if not initial else a.bottom),
                self.rng.uniform(-30, 30), self.rng.uniform(70, 160), self.rng.uniform(0, 6.28),
                self.rng.uniform(-4, 4), self.rng.choice(self.COLORS), self.rng.uniform(5, 9)]

    def update(self, dt):
        for p in self.parts:
            p[0] += (p[2] + math.sin(p[4]) * 20) * dt
            p[1] += p[3] * dt
            p[4] += p[5] * dt
            if p[1] > self.area.bottom + 20:
                p[:] = self._new()

    def draw(self, surf):
        for p in self.parts:
            G.draw_confetti(surf, (p[0], p[1]), p[7], p[6], p[4])
