import pytest
from plxhelper.pipe import RoundProfile


@pytest.fixture(params=[
    RoundProfile(radius=55.0),
    RoundProfile(diameter=110.0),
])
def round(request) -> RoundProfile:
    return request.param


def test_round(round):
    assert round


def test_round_members(round):
    assert round.radius == pytest.approx(55.0)
    assert round.diameter == pytest.approx(110.0)
    assert round.rise == pytest.approx(110.0)
    assert round.span == pytest.approx(110.0)
