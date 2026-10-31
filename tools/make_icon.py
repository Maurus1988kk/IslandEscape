"""Crea tools/icona.ico disegnando Bussolino con pygame (Pillow serve solo per salvare il .ico).

    python tools/make_icon.py
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

import pygame  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from game.gfx import draw as G  # noqa: E402
from game.ui.parrot import Parrot  # noqa: E402


def main():
    pygame.init()
    big = 512
    # Disegno su sfondo pieno e a doppia risoluzione: bordi puliti dopo il ridimensionamento.
    surf = pygame.Surface((big, big))
    surf.fill((20, 70, 140))
    c = (big // 2, big // 2)
    G.aa_circle(surf, (40, 130, 220), c, big * 0.46)
    G.draw_compass_rose(surf, c, big * 0.39, labels=False, bg=False)
    parrot = Parrot((c[0], c[1] + 44), 2.9, perch=False)
    parrot.t = 0.0
    parrot.draw(surf)
    small = pygame.transform.smoothscale(surf, (256, 256))
    img = Image.frombytes("RGB", (256, 256), pygame.image.tobytes(small, "RGB")).convert("RGBA")
    mask = Image.new("L", (1024, 1024), 0)
    ImageDraw.Draw(mask).ellipse((4, 4, 1020, 1020), fill=255)
    img.putalpha(mask.resize((256, 256), Image.LANCZOS))
    out = os.path.join(HERE, "icona.ico")
    img.save(out, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("Icona creata:", out)


if __name__ == "__main__":
    main()
