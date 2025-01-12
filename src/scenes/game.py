import pygame

import core.constants as const
import core.assets as asset
import core.input as input
from scenes.scene import Scene

import scenes.menu

MAX_X = const.WINDOW_WIDTH - asset.DEBUG_SPRITE.get_width()
MAX_Y = const.WINDOW_HEIGHT - asset.DEBUG_SPRITE.get_height()


class Game(Scene):

    pirate_x = 0
    pirate_y = 0
    pirate_vx = 1
    pirate_vy = 1
    pirate_speed = 64

    def enter(self) -> None:
        pygame.mixer.Channel(0).play(asset.DEBUG_THEME, -1)

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
            self.statemachine.change_state(scenes.menu.Menu)
            return

        self.pirate_x += self.pirate_vx * self.pirate_speed * dt
        self.pirate_y += self.pirate_vy * self.pirate_speed * dt

        if self.pirate_vx > 0 and self.pirate_x > MAX_X:
            self.pirate_vx = -1
        elif self.pirate_vx < 0 and self.pirate_x < 0:
            self.pirate_vx = 1

        if self.pirate_vy > 0 and self.pirate_y > MAX_Y:
            self.pirate_vy = -1
        elif self.pirate_vy < 0 and self.pirate_y < 0:
            self.pirate_vy = 1

        surface.fill(const.MAGENTA)
        surface.blit(asset.DEBUG_SPRITE, (self.pirate_x, self.pirate_y))

    def exit(self) -> None:
        pygame.mixer.Channel(0).stop()
