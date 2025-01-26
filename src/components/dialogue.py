from dataclasses import dataclass
from enum import Enum
from collections import deque
import random
from typing import Callable
from functools import partial
import textwrap
import pygame

from components.audio import AudioChannel, play_sound
from components.camera import Camera
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


class DialogueStyle(Enum):
    DEFAULT = "default"
    PHONE = "phone"
    SIGN = "sign"
    NOTE = "note"
    COMMS = "comms"


@dataclass
class DialogueButton:
    text: str
    callback: Callable
    selected: bool = False


# shows a message with the typewriter effect
@dataclass
class DialogueMessagePacket:
    style: DialogueStyle = DialogueStyle.DEFAULT
    graphic: pygame.Surface = None
    name: str = ""
    sounds: list[pygame.mixer.Sound] = None
    message: str = ""
    buttons: list[DialogueButton] = None
    skippable = True


# delays for the specified duration and optionally plays a sound when it starts
@dataclass
class DialogueDelayPacket:
    duration: float
    sound: pygame.mixer.Sound = None


# pans the camera to the specified location
@dataclass
class DialogueCameraPanPacket:
    duration: float
    target: pygame.Vector2 = None  # leave none to use player pos


@dataclass
class DialogueSystem:
    queue: deque = None
    char_index: int = 0
    font: pygame.Font = None
    rect: pygame.Rect = None
    text: str = None
    script_scenes: dict[str, list[str]] = None
    executed_scenes: set[str] = None
    show_timer: Timer = None  # delay before dialogue is shown or updated
    complete_timer: Timer = None  # delay before dialogue can be dismissed
    character_timer: Timer = None  # delay between characters in a message
    delay_timer: Timer = None  # used by delay and camera pan packets
    # camera's position at the start of the current camera pan
    pan_start: pygame.Vector2 = None
    desired_music_index: int = None  # used to change music inside a scene


def dialogue_wrap_message(message: str) -> str:
    return "\n".join([textwrap.fill(ln, DIALOGUE_LINE_LENGTH) for ln in message.split("\n")])


def dialogue_initialise(dialogue: DialogueSystem) -> None:
    dialogue.queue = deque()
    dialogue.char_index = 0
    dialogue.font = a.DEBUG_FONT
    dialogue.rect = pygame.Rect(
        20, c.WINDOW_HEIGHT - 100, c.WINDOW_WIDTH - 40, 80)
    dialogue.text = ""
    dialogue.show_timer = Timer()
    dialogue.character_timer = Timer()
    dialogue.complete_timer = Timer()
    dialogue.delay_timer = Timer()
    dialogue.script_scenes = {}
    dialogue.executed_scenes = set()


def dialogue_add_packet(dialogue: DialogueSystem, packet) -> None:
    dialogue.queue.append(packet)


def dialogue_pop_packet(dialogue: DialogueSystem) -> None:
    dialogue.queue.popleft()


def dialogue_load_script(dialogue: DialogueSystem, script: str) -> None:
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


def dialogue_has_executed_scene(dialogue: DialogueSystem, scene_name: str) -> bool:
    return scene_name.lower() in dialogue.executed_scenes


def dialogue_remove_executed_scene(dialogue: DialogueSystem, scene_name: str) -> bool:
    if dialogue_has_executed_scene(dialogue, scene_name):
        dialogue.executed_scenes.remove(scene_name.lower())
        return True
    return False


