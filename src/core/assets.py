from dataclasses import dataclass
import pygame

import core.constants as c
from utilities.sprite import get_sprite_from_sheet, slice_sheet


## IMAGES (png, webp or jpg for web compatibility)
IMG = "assets/img/"

# icon
ICON = pygame.image.load("assets/icon.png")

# debug
DEBUG_IMAGE_16 = pygame.image.load(IMG + "debug/image_16.png")
DEBUG_IMAGE_64 = pygame.image.load(IMG + "debug/image_64.png")
DEBUG_SPRITE_128 = pygame.image.load(IMG + "debug/pirate_128.png")
DEBUG_SPRITE_64 = pygame.image.load(IMG + "debug/pirate_64.png")

# player
PLAYER_FRAMES = slice_sheet(IMG + "player.png", 32, 32)

# terrain
TERRAIN = pygame.image.load(IMG + "terrain.png")

# entities
PATROL_FRAMES = slice_sheet(IMG + "entities/patrol.png", 32, 32)
SPIKE_TRAP_FRAMES = slice_sheet(IMG + "entities/spike_trap.png", 16, 16)
SECURITY_CAMERA_FRAMES = slice_sheet(IMG + "entities/security_camera.png", 16, 16)
BUTTON_FRAMES = slice_sheet(IMG + "entities/button.png", 16, 16)
SIGN = get_sprite_from_sheet(TERRAIN, 0, 6 * c.TILE_SIZE, c.TILE_SIZE, c.TILE_SIZE)


## AUDIO (ogg for web compatibility)
SFX = "assets/sfx/"

# music
DEBUG_THEME_MENU = pygame.mixer.Sound(SFX + "menu.ogg")
THEME_MUSIC = [
    pygame.mixer.Sound(SFX + "theme-0.ogg"),
    pygame.mixer.Sound(SFX + "theme-1.ogg"),
    pygame.mixer.Sound(SFX + "theme-2.ogg"),
    pygame.mixer.Sound(SFX + "theme-3.ogg"),
]

# player
JUMP = pygame.mixer.Sound(SFX + "jump.ogg")
ROLL = pygame.mixer.Sound(SFX + "roll.ogg")
FOOTSTEPS = [
    pygame.mixer.Sound(SFX + "footstep_1.ogg"),
    pygame.mixer.Sound(SFX + "footstep_2.ogg"),
    pygame.mixer.Sound(SFX + "patrol_footstep_1.ogg"),
    pygame.mixer.Sound(SFX + "patrol_footstep_2.ogg"),
]
CAUGHT_SIGHT = pygame.mixer.Sound(SFX + "caught_sight.ogg")
CAUGHT_HOLE = pygame.mixer.Sound(SFX + "caught_hole.ogg")

# ui
UI_SELECT = pygame.mixer.Sound(SFX + "select.ogg")
UI_HOVER = pygame.mixer.Sound(SFX + "hover.ogg")

# entities
CAMERA_HUM = pygame.mixer.Sound(SFX + "camera_hum.ogg")
ZOMBIE_CHASE = pygame.mixer.Sound(SFX + "zomb_chase.ogg")
ZOMBIE_RETREAT = pygame.mixer.Sound(SFX + "zomb_retreat.ogg")


# FONTS (ttf for web compatibility)

DEBUG_FONT = pygame.font.Font("assets/joystix.ttf", 10)


## DIALOGUE

with open("assets/script.txt") as script:
    GAME_SCRIPT = script.read()


@dataclass
class DialogueCharacter:
    name: str
    sprites: list[pygame.Surface]
    sounds: list[pygame.mixer.Sound]


DIALOGUE_PLACEHOLDER_AVATARS = slice_sheet(IMG + "dialogue_placeholder_avatars.png", 64, 64)
DIALOGUE_PLACEHOLDER_SOUNDS = [
    pygame.mixer.Sound(SFX + "dialogue_high_1.ogg"),
    pygame.mixer.Sound(SFX + "dialogue_high_2.ogg"),
    pygame.mixer.Sound(SFX + "dialogue_low_1.ogg"),
    pygame.mixer.Sound(SFX + "dialogue_low_2.ogg"),
    pygame.mixer.Sound(SFX + "dialogue_comms_1.ogg"),
    pygame.mixer.Sound(SFX + "dialogue_comms_2.ogg"),
    pygame.mixer.Sound(SFX + "dialogue_sign_1.ogg"),
    pygame.mixer.Sound(SFX + "dialogue_sign_2.ogg"),
]

COMMS_OPEN = pygame.mixer.Sound(SFX + "comms_open.ogg")

DIALOGUE_CHARACTERS = {
    "default": DialogueCharacter(
        "???",
        [DEBUG_IMAGE_64],
        DIALOGUE_PLACEHOLDER_SOUNDS[0:2],
    ),
    "sign": DialogueCharacter(
        "Sign",
        [DEBUG_IMAGE_64],
        DIALOGUE_PLACEHOLDER_SOUNDS[6:8],
    ),
    "phone": DialogueCharacter(
        "Phone",
        [DEBUG_IMAGE_64],
        DIALOGUE_PLACEHOLDER_SOUNDS[0:2],
    ),
    "luke": DialogueCharacter(
        "Luke",
        DIALOGUE_PLACEHOLDER_AVATARS,
        DIALOGUE_PLACEHOLDER_SOUNDS[0:2],
    ),
    "rogan_no_comms": DialogueCharacter(
        "Rogan",
        DIALOGUE_PLACEHOLDER_AVATARS,
        DIALOGUE_PLACEHOLDER_SOUNDS[2:4],
    ),
    "rogan": DialogueCharacter(
        "Rogan",
        DIALOGUE_PLACEHOLDER_AVATARS,
        DIALOGUE_PLACEHOLDER_SOUNDS[4:6],
    ),
}

print("Loaded assets")
