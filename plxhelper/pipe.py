from __future__ import annotations

from dataclasses import dataclass
from math import asin, degrees, acos
from typing import TypeVar, Generic
from scipy.special import sindg, cosdg

from helper_metaclasses import RequiredMembersABCMeta
from plxhelper.geo import HasCoordinateSystem
from plxhelper.plaxis_helper import add_box

L = TypeVar("L")  # length type
A = TypeVar("A")  # angle type


@dataclass
class RelativePosition(Generic[L]):
    """Relative position of object (usually in reference to the origin of a containing object).

    If there is a containing object reference it must have a coordinate_system.
    """

    i: L  # relative position of object to origin of a containing object along axis0
    j: L | None = None  # relative position of object to origin of a containing object along axis1
    k: L | None = None  # relative position of object to origin of a containing object along axis2
    container: HasCoordinateSystem[L] | None = None


# Using this metaclass to fail early
class PipeProfileABCMeta(Generic[L], RequiredMembersABCMeta):
    """Check for presence of the members below, so I don't forget to include them."""

    required: list[str] = ["rise", "span", "top_rise", "continuous"]


class PipeProfileABC(Generic[L], metaclass=PipeProfileABCMeta[L]):
    rise: L
    span: L
    top_rise: L
    continuous: bool


class ContinuousPipeProfileABC(PipeProfileABC):
    continuous: bool = True
    bedding: Bedding | None = None


class DiscontinuousPipeProfileABC(PipeProfileABC):
    continuous: bool = False
    footings: list[Footing] | None = None

    def add_footing_pair(
            self,
            width,
            height,
            outside,
            key,
    ) -> None:
        """Add footings as a pair of rectangles. The x, y, z is the top center of the structure to be
        supported by the footing pair:

                  _______o________    <---- origin is top center, o
                 /   ^structure^  \
                /                  \
         ______/_____          _____\______
        |  footing1  |        |  footing0  |
        |____________|        |____________|
        """
        x, y, z = 0, 0, 0
        dx = self.span / 2 + outside - width / 2
        dz = z - self.rise + key
        footing_objs = []
        for plus_or_minus in (lambda lhs: lhs * rhs for rhs in (1, -1)):
            xi = x + plus_or_minus(dx)
            footing = add_box(xi, y, dz, width, height, axis1, axis2)
            footing_objs.append(footing)
        self.footings = footing_objs

    def add_footing(self,
                    width,
                    height,
                    outside,
                    key=None,
                    ):
        pass


class CurvedPipeProfileABC(Generic[L, A], PipeProfileABC[L]):
    """Adds an A to the Generic for the angles."""
    pass


class CurvedContinuousPipeProfileABC(CurvedPipeProfileABC[L, A], ContinuousPipeProfileABC[L]):
    bedding: CurvedBedding[L, A] | None = None

    def add_bedding(self, angle, thickness):
        self.bedding = CurvedBedding(angle, thickness)


class CurvedDiscontinuousPipeProfileABC(CurvedPipeProfileABC[L, A], DiscontinuousPipeProfileABC[L]):
    pass


class RoundProfile(CurvedContinuousPipeProfileABC[L, A]):
    """Information thoroughly defining a 2D round shape."""

    radius: L
    diameter: L
    r: L
    d: L

    def __init__(self, radius: L | None = None, diameter: L | None = None):
        match radius, diameter:
            case None, None:
                raise TypeError("radius or diameter required")
            case _, None:
                self.radius = self.r = radius
                self.diameter = self.d = radius * 2
            case None, _:
                self.diameter = self.d = diameter
                self.radius = self.r = diameter / 2
            case _:
                raise TypeError("provide only the radius or diameter, not both")
        self.rise = self.diameter
        self.span = self.diameter

    @property
    def info_dict(self):
        return dict(
            segments=[
                dict(SegmentType="Arc",
                     RelativeStartAngle1=180,  # deg; 180 because starting at crown
                     Radius=self.radius,
                     CentralAngle=360  # deg
                     ),
            ])


class PipeArchProfile(CurvedContinuousPipeProfileABC[L, A]):
    """Information thoroughly defining a 2D pipe arch shape."""

    r_t: L
    r_b: L
    r_c: L
    theta_t: A
    theta_b: A
    theta_c: A
    a: L
    b: L
    c: L
    alpha: A
    beta: A
    gamma: A
    α: A
    β: A
    γ: A

    def __init__(self, r_t: L, r_b: L, r_c: L, *, rise: L | None = None, span: L | None = None):
        self.r_t = r_t
        self.r_b = r_b
        self.r_c = r_c
        self.a = a = r_b - r_c
        self.b = b = r_t - r_c
        match rise, span:
            case None, None:
                raise TypeError("span or rise required")
            case _, None:
                self.rise = rise
                self.c = c = r_b + r_t - rise
                self.γ = self.gamma = γ = degrees(acos((a ** 2 + b ** 2 - c ** 2) / (2 * a * b)))
                self.α = self.alpha = α = degrees(asin(a / c * sindg(γ)))
                self.span = 2 * (r_c + b * sindg(α))
                self.β = self.beta = β = 180.0 - α - γ
            case None, _:
                self.span = span
                self.α = self.alpha = α = degrees(asin((1 / 2 * span - r_c) / b))
                self.β = self.beta = β = degrees(asin(b / a * sindg(α)))
                self.γ = self.gamma = γ = 180.0 - α - β
                self.c = c = (a ** 2 + b ** 2 - 2 * a * b * cosdg(γ)) ** 0.5
                self.rise = r_b + r_t - c
            case _:
                raise TypeError("provide only the span or rise, not both")
        self.θ_t = self.theta_t = 2 * α
        self.θ_b = self.theta_b = 2 * β
        self.θ_c = self.theta_c = γ

    @property
    def info_dict(self):
        return dict(
            segments=[
                dict(SegmentType="Arc",
                     RelativeStartAngle1=180,  # deg; 180 because starting at crown
                     Radius=self.r_t,
                     CentralAngle=self.theta_t / 2
                     ),
                dict(SegmentType="Arc",
                     Radius=self.r_c,
                     CentralAngle=self.theta_c / 2
                     ),
                dict(SegmentType="SymmetricExtend",
                     ),
                dict(SegmentType="SymmetricClose",
                     ),
            ])


@dataclass
class Footing(Generic[L]):
    width: L
    height: L
    outside: L
    key: L  # depth into footing of pipe legs


@dataclass
class PedestalFooting(Footing[L]):
    stem_height: L
    stem_center: L


@dataclass
class Bedding:
    pass


@dataclass
class RectangularBedding(Generic[L], Bedding):
    width: L
    height: L
    embedment: L  # depth into bedding of pipe invert


@dataclass
class CurvedBedding(Generic[L, A], Bedding):
    angle: A
    thickness: L
