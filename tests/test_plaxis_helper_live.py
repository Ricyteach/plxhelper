import pytest

from plxhelper.plaxis_helper import (
    connect_server,
    add_pipe_structure,
    skew_extrude,
    extrude,
    cut,
)

connect_server()

from plxhelper.plaxis_helper import g_i

# in-situ soil parameters and geometry
γ_soil_pci = (γ_soil := 120) / 1728  # pcf
Ms_psi = 1000  # psi
h_cover_in = (h_cover := 40) * 12  # ft
h_bedding_in = (h_bedding := 10) * 12  # ft
h_footing_in = (h_footing := 2.5) * 12  # ft
h_key_in = 5  # in
w_footing_in = (2 * (3 + 7 / 12)) * 12  # ft
offset_footing_in = w_footing_in / 2

# pipe geometry
r_ID_in = (13) * 12  # ft
h_ID_in = r_ID_in
w_ID_in = 2 * r_ID_in
span_ID_in = 2 * r_ID_in
gage_in = 5 / 16  # in
depth_in = 6  # in
r_AVG_in = r_ID_in + depth_in / 2
h_AVG_in = r_AVG_in
w_AVG_in = 2 * r_AVG_in
span_AVG_in = 2 * r_AVG_in

## For Duncan-Selig soil model interpolation only ##
# depth from structure crown to springline
d_springline_in = h_AVG_in - 5  # in
# height of soil from grade to springline
h_springline_in = h_cover_in + d_springline_in

# modeled extents
grade_el = h_cover_in + h_AVG_in
h_model_in = h_cover_in + h_AVG_in + (h_footing_in - h_key_in) + h_bedding_in
water_el = grade_el - h_model_in
xmin, ymin, xmax, ymax = (-w_AVG_in * 3, -w_AVG_in * 6, w_AVG_in * 3, w_AVG_in * 6)


@pytest.fixture(params=(True, False))
def with_footing(request):
    return request.param


@pytest.fixture
def pipe_shape_info_dict(with_footing):
    # draw shape starting at invert but offset from z elevation
    return dict(
        Offset1=span_AVG_in / 2,
        Offset2=-h_AVG_in,
        footing=(
            footing_info := dict(
                span=span_AVG_in,
                rise=h_AVG_in,
                width=w_footing_in,
                height=h_footing_in,
                outside=offset_footing_in,
                key=h_key_in,
            )
        )
        if with_footing
        else None,
        segments=[
            dict(
                SegmentType="Arc",
                RelativeStartAngle1=90,  # deg; 90 because starting at invert
                Radius=r_AVG_in,  # in
                CentralAngle=180,  # deg
            ),
        ],
    )


@pytest.fixture
def cutting_length(with_footing):
    if with_footing:
        return 6
    else:
        return 2


def test_add_pipe_structure(pipe_shape_info_dict, cutting_length):
    length = 500
    axis1, axis2 = ((1, 0, 0), (0, 0, 1))
    start_point = (0, 0, 0)
    pipe_structure_dict = add_pipe_structure(
        start_point, pipe_shape_info_dict, axis1, axis2
    )
    pipe_structures = tuple(pipe_structure_dict.values())
    extruded_pipe_structures = extrude(
        to_extrude=pipe_structures, length=length, vector=(0, 1, 0)
    )
    assert extruded_pipe_structures
    cutter_obj = g_i.surface(
        (-span_AVG_in, length / 2, -h_AVG_in * 2),
        (span_AVG_in, length / 2, -h_AVG_in * 2),
        (span_AVG_in, length / 2, h_AVG_in * 2),
        (-span_AVG_in, length / 2, h_AVG_in * 2),
    )
    try:
        cut_list = cut(g_i.group(extruded_pipe_structures), cutter_obj)
        g_i.ungroup(extruded_pipe_structures)
        assert len(cut_list) == cutting_length
    finally:
        assert all(map(g_i.delete, g_i.Geometry))
