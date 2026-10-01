import numpy as np
import pytest
from plxhelper.geo import Vector


@pytest.fixture
def tuple_a():
    return 1, 2, 3


@pytest.fixture
def tuple_b():
    return 5, 7, 11


@pytest.fixture
def a_plus_b(tuple_a, tuple_b):
    return tuple(a + b for a, b in zip(tuple_a, tuple_b))


@pytest.fixture
def a_minus_b(tuple_a, tuple_b):
    return tuple(a - b for a, b in zip(tuple_a, tuple_b))


@pytest.fixture
def vector_a(tuple_a):
    return Vector(*tuple_a)


@pytest.fixture
def vector_b(tuple_b):
    return Vector(*tuple_b)


def test_vector(vector_a, vector_b):
    assert vector_a
    assert vector_b


def test_equal(vector_a, tuple_a):
    assert vector_a == tuple_a


def test_add_vectors(vector_a, vector_b, a_plus_b):
    assert (vector_a + vector_b) == a_plus_b


def test_minus_vectors(vector_a, vector_b, a_minus_b):
    assert (vector_a - vector_b) == a_minus_b


def test_add_tuple(vector_a, tuple_b, a_plus_b):
    assert (vector_c := (vector_a + tuple_b)) == a_plus_b
    assert type(vector_c) is Vector


def test_minus_tuple(vector_a, tuple_b, a_minus_b):
    assert (vector_c := (vector_a - tuple_b)) == a_minus_b
    assert type(vector_c) is Vector


def test_rotate_z(vector_a):
    assert vector_a.rotate_z(90) == pytest.approx((-vector_a.j, vector_a.i, vector_a.k))
    assert vector_a.rotate_z(-90) == pytest.approx(
        (vector_a.j, -vector_a.i, vector_a.k)
    )


def test_dot(vector_a, vector_b, tuple_a, tuple_b):
    assert vector_a.dot(vector_b) == np.dot(tuple_a, tuple_b)


def test_dot_equal(vector_a):
    assert vector_a.dot(vector_a) == 1


def test_dot_opposed(vector_a):
    assert vector_a.dot(-vector_a) == -1


def test_dot_perpendicular():
    assert Vector(1, 0, 0).dot((0, 1, 0)) == 0


def test_matmul(vector_a, vector_b, tuple_a, tuple_b):
    assert vector_a @ vector_b == tuple(np.cross(tuple_a, tuple_b))


# Rotate corner test cases
ROTATE_CORNER_CASES = [
    # case 1
    (([1, 0], [0, 1, 0], 90), TypeError),
    # case 2
    (([1, 0, 0, 0], [0, 1, 0], 90), TypeError),
    # case 3
    (([1, '0', 0], [0, 1, 0], 90), TypeError),
    # case 4
    (([1, 0, 0], [0, '1', 0], 90), TypeError),
    # case 5
    ((['1', 0, 0], [0, 1, 0], 90), TypeError),
    # case 6
    (([1, 0, 0], [0, 1, 0], '90'), TypeError),
    # case 7
    (([0, 0, 0], [0, 1, 0], 90), ValueError),
    # case 8
    (([1, 0, 0], [0, 0, 0], 90), ValueError),
]

# Rotate valid test cases
ROTATE_VALID_CASES = [
    # case 1
    (([1, 0, 0], [0, 1, 0], 90), [0, 0, -1]),
    # case 2
    (([1, 0, 0], [0, -1, 0], 90), [0, 0, 1]),
    # case 3
    (([0, 1, 0], [1, 0, 0], 90), [0, 0, 1]),
    # case 4
    (([0, 1, 0], [-1, 0, 0], 90), [0, 0, -1]),
    # case 5
    (([0, 1, 0], [0, 0, 1], 90), [-1, 0, 0]),
    # case 6
    (([0, 1, 0], [0, 0, -1], 90), [1, 0, 0]),
    # case 7
    (([1, 0, 1], [0, 1, 0], 90), [1, 0, -1]),
    # case 8
    (([1, 0, 1], [0, -1, 0], 90), [-1, 0, 1]),
    # case 9
    (([0, 1, 1], [1, 0, 0], 90), [0, -1, 1]),
    # case 10
    (([0, 1, 1], [-1, 0, 0], 90), [0, 1, -1]),
    # case 11
    (([1, 1, 0], [0, 0, 1], 90), [-1, 1, 0]),
    # case 12
    (([1, 1, 0], [0, 0, -1], 90), [1, -1, 0]),
    # case 13
    (([1, 1, 1], [0, 1, 0], 90), [1, 1, -1]),
    # case 14
    (([1, 1, 1], [1, 0, 0], 90), [1, -1, 1]),
    # case 15
    (([1, 1, 1], [0, 0, 1], 90), [-1, 1, 1]),
    # case 16
    (([1, 0, 0], [0, 1, 0], 0), [1, 0, 0]),
    # case 17
    (([1, 0, 0], [0, 1, 0], 45), [0.7071067811865476, 0.0, -0.7071067811865475]),
    # case 18
    (([1, 0, 0], [0, 1, 0], 135), [-0.7071067811865475, 0.0, -0.7071067811865477]),
    # case 19
    (([1, 0, 0], [0, 1, 0], 225), [-0.7071067811865477, 0.0, 0.7071067811865474]),
    # case 20
    (([1, 0, 0], [0, 1, 0], -45), [0.7071067811865476, 0.0, 0.7071067811865475]),
    # case 21
    (([1, 0, 0], [0, 1, 0], -135), [-0.7071067811865475, 0.0, 0.7071067811865477]),
    # case 22
    (([1, 0, 0], [0, 1, 0], -225), [-0.7071067811865477, 0.0, -0.7071067811865474]),
]


@pytest.fixture(params=ROTATE_VALID_CASES)
def rotate_valid_cases(request):
    return request.param


def test_rotate_valid_cases(rotate_valid_cases):
    rotate_args, answer = rotate_valid_cases
    rotated = Vector.rotate(*rotate_args)
    assert rotated == pytest.approx(answer)


@pytest.fixture(params=ROTATE_CORNER_CASES)
def rotate_corner_cases(request):
    return request.param


def test_rotate_corner_cases(rotate_corner_cases):
    rotate_args, error_type = rotate_corner_cases
    with pytest.raises(error_type):
        Vector.rotate(*rotate_args)
