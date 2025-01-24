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

    def enter(self) -> None:
        camera_reset(self.camera)
        play_sound(AudioChannel.MUSIC, a.THEME_MUSIC[0], -1)

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

        # RENDER
        surface.fill(c.WHITE)

        if self.in_settings:
            settings_render(self.settings, surface)

    def exit(self) -> None:
        stop_all_sounds()
