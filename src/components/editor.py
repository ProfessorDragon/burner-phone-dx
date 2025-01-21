from enum import Enum
import json
from math import ceil
import os
import subprocess
import pygame

from components.enemy import ENEMY_CLASSES, enemy_from_json, render_path
from components.tiles import TileData, render_tile, render_tile_hitbox
import core.input as t
import core.constants as c
import core.assets as a
from components.camera import (
    Camera,
    camera_from_screen,
    camera_to_screen_shake,
    camera_to_screen_shake_rect,
)
from scenes.scene import Scene, scene_reset

EDITOR_DEFAULT_LEVEL = "assets/default_level.json"
TILE_SHORTCUTS = [0, 9, 19, 27, 45]


class EditorMode(Enum):
    VIEW = "view"
    TILES = "tiles"
    WALLS = "walls"
    ENEMIES = "enemies"


def _camera_from_mouse(camera: Camera) -> pygame.Vector2:
    return pygame.Vector2(camera_from_screen(camera, *pygame.mouse.get_pos()))


def _floor_point(vec: pygame.Vector2, upscale=True) -> pygame.Vector2:
    vec = pygame.Vector2(vec.x // c.TILE_SIZE, vec.y // c.TILE_SIZE)
    if upscale:
        return vec * c.TILE_SIZE
    return vec


def _ceil_point(vec: pygame.Vector2, upscale=True) -> pygame.Vector2:
    vec = pygame.Vector2(ceil(vec.x / c.TILE_SIZE), ceil(vec.y / c.TILE_SIZE))
    if upscale:
        return vec * c.TILE_SIZE
    return vec


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
        self.drag_tile: tuple[int, int] = None
        self.tile_data = TileData()
        self.enemy_index = 0
        self.enemy_path: list[pygame.Vector2] = []

    def set_mode(self, mode: EditorMode) -> None:
        self.mode = mode
        self.debug_text = None

    def save(self, *, pretty=False) -> None:
        data = {
            "grid_collision": list(self.scene.grid_collision),
            "grid_tiles": {
                f"{k[0]},{k[1]}": [(*tile,) for tile in tiles]
                for k, tiles in self.scene.grid_tiles.items()
            },
            "walls": [(*wall,) for wall in self.scene.walls],
            "enemies": [
                {"class": enemy.__class__.__name__, **enemy.to_json()}
                for enemy in self.scene.enemies
            ],
        }
        with open(EDITOR_DEFAULT_LEVEL, "w") as f:
            if pretty:
                json.dump(data, f)
            else:
                json.dump(data, f, separators=(",", ":"))

    def load(self) -> None:
        with open(EDITOR_DEFAULT_LEVEL) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print("ERROR: Failed to parse level data")
                return
        self.scene.grid_collision = set([tuple(pos) for pos in data["grid_collision"]])
        self.scene.grid_tiles = {
            (*map(int, k.split(",")),): [TileData(*tile) for tile in tiles]
            for k, tiles in data["grid_tiles"].items()
        }
        self.scene.walls = [pygame.Rect(wall) for wall in data["walls"]]
        self.scene.enemies = [enemy_from_json(enemy) for enemy in data["enemies"]]

    def update_state(
        self, dt: float, action_buffer: t.InputBuffer, mouse_buffer: t.InputBuffer
    ) -> None:
        self.dt = dt
        self.action_buffer = action_buffer
        self.mouse_buffer = mouse_buffer

    def view_mode(self) -> None:
        a_held = t.is_held(self.action_buffer, t.Action.A)
        dx = t.is_held(self.action_buffer, t.Action.RIGHT) - t.is_held(
            self.action_buffer, t.Action.LEFT
        )
        dy = t.is_held(self.action_buffer, t.Action.DOWN) - t.is_held(
            self.action_buffer, t.Action.UP
        )
        move_vec = pygame.Vector2(dx, dy) * self.dt * (50 if a_held else 250)
        self.scene.player.motion.position += move_vec

    def wall_mode(self) -> None:
        a_held = t.is_held(self.action_buffer, t.Action.A)
        if a_held:
            self.debug_text = "free"
        else:
            self.debug_text = "grid"

        if t.is_held(self.mouse_buffer, t.MouseButton.LEFT) and not a_held:
            x, y = _floor_point(_camera_from_mouse(self.scene.camera), False)
            id = (int(x), int(y))
            if self.drag_tile != id:
                if id in self.scene.grid_collision:
                    self.scene.grid_collision.remove(id)
                else:
                    self.scene.grid_collision.add(id)
            self.drag_tile = id
        else:
            self.drag_tile = None

        if t.is_pressed(self.mouse_buffer, t.MouseButton.LEFT) and a_held:
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

    def tile_mode(self) -> None:
        a_held = t.is_held(self.action_buffer, t.Action.A)
        self.debug_text = f"{self.tile_data.x}, {self.tile_data.y}, {int(self.tile_data.render_z)}"
        if a_held:
            self.debug_text += " z+"

        if t.is_held(self.mouse_buffer, t.MouseButton.LEFT):
            new_tile_data = self.tile_data.copy()
            if a_held:
                new_tile_data.render_z += 1
            x, y = _floor_point(_camera_from_mouse(self.scene.camera), False)
            id = (int(x), int(y))
            cur = self.scene.grid_tiles.get(id, [])
            if new_tile_data not in cur:
                self.scene.grid_tiles.setdefault(id, [])
                # replace bg tiles
                if new_tile_data.render_z < 0 and len(cur) > 0 and cur[0].render_z < 0:
                    self.scene.grid_tiles[id][0] = new_tile_data
                # append to mg tiles
                else:
                    self.scene.grid_tiles[id].append(new_tile_data)

        if t.is_held(self.mouse_buffer, t.MouseButton.RIGHT):
            x, y = _floor_point(_camera_from_mouse(self.scene.camera), False)
            id = (int(x), int(y))
            if self.drag_tile != id and len(self.scene.grid_tiles.get(id, [])) > 0:
                self.scene.grid_tiles[id].pop()
                if len(self.scene.grid_tiles[id]) == 0:
                    self.scene.grid_tiles.pop(id)
            self.drag_tile = id
        else:
            self.drag_tile = None

        if t.is_pressed(self.mouse_buffer, t.MouseButton.MIDDLE):
            x, y = _floor_point(_camera_from_mouse(self.scene.camera), False)
            id = (int(x), int(y))
            if len(self.scene.grid_tiles.get(id, [])) > 0:
                print(self.scene.grid_tiles[id])
                self.tile_data = self.scene.grid_tiles[id][-1].copy()

        shortcuts = TILE_SHORTCUTS
        if t.is_pressed(self.action_buffer, t.Action.LEFT):
            if a_held:
                for pos in shortcuts[::-1]:
                    if pos < self.tile_data.x:
                        self.tile_data.x = pos
                        break
                else:  # fancy :-)
                    self.tile_data.x = shortcuts[-1]
                self.tile_data.y = 0
            else:
                self.tile_data.x = (self.tile_data.x - 1) % 64
        if t.is_pressed(self.action_buffer, t.Action.RIGHT):
            if a_held:
                for pos in shortcuts:
                    if pos > self.tile_data.x:
                        self.tile_data.x = pos
                        break
                else:
                    self.tile_data.x = shortcuts[0]
                self.tile_data.y = 0
            else:
                self.tile_data.x = (self.tile_data.x + 1) % 64
        if t.is_pressed(self.action_buffer, t.Action.DOWN):
            if a_held:
                self.tile_data.render_z = max(self.tile_data.render_z - 1, -1)
            else:
                self.tile_data.y = (self.tile_data.y - 1) % 3
        if t.is_pressed(self.action_buffer, t.Action.UP):
            if a_held:
                self.tile_data.render_z += 1
            else:
                self.tile_data.y = (self.tile_data.y + 1) % 3

    def enemy_mode(self) -> None:
        a_held = t.is_held(self.action_buffer, t.Action.A)
        if a_held:
            self.debug_text = "path paint"
        else:
            if self.drag_start and len(self.scene.enemies) > 0:
                self.debug_text = f"facing {getattr(self.scene.enemies[-1], 'facing', '')}"
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
    pressed = pygame.key.get_pressed()

    if editor.enabled and pressed[pygame.K_LCTRL]:
        # save
        if just_pressed[pygame.K_s]:
            editor.save()
            return
        # load
        if just_pressed[pygame.K_o]:
            editor.load()
            return
        # raw edit (for directly modifying json data)
        if just_pressed[pygame.K_e]:
            editor.save(pretty=True)
            subprocess.call(["notepad", os.path.abspath(EDITOR_DEFAULT_LEVEL)])
            editor.load()
            return

    # debug shortcuts
    if just_pressed[pygame.K_r]:
        scene_reset(editor.scene)
    if just_pressed[pygame.K_f]:
        c.DEBUG_HITBOXES = not c.DEBUG_HITBOXES

    # editor toggle
    if just_pressed[pygame.K_e]:
        editor.enabled = not editor.enabled

    if not editor.enabled:
        return

    editor.update_state(dt, action_buffer, mouse_buffer)

    if just_pressed[pygame.K_1]:
        editor.set_mode(EditorMode.VIEW)
    elif just_pressed[pygame.K_2]:
        editor.set_mode(EditorMode.WALLS)
    elif just_pressed[pygame.K_3]:
        editor.set_mode(EditorMode.TILES)
    elif just_pressed[pygame.K_4]:
        editor.set_mode(EditorMode.ENEMIES)

    match editor.mode:
        case EditorMode.VIEW:
            if not pressed[pygame.K_LCTRL]:
                editor.view_mode()

        case EditorMode.WALLS:
            editor.wall_mode()

        case EditorMode.TILES:
            editor.tile_mode()

        case EditorMode.ENEMIES:
            editor.enemy_mode()


def editor_render(editor: Editor, surface: pygame.Surface):
    if not editor.enabled:
        return

    match editor.mode:
        case EditorMode.TILES:
            x, y = _floor_point(_camera_from_mouse(editor.scene.camera), False)
            if editor.tile_data in editor.scene.grid_tiles.get((x, y), []):
                pygame.draw.rect(
                    surface,
                    c.WHITE,
                    camera_to_screen_shake_rect(
                        editor.scene.camera,
                        x * c.TILE_SIZE,
                        y * c.TILE_SIZE,
                        c.TILE_SIZE,
                        c.TILE_SIZE,
                    ),
                    1,
                )
            else:
                new_tile_data = editor.tile_data.copy()
                if t.is_held(editor.action_buffer, t.Action.A):
                    new_tile_data.render_z += 1
                render_tile(surface, editor.scene.camera, x, y, new_tile_data)
                render_tile_hitbox(surface, editor.scene.camera, x, y, new_tile_data)
            surface.blit(
                a.TERRAIN,
                (
                    surface.get_width() // 2 - c.HALF_TILE_SIZE - editor.tile_data.x * c.TILE_SIZE,
                    surface.get_height() - c.TILE_SIZE,
                ),
                (0, editor.tile_data.y * c.TILE_SIZE, a.TERRAIN.get_width(), c.TILE_SIZE),
            )
            pygame.draw.rect(
                surface,
                c.WHITE,
                pygame.Rect(
                    surface.get_width() // 2 - c.HALF_TILE_SIZE,
                    surface.get_height() - c.TILE_SIZE,
                    c.TILE_SIZE,
                    c.TILE_SIZE,
                ),
                1,
            )

        case EditorMode.ENEMIES:
            x, y = _floor_point(_camera_from_mouse(editor.scene.camera))
            pygame.draw.circle(
                surface, c.WHITE, camera_to_screen_shake(editor.scene.camera, x, y), 2
            )
            render_path(surface, editor.scene.camera, editor.enemy_path)

    # debug text
    debug_text = str(editor.mode)
    if editor.debug_text is not None:
        debug_text += "\n" + str(editor.debug_text)
    mode_text = a.DEBUG_FONT.render(debug_text, False, c.WHITE, c.BLACK)
    surface.blit(mode_text, (surface.get_width() - mode_text.get_width(), 0))
