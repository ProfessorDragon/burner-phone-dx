from dataclasses import dataclass
from enum import IntEnum, auto

import pygame

import core.input as t
import core.assets as a
from components.motion import Motion, motion_update
from components.camera import Camera, camera_to_screen_shake
from components.animation import (
    Animator,
    Animation,
    animator_switch_animation,
    animator_update,
    animator_get_frame,
    animator_initialise,
)


class Direction(IntEnum):
    N = 0
    NE = auto()
    E = auto()
    SE = auto()
    S = auto()
    SW = auto()
    W = auto()
    NW = auto()


@dataclass(slots=True)
class Player:
    motion: Motion
    animator: Animator = None
    direction: IntEnum = Direction.E


def player_initialise() -> Player:
    player = Player(Motion.empty())
    player.animator = Animator()
    animation_mapping = {
        "idle_left": Animation([a.PLAYER_FRAMES_LEFT[0]], 1),
        "idle_right": Animation([a.PLAYER_FRAMES_RIGHT[0]], 1),
        "idle_down": Animation([a.PLAYER_FRAMES_RIGHT[0]], 1),
        "idle_up": Animation([a.PLAYER_FRAMES_RIGHT[0]], 1),
        "walk_left": Animation(a.PLAYER_FRAMES_LEFT, 0.1),
        "walk_right": Animation(a.PLAYER_FRAMES_RIGHT, 0.1),
        "walk_down": Animation(a.PLAYER_FRAMES_RIGHT, 0.1),
        "walk_up": Animation(a.PLAYER_FRAMES_RIGHT, 0.1),
    }
    animator_initialise(player.animator, animation_mapping, "idle_right")
    return player


def player_rect(motion: Motion):
    # round for accurate collision.
    return pygame.Rect(round(motion.position.x), round(motion.position.y), 16, 8)


def player_update(
    player: Player,
    dt: float,
    action_buffer: t.InputBuffer,
    walls: list[pygame.Rect],
) -> None:
    # lateral movement
    dx = (t.is_held(action_buffer, t.Action.RIGHT) - t.is_held(action_buffer, t.Action.LEFT)) * 200
    dy = (t.is_held(action_buffer, t.Action.DOWN) - t.is_held(action_buffer, t.Action.UP)) * 200
    if dx != 0 and dy != 0:
        # trig shortcut, normalizing the vector
        dx *= 0.707
        dy *= 0.707

    # jumping
    # if input.is_pressed(action_buffer, input.Action.A):
    #     player.motion.acceleration.z = 1000

    # collision!!
    # I'VE PLAYED THESE GAMES BEFOREEEE
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

    # Handle animation transitions
    if dx > 0:
        player.direction = Direction.E
        animator_switch_animation(player.animator, "walk_right")
    elif dx < 0:
        player.direction = Direction.W
        animator_switch_animation(player.animator, "walk_left")
    elif dy > 0:
        player.direction = Direction.S
        animator_switch_animation(player.animator, "walk_down")
    elif dy < 0:
        player.direction = Direction.N
        animator_switch_animation(player.animator, "walk_right")
    elif player.direction == Direction.E:
        animator_switch_animation(player.animator, "idle_right")
    elif player.direction == Direction.W:
        animator_switch_animation(player.animator, "idle_left")
    elif player.direction == Direction.S:
        animator_switch_animation(player.animator, "idle_down")
    elif player.direction == Direction.N:
        animator_switch_animation(player.animator, "idle_up")

    motion_update(player.motion, dt)
    animator_update(player.animator, dt)


def player_render(player: Player, surface: pygame.Surface, camera: Camera) -> None:
    render_position = (player.motion.position.x - 8, player.motion.position.y - 24)
    surface.blit(
        animator_get_frame(player.animator),
        camera_to_screen_shake(camera, *render_position),
    )
