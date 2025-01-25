from dataclasses import dataclass
import pygame

from components.camera import Camera


@dataclass(slots=True)
class Decor:
    position: pygame.Vector2
    sprite_index: int = 0


# todo
def decor_render(surface: pygame.Surface, camera: Camera, decor: Decor):
    pass
