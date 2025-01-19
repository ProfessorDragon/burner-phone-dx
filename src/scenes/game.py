import pygame

from components.editor import Editor, editor_update
from components.enemy import PatrolEnemy, SpotlightEnemy, enemy_render, enemy_update
import core.input as t
import core.constants as c
from components.player import (
    player_rect,
    player_update,
    player_render,
    player_initialise,
)
from components.walls import draw_wall
from components.motion import Motion
from components.camera import (
    Camera,
    camera_follow,
    camera_update,
    camera_to_screen_shake,
    camera_reset,
)

from scenes.scene import RenderLayer, Scene
import scenes.scenemapping as scene
from components.statemachine import StateMachine, statemachine_change_state


def tile_size_rect(x: float, y: float, w: float = 1, h: float = 1) -> pygame.Rect:
    return pygame.Rect(x * c.TILE_SIZE, y * c.TILE_SIZE, w * c.TILE_SIZE, h * c.TILE_SIZE)


def tile_size_vec(x: float, y: float) -> pygame.Vector2:
    return pygame.Vector2(x * c.TILE_SIZE, y * c.TILE_SIZE)


class Game(Scene):
    def __init__(self, statemachine: StateMachine) -> None:
        super().__init__(statemachine)

        self.paused = False
        self.pause_overlay = pygame.Surface(c.WINDOW_SIZE)
        self.pause_overlay.fill(c.WHITE)
        self.pause_overlay.set_alpha(128)

        self.player = player_initialise()

        self.camera = Camera(
            Motion(
                pygame.Vector2(*player_rect(self.player.motion).center),
                pygame.Vector2(),
                pygame.Vector2(),
            ),
            pygame.Vector2(),
            pygame.Vector2(),
            pygame.Vector2(30, 30),
        )
        self.camera.offset = pygame.Vector2(c.WINDOW_WIDTH / 2, c.WINDOW_HEIGHT / 2)

        self.background = pygame.Surface((500, 300), pygame.SRCALPHA)
        self.player_layer = pygame.Surface((500, 300), pygame.SRCALPHA)

        # bg grid
        for y in range(1, int(self.background.get_height() / c.TILE_SIZE / c.PERSPECTIVE)):
            pygame.draw.line(
                self.background,
                c.BLACK if y % 2 == 0 else c.GRAY,
                (0, y * c.TILE_SIZE * c.PERSPECTIVE),
                (self.background.get_width(), y * c.TILE_SIZE * c.PERSPECTIVE),
            )
        for x in range(1, int(self.background.get_width() / c.TILE_SIZE)):
            pygame.draw.line(
                self.background,
                c.BLACK,
                (x * c.TILE_SIZE, 0),
                (x * c.TILE_SIZE, self.background.get_height()),
            )

        self.walls: list[pygame.Rect] = [
            tile_size_rect(4, 5),
            tile_size_rect(5, 5),
            tile_size_rect(5, 4),
            tile_size_rect(6, 6),
            tile_size_rect(7, 6),
            tile_size_rect(6, 7),
        ]

        patrol = PatrolEnemy()
        patrol.path = [
            tile_size_vec(3, 5),
            tile_size_vec(3, 7),
            tile_size_vec(2, 6),
        ]
        patrol.motion.position = patrol.path[0].copy()
        spotlight = SpotlightEnemy()
        spotlight.path = [
            tile_size_vec(3, 0),
            tile_size_vec(6, 0),
            tile_size_vec(6, 3),
            tile_size_vec(3, 3),
        ]
        spotlight.motion.position = spotlight.path[0].copy()
        self.enemies: list[PatrolEnemy] = [patrol, spotlight]

    def enter(self) -> None:
        camera_reset(self.camera)
        # pygame.mixer.Channel(0).play(a.DEBUG_THEME_GAME, -1) # driving me insane

    def execute(
        self,
        surface: pygame.Surface,
        dt: float,
        action_buffer: t.InputBuffer,
        mouse_buffer: t.InputBuffer,
    ) -> None:

        # INPUT
        if action_buffer[t.Action.START] == t.InputState.PRESSED:
            statemachine_change_state(self.statemachine, scene.SceneState.MENU)
            return

        if action_buffer[t.Action.SELECT] == t.InputState.PRESSED:
            # Might want to enable pause UI here
            # Set Pause UI overlay to top option
            self.paused = not self.paused

        # UPDATE

        editor_update(self, action_buffer, mouse_buffer)

        if not self.paused:
            if not Editor.enabled:
                player_update(self.player, dt, action_buffer, self.walls)
                for enemy in self.enemies:
                    enemy_update(enemy, dt, self.player)
            camera_follow(self.camera, *player_rect(self.player.motion).center)
            camera_update(self.camera, dt)

        # RENDER

        # background
        surface.fill(c.WHITE)
        surface.blit(self.background, camera_to_screen_shake(self.camera, 0, 0))

        # player feet
        terrain_cutoff = round(self.player.motion.position.y) + 8

        # behind player
        surface.blit(
            self.player_layer,
            camera_to_screen_shake(self.camera, 0, -c.HALF_TILE_SIZE),
            (0, 0, self.player_layer.get_width(), terrain_cutoff),
        )
        for enemy in self.enemies:
            enemy_render(
                enemy,
                surface,
                self.camera,
                (
                    RenderLayer.PLAYER_BG
                    if enemy.motion.position.y <= terrain_cutoff
                    else RenderLayer.BACKGROUND
                ),
            )

        # player
        player_render(self.player, surface, self.camera)

        # in front
        surface.blit(
            self.player_layer,
            camera_to_screen_shake(
                self.camera,
                0,
                -c.HALF_TILE_SIZE + terrain_cutoff,
            ),
            (
                0,
                terrain_cutoff,
                self.player_layer.get_width(),
                self.player_layer.get_height() - terrain_cutoff,
            ),
        )
        for enemy in self.enemies:
            enemy_render(
                enemy,
                surface,
                self.camera,
                (
                    RenderLayer.PLAYER_FG
                    if enemy.motion.position.y > terrain_cutoff
                    else RenderLayer.FOREGROUND
                ),
            )

        # hitboxes
        for i, wall in enumerate(self.walls):
            draw_wall(surface, self.camera, i, wall)

        if self.paused:
            surface.blit(self.pause_overlay, (0, 0))

    def exit(self) -> None:
        pygame.mixer.Channel(0).stop()
        pygame.mixer.Channel(1).stop()
