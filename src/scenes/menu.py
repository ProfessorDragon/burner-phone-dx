import pygame

import core.constants as const
import core.input as input
import core.assets as asset
from components.camera import (
    Camera, camera_update, camera_to_screen_shake, camera_reset
)
from components.motion import Vector2, Motion
from components.animation import (
    Animator, Animation, animator_get_frame, animator_update,
    animator_initialise, animator_switch_animation
)
from components.settings import Settings, settings_render, settings_update

from scenes.scene import Scene
import scenes.scenemapping as scene
from components.statemachine import StateMachine, statemachine_change_state


class Menu(Scene):
    def __init__(self, statemachine: StateMachine) -> None:
        super().__init__(statemachine)

        self.camera = Camera(
            Motion.empty(),
            Vector2(),
            Vector2(),
            Vector2(30, 30)
        )

        self.debug = Animator()
        debug_animation_mapping = {0: Animation(asset.DEBUG_FRAMES, 0.1)}
        animator_initialise(self.debug, debug_animation_mapping, 0)

        debug_size = animator_get_frame(self.debug).get_size()
        self.debug_pos = Vector2(
            const.WINDOW_CENTRE[0] - debug_size[0] // 2,
            const.WINDOW_CENTRE[1] - debug_size[1] // 2
        )

        self.settings = Settings()

    def enter(self) -> None:
        camera_reset(self.camera)
        animator_switch_animation(self.debug, 0)
        pygame.mixer.Channel(0).play(asset.DEBUG_THEME_MENU, -1)

    def execute(
        self,
        surface: pygame.Surface,
        dt: float,
        action_buffer: input.InputBuffer,
        mouse_buffer: input.InputBuffer
    ) -> None:
        # INPUT
        if action_buffer[input.Action.START] == input.InputState.PRESSED:
            statemachine_change_state(self.statemachine, scene.SceneState.GAME)
            return

        if action_buffer[input.Action.B] == input.InputState.HELD:
            self.camera.trauma += 0.01

        # UPDATE
        camera_update(self.camera, dt)
        animator_update(self.debug, dt)
        settings_update(self.settings, dt, action_buffer, mouse_buffer)

        # RENDER
        surface.fill(const.WHITE)
        surface.blit(
            animator_get_frame(self.debug),
            camera_to_screen_shake(self.camera, *self.debug_pos)
        )
        settings_render(self.settings, surface)

    def exit(self) -> None:
        pygame.mixer.Channel(0).stop()
        pygame.mixer.Channel(1).stop()
