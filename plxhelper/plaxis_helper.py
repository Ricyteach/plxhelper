"""helpers for creating Plaxis 3D projects"""
from math import radians, cos
from typing import TypedDict, Required, NotRequired, Sequence
import numpy as np

from plxscripting.easy import new_server
import plxhelper.linear_elastic_soil as linear_elastic_soil
import plxhelper.duncan_selig as duncan_selig
import plxhelper.plate as plate
from plxhelper.geo import (
    BoundingBox,
    D2PointPair_co,
    D2Point_co,
    Vector,
    Vector_co,
    Point,
)
from plxhelper.plaxis_protocol import floatify


def connect_server():
    global s_i, g_i
    s_i, g_i = new_server(address="localhost", port=10000, password="python")


def add_soil_layer_materials(soil_materials_list):
    """Set the soil layer materials.

    Can't be run until after layers created in a borehole.
    Because Plaxis is stupid."""
    for layer, soil_material_obj in zip(g_i.Soillayers, soil_materials_list):
        layer.Soil.Material = soil_material_obj


def process_boreholes(boreholes_dict, layer_soilmat_obj_list):
    """The BoreholesDict is of the form:

    BoreholesDict: Dict[tuple[x_coord, y_coord], BoreholeInfoDict]

    ...where BoreholeInfoDict is of the form:

    class BoreholeInfoDict(TypedDict)
        layers: Required[list[depth_i]]
        top_el: NotRequired[float]
        water_table_el: NotRequired[float]"""

    # only add the soil materials ONCE
    iter_soil_layer_materials_list = iter(layer_soilmat_obj_list)

    for borehole_idx, (coords, borehole_info_dict) in enumerate(boreholes_dict.items()):
        borehole_g = g_i.borehole(*coords)
        for layer_th in borehole_info_dict["layers"]:
            g_i.soillayer(borehole_g, layer_th)
        # materials are only iterated over once here
        add_soil_layer_materials(iter_soil_layer_materials_list)
        borehole_g.Head = borehole_info_dict.get("water_table_el", 0)
        if top_el := borehole_info_dict.get("top_el"):
            for bv_layer_zone_obj in (
                getattr(g_i, f"BVLayerZone_{n + 1}")
                for n in range(len(layer_soilmat_obj_list))
            ):
                bv_layer_zone_obj.Top = top_el
                for layer_th in borehole_info_dict["layers"]:
                    bv_layer_zone_obj.Bottom = top_el - layer_th


def add_box(
    x,
    y,
    z,
    width,
    height,
    axis1,
    axis2=(0, 0, 1),
):
    """Add a rectangular Surface/Polygon. The x, y, z is the top center of the box:

     __o__   <---- top center
    | box |
    |_____|
    """

    xi = x + width / 2
    zi = z - height
    select_backfill_curve = g_i.polycurve(
        (xi, y, zi),
        axis1,
        axis2,
        *("line", 90, height),
        *("line", 90, width),
        *("line", 90, height),
        *("line", 90, width),
    )[
        0
    ]  # index 0 because this returns a list of stuff, not just the curve. sigh. Plaxis.
    try:
        return g_i.surface(select_backfill_curve)
    finally:
        g_i.delete(select_backfill_curve)


class PipeStructure(TypedDict):
    pipe: Required[object]
    footing1: NotRequired[object]
    footing2: NotRequired[object]
    select_backfill: NotRequired[object]


def add_pipe_structure(xyz, shape_info_dict, axis1, axis2=(0, 0, 1)) -> PipeStructure:
    results = dict(poly_curve_obj=(poly_curve_obj := g_i.polycurve(xyz, axis1, axis2)))
    for segment_info in shape_info_dict["segments"]:
        _add_segment(poly_curve_obj, segment_info)

    for offset, value in (
        (offset, shape_info_dict.get(offset)) for offset in ("Offset1", "Offset2")
    ):
        if value is not None:
            setattr(poly_curve_obj, offset, value)
    if footing_info_dict := shape_info_dict.get("footing"):
        results.update(
            **add_footing_pair(*xyz, **footing_info_dict, axis1=axis1, axis2=axis2)
        )
    if select_backfill_info_dict := shape_info_dict.get("select_backfill"):
        results.update(
            select_backfill=add_select_backfill(
                *xyz, **select_backfill_info_dict, axis1=axis1, axis2=axis2
            )
        )
    return results


def _add_segment(poly_curve_obj, segment_info):
    segment_info_copy = segment_info.copy()
    add_segment_func = _SEGMENT_ADD_DICT[segment_info_copy.pop("SegmentType")]
    add_segment_func(poly_curve_obj, segment_info_copy)


