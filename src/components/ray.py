from dataclasses import dataclass
from math import pi
import pygame
from pygame import gfxdraw

from components.camera import Camera, camera_to_screen_shake
from components.player import Player, player_rect
import core.constants as c
from utilities.math import point_in_circle, point_in_ellipse


@dataclass
class SightData:
    radius: float
    angle: float
    z_offset: float = 0
    center: pygame.Vector2 = None
    facing: float = 0
    collision_depths: list[float] = None
    render_segs: list[tuple[int, int]] = None


def grid_raycast(
    vec: pygame.Vector2,
    center: pygame.Vector2,
    grid_collision: set[tuple[int, int]],
    steps: int,
    start_step: int,
) -> float:
    last_tile = None
    for i in range(min(start_step, steps), steps):
        percent = float(i) / steps
        ray = vec * percent
        x, y = int((ray.x + center.x) // c.TILE_SIZE), int((ray.y + center.y) // c.TILE_SIZE)
        if last_tile == (x, y):
            continue
        if (x, y) in grid_collision:
            return percent
        last_tile = (x, y)
    return 1


def compile_sight(data: SightData, grid_collision: set[tuple[int, int]]) -> None:
    assert data.center is not None
    segs = int(pi / 360 * data.radius * data.angle)
    steps = int(data.radius / c.HALF_TILE_SIZE)
    data.collision_depths = []
    data.render_segs = [(data.radius, data.radius + data.z_offset)]
    for i in range(segs):
        percent = float(i) / (segs - 1)
        sight = pygame.Vector2(data.radius, 0).rotate(-data.facing + data.angle * (percent - 0.5))
        depth = grid_raycast(sight, data.center, grid_collision, steps, 3)
        data.collision_depths.append(depth)
        sight *= depth
        data.render_segs.append((data.radius + sight.x, data.radius + sight.y))


def collide_sight(player: Player, data: SightData) -> bool:
    if data.collision_depths is None:
        return
    prect = player_rect(player.motion)
    if not point_in_circle(*prect.center, *data.center, data.radius):
        return False
    player_dist = pygame.Vector2(prect.center) - data.center
    nearest = None
    steps = len(data.collision_depths) - 1
    for i, depth in enumerate(data.collision_depths):
        percent = float(i) / steps
        theta = -data.facing + data.angle * (percent - 0.5)
        delta = player_dist.angle_to(pygame.Vector2(1, 0).rotate(theta)) % 360
        if delta > 180:
            delta -= 360
        # spent half an hour debugging because i forgot an abs here
        if nearest is None or abs(delta) < abs(nearest[2]):
            nearest = (i, depth, delta)
    if nearest is not None:
        if (
            abs(nearest[2]) <= float(data.angle) / steps
            and player_dist.magnitude() < data.radius * nearest[1] - 1
        ):
            return True
    return False


def render_sight(surface: pygame.Surface, camera: Camera, data: SightData) -> None:
    if data.render_segs is None:
        return
    color = (162, 48, 0, 96)
    sight_surf = pygame.Surface((data.radius * 2, data.radius * 2), pygame.SRCALPHA)
    gfxdraw.aapolygon(sight_surf, data.render_segs, color)
    pygame.draw.polygon(sight_surf, color, data.render_segs)
    surface.blit(
        sight_surf,
        camera_to_screen_shake(
            camera,
            data.center.x - sight_surf.get_width() // 2,
            data.center.y - sight_surf.get_height() // 2,
        ),
    )
