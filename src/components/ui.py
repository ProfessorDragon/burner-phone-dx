import pygame
from enum import IntEnum
from typing import Any, Callable, Self
import core.assets as assets
import core.constants as const
import core.input as input
from components.object import AbstractObject
from components.graphic import Graphic, StaticImage, StaticText
from utilities.math import clamp

class InputBinding:
    def __init__(
            self,
            input_enum: IntEnum,
            input_state: IntEnum,
            method: Callable[[], bool]
        ) -> None:
        self.input_enum = input_enum
        self.input_state = input_state
        self.method = method
    
    def call(self, scene) -> bool:
        if isinstance(self.input_enum, input.Action):
            if self.input_state == input.InputState.REPEATED:
                if scene.selection.is_pressed_or_repeated(scene, self.input_enum):
                    return self.method()
                return None
            if scene.action_buffer[self.input_enum] == self.input_state:
                return self.method()
        if isinstance(self.input_enum, input.MouseButton):
            if scene.mouse_buffer[self.input_enum] == self.input_state:
                return self.method()
        return None


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

        # real position of the object on screen
        self.out_x, self.out_y = 0, 0

        # stored for hit detection
        self.out_w, self.out_h = graphic.get_frame().get_size()
        # number of buffer pixels to add around the graphic for hit detection
        self.hit_inflate = 4

        # grid
        self.grid_start = grid_start
        self.grid_size = grid_size
        self.generate_grid()

        # bindings
        self.selected = False
        self.bindings: list[InputBinding] = []

    def generate_grid(self) -> None:
        self.grid = []
        for y in range(self.grid_start[1], self.grid_start[1] + self.grid_size[1]):
            for x in range(self.grid_start[0], self.grid_start[0] + self.grid_size[0]):
                self.grid.append((x, y))
    
    def bind(self, *args) -> Self:
        self.bindings.append(InputBinding(*args))
        return self

    def bind_click(self, method: Callable) -> Self:
        self.bind(input.Action.A, input.InputState.RELEASED, method)
        self.bind(input.MouseButton.LEFT, input.InputState.RELEASED, method)
        return self

    def update(self, scene) -> None:
        super().update(scene)
        self.graphic.update(scene.dt)

        screen_w, screen_h = scene.surface.get_size()
        self.out_x = self.x_percent * (screen_w - self.out_w)
        self.out_y = self.y_percent * (screen_h - self.out_h)

        if scene.selection.using_mouse:
            self.selected = (
                -self.hit_inflate <= scene.selection.mouse_x - self.out_x <= self.out_w + self.hit_inflate and \
                -self.hit_inflate <= scene.selection.mouse_y - self.out_y <= self.out_h + self.hit_inflate
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


# preset ui object for modifying boolean values
class Checkbox(UIObject):
    def __init__(
            self,
            label: str,
            enabled: bool,
            x_percent: float,
            y_percent: float,
            grid_start: tuple[int, int]
        ):
        self.label = label
        self.enabled = enabled

        # create graphics beforehand cause there's only 2
        self.true_g = self.create_graphic(True)
        self.false_g = self.create_graphic(False)

        # super
        graphic = self.true_g if self.enabled else self.false_g
        super().__init__(graphic, x_percent, y_percent, grid_start)

        # bindings
        self.bind_click(self.toggle)
        self.on_change = None
    
    def create_graphic(self, enabled: bool) -> Graphic:
        text = StaticText(self.label, assets.DEBUG_FONT).get_frame()
        if enabled: image = StaticText("N", assets.DEBUG_FONT, const.RED).get_frame()
        else: image = StaticText("Y", assets.DEBUG_FONT, const.GREEN).get_frame()

        surf = pygame.Surface((120, text.get_height()), pygame.SRCALPHA)
        surf.blit(text, (0, 0))
        surf.blit(image, (surf.get_width() - image.get_width(), 0))
        
        return StaticImage(surf)
    
    def update(self, scene) -> None:
        super().update(scene)
        self.graphic = self.true_g if self.enabled else self.false_g
    
    def toggle(self):
        self.enabled = not self.enabled
        if callable(self.on_change):
            self.on_change(self.enabled)
    
    def bind_change(self, on_change: Callable[[bool], Any] = None) -> Self:
        self.on_change = on_change
        return self


# preset ui object for modifying numerical values
class Slider(UIObject):
    def __init__(
            self,
            label: str,
            value: float,
            x_percent: float,
            y_percent: float,
            grid_start: tuple[int, int]
        ):
        self.label = label
        self.value = value

        # constants
        self.step = 0.05
        self.slide_x, self.slide_w = 120, 64

        # super
        super().__init__(self.create_graphic(), x_percent, y_percent, grid_start)

        # bindings
        self.bind(input.Action.LEFT, input.InputState.REPEATED, self.decrement)
        self.bind(input.Action.RIGHT, input.InputState.REPEATED, self.increment)
        self.bind(input.MouseButton.LEFT, input.InputState.HELD, self.mouse_drag)
        self.mouse_value = 0
        self.on_change = None
    
    def create_graphic(self) -> Graphic:
        text = StaticText(self.label, assets.DEBUG_FONT).get_frame()
        num = StaticText(str(int(self.value*100)), assets.DEBUG_FONT).get_frame()

        surf = pygame.Surface((self.slide_x + self.slide_w, num.get_height()), pygame.SRCALPHA)
        surf.blit(text, (0, 0))
        surf.blit(num, (self.slide_x - 5 - num.get_width(), 0))
        surf.blit(assets.DEBUG_IMAGE, (self.slide_x, 4), (0, 4, self.slide_w, surf.get_height() - 8))
        surf.blit(assets.DEBUG_IMAGE, (self.slide_x, 0), (0, 0, self.value * self.slide_w, surf.get_height()))

        return StaticImage(surf)

    def update(self, scene) -> None:
        super().update(scene)
        rel = scene.selection.mouse_x - self.out_x - self.slide_x
        if rel >= -self.hit_inflate:
            # store the value it WOULD be if the mouse was dragging it
            self.mouse_value = round(rel / self.slide_w / self.step) * self.step
        else:
            # clicking on the label shouldn't change the slider's value
            self.mouse_value = self.value
    
    def set(self, value: float) -> None:
        prev = self.value
        self.value = clamp(round(value, 2), 0, 1)
        if prev != self.value and callable(self.on_change):
            self.graphic = self.create_graphic()
            self.on_change(self.value)
    
    def decrement(self):
        self.set(self.value - self.step * 2)
        return False

    def increment(self):
        self.set(self.value + self.step * 2)
        return False
    
    def mouse_drag(self):
        self.set(self.mouse_value)
    
    def bind_change(self, on_change: Callable[[float], Any] = None) -> Self:
        self.on_change = on_change
        return self


# handles the grid and mouse based selection of ui objects
class Selection:
    def __init__(self, grid_w: int, grid_h: int) -> None:
        self.x, self.y = 0, 0
        self.grid_w, self.grid_h = grid_w, grid_h
        self.empty_spaces = []
        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
        self.selected_object: UIObject = None
        self.using_mouse = False
        self.repeating_direction = False
    
    def append_empty(self, x: int, y: int) -> None:
        self.empty_spaces.append((x, y))
    
    def is_pressed_or_repeated(self, scene, input_enum: IntEnum) -> bool:
        return scene.is_pressed(input_enum) or \
            (self.repeating_direction and scene.is_held(input_enum))

    def update(self, scene) -> None:
        # detect accept/cancel inputs FIRST since mouse detection sets selected_object to None
        consume_input = False
        if self.selected_object is not None:
            for binding in self.selected_object.bindings:
                if binding.call(scene) is False:
                    consume_input = True

        # detect changes in selection
        # update keyboard
        dx = self.is_pressed_or_repeated(scene, input.Action.RIGHT) - \
            self.is_pressed_or_repeated(scene, input.Action.LEFT)
        dy = self.is_pressed_or_repeated(scene, input.Action.DOWN) - \
            self.is_pressed_or_repeated(scene, input.Action.UP)
        if dx != 0 or dy != 0:
            if self.using_mouse:
                self.using_mouse = False
            if self.selected_object is not None:
                if not consume_input: self.increment(dx, dy)
                self.repeating_direction = False
                scene.set_timer("repeat_direction", 0.1 if consume_input else 0.15, self.repeat_direction)
        else:
            # then update mouse if necessary
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if mouse_x != self.mouse_x or mouse_y != self.mouse_y:
                if not self.using_mouse:
                    self.using_mouse = True
                self.mouse_x, self.mouse_y = mouse_x, mouse_y
                self.selected_object = None

    def get_pos(self) -> tuple[float, float]:
        return (self.x, self.y)
        
    def increment(self, dx: int, dy: int) -> None:
        if self.selected_object is None:
            return
        avoid_spaces = self.selected_object.grid + self.empty_spaces
        i = 0
        while self.get_pos() in avoid_spaces and i < len(avoid_spaces):
            if self.grid_w > 0:
                self.x = (self.x + dx) % self.grid_w
            if self.grid_h > 0:
                self.y = (self.y + dy) % self.grid_h
            i += 1
    
    def repeat_direction(self) -> None:
        self.repeating_direction = True

    def set_selected_object(self, object: UIObject) -> None:
        if object == self.selected_object:
            return
        if self.selected_object is not None:
            self.selected_object.selected = False
        if self.using_mouse and len(object.grid) > 0:
            self.x, self.y = object.grid[0]
        self.selected_object = object
