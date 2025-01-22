import random
import pygame

from components.audio import AudioChannel, play_sound
from components.entities.entity_util import render_shadow
import core.assets as a
import core.constants as c
from components.animation import (
    Animator,
    animator_get_frame,
    animator_initialise,
    animator_switch_animation,
    animator_update,
    walking_animation_mapping,
)
from components.camera import Camera, camera_to_screen_shake
from components.entities.entity import DIST_THRESHOLD, Entity, entity_follow
from components.motion import Direction, direction_from_delta, motion_update
from components.player import Player, PlayerCaughtStyle, player_caught, player_rect
from scenes.scene import PLAYER_LAYER, PLAYER_OR_FG, RenderLayer


class ZombieEnemy(Entity):
    def __init__(self, movement_center: pygame.Vector2):
        super().__init__()
        self.animator = Animator()
        animator_initialise(self.animator, walking_animation_mapping(a.PATROL_FRAMES, 0.07))
        self.direction = Direction.N
        self.movement_center = movement_center
        self.movement_radius = 96
        self.reset()

    def get_hitbox(self) -> pygame.Rect:
        return pygame.Rect(
            round(self.motion.position.x) + 12, round(self.motion.position.y) + 28, 8, 4
        )

    def get_terrain_cutoff(self) -> float:
        return self.motion.position.y + 32

    def to_json(self):
        return {"pos": (*self.movement_center,)}

    @staticmethod
    def from_json(js):
        return ZombieEnemy(pygame.Vector2(js["pos"]))

    def reset(self) -> None:
        self.motion.position = self.movement_center.copy()
        self.chasing = True
        self.randomize_walk_speed()

    def randomize_walk_speed(self) -> None:
        self.walk_speed = 200 * random.uniform(0.8, 1.2)

    def update(
        self, dt: float, player: Player, camera: Camera, grid_collision: set[tuple[int, int]]
    ) -> None:
        self.motion.velocity = pygame.Vector2()
        prect = player_rect(player.motion)
        hitbox = self.get_hitbox()
        # only move when player moves
        player_dist = pygame.Vector2(prect.center) - pygame.Vector2(hitbox.center)
        if player.motion.velocity.magnitude_squared() > 0:
            center_dist = (
                self.movement_center + pygame.Vector2(16, 30) - pygame.Vector2(hitbox.center)
            )
            if self.chasing:
                if center_dist.magnitude() < self.movement_radius:
                    entity_follow(self, player_dist, self.walk_speed)
                else:
                    self.chasing = False
                    self.randomize_walk_speed()
                    if player_dist.magnitude() < self.movement_radius * 1.5:
                        play_sound(AudioChannel.SFX, a.ZOMBIE)
            else:
                if center_dist.magnitude_squared() > DIST_THRESHOLD * dt:
                    entity_follow(self, center_dist, self.walk_speed)
                else:
                    self.chasing = True
                    self.randomize_walk_speed()
        if self.motion.velocity.magnitude_squared() > 0:
            self.direction = direction_from_delta(*self.motion.velocity)
        elif random.randint(1, 300) == 1:
            self.direction = Direction((self.direction + 1) % 8)

        # collision
        if prect.colliderect(hitbox):
            player_caught(player, camera, PlayerCaughtStyle.ZOMBIE)

        # animation
        if self.motion.velocity.magnitude_squared() > 0:
            animator_switch_animation(self.animator, f"walk_{self.direction}")
        else:
            animator_switch_animation(self.animator, f"idle_{self.direction}")
        animator_update(self.animator, dt)

        motion_update(self.motion, dt)

    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
        if layer in PLAYER_LAYER:
            render_shadow(surface, camera, self.motion, self.direction)
            surface.blit(
                animator_get_frame(self.animator),
                camera_to_screen_shake(camera, *self.motion.position),
            )
        if layer in PLAYER_OR_FG and c.DEBUG_HITBOXES:
            pygame.draw.circle(
                surface,
                c.RED,
                camera_to_screen_shake(camera, *(self.movement_center + pygame.Vector2(16, 30))),
                self.movement_radius,
                1,
            )
