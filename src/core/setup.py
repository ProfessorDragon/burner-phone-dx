import platform
import pygame

import core.constants as c


pygame.init()

if c.IS_WEB:
    platform.window.canvas.style.imageRendering = "pixelated"
    window = pygame.display.set_mode(c.WINDOW_SETUP["size"])
else:
    window = pygame.display.set_mode(**c.WINDOW_SETUP)


clock = pygame.time.Clock()


print("Setup complete")
