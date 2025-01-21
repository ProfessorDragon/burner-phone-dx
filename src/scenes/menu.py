import pygame

import core.constants as c
import core.input as t
import core.assets as a
from components.camera import (
    Camera,
    camera_update,
    camera_to_screen_shake,
    camera_reset,
)
from components.motion import Motion
from components.animation import (
    Animator,
    Animation,
    animator_get_frame,
    animator_update,
    animator_initialise,
    animator_switch_animation,
)
from components.settings import Settings, settings_render, settings_update
from components.dialogue import (
    DialogueSystem,
    dialogue_initialise,
    dialogue_update,
    dialogue_render,
    dialogue_reset_queue,
)

from scenes.scene import Scene
import scenes.scenemapping as scene
from components.statemachine import StateMachine, statemachine_change_state


class Menu(Scene):
    def __init__(self, statemachine: StateMachine) -> None:
        super().__init__(statemachine)

        self.camera = Camera.empty()

        self.settings = Settings()
        self.dialogue = DialogueSystem()
        dialogue_initialise(self.dialogue)

    def enter(self) -> None:
        dialogue_reset_queue(self.dialogue)
        camera_reset(self.camera)
        pygame.mixer.Channel(0).play(a.DEBUG_THEME_MENU, -1)

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
        in_dialogue = dialogue_update(self.dialogue, dt, action_buffer, mouse_buffer)

        if not in_dialogue:
            settings_update(self.settings, dt, action_buffer, mouse_buffer)

        # RENDER
        surface.fill(c.WHITE)
        dialogue_render(self.dialogue, surface)

        if not in_dialogue:
            settings_render(self.settings, surface)

    def exit(self) -> None:
        pygame.mixer.Channel(0).stop()
        pygame.mixer.Channel(1).stop()
