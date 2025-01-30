import platform
import pygame
import json

import core.constants as c
import core.globals as g


pygame.init()


# i can't seem to get this function to work at runtime, it just freezes the display
def setup_window() -> pygame.Surface:
    if c.IS_WEB:
        platform.window.canvas.style.imageRendering = "pixelated"
        return pygame.display.set_mode(
            c.WINDOW_SIZE,
        )
    else:
        return pygame.display.set_mode(
            size=c.WINDOW_SIZE,
            flags=pygame.SCALED
            | (pygame.FULLSCREEN if g.settings["fullscreen"] else pygame.RESIZABLE),
            vsync=1 if g.settings["vsync"] else 0,
        )


window = setup_window()

clock = pygame.time.Clock()


print("Setup complete")


def load_settings() -> None:
    if not c.IS_WEB:
        return
    json_str = platform.window.localStorage.getItem("settings")
    if json_str:
        g.settings = json.loads(json_str)


def write_settings() -> None:
    if not c.IS_WEB:
        return
    json_str = json.dumps(g.settings)
    platform.window.localStorage.setItem("settings", json_str)


# Try load settings from web
load_settings()
