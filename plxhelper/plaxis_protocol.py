from __future__ import annotations

from typing import NewType, Protocol

PlxNumber = NewType("PlxFloat", str)


class PlxStr(Protocol):
    def __str__(self) -> str:
        ...


class PlxBoundingBox(Protocol):
    xMin: PlxNumber
    yMin: PlxNumber
    zMin: PlxNumber
    xMax: PlxNumber
    yMax: PlxNumber
    zMax: PlxNumber


class PlxObj(Protocol):
    BoundingBox: PlxBoundingBox


PlxListable = list[PlxObj]
PlxProtocol = PlxObj | PlxListable


class FloatifyError(ValueError):
    pass


def floatify(value) -> float:
    try:
        return float(str(value))
    except Exception as exc:
        raise FloatifyError() from exc
