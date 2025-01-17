from dataclasses import dataclass


@dataclass(slots=True)
class Vector2:
    x: float
    y: float

    def __iter__(self):
        return iter((self.x, self.y))


@dataclass(slots=True)
class Motion:
    position: Vector2
    velocity: Vector2
    acceleration: Vector2


def motion_update(motion: Motion, dt: float) -> None:
    motion.vx += motion.ax * dt
    motion.vy += motion.ay * dt
    motion.x += motion.vx * dt
    motion.y += motion.vy * dt
