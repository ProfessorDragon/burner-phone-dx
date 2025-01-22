from dataclasses import dataclass
from functools import partial
import pygame

from components.timer import Stopwatch, stopwatch_reset, stopwatch_update, timer_update
import core.assets as a
import core.constants as c
import core.input as t

from components.dialogue import (
    DialogueSystem,
    dialogue_execute_script_scene,
    dialogue_has_executed_scene,
    dialogue_initialise,
    dialogue_load_script,
    dialogue_render,
    dialogue_reset_queue,
    dialogue_update,
)
from components.editor import Editor, editor_render, editor_update
from components.entities.entity import Entity, entity_render, entity_reset, entity_update
from components.player import (
    PlayerCaughtStyle,
    player_reset,
    player_rect,
    player_render_overlays,
    player_update,
    player_render,
    player_initialise,
)
from components.tiles import (
    TileData,
    grid_collision_rect,
    render_tile,
    render_tile_hitbox,
    render_wall,
)
from components.camera import (
    Camera,
    camera_follow,
    camera_to_screen_shake,
    camera_update,
    camera_reset,
)

from scenes.scene import RenderLayer, Scene, scene_reset
import scenes.scenemapping as scene
from components.statemachine import StateMachine, statemachine_change_state


@dataclass
class GameProgression:
    checkpoint: pygame.Vector2 = None
    has_comms: bool = False


def _tile_size_rect(x: float, y: float, w: float = 1, h: float = 1) -> pygame.Rect:
    return pygame.Rect(x * c.TILE_SIZE, y * c.TILE_SIZE, w * c.TILE_SIZE, h * c.TILE_SIZE)


def _tile_size_vec(x: float, y: float) -> pygame.Vector2:
    return pygame.Vector2(x * c.TILE_SIZE, y * c.TILE_SIZE)


def _post_death_comms(dialogue: DialogueSystem, caught_style: PlayerCaughtStyle) -> None:
    state_name = "FIRST"  # todo
    scene_name = f"{state_name} CAUGHT {caught_style.name}"
    if not dialogue_has_executed_scene(dialogue, scene_name):
        dialogue_execute_script_scene(dialogue, scene_name)


