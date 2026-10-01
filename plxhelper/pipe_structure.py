from __future__ import annotations
from typing import Generic, TypedDict, Required, NotRequired
from scipy.special import tandg

from plxhelper.pipe import ContinuousPipeProfileABC
from plxhelper.plaxis_helper import add_box, add_isosceles_trapezoid, connect_server

connect_server()

from plxhelper.plaxis_helper import g_i


class PipeStructure:
    pipe_list: list[ContinuousPipeProfileABC]
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
        if backfill_info_dict := shape_info_dict.get("backfill"):
            results.update(
                backfill=add_backfill(
                    *xyz, **backfill_info_dict, axis1=axis1, axis2=axis2
                )
            )
        if select_backfill_info_dict and backfill_info_dict:
            backfill = results["backfill"]
            select_backfill = results["select_backfill"]
            backfill_polygons = g_i.intersect(backfill, select_backfill)
            if len(backfill_polygons) != 2:
                raise ValueError("Backfill and select backfill geometry incompatible")
            results["backfill"] = backfill_polygons[0]
            results["select_backfill"] = backfill_polygons[1]
        return results

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

    def add_backfill(
        x,
        y,
        z,
        h_cover,
        short_width,
        slopes_deg,
        height,
        axis1,
        axis2=(0, 0, 1),
    ):
        zi = z + h_cover
        long_width = short_width + 2 * (height / tandg(slopes_deg))
        return add_isosceles_trapezoid(x, y, zi, short_width, long_width, height, axis1, axis2)

    def slice_pipe_structure_soil(shape_info_dict, pipe_structure: PipeStructure, lift_thickness: float):
        if select_backfill_info_dict := shape_info_dict.get("select_backfill"):
            min_cover = select_backfill_info_dict["min_cover"]


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
