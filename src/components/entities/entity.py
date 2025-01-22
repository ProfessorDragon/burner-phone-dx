from abc import ABC, abstractmethod
from math import cos, radians
from typing import Any
import pygame

from components.player import Player
import core.assets as a
import core.constants as c
from components.camera import Camera, camera_to_screen_shake, camera_to_screen_shake_rect
from components.motion import Motion
from scenes.scene import PLAYER_OR_FG, RenderLayer

DIST_THRESHOLD = 300
TURN_THRESHOLD = 100


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


# base class
class Entity(ABC):
    def __init__(self):
        self.motion = Motion.empty()

    # some standard methods to make it easier on the editor
    def get_hitbox(self) -> pygame.Rect:
        return pygame.Rect(
            self.motion.position.x - c.HALF_TILE_SIZE,
            self.motion.position.y - c.HALF_TILE_SIZE,
            c.TILE_SIZE,
            c.TILE_SIZE,
        )

    # some standard methods to make it easier on the editor
    def get_path(self) -> list[pygame.Vector2]:
        return None

    @abstractmethod
    def to_json(self) -> dict[str, Any]: ...

    @staticmethod
    @abstractmethod
    def from_json(js: dict[str, Any]): ...

    @abstractmethod
    def reset(self) -> None: ...

    @abstractmethod
    def update(
        self, dt: float, player: Player, camera: Camera, grid_collision: set[tuple[int, int]]
    ) -> None: ...

    @abstractmethod
    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None: ...


# extension 2 mathematics put to use (kinda)
def entity_follow(entity: Entity, dist: pygame.Vector2, speed: float):
    entity.motion.velocity = dist.normalize() * speed
    entity.motion.velocity *= (
        (0.5 - c.PERSPECTIVE / 2) * cos(2 * radians(dist.angle_to(pygame.Vector2(1, 0))))
        + 0.5
        + c.PERSPECTIVE / 2
    )


def entity_reset(entity: Entity) -> None:
    entity.reset()


def entity_update(
    entity: Entity, dt: float, player: Player, camera: Camera, grid_collision: set[tuple[int, int]]
) -> None:
    entity.update(dt, player, camera, grid_collision)


def entity_render(
    entity: Entity,
    surface: pygame.Surface,
    camera: Camera,
    layer: RenderLayer,
) -> None:
    entity.render(surface, camera, layer)

    if c.DEBUG_HITBOXES:
        if layer == RenderLayer.RAYS:
            path = entity.get_path()
            if path is not None:
                render_path(surface, camera, path)
        if layer in PLAYER_OR_FG:
            hitbox = entity.get_hitbox()
            if hitbox:
                pygame.draw.rect(surface, c.RED, camera_to_screen_shake_rect(camera, *hitbox), 1)
