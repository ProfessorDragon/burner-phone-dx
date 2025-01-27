import pygame

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
from components.player import Player, player_rect
import core.assets as a
import core.constants as c
from components.entities.entity import Entity
from scenes.scene import PLAYER_LAYER, RenderLayer


class GateEntity(Entity):
    def __init__(self):
        super().__init__()
        self.animator = Animator()
        animation_mapping = {
            "closed_0": Animation([a.GATE_FRAMES[0]]),
            "closed_1": Animation([a.GATE_FRAMES[4]]),
            "closed_2": Animation([a.GATE_FRAMES[8]]),
            "open_0": Animation(a.GATE_FRAMES[1:4], 0.1, False),
            "open_1": Animation(a.GATE_FRAMES[5:8], 0.1, False),
            "open_2": Animation(a.GATE_FRAMES[9:12], 0.1, False),
        }
        animator_initialise(self.animator, animation_mapping)
        self.activated = False
        self.id = "default"
        self.color = 0
        self.reset()

    def get_hitbox(self) -> pygame.Rect:
        return pygame.Rect(self.motion.position.x, self.motion.position.y + 30, 32, 4)

    def get_terrain_cutoff(self) -> float:
        return self.motion.position.y + 32

    def to_json(self):
        return {"pos": (*self.motion.position,), "id": self.id, "color": self.color}

    @staticmethod
    def from_json(js):
        ent = GateEntity()
        ent.motion.position = pygame.Vector2(js["pos"])
        ent.id = js.get("id", "default")
        ent.color = js.get("color", 0)
        animator_switch_animation(ent.animator, f"closed_{ent.color}")
        return ent

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
        # collision
        prev_activated = self.activated
        self.activated = self.id in player.progression.activated_buttons
        if not self.activated:
            prect = player_rect(player.motion)
            if prect.colliderect(self.get_hitbox()):
                if player.motion.velocity.y > 0:  # player travelling down
                    player.motion.position.y = self.motion.position.y - 2
                elif player.motion.velocity.y < 0:  # player travelling up
                    player.motion.position.y = self.motion.position.y + 2 + prect.h
                player.motion.velocity.y = 0

        # animation
        if prev_activated != self.activated:
            animator_switch_animation(
                self.animator,
                f"open_{self.color}" if self.activated else f"closed_{self.color}",
            )
            animator_reset(self.animator)
        animator_update(self.animator, dt)

    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
        if layer in PLAYER_LAYER:
            surface.blit(
                animator_get_frame(self.animator),
                camera_to_screen_shake(camera, *self.motion.position),
            )
