from abc import abstractmethod
from components.statemachine import State
import core.input as t

import pygame


class Scene(State):
    @abstractmethod
    def enter(self) -> None: ...

    @abstractmethod
    def execute(
        self,
        surface: pygame.Surface,
        dt: float,
        action_buffer: t.InputBuffer,
        mouse_buffer: t.InputBuffer,
    ) -> None: ...

    @abstractmethod
    def exit(self) -> None: ...
