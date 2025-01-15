import pygame
from abc import ABC, abstractmethod
from typing import Callable
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


# object that is fixed on the screen and positioned using a percentage
class ScreenObject(AbstractObject):
    def __init__(
            self,
            graphic: Graphic,
            x_percent: float,
            y_percent: float
        ):
        super().__init__()
        self.graphic = graphic
        self.x_percent, self.y_percent = x_percent, y_percent

    def update(self, scene) -> None:
        super().update(scene)
        self.graphic.update(scene.dt)

    def draw(self, scene) -> None:
        frame = self.graphic.get_frame()
        out_w, out_h = frame.get_size()
        screen_w, screen_h = scene.surface.get_size()
        out_x, out_y = self.x_percent * (screen_w - out_w), self.y_percent * (screen_h - out_h)
        scene.surface.blit(frame, (out_x, out_y))


# object that can be selected in the selection grid
class UIObject(ScreenObject):
    def __init__(
            self,
            graphic: Graphic,
            x_percent: float,
            y_percent: float,
            grid_start: tuple[int, int],
            grid_size: tuple[int, int] = (1, 1)
        ):
        super().__init__(graphic, x_percent, y_percent)
        self.out_x, self.out_y = 0, 0 # real position of the object on screen
        self.out_w, self.out_h = graphic.get_frame().get_size() # stored for mouse hitbox detection
        self.grid_start = grid_start
        self.grid_size = grid_size
        self.generate_grid()
        self.selected = False
        self.on_accept = None
        self.on_cancel = None

    def generate_grid(self) -> None:
        self.grid = []
        for y in range(self.grid_start[1], self.grid_start[1] + self.grid_size[1]):
            for x in range(self.grid_start[0], self.grid_start[0] + self.grid_size[0]):
                self.grid.append((x, y))

    def bind(self, on_accept: Callable = None, on_cancel: Callable = None):
        self.on_accept = on_accept
        self.on_cancel = on_cancel
        return self

    def update(self, scene) -> None:
        super().update(scene)
        self.graphic.update(scene.dt)

        screen_w, screen_h = scene.surface.get_size()
        self.out_x = self.x_percent * (screen_w - self.out_w)
        self.out_y = self.y_percent * (screen_h - self.out_h)

        if scene.selection.using_mouse:
            self.selected = (
                0 <= scene.selection.mouse_x - self.out_x <= self.out_w and \
                0 <= scene.selection.mouse_y - self.out_y <= self.out_h
            )
        else:
            self.selected = scene.selection.get_pos() in self.grid

        if self.selected:
            scene.selection.set_selected_object(self)

    def draw(self, scene) -> None:
        frame = self.graphic.get_frame().convert_alpha()
        if self.selected:
            frame.fill((96, 96, 96), special_flags=pygame.BLEND_RGB_ADD)
        scene.surface.blit(frame, (self.out_x, self.out_y))
