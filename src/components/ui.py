from dataclasses import dataclass
from typing import Callable
import pygame

import core.setup as setup
import core.assets as a
import core.constants as c
import core.input as t
import core.globals as g
from components.audio import AudioChannel, play_sound, try_play_sound
from utilities.math import clamp


BUTTON_SIZE = (96, 16)


@dataclass(slots=True)
class Button:
    key: str
    rect: pygame.Rect
    graphic: pygame.Surface
    callback: Callable


@dataclass(slots=True)
class Checkbox:
    key: str
    rect: pygame.Rect
    graphic_enabled: pygame.Surface
    graphic_disabled: pygame.Surface
    enabled: bool
    name_render: pygame.Surface
    callback: Callable


@dataclass(slots=True)
class Slider:
    key: str
    rect: pygame.Rect
    min_value: int
    max_value: int
    value: int
    filled_rect: pygame.Rect
    name_render: pygame.Surface
    value_render: pygame.Surface
    callback: Callable


def button_activate(button: Button) -> None:
    if callable(button.callback):
        button.callback()
    setup.write_settings()


def checkbox_set_enabled(checkbox: Checkbox, enabled: bool) -> None:
    if checkbox.key:
        g.settings[checkbox.key] = enabled

    checkbox.enabled = enabled
    if callable(checkbox.callback):
        checkbox.callback(checkbox.enabled)
    setup.write_settings()


def checkbox_toggle(checkbox: Checkbox) -> None:
    checkbox_set_enabled(checkbox, not checkbox.enabled)


def slider_percent(slider: Slider) -> float:
    difference = slider.max_value - slider.min_value
    return (slider.value - slider.min_value) / difference


def slider_value_render(slider: Slider) -> None:
    slider.value_render = a.DEBUG_FONT.render(
        str(int(slider.value)), False, c.WHITE)


def slider_set_value(slider: Slider, value: int) -> None:
    slider.value = clamp(value, slider.min_value, slider.max_value)
    slider.filled_rect = (
        slider.rect.x,
        slider.rect.y,
        slider_percent(slider) * slider.rect.w,
        slider.rect.h,
    )
    slider_value_render(slider)
    if slider.key:
        g.settings[slider.key] = slider.value
    if callable(slider.callback):
        slider.callback(slider.value)
    setup.write_settings()


def slider_set_value_mouse(slider: Slider, x: int) -> None:
    if x <= slider.rect.x:
        slider_set_value(slider, slider.min_value)
        return

    if x >= slider.rect.x + slider.rect.w:
        slider_set_value(slider, slider.max_value)
        return

    difference = slider.max_value - slider.min_value
    percent = (x - slider.rect.x) / slider.rect.w
    value = int(percent * difference + slider.min_value)
    slider_set_value(slider, value)


def button_render(surface: pygame.Surface, button: Button, selected: bool) -> None:
    surface.blit(a.MENU_BUTTONS[1 if selected else 0], button.rect.topleft)
    surface.blit(
        button.graphic,
        (
            button.rect.centerx - button.graphic.get_width() // 2,
            button.rect.centery - button.graphic.get_height() // 2,
        ),
    )
    if selected:
        surface.blit(a.MENU_BUTTONS[2], button.rect.topleft,
                     special_flags=pygame.BLEND_RGB_ADD)


def slider_render(surface: pygame.Surface, slider: Slider, selected: bool) -> None:
    surface.blit(slider.name_render, (slider.rect.left - 150, slider.rect.y))
    surface.blit(a.MENU_BUTTONS[1 if selected else 0], slider.rect.topleft)
    surface.blit(
        a.MENU_BUTTONS[3], slider.rect.topleft, (
            0, 0, slider.filled_rect[2], slider.filled_rect[3])
    )
    surface.blit(slider.value_render, (slider.rect.right + 20, slider.rect.y))
    if selected:
        surface.blit(
            a.MENU_BUTTONS[2], (slider.rect.x,
                                slider.rect.y), special_flags=pygame.BLEND_RGB_ADD
        )


def checkbox_render(surface: pygame.Surface, checkbox: Checkbox, selected: bool) -> None:
    surface.blit(checkbox.name_render,
                 (checkbox.rect.x - 150, checkbox.rect.y))
    surface.blit(a.MENU_BUTTONS[1 if selected else 0], checkbox.rect.topleft)
    if checkbox.enabled:
        surface.blit(
            checkbox.graphic_enabled,
            (
                checkbox.rect.centerx - checkbox.graphic_enabled.get_width() // 2,
                checkbox.rect.centery - checkbox.graphic_enabled.get_height() // 2,
            ),
        )
    else:
        surface.blit(
            checkbox.graphic_disabled,
            (
                checkbox.rect.centerx - checkbox.graphic_disabled.get_width() // 2,
                checkbox.rect.centery - checkbox.graphic_disabled.get_height() // 2,
            ),
        )
    if selected:
        surface.blit(
            a.MENU_BUTTONS[2],
            (checkbox.rect.x, checkbox.rect.y),
            special_flags=pygame.BLEND_RGB_ADD,
        )


def ui_list_update_selection(
    action_buffer: t.InputBuffer,
    mouse_position: pygame.Vector2 | None,
    ui_list: list,
    ui_index: int,
) -> int | None:

    # Check if mouse moved and is over rect
    if mouse_position is not None:
        for i, element in enumerate(ui_list):
            if element.rect.collidepoint(mouse_position):
                if i != ui_index:
                    try_play_sound(AudioChannel.UI, a.UI_HOVER)
                return i

        return None

    else:
        # Check if direction pressed and move index
        if t.is_pressed(action_buffer, t.Action.UP):
            play_sound(AudioChannel.UI, a.UI_HOVER)
            if ui_index is None:
                return 0
            return (ui_index - 1) % len(ui_list)

        if t.is_pressed(action_buffer, t.Action.DOWN):
            play_sound(AudioChannel.UI, a.UI_HOVER)
            if ui_index is None:
                return 0
            return (ui_index + 1) % len(ui_list)

        return ui_index


def ui_list_render(surface: pygame.Surface, ui_list: list, ui_index: int) -> None:
    for i, element in enumerate(ui_list):
        selected = i == ui_index
        if isinstance(element, Slider):
            slider_render(surface, element, selected)
        elif isinstance(element, Checkbox):
            checkbox_render(surface, element, selected)
        elif isinstance(element, Button):
            button_render(surface, element, selected)
