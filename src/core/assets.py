import pygame

from utilities.sprite import slice_sheet


# FONTS (ttf for web compatibility)

DEBUG_FONT = pygame.font.Font("assets/joystix.ttf", 10)


# IMAGES (png, webp or jpg for web compatibility)
IMG = "assets/img/"
ICON = pygame.image.load(IMG + "icon.png")
DEBUG_SPRITE_64 = pygame.image.load(IMG + "pirate.png")

# player
PLAYER_FRAMES = slice_sheet(IMG + "player.png", 32, 32)
CAUGHT_INDICATORS = slice_sheet(IMG + "huh_sheet.png", 16, 16)
CHECKPOINT_FRAMES = slice_sheet(IMG + "checkpoint.png", 32, 32)
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
    [[surf] for surf in slice_sheet(IMG + "decor/trees.png", 64, 64)]  # 0-7
    + [
        [pygame.image.load(IMG + "decor/shipping_container.png")],  # 8
        [pygame.image.load(IMG + "decor/shack.png")],  # 9
        slice_sheet(IMG + "decor/tube.png", 64, 64),  # 10
        slice_sheet(IMG + "decor/tube_skinny.png", 64, 64),  # 11
    ]
    + [[surf] for surf in slice_sheet(IMG + "decor/bushes.png", 32, 32)]  # 12-13
    + [
        [pygame.image.load(IMG + "decor/lab_door.png")],  # 14
    ]
)

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
MENU_BUTTONS = slice_sheet(MENU + "buttons.png", 96, 16)


def _generate_controls():
    diagram = pygame.image.load(MENU + "controls.png")
    cx, cy = MENU_CONTROLS.get_width() // 2, MENU_CONTROLS.get_height() // 2
    MENU_CONTROLS.blit(
        diagram,
        (cx - diagram.get_width() // 2 - 20, cy - diagram.get_height() // 2 + 1),
    )
    move = DEBUG_FONT.render("Move", False, (255, 255, 255))
    jump = DEBUG_FONT.render("Jump", False, (255, 255, 255))
    roll = DEBUG_FONT.render("Roll", False, (255, 255, 255))
    MENU_CONTROLS.blit(move, (cx - move.get_width() // 2 - 57, cy - 26))
    MENU_CONTROLS.blit(jump, (cx - jump.get_width() // 2 + 95, cy - jump.get_height() // 2 - 12))
    MENU_CONTROLS.blit(roll, (cx - roll.get_width() // 2 + 95, cy - roll.get_height() // 2 + 12))


MENU_CONTROLS = pygame.Surface((256, 64), pygame.SRCALPHA)
_generate_controls()


# AUDIO (ogg for web compatibility)
SFX = "assets/sfx/"

# music
THEME_MUSIC_PATH = [
    SFX + "theme_0.ogg",
    SFX + "theme_1.ogg",
    SFX + "theme_2.ogg",
    SFX + "theme_3.ogg",
]

STATIC_PATH = SFX + "static.ogg"
STATIC = pygame.mixer.Sound(STATIC_PATH)

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

# entities
CAMERA_HUM = pygame.mixer.Sound(SFX + "camera_hum.ogg")
ZOMBIE_CHASE = pygame.mixer.Sound(SFX + "zomb_chase.ogg")
ZOMBIE_RETREAT = pygame.mixer.Sound(SFX + "zomb_retreat.ogg")
GATE_OPEN = pygame.mixer.Sound(SFX + "gate_open.ogg")
BONUS_UNLOCK = pygame.mixer.Sound(SFX + "bonus.ogg")

# menu
UI_SELECT = pygame.mixer.Sound(SFX + "select.ogg")
UI_HOVER = pygame.mixer.Sound(SFX + "hover.ogg")


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
