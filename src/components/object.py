from dataclasses import dataclass


@dataclass
class SimulatedObject:
    x: float = 0
    y: float = 0
    vx: float = 0
    vy: float = 0
    ax: float = 0
    ay: float = 0

    def update(self, dt: float) -> None:
        self.vx += self.ax * dt
        self.vy += self.ay * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def get_pos(self) -> tuple[float, float]:
        return (self.x, self.y)
