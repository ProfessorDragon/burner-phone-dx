import pygame
# import random

import core.input as input
import core.constants as const
# from components.graphic import StaticImage
# import core.assets as asset
# from components.object import AbstractObject, SimulatedPosition, GameObject
# from components.camera import Camera

from scenes.scene import Scene
import scenes.scenemapping as scene
from components.statemachine import statemachine_change_state


class Game(Scene):
    # REBOUND_X = const.WINDOW_WIDTH - asset.DEBUG_SPRITE.get_width()
    # REBOUND_Y = const.WINDOW_HEIGHT - asset.DEBUG_SPRITE.get_height()
    #
    # paused = False
    # pause_overlay = pygame.Surface(const.WINDOW_SIZE)
    # pause_overlay.fill(const.WHITE)
    # pause_overlay.set_alpha(128)

    def enter(self) -> None:
        # self.camera = Camera(SimulatedPosition(*const.WINDOW_CENTRE))
        # self.objects: list[AbstractObject] = []
        # for i in range(10):
        #     obj = GameObject(StaticImage(asset.DEBUG_SPRITE))
        #     obj.x = random.randint(0, self.REBOUND_X)
        #     obj.y = random.randint(0, self.REBOUND_Y)
        #     obj.vx = random.randint(-64, 64)
        #     obj.vy = random.randint(-64, 64)
        #     self.objects.append(obj)
        # pygame.mixer.Channel(0).play(asset.DEBUG_THEME, -1)
        pass

    def execute(
        self,
        surface: pygame.Surface,
        dt: float,
        action_buffer: input.InputBuffer,
        mouse_buffer: input.InputBuffer
    ) -> None:
        if action_buffer[input.Action.START] == input.InputState.PRESSED:
            statemachine_change_state(self.statemachine, scene.SceneState.MENU)
            return

        # if action_buffer[input.Action.SELECT] == input.InputState.PRESSED:
        #     self.paused = not self.paused
        #     # Might want to enable pause UI here
        #     # Set Pause UI overlay to top option
        #
        # if self.paused:
        #     pass
        #
        # else:
        #     for obj in self.objects:
        #         if (
        #             obj.vx > 0 and obj.x > self.REBOUND_X or
        #             obj.vx < 0 and obj.x < 0
        #         ):
        #             obj.vx *= -1
        #             self.camera.set_camera_shake(0.4)
        #
        #         if (
        #             obj.vy > 0 and obj.y > self.REBOUND_Y or
        #             obj.vy < 0 and obj.y < 0
        #         ):
        #             obj.vy *= -1
        #             self.camera.set_camera_shake(0.4)
        #
        #         obj.update(self)

        surface.fill(const.MAGENTA)

        # for obj in self.objects:
        #     obj.draw(self)
        #
        # if self.paused:
        #     self.surface.blit(self.pause_overlay, (0, 0))

    def exit(self) -> None:
        # pygame.mixer.Channel(0).stop()
        pass
