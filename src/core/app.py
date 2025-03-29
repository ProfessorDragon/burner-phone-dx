import asyncio
import pygame

import core.setup as setup
import core.assets as a
import core.constants as c
import core.input as t
import core.globals as g

from components.audio import AudioChannel
from components.statemachine import (
    StateMachine,
    statemachine_initialise,
    statemachine_execute,
)
import scenes.scenemapping as scene


def run() -> None:
    pygame.display.set_caption(c.CAPTION)
    pygame.display.set_icon(a.ICON)
    scene_manager = StateMachine()
    statemachine_initialise(scene_manager, scene.SCENE_MAPPING, scene.SceneState.MENU)
    asyncio.run(game_loop(setup.window, setup.clock, scene_manager))


async def game_loop(
    surface: pygame.Surface, clock: pygame.time.Clock, scene_manager: StateMachine
) -> None:
    mouse_buffer: t.InputBuffer = [t.InputState.NOTHING for _ in t.MouseButton]

    action_buffer: t.InputBuffer = [t.InputState.NOTHING for _ in t.Action]

    last_action_mapping_pressed = [t.action_mappings[action][0] for action in t.Action]

    print("Starting game loop")

    while True:
        elapsed_time = clock.tick(c.FPS)
        dt = elapsed_time / 1000.0  # Convert to seconds
        dt = min(dt, c.MAX_DT)  # Clamp delta time
        dt *= g.time_dilation

        update_action_buffer(action_buffer, last_action_mapping_pressed)

        running = input_event_queue(action_buffer)

        if not running:
            surface.fill(c.BLACK)
            terminate()

        update_mouse_buffer(mouse_buffer)

        statemachine_execute(scene_manager, surface, dt, action_buffer, mouse_buffer)

        # debug_str = f"FPS {clock.get_fps():.0f}\nDT {dt:.3f}"
        # surface.blit(
        #     a.DEBUG_FONT.render(debug_str, False, c.WHITE, c.BLACK),
        #     (0, 0),
        # )

        # Keep these calls together in this order
        pygame.display.flip()
        await asyncio.sleep(0)  # Very important, and keep it 0


def input_event_queue(action_buffer: t.InputBuffer) -> bool:
    """
    Pumps the event queue and handles application events
    Returns False if application should terminate, else True
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.MOUSEWHEEL and not c.IS_WEB:
            if event.y < 0:
                action_buffer[t.Action.RIGHT] = t.InputState.PRESSED
            elif event.y > 0:
                action_buffer[t.Action.LEFT] = t.InputState.PRESSED

        elif event.type == pygame.WINDOWFOCUSGAINED:
            pygame.mixer.music.unpause()

        # if (c.IS_WEB and not pygame.mouse.get_focused()) or event.type == pygame.WINDOWFOCUSLOST:
        #     for channel in AudioChannel:
        #         pygame.mixer.Channel(channel).pause()
        # if event.type == pygame.VIDEORESIZE:
        #     pass

        # HACK: For quick development
        # NOTE: It overrides exiting fullscreen when in browser
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if not c.IS_WEB:
                return False

    return True


def update_action_buffer(
    action_buffer: t.InputBuffer, last_action_mapping_pressed: list[int]
) -> None:
    # get_just_pressed() and get_just_released() do not work with web ;(
    keys_held = pygame.key.get_pressed()
    for action in t.Action:
        if action_buffer[action] == t.InputState.NOTHING:
            # Check if any alternate keys for the action were just pressed
            for mapping in t.action_mappings[action]:
                if mapping == last_action_mapping_pressed[action]:
                    continue

                # If an alternate key was pressed than last recorded key
                if keys_held[mapping]:
                    # Set that key bind as the current bind to 'track'
                    last_action_mapping_pressed[action] = mapping

        if keys_held[last_action_mapping_pressed[action]]:
            if (
                action_buffer[action] == t.InputState.NOTHING
                or action_buffer[action] == t.InputState.RELEASED
            ):
                action_buffer[action] = t.InputState.PRESSED
            elif action_buffer[action] == t.InputState.PRESSED:
                action_buffer[action] = t.InputState.HELD
        else:
            if (
                action_buffer[action] == t.InputState.PRESSED
                or action_buffer[action] == t.InputState.HELD
            ):
                action_buffer[action] = t.InputState.RELEASED
            elif action_buffer[action] == t.InputState.RELEASED:
                action_buffer[action] = t.InputState.NOTHING


def update_mouse_buffer(mouse_buffer: t.InputBuffer) -> None:
    # get_just_pressed() and get_just_released() do not work with web ;(
    mouse_pressed = pygame.mouse.get_pressed()
    for button in t.MouseButton:
        if mouse_pressed[button]:
            if (
                mouse_buffer[button] == t.InputState.NOTHING
                or mouse_buffer[button] == t.InputState.RELEASED
            ):
                mouse_buffer[button] = t.InputState.PRESSED
            elif mouse_buffer[button] == t.InputState.PRESSED:
                mouse_buffer[button] = t.InputState.HELD
        else:
            if (
                mouse_buffer[button] == t.InputState.PRESSED
                or mouse_buffer[button] == t.InputState.HELD
            ):
                mouse_buffer[button] = t.InputState.RELEASED
            elif mouse_buffer[button] == t.InputState.RELEASED:
                mouse_buffer[button] = t.InputState.NOTHING


def terminate() -> None:
    print("Terminated application")
    setup.write_settings()
    pygame.quit()
    raise SystemExit
