from dataclasses import dataclass
import pygame

from components.audio import AudioChannel, play_sound, set_music_volume, set_sfx_volume
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

        self.ui_music_slider = Slider(
            pygame.Rect(250, 100, 100, 10), 0, 100, 0, None,
            a.DEBUG_FONT.render("MUSIC VOLUME", False, c.WHITE)
        )
        slider_set_value(self.ui_music_slider, 50)

        self.ui_sfx_slider = Slider(
            pygame.Rect(250, 130, 100, 10), 0, 100, 0, None,
            a.DEBUG_FONT.render("SFX VOLUME", False, c.WHITE)
        )
        slider_set_value(self.ui_sfx_slider, 30)

        self.ui_fullscreen_checkbox = Checkbox(
            pygame.Rect(250, 160, 100, 20),
            self.graphic_enabled,
            self.graphic_disabled,
            True,
            a.DEBUG_FONT.render("FULLSCREEN?", False, c.WHITE)
        )

        self.ui_vsync_checkbox = Checkbox(
            pygame.Rect(250, 190, 100, 20),
            self.graphic_enabled,
            self.graphic_disabled,
            True,
            a.DEBUG_FONT.render("VSYNC?", False, c.WHITE)
        )

        self.ui_screenshake_checkbox = Checkbox(
            pygame.Rect(250, 220, 100, 20),
            self.graphic_enabled,
            self.graphic_disabled,
            True,
            a.DEBUG_FONT.render("SCREENSHAKE?", False, c.WHITE)
        )

        self.ui_default_button = Button(
            pygame.Rect(250, 250, 100, 20),
            a.DEBUG_FONT.render("DEFAULT", False, c.WHITE),
        )

        # the slider currently being dragged by the mouse
        self.selected_slider = None

        self.ui_index = 0
        self.last_mouse_position = (0, 0)

        set_music_volume(slider_percent(self.ui_music_slider))
        set_sfx_volume(slider_percent(self.ui_sfx_slider))

        self.ui_list = [
            self.ui_music_slider,
            self.ui_sfx_slider,
            self.ui_fullscreen_checkbox,
            self.ui_vsync_checkbox,
            self.ui_screenshake_checkbox,
            self.ui_default_button
        ]


def settings_update(
    settings: Settings,
    dt: float,
    action_buffer: t.InputBuffer,
    mouse_buffer: t.InputBuffer,
) -> None:
    mouse_position = pygame.mouse.get_pos()

    # Check if direction pressed and move index
    if t.is_pressed(action_buffer, t.Action.UP):
        settings.ui_index -= 1
        settings.ui_index %= len(settings.ui_list)
    if t.is_pressed(action_buffer, t.Action.DOWN):
        settings.ui_index += 1
        settings.ui_index %= len(settings.ui_list)

    # Check if mouse moved and is over rect
    if (mouse_position != settings.last_mouse_position and
            settings.selected_slider is None):
        for i, element in enumerate(settings.ui_list):
            if element.rect.collidepoint(mouse_position):
                settings.ui_index = i

    if settings.selected_slider:
        if (mouse_buffer[t.MouseButton.LEFT] == t.InputState.RELEASED):
            # TODO: This is where we write/save value and apply setting
            play_sound(AudioChannel.UI, a.UI_SELECT)
            settings.selected_slider = None
        else:
            slider_set_value_mouse(settings.selected_slider, mouse_position[0])
    else:
        # MOUSE INPUT
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

        # KEYBOARD INPUT
        if settings.selected_slider is None:
            element = settings.ui_list[settings.ui_index]
            if t.is_pressed(action_buffer, t.Action.A):
                if isinstance(element, Checkbox):
                    checkbox_toggle(element)
                elif isinstance(element, Button):
                    pass
                play_sound(AudioChannel.UI, a.UI_SELECT)
            elif t.is_held(action_buffer, t.Action.LEFT):
                if isinstance(element, Slider):
                    slider_set_value(element, element.value - 0.1)
            elif t.is_held(action_buffer, t.Action.RIGHT):
                if isinstance(element, Slider):
                    slider_set_value(element, element.value + 0.1)

    settings.last_mouse_position = mouse_position


def settings_render(settings: Settings, surface: pygame.Surface) -> None:
    surface.blit(a.MENU_BLUR_FULL, (0, 0))

    move = a.DEBUG_FONT.render("Move", False, c.WHITE)
    jump = a.DEBUG_FONT.render("Jump", False, c.WHITE)
    roll = a.DEBUG_FONT.render("Roll", False, c.WHITE)
    footer = a.DEBUG_FONT.render(
        "Best played in fullscreen with sound on", False, c.WHITE)
    surface.blit(
        a.MENU_CONTROLS, (150, 10)
    )
    surface.blit(move, (190, 10))
    surface.blit(jump, (350, 20))
    surface.blit(roll, (350, 50))
    # surface.blit(footer, (90, 70))

    for i, element in enumerate(settings.ui_list):
        selected = i == settings.ui_index

        if isinstance(element, Slider):
            slider_render(surface, element, selected)
        elif isinstance(element, Checkbox):
            checkbox_render(surface, element, selected)
        elif isinstance(element, Button):
            button_render(surface, element, selected)
