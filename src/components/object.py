from abc import ABC, abstractmethod
from components.graphic import Graphic


class AbstractObject(ABC):
    x: float = 0
    y: float = 0

    def __init__(self, x: float = 0, y: float = 0) -> None:
        self.x = x
        self.y = y

    @abstractmethod
    def update(self, scene) -> None: ...

    @abstractmethod
    def draw(self, scene) -> None: ...

    def get_pos(self) -> tuple[float, float]:
        return (self.x, self.y)


# object that can move with velocity and acceleration
class SimulatedObject(AbstractObject):
    vx: float = 0
    vy: float = 0
    ax: float = 0
    ay: float = 0

    def update(self, scene) -> None:
        self.vx += self.ax * scene.dt
        self.vy += self.ay * scene.dt
        self.x += self.vx * scene.dt
        self.y += self.vy * scene.dt

    def draw(self, scene) -> None:
        pass


# object that can move and renders using a Graphic
class GameObject(SimulatedObject):
    def __init__(self, graphic: Graphic, x: float = 0, y: float = 0) -> None:
        super().__init__(x, y)
        self.graphic = graphic

    def update(self, scene) -> None:
        super().update(scene)
        self.graphic.update(scene.dt)

    def draw(self, scene) -> None:
        scene.surface.blit(
            self.graphic.get_frame(),
            scene.camera.world_to_screen_shake(*self.get_pos())
        )
