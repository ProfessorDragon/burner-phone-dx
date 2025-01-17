import pygame

from components.player import Player, player_rect, player_update
from components.walls import draw_wall, tile_size_rect
import core.input as input
import core.constants as c
import core.assets as asset
from components.motion import Vector2, Motion
from components.camera import (
    Camera,
    camera_follow,
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

        self.player = Player(Motion.empty())

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

        self.walls = [
            tile_size_rect(4, 5),
            tile_size_rect(5, 5),
            tile_size_rect(5, 4),
            tile_size_rect(6, 6),
        ]
        # self.enemies: list[Enemy] = []

    def enter(self) -> None:
        camera_reset(self.camera)
        pygame.mixer.Channel(0).play(asset.DEBUG_THEME_GAME, -1)

    def execute(
        self,
        surface: pygame.Surface,
        dt: float,
        action_buffer: input.InputBuffer,
        mouse_buffer: input.InputBuffer,
    ) -> None:
        # INPUT
        if action_buffer[input.Action.START] == input.InputState.PRESSED:
            statemachine_change_state(self.statemachine, scene.SceneState.MENU)
            return

        if action_buffer[input.Action.SELECT] == input.InputState.PRESSED:
            # Might want to enable pause UI here
            # Set Pause UI overlay to top option
            self.paused = not self.paused

        # UPDATE
        if self.paused:
            pass

        else:
            player_update(self.player, dt, action_buffer, self.walls)
            # for enemy in self.enemies: enemy_update

            camera_follow(self.camera, *player_rect(self.player.motion).center)
            camera_update(self.camera, dt)

        # RENDER
        surface.fill(c.MAGENTA)

        for y in range(1, int(surface.get_height() / c.TILE_SIZE)):
            pygame.draw.line(
                surface,
                c.BLACK,
                (0, y * c.TILE_SIZE),
                (surface.get_width(), y * c.TILE_SIZE),
            )
        for x in range(1, int(surface.get_width() / c.TILE_SIZE)):
            pygame.draw.line(
                surface,
                c.BLACK,
                (x * c.TILE_SIZE, 0),
                (x * c.TILE_SIZE, surface.get_height()),
            )

        for wall in self.walls:
            draw_wall(surface, self.camera, wall)

        surface.blit(
            asset.DEBUG_IMAGE,
            camera_to_screen_shake(self.camera, *self.player.motion.position),
            (0, 0, 32, 32),
        )
        # for enemy in self.enemies: enemy_draw

        if self.paused:
            surface.blit(self.pause_overlay, (0, 0))

    def exit(self) -> None:
        pygame.mixer.Channel(0).stop()
        pygame.mixer.Channel(1).stop()


def bounce(motion: Motion, min_x: int, max_x: int, min_y: int, max_y: int) -> bool:
    bounced = False
    if (
        motion.velocity.x > 0
        and motion.position.x > max_x
        or motion.velocity.x < 0
        and motion.position.x < min_x
    ):
        motion.velocity.x *= -1
        bounced = True

    if (
        motion.velocity.y > 0
        and motion.position.y > max_y
        or motion.velocity.y < 0
        and motion.position.y < min_y
    ):
        motion.velocity.y *= -1
        bounced = True

    return bounced
