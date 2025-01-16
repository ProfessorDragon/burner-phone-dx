from abc import ABC, abstractmethod
from typing import Hashable
import pygame
import core.constants as const


class Graphic(ABC):
    @abstractmethod
    def update(self, dt: float) -> None: ...

    @abstractmethod
    def get_frame(self) -> pygame.Surface: ...


class StaticImage(Graphic):
    def __init__(self, image: pygame.Surface) -> None:
        self.image = image

    def update(self, dt: float) -> None:
        pass

    def get_frame(self) -> pygame.Surface:
        return self.image


class StaticText(StaticImage):
    def __init__(
        self,
        text: str,
        font: pygame.Font,
        fg: pygame.Color = const.WHITE,
        bg: pygame.Color = const.BLACK
    ) -> None:
        super().__init__(font.render(text, False, fg, bg))


class DynamicText(Graphic):
    def __init__(
        self,
        text: str,
        font: pygame.Font,
        fg: pygame.Color = const.WHITE,
        bg: pygame.Color = const.BLACK
    ) -> None:
        self.text = text
        self.font = font
        self.fg = fg
        self.bg = bg

    def update(self, dt: float) -> None:
        pass

    def get_frame(self) -> pygame.Surface:
        return self.font.render(self.text, False, self.fg, self.bg)


class AnimationPlayer(Graphic):
    def __init__(
        self,
        unique_identifier: Hashable,
        frames: list[pygame.Surface],
        duration: float
    ) -> None:
        self.animations = {}
        self.state = None
        self.frame_index = 0
        self.elasped_time = 0.0
        self.frames = []
        self.frame_duration = 0.0

        self.add_animation(unique_identifier, frames, duration)
        self.switch_animation(unique_identifier)

    def update(self, dt: float) -> None:
        self.elasped_time += dt
        if self.elasped_time > self.frame_duration:
            self.frame_index += 1
            self.frame_index %= len(self.frames)
            self.elasped_time = 0.0

    def get_frame(self) -> pygame.Surface:
        return self.frames[self.frame_index]

    def add_animation(
        self,
        unique_identifier: Hashable,
        frames: list[pygame.Surface],
        duration: float
    ) -> None:
        self.animations[unique_identifier] = (frames, duration)

    def switch_animation(self, unique_identifier: Hashable) -> None:
        self.state = unique_identifier
        self.frames = self.animations[unique_identifier][0]
        self.frame_duration = self.animations[unique_identifier][1]

        self.reset()

    def reset(self) -> None:
        self.frame_index = 0
        self.elasped_time = 0.0
