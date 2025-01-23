def clamp(value: int | float, minimum: int | float, maximum: int | float) -> int | float:
    return min(max(value, minimum), maximum)


def lerp(a: int | float, b: int | float, t: int | float) -> int | float:
    return a * (1 - t) + b * t


def point_in_circle(x: float, y: float, mx: float, my: float, r: float) -> bool:
    return (x - mx) ** 2 / (r**2) + (y - my) ** 2 / (r**2) < 1


def point_in_ellipse(x: float, y: float, mx: float, my: float, rx: float, ry: float) -> bool:
    return (x - mx) ** 2 / (rx**2) + (y - my) ** 2 / (ry**2) < 1


def list_range(min: float, max: float) -> list[int]:
    return list(range(min, max + 1))
