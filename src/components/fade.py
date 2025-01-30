from dataclasses import dataclass
from typing import Callable
import pygame

import core.constants as c
from components.timer import Timer, timer_reset, timer_update


@dataclass
class ScreenFade:
    duration: float = 0
    fading_in: bool = True
    timer: Timer = None
    surf: pygame.Surface = None


def fade_initialise(fade: ScreenFade, duration: float) -> None:
    fade.duration = duration
    fade.timer = Timer()
    fade.surf = pygame.Surface(c.WINDOW_SIZE)
    fade.surf.fill(c.BLACK)


def fade_start(fade: ScreenFade, fading_in: bool, callback: Callable = None) -> None:
    fade.fading_in = fading_in
    timer_reset(fade.timer, fade.duration, callback)


def fade_active(fade: ScreenFade) -> bool:
    return fade.timer.remaining > 0


def fade_update(fade: ScreenFade, dt: float) -> None:
    timer_update(fade.timer, dt)


def fade_render(fade: ScreenFade, surface: pygame.Surface) -> None:
    if fade.timer.duration == 0:
        percent = 0
    else:
        percent = (
            fade.timer.remaining if fade.fading_in else fade.timer.elapsed) / fade.timer.duration
    if percent > 0:
        fade.surf.set_alpha(percent * 255)
        surface.blit(fade.surf, (0, 0))
