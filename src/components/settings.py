from dataclasses import dataclass
import pygame

from components.audio import AudioChannel, play_sound
import core.constants as c
import core.input as t
import core.assets as a
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
        self.graphic_enabled = a.DEBUG_FONT.render("Y", False, c.GREEN)
        self.graphic_disabled = a.DEBUG_FONT.render("N", False, c.RED)

        self.ui_music_slider = Slider(pygame.Rect(10, 100, 100, 10), 0, 100)
        slider_set_value(self.ui_music_slider, 30)

        self.ui_sfx_slider = Slider(pygame.Rect(10, 120, 100, 10), 0, 100)
        slider_set_value(self.ui_sfx_slider, 30)

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
            a.DEBUG_FONT.render("DEFAULT", False, c.WHITE),
        )

        # the slider currently being dragged by the mouse
        self.selected_slider = None

        pygame.mixer.Channel(AudioChannel.MUSIC).set_volume(slider_percent(self.ui_music_slider))
        pygame.mixer.Channel(AudioChannel.PLAYER).set_volume(slider_percent(self.ui_sfx_slider))
        pygame.mixer.Channel(AudioChannel.UI).set_volume(slider_percent(self.ui_sfx_slider))
        pygame.mixer.Channel(AudioChannel.SFX).set_volume(slider_percent(self.ui_sfx_slider))


def settings_update(
    settings: Settings,
    dt: float,
    action_buffer: t.InputBuffer,
    mouse_buffer: t.InputBuffer,
) -> None:
    mouse_position = pygame.mouse.get_pos()

    # sliders
    if settings.ui_music_slider.rect.collidepoint(mouse_position):
        if mouse_buffer[t.MouseButton.LEFT] == t.InputState.PRESSED:
            settings.selected_slider = settings.ui_music_slider
    elif settings.ui_sfx_slider.rect.collidepoint(mouse_position):
        if mouse_buffer[t.MouseButton.LEFT] == t.InputState.PRESSED:
            settings.selected_slider = settings.ui_sfx_slider
    # checkboxes
    elif settings.ui_vsync_checkbox.rect.collidepoint(mouse_position):
        if mouse_buffer[t.MouseButton.LEFT] == t.InputState.PRESSED:
            checkbox_toggle(settings.ui_vsync_checkbox)
            play_sound(AudioChannel.UI, a.UI_SELECT)
    elif settings.ui_fullscreen_checkbox.rect.collidepoint(mouse_position):
        if mouse_buffer[t.MouseButton.LEFT] == t.InputState.PRESSED:
            checkbox_toggle(settings.ui_fullscreen_checkbox)
            play_sound(AudioChannel.UI, a.UI_SELECT)
    elif settings.ui_screenshake_checkbox.rect.collidepoint(mouse_position):
        if mouse_buffer[t.MouseButton.LEFT] == t.InputState.PRESSED:
            checkbox_toggle(settings.ui_screenshake_checkbox)
            play_sound(AudioChannel.UI, a.UI_SELECT)
    # buttons
    elif settings.ui_default_button.rect.collidepoint(mouse_position):
        if mouse_buffer[t.MouseButton.LEFT] == t.InputState.PRESSED:
            play_sound(AudioChannel.UI, a.UI_SELECT)

    if settings.selected_slider:
        if mouse_buffer[t.MouseButton.LEFT] == t.InputState.RELEASED:
            # TODO: This is where we write/save value and apply setting
            play_sound(AudioChannel.UI, a.UI_SELECT)
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
