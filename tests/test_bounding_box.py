from math import radians

import pytest
from plxhelper.geo import BoundingBox, Point, Vector


@pytest.fixture
def vector():
    return Vector(1, 2, 3)


@pytest.fixture
def start_point():
    return Point(1, 1, 1)


@pytest.fixture
def bounding_box(start_point, vector):
    return BoundingBox.from_min_max((1, 1, 1), tuple(vector) + Vector(*start_point))


@pytest.fixture
def rotation_angle():
    return 90


@pytest.fixture
def bounding_box_rotated_tuple(rotation_angle):
    return {
        90: ((0.5, 1.5, 1), (2.5, 2.5, 4)),
    }[rotation_angle]


def test_bounding_box(bounding_box):
    assert bounding_box


def test_bounding_box_vector(bounding_box, vector):
    assert bounding_box.vector == vector


def test_bounding_box_magnitude(bounding_box, vector):
    assert bounding_box.magnitude == vector.magnitude


def test_bounding_box_resized(bounding_box):
    increment = bounding_box.magnitude * 2
    new_length = increment * 3 / 2
    bounding_box_resized = bounding_box.resized(increment)
    assert bounding_box_resized.magnitude == new_length


def test_points(bounding_box):
    assert bounding_box.points == ((1, 1, 1), (2, 3, 1), (2, 3, 4), (1, 1, 4))


def test_bounding_box_rotate(bounding_box, bounding_box_rotated_tuple, rotation_angle):
    angle_d = rotation_angle
    result = bounding_box.rotated(angle_d)
    assert result == pytest.approx([*bounding_box_rotated_tuple])