# executes a section from the currently loaded script.
def dialogue_execute_script_scene(dialogue: DialogueSystem, scene_name: str) -> None:
    if not scene_name:
        return
    scene_name = scene_name.lower()
    if scene_name not in dialogue.script_scenes:
        print(f"ERROR: Scene {scene_name} does not exist in dialogue scenes")
        return

    print(f"Executing script scene {scene_name.upper()}")
    dialogue_reset_queue(dialogue)
    dialogue.executed_scenes.add(scene_name)

    dialogue_packet = DialogueMessagePacket()
    dialogue_packet.graphic = a.DEBUG_SPRITE_64
    last_character_id = "default"

    for ln in dialogue.script_scenes[scene_name]:
        if not ln.strip():
            continue

        if " " in ln:
            cmd, content = ln.split(" ", 1)
        else:
            cmd, content = ln, ""

        if not cmd.replace("#", ""):
            continue

        match cmd:
            case "-":
                dialogue_packet.message = dialogue_wrap_message(
                    content.replace("\\n", "\n"))
                dialogue_add_packet(dialogue, dialogue_packet)
                new_packet = DialogueMessagePacket()
                new_packet.style = dialogue_packet.style
                new_packet.graphic = dialogue_packet.graphic
                new_packet.name = dialogue_packet.name
                new_packet.sounds = dialogue_packet.sounds
                dialogue_packet = new_packet

            case "style":
                args = content.split(" ")
                dialogue_packet.style = DialogueStyle(args[0])
                if len(args) <= 1 or args[1] != "silent":
                    # play the opening sound for phone or comms, and delay until sound is finished
                    if dialogue_packet.style == DialogueStyle.PHONE:
                        delay = DialogueDelayPacket(0.6)
                        delay.sound = a.OPEN_PHONE
                        dialogue_add_packet(dialogue, delay)
                    elif dialogue_packet.style == DialogueStyle.COMMS:
                        delay = DialogueDelayPacket(0.6)
                        delay.sound = a.OPEN_COMMS
                        dialogue_add_packet(dialogue, delay)

            case "char":
                args = content.split(" ", 1)
                if len(args) > 1 and args[1] in a.DIALOGUE_CHARACTERS:
                    character = a.DIALOGUE_CHARACTERS.get(
                        args[1], a.DIALOGUE_CHARACTERS["default"])
                    last_character_id = args[1]
                else:
                    character = a.DIALOGUE_CHARACTERS.get(
                        last_character_id, a.DIALOGUE_CHARACTERS["default"]
                    )
                if int(args[0]) < len(character.sprites):
                    dialogue_packet.graphic = character.sprites[int(args[0])]
                dialogue_packet.name = character.name
                dialogue_packet.sounds = character.sounds

            case "noskip":
                dialogue_packet.skippable = False

            case "goto":
                dialogue_packet.buttons = [
                    DialogueButton(
                        "", partial(dialogue_execute_script_scene,
                                    dialogue, content), True
                    )
                ]

            case "buttons":
                dialogue_packet.buttons = []
                for opt in content.split("|"):
                    text, target_scene = opt.rsplit("=")
                    dialogue_packet.buttons.append(
                        DialogueButton(
                            text, partial(
                                dialogue_execute_script_scene, dialogue, target_scene)
                        )
                    )
                dialogue_packet.buttons[-1].selected = True

            case "delay":
                duration = float(content)
                dialogue_add_packet(dialogue, DialogueDelayPacket(duration))

            case "pan":
                args = [float(arg) for arg in content.split(" ")]
                pan = DialogueCameraPanPacket(0)
                if len(args) > 0:
                    pan.duration = args[0]
                if len(args) > 2:
                    pan.target = pygame.Vector2(
                        args[1] * c.TILE_SIZE, args[2] * c.TILE_SIZE)
                dialogue_add_packet(dialogue, pan)

            case "music":
                dialogue.desired_music_index = int(content)

            case "require":
                if not dialogue_has_executed_scene(dialogue, content):
                    return

            case _:
                print(
                    f"ERROR: Invalid script line in scene {scene_name}:\n{ln}")
                continue


