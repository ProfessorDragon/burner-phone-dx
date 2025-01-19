from abc import ABC
from enum import IntEnum, auto
from math import cos, radians

import pygame
from components.player import Player, player_caught, player_rect
import core.assets as a
import core.constants as c
from components.animation import Animator
from components.camera import Camera, camera_to_screen_shake
from components.motion import Motion, motion_update
from scenes.scene import RenderLayer
from utilities.math import point_in_ellipse


class EnemyType(IntEnum):
    NONE = 0  # never used
    PATROL = auto()
    SPOTLIGHT = auto()


# base class
class Enemy(ABC):
    def __init__(self):
        self.motion = Motion.empty()
        self.type = EnemyType.NONE


class PatrolEnemy(Enemy):
    def __init__(self):
        super().__init__()
        self.type = EnemyType.PATROL
        self.animator = Animator()
        self.facing = 0
        self.path: list[pygame.Vector2] = []
        self.active_point = 0
        self.sight_radius = 96
        self.sight_angle = 10


class SpotlightEnemy(Enemy):
    def __init__(self):
        super().__init__()
        self.type = EnemyType.SPOTLIGHT
        self.path: list[pygame.Vector2] = []
        self.active_point = 0
        self.light_radius = 48


def _enemy_follow(enemy: Enemy, dist: pygame.Vector2, speed: float):
    enemy.motion.velocity = dist.normalize() * speed
    enemy.motion.velocity *= (
        (0.5 - c.PERSPECTIVE / 2) * cos(2 * radians(dist.angle_to(pygame.Vector2(1, 0))))
        + 0.5
        + c.PERSPECTIVE / 2
    )


def enemy_update(enemy: Enemy, dt: float, player: Player):
    prect = player_rect(player.motion)

    match enemy.type:

        case EnemyType.PATROL:
            if len(enemy.path) > 0:
                target = enemy.path[enemy.active_point]
                dist = target - enemy.motion.position
                target_facing = dist.angle_to(pygame.Vector2(1, 0))
                turn = (target_facing - enemy.facing) % 360
                if turn > 180:
                    turn -= 360
                # not facing in correct direction, turn
                if abs(turn) > 1:
                    if abs(turn) > 5:
                        enemy.facing -= 5
                    else:
                        enemy.facing = target_facing
                # follow path
                elif dist.magnitude() > 1:
                    _enemy_follow(enemy, dist, 100)
                # use next point
                else:
                    enemy.motion.position = target.copy()
                    enemy.motion.velocity = pygame.Vector2()
                    enemy.active_point = (enemy.active_point + 1) % len(enemy.path)
            if prect.colliderect(
                pygame.Rect(enemy.motion.position.x, enemy.motion.position.y - 32, 32, 32)
            ):
                player_caught(player)
            elif point_in_ellipse(
                *prect.center,
                enemy.motion.position.x + 16,
                enemy.motion.position.y - 16,
                enemy.sight_radius,
                enemy.sight_radius * c.PERSPECTIVE,
            ):
                pdist = pygame.Vector2(*prect.center) - pygame.Vector2(
                    enemy.motion.position.x, enemy.motion.position.y - 16
                )
                pangle = pdist.angle_to(pygame.Vector2(1, 0)) - enemy.facing
                if abs(pangle) <= enemy.sight_angle * 0.6:
                    player_caught(player)

        case EnemyType.SPOTLIGHT:
            if len(enemy.path) > 0:
                target = enemy.path[enemy.active_point]
                dist = target - enemy.motion.position
                # follow path
                if dist.magnitude() > 1:
                    _enemy_follow(enemy, dist, 50)
                # use next point
                else:
                    enemy.motion.position = target.copy()
                    enemy.motion.velocity = pygame.Vector2()
                    enemy.active_point = (enemy.active_point + 1) % len(enemy.path)
            if point_in_ellipse(
                *prect.center,
                *enemy.motion.position,
                enemy.light_radius + 8,
                (enemy.light_radius + 8) * c.PERSPECTIVE,
            ):
                player_caught(player)

    motion_update(enemy.motion, dt)


def enemy_render(enemy: Enemy, surface: pygame.Surface, camera: Camera, layer: RenderLayer):

    match enemy.type:

        case EnemyType.PATROL:
            render_position = (enemy.motion.position.x, enemy.motion.position.y - 32)
            if layer < RenderLayer.PLAYER:
                sight_left = pygame.Vector2(enemy.sight_radius, 0).rotate(
                    enemy.facing - enemy.sight_angle // 2
                )
                sight_right = pygame.Vector2(enemy.sight_radius, 0).rotate(
                    enemy.facing + enemy.sight_angle // 2
                )
                sight = pygame.Surface(
                    (enemy.sight_radius * 2, enemy.sight_radius * 2 * c.PERSPECTIVE),
                    pygame.SRCALPHA,
                )
                pygame.draw.polygon(
                    sight,
                    (255, 0, 0, 96),
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
                    a.DEBUG_SPRITE_SMALL,
                    camera_to_screen_shake(camera, *render_position),
                    (0, 0, 32, 32),
                )

        case EnemyType.SPOTLIGHT:
            if layer > RenderLayer.PLAYER:
                render_position = (
                    enemy.motion.position.x - enemy.light_radius,
                    enemy.motion.position.y - enemy.light_radius * c.PERSPECTIVE,
                )
                sprite = pygame.Surface(
                    (enemy.light_radius * 2, enemy.light_radius * 2 * c.PERSPECTIVE),
                    pygame.SRCALPHA,
                )
                pygame.draw.ellipse(sprite, (255, 255, 0, 96), sprite.get_rect())
                surface.blit(sprite, camera_to_screen_shake(camera, *render_position))
