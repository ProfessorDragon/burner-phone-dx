import pygame

import core.assets as a
import core.constants as c
from components.audio import AudioChannel, channel_busy, play_sound
from components.entities.entity_util import path_from_json, path_to_json, render_shadow
from components.animation import (
    Animator,
    animator_get_frame,
    animator_initialise,
    animator_switch_animation,
    animator_update,
    walking_animation_mapping,
)
from components.camera import Camera, camera_to_screen_shake
from components.entities.entity import DIST_THRESHOLD, TURN_THRESHOLD, Entity, entity_follow
from components.motion import Direction, direction_from_angle, motion_update
from components.player import Player, PlayerCaughtStyle, player_caught, player_rect
from components.ray import SightData, collide_sight, compile_sight, render_sight
from scenes.scene import PLAYER_LAYER, RenderLayer


class PatrolEnemy(Entity):
    def __init__(self, path: list[pygame.Vector2]):
        super().__init__()
        self.animator = Animator()
        animator_initialise(self.animator, walking_animation_mapping(a.PATROL_FRAMES, 0.09))
        self.path: list[pygame.Vector2] = path
        self.facing = 0
        self.direction = Direction.N
        self.sight_data = SightData(c.TILE_SIZE * 5, 20, 0)
        self.reset()

    def get_hitbox(self) -> pygame.Rect:
        return pygame.Rect(self.motion.position.x + 12, self.motion.position.y + 28, 8, 4)

    def get_terrain_cutoff(self) -> float:
        return self.motion.position.y + 32

    def get_path(self) -> list[pygame.Vector2]:
        return self.path

    def to_json(self):
        if len(self.path) > 1:
            return {"path": path_to_json(self.path)}
        return {"pos": (*self.motion.position,), "facing": self.facing}

    @staticmethod
    def from_json(js):
        if "path" in js:
            return PatrolEnemy(path_from_json(js["path"]))
        enemy = PatrolEnemy([pygame.Vector2(js["pos"])])
        enemy.facing = js.get("facing", 0)
        return enemy

    def reset(self) -> None:
        self.motion.position = self.path[0].copy()
        if len(self.path) > 1:
            self.facing = (self.path[1] - self.path[0]).angle_to(pygame.Vector2(1, 0))
            self.active_point = 1
        else:
            self.active_point = 0

    def update(
        self,
        dt: float,
        time: float,
        player: Player,
        camera: Camera,
        grid_collision: set[tuple[int, int]],
    ) -> None:
        if len(self.path) > 1:
            target = self.path[self.active_point]
            dist = target - self.motion.position
            target_facing = dist.angle_to(pygame.Vector2(1, 0))
            turn = (target_facing - self.facing) % 360
            if turn > 180:
                turn -= 360
            # not facing in correct direction, turn
            if abs(turn) > TURN_THRESHOLD * dt:
                if abs(turn) > 600 * dt:
                    self.facing += turn / abs(turn) * 600 * dt
                else:
                    self.facing = target_facing
                self.motion.velocity = pygame.Vector2()
            # follow path
            elif dist.magnitude_squared() > DIST_THRESHOLD * dt:
                entity_follow(self, dist, 100)
            # use next point
            else:
                self.motion.position = target.copy()
                self.motion.velocity = pygame.Vector2()
                self.active_point = (self.active_point + 1) % len(self.path)
        self.direction = direction_from_angle(self.facing)

        # collision
        prect = player_rect(player.motion)
        if prect.colliderect(self.get_hitbox()):
            player_caught(player, camera, PlayerCaughtStyle.SIGHT)
        else:
            self.sight_data.center = self.motion.position + pygame.Vector2(16, 16)
            self.sight_data.facing = self.facing
            if len(self.path) > 1 or not self.sight_data.compiled:
                compile_sight(self.sight_data, grid_collision)
            if collide_sight(player, self.sight_data):
                player_caught(player, camera, PlayerCaughtStyle.SIGHT)
        motion_update(self.motion, dt)

        # animation
        if self.motion.velocity.magnitude_squared() > 0:
            animator_switch_animation(self.animator, f"walk_{self.direction}")
        else:
            animator_switch_animation(self.animator, f"idle_{self.direction}")

        prev_frame = self.animator.frame_index
        animator_update(self.animator, dt)
        if self.motion.velocity.magnitude_squared() > 0 and not channel_busy(AudioChannel.ENTITY):
            step_frames = (7, 3)
            if prev_frame not in step_frames and self.animator.frame_index in step_frames:
                play_sound(
                    AudioChannel.ENTITY,
                    a.FOOTSTEPS[2 if self.animator.frame_index == step_frames[0] else 3],
                )

    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
        frame = animator_get_frame(self.animator)
        if layer == RenderLayer.RAYS:
            render_sight(surface, camera, self.sight_data)
        if layer in PLAYER_LAYER:
            render_shadow(surface, camera, self.motion, self.direction)
            surface.blit(
                frame,
                camera_to_screen_shake(camera, *self.motion.position),
            )
