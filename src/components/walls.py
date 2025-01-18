import pygame

import core.constants as c
import core.assets as a
from components.camera import Camera, camera_to_screen_shake


def tile_size_rect(x: float, y: float, w: float = 1, h: float = 1):
    return pygame.Rect(
        x * c.TILE_SIZE, y * c.TILE_SIZE, w * c.TILE_SIZE, h * c.TILE_SIZE
    )


def draw_wall(surface: pygame.Surface, camera: Camera, index: int, wall: pygame.Rect):
    pygame.draw.rect(
        surface,
        c.BLUE,  # BLUE
        (
            *camera_to_screen_shake(camera, wall.x, wall.y),
            wall.w,
            wall.h,
        ),
        1,
    )
    text = a.DEBUG_FONT.render(str(index), False, c.BLUE)
    surface.blit(
        text,
        camera_to_screen_shake(
            camera,
            wall.centerx - text.get_width() / 2,
            wall.centery - text.get_height() / 2,
        ),
    )
