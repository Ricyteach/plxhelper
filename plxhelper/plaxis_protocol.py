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


def floatify(value) -> float:
    return float(str(value))
