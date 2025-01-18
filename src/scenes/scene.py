from abc import abstractmethod
from components.statemachine import State
import core.input as i

import pygame


class Scene(State):
    @abstractmethod
    def enter(self) -> None: ...

    @abstractmethod
    def execute(
        self,
        surface: pygame.Surface,
        dt: float,
        action_buffer: i.InputBuffer,
        mouse_buffer: i.InputBuffer
    ) -> None: ...

    @abstractmethod
    def exit(self) -> None: ...
