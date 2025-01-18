from dataclasses import dataclass

import pygame

import core.input as i
import core.constants as c
import core.assets as a
from components.motion import Motion, motion_update
from components.camera import Camera, camera_to_screen_shake
from components.animation import (
    Animator, Animation, animator_switch_animation, animator_update,
    animator_get_frame, animator_initialise
)


@dataclass(slots=True)
class Player:
    motion: Motion
    animator: Animator = None
    direction: int = 1


def player_initialise() -> Player:
    player = Player(Motion.empty())
    player.animator = Animator()
    animation_mapping = {
        'idle_left': Animation([a.PLAYER_FRAMES_LEFT[0]], 1),
        'walk_left': Animation(a.PLAYER_FRAMES_LEFT, 0.15),
        'idle_right': Animation([a.PLAYER_FRAMES_RIGHT[0]], 1),
        'walk_right': Animation(a.PLAYER_FRAMES_RIGHT, 0.15),
    }
    animator_initialise(player.animator, animation_mapping, 'idle_right')
    return player


def player_rect(motion: Motion):
    return pygame.Rect(*motion.position, 16, c.TILE_SIZE // 2)


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
        # trig shortcut, normalizing the vector
        dx *= 0.707
        dy *= 0.707

    # jumping
    # if input.is_pressed(action_buffer, input.Action.A):
    #     player.motion.acceleration.z = 1000

    # collision!!
    # split the horizontal and vertical components
    player.motion.velocity.x = dx
    player.motion.velocity.y = dy

    # horizontal collision
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

    # Handle animation transitions
    if dx > 0 or dy != 0 and player.direction == 1:
        player.direction = 1
        animator_switch_animation(player.animator, 'walk_right')
    if dx < 0 or dy != 0 and player.direction == -1:
        player.direction = -1
        animator_switch_animation(player.animator, 'walk_left')
    if dx == 0 and dy == 0:
        if player.direction == 1:
            animator_switch_animation(player.animator, 'idle_right')
        elif player.direction == -1:
            animator_switch_animation(player.animator, 'idle_left')

    motion_update(player.motion, dt)
    animator_update(player.animator, dt)


def player_render(
    player: Player, surface: pygame.Surface, camera: Camera
) -> None:
    render_position = (player.motion.position.x - 8,
                       player.motion.position.y - 16)
    surface.blit(
        animator_get_frame(player.animator),
        camera_to_screen_shake(camera, *render_position)
    )
