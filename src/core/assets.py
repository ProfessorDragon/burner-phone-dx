from dataclasses import dataclass
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
PLAYER_FRAMES = slice_sheet("assets/img/player.png", 32, 32)

# terrain
TERRAIN = pygame.image.load("assets/img/terrain.png")

# entities
PATROL_FRAMES = slice_sheet("assets/img/entities/patrol.png", 32, 32)
SPIKE_TRAP_FRAMES = slice_sheet("assets/img/entities/spike_trap.png", 16, 16)
BUTTON_FRAMES = slice_sheet("assets/img/entities/button.png", 16, 16)


## AUDIO (ogg for web compatibility)

# music
DEBUG_THEME_GAME = pygame.mixer.Sound("assets/sfx/theme.ogg")
DEBUG_THEME_MENU = pygame.mixer.Sound("assets/sfx/menu.ogg")

# sfx
DEBUG_BONK = pygame.mixer.Sound("assets/sfx/bonk.ogg")


# FONTS (ttf for web compatibility)

DEBUG_FONT = pygame.font.Font("assets/joystix.ttf", 10)


## DIALOGUE

with open("assets/script.txt") as script:
    GAME_SCRIPT = script.read()


@dataclass
class DialogueCharacter:
    name: str
    sprites: list[pygame.Surface]


DIALOGUE_PLACEHOLDER_AVATARS = slice_sheet("assets/img/dialogue_placeholder_avatars.png", 64, 64)
DIALOGUE_CHARACTERS = {
    "phone": DialogueCharacter("Phone", [DEBUG_IMAGE]),
    "luke": DialogueCharacter("Luke", DIALOGUE_PLACEHOLDER_AVATARS),
    "rogan": DialogueCharacter("Rogan", DIALOGUE_PLACEHOLDER_AVATARS),
}

print("Loaded assets")
