import sys
import pygame

# game constants
TILE_SIZE = 16
HALF_TILE_SIZE = 8

# Pygame constants
WINDOW_WIDTH = 32 * TILE_SIZE
WINDOW_HEIGHT = 18 * TILE_SIZE
WINDOW_SIZE = (WINDOW_WIDTH, WINDOW_HEIGHT)
WINDOW_CENTRE = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

IS_WEB = sys.platform == "emscripten"
IS_PRODUCTION = IS_WEB
CAPTION = "BURNER PHONE DX"
FPS = 0  # 0 = Uncapped -> let VSYNC decide best tick speed if enabled
MAX_DT = 1 / 60

# Colour constants
WHITE = pygame.Color(255, 255, 255)
BLACK = pygame.Color(0, 0, 0)
GRAY = pygame.Color(128, 128, 128)
RED = pygame.Color(255, 0, 0)
YELLOW = pygame.Color(255, 255, 0)
GREEN = pygame.Color(0, 255, 0)
CYAN = pygame.Color(0, 255, 255)
BLUE = pygame.Color(0, 0, 255)
MAGENTA = pygame.Color(255, 0, 255)

print("Loaded constants")
