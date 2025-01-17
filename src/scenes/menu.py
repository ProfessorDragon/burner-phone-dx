import core.constants as const
import core.input as input
# import core.assets as assets
# from components.object import AbstractObject, GameObject
# from components.ui import Checkbox, Selection, ScreenObject, Slider, UIObject
# from components.graphic import AnimationPlayer, DynamicText, StaticImage, StaticText
# from components.camera import Camera

import pygame
from scenes.scene import Scene
import scenes.scenemapping as scene
from components.statemachine import statemachine_change_state


class Menu(Scene):
    def enter(self) -> None:
        # self.camera = Camera(SimulatedPosition())
        # self.selection = Selection(1, 5)
        #
        # self.objects: list[AbstractObject] = []
        # self.objects.append(
        #     Slider("Music", .5, .1,  .2, (0, 0))
        #     .bind_change(lambda value: self.debug_text(str(value)))
        # )
        # self.objects.append(
        #     Slider("SFX", .5, .1,  .25, (0, 1))
        #     .bind_change(lambda value: self.debug_text(str(value)))
        # )
        # self.objects.append(
        #     Checkbox("Fullscreen", False, .1, .3, (0, 2))
        #     .bind_change(lambda enabled: self.debug_text(str(enabled)))
        # )
        # self.objects.append(
        #     Checkbox("Vsync", False, .1, .35, (0, 3))
        #     .bind_change(lambda enabled: self.debug_text(str(enabled)))
        # )
        # self.objects.append(
        #     Checkbox("Show FPS", False, .1, .4, (0, 4))
        #     .bind_change(lambda enabled: self.debug_text(str(enabled)))
        # )
        #
        # self.objects.append(GameObject(AnimationPlayer(
        #     "spin", assets.DEBUG_FRAMES, 0.2), -32, -32))
        #
        # self.debug_text_g = DynamicText("", assets.DEBUG_FONT)
        # self.objects.append(ScreenObject(self.debug_text_g, .5, 1))
        pass

    # def debug_text(self, text: str) -> None:
    #     self.debug_text_g.text = text
    #     if text:
    #         self.set_timer("debug_text", 1.0, self.debug_text, "")

    def execute(
        self,
        surface: pygame.Surface,
        dt: float,
        action_buffer: input.InputBuffer,
        mouse_buffer: input.InputBuffer
    ) -> None:
        if action_buffer[input.Action.START] == input.InputState.PRESSED:
            statemachine_change_state(self.statemachine, scene.SceneState.GAME)
            return

        # if action_buffer[input.Action.A] == input.InputState.HELD:
        #     self.camera.add_camera_shake(self.dt)
        #
        # for obj in self.objects:
        #     obj.update(self)

        surface.fill(const.WHITE)

        # for obj in self.objects:
        #     obj.draw(self)
        #
        # trauma_text = assets.DEBUG_FONT.render(
        #     f"TRAUMA {self.camera.trauma:.2f}", False, const.RED, const.BLACK)
        # shake_text = assets.DEBUG_FONT.render(
        #     f"SHAKE {self.camera.shake:.2f}", False, const.BLUE, const.BLACK)
        # self.surface.blit(trauma_text, (0, 24))
        # self.surface.blit(shake_text, (0, 36))

    def exit(self) -> None:
        pass
