"""Costanti del gioco: dimensioni, colori, layout, tappe e oggetti."""

TITLE = "Fuga dall'Isola Sperduta"
EXE_NAME = "FugaDallIsola"
APP_DIR_NAME = "FugaIsola"
VERSION = "1.0.0"

# Risoluzione logica: tutto viene disegnato qui e poi scalato sulla finestra.
WIDTH, HEIGHT = 1280, 720
FPS = 60

# ---------------------------------------------------------------- layout
TOPBAR_H = 90
INV_Y = 640                      # inizio della barra inventario
INV_H = HEIGHT - INV_Y
PANEL_W = 410                    # colonna sinistra con Bussolino
PLAY_RECT = (420, 96, 850, 538)  # area di gioco (x, y, w, h)
BUTTON_MIN_H = 80

PARROT_POS = (105, 168)
HINT_BTN_RECT = (208, 112, 194, 84)
BUBBLE_RECT = (12, 236, 396, 300)
BUBBLE_RECT_SHORT = (12, 236, 396, 200)
NEXT_BTN_RECT = (92, 548, 236, 84)
PAUSE_BTN_RECT = (1186, 5, 88, 82)

# ---------------------------------------------------------------- testo
FONT_NAMES = "verdana,tahoma,arial,segoeui"
FONT_NORMAL = 30
FONT_MIN = 28
FONT_BUTTON = 32
FONT_BIG = 44
FONT_TITLE = 62
FONT_LABEL = 26  # etichette brevi su mappa e inventario

# ---------------------------------------------------------------- colori
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
TEXT_DARK = (28, 30, 48)
TEXT_SOFT = (70, 74, 96)

SKY_TOP = (78, 168, 240)
SKY_BOTTOM = (176, 226, 255)
SEA_DEEP = (18, 92, 165)
SEA_LIGHT = (38, 150, 205)
FOAM = (232, 246, 255)
SAND = (246, 214, 140)
SAND_DARK = (222, 184, 108)
GRASS = (92, 176, 82)
GRASS_DARK = (58, 138, 62)
ROCK = (128, 124, 134)
ROCK_DARK = (88, 84, 96)
WOOD = (150, 96, 48)
WOOD_DARK = (104, 64, 30)
ROPE = (214, 176, 98)
SAIL = (250, 246, 232)

BTN_GREEN = (28, 134, 74)
BTN_BLUE = (30, 96, 190)
BTN_ORANGE = (214, 104, 22)
BTN_YELLOW = (250, 200, 52)
BTN_RED = (196, 62, 58)
BTN_PURPLE = (124, 74, 186)
BTN_GRAY = (110, 116, 130)
BTN_TEAL = (16, 128, 138)

OK_GREEN = (28, 150, 70)
KO_ORANGE = (232, 118, 36)
NORTH_RED = (214, 46, 46)
HIGHLIGHT = (255, 224, 60)
PANEL_BG = (255, 255, 255)
NIGHT_TOP = (6, 10, 34)
NIGHT_BOTTOM = (26, 42, 92)

# ---------------------------------------------------------------- direzioni
DIRS = ("N", "E", "S", "O")  # ordine in senso orario
DIR_NAMES = {"N": "Nord", "E": "Est", "S": "Sud", "O": "Ovest"}
DIR_COLORS = {"N": NORTH_RED, "E": BTN_ORANGE, "S": BTN_BLUE, "O": BTN_PURPLE}

# ---------------------------------------------------------------- oggetti
ITEMS = ("rosa", "corda", "tronchi", "vela", "stella")
ITEM_NAMES = {
    "rosa": "Rosa dei venti",
    "corda": "Corda",
    "tronchi": "Tronchi",
    "vela": "Vela",
    "stella": "Stella Polare",
}
STAGE_ITEM = {1: "rosa", 2: "corda", 3: "tronchi", 4: "vela", 5: "stella", 6: None}
STAGE_COUNT = 6

TIMER_CHOICES = (0, 30, 45, 60)  # minuti, 0 = spento