def _add_arc(poly_curve_obj, segment_info):
    segment_obj = poly_curve_obj.add()
    segment_obj.SegmentType = "Arc"
    segment_obj.ArcProperties.setproperties(*segment_info.items())


def _add_line(poly_curve_obj, segment_info):
    segment_obj = poly_curve_obj.add()
    segment_obj.SegmentType = "Line"
    segment_obj.LineProperties.setproperties(*segment_info.items())


def _add_symmetric_extend(poly_curve_obj, segment_info):
    poly_curve_obj.extendtosymmetryaxis()
    # sometimes this can return multiple segments so...:
    if segment_info:
        raise Exception(
            "Unsupported; the return of an extended polycurve is a tad complex"
        )


def _add_symmetric_close(poly_curve_obj, segment_info):
    poly_curve_obj.symmetricclose()
    # sometimes this can return multiple segments so...:
    if segment_info:
        raise Exception(
            "Unsupported; the return of a closed polycurve is a tad complex"
        )


_SEGMENT_ADD_DICT = dict(
    Arc=_add_arc,
    Line=_add_line,
    SymmetricExtend=_add_symmetric_extend,
    SymmetricClose=_add_symmetric_close,
)


class FootingPair(TypedDict):
    footing1: Required[object]
    footing2: Required[object]


def add_footing_pair(
    x,
    y,
    z,
    span,
    rise,
    width,
    height,
    outside,
    key,
    axis1,
    axis2=(0, 0, 1),
) -> FootingPair:
    """Add footings as a pair of rectangular Surface/Polygons. The x, y, z is the top center of the structure to be
    supported by the footing pair:

              _______o________    <---- top center at o
             /   ^structure^  \
            /                  \
     ______/_____          _____\______
    |  footing2  |        |  footing1  |
    |____________|        |____________|
    """
    dx = span / 2 + outside - width / 2
    zi = z - rise + key
    footing_objs = []
    for plus_or_minus in (lambda lhs: lhs * rhs for rhs in (1, -1)):
        xi = x + plus_or_minus(dx)
        footing_box = add_box(xi, y, zi, width, height, axis1, axis2)
        footing_objs.append(footing_box)
    footing_pair = dict(zip(("footing1", "footing2"), footing_objs))
    return footing_pair


def add_select_backfill(
    x,
    y,
    z,
    width,
    height,
    h_min,
    axis1,
    axis2=(0, 0, 1),
):
    zi = z + h_min
    return add_box(x, y, zi, width, height, axis1, axis2)


class phase:
    """Phase function decorator that returns tree node leading to subsequent phase nodes.

    Phase function sequence required to be in the form of:

    @phase()
    def phase_0(phase_obj):
        '''Initial Phase'''
        ...

    @phase(phase_1)
    def phase_1(phase_obj):
        '''Phase 1'''
        ...
    """

    def __init__(self, parentphase=None):
        self.parentphase = parentphase
        self.children = []  # references to other nodes
        if parentphase is not None:
            parentphase.children.append(self)

    def traverse(self):
        # moves through each node referenced from self downwards
        nodes_to_visit = [self]
        while len(nodes_to_visit) > 0:
            yield (current_node := nodes_to_visit.pop())
            nodes_to_visit += current_node.children

    def __call__(self, func):
        self.func = func
        return self

    def process_phase_tree(self):
        if self.parentphase is not None:
            raise phase.PhaseException("Can only process starting with initial phase.")
        for p in self.traverse():
            # add phase to plaxis
            p.phase_obj = (
                g_i.Phases[0]
                if p.parentphase is None
                else g_i.phase(p.parentphase.phase_obj)
            )
            # run phase setup
            p.func(p.phase_obj)

    class PhaseException(Exception):
        ...


def _g_i_method(method_name):
    """Used to delay calls to g_i method until after it's been initialized."""

    def wrapped(*args, **kwargs):
        return getattr(g_i, method_name)(*args, **kwargs)

    return wrapped


MATERIAL_TYPE_DICT = dict(
    linear_elastic_soil=(_g_i_method("soilmat"), linear_elastic_soil.soilmat_kwargs),
    duncan_selig=(_g_i_method("soilmat"), duncan_selig.soilmat_kwargs),
    duncan_selig_interpolated=(
        _g_i_method("soilmat"),
        duncan_selig.soilmat_interpolated_kwargs,
    ),
    plate=(_g_i_method("platemat"), plate.platemat_kwargs),
)


