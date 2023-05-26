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
    assert type(vector_c) is type(a_plus_b)


def test_minus_tuple(vector_a, tuple_b, a_minus_b):
    assert (vector_c := (vector_a - tuple_b)) == a_minus_b
    assert type(vector_c) is type(a_minus_b)


def test_coerce_type(tuple_a):
    assert (result := Vector._coerce(tuple_a, tuple)) == tuple_a
    assert type(result) is tuple


def test_rotate_z(vector_a):
    assert vector_a.rotate_z(90) == pytest.approx((-vector_a.j, vector_a.i, vector_a.k))
    assert vector_a.rotate_z(-90) == pytest.approx(
        (vector_a.j, -vector_a.i, vector_a.k)
    )
