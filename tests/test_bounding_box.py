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
    return BoundingBox(Point(1, 1, 1), Point(*(vector + Vector(*start_point))))


def test_bounding_box(bounding_box):
    assert bounding_box


def test_bounding_box_vector(bounding_box, vector):
    assert bounding_box.vector == vector


def test_bounding_box_magnitude(bounding_box, vector):
    assert bounding_box.magnitude == vector.magnitude


def test_bounding_box_resized(bounding_box):
    increment = bounding_box.magnitude * 2
    new_length = increment * 3/2
    bounding_box_resized = bounding_box.resized(increment)
    assert bounding_box_resized.magnitude == new_length
