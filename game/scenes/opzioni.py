"""Schermata delle opzioni."""

from .. import config as C
from ..gfx import draw as G
from ..tts import ERROR, READY, STARTING
from ..ui import fonts
from ..ui.widgets import Button
from .base import Scene
from .common import beach_background

ROW_Y = (128, 252, 376, 520)
LABEL_X = 60
BTN_X = 520


class OptionsScene(Scene):
    ambient = "waves"

    def __init__(self, app):
        super().__init__(app)
        self.timer_btns = []
        x = BTN_X
        for m in C.TIMER_CHOICES:
            label = "Spento" if m == 0 else f"{m} min"
            b = Button((x, ROW_Y[0], 176, 86), label, (lambda v=m: self._set_timer(v)), C.BTN_GRAY)
            self.timer_btns.append((m, b))
            x += 188
        self.sound_btns = self._yes_no(ROW_Y[1], "sound")
        self.tts_btns = self._yes_no(ROW_Y[2], "tts")
        self.upper_btns = self._yes_no(ROW_Y[3], "uppercase")
        self.btn_back = Button((40, 616, 300, 84), "Indietro", app.go_menu, C.BTN_BLUE, icon="home")
        self.buttons = [b for _, b in self.timer_btns] + [b for _, b in self.sound_btns + self.tts_btns + self.upper_btns]
        self.buttons.append(self.btn_back)
        self._tts_was = app.tts.status
        self._refresh()

    def _yes_no(self, y, key):
        yes = Button((BTN_X, y, 220, 86), "Sì", (lambda: self._set(key, True)), C.BTN_GRAY)
        no = Button((BTN_X + 236, y, 220, 86), "No", (lambda: self._set(key, False)), C.BTN_GRAY)
        return [(True, yes), (False, no)]

    def _set_timer(self, minutes):
        self.app.options.timer_minutes = minutes
        self.app.apply_options()
        self._refresh()

    def _set(self, key, value):
        setattr(self.app.options, key, value)
        self.app.apply_options()
        if key == "tts" and value and self.app.tts.status == READY:
            self.app.speak("Ciao! Sono Bussolino. Vi leggerò le frasi del gioco.")
        self._refresh()

    def _refresh(self):
        o = self.app.options
        for m, b in self.timer_btns:
            b.selected = (m == o.timer_minutes)
            b.color = C.BTN_GREEN if b.selected else C.BTN_GRAY
        for group, val in ((self.sound_btns, o.sound), (self.tts_btns, o.tts), (self.upper_btns, o.uppercase)):
            for v, b in group:
                b.selected = (v == val)
                b.color = C.BTN_GREEN if b.selected else C.BTN_GRAY

    def handle_event(self, ev):
        for b in self.buttons:
            if b.handle_event(ev):
                return

    def update(self, dt):
        super().update(dt)
        for b in self.buttons:
            b.update(dt)
        st = self.app.tts.status
        if st != self._tts_was:
            if st == ERROR and self.app.options.tts:
                self.app.options.tts = False
                self.app.apply_options()
            if st == READY and self.app.options.tts:
                self.app.speak("Ciao! Sono Bussolino. Vi leggerò le frasi del gioco.")
            self._tts_was = st
            self._refresh()

    def draw(self, surf):
        beach_background(surf, self.t, horizon=330)
        G.alpha_rect(surf, (20, 20, 1240, 590), (255, 252, 240, 235), 30)
        fonts.draw(surf, "Opzioni", (640, 68), 50, (30, 90, 180), True, anchor="center")
        labels = ("Timer da escape room", "Suoni", "Lettura vocale", "TUTTO MAIUSCOLO")
        for y, text in zip(ROW_Y, labels):
            fonts.draw(surf, text, (LABEL_X, y + 43), 34, C.TEXT_DARK, True, anchor="midleft",
                       transform=(text != "TUTTO MAIUSCOLO"))
        tts = self.app.tts
        if tts.status == STARTING:
            msg, col = "Controllo la voce...", C.TEXT_SOFT
        elif tts.status == READY:
            msg, col = tts.message, C.OK_GREEN
        elif tts.status == ERROR:
            msg, col = tts.message + " L'opzione è stata spenta.", C.KO_ORANGE
        else:
            msg, col = "Bussolino legge ad alta voce i fumetti.", C.TEXT_SOFT
        fonts.draw(surf, msg, (LABEL_X, ROW_Y[2] + 100), 28, col, True, anchor="topleft")
        fonts.draw(surf, "Il timer non fa mai perdere: alla fine si continua a giocare.", (LABEL_X, ROW_Y[0] + 92), 26,
                   C.TEXT_SOFT, anchor="topleft")
        for b in self.buttons:
            b.draw(surf)
