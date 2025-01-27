from enum import Enum
import json
from math import ceil
import os
import random
import subprocess
import pygame

from components.decor import Decor, decor_from_json, decor_rect, decor_to_json
from components.entities.all import ENTITY_CLASSES, entity_from_json
from components.entities.entity import Entity, render_path
from components.player import player_reset
from components.tile import TileData, tile_render, tile_render_hitbox
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
from utilities.math import list_range


EDITOR_DEFAULT_LEVEL = "assets/default_level.json"
TILE_GROUPS = {
    0: [  # floor + lake
        list_range(9, 11) + [0] * 6,
        list_range(12, 14) + [3] * 6,
        list_range(20, 23),
        list_range(42, 44),
    ],
    3: [  # walls
        list_range(1, 4) + [0],
        list_range(5, 16) + [0],
        list_range(18, 21) + [17] * 6,
    ],
    4: [  # above floor
        list_range(3, 7) + [0] * 12,
        list_range(8, 12) + [1] * 12,
        list_range(14, 19) + [2] * 12,
    ],
    5: [  # bottom edging
        [1, 2] * 6 + list_range(3, 7),
        [9, 10] * 6 + list_range(11, 14),
    ],
    7: [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9], [10, 11]],  # side edging
}


class EditorMode(Enum):
    VIEW = "view"
    TILES = "tiles"
    WALLS = "walls"
    ENTITY = "entities"
    DECOR = "decor"


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


def _nudge_region(scene: Scene, old_region: pygame.Rect, tdx: float, tdy: float) -> None:
    dx, dy = tdx * c.TILE_SIZE, tdy * c.TILE_SIZE
    vec = pygame.Vector2(dx, dy)
    new_region = old_region.copy()
    new_region.topleft += vec
    tile_region = pygame.Rect(
        new_region.x // c.TILE_SIZE,
        new_region.y // c.TILE_SIZE,
        new_region.w // c.TILE_SIZE,
        new_region.h // c.TILE_SIZE,
    )
    for y in (
        range(tile_region.top, tile_region.bottom)
        if tdy <= 0
        else range(tile_region.bottom - 1, tile_region.top - 1, -1)
    ):
        for x in (
            range(tile_region.left, tile_region.right)
            if tdx <= 0
            else range(tile_region.right - 1, tile_region.left - 1, -1)
        ):
            old_id = (x - tdx, y - tdy)
            new_id = (x, y)
            scene.grid_tiles[new_id] = scene.grid_tiles.get(old_id, [])
            if old_id in scene.grid_tiles:
                scene.grid_tiles.pop(old_id)
            if old_id in scene.grid_collision:
                scene.grid_collision.remove(old_id)
                scene.grid_collision.add(new_id)
    for wall in scene.walls:
        if old_region.colliderect(wall):
            wall.topleft += vec
    for i, ent in enumerate(scene.entities):
        if old_region.colliderect(ent.get_hitbox()):
            _nudge_entity(scene, i, dx, dy)
    for dec in scene.decor:
        if old_region.colliderect(decor_rect(dec)):
            dec.position += vec
    old_region.topleft += vec


