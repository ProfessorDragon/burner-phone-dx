import pygame

import core.assets as a
from components.animation import (
    Animation,
    Animator,
    animator_get_frame,
    animator_initialise,
    animator_reset,
    animator_switch_animation,
    animator_update,
)
from components.camera import Camera, camera_to_screen_shake
from components.entities.entity import Entity
from components.player import Player, PlayerCaughtStyle, player_caught, player_rect
from scenes.scene import PLAYER_OR_BG, RenderLayer


class SpikeTrapEnemy(Entity):
    def __init__(self):
        super().__init__()
        self.animator = Animator()
        animation_mapping = {
            "idle": Animation([a.SPIKE_TRAP_FRAMES[0]]),
            "stepped_on": Animation([a.SPIKE_TRAP_FRAMES[1]]),
            "activated": Animation(a.SPIKE_TRAP_FRAMES[2:], 0.1, False),
        }
        animator_initialise(self.animator, animation_mapping)
        self.reset()

    def get_hitbox(self) -> pygame.Rect:
        return pygame.Rect(self.motion.position.x + 4, self.motion.position.y + 2, 8, 12)

    def to_json(self):
        return {"pos": (*self.motion.position,)}

    @staticmethod
    def from_json(js):
        enemy = SpikeTrapEnemy()
        enemy.motion.position = pygame.Vector2(js["pos"])
        return enemy

    def reset(self) -> None:
        self.stepped_on = False
        self.activated = False
        animator_switch_animation(self.animator, "idle")

    def update(
        self, dt: float, player: Player, camera: Camera, grid_collision: set[tuple[int, int]]
    ) -> None:
        # collision
        if player.z_position == 0:
            prect = player_rect(player.motion)
            prev_stepped = self.stepped_on
            self.stepped_on = prect.colliderect(self.get_hitbox())
            if self.stepped_on and not prev_stepped:
                if not self.activated:
                    animator_switch_animation(self.animator, "stepped_on")
                else:
                    player_caught(player, camera, PlayerCaughtStyle.HOLE)
            elif not self.stepped_on and prev_stepped:
                self.activated = True
                animator_switch_animation(self.animator, "activated")
                animator_reset(self.animator)
        animator_update(self.animator, dt)

    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
        if layer in PLAYER_OR_BG:
            surface.blit(
                animator_get_frame(self.animator),
                camera_to_screen_shake(camera, *self.motion.position),
            )
