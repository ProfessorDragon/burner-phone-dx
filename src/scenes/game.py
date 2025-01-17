import pygame

from components.player import Player, player_update
import core.input as input
import core.constants as const
import core.assets as asset
from components.motion import Vector2, Motion, motion_update
from components.camera import (
    Camera, camera_update, camera_to_screen_shake, camera_reset
)

from scenes.scene import Scene
import scenes.scenemapping as scene
from components.statemachine import StateMachine, statemachine_change_state


class Game(Scene):
    def __init__(self, statemachine: StateMachine) -> None:
        super().__init__(statemachine)

        self.paused = False
        self.pause_overlay = pygame.Surface(const.WINDOW_SIZE)
        self.pause_overlay.fill(const.WHITE)
        self.pause_overlay.set_alpha(128)

        self.camera = Camera(
            Motion.empty(),
            Vector2(),
            Vector2(),
            Vector2(30, 30)
        )

        self.player = Player(
            Motion.empty()
        )
        # self.enemies: list[Enemy] = []

    def enter(self) -> None:
        camera_reset(self.camera)
        pygame.mixer.Channel(0).play(asset.DEBUG_THEME_GAME, -1)

    def execute(
        self,
        surface: pygame.Surface,
        dt: float,
        action_buffer: input.InputBuffer,
        mouse_buffer: input.InputBuffer
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
            player_update(self.player, dt, action_buffer)
            # for enemy in self.enemies: enemy_update

            camera_update(self.camera, dt)

        # RENDER
        surface.fill(const.MAGENTA)

        surface.blit(
            asset.DEBUG_IMAGE,
            camera_to_screen_shake(self.camera, *self.player.motion.position)
        )
        # for enemy in self.enemies: enemy_draw

        if self.paused:
            self.surface.blit(self.pause_overlay, (0, 0))

    def exit(self) -> None:
        pygame.mixer.Channel(0).stop()
        pygame.mixer.Channel(1).stop()


def bounce(
    motion: Motion, min_x: int, max_x: int, min_y: int, max_y: int
) -> bool:
    bounced = False
    if (
        motion.velocity.x > 0 and motion.position.x > max_x or
        motion.velocity.x < 0 and motion.position.x < min_x
    ):
        motion.velocity.x *= -1
        bounced = True

    if (
        motion.velocity.y > 0 and motion.position.y > max_y or
        motion.velocity.y < 0 and motion.position.y < min_y
    ):
        motion.velocity.y *= -1
        bounced = True

    return bounced
