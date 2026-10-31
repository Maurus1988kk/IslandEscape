"""Classe Scene e StageScene (parti comuni a tutte le tappe)."""

import math
import random

import pygame

from .. import config as C
from .. import save
from .. import testi as T
from ..gfx import draw as G
from ..ui import fonts
from ..ui.parrot import Parrot
from ..ui.widgets import (DOWN, Button, CompleteCard, HintCard, InventoryBar, SpeechBubble, Toast)


class Scene:
    in_game = False      # conta il tempo e permette la pausa
    ambient = None       # suono di sottofondo ("waves" o None)

    def __init__(self, app):
        self.app = app
        self.t = 0.0

    def enter(self):
        pass

    def exit(self):
        pass

    def on_pause(self):
        pass

    def handle_event(self, ev):
        pass

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        pass

    def restart(self):
        """Nuova istanza per "Ricomincia tappa" (None = non si può)."""
        return None


class StageScene(Scene):
    in_game = True
    ambient = "waves"
    stage = 0
    night = False
    topbar_alpha = 165
    panel_color = (255, 255, 255, 70)

    def __init__(self, app):
        super().__init__(app)
        self.parrot = Parrot(C.PARROT_POS, 0.95)
        self.bubble = SpeechBubble(C.BUBBLE_RECT, (C.PARROT_POS[0] + 34, C.PARROT_POS[1] + 66))
        self.btn_next = Button(C.NEXT_BTN_RECT, "Avanti", self._next_line, C.BTN_GREEN, icon="play")
        self.btn_next.visible = False
        self.btn_hint = Button(C.HINT_BTN_RECT, "Indizio", self.open_hint, C.BTN_YELLOW, C.TEXT_DARK, icon="bulb")
        self.btn_hint.visible = False
        self.btn_pause = Button(C.PAUSE_BTN_RECT, "", app.open_pause, C.BTN_GRAY, icon="pause")
        self.inventory = InventoryBar(app.state)
        self.choices = []
        self.on_choice = None
        self.buttons = []
        self.drag_groups = []
        self.toast = None
        self.card = None
        self.dialog = []
        self.dialog_then = None
        self.task_text = ""
        self.q_errors = 0
        self.hint = ("", "")
        self.hint_drawer = None
        self.hint_level = 0
        self.timers = []
        self.locked = False
        self.finished = False
        self.title = T.STAGE_TITLES.get(self.stage, "")

    # ------------------------------------------------------------ ciclo di vita
    def enter(self):
        self.app.state.stage = self.stage
        self.start()

    def start(self):
        """Da ridefinire: primo passo della tappa."""

    def restart(self):
        self.app.state.prepare_stage(self.stage)
        return type(self)(self.app)

    def on_pause(self):
        for g in self.drag_groups:
            g.cancel()

    # ------------------------------------------------------------ dialoghi e compiti
    def speak(self, text):
        self.app.speak(text)

    def say(self, lines, then=None):
        if isinstance(lines, str):
            lines = [lines]
        self.dialog = list(lines)
        self.dialog_then = then
        self.clear_choices()
        self.btn_hint.visible = False
        self._show_line()

    def _show_line(self):
        text = self.dialog[0]
        self.bubble.set_rect(C.BUBBLE_RECT)
        self.bubble.set_text(text)
        self.parrot.talk(min(3.0, 0.5 + len(text) * 0.035))
        self.speak(text)
        self.btn_next.visible = True

    def _next_line(self):
        if self.dialog:
            self.dialog.pop(0)
        if self.dialog:
            self._show_line()
            return
        self.btn_next.visible = False
        then, self.dialog_then = self.dialog_then, None
        if then:
            then()

    @property
    def in_dialog(self):
        return bool(self.dialog)

    def task(self, text, hint="", hint2="", drawer=None, choices=None, on_choice=None, keep_errors=False):
        self.dialog = []
        self.dialog_then = None
        self.btn_next.visible = False
        self.task_text = text
        self.bubble.set_text(text)
        self.parrot.talk(min(3.0, 0.5 + len(text) * 0.035))
        self.speak(text)
        if not keep_errors:
            self.q_errors = 0
            self.hint_level = 0
            self.btn_hint.visible = False
            self.btn_hint.pulse = False
        self.hint = (hint, hint2 or hint)
        self.hint_drawer = drawer
        if choices:
            self.set_choices(choices, on_choice)
        else:
            self.clear_choices()

    def set_choices(self, choices, on_choice):
        """choices: lista di (testo, valore[, colore]). Pulsanti grandi nella colonna di sinistra."""
        self.on_choice = on_choice
        self.choices = []
        n = len(choices)
        if n <= 2:
            rows = [548]
            self.bubble.set_rect(C.BUBBLE_RECT)
        else:
            rows = [450, 548]
            self.bubble.set_rect(C.BUBBLE_RECT_SHORT)
        for i, ch in enumerate(choices):
            label, value = ch[0], ch[1]
            color = ch[2] if len(ch) > 2 else C.BTN_BLUE
            row = rows[i // 2] if n > 2 else rows[0]
            col = i % 2
            if n == 3 and i == 2:
                rect = (110, row, 190, 86)
            elif n == 1:
                rect = (92, row, 236, 86)
            else:
                rect = (14 + col * 200, row, 188, 86)
            btn = Button(rect, label, None, color)
            btn.on_click = (lambda v=value, b=btn: self._choice(v, b))
            self.choices.append(btn)

    def _choice(self, value, btn):
        if self.on_choice:
            self.on_choice(value, btn)

    def clear_choices(self):
        self.choices = []
        self.on_choice = None
        self.bubble.set_rect(C.BUBBLE_RECT)

    # ------------------------------------------------------------ feedback
    def wrong(self, msg=None, count=True, center=None):
        msg = msg or T.WRONG_DEFAULT
        if count:
            self.q_errors += 1
            self.app.state.add_error(self.stage)
        self.toast = Toast(msg, False, center or (845, 150))
        self.app.audio.play("wrong")
        self.parrot.think()
        self.speak(msg)
        if self.q_errors >= 2 and self.hint[0]:
            if not self.btn_hint.visible:
                self.btn_hint.visible = True
            self.btn_hint.pulse = True

    def right(self, msg=None, speak=True, center=None, sound="correct"):
        msg = msg or random.choice(T.RIGHT_DEFAULT)
        self.toast = Toast(msg, True, center or (845, 150))
        self.app.audio.play(sound)
        self.parrot.happy()
        if speak:
            self.speak(msg)

    def info(self, msg, center=None):
        """Avviso gentile che non conta come errore (es. una roccia)."""
        self.toast = Toast(msg, False, center or (845, 150), 1.8)
        self.app.audio.play("bump")
        self.speak(msg)

    def open_hint(self):
        if self.card is not None:
            return
        explicit = self.q_errors >= 4
        self.hint_level = max(self.hint_level, 2 if explicit else 1)
        text = self.hint[1] if explicit else self.hint[0]
        self.card = HintCard(text, explicit, self._close_card, self.hint_drawer)
        self.btn_hint.pulse = False
        self.speak(text)
        self.on_hint(self.hint_level)

    def on_hint(self, level):
        """Le tappe possono mostrare aiuti nella scena (lettere chiare, frecce...)."""

    def _close_card(self):
        self.card = None

    def after(self, seconds, fn):
        self.timers.append([seconds, fn])

    # ------------------------------------------------------------ fine tappa
    def complete(self, rule=None, delay=1.0):
        if self.finished:
            return
        self.finished = True
        self.locked = True
        self.clear_choices()
        self.btn_hint.visible = False
        item = C.STAGE_ITEM.get(self.stage)
        rule = rule or T.STAGE_RULES.get(self.stage, "")
        self.after(delay, lambda: self._show_complete(item, rule))

    def _show_complete(self, item, rule):
        self.card = CompleteCard(T.STAGE_DONE, item, rule, lambda: self._after_card(item))
        self.app.audio.play("victory", 0.7)
        self.speak(T.STAGE_DONE + " " + rule)

    def _after_card(self, item):
        center = self.card.item_center() if self.card else (640, 360)
        self.card = None
        self.app.state.last_completed = self.stage
        if item:
            self.inventory.fly_in(item, center, on_done=self._finish)
        else:
            self._finish()

    def _finish(self):
        save.save_game(self.app.state)
        self.after(0.6, lambda: self.app.go_map(self.stage + 1))

    # ------------------------------------------------------------ eventi
    def handle_event(self, ev):
        if self.card is not None:
            self.card.handle_event(ev)
            return
        if self.btn_pause.handle_event(ev):
            return
        if self.btn_hint.handle_event(ev):
            return
        if self.btn_next.handle_event(ev):
            return
        for b in list(self.choices):
            if b.handle_event(ev):
                return
        for b in list(self.buttons):
            if b.handle_event(ev):
                return
        if self.in_dialog or self.locked:
            return
        self.on_event(ev)

    def on_event(self, ev):
        """Da ridefinire: interazioni nell'area di gioco."""

    @staticmethod
    def in_play(pos):
        return pygame.Rect(C.PLAY_RECT).collidepoint(pos)

    # ------------------------------------------------------------ update
    def update(self, dt):
        super().update(dt)
        self.parrot.update(dt)
        self.bubble.update(dt)
        for b in [self.btn_next, self.btn_hint, self.btn_pause] + self.choices + self.buttons:
            b.update(dt)
        self.inventory.update(dt)
        if self.toast:
            self.toast.update(dt)
            if self.toast.done:
                self.toast = None
        if self.card:
            self.card.update(dt)
        due = []
        for tm in self.timers:
            tm[0] -= dt
            if tm[0] <= 0:
                due.append(tm)
        for tm in due:
            if tm in self.timers:
                self.timers.remove(tm)
                tm[1]()
        self.on_update(dt)

    def on_update(self, dt):
        pass

    # ------------------------------------------------------------ disegno
    def draw(self, surf):
        self.draw_background(surf)
        self.draw_play(surf)
        self.draw_panel(surf)
        self.draw_topbar(surf)
        self.inventory.draw(surf)
        self.draw_front(surf)
        if self.toast:
            self.toast.draw(surf)
        if self.card:
            self.card.draw(surf)

    def draw_background(self, surf):
        surf.fill((90, 160, 220))

    def draw_play(self, surf):
        pass

    def draw_front(self, surf):
        for g in self.drag_groups:
            g.draw_dragging(surf)

    def draw_panel(self, surf):
        G.alpha_rect(surf, pygame.Rect(0, C.TOPBAR_H, C.PANEL_W, C.INV_Y - C.TOPBAR_H), self.panel_color, 0)
        self.parrot.draw(surf)
        self.bubble.draw(surf)
        self.btn_hint.draw(surf)
        self.btn_next.draw(surf)
        for b in self.choices:
            b.draw(surf)

    def draw_topbar(self, surf):
        G.alpha_rect(surf, pygame.Rect(0, 0, C.WIDTH, C.TOPBAR_H), (16, 26, 56, self.topbar_alpha), 0)
        fonts.draw(surf, f"Tappa {self.stage} di 6", (20, 8), 26, (255, 220, 90), True, shadow=(0, 0, 0))
        fonts.draw(surf, self.title, (20, 40), 34, C.WHITE, True, shadow=(0, 0, 0))
        draw_timer(surf, self.app, (955, 46))
        if "rosa" in self.app.state.inventory:
            G.draw_compass_rose(surf, (1118, 46), 23, labels=True, label_size=19)
        self.btn_pause.draw(surf)
        for b in self.buttons:
            b.draw(surf)


def draw_timer(surf, app, center):
    minutes = app.options.timer_minutes
    if not minutes:
        return
    remaining = minutes * 60 - app.state.elapsed
    if remaining > 0:
        m, s = divmod(int(math.ceil(remaining)), 60)
        text = f"{m:02d}:{s:02d}"
        color = C.WHITE if remaining > 300 else (255, 214, 80)
    else:
        m, s = divmod(int(-remaining), 60)
        text = f"+{m:02d}:{s:02d}"
        color = (255, 190, 120)
    G.icon_clock(surf, (center[0] - 62, center[1]), 20, C.WHITE, (app.state.elapsed % 60) / 60)
    fonts.draw(surf, text, (center[0] - 34, center[1]), 34, color, True, anchor="midleft", shadow=(0, 0, 0),
               transform=False)
