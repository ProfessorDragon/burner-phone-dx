from components.statemachine import StateMachine, statemachine_change_state
from scenes.scene import Scene
import scenes.scenemapping as scene
from components.settings import Settings, settings_render, settings_update, settings_load
from components.animation import (
    Animator,
    Animation,
    animator_initialise,
    animator_update,
    animator_get_frame,
)
from components.camera import (
    Camera,
    camera_update,
    camera_reset,
)
from components.audio import AudioChannel, play_sound, stop_music, try_play_sound, play_music
from components.fade import (
    ScreenFade,
    fade_active,
    fade_initialise,
    fade_render,
    fade_start,
    fade_update,
)
from enum import IntEnum, auto
import pygame

from components.timer import Timer, timer_reset, timer_update
from components.ui import (
    BUTTON_SIZE,
    Button,
    button_activate,
    ui_list_render,
    ui_list_update_selection,
)
import core.input as t
import core.assets as a
import core.constants as c


class MenuScreen(IntEnum):
    MAIN_MENU = 0
    SETTINGS = auto()
    CREDITS = auto()
    PRE_GAME = auto()


def _fade_music() -> None:
    pygame.mixer.music.fadeout(250)


def _generate_credits() -> pygame.Surface:
    title_height = c.WINDOW_HEIGHT
    line_height = a.DEBUG_FONT.size("0")[1]
    lines = a.CREDITS.split("\n")
    surf = pygame.Surface(
        (c.WINDOW_WIDTH, line_height * len(lines) + title_height), pygame.SRCALPHA
    )
    surf.blit(a.MENU_BACK, (0, 0))
    surf.blit(a.MENU_BLUR, (0, 0))
    for i, ln in enumerate(lines):
        color = c.WHITE
        if ln.startswith("# "):
            ln = ln[2:]
            color = c.GREEN
        elif ln.startswith("## "):
            ln = ln[3:]
            color = c.MAGENTA
        text = a.DEBUG_FONT.render(ln, False, color)
        surf.blit(
            text, (surf.get_width() // 2 - text.get_width() //
                   2, i * line_height + title_height)
        )
    return surf


