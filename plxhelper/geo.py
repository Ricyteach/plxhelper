from __future__ import annotations

from dataclasses import dataclass, field
from math import dist, isclose, acos, degrees
from numbers import Real
from typing import NamedTuple, TypeVar, Generic, Iterable, Protocol, cast

from scipy.special import cosdg, sindg
import numpy as np

from plxhelper.iterable_helper import coerce
from plxhelper.plaxis_protocol import PlxProtocol, floatify

CoordVar = TypeVar("CoordVar", bound=float)
VectorLike = tuple[CoordVar, CoordVar, CoordVar]
PointLike = tuple[CoordVar, CoordVar, CoordVar] | tuple[CoordVar, CoordVar]
BoundingBox_co = tuple[PointLike[CoordVar], PointLike[CoordVar]]


def rotate(vec: VectorLike[CoordVar], axis: VectorLike[CoordVar], theta_deg: CoordVar) -> VectorLike[CoordVar]:
    """
    Rotates a 3D vector around a given axis by a specified angle.

    Args:
        vec: The original vector.
        axis: The axis of rotation.
        theta_deg: The angle of rotation in degrees.

    Returns:
        The rotated vector.

    Raises:
        TypeError: If `vec` or `axis` is not a 3-tuple of numbers, or if `theta_deg` is not a number.
        ValueError: If `vec` or `axis` is the zero vector.
    """

    # Check that both input vectors have length 3 and all the atomic values are numbers
    match [vec, axis, theta_deg]:
        case (x, y, z), (i, j, k), a if all(isinstance(v, Real) for v in (x, y, z, i, j, k)):
            if x == y == z == 0:
                raise ValueError("The vector to be rotated cannot be the zero vector")
            if i == j == k == 0:
                raise ValueError("The axis of rotation cannot be the zero vector")
            if not isinstance(a, (float, int)):
                raise TypeError("The angle of rotation must be a number")
        case (_, _, _), _, _:
            raise TypeError("All vector/point components must be numbers")
        case _, (_, _, _), _:
            raise TypeError("All axis components must be numbers")
        case _:
            raise TypeError("Both the vector and axis of rotation must be 3-dimensional")

    # Convert the tuples to numpy arrays
    v_arr = np.array([float(x), float(y), float(z)])
    a_arr = np.array([float(i), float(j), float(k)])

    # Normalize the vectors
    v_hat = v_arr / np.linalg.norm(v_arr)
    a_hat = a_arr / np.linalg.norm(a_arr)

    # If v and a are pointing in the same direction, no rotation is needed
    if np.isclose(np.dot(v_hat, a_hat), 1.0):
        return vec

    # Convert the angle to radians
    theta_rad = np.deg2rad(theta_deg)

    # Calculate components of the rotated vector
    component1 = v_arr * np.cos(theta_rad)
    component2 = np.cross(a_hat, v_arr) * np.sin(theta_rad)
    component3 = a_hat * np.dot(a_hat, v_arr) * (1 - np.cos(theta_rad))

    # Add the components to get the rotated vector
    rotated_v = component1 + component2 + component3

    # Convert the rotated vector back to a tuple and return it
    return tuple(rotated_v)


