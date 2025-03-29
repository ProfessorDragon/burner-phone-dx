from dataclasses import dataclass
from enum import IntEnum, auto
import pygame

import core.assets as a
import core.constants as c
import core.input as t
import core.globals as g
from components.audio import AudioChannel, play_sound
from components.dialogue import (
    DialogueSystem,
    dialogue_execute_script_scene,
    dialogue_has_executed_scene,
)
from components.entities.entity_util import render_shadow
from components.tile import grid_collision_rect
from components.timer import Timer, timer_reset, timer_update
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
    OUTDOORS = auto()
    HALFWAY = auto()
    LAB = auto()
    FINALE = auto()
    FINALE_NO_MOVEMENT = auto()


@dataclass
class PlayerProgression:
    checkpoint: pygame.Vector2 = None
    main_story: MainStoryProgress = MainStoryProgress.INTRO
    activated_buttons: set[str] = None
    checkpoint_buttons: set[str] = None
    unlocked_camera_boundaries: set[str] = None


@dataclass
class PlayerInteraction:
    scene_name: str | None
    requires_input: bool
    direction: Direction = None


class PlayerCaughtStyle(IntEnum):
    NONE = 0
    SIGHT = auto()
    HOLE = auto()
    ZOMBIE = auto()


class Player:
    def __init__(self):
        self.motion = Motion.empty()
        self.directional_input = pygame.Vector2()
        self.z_position = 0
        self.z_velocity = 0

        # normal animation states
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
                    "roll": [
                        Animation(a.PLAYER_FRAMES[70:75], 0.07, False),
                        Animation(a.PLAYER_FRAMES[65:70], 0.07, False),
                        Animation(a.PLAYER_FRAMES[60:65], 0.07, False),
                        Animation(a.PLAYER_FRAMES[75:80], 0.07, False),
                    ],
                },
            )
        )
        animator_initialise(self.animator, animation_mapping)

        # that little indicator which shows when the player gets a checkpoint
        # (functionality is currently commented out in player_set_checkpoint)
        self.checkpoint_animation_timer = Timer()
        self.checkpoint_animator = Animator()
        animator_initialise(self.checkpoint_animator, {0: Animation(a.CHECKPOINT_FRAMES, 0.08)})

        self.progression = PlayerProgression()

        self.direction = Direction.S
        self.caught_timer = Timer()  # resets scene and player when completed
        self.caught_style = PlayerCaughtStyle.NONE
        self.interaction = PlayerInteraction(None, False)

        # rolling
        self.roll_max_timer = Timer()  # duration of the current roll
        self.roll_cooldown_timer = Timer()  # delay before another roll can be performed

        # consts
        self.walk_speed = 150  # allows jumping a 3 tile gap
        self.roll_max_speed = 350  # allows jumping a 4 tile gap (also barely a 5 tile lake)
        self.jump_velocity = 130  # about a tile high
        self.z_acceleration = 600


def player_rect(motion: Motion) -> pygame.Rect:
    # round for accurate collision.
    return pygame.Rect(round(motion.position.x) + 11, round(motion.position.y) + 28, 10, 4)


def _player_movement(player: Player, dt: float, action_buffer: t.InputBuffer) -> None:
    player.directional_input = pygame.Vector2(
        t.is_held(action_buffer, t.Action.RIGHT) - t.is_held(action_buffer, t.Action.LEFT),
        t.is_held(action_buffer, t.Action.DOWN) - t.is_held(action_buffer, t.Action.UP),
    )
    # no roll control
    if player.roll_max_timer.remaining > 0:
        return
    # lateral movement
    player.motion.velocity = player.directional_input * player.walk_speed
    if player.directional_input.x != 0 and player.directional_input.y != 0:
        player.motion.velocity *= 0.707  # trig shortcut, normalizing the vector


