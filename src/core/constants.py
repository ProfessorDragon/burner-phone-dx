import pygame

TILE_SIZE = 32
HALF_TILE_SIZE = 16

# Pygame constants
WINDOW_WIDTH = 16 * TILE_SIZE
WINDOW_HEIGHT = 9 * TILE_SIZE
WINDOW_SIZE = (WINDOW_WIDTH, WINDOW_HEIGHT)
WINDOW_CENTRE = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

WINDOW_SETUP = {
    "size": WINDOW_SIZE,
    "flags": pygame.SCALED | pygame.RESIZABLE,
    "depth": 0,
    "display": 0,
    "vsync": 1,
}

CAPTION = "Pirate Software - Game Jam 16"
FPS = 0  # 0 = Uncapped -> let VSYNC decide best tick speed if enabled
MAX_DT = 1 / 60

# Colour constants
WHITE = pygame.Color(255, 255, 255)
BLACK = pygame.Color(0, 0, 0)
RED = pygame.Color(255, 0, 0)
YELLOW = pygame.Color(255, 255, 0)
GREEN = pygame.Color(0, 255, 0)
CYAN = pygame.Color(0, 255, 255)
BLUE = pygame.Color(0, 0, 255)
MAGENTA = pygame.Color(255, 0, 255)

print("Loaded constants")