def _nudge_entity(scene: Scene, idx: int, dx: float, dy: float) -> Entity:
    js = scene.entities[idx].to_json()
    js["class"] = scene.entities[idx].__class__.__name__
    if "pos" in js:
        js["pos"] = (js["pos"][0] + dx, js["pos"][1] + dy)
    if "path" in js:
        js["path"] = [(point[0] + dx, point[1] + dy) for point in js["path"]]
    scene.entities[idx] = entity_from_json(js)


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
        # any mode
        self.drag_start: pygame.Vector2 = None
        self.drag_tile: tuple[int, int] = None
        # view mode
        self.measure_tile: tuple[int, int] = None
        self.move_region: pygame.Rect = None
        # tile mode
        self.tile_data = TileData()
        self.stored_tile_data = TileData()
        self.tile_group_index = -1
        # entity mode
        self.entity_index = 0
        self.entity_path: list[pygame.Vector2] = []
        # decor mode
        self.decor_index = 0

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
            "decor": [decor_to_json(dec) for dec in self.scene.decor],
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
        self.scene.decor = [decor_from_json(dec) for dec in data["decor"]]

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
        if t.is_pressed(self.mouse_buffer, t.MouseButton.LEFT):
            if self.a_held:
                self.drag_start = _camera_from_mouse(self.scene.camera)
            else:
                x, y = _floor_point(_camera_from_mouse(self.scene.camera), False)
                if self.measure_tile == (x, y):
                    self.measure_tile = None
                else:
                    self.measure_tile = (x, y)

        if self.drag_start is not None:
            end = _camera_from_mouse(self.scene.camera)
            self.move_region = pygame.Rect(self.drag_start, (end - self.drag_start))
            if t.is_released(self.mouse_buffer, t.MouseButton.LEFT):
                if self.move_region.w <= 0 or self.move_region.h <= 0:
                    self.move_region = None
                else:
                    self.drag_start, end = _floor_point(self.drag_start), _ceil_point(end)
                    self.move_region = pygame.Rect(self.drag_start, (end - self.drag_start))
                self.drag_start = None

        if t.is_pressed(self.mouse_buffer, t.MouseButton.RIGHT):
            self.measure_tile = None
            self.move_region = None

        if self.a_held:
            if self.move_region is not None:
                if t.is_pressed(self.action_buffer, t.Action.LEFT):
                    _nudge_region(self.scene, self.move_region, -1, 0)
                if t.is_pressed(self.action_buffer, t.Action.RIGHT):
                    _nudge_region(self.scene, self.move_region, 1, 0)
                if t.is_pressed(self.action_buffer, t.Action.UP):
                    _nudge_region(self.scene, self.move_region, 0, -1)
                if t.is_pressed(self.action_buffer, t.Action.DOWN):
                    _nudge_region(self.scene, self.move_region, 0, 1)

        else:
            vec = pygame.Vector2(
                t.is_held(self.action_buffer, t.Action.RIGHT)
                - t.is_held(self.action_buffer, t.Action.LEFT),
                t.is_held(self.action_buffer, t.Action.DOWN)
                - t.is_held(self.action_buffer, t.Action.UP),
            )
            if self.b_held:
                vec *= 2000
            else:
                vec *= self.scene.player.walk_speed * 2
            self.scene.player.motion.position += vec * self.dt

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

        if self.drag_start is not None:
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

        if len(self.scene.walls) > 0 and self.a_held and c.DEBUG_HITBOXES:
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
            self.debug_text = (
                f"GROUP {self.tile_group_index}, {self.tile_data.y}, {int(self.tile_data.render_z)}"
            )
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
                for x in TILE_GROUPS[self.tile_data.y][self.tile_group_index]:
                    tile_copy = self.tile_data.copy()
                    tile_copy.x = x
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
            self.tile_group_index = -1

        if t.is_pressed(self.action_buffer, t.Action.LEFT):
            if self.a_held:
                if self.tile_data.y in TILE_GROUPS:
                    if self.tile_group_index < 0:
                        self.tile_group_index = 0
                    self.tile_group_index = (self.tile_group_index - 1) % len(
                        TILE_GROUPS[self.tile_data.y]
                    )
                    self.tile_data.x = TILE_GROUPS[self.tile_data.y][self.tile_group_index][0]
            else:
                self.tile_group_index = -1
                self.tile_data.x = (self.tile_data.x - 1) % (a.TERRAIN.get_width() // c.TILE_SIZE)
        if t.is_pressed(self.action_buffer, t.Action.RIGHT):
            if self.a_held:
                if self.tile_data.y in TILE_GROUPS:
                    self.tile_group_index = (self.tile_group_index + 1) % len(
                        TILE_GROUPS[self.tile_data.y]
                    )
                    self.tile_data.x = TILE_GROUPS[self.tile_data.y][self.tile_group_index][0]
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
        elif self.drag_start and len(self.scene.entities) > 0:
            ent = self.scene.entities[-1]
            self.debug_text = f"facing {getattr(ent, 'facing', '')}"
            self.debug_text += f"\nw {getattr(ent, 'w', '')} h {getattr(ent, 'h', '')}"
        else:
            entity_name = ENTITY_CLASSES[self.entity_index].__name__
            entity_name = entity_name.removesuffix("Entity").removesuffix("Enemy")
            self.debug_text = f"{self.entity_index} {entity_name}"

        if t.is_pressed(self.mouse_buffer, t.MouseButton.LEFT):
            # path paint
            if self.a_held:
                self.entity_path.append(_floor_point(_camera_from_mouse(self.scene.camera)))
            # place ent
            else:
                x, y = _floor_point(_camera_from_mouse(self.scene.camera))
                if len(self.entity_path) == 0:
                    self.entity_path.append((x, y))
                # just put in a lot of properties, only the necessary ones will be used
                entity = entity_from_json(
                    {
                        "class": ENTITY_CLASSES[self.entity_index].__name__,
                        "pos": (x, y),
                        "w": 1,
                        "h": 1,
                        "path": self.entity_path,
                        "facing": 0,
                    }
                )
                self.scene.entities.append(entity)
                self.drag_start = pygame.Vector2(x, y)
                self.entity_path.clear()

        if t.is_pressed(self.mouse_buffer, t.MouseButton.RIGHT):
            # path paint
            if self.a_held:
                if len(self.entity_path) > 0:
                    self.entity_path.pop()
            # delete entity
            else:
                pos = _camera_from_mouse(self.scene.camera)
                for i, entity in enumerate(self.scene.entities[::-1]):
                    if entity.get_hitbox().collidepoint(pos):
                        self.scene.entities.pop(len(self.scene.entities) - 1 - i)
                        break

        if t.is_pressed(self.mouse_buffer, t.MouseButton.MIDDLE):
            pos = _camera_from_mouse(self.scene.camera)
            for i, entity in enumerate(self.scene.entities[::-1]):
                if entity.get_hitbox().collidepoint(pos):
                    self.entity_index = ENTITY_CLASSES.index(entity.__class__)
                    self.entity_path = [point.copy() for point in entity.get_path() or []]
                    # bring to front
                    self.scene.entities.append(
                        self.scene.entities.pop(len(self.scene.entities) - 1 - i)
                    )
                    break

        ent = self.scene.entities[-1] if len(self.scene.entities) > 0 else None

        if self.drag_start is not None and ent:
            end = _camera_from_mouse(self.scene.camera)
            dx, dy = _floor_point(end, False) - _floor_point(self.drag_start, False)
            ent.w, ent.h = max(dx + 1, 1), max(dy + 1, 1)
            if (end - self.drag_start).magnitude() > c.TILE_SIZE * 1.5:
                ent.facing = (
                    round((end - self.drag_start).angle_to(pygame.Vector2(1, 0)) / 15.0) * 15
                )
            if t.is_released(self.mouse_buffer, t.MouseButton.LEFT):
                self.drag_start = None

        if t.is_pressed(self.action_buffer, t.Action.LEFT):
            if self.a_held:
                _nudge_entity(self.scene, -1, -c.HALF_TILE_SIZE, 0)
            else:
                self.entity_index = (self.entity_index - 1) % len(ENTITY_CLASSES)
        if t.is_pressed(self.action_buffer, t.Action.RIGHT):
            if self.a_held:
                _nudge_entity(self.scene, -1, c.HALF_TILE_SIZE, 0)
            else:
                self.entity_index = (self.entity_index + 1) % len(ENTITY_CLASSES)
        if t.is_pressed(self.action_buffer, t.Action.UP):
            if self.a_held:
                _nudge_entity(self.scene, -1, 0, -c.HALF_TILE_SIZE)
        if t.is_pressed(self.action_buffer, t.Action.DOWN):
            if self.a_held:
                _nudge_entity(self.scene, -1, 0, c.HALF_TILE_SIZE)

    def decor_mode(self) -> None:
        self.debug_text = f"{self.decor_index}/{len(a.DECOR)-1}"

        if t.is_pressed(self.mouse_buffer, t.MouseButton.LEFT):
            pos = _floor_point(_camera_from_mouse(self.scene.camera))
            self.scene.decor.append(Decor(pos, self.decor_index))

        if t.is_pressed(self.mouse_buffer, t.MouseButton.RIGHT):
            pos = _camera_from_mouse(self.scene.camera)
            for i, dec in enumerate(self.scene.decor[::-1]):
                if decor_rect(dec).collidepoint(pos):
                    self.scene.decor.pop(len(self.scene.decor) - 1 - i)
                    break

        dec = None
        if len(self.scene.decor) > 0:
            dec = self.scene.decor[-1]
        if t.is_pressed(self.action_buffer, t.Action.LEFT):
            if self.a_held and dec:
                dec.position.x -= c.HALF_TILE_SIZE
            else:
                self.decor_index = (self.decor_index - 1) % len(a.DECOR)
        if t.is_pressed(self.action_buffer, t.Action.RIGHT):
            if self.a_held and dec:
                dec.position.x += c.HALF_TILE_SIZE
            else:
                self.decor_index = (self.decor_index + 1) % len(a.DECOR)
        if t.is_pressed(self.action_buffer, t.Action.UP):
            if self.a_held and dec:
                dec.position.y -= c.HALF_TILE_SIZE
        if t.is_pressed(self.action_buffer, t.Action.DOWN):
            if self.a_held and dec:
                dec.position.y += c.HALF_TILE_SIZE


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
        if t.is_held(action_buffer, t.Action.SELECT):
            player_reset(editor.scene.player)
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
    elif just_pressed[pygame.K_2]:
        editor.set_mode(EditorMode.WALLS)
        c.DEBUG_HITBOXES = True
    elif just_pressed[pygame.K_3]:
        editor.set_mode(EditorMode.TILES)
    elif just_pressed[pygame.K_4]:
        editor.set_mode(EditorMode.ENTITY)
    elif just_pressed[pygame.K_5]:
        editor.set_mode(EditorMode.DECOR)

    match editor.mode:
        case EditorMode.VIEW:
            if not pressed[pygame.K_LCTRL]:
                editor.view_mode()

        case EditorMode.WALLS:
            editor.wall_mode()

        case EditorMode.TILES:
            editor.tile_mode()

        case EditorMode.ENTITY:
            editor.entity_mode()

        case EditorMode.DECOR:
            editor.decor_mode()


def editor_render(editor: Editor, surface: pygame.Surface):
    if c.DEBUG_HITBOXES:
        origin = camera_to_screen_shake(editor.scene.camera, 0, 0)
        screen = (origin[0] % surface.get_width(), origin[1] % surface.get_height())
        pygame.draw.line(surface, c.BLACK, (0, screen[1]), (surface.get_width(), screen[1]))
        pygame.draw.line(surface, c.BLACK, (screen[0], 0), (screen[0], surface.get_height()))

    if not editor.enabled:
        return

    match editor.mode:
        case EditorMode.VIEW:
            if editor.measure_tile is not None:
                pygame.draw.rect(
                    surface,
                    c.BLACK,
                    camera_to_screen_shake_rect(
                        editor.scene.camera,
                        editor.measure_tile[0] * c.TILE_SIZE,
                        editor.measure_tile[1] * c.TILE_SIZE,
                        c.TILE_SIZE,
                        c.TILE_SIZE,
                    ),
                    1,
                )
                text = a.DEBUG_FONT.render(
                    f"{editor.measure_tile[0]},{editor.measure_tile[1]}", False, c.WHITE, c.BLACK
                )
                y_offset = (
                    -text.get_height() - 0.25 * c.TILE_SIZE
                    if _camera_from_mouse(editor.scene.camera).y
                    > (editor.measure_tile[1] + 1) * c.TILE_SIZE
                    else 1.25 * c.TILE_SIZE
                )
                surface.blit(
                    text,
                    camera_to_screen_shake(
                        editor.scene.camera,
                        (editor.measure_tile[0] + 0.5) * c.TILE_SIZE - text.get_width() // 2,
                        editor.measure_tile[1] * c.TILE_SIZE + y_offset,
                    ),
                )
            if editor.move_region is not None:
                pygame.draw.rect(
                    surface,
                    c.YELLOW,
                    camera_to_screen_shake_rect(editor.scene.camera, *editor.move_region),
                    1,
                )

        case EditorMode.TILES:
            x, y = _floor_point(_camera_from_mouse(editor.scene.camera), False)
            new_tile_data = editor.tile_data.copy()
            if editor.a_held:
                new_tile_data.render_z += 1
            if new_tile_data in editor.scene.grid_tiles.get((x, y), []):
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
                tile_render(surface, editor.scene.camera, x, y, new_tile_data)
                tile_render_hitbox(surface, editor.scene.camera, x, y, new_tile_data)
            surface.blit(
                a.TERRAIN,
                (
                    surface.get_width() // 2 - c.HALF_TILE_SIZE - new_tile_data.x * c.TILE_SIZE,
                    surface.get_height() - c.TILE_SIZE,
                ),
                (0, new_tile_data.y * c.TILE_SIZE, a.TERRAIN.get_width(), c.TILE_SIZE),
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

        case EditorMode.ENTITY:
            render_path(surface, editor.scene.camera, editor.entity_path, c.WHITE)
            x, y = _floor_point(_camera_from_mouse(editor.scene.camera))
            pygame.draw.circle(
                surface,
                c.RED if editor.a_held else c.WHITE,
                camera_to_screen_shake(editor.scene.camera, x, y),
                2,
            )

    # debug text
    debug_text = str(editor.mode)
    if editor.debug_text is not None:
        debug_text += "\n" + str(editor.debug_text)
    mode_text = a.DEBUG_FONT.render(debug_text, False, c.WHITE, c.BLACK)
    surface.blit(mode_text, (surface.get_width() - mode_text.get_width(), 0))
