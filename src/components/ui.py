import pygame
import core.input as input
from components.object import UIObject


class Selection:
    def __init__(self, grid_w: int, grid_h: int) -> None:
        self.x, self.y = 0, 0
        self.grid_w, self.grid_h = grid_w, grid_h
        self.empty_spaces = []
        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
        self.selected_object = None
        self.using_mouse = False

    def update(self, scene) -> None:
        # detect accept/cancel inputs FIRST since mouse detection sets selected_object to None
        if self.selected_object is not None:
            if callable(self.selected_object.on_accept) and (
                    scene.action_buffer[input.Action.A] == input.InputState.PRESSED or
                    scene.mouse_buffer[input.MouseButton.LEFT] == input.InputState.PRESSED
                ):
                self.selected_object.on_accept()
            elif callable(self.selected_object.on_cancel) and (
                    scene.action_buffer[input.Action.B] == input.InputState.PRESSED or
                    scene.mouse_buffer[input.MouseButton.RIGHT] == input.InputState.PRESSED
                ):
                self.selected_object.on_cancel()

        # detect changes in selection
        # update keyboard
        dx = (scene.action_buffer[input.Action.RIGHT] == input.InputState.PRESSED) - \
            (scene.action_buffer[input.Action.LEFT] == input.InputState.PRESSED)
        dy = (scene.action_buffer[input.Action.DOWN] == input.InputState.PRESSED) - \
            (scene.action_buffer[input.Action.UP] == input.InputState.PRESSED)
        if dx != 0 or dy != 0:
            if self.using_mouse:
                self.using_mouse = False
            if self.selected_object is not None:
                self.increment(dx, dy)
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

    def set_selected_object(self, object: UIObject) -> None:
        if object == self.selected_object:
            return
        if self.selected_object is not None:
            self.selected_object.selected = False
        if self.using_mouse and len(object.grid) > 0:
            self.x, self.y = object.grid[0]
        self.selected_object = object
