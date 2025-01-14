import pygame
from abc import abstractmethod

from components.camera import Camera
from components.object import GameObject
from components.statemachine import State, StateMachine
import core.input as input


class Scene(State):
    surface: pygame.Surface = None
    camera: Camera = None
    objects: list[GameObject] = []

    def __init__(self, statemachine: StateMachine, surface: pygame.Surface):
        super().__init__(statemachine)
        self.surface = surface
        self.camera = None
        self.objects = []

    @abstractmethod
    def enter(self) -> None: ...

    @abstractmethod
    def execute(
        self,
        dt: float,
        action_buffer: input.InputBuffer,
        mouse_buffer: input.InputBuffer
    ) -> None: ...

    @abstractmethod
    def exit(self) -> None: ...
