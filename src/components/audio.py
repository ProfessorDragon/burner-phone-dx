from enum import IntEnum, auto
import pygame


class AudioChannel(IntEnum):
    MUSIC = 0
    UI = auto()
    PLAYER = auto()
    PLAYER_ALT = auto()
    ENTITY = auto()


def play_sound(channel: AudioChannel, sound: pygame.Sound, *args) -> None:
    pygame.mixer.Channel(channel).play(sound, *args)


def channel_busy(channel: AudioChannel) -> bool:
    return pygame.mixer.Channel(channel).get_busy()


def stop_all_sounds() -> None:
    for channel in AudioChannel:
        pygame.mixer.Channel(channel).stop()


def set_music_volume(value: float) -> None:
    pygame.mixer.Channel(AudioChannel.MUSIC).set_volume(value)


def set_sfx_volume(value: float) -> None:
    for channel in AudioChannel:
        if channel != AudioChannel.MUSIC:
            pygame.mixer.Channel(channel).set_volume(value)