def material_creator(type_name, *args, **kwargs):
    """Makes a material creator function.
    Creator tries to load it using an existing canned material. Makes a new one using *args otherwise.
    """

    def create_material():
        xxxmat, get_xxxmat_kwargs = MATERIAL_TYPE_DICT[type_name]
        soilmat_kwargs = get_xxxmat_kwargs(*args, **kwargs)
        return xxxmat(*soilmat_kwargs.items())

    return create_material


def skew_extrude(cross_section_obj, skew, lengths=None, xyz_vectors=None):
    """The cross_section_obj needs to be carefully supplied because this function assumes it is oriented in a
    "positive" direction, and is a "regular", symmetrical type of object - no weird shapes.

    When walking forward, left turns are positive skew, right turns are negative skew.

         Negative skew --> __________
                          /
    Forward -->  ________/<--- Positive skew
    """


def extrude(to_extrude, length=None, vector: Vector_co = None):
    """Plaxis-extrude valid Plaxis objects (individual or lists/groups).

    Supply either:
    1) a vector direction and extrude length
    2) just a vector representing the direction and length
    3) just a length and derive the direction from the Plaxis objects (not yet supported)
    """

    xyz_vector = Vector(*vector)
    if xyz_vector is None:
        raise NotImplementedError("will support grabbing xyz_vector later")
    vec_magnitude = xyz_vector.magnitude
    if (center_length := length) is None:
        center_length = vec_magnitude
    xyz_direction = xyz_vector / vec_magnitude
    xyz_extrude = xyz_direction * center_length
    extruded_obj: list | object = list(
        grp := g_i.group(g_i.extrude(to_extrude, xyz_extrude))
    )
    g_i.ungroup(grp)
    # exclude non-Geometry entities (e.g., Soil)
    return [obj for obj in extruded_obj if obj in g_i.Geometry]


def cut(to_cut_obj, cutter_obj) -> list:
    """Used to "cut" an object or group of objects using a "cutter" object.

    Returns just the pieces of to_cut_obj.
    """
    if cutter_obj not in g_i.Surfaces:
        raise TypeError("cutter_obj must be a Polygon or Surface")
    # collection of the all the results of intersect actions
    cut_list = []
    # use group() to handle the case of 1 or multiple objects
    group_to_cut = g_i.group(to_cut_obj)
    # intersect with cutter_obj one item at a time (in case any items overlap)
    for obj in group_to_cut:
        intersect_result = g_i.intersect(obj, cutter_obj, True)
        cut_list.extend(intersect_result)
    # remove the group(); no longer needed
    g_i.ungroup(group_to_cut)
    # only need geometry objects (not interested in Soil objects)
    cut_geometries = [obj for obj in cut_list if obj in g_i.Geometry]
    # the cut_list includes pieces of cutter_obj and/or copies of cutter_obj itself
    # remove these undesired pieces:
    for intersect_result in cut_geometries[:]:
        # assume all undesired pieces are in Surfaces
        if intersect_result in g_i.Surfaces:
            # intersect the piece with cutter_obj
            sub_intersect_result = g_i.group(
                g_i.intersect(intersect_result, cutter_obj, True)
            )
            # decide if the intersect_result should be removed from cut_geometries
            if len(sub_intersect_result) > 1:
                # more than 1 item means there could be an item to remove
                # recombine the two items and then try to merge them with the cutter_obj
                recombined_grp = g_i.group(g_i.combine(sub_intersect_result, True))
                merged = g_i.mergeequivalents(cutter_obj, recombined_grp)
                try:
                    if merged == "No equivalent geometric objects found":
                        raise Exception()
                except Exception:
                    # merge failed; the piece was NOT part of the cutter_obj
                    g_i.delete(recombined_grp)
                    continue
                else:
                    # merge succeeded; the piece was part of the cutter_obj
                    g_i.delete(intersect_result)
                    cut_geometries.remove(intersect_result)
                finally:
                    g_i.delete(sub_intersect_result)
            else:
                # only 1 item means the piece is the same geometry as the cutter_obj
                g_i.delete(intersect_result)
                cut_geometries.remove(intersect_result)
                g_i.delete(sub_intersect_result)
    return cut_geometries


def copy(to_copy_obj):
    return g_i.combine(to_copy_obj, to_copy_obj, True)


def cog(obj):
    cog_obj = obj.CenterOfGravity
    return Point(*(floatify(v) for v in (cog_obj.x, cog_obj.y, cog_obj.z)))


def rotate(obj, angle, vector):
    result = g_i.arrayp(obj, *vector, angle, 2, True)
    g_i.delete(obj)
    return result


def translate(obj, vector):
    result = g_i.arrayr(obj, 2, *vector)
    g_i.delete(obj)
    return result


