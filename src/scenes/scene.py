from abc import abstractmethod
from enum import IntEnum
from components.statemachine import State
import core.input as t

import pygame


class RenderLayer(IntEnum):
    BACKGROUND = -2
    PLAYER_BG = -1
    PLAYER = 0
    PLAYER_FG = 1
    FOREGROUND = 2


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


# for clarity
def scene_reset(scene: Scene):
    scene.enter()
