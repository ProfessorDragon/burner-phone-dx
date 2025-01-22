from dataclasses import dataclass
from typing import Callable


@dataclass
class Timer:
    duration: float = 0
    remaining: float = 0
    elapsed: float = 0
    callback: Callable = None


# returns true if time remaining just reached zero (this is very useful)
def timer_update(timer: Timer, dt: float) -> bool:
    prev_remaining = timer.remaining
    timer.elapsed += dt
    timer.elapsed = min(timer.elapsed, timer.duration)
    timer.remaining = timer.duration - timer.elapsed
    if prev_remaining > 0 and timer.remaining <= 0:
        # execute binding
        if callable(timer.callback):
            timer.callback()
        return True
    return False


def timer_reset(timer: Timer, duration: float, callback: Callable = None) -> None:
    timer.duration = duration
    timer.elapsed = 0
    timer.remaining = duration
    timer.callback = callback


@dataclass
class Stopwatch:
    elapsed: float = 0
    bindings: dict[int, Callable] = None


def stopwatch_update(stopwatch: Stopwatch, dt: float) -> None:
    prev_elapsed = stopwatch.elapsed
    stopwatch.elapsed += dt
    if stopwatch.bindings:
        for time, callback in stopwatch.bindings.items():
            if prev_elapsed < time and stopwatch.elapsed > time and callable(callback):
                callback()


def stopwatch_reset(stopwatch: Stopwatch, bindings: dict[int, Callable] = None) -> None:
    stopwatch.elapsed = 0
    stopwatch.bindings = bindings
