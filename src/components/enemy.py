from abc import ABC, abstractmethod
from math import cos, radians
import random
from typing import Any
import pygame

from components.player import Player, player_caught, player_rect, shadow_render
from components.ray import SightData, collide_sight, compile_sight, render_sight
import core.assets as a
import core.constants as c
from components.animation import (
    Animation,
    Animator,
    animator_get_frame,
    animator_initialise,
    animator_reset,
    animator_switch_animation,
    animator_update,
    directional_animation_mapping,
    walking_animation_mapping,
)
from components.camera import Camera, camera_to_screen_shake, camera_to_screen_shake_rect
from components.motion import (
    Direction,
    Motion,
    direction_from_angle,
    direction_from_delta,
    motion_update,
)
from scenes.scene import PLAYER_LAYER, PLAYER_OR_BG, PLAYER_OR_FG, RenderLayer
from utilities.math import point_in_ellipse


def render_path(surface: pygame.Surface, camera: Camera, path: list[pygame.Vector2]) -> None:
    if len(path) == 0:
        return
    if len(path) == 1:
        pygame.draw.circle(surface, c.RED, camera_to_screen_shake(camera, *path[0]), 3)
    else:
        pygame.draw.polygon(
            surface,
            c.RED,
            [camera_to_screen_shake(camera, *point) for point in path],
            1,
        )

    for i, point in enumerate(path):
        surface.blit(
            a.DEBUG_FONT.render(str(i), False, c.RED),
            camera_to_screen_shake(camera, *point),
        )


def _path_to_json(path: list[pygame.Vector2]) -> list[tuple[int, int]]:
    return [(int(point.x), int(point.y)) for point in path]


def _path_from_json(js_path: list[tuple[int, int]]) -> list[pygame.Vector2]:
    return [pygame.Vector2(point) for point in js_path]


# base class
class Enemy(ABC):
    def __init__(self):
        self.motion = Motion.empty()

    # some standard methods to make it easier on the editor
    def get_hitbox(self) -> pygame.Rect:
        return pygame.Rect(
            self.motion.position.x - c.HALF_TILE_SIZE,
            self.motion.position.y - c.HALF_TILE_SIZE,
            c.TILE_SIZE,
            c.TILE_SIZE,
        )

    # some standard methods to make it easier on the editor
    def get_path(self) -> list[pygame.Vector2]:
        return None

    @abstractmethod
    def to_json(self) -> dict[str, Any]: ...

    @staticmethod
    @abstractmethod
    def from_json(js: dict[str, Any]): ...

    @abstractmethod
    def reset(self) -> None: ...

    @abstractmethod
    def update(
        self, dt: float, player: Player, camera: Camera, grid_collision: set[tuple[int, int]]
    ) -> None: ...

    @abstractmethod
    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None: ...


def enemy_from_json(js: dict[str, Any]) -> Enemy:
    for cls in ENEMY_CLASSES:
        if cls.__name__ == js["class"]:
            return cls.from_json(js)
    return None


# extension 2 mathematics put to use (kinda)
def _enemy_follow(enemy: Enemy, dist: pygame.Vector2, speed: float):
    enemy.motion.velocity = dist.normalize() * speed
    enemy.motion.velocity *= (
        (0.5 - c.PERSPECTIVE / 2) * cos(2 * radians(dist.angle_to(pygame.Vector2(1, 0))))
        + 0.5
        + c.PERSPECTIVE / 2
    )


