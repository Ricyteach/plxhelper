from __future__ import annotations

from math import dist
from typing import NamedTuple, NewType

from plxhelper.plaxis_protocol import PlxProtocol, floatify

Coord = NewType("Coord", float)


class Point(NamedTuple):
    x: float
    y: float
    z: float = None


class BoundingBox(NamedTuple):
    p_min: Point  # xMin, yMin, zMin
    p_max: Point  # xMax, yMax, zMax

    @staticmethod
    def from_plx(plx_obj: PlxProtocol) -> BoundingBox:
        attr_list = ("xMin", "yMin", "zMin", "xMax", "yMax", "zMax")
        try:
            return BoundingBox(
                Point(
                    *(floatify(getattr(plx_obj.BoundingBox, k)) for k in attr_list[:3])
                ),
                Point(
                    *(floatify(getattr(plx_obj.BoundingBox, k)) for k in attr_list[3:])
                ),
            )
        except AttributeError:
            pass
        # assume obj is a listable
        result = BoundingBox.find_min_max(
            [BoundingBox.from_plx(item) for item in plx_obj], key=floatify
        )
        return result

    @classmethod
    def find_min_max(cls, obj_list: list[BoundingBox], key=None) -> BoundingBox:
        """Finds the overall box bounding a list of boxes."""

        if key is None:

            def key(x):
                return x

        min_values = {}
        max_values = {}

        for attr in ["x", "y", "z"]:
            min_values[attr] = min(key(getattr(obj.p_min, attr)) for obj in obj_list)
            max_values[attr] = max(key(getattr(obj.p_max, attr)) for obj in obj_list)

        return cls(
            Point(
                Coord(min_values["x"]),
                Coord(min_values["y"]),
                Coord(min_values["z"]),
            ),
            Point(
                Coord(max_values["x"]),
                Coord(max_values["y"]),
                Coord(max_values["z"]),
            ),
        )

    @property
    def width(self) -> float:
        """Finds the width of a bounding_box in the XY plane of 3D space."""

        # Calculate the width of the rectangle in the XY plane.
        width_xy = dist(
            (self.p_min.x, self.p_min.y),
            (self.p_max.x, self.p_max.y),
        )

        # Return the width of the rectangle.
        return width_xy

    @property
    def height(self) -> float:
        """Finds the height of a bounding_box in the Z direction of 3D space."""

        # Return the height of the rectangle.
        return self.p_max.z - self.p_min.z

    def resized_bounding_box(bounding_box, increment: float) -> BoundingBox:
        """Increments the (p_min, p_max) point tuples in 3D space of a bounding box

        Returns: A (i_min, i_max) point tuple that is on the same line as (p_min, p_max), but the distance between (
        i_min, i_max) has been resized by `increment`.
        """

        p_min, p_max = bounding_box

        # Return the incremented bounding_box

        i_min, i_max = None, None

        return i_min, i_max
