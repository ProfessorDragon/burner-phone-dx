from dataclasses import dataclass
from enum import IntEnum, auto
import pygame

from components.audio import AudioChannel, play_sound
from components.dialogue import DialogueSystem, dialogue_execute_script_scene
from components.entities.entity_util import render_shadow
from components.tiles import grid_collision_rect
from components.timer import Timer, timer_reset
import core.input as t
import core.assets as a
import core.constants as c
from components.motion import (
    Direction,
    Motion,
    angle_from_direction,
    direction_from_delta,
    motion_update,
)
from components.camera import (
    Camera,
    camera_to_screen,
    camera_to_screen_shake,
    camera_to_screen_shake_rect,
)
from components.animation import (
    Animator,
    Animation,
    animator_reset,
    animator_switch_animation,
    animator_update,
    animator_get_frame,
    animator_initialise,
    directional_animation_mapping,
    walking_animation_mapping,
)


class MainStoryProgress(IntEnum):
    INTRO = 0
    COMMS = auto()
    HALFWAY = auto()


@dataclass
class PlayerProgression:
    checkpoint: pygame.Vector2 = None
    main_story: MainStoryProgress = MainStoryProgress.INTRO


class PlayerCaughtStyle(IntEnum):
    NONE = 0
    SIGHT = auto()
    HOLE = auto()
    ZOMBIE = auto()


class Player:
    def __init__(self, spawn_position: pygame.Vector2):
        self.motion = Motion.empty()
        self.motion.position = spawn_position
        self.z_position = 0
        self.z_velocity = 0
        self.animator = Animator()
        animation_mapping = walking_animation_mapping(a.PLAYER_FRAMES)
        animation_mapping.update(
            directional_animation_mapping(
                {
                    "jump": [
                        Animation(a.PLAYER_FRAMES[55:60], 0.08, False),
                        Animation(a.PLAYER_FRAMES[45:50], 0.08, False),
                        Animation(a.PLAYER_FRAMES[40:45], 0.08, False),
                        Animation(a.PLAYER_FRAMES[50:55], 0.08, False),
                    ],
                }
            )
        )
        animator_initialise(self.animator, animation_mapping)

        self.direction = Direction.E
        self.progression = PlayerProgression()
        self.progression.checkpoint = self.motion.position.copy()
        self.caught_timer = Timer()  # resets scene and player when completed
        self.caught_style = PlayerCaughtStyle.NONE
        self.interact_scene = None  # if set, runs the dialogue script scene when jump is pressed

        # consts
        self.walk_speed = 150
        self.jump_velocity = 120


def player_rect(motion: Motion):
    # round for accurate collision.
    return pygame.Rect(round(motion.position.x) + 11, round(motion.position.y) + 28, 10, 4)


def _player_movement(player: Player, dt: float, action_buffer: t.InputBuffer):
    # lateral movement
    dx = t.is_held(action_buffer, t.Action.RIGHT) - t.is_held(action_buffer, t.Action.LEFT)
    dy = t.is_held(action_buffer, t.Action.DOWN) - t.is_held(action_buffer, t.Action.UP)
    if dx != 0 and dy != 0:
        # trig shortcut, normalizing the vector
        dx *= 0.707
        dy *= 0.707

    player.motion.velocity.x = dx * player.walk_speed
    player.motion.velocity.y = dy * player.walk_speed * c.PERSPECTIVE
    if player.z_position > 0:
        pass  # maybe reduce air control if jumping?


def _player_collision(
    player: Player, dt: float, grid_collision: set[tuple[int, int]], walls: list[pygame.Rect]
):
    # I'VE PLAYED THESE GAMES BEFOREEEE
    # horizontal collision
    if player.motion.velocity.x != 0:
        m = player.motion.copy()
        m.velocity.y = 0
        motion_update(m, dt)
        prect = player_rect(m)
        top, bottom = prect.top // c.TILE_SIZE, prect.bottom // c.TILE_SIZE
        left, right = prect.left // c.TILE_SIZE, prect.right // c.TILE_SIZE
        walls_with_grid = walls + [
            grid_collision_rect(grid_collision, right, top),
            grid_collision_rect(grid_collision, right, bottom),
            grid_collision_rect(grid_collision, left, top),
            grid_collision_rect(grid_collision, left, bottom),
        ]
        for wall in walls_with_grid:
            if wall is not None and prect.colliderect(wall):
                if m.velocity.x > 0:
                    player.motion.position.x = wall.left - prect.w - 11
                else:
                    player.motion.position.x = wall.right - 11
                player.motion.velocity.x = 0

    # vertical collision
    if player.motion.velocity.y != 0:
        m = player.motion.copy()
        m.velocity.x = 0
        motion_update(m, dt)
        prect = player_rect(m)
        top, bottom = prect.top // c.TILE_SIZE, prect.bottom // c.TILE_SIZE
        left, right = prect.left // c.TILE_SIZE, prect.right // c.TILE_SIZE
        walls_with_grid = walls + [
            grid_collision_rect(grid_collision, right, top),
            grid_collision_rect(grid_collision, left, top),
            grid_collision_rect(grid_collision, right, bottom),
            grid_collision_rect(grid_collision, left, bottom),
        ]
        for wall in walls_with_grid:
            if wall is not None and prect.colliderect(wall):
                if m.velocity.y > 0:
                    player.motion.position.y = wall.top - 32
                else:
                    player.motion.position.y = wall.bottom - 32 + prect.h
                player.motion.velocity.y = 0