def _dialogue_update_message(
    dialogue: DialogueSystem,
    packet: DialogueMessagePacket,
    dt: float,
    action_buffer: t.InputBuffer,
    mouse_bufffer: t.InputBuffer,
) -> None:
    is_complete = dialogue.char_index >= len(packet.message)

    # confirm
    if t.is_pressed(action_buffer, t.Action.A):
        if not is_complete:
            if packet.skippable:
                # Skip writing
                dialogue.char_index = len(packet.message)
                dialogue.text = packet.message
                timer_reset(dialogue.complete_timer, COMPLETED_DELAY)

        elif dialogue.complete_timer.remaining <= 0:
            # play_sound(AudioChannel.UI, a.UI_SELECT) # sounds bad
            # Activate selected button
            if packet.buttons is not None:
                selected_index = [i for i, btn in enumerate(
                    packet.buttons) if btn.selected]
                if len(selected_index) > 0:
                    dialogue_pop_packet(dialogue)
                    packet.buttons[selected_index[0]].callback()
                    return
            # Go to next packet
            else:
                dialogue_pop_packet(dialogue)
                dialogue_try_reset(dialogue)

        return

    if packet.buttons is not None and len(packet.buttons) > 1:
        dx = t.is_pressed(action_buffer, t.Action.RIGHT) - t.is_pressed(
            action_buffer, t.Action.LEFT
        )
        if dx != 0:
            play_sound(AudioChannel.UI, a.UI_HOVER)
            selected_index = [i for i, btn in enumerate(
                packet.buttons) if btn.selected]
            if len(selected_index) > 0:
                packet.buttons[selected_index[0]].selected = False
                packet.buttons[(selected_index[0] + dx) %
                               len(packet.buttons)].selected = True
            else:
                packet.buttons[0].selected = True
            return

    if is_complete:
        if timer_update(dialogue.complete_timer, dt):
            play_sound(AudioChannel.UI, a.UI_HOVER)
        return

    timer_update(dialogue.character_timer, dt)

    # render next letter
    if dialogue.character_timer.remaining <= 0:
        new_char = packet.message[dialogue.char_index]
        dialogue.char_index += 1
        dialogue.text = packet.message[: dialogue.char_index]

        # now is complete
        if dialogue.char_index >= len(packet.message):
            timer_reset(dialogue.complete_timer, COMPLETED_DELAY)
        # Wait for time before next letter
        else:
            if new_char == " ":
                timer_reset(dialogue.character_timer, SPACE_SPEED)
            else:
                if packet.sounds and dialogue.char_index % 4 == 0:
                    play_sound(AudioChannel.UI, random.choice(packet.sounds))
                if new_char in "?!.":
                    timer_reset(dialogue.character_timer, END_SENTENCE_SPEED)
                else:
                    timer_reset(dialogue.character_timer, LETTER_SPEED)


def _dialogue_update_delay(
    dialogue: DialogueSystem,
    packet: DialogueDelayPacket,
    dt: float,
) -> None:
    # start timer
    if dialogue.delay_timer.remaining <= 0:
        if packet.sound:
            play_sound(AudioChannel.UI, packet.sound)
        timer_reset(dialogue.delay_timer, packet.duration)

    if timer_update(dialogue.delay_timer, dt):
        dialogue_pop_packet(dialogue)


def _dialogue_update_camera_pan(
    dialogue: DialogueSystem,
    packet: DialogueCameraPanPacket,
    dt: float,
    camera: Camera,
    camera_target: pygame.Vector2,
) -> None:
    # start timer
    if dialogue.delay_timer.remaining <= 0:
        dialogue.pan_start = camera.motion.position.copy()
        timer_reset(dialogue.delay_timer, packet.duration)

    if packet.target is not None:
        camera_target = packet.target

    timer_update(dialogue.delay_timer, dt)

    if dialogue.delay_timer.remaining <= 0:
        camera.motion.position = camera_target
        dialogue_pop_packet(dialogue)
    else:
        percent = dialogue.delay_timer.elapsed / dialogue.delay_timer.duration
        camera.motion.position = dialogue.pan_start + \
            (camera_target - dialogue.pan_start) * percent


# returns true if there is dialogue playing currently
def dialogue_update(
    dialogue: DialogueSystem,
    dt: float,
    action_buffer: t.InputBuffer,
    mouse_bufffer: t.InputBuffer,
    camera: Camera,
    camera_target: pygame.Vector2,
) -> bool:
    if not dialogue.queue:
        return False

    timer_update(dialogue.show_timer, dt)
    if dialogue.show_timer.remaining > 0:
        return True

    active_packet = dialogue.queue[0]

    if isinstance(active_packet, DialogueMessagePacket):
        _dialogue_update_message(
            dialogue, active_packet, dt, action_buffer, mouse_bufffer)
    elif isinstance(active_packet, DialogueDelayPacket):
        _dialogue_update_delay(dialogue, active_packet, dt)
    elif isinstance(active_packet, DialogueCameraPanPacket):
        _dialogue_update_camera_pan(
            dialogue, active_packet, dt, camera, camera_target)
    # can add more types if necessary

    return True


