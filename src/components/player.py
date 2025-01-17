from dataclasses import dataclass

import core.input as input
from components.motion import Motion, motion_update


@dataclass(slots=True)
class Player:
    motion: Motion


def player_update(player: Player, dt: float, action_buffer: input.InputBuffer):
    dx = input.is_held(action_buffer, input.Action.RIGHT) - input.is_held(action_buffer, input.Action.LEFT)
    dy = input.is_held(action_buffer, input.Action.DOWN) - input.is_held(action_buffer, input.Action.UP)
    if dx != 0 and dy != 0:
        # trig shortcut, multiply by 1/sqrt(2) for accurate diagonal movement speeds
        dx *= 0.707
        dy *= 0.707
    player.motion.velocity.x = dx * 200
    player.motion.velocity.y = dy * 200
    motion_update(player.motion, dt)
