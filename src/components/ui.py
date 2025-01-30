from dataclasses import dataclass
import pygame

import core.constants as c
import core.assets as a
from utilities.math import clamp


SELECTED = pygame.Surface((200, 20), pygame.SRCALPHA)
SELECTED.set_alpha(50)
SELECTED.fill((255, 255, 255))


@dataclass(slots=True)
class Button:
    rect: pygame.Rect
    graphic: pygame.Surface


@dataclass(slots=True)
class Checkbox:
    rect: pygame.Rect
    graphic_enabled: pygame.Surface
    graphic_disabled: pygame.Surface
    enabled: bool = True
    name_render: pygame.Surface = None


@dataclass(slots=True)
class Slider:
    rect: pygame.rect
    min_value: int
    max_value: int
    value: int = 0
    filled_rect: pygame.Rect = None
    name_render: pygame.Surface = None
    value_render: pygame.Surface = None


def checkbox_toggle(checkbox: Checkbox) -> None:
    checkbox.enabled = not checkbox.enabled


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
    pygame.draw.rect(surface, c.BLACK, button.rect)
    surface.blit(button.graphic, (button.rect.x, button.rect.y))
    if selected:
        surface.blit(SELECTED, (button.rect.x, button.rect.y))


def slider_render(surface: pygame.Surface, slider: Slider, selected: bool) -> None:
    surface.blit(slider.name_render, (slider.rect.x - 150, slider.rect.y))
    pygame.draw.rect(surface, c.BLACK, slider.rect)
    pygame.draw.rect(surface, c.MAGENTA, slider.filled_rect)
    surface.blit(slider.value_render,
                 (slider.rect.x + slider.rect.w + 20, slider.rect.y))
    if selected:
        surface.blit(SELECTED, (slider.rect.x, slider.rect.y))


def checkbox_render(surface: pygame.Surface, checkbox: Checkbox, selected: bool) -> None:
    surface.blit(checkbox.name_render,
                 (checkbox.rect.x - 150, checkbox.rect.y))
    pygame.draw.rect(surface, c.BLACK, checkbox.rect)
    if checkbox.enabled:
        surface.blit(checkbox.graphic_enabled,
                     (checkbox.rect.x, checkbox.rect.y))
    else:
        surface.blit(checkbox.graphic_disabled,
                     (checkbox.rect.x, checkbox.rect.y))
    if selected:
        surface.blit(SELECTED, (checkbox.rect.x, checkbox.rect.y))
