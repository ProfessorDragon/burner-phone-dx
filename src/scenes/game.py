import pygame
import random

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

        self.REBOUND_X = const.WINDOW_WIDTH - asset.DEBUG_SPRITE.get_width()
        self.REBOUND_Y = const.WINDOW_HEIGHT - asset.DEBUG_SPRITE.get_height()

        self.paused = False
        self.pause_overlay = pygame.Surface(const.WINDOW_SIZE)
        self.pause_overlay.fill(const.WHITE)
        self.pause_overlay.set_alpha(128)

        self.camera = Camera(
            Motion(Vector2(), Vector2(), Vector2()),
            Vector2(),
            Vector2(),
            Vector2(30, 30)
        )
        self.bouncing_logos: list[Motion] = [
            Motion(Vector2(), Vector2(), Vector2()) for _ in range(10)]

    def enter(self) -> None:
        camera_reset(self.camera)

        for logo in self.bouncing_logos:
            logo.position.x = random.randint(0, self.REBOUND_X)
            logo.position.y = random.randint(0, self.REBOUND_Y)
            logo.velocity.x = random.randint(-64, 64)
            logo.velocity.y = random.randint(-64, 64)

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
            for logo in self.bouncing_logos:
                motion_update(logo, dt)

                if bounce(logo, 0, self.REBOUND_X, 0, self.REBOUND_Y):
                    self.camera.trauma = 0.5
                    pygame.mixer.Channel(1).play(asset.DEBUG_BONK)

            camera_update(self.camera, dt)

        # RENDER
        surface.fill(const.MAGENTA)

        for logo in self.bouncing_logos:
            surface.blit(
                asset.DEBUG_SPRITE,
                camera_to_screen_shake(self.camera, *logo.position)
            )

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
