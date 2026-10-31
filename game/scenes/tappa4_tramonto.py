"""Tappa 4 - Il tramonto e la mappa del tesoro (premio: Vela)."""

import math

import pygame

from .. import config as C
from .. import testi as T
from ..gfx import draw as G
from ..logic import places as PL
from ..ui import fonts
from .base import StageScene
from .tappa1_spiaggia import choice_list

MX, MY = 455, 104          # angolo della griglia della mappa
CW, CH = 170, 130          # dimensioni di una casella
HORIZON = 440
LABELS = {"tartaruga": "Roccia\ntartaruga", "palma": "Palma\ngigante"}
PIECES = ("corda", "tela", "albero")
SAIL_BOX = pygame.Rect(1144, 108, 120, 250)


def cell_center(cell):
    return (MX + (cell[0] + 0.5) * CW, MY + (cell[1] + 0.5) * CH)


def cell_at(pos):
    c = int((pos[0] - MX) // CW)
    r = int((pos[1] - MY) // CH)
    if 0 <= c < PL.MAP_COLS and 0 <= r < PL.MAP_ROWS:
        return (c, r)
    return None


class Tappa4(StageScene):
    stage = 4

    def __init__(self, app):
        super().__init__(app)
        self.phase = "intro"
        self.sun_k = 0.0
        self.setting = False
        self.map_mode = False
        self.riddle_idx = 0
        self.found = []
        self.pieces = []
        self.wrong_flash = {}
        self.arrows = False

    def start(self):
        self.setting = True
        self.say(T.T4_INTRO, self._ask_sunset)

    # ------------------------------------------------ parte A
    def _ask_sunset(self):
        self.phase = "q1"
        self.task(T.T4_Q1, T.T4_Q1_HINT, T.T4_Q1_HINT2, choices=choice_list(), on_choice=self._answer)

    def _answer(self, value, btn):
        if value == "O":
            btn.flash(True)
            self.clear_choices()
            self.right(T.T4_Q1_OK)
            self.phase = "wait"
            self.after(2.6, self._start_map)
        else:
            btn.flash(False)
            self.wrong()

    # ------------------------------------------------ parte B
    def _start_map(self):
        self.map_mode = True
        self.phase = "map_intro"
        self.say(T.T4_MAP_INTRO, lambda: self._ask_riddle(0))

    def _ask_riddle(self, i):
        self.riddle_idx = i
        self.arrows = False
        r = PL.RIDDLES[i]
        self.phase = "riddle"
        self.task(r["text"], r["hint"], r["hint2"])

    def on_hint(self, level):
        if self.phase == "riddle" and level >= 2:
            self.arrows = True

    def _tap(self, pos):
        cell = cell_at(pos)
        if cell is None:
            return
        place = PL.place_at(cell)
        if place is None or place in self.found:
            return
        riddle = PL.RIDDLES[self.riddle_idx]
        if place == riddle["answer"]:
            self.found.append(place)
            self.pieces.append(riddle["piece"])
            self.phase = "wait"
            self.arrows = False
            self.btn_hint.visible = False
            self.right(T.T4_DONE_PIECE[self.riddle_idx])
            if self.riddle_idx + 1 < len(PL.RIDDLES):
                self.after(2.2, lambda: self._ask_riddle(self.riddle_idx + 1))
            else:
                self.complete(delay=2.2)
        else:
            self.wrong_flash[place] = 1.0
            self.wrong(T.T4_WRONG)

    # ------------------------------------------------ ciclo
    def on_event(self, ev):
        if self.phase == "riddle" and ev.type == pygame.MOUSEBUTTONDOWN and self.in_play(ev.pos):
            self._tap(ev.pos)

    def on_update(self, dt):
        if self.setting:
            self.sun_k = min(1.0, self.sun_k + dt / 6.0)
        for k in list(self.wrong_flash):
            self.wrong_flash[k] -= dt
            if self.wrong_flash[k] <= 0:
                del self.wrong_flash[k]

    def draw_background(self, surf):
        if self.map_mode:
            G.draw_sea(surf, (0, 0, C.WIDTH, C.HEIGHT), self.t, rows=8)
            return
        k = G.ease_in_out(self.sun_k)
        top = G.lerp_color((80, 130, 210), (54, 40, 110), k)
        bottom = G.lerp_color((250, 200, 140), (250, 120, 70), k)
        G.vgradient_live(surf, (0, 0, C.WIDTH, HORIZON), top, bottom)
        sun_y = G.lerp(170, HORIZON + 18, k)
        sun_col = G.lerp_color((255, 210, 80), (250, 90, 50), k)
        G.draw_sun(surf, (845, sun_y), 54, self.t, sun_col, rays=k < 0.7)
        sea_top = G.lerp_color((70, 130, 190), (120, 70, 110), k)
        sea_bot = G.lerp_color((30, 80, 150), (40, 30, 80), k)
        G.draw_sea(surf, (0, HORIZON, C.WIDTH, C.HEIGHT - HORIZON), self.t, sea_top, sea_bot,
                   G.lerp_color(C.FOAM, (255, 180, 120), k), rows=5)
        for i in range(8):
            y = HORIZON + 14 + i * 20
            w = 120 - i * 10 + 10 * math.sin(self.t * 3 + i)
            pygame.draw.line(surf, G.lerp_color((255, 230, 150), sun_col, 0.5), (int(845 - w / 2), y), (int(845 + w / 2), y), 4)
        sil = (40, 26, 50)
        G.aa_polygon(surf, sil, [(380, 640), (420, 560), (560, 530), (700, 548), (760, 600), (790, 640)])
        G.draw_palm(surf, (520, 548), 170, self.t, 0.22, silhouette=sil)
        G.draw_palm(surf, (640, 548), 130, self.t, -0.1, silhouette=sil)
        G.aa_polygon(surf, sil, [(1100, 640), (1150, 590), (1230, 575), (1280, 590), (1280, 640)])

    def draw_play(self, surf):
        if not self.map_mode:
            return
        play = pygame.Rect(C.PLAY_RECT)
        clip = surf.get_clip()
        surf.set_clip(play)
        center = (MX + CW * 2, MY + CH * 2)
        G.aa_polygon(surf, G.lerp_color(C.FOAM, C.SEA_LIGHT, 0.4), G.island_points(center, 410, 304, seed=6, wobble=0.06))
        G.aa_polygon(surf, C.SAND, G.island_points(center, 392, 290, seed=6, wobble=0.06))
        G.aa_polygon(surf, (150, 200, 110), G.island_points(center, 350, 250, seed=7, wobble=0.07))
        surf.set_clip(clip)
        for c in range(1, PL.MAP_COLS):
            x = MX + c * CW
            G.dashed_line(surf, (110, 160, 80), (x, MY + 8), (x, MY + CH * PL.MAP_ROWS - 8), 2, 10, 10)
        for r in range(1, PL.MAP_ROWS):
            y = MY + r * CH
            G.dashed_line(surf, (110, 160, 80), (MX + 8, y), (MX + CW * PL.MAP_COLS - 8, y), 2, 10, 10)
        G.draw_compass_rose(surf, (500, 578), 30, label_size=20)
        riddle = PL.RIDDLES[self.riddle_idx]
        if self.arrows and self.phase == "riddle":
            for direction, ref in riddle["clues"]:
                p = cell_center(PL.PLACES[ref])
                vec = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "O": (-1, 0)}[direction]
                length = (CH if vec[1] else CW) * 1.4
                end = (p[0] + vec[0] * length, p[1] + vec[1] * length)
                G.arrow(surf, (60, 40, 0), p, end, 16, 40)
                G.arrow(surf, (255, 220, 40), p, end, 10, 32)
        for pid, cell in PL.PLACES.items():
            cx, cy = cell_center(cell)
            if pid in self.found:
                G.aa_circle(surf, (255, 240, 170), (cx, cy - 18), 50)
            if pid in self.wrong_flash:
                k = self.wrong_flash[pid]
                G.aa_circle(surf, (255, 200, 150), (cx, cy - 18), 48 * k + 4)
            G.draw_place(surf, pid, (cx, cy - 20), 0.82, self.t)
            label = LABELS.get(pid, PL.PLACE_NAMES[pid])
            lines = [fonts.tx(x) for x in label.split("\n")]
            size = 24
            lh = fonts.line_height(size, True)
            w = max(fonts.get(size, True).size(x)[0] for x in lines) + 14
            box = pygame.Rect(0, 0, w, lh * len(lines) + 4)
            box.midtop = (int(cx), int(cy + 16))
            G.alpha_rect(surf, box, (255, 255, 255, 215), 10)
            fonts.draw_lines(surf, lines, box, size, C.TEXT_DARK, True, "center", "center")
            if pid in self.found:
                G.badge(surf, (cx + 46, cy - 46), 18, True)
        # pezzi della vela trovati
        G.panel(surf, SAIL_BOX, (255, 250, 230), 16, border=(200, 160, 80))
        fonts.draw(surf, "Vela", (SAIL_BOX.centerx, SAIL_BOX.y + 22), 26, C.TEXT_DARK, True, anchor="center")
        for i, piece in enumerate(PIECES):
            p = (SAIL_BOX.centerx, SAIL_BOX.y + 78 + i * 66)
            if piece in self.pieces:
                if piece == "corda":
                    G.draw_rope(surf, p, 0.8)
                elif piece == "tela":
                    G.draw_sail(surf, (p[0] + 4, p[1]), 0.8, mast=False, rope=False)
                else:
                    G.thick_line(surf, C.WOOD_DARK, (p[0] - 26, p[1] + 20), (p[0] + 26, p[1] - 20), 8)
            else:
                G.aa_ring(surf, (190, 170, 130), p, 24, 3)
                fonts.draw(surf, "?", p, 28, (190, 170, 130), True, anchor="center", transform=False)
