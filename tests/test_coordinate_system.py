import pytest
from plxhelper.geo import CoordinateSystem, Vector
import numpy as np

INVALID_KWARGS = [
    dict(
        axis0=(),
        axis1=(),
        x=0,
        y=0,
        z=0,
        origin=(),
        exception=TypeError,
    ),
    dict(
        axis0=(1, 0, 0),
        axis1=(0, 0, 1),
        x=0,
        y=0,
        z=0,
        origin=(1, 1, 1),
        exception=TypeError,
    ),
]

VALID_KWARGS = [
    dict(
    ),
    dict(
        axis0=(1, 0, 0),
        axis1=(0, 0, 1),
        origin=(1, 1, 1),
    ),
    dict(
        axis0=(1, 0, 0),
        axis1=(0, 0, 1),
        x=1,
        y=1,
        z=1,
    ),
    dict(
        axis0=(1.1, 3.3, 0),
        axis1=(0, 0, 10),
        x=1,
        y=2,
        z=3,
    ),
    dict(
        axis0=(-1, 0, 0),
        axis1=(0, 0, -1),
        origin=(1, 2, 3),
    ),
]


@pytest.fixture(params=VALID_KWARGS)
def valid_coord_system_kwargs(request):
    return request.param


@pytest.fixture(params=INVALID_KWARGS)
def invalid_coord_system_kwargs(request):
    return request.param


@pytest.fixture
def coord_system(valid_coord_system_kwargs):
    return CoordinateSystem(**valid_coord_system_kwargs)


def test_coord_system_exception(invalid_coord_system_kwargs):
    exc = invalid_coord_system_kwargs.pop("exception", None)
    with pytest.raises(exc):
        CoordinateSystem(**invalid_coord_system_kwargs)


def test_coord_system(coord_system):
    assert coord_system


def test_convert_global(coord_system):
    point = [10, 10, 10]
    result = np.array(coord_system.convert_global(point))
    result_hat = result / np.linalg.norm(result)
    origin = np.array(coord_system.origin)
    origin_hat = origin / np.linalg.norm(origin)
    origin_shadow = np.dot(result_hat, origin) * result_hat
    result_length = np.linalg.norm(result) - np.linalg.norm(origin_shadow)
    expected_length = np.linalg.norm(point)
    assert result_length == pytest.approx(expected_length)