class Game(Scene):
    def __init__(self, statemachine: StateMachine) -> None:
        super().__init__(statemachine)

        self.paused = False
        self.pause_overlay = pygame.Surface(c.WINDOW_SIZE)
        self.pause_overlay.fill(c.WHITE)
        self.pause_overlay.set_alpha(128)

        self.player = player_initialise()

        self.camera = Camera.empty()
        self.camera.motion.position = pygame.Vector2(player_rect(self.player.motion).center)
        self.camera.offset = pygame.Vector2(c.WINDOW_WIDTH / 2, c.WINDOW_HEIGHT / 2)

        self.dialogue = DialogueSystem()
        dialogue_initialise(self.dialogue)
        dialogue_load_script(self.dialogue, a.GAME_SCRIPT)

        self.progression = GameProgression()
        self.progression.checkpoint = self.player.motion.position.copy()

        self.post_death_stopwatch = Stopwatch()

        self.grid_collision: set[tuple[int, int]] = set()
        self.grid_tiles: dict[tuple[int, int], list[TileData]] = {}
        self.walls: list[pygame.Rect] = []
        self.entities: list[Entity] = []
        # self.decor: list[Decor] = []

        self.editor = Editor(self)
        self.editor.load()

    def enter(self) -> None:
        camera_reset(self.camera)
        dialogue_reset_queue(self.dialogue)
        for entity in self.entities:
            entity_reset(entity)
        # pygame.mixer.Channel(0).play(a.DEBUG_THEME_GAME, -1) # driving me insane

    def execute(
        self,
        surface: pygame.Surface,
        dt: float,
        action_buffer: t.InputBuffer,
        mouse_buffer: t.InputBuffer,
    ) -> None:

        # INPUT
        if t.is_pressed(action_buffer, t.Action.START):
            statemachine_change_state(self.statemachine, scene.SceneState.MENU)
            return

        # UPDATE

        editor_update(self.editor, dt, action_buffer, mouse_buffer)

        in_dialogue = dialogue_update(self.dialogue, dt, action_buffer, mouse_buffer)

        # update and render entities within this area
        entity_bounds = pygame.Rect(
            self.camera.motion.position.x - self.camera.offset.x - c.TILE_SIZE * 8,
            self.camera.motion.position.y - self.camera.offset.y - c.TILE_SIZE * 8,
            surface.get_width() + c.TILE_SIZE * 16,
            surface.get_height() + c.TILE_SIZE * 16,
        )

        if not self.paused:
            if not self.editor.enabled and not in_dialogue:
                # timers
                if self.player.caught_timer.remaining > 0:
                    timer_update(self.player.caught_timer, dt)
                    if self.player.caught_timer.remaining <= 0:
                        scene_reset(self)
                        if self.progression.has_comms:
                            bindings = {
                                0.5: partial(
                                    _post_death_comms, self.dialogue, self.player.caught_style
                                )
                            }
                            stopwatch_reset(self.post_death_stopwatch, bindings)
                        player_reset(self.player, self.progression.checkpoint)
                stopwatch_update(self.post_death_stopwatch, dt)

                # player
                player_update(self.player, dt, action_buffer, self.grid_collision, self.walls)

                # entities
                for entity in self.entities:
                    if entity_bounds.collidepoint(entity.get_hitbox().center):
                        entity_update(entity, dt, self.player, self.camera, self.grid_collision)

                # dialogue
                if t.is_pressed(action_buffer, t.Action.SELECT):
                    # self.paused = True
                    dialogue_execute_script_scene(self.dialogue, "shadowless tree")
                    dialogue_update(self.dialogue, dt)

            # general
            camera_follow(self.camera, *player_rect(self.player.motion).center)
            camera_update(self.camera, dt)

        else:
            # paused
            if t.is_pressed(action_buffer, t.Action.SELECT):
                self.paused = False

        # RENDER

        # background
        surface.fill(c.GRAY)  # can remove once map is made

        # for some reason, subtracting the z position looks good.
        terrain_cutoff = round(self.player.motion.position.y - self.player.z_position)

        # render tiles within this area
        tile_bounds = pygame.Rect(
            (self.camera.motion.position.x - self.camera.offset.x) // c.TILE_SIZE,
            (self.camera.motion.position.y - self.camera.offset.y) // c.TILE_SIZE,
            surface.get_width() // c.TILE_SIZE,
            surface.get_height() // c.TILE_SIZE,
        )

        # behind player
        not_bg_tiles = []
        for y in range(tile_bounds.top, tile_bounds.bottom + 1):
            for x in range(tile_bounds.left, tile_bounds.right + 1):
                for tile in self.grid_tiles.get((x, y), []):
                    if tile.render_z < 0:
                        render_tile(surface, self.camera, x, y, tile)
                    else:
                        not_bg_tiles.append((x, y, tile))
        for entity in self.entities:
            if entity_bounds.collidepoint(entity.get_hitbox().center):
                entity_render(entity, surface, self.camera, RenderLayer.RAYS)
        for x, y, tile in not_bg_tiles:
            if terrain_cutoff + 16 > (y + tile.render_z) * c.TILE_SIZE:
                render_tile(surface, self.camera, x, y, tile)
        for entity in self.entities:
            if entity_bounds.collidepoint(entity.get_hitbox().center):
                entity_render(
                    entity,
                    surface,
                    self.camera,
                    (
                        RenderLayer.PLAYER_BG
                        if entity.motion.position.y <= terrain_cutoff
                        else RenderLayer.BACKGROUND
                    ),
                )

        # player
        player_render(self.player, surface, self.camera)

        # in front of player
        for x, y, tile in not_bg_tiles:
            if terrain_cutoff + 16 <= (y + tile.render_z) * c.TILE_SIZE:
                render_tile(surface, self.camera, x, y, tile)
        for entity in self.entities:
            if entity_bounds.collidepoint(entity.get_hitbox().center):
                entity_render(
                    entity,
                    surface,
                    self.camera,
                    (
                        RenderLayer.PLAYER_FG
                        if entity.motion.position.y > terrain_cutoff
                        else RenderLayer.FOREGROUND
                    ),
                )

        # hitboxes
        if c.DEBUG_HITBOXES:
            origin_text = a.DEBUG_FONT.render("0", False, c.WHITE)
            surface.blit(
                origin_text,
                camera_to_screen_shake(
                    self.camera, -origin_text.get_width() // 2, -origin_text.get_height() // 2
                ),
            )
            for i, wall in enumerate(self.walls):
                render_wall(surface, self.camera, i, wall)
            for y in range(tile_bounds.top, tile_bounds.bottom + 1):
                for x in range(tile_bounds.left, tile_bounds.right + 1):
                    crect = grid_collision_rect(self.grid_collision, x, y)
                    if crect is not None:
                        render_wall(surface, self.camera, None, crect)
                    for tile in self.grid_tiles.get((x, y), []):
                        render_tile_hitbox(surface, self.camera, x, y, tile)

        # player again
        player_render_overlays(self.player, surface, self.camera)

        # ui
        dialogue_render(self.dialogue, surface)
        editor_render(self.editor, surface)

        if self.paused:
            surface.blit(self.pause_overlay, (0, 0))

    def exit(self) -> None:
        pygame.mixer.Channel(0).stop()
        pygame.mixer.Channel(1).stop()
