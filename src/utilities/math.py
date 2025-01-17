from components.motion import Vector2


def clamp(
    value: int | float, minimum: int | float, maximum: int | float
) -> int | float:
    return min(max(value, minimum), maximum)


def lerp(a: int | float, b: int | float, t: int | float) -> int | float:
    return a * (1 - t) + b * t


def vec_midpoint(a: Vector2, b: Vector2) -> Vector2:
    return Vector2((a.x + b.x) / 2, (a.y + b.y) / 2)
