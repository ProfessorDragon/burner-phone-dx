import pygame

import core.assets as a
from components.animation import (
    Animation,
    Animator,
    animator_get_frame,
    animator_initialise,
    animator_switch_animation,
    animator_update,
    directional_animation_mapping,
)
from components.camera import Camera, camera_to_screen_shake
from components.entities.entity import TURN_THRESHOLD, Entity
from components.motion import Direction, direction_from_angle
from components.player import Player, PlayerCaughtStyle, player_caught
from components.ray import SightData, collide_sight, compile_sight, render_sight
from scenes.scene import PLAYER_LAYER, RenderLayer


class SecurityCameraEnemy(Entity):
    def __init__(self):
        super().__init__()
        self.animator = Animator()
        animation_mapping = directional_animation_mapping(
            {
                "swivel": [
                    Animation([a.SECURITY_CAMERA_FRAMES[4]]),
                    Animation([a.SECURITY_CAMERA_FRAMES[3]]),
                    Animation([a.SECURITY_CAMERA_FRAMES[2]]),
                    Animation([a.SECURITY_CAMERA_FRAMES[1]]),
                    Animation([a.SECURITY_CAMERA_FRAMES[0]]),
                    Animation([a.SECURITY_CAMERA_FRAMES[7]]),
                    Animation([a.SECURITY_CAMERA_FRAMES[6]]),
                    Animation([a.SECURITY_CAMERA_FRAMES[5]]),
                ]
            }
        )
        animator_initialise(self.animator, animation_mapping)
        self.facing = 0
        self.sight_data = SightData(96, 30)
        self.swivel = 0
        self.swivel_angle = 60
        self.swivel_forwards = True
        self.reset()

    def get_hitbox(self) -> pygame.Rect:
        return pygame.Rect(*self.motion.position, 16, 16)

    def to_json(self):
        return {
            "pos": (*self.motion.position,),
            "facing": self.facing,
            "z": self.sight_data.z_offset,
        }

    @staticmethod
    def from_json(js):
        enemy = SecurityCameraEnemy()
        enemy.motion.position = pygame.Vector2(js["pos"])
        enemy.facing = js.get("facing", 0)
        enemy.sight_data.z_offset = js.get("z", 0)
        return enemy

    def reset(self) -> None:
        self.swivel = 0

    def update(
        self, dt: float, player: Player, camera: Camera, grid_collision: set[tuple[int, int]]
    ) -> None:
        if self.swivel_forwards:
            target_swivel = self.swivel_angle / 2
        else:
            target_swivel = -self.swivel_angle / 2
        turn = (target_swivel - self.swivel) % 360
        if turn > 180:
            turn -= 360
        # not facing in correct direction, turn
        if abs(turn) > TURN_THRESHOLD * dt:
            if self.swivel_forwards:
                self.swivel += 30 * dt
            else:
                self.swivel -= 30 * dt
        # inverse swivel direction
        else:
            self.swivel_forwards = not self.swivel_forwards

        # collision
        self.sight_data.center = self.motion.position + pygame.Vector2(8, 8)
        self.sight_data.facing = self.facing + self.swivel
        compile_sight(self.sight_data, grid_collision)
        if collide_sight(player, self.sight_data):
            player_caught(player, camera, PlayerCaughtStyle.SIGHT)

        # animation
        direction = direction_from_angle(self.facing)  # looks better without adding swivel
        animator_switch_animation(self.animator, f"swivel_{direction}")
        animator_update(self.animator, dt)

    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
        if layer == RenderLayer.RAYS:
            render_sight(surface, camera, self.sight_data)
        if layer in PLAYER_LAYER:
            surface.blit(
                animator_get_frame(self.animator),
                camera_to_screen_shake(
                    camera,
                    self.motion.position.x,
                    self.motion.position.y + self.sight_data.z_offset,
                ),
            )
