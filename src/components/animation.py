from collections.abc import Hashable
from dataclasses import dataclass

import pygame


@dataclass(slots=True)
class Animation:
    frames: list[pygame.Surface]
    frame_duration: float


@dataclass(slots=True)
class Animator:
    animations: dict[Hashable, Animation] = None
    state_id: Hashable = None
    frame_index: int = 0
    elapsed_time: float = 0.0


def animator_initialise(
    animator: Animator,
    animation_mapping: dict[Hashable, Animation],
    initial_id: Hashable
) -> None:
    animator.animations = animation_mapping
    animator.state_id = initial_id


def animator_get_frame(animator: Animator) -> pygame.Surface:
    return animator.animations[animator.state_id].frames[animator.frame_index]


def animator_reset(animator: Animator) -> None:
    animator.frame_index = 0
    animator.elapsed_time = 0.0


def animator_switch_animation(animator: Animator, id: Hashable) -> None:
    # Cannot switch to current animation
    if id == animator.state_id:
        return

    if id not in animator.animations:
        print(f"ERROR: id: {id} does not exist in animator")
        return

    animator.state_id = id
    animator_reset(animator)


def animator_update(animator: Animator, dt: float) -> None:
    animator.elapsed_time += dt
    current_animation = animator.animations[animator.state_id]

    if animator.elapsed_time > current_animation.frame_duration:
        animator.frame_index += 1
        animator.frame_index %= len(current_animation.frames)
        animator.elapsed_time = 0.0
