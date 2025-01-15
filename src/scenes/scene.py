import pygame
from abc import abstractmethod
from typing import Callable, Hashable

from components.camera import Camera
from components.object import AbstractObject
from components.statemachine import State, StateMachine
from components.ui import Selection
import core.input as input


class SceneTimer:
    def __init__(
            self,
            id: Hashable,
            time: float,
            method: Callable,
            *args,
            **kwargs
        ):
        self.id = id
        self.current_time = time
        self.method = method
        self.args = args
        self.kwargs = kwargs

    def __hash__(self):
        return self.id

    def __eq__(self, value):
        if isinstance(value, SceneTimer):
            return self.id == value.id
        return self.id == value

    # update timer. returns true if still active
    def update(self, dt: float) -> bool:
        self.current_time -= dt
        if self.current_time <= 0:
            self.method(*self.args, **self.kwargs)
            return False
        return True


class Scene(State):
    # handled in __init__
    surface: pygame.Surface = None
    timers: list[SceneTimer] = []

    # set on enter per-instance
    camera: Camera = None
    selection: Selection = None

    # updated each execute call
    dt: float = 0
    action_buffer: input.InputBuffer = None
    mouse_buffer: input.InputBuffer = None

    def __init__(self, statemachine: StateMachine, surface: pygame.Surface):
        super().__init__(statemachine)
        self.surface = surface
        self.timers = []

    @abstractmethod
    def enter(self) -> None: ...

    @abstractmethod
    def execute(self) -> None: ...

    @abstractmethod
    def exit(self) -> None: ...

    # util function to update the important scene things
    def update(self):
        self.update_timers()
        if self.camera: self.camera.update(self)
        if self.selection: self.selection.update(self)

    def update_timers(self):
        i = len(self.timers) - 1
        while i >= 0:
            if not self.timers[i].update(self.dt):
                self.timers.pop(i)
            i -= 1

    def set_timer(self, id: Hashable, *args, **kwargs):
        timer = SceneTimer(id, *args, **kwargs)
        try:
            idx = self.timers.index(id)
            self.timers[idx] = timer # overwrite timer if it already exists
        except ValueError:
            self.timers.append(timer) # otherwise make a new one
