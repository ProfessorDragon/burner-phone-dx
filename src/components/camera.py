from dataclasses import dataclass
import random

from components.motion import Vector2, Motion, motion_update
from utilities.math import clamp, vec_size


@dataclass(slots=True)
class Camera:
    motion: Motion
    offset: Vector2
    shake_offset: Vector2
    max_shake_offset: Vector2
    trauma: float = 0.0
    max_shake_duration: float = 2.0


def camera_follow(camera: Camera, x: float, y: float, speed: float = 8) -> None:
    dist = Vector2(x - camera.motion.position.x, y - camera.motion.position.y)
    if vec_size(dist) < 1:
        camera.motion.position = Vector2(x, y)
        camera.motion.velocity = Vector2()
    else:
        camera.motion.velocity = Vector2(
            dist.x * speed,
            dist.y * speed,
        )


def camera_update(camera: Camera, dt: float) -> None:
    # Update shake
    camera.trauma -= dt / camera.max_shake_duration

    if camera.trauma > 0:
        shake = camera.trauma**3  # Can square trauma too
        camera.shake_offset.x = (
            camera.max_shake_offset.x * shake * random.uniform(-1, 1)
        )
        camera.shake_offset.y = (
            camera.max_shake_offset.y * shake * random.uniform(-1, 1)
        )
    elif camera.trauma < 0:
        camera.shake_offset.x = 0
        camera.shake_offset.y = 0

    camera.trauma = clamp(camera.trauma, 0, 1)

    # Update motion
    motion_update(camera.motion, dt)


def camera_to_screen(camera: Camera, x: float, y: float) -> tuple[int, int]:
    # round to reduce jitter.
    return (
        round(x - camera.motion.position.x + camera.offset.x),
        round(y - camera.motion.position.y + camera.offset.y),
    )


def camera_to_screen_shake(camera: Camera, x: float, y: float) -> tuple[int, int]:
    screen_x = x - camera.motion.position.x + camera.offset.x
    screen_y = y - camera.motion.position.y + camera.offset.y
    return (
        round(screen_x + camera.shake_offset.x),
        round(screen_y + camera.shake_offset.y),
    )


def camera_from_screen(camera: Camera, x: float, y: float) -> tuple[int, int]:
    return (
        round(x + camera.motion.position.x - camera.offset.x),
        round(y + camera.motion.position.y - camera.offset.y),
    )


def camera_reset(camera: Camera) -> None:
    camera.trauma = 0.0
    camera.shake_offset.x = 0.0
    camera.shake_offset.y = 0.0
