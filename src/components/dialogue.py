from dataclasses import dataclass
from queue import deque
import pygame

import core.assets as a
import core.constants as c
import core.input as i
from components.timer import Timer, timer_reset, timer_update


# These constants should go elsewhere
LETTER_SPEED = 0.04
SPACE_SPEED = 0.08
END_SENTENCE_SPEED = 0.2

# Continue icon
CONTINUE = a.DEBUG_FONT.render("<SELECT> to continue", False, c.WHITE)


@dataclass
class DialoguePacket:
    graphic: pygame.Surface = None
    name: pygame.Surface = None
    message: str = ''


@dataclass
class DialogueSystem:
    queue: list[DialoguePacket] = None
    char_index: int = 0
    font: pygame.Font = None
    rect: pygame.Rect = None
    text: pygame.Surface = None
    timer: Timer = None


def dialogue_packet_create(
    graphic: pygame.Surface, name: str, message: str
) -> DialoguePacket:
    packet = DialoguePacket()
    packet.graphic = graphic
    packet.name = a.DEBUG_FONT.render(name, False, c.WHITE)
    packet.message = message
    return packet


def dialogue_initialise(dialogue: DialogueSystem) -> None:
    dialogue.queue = deque()
    dialogue.char_index = 0
    dialogue.font = a.DEBUG_FONT
    dialogue.rect = pygame.Rect(
        20, c.WINDOW_HEIGHT - 100, c.WINDOW_WIDTH - 40, 80
    )
    dialogue.text = a.DEBUG_FONT.render("", False, c.WHITE)
    dialogue.timer = Timer()


def dialogue_add_packet(
    dialogue: DialogueSystem, packet: DialoguePacket
) -> None:
    dialogue.queue.append(packet)


def dialogue_update(
    dialogue: DialogueSystem, dt: float,
    action_buffer: i.InputBuffer, mouse_bufffer: i.InputBuffer
) -> bool:
    '''
    Return true if there is dialogue playing currently
    '''
    if not dialogue.queue:
        return False

    active_packet = dialogue.queue[0]

    if i.is_pressed(action_buffer, i.Action.SELECT):
        # Go to next packet
        if dialogue.char_index >= len(active_packet.message):
            dialogue.queue.popleft()
            dialogue_try_reset(dialogue)
        # Skip writing
        else:
            dialogue.char_index = len(active_packet.message)
            dialogue.text = dialogue.font.render(
                active_packet.message, False, c.WHITE
            )

    elif dialogue.char_index < len(active_packet.message):
        timer_update(dialogue.timer, dt)

        # Then render next letter
        if dialogue.timer.remaining <= 0:
            new_char = active_packet.message[dialogue.char_index]
            dialogue.char_index += 1
            new_string = active_packet.message[:dialogue.char_index]
            dialogue.text = dialogue.font.render(new_string, False, c.WHITE)

            # Wait for time before next letter
            if new_char == ' ':
                dialogue.timer.duration = SPACE_SPEED
            elif new_char in '?!.':
                dialogue.timer.duration = END_SENTENCE_SPEED
            else:
                dialogue.timer.duration = LETTER_SPEED
            timer_reset(dialogue.timer)

    return True


def dialogue_render(dialogue: DialogueSystem, surface: pygame.Surface) -> bool:
    if not dialogue.queue:
        return

    active_packet = dialogue.queue[0]

    pygame.draw.rect(surface, c.BLACK, dialogue.rect)
    surface.blit(active_packet.graphic, (dialogue.rect.x, dialogue.rect.y))
    surface.blit(
        active_packet.name,
        (dialogue.rect.x, dialogue.rect.y + dialogue.rect.h - 20)
    )
    surface.blit(dialogue.text, (dialogue.rect.x + 80, dialogue.rect.y))
    if dialogue.char_index >= len(active_packet.message):
        surface.blit(
            CONTINUE,
            (dialogue.rect.x + 280, dialogue.rect.y + 60)
        )


def dialogue_try_reset(dialogue: DialogueSystem) -> None:
    if dialogue.queue:
        dialogue.char_index = 0
        dialogue.text = a.DEBUG_FONT.render("", False, c.WHITE)
