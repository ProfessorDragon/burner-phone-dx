import random
from dataclasses import dataclass

import core.constants as const
from components.object import SimulatedObject
from utilities.math import clamp


# To make x, y position the centre of the camera
OFFSET_X, OFFSET_Y = const.WINDOW_CENTRE


@dataclass
class Camera:
    pos: SimulatedObject
    trauma: float = 0.0  # Value between 0 and 1
    shake: float = 0.0  # Value between 0 and 1
    shake_offset_x: float = 0
    shake_offset_y: float = 0
    max_shake_offset_x: float = 30
    max_shake_offset_y: float = 30
    max_screenshake_duration: float = 2.0  # In seconds

    def update(self, scene) -> None:
        self.trauma -= scene.dt / self.max_screenshake_duration

        if self.trauma > 0:
            self.shake = self.trauma ** 3  # Can square trauma too
            self.shake_offset_x = self.max_shake_offset_x * \
                self.shake * random.uniform(-1, 1)
            self.shake_offset_y = self.max_shake_offset_y * \
                self.shake * random.uniform(-1, 1)
        elif self.trauma < 0:
            self.shake = 0
            self.shake_offset_x = 0
            self.shake_offset_y = 0

        self.trauma = clamp(self.trauma, 0, 1)
        self.pos.update(scene)

    def add_camera_shake(self, damage: float) -> None:
        self.trauma += damage

    def set_camera_shake(self, damage: float) -> None:
        self.trauma = damage

    def world_to_screen(self, x: float, y: float) -> tuple[int, int]:
        return (int(x - self.pos.x + OFFSET_X),
                int(y - self.pos.y + OFFSET_Y))

    def world_to_screen_shake(self, x: float, y: float) -> tuple[int, int]:
        return (int(x - self.pos.x + OFFSET_X + self.shake_offset_x),
                int(y - self.pos.y + OFFSET_Y + self.shake_offset_y))
