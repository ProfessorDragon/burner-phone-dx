from abc import ABC, abstractmethod
from math import cos, radians

import pygame
from components.player import Player, player_caught, player_rect
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
from components.camera import Camera, camera_to_screen_shake, camera_to_screen_shake_rect
from components.motion import Direction, Motion, direction_from_angle, motion_update
from scenes.scene import RenderLayer
from utilities.math import point_in_ellipse


# base class
class Enemy(ABC):
    def __init__(self):
        self.motion = Motion.empty()

    def get_hitbox(self) -> pygame.Rect:
        return None

    @abstractmethod
    def update(self, dt: float, player: Player, camera: Camera) -> None: ...

    @abstractmethod
    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None: ...


# extension 2 mathematics put to use (kinda)
def _enemy_follow(enemy: Enemy, dist: pygame.Vector2, speed: float):
    enemy.motion.velocity = dist.normalize() * speed
    enemy.motion.velocity *= (
        (0.5 - c.PERSPECTIVE / 2) * cos(2 * radians(dist.angle_to(pygame.Vector2(1, 0))))
        + 0.5
        + c.PERSPECTIVE / 2
    )


class PatrolEnemy(Enemy):
    def __init__(self):
        super().__init__()
        self.animator = Animator()
        animation_mapping = directional_animation_mapping(
            {
                "idle": [
                    Animation([a.PATROL_FRAMES[4]], 1),
                    Animation([a.PATROL_FRAMES[3]], 1),
                    Animation([a.PATROL_FRAMES[2]], 1),
                    Animation([a.PATROL_FRAMES[1]], 1),
                    Animation([a.PATROL_FRAMES[0]], 1),
                    Animation([a.PATROL_FRAMES[7]], 1),
                    Animation([a.PATROL_FRAMES[6]], 1),
                    Animation([a.PATROL_FRAMES[5]], 1),
                ],
                "walk": [
                    Animation(a.PATROL_FRAMES[32:40], 0.07),
                    Animation(a.PATROL_FRAMES[16:24], 0.07),
                    Animation(a.PATROL_FRAMES[8:16], 0.07),
                    Animation(a.PATROL_FRAMES[24:32], 0.07),
                ],
            }
        )
        animator_initialise(self.animator, animation_mapping)
        self.direction = Direction.E
        self.facing = 0
        self.path: list[pygame.Vector2] = []
        self.active_point = 0
        self.sight_radius = 96
        self.sight_angle = 10

    def get_hitbox(self) -> pygame.Rect:
        return pygame.Rect(self.motion.position.x + 12, self.motion.position.y + 28, 8, 4)

    def update(self, dt: float, player: Player, camera: Camera) -> None:
        if len(self.path) > 0:
            target = self.path[self.active_point]
            dist = target - self.motion.position
            target_facing = dist.angle_to(pygame.Vector2(1, 0))
            turn = (target_facing - self.facing) % 360
            if turn > 180:
                turn -= 360
            # not facing in correct direction, turn
            if abs(turn) > 1:
                if abs(turn) > 5:
                    self.facing -= 5
                else:
                    self.facing = target_facing
            # follow path
            elif dist.magnitude() > 1:
                _enemy_follow(self, dist, 100)
            # use next point
            else:
                self.motion.position = target.copy()
                self.motion.velocity = pygame.Vector2()
                self.active_point = (self.active_point + 1) % len(self.path)
            self.direction = direction_from_angle(self.facing)

        # collision
        prect = player_rect(player.motion)
        if prect.colliderect(self.get_hitbox()):
            player_caught(player, camera)
        elif point_in_ellipse(
            *prect.center,
            self.motion.position.x + 16,
            self.motion.position.y + 16,
            self.sight_radius,
            self.sight_radius * c.PERSPECTIVE,
        ):
            pdist = pygame.Vector2(*prect.center) - pygame.Vector2(
                self.motion.position.x + 16, self.motion.position.y + 16
            )
            theta = (pdist.angle_to(pygame.Vector2(1, 0)) - self.facing) % 360
            if theta < self.sight_angle / 2 + 1 or theta > 360 - (self.sight_angle / 2 + 1):
                player_caught(player, camera)

        # animation
        if self.motion.velocity.magnitude_squared() > 0:
            animator_switch_animation(self.animator, f"walk_{self.direction}")
        else:
            animator_switch_animation(self.animator, f"idle_{self.direction}")
        animator_update(self.animator, dt)

        motion_update(self.motion, dt)

    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
        render_position = self.motion.position
        if layer < RenderLayer.PLAYER:
            sight_left = pygame.Vector2(self.sight_radius, 0).rotate(
                self.facing - self.sight_angle // 2
            )
            sight_right = pygame.Vector2(self.sight_radius, 0).rotate(
                self.facing + self.sight_angle // 2
            )
            sight = pygame.Surface(
                (self.sight_radius * 2, self.sight_radius * 2 * c.PERSPECTIVE),
                pygame.SRCALPHA,
            )
            pygame.draw.polygon(
                sight,
                (162, 48, 0, 96),
                [
                    (sight.get_width() // 2, sight.get_height() // 2),
                    (
                        sight.get_width() // 2 + sight_left.x,
                        sight.get_height() // 2 - sight_left.y * c.PERSPECTIVE,
                    ),
                    (
                        sight.get_width() // 2 + sight_right.x,
                        sight.get_height() // 2 - sight_right.y * c.PERSPECTIVE,
                    ),
                ],
            )
            surface.blit(
                sight,
                camera_to_screen_shake(
                    camera,
                    render_position[0] + 16 - sight.get_width() // 2,
                    render_position[1] + 16 - sight.get_height() // 2,
                ),
            )
        if abs(layer) <= RenderLayer.PLAYER_FG:
            surface.blit(
                animator_get_frame(self.animator),
                camera_to_screen_shake(camera, *render_position),
            )


class SpotlightEnemy(Enemy):
    def __init__(self):
        super().__init__()
        self.path: list[pygame.Vector2] = []
        self.active_point = 0
        self.light_radius = 48

    def update(self, dt: float, player: Player, camera: Camera) -> None:
        if len(self.path) > 0:
            target = self.path[self.active_point]
            dist = target - self.motion.position
            # follow path
            if dist.magnitude() > 1:
                _enemy_follow(self, dist, 50)
            # use next point
            else:
                self.motion.position = target.copy()
                self.motion.velocity = pygame.Vector2()
                self.active_point = (self.active_point + 1) % len(self.path)

        # collision
        prect = player_rect(player.motion)
        if point_in_ellipse(
            *prect.center,
            *self.motion.position,
            self.light_radius - 4,
            (self.light_radius - 4) * c.PERSPECTIVE,
        ):
            player_caught(player, camera)

        motion_update(self.motion, dt)

    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
        if layer > RenderLayer.PLAYER:
            render_position = (
                self.motion.position.x - self.light_radius,
                self.motion.position.y - self.light_radius * c.PERSPECTIVE,
            )
            sprite = pygame.Surface(
                (self.light_radius * 2, self.light_radius * 2 * c.PERSPECTIVE),
                pygame.SRCALPHA,
            )
            pygame.draw.ellipse(sprite, (255, 255, 0, 96), sprite.get_rect())
            surface.blit(sprite, camera_to_screen_shake(camera, *render_position))


class SpikeTrapEnemy(Enemy):
    def __init__(self):
        super().__init__()
        self.stepped_on = False
        self.activated = False

    def get_hitbox(self) -> pygame.Rect:
        return pygame.Rect(*self.motion.position, 32, 16)

    def update(self, dt: float, player: Player, camera: Camera) -> None:
        if player.z_position == 0:
            prect = player_rect(player.motion)
            prev_stepped = self.stepped_on
            self.stepped_on = prect.colliderect(self.get_hitbox())
            if self.stepped_on and not prev_stepped:
                if not self.activated:
                    self.activated = True
                else:
                    player_caught(player, camera)

    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
        if layer < RenderLayer.PLAYER:
            render_position = self.motion.position
            surface.blit(
                a.DEBUG_SPRITE_SMALL,
                camera_to_screen_shake(camera, *render_position),
                (0, 0, 32, 16),
            )


def enemy_update(enemy: Enemy, dt: float, player: Player, camera: Camera):
    enemy.update(dt, player, camera)


def enemy_render(enemy: Enemy, surface: pygame.Surface, camera: Camera, layer: RenderLayer):
    enemy.render(surface, camera, layer)

    if c.DEBUG_HITBOXES and layer > RenderLayer.PLAYER:
        hitbox = enemy.get_hitbox()
        if hitbox:
            pygame.draw.rect(surface, c.RED, camera_to_screen_shake_rect(camera, *hitbox), 1)
