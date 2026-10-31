"""Menu principale e scelta del nome della squadra."""

import math

import pygame

from .. import config as C
from .. import save
from ..gfx import draw as G
from ..state import MAX_TEAM_NAME, clean_team_name
from ..ui import fonts
from ..ui.parrot import Parrot
from ..ui.widgets import Button
from .base import Scene
from .common import beach_background


class MenuScene(Scene):
    ambient = "waves"

    def __init__(self, app):
        super().__init__(app)
        self.parrot = Parrot((215, 330), 1.7, perch=False)
        self.parrot.flying = True
        self.has_save = save.has_save()
        x, w, h, gap = 640 - 220, 440, 86, 18
        y = 250
        self.buttons = [Button((x, y, w, h), "Nuova partita", app.go_team, C.BTN_GREEN, icon="play")]
        y += h + gap
        if self.has_save:
            self.buttons.append(Button((x, y, w, h), "Continua", app.continue_game, C.BTN_BLUE, icon="restart"))
            y += h + gap
        self.buttons.append(Button((x, y, w, h), "Opzioni", app.go_options, C.BTN_PURPLE, icon="gear"))
        y += h + gap
        self.buttons.append(Button((x, y, w, h), "Esci", app.quit, C.BTN_RED, icon="exit"))

    def handle_event(self, ev):
        for b in self.buttons:
            if b.handle_event(ev):
                return

    def update(self, dt):
        super().update(dt)
        self.parrot.update(dt)
        self.parrot.y = 330 + 18 * math.sin(self.t * 1.4)
        for b in self.buttons:
            b.update(dt)

    def draw(self, surf):
        beach_background(surf, self.t, horizon=330)
        fonts.draw_outlined(surf, C.TITLE, (640, 92), 64, (255, 214, 60), (90, 40, 10), True, width=4)
        fonts.draw(surf, "Un'escape room per imparare a orientarsi", (640, 168), 30, C.WHITE, True,
                   anchor="center", shadow=(20, 40, 80))
        self.parrot.draw(surf)
        for b in self.buttons:
            b.draw(surf)
        fonts.draw(surf, "F11: schermo intero / finestra", (20, 700), 22, (230, 240, 255), anchor="bottomleft",
                   shadow=(0, 0, 0))
        fonts.draw(surf, f"versione {C.VERSION}", (1260, 700), 22, (230, 240, 255), anchor="bottomright",
                   shadow=(0, 0, 0))


class TeamScene(Scene):
    ambient = "waves"

    def __init__(self, app):
        super().__init__(app)
        self.name = ""
        self.parrot = Parrot((190, 470), 1.4)
        self.btn_start = Button((380, 470, 380, 90), "Inizia", self._start, C.BTN_GREEN, icon="play")
        self.btn_skip = Button((780, 470, 300, 90), "Salta", self._skip, C.BTN_BLUE)
        self.btn_back = Button((40, 610, 260, 84), "Indietro", app.go_menu, C.BTN_GRAY, icon="home")
        self.buttons = [self.btn_start, self.btn_skip, self.btn_back]

    def enter(self):
        try:
            pygame.key.start_text_input()
        except Exception:
            pass

    def exit(self):
        try:
            pygame.key.stop_text_input()
        except Exception:
            pass

    def _start(self):
        self.app.new_game(clean_team_name(self.name))

    def _skip(self):
        self.app.new_game("")

    def handle_event(self, ev):
        if ev.type == pygame.TEXTINPUT:
            cand = clean_team_name(self.name + ev.text)
            if len(cand) <= MAX_TEAM_NAME and len(cand) >= len(self.name.strip()):
                self.name = (self.name + ev.text)[:MAX_TEAM_NAME]
            return
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_BACKSPACE:
                self.name = self.name[:-1]
            elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._start()
            return
        for b in self.buttons:
            if b.handle_event(ev):
                return

    def update(self, dt):
        super().update(dt)
        self.parrot.update(dt)
        for b in self.buttons:
            b.update(dt)
        self.btn_start.pulse = bool(self.name.strip())

    def draw(self, surf):
        beach_background(surf, self.t, horizon=330)
        G.panel(surf, (300, 120, 860, 300), (255, 252, 240), 30, border=(40, 110, 200))
        fonts.draw(surf, "Nuova partita", (730, 172), 48, (30, 90, 180), True, anchor="center")
        fonts.draw(surf, "Come si chiama la vostra squadra?", (730, 236), 32, C.TEXT_DARK, True, anchor="center")
        box = pygame.Rect(380, 276, 700, 92)
        G.rounded_rect(surf, C.WHITE, box, 18)
        G.rounded_rect(surf, (40, 110, 200), box, 18, 4)
        shown = self.name if self.name else ""
        r = fonts.draw(surf, shown, (box.x + 24, box.centery), 40, C.TEXT_DARK, True, anchor="midleft")
        if int(self.t * 2) % 2 == 0:
            x = r.right + 4 if shown else box.x + 26
            pygame.draw.line(surf, C.TEXT_DARK, (x, box.y + 20), (x, box.bottom - 20), 3)
        if not shown:
            fonts.draw(surf, "(facoltativo: scrivete con la tastiera)", (box.x + 40, box.centery), 28,
                       (150, 150, 160), anchor="midleft")
        self.parrot.draw(surf)
        for b in self.buttons:
            b.draw(surf)
