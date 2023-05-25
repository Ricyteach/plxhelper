"""Test plaxis_helper stuff. Do not import plaxis_helper; using patched version instead (see conftest.py)."""
import pytest


def test_g_i_connected(plaxis_helper, g_i, s_i):
    assert plaxis_helper.s_i is s_i
    assert plaxis_helper.g_i is g_i


@pytest.fixture(
    params=[
        ("linear_elastic_soil", "Grout", 40),  # pcf
        ("plate", "GRPLinerPipe", "34mm", "Short"),
    ]
)
def material_type(request):
    return request.param


def test_create_material(plaxis_helper, material_type):
    assert plaxis_helper.material_creator(*material_type)()


@pytest.fixture(
    params=[
        (
            (0, -180, 100),
            ((1, 0, 0), (0, 0, 1)),
            dict(
                segments=[
                    dict(
                        SegmentType="Arc",
                        RelativeStartAngle1=180,  # deg; 180 because starting at crown
                        Radius=33.5,  # in
                        CentralAngle=85.2,  # deg
                    ),
                    dict(
                        SegmentType="Arc",
                        Radius=8.875,  # in
                        CentralAngle=78.3,  # deg
                    ),
                    dict(
                        SegmentType="SymmetricExtend",
                    ),
                    dict(
                        SegmentType="SymmetricClose",
                    ),
                ]
            ),
        ),
        (
            (0, -180, 100),
            ((1, 0, 0), (0, 0, 1)),
            dict(
                Offset1=318 / 2,
                Offset2=-159,
                footing=(
                    footing_info := dict(
                        span=318,
                        rise=159,
                        width=86,
                        height=30,
                        outside=43,
                        key=5,
                    )
                ),
                segments=[
                    dict(
                        SegmentType="Arc",
                        RelativeStartAngle1=90,  # deg; 90 because starting at invert
                        Radius=159,  # in
                        CentralAngle=180,  # deg
                    ),
                ],
            ),
        ),
    ]
)
def add_pipe_params(request):
    return request.param


def test_add_pipe(plaxis_helper, add_pipe_params):
    assert plaxis_helper.add_pipe(*add_pipe_params)
