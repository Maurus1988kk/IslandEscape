"""Font, testo a capo automatico e opzione TUTTO MAIUSCOLO."""

import pygame

from .. import config

_uppercase = False
_fonts = {}
_render_cache = {}
_CACHE_MAX = 700


def set_uppercase(value):
    global _uppercase
    if bool(value) != _uppercase:
        _uppercase = bool(value)
        _render_cache.clear()


def is_uppercase():
    return _uppercase


def reset():
    """Da chiamare dopo pygame.init(): i font creati prima non sono più validi."""
    _fonts.clear()
    _render_cache.clear()


def tx(text):
    """Applica l'opzione stampatello."""
    return text.upper() if _uppercase else text


def get(size, bold=False):
    key = (int(size), bool(bold))
    font = _fonts.get(key)
    if font is None:
        if not pygame.font.get_init():
            pygame.font.init()
        font = None
        try:
            font = pygame.font.SysFont(config.FONT_NAMES, int(size), bold=bold)
            if font.metrics("àèéìòù") is None or None in font.metrics("àèéìòù"):
                font = None
        except Exception:
            font = None
        if font is None:
            # Font predefinito di pygame (freesansbold): contiene le lettere accentate.
            font = pygame.font.Font(None, int(size * 1.35))
        _fonts[key] = font
    return font


def render(text, size, color, bold=False, transform=True):
    if transform:
        text = tx(text)
    key = (text, int(size), tuple(color), bool(bold))
    surf = _render_cache.get(key)
    if surf is None:
        if len(_render_cache) > _CACHE_MAX:
            _render_cache.clear()
        surf = get(size, bold).render(text, True, color)
        _render_cache[key] = surf
    return surf


def text_size(text, size, bold=False, transform=True):
    if transform:
        text = tx(text)
    return get(size, bold).size(text)


def wrap(text, size, max_width, bold=False):
    """Divide il testo (già trasformato) in righe che stanno in max_width."""
    font = get(size, bold)
    lines = []
    for para in tx(text).split("\n"):
        words = para.split(" ")
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if font.size(trial)[0] <= max_width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def line_height(size, bold=False):
    return int(get(size, bold).get_linesize() * 1.02)


def fit(text, max_width, max_height, sizes=(34, 32, 30, 28), bold=False):
    """Sceglie la dimensione più grande per cui il testo sta nel riquadro."""
    for size in sizes:
        lines = wrap(text, size, max_width, bold)
        if len(lines) * line_height(size, bold) <= max_height:
            return size, lines
    size = sizes[-1]
    return size, wrap(text, size, max_width, bold)


def draw(surface, text, pos, size=config.FONT_NORMAL, color=config.TEXT_DARK, bold=False,
         anchor="topleft", shadow=None, shadow_offset=(2, 2), transform=True):
    surf = render(text, size, color, bold, transform)
    rect = surf.get_rect(**{anchor: (int(pos[0]), int(pos[1]))})
    if shadow is not None:
        sh = render(text, size, shadow, bold, transform)
        surface.blit(sh, rect.move(shadow_offset))
    surface.blit(surf, rect)
    return rect


def draw_outlined(surface, text, pos, size, color, outline, bold=True, anchor="center", width=2):
    surf = render(text, size, color, bold)
    out = render(text, size, outline, bold)
    rect = surf.get_rect(**{anchor: (int(pos[0]), int(pos[1]))})
    for dx in (-width, 0, width):
        for dy in (-width, 0, width):
            if dx or dy:
                surface.blit(out, rect.move(dx, dy))
    surface.blit(surf, rect)
    return rect


def draw_lines(surface, lines, rect, size, color=config.TEXT_DARK, bold=False, align="center",
               valign="center"):
    """Disegna righe già divise dentro un rettangolo."""
    rect = pygame.Rect(rect)
    lh = line_height(size, bold)
    total = lh * len(lines)
    if valign == "center":
        y = rect.y + (rect.h - total) // 2
    elif valign == "bottom":
        y = rect.bottom - total
    else:
        y = rect.y
    for line in lines:
        surf = render(line, size, color, bold, transform=False)
        if align == "center":
            x = rect.centerx - surf.get_width() // 2
        elif align == "right":
            x = rect.right - surf.get_width()
        else:
            x = rect.x
        surface.blit(surf, (x, y))
        y += lh
    return total


def draw_wrapped(surface, text, rect, sizes=(32, 30, 28), color=config.TEXT_DARK, bold=False,
                 align="center", valign="center"):
    rect = pygame.Rect(rect)
    size, lines = fit(text, rect.w, rect.h, sizes, bold)
    draw_lines(surface, lines, rect, size, color, bold, align, valign)
    return size
