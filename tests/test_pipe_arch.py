import pytest
from plxhelper.pipe import PipeArchProfile


@pytest.fixture(params=[
    PipeArchProfile(43.0, 132.3, 18.5, rise=55.0),
    PipeArchProfile(43.0, 132.3, 18.5, span=82.7153),
])
def pipe_arch(request):
    return request.param


def test_pipe_arch(pipe_arch):
    assert pipe_arch


def test_pipe_arch_members(pipe_arch):
    assert pipe_arch.rise == pytest.approx(55.0)
    assert pipe_arch.span == pytest.approx(82.7153)
    assert pipe_arch.a ==  pytest.approx(113.8)
    assert pipe_arch.b ==  pytest.approx(24.5)
    assert pipe_arch.c ==  pytest.approx(120.3)
    assert pipe_arch.alpha == pytest.approx(68.90184)
    assert pipe_arch.beta == pytest.approx(11.587136)
    assert pipe_arch.gamma == pytest.approx(99.511)
