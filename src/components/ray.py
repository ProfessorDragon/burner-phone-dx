from dataclasses import dataclass
from math import pi
import pygame
from pygame import gfxdraw

from components.camera import Camera, camera_to_screen_shake
from components.player import Player, player_rect
from components.tiles import grid_collision_rect
import core.constants as c
from utilities.math import point_in_circle, point_in_ellipse


@dataclass
class SightData:
    # parameters
    radius: float
    angle: float
    z_offset: float = 0
    center: pygame.Vector2 = None
    facing: float = 0

    # compiled data
    compiled: bool = False
    collision_depths: list[float] = None
    render_segs: list[tuple[int, int]] = None


def grid_raycast(
    vec: pygame.Vector2,
    center: pygame.Vector2,
    grid_collision: set[tuple[int, int]],
    steps: int,
    start_step: int,
) -> float:
    for i in range(min(start_step, steps), steps):
        percent = float(i) / steps
        ray = vec * percent
        x = int((ray.x + center.x) // c.TILE_SIZE)
        y = int((ray.y + center.y) // c.TILE_SIZE)
        if (x, y) in grid_collision:
            return percent
    return 1


def compile_sight(data: SightData, grid_collision: set[tuple[int, int]]) -> None:
    assert data.center is not None
    # fwiw, this is relatively cheap. my computer can handle almost 200 steps without lag
    # so, as long as there isn't an excessive amount of raycasting enemies on screen at once, it's fine
    segs = int(pi / 360 * data.radius * data.angle)
    steps = int(data.radius / 4)
    offset_center = data.center + pygame.Vector2(0, data.z_offset)
    data.collision_depths = []
    data.render_segs = [(data.radius, data.radius + data.z_offset)]
    for i in range(segs):
        percent = float(i) / (segs - 1)
        sight = pygame.Vector2(data.radius, 0).rotate(-data.facing + data.angle * (percent - 0.5))
        sight.y -= data.z_offset
        depth = grid_raycast(sight, offset_center, grid_collision, steps, 2)
        data.collision_depths.append(depth)
        sight *= depth
        sight.y += data.z_offset
        data.render_segs.append((data.radius + sight.x, data.radius + sight.y))
    data.compiled = True


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
