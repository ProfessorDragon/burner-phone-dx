from abc import ABC, abstractmethod
from math import cos, radians
from typing import Any
import pygame

from components.entities.entity_util import render_path
from components.player import Player
import core.constants as c
from components.camera import Camera, camera_to_screen_shake_rect
from components.motion import Motion
from scenes.scene import PLAYER_OR_FG, RenderLayer

DIST_THRESHOLD = 300
TURN_THRESHOLD = 100


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

    def get_terrain_cutoff(self) -> float:
        return self.motion.position.y + 16

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
        self,
        dt: float,
        time: float,
        player: Player,
        camera: Camera,
        grid_collision: set[tuple[int, int]],
    ) -> None: ...

    @abstractmethod
    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None: ...


def entity_follow(entity: Entity, dist: pygame.Vector2, speed: float):
    entity.motion.velocity = dist.normalize() * speed


def entity_reset(entity: Entity) -> None:
    entity.reset()


def entity_update(
    entity: Entity,
    dt: float,
    time: float,
    player: Player,
    camera: Camera,
    grid_collision: set[tuple[int, int]],
) -> None:
    entity.update(dt, time, player, camera, grid_collision)


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
