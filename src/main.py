import sys
import platform
import asyncio
import pygame


# Try to declare all your globals at once to facilitate compilation later.
# Pygame constants
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 360
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
MAX_DT = 1/60

# Colour constants
WHITE = pygame.Color(255, 255, 255)
BLACK = pygame.Color(0, 0, 0)
RED = pygame.Color(255, 0, 0)
YELLOW = pygame.Color(255, 255, 0)
GREEN = pygame.Color(0, 255, 0)
CYAN = pygame.Color(0, 255, 255)
BLUE = pygame.Color(0, 0, 255)
MAGENTA = pygame.Color(255, 0, 255)


# Do init here
pygame.init()

if sys.platform == "emscripten":  # If running in browser
    platform.window.canvas.style.imageRendering = "pixelated"
    window = pygame.display.set_mode(WINDOW_SETUP["size"])
else:
    window = pygame.display.set_mode(**WINDOW_SETUP)

clock = pygame.time.Clock()


# Load any assets right now to avoid lag at runtime or network errors.
# Load sprites (png, webp or jpg for web compatibility)
ICON = pygame.image.load("res/icon.png")
DEBUG_SPRITE = pygame.image.load("res/img/icon_pirate.png")

# Load audio (ogg for web compatibility)
DEBUG_THEME = pygame.mixer.Sound("res/sfx/theme.ogg")

# Load fonts (ttf for web compatibility)
DEBUG_FONT = pygame.font.Font("res/joystix.ttf", 10)

# Setup pygame display
pygame.display.set_caption(CAPTION)
pygame.display.set_icon(ICON)


async def main() -> None:
    pygame.mixer.Channel(0).play(DEBUG_THEME, -1)

    MAX_X = WINDOW_WIDTH - DEBUG_SPRITE.get_width()
    MAX_Y = WINDOW_HEIGHT - DEBUG_SPRITE.get_height()

    pirate_x = 0
    pirate_y = 0
    pirate_vx = 1
    pirate_vy = 1
    pirate_speed = 64

    while True:
        elapsed_time = clock.tick(FPS)
        dt = elapsed_time / 1000.0  # Convert to seconds
        dt = min(dt, MAX_DT)  # Clamp delta time

        # INPUT
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    terminate()

        # UPDATE
        pirate_x += pirate_vx * pirate_speed * dt
        pirate_y += pirate_vy * pirate_speed * dt

        if pirate_vx > 0 and pirate_x > MAX_X:
            pirate_vx = -1
        elif pirate_vx < 0 and pirate_x < 0:
            pirate_vx = 1

        if pirate_vy > 0 and pirate_y > MAX_Y:
            pirate_vy = -1
        elif pirate_vy < 0 and pirate_y < 0:
            pirate_vy = 1

        # RENDER
        # Do your rendering here, note that it's NOT an infinite loop,
        # and it is fired only when VSYNC occurs
        # Usually 1/60 or more times per seconds on desktop
        # could be less on some mobile devices
        window.fill(WHITE)

        window.blit(DEBUG_SPRITE, (pirate_x, pirate_y))

        debug_string = f"FPS {clock.get_fps():.0f}\nDT {dt}"
        debug_text = DEBUG_FONT.render(debug_string, False, MAGENTA)
        window.blit(debug_text, (0, 0))

        # Keep these calls together in this order
        pygame.display.flip()
        await asyncio.sleep(0)  # Very important, and keep it 0


def terminate() -> None:
    window.fill(BLACK)
    pygame.mixer.stop()
    pygame.quit()
    raise SystemExit


if __name__ == "__main__":
    # This is the program entry point:
    asyncio.run(main())

# Do not add anything from here, especially sys.exit/pygame.quit
# asyncio.run is non-blocking on pygame-wasm and code would be executed
# right before program start main()