def skew_cut(
    to_cut_obj,
    cutter_obj,
    skew_deg: float,
    xy_direction: tuple[float, float],
) -> list:
    """Used to "skew cut" an object or group of objects using a "cutter" object. The cutter is assumed to be a plane
    whose altitude is the z-axis.

    The pieces "forward" of the cutter are deleted.
    """
    if abs(skew_deg) >= 180:
        raise ValueError("Skew cutting is limited to 180 degrees")
    cog_xy_cutter = cog(cutter_obj)[:2]
    rotated_cutter = rotate(
        cutter_obj, skew_deg, ((*cog_xy_cutter, 0), (*cog_xy_cutter, 1))
    )
    cut_results = cut(to_cut_obj, rotated_cutter)
    # eliminate objects "forward" of cutter in xy_direction
    if len(cut_results) % 2 != 0:
        raise ValueError(
            f"cutter_obj did not cut into even number of pieces and this is not supported"
        )
    results_copy = cut_results[:]
    keeps = []
    for cut_pair in (
        results_copy[idx : idx + 2] for idx in range(0, len(results_copy), 2)
    ):
        keep = []
        discard = []
        cog_xy_pair = tuple(cog(obj)[:2] for obj in cut_pair)
        for point, obj in zip(cog_xy_pair, cut_pair):
            vec_difference = Vector.__sub__((*point, 0), (*cog_xy_cutter, 0))
            normal = Vector.rotate_z((*xy_direction, 0), skew_deg)
            # if the dot product is +, the point is "in front"
            if (dot_product := np.dot(normal, vec_difference)) < 0:
                keep.append(obj)
            elif dot_product > 0:
                discard.append(obj)
        if len(keep) == 1 and len(discard) == 1:
            keeps.append(keep[0])
            g_i.delete(discard[0])
        else:
            raise ValueError("the front piece to be removed could not be determined")
    fronts_grp = g_i.group(keeps)
    try:
        return keeps[0] if len(fronts_grp) == 1 else keeps
    finally:
        g_i.ungroup(fronts_grp)


def _skew_cut_arbitrary(
    to_cut_obj,
    skew_deg: float,
    cut_2d_definition: D2Point_co | D2PointPair_co,
    direction: tuple[float, float] | None = None,
) -> list:
    group_obj: Sequence = g_i.group(to_cut_obj)
    cut_obj_bounding_box = BoundingBox.from_plx(group_obj)
    p_min_z = cut_obj_bounding_box.p_min.z
    p_max_z = cut_obj_bounding_box.p_max.z

    # create bounding_box containing the center of the cutter
    match cut_2d_definition, direction:
        # 2d line segment case for creating the cutter
        case ((p_min_x, p_min_y), (p_max_x, p_max_y)), None:
            # todo check to see if segment end points compatible with group_obj..?
            ...
        # center point and direction case for creating the cutter
        case (p_center_x, p_center_y), (direction_x, direction_y):
            # todo check to see if center compatible with group_obj
            # max x distance between center x and x bounds of cut_obj_bounding_box
            dx_max = max(
                p_center_x - cut_obj_bounding_box.p_min.x,
                cut_obj_bounding_box.p_max.x - p_center_x,
            )
            # max y distance between center y and y bounds of cut_obj_bounding_box
            dy_max = max(
                p_center_y - cut_obj_bounding_box.p_min.y,
                cut_obj_bounding_box.p_max.y - p_center_y,
            )
            cut_obj_bounding_box_recentered = BoundingBox.from_min_max(
                (
                    p_center_x - dx_max,
                    p_center_y - dy_max,
                    p_min_z,
                ),
                (
                    p_center_x + dx_max,
                    p_center_y + dy_max,
                    p_max_z,
                ),
            )

            bounding_box = BoundingBox.from_min_max(p_min, p_max)

        case invalid_with_direction, (direction_x, direction_y):
            raise TypeError("direction not needed when bounding box provided")
        case invalid_without_direction, None:
            raise TypeError("center point supplied but missing direction argument")
        case _:
            raise TypeError()

    # create the cutter from the bounding_box
    cutter_angle_deg = skew_deg / 2
    cut_obj_bounding_box.width * (1 / cos(radians(cutter_angle_deg)) - 1)
    required_box_stretch = 0
    cutter_line = (
        BoundingBox.from_min_max(*bounding_box)
        .resized(required_box_stretch)
        .rotated(cutter_angle_deg)
    )
    cutter_obj = g_i.surface(points(cutter_line))
    cut(to_cut_obj, cutter_obj)
    # todo delete the extraneous objects
    g_i.ungroup(group_obj)
