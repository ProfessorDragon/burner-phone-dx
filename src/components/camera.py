import random
from dataclasses import dataclass

import core.constants as const
from components.motion import Vector2, Motion, update_motion
from utilities.math import clamp


@dataclass(slots=True)
class Camera:
    motion: Motion
    offset: Vector2 = Vector2(*const.WINDOW_CENTRE)
    trauma: float = 0.0  # Value between 0 and 1
    max_shake_duration: float = 2.0  # In seconds
    shake_offset: Vector2 = Vector2(0, 0)
    max_shake_offset: Vector2 = Vector2(30, 30)


def camera_update(camera: Camera, dt: float) -> None:
    # Update shake
    camera.trauma -= dt / camera.max_screenshake_duration

    if camera.trauma > 0:
        shake = camera.trauma ** 3  # Can square trauma too
        camera.shake_offset.x = camera.max_shake_offset.x * \
            shake * random.uniform(-1, 1)
        camera.shake_offset.y = camera.max_shake_offset.y * \
            shake * random.uniform(-1, 1)
    elif camera.trauma < 0:
        camera.shake_offset.x = 0
        camera.shake_offset.y = 0

    camera.trauma = clamp(camera.trauma, 0, 1)

    # Update motion
    update_motion(camera.motion, dt)


def camera_to_screen(camera: Camera, x: float, y: float) -> tuple[int, int]:
    return (int(x - camera.motion.x + camera.offset.x),
            int(y - camera.position.y + camera.offset.y))


def camera_to_screen_shake(
    camera: Camera, x: float, y: float
) -> tuple[int, int]:
    return (int(x - camera.motion.x + camera.offset.x + camera.shake_offset.x),
            int(y - camera.motion.y + camera.offset.y + camera.shake_offset.y))
