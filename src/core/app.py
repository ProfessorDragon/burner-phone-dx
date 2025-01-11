import sys
import platform
import asyncio
import pygame

import core.constants as const
import core.assets as asset


def run() -> None:
    window = setup_window()
    clock = pygame.time.Clock()

    print("Setup complete")

    asyncio.run(game_loop(window, clock))


def setup_window() -> pygame.Surface:
    # Setup pygame display
    if sys.platform == "emscripten":  # If running in browser
        platform.window.canvas.style.imageRendering = "pixelated"
        window = pygame.display.set_mode(const.WINDOW_SETUP["size"])
    else:
        window = pygame.display.set_mode(**const.WINDOW_SETUP)

    pygame.display.set_caption(const.CAPTION)
    pygame.display.set_icon(asset.ICON)

    return window


async def game_loop(surface: pygame.Surface, clock: pygame.Clock) -> None:
    pygame.mixer.Channel(0).play(asset.DEBUG_THEME, -1)

    MAX_X = const.WINDOW_WIDTH - asset.DEBUG_SPRITE.get_width()
    MAX_Y = const.WINDOW_HEIGHT - asset.DEBUG_SPRITE.get_height()

    pirate_x = 0
    pirate_y = 0
    pirate_vx = 1
    pirate_vy = 1
    pirate_speed = 64

    print("Running game loop")

    while True:
        elapsed_time = clock.tick(const.FPS)
        dt = elapsed_time / 1000.0  # Convert to seconds
        dt = min(dt, const.MAX_DT)  # Clamp delta time

        # INPUT
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate(surface)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    terminate(surface)

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
        surface.fill(const.WHITE)

        surface.blit(asset.DEBUG_SPRITE, (pirate_x, pirate_y))

        debug_str = f"FPS {clock.get_fps():.0f}\nDT {dt}"
        debug_text = asset.DEBUG_FONT.render(debug_str, False, const.MAGENTA)
        surface.blit(debug_text, (0, 0))

        # Keep these calls together in this order
        pygame.display.flip()
        await asyncio.sleep(0)  # Very important, and keep it 0


def terminate(surface: pygame.Surface) -> None:
    surface.fill(const.BLACK)
    pygame.mixer.stop()
    pygame.quit()
    raise SystemExit
