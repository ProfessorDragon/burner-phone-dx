import pygame

import core.constants as c
from components.camera import Camera
from components.entities.entity import Entity
from components.player import Player, PlayerCaughtStyle, player_caught, player_rect
from scenes.scene import RenderLayer


class LakeEnemy(Entity):
    def __init__(self):
        super().__init__()
        self.w, self.h = 1, 1
        self.reset()

    def get_hitbox(self) -> pygame.Rect:
        # small hitboxes are good! but make sure to patch any holes as a result.
        return pygame.Rect(
            self.motion.position.x + 5,
            self.motion.position.y + 5,
            c.TILE_SIZE * self.w - 10,
            c.TILE_SIZE * self.h - 10,
        )

    def to_json(self):
        return {"pos": (*self.motion.position,), "w": self.w, "h": self.h}

    @staticmethod
    def from_json(js):
        entity = LakeEnemy()
        entity.motion.position = pygame.Vector2(js["pos"])
        entity.w, entity.h = js.get("w", 1), js.get("h", 1)
        return entity

    def reset(self) -> None:
        pass

    def update(
        self,
        dt: float,
        time: float,
        player: Player,
        camera: Camera,
        grid_collision: set[tuple[int, int]],
    ) -> None:
        prect = player_rect(player.motion)
        if prect.colliderect(self.get_hitbox()) and player.z_position == 0:
            player_caught(player, camera, PlayerCaughtStyle.HOLE)

    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
        pass
