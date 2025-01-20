from dataclasses import dataclass
from enum import Enum
from queue import deque
import textwrap
import pygame

import core.assets as a
import core.constants as c
import core.input as t
from components.timer import Timer, timer_reset, timer_update


# These constants should go elsewhere
LETTER_SPEED = 0.02
SPACE_SPEED = 0.04
END_SENTENCE_SPEED = 0.1
DIALOGUE_LINE_LENGTH = 44

# Continue icon
CONTINUE = a.DEBUG_FONT.render("<SELECT> to continue", False, c.WHITE)


class DialogueStyle(Enum):
    DEFAULT = "default"
    PHONE = "phone"
    COMMS = "comms"


@dataclass
class DialoguePacket:
    style: DialogueStyle = DialogueStyle.DEFAULT
    graphic: pygame.Surface = None
    name: str = ""
    message: str = ""


@dataclass
class DialogueSystem:
    queue: list[DialoguePacket] = None
    char_index: int = 0
    font: pygame.Font = None
    rect: pygame.Rect = None
    text: pygame.Surface = None
    timer: Timer = None
    script_scenes: dict[str, list[str]] = None


def dialogue_wrap_message(message: str) -> str:
    return "\n".join([textwrap.fill(ln, DIALOGUE_LINE_LENGTH) for ln in message.split("\n")])


def dialogue_packet_create(graphic: pygame.Surface, name: str, message: str) -> DialoguePacket:
    packet = DialoguePacket()
    packet.graphic = graphic
    packet.name = name
    packet.message = dialogue_wrap_message(message)
    return packet


def dialogue_initialise(dialogue: DialogueSystem) -> None:
    dialogue.queue = deque()
    dialogue.char_index = 0
    dialogue.font = a.DEBUG_FONT
    dialogue.rect = pygame.Rect(20, c.WINDOW_HEIGHT - 100, c.WINDOW_WIDTH - 40, 80)
    dialogue.text = a.DEBUG_FONT.render("", False, c.WHITE)
    dialogue.timer = Timer()


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
            scene_name = ln[1:-1]
            scene_content = []
        elif ln.strip():
            scene_content.append(ln)
    if scene_name is not None:
        dialogue.script_scenes[scene_name] = scene_content


def dialogue_execute_script_scene(dialogue: DialogueSystem, scene_name: str) -> None:
    if scene_name not in dialogue.script_scenes:
        print(f"ERROR: Scene {scene_name} does not exist in dialogue scenes")
        return

    dialogue_force_reset(dialogue)

    dialogue_packet = DialoguePacket()
    dialogue_packet.graphic = a.DEBUG_SPRITE_SMALL

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
                dialogue_packet.name = content

            case "buttons":
                options = content.split("|")
                # todo

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

    if action_buffer and t.is_pressed(action_buffer, t.Action.SELECT):
        # Go to next packet
        if dialogue.char_index >= len(active_packet.message):
            dialogue.queue.popleft()
            dialogue_try_reset(dialogue)
        # Skip writing
        else:
            dialogue.char_index = len(active_packet.message)
            dialogue.text = dialogue.font.render(active_packet.message, False, c.WHITE)

    elif dialogue.char_index < len(active_packet.message):
        timer_update(dialogue.timer, dt)

        # Then render next letter
        if dialogue.timer.remaining <= 0:
            new_char = active_packet.message[dialogue.char_index]
            dialogue.char_index += 1
            new_string = active_packet.message[: dialogue.char_index]
            dialogue.text = dialogue.font.render(new_string, False, c.WHITE)

            # Wait for time before next letter
            if new_char == " ":
                dialogue.timer.duration = SPACE_SPEED
            elif new_char in "?!.":
                dialogue.timer.duration = END_SENTENCE_SPEED
            else:
                dialogue.timer.duration = LETTER_SPEED
            timer_reset(dialogue.timer)

    return True


def dialogue_render(dialogue: DialogueSystem, surface: pygame.Surface) -> bool:
    if not dialogue.queue:
        return

    active_packet = dialogue.queue[0]

    match active_packet.style:
        case DialogueStyle.DEFAULT:
            pygame.draw.rect(surface, c.BLACK, dialogue.rect)
        case DialogueStyle.PHONE:
            pygame.draw.rect(surface, c.GRAY, dialogue.rect)
        case DialogueStyle.COMMS:
            pygame.draw.rect(surface, c.GREEN, dialogue.rect)

    surface.blit(active_packet.graphic, (dialogue.rect.x, dialogue.rect.y), (0, 0, 64, 64))
    surface.blit(
        a.DEBUG_FONT.render(active_packet.name, False, c.WHITE),
        (dialogue.rect.x, dialogue.rect.y + dialogue.rect.h - 15),
    )
    surface.blit(dialogue.text, (dialogue.rect.x + 80, dialogue.rect.y + 10))
    if dialogue.char_index >= len(active_packet.message):
        surface.blit(CONTINUE, (dialogue.rect.x + 280, dialogue.rect.y + 60))


def dialogue_force_reset(dialogue: DialogueSystem) -> None:
    dialogue.char_index = 0
    dialogue.text = a.DEBUG_FONT.render("", False, c.WHITE)


def dialogue_try_reset(dialogue: DialogueSystem) -> None:
    if dialogue.queue:
        dialogue_force_reset(dialogue)
