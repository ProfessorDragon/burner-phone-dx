from dataclasses import dataclass
from math import pi, radians, sin
import pygame
from pygame import gfxdraw

import core.constants as c
from utilities.math import point_in_circle
from components.camera import Camera, camera_to_screen_shake


@dataclass
class SightData:
    # parameters
    radius: float  # radius of the cone of sight
    angle: float  # angle of the cone of sight
    z_offset: float = 0  # how high up the raycast starts (negative is higher)
    center: pygame.Vector2 = None  # start position of raycast
    facing: float = 0  # current rotation of the raycast

    # compiled data
    compiled: bool = False
    collision_depths: list[float] = None
    render_segs: list[tuple[int, int]] = None


def _grid_raycast(
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


def sight_compile(data: SightData, grid_collision: set[tuple[int, int]] = None) -> None:
    assert data.center is not None
    # fwiw, this is relatively cheap. my computer can handle almost 200 steps without lag
    # so, as long as there isn't an excessive amount of raycasting entities on screen at once, it's fine
    segs = int(pi / 360 * data.radius * data.angle)
    steps = int(data.radius / 4)
    # strategically ignore some collision at the start
    start_step = int((data.z_offset * sin(radians(data.facing)) - data.z_offset) / 4) + 2
    offset_center = data.center + pygame.Vector2(0, data.z_offset)
    data.collision_depths = []
    data.render_segs = [(data.radius, data.radius + data.z_offset)]
    for i in range(segs):
        percent = float(i) / (segs - 1)
        sight = pygame.Vector2(data.radius, 0).rotate(-data.facing + data.angle * (percent - 0.5))
        sight.y -= data.z_offset
        if grid_collision is not None:
            depth = _grid_raycast(sight, offset_center, grid_collision, steps, start_step)
        else:
            depth = 1
        data.collision_depths.append(depth)
        sight *= depth
        sight.y += data.z_offset
        data.render_segs.append((data.radius + sight.x, data.radius + sight.y))
    data.compiled = True


def sight_collides(data: SightData, point: pygame.Vector2) -> bool:
    if data.collision_depths is None:
        return
    if not point_in_circle(*point, *data.center, data.radius):
        return False
    dist = point - data.center
    nearest = None
    steps = len(data.collision_depths) - 1
    for i, depth in enumerate(data.collision_depths):
        percent = float(i) / steps
        theta = -data.facing + data.angle * (percent - 0.5)
        delta = dist.angle_to(pygame.Vector2(1, 0).rotate(theta)) % 360
        if delta > 180:
            delta -= 360
        # spent half an hour debugging because i forgot an abs here
        if nearest is None or abs(delta) < abs(nearest[2]):
            nearest = (i, depth, delta)
    if nearest is not None:
        if (
            abs(nearest[2]) <= float(data.angle) / steps
            and dist.magnitude() < data.radius * nearest[1] - 1
        ):
            return True
    return False


def sight_render(
    surface: pygame.Surface, camera: Camera, data: SightData, color: pygame.Color = (64, 64, 64)
) -> None:
    if data.render_segs is None:
        return
    sight_surf = pygame.Surface((data.radius * 2, data.radius * 2), pygame.SRCALPHA)
    if not c.IS_WEB:
        gfxdraw.aapolygon(sight_surf, data.render_segs, color)
    pygame.draw.polygon(sight_surf, color, data.render_segs)
    surface.blit(
        sight_surf,
        camera_to_screen_shake(
            camera,
            data.center.x - sight_surf.get_width() // 2,
            data.center.y - sight_surf.get_height() // 2,
        ),
        special_flags=pygame.BLEND_RGB_ADD,
    )
