from enum import IntEnum, auto
import pygame


class AudioChannel(IntEnum):
    MUSIC = 0
    PLAYER = auto()
    UI = auto()
    SFX = auto()


def play_sound(channel: AudioChannel, sound: pygame.Sound, *args) -> None:
    pygame.mixer.Channel(channel).play(sound, *args)


def stop_all_sounds() -> None:
    for channel in AudioChannel:
        pygame.mixer.Channel(channel).stop()