class PatrolEnemy(Enemy):
    def __init__(self, path: list[pygame.Vector2]):
        super().__init__()
        self.animator = Animator()
        animator_initialise(self.animator, walking_animation_mapping(a.PATROL_FRAMES, 0.09))
        self.path: list[pygame.Vector2] = path
        self.facing = 0
        self.direction = Direction.N
        self.sight_data = SightData(80, 14)
        self.reset()

    def get_hitbox(self) -> pygame.Rect:
        return pygame.Rect(self.motion.position.x + 12, self.motion.position.y + 28, 8, 4)

    def get_path(self) -> list[pygame.Vector2]:
        return self.path

    def to_json(self):
        if len(self.path) > 1:
            return {"path": _path_to_json(self.path)}
        return {"pos": (*self.motion.position,), "facing": self.facing}

    @staticmethod
    def from_json(js):
        if "path" in js:
            return PatrolEnemy(_path_from_json(js["path"]))
        enemy = PatrolEnemy([pygame.Vector2(js["pos"])])
        enemy.facing = js.get("facing", 0)
        return enemy

    def reset(self) -> None:
        self.motion.position = self.path[0].copy()
        if len(self.path) > 1:
            self.facing = (self.path[1] - self.path[0]).angle_to(pygame.Vector2(1, 0))
            self.active_point = 1
        else:
            self.active_point = 0

    def update(
        self, dt: float, player: Player, camera: Camera, grid_collision: set[tuple[int, int]]
    ) -> None:
        if len(self.path) > 1:
            target = self.path[self.active_point]
            dist = target - self.motion.position
            target_facing = dist.angle_to(pygame.Vector2(1, 0))
            turn = (target_facing - self.facing) % 360
            if turn > 180:
                turn -= 360
            # not facing in correct direction, turn
            if abs(turn) > 1:
                if abs(turn) > 5:
                    self.facing += turn / abs(turn) * 5
                else:
                    self.facing = target_facing
            # follow path
            elif dist.magnitude_squared() > 1:
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
        else:
            self.sight_data.center = self.motion.position + pygame.Vector2(16, 16)
            self.sight_data.facing = self.facing
            compile_sight(self.sight_data, grid_collision)
            if collide_sight(player, self.sight_data):
                player_caught(player, camera)

        # animation
        if self.motion.velocity.magnitude_squared() > 0:
            animator_switch_animation(self.animator, f"walk_{self.direction}")
        else:
            animator_switch_animation(self.animator, f"idle_{self.direction}")
        animator_update(self.animator, dt)

        motion_update(self.motion, dt)

    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
        frame = animator_get_frame(self.animator)
        if layer == RenderLayer.RAYS:
            render_sight(surface, camera, self.sight_data)
        if layer in PLAYER_LAYER:
            shadow_render(surface, camera, self.motion, self.direction)
            surface.blit(
                frame,
                camera_to_screen_shake(camera, *self.motion.position),
            )


