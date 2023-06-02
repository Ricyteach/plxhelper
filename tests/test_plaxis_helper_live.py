import pytest
from scipy.special import cosdg

from plxhelper.geo import BoundingBox
from plxhelper.plaxis_helper import (
    connect_server,
    add_pipe_structure,
    skew_extrude,
    extrude,
    cut,
    rotate,
    skew_cut,
    translate,
    add_box,
)

connect_server()

from plxhelper.plaxis_helper import g_i

# in-situ soil parameters and geometry
γ_soil_pci = (γ_soil := 120) / 1728  # pcf
Ms_psi = 1000  # psi
h_mincover_in = 3.5 * 12  # ft
h_cover_in = (h_cover := 40) * 12  # ft
h_bedding_in = (h_bedding := 10) * 12  # ft
h_footing_in = (h_footing := 2.5) * 12  # ft
h_key_in = 5  # in
w_footing_in = (2 * (3 + 7 / 12)) * 12  # ft
offset_footing_in = w_footing_in / 2
backfill_outside_in = 36

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


# pipe extrusion
length = 500
axis1, axis2 = ((1, 0, 0), (0, 0, 1))
start_point = (0, 0, 0)
extrude_vector = (0, 1, 0)


@pytest.fixture
def clear_plaxis_at_completion():
    yield
    assert all(map(g_i.delete, g_i.Geometry))


@pytest.fixture(params=(True, False), ids=["with_footings", "no_footings"])
def with_footings_and_backfill(request, clear_plaxis_at_completion):
    return request.param


@pytest.fixture
def pipe_shape_info_dict(with_footings_and_backfill):
    # draw shape starting at invert but offset from z elevation
    return dict(
        Offset1=span_AVG_in / 2,
        Offset2=-h_AVG_in,
        footing=(
            dict(
                span=span_AVG_in,
                rise=h_AVG_in,
                width=w_footing_in,
                height=h_footing_in,
                outside=offset_footing_in,
                key=h_key_in,
            )
        )
        if with_footings_and_backfill
        else None,
        select_backfill=(
            dict(
                width=w_AVG_in + backfill_outside_in * 2,
                height=h_AVG_in + h_mincover_in - h_key_in,
                h_min=h_mincover_in,
            )
        )
        if with_footings_and_backfill
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
def no_of_cuttings(with_footings_and_backfill):
    if with_footings_and_backfill:
        return 8
    else:
        return 2


@pytest.fixture
def cutting_angle_deg():
    return 15  # 180 - 127.5  # deg


@pytest.fixture
def extruded_pipe_structures(pipe_shape_info_dict):
    pipe_structure_dict = add_pipe_structure(
        start_point, pipe_shape_info_dict, axis1, axis2
    )
    pipe_structures = tuple(pipe_structure_dict.values())
    extruded_pipe_structures = extrude(
        to_extrude=pipe_structures, length=length, vector=extrude_vector
    )
    assert extruded_pipe_structures
    return extruded_pipe_structures


@pytest.fixture
def cutter_obj():
    return g_i.surface(
        (-span_AVG_in, length / 2, -h_AVG_in * 2),
        (span_AVG_in, length / 2, -h_AVG_in * 2),
        (span_AVG_in, length / 2, h_AVG_in * 2),
        (-span_AVG_in, length / 2, h_AVG_in * 2),
    )


@pytest.fixture
def cutting_angles_deg():
    return 0, -90, 52.5, 0


@pytest.fixture
def extrusion_lengths():
    return 300, 550, 300


def test_add_extrude_and_cut_pipe_structure(
    cutter_obj, extruded_pipe_structures, no_of_cuttings
):
    cut_list = cut(g_i.group(extruded_pipe_structures), cutter_obj)
    g_i.ungroup(extruded_pipe_structures)
    assert len(cut_list) == no_of_cuttings


def test_add_extrude_and_skew_cut_pipe_structure(
    extruded_pipe_structures,
    cutter_obj,
    cutting_angle_deg,
    no_of_cuttings,
    with_footings_and_backfill,
):
    results = skew_cut(
        extruded_pipe_structures, cutter_obj, cutting_angle_deg, extrude_vector[:2]
    )
    if isinstance(results, list):
        assert len(results) == no_of_cuttings / 2
    if not with_footings_and_backfill:
        assert not isinstance(results, list)


def test_add_extrude_and_skew_cut_pipe_structure_multiple_turns(
    pipe_shape_info_dict,
    cutting_angles_deg,
    extrusion_lengths,
):
    start_point = -100, -100, 0
    start_direction = 1, 1, 0
    pipe_structure_dict = add_pipe_structure(
        (0, 0, 0), pipe_shape_info_dict, axis1=(1, 0, 0)
    )
    pipe_structures = g_i.group(tuple(pipe_structure_dict.values()))
    pipe_structures_bb = BoundingBox.from_plx(pipe_structures)
    pipe_structures_width = pipe_structures_bb.p_max.x - pipe_structures_bb.p_min.x
    pipe_structures_height = pipe_structures_bb.p_max.z - pipe_structures_bb.p_min.z

    cutter_width = (
        1.01
        * pipe_structures_width
        / min(cosdg(abs(a) / 2) for a in cutting_angles_deg)
    )
    cutter_height = 1.10 * pipe_structures_height

    cutter_box = add_box(
        0,
        0,
        h_mincover_in + 0.05 * pipe_structures_height,
        cutter_width,
        cutter_height,
        (1, 0, 0),
    )

    length0 = extrusion_lengths[0]
    extrude_vector0 = None
    extruded_pipe_structures = extrude(
        to_extrude=pipe_structures, length=length0, vector=extrude_vector0
    )
