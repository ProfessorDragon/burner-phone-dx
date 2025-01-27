from dataclasses import dataclass
from typing import Any, Iterable
import pygame

import core.constants as c
import core.assets as a
from components.camera import Camera, camera_to_screen_shake


@dataclass(slots=True)
class TileData:
    x: int = 0
    y: int = 0
    render_z: float = -1

    def __iter__(self) -> Iterable:
        return iter((self.x, self.y, self.render_z))

    def copy(self):
        return TileData(*self)  # satisfying


def grid_collision_rect(grid_collision: set[tuple[int, int]], x: int, y: int) -> pygame.Rect | None:
    if (x, y) not in grid_collision:
        return None
    return pygame.Rect(x * c.TILE_SIZE, y * c.TILE_SIZE, c.TILE_SIZE, c.TILE_SIZE)


def tile_render(
    surface: pygame.Surface,
    camera: Camera,
    grid_x: float,
    grid_y: float,
    tile: TileData,
) -> None:
    surface.blit(
        a.TERRAIN,
        camera_to_screen_shake(camera, grid_x * c.TILE_SIZE, grid_y * c.TILE_SIZE),
        (tile.x * c.TILE_SIZE, tile.y * c.TILE_SIZE, c.TILE_SIZE, c.TILE_SIZE),
    )


def tile_render_hitbox(
    surface: pygame.Surface,
    camera: Camera,
    grid_x: float,
    grid_y: float,
    tile: TileData,
) -> None:
    if tile.render_z < 0:
        return
    dest = camera_to_screen_shake(camera, grid_x * c.TILE_SIZE, grid_y * c.TILE_SIZE)
    pygame.draw.line(
        surface,
        c.WHITE,
        (
            dest[0],
            dest[1] + (tile.render_z + 1) * c.TILE_SIZE - 1 - tile.render_z,
        ),
        (
            dest[0] + c.TILE_SIZE - 1,
            dest[1] + (tile.render_z + 1) * c.TILE_SIZE - 1 - tile.render_z,
        ),
    )


def wall_render(
    surface: pygame.Surface, camera: Camera, index: Any | None, wall: pygame.Rect
) -> None:
    pygame.draw.rect(
        surface,
        c.MAGENTA,  # BLUE
        (
            *camera_to_screen_shake(camera, wall.x, wall.y),
            wall.w,
            wall.h,
        ),
        1,
    )
    if index is not None:
        text = a.DEBUG_FONT.render(str(index), False, c.MAGENTA)
        surface.blit(
            text,
            camera_to_screen_shake(
                camera,
                wall.centerx - text.get_width() / 2,
                wall.centery - text.get_height() / 2,
            ),
        )
