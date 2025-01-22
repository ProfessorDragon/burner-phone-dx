from dataclasses import dataclass
from enum import Enum
from queue import deque
from typing import Callable
from functools import partial
import textwrap
import pygame

import core.assets as a
import core.constants as c
import core.input as t
from components.timer import Timer, timer_reset, timer_update


# These constants should go elsewhere
LETTER_SPEED = 0.01
SPACE_SPEED = 0.02
END_SENTENCE_SPEED = 0.12
COMPLETED_DELAY = END_SENTENCE_SPEED
DIALOGUE_LINE_LENGTH = 44

# Continue icon
CONTINUE_ICON = a.DEBUG_FONT.render("<A> to continue", False, c.WHITE)


class DialogueStyle(Enum):
    DEFAULT = "default"
    PHONE = "phone"
    COMMS = "comms"


@dataclass
class DialogueButton:
    text: str
    callback: Callable
    selected: bool = False


@dataclass
class DialoguePacket:
    style: DialogueStyle = DialogueStyle.DEFAULT
    graphic: pygame.Surface = None
    name: str = ""
    message: str = ""
    buttons: list[DialogueButton] = None


@dataclass
class DialogueSystem:
    queue: list[DialoguePacket] = None
    char_index: int = 0
    font: pygame.Font = None
    rect: pygame.Rect = None
    text: pygame.Surface = None
    character_timer: Timer = None
    complete_timer: Timer = None
    script_scenes: dict[str, list[str]] = None


def dialogue_wrap_message(message: str) -> str:
    return "\n".join([textwrap.fill(ln, DIALOGUE_LINE_LENGTH) for ln in message.split("\n")])


def dialogue_initialise(dialogue: DialogueSystem) -> None:
    dialogue.queue = deque()
    dialogue.char_index = 0
    dialogue.font = a.DEBUG_FONT
    dialogue.rect = pygame.Rect(20, c.WINDOW_HEIGHT - 100, c.WINDOW_WIDTH - 40, 80)
    dialogue.text = a.DEBUG_FONT.render("", False, c.WHITE)
    dialogue.character_timer = Timer()
    dialogue.complete_timer = Timer()


def dialogue_add_packet(dialogue: DialogueSystem, packet: DialoguePacket) -> None:
    dialogue.queue.append(packet)


def dialogue_load_script(dialogue: DialogueSystem, script: str) -> None:
    if dialogue.script_scenes is None:
        dialogue.script_scenes = {}
    scene_name = None
    scene_content = []
    for ln in script.split("\n"):
        if ln.startswith("[") and ln.endswith("]"):
            if scene_name is not None:
                dialogue.script_scenes[scene_name] = scene_content
            scene_name = ln[1:-1].lower()
            scene_content = []
        elif ln.strip():
            scene_content.append(ln)
    if scene_name is not None:
        dialogue.script_scenes[scene_name] = scene_content


def dialogue_execute_script_scene(dialogue: DialogueSystem, scene_name: str) -> None:
    if not scene_name:
        return
    scene_name = scene_name.lower()
    if scene_name not in dialogue.script_scenes:
        print(f"ERROR: Scene {scene_name} does not exist in dialogue scenes")
        return

    dialogue_reset_queue(dialogue)

    dialogue_packet = DialoguePacket()
    dialogue_packet.graphic = a.DEBUG_SPRITE_64
    last_character_id = None

    for ln in dialogue.script_scenes[scene_name]:
        if not ln.strip():
            continue

        if " " in ln:
            cmd, content = ln.split(" ", 1)
        else:
            cmd, content = ln, ""

        match cmd:
            case "#":
                continue

            case "-":
                dialogue_packet.message = dialogue_wrap_message(content.replace("\\n", "\n"))
                dialogue_add_packet(dialogue, dialogue_packet)
                new_packet = DialoguePacket()
                new_packet.style = dialogue_packet.style
                new_packet.graphic = dialogue_packet.graphic
                new_packet.name = dialogue_packet.name
                dialogue_packet = new_packet

            case "style":
                dialogue_packet.style = DialogueStyle(content)

            case "char":
                args = content.split(" ", 1)
                if len(args) > 1:
                    character = a.DIALOGUE_CHARACTERS[args[1]]
                    last_character_id = args[1]
                else:
                    character = a.DIALOGUE_CHARACTERS[last_character_id]
                dialogue_packet.graphic = character.sprites[int(args[0])]
                dialogue_packet.name = character.name

            case "buttons":
                dialogue_packet.buttons = []
                for opt in content.split("|"):
                    text, target_scene = opt.rsplit("=")
                    dialogue_packet.buttons.append(
                        DialogueButton(
                            text, partial(dialogue_execute_script_scene, dialogue, target_scene)
                        )
                    )
                dialogue_packet.buttons[-1].selected = True

            case _:
                print(f"ERROR: Invalid script line in scene {scene_name}:\n{ln}")
                continue


