from collections import deque
from functools import partial
import pygame

from components.audio import AudioChannel, play_sound, stop_all_sounds, try_play_sound
from components.decor import Decor
from components.entities.camera_boundary import CameraBoundaryEntity
from components.timer import (
    Stopwatch,
    Timer,
    stopwatch_reset,
    stopwatch_update,
    timer_reset,
    timer_update,
)
import core.assets as a
import core.constants as c
import core.input as t

from components.dialogue import (
    DialogueSystem,
    dialogue_execute_script_scene,
    dialogue_has_executed_scene,
    dialogue_initialise,
    dialogue_load_script,
    dialogue_remove_executed_scene,
    dialogue_render,
    dialogue_reset_queue,
    dialogue_update,
)
from components.editor import Editor, editor_render, editor_update
from components.entities.entity import Entity, entity_render, entity_reset, entity_update
from components.player import (
    MainStoryProgress,
    Player,
    PlayerCaughtStyle,
    player_reset,
    player_rect,
    player_render_overlays,
    player_update,
    player_render,
)
from components.tiles import (
    TileData,
    grid_collision_rect,
    tile_render,
    tile_render_hitbox,
    wall_render,
)
from components.camera import (
    Camera,
    camera_follow,
    camera_rect,
    camera_update,
    camera_reset,
)

from scenes.scene import RenderLayer, Scene, scene_reset
import scenes.scenemapping as scene
from components.statemachine import StateMachine, statemachine_change_state


def _tile_size_rect(x: float, y: float, w: float = 1, h: float = 1) -> pygame.Rect:
    return pygame.Rect(x * c.TILE_SIZE, y * c.TILE_SIZE, w * c.TILE_SIZE, h * c.TILE_SIZE)


def _tile_size_vec(x: float, y: float) -> pygame.Vector2:
    return pygame.Vector2(x * c.TILE_SIZE, y * c.TILE_SIZE)


def _story_progression_logic(player: Player, dialogue: DialogueSystem, phone_timer: Timer) -> None:
    if player.progression.main_story == MainStoryProgress.INTRO:
        # opening call
        if (
            dialogue_has_executed_scene(dialogue, "OPENING CALL 1")
            and not dialogue_has_executed_scene(dialogue, "OPENING ACCEPT MAIN")
            and phone_timer.remaining <= 0
        ):
            timer_reset(
                phone_timer,
                5,
                lambda: dialogue_execute_script_scene(dialogue, "OPENING CALL 2"),
            )

        # this is REQUIRED to make the shadowless tree dialogue go smoothly.
        # and yes this took like two hours to figure out. please don't change it :'(
        if dialogue_has_executed_scene(
            dialogue, "REVOKE COMMS"
        ) and not dialogue_has_executed_scene(dialogue, "SHADOWLESS TREE"):
            # if trying to revoke comms but it hasn't played shadowless tree yet, stop trying to revoke comms
            dialogue_remove_executed_scene(dialogue, "REVOKE COMMS")

    elif player.progression.main_story == MainStoryProgress.COMMS:
        if (
            dialogue_has_executed_scene(dialogue, "REVOKE COMMS")
            and dialogue_has_executed_scene(dialogue, "SHADOWLESS TREE")
            and not dialogue_has_executed_scene(dialogue, "SETUP ACCEPT")
        ):
            # if trying to revoke comms, played shadowless tree, and declined the call, reset to intro
            player.progression.main_story = MainStoryProgress.INTRO
            dialogue_remove_executed_scene(dialogue, "SHADOWLESS TREE")


def _post_death_comms(
    story: MainStoryProgress, dialogue: DialogueSystem, caught_style: PlayerCaughtStyle
) -> None:
    if story < MainStoryProgress.COMMS:
        return
    state_name = "FIRST"
    if story >= MainStoryProgress.HALFWAY:
        state_name = "SECOND"
    scene_name = f"{state_name} CAUGHT {caught_style.name}"
    if not dialogue_has_executed_scene(dialogue, scene_name):
        dialogue_execute_script_scene(dialogue, scene_name)


def _camera_target(player: Player) -> pygame.Vector2:
    return pygame.Vector2(player_rect(player.motion).center)


