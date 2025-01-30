from dataclasses import dataclass
import pygame

from utilities.sprite import slice_sheet


# IMAGES (png, webp or jpg for web compatibility)
IMG = "assets/img/"
ICON = pygame.image.load(IMG + "icon.png")
DEBUG_SPRITE_64 = pygame.image.load(IMG + "pirate.png")

# player
PLAYER_FRAMES = slice_sheet(IMG + "player.png", 32, 32)
CAUGHT_INDICATORS = slice_sheet(IMG + "huh_sheet.png", 16, 16)
VIGNETTE = pygame.image.load(IMG + "vignette.png")

# terrain
TERRAIN = pygame.image.load(IMG + "terrain.png")

# entities
PATROL_FRAMES = slice_sheet(IMG + "entities/patrol.png", 32, 32)
ZOMBIE_FRAMES = slice_sheet(IMG + "entities/zombie.png", 32, 32)
SECURITY_CAMERA_FRAMES = slice_sheet(IMG + "entities/security_camera.png", 16, 16)
SPIKE_TRAP_FRAMES = slice_sheet(IMG + "entities/spike_trap.png", 16, 16)
BUTTON_FRAMES = slice_sheet(IMG + "entities/button.png", 16, 16)
GATE_FRAMES = slice_sheet(IMG + "entities/gate.png", 32, 32)

# decor
DECOR = (
    [[surf] for surf in slice_sheet(IMG + "decor/trees.png", 64, 64)]
    + [  # 0-7
        [pygame.image.load(IMG + "decor/shipping_container.png")],  # 8
        [pygame.image.load(IMG + "decor/shack.png")],  # 9
        slice_sheet(IMG + "decor/tube.png", 64, 64),  # 10
    ]
    + [[surf] for surf in slice_sheet(IMG + "decor/bushes.png", 32, 32)]
)  # 11-12

# menu
MENU = "assets/menu/"
MENU_BACK = pygame.image.load(MENU + "menu_back.png")
MENU_BLUR = pygame.image.load(MENU + "menu_blur.png")
MENU_BACK_ALT = pygame.image.load(MENU + "menu_back_alt.png")
MENU_BLUR_FULL = pygame.image.load(MENU + "menu_blur_full.png")
MENU_SCANS = [
    pygame.image.load(MENU + "scan1.png"),
    pygame.image.load(MENU + "scan2.png"),
    pygame.image.load(MENU + "scan3.png"),
]
MENU_CONTROLS = pygame.image.load(MENU + "controls.png")


# AUDIO (ogg for web compatibility)
SFX = "assets/sfx/"

# music
THEME_MUSIC = [
    pygame.mixer.Sound(SFX + "theme_0.ogg"),
    pygame.mixer.Sound(SFX + "theme_1.ogg"),
    pygame.mixer.Sound(SFX + "theme_2.ogg"),
    pygame.mixer.Sound(SFX + "theme_3.ogg"),
]
STATIC = pygame.mixer.Sound(SFX + "static.ogg")

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
EXPLOSIONS = [
    pygame.mixer.Sound(SFX + "explosion_1.ogg"),
    pygame.mixer.Sound(SFX + "explosion_2.ogg"),
]

# ui
UI_SELECT = pygame.mixer.Sound(SFX + "select.ogg")
UI_HOVER = pygame.mixer.Sound(SFX + "hover.ogg")

# entities
CAMERA_HUM = pygame.mixer.Sound(SFX + "camera_hum.ogg")
ZOMBIE_CHASE = pygame.mixer.Sound(SFX + "zomb_chase.ogg")
ZOMBIE_RETREAT = pygame.mixer.Sound(SFX + "zomb_retreat.ogg")
GATE_OPEN = pygame.mixer.Sound(SFX + "gate_open.ogg")


# FONTS (ttf for web compatibility)

DEBUG_FONT = pygame.font.Font("assets/joystix.ttf", 10)


# DIALOGUE

with open("assets/script.txt") as f:
    GAME_SCRIPT = f.read()

DIALOGUE_AVATARS = slice_sheet(IMG + "avatars.png", 64, 64)
DIALOGUE_SOUNDS = [
    pygame.mixer.Sound(SFX + "dialogue_high_1.ogg"),
    pygame.mixer.Sound(SFX + "dialogue_high_2.ogg"),
    pygame.mixer.Sound(SFX + "dialogue_low_1.ogg"),
    pygame.mixer.Sound(SFX + "dialogue_low_2.ogg"),
    pygame.mixer.Sound(SFX + "dialogue_comms_1.ogg"),
    pygame.mixer.Sound(SFX + "dialogue_comms_2.ogg"),
    pygame.mixer.Sound(SFX + "dialogue_sign_1.ogg"),
    pygame.mixer.Sound(SFX + "dialogue_sign_2.ogg"),
    pygame.mixer.Sound(SFX + "dialogue_evil_1.ogg"),
    pygame.mixer.Sound(SFX + "dialogue_evil_2.ogg"),
]

OPEN_PHONE = pygame.mixer.Sound(SFX + "open_phone.ogg")
OPEN_COMMS = pygame.mixer.Sound(SFX + "open_comms.ogg")

with open("assets/credits.txt") as f:
    CREDITS = f.read()

print("Loaded assets")
