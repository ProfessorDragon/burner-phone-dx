from components.graphic import Graphic


class SimulatedObject:
    x: float = 0
    y: float = 0
    vx: float = 0
    vy: float = 0
    ax: float = 0
    ay: float = 0

    def __init__(self, x: float = 0, y: float = 0):
        self.x = x
        self.y = y

    def update(self, dt: float) -> None:
        self.vx += self.ax * dt
        self.vy += self.ay * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def get_pos(self) -> tuple[float, float]:
        return (self.x, self.y)


class GameObject(SimulatedObject):
    def __init__(self, graphic: Graphic, x: float = 0, y: float = 0):
        super().__init__(x, y)
        self.graphic = graphic
    
    def update(self, dt: float) -> None:
        super().update(dt)
        self.graphic.update(dt)
    
    def draw(self, scene) -> None:
        scene.surface.blit(
            self.graphic.get_frame(),
            scene.camera.world_to_screen_shake(*self.get_pos())
        )
