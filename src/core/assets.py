import pygame

from utilities.sprite import slice_sheet


## IMAGES (png, webp or jpg for web compatibility)

# icon
ICON = pygame.image.load("assets/icon.png")

# debug
DEBUG_IMAGE = pygame.image.load("assets/img/debug_image.png")
DEBUG_SPRITE = pygame.image.load("assets/img/icon_pirate.png")
DEBUG_SPRITE_SMALL = pygame.image.load("assets/img/icon_pirate_small.png")
DEBUG_FRAMES = slice_sheet("assets/img/impossible_spin.png", 64, 64)

# player
PLAYER_FRAMES = slice_sheet("assets/img/player_sheet_2.png", 32, 32)

# terrain
TERRAIN_SHEET = pygame.image.load("assets/img/terrain_sheet.png")

# enemies
PATROL_FRAMES = slice_sheet("assets/img/patrol_sheet.png", 32, 32)


## AUDIO (ogg for web compatibility)

# music
DEBUG_THEME_GAME = pygame.mixer.Sound("assets/sfx/theme.ogg")
DEBUG_THEME_MENU = pygame.mixer.Sound("assets/sfx/menu.ogg")

# sfx
DEBUG_BONK = pygame.mixer.Sound("assets/sfx/bonk.ogg")


# FONTS (ttf for web compatibility)

DEBUG_FONT = pygame.font.Font("assets/joystix.ttf", 10)


## MISC

with open("assets/script.txt") as script:
    GAME_SCRIPT = script.read()

print("Loaded assets")
