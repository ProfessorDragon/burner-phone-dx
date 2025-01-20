from dataclasses import dataclass
import json
from math import ceil, floor
import pygame

import core.input as t
import core.constants as c
from components.camera import camera_from_screen
from scenes.scene import Scene

# terrain pasting
# if mouse_buffer[t.MouseButton.LEFT] == t.InputState.PRESSED:
#     x, y = camera_from_screen(scene.camera, *pygame.mouse.get_pos())
#     x = x // c.HALF_TILE_SIZE * c.HALF_TILE_SIZE
#     y = y // c.HALF_TILE_SIZE * c.HALF_TILE_SIZE
#     (
#         scene.background if scene.terrain_paste_layer == 0 else scene.player_layer
#     ).blit(
#         a.TERRAIN_SHEET,
#         (
#             x,
#             y,
#         ),
#         (
#             scene.terrain_paste_tile[0] * c.TILE_SIZE,
#             scene.terrain_paste_tile[1] * c.HALF_TILE_SIZE,
#             16,
#             16,
#         ),
#     )
# if _key_pressed(pygame.K_1):
#     scene.terrain_paste_tile = (0, 0)
#     scene.terrain_paste_layer = 1
# if _key_pressed(pygame.K_2):
#     scene.terrain_paste_tile = (0, 1)
#     scene.terrain_paste_layer = 0
# if _key_pressed(pygame.K_3):
#     scene.terrain_paste_tile = (0, 2)
#     scene.terrain_paste_layer = 0


@dataclass(slots=True)
class Editor:
    enabled = False
    # terrain_paste_tile = (0, 2)
    # terrain_paste_layer = 0
    wall_paste_start = None


def _editor_wall_create(
    scene: Scene, action_buffer: t.InputBuffer, mouse_buffer: t.InputBuffer
) -> None:
    if t.is_pressed(mouse_buffer, t.MouseButton.LEFT):
        Editor.wall_paste_start = camera_from_screen(scene.camera, *pygame.mouse.get_pos())
        scene.walls.append(pygame.Rect(*Editor.wall_paste_start, 1, 1))
    if t.is_pressed(mouse_buffer, t.MouseButton.RIGHT):
        x, y = camera_from_screen(scene.camera, *pygame.mouse.get_pos())
        for i, wall in enumerate(scene.walls[::-1]):
            if wall.collidepoint(x, y):
                scene.walls.pop(len(scene.walls) - 1 - i)
                break
    if Editor.wall_paste_start:
        start, end = Editor.wall_paste_start, camera_from_screen(
            scene.camera, *pygame.mouse.get_pos()
        )
        if t.is_held(action_buffer, t.Action.A):
            start = (
                floor(start[0] / c.TILE_SIZE) * c.TILE_SIZE,
                floor(start[1] / c.TILE_SIZE) * c.TILE_SIZE,
            )
            end = (
                ceil(end[0] / c.TILE_SIZE) * c.TILE_SIZE,
                ceil(end[1] / c.TILE_SIZE) * c.TILE_SIZE,
            )
        scene.walls[-1] = pygame.Rect(*start, end[0] - start[0], end[1] - start[1])
        if t.is_released(mouse_buffer, t.MouseButton.LEFT):
            if start[0] >= end[0] or start[1] >= end[1]:
                scene.walls.pop()
            Editor.wall_paste_start = None


def _editor_wall_tweak(scene: Scene, action_buffer: t.InputBuffer) -> None:
    wall = scene.walls[-1]

    # expand
    if t.is_held(action_buffer, t.Action.A):
        if t.is_pressed(action_buffer, t.Action.LEFT):
            wall.x -= 1
            wall.width += 1
        if t.is_pressed(action_buffer, t.Action.RIGHT):
            wall.width += 1
        if t.is_pressed(action_buffer, t.Action.UP):
            wall.y -= 1
            wall.height += 1
        if t.is_pressed(action_buffer, t.Action.DOWN):
            wall.height += 1
    # contract
    elif t.is_held(action_buffer, t.Action.B):
        if t.is_pressed(action_buffer, t.Action.LEFT):
            wall.width -= 1
        if t.is_pressed(action_buffer, t.Action.RIGHT):
            wall.x += 1
            wall.width -= 1
        if t.is_pressed(action_buffer, t.Action.UP):
            wall.height -= 1
        if t.is_pressed(action_buffer, t.Action.DOWN):
            wall.y += 1
            wall.height -= 1
    # move
    else:
        if t.is_pressed(action_buffer, t.Action.LEFT):
            wall.move_ip(-1, 0)
        if t.is_pressed(action_buffer, t.Action.RIGHT):
            wall.move_ip(1, 0)
        if t.is_pressed(action_buffer, t.Action.UP):
            wall.move_ip(0, -1)
        if t.is_pressed(action_buffer, t.Action.DOWN):
            wall.move_ip(0, 1)


def editor_update(scene: Scene, action_buffer: t.InputBuffer, mouse_buffer: t.InputBuffer) -> None:
    just_pressed = pygame.key.get_just_pressed()

    # editor toggle
    if just_pressed[pygame.K_e]:
        Editor.enabled = not Editor.enabled

    if not Editor.enabled:
        return

    pressed = pygame.key.get_pressed()

    # save/load
    if pressed[pygame.K_LCTRL]:
        if just_pressed[pygame.K_s]:
            data = [(*wall,) for wall in scene.walls]
            with open("assets/default_level.json", "w") as f:
                json.dump(data, f)
            return
        if just_pressed[pygame.K_o]:
            with open("assets/default_level.json") as f:
                data = json.load(f)
            scene.walls = [pygame.Rect(wall) for wall in data]
            return

    # walls
    _editor_wall_create(scene, action_buffer, mouse_buffer)
    if len(scene.walls) > 0:
        _editor_wall_tweak(scene, action_buffer)
