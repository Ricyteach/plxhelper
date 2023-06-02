from __future__ import annotations

from math import dist
from typing import NamedTuple, TypeVar, Generic, Iterable

from scipy.special import cosdg, sindg

from plxhelper.plaxis_protocol import PlxProtocol, floatify

Coord_co = TypeVar("Coord_co", bound=float)
Vector_co = TypeVar("Vector_co", bound=tuple[float, float, float])
Point_co = TypeVar("Point_co", covariant=True, bound=tuple[float, float, float])
BoundingBox_co = TypeVar(
    "BoundingBox_co",
    covariant=True,
    bound=tuple[tuple[float, float, float], tuple[float, float, float]],
)
D2Point_co = TypeVar(
    "D2Point_co",
    covariant=True,
    bound=tuple[float, float],
)
D2PointPair_co = TypeVar(
    "D2PointPair_co",
    covariant=True,
    bound=tuple[tuple[float, float], tuple[float, float]],
)


class Vector(NamedTuple, Generic[Coord_co, Vector_co]):
    i: Coord_co
    j: Coord_co
    k: Coord_co

    def _coerce(self: Iterable[float], type_: type[Vector_co]) -> Vector_co:
        try:
            return type_(v for v, _ in zip(self, range(3), strict=True))
        except TypeError:
            return type_(*(v for v, _ in zip(self, range(3), strict=True)))

    def __add__(self, other: Vector_co) -> Vector_co:
        return Vector._coerce(
            (lhs + rhs for lhs, rhs in zip(self, other, strict=True)), type(other)
        )

    __radd__ = __add__

    def __sub__(self, other: Vector_co) -> Vector_co:
        return Vector(
            *(lhs - rhs for lhs, rhs in zip(self, other, strict=True))
        )._coerce(type(other))

    def __rsub__(self, other: Vector_co) -> Vector_co:
        return Vector(
            *(lhs - rhs for lhs, rhs in zip(other, self, strict=True))
        )._coerce(type(other))

    def __neg__(self) -> Vector:
        return Vector(*(-coord for coord in self))

    def __mul__(self, other: float) -> Vector:
        return Vector(*(other * value for value in self))

    __rmul__ = __mul__

    def __truediv__(self, other: float) -> Vector:
        return self * (1 / other)

    @property
    def magnitude(self) -> float:
        return dist(self, (0, 0, 0))

    def rotate_z(self: Vector_co, θ_deg: float) -> Vector_co:
        x, y, z = self
        i = x * cosdg(θ_deg) - y * sindg(θ_deg)
        j = x * sindg(θ_deg) + y * cosdg(θ_deg)
        k = z
        return Vector._coerce((i, j, k), type(self))


class Point(NamedTuple):
    x: Coord_co
    y: Coord_co
    z: Coord_co


class BoundingBox(NamedTuple, Generic[Point_co]):
    """
    A rectangle or box with one corner at p_min, and another corner at p_max.
    The BB is always assumed to be oriented so that the BB height is along the z-axis.

    Attributes:
        p_min: The minimum point of the bounding box.
        p_max: The maximum point of the bounding box.
    """

    p_min: Point_co  # xMin, yMin, zMin
    p_max: Point_co  # xMax, yMax, zMax

    @classmethod
    def from_min_max(cls, p_min: Point_co, p_max: Point_co) -> BoundingBox:
        if any(
            (_min := coord_min) > (_max := coord_max) and (_field := field)
            for coord_min, coord_max, field in zip(p_min, p_max, "xyz", strict=True)
        ):
            raise ValueError(
                f"INVALID: (min_{_field!s} = {_min}) > (coord_max{_field!s} = {_max})"
            )
        return cls(Point(*p_min), Point(*p_max))

    @staticmethod
    def from_plx(plx_obj: PlxProtocol) -> BoundingBox:
        attr_list = ("xMin", "yMin", "zMin", "xMax", "yMax", "zMax")
        try:
            p_min = tuple(
                floatify(getattr(plx_obj.BoundingBox, k)) for k in attr_list[:3]
            )
            p_max = tuple(
                floatify(getattr(plx_obj.BoundingBox, k)) for k in attr_list[3:]
            )
        except AttributeError:
            pass
        else:
            return BoundingBox.from_min_max(
                p_min,
                p_max,
            )
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
                min_values["x"],
                min_values["y"],
                min_values["z"],
            ),
            Point(
                max_values["x"],
                max_values["y"],
                max_values["z"],
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
        return abs(self.p_max.z - self.p_min.z)

    @property
    def magnitude(self) -> float:
        return dist(*self)

    @property
    def vector(self) -> Vector:
        return Vector(*self.p_max) - Vector(*self.p_min)

    @property
    def points(self) -> tuple[Point_co, Point_co, Point_co, Point_co]:
        """
        A 4-tuple of Point objects representing the box rectangle.
        """

        width_vector = Vector(
            self.p_max.x - self.p_min.x, self.p_max.y - self.p_min.y, 0
        )

        p_2 = self.p_min + Vector(width_vector.i, width_vector.j, 0)
        p_4 = self.p_max + Vector(-width_vector.i, -width_vector.j, 0)

        return (
            self.p_min,
            p_2,
            self.p_max,
            p_4,
        )

    def resized(self, increment: float) -> BoundingBox:
        """Increments the (p_min, p_max) point tuples in 3D space of a bounding box

        Returns: A point that is on the same line as (p_min, p_max), but the distance between (i_min, i_max) has been
        resized by `increment`.
        """

        # get unit vector for the box
        change = self.vector / self.magnitude * increment / 2
        p_min_vec = Vector(*self.p_min) - change
        p_max_vec = Vector(*self.p_max) + change
        return self.__class__.from_min_max(Point(*p_min_vec), Point(*p_max_vec))

    def rotated(self, angle_d):
        vector_to_rotate = self.vector / 2
        vector_rotated = vector_to_rotate.rotate_z(angle_d)
        vector_move = vector_rotated - vector_to_rotate
        p_min_moved = self.p_min - vector_move
        p_max_moved = self.p_max + vector_move
        p_min = (
            min(p_min_moved.x, p_max_moved.x),
            min(p_min_moved.y, p_max_moved.y),
            p_min_moved.z,
        )
        p_max = (
            max(p_min_moved.x, p_max_moved.x),
            max(p_min_moved.y, p_max_moved.y),
            p_max_moved.z,
        )
        return self.__class__.from_min_max(p_min, p_max)

    def translated(self, vector: Vector_co):
        return self.__class__.from_min_max(
            Vector.__add__(self.p_min, vector), Vector.__add__(self.p_max, vector)
        )
