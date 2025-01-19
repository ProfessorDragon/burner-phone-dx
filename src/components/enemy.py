from dataclasses import dataclass

import pygame
import core.assets as a
import core.constants as c
from components.animation import Animator
from components.camera import Camera, camera_to_screen_shake
from components.motion import Motion, Vector2, motion_update


class PatrolEnemy:
    def __init__(self):
        self.motion = Motion.empty()
        self.animator = Animator()
        self.facing = 0
        self.path: list[Vector2] = []
        self.active_point = 0


def enemy_update(enemy: PatrolEnemy, dt: float):
    if len(enemy.path) > 0:
        target = enemy.path[enemy.active_point]
        dist = target - enemy.motion.position
        target_facing = dist.angle_to(Vector2())
        turn = (target_facing - enemy.facing + 180) % 360 - 180  # will always turn clockwise
        # not facing in correct direction, turn
        if turn != 0:
            if abs(turn) < 5:
                enemy.facing = target_facing
            else:
                enemy.facing += turn / abs(turn) * 5
        # follow path
        elif dist.magnitude() > 1:
            enemy.motion.velocity = dist.normalize() * 50
        # use next point
        else:
            enemy.motion.position = target.copy()
            enemy.motion.velocity = Vector2()
            enemy.active_point = (enemy.active_point + 1) % len(enemy.path)

    motion_update(enemy.motion, dt)


def enemy_render(enemy: PatrolEnemy, surface: pygame.Surface, camera: Camera):
    sprite = a.DEBUG_SPRITE_SMALL
    render_position = (enemy.motion.position.x, enemy.motion.position.y)
    center_position = camera_to_screen_shake(
        camera,
        render_position[0] + 16,
        render_position[1] + 16,
    )
    sight_left = Vector2(96, 0).rotate(enemy.facing - 5)
    sight_right = Vector2(96, 0).rotate(enemy.facing + 5)
    # halve the y to account for perspective
    pygame.draw.polygon(
        surface,
        c.RED,
        [
            center_position,
            (center_position[0] + sight_left.x, center_position[1] - sight_left.y // 2),
            (center_position[0] + sight_right.x, center_position[1] - sight_right.y // 2),
        ],
    )
    surface.blit(sprite, camera_to_screen_shake(camera, *render_position), (0, 0, 32, 32))
