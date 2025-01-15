import pygame
from abc import abstractmethod

from components.camera import Camera
from components.object import SimulatedObject
from components.statemachine import State, StateMachine
from components.ui import Selection
import core.input as input


class Scene(State):
    # passed to __init__
    surface: pygame.Surface = None

    # set on enter per-instance
    camera: Camera = None
    selection: Selection = None
    objects: list[SimulatedObject] = []

    # updated each execute call
    dt: float = 0
    action_buffer: input.InputBuffer = None
    mouse_buffer: input.InputBuffer = None

    def __init__(self, statemachine: StateMachine, surface: pygame.Surface):
        super().__init__(statemachine)
        self.surface = surface
        self.camera = None
        self.objects = []

    @abstractmethod
    def enter(self) -> None: ...

    @abstractmethod
    def execute(self) -> None: ...

    @abstractmethod
    def exit(self) -> None: ...
