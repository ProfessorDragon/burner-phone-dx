import pygame
import random

from components.graphic import StaticImage
import core.constants as const
import core.assets as asset
import core.input as input
from components.object import AbstractObject, SimulatedObject, GameObject
from components.camera import Camera

from scenes.scene import Scene
import scenes.menu


class Game(Scene):
    REBOUND_X = const.WINDOW_WIDTH - asset.DEBUG_SPRITE.get_width()
    REBOUND_Y = const.WINDOW_HEIGHT - asset.DEBUG_SPRITE.get_height()

    paused = False
    pause_overlay = pygame.Surface(const.WINDOW_SIZE)
    pause_overlay.fill(const.WHITE)
    pause_overlay.set_alpha(128)

    def enter(self) -> None:
        self.camera = Camera(SimulatedObject(*const.WINDOW_CENTRE))
        self.objects: list[AbstractObject] = []
        for i in range(10):
            obj = GameObject(StaticImage(asset.DEBUG_SPRITE))
            obj.x = random.randint(0, self.REBOUND_X)
            obj.y = random.randint(0, self.REBOUND_Y)
            obj.vx = random.randint(-64, 64)
            obj.vy = random.randint(-64, 64)
            self.objects.append(obj)
        pygame.mixer.Channel(0).play(asset.DEBUG_THEME, -1)

    def execute(self) -> None:
        if self.action_buffer[input.Action.START] == input.InputState.PRESSED:
            self.statemachine.change_state(scenes.menu.Menu)
            return

        if self.action_buffer[input.Action.SELECT] == input.InputState.PRESSED:
            self.paused = not self.paused
            # Might want to enable pause UI here
            # Set Pause UI overlay to top option

        if self.paused:
            pass
    
        else:
            self.update()

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

                obj.update(self)

        self.surface.fill(const.MAGENTA)

        for obj in self.objects:
            obj.draw(self)

        if self.paused:
            self.surface.blit(self.pause_overlay, (0, 0))

    def exit(self) -> None:
        pygame.mixer.Channel(0).stop()
