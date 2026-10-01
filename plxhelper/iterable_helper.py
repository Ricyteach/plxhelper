from __future__ import annotations

from typing import Iterable, TypeVar

T = TypeVar("T")


def coerce(iterable: Iterable[T], type_: type) -> Iterable[T]:
    # wrote this to solve the problem of incompatible signatures between tuples and NamedTuples
    try:
        # most built-ins accept one iterable argument in constructor
        return type_(iterable)
    except TypeError:
        # assume a custom class expects unpacked args
        try:
            return type_(*iterable)
        except TypeError:
            raise
