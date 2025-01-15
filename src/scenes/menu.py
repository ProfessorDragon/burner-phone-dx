import core.constants as const
import core.input as input
import core.assets as assets
from components.object import AbstractObject, GameObject, ScreenObject, UIObject
from components.ui import Selection
from components.graphic import AnimationPlayer, DynamicText, StaticImage, StaticText
from components.camera import Camera
from components.camera import SimulatedObject

from scenes.scene import Scene
import scenes.game


class Menu(Scene):
    def enter(self) -> None:
        self.camera = Camera(SimulatedObject())
        self.selection = Selection(3, 2) # creates a simulated 3x2 grid of ui objects
        self.selection.empty_spaces.append((2, 0)) # indicates there is nothing in this space and should be skipped over

        self.objects: list[AbstractObject] = []
        self.debug_anim_g = AnimationPlayer("spin", assets.DEBUG_FRAMES, 0.2)
        self.objects.append( # 1
            UIObject(self.debug_anim_g, .1,  .2, (0, 0))
            .bind(lambda: self.debug_text("Pressed 1"))
        )
        self.objects.append( # 2
            UIObject(StaticText("""\
<-- animated button
   text button ^^
vv random object vv""", assets.DEBUG_FONT), .5, .2, (1, 0))
            .bind(lambda: self.debug_text("Pressed 2"))
        )
        self.objects.append( # 3
            UIObject(StaticText("""\
THESE ARE BUTTONS! ACTIVATE ME USING Z OR LEFT CLICK.
move the mouse and hover over buttons!
use wasd/arrows to select buttons with the keyboard!""", assets.DEBUG_FONT), 0, .8, (0, 1), (2, 1))
            .bind(lambda: self.debug_text("Pressed 3"))
        )
        self.objects.append( # 4
            UIObject(StaticImage(assets.DEBUG_SPRITE), 1, .8, (2, 1))
            .bind(lambda: self.debug_text("this text is dynamically sized and positioned"))
        )
        # creates a ui grid as such:
        # 1 | 2 | E
        # --+---+--
        # [ 3 ] | 4
        # making submenus should also be achievable with a state machine...
        # will implement a method of disabling the old ui objects if this is the case

        self.objects.append(GameObject(self.debug_anim_g, -32, -32))

        self.debug_text_g = DynamicText("", assets.DEBUG_FONT)
        self.objects.append(ScreenObject(self.debug_text_g, .5, 1))

    def debug_text(self, text: str) -> None:
        self.debug_text_g.text = text
        if text:
            self.set_timer("debug_text", 1.0, self.debug_text, "")

    def execute(self) -> None:
        if self.action_buffer[input.Action.START] == input.InputState.PRESSED:
            self.statemachine.change_state(scenes.game.Game)
            return

        if self.action_buffer[input.Action.A] == input.InputState.HELD:
            self.camera.add_camera_shake(self.dt)

        self.update()
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
