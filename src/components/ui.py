import pygame
from components.object import UIObject
import core.input as input

class Selection:
    def __init__(self, grid_w: int, grid_h: int) -> None:
        self.x, self.y = 0, 0
        self.grid_w, self.grid_h = grid_w, grid_h
        self.mouse_x, self.mouse_y = 0, 0
        self.selected_object = None
        self.using_mouse = True
    
    def update(self, scene) -> None:
        # first update keyboard
        dx = (scene.action_buffer[input.Action.RIGHT] == input.InputState.PRESSED) - \
            (scene.action_buffer[input.Action.LEFT] == input.InputState.PRESSED)
        dy = (scene.action_buffer[input.Action.DOWN] == input.InputState.PRESSED) - \
            (scene.action_buffer[input.Action.UP] == input.InputState.PRESSED)
        if dx != 0 or dy != 0:
            if self.using_mouse:
                self.using_mouse = False
                pygame.mouse.set_visible(False)
            else:
                self.increment(dx, dy)
            return

        # then update mouse if necessary
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if mouse_x != self.mouse_x or mouse_y != self.mouse_y:
            if not self.using_mouse:
                self.using_mouse = True
                pygame.mouse.set_visible(True)
            self.mouse_x, self.mouse_y = mouse_x, mouse_y
    
    def get_pos(self) -> tuple[float, float]:
        return (self.x, self.y)
            
    def increment(self, dx: int, dy: int) -> None:
        if self.selected_object is None:
            return
        i = 0
        while self.get_pos() in self.selected_object.grid and \
                i < len(self.selected_object.grid):
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
        if self.using_mouse:
            self.x, self.y = object.grid[0]
        self.selected_object = object
