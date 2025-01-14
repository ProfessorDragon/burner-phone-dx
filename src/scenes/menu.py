import pygame

from components.object import GameObject
import core.constants as const
import core.input as input
import core.assets as assets
from components.graphic import AnimationPlayer
from components.camera import Camera
from components.camera import SimulatedObject

from scenes.scene import Scene
import scenes.game


class Menu(Scene):
    def enter(self) -> None:
        self.camera = Camera(SimulatedObject())
        self.DEBUG = GameObject(AnimationPlayer("spin", assets.DEBUG_FRAMES, 0.1), -32, -32)

    def execute(
        self,
        dt: float,
        action_buffer: input.InputBuffer,
        mouse_buffer: input.InputBuffer
    ) -> None:
        if action_buffer[input.Action.START] == input.InputState.PRESSED:
            self.statemachine.change_state(scenes.game.Game)
            return

        if action_buffer[input.Action.SELECT] == input.InputState.HELD:
            self.camera.add_camera_shake(dt)

        self.camera.update(dt)
        self.DEBUG.update(dt)

        self.surface.fill(const.CYAN)
        self.DEBUG.draw(self)

        trauma_text = assets.DEBUG_FONT.render(
            f"TRAUMA {self.camera.trauma:.2f}", False, const.RED, const.BLACK)
        shake_text = assets.DEBUG_FONT.render(
            f"SHAKE {self.camera.shake:.2f}", False, const.BLUE, const.BLACK)
        self.surface.blit(trauma_text, (0, 24))
        self.surface.blit(shake_text, (0, 36))

    def exit(self) -> None:
        pass