class Game(Scene):
    def __init__(self, statemachine: StateMachine) -> None:
        super().__init__(statemachine)

        self.paused = False
        self.pause_overlay = pygame.Surface(c.WINDOW_SIZE)
        self.pause_overlay.fill(c.WHITE)
        self.pause_overlay.set_alpha(128)

        self.player = Player(_tile_size_vec(6.5, -10.5))

        self.camera = Camera.empty()
        self.camera.offset = pygame.Vector2(c.WINDOW_WIDTH / 2, c.WINDOW_HEIGHT / 2)

        self.dialogue = DialogueSystem()
        dialogue_initialise(self.dialogue)
        dialogue_load_script(self.dialogue, a.GAME_SCRIPT)

        self.global_stopwatch = Stopwatch()
        self.phone_timer = Timer()
        self.comms_timer = Timer()

        self.music_index = 1

        self.grid_collision: set[tuple[int, int]] = set()
        self.grid_tiles: dict[tuple[int, int], list[TileData]] = {}
        self.walls: list[pygame.Rect] = []
        self.entities: list[Entity] = []
        self.decor: list[Decor] = []

        self.editor = Editor(self)
        self.editor.load()

    # everything here runs when the player dies as wel as when the game begins
    # anything exclusive to the game beginning should go in init
    def enter(self) -> None:
        camera_reset(self.camera)
        dialogue_reset_queue(self.dialogue)
        if not dialogue_has_executed_scene(self.dialogue, "OPENING CALL 1"):
            timer_reset(
                self.phone_timer,
                1,
                lambda: dialogue_execute_script_scene(self.dialogue, "OPENING CALL 1"),
            )
        stopwatch_reset(self.global_stopwatch)
        for entity in self.entities:
            entity_reset(entity)
        # 'try' so it does't restart when player dies
        try_play_sound(AudioChannel.MUSIC, a.THEME_MUSIC[self.music_index], -1)

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

        camera_target = _camera_target(self.player)
        in_dialogue = dialogue_update(
            self.dialogue, dt, action_buffer, mouse_buffer, self.camera, camera_target
        )
        if not in_dialogue:
            _story_progression_logic(self.player, self.dialogue, self.phone_timer)

        # update and render entities within this area
        entity_bounds = camera_rect(self.camera).inflate(c.TILE_SIZE * 12, c.TILE_SIZE * 12)

        if not self.paused:
            if self.editor.enabled:
                camera_follow(self.camera, *camera_target)
                camera_update(self.camera, dt)

            elif not in_dialogue:
                # change music after dialogue finished
                if self.dialogue.desired_music_index is not None:
                    self.music_index = self.dialogue.desired_music_index
                    play_sound(AudioChannel.MUSIC, a.THEME_MUSIC[self.music_index], -1)
                    self.dialogue.desired_music_index = None

                # reset scene after player is caught
                if timer_update(self.player.caught_timer, dt):
                    scene_reset(self)
                    timer_reset(
                        self.comms_timer,
                        0.5,
                        partial(
                            _post_death_comms,
                            self.player.progression.main_story,
                            self.dialogue,
                            self.player.caught_style,
                        ),
                    )
                    player_reset(self.player)

                    # instantly update the camera to the target so any boundaries don't accidentally get locked on
                    camera_target = _camera_target(self.player)
                    self.camera.motion.position = camera_target
                    for ent in self.entities:
                        if isinstance(ent, CameraBoundaryEntity):
                            entity_update(
                                ent,
                                dt,
                                self.global_stopwatch.elapsed,
                                self.player,
                                self.camera,
                                self.grid_collision,
                            )

                stopwatch_update(self.global_stopwatch, dt)
                if self.player.caught_timer.remaining <= 0:
                    timer_update(self.phone_timer, dt)
                    timer_update(self.comms_timer, dt)

                # player
                player_update(
                    self.player, dt, action_buffer, self.grid_collision, self.walls, self.dialogue
                )

                # camera (after player so it can follow, before entities to enact bounds)
                camera_follow(self.camera, *camera_target)
                camera_update(self.camera, dt)

                # entities
                for entity in self.entities:
                    path = entity.get_path()
                    if path:
                        bound_rects = [pygame.Rect(point, (1, 1)) for point in path]
                    else:
                        bound_rects = [entity.get_hitbox()]
                    if entity_bounds.collidelist(bound_rects) >= 0:
                        entity_update(
                            entity,
                            dt,
                            self.global_stopwatch.elapsed,
                            self.player,
                            self.camera,
                            self.grid_collision,
                        )

                # pausing
                if t.is_pressed(action_buffer, t.Action.SELECT):
                    self.paused = True
                    play_sound(AudioChannel.UI, a.UI_SELECT)

        else:
            # paused
            if t.is_pressed(action_buffer, t.Action.SELECT):
                self.paused = False
                play_sound(AudioChannel.UI, a.UI_HOVER)

        # RENDER

        # background
        surface.fill(c.GRAY)  # can remove once map is made

        # for some reason, subtracting the z position looks good.
        terrain_cutoff = round(self.player.motion.position.y - self.player.z_position + 32)

        # render tiles within this area
        tile_bounds = pygame.Rect(
            (self.camera.motion.position.x - self.camera.offset.x - self.camera.shake_offset.x)
            // c.TILE_SIZE,
            (self.camera.motion.position.y - self.camera.offset.y - self.camera.shake_offset.y)
            // c.TILE_SIZE,
            surface.get_width() // c.TILE_SIZE,
            surface.get_height() // c.TILE_SIZE,
        )

        # behind player
        cutoff_bg_tiles = deque()
        cutoff_fg_tiles = deque()
        for y in range(tile_bounds.top, tile_bounds.bottom + 1):
            for x in range(tile_bounds.left, tile_bounds.right + 1):
                for tile in self.grid_tiles.get((x, y), []):
                    if tile.render_z < 0:
                        tile_render(surface, self.camera, x, y, tile)
                    elif terrain_cutoff > (y + tile.render_z + 1) * c.TILE_SIZE:
                        cutoff_bg_tiles.append((x, y, tile))
                    else:
                        cutoff_fg_tiles.append((x, y, tile))
        for entity in self.entities:
            if entity_bounds.colliderect(entity.get_hitbox()):
                entity_render(entity, surface, self.camera, RenderLayer.RAYS)
        while cutoff_bg_tiles:
            x, y, tile = cutoff_bg_tiles.popleft()
            tile_render(surface, self.camera, x, y, tile)
        for entity in self.entities:
            if entity_bounds.colliderect(entity.get_hitbox()):
                entity_render(
                    entity,
                    surface,
                    self.camera,
                    (
                        RenderLayer.PLAYER_BG
                        if entity.get_terrain_cutoff() < terrain_cutoff
                        else RenderLayer.BACKGROUND
                    ),
                )

        # player
        player_render(self.player, surface, self.camera)

        # in front of player
        while cutoff_fg_tiles:
            x, y, tile = cutoff_fg_tiles.popleft()
            tile_render(surface, self.camera, x, y, tile)
        for entity in self.entities:
            if entity_bounds.colliderect(entity.get_hitbox()):
                entity_render(
                    entity,
                    surface,
                    self.camera,
                    (
                        RenderLayer.PLAYER_FG
                        if entity.get_terrain_cutoff() >= terrain_cutoff
                        else RenderLayer.FOREGROUND
                    ),
                )

        # hitboxes
        if c.DEBUG_HITBOXES:
            for i, wall in enumerate(self.walls):
                wall_render(surface, self.camera, i, wall)
            for y in range(tile_bounds.top, tile_bounds.bottom + 1):
                for x in range(tile_bounds.left, tile_bounds.right + 1):
                    crect = grid_collision_rect(self.grid_collision, x, y)
                    if crect is not None:
                        wall_render(surface, self.camera, None, crect)
                    for tile in self.grid_tiles.get((x, y), []):
                        tile_render_hitbox(surface, self.camera, x, y, tile)

        # player again
        player_render_overlays(self.player, surface, self.camera)

        # ui
        dialogue_render(self.dialogue, surface)
        editor_render(self.editor, surface)

        if self.paused:
            surface.blit(self.pause_overlay, (0, 0))

    def exit(self) -> None:
        stop_all_sounds()
