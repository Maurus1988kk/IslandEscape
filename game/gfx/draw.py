"""Funzioni di disegno: tutto è fatto con primitive pygame (niente immagini esterne)."""

import math
import random

import pygame
from pygame import gfxdraw

from .. import config as C

_cache = {}
_rect_cache = {}
_CACHE_MAX = 400
_RECT_CACHE_MAX = 300


def clear_caches():
    _cache.clear()
    _rect_cache.clear()


def _cache_put(store, key, value, limit):
    """Cache semplice: se diventa troppo grande la svuota (evita di consumare memoria)."""
    if len(store) >= limit:
        store.clear()
    store[key] = value
    return value


# ================================================================ utilità
def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    t = clamp(t, 0.0, 1.0)
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


def shade(color, factor):
    """factor < 1 scurisce, > 1 schiarisce."""
    if factor >= 1:
        return tuple(int(c + (255 - c) * (factor - 1)) for c in color[:3])
    return tuple(int(c * factor) for c in color[:3])


def with_alpha(color, alpha):
    return (color[0], color[1], color[2], int(clamp(alpha, 0, 255)))


def ease_out_back(t, s=1.70158):
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


def ease_out(t):
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    return 3 * t * t - 2 * t * t * t


def rot_point(p, center, ang_rad):
    x, y = p[0] - center[0], p[1] - center[1]
    c, s = math.cos(ang_rad), math.sin(ang_rad)
    return (center[0] + x * c - y * s, center[1] + x * s + y * c)


def _ipts(points):
    return [(int(x + 0.5), int(y + 0.5)) for x, y in points]


def aa_polygon(surf, color, points):
    if len(points) < 3:
        return
    pts = _ipts(points)
    gfxdraw.filled_polygon(surf, pts, color)
    gfxdraw.aapolygon(surf, pts, color)


def aa_circle(surf, color, center, r):
    r = int(round(r))
    if r < 1:
        return
    x, y = int(round(center[0])), int(round(center[1]))
    gfxdraw.filled_circle(surf, x, y, r, color)
    gfxdraw.aacircle(surf, x, y, r, color)


def aa_ring(surf, color, center, r, width):
    r = int(r + 0.5)
    w = max(1, int(width + 0.5))
    if r < 1:
        return
    x, y = int(center[0] + 0.5), int(center[1] + 0.5)
    if len(color) > 3 and color[3] < 255:
        for k in range(w):
            gfxdraw.circle(surf, x, y, r - k, color)
        return
    pygame.draw.circle(surf, color, (x, y), r, min(w, r))
    gfxdraw.aacircle(surf, x, y, r, color)
    if r - w > 0:
        gfxdraw.aacircle(surf, x, y, r - w, color)


def circle_points(center, r, n=32, start=0.0):
    return [(center[0] + r * math.cos(start + 2 * math.pi * i / n),
             center[1] + r * math.sin(start + 2 * math.pi * i / n)) for i in range(n)]


def ellipse_points(center, rx, ry, n=36, rot=0.0):
    pts = []
    c, s = math.cos(rot), math.sin(rot)
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        pts.append((center[0] + x * c - y * s, center[1] + x * s + y * c))
    return pts


def aa_ellipse(surf, color, center, rx, ry, rot=0.0, n=36):
    aa_polygon(surf, color, ellipse_points(center, rx, ry, n, rot))


def thick_line(surf, color, a, b, width):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    if length < 0.5:
        aa_circle(surf, color, a, width / 2)
        return
    nx, ny = -dy / length * width / 2, dx / length * width / 2
    aa_polygon(surf, color, [(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny),
                             (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)])
    aa_circle(surf, color, a, width / 2 - 0.5)
    aa_circle(surf, color, b, width / 2 - 0.5)


def polyline(surf, color, points, width):
    for a, b in zip(points, points[1:]):
        thick_line(surf, color, a, b, width)


def dashed_line(surf, color, a, b, width=4, dash=14, gap=10, offset=0.0):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    if length < 1:
        return
    ux, uy = dx / length, dy / length
    pos = -(offset % (dash + gap))
    w = max(1, int(width + 0.5))
    while pos < length:
        s = max(0.0, pos)
        e = min(length, pos + dash)
        if e > s:
            pygame.draw.line(surf, color, (int(a[0] + ux * s), int(a[1] + uy * s)),
                             (int(a[0] + ux * e), int(a[1] + uy * e)), w)
        pos += dash + gap


def arrow(surf, color, start, end, width=8, head=26):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    if length < 1:
        return
    ux, uy = dx / length, dy / length
    base = (end[0] - ux * head, end[1] - uy * head)
    thick_line(surf, color, start, base, width)
    nx, ny = -uy, ux
    aa_polygon(surf, color, [end, (base[0] + nx * head * 0.6, base[1] + ny * head * 0.6),
                             (base[0] - nx * head * 0.6, base[1] - ny * head * 0.6)])


def rounded_rect(surf, color, rect, radius=16, width=0):
    pygame.draw.rect(surf, color, rect, width, border_radius=int(radius))


def alpha_rect(surf, rect, color, radius=16):
    rect = pygame.Rect(rect)
    if rect.w <= 0 or rect.h <= 0:
        return
    key = (rect.size, tuple(color), int(radius))
    s = _rect_cache.get(key)
    if s is None:
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(s, color, s.get_rect(), border_radius=int(radius))
        _cache_put(_rect_cache, key, s, _RECT_CACHE_MAX)
    surf.blit(s, rect.topleft)


def panel(surf, rect, color=C.PANEL_BG, radius=22, border=None, shadow=True):
    rect = pygame.Rect(rect)
    if shadow:
        alpha_rect(surf, rect.move(0, 6), (0, 0, 0, 70), radius)
    rounded_rect(surf, color, rect, radius)
    if border:
        rounded_rect(surf, border, rect, radius, 4)


