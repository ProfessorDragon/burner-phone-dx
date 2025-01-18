from dataclasses import dataclass

import pygame

import core.input as i
import core.constants as c
from components.motion import Motion, Motion3D, motion3d_update, motion_update


@dataclass(slots=True)
class Player:
    motion: Motion


def player_rect(motion: Motion):
    return pygame.Rect(*motion.position, c.TILE_SIZE, c.TILE_SIZE)


def player_update(
    player: Player,
    dt: float,
    action_buffer: i.InputBuffer,
    walls: list[pygame.Rect],
) -> None:
    # lateral movement
    dx = (
        i.is_held(action_buffer, i.Action.RIGHT)
        - i.is_held(action_buffer, i.Action.LEFT)
    ) * 200
    dy = (
        i.is_held(action_buffer, i.Action.DOWN)
        - i.is_held(action_buffer, i.Action.UP)
    ) * 200
    if dx != 0 and dy != 0:
        # trig shortcut, multiply by 1/sqrt(2) for accurate diagonal movement speeds
        dx *= 0.707
        dy *= 0.707

    # jumping
    # if input.is_pressed(action_buffer, input.Action.A):
    #     player.motion.acceleration.z = 1000

    # collision!!
    # splitting the horizontal and vertical components is the best method i've found to date
    player.motion.velocity.x = dx
    player.motion.velocity.y = dy

    # horizontal collision
    # I'VE PLAYED THESE GAMES BEFORE!!!
    if player.motion.velocity.x != 0:
        m = player.motion.copy()
        m.velocity.y = 0
        motion_update(m, dt)
        rect = player_rect(m)
        for wall in walls:
            if rect.colliderect(wall):
                if m.velocity.x > 0:
                    player.motion.position.x = wall.left - rect.w
                else:
                    player.motion.position.x = wall.right
                player.motion.velocity.x = 0
                break

    # vertical collision
    # I'VE PLAYED THESE GAMES BEFOREEEEE
    if player.motion.velocity.y != 0:
        m = player.motion.copy()
        m.velocity.x = 0
        motion_update(m, dt)
        rect = player_rect(m)
        for wall in walls:
            if rect.colliderect(wall):
                if m.velocity.y > 0:
                    player.motion.position.y = wall.top - rect.h
                else:
                    player.motion.position.y = wall.bottom
                player.motion.velocity.y = 0
                break

    motion_update(player.motion, dt)