def _dialogue_render_message(
    dialogue: DialogueSystem, packet: DialogueMessagePacket, surface: pygame.Surface
) -> None:
    # styling
    inner_rect = dialogue.rect.copy()
    inner_rect.x += 1
    inner_rect.w -= 2
    inner_rect.y += 1
    inner_rect.h -= 2
    fg_color = c.WHITE
    match packet.style:
        case DialogueStyle.DEFAULT:
            pygame.draw.rect(surface, (70, 60, 70), dialogue.rect, 0, 8)
            pygame.draw.rect(surface, (150, 140, 150), dialogue.rect, 2, 8)
        case DialogueStyle.PHONE:
            pygame.draw.rect(surface, (70, 60, 70), dialogue.rect, 0, 8)
            pygame.draw.rect(surface, (150, 140, 150), dialogue.rect, 2, 8)
        case DialogueStyle.SIGN:
            pygame.draw.rect(surface, (68, 13, 113), dialogue.rect, 0, 8)
            pygame.draw.rect(surface, (195, 178, 253), dialogue.rect, 2, 8)
        case DialogueStyle.COMMS:
            pygame.draw.rect(surface, (0, 128, 0), dialogue.rect, 0, 8)
            pygame.draw.rect(surface, (0, 255, 0), dialogue.rect, 2, 8)

    graphic = packet.graphic
    surface.blit(graphic, (dialogue.rect.x + 3,
                 dialogue.rect.y + 3), (0, 0, 64, 64))
    name = a.DEBUG_FONT.render(packet.name, False, fg_color)
    surface.blit(
        name,
        (
            dialogue.rect.left + 3 + 32 - name.get_width() / 2,
            dialogue.rect.bottom - name.get_height() - 2,
        ),
    )

    surface.blit(
        dialogue.font.render(dialogue.text, False, fg_color),
        (dialogue.rect.x + 80, dialogue.rect.y + 10),
    )
    if dialogue.char_index >= len(packet.message) and dialogue.complete_timer.remaining <= 0:
        x = dialogue.rect.right - 10
        y = dialogue.rect.bottom - 2
        if packet.buttons is not None and len(packet.buttons) > 1:
            for button in packet.buttons[::-1]:
                button_icon = dialogue.font.render(
                    button.text, False, c.WHITE if button.selected else (
                        200, 200, 200)
                )
                x -= button_icon.get_width()
                surface.blit(button_icon, (x, y - button_icon.get_height()))
                if button.selected:
                    pygame.draw.polygon(
                        surface,
                        fg_color,
                        [
                            (x - 4, y - button_icon.get_height() // 2),
                            (x - 7, y - button_icon.get_height() + 3),
                            (x - 7, y - 3),
                        ],
                    )
                x -= 20
        else:
            continue_icon = a.DEBUG_FONT.render(
                "<A> to continue", False, fg_color)
            surface.blit(
                continue_icon,
                (x - continue_icon.get_width(), y - continue_icon.get_height()),
            )


def dialogue_render(dialogue: DialogueSystem, surface: pygame.Surface) -> None:
    if not dialogue.queue:
        return
    if dialogue.show_timer.remaining > 0:
        return

    active_packet = dialogue.queue[0]

    if isinstance(active_packet, DialogueMessagePacket):
        _dialogue_render_message(dialogue, active_packet, surface)


def dialogue_reset_packet(dialogue: DialogueSystem) -> None:
    dialogue.char_index = 0
    dialogue.text = ""
    timer_reset(dialogue.delay_timer, 0)


def dialogue_reset_queue(dialogue: DialogueSystem) -> None:
    dialogue_reset_packet(dialogue)
    dialogue.queue.clear()


def dialogue_try_reset(dialogue: DialogueSystem) -> None:
    if dialogue.queue:
        dialogue_reset_packet(dialogue)