def dialogue_update(
    dialogue: DialogueSystem,
    dt: float,
    action_buffer: t.InputBuffer = None,
    mouse_bufffer: t.InputBuffer = None,
) -> bool:
    """
    Return true if there is dialogue playing currently
    """
    if not dialogue.queue:
        return False

    active_packet = dialogue.queue[0]
    is_complete = dialogue.char_index >= len(active_packet.message)
    has_buttons = active_packet.buttons is not None

    if action_buffer:
        if t.is_pressed(action_buffer, t.Action.SELECT) or t.is_pressed(action_buffer, t.Action.A):
            if not is_complete:
                # Skip writing
                dialogue.char_index = len(active_packet.message)
                dialogue.text = dialogue.font.render(active_packet.message, False, c.WHITE)
                dialogue.complete_timer.duration = COMPLETED_DELAY
                timer_reset(dialogue.complete_timer)

            elif dialogue.complete_timer.remaining <= 0:
                # Activate selected button
                if has_buttons:
                    selected_index = [
                        i for i, btn in enumerate(active_packet.buttons) if btn.selected
                    ]
                    if len(selected_index) > 0:
                        dialogue.queue.popleft()
                        active_packet.buttons[selected_index[0]].callback()
                        return True
                # Go to next packet
                else:
                    dialogue.queue.popleft()
                    dialogue_try_reset(dialogue)

            return True

        if has_buttons:
            dx = t.is_pressed(action_buffer, t.Action.RIGHT) - t.is_pressed(
                action_buffer, t.Action.LEFT
            )
            if dx != 0:
                selected_index = [i for i, btn in enumerate(active_packet.buttons) if btn.selected]
                if len(selected_index) > 0:
                    active_packet.buttons[selected_index[0]].selected = False
                    active_packet.buttons[
                        (selected_index[0] + dx) % len(active_packet.buttons)
                    ].selected = True
                else:
                    active_packet.buttons[0].selected = True
                return True

    if is_complete:
        timer_update(dialogue.complete_timer, dt)

    else:
        timer_update(dialogue.character_timer, dt)

        # Then render next letter
        if dialogue.character_timer.remaining <= 0:
            new_char = active_packet.message[dialogue.char_index]
            dialogue.char_index += 1
            new_string = active_packet.message[: dialogue.char_index]
            dialogue.text = dialogue.font.render(new_string, False, c.WHITE)

            # now is complete
            if dialogue.char_index >= len(active_packet.message):
                dialogue.complete_timer.duration = COMPLETED_DELAY
                timer_reset(dialogue.complete_timer)
            else:
                # Wait for time before next letter
                if new_char == " ":
                    dialogue.character_timer.duration = SPACE_SPEED
                elif new_char in "?!.":
                    dialogue.character_timer.duration = END_SENTENCE_SPEED
                else:
                    dialogue.character_timer.duration = LETTER_SPEED
                timer_reset(dialogue.character_timer)

    return True


def dialogue_render(dialogue: DialogueSystem, surface: pygame.Surface) -> bool:
    if not dialogue.queue:
        return

    active_packet = dialogue.queue[0]

    # background
    inner_rect = dialogue.rect.copy()
    inner_rect.x += 1
    inner_rect.w -= 2
    inner_rect.y += 1
    inner_rect.h -= 2
    match active_packet.style:
        case DialogueStyle.DEFAULT:
            pygame.draw.rect(surface, c.BLACK, dialogue.rect)
            pygame.draw.rect(surface, c.GRAY, inner_rect, 1)
        case DialogueStyle.PHONE:
            pygame.draw.rect(surface, c.GRAY, dialogue.rect, 0, 8)
            pygame.draw.rect(surface, c.WHITE, dialogue.rect, 1, 8)
        case DialogueStyle.COMMS:
            pygame.draw.rect(surface, (0, 128, 0), dialogue.rect)
            pygame.draw.rect(surface, (0, 255, 0), inner_rect, 1)

    graphic = active_packet.graphic
    surface.blit(graphic, (dialogue.rect.x + 3, dialogue.rect.y + 3), (0, 0, 64, 64))
    name = a.DEBUG_FONT.render(active_packet.name, False, c.WHITE)
    surface.blit(
        name,
        (
            dialogue.rect.left + 3 + 32 - name.get_width() / 2,
            dialogue.rect.bottom - name.get_height() - 2,
        ),
    )

    surface.blit(dialogue.text, (dialogue.rect.x + 80, dialogue.rect.y + 10))
    if dialogue.char_index >= len(active_packet.message) and dialogue.complete_timer.remaining <= 0:
        x = dialogue.rect.right - 10
        y = dialogue.rect.bottom - 2
        if active_packet.buttons is not None:
            for button in active_packet.buttons[::-1]:
                button_icon = dialogue.font.render(
                    button.text, False, c.WHITE if button.selected else (200, 200, 200)
                )
                x -= button_icon.get_width()
                surface.blit(button_icon, (x, y - button_icon.get_height()))
                if button.selected:
                    pygame.draw.polygon(
                        surface,
                        c.WHITE,
                        [
                            (x - 4, y - button_icon.get_height() // 2),
                            (x - 7, y - button_icon.get_height() + 3),
                            (x - 7, y - 3),
                        ],
                    )
                x -= 20
        else:
            surface.blit(
                CONTINUE_ICON,
                (
                    x - CONTINUE_ICON.get_width(),
                    y - CONTINUE_ICON.get_height(),
                ),
            )


def dialogue_reset_packet(dialogue: DialogueSystem) -> None:
    dialogue.char_index = 0
    dialogue.text = a.DEBUG_FONT.render("", False, c.WHITE)


def dialogue_reset_queue(dialogue: DialogueSystem) -> None:
    dialogue_reset_packet(dialogue)
    dialogue.queue.clear()


def dialogue_try_reset(dialogue: DialogueSystem) -> None:
    if dialogue.queue:
        dialogue_reset_packet(dialogue)