class Vector(Generic[CoordVar], NamedTuple):
    i: CoordVar
    j: CoordVar
    k: CoordVar

    def __add__(self: Iterable[CoordVar], other: Iterable[CoordVar]) -> Iterable[CoordVar]:
        return coerce((lhs + rhs for lhs, rhs in zip(self, other, strict=True)), type(self))

    __radd__ = __add__

    def __sub__(self: Iterable[CoordVar], other: Iterable[CoordVar]) -> Iterable[CoordVar]:
        return coerce((lhs - rhs for lhs, rhs in zip(self, other, strict=True)), type(self))

    def __rsub__(self: Iterable[CoordVar], other: Iterable[CoordVar]) -> Iterable[CoordVar]:
        return coerce((lhs - rhs for lhs, rhs in zip(other, self, strict=True)), type(self))

    def __neg__(self: Iterable[CoordVar]) -> Iterable[CoordVar]:
        return coerce((-coord for coord in self), type(self))

    def __mul__(self: Iterable[CoordVar], other: float) -> Iterable[CoordVar]:
        return coerce((other * value for value in self), type(self))

    __rmul__ = __mul__

    def __matmul__(self: Iterable[CoordVar], other):
        return coerce(np.cross(self, other), type(self))

    def __rmatmul__(self: Iterable[CoordVar], other):
        return coerce(np.cross(other, self), type(other))

    def __truediv__(self: Iterable[CoordVar], other: CoordVar) -> Iterable[CoordVar]:
        return coerce((v * (1 / other) for v in self), type(self))

    @property
    def magnitude(self) -> float:
        return dist(self, (0, 0, 0))

    @property
    def unit(self) -> Vector:
        return self / self.magnitude

    def rotate(self, axis: Iterable[CoordVar], θ_deg: CoordVar) -> Iterable[CoordVar]:
        """Rotate the vector by the given angle around axis."""

        return coerce(rotate(self, axis, θ_deg), type(self))

    def rotate_z(self: Iterable[CoordVar], θ_deg: float) -> Iterable[CoordVar]:
        x, y, z = self
        i = x * cosdg(θ_deg) - y * sindg(θ_deg)
        j = x * sindg(θ_deg) + y * cosdg(θ_deg)
        k = z
        return coerce((i, j, k), type(self))

    def dot(self: Iterable[CoordVar], other: Iterable[CoordVar]) -> CoordVar:
        return cast(CoordVar, sum([i * j for (i, j) in zip(self, other)]))


class Point(Generic[CoordVar], NamedTuple):
    x: CoordVar
    y: CoordVar
    z: CoordVar


class BoundingBox(Generic[CoordVar], NamedTuple):
    """
    A rectangle or box with one corner at p_min, and another corner at p_max.
    The BB is always assumed to be oriented so that the BB height is along the z-axis.

    Attributes:
        p_min: The minimum point of the bounding box.
        p_max: The maximum point of the bounding box.
    """

    p_min: PointLike[CoordVar]  # xMin, yMin, zMin
    p_max: PointLike[CoordVar]  # xMax, yMax, zMax

    @classmethod
    def from_min_max(cls, p_min: PointLike, p_max: PointLike) -> BoundingBox[CoordVar]:
        if any(
            (_min := coord_min) > (_max := coord_max) and (_field := field)
            for coord_min, coord_max, field in zip(p_min, p_max, "xyz", strict=True)
        ):
            raise ValueError(
                f"INVALID: (min_{_field!s} = {_min}) > (coord_max{_field!s} = {_max})"
            )
        return cls(Point(*p_min), Point(*p_max))

    @staticmethod
    def from_plx(plx_obj: PlxProtocol) -> BoundingBox[CoordVar]:
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
    def find_min_max(cls, obj_list: list[BoundingBox[CoordVar]], key=None) -> BoundingBox[CoordVar]:
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
    def points(self) -> tuple[PointLike, PointLike, PointLike, PointLike]:
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

    def resized(self, increment: float) -> BoundingBox[CoordVar]:
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

    def translated(self, vector: VectorLike):
        return self.__class__.from_min_max(
            Vector.__add__(self.p_min, vector), Vector.__add__(self.p_max, vector)
        )


def unit_vector(vector: VectorLike) -> np.ndarray:
    """Returns the unit vector of the vector."""
    return vector / np.linalg.norm(vector)


def angle_between_vectors(v1: VectorLike, v2: VectorLike) -> float:
    """Calculate the angle between two vectors."""
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))


