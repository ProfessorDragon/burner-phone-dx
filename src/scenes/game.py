import pygame
import random

from components.graphic import StaticImage
import core.constants as const
import core.assets as asset
import core.input as input
from components.object import SimulatedObject, GameObject
from components.camera import Camera

from scenes.scene import Scene
import scenes.menu


class Game(Scene):
    REBOUND_X = const.WINDOW_WIDTH - asset.DEBUG_SPRITE.get_width()
    REBOUND_Y = const.WINDOW_HEIGHT - asset.DEBUG_SPRITE.get_height()

    def enter(self) -> None:
        self.camera = Camera(SimulatedObject(*const.WINDOW_CENTRE))
        self.objects = []
        for i in range(10):
            obj = GameObject(StaticImage(asset.DEBUG_SPRITE))
            obj.x = random.randint(0, self.REBOUND_X)
            obj.y = random.randint(0, self.REBOUND_Y)
            obj.vx = 64
            obj.vy = 64
            self.objects.append(obj)
        # pygame.mixer.Channel(0).play(asset.DEBUG_THEME, -1)

    def execute(
        self,
        dt: float,
        action_buffer: input.InputBuffer,
        mouse_buffer: input.InputBuffer
    ) -> None:
        if action_buffer[input.Action.START] == input.InputState.PRESSED:
            self.statemachine.change_state(scenes.menu.Menu)
            return

        for obj in self.objects:
            if (
                obj.vx > 0 and obj.x > self.REBOUND_X or
                obj.vx < 0 and obj.x < 0
            ):
                obj.vx *= -1
                self.camera.set_camera_shake(0.4)

            if (
                obj.vy > 0 and obj.y > self.REBOUND_Y or
                obj.vy < 0 and obj.y < 0
            ):
                obj.vy *= -1
                self.camera.set_camera_shake(0.4)

            obj.update(dt)

        self.camera.update(dt)

        self.surface.fill(const.MAGENTA)

        for obj in self.objects:
            obj.draw(self)

    def exit(self) -> None:
        pygame.mixer.Channel(0).stop()
