from dataclasses import dataclass


@dataclass
class Timer:
    duration: float
    remaining: float = 0
    elapsed: float = 0


def timer_update(timer: Timer, dt: float) -> None:
    timer.elapsed += dt
    timer.elapsed = min(timer.elapsed, timer.duration)
    timer.remaining = timer.duration - timer.elapsed


def timer_reset(timer: Timer) -> None:
    timer.elapsed = 0
    timer.remaining = timer.duration
