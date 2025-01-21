from abc import ABC, abstractmethod
from math import cos, radians
import random
from typing import Any, Self

import pygame
from components.player import Player, player_caught, player_rect, shadow_render
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
from scenes.scene import RenderLayer
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


def collide_sight(
    player: Player,
    *,
    center: pygame.Vector2,
    facing: float,
    radius: float,
    angle: float,
) -> bool:
    prect = player_rect(player.motion)
    if point_in_ellipse(
        *prect.center,
        *center,
        radius,
        radius * c.PERSPECTIVE,
    ):
        pdist = pygame.Vector2(prect.center) - center
        theta = (pdist.angle_to(pygame.Vector2(1, 0)) - facing) % 360
        if theta < angle / 2 + 1 or theta > 360 - (angle / 2 + 1):
            return True
    return False


def render_sight(
    surface: pygame.Surface,
    camera: Camera,
    *,
    center: pygame.Vector2,
    facing: float,
    radius: float,
    angle: float,
    z_offset: float = 0,
) -> None:
    sight_left = pygame.Vector2(radius, 0).rotate(facing - angle // 2)
    sight_right = pygame.Vector2(radius, 0).rotate(facing + angle // 2)
    sight = pygame.Surface((radius * 2, radius * 2 * c.PERSPECTIVE), pygame.SRCALPHA)
    pygame.draw.polygon(
        sight,
        (162, 48, 0, 96),
        [
            (
                sight.get_width() // 2,
                sight.get_height() // 2 + z_offset,
            ),
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
            camera, center.x - sight.get_width() // 2, center.y - sight.get_height() // 2
        ),
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
    def from_json(js: dict[str, Any]) -> Self: ...

    @abstractmethod
    def reset(self) -> None: ...

    @abstractmethod
    def update(self, dt: float, player: Player, camera: Camera) -> None: ...

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
        self.sight_radius = 80
        self.sight_angle = 14
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

    def update(self, dt: float, player: Player, camera: Camera) -> None:
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
        elif collide_sight(
            player,
            center=self.motion.position + pygame.Vector2(16, 16),
            facing=self.facing,
            radius=self.sight_radius,
            angle=self.sight_angle,
        ):
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
        if layer < RenderLayer.PLAYER:
            render_sight(
                surface,
                camera,
                center=self.motion.position + pygame.Vector2(16, 16),
                facing=self.facing,
                radius=self.sight_radius,
                angle=self.sight_angle,
            )
        if abs(layer) <= RenderLayer.PLAYER_FG:
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

    def update(self, dt: float, player: Player, camera: Camera) -> None:
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
        if layer > RenderLayer.PLAYER:
            render_position = (
                self.motion.position.x - self.light_radius,
                self.motion.position.y - self.light_radius * c.PERSPECTIVE,
            )
            sprite = pygame.Surface(
                (self.light_radius * 2, self.light_radius * 2 * c.PERSPECTIVE),
                pygame.SRCALPHA,
            )
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

    def update(self, dt: float, player: Player, camera: Camera) -> None:
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
        if layer < RenderLayer.PLAYER:
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
        self.z = 0
        self.facing = 0
        self.target_facing = None
        self.sight_radius = 96
        self.sight_angle = 30
        self.swivel_angle = 90
        self.swivel_forwards = True
        self.reset()

    def get_hitbox(self) -> pygame.Rect:
        return pygame.Rect(*self.motion.position, 16, 16)

    def to_json(self):
        return {
            "pos": (*self.motion.position,),
            "z": self.z,
            "facing": self.facing,
        }

    @staticmethod
    def from_json(js):
        enemy = SecurityCameraEnemy()
        enemy.motion.position = pygame.Vector2(js["pos"])
        enemy.z = js.get("z", 0)
        enemy.facing = js.get("facing", 0)
        return enemy

    def reset(self) -> None:
        pass

    def update(self, dt: float, player: Player, camera: Camera) -> None:
        if self.target_facing is None:
            self.target_facing = (self.facing + self.swivel_angle / 2) % 360
        turn = (self.target_facing - self.facing) % 360
        if turn > 180:
            turn -= 360
        # not facing in correct direction, turn
        if abs(turn) > 1:
            if self.swivel_forwards:
                self.facing += 0.25
            else:
                self.facing -= 0.25
        # inverse swivel direction
        else:
            if self.swivel_forwards:
                self.target_facing = self.target_facing - self.swivel_angle
            else:
                self.target_facing = self.target_facing + self.swivel_angle
            self.target_facing %= 360
            self.swivel_forwards = not self.swivel_forwards

        # collision
        if collide_sight(
            player,
            center=self.motion.position + pygame.Vector2(8, 8),
            facing=self.facing,
            radius=self.sight_radius,
            angle=self.sight_angle,
        ):
            player_caught(player, camera)

        # animation
        direction = direction_from_angle(self.facing)
        animator_switch_animation(self.animator, f"swivel_{direction}")
        animator_update(self.animator, dt)

    def render(self, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
        if layer < RenderLayer.PLAYER:
            render_sight(
                surface,
                camera,
                center=self.motion.position + pygame.Vector2(8, 8),
                facing=self.facing,
                radius=self.sight_radius,
                angle=self.sight_angle,
                z_offset=self.z,
            )
        if abs(layer) <= RenderLayer.PLAYER_FG:
            surface.blit(
                animator_get_frame(self.animator),
                camera_to_screen_shake(
                    camera, self.motion.position.x, self.motion.position.y + self.z
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

    def update(self, dt: float, player: Player, camera: Camera) -> None:
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
        if abs(layer) <= RenderLayer.PLAYER_FG:
            shadow_render(surface, camera, self.motion, self.direction)
            surface.blit(
                animator_get_frame(self.animator),
                camera_to_screen_shake(camera, *self.motion.position),
            )
        if layer > RenderLayer.PLAYER and c.DEBUG_HITBOXES:
            pygame.draw.circle(
                surface,
                c.RED,
                camera_to_screen_shake(camera, *(self.movement_center + pygame.Vector2(16, 30))),
                self.movement_radius,
                1,
            )


def enemy_reset(enemy: Enemy) -> None:
    enemy.reset()


def enemy_update(enemy: Enemy, dt: float, player: Player, camera: Camera) -> None:
    enemy.update(dt, player, camera)


def enemy_render(enemy: Enemy, surface: pygame.Surface, camera: Camera, layer: RenderLayer) -> None:
    enemy.render(surface, camera, layer)

    if c.DEBUG_HITBOXES:
        if layer < RenderLayer.PLAYER:
            path = enemy.get_path()
            if path is not None:
                render_path(surface, camera, path)
        elif layer > RenderLayer.PLAYER:
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
