import pygame
from components.graphic import Graphic


class SimulatedObject:
    x: float = 0
    y: float = 0
    vx: float = 0
    vy: float = 0
    ax: float = 0
    ay: float = 0

    def __init__(self, x: float = 0, y: float = 0) -> None:
        self.x = x
        self.y = y

    def update(self, scene) -> None:
        self.vx += self.ax * scene.dt
        self.vy += self.ay * scene.dt
        self.x += self.vx * scene.dt
        self.y += self.vy * scene.dt

    def get_pos(self) -> tuple[float, float]:
        return (self.x, self.y)


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


class UIObject(SimulatedObject):
    def __init__(
            self,
            graphic: Graphic,
            x_percent: float,
            y_percent: float,
            grid_start: tuple[int, int],
            grid_end: tuple[int, int] | None = None
        ):
        super().__init__(0, 0)
        self.graphic = graphic
        self.x_percent, self.y_percent = x_percent, y_percent
        self.out_x, self.out_h = 0, 0 # real position of the object on screen
        self.out_w, self.out_h = graphic.get_frame().get_size() # for mouse hitbox detection
        self.grid_start = grid_start
        self.grid_end = grid_start if grid_end is None else grid_end
        self.generate_grid()
        self.selected = False
    
    def generate_grid(self) -> None:
        self.grid = []
        for y in range(self.grid_start[1], self.grid_end[1] + 1):
            for x in range(self.grid_start[0], self.grid_end[0] + 1):
                self.grid.append((x, y))

    def update(self, scene) -> None:
        super().update(scene)
        self.graphic.update(scene.dt)

        screen_w, screen_h = scene.surface.get_size()
        self.out_x = self.x_percent * (screen_w - self.out_w)
        self.out_y = self.y_percent * (screen_h - self.out_h)

        prev_selected = self.selected
        if scene.selection.using_mouse:
            self.selected = (
                0 <= scene.selection.mouse_x - self.out_x <= self.out_w and \
                0 <= scene.selection.mouse_y - self.out_y <= self.out_h
            )
        else:
            self.selected = scene.selection.get_pos() in self.grid

        if prev_selected != self.selected:
            scene.selection.set_selected_object(self)

    def draw(self, scene) -> None:
        frame = self.graphic.get_frame().convert_alpha()
        if self.selected:
            frame.fill((64, 64, 64), special_flags=pygame.BLEND_RGB_ADD)
        scene.surface.blit(frame, (self.out_x, self.out_y))