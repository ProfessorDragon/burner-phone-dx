import pygame
from enum import IntEnum, auto


class InputState(IntEnum):
    NOTHING = 0  # released for >1 frame
    PRESSED = auto()  # just pressed, active for 1 frame
    HELD = auto()  # pressed for >1 frame
    RELEASED = auto()  # just released, active for 1 frame


class MouseButton(IntEnum):
    LEFT = 0
    MIDDLE = 1
    RIGHT = 2


class Action(IntEnum):
    LEFT = 0
    RIGHT = auto()
    UP = auto()
    DOWN = auto()
    A = auto()
    B = auto()
    SELECT = auto()
    START = auto()


InputBuffer = list[InputState]


def is_pressed(action_buffer: InputBuffer, input_enum: IntEnum) -> bool:
    return action_buffer[input_enum] == InputState.PRESSED


def is_held(action_buffer: InputBuffer, input_enum: IntEnum) -> bool:
    return action_buffer[input_enum] == InputState.HELD


def is_released(action_buffer: InputBuffer, input_enum: IntEnum) -> bool:
    return action_buffer[input_enum] == InputState.RELEASED


def is_nothing(action_buffer: InputBuffer, input_enum: IntEnum) -> bool:
    return action_buffer[input_enum] == InputState.NOTHING


action_mappings = {
    Action.LEFT: [pygame.K_a, pygame.K_LEFT],
    Action.RIGHT: [pygame.K_d, pygame.K_RIGHT],
    Action.UP: [pygame.K_w, pygame.K_UP],
    Action.DOWN: [pygame.K_s, pygame.K_DOWN],
    Action.A: [pygame.K_z, pygame.K_SLASH],
    Action.B: [pygame.K_x, pygame.K_PERIOD],
    Action.SELECT: [pygame.K_LSHIFT, pygame.K_RSHIFT],
    Action.START: [pygame.K_RETURN, pygame.K_SPACE],
}
