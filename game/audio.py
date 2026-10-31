"""Effetti sonori generati via codice (modulo standard array, niente numpy).

Se l'audio non si inizializza il gioco continua in silenzio.
I campioni vengono calcolati in un thread, così l'avvio non si blocca.
"""

import array
import logging
import math
import random
import threading

import pygame

log = logging.getLogger("fuga")

RATE = 22050
TWO_PI = 2.0 * math.pi

# Note (Hz)
C5, D5, E5, F5, G5, A5, B5 = 523.25, 587.33, 659.25, 698.46, 783.99, 880.00, 987.77
C6, E6, G6 = 1046.50, 1318.51, 1567.98
G4, A4, B4, E4, C4 = 392.00, 440.00, 493.88, 329.63, 261.63


def _tone(freq, dur, vol=0.5, rate=RATE, attack=0.008, release=0.12, harmonics=(1.0, 0.3, 0.12),
          slide=0.0, vibrato=0.0):
    n = int(dur * rate)
    out = [0.0] * n
    a_n = max(1, int(attack * rate))
    r_n = max(1, int(release * rate))
    norm = sum(harmonics)
    phase = 0.0
    for i in range(n):
        t = i / rate
        f = freq * (1.0 + slide * (i / n))
        if vibrato:
            f *= 1.0 + 0.012 * math.sin(TWO_PI * vibrato * t)
        phase += TWO_PI * f / rate
        s = 0.0
        for h, amp in enumerate(harmonics, start=1):
            s += amp * math.sin(phase * h)
        env = 1.0
        if i < a_n:
            env = i / a_n
        elif i > n - r_n:
            env = max(0.0, (n - i) / r_n)
        out[i] = vol * env * s / norm
    return out


def _silence(dur, rate=RATE):
    return [0.0] * int(dur * rate)


def _concat(*parts):
    out = []
    for p in parts:
        out.extend(p)
    return out


def _mix(base, other, offset_s, rate=RATE):
    start = int(offset_s * rate)
    need = start + len(other)
    if need > len(base):
        base.extend([0.0] * (need - len(base)))
    for i, v in enumerate(other):
        base[start + i] += v
    return base


def make_correct(rate=RATE):
    notes = [(C5, 0.09), (E5, 0.09), (G5, 0.09), (C6, 0.26)]
    out = []
    t = 0.0
    for f, d in notes:
        _mix(out, _tone(f, d + 0.06, 0.42, rate, release=0.08), t, rate)
        t += d
    return out


def make_wrong(rate=RATE):
    # Due note morbide che scendono: non punitivo.
    a = _tone(G4, 0.16, 0.30, rate, attack=0.02, release=0.1, harmonics=(1.0, 0.15))
    b = _tone(E4, 0.26, 0.28, rate, attack=0.02, release=0.18, harmonics=(1.0, 0.15))
    return _concat(a, _silence(0.03, rate), b)


def make_click(rate=RATE):
    return _tone(880, 0.05, 0.22, rate, attack=0.002, release=0.04, harmonics=(1.0, 0.2))


def make_pop(rate=RATE):
    return _tone(600, 0.12, 0.30, rate, attack=0.004, release=0.09, slide=0.9, harmonics=(1.0, 0.25))


def make_whoosh(rate=RATE):
    out = []
    rnd = random.Random(7)
    n = int(0.45 * rate)
    lp = 0.0
    for i in range(n):
        x = i / n
        cut = 0.05 + 0.5 * x
        lp += cut * (rnd.uniform(-1, 1) - lp)
        env = math.sin(math.pi * x) ** 2
        out.append(0.5 * env * lp)
    return _mix(out, _tone(500, 0.45, 0.12, rate, slide=1.2, attack=0.1, release=0.2), 0.0, rate)


def make_victory(rate=RATE):
    melody = [(C5, 0.15), (E5, 0.15), (G5, 0.15), (C6, 0.3), (G5, 0.15), (C6, 0.6)]
    out = []
    t = 0.0
    for f, d in melody:
        _mix(out, _tone(f, d + 0.1, 0.36, rate, release=0.12, vibrato=5.0), t, rate)
        _mix(out, _tone(f / 2, d + 0.1, 0.16, rate, release=0.12), t, rate)
        t += d
    for f in (C5, E5, G5, C6):
        _mix(out, _tone(f, 1.0, 0.14, rate, attack=0.05, release=0.6), t, rate)
    return out


def make_bump(rate=RATE):
    return _tone(180, 0.18, 0.40, rate, attack=0.004, release=0.14, slide=-0.4, harmonics=(1.0, 0.4, 0.1))


def make_step(rate=RATE):
    return _tone(330, 0.07, 0.20, rate, attack=0.003, release=0.05, harmonics=(1.0, 0.1))


