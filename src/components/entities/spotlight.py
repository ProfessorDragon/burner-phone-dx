import pygame

import core.constants as c
from components.camera import Camera, camera_to_screen_shake
from components.entities.entity import DIST_THRESHOLD, Entity, entity_follow
from components.entities.entity_util import path_from_json, path_to_json
from components.motion import motion_update
from components.player import Player, PlayerCaughtStyle, player_caught, player_rect
from scenes.scene import PLAYER_OR_FG, RenderLayer
from utilities.math import point_in_circle


class SpotlightEnemy(Entity):
    def __init__(self, path: list[pygame.Vector2]):
        super().__init__()
        self.path: list[pygame.Vector2] = path
        self.active_point = 0
        self.light_radius = c.TILE_SIZE * 3
        self.reset()

    def get_path(self) -> list[pygame.Vector2]:
        return self.path

    def to_json(self):
        return {"path": path_to_json(self.path)}

    @staticmethod
    def from_json(js):
        return SpotlightEnemy(path_from_json(js["path"]))

    def reset(self) -> None:
        self.motion.position = self.path[0].copy()
        self.active_point = 0

    def update(
        self,
        dt: float,
        time: float,
        player: Player,
        camera: Camera,
        grid_collision: set[tuple[int, int]],
    ) -> None:
        if len(self.path) > 0:
            target = self.path[self.active_point]
            dist = target - self.motion.position
            # follow path
            if dist.magnitude_squared() > DIST_THRESHOLD * dt:
                entity_follow(self, dist, 50)
            # use next point
            else:
                self.motion.position = target.copy()
                self.motion.velocity = pygame.Vector2()
                self.active_point = (self.active_point + 1) % len(self.path)

        # collision
        prect = player_rect(player.motion)
        if point_in_circle(*prect.center, *self.motion.position, self.light_radius - 1):
            player_caught(player, camera, PlayerCaughtStyle.SIGHT)

        motion_update(self.motion, dt)

    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
        if layer in PLAYER_OR_FG:
            rx, ry = self.light_radius, self.light_radius
            render_position = (self.motion.position.x - rx, self.motion.position.y - ry)
            sprite = pygame.Surface((rx * 2, ry * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(sprite, (255, 255, 0, 96), sprite.get_rect())
            surface.blit(sprite, camera_to_screen_shake(camera, *render_position))
