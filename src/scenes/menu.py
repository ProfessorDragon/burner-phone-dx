import pygame

from components.audio import AudioChannel, play_sound, stop_all_sounds
import core.constants as c
import core.input as t
import core.assets as a
from components.camera import (
    Camera,
    camera_update,
    camera_reset,
)
from components.animation import (
    Animator,
    Animation,
    animator_initialise,
    animator_update,
    animator_get_frame,
)
from components.settings import Settings, settings_render, settings_update

from scenes.scene import Scene
import scenes.scenemapping as scene
from components.statemachine import StateMachine, statemachine_change_state


class Menu(Scene):
    def __init__(self, statemachine: StateMachine) -> None:
        super().__init__(statemachine)

        self.camera = Camera.empty()

        self.settings = Settings()
        self.in_settings = False

        self.scan_lines = Animator()
        animator_initialise(self.scan_lines, {0: Animation(a.MENU_SCANS, 0.1)}, 0)

    def enter(self) -> None:
        camera_reset(self.camera)
        play_sound(AudioChannel.MUSIC, a.THEME_MUSIC[2], -1)

    def execute(
        self,
        surface: pygame.Surface,
        dt: float,
        action_buffer: t.InputBuffer,
        mouse_buffer: t.InputBuffer,
    ) -> None:
        # INPUT
        if t.is_pressed(action_buffer, t.Action.START):
            statemachine_change_state(self.statemachine, scene.SceneState.GAME)
            return

        if t.is_held(action_buffer, t.Action.B):
            self.camera.trauma += 0.01

        # UPDATE
        camera_update(self.camera, dt)
        animator_update(self.scan_lines, dt)

        # RENDER
        # surface.fill(c.BLACK)
        surface.blit(a.MENU_BACK, (0, 0))

        # Render button UI here under scan lines

        surface.blit(animator_get_frame(self.scan_lines), (0, 0))
        surface.blit(a.MENU_BLUR, (0, 0))

        if self.in_settings:
            settings_render(self.settings, surface)

    def exit(self) -> None:
        stop_all_sounds()