@dataclass
class CoordinateSystem(Generic[CoordVar]):
    """A set of perpendicular cartesian axes at a fixed position.

    The axes are requires to be iterables of length 3.
    """

    axis0: VectorLike[CoordVar] = field(default=(1, 0, 0))
    axis1: VectorLike[CoordVar] = field(default=(0, 0, 1))
    x: CoordVar = field(default=None, repr=False)
    y: CoordVar = field(default=None, repr=False)
    z: CoordVar = field(default=None, repr=False)
    origin: Point[CoordVar] = field(default=None)
    u0: Vector[CoordVar] = field(init=False, repr=False)
    u1: Vector[CoordVar] = field(init=False, repr=False)
    u2: Vector[CoordVar] = field(init=False, repr=False)

    def __post_init__(self):

        # origin point
        match (self.x, self.y, self.z), self.origin:
            case (x, y, z), None:
                self.x = x if x is not None else 0
                self.y = y if y is not None else 0
                self.z = z if z is not None else 0
                self.origin = Point(self.x, self.y, self.z)
            case (None, None, None), point:
                self.x, self.y, self.z = point
                self.origin = Point(*point)
            case _:
                raise TypeError()

        # axes and unit axes 0 and 1
        for axis, num in zip((self.axis0, self.axis1), "01"):
            match axis:
                case (i, j, k):
                    setattr(self, f"u{num}", Vector(i, j, k).unit)

                    # check for the case of exhausted iterators for this axis (for the repr)
                    match axis:
                        case (_, _, _):
                            pass
                        case _:
                            # replace with a tuple for this case
                            setattr(self, f"axis{num}", (i, j, k))
                case _:
                    raise TypeError(f"axis{num} required to be a VectorLike of length 3; "
                                    f"length {num} instead")

        # unit axis 2
        self.u2 = cast(Vector[CoordVar], self.u0 @ self.u1)

        # check for perpendicular axes
        if not isclose(self.u0.dot(self.u1), 0):
            raise ValueError("axes must be perpendicular")

    def convert_global(self, point: PointLike[CoordVar]) -> PointLike[CoordVar]:
        """Converts a point from local to global coordinates.

        Args:
            point: a 3-tuple representing the coordinates of the point in the local coordinate system.

        Returns:
            A 3-tuple representing the coordinates of the point in the global coordinate system.
        """
        point = np.array(point)
        origin = np.array(self.origin)

        # Translate the point to global coordinates
        point = translate(point, origin)

        # Calculate the rotation angles
        theta0 = angle_between_vectors((1, 0, 0), self.u0)
        theta1 = angle_between_vectors((0, 1, 0), self.u1)

        # Rotate the point to match the global coordinate system
        point = rotate(point, (0, 0, 1), theta0)
        point = rotate(point, self.u0, theta1)

        return tuple(point)

        # translate the point
        iter_point = iter(point)
        translated_coords = []
        for global_coord in self.origin:
            local_coord = next(iter_point, None)
            translated_coords.append(local_coord + global_coord) if local_coord is not None else global_coord
        if next(iter_point,(sentinel:=object())) is not sentinel:
            raise TypeError(f"The point object is more than length 3")

        # rotate the point vector
        p⃗_i = Vector(*translated_coords)
        ## start with closing angle between system x (û) and global x (ĝ) axes
        û = self.u0
        ĝ = Vector(1, 0, 0)
        if not all(np.isclose(û, ĝ)):
            ### only do first rotation if û and ĝ are not the same
            if not all(np.isclose(û, -ĝ)):
                ### close the angle by rotating around some n̂
                n̂ = û @ ĝ
                ### rotation angle
                dθ_xx = degrees(acos(û.dot(ĝ)))
                ### point vector after first rotation
                p⃗_i = p⃗_i.rotate(n̂, dθ_xx)
                ### rotate the coordinate system y using this first rotation
                û = self.u1.rotate(n̂, dθ_xx)
            ### only do second rotation if û and ĝ are opposed
            if all(np.isclose(û, -ĝ)):
                ### rotation axis is coordinate system y
                p⃗_i = Vector(-p⃗_i.i, p⃗_i.j, -p⃗_i.k)
                ### rotate the coordinate system y using this first rotation
                û = Vector(-self.u1.i, self.u1.j, -self.u1.k)
        else:
            ### did not rotate, proceed to next axis, coordinate system y
            û = self.u1
        ## close the angle between rotated coordinate system y and global x by rotating around some new n̂
        ĝ = Vector(0, 1, 0)
        ### only do the rotation if û and ĝ are not the same
        if not all(np.isclose(û, ĝ)):
            ### point vector after second rotation
            if not all(np.isclose(û, -ĝ)):
                ### rotation axis
                n̂ = û @ ĝ
                ### rotation angle
                dθ_yy = degrees(acos(û.dot(ĝ)))
                p⃗_i = p⃗_i.rotate(n̂, dθ_yy)
            else:
                ### handle case of û and ĝ directly opposed to each other
                p⃗_i = Vector(p⃗_i.i, -p⃗_i.j, p⃗_i.k)
        return cast(PointLike[CoordVar], coerce((coord for coord,_ in zip(p⃗_i, point)), type(point)))


class HasCoordinateSystem(Protocol[CoordVar]):
    fixed_trajectory: CoordinateSystem[CoordVar]
