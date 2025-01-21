from dataclasses import dataclass
from enum import Enum
import json
from math import ceil, floor
import pygame

from components.enemy import ENEMY_CLASSES, enemy_from_json, render_path
import core.input as t
import core.constants as c
import core.assets as a
from components.camera import Camera, camera_from_screen
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


def _camera_from_mouse(camera: Camera) -> pygame.Vector2:
    return pygame.Vector2(camera_from_screen(camera, *pygame.mouse.get_pos()))


def _floor_point(vec: pygame.Vector2) -> pygame.Vector2:
    return pygame.Vector2(
        floor(vec.x / c.TILE_SIZE) * c.TILE_SIZE,
        floor(vec.y / c.TILE_SIZE) * c.TILE_SIZE,
    )


def _ceil_point(vec: pygame.Vector2) -> pygame.Vector2:
    return pygame.Vector2(
        ceil(vec.x / c.TILE_SIZE) * c.TILE_SIZE,
        ceil(vec.y / c.TILE_SIZE) * c.TILE_SIZE,
    )


class Editor:
    def __init__(self, scene: Scene):
        self.scene = scene
        self.enabled = False
        self.mode = EditorMode.VIEW
        self.dt = 0
        self.action_buffer: t.InputBuffer = None
        self.mouse_buffer: t.InputBuffer = None
        self.debug_text: str = None
        self.drag_start: pygame.Vector2 = None
        self.enemy_index = 0
        self.enemy_path: list[pygame.Vector2] = []
        # self.terrain_paste_tile = (0, 2)
        # self.terrain_paste_layer = 0

    def set_mode(self, mode: EditorMode) -> None:
        self.mode = mode
        self.debug_text = None

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
        a_held = t.is_held(self.action_buffer, t.Action.A)
        b_held = t.is_held(self.action_buffer, t.Action.B)
        if a_held:
            if self.drag_start:
                self.debug_text = "snap"
            else:
                self.debug_text = "expand"
        elif b_held:
            self.debug_text = "contract"
        else:
            self.debug_text = "place/move"

        if t.is_pressed(self.mouse_buffer, t.MouseButton.LEFT):
            self.drag_start = _camera_from_mouse(self.scene.camera)
            self.scene.walls.append(pygame.Rect(*self.drag_start, 1, 1))

        if t.is_pressed(self.mouse_buffer, t.MouseButton.RIGHT):
            pos = _camera_from_mouse(self.scene.camera)
            for i, wall in enumerate(self.scene.walls[::-1]):
                if wall.collidepoint(pos):
                    self.scene.walls.pop(len(self.scene.walls) - 1 - i)
                    break

        if self.drag_start:
            start = self.drag_start.copy()
            end = _camera_from_mouse(self.scene.camera)
            if a_held:
                start, end = _floor_point(start), _ceil_point(end)
            self.scene.walls[-1] = pygame.Rect(*start, end.x - start.x, end.y - start.y)
            if t.is_released(self.mouse_buffer, t.MouseButton.LEFT):
                if start.x >= end.x or start.y >= end.y:
                    self.scene.walls.pop()
                self.drag_start = None

        if len(self.scene.walls) == 0:
            return

        wall = self.scene.walls[-1]
        # expand
        if a_held:
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
        elif b_held:
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
        a_held = t.is_held(self.action_buffer, t.Action.A)
        if a_held:
            self.debug_text = "path paint"
        else:
            if self.drag_start:
                self.debug_text = "set facing"
            else:
                self.debug_text = "place enemy"

        if t.is_pressed(self.mouse_buffer, t.MouseButton.LEFT):
            # path paint
            if a_held:
                self.enemy_path.append(_floor_point(_camera_from_mouse(self.scene.camera)))
            # place enemy
            else:
                pos = _floor_point(_camera_from_mouse(self.scene.camera))
                if len(self.enemy_path) == 0:
                    self.enemy_path.append(pos)
                # just put in a lot of properties, only the necessary ones will be used
                enemy = enemy_from_json(
                    {
                        "class": ENEMY_CLASSES[self.enemy_index].__name__,
                        "pos": (*pos,),
                        "path": self.enemy_path,
                        "facing": 0,
                    }
                )
                self.scene.enemies.append(enemy)
                self.drag_start = pos
                self.enemy_path.clear()

        if t.is_pressed(self.mouse_buffer, t.MouseButton.RIGHT):
            # path paint
            if a_held:
                if len(self.enemy_path) > 0:
                    self.enemy_path.pop()
            # delete enemy
            else:
                pos = _camera_from_mouse(self.scene.camera)
                for i, enemy in enumerate(self.scene.enemies[::-1]):
                    if enemy.get_hitbox().collidepoint(pos):
                        self.scene.enemies.pop(len(self.scene.enemies) - 1 - i)
                        break

        if self.drag_start:
            end = _camera_from_mouse(self.scene.camera)
            if (end - self.drag_start).magnitude() > c.TILE_SIZE * 1.5:
                self.scene.enemies[-1].facing = (
                    round((end - self.drag_start).angle_to(pygame.Vector2(1, 0)) / 5.0) * 5
                )
            if t.is_released(self.mouse_buffer, t.MouseButton.LEFT):
                self.drag_start = None

        if t.is_pressed(self.action_buffer, t.Action.UP):
            self.enemy_index = (self.enemy_index + 1) % len(ENEMY_CLASSES)
        if t.is_pressed(self.action_buffer, t.Action.DOWN):
            self.enemy_index = (self.enemy_index - 1) % len(ENEMY_CLASSES)

        self.debug_text += (
            f"\n{self.enemy_index} {ENEMY_CLASSES[self.enemy_index].__name__.removesuffix('Enemy')}"
        )


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
        editor.set_mode(EditorMode.VIEW)
    elif just_pressed[pygame.K_2]:
        editor.set_mode(EditorMode.WALLS)
    elif just_pressed[pygame.K_3]:
        editor.set_mode(EditorMode.ENEMIES)

    match editor.mode:
        case EditorMode.VIEW:
            if not pressed[pygame.K_LCTRL]:
                editor.view_mode()

        case EditorMode.WALLS:
            editor.wall_mode()

        case EditorMode.ENEMIES:
            editor.enemy_mode()


def editor_render(editor: Editor, surface: pygame.Surface):
    if not editor.enabled:
        return
    # enemy path
    if editor.mode == EditorMode.ENEMIES:
        render_path(surface, editor.scene.camera, editor.enemy_path)
    # debug text
    debug_text = str(editor.mode)
    if editor.debug_text is not None:
        debug_text += "\n" + str(editor.debug_text)
    mode_text = a.DEBUG_FONT.render(debug_text, False, c.WHITE, c.BLACK)
    surface.blit(mode_text, (surface.get_width() - mode_text.get_width(), 0))
