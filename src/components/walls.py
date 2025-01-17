from dataclasses import dataclass

import pygame
from components.camera import Camera, camera_to_screen_shake
import core.constants as c
from components.motion import Vector2


def tile_size_rect(x: float, y: float, w: float = 1, h: float = 1):
    return pygame.Rect(
        x * c.TILE_SIZE, y * c.TILE_SIZE, w * c.TILE_SIZE, h * c.TILE_SIZE
    )


def draw_wall(surface: pygame.Surface, camera: Camera, wall: pygame.Rect):
    pygame.draw.rect(
        surface,
        c.BLUE,
        (
            *camera_to_screen_shake(camera, wall.x, wall.y),
            wall.w + 1,
            wall.h + 1,
        ),
        1,
    )