def make_waves(rate=RATE, seconds=6.0):
    """Rumore filtrato con un'onda lenta: sciabordio leggero, ripetibile senza scatti."""
    rnd = random.Random(3)
    n = int(seconds * rate)
    out = [0.0] * n
    lp1 = lp2 = 0.0
    for i in range(n):
        x = i / n
        swell = 0.55 + 0.45 * math.sin(TWO_PI * 2 * x - math.pi / 2)  # 2 onde per ciclo
        lp1 += 0.08 * (rnd.uniform(-1, 1) - lp1)
        lp2 += 0.08 * (lp1 - lp2)
        out[i] = 0.9 * swell * lp2
    fade = int(0.25 * rate)
    for i in range(fade):  # raccordo morbido per il loop
        k = i / fade
        out[i] *= k
        out[n - 1 - i] *= k
    return out


GENERATORS = {
    "correct": make_correct,
    "wrong": make_wrong,
    "click": make_click,
    "pop": make_pop,
    "whoosh": make_whoosh,
    "victory": make_victory,
    "bump": make_bump,
    "step": make_step,
    "waves": make_waves,
}


def to_bytes(samples, size, channels):
    """Converte campioni float (-1..1) nel formato del mixer."""
    if size in (-16, 16):
        top = 32767 if size < 0 else 65535
        if size < 0:
            data = array.array("h", (int(max(-1.0, min(1.0, s)) * top) for s in samples))
        else:
            data = array.array("H", (int((max(-1.0, min(1.0, s)) + 1.0) * 0.5 * top) for s in samples))
    elif size in (-8, 8):
        if size < 0:
            data = array.array("b", (int(max(-1.0, min(1.0, s)) * 127) for s in samples))
        else:
            data = array.array("B", (int((max(-1.0, min(1.0, s)) + 1.0) * 127.5) for s in samples))
    elif size == 32:
        data = array.array("f", (max(-1.0, min(1.0, s)) for s in samples))
    elif size == -32:
        data = array.array("i", (int(max(-1.0, min(1.0, s)) * 2147483647) for s in samples))
    else:
        raise ValueError(f"formato audio non gestito: {size}")
    if channels > 1:
        multi = array.array(data.typecode)
        for v in data:
            multi.extend([v] * channels)
        data = multi
    return data.tobytes()


class Audio:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.ok = False
        self.sounds = {}
        self._raw = None
        self._ambient_name = None
        self._ambient_channel = None
        self._fmt = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(RATE, -16, 1, 512)
            init = pygame.mixer.get_init()
            if not init:
                raise RuntimeError("mixer non inizializzato")
            freq, size, channels = init
            self._fmt = (freq, size, channels)
            pygame.mixer.set_num_channels(12)
            pygame.mixer.set_reserved(1)
            self._ambient_channel = pygame.mixer.Channel(0)
            self.ok = True
        except Exception as exc:  # audio assente: si gioca in silenzio
            log.info("Audio non disponibile: %s", exc)
            self.ok = False
            return
        threading.Thread(target=self._build, name="audio-build", daemon=True).start()

    def _build(self):
        freq, size, channels = self._fmt
        raw = {}
        for name, gen in GENERATORS.items():
            try:
                raw[name] = to_bytes(gen(freq), size, channels)
            except Exception as exc:
                log.warning("Suono %s non generato: %s", name, exc)
        self._raw = raw

    def wait_ready(self, timeout=10.0):
        """Solo per i test: aspetta che i suoni siano pronti."""
        import time
        end = time.time() + timeout
        while self.ok and self._raw is None and time.time() < end:
            time.sleep(0.02)
        self.update()

    def update(self):
        if self._raw is not None:
            raw, self._raw = self._raw, None
            for name, data in raw.items():
                try:
                    self.sounds[name] = pygame.mixer.Sound(buffer=data)
                except Exception as exc:
                    log.warning("Suono %s non caricato: %s", name, exc)
            if "waves" in self.sounds:
                self.sounds["waves"].set_volume(0.16)
            if self._ambient_name:
                self.set_ambient(self._ambient_name, force=True)

    def play(self, name, volume=1.0):
        if not (self.ok and self.enabled):
            return
        snd = self.sounds.get(name)
        if snd is None:
            return
        try:
            ch = snd.play()
            if ch is not None:
                ch.set_volume(volume)
        except Exception:
            pass

    def set_enabled(self, enabled):
        self.enabled = enabled
        if not self.ok:
            return
        if not enabled:
            try:
                pygame.mixer.stop()
            except Exception:
                pass
        else:
            self.set_ambient(self._ambient_name, force=True)

    def set_ambient(self, name, force=False):
        """Suono di sottofondo in loop (per ora solo le onde) oppure None."""
        if name == self._ambient_name and not force:
            return
        self._ambient_name = name
        if not self.ok or self._ambient_channel is None:
            return
        try:
            if not self.enabled or name is None or name not in self.sounds:
                self._ambient_channel.fadeout(400)
                return
            self._ambient_channel.play(self.sounds[name], loops=-1, fade_ms=800)
        except Exception:
            pass
