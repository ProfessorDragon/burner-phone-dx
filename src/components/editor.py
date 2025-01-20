from dataclasses import dataclass
from enum import Enum
import json
from math import ceil, floor
import pygame

from components.enemy import Enemy, enemy_from_json, enemy_update
import core.input as t
import core.constants as c
import core.assets as a
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


class EditorMode(Enum):
    VIEW = "view"
    WALLS = "walls"
    ENEMIES = "enemies"


class Editor:
    def __init__(self, scene: Scene):
        self.scene = scene
        self.enabled = False
        self.mode = EditorMode.VIEW
        self.dt = 0
        self.action_buffer: t.InputBuffer = None
        self.mouse_buffer: t.InputBuffer = None
        self.wall_paste_start = None
        # self.terrain_paste_tile = (0, 2)
        # self.terrain_paste_layer = 0

    def save(self) -> None:
        data = {
            "walls": [(*wall,) for wall in self.scene.walls],
            "enemies": [
                {"class": enemy.__class__.__name__, **enemy.to_json()}
                for enemy in self.scene.enemies
            ],
        }
        with open("assets/default_level.json", "w") as f:
            json.dump(data, f, separators=(",", ":"))

    def load(self) -> None:
        with open("assets/default_level.json") as f:
            data = json.load(f)
        self.scene.walls = [pygame.Rect(wall) for wall in data["walls"]]
        self.scene.enemies = [enemy_from_json(enemy) for enemy in data["enemies"]]

    def update_state(
        self, dt: float, action_buffer: t.InputBuffer, mouse_buffer: t.InputBuffer
    ) -> None:
        self.dt = dt
        self.action_buffer = action_buffer
        self.mouse_buffer = mouse_buffer

    def view_mode(self) -> None:
        dx = t.is_held(self.action_buffer, t.Action.RIGHT) - t.is_held(
            self.action_buffer, t.Action.LEFT
        )
        dy = t.is_held(self.action_buffer, t.Action.DOWN) - t.is_held(
            self.action_buffer, t.Action.UP
        )
        move_vec = pygame.Vector2(dx, dy) * self.dt * 250
        self.scene.player.motion.position += move_vec

    def wall_mode(self) -> None:
        if t.is_pressed(self.mouse_buffer, t.MouseButton.LEFT):
            self.wall_paste_start = camera_from_screen(self.scene.camera, *pygame.mouse.get_pos())
            self.scene.walls.append(pygame.Rect(*self.wall_paste_start, 1, 1))
        if t.is_pressed(self.mouse_buffer, t.MouseButton.RIGHT):
            x, y = camera_from_screen(self.scene.camera, *pygame.mouse.get_pos())
            for i, wall in enumerate(self.scene.walls[::-1]):
                if wall.collidepoint(x, y):
                    self.scene.walls.pop(len(self.scene.walls) - 1 - i)
                    break
        if self.wall_paste_start:
            start, end = self.wall_paste_start, camera_from_screen(
                self.scene.camera, *pygame.mouse.get_pos()
            )
            if t.is_held(self.action_buffer, t.Action.A):
                start = (
                    floor(start[0] / c.TILE_SIZE) * c.TILE_SIZE,
                    floor(start[1] / c.TILE_SIZE) * c.TILE_SIZE,
                )
                end = (
                    ceil(end[0] / c.TILE_SIZE) * c.TILE_SIZE,
                    ceil(end[1] / c.TILE_SIZE) * c.TILE_SIZE,
                )
            self.scene.walls[-1] = pygame.Rect(*start, end[0] - start[0], end[1] - start[1])
            if t.is_released(self.mouse_buffer, t.MouseButton.LEFT):
                if start[0] >= end[0] or start[1] >= end[1]:
                    self.scene.walls.pop()
                self.wall_paste_start = None

        if len(self.scene.walls) == 0:
            return

        wall = self.scene.walls[-1]
        # expand
        if t.is_held(self.action_buffer, t.Action.A):
            if t.is_pressed(self.action_buffer, t.Action.LEFT):
                wall.x -= 1
                wall.width += 1
            if t.is_pressed(self.action_buffer, t.Action.RIGHT):
                wall.width += 1
            if t.is_pressed(self.action_buffer, t.Action.UP):
                wall.y -= 1
                wall.height += 1
            if t.is_pressed(self.action_buffer, t.Action.DOWN):
                wall.height += 1
        # contract
        elif t.is_held(self.action_buffer, t.Action.B):
            if t.is_pressed(self.action_buffer, t.Action.LEFT):
                wall.width -= 1
            if t.is_pressed(self.action_buffer, t.Action.RIGHT):
                wall.x += 1
                wall.width -= 1
            if t.is_pressed(self.action_buffer, t.Action.UP):
                wall.height -= 1
            if t.is_pressed(self.action_buffer, t.Action.DOWN):
                wall.y += 1
                wall.height -= 1
        # move
        else:
            if t.is_pressed(self.action_buffer, t.Action.LEFT):
                wall.move_ip(-1, 0)
            if t.is_pressed(self.action_buffer, t.Action.RIGHT):
                wall.move_ip(1, 0)
            if t.is_pressed(self.action_buffer, t.Action.UP):
                wall.move_ip(0, -1)
            if t.is_pressed(self.action_buffer, t.Action.DOWN):
                wall.move_ip(0, 1)

    def enemy_mode(self) -> None:
        pass


def editor_update(
    editor: Editor, dt: float, action_buffer: t.InputBuffer, mouse_buffer: t.InputBuffer
) -> None:
    just_pressed = pygame.key.get_just_pressed()

    # editor toggle
    if just_pressed[pygame.K_e]:
        editor.enabled = not editor.enabled

    if not editor.enabled:
        return

    pressed = pygame.key.get_pressed()

    # save/load
    if pressed[pygame.K_LCTRL]:
        if just_pressed[pygame.K_s]:
            editor.save()
            return
        if just_pressed[pygame.K_o]:
            editor.load()
            return

    editor.update_state(dt, action_buffer, mouse_buffer)

    if just_pressed[pygame.K_1]:
        editor.mode = EditorMode.VIEW
    elif just_pressed[pygame.K_2]:
        editor.mode = EditorMode.WALLS
    elif just_pressed[pygame.K_3]:
        editor.mode = EditorMode.ENEMIES

    match editor.mode:
        case EditorMode.VIEW:
            if not pressed[pygame.K_LCTRL]:
                editor.view_mode()

        case EditorMode.WALLS:
            editor.wall_mode()

        case EditorMode.ENEMIES:
            editor.enemy_mode()


def editor_render(editor: Editor, surface: pygame.Surface):
    if editor.enabled:
        mode_text = a.DEBUG_FONT.render(str(editor.mode), False, c.WHITE, c.BLACK)
        surface.blit(mode_text, (surface.get_width() - mode_text.get_width(), 0))
