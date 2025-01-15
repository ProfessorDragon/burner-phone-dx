from components.object import GameObject, UIObject
from components.ui import Selection
import core.constants as const
import core.input as input
import core.assets as assets
from components.graphic import AnimationPlayer, StaticImage, StaticText
from components.camera import Camera
from components.camera import SimulatedObject

from scenes.scene import Scene
import scenes.game


class Menu(Scene):
    def enter(self) -> None:
        self.camera = Camera(SimulatedObject())
        self.selection = Selection(3, 2) # creates a simulated 2x2 grid of ui objects
        self.objects = []
        self.objects.append(GameObject(AnimationPlayer(
            "spin", assets.DEBUG_FRAMES, 0.1), -32, -32))
        self.objects.append(UIObject(StaticImage(assets.DEBUG_SPRITE), 0, 0, (0, 0)))
        self.objects.append(UIObject(StaticText("Hi there", assets.DEBUG_FONT), .5, .2, (1, 0)))
        self.objects.append(UIObject(StaticText("LONG TEXT"*4, assets.DEBUG_FONT), 0, .8, (0, 1), (1, 1)))
        self.objects.append(UIObject(StaticImage(assets.DEBUG_SPRITE), 1, .5, (2, 0), (2, 1)))

    def execute(self) -> None:
        if self.action_buffer[input.Action.START] == input.InputState.PRESSED:
            self.statemachine.change_state(scenes.game.Game)
            return

        if self.action_buffer[input.Action.A] == input.InputState.HELD:
            self.camera.add_camera_shake(self.dt)

        self.camera.update(self)
        self.selection.update(self)
        for obj in self.objects:
            obj.update(self)

        self.surface.fill(const.CYAN)
        for obj in self.objects:
            obj.draw(self)

        trauma_text = assets.DEBUG_FONT.render(
            f"TRAUMA {self.camera.trauma:.2f}", False, const.RED, const.BLACK)
        shake_text = assets.DEBUG_FONT.render(
            f"SHAKE {self.camera.shake:.2f}", False, const.BLUE, const.BLACK)
        self.surface.blit(trauma_text, (0, 24))
        self.surface.blit(shake_text, (0, 36))

    def exit(self) -> None:
        pass
