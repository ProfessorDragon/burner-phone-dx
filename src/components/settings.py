from dataclasses import dataclass
import pygame

from components.audio import (
    AudioChannel,
    play_sound,
    set_music_volume,
    set_sfx_volume,
    try_play_sound,
)
import core.constants as c
import core.input as t
import core.assets as a
from components.ui import (
    BUTTON_SIZE,
    Slider,
    Checkbox,
    Button,
    button_activate,
    button_render,
    checkbox_set_enabled,
    slider_render,
    slider_set_value,
    slider_set_value_mouse,
    checkbox_render,
    checkbox_toggle,
    slider_percent,
    ui_list_render,
    ui_list_update_selection,
)


@dataclass
class Settings:
    def __init__(self) -> None:
        self.title = a.DEBUG_FONT.render("SETTINGS", False, c.WHITE)

        self.graphic_enabled = a.DEBUG_FONT.render("Enabled", False, c.GREEN)
        self.graphic_disabled = a.DEBUG_FONT.render("Disabled", False, c.RED)

        self.ui_music_slider = Slider(
            pygame.Rect(250, 50, *BUTTON_SIZE),
            0,
            100,
            0,
            None,
            a.DEBUG_FONT.render("MUSIC VOLUME", False, c.WHITE),
            None,
            lambda value: print(value),
        )

        self.ui_sfx_slider = Slider(
            pygame.Rect(250, 75, *BUTTON_SIZE),
            0,
            100,
            0,
            None,
            a.DEBUG_FONT.render("SFX VOLUME", False, c.WHITE),
            None,
            lambda value: print(value),
        )

        self.ui_fullscreen_checkbox = Checkbox(
            pygame.Rect(250, 100, *BUTTON_SIZE),
            self.graphic_enabled,
            self.graphic_disabled,
            True,
            a.DEBUG_FONT.render("FULLSCREEN?", False, c.WHITE),
            lambda enabled: print(enabled),
        )

        self.ui_vsync_checkbox = Checkbox(
            pygame.Rect(250, 125, *BUTTON_SIZE),
            self.graphic_enabled,
            self.graphic_disabled,
            True,
            a.DEBUG_FONT.render("VSYNC?", False, c.WHITE),
            lambda enabled: print(enabled),
        )

        self.ui_screenshake_checkbox = Checkbox(
            pygame.Rect(250, 150, *BUTTON_SIZE),
            self.graphic_enabled,
            self.graphic_disabled,
            True,
            a.DEBUG_FONT.render("SCREENSHAKE?", False, c.WHITE),
            lambda enabled: print(enabled),
        )

        self.ui_default_button = Button(
            pygame.Rect(250, 175, *BUTTON_SIZE),
            a.DEBUG_FONT.render("DEFAULT", False, c.WHITE),
            lambda: settings_reset(self),
        )

        self.ui_back_button = Button(
            pygame.Rect(250, 200, *BUTTON_SIZE),
            a.DEBUG_FONT.render("BACK", False, c.WHITE),
            lambda: settings_exit(self),
        )

        # the slider currently being dragged by the mouse
        self.selected_slider = None

        self.ui_index = 0
        self.last_mouse_position = None

        settings_reset(self)
        set_music_volume(slider_percent(self.ui_music_slider))
        set_sfx_volume(slider_percent(self.ui_sfx_slider))

        self.ui_list = [
            self.ui_music_slider,
            self.ui_sfx_slider,
            self.ui_fullscreen_checkbox,
            self.ui_vsync_checkbox,
            self.ui_screenshake_checkbox,
            self.ui_default_button,
            self.ui_back_button,
        ]

        self.should_exit = False


def settings_reset(settings: Settings) -> None:
    slider_set_value(settings.ui_music_slider, 50)
    slider_set_value(settings.ui_sfx_slider, 30)
    checkbox_set_enabled(settings.ui_vsync_checkbox, True)
    checkbox_set_enabled(settings.ui_screenshake_checkbox, True)


def settings_exit(settings: Settings) -> None:
    settings.should_exit = True


def settings_update(
    settings: Settings,
    dt: float,
    action_buffer: t.InputBuffer,
    mouse_buffer: t.InputBuffer,
) -> None:
    mouse_position = pygame.mouse.get_pos()

    settings.ui_index = ui_list_update_selection(
        action_buffer,
        (
            mouse_position
            if settings.selected_slider is None and mouse_position != settings.last_mouse_position
            else None
        ),
        settings.ui_list,
        settings.ui_index,
    )

    if settings.selected_slider:
        if mouse_buffer[t.MouseButton.LEFT] == t.InputState.RELEASED:
            play_sound(AudioChannel.UI, a.UI_SELECT)
            settings.selected_slider = None
        else:
            slider_set_value_mouse(settings.selected_slider, mouse_position[0])

    else:
        # MOUSE INPUT
        if mouse_buffer[t.MouseButton.LEFT] == t.InputState.PRESSED:
            for element in settings.ui_list:
                if element.rect.collidepoint(mouse_position):
                    if isinstance(element, Button):
                        button_activate(element)
                        play_sound(AudioChannel.UI, a.UI_SELECT)
                    elif isinstance(element, Checkbox):
                        checkbox_toggle(element)
                        play_sound(AudioChannel.UI, a.UI_SELECT)
                    elif isinstance(element, Slider):
                        settings.selected_slider = element

        # KEYBOARD INPUT
        if settings.selected_slider is None:
            element = settings.ui_list[settings.ui_index]
            if t.is_pressed(action_buffer, t.Action.A):
                if isinstance(element, Button):
                    button_activate(element)
                elif isinstance(element, Checkbox):
                    checkbox_toggle(element)
                play_sound(AudioChannel.UI, a.UI_SELECT)
            elif t.is_held(action_buffer, t.Action.LEFT):
                if isinstance(element, Slider):
                    slider_set_value(element, element.value - 0.5)
            elif t.is_held(action_buffer, t.Action.RIGHT):
                if isinstance(element, Slider):
                    slider_set_value(element, element.value + 0.5)
            elif t.is_released(action_buffer, t.Action.LEFT):
                if isinstance(element, Slider):
                    play_sound(AudioChannel.UI, a.UI_SELECT)
            elif t.is_released(action_buffer, t.Action.RIGHT):
                if isinstance(element, Slider):
                    play_sound(AudioChannel.UI, a.UI_SELECT)

    settings.last_mouse_position = mouse_position


def settings_render(settings: Settings, surface: pygame.Surface) -> None:
    surface.blit(settings.title, (surface.get_width() // 2 - settings.title.get_width() // 2, 15))

    surface.blit(
        a.MENU_CONTROLS, (surface.get_width() // 2 - a.MENU_CONTROLS.get_width() // 2, 225)
    )

    ui_list_render(surface, settings.ui_list, settings.ui_index)
