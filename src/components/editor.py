from enum import Enum
import json
from math import ceil
import os
import random
import subprocess
import pygame

from components.entities.all import ENTITY_CLASSES, entity_from_json
from components.entities.entity import render_path
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
TILE_GROUPS = [
    [(9, 0), (10, 0), (11, 0)] + [(0, 0)] * 3,
    [(12, 0), (13, 0), (14, 0)] + [(3, 0)] * 3,
    [(20, 0), (21, 0), (22, 0), (23, 0)],
]


class EditorMode(Enum):
    VIEW = "view"
    TILES = "tiles"
    WALLS = "walls"
    ENTITIES = "entities"


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
        self.a_held = False
        self.b_held = False
        self.debug_text: str = None
        self.drag_start: pygame.Vector2 = None
        self.drag_tile: tuple[int, int] = None
        self.tile_data = TileData()
        self.stored_tile_data = TileData()
        self.tile_group_index = -1
        self.entity_index = 0
        self.entity_path: list[pygame.Vector2] = []

    def set_mode(self, mode: EditorMode) -> None:
        if self.mode == mode:
            return
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
            "entities": [
                {"class": entity.__class__.__name__, **entity.to_json()}
                for entity in self.scene.entities
            ],
        }
        with open(EDITOR_DEFAULT_LEVEL, "w") as f:
            if pretty:
                json.dump(data, f)
            else:
                json.dump(data, f, separators=(",", ":"))

    def load(self) -> None:
        if not os.path.isfile(EDITOR_DEFAULT_LEVEL):
            return
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
        self.scene.entities = [entity_from_json(entity) for entity in data["entities"]]

    def update_state(
        self, dt: float, action_buffer: t.InputBuffer, mouse_buffer: t.InputBuffer
    ) -> None:
        self.dt = dt
        self.action_buffer = action_buffer
        self.mouse_buffer = mouse_buffer
        self.a_held = t.is_held(self.action_buffer, t.Action.A) or t.is_held(
            action_buffer, t.Action.SELECT
        )
        self.b_held = t.is_held(self.action_buffer, t.Action.B)

    def view_mode(self) -> None:
        dx = t.is_held(self.action_buffer, t.Action.RIGHT) - t.is_held(
            self.action_buffer, t.Action.LEFT
        )
        dy = t.is_held(self.action_buffer, t.Action.DOWN) - t.is_held(
            self.action_buffer, t.Action.UP
        )
        move_vec = pygame.Vector2(dx, dy) * self.dt * (50 if self.a_held else 250)
        self.scene.player.motion.position += move_vec

    def wall_mode(self) -> None:
        if self.a_held:
            self.debug_text = "free"
        else:
            self.debug_text = "grid"

        if t.is_held(self.mouse_buffer, t.MouseButton.LEFT) and not self.a_held:
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

        if t.is_pressed(self.mouse_buffer, t.MouseButton.LEFT) and self.a_held:
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
            if self.a_held:
                start, end = _floor_point(start), _ceil_point(end)
            self.scene.walls[-1] = pygame.Rect(*start, end.x - start.x, end.y - start.y)
            if t.is_released(self.mouse_buffer, t.MouseButton.LEFT):
                if start.x > end.x or start.y > end.y:
                    self.scene.walls.pop()
                if start.x == end.x:
                    self.scene.walls[-1].width += 2
                    self.scene.walls[-1].x -= 1
                if start.y == end.y:
                    self.scene.walls[-1].height += 2
                    self.scene.walls[-1].y -= 1
                self.drag_start = None

        if len(self.scene.walls) == 0 or not c.DEBUG_HITBOXES:
            return

        wall = self.scene.walls[-1]
        if t.is_pressed(self.action_buffer, t.Action.LEFT):
            wall.x -= 1
        if t.is_pressed(self.action_buffer, t.Action.RIGHT):
            wall.x += 1
        if t.is_pressed(self.action_buffer, t.Action.UP):
            wall.y -= 1
        if t.is_pressed(self.action_buffer, t.Action.DOWN):
            wall.y += 1

    def tile_mode(self) -> None:
        if self.tile_group_index < 0:
            self.debug_text = (
                f"{self.tile_data.x}, {self.tile_data.y}, {int(self.tile_data.render_z)}"
            )
        else:
            self.debug_text = f"GROUP {self.tile_group_index}"
        if self.a_held:
            self.debug_text += " z+"
        if self.b_held:
            self.debug_text += " add"

        if t.is_held(self.mouse_buffer, t.MouseButton.LEFT):
            new_tile_data = []
            if self.tile_group_index < 0:
                tile_copy = self.tile_data.copy()
                if self.a_held:
                    tile_copy.render_z += 1
                new_tile_data.append(tile_copy)
            else:
                for x, y in TILE_GROUPS[self.tile_group_index]:
                    tile_copy = self.tile_data.copy()
                    tile_copy.x, tile_copy.y = x, y
                    if self.a_held:
                        tile_copy.render_z += 1
                    new_tile_data.append(tile_copy)
            x, y = _floor_point(_camera_from_mouse(self.scene.camera), False)
            id = (int(x), int(y))
            cur = self.scene.grid_tiles.get(id, [])
            if all(tile_copy not in cur for tile_copy in new_tile_data):
                self.scene.grid_tiles.setdefault(id, [])
                # add
                if self.b_held:
                    self.scene.grid_tiles[id].append(random.choice(new_tile_data))
                    self.scene.grid_tiles[id].sort(key=lambda tile: tile.render_z)
                # overwrite
                else:
                    self.scene.grid_tiles[id] = [random.choice(new_tile_data)]

        if t.is_held(self.mouse_buffer, t.MouseButton.RIGHT):
            x, y = _floor_point(_camera_from_mouse(self.scene.camera), False)
            id = (int(x), int(y))
            if self.drag_tile != id and len(self.scene.grid_tiles.get(id, [])) > 0:
                if self.b_held:
                    self.scene.grid_tiles.pop(id)
                else:
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
                tile = self.scene.grid_tiles[id][-1]
                if self.tile_data == tile:
                    self.tile_data = self.stored_tile_data
                else:
                    self.stored_tile_data = self.tile_data.copy()
                    self.tile_data = tile.copy()

        if t.is_pressed(self.action_buffer, t.Action.LEFT):
            if self.a_held:
                if self.tile_group_index < 0:
                    self.tile_group_index = 0
                self.tile_group_index = (self.tile_group_index - 1) % len(TILE_GROUPS)
                self.tile_data.x, self.tile_data.y = TILE_GROUPS[self.tile_group_index][0]
            else:
                self.tile_group_index = -1
                self.tile_data.x = (self.tile_data.x - 1) % (a.TERRAIN.get_width() // c.TILE_SIZE)
        if t.is_pressed(self.action_buffer, t.Action.RIGHT):
            if self.a_held:
                self.tile_group_index = (self.tile_group_index + 1) % len(TILE_GROUPS)
                self.tile_data.x, self.tile_data.y = TILE_GROUPS[self.tile_group_index][0]
            else:
                self.tile_group_index = -1
                self.tile_data.x = (self.tile_data.x + 1) % (a.TERRAIN.get_width() // c.TILE_SIZE)
        if t.is_pressed(self.action_buffer, t.Action.DOWN):
            if self.a_held:
                self.tile_data.render_z = max(self.tile_data.render_z - 1, -1)
            else:
                self.tile_group_index = -1
                self.tile_data.y = (self.tile_data.y + 1) % (a.TERRAIN.get_height() // c.TILE_SIZE)
        if t.is_pressed(self.action_buffer, t.Action.UP):
            if self.a_held:
                self.tile_data.render_z += 1
            else:
                self.tile_group_index = -1
                self.tile_data.y = (self.tile_data.y - 1) % (a.TERRAIN.get_height() // c.TILE_SIZE)

    def entity_mode(self) -> None:
        if self.a_held:
            self.debug_text = "path paint"
        else:
            if self.drag_start and len(self.scene.entities) > 0:
                self.debug_text = f"facing {getattr(self.scene.entities[-1], 'facing', '')}"
            else:
                self.debug_text = "place entity"

        if t.is_pressed(self.mouse_buffer, t.MouseButton.LEFT):
            # path paint
            if self.a_held:
                self.entity_path.append(_floor_point(_camera_from_mouse(self.scene.camera)))
            # place ent
            else:
                pos = _floor_point(_camera_from_mouse(self.scene.camera))
                if len(self.entity_path) == 0:
                    self.entity_path.append(pos)
                # just put in a lot of properties, only the necessary ones will be used
                entity = entity_from_json(
                    {
                        "class": ENTITY_CLASSES[self.entity_index].__name__,
                        "pos": (*pos,),
                        "path": self.entity_path,
                        "facing": 0,
                    }
                )
                self.scene.entities.append(entity)
                self.drag_start = pos
                self.entity_path.clear()

        if t.is_pressed(self.mouse_buffer, t.MouseButton.RIGHT):
            # path paint
            if self.a_held:
                if len(self.entity_path) > 0:
                    self.entity_path.pop()
            # delete ent
            else:
                pos = _camera_from_mouse(self.scene.camera)
                for i, entity in enumerate(self.scene.entities[::-1]):
                    if entity.get_hitbox().collidepoint(pos):
                        self.scene.entities.pop(len(self.scene.entities) - 1 - i)
                        break

        if self.drag_start:
            end = _camera_from_mouse(self.scene.camera)
            if (end - self.drag_start).magnitude() > c.TILE_SIZE * 1.5:
                self.scene.entities[-1].facing = (
                    round((end - self.drag_start).angle_to(pygame.Vector2(1, 0)) / 10.0) * 10
                )
            if t.is_released(self.mouse_buffer, t.MouseButton.LEFT):
                self.drag_start = None

        if t.is_pressed(self.action_buffer, t.Action.LEFT):
            self.entity_index = (self.entity_index - 1) % len(ENTITY_CLASSES)
        if t.is_pressed(self.action_buffer, t.Action.RIGHT):
            self.entity_index = (self.entity_index + 1) % len(ENTITY_CLASSES)

        entity_name = ENTITY_CLASSES[self.entity_index].__name__
        entity_name = entity_name.removesuffix("Entity").removesuffix("Enemy")
        self.debug_text += f"\n{self.entity_index} {entity_name}"


def editor_update(
    editor: Editor, dt: float, action_buffer: t.InputBuffer, mouse_buffer: t.InputBuffer
) -> None:
    just_pressed = pygame.key.get_just_pressed()
    pressed = pygame.key.get_pressed()

    if editor.enabled and pressed[pygame.K_LCTRL]:
        # save
        if pressed[pygame.K_s] and t.is_pressed(action_buffer, t.Action.DOWN):
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
    if just_pressed[pygame.K_t]:
        c.TIME_DILATION = 0.25 if c.TIME_DILATION == 1.0 else 1.0

    # editor toggle
    if just_pressed[pygame.K_e]:
        editor.enabled = not editor.enabled

    if not editor.enabled:
        return

    editor.update_state(dt, action_buffer, mouse_buffer)

    if just_pressed[pygame.K_1]:
        editor.set_mode(EditorMode.VIEW)
        c.DEBUG_HITBOXES = False
    elif just_pressed[pygame.K_2]:
        editor.set_mode(EditorMode.WALLS)
        c.DEBUG_HITBOXES = True
    elif just_pressed[pygame.K_3]:
        editor.set_mode(EditorMode.TILES)
        c.DEBUG_HITBOXES = False
    elif just_pressed[pygame.K_4]:
        editor.set_mode(EditorMode.ENTITIES)
        c.DEBUG_HITBOXES = True

    match editor.mode:
        case EditorMode.VIEW:
            if not pressed[pygame.K_LCTRL]:
                editor.view_mode()

        case EditorMode.WALLS:
            editor.wall_mode()

        case EditorMode.TILES:
            editor.tile_mode()

        case EditorMode.ENTITIES:
            editor.entity_mode()


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
                c.WHITE if editor.tile_group_index < 0 else c.BLUE,
                pygame.Rect(
                    surface.get_width() // 2 - c.HALF_TILE_SIZE - 1,
                    surface.get_height() - c.TILE_SIZE - 1,
                    c.TILE_SIZE + 2,
                    c.TILE_SIZE + 2,
                ),
                1,
            )

        case EditorMode.ENTITIES:
            x, y = _floor_point(_camera_from_mouse(editor.scene.camera))
            pygame.draw.circle(
                surface, c.WHITE, camera_to_screen_shake(editor.scene.camera, x, y), 2
            )
            render_path(surface, editor.scene.camera, editor.entity_path)

    # debug text
    debug_text = str(editor.mode)
    if editor.debug_text is not None:
        debug_text += "\n" + str(editor.debug_text)
    mode_text = a.DEBUG_FONT.render(debug_text, False, c.WHITE, c.BLACK)
    surface.blit(mode_text, (surface.get_width() - mode_text.get_width(), 0))
