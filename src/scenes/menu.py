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
from components.ui import (
    Slider, Checkbox, Button, button_render, slider_render, slider_set_value,
    slider_set_value_mouse, checkbox_render, checkbox_toggle
)

from scenes.scene import Scene
import scenes.scenemapping as scene
from components.statemachine import StateMachine, statemachine_change_state


class Menu(Scene):
    def __init__(self, statemachine: StateMachine) -> None:
        super().__init__(statemachine)

        self.camera = Camera(
            Motion(Vector2(), Vector2(), Vector2()),
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

        self.graphic_enabled = asset.DEBUG_FONT.render(
            "Y", False, const.GREEN
        )
        self.graphic_disabled = asset.DEBUG_FONT.render(
            "N", False, const.RED
        )

        self.ui_music_slider = Slider(
            pygame.Rect(10, 100, 100, 10), 0, 100
        )
        slider_set_value(self.ui_music_slider, 50)

        self.ui_sfx_slider = Slider(pygame.Rect(10, 120, 100, 10), 0, 100)
        slider_set_value(self.ui_sfx_slider, 50)

        self.ui_fullscreen_checkbox = Checkbox(
            pygame.Rect(10, 140, 15, 15),
            self.graphic_enabled,
            self.graphic_disabled,
            True
        )

        self.ui_vsync_checkbox = Checkbox(
            pygame.Rect(10, 190, 15, 15),
            self.graphic_enabled,
            self.graphic_disabled,
            True
        )

        self.ui_screenshake_checkbox = Checkbox(
            pygame.Rect(10, 240, 15, 15),
            self.graphic_enabled,
            self.graphic_disabled,
            True
        )

        self.ui_default_button = Button(
            pygame.Rect(10, 270, 70, 20),
            asset.DEBUG_FONT.render("DEFAULT", False, const.WHITE)
        )

        self.selected_slider = None

    def enter(self) -> None:
        camera_reset(self.camera)
        animator_switch_animation(self.debug, 0)

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
        mouse_position = pygame.mouse.get_pos()

        camera_update(self.camera, dt)
        animator_update(self.debug, dt)

        if self.ui_music_slider.rect.collidepoint(mouse_position):
            if mouse_buffer[input.MouseButton.LEFT] == input.InputState.PRESSED:
                self.selected_slider = self.ui_music_slider
        elif self.ui_sfx_slider.rect.collidepoint(mouse_position):
            if mouse_buffer[input.MouseButton.LEFT] == input.InputState.PRESSED:
                self.selected_slider = self.ui_sfx_slider
        elif self.ui_vsync_checkbox.rect.collidepoint(mouse_position):
            if mouse_buffer[input.MouseButton.LEFT] == input.InputState.PRESSED:
                checkbox_toggle(self.ui_vsync_checkbox)
        elif self.ui_fullscreen_checkbox.rect.collidepoint(mouse_position):
            if mouse_buffer[input.MouseButton.LEFT] == input.InputState.PRESSED:
                checkbox_toggle(self.ui_fullscreen_checkbox)
        elif self.ui_screenshake_checkbox.rect.collidepoint(mouse_position):
            if mouse_buffer[input.MouseButton.LEFT] == input.InputState.PRESSED:
                checkbox_toggle(self.ui_screenshake_checkbox)
        elif self.ui_default_button.rect.collidepoint(mouse_position):
            if mouse_buffer[input.MouseButton.LEFT] == input.InputState.PRESSED:
                print("Pressed button")

        if self.selected_slider:
            if mouse_buffer[input.MouseButton.LEFT] == input.InputState.RELEASED:
                self.selected_slider = None
                # TODO: This is where we write/save value and apply setting
            else:
                slider_set_value_mouse(self.selected_slider, mouse_position[0])

        # RENDER
        surface.fill(const.WHITE)
        surface.blit(
            animator_get_frame(self.debug),
            camera_to_screen_shake(self.camera, *self.debug_pos)
        )
        slider_render(surface, self.ui_sfx_slider)
        slider_render(surface, self.ui_music_slider)
        checkbox_render(surface, self.ui_vsync_checkbox)
        checkbox_render(surface, self.ui_fullscreen_checkbox)
        checkbox_render(surface, self.ui_screenshake_checkbox)
        button_render(surface, self.ui_default_button)

    def exit(self) -> None:
        pass
