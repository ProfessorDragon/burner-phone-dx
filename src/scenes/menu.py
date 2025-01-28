from enum import IntEnum, auto
import pygame

from components.timer import Timer, timer_reset, timer_update
import core.input as t
import core.assets as a
import core.constants as c
import scenes.scenemapping as scene
from components.audio import AudioChannel, play_sound, stop_music
from components.camera import (
    Camera,
    camera_update,
    camera_reset,
)
from components.animation import (
    Animator,
    Animation,
    animator_initialise,
    animator_update,
    animator_get_frame,
)
from components.settings import Settings, settings_render, settings_update
from scenes.scene import Scene
from components.statemachine import StateMachine, statemachine_change_state


class MenuScreen(IntEnum):
    MAIN_MENU = 0
    SETTINGS = auto()
    PRE_GAME = auto()


class Menu(Scene):
    def __init__(self, statemachine: StateMachine) -> None:
        super().__init__(statemachine)

        self.camera = Camera.empty()

        self.settings = Settings()

        self.screen = MenuScreen.MAIN_MENU

        self.fade_timer = Timer()  # for fading the scene into the game
        self.fading_in = False
        self.fade_overlay = pygame.Surface(c.WINDOW_SIZE)
        self.fade_overlay.fill(c.BLACK)

        self.scan_lines = Animator()
        animator_initialise(self.scan_lines, {0: Animation(a.MENU_SCANS, 0.1)})

    def enter(self) -> None:
        camera_reset(self.camera)
        play_sound(AudioChannel.MUSIC, a.THEME_MUSIC[2], -1)

    def execute(
        self,
        surface: pygame.Surface,
        dt: float,
        action_buffer: t.InputBuffer,
        mouse_buffer: t.InputBuffer,
    ) -> None:
        # INPUT
        if t.is_pressed(action_buffer, t.Action.START):
            if self.screen == MenuScreen.MAIN_MENU:
                self.show_controls()
            elif self.screen == MenuScreen.PRE_GAME:
                self.start_game()

        if t.is_held(action_buffer, t.Action.B):
            self.camera.trauma += 0.01

        # UPDATE
        timer_update(self.fade_timer, dt)
        camera_update(self.camera, dt)
        animator_update(self.scan_lines, dt)

        # RENDER
        if self.screen == MenuScreen.PRE_GAME:
            surface.fill(c.BLACK)
            controls = a.DEBUG_FONT.render("insert controls graphic here", False, c.WHITE)
            surface.blit(
                controls,
                (
                    surface.get_width() // 2 - controls.get_width() // 2,
                    surface.get_height() // 2 - controls.get_height() // 2,
                ),
            )
            footer = a.DEBUG_FONT.render("Best played in fullscreen with sound on", False, c.WHITE)
            surface.blit(
                footer,
                (surface.get_width() // 2 - footer.get_width() // 2, surface.get_height() - 50),
            )

        else:
            surface.blit(a.MENU_BACK, (0, 0))

            # button and settings go here under scan lines
            if self.screen == MenuScreen.SETTINGS:
                settings_render(self.settings, surface)

            surface.blit(animator_get_frame(self.scan_lines), (0, 0))
            surface.blit(a.MENU_BLUR, (0, 0))

        # fade in/out
        if self.fade_timer.duration > 0:
            fade_percent = (
                self.fade_timer.remaining if self.fading_in else self.fade_timer.elapsed
            ) / self.fade_timer.duration
            if fade_percent > 0:
                self.fade_overlay.set_alpha(fade_percent * 255)
                surface.blit(self.fade_overlay, (0, 0))

    def exit(self) -> None:
        stop_music()

    def show_controls(self) -> None:
        self.fading_in = False
        timer_reset(self.fade_timer, 0.5, self.show_controls_transition)

    def show_controls_transition(self) -> None:
        self.screen = MenuScreen.PRE_GAME
        self.fading_in = True
        timer_reset(self.fade_timer, 0.5)

    def start_game(self) -> None:
        self.fading_in = False
        timer_reset(
            self.fade_timer,
            0.5,
            lambda: statemachine_change_state(self.statemachine, scene.SceneState.GAME),
        )
