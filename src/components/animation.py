from collections.abc import Hashable
from dataclasses import dataclass

import pygame

from components.motion import Direction


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
    initial_id: Hashable | None = None,
) -> None:
    animator.animations = animation_mapping
    animator.state_id = initial_id if initial_id is not None else list(animation_mapping.keys())[0]


def directional_animation_mapping(
    directional_mapping: dict[str, list[Animation]]
) -> dict[Hashable, Animation]:
    animation_mapping = {}
    for name, anims in directional_mapping.items():
        if len(anims) not in (4, 8):
            print(f"ERROR: Cannot have directional animation mapping for {len(anims)} items")
            continue
        is_4 = len(anims) == 4
        directions = [
            Direction.N,
            Direction.NE,
            Direction.E,
            Direction.SE,
            Direction.S,
            Direction.SW,
            Direction.W,
            Direction.NW,
        ]
        for i, dir in enumerate(directions):
            if is_4:
                if dir in (Direction.NE, Direction.SE):
                    idx = 1
                elif dir in (Direction.SW, Direction.NW):
                    idx = 3
                else:
                    idx = i // 2
            else:
                idx = i
            animation_mapping[f"{name}_{dir}"] = anims[idx]
    return animation_mapping


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
        print(f"ERROR: Animation {id} does not exist in animator")
        return

    animator.state_id = id
    if id is not None:
        animator.frame_index %= len(animator.animations[id].frames)


def animator_update(animator: Animator, dt: float) -> None:
    animator.elapsed_time += dt
    if animator.state_id is not None:
        current_animation = animator.animations[animator.state_id]

    if animator.elapsed_time > current_animation.frame_duration:
        animator.frame_index += 1
        animator.frame_index %= len(current_animation.frames)
        animator.elapsed_time = 0.0
