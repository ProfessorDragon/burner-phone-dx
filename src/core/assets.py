import pygame


pygame.init()


# Load sprites (png, webp or jpg for web compatibility)
ICON = pygame.image.load("assets/icon.png")
DEBUG_SPRITE = pygame.image.load("assets/img/icon_pirate.png")

# Load audio (ogg for web compatibility)
DEBUG_THEME = pygame.mixer.Sound("assets/sfx/theme.ogg")

# Load fonts (ttf for web compatibility)
DEBUG_FONT = pygame.font.Font("assets/joystix.ttf", 10)

print("Loaded assets")
