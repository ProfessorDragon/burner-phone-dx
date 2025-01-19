from dataclasses import dataclass
import pygame
from components.camera import camera_from_screen
import core.input as t

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

editor_enabled = False


@dataclass(slots=True)
class Editor:
    enabled = False
    # terrain_paste_tile = (0, 2)
    # terrain_paste_layer = 0
    wall_paste_start = None


def editor_update(scene, action_buffer, mouse_buffer):
    if pygame.key.get_just_pressed()[pygame.K_e]:
        Editor.enabled = not Editor.enabled

    if not Editor.enabled:
        return

    # collision editor
    if mouse_buffer[t.MouseButton.LEFT] == t.InputState.PRESSED:
        Editor.wall_paste_start = camera_from_screen(scene.camera, *pygame.mouse.get_pos())
        scene.walls.append(pygame.Rect(*Editor.wall_paste_start, 1, 1))
    if mouse_buffer[t.MouseButton.RIGHT] == t.InputState.PRESSED:
        x, y = camera_from_screen(scene.camera, *pygame.mouse.get_pos())
        for i, wall in enumerate(scene.walls):
            if wall.collidepoint(x, y):
                scene.walls.pop(i)
                break
    if Editor.wall_paste_start:
        start, end = Editor.wall_paste_start, camera_from_screen(
            scene.camera, *pygame.mouse.get_pos()
        )
        if action_buffer[t.Action.A] == t.InputState.HELD:
            start = (round(start[0] / 8.0) * 8, round(start[1] / 8.0) * 8)
            end = (round(end[0] / 8.0) * 8, round(end[1] / 8.0) * 8)
        scene.walls[-1] = pygame.Rect(*start, end[0] - start[0], end[1] - start[1])
        if mouse_buffer[t.MouseButton.LEFT] == t.InputState.RELEASED:
            if start[0] >= end[0] or start[1] >= end[1]:
                scene.walls.pop()
            Editor.wall_paste_start = None

    wall = scene.walls[-1]

    # expand
    if action_buffer[t.Action.A] == t.InputState.HELD:
        if action_buffer[t.Action.LEFT] == t.InputState.PRESSED:
            wall.x -= 1
            wall.width += 1
        if action_buffer[t.Action.RIGHT] == t.InputState.PRESSED:
            wall.width += 1
        if action_buffer[t.Action.UP] == t.InputState.PRESSED:
            wall.y -= 1
            wall.height += 1
        if action_buffer[t.Action.DOWN] == t.InputState.PRESSED:
            wall.height += 1
    # contract
    elif action_buffer[t.Action.B] == t.InputState.HELD:
        if action_buffer[t.Action.LEFT] == t.InputState.PRESSED:
            wall.width -= 1
        if action_buffer[t.Action.RIGHT] == t.InputState.PRESSED:
            wall.x += 1
            wall.width -= 1
        if action_buffer[t.Action.UP] == t.InputState.PRESSED:
            wall.height -= 1
        if action_buffer[t.Action.DOWN] == t.InputState.PRESSED:
            wall.y += 1
            wall.height -= 1
    # move
    else:
        if action_buffer[t.Action.LEFT] == t.InputState.PRESSED:
            wall.move_ip(-1, 0)
        if action_buffer[t.Action.RIGHT] == t.InputState.PRESSED:
            wall.move_ip(1, 0)
        if action_buffer[t.Action.UP] == t.InputState.PRESSED:
            wall.move_ip(0, -1)
        if action_buffer[t.Action.DOWN] == t.InputState.PRESSED:
            wall.move_ip(0, 1)