def player_update(
    player: Player,
    dt: float,
    action_buffer: t.InputBuffer,
    grid_collision: set[tuple[int, int]],
    walls: list[pygame.Rect],
    dialogue: DialogueSystem,
) -> None:

    # movement
    if player.caught_timer.remaining <= 0:
        _player_movement(player, dt, action_buffer)
        if t.is_pressed(action_buffer, t.Action.A):
            # interact
            if player.interact_scene is not None:
                player.direction = Direction.N
                dialogue_execute_script_scene(dialogue, player.interact_scene)
            # jump
            elif player.z_position == 0:
                player.z_velocity = -player.jump_velocity
                animator_reset(player.animator)
                play_sound(AudioChannel.PLAYER, a.JUMP)

    # collision
    dx, dy = player.motion.velocity
    _player_collision(player, dt, grid_collision, walls)

    motion_update(player.motion, dt)
    player.z_velocity += 600 * dt
    player.z_position = min(player.z_position + player.z_velocity * dt, 0)

    if dx != 0 or dy != 0:
        player.direction = direction_from_delta(dx, dy)
    if player.z_position < 0:
        animator_switch_animation(player.animator, f"jump_{player.direction}")
    elif dx != 0 or dy != 0:
        animator_switch_animation(player.animator, f"walk_{player.direction}")
    else:
        animator_switch_animation(player.animator, f"idle_{player.direction}")

    prev_frame = player.animator.frame_index
    animator_update(player.animator, dt)
    if player.z_position >= 0 and (dx != 0 or dy != 0):
        step_frames = (7, 3)
        if prev_frame not in step_frames and player.animator.frame_index in step_frames:
            play_sound(
                AudioChannel.PLAYER,
                a.FOOTSTEPS[0 if player.animator.frame_index == step_frames[0] else 1],
            )


def player_caught(player: Player, camera: Camera, style: PlayerCaughtStyle) -> None:
    if player.caught_timer.remaining > 0:
        return
    timer_reset(player.caught_timer, 0.5)
    player.caught_style = style
    player.motion.velocity = pygame.Vector2()
    camera.trauma = 0.4
    if style == PlayerCaughtStyle.HOLE:
        play_sound(AudioChannel.PLAYER, a.CAUGHT_HOLE)
    else:
        play_sound(AudioChannel.PLAYER, a.CAUGHT_SIGHT)


def player_reset(player: Player) -> None:
    player.motion.position = player.progression.checkpoint.copy()
    player.motion.velocity = pygame.Vector2()
    player.motion.acceleration = pygame.Vector2()
    player.caught_style = PlayerCaughtStyle.NONE


def player_render(player: Player, surface: pygame.Surface, camera: Camera) -> None:
    frame = animator_get_frame(player.animator)

    # caught in hole
    if player.caught_timer.remaining > 0:
        if player.caught_style == PlayerCaughtStyle.HOLE:
            px = player.caught_timer.elapsed * 32
            scaled_frame = pygame.transform.smoothscale(frame, (32 - px, 32 - px))
            scaled_frame.fill(
                tuple(128 * player.caught_timer.elapsed for _ in range(3)),
                special_flags=pygame.BLEND_RGB_SUB,
            )
            render_position = player.motion.position + pygame.Vector2(px / 2, px / 2)
            render_position += pygame.Vector2(px * 0.25, 0).rotate(
                -angle_from_direction(player.direction)
            )
            render_position.y += px * 0.5
            surface.blit(scaled_frame, camera_to_screen_shake(camera, *render_position))
            return

    # normal rendering
    render_shadow(surface, camera, player.motion, player.direction, player.z_position)
    surface.blit(
        frame,
        camera_to_screen_shake(
            camera, player.motion.position.x, player.motion.position.y + player.z_position
        ),
    )


def player_render_overlays(player: Player, surface: pygame.Surface, camera: Camera) -> None:
    # caught by sight or zombie
    if player.caught_timer.remaining > 0:
        alert = None
        y_offset = 0
        if player.caught_style == PlayerCaughtStyle.SIGHT:
            alert = a.DEBUG_FONT.render("!!", False, c.RED)
            y_offset = -8
        elif player.caught_style == PlayerCaughtStyle.ZOMBIE:
            alert = a.DEBUG_FONT.render("!!", False, c.GREEN)
            y_offset = 12
        if alert is not None:
            surface.blit(
                alert,
                camera_to_screen(
                    camera,
                    player.motion.position.x + 16 - alert.get_width() // 2,
                    player.motion.position.y + y_offset + player.caught_timer.remaining * 8,
                ),
            )

    # hitbox
    if c.DEBUG_HITBOXES:
        pygame.draw.rect(
            surface,
            c.CYAN,
            camera_to_screen_shake_rect(camera, *player_rect(player.motion)),
            1,
        )
