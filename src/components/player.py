import pygame

import core.input as t
import core.assets as a
import core.constants as c
from components.motion import Direction, Motion, motion_update
from components.camera import Camera, camera_to_screen, camera_to_screen_shake
from components.animation import (
    Animator,
    Animation,
    animator_switch_animation,
    animator_update,
    animator_get_frame,
    animator_initialise,
    directional_animation_mapping,
)


class Player:
    def __init__(self):
        self.motion = Motion.empty()
        self.animator = Animator()
        self.direction = Direction.E
        self.walk_speed = 150
        self.caught_timer = 0


def player_initialise() -> Player:
    player = Player()
    animation_mapping = directional_animation_mapping(
        {
            "idle": [
                Animation([a.PLAYER_FRAMES[4]], 1),
                Animation([a.PLAYER_FRAMES[3]], 1),
                Animation([a.PLAYER_FRAMES[2]], 1),
                Animation([a.PLAYER_FRAMES[1]], 1),
                Animation([a.PLAYER_FRAMES[0]], 1),
                Animation([a.PLAYER_FRAMES[7]], 1),
                Animation([a.PLAYER_FRAMES[6]], 1),
                Animation([a.PLAYER_FRAMES[5]], 1),
            ],
            "walk": [
                Animation(a.PLAYER_FRAMES[32:40], 0.07),
                Animation(a.PLAYER_FRAMES[16:24], 0.07),
                Animation(a.PLAYER_FRAMES[8:16], 0.07),
                Animation(a.PLAYER_FRAMES[24:32], 0.07),
            ],
        }
    )
    animator_initialise(player.animator, animation_mapping)
    return player


def player_rect(motion: Motion):
    # round for accurate collision.
    return pygame.Rect(round(motion.position.x), round(motion.position.y), 16, 8)


def _player_movement(player: Player, dt: float, action_buffer: t.InputBuffer):
    # lateral movement
    dx = (
        t.is_held(action_buffer, t.Action.RIGHT) - t.is_held(action_buffer, t.Action.LEFT)
    ) * player.walk_speed
    dy = (
        t.is_held(action_buffer, t.Action.DOWN) - t.is_held(action_buffer, t.Action.UP)
    ) * player.walk_speed
    if dx != 0 and dy != 0:
        # trig shortcut, normalizing the vector
        dx *= 0.707
        dy *= 0.707

    # jumping
    # if input.is_pressed(action_buffer, input.Action.A):
    #     player.motion.acceleration.z = 1000

    player.motion.velocity.x = dx
    player.motion.velocity.y = dy * c.PERSPECTIVE


def _player_collision(player: Player, dt: float, walls: list[pygame.Rect]):
    # I'VE PLAYED THESE GAMES BEFOREEEE
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


def player_update(
    player: Player,
    dt: float,
    action_buffer: t.InputBuffer,
    walls: list[pygame.Rect],
) -> None:

    if player.caught_timer <= 0:
        _player_movement(player, dt, action_buffer)
    else:
        player.caught_timer -= dt
        if player.caught_timer <= 0:
            player_kill(player)
            return

    dx, dy = player.motion.velocity
    _player_collision(player, dt, walls)

    # Handle animation transitions
    if dx != 0 or dy != 0:
        if dx > 0:
            if dy > 0:
                player.direction = Direction.SE
            elif dy < 0:
                player.direction = Direction.NE
            else:
                player.direction = Direction.E
        elif dx < 0:
            if dy > 0:
                player.direction = Direction.SW
            elif dy < 0:
                player.direction = Direction.NW
            else:
                player.direction = Direction.W
        elif dy > 0:
            player.direction = Direction.S
        else:
            player.direction = Direction.N
        animator_switch_animation(player.animator, f"walk_{player.direction}")
    else:
        animator_switch_animation(player.animator, f"idle_{player.direction}")

    motion_update(player.motion, dt)
    animator_update(player.animator, dt)


def player_caught(player: Player):
    if player.caught_timer > 0:
        return
    # todo: add screen shake here. how? idk, aside from passing the camera object through a lengthy chain of args...
    player.caught_timer = 0.5
    player.motion.velocity = pygame.Vector2()


def player_kill(player: Player):
    player.motion.position = pygame.Vector2()
    player.motion.velocity = pygame.Vector2()


def player_render(player: Player, surface: pygame.Surface, camera: Camera) -> None:
    frame = animator_get_frame(player.animator)
    render_position = (player.motion.position.x - 8, player.motion.position.y - 24)

    # if we want a 'real' shadow:
    # shadow = pygame.transform.flip(pygame.transform.scale_by(frame, (1, 0.5)), False, True)
    # surface.blit(
    #     shadow,
    #     camera_to_screen_shake(camera, render_position[0], render_position[1] + frame.get_height()),
    # )

    shadow = pygame.Surface((frame.get_width(), 6), pygame.SRCALPHA)
    pygame.draw.ellipse(
        shadow,
        (0, 0, 0, 50),
        pygame.Rect(5, 0, frame.get_width() - 10, 6),
    )
    surface.blit(
        shadow,
        camera_to_screen_shake(
            camera, render_position[0], render_position[1] + frame.get_height() - 3
        ),
    )
    surface.blit(
        frame,
        camera_to_screen_shake(camera, *render_position),
    )

    # caught alert
    if player.caught_timer > 0:
        alert = a.DEBUG_FONT.render("!!", False, c.RED)
        surface.blit(
            alert,
            camera_to_screen(
                camera,
                render_position[0] + frame.get_width() // 2 - alert.get_width() // 2,
                render_position[1] - 16 + player.caught_timer * 8,
            ),
        )

    # hitbox
    hitbox = player_rect(player.motion)
    pygame.draw.rect(
        surface,
        c.CYAN,
        (*camera_to_screen_shake(camera, hitbox[0], hitbox[1]), hitbox[2], hitbox[3]),
        1,
    )
