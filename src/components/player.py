from enum import IntEnum, auto
import pygame

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


class PlayerCaughtStyle(IntEnum):
    NONE = 0
    SIGHT = auto()
    HOLE = auto()
    ZOMBIE = auto()


class Player:
    def __init__(self):
        self.motion = Motion.empty()
        self.z_position = 0
        self.z_velocity = 0
        self.animator = Animator()
        self.direction = Direction.E
        self.walk_speed = 150
        self.caught_timer = Timer()
        self.caught_style = PlayerCaughtStyle.NONE


def player_initialise() -> Player:
    player = Player()
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
    animator_initialise(player.animator, animation_mapping)
    return player


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
) -> None:

    # movement
    if player.caught_timer.remaining <= 0:
        _player_movement(player, dt, action_buffer)
        # jumping
        if player.z_position == 0 and t.is_pressed(action_buffer, t.Action.A):
            player.z_velocity = -130
            animator_reset(player.animator)
            pygame.mixer.Channel(1).play(a.JUMP)

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
        if prev_frame not in (3, 7) and player.animator.frame_index in (3, 7):
            pygame.mixer.Channel(1).play(a.FOOTSTEP)


def player_caught(player: Player, camera: Camera, style: PlayerCaughtStyle) -> None:
    if player.caught_timer.remaining > 0:
        return
    timer_reset(player.caught_timer, 0.5)
    player.caught_style = style
    player.motion.velocity = pygame.Vector2()
    camera.trauma = 0.4
    if style == PlayerCaughtStyle.HOLE:
        pygame.mixer.Channel(1).play(a.CAUGHT_HOLE)
    else:
        pygame.mixer.Channel(1).play(a.CAUGHT_SIGHT)


def player_reset(player: Player, position: pygame.Vector2) -> None:
    player.motion.position = position.copy()
    player.motion.velocity = pygame.Vector2()
    player.motion.acceleration = pygame.Vector2()
    player.caught_style = PlayerCaughtStyle.NONE


def shadow_render(
    surface: pygame.Surface,
    camera: Camera,
    motion: Motion,
    direction: Direction,
    z_position: float = 0,
) -> None:
    # use two vectors because we NEED to preserve decimal places
    shadow_tl = pygame.Vector2(motion.position.x + 10, motion.position.y + 29)
    shadow_wh = pygame.Vector2(12, 6)
    if motion.velocity.x != 0:
        if direction in (Direction.W, Direction.NW, Direction.SW):
            shadow_wh.x += 2
        elif direction in (Direction.E, Direction.NE, Direction.SE):
            shadow_tl.x -= 2
            shadow_wh.x += 2
    if z_position < -5:
        shadow_wh.x -= 2
        shadow_wh.y -= 2
        shadow_tl.x += 1
        shadow_tl.y += 1
    shadow = pygame.Surface(shadow_wh, pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 50), pygame.Rect(0, 0, *shadow_wh))
    surface.blit(shadow, camera_to_screen_shake(camera, *shadow_tl))


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
    shadow_render(surface, camera, player.motion, player.direction, player.z_position)
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
