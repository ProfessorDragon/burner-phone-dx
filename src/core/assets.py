from dataclasses import dataclass
import pygame

from utilities.sprite import slice_sheet


## IMAGES (png, webp or jpg for web compatibility)

# icon
ICON = pygame.image.load("assets/icon.png")

# debug
DEBUG_IMAGE_16 = pygame.image.load("assets/img/debug/image_16.png")
DEBUG_IMAGE_64 = pygame.image.load("assets/img/debug/image_64.png")
DEBUG_SPRITE_128 = pygame.image.load("assets/img/debug/pirate_128.png")
DEBUG_SPRITE_64 = pygame.image.load("assets/img/debug/pirate_64.png")

# player
PLAYER_FRAMES = slice_sheet("assets/img/player.png", 32, 32)

# terrain
TERRAIN = pygame.image.load("assets/img/terrain.png")

# entities
PATROL_FRAMES = slice_sheet("assets/img/entities/patrol.png", 32, 32)
SPIKE_TRAP_FRAMES = slice_sheet("assets/img/entities/spike_trap.png", 16, 16)
SECURITY_CAMERA_FRAMES = slice_sheet("assets/img/entities/security_camera.png", 16, 16)
BUTTON_FRAMES = slice_sheet("assets/img/entities/button.png", 16, 16)


## AUDIO (ogg for web compatibility)

# music
DEBUG_THEME_MENU = pygame.mixer.Sound("assets/sfx/menu.ogg")

# player
JUMP = pygame.mixer.Sound("assets/sfx/jump.ogg")
FOOTSTEP = pygame.mixer.Sound("assets/sfx/footstep.ogg")
CAUGHT_SIGHT = pygame.mixer.Sound("assets/sfx/caught_sight.ogg")
CAUGHT_HOLE = pygame.mixer.Sound("assets/sfx/caught_hole.ogg")

# ui
UI_SELECT = pygame.mixer.Sound("assets/sfx/select.ogg")
UI_HOVER = pygame.mixer.Sound("assets/sfx/hover.ogg")

# entities
ZOMBIE = pygame.mixer.Sound("assets/sfx/zomb.ogg")


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
    "phone": DialogueCharacter("Phone", [DEBUG_IMAGE_64]),
    "luke": DialogueCharacter("Luke", DIALOGUE_PLACEHOLDER_AVATARS),
    "rogan": DialogueCharacter("Rogan", DIALOGUE_PLACEHOLDER_AVATARS),
}

print("Loaded assets")
