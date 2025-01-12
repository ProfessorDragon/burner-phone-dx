import pygame

import core.constants as const
import core.input as input
from scenes.scene import Scene

import scenes.game


class Menu(Scene):
    def enter(self) -> None:
        pass

    def execute(
        self,
        surface: pygame.Surface,
        dt: float,
        action_buffer: input.InputBuffer,
        mouse_buffer: input.InputBuffer
    ) -> None:
        if (
            action_buffer[input.Action.START] == input.InputState.PRESSED or
            mouse_buffer[input.MouseButton.LEFT] == input.InputState.PRESSED
        ):
            self.statemachine.change_state(scenes.game.Game)
            return
        surface.fill(const.GREEN)

    def exit(self) -> None:
        pass
