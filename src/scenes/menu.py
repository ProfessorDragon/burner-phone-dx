from enum import IntEnum, auto
import pygame

from components.timer import Timer, timer_reset, timer_update
import core.input as t
import core.assets as a
import core.constants as c
from components.fade import (
    ScreenFade,
    fade_active,
    fade_initialise,
    fade_render,
    fade_start,
    fade_update,
)
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

import scenes.scenemapping as scene
from scenes.scene import Scene
from components.statemachine import StateMachine, statemachine_change_state


class MenuScreen(IntEnum):
    MAIN_MENU = 0
    SETTINGS = auto()
    CREDITS = auto()
    PRE_GAME = auto()


def _generate_credits() -> pygame.Surface:
    line_height = a.DEBUG_FONT.size("0")[1]
    lines = a.CREDITS.split("\n")
    surf = pygame.Surface((c.WINDOW_WIDTH, line_height * len(lines)), pygame.SRCALPHA)
    for i, ln in enumerate(lines):
        color = c.WHITE
        if ln.startswith("# "):
            ln = ln[2:]
            color = c.GREEN
        elif ln.startswith("## "):
            ln = ln[3:]
            color = c.MAGENTA
        text = a.DEBUG_FONT.render(ln, False, color)
        surf.blit(text, (surf.get_width() // 2 - text.get_width() // 2, i * line_height))
    return surf


class Menu(Scene):
    def __init__(self, statemachine: StateMachine) -> None:
        super().__init__(statemachine)

        self.camera = Camera.empty()

        self.fade = ScreenFade()
        fade_initialise(self.fade, 0.25)

        self.scan_lines = Animator()
        animator_initialise(self.scan_lines, {0: Animation(a.MENU_SCANS, 0.1)})

        # settings
        self.settings = Settings()

        # credits
        self.credits_timer = Timer()
        self.credits_surf: pygame.Surface = None

    def enter(self) -> None:
        self.screen = MenuScreen.MAIN_MENU
        fade_start(self.fade, True)
        camera_reset(self.camera)
        play_sound(AudioChannel.MUSIC, a.THEME_MUSIC[2], -1)
        #####
        self.start_credits()

    def execute(
        self,
        surface: pygame.Surface,
        dt: float,
        action_buffer: t.InputBuffer,
        mouse_buffer: t.InputBuffer,
    ) -> None:
        # INPUT
        if t.is_pressed(action_buffer, t.Action.START) or t.is_pressed(action_buffer, t.Action.A):
            if not fade_active(self.fade) or self.fade.fading_in:
                if self.screen == MenuScreen.MAIN_MENU:
                    fade_start(self.fade, False, self.fade_controls)
                elif self.screen == MenuScreen.PRE_GAME:
                    fade_start(
                        self.fade,
                        False,
                        lambda: statemachine_change_state(self.statemachine, scene.SceneState.GAME),
                    )

        if t.is_held(action_buffer, t.Action.B):
            self.camera.trauma += 0.01

        # UPDATE

        fade_update(self.fade, dt)
        camera_update(self.camera, dt)
        animator_update(self.scan_lines, dt)

        if self.screen == MenuScreen.CREDITS:
            if timer_update(self.credits_timer, dt):
                fade_start(self.fade, False, self.fade_menu)
                return

        # RENDER

        if self.screen == MenuScreen.PRE_GAME:
            surface.blit(a.MENU_BACK_ALT, (0, 0))
            surface.blit(animator_get_frame(self.scan_lines), (0, 0))
            cx, cy = surface.get_width() // 2, surface.get_height() // 2 - 20
            surface.blit(
                a.MENU_CONTROLS,
                (
                    cx - a.MENU_CONTROLS.get_width() // 2 - 20,
                    cy - a.MENU_CONTROLS.get_height() // 2 + 1,
                ),
            )
            move = a.DEBUG_FONT.render("Move", False, c.WHITE)
            jump = a.DEBUG_FONT.render("Jump", False, c.WHITE)
            roll = a.DEBUG_FONT.render("Roll", False, c.WHITE)
            surface.blit(move, (cx - move.get_width() // 2 - 57, cy - 26))
            surface.blit(jump, (cx - jump.get_width() // 2 + 95, cy - jump.get_height() // 2 - 12))
            surface.blit(roll, (cx - roll.get_width() // 2 + 95, cy - roll.get_height() // 2 + 12))
            footer = a.DEBUG_FONT.render("Best played in fullscreen with sound on", False, c.WHITE)
            surface.blit(footer, (cx - footer.get_width() // 2, cy + 75))
            surface.blit(a.MENU_BLUR_FULL, (0, 0))

        elif self.screen == MenuScreen.CREDITS:
            surface.blit(a.MENU_BACK_ALT, (0, 0))
            surface.blit(animator_get_frame(self.scan_lines), (0, 0))
            percent = self.credits_timer.elapsed / self.credits_timer.duration
            y = surface.get_height() - percent * (
                self.credits_surf.get_height() + surface.get_height()
            )
            surface.blit(self.credits_surf, (0, y))
            surface.blit(a.MENU_BLUR_FULL, (0, 0))

        else:
            surface.blit(a.MENU_BACK, (0, 0))
            # button and settings go here under scan lines
            if self.screen == MenuScreen.SETTINGS:
                settings_render(self.settings, surface)
            surface.blit(animator_get_frame(self.scan_lines), (0, 0))
            surface.blit(a.MENU_BLUR, (0, 0))

        # fade in/out
        fade_render(self.fade, surface)

    def exit(self) -> None:
        stop_music()

    def start_credits(self) -> None:
        self.screen = MenuScreen.CREDITS
        self.credits_surf = _generate_credits()
        timer_reset(self.credits_timer, 10)

    def fade_menu(self) -> None:
        self.screen = MenuScreen.MAIN_MENU
        fade_start(self.fade, True)

    def fade_controls(self) -> None:
        self.screen = MenuScreen.PRE_GAME
        fade_start(self.fade, True)
