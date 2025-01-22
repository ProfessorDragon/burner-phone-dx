import pygame

import core.assets as a
import core.constants as c
from components.camera import Camera, camera_to_screen_shake
from components.motion import Direction, Motion


def render_shadow(
    surface: pygame.Surface,
    camera: Camera,
    motion: Motion,
    direction: Direction,
    z_position: float = 0,
) -> None:
    # use two vectors because we NEED to preserve decimal places
    shadow_tl = pygame.Vector2(motion.position.x + 10, motion.position.y + 30)
    shadow_wh = pygame.Vector2(12, 4)
    if motion.velocity.x != 0:
        if direction in (Direction.W, Direction.NW, Direction.SW):
            shadow_wh.x += 2
        elif direction in (Direction.E, Direction.NE, Direction.SE):
            shadow_tl.x -= 2
            shadow_wh.x += 2
    if z_position < -5:
        shadow_wh.x -= 2
        shadow_wh.y -= 2
        shadow_tl.x += 1
        shadow_tl.y += 1
    shadow = pygame.Surface(shadow_wh, pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 50), pygame.Rect(0, 0, *shadow_wh))
    surface.blit(shadow, camera_to_screen_shake(camera, *shadow_tl))


def render_path(surface: pygame.Surface, camera: Camera, path: list[pygame.Vector2]) -> None:
    if len(path) == 0:
        return
    if len(path) == 1:
        pygame.draw.circle(surface, c.RED, camera_to_screen_shake(camera, *path[0]), 3)
    else:
        pygame.draw.polygon(
            surface,
            c.RED,
            [camera_to_screen_shake(camera, *point) for point in path],
            1,
        )

    for i, point in enumerate(path):
        surface.blit(
            a.DEBUG_FONT.render(str(i), False, c.RED),
            camera_to_screen_shake(camera, *point),
        )


def path_to_json(path: list[pygame.Vector2]) -> list[tuple[int, int]]:
    return [(int(point.x), int(point.y)) for point in path]


def path_from_json(js_path: list[tuple[int, int]]) -> list[pygame.Vector2]:
    return [pygame.Vector2(point) for point in js_path]
