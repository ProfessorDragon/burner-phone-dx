from dataclasses import dataclass
from enum import IntEnum, auto
import pygame


class Direction(IntEnum):
    N = 0
    NE = auto()
    E = auto()
    SE = auto()
    S = auto()
    SW = auto()
    W = auto()
    NW = auto()


# @dataclass(slots=True)
# class pygame.Vector2:
#     x: float = 0.0
#     y: float = 0.0
#
#     def __iter__(self):
#         return iter((self.x, self.y))
#
#     def copy(self):
#         return pygame.Vector2(self.x, self.y)


@dataclass
class Motion:
    position: pygame.Vector2
    velocity: pygame.Vector2
    acceleration: pygame.Vector2

    def copy(self):
        return Motion(self.position.copy(), self.velocity.copy(), self.acceleration.copy())

    @staticmethod
    def empty():
        return Motion(pygame.Vector2(), pygame.Vector2(), pygame.Vector2())


def motion_update(motion: Motion, dt: float) -> None:
    motion.velocity.x += motion.acceleration.x * dt
    motion.velocity.y += motion.acceleration.y * dt
    motion.position.x += motion.velocity.x * dt
    motion.position.y += motion.velocity.y * dt
