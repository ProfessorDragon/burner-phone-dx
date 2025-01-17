from dataclasses import dataclass
import pygame

import core.constants as c
import core.input as input
import core.assets as asset
from components.ui import (
    Slider,
    Checkbox,
    Button,
    button_render,
    slider_render,
    slider_set_value,
    slider_set_value_mouse,
    checkbox_render,
    checkbox_toggle,
    slider_percent,
)


@dataclass
class Settings:
    def __init__(self) -> None:
        self.graphic_enabled = asset.DEBUG_FONT.render("Y", False, c.GREEN)
        self.graphic_disabled = asset.DEBUG_FONT.render("N", False, c.RED)

        self.ui_music_slider = Slider(pygame.Rect(10, 100, 100, 10), 0, 100)
        slider_set_value(self.ui_music_slider, 20)

        self.ui_sfx_slider = Slider(pygame.Rect(10, 120, 100, 10), 0, 100)
        slider_set_value(self.ui_sfx_slider, 20)

        self.ui_fullscreen_checkbox = Checkbox(
            pygame.Rect(10, 140, 15, 15),
            self.graphic_enabled,
            self.graphic_disabled,
            True,
        )

        self.ui_vsync_checkbox = Checkbox(
            pygame.Rect(10, 190, 15, 15),
            self.graphic_enabled,
            self.graphic_disabled,
            True,
        )

        self.ui_screenshake_checkbox = Checkbox(
            pygame.Rect(10, 240, 15, 15),
            self.graphic_enabled,
            self.graphic_disabled,
            True,
        )

        self.ui_default_button = Button(
            pygame.Rect(10, 270, 70, 20),
            asset.DEBUG_FONT.render("DEFAULT", False, c.WHITE),
        )

        # the slider currently being dragged by the mouse
        self.selected_slider = None

        pygame.mixer.Channel(0).set_volume(slider_percent(self.ui_music_slider))
        pygame.mixer.Channel(1).set_volume(slider_percent(self.ui_sfx_slider))


def settings_update(
    settings: Settings,
    dt: float,
    action_buffer: input.InputBuffer,
    mouse_buffer: input.InputBuffer,
) -> None:
    mouse_position = pygame.mouse.get_pos()

    if settings.ui_music_slider.rect.collidepoint(mouse_position):
        if mouse_buffer[input.MouseButton.LEFT] == input.InputState.PRESSED:
            settings.selected_slider = settings.ui_music_slider
    elif settings.ui_sfx_slider.rect.collidepoint(mouse_position):
        if mouse_buffer[input.MouseButton.LEFT] == input.InputState.PRESSED:
            settings.selected_slider = settings.ui_sfx_slider
    elif settings.ui_vsync_checkbox.rect.collidepoint(mouse_position):
        if mouse_buffer[input.MouseButton.LEFT] == input.InputState.PRESSED:
            checkbox_toggle(settings.ui_vsync_checkbox)
            pygame.mixer.Channel(1).play(asset.DEBUG_BONK)
    elif settings.ui_fullscreen_checkbox.rect.collidepoint(mouse_position):
        if mouse_buffer[input.MouseButton.LEFT] == input.InputState.PRESSED:
            checkbox_toggle(settings.ui_fullscreen_checkbox)
            pygame.mixer.Channel(1).play(asset.DEBUG_BONK)
    elif settings.ui_screenshake_checkbox.rect.collidepoint(mouse_position):
        if mouse_buffer[input.MouseButton.LEFT] == input.InputState.PRESSED:
            checkbox_toggle(settings.ui_screenshake_checkbox)
            pygame.mixer.Channel(1).play(asset.DEBUG_BONK)
    elif settings.ui_default_button.rect.collidepoint(mouse_position):
        if mouse_buffer[input.MouseButton.LEFT] == input.InputState.PRESSED:
            pygame.mixer.Channel(1).play(asset.DEBUG_BONK)

    if settings.selected_slider:
        if mouse_buffer[input.MouseButton.LEFT] == input.InputState.RELEASED:
            pygame.mixer.Channel(1).play(asset.DEBUG_BONK)
            # TODO: This is where we write/save value and apply setting
            if settings.selected_slider == settings.ui_music_slider:
                pygame.mixer.Channel(0).set_volume(
                    slider_percent(settings.ui_music_slider)
                )
            elif settings.selected_slider == settings.ui_sfx_slider:
                pygame.mixer.Channel(1).set_volume(
                    slider_percent(settings.ui_sfx_slider)
                )
            settings.selected_slider = None
        else:
            slider_set_value_mouse(settings.selected_slider, mouse_position[0])


def settings_render(settings: Settings, surface: pygame.Surface) -> None:
    slider_render(surface, settings.ui_sfx_slider)
    slider_render(surface, settings.ui_music_slider)
    checkbox_render(surface, settings.ui_vsync_checkbox)
    checkbox_render(surface, settings.ui_fullscreen_checkbox)
    checkbox_render(surface, settings.ui_screenshake_checkbox)
    button_render(surface, settings.ui_default_button)