def _player_collision(
    player: Player, dt: float, grid_collision: set[tuple[int, int]], walls: list[pygame.Rect]
) -> None:
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
    mouse_buffer: t.InputBuffer,
    grid_collision: set[tuple[int, int]],
    walls: list[pygame.Rect],
    dialogue: DialogueSystem,
) -> None:

    is_moving = False

    # movement
    if player.caught_timer.remaining <= 0:
        _player_movement(player, dt, action_buffer)
        is_moving = player.motion.velocity.magnitude_squared() > 0

        if is_moving:
            player.direction = direction_from_delta(*player.motion.velocity)

        if player.interaction.scene_name is not None and not player.interaction.requires_input:
            if not dialogue_has_executed_scene(dialogue, player.interaction.scene_name):
                dialogue_execute_script_scene(dialogue, player.interaction.scene_name)
                player.interaction.scene_name = None

        if t.is_pressed(action_buffer, t.Action.A) or t.is_pressed(
            mouse_buffer, t.MouseButton.LEFT
        ):
            # interact
            if player.interaction.scene_name is not None and player.interaction.requires_input:
                if player.interaction.direction is not None:
                    player.direction = player.interaction.direction
                is_moving = False
                player.motion.position.x = int(player.motion.position.x)  # reduces jitter
                player.motion.position.y = int(player.motion.position.y)
                player.motion.velocity = pygame.Vector2()
                dialogue_execute_script_scene(dialogue, player.interaction.scene_name)
            # jumping
            elif player.z_position == 0:
                player.z_velocity = -player.jump_velocity
                animator_reset(player.animator)
                play_sound(AudioChannel.PLAYER, a.JUMP)

        if t.is_pressed(action_buffer, t.Action.B) or t.is_pressed(
            mouse_buffer, t.MouseButton.RIGHT
        ):
            # maybe start rolling
            if (
                is_moving
                and player.roll_cooldown_timer.remaining <= 0  # not on cooldown
                and player.roll_max_timer.remaining <= 0  # not currently rolling
                and player.z_position == 0  # is grounded
            ):
                animator_reset(player.animator)
                timer_reset(player.roll_max_timer, 0.3)
                timer_reset(player.roll_cooldown_timer, 0.65)
                play_sound(AudioChannel.PLAYER_ALT, a.ROLL)

        # timers
        timer_update(player.roll_max_timer, dt)
        timer_update(player.roll_cooldown_timer, dt)

    # apply roll velocity
    if player.roll_max_timer.remaining > 0 and player.motion.velocity.magnitude_squared() > 0:
        player.motion.velocity = player.motion.velocity.normalize() * (
            (player.roll_max_speed - player.walk_speed)
            * (player.roll_max_timer.remaining / player.roll_max_timer.duration)
            + player.walk_speed
        )

    # collision
    _player_collision(player, dt, grid_collision, walls)
    motion_update(player.motion, dt)
    player.z_velocity += player.z_acceleration * dt
    player.z_position = min(player.z_position + player.z_velocity * dt, 0)

    # animation
    if player.caught_timer.remaining <= 0:
        step_frames = ()
        if player.roll_max_timer.remaining > 0:
            animator_switch_animation(player.animator, f"roll_{player.direction}")
        elif player.z_position < 0:
            animator_switch_animation(player.animator, f"jump_{player.direction}")
        elif is_moving:
            animator_switch_animation(player.animator, f"walk_{player.direction}")
            step_frames = (7, 3)
        else:
            animator_switch_animation(player.animator, f"idle_{player.direction}")

        prev_frame = player.animator.frame_index
        animator_update(player.animator, dt)
        if prev_frame not in step_frames and player.animator.frame_index in step_frames:
            play_sound(
                AudioChannel.PLAYER,
                a.FOOTSTEPS[0 if player.animator.frame_index == step_frames[0] else 1],
            )
    timer_update(player.checkpoint_animation_timer, dt)
    if player.checkpoint_animation_timer.remaining > 0:
        animator_update(player.checkpoint_animator, dt)


def player_caught(player: Player, camera: Camera, style: PlayerCaughtStyle) -> None:
    if player.caught_timer.remaining > 0:
        return
    player.caught_style = style
    player.motion.velocity = pygame.Vector2()
    player.directional_input = pygame.Vector2()
    timer_reset(player.caught_timer, 0.5)
    timer_reset(player.roll_max_timer, 0)
    camera.trauma = 0.4
    if style == PlayerCaughtStyle.HOLE:
        play_sound(AudioChannel.PLAYER, a.CAUGHT_HOLE)
    else:
        play_sound(AudioChannel.PLAYER, a.CAUGHT_SIGHT)


def player_set_checkpoint(player: Player, pos: pygame.Vector2) -> None:
    player.progression.checkpoint = pos
    player.progression.checkpoint_buttons = player.progression.activated_buttons.copy()
    # animator_reset(player.checkpoint_animator)
    # timer_reset(player.checkpoint_animation_timer, 1)


def player_reset(player: Player) -> None:
    player.motion.position = player.progression.checkpoint.copy()
    player.motion.velocity = pygame.Vector2()
    player.motion.acceleration = pygame.Vector2()
    player.caught_style = PlayerCaughtStyle.NONE
    player.progression.activated_buttons = player.progression.checkpoint_buttons.copy()


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
            alert = a.CAUGHT_INDICATORS[0]
            y_offset = -8
        elif player.caught_style == PlayerCaughtStyle.ZOMBIE:
            alert = a.CAUGHT_INDICATORS[1]
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
    if g.show_hitboxes:
        pygame.draw.rect(
            surface,
            c.CYAN,
            camera_to_screen_shake_rect(camera, *player_rect(player.motion)),
            1,
        )

    # checkpoint animation
    if player.checkpoint_animation_timer.remaining > 0:
        surface.blit(
            animator_get_frame(player.checkpoint_animator),
            (surface.get_width() - 32, surface.get_height() - 36),
            special_flags=pygame.BLEND_RGB_ADD,
        )
