"""Applicazione: finestra, ciclo principale, cambio scena, scorciatoie, gestione errori."""

import logging
import os
import sys
import time

import pygame

from . import config as C
from . import save
from .audio import Audio
from .state import GameState
from .tts import TTS
from .ui import fonts, widgets

log = logging.getLogger("fuga")


def _set_dpi_aware():
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def make_window_icon():
    from .gfx import draw as G
    s = pygame.Surface((64, 64), pygame.SRCALPHA)
    G.aa_circle(s, (30, 110, 190), (32, 32), 31)
    G.draw_compass_rose(s, (32, 32), 24, labels=False, bg=True)
    return s


class App:
    def __init__(self, fullscreen=True):
        self.options = save.load_options()
        fonts.set_uppercase(self.options.uppercase)
        _set_dpi_aware()
        # Se la maestra passa a un'altra finestra, il gioco non si riduce a icona.
        os.environ.setdefault("SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS", "0")
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        from .gfx import draw as G
        fonts.reset()
        G.clear_caches()
        pygame.display.set_caption(C.TITLE)
        try:
            pygame.display.set_icon(make_window_icon())
        except Exception:
            pass
        self.fullscreen = fullscreen
        self._set_mode()
        self.canvas = pygame.Surface((C.WIDTH, C.HEIGHT), 0, 32)
        if pygame.display.get_surface().get_bitsize() >= 24:
            self.canvas = self.canvas.convert()
        self._scaled = None
        self.clock = pygame.time.Clock()
        self.audio = Audio(self.options.sound)
        widgets.SOUND_HOOK = self.audio.play
        self.tts = TTS()
        if self.options.tts:
            self.tts.enable()
        self.state = GameState()
        self.scene = None
        self.overlay = None
        self.running = True
        self.fade = 0.0
        self.time = 0.0
        self.crashes = []
        self.fatal_message = None
        self._last_down = (-1000.0, (0, 0))
        try:
            pygame.key.stop_text_input()
        except Exception:
            pass
        self.go_menu()

    # ------------------------------------------------------------ finestra
    def _set_mode(self):
        if self.fullscreen:
            try:
                pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            except pygame.error as exc:
                log.warning("Schermo intero non disponibile: %s", exc)
                self.fullscreen = False
        if not self.fullscreen:
            w, h = C.WIDTH, C.HEIGHT
            try:
                dw, dh = pygame.display.get_desktop_sizes()[0]
                if dw < w + 40 or dh < h + 80:
                    k = min((dw - 40) / w, (dh - 80) / h)
                    w, h = max(640, int(w * k)), max(360, int(h * k))
            except Exception:
                pass
            pygame.display.set_mode((w, h), pygame.RESIZABLE)
        self._scaled = None

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self._set_mode()

    def _view(self):
        ww, wh = pygame.display.get_surface().get_size()
        scale = min(ww / C.WIDTH, wh / C.HEIGHT)
        sw, sh = max(1, int(C.WIDTH * scale)), max(1, int(C.HEIGHT * scale))
        return scale, (ww - sw) // 2, (wh - sh) // 2, sw, sh

    def to_logical(self, pos, clamp=False):
        scale, ox, oy, _, _ = self._view()
        x = (pos[0] - ox) / scale
        y = (pos[1] - oy) / scale
        if clamp:
            x = min(max(x, 0), C.WIDTH - 1)
            y = min(max(y, 0), C.HEIGHT - 1)
        elif not (0 <= x < C.WIDTH and 0 <= y < C.HEIGHT):
            return None
        return (int(x), int(y))

    # ------------------------------------------------------------ ciclo
    def run(self):
        while self.running:
            dt = min(self.clock.tick(C.FPS) / 1000.0, 0.05)
            try:
                self.frame(dt)
            except Exception:
                self.on_crash()
        self.shutdown()

    def frame(self, dt):
        self.time += dt
        for ev in pygame.event.get():
            self.process_event(ev)
        self.audio.update()
        self.update(dt)
        self.render()

    def target(self):
        return self.overlay if self.overlay is not None else self.scene

    def process_event(self, ev):
        if ev.type == pygame.QUIT:
            self.running = False
            return
        if ev.type == pygame.KEYDOWN:
            if self._shortcut(ev):
                return
            self.target().handle_event(ev)
            return
        if ev.type == pygame.TEXTINPUT:
            self.target().handle_event(ev)
            return
        if ev.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            if getattr(ev, "button", 1) not in (1, 2, 3):
                return  # rotellina
            down = ev.type == pygame.MOUSEBUTTONDOWN
            lp = self.to_logical(ev.pos, clamp=not down)
            if lp is None:
                return
            if down:
                last_t, last_p = self._last_down
                if self.time - last_t < 0.07 and abs(lp[0] - last_p[0]) + abs(lp[1] - last_p[1]) < 30:
                    return  # doppio evento dello stesso tocco
                self._last_down = (self.time, lp)
            self.target().handle_event(pygame.event.Event(ev.type, pos=lp, button=1))
            return
        if ev.type == pygame.MOUSEMOTION:
            lp = self.to_logical(ev.pos, clamp=True)
            self.target().handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=lp, rel=ev.rel,
                                                          buttons=getattr(ev, "buttons", (0, 0, 0))))
            return
        if ev.type == pygame.WINDOWFOCUSLOST:
            self.scene.on_pause()
            return
        if ev.type in (pygame.WINDOWRESIZED, pygame.WINDOWSIZECHANGED):
            self._scaled = None

    def _shortcut(self, ev):
        mods = ev.mod
        if ev.key == pygame.K_F11:
            self.toggle_fullscreen()
            return True
        if (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_SHIFT):
            digit = None
            sc = getattr(ev, "scancode", 0)
            if pygame.K_1 <= ev.key <= pygame.K_6:
                digit = ev.key - pygame.K_0
            elif pygame.K_KP1 <= ev.key <= pygame.K_KP6:
                digit = ev.key - pygame.K_KP1 + 1
            elif 30 <= sc <= 35:
                digit = sc - 29
            if digit:
                self.teacher_jump(digit)
                return True
            if ev.key == pygame.K_v or sc == 25:
                self.teacher_jump("V")
                return True
        if ev.key == pygame.K_ESCAPE:
            if self.overlay is not None:
                self.overlay.on_escape()
            elif self.scene.in_game:
                self.open_pause()
            return True
        return False

    def update(self, dt):
        if self.overlay is not None:
            self.overlay.update(dt)
        else:
            self.scene.update(dt)
            if self.scene.in_game:
                self.state.elapsed += dt
                self._check_timer()
        self.fade = max(0.0, self.fade - dt / 0.35)

    def _check_timer(self):
        minutes = self.options.timer_minutes
        if minutes and not self.state.timer_expired_ack and self.state.elapsed >= minutes * 60:
            from .scenes.pausa import TimerOverlay
            self.scene.on_pause()
            self.overlay = TimerOverlay(self)

    def render(self):
        self.scene.draw(self.canvas)
        if self.overlay is not None:
            self.overlay.draw(self.canvas)
        if self.fade > 0:
            veil = pygame.Surface((C.WIDTH, C.HEIGHT))
            veil.set_alpha(int(255 * self.fade))
            self.canvas.blit(veil, (0, 0))
        win = pygame.display.get_surface()
        scale, ox, oy, sw, sh = self._view()
        if (sw, sh) == (C.WIDTH, C.HEIGHT):
            win.blit(self.canvas, (ox, oy))
        else:
            if self._scaled is None or self._scaled.get_size() != (sw, sh):
                self._scaled = pygame.Surface((sw, sh), 0, self.canvas)
            try:
                pygame.transform.smoothscale(self.canvas, (sw, sh), self._scaled)
            except (ValueError, pygame.error):
                pygame.transform.scale(self.canvas, (sw, sh), self._scaled)
            win.blit(self._scaled, (ox, oy))
        ww, wh = win.get_size()
        if ox > 0:
            win.fill((0, 0, 0), (0, 0, ox, wh))
            win.fill((0, 0, 0), (ox + sw, 0, ww - ox - sw, wh))
        if oy > 0:
            win.fill((0, 0, 0), (0, 0, ww, oy))
            win.fill((0, 0, 0), (0, oy + sh, ww, wh - oy - sh))
        pygame.display.flip()

    # ------------------------------------------------------------ scene
    def change_scene(self, scene):
        if self.scene is not None:
            try:
                self.scene.exit()
            except Exception:
                log.exception("Errore uscendo dalla scena")
        self.overlay = None
        self.tts.stop()
        self.scene = scene
        self.fade = 1.0
        scene.enter()
        self.audio.set_ambient(scene.ambient)

    def go_menu(self):
        from .scenes.menu import MenuScene
        self.change_scene(MenuScene(self))

    def go_options(self):
        from .scenes.opzioni import OptionsScene
        self.change_scene(OptionsScene(self))

    def go_team(self):
        from .scenes.menu import TeamScene
        self.change_scene(TeamScene(self))

    def new_game(self, team_name=""):
        from .scenes.intro import IntroScene
        save.delete_game()
        self.state = GameState(team_name=team_name)
        self.change_scene(IntroScene(self))

    def continue_game(self):
        st = save.load_game()
        if st is None:
            self.go_menu()
            return
        self.state = st
        self.go_map(st.last_completed + 1)

    def go_map(self, next_stage):
        from .scenes.mappa import MapScene
        self.change_scene(MapScene(self, next_stage))

    def go_stage(self, n):
        from .scenes import make_stage
        for item in self.state.items_before(n):
            self.state.add_item(item)
        self.state.stage = n
        self.change_scene(make_stage(self, n))

    def go_victory(self):
        from .scenes.vittoria import VictoryScene
        save.delete_game()
        self.change_scene(VictoryScene(self))

    def teacher_jump(self, target):
        log.info("Scorciatoia maestra: %s", target)
        if target == "V":
            self.state.prepare_stage(6)
            self.state.last_completed = 6
            self.state.add_item("rosa")
            self.go_victory()
        else:
            self.state.prepare_stage(int(target))
            self.go_stage(int(target))

    def restart_current(self):
        new = self.scene.restart()
        if new is not None:
            self.change_scene(new)
        else:
            self.overlay = None

    def open_pause(self):
        if self.overlay is None and self.scene.in_game:
            from .scenes.pausa import PauseOverlay
            self.scene.on_pause()
            self.tts.stop()
            self.overlay = PauseOverlay(self)

    def close_overlay(self):
        self.overlay = None

    def quit(self):
        self.running = False

    def speak(self, text):
        if self.options.tts and text:
            self.tts.say(text)

    # ------------------------------------------------------------ opzioni
    def apply_options(self):
        fonts.set_uppercase(self.options.uppercase)
        self.audio.set_enabled(self.options.sound)
        if self.options.tts:
            self.tts.enable()
        else:
            self.tts.disable()
        save.save_options(self.options)

    # ------------------------------------------------------------ errori
    def on_crash(self):
        log.exception("Errore imprevisto durante il gioco")
        from .scenes.errore import ErrorScene
        now = time.time()
        self.crashes = [t for t in self.crashes if now - t < 15] + [now]
        if len(self.crashes) >= 3 or isinstance(self.scene, ErrorScene):
            self.fatal_message = ("Il gioco ha avuto un problema e deve chiudersi.\n"
                                  f"I dettagli sono nel file:\n{save.log_path()}")
            self.running = False
            return
        try:
            self.overlay = None
            self.change_scene(ErrorScene(self))
        except Exception:
            log.exception("Impossibile mostrare la schermata di errore")
            self.fatal_message = f"Il gioco ha avuto un problema.\nDettagli in: {save.log_path()}"
            self.running = False

    def shutdown(self):
        try:
            self.tts.shutdown()
        except Exception:
            pass
        pygame.quit()