class Menu(Scene):
    def __init__(self, statemachine: StateMachine) -> None:
        super().__init__(statemachine)

        self.camera = Camera.empty()

        self.fade = ScreenFade()
        fade_initialise(self.fade, 0.25)

        self.scan_lines = Animator()
        animator_initialise(self.scan_lines, {0: Animation(a.MENU_SCANS, 0.1)})

        # buttons
        self.ui_start_button = Button(
            "",
            pygame.Rect(208, 190, *BUTTON_SIZE),
            a.DEBUG_FONT.render("START", False, c.WHITE),
            self.start_controls,
        )

        self.ui_settings_button = Button(
            "",
            pygame.Rect(208, 210, *BUTTON_SIZE),
            a.DEBUG_FONT.render("SETTINGS", False, c.WHITE),
            self.start_settings,
        )

        self.ui_credits_button = Button(
            "",
            pygame.Rect(208, 230, *BUTTON_SIZE),
            a.DEBUG_FONT.render("CREDITS", False, c.WHITE),
            self.start_credits,
        )

        self.ui_quit_button = Button(
            "",
            pygame.Rect(208, 250, *BUTTON_SIZE),
            a.DEBUG_FONT.render("QUIT", False, c.WHITE),
            terminate,
        )

        self.ui_index = 0
        self.last_mouse_position = None

        self.ui_list = [
            self.ui_start_button,
            self.ui_settings_button,
            self.ui_credits_button,
        ]
        if not c.IS_WEB:
            self.ui_list.append(self.ui_quit_button)

        # settings
        self.settings = Settings()

        # credits
        self.credits_timer = Timer()
        self.credits_surf: pygame.Surface = None
        self.should_show_credits = False  # set from Game class

    def enter(self) -> None:
        settings_load(self.settings)
        camera_reset(self.camera)
        self.fade_main_menu()
        if self.should_show_credits:
            self.should_show_credits = False
            play_music(a.STATIC_PATH, -1)
            self.start_credits()

    def execute(
        self,
        surface: pygame.Surface,
        dt: float,
        action_buffer: t.InputBuffer,
        mouse_buffer: t.InputBuffer,
    ) -> None:
        # UPDATE
        fade_update(self.fade, dt)
        camera_update(self.camera, dt)
        animator_update(self.scan_lines, dt)

        if self.screen == MenuScreen.MAIN_MENU:
            mouse_position = pygame.mouse.get_pos()

            self.ui_index = ui_list_update_selection(
                action_buffer,
                (
                    mouse_position
                    if mouse_position != self.last_mouse_position
                    and self.last_mouse_position is not None
                    else None
                ),
                self.ui_list,
                self.ui_index,
            )

            if mouse_buffer[t.MouseButton.LEFT] == t.InputState.PRESSED:
                for element in self.ui_list:
                    if element.rect.collidepoint(mouse_position):
                        button_activate(element)
                        play_sound(AudioChannel.UI, a.UI_SELECT)

            if self.ui_index is not None:
                element = self.ui_list[self.ui_index]
                if t.is_pressed(action_buffer, t.Action.A):
                    button_activate(element)
                    play_sound(AudioChannel.UI, a.UI_SELECT)

            self.last_mouse_position = mouse_position

        elif self.screen == MenuScreen.PRE_GAME:
            if t.is_pressed(action_buffer, t.Action.A) or t.is_pressed(
                mouse_buffer, t.MouseButton.LEFT
            ):
                if not fade_active(self.fade) or self.fade.fading_in:
                    _fade_music()
                    fade_start(
                        self.fade,
                        False,
                        lambda: statemachine_change_state(
                            self.statemachine, scene.SceneState.GAME),
                    )

        elif self.screen == MenuScreen.SETTINGS:
            settings_update(self.settings, dt, action_buffer, mouse_buffer)
            if self.settings.should_exit:
                self.start_main_menu()
                return

        elif self.screen == MenuScreen.CREDITS:
            if timer_update(self.credits_timer, dt):
                fade_start(self.fade, False, self.fade_main_menu)
                return

        # RENDER
        if self.screen == MenuScreen.MAIN_MENU:
            surface.fill((27, 27, 27))
            surface.blit(animator_get_frame(self.scan_lines), (0, 0))
            surface.blit(a.MENU_BACK, (0, 0))
            ui_list_render(surface, self.ui_list, self.ui_index)
            surface.blit(a.MENU_BLUR, (0, 0))

        else:
            surface.blit(a.MENU_BACK_ALT, (0, 0))
            surface.blit(animator_get_frame(self.scan_lines), (0, 0))

        if self.screen == MenuScreen.PRE_GAME:
            surface.blit(
                a.MENU_CONTROLS,
                (
                    surface.get_width() // 2 - a.MENU_CONTROLS.get_width() // 2,
                    surface.get_height() // 2 - a.MENU_CONTROLS.get_height() // 2 - 10,
                ),
            )
            footer = a.DEBUG_FONT.render(
                "Best played in fullscreen with sound on", False, c.WHITE)
            surface.blit(footer, (surface.get_width() //
                         2 - footer.get_width() // 2, 200))

        elif self.screen == MenuScreen.SETTINGS:
            settings_render(self.settings, surface)

        elif self.screen == MenuScreen.CREDITS:
            percent = self.credits_timer.elapsed / self.credits_timer.duration
            y = -percent * self.credits_surf.get_height()
            surface.blit(self.credits_surf, (0, y))

        if self.screen != MenuScreen.MAIN_MENU:
            surface.blit(a.MENU_BLUR_FULL, (0, 0))

        # fade in/out
        fade_render(self.fade, surface)

    def exit(self) -> None:
        stop_music()

    def change_screen(self, screen: MenuScreen) -> None:
        self.screen = screen

    def start_main_menu(self) -> None:
        self.change_screen(MenuScreen.MAIN_MENU)
        play_music(a.THEME_MUSIC_PATH[2], -1)

    def start_controls(self) -> None:
        if not fade_active(self.fade):
            _fade_music()
            fade_start(self.fade, False, self.fade_controls)

    def start_settings(self) -> None:
        self.settings.ui_index = 0
        self.settings.last_mouse_position = pygame.mouse.get_pos()
        self.settings.should_exit = False
        self.change_screen(MenuScreen.SETTINGS)

    def start_credits(self) -> None:
        self.change_screen(MenuScreen.CREDITS)
        self.credits_surf = _generate_credits()
        timer_reset(self.credits_timer, 10)

    def fade_main_menu(self) -> None:
        self.start_main_menu()
        fade_start(self.fade, True)

    def fade_controls(self) -> None:
        self.change_screen(MenuScreen.PRE_GAME)
        fade_start(self.fade, True)
        play_music(a.STATIC_PATH, -1)


def terminate() -> None:
    print("Terminated application")
    pygame.quit()
    raise SystemExit
