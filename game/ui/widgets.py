"""Widget dell'interfaccia: pensati per la LIM (solo tocco/mouse, elementi grandi).

Gli eventi arrivano già convertiti in coordinate logiche (1280x720).
I pulsanti scattano alla pressione (più affidabile sul tocco) con un breve
intervallo di sicurezza contro i doppi tocchi.
"""

import math

import pygame

from .. import config as C
from ..gfx import draw as G
from . import fonts

DOWN, UP, MOTION = pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION

# Impostato dall'App: funzione play(nome_suono)
SOUND_HOOK = None


def play_sound(name):
    if SOUND_HOOK and name:
        try:
            SOUND_HOOK(name)
        except Exception:
            pass


def now_ms():
    return pygame.time.get_ticks()


# ================================================================ Button
class Button:
    COOLDOWN_MS = 280
    _last_fire = -100000

    def __init__(self, rect, text="", on_click=None, color=C.BTN_BLUE, text_color=C.WHITE, icon=None,
                 font_size=C.FONT_BUTTON, sound="click", icon_color=None):
        self.rect = pygame.Rect(rect)
        if self.rect.h < C.BUTTON_MIN_H:
            self.rect.h = C.BUTTON_MIN_H
        self.text = text
        self.on_click = on_click
        self.color = color
        self.text_color = text_color
        self.icon = icon
        self.icon_color = icon_color or text_color
        self.font_size = font_size
        self.sound = sound
        self.visible = True
        self.enabled = True
        self.pulse = False
        self.selected = None   # None = non è un interruttore; True/False = mostra il cerchio con la spunta
        self.hover = False
        self.press_t = 0.0
        self.t = 0.0
        self.mark = None       # None / "ok" / "ko": badge di feedback sopra il pulsante
        self.mark_t = 0.0

    @classmethod
    def reset_cooldown(cls):
        cls._last_fire = -100000

    def fire(self):
        Button._last_fire = now_ms()
        self.press_t = 0.15
        play_sound(self.sound)
        if self.on_click:
            self.on_click()

    def handle_event(self, ev):
        if not (self.visible and self.enabled):
            return False
        if ev.type == MOTION:
            self.hover = self.rect.collidepoint(ev.pos)
            return False
        if ev.type == DOWN and self.rect.collidepoint(ev.pos):
            if now_ms() - Button._last_fire < self.COOLDOWN_MS:
                return True
            self.fire()
            return True
        return False

    def flash(self, ok):
        self.mark = "ok" if ok else "ko"
        self.mark_t = 1.4

    def update(self, dt):
        self.t += dt
        self.press_t = max(0.0, self.press_t - dt)
        if self.mark_t > 0:
            self.mark_t -= dt
            if self.mark_t <= 0:
                self.mark = None

    def draw(self, surf):
        if not self.visible:
            return
        r = self.rect
        radius = min(22, r.h // 3)
        color = self.color if self.enabled else (150, 154, 162)
        pressed = self.press_t > 0
        dy = 4 if pressed else 0
        if self.pulse and self.enabled:
            k = 0.5 + 0.5 * math.sin(self.t * 6)
            G.alpha_rect(surf, r.inflate(14 + 8 * k, 14 + 8 * k).move(0, 2), (255, 230, 60, int(120 + 100 * k)), radius + 8)
        G.rounded_rect(surf, G.shade(color, 0.62), r.move(0, 6), radius)
        face = r.move(0, dy)
        G.rounded_rect(surf, G.shade(color, 1.1) if self.hover and not pressed else color, face, radius)
        G.rounded_rect(surf, G.shade(color, 1.28), pygame.Rect(face.x + 8, face.y + 5, face.w - 16, 6), 3)
        content_left = face.x + 14
        if self.selected is not None:
            cc = (face.x + 34, face.centery)
            G.aa_circle(surf, C.WHITE, cc, 17)
            if self.selected:
                G.aa_circle(surf, G.shade(color, 0.6), cc, 13)
                G.icon_check(surf, cc, 22, C.WHITE, 4)
            else:
                G.aa_circle(surf, G.shade(color, 0.9), cc, 13)
            content_left = face.x + 58
        avail = pygame.Rect(content_left, face.y, face.right - 12 - content_left, face.h)
        icon_size = int(min(face.h * 0.5, 44))
        if self.icon and self.text:
            size = self._fit_size(avail.w - icon_size - 12)
            tw = fonts.text_size(self.text, size, True)[0]
            total = icon_size + 12 + tw
            x0 = avail.centerx - total // 2
            G.draw_icon(surf, self.icon, (x0 + icon_size / 2, face.centery), icon_size, self.icon_color)
            fonts.draw(surf, self.text, (x0 + icon_size + 12, face.centery), size, self.text_color, True, anchor="midleft")
        elif self.icon:
            G.draw_icon(surf, self.icon, face.center, int(min(face.h, face.w) * 0.55), self.icon_color)
        elif self.text:
            size = self._fit_size(avail.w)
            fonts.draw(surf, self.text, avail.center, size, self.text_color, True, anchor="center")
        if self.mark:
            G.badge(surf, (face.right - 6, face.y + 6), 20, self.mark == "ok")

    def _fit_size(self, width):
        size = self.font_size
        while size > 22 and fonts.text_size(self.text, size, True)[0] > width:
            size -= 2
        return size


# ================================================================ trascinabili
class Draggable:
    """Etichetta (o oggetto) trascinabile con mouse o tocco."""

    def __init__(self, home, size=(96, 96), text="", color=C.BTN_BLUE, text_color=C.WHITE, drawer=None,
                 data=None, font_size=52):
        self.home = (float(home[0]), float(home[1]))
        self.pos = list(self.home)
        self.size = size
        self.text = text
        self.color = color
        self.text_color = text_color
        self.drawer = drawer
        self.data = data if data is not None else text
        self.font_size = font_size
        self.on_drop = None   # funzione(drag, pos) -> True se accettato
        self.dragging = False
        self.locked = False
        self.visible = True
        self.enabled = True
        self.glow = False
        self.grab = (0.0, 0.0)
        self.anim = None
        self.t = 0.0
        self.moved = 0.0
        self._not_pressed = 0.0
        self.scale_anim = 0.0

    @property
    def rect(self):
        r = pygame.Rect(0, 0, *self.size)
        r.center = (int(self.pos[0]), int(self.pos[1]))
        return r

    def hit(self, pos):
        return self.rect.inflate(20, 20).collidepoint(pos)

    def start_drag(self, pos):
        self.dragging = True
        self.anim = None
        self.moved = 0.0
        self._not_pressed = 0.0
        self.grab = (self.pos[0] - pos[0], self.pos[1] - pos[1])
        play_sound("click")

    def handle_event(self, ev):
        if not (self.visible and self.enabled) or self.locked:
            return False
        if ev.type == DOWN and not self.dragging and self.hit(ev.pos):
            self.start_drag(ev.pos)
            return True
        if ev.type == MOTION and self.dragging:
            nx, ny = ev.pos[0] + self.grab[0], ev.pos[1] + self.grab[1]
            self.moved += math.hypot(nx - self.pos[0], ny - self.pos[1])
            self.pos = [G.clamp(nx, 0, C.WIDTH), G.clamp(ny, 0, C.HEIGHT)]
            self._not_pressed = 0.0
            return True
        if ev.type in (UP, DOWN) and self.dragging:
            # DOWN mentre si trascina = l'UP precedente è andato perso: si lascia lì.
            if ev.type == UP:
                self.pos = [G.clamp(ev.pos[0] + self.grab[0], 0, C.WIDTH), G.clamp(ev.pos[1] + self.grab[1], 0, C.HEIGHT)]
            self.drop()
            return True
        return False

    def drop(self):
        self.dragging = False
        accepted = False
        if self.on_drop:
            accepted = self.on_drop(self, (self.pos[0], self.pos[1]))
        if not accepted and not self.locked:
            self.go_home()

    def cancel(self):
        if self.dragging:
            self.dragging = False
            self.go_home()

    def go_home(self, bounce=True):
        self.anim = ((self.pos[0], self.pos[1]), self.home, 0.0, 0.5 if bounce else 0.25, bounce)

    def snap(self, center, lock=True):
        self.home = (float(center[0]), float(center[1]))
        self.anim = ((self.pos[0], self.pos[1]), self.home, 0.0, 0.22, False)
        self.locked = lock
        self.scale_anim = 0.35

    def place(self, center):
        self.home = (float(center[0]), float(center[1]))
        self.pos = list(self.home)
        self.anim = None

    def update(self, dt):
        self.t += dt
        self.scale_anim = max(0.0, self.scale_anim - dt)
        if self.dragging:
            pressed = any(pygame.mouse.get_pressed()) if pygame.display.get_init() else True
            self._not_pressed = 0.0 if pressed else self._not_pressed + dt
            if self._not_pressed > 0.6:  # l'UP non è mai arrivato
                self.drop()
        if self.anim:
            a, b, t, dur, bounce = self.anim
            t += dt
            k = min(1.0, t / dur)
            e = G.ease_out_back(k, 2.2) if bounce else G.ease_out(k)
            self.pos = [G.lerp(a[0], b[0], e), G.lerp(a[1], b[1], e)]
            self.anim = None if k >= 1 else (a, b, t, dur, bounce)

    def draw(self, surf):
        if not self.visible:
            return
        r = self.rect
        if self.dragging or self.scale_anim > 0:
            grow = 10 if self.dragging else int(12 * math.sin(self.scale_anim / 0.35 * math.pi))
            r = r.inflate(grow, grow)
        if self.glow and not self.locked and not self.dragging:
            k = 0.5 + 0.5 * math.sin(self.t * 5)
            G.alpha_rect(surf, r.inflate(18 + 8 * k, 18 + 8 * k), (255, 230, 60, int(110 + 100 * k)), 26)
        if self.dragging:
            G.alpha_rect(surf, r.move(6, 10), (0, 0, 0, 80), 20)
        if self.drawer:
            self.drawer(surf, r, self)
            return
        G.rounded_rect(surf, G.shade(self.color, 0.6), r.move(0, 5), 20)
        G.rounded_rect(surf, self.color, r, 20)
        G.rounded_rect(surf, (255, 255, 255), r, 20, 4)
        fonts.draw(surf, self.text, r.center, self.font_size, self.text_color, True, anchor="center",
                   transform=False)


class DragGroup:
    def __init__(self, items=None):
        self.items = list(items or [])

    def add(self, item):
        self.items.append(item)
        return item

    def active(self):
        for it in self.items:
            if it.dragging:
                return it
        return None

    def handle_event(self, ev):
        act = self.active()
        if act is not None:
            return act.handle_event(ev)
        if ev.type == DOWN:
            for it in reversed(self.items):
                if it.handle_event(ev):
                    self.items.remove(it)
                    self.items.append(it)
                    return True
        return False

    def cancel(self):
        for it in self.items:
            it.cancel()

    def update(self, dt):
        for it in self.items:
            it.update(dt)

    def draw(self, surf):
        """Disegna gli oggetti fermi; quelli trascinati li disegna draw_dragging (sopra a tutto)."""
        for it in self.items:
            if not it.dragging:
                it.draw(surf)

    def draw_dragging(self, surf):
        for it in self.items:
            if it.dragging:
                it.draw(surf)


class DropSlot:
    def __init__(self, rect, key, color=(255, 255, 255)):
        self.rect = pygame.Rect(rect)
        self.key = key
        self.color = color
        self.content = None
        self.hover = False
        self.ghost = None   # lettera chiara mostrata come indizio
        self.glow = False
        self.t = 0.0

    def update(self, dt, drag=None):
        self.t += dt
        self.hover = bool(drag and self.content is None and self.rect.inflate(30, 30).collidepoint(drag.pos))

    def accepts_point(self, pos, margin=34):
        return self.rect.inflate(margin * 2, margin * 2).collidepoint(pos)

    def draw(self, surf):
        r = self.rect
        if self.glow and self.content is None:
            k = 0.5 + 0.5 * math.sin(self.t * 5)
            G.alpha_rect(surf, r.inflate(16 + 10 * k, 16 + 10 * k), (255, 230, 60, int(110 + 110 * k)), 26)
        fill = (255, 250, 210, 230) if self.hover else (255, 255, 255, 150)
        G.alpha_rect(surf, r, fill, 20)
        dash_rect(surf, r, (60, 60, 80), 4, 20, t=self.t)
        if self.ghost and self.content is None:
            fonts.draw(surf, self.ghost, r.center, 52, (190, 190, 200), True, anchor="center", transform=False)


def dash_rect(surf, rect, color, width=3, radius=18, dash=14, gap=10, t=0.0):
    r = pygame.Rect(rect).inflate(-radius, -radius)
    off = t * 20
    G.dashed_line(surf, color, (r.left, rect.top + 2), (r.right, rect.top + 2), width, dash, gap, off)
    G.dashed_line(surf, color, (rect.right - 2, r.top), (rect.right - 2, r.bottom), width, dash, gap, off)
    G.dashed_line(surf, color, (r.right, rect.bottom - 2), (r.left, rect.bottom - 2), width, dash, gap, off)
    G.dashed_line(surf, color, (rect.left + 2, r.bottom), (rect.left + 2, r.top), width, dash, gap, off)


# ================================================================ slider
class Slider:
    def __init__(self, rect, value=0.0, on_change=None, on_release=None, left="Mattina", right="Sera"):
        self.rect = pygame.Rect(rect)
        self.value = value
        self.on_change = on_change
        self.on_release = on_release
        self.left = left
        self.right = right
        self.dragging = False
        self.enabled = True
        self.visible = True
        self.marker = None   # valore da evidenziare (indizio)
        self.knob_r = 42
        self.label_mode = "below"
        self.t = 0.0

    def _x_to_value(self, x):
        return G.clamp((x - self.rect.x) / self.rect.w, 0.0, 1.0)

    def knob_center(self):
        return (self.rect.x + self.value * self.rect.w, self.rect.centery)

    def handle_event(self, ev):
        if not (self.enabled and self.visible):
            return False
        hit = self.rect.inflate(2 * self.knob_r + 20, 2 * self.knob_r + 10)
        if ev.type == DOWN and hit.collidepoint(ev.pos):
            self.dragging = True
            self.set_value(self._x_to_value(ev.pos[0]))
            return True
        if ev.type == MOTION and self.dragging:
            self.set_value(self._x_to_value(ev.pos[0]))
            return True
        if ev.type == UP and self.dragging:
            self.dragging = False
            self.set_value(self._x_to_value(ev.pos[0]))
            if self.on_release:
                self.on_release(self.value)
            return True
        return False

    def set_value(self, v):
        self.value = v
        if self.on_change:
            self.on_change(v)

    def update(self, dt):
        self.t += dt
        if self.dragging and pygame.display.get_init() and not any(pygame.mouse.get_pressed()):
            self.dragging = False
            if self.on_release:
                self.on_release(self.value)

    def draw(self, surf):
        if not self.visible:
            return
        r = self.rect
        track = pygame.Rect(r.x, r.centery - 12, r.w, 24)
        G.rounded_rect(surf, (60, 50, 40), track.move(0, 3), 12)
        n = 24
        for i in range(n):
            k = i / (n - 1)
            col = G.lerp_color((250, 140, 60), (255, 230, 90), 1 - abs(k - 0.5) * 2)
            x0 = track.x + int(track.w * i / n)
            x1 = track.x + int(track.w * (i + 1) / n)
            pygame.draw.rect(surf, col, (x0, track.y, x1 - x0 + 1, track.h))
        G.rounded_rect(surf, (90, 70, 50), track, 12, 3)
        if self.marker is not None:
            mx = r.x + self.marker * r.w
            k = 0.5 + 0.5 * math.sin(self.t * 6)
            tri = [(mx, track.y - 6), (mx - 18, track.y - 38 - 6 * k), (mx + 18, track.y - 38 - 6 * k)]
            G.aa_polygon(surf, (120, 90, 10), [(x, y + 3) for x, y in tri])
            G.aa_polygon(surf, (255, 230, 40), tri)
        if self.label_mode == "sides":
            lx, rx = r.x - 76, r.right + 76
            G.draw_sun(surf, (lx, r.centery - 22), 13, 0, (255, 160, 70), rays=False)
            G.draw_sun(surf, (rx, r.centery - 22), 13, 0, (250, 110, 60), rays=False)
            fonts.draw(surf, self.left, (lx, r.centery + 12), 26, C.WHITE, True, anchor="center", shadow=(40, 30, 20))
            fonts.draw(surf, self.right, (rx, r.centery + 12), 26, C.WHITE, True, anchor="center", shadow=(40, 30, 20))
        else:
            G.draw_sun(surf, (r.x - 50, r.centery), 16, 0, (255, 160, 70), rays=False)
            G.draw_sun(surf, (r.right + 50, r.centery), 16, 0, (250, 110, 60), rays=False)
            fonts.draw(surf, self.left, (r.x, r.centery + 34), 26, C.WHITE, True, anchor="midtop", shadow=(40, 30, 20))
            fonts.draw(surf, self.right, (r.right, r.centery + 34), 26, C.WHITE, True, anchor="midtop", shadow=(40, 30, 20))
        kc = self.knob_center()
        G.aa_circle(surf, (60, 40, 20), (kc[0], kc[1] + 4), self.knob_r)
        G.aa_circle(surf, (255, 255, 255), kc, self.knob_r)
        G.draw_sun(surf, kc, self.knob_r * 0.62, self.t, (255, 200, 50), rays=False)


# ================================================================ fumetto
class SpeechBubble:
    def __init__(self, rect, tail_to):
        self.rect = pygame.Rect(rect)
        self.tail_to = tail_to
        self.text = ""
        self.pop = 0.0
        self.visible = True
        self._layout = None

    def set_text(self, text):
        if text != self.text:
            self.text = text
            self.pop = 0.25
            self._layout = None

    def set_rect(self, rect):
        rect = pygame.Rect(rect)
        if rect != self.rect:
            self.rect = rect
            self._layout = None

    def update(self, dt):
        self.pop = max(0.0, self.pop - dt)

    def draw(self, surf):
        if not self.visible or not self.text:
            return
        r = self.rect
        if self.pop > 0:
            k = 1 - self.pop / 0.25
            s = 0.9 + 0.1 * G.ease_out_back(k)
            r = pygame.Rect(0, 0, int(r.w * s), int(r.h * s))
            r.center = self.rect.center
        G.alpha_rect(surf, r.move(0, 6), (0, 0, 0, 70), 26)
        tx = G.clamp(self.tail_to[0], r.x + 40, r.right - 40)
        tail = [(tx - 22, r.y + 4), (self.tail_to[0], self.tail_to[1]), (tx + 22, r.y + 4)]
        G.aa_polygon(surf, (40, 44, 70), [(tail[0][0] - 3, tail[0][1]), (tail[1][0], tail[1][1] - 4), (tail[2][0] + 3, tail[2][1])])
        G.rounded_rect(surf, C.WHITE, r, 26)
        G.rounded_rect(surf, (40, 44, 70), r, 26, 4)
        G.aa_polygon(surf, C.WHITE, [(tail[0][0] + 1, tail[0][1] + 6), tail[1], (tail[2][0] - 1, tail[2][1] + 6)])
        inner = r.inflate(-30, -26)
        if self._layout is None or self._layout[0] != (inner.size, fonts.is_uppercase()):
            size, lines = fonts.fit(self.text, inner.w, inner.h, (34, 32, 30, 28))
            self._layout = ((inner.size, fonts.is_uppercase()), size, lines)
        _, size, lines = self._layout
        fonts.draw_lines(surf, lines, inner, size, C.TEXT_DARK, False, "center", "center")


# ================================================================ feedback
class Toast:
    def __init__(self, text, ok, center=(845, 150), duration=2.2):
        self.text = text
        self.ok = ok
        self.center = center
        self.duration = duration
        self.t = 0.0

    @property
    def done(self):
        return self.t >= self.duration

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        k = min(1.0, self.t / 0.25)
        fade = 1.0 if self.t < self.duration - 0.3 else max(0.0, (self.duration - self.t) / 0.3)
        if fade <= 0:
            return
        size, lines = fonts.fit(self.text, 520, 90, (32, 30, 28), True)
        tw = max(fonts.get(size, True).size(line)[0] for line in lines)
        w = tw + 120
        h = max(92, len(lines) * fonts.line_height(size, True) + 30)
        s = 0.8 + 0.2 * G.ease_out_back(k)
        rect = pygame.Rect(0, 0, int(w * s), int(h * s))
        rect.center = self.center
        col = C.OK_GREEN if self.ok else C.KO_ORANGE
        G.alpha_rect(surf, rect.move(0, 6), (0, 0, 0, int(70 * fade)), 24)
        G.rounded_rect(surf, C.WHITE, rect, 24)
        G.rounded_rect(surf, col, rect, 24, 5)
        G.badge(surf, (rect.x + 46, rect.centery), 28, self.ok)
        text_rect = pygame.Rect(rect.x + 86, rect.y, rect.w - 100, rect.h)
        fonts.draw_lines(surf, lines, text_rect, size, C.TEXT_DARK, True, "left", "center")


class HintCard:
    """Riquadro dell'indizio (con eventuale disegno) e pulsante "Ho capito!"."""

    def __init__(self, text, explicit, on_close, drawer=None):
        self.text = text
        self.explicit = explicit
        self.drawer = drawer
        self.on_close = on_close
        self.t = 0.0
        w = 780 if drawer else 680
        h = 430 if drawer else 340
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (845, 360)
        self.btn = Button((0, 0, 300, 84), "Ho capito!", self._close, C.BTN_GREEN, icon="check")
        self.btn.rect.midbottom = (self.rect.centerx, self.rect.bottom - 22)

    def _close(self):
        if self.on_close:
            self.on_close()

    def handle_event(self, ev):
        self.btn.handle_event(ev)
        return True  # finestra modale

    def update(self, dt):
        self.t += dt
        self.btn.update(dt)

    def draw(self, surf):
        G.alpha_rect(surf, pygame.Rect(0, 0, C.WIDTH, C.HEIGHT), (0, 0, 0, 90), 0)
        k = G.ease_out_back(min(1.0, self.t / 0.3))
        r = self.rect.inflate(-(1 - k) * 80, -(1 - k) * 60)
        G.panel(surf, r, (255, 250, 222), 28, border=(214, 160, 30))
        G.icon_bulb(surf, (r.x + 52, r.y + 52), 62)
        title = "Indizio speciale" if self.explicit else "Indizio"
        fonts.draw(surf, title, (r.x + 96, r.y + 52), 38, (150, 96, 10), True, anchor="midleft")
        if self.drawer:
            art = pygame.Rect(r.x + 24, r.y + 96, 330, r.h - 210)
            self.drawer(surf, art, self.t)
            text_rect = pygame.Rect(art.right + 20, r.y + 96, r.right - art.right - 44, r.h - 210)
        else:
            text_rect = pygame.Rect(r.x + 36, r.y + 96, r.w - 72, r.h - 210)
        fonts.draw_wrapped(surf, self.text, text_rect, (34, 32, 30, 28), C.TEXT_DARK, False, "center", "center")
        self.btn.rect.midbottom = (r.centerx, r.bottom - 22)
        self.btn.draw(surf)


class CompleteCard:
    """Schermata "Tappa superata!" con oggetto guadagnato e regola imparata."""

    def __init__(self, title, item, rule, on_next, button_text="Avanti"):
        self.title = title
        self.item = item
        self.rule = rule
        self.on_next = on_next
        self.t = 0.0
        self.rect = pygame.Rect(0, 0, 820, 500)
        self.rect.center = (C.WIDTH // 2, 350)
        self.btn = Button((0, 0, 300, 86), button_text, self._next, C.BTN_GREEN, icon="play")
        self.closing = False

    def _next(self):
        if not self.closing:
            self.closing = True
            if self.on_next:
                self.on_next()

    def item_center(self):
        return (self.rect.centerx, self.rect.y + 190)

    def handle_event(self, ev):
        if self.t > 0.6:
            self.btn.handle_event(ev)
        return True

    def update(self, dt):
        self.t += dt
        self.btn.update(dt)

    def draw(self, surf):
        G.alpha_rect(surf, pygame.Rect(0, 0, C.WIDTH, C.HEIGHT), (10, 20, 40, 150), 0)
        k = G.ease_out_back(min(1.0, self.t / 0.35))
        r = self.rect.inflate(-(1 - k) * 160, -(1 - k) * 100)
        G.panel(surf, r, (255, 252, 236), 32, border=(230, 170, 40))
        fonts.draw_outlined(surf, self.title, (r.centerx, r.y + 60), 54, (255, 210, 50), (120, 70, 0), True, width=3)
        for i in range(8):
            a = self.t * 0.8 + i * math.pi / 4
            rr = 110 + 8 * math.sin(self.t * 3 + i)
            p = (r.centerx + math.cos(a) * rr, r.y + 190 + math.sin(a) * rr * 0.55)
            G.draw_star(surf, p, 10 + 3 * math.sin(self.t * 4 + i), (255, 214, 60))
        if self.item:
            G.aa_circle(surf, (255, 236, 170), (r.centerx, r.y + 190), 78)
            G.blit_item(surf, self.item, (r.centerx, r.y + 190), 2.0)
        text_rect = pygame.Rect(r.x + 50, r.y + 285, r.w - 100, 110)
        fonts.draw_wrapped(surf, self.rule, text_rect, (38, 36, 34, 32, 30), C.TEXT_DARK, True, "center", "center")
        self.btn.rect.midbottom = (r.centerx, r.bottom - 22)
        if self.t > 0.6:
            self.btn.draw(surf)


# ================================================================ inventario
class InventoryBar:
    def __init__(self, state):
        self.state = state
        self.rect = pygame.Rect(0, C.INV_Y, C.WIDTH, C.INV_H)
        self.flying = []   # [item, from, t, on_done]
        self.pop = {}
        self._layout = None
        self._cached = None

    def _compute_layout(self):
        size = 26
        icon_w = 62
        while True:
            widths = [icon_w + fonts.text_size(C.ITEM_NAMES[i], size, True)[0] + 26 for i in C.ITEMS]
            if sum(widths) + 12 * (len(widths) - 1) <= C.WIDTH - 28 or size <= 18:
                break
            size -= 2
        total = sum(widths) + 12 * (len(widths) - 1)
        x = (C.WIDTH - total) // 2
        slots = {}
        for item, w in zip(C.ITEMS, widths):
            slots[item] = pygame.Rect(x, self.rect.y + 8, w, self.rect.h - 16)
            x += w + 12
        return (fonts.is_uppercase(), size, slots)

    def layout(self):
        if self._layout is None or self._layout[0] != fonts.is_uppercase():
            self._layout = self._compute_layout()
        return self._layout

    def slot_center(self, item):
        _, _, slots = self.layout()
        r = slots[item]
        return (r.x + 36, r.centery)

    def fly_in(self, item, from_pos, on_done=None):
        self.flying.append([item, from_pos, 0.0, on_done])
        play_sound("whoosh")

    def update(self, dt):
        for f in list(self.flying):
            f[2] += dt
            if f[2] >= 0.9:
                self.flying.remove(f)
                self.state.add_item(f[0])
                self.pop[f[0]] = 0.4
                play_sound("pop")
                if f[3]:
                    f[3]()
        for k in list(self.pop):
            self.pop[k] -= dt
            if self.pop[k] <= 0:
                del self.pop[k]

    def draw(self, surf):
        flying = {f[0] for f in self.flying}
        if not self.flying and not self.pop:
            key = (tuple(self.state.inventory), fonts.is_uppercase())
            if self._cached is None or self._cached[0] != key:
                img = pygame.Surface(self.rect.size, pygame.SRCALPHA)
                self._draw_bar(img, set(), offset=self.rect.y)
                self._cached = (key, img)
            surf.blit(self._cached[1], self.rect.topleft)
            return
        self._draw_bar(surf, flying)
        self._draw_flying(surf)

    def _draw_bar(self, surf, flying, offset=0):
        bar = self.rect.move(0, -offset)
        G.alpha_rect(surf, bar, (52, 34, 20, 235), 0)
        pygame.draw.line(surf, (150, 100, 50), (0, bar.y), (C.WIDTH, bar.y), 4)
        _, size, slots = self.layout()
        for item in C.ITEMS:
            r = slots[item].move(0, -offset)
            have = item in self.state.inventory and item not in flying
            if have:
                G.rounded_rect(surf, (255, 244, 214), r, 16)
                scale = 1.0 + 0.35 * math.sin(self.pop.get(item, 0) / 0.4 * math.pi) if item in self.pop else 1.0
                G.blit_item(surf, item, (r.x + 36, r.centery), 0.9 * scale)
                fonts.draw(surf, C.ITEM_NAMES[item], (r.x + 68, r.centery), size, C.TEXT_DARK, True, anchor="midleft")
            else:
                G.alpha_rect(surf, r, (255, 255, 255, 40), 16)
                dash_rect(surf, r, (190, 160, 120), 3, 16)
                fonts.draw(surf, "?", (r.x + 36, r.centery), 34, (190, 160, 120), True, anchor="center", transform=False)

    def _draw_flying(self, surf):
        for item, start, t, _ in self.flying:
            k = G.ease_in_out(min(1.0, t / 0.9))
            end = self.slot_center(item)
            x = G.lerp(start[0], end[0], k)
            y = G.lerp(start[1], end[1], k) - math.sin(k * math.pi) * 160
            G.blit_glow(surf, (x, y), 50, (90, 80, 30), 0.8)
            G.blit_item(surf, item, (x, y), G.lerp(2.0, 0.9, k))
