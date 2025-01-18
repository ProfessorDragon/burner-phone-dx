import pygame

from components.editor import Editor, editor_update
import core.input as t
import core.constants as c
import core.assets as a
from components.player import (
    player_rect,
    player_update,
    player_render,
    player_initialise,
)
from components.walls import draw_wall, tile_size_rect
from components.motion import Vector2, Motion
from components.camera import (
    Camera,
    camera_follow,
    camera_from_screen,
    camera_update,
    camera_to_screen_shake,
    camera_reset,
)

from scenes.scene import Scene
import scenes.scenemapping as scene
from components.statemachine import StateMachine, statemachine_change_state


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
                Vector2(*player_rect(self.player.motion).center), Vector2(), Vector2()
            ),
            Vector2(),
            Vector2(),
            Vector2(30, 30),
        )
        # not sure why this was removed?
        self.camera.offset = Vector2(c.WINDOW_WIDTH / 2, c.WINDOW_HEIGHT / 2)

        self.background = pygame.Surface((500, 300), pygame.SRCALPHA)
        self.player_layer = pygame.Surface((500, 300), pygame.SRCALPHA)

        # bg grid
        for y in range(1, int(self.background.get_height() / c.TILE_SIZE)):
            pygame.draw.line(
                self.background,
                c.BLACK,
                (0, y * c.TILE_SIZE),
                (self.background.get_width(), y * c.TILE_SIZE),
            )
        for x in range(1, int(self.background.get_width() / c.TILE_SIZE)):
            pygame.draw.line(
                self.background,
                c.BLACK,
                (x * c.TILE_SIZE, 0),
                (x * c.TILE_SIZE, self.background.get_height()),
            )

        self.walls = [
            tile_size_rect(4, 5),
            tile_size_rect(5, 5),
            tile_size_rect(5, 4),
            tile_size_rect(6, 6),
            tile_size_rect(7, 6),
            tile_size_rect(6, 7),
        ]
        # self.enemies: list[Enemy] = []

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

        editor_update(self, action_buffer, mouse_buffer)

        # UPDATE
        if self.paused:
            pass

        else:
            if not Editor.enabled:
                player_update(self.player, dt, action_buffer, self.walls)
            # for enemy in self.enemies: enemy_update
            camera_follow(self.camera, *player_rect(self.player.motion).center)
            camera_update(self.camera, dt)

        # RENDER
        surface.fill(c.WHITE)

        px, py = round(self.player.motion.position.x), round(
            self.player.motion.position.y
        )

        surface.blit(self.background, camera_to_screen_shake(self.camera, 0, 0))

        surface.blit(
            self.player_layer,
            camera_to_screen_shake(self.camera, 0, -c.HALF_TILE_SIZE),
            (0, 0, self.player_layer.get_width(), py + 8),
        )

        player_render(self.player, surface, self.camera)

        surface.blit(
            self.player_layer,
            camera_to_screen_shake(
                self.camera,
                0,
                -c.HALF_TILE_SIZE + py + 8,
            ),
            (
                0,
                py + 8,
                self.player_layer.get_width(),
                self.player_layer.get_height() - py - 8,
            ),
        )

        for i, wall in enumerate(self.walls):
            draw_wall(surface, self.camera, i, wall)

        # for enemy in self.enemies: enemy_draw

        if self.paused:
            surface.blit(self.pause_overlay, (0, 0))

    def exit(self) -> None:
        pygame.mixer.Channel(0).stop()
        pygame.mixer.Channel(1).stop()
