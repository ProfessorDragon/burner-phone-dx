import pygame

import core.constants as const
import core.input as input
import core.assets as assets
from components.animation import AnimationPlayer
from components.camera import Camera
from components.camera import SimulatedObject

from scenes.scene import Scene
import scenes.game


DEBUG = AnimationPlayer("spin", assets.DEBUG_FRAMES, 0.1)
CAMERA = Camera(SimulatedObject())


class Menu(Scene):
    def enter(self) -> None:
        DEBUG.reset()

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

        if action_buffer[input.Action.SELECT] == input.InputState.HELD:
            CAMERA.add_camera_shake(dt)

        DEBUG.update(dt)
        CAMERA.update(dt)

        surface.fill(const.CYAN)
        surface.blit(DEBUG.get_frame(), CAMERA.world_to_screen_shake(-32, -32))
        trauma_text = assets.DEBUG_FONT.render(
            f"TRAUMA {CAMERA.trauma:.2f}", False, const.RED, const.BLACK)
        shake_text = assets.DEBUG_FONT.render(
            f"SHAKE {CAMERA.shake:.2f}", False, const.BLUE, const.BLACK)
        surface.blit(trauma_text, (0, 24))
        surface.blit(shake_text, (0, 36))

    def exit(self) -> None:
        pass
