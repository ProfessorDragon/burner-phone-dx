from dataclasses import dataclass
import pygame

# pygame vector (1) is faster and (2) has more calculation features
Vector2 = pygame.Vector2

# @dataclass(slots=True)
# class Vector2:
#     x: float = 0.0
#     y: float = 0.0

#     def __iter__(self):
#         return iter((self.x, self.y))

#     def copy(self):
#         return Vector2(self.x, self.y)


@dataclass(slots=True)
class Vector3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __iter__(self):
        return iter((self.x, self.y, self.z))


@dataclass
class Motion:
    position: Vector2
    velocity: Vector2
    acceleration: Vector2

    def copy(self):
        return Motion(self.position.copy(), self.velocity.copy(), self.acceleration.copy())

    @staticmethod
    def empty():
        return Motion(Vector2(), Vector2(), Vector2())


def motion_update(motion: Motion, dt: float) -> None:
    motion.velocity.x += motion.acceleration.x * dt
    motion.velocity.y += motion.acceleration.y * dt
    motion.position.x += motion.velocity.x * dt
    motion.position.y += motion.velocity.y * dt


@dataclass
class Motion3D:
    position: Vector3
    velocity: Vector3
    acceleration: Vector3

    @staticmethod
    def empty():
        return Motion(Vector3(), Vector3(), Vector3())


def motion3d_update(motion: Motion3D, dt: float) -> None:
    motion.velocity.x += motion.acceleration.x * dt
    motion.velocity.x += motion.acceleration.x * dt
    motion.velocity.z += motion.acceleration.z * dt
    motion.position.x += motion.velocity.x * dt
    motion.position.y += motion.velocity.y * dt
    motion.position.z += motion.velocity.z * dt
