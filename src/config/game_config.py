# Constantes e configuracoes do jogo.

# Janela
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
FPS           = 60
WINDOW_TITLE  = "PAPERWORLDS"

# Mundo (4x a area original: 240 -> 480 celulas por eixo)
CELL_SIZE    = 6
WORLD_COLS   = 480
WORLD_ROWS   = 480
WORLD_WIDTH  = WORLD_COLS * CELL_SIZE   # 2880 px
WORLD_HEIGHT = WORLD_ROWS * CELL_SIZE   # 2880 px

# Jogador
PLAYER_SPEED      = 155.0
PLAYER_RADIUS     = 9
TRAIL_WIDTH       = 5
TRAIL_SAMPLE_DIST = 3.5
MIN_CLAIM_POINTS  = 10
CLOSE_THRESHOLD   = 22.0

# Ressurreicao: raio minimo de celulas livres (sem tinta) para renascer.
# O disco inteiro precisa estar jogavel e sem dono.
RESPAWN_CLEAR_RADIUS_CELLS = 4
RESPAWN_SEED_RADIUS_CELLS  = 4

# Bots
BOT_SPEED_BASE  = 125.0
NUM_BOTS        = 8
AI_THINK_MIN    = 0.18
AI_THINK_MAX    = 0.45
AI_HUNT_RANGE   = 160.0
AI_DANGER_RANGE = 90.0

BOT_NAMES = [
    "Nova", "Blitz", "Shadow", "Pulse", "Vortex",
    "Echo", "Forge", "Drift",  "Pixel", "Quark",
    "Apex", "Rune",  "Flux",   "Spark", "Orbit", "Cipher",
]

# Colisao
KILL_RADIUS          = PLAYER_RADIUS + 2
SELF_IMMUNITY_POINTS = 22
MIN_SELF_TRAIL       = 24

# Camera
CAMERA_LERP = 0.15

# Cores
BG_COLOR   = (28,  32,  38)
GRID_COLOR = (38,  42,  50)
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
YELLOW     = (255, 220, 50)
RED        = (255, 70,  70)
GREEN      = (80,  220, 120)

# Direcoes
DIR_UP    = (0, -1)
DIR_DOWN  = (0,  1)
DIR_LEFT  = (-1, 0)
DIR_RIGHT = (1,  0)
DIRECTIONS = [DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT]

# Skins
SKINS = [
    {"id": 0, "name": "Azure",   "primary": (70,  170, 255), "secondary": (40,  100, 180), "accent": (200, 230, 255)},
    {"id": 1, "name": "Crimson", "primary": (255, 70,  70),  "secondary": (180, 30,  30),  "accent": (255, 200, 200)},
    {"id": 2, "name": "Emerald", "primary": (60,  220, 120), "secondary": (20,  140, 70),  "accent": (180, 255, 200)},
    {"id": 3, "name": "Amber",   "primary": (255, 180, 40),  "secondary": (200, 120, 20),  "accent": (255, 230, 150)},
    {"id": 4, "name": "Violet",  "primary": (180, 90,  255), "secondary": (110, 40,  180), "accent": (230, 200, 255)},
    {"id": 5, "name": "Rose",    "primary": (255, 100, 180), "secondary": (180, 40,  100), "accent": (255, 200, 230)},
    {"id": 6, "name": "Teal",    "primary": (50,  210, 210), "secondary": (20,  130, 140), "accent": (180, 255, 255)},
    {"id": 7, "name": "Gold",    "primary": (255, 215, 60),  "secondary": (180, 140, 20),  "accent": (255, 245, 180)},
    {"id": 8, "name": "Indigo",  "primary": (100, 120, 255), "secondary": (50,  60,  180), "accent": (200, 210, 255)},
    {"id": 9, "name": "Lime",    "primary": (160, 255, 50),  "secondary": (90,  160, 20),  "accent": (220, 255, 180)},
]

# Persistencia
SAVE_FILE = "territorio_save.json"