def vgradient(size, top, bottom):
    """Sfumatura verticale memorizzata (da usare solo con colori fissi)."""
    key = ("vgrad", tuple(size), tuple(top), tuple(bottom))
    s = _cache.get(key)
    if s is None:
        w, h = int(size[0]), int(size[1])
        s = pygame.Surface((w, h))
        if pygame.display.get_init() and pygame.display.get_surface() is not None:
            s = s.convert()
        for y in range(h):
            pygame.draw.line(s, lerp_color(top, bottom, y / max(1, h - 1)), (0, y), (w, y))
        _cache_put(_cache, key, s, _CACHE_MAX)
    return s


def vgradient_live(surf, rect, top, bottom, step=4):
    """Sfumatura disegnata al volo: per colori che cambiano a ogni fotogramma."""
    rect = pygame.Rect(rect)
    for y in range(0, rect.h, step):
        col = lerp_color(top, bottom, y / max(1, rect.h - 1))
        surf.fill(col, (rect.x, rect.y + y, rect.w, min(step, rect.h - y)))


def glow(radius, color, strength=1.0):
    """Alone luminoso: colore che sfuma verso il nero, da sommare (BLEND_RGB_ADD)."""
    r = max(2, int(radius) // 4 * 4)
    strength = round(max(0.0, min(1.0, strength)) * 20) / 20
    key = ("glow", r, tuple(color[:3]), strength)
    s = _cache.get(key)
    if s is None:
        s = pygame.Surface((2 * r, 2 * r))
        s.fill((0, 0, 0))
        for i in range(r, 0, -1):
            f = strength * (1 - i / r) ** 2
            pygame.draw.circle(s, tuple(min(255, int(ch * f)) for ch in color[:3]), (r, r), i)
        _cache_put(_cache, key, s, _CACHE_MAX)
    return s


def blit_glow(surf, center, radius, color, strength=1.0):
    if strength <= 0.02:
        return
    g = glow(radius, color, strength)
    r = g.get_width() // 2
    surf.blit(g, (int(center[0] - r), int(center[1] - r)), special_flags=pygame.BLEND_RGB_ADD)


def star_points(center, r_out, r_in, n=5, rot=-math.pi / 2):
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        a = rot + math.pi * i / n
        pts.append((center[0] + r * math.cos(a), center[1] + r * math.sin(a)))
    return pts


def draw_star(surf, center, r, color=(255, 236, 120), outline=None):
    if outline:
        aa_polygon(surf, outline, star_points(center, r + 3, r * 0.45 + 2))
    aa_polygon(surf, color, star_points(center, r, r * 0.45))


# ================================================================ icone
def icon_check(surf, center, size, color=C.WHITE, width=None):
    w = width or max(4, int(size * 0.18))
    cx, cy = center
    pts = [(cx - size * 0.42, cy + size * 0.02), (cx - size * 0.12, cy + size * 0.32),
           (cx + size * 0.45, cy - size * 0.3)]
    polyline(surf, color, pts, w)


def icon_cross(surf, center, size, color=C.WHITE, width=None):
    w = width or max(4, int(size * 0.18))
    cx, cy = center
    d = size * 0.34
    thick_line(surf, color, (cx - d, cy - d), (cx + d, cy + d), w)
    thick_line(surf, color, (cx - d, cy + d), (cx + d, cy - d), w)


def badge(surf, center, r, ok=True):
    """Cerchio con spunta (giusto) o croce (sbagliato): forma + colore, per i daltonici."""
    aa_circle(surf, shade(C.OK_GREEN if ok else C.KO_ORANGE, 0.75), (center[0], center[1] + 3), r)
    aa_circle(surf, C.OK_GREEN if ok else C.KO_ORANGE, center, r)
    aa_circle(surf, C.WHITE, center, r * 0.86)
    aa_circle(surf, C.OK_GREEN if ok else C.KO_ORANGE, center, r * 0.76)
    if ok:
        icon_check(surf, center, r * 1.1, C.WHITE)
    else:
        icon_cross(surf, center, r * 1.05, C.WHITE)


def icon_pause(surf, center, size, color=C.WHITE):
    cx, cy = center
    w, h = size * 0.22, size * 0.7
    for dx in (-size * 0.2, size * 0.2):
        pygame.draw.rect(surf, color, (int(cx + dx - w / 2), int(cy - h / 2), int(w), int(h)), border_radius=4)


def icon_arrow_dir(surf, center, size, color=C.WHITE, direction="N"):
    ang = {"N": -90, "E": 0, "S": 90, "O": 180}[direction]
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    tip = (center[0] + ux * size * 0.5, center[1] + uy * size * 0.5)
    tail = (center[0] - ux * size * 0.45, center[1] - uy * size * 0.45)
    arrow(surf, color, tail, tip, width=max(5, size * 0.2), head=size * 0.5)


def icon_play(surf, center, size, color=C.WHITE):
    cx, cy = center
    aa_polygon(surf, color, [(cx - size * 0.3, cy - size * 0.4), (cx + size * 0.42, cy),
                             (cx - size * 0.3, cy + size * 0.4)])


def icon_bulb(surf, center, size, color=(255, 236, 110)):
    cx, cy = center
    aa_circle(surf, (120, 90, 20), (cx, cy - size * 0.1), size * 0.36)
    aa_circle(surf, color, (cx, cy - size * 0.1), size * 0.31)
    aa_circle(surf, (255, 252, 220), (cx - size * 0.1, cy - size * 0.2), size * 0.09)
    pygame.draw.rect(surf, (90, 90, 100), (int(cx - size * 0.15), int(cy + size * 0.2),
                                           int(size * 0.3), int(size * 0.22)), border_radius=3)
    for i in range(2):
        y = int(cy + size * 0.26 + i * size * 0.09)
        pygame.draw.line(surf, (160, 160, 170), (int(cx - size * 0.15), y), (int(cx + size * 0.15), y), 2)


def icon_clock(surf, center, r, color=C.WHITE, frac=0.0):
    aa_circle(surf, color, center, r)
    aa_circle(surf, (40, 60, 90), center, r - 3)
    a = -math.pi / 2 + 2 * math.pi * frac
    thick_line(surf, color, center, (center[0] + math.cos(a) * r * 0.7, center[1] + math.sin(a) * r * 0.7), 3)
    thick_line(surf, color, center, (center[0], center[1] - r * 0.5), 3)


def icon_restart(surf, center, size, color=C.WHITE):
    cx, cy = center
    r = size * 0.36
    pts = [(cx + r * math.cos(a), cy + r * math.sin(a))
           for a in [math.radians(d) for d in range(-60, 230, 15)]]
    polyline(surf, color, pts, max(4, size * 0.13))
    end = pts[0]
    aa_polygon(surf, color, [(end[0] + size * 0.2, end[1] - size * 0.06), (end[0] - size * 0.14, end[1] - size * 0.22),
                             (end[0] - size * 0.04, end[1] + size * 0.16)])


def icon_home(surf, center, size, color=C.WHITE):
    cx, cy = center
    aa_polygon(surf, color, [(cx - size * 0.45, cy), (cx, cy - size * 0.42), (cx + size * 0.45, cy)])
    pygame.draw.rect(surf, color, (int(cx - size * 0.3), int(cy - 2), int(size * 0.6), int(size * 0.4)))


def icon_exit(surf, center, size, color=C.WHITE):
    cx, cy = center
    pygame.draw.rect(surf, color, (int(cx - size * 0.4), int(cy - size * 0.4), int(size * 0.45), int(size * 0.8)), 4)
    arrow(surf, color, (cx - size * 0.1, cy), (cx + size * 0.45, cy), width=6, head=size * 0.3)


def icon_gear(surf, center, size, color=C.WHITE):
    cx, cy = center
    pts = []
    for i in range(16):
        r = size * (0.45 if i % 2 == 0 else 0.34)
        a = 2 * math.pi * i / 16
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    aa_polygon(surf, color, pts)
    aa_circle(surf, (60, 60, 80), center, size * 0.15)


ICONS = {
    "check": icon_check, "cross": icon_cross, "pause": icon_pause, "play": icon_play,
    "bulb": icon_bulb, "restart": icon_restart, "home": icon_home, "exit": icon_exit,
    "gear": icon_gear,
}


def draw_icon(surf, name, center, size, color=C.WHITE):
    if name in ("N", "E", "S", "O"):
        icon_arrow_dir(surf, center, size, color, name)
    elif name == "bulb":
        icon_bulb(surf, center, size)
    elif name in ICONS:
        ICONS[name](surf, center, size, color)


# ================================================================ paesaggio
def draw_sky(surf, rect, top=C.SKY_TOP, bottom=C.SKY_BOTTOM):
    rect = pygame.Rect(rect)
    surf.blit(vgradient(rect.size, top, bottom), rect.topleft)


def draw_sea(surf, rect, t, top=C.SEA_LIGHT, bottom=C.SEA_DEEP, wave=C.FOAM, rows=6, speed=18, amp=5):
    rect = pygame.Rect(rect)
    surf.blit(vgradient(rect.size, top, bottom), rect.topleft)
    spacing = 110
    for k in range(rows):
        y = rect.y + (k + 0.6) * rect.h / rows
        shift = (t * speed * (1 if k % 2 else -1) + k * 47) % spacing
        x = rect.x - spacing + shift
        col = lerp_color(wave, top if k < rows / 2 else bottom, 0.35)
        while x < rect.right + spacing:
            pts = [(int(x + i * 6), int(y + amp * math.sin(i * 0.55 + t * 2 + k))) for i in range(7)]
            if rect.collidepoint(pts[0]) or rect.collidepoint(pts[-1]):
                pygame.draw.lines(surf, col, False, pts, 3)
            x += spacing


def draw_cloud(surf, center, scale=1.0, color=(255, 255, 255)):
    cx, cy = center
    for dx, dy, r in ((-40, 8, 26), (-12, -6, 34), (24, 0, 30), (50, 10, 22), (6, 14, 30)):
        aa_circle(surf, color, (cx + dx * scale, cy + dy * scale), r * scale)


def draw_sun(surf, center, r, t=0.0, color=(255, 214, 64), rays=True, ray_color=None):
    cx, cy = center
    if rays:
        rc = ray_color or (255, 236, 140)
        for i in range(12):
            a = t * 0.4 + i * math.pi / 6
            p1 = (cx + math.cos(a) * r * 1.2, cy + math.sin(a) * r * 1.2)
            p2 = (cx + math.cos(a) * r * 1.55, cy + math.sin(a) * r * 1.55)
            thick_line(surf, rc, p1, p2, max(3, r * 0.12))
    blit_glow(surf, center, r * 2.0, (120, 90, 10), 0.6)
    aa_circle(surf, shade(color, 0.92), center, r)
    aa_circle(surf, color, (cx - r * 0.06, cy - r * 0.06), r * 0.9)
    aa_circle(surf, shade(color, 1.25), (cx - r * 0.3, cy - r * 0.3), r * 0.25)


def island_points(center, rx, ry, seed=1, n=40, wobble=0.12):
    rnd = random.Random(seed)
    phases = [rnd.uniform(0, 6.28) for _ in range(3)]
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        f = 1 + wobble * (math.sin(3 * a + phases[0]) + 0.6 * math.sin(5 * a + phases[1])
                          + 0.4 * math.sin(7 * a + phases[2])) / 2
        pts.append((center[0] + rx * f * math.cos(a), center[1] + ry * f * math.sin(a)))
    return pts


def draw_island(surf, center, rx, ry, seed=1, sand=C.SAND, grass=C.GRASS):
    pts_foam = island_points(center, rx * 1.06, ry * 1.08, seed)
    aa_polygon(surf, lerp_color(C.FOAM, C.SEA_LIGHT, 0.4), pts_foam)
    aa_polygon(surf, sand, island_points(center, rx, ry, seed))
    aa_polygon(surf, grass, island_points(center, rx * 0.78, ry * 0.72, seed + 4))
    aa_polygon(surf, shade(grass, 0.9), island_points((center[0] + rx * 0.08, center[1] - ry * 0.05),
                                                      rx * 0.42, ry * 0.36, seed + 9))


def draw_palm(surf, base, height=150, t=0.0, lean=0.18, trunk=(140, 96, 52), leaf=(46, 150, 64),
              silhouette=None):
    bx, by = base
    sway = math.sin(t * 1.3 + bx * 0.01) * 0.03
    top = (bx + height * (lean + sway), by - height)
    segs = 7
    tc = silhouette or trunk
    for i in range(segs):
        f0, f1 = i / segs, (i + 1) / segs
        p0 = (lerp(bx, top[0], f0 ** 1.4), lerp(by, top[1], f0))
        p1 = (lerp(bx, top[0], f1 ** 1.4), lerp(by, top[1], f1))
        w = lerp(height * 0.11, height * 0.06, f0)
        thick_line(surf, tc if silhouette else (shade(tc, 0.85) if i % 2 else tc), p0, p1, w)
    lc = silhouette or leaf
    for k in range(6):
        a = math.radians(-170 + k * 34) + sway * 4
        length = height * (0.55 if k in (0, 5) else 0.62)
        tip = (top[0] + math.cos(a) * length, top[1] + math.sin(a) * length * 0.7 + length * 0.18)
        mid = (top[0] + math.cos(a) * length * 0.5, top[1] + math.sin(a) * length * 0.35 - length * 0.08)
        nx, ny = -(mid[1] - top[1]), mid[0] - top[0]
        nl = math.hypot(nx, ny) or 1
        nx, ny = nx / nl * height * 0.08, ny / nl * height * 0.08
        aa_polygon(surf, lc if silhouette else (shade(lc, 0.85) if k % 2 else lc),
                   [top, (mid[0] + nx, mid[1] + ny), tip, (mid[0] - nx, mid[1] - ny)])
    if not silhouette:
        for dx in (-6, 6, 0):
            aa_circle(surf, (110, 70, 30), (top[0] + dx * height / 150, top[1] + 6 * height / 150), height * 0.045)


def draw_palm_top(surf, center, r, t=0.0, leaf=(46, 150, 64)):
    """Palma vista dall'alto: una stella di foglie."""
    cx, cy = center
    for k in range(7):
        a = k * 2 * math.pi / 7 + 0.05 * math.sin(t + k)
        tip = (cx + math.cos(a) * r, cy + math.sin(a) * r)
        side = a + math.pi / 2
        w = r * 0.22
        mid = (cx + math.cos(a) * r * 0.5, cy + math.sin(a) * r * 0.5)
        aa_polygon(surf, shade(leaf, 0.85) if k % 2 else leaf,
                   [center, (mid[0] + math.cos(side) * w, mid[1] + math.sin(side) * w), tip,
                    (mid[0] - math.cos(side) * w, mid[1] - math.sin(side) * w)])
    aa_circle(surf, (120, 80, 36), center, r * 0.16)


def draw_tree_top(surf, center, r, color=(52, 140, 66)):
    aa_circle(surf, shade(color, 0.7), (center[0] + 4, center[1] + 5), r)
    aa_circle(surf, color, center, r)
    aa_circle(surf, shade(color, 1.18), (center[0] - r * 0.3, center[1] - r * 0.3), r * 0.45)


def draw_rock(surf, center, r, seed=0, color=C.ROCK):
    rnd = random.Random(seed)
    pts = []
    for i in range(9):
        a = 2 * math.pi * i / 9
        rr = r * rnd.uniform(0.75, 1.05)
        pts.append((center[0] + rr * math.cos(a), center[1] + rr * 0.8 * math.sin(a)))
    aa_polygon(surf, shade(color, 0.7), [(x + 3, y + 4) for x, y in pts])
    aa_polygon(surf, color, pts)
    aa_polygon(surf, shade(color, 1.2), [(center[0] - r * 0.5, center[1] - r * 0.2), (center[0] - r * 0.1, center[1] - r * 0.6),
                                         (center[0] + r * 0.2, center[1] - r * 0.3)])


def draw_whirlpool(surf, center, r, t=0.0):
    cx, cy = center
    aa_circle(surf, (24, 80, 150), center, r)
    for k in range(3):
        pts = []
        for i in range(40):
            f = i / 39
            a = t * 3 + k * 2 * math.pi / 3 + f * 4.5
            rr = r * (1 - f) * 0.95
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
        polyline(surf, (200, 230, 255), pts, 3)


def draw_compass_rose(surf, center, r, labels=True, rot_deg=0.0, label_size=None, letters=("N", "E", "S", "O"),
                      bg=True, letter_color=C.TEXT_DARK, north_color=C.NORTH_RED):
    """Rosa dei venti a 8 punte (disegnata una volta e poi riusata). rot_deg ruota in senso orario."""
    size = label_size or max(18, int(r * 0.42))
    margin = int(r * 1.1 + (size * 1.3 if labels else 0)) + 4
    key = ("rose", round(r, 1), labels, round(rot_deg, 1), size, tuple(letters), bg, letter_color, north_color)
    img = _cache.get(key)
    if img is None:
        img = pygame.Surface((2 * margin, 2 * margin), pygame.SRCALPHA)
        _draw_compass_rose(img, (margin, margin), r, labels, rot_deg, size, letters, bg, letter_color, north_color)
        _cache_put(_cache, key, img, _CACHE_MAX)
    surf.blit(img, (int(center[0] - margin), int(center[1] - margin)))


def _draw_compass_rose(surf, center, r, labels, rot_deg, label_size, letters, bg, letter_color, north_color):
    from ..ui import fonts
    cx, cy = center
    base = math.radians(rot_deg - 90)
    if bg:
        aa_circle(surf, (248, 244, 230), center, r * 1.02)
        aa_ring(surf, (70, 60, 50), center, r * 1.02, 3)
    for i in range(8):
        a = base + i * math.pi / 4
        main = i % 2 == 0
        length = r * (0.92 if main else 0.5)
        w = r * (0.2 if main else 0.12)
        tip = (cx + math.cos(a) * length, cy + math.sin(a) * length)
        left = (cx + math.cos(a - math.pi / 2) * w, cy + math.sin(a - math.pi / 2) * w)
        right = (cx + math.cos(a + math.pi / 2) * w, cy + math.sin(a + math.pi / 2) * w)
        col = north_color if (main and i == 0) else ((60, 70, 100) if main else (150, 150, 170))
        aa_polygon(surf, col, [center, left, tip])
        aa_polygon(surf, shade(col, 1.45), [center, right, tip])
    aa_circle(surf, (240, 200, 60), center, r * 0.1)
    if labels:
        size = label_size or max(18, int(r * 0.42))
        for i, letter in enumerate(letters):
            if not letter:
                continue
            a = base + i * math.pi / 2
            p = (cx + math.cos(a) * (r * 1.02 + size * 0.62), cy + math.sin(a) * (r * 1.02 + size * 0.62))
            fonts.draw_outlined(surf, letter, p, size, north_color if letter == "N" else letter_color,
                                (255, 255, 255), bold=True, width=2)


def draw_broken_canoe(surf, center, scale=1.0, angle=0.0, color=(196, 92, 52)):
    cx, cy = center
    pts = [(-70, -8), (-40, -16), (20, -16), (52, -6), (40, 6), (-10, 14), (-50, 12), (-74, 2)]
    pts = [rot_point((cx + x * scale, cy + y * scale), center, angle) for x, y in pts]
    aa_polygon(surf, shade(color, 0.6), [(x + 3, y + 5) for x, y in pts])
    aa_polygon(surf, color, pts)
    inner = [(-58, -6), (10, -9), (36, -3), (-10, 6), (-56, 5)]
    aa_polygon(surf, shade(color, 0.7), [rot_point((cx + x * scale, cy + y * scale), center, angle) for x, y in inner])
    # bordo spezzato
    crack = [(52, -6), (60, -14), (58, 0), (66, 4), (40, 6)]
    aa_polygon(surf, shade(color, 0.85), [rot_point((cx + x * scale, cy + y * scale), center, angle) for x, y in crack])


def draw_explorer_top(surf, center, scale=1.0, facing_deg=0.0, arms=False, hat=(214, 160, 70), shirt=(40, 120, 210)):
    """Esploratore visto dall'alto. facing_deg: verso dove guarda (0 = alto, senso orario)."""
    cx, cy = center
    a = math.radians(facing_deg)

    def P(x, y):
        return rot_point((cx + x * scale, cy + y * scale), center, a)

    if arms:
        for side in (-1, 1):
            thick_line(surf, (240, 196, 160), P(side * 14, 0), P(side * 46, 0), 9 * scale)
            aa_circle(surf, (240, 196, 160), P(side * 48, 0), 6 * scale)
    else:
        for side in (-1, 1):
            aa_circle(surf, (240, 196, 160), P(side * 20, -6), 6 * scale)
    aa_ellipse(surf, shirt, P(0, 2), 22 * scale, 13 * scale, a)
    aa_circle(surf, shade(hat, 0.75), P(0, 0), 17 * scale)
    aa_circle(surf, hat, P(0, 0), 14 * scale)
    aa_polygon(surf, shade(hat, 0.8), [P(-10, -12), P(10, -12), P(0, -26)])  # visiera = davanti
    aa_circle(surf, shade(hat, 1.2), P(-4, -3), 5 * scale)


def draw_explorer_back(surf, center, scale=1.0, arms=True):
    """Bambino visto da dietro, con le braccia aperte (trucco delle braccia)."""
    cx, cy = center
    skin = (240, 196, 160)
    shirt = (40, 120, 210)
    if arms:
        thick_line(surf, skin, (cx - 20 * scale, cy - 20 * scale), (cx - 88 * scale, cy - 34 * scale), 13 * scale)
        thick_line(surf, skin, (cx + 20 * scale, cy - 20 * scale), (cx + 88 * scale, cy - 34 * scale), 13 * scale)
    thick_line(surf, (60, 70, 110), (cx - 10 * scale, cy + 30 * scale), (cx - 14 * scale, cy + 72 * scale), 14 * scale)
    thick_line(surf, (60, 70, 110), (cx + 10 * scale, cy + 30 * scale), (cx + 14 * scale, cy + 72 * scale), 14 * scale)
    pygame.draw.rect(surf, shirt, (int(cx - 26 * scale), int(cy - 30 * scale), int(52 * scale), int(66 * scale)),
                     border_radius=int(14 * scale))
    aa_circle(surf, (110, 70, 40), (cx, cy - 52 * scale), 22 * scale)  # capelli (da dietro)
    aa_ellipse(surf, (214, 160, 70), (cx, cy - 66 * scale), 34 * scale, 9 * scale)
    aa_circle(surf, (214, 160, 70), (cx, cy - 72 * scale), 16 * scale)


def draw_logs(surf, center, scale=1.0):
    cx, cy = center
    for i, (dx, dy) in enumerate(((-18, 10), (18, 10), (0, -10))):
        x, y = cx + dx * scale, cy + dy * scale
        rect = pygame.Rect(0, 0, int(56 * scale), int(20 * scale))
        rect.center = (int(x), int(y))
        pygame.draw.rect(surf, C.WOOD, rect, border_radius=int(10 * scale))
        pygame.draw.line(surf, C.WOOD_DARK, (rect.x + 8, rect.centery), (rect.right - 14, rect.centery), max(1, int(2 * scale)))
        aa_circle(surf, (214, 168, 110), (rect.right - 6 * scale, rect.centery), 9 * scale)
        aa_ring(surf, C.WOOD_DARK, (rect.right - 6 * scale, rect.centery), 9 * scale, max(1, 2 * scale))
        aa_circle(surf, C.WOOD_DARK, (rect.right - 6 * scale, rect.centery), 2.5 * scale)


def draw_rope(surf, center, scale=1.0):
    cx, cy = center
    for k, r in enumerate((24, 18, 12)):
        aa_ring(surf, shade(C.ROPE, 0.75 if k % 2 else 0.9), (cx, cy), r * scale + 3, 6 * scale)
        aa_ring(surf, C.ROPE, (cx, cy), r * scale, 5 * scale)
    thick_line(surf, C.ROPE, (cx + 22 * scale, cy + 6 * scale), (cx + 34 * scale, cy + 22 * scale), 5 * scale)


def draw_sail(surf, center, scale=1.0, mast=True, cloth=True, rope=True):
    cx, cy = center
    if mast:
        thick_line(surf, C.WOOD_DARK, (cx - 10 * scale, cy + 30 * scale), (cx - 10 * scale, cy - 34 * scale), 6 * scale)
    if cloth:
        pts = [(cx - 6 * scale, cy - 30 * scale), (cx + 26 * scale, cy + 18 * scale), (cx - 6 * scale, cy + 20 * scale)]
        aa_polygon(surf, (200, 194, 180), [(x + 2, y + 2) for x, y in pts])
        aa_polygon(surf, C.SAIL, pts)
        thick_line(surf, (220, 80, 60), (cx - 4 * scale, cy - 4 * scale), (cx + 12 * scale, cy - 2 * scale), 4 * scale)
    if rope:
        thick_line(surf, C.ROPE, (cx - 10 * scale, cy - 32 * scale), (cx + 24 * scale, cy + 26 * scale), 2.5 * scale)


def draw_item(surf, item, center, scale=1.0):
    if item == "rosa":
        draw_compass_rose(surf, center, 24 * scale, labels=False)
    elif item == "corda":
        draw_rope(surf, center, scale)
    elif item == "tronchi":
        draw_logs(surf, center, scale * 0.9)
    elif item == "vela":
        draw_sail(surf, center, scale * 0.95)
    elif item == "stella":
        aa_circle(surf, (255, 246, 200), center, 26 * scale)
        draw_star(surf, center, 24 * scale, (255, 236, 120), outline=(150, 120, 30))


def item_icon(item, scale=1.0):
    """Icona dell'oggetto disegnata una volta sola e poi riusata (più veloce)."""
    key = ("item", item, round(scale, 2))
    s = _cache.get(key)
    if s is None:
        size = int(72 * scale)
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        draw_item(s, item, (size / 2, size / 2), scale)
        _cache_put(_cache, key, s, _CACHE_MAX)
    return s


def blit_item(surf, item, center, scale=1.0):
    icon = item_icon(item, scale)
    surf.blit(icon, icon.get_rect(center=(int(center[0]), int(center[1]))))


def draw_raft(surf, center, scale=1.0, parts=("tronchi", "corda", "vela"), anim=None):
    """Zattera vista di lato. `parts` = pezzi già montati. anim: {parte: 0..1} per l'aggancio."""
    cx, cy = center
    anim = anim or {}
    if "tronchi" in parts:
        k = ease_out_back(anim.get("tronchi", 1.0))
        for i in range(5):
            x = cx + (i - 2) * 44 * scale
            rect = pygame.Rect(0, 0, int(40 * scale), int(30 * scale))
            rect.center = (int(x), int(cy + (1 - k) * -40))
            pygame.draw.rect(surf, C.WOOD if i % 2 == 0 else shade(C.WOOD, 0.88), rect, border_radius=int(12 * scale))
            aa_ring(surf, C.WOOD_DARK, (rect.centerx, rect.centery), 10 * scale, 2)
        pygame.draw.rect(surf, shade(C.WOOD, 0.8), (int(cx - 112 * scale), int(cy - 22 * scale), int(224 * scale), int(10 * scale)),
                         border_radius=4)
    if "corda" in parts:
        k = anim.get("corda", 1.0)
        for dx in (-66, 66):
            x = cx + dx * scale
            for j in range(3):
                y = cy - 14 * scale + j * 10 * scale
                thick_line(surf, C.ROPE, (x - 12 * scale * k, y), (x + 12 * scale * k, y + 4 * scale), 4 * scale)
    if "vela" in parts:
        k = ease_out_back(anim.get("vela", 1.0))
        top = cy - 22 * scale - 170 * scale * k
        thick_line(surf, C.WOOD_DARK, (cx, cy - 20 * scale), (cx, top), 8 * scale)
        if k > 0.2:
            pts = [(cx + 6 * scale, top + 8 * scale), (cx + 100 * scale * k, cy - 50 * scale),
                   (cx + 6 * scale, cy - 44 * scale)]
            aa_polygon(surf, (200, 194, 180), [(x + 3, y + 3) for x, y in pts])
            aa_polygon(surf, C.SAIL, pts)
            draw_star(surf, (cx + 32 * scale, cy - 92 * scale * k), 10 * scale, (240, 90, 60))
        aa_polygon(surf, (220, 60, 60), [(cx, top), (cx + 26 * scale, top + 8 * scale), (cx, top + 16 * scale)])


def draw_raft_top(surf, center, size, t=0.0, night=False):
    """Zattera vista dall'alto per la mappa del mare (prua verso Nord)."""
    cx, cy = center
    s = size / 50.0
    bob = math.sin(t * 3) * 1.5
    for i in range(4):
        rect = pygame.Rect(0, 0, int(9 * s), int(36 * s))
        rect.center = (int(cx + (i - 1.5) * 9.5 * s), int(cy + bob))
        pygame.draw.rect(surf, C.WOOD if i % 2 else shade(C.WOOD, 0.85), rect, border_radius=int(4 * s))
    pygame.draw.line(surf, C.ROPE, (int(cx - 19 * s), int(cy - 10 * s + bob)), (int(cx + 19 * s), int(cy - 10 * s + bob)), max(2, int(3 * s)))
    pygame.draw.line(surf, C.ROPE, (int(cx - 19 * s), int(cy + 10 * s + bob)), (int(cx + 19 * s), int(cy + 10 * s + bob)), max(2, int(3 * s)))
    aa_polygon(surf, C.SAIL if not night else (190, 190, 210),
               [(cx, cy - 16 * s + bob), (cx + 14 * s, cy + 4 * s + bob), (cx - 14 * s, cy + 4 * s + bob)])
    aa_circle(surf, C.WOOD_DARK, (cx, cy + bob), 3 * s)


def draw_stick_top(surf, center, r=10):
    aa_circle(surf, (210, 180, 120), (center[0] + 2, center[1] + 2), r + 8)
    aa_circle(surf, C.WOOD_DARK, center, r + 2)
    aa_circle(surf, C.WOOD, center, r)
    aa_ring(surf, C.WOOD_DARK, center, r * 0.6, 2)


def draw_shadow(surf, base, vec, width=16, color=(40, 30, 20, 110)):
    bx, by = base
    length = math.hypot(*vec)
    if length < 1:
        return
    ux, uy = vec[0] / length, vec[1] / length
    nx, ny = -uy, ux
    tip = (bx + vec[0], by + vec[1])
    pts = [(bx + nx * width / 2, by + ny * width / 2), (tip[0] + nx * width / 3, tip[1] + ny * width / 3),
           (tip[0] + ux * width / 3, tip[1] + uy * width / 3),
           (tip[0] - nx * width / 3, tip[1] - ny * width / 3), (bx - nx * width / 2, by - ny * width / 2)]
    aa_polygon(surf, color, pts)


def draw_tent(surf, center, scale=1.0):
    cx, cy = center
    aa_polygon(surf, (200, 70, 50), [(cx - 26 * scale, cy + 18 * scale), (cx, cy - 22 * scale), (cx + 26 * scale, cy + 18 * scale)])
    aa_polygon(surf, (150, 40, 30), [(cx - 7 * scale, cy + 18 * scale), (cx, cy - 4 * scale), (cx + 7 * scale, cy + 18 * scale)])


def draw_house(surf, center, scale=1.0, wall=(250, 236, 200), roof=(200, 70, 50)):
    cx, cy = center
    pygame.draw.rect(surf, wall, (int(cx - 22 * scale), int(cy - 8 * scale), int(44 * scale), int(30 * scale)))
    aa_polygon(surf, roof, [(cx - 28 * scale, cy - 6 * scale), (cx, cy - 30 * scale), (cx + 28 * scale, cy - 6 * scale)])
    pygame.draw.rect(surf, (120, 80, 50), (int(cx - 6 * scale), int(cy + 6 * scale), int(12 * scale), int(16 * scale)))
    pygame.draw.rect(surf, (120, 190, 240), (int(cx + 8 * scale), int(cy), int(9 * scale), int(9 * scale)))


# ================================================================ luoghi della mappa (tappa 4)
def draw_place(surf, place, center, s=1.0, t=0.0):
    cx, cy = center
    if place == "faro":
        aa_polygon(surf, (240, 240, 240), [(cx - 14 * s, cy + 30 * s), (cx - 8 * s, cy - 24 * s), (cx + 8 * s, cy - 24 * s), (cx + 14 * s, cy + 30 * s)])
        for k in range(3):
            y0 = cy + 20 * s - k * 18 * s
            aa_polygon(surf, (210, 50, 50), [(cx - 13.5 * s + k * 2 * s, y0), (cx - 12.5 * s + k * 2 * s, y0 - 8 * s),
                                             (cx + 12.5 * s - k * 2 * s, y0 - 8 * s), (cx + 13.5 * s - k * 2 * s, y0)])
        pygame.draw.rect(surf, (60, 60, 70), (int(cx - 11 * s), int(cy - 36 * s), int(22 * s), int(13 * s)))
        aa_circle(surf, (255, 230, 90), (cx, cy - 30 * s), 6 * s)
        aa_polygon(surf, (60, 60, 70), [(cx - 13 * s, cy - 36 * s), (cx, cy - 46 * s), (cx + 13 * s, cy - 36 * s)])
        a = t * 1.5
        beam = [(cx, cy - 30 * s), (cx + math.cos(a) * 60 * s, cy - 30 * s + math.sin(a) * 14 * s - 8 * s),
                (cx + math.cos(a) * 60 * s, cy - 30 * s + math.sin(a) * 14 * s + 8 * s)]
        aa_polygon(surf, (255, 240, 150, 90), beam)
    elif place == "grotta":
        aa_polygon(surf, (120, 116, 126), [(cx - 42 * s, cy + 28 * s), (cx - 30 * s, cy - 18 * s), (cx - 4 * s, cy - 34 * s),
                                           (cx + 26 * s, cy - 24 * s), (cx + 42 * s, cy + 28 * s)])
        aa_polygon(surf, (150, 146, 156), [(cx - 30 * s, cy - 18 * s), (cx - 4 * s, cy - 34 * s), (cx + 6 * s, cy - 20 * s), (cx - 20 * s, cy - 8 * s)])
        aa_ellipse(surf, (30, 26, 34), (cx + 2 * s, cy + 12 * s), 18 * s, 17 * s)
        pygame.draw.rect(surf, (30, 26, 34), (int(cx - 16 * s), int(cy + 12 * s), int(36 * s), int(16 * s)))
    elif place == "palma":
        draw_palm(surf, (cx - 6 * s, cy + 32 * s), 80 * s, t, lean=0.12)
        aa_ellipse(surf, (60, 140, 60), (cx, cy + 32 * s), 30 * s, 7 * s)
    elif place == "cascata":
        aa_polygon(surf, (120, 116, 126), [(cx - 40 * s, cy + 10 * s), (cx - 30 * s, cy - 36 * s), (cx + 30 * s, cy - 36 * s), (cx + 40 * s, cy + 10 * s)])
        pygame.draw.rect(surf, (120, 200, 250), (int(cx - 14 * s), int(cy - 36 * s), int(28 * s), int(52 * s)))
        for k in range(4):
            x = cx - 10 * s + k * 7 * s
            y = cy - 30 * s + ((t * 60 + k * 13) % (40 * s))
            pygame.draw.line(surf, (235, 250, 255), (int(x), int(y)), (int(x), int(y + 8 * s)), 2)
        aa_ellipse(surf, (70, 150, 220), (cx, cy + 22 * s), 34 * s, 10 * s)
        aa_ellipse(surf, (225, 245, 255), (cx, cy + 18 * s), 18 * s, 5 * s)
    elif place == "capanna":
        pygame.draw.rect(surf, (176, 120, 66), (int(cx - 28 * s), int(cy - 6 * s), int(56 * s), int(34 * s)))
        for k in range(5):
            x = int(cx - 26 * s + k * 13 * s)
            pygame.draw.line(surf, (130, 84, 40), (x, int(cy - 6 * s)), (x, int(cy + 28 * s)), 2)
        aa_polygon(surf, (222, 190, 90), [(cx - 38 * s, cy - 2 * s), (cx, cy - 38 * s), (cx + 38 * s, cy - 2 * s)])
        aa_polygon(surf, (190, 156, 70), [(cx - 38 * s, cy - 2 * s), (cx, cy - 38 * s), (cx - 4 * s, cy - 2 * s)])
        pygame.draw.rect(surf, (70, 44, 20), (int(cx - 8 * s), int(cy + 8 * s), int(16 * s), int(20 * s)))
    elif place == "lago":
        aa_ellipse(surf, (90, 170, 90), (cx, cy + 4 * s), 46 * s, 28 * s)
        aa_ellipse(surf, (60, 140, 220), (cx, cy + 4 * s), 40 * s, 22 * s)
        aa_ellipse(surf, (150, 210, 250), (cx - 10 * s, cy - 2 * s), 14 * s, 5 * s)
        for k in range(3):
            x = cx + 26 * s + k * 5 * s
            pygame.draw.line(surf, (40, 110, 40), (int(x), int(cy + 18 * s)), (int(x + 2 * s), int(cy - 6 * s)), 3)
    elif place == "tartaruga":
        aa_ellipse(surf, (100, 96, 106), (cx + 32 * s, cy + 4 * s), 12 * s, 9 * s)  # testa
        for dx, dy in ((-24, 18), (22, 18), (-24, -10), (22, -10)):
            aa_ellipse(surf, (100, 96, 106), (cx + dx * s, cy + dy * s), 9 * s, 6 * s)
        aa_ellipse(surf, (126, 122, 134), (cx, cy + 4 * s), 32 * s, 22 * s)
        for dx, dy in ((-12, -4), (12, -4), (0, 10), (-14, 12), (14, 12), (0, -12)):
            aa_circle(surf, (150, 146, 158), (cx + dx * s, cy + dy * s), 6 * s)
        aa_circle(surf, (20, 20, 20), (cx + 36 * s, cy + 1 * s), 2.5 * s)
    elif place == "relitto":
        aa_polygon(surf, (120, 76, 40), [(cx - 44 * s, cy - 2 * s), (cx + 40 * s, cy - 10 * s), (cx + 30 * s, cy + 22 * s), (cx - 34 * s, cy + 24 * s)])
        aa_polygon(surf, (92, 56, 28), [(cx - 30 * s, cy + 4 * s), (cx + 24 * s, cy - 2 * s), (cx + 20 * s, cy + 10 * s), (cx - 26 * s, cy + 12 * s)])
        thick_line(surf, (92, 56, 28), (cx + 2 * s, cy - 4 * s), (cx + 18 * s, cy - 40 * s), 5 * s)
        aa_polygon(surf, (230, 226, 210), [(cx + 16 * s, cy - 36 * s), (cx + 34 * s, cy - 24 * s), (cx + 10 * s, cy - 18 * s)])
        for dx in (-20, 0, 20):
            thick_line(surf, (70, 40, 20), (cx + dx * s, cy + 16 * s), (cx + (dx + 4) * s, cy + 2 * s), 3)


def draw_confetti(surf, pos, size, color, angle):
    w, h = size, size * 0.5
    pts = [rot_point((pos[0] + dx, pos[1] + dy), pos, angle) for dx, dy in ((-w, -h), (w, -h), (w, h), (-w, h))]
    aa_polygon(surf, color, pts)