class SpotlightEnemy(Enemy):
    def __init__(self, path: list[pygame.Vector2]):
        super().__init__()
        self.path: list[pygame.Vector2] = path
        self.active_point = 0
        self.light_radius = 48
        self.reset()

    def get_path(self) -> list[pygame.Vector2]:
        return self.path

    def to_json(self):
        return {"path": _path_to_json(self.path)}

    @staticmethod
    def from_json(js):
        return SpotlightEnemy(_path_from_json(js["path"]))

    def reset(self) -> None:
        self.motion.position = self.path[0].copy()
        self.active_point = 0

    def update(
        self, dt: float, player: Player, camera: Camera, grid_collision: set[tuple[int, int]]
    ) -> None:
        if len(self.path) > 0:
            target = self.path[self.active_point]
            dist = target - self.motion.position
            # follow path
            if dist.magnitude_squared() > 1:
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
        if layer in PLAYER_OR_FG:
            rx, ry = self.light_radius, self.light_radius * c.PERSPECTIVE
            render_position = (self.motion.position.x - rx, self.motion.position.y - ry)
            sprite = pygame.Surface((rx * 2, ry * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(sprite, (255, 255, 0, 96), sprite.get_rect())
            surface.blit(sprite, camera_to_screen_shake(camera, *render_position))


class SpikeTrapEnemy(Enemy):
    def __init__(self):
        super().__init__()
        self.animator = Animator()
        animation_mapping = {
            "idle": Animation([a.SPIKE_TRAP_FRAMES[0]]),
            "stepped_on": Animation([a.SPIKE_TRAP_FRAMES[1]]),
            "activated": Animation(a.SPIKE_TRAP_FRAMES[2:], 0.1, False),
        }
        animator_initialise(self.animator, animation_mapping)
        self.reset()

    def get_hitbox(self) -> pygame.Rect:
        return pygame.Rect(self.motion.position.x + 4, self.motion.position.y + 2, 8, 12)

    def to_json(self):
        return {"pos": (*self.motion.position,)}

    @staticmethod
    def from_json(js):
        enemy = SpikeTrapEnemy()
        enemy.motion.position = pygame.Vector2(js["pos"])
        return enemy

    def reset(self) -> None:
        self.stepped_on = False
        self.activated = False
        animator_switch_animation(self.animator, "idle")

    def update(
        self, dt: float, player: Player, camera: Camera, grid_collision: set[tuple[int, int]]
    ) -> None:
        # collision
        if player.z_position == 0:
            prect = player_rect(player.motion)
            prev_stepped = self.stepped_on
            self.stepped_on = prect.colliderect(self.get_hitbox())
            if self.stepped_on and not prev_stepped:
                if not self.activated:
                    animator_switch_animation(self.animator, "stepped_on")
                else:
                    player_caught(player, camera)
            elif not self.stepped_on and prev_stepped:
                self.activated = True
                animator_switch_animation(self.animator, "activated")
                animator_reset(self.animator)
        animator_update(self.animator, dt)

    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
        if layer in PLAYER_OR_BG:
            surface.blit(
                animator_get_frame(self.animator),
                camera_to_screen_shake(camera, *self.motion.position),
            )


class SecurityCameraEnemy(Enemy):
    def __init__(self):
        super().__init__()
        self.animator = Animator()
        animation_mapping = directional_animation_mapping(
            {
                "swivel": [
                    Animation([a.DEBUG_IMAGE_16]),
                    Animation([a.DEBUG_IMAGE_16]),
                    Animation([a.DEBUG_IMAGE_16]),
                    Animation([a.DEBUG_IMAGE_16]),
                ]
            }
        )
        animator_initialise(self.animator, animation_mapping)
        self.facing = 0
        self.sight_data = SightData(96, 30)
        self.swivel = 0
        self.swivel_angle = 60
        self.swivel_forwards = True
        self.reset()

    def get_hitbox(self) -> pygame.Rect:
        return pygame.Rect(*self.motion.position, 16, 16)

    def to_json(self):
        return {
            "pos": (*self.motion.position,),
            "facing": self.facing,
            "z": self.sight_data.z_offset,
        }

    @staticmethod
    def from_json(js):
        enemy = SecurityCameraEnemy()
        enemy.motion.position = pygame.Vector2(js["pos"])
        enemy.facing = js.get("facing", 0)
        enemy.sight_data.z_offset = js.get("z", 0)
        return enemy

    def reset(self) -> None:
        self.swivel = 0

    def update(
        self, dt: float, player: Player, camera: Camera, grid_collision: set[tuple[int, int]]
    ) -> None:
        if self.swivel_forwards:
            target_swivel = self.swivel_angle / 2
        else:
            target_swivel = -self.swivel_angle / 2
        turn = (target_swivel - self.swivel) % 360
        if turn > 180:
            turn -= 360
        # not facing in correct direction, turn
        if abs(turn) > 1:
            if self.swivel_forwards:
                self.swivel += 0.25
            else:
                self.swivel -= 0.25
        # inverse swivel direction
        else:
            self.swivel_forwards = not self.swivel_forwards

        # collision
        self.sight_data.center = self.motion.position + pygame.Vector2(8, 8)
        self.sight_data.facing = self.facing + self.swivel
        compile_sight(self.sight_data, grid_collision)
        if collide_sight(player, self.sight_data):
            player_caught(player, camera)

        # animation
        direction = direction_from_angle(self.facing + self.swivel)
        animator_switch_animation(self.animator, f"swivel_{direction}")
        animator_update(self.animator, dt)

    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
        if layer == RenderLayer.RAYS:
            render_sight(surface, camera, self.sight_data)
        if layer in PLAYER_LAYER:
            surface.blit(
                animator_get_frame(self.animator),
                camera_to_screen_shake(
                    camera,
                    self.motion.position.x,
                    self.motion.position.y + self.sight_data.z_offset,
                ),
            )


class ZombieEnemy(Enemy):
    def __init__(self, movement_center: pygame.Vector2):
        super().__init__()
        self.animator = Animator()
        animator_initialise(self.animator, walking_animation_mapping(a.PATROL_FRAMES, 0.07))
        self.direction = Direction.N
        self.movement_center = movement_center
        self.movement_radius = 96
        self.reset()

    def get_hitbox(self) -> pygame.Rect:
        return pygame.Rect(
            round(self.motion.position.x) + 12, round(self.motion.position.y) + 28, 8, 4
        )

    def to_json(self):
        return {"pos": (*self.movement_center,)}

    @staticmethod
    def from_json(js):
        return ZombieEnemy(pygame.Vector2(js["pos"]))

    def reset(self) -> None:
        self.motion.position = self.movement_center.copy()
        self.chasing = True
        self.randomize_walk_speed()

    def randomize_walk_speed(self) -> None:
        self.walk_speed = 200 * random.uniform(0.8, 1.2)

    def update(
        self, dt: float, player: Player, camera: Camera, grid_collision: set[tuple[int, int]]
    ) -> None:
        self.motion.velocity = pygame.Vector2()
        prect = player_rect(player.motion)
        hitbox = self.get_hitbox()
        # only move when player moves
        player_dist = pygame.Vector2(prect.center) - pygame.Vector2(hitbox.center)
        if player.motion.velocity.magnitude_squared() > 0:
            center_dist = (
                self.movement_center + pygame.Vector2(16, 30) - pygame.Vector2(hitbox.center)
            )
            if self.chasing:
                if center_dist.magnitude() < self.movement_radius:
                    _enemy_follow(self, player_dist, self.walk_speed)
                else:
                    self.chasing = False
                    self.randomize_walk_speed()
            else:
                if center_dist.magnitude_squared() > 1:
                    _enemy_follow(self, center_dist, self.walk_speed)
                else:
                    self.chasing = True
                    self.randomize_walk_speed()
        if self.motion.velocity.magnitude_squared() > 0:
            self.direction = direction_from_delta(*self.motion.velocity)
        elif random.randint(1, 300) == 1:
            self.direction = Direction((self.direction + 1) % 8)

        # collision
        if prect.colliderect(hitbox):
            player_caught(player, camera)

        # animation
        if self.motion.velocity.magnitude_squared() > 0:
            animator_switch_animation(self.animator, f"walk_{self.direction}")
        else:
            animator_switch_animation(self.animator, f"idle_{self.direction}")
        animator_update(self.animator, dt)

        motion_update(self.motion, dt)

    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
        if layer in PLAYER_LAYER:
            shadow_render(surface, camera, self.motion, self.direction)
            surface.blit(
                animator_get_frame(self.animator),
                camera_to_screen_shake(camera, *self.motion.position),
            )
        if layer in PLAYER_OR_FG and c.DEBUG_HITBOXES:
            pygame.draw.circle(
                surface,
                c.RED,
                camera_to_screen_shake(camera, *(self.movement_center + pygame.Vector2(16, 30))),
                self.movement_radius,
                1,
            )


def enemy_reset(enemy: Enemy) -> None:
    enemy.reset()


def enemy_update(
    enemy: Enemy, dt: float, player: Player, camera: Camera, grid_collision: set[tuple[int, int]]
) -> None:
    enemy.update(dt, player, camera, grid_collision)


def enemy_render(
    enemy: Enemy,
    surface: pygame.Surface,
    camera: Camera,
    layer: RenderLayer,
) -> None:
    enemy.render(surface, camera, layer)

    if c.DEBUG_HITBOXES:
        if layer == RenderLayer.RAYS:
            path = enemy.get_path()
            if path is not None:
                render_path(surface, camera, path)
        if layer in PLAYER_OR_FG:
            hitbox = enemy.get_hitbox()
            if hitbox:
                pygame.draw.rect(surface, c.RED, camera_to_screen_shake_rect(camera, *hitbox), 1)


ENEMY_CLASSES = [
    PatrolEnemy,
    SpotlightEnemy,
    SpikeTrapEnemy,
    SecurityCameraEnemy,
    ZombieEnemy,
]
