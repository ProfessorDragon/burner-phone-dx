from math import pi, sin
import pygame

from components.audio import AudioChannel, try_play_sound
import core.assets as a
import core.constants as c
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
from components.entities.entity import Entity
from components.motion import direction_from_angle
from components.player import MainStoryProgress, Player, PlayerCaughtStyle, player_caught
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
        self.inverse_direction = False
        self.sight_data = SightData(c.TILE_SIZE * 5.5, 45, -16)
        self.swivel = 0
        self.swivel_angle = 60
        self.should_raycast = False
        self.reset()

    def get_hitbox(self) -> pygame.Rect:
        return pygame.Rect(*self.motion.position, 16, 16)

    def to_json(self):
        js = {
            "pos": (*self.motion.position,),
            "facing": self.facing,
            "inverse": self.inverse_direction,
            "z": self.sight_data.z_offset,
            "raycast": self.should_raycast,
        }
        return js

    @staticmethod
    def from_json(js):
        enemy = SecurityCameraEnemy()
        enemy.motion.position = pygame.Vector2(js["pos"])
        enemy.facing = js.get("facing", 0)
        enemy.inverse_direction = js.get("inverse", False)
        enemy.sight_data.z_offset = js.get("z", -16)
        enemy.should_raycast = js.get("raycast", False)
        return enemy

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
        # don't swivel before the player has gotten comms (prevent progression)
        # don't swivel during the finale (prevent going back)
        if MainStoryProgress.COMMS <= player.progression.main_story < MainStoryProgress.FINALE:
            self.swivel = self.swivel_angle / 2 * sin(pi * time / 2)
            self.swivel *= -1 if self.inverse_direction else 1
            try_play_sound(AudioChannel.ENTITY_ALT, a.CAMERA_HUM)
        else:
            self.swivel = 0

        # collision
        self.sight_data.center = self.motion.position + pygame.Vector2(8, 8)
        self.sight_data.facing = self.facing + self.swivel
        compile_sight(self.sight_data, grid_collision if self.should_raycast else None)
        if collide_sight(player, self.sight_data):
            player_caught(player, camera, PlayerCaughtStyle.SIGHT)

        # animation
        direction = direction_from_angle(self.facing + self.swivel)
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
