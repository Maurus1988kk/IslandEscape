"""Modello semplice del sole e dell'ombra di un bastone (tappa 3).

t va da 0 (alba) a 1 (tramonto). Gli azimut sono in gradi, misurati in senso
orario dal Nord: 0 = Nord, 90 = Est, 180 = Sud, 270 = Ovest.
È il modello dell'equinozio: il sole sorge esattamente a Est e tramonta a Ovest.
"""

import math

NOON = 0.5
NOON_TOLERANCE = 0.06
STICK_HEIGHT = 120.0     # "altezza" del bastone in pixel: lunghezza ombra = h / tan(elev)
MAX_SHADOW = 235.0       # limite per non uscire dallo schermo


def clamp01(t):
    return max(0.0, min(1.0, float(t)))


def sun_azimuth(t):
    return 90.0 + 180.0 * clamp01(t)


def sun_elevation(t):
    return 5.0 + 60.0 * math.sin(math.pi * clamp01(t))


def shadow_azimuth(t):
    return (sun_azimuth(t) + 180.0) % 360.0


def shadow_length(t, stick_height=STICK_HEIGHT, max_len=MAX_SHADOW):
    elev = math.radians(sun_elevation(t))
    return min(max_len, stick_height / math.tan(elev))


def azimuth_to_vector(azimuth_deg):
    """Vettore unitario sullo schermo con il Nord in alto (y cresce verso il basso)."""
    a = math.radians(azimuth_deg)
    return (math.sin(a), -math.cos(a))


def shadow_vector(t, stick_height=STICK_HEIGHT, max_len=MAX_SHADOW):
    dx, dy = azimuth_to_vector(shadow_azimuth(t))
    length = shadow_length(t, stick_height, max_len)
    return (dx * length, dy * length)


def azimuth_to_dir(azimuth_deg):
    """Punto cardinale più vicino (N, E, S, O)."""
    idx = int(((azimuth_deg % 360.0) + 45.0) // 90.0) % 4
    return ("N", "E", "S", "O")[idx]


def is_noon(t, tol=NOON_TOLERANCE):
    return abs(clamp01(t) - NOON) <= tol


def time_label(t):
    t = clamp01(t)
    if t < 0.08:
        return "Alba"
    if t < 0.42:
        return "Mattina"
    if t <= 0.58:
        return "Mezzogiorno"
    if t <= 0.92:
        return "Pomeriggio"
    return "Tramonto"
