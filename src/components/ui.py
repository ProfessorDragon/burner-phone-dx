from dataclasses import dataclass
import pygame

import core.constants as c
from utilities.math import clamp


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


@dataclass(slots=True)
class Slider:
    rect: pygame.rect
    min_value: int
    max_value: int
    value: int = 0
    filled_rect: pygame.Rect = None


def checkbox_toggle(checkbox: Checkbox) -> None:
    checkbox.enabled = not checkbox.enabled


def slider_percent(slider: Slider) -> float:
    difference = slider.max_value - slider.min_value
    return (slider.value - slider.min_value) / difference


def slider_set_value(slider: Slider, value: int) -> None:
    slider.value = clamp(value, slider.min_value, slider.max_value)
    slider.filled_rect = (
        slider.rect.x,
        slider.rect.y,
        slider_percent(slider) * slider.rect.w,
        slider.rect.h,
    )


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


def button_render(surface: pygame.Surface, button: Button) -> None:
    pygame.draw.rect(surface, c.BLACK, button.rect)
    surface.blit(button.graphic, (button.rect.x, button.rect.y))


def slider_render(surface: pygame.Surface, slider: Slider) -> None:
    pygame.draw.rect(surface, c.BLACK, slider.rect)
    pygame.draw.rect(surface, c.MAGENTA, slider.filled_rect)


def checkbox_render(surface: pygame.Surface, checkbox: Checkbox) -> None:
    pygame.draw.rect(surface, c.BLACK, checkbox.rect)
    if checkbox.enabled:
        surface.blit(checkbox.graphic_enabled, (checkbox.rect.x, checkbox.rect.y))
    else:
        surface.blit(checkbox.graphic_disabled, (checkbox.rect.x, checkbox.rect.y))
