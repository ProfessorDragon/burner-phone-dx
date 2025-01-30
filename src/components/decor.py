from dataclasses import dataclass
from typing import Any
import pygame

import core.assets as a
import core.constants as c
import core.globals as g
from components.camera import Camera, camera_to_screen_shake, camera_to_screen_shake_rect
from scenes.scene import PLAYER_OR_FG, RenderLayer


@dataclass(slots=True)
class Decor:
    position: pygame.Vector2
    sprite_index: int = 0


def decor_rect(dec: Decor) -> pygame.Rect:
    return a.DECOR[dec.sprite_index][0].get_rect().move(dec.position)


def decor_to_json(dec: Decor) -> dict[str, Any]:
    return {"pos": (*dec.position,), "sprite": dec.sprite_index}


def decor_from_json(js: dict[str, Any]) -> Decor:
    return Decor(pygame.Vector2(js["pos"]), js.get("sprite", 0))


def decor_render(
    dec: Decor, surface: pygame.Surface, camera: Camera, layer: RenderLayer, time: float
):
    # offset the animation based on position to make it not look super repetitive
    idx = (time + dec.position.x * 0.003 + dec.position.y * 0.002) // 0.1
    frames = a.DECOR[dec.sprite_index]
    frame = frames[int(idx % len(frames))]
    if layer in PLAYER_OR_FG:
        frame = frame.copy()
        frame.set_alpha(96)
    surface.blit(frame, camera_to_screen_shake(camera, *dec.position))
    if g.show_hitboxes:
        pygame.draw.rect(
            surface,
            c.GREEN,
            camera_to_screen_shake_rect(camera, *decor_rect(dec)),
            1,
        )
