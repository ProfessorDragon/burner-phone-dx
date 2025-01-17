from dataclasses import dataclass


@dataclass(slots=True)
class Vector2:
    x: float = 0.0
    y: float = 0.0

    def __iter__(self):
        return iter((self.x, self.y))


@dataclass
class Motion:
    position: Vector2
    velocity: Vector2
    acceleration: Vector2

    @staticmethod
    def empty():
        return Motion(Vector2(), Vector2(), Vector2())


def motion_update(motion: Motion, dt: float) -> None:
    motion.velocity.x += motion.acceleration.x * dt
    motion.velocity.y += motion.acceleration.y * dt
    motion.position.x += motion.velocity.x * dt
    motion.position.y += motion.velocity.y * dt
