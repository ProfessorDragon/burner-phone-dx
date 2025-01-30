import platform
import pygame
import json

import core.constants as c
import core.globals as g


pygame.init()

if c.IS_WEB:
    platform.window.canvas.style.imageRendering = "pixelated"
    window = pygame.display.set_mode(c.WINDOW_SETUP["size"])
else:
    window = pygame.display.set_mode(**c.WINDOW_SETUP)


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
