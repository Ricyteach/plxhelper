import contextlib
from typing import Iterator

from plxhelper.geo import Point_co, Vector_co, Point
from plxhelper.plaxis_helper import add_box, PipeStructure, g_i


class PipePath:
    shape_info_dict: dict
    segment_lengths: list[float]
    angles_deg: list[float]

    def __init__(
        self,
        shape_info_dict: dict,
        extrusion_lengths: list[float],
        angles_deg: list[float],
    ):
        self.shape_info_dict = shape_info_dict
        self.segment_lengths = extrusion_lengths
        self.angles_deg = angles_deg
        self._set_width()
        self._set_height()

    @property
    def extrusion_points(self) -> list[Point]:
        return []

    @property
    def rotation_points(self) -> list[Point]:
        return []

    @property
    def width(self) -> float:
        return self._width

    def _set_width(self):
        self._width = 0

    @property
    def height(self):
        return self._height

    def _set_height(self):
        self._height = 0

    @property
    def cutter(self):
        return self._cutter

    def set_up(self):
        self._cutter = add_box()
        self._pipe_structure = PipeStructure()

    def tear_down(self):
        g_i.delete(self._cutter)
        del self._cutter
        pipe_structure_grp = g_i.group(tuple(self._pipe_structure.values()))
        g_i.delete(pipe_structure_grp)
        del self._pipe_structure

    def add_pipe_path(self, start_point: Point_co, start_direction: Vector_co):
        ...


@contextlib.contextmanager
def _pipe_path(
    shape_info_dict: dict, extrusion_lengths: list[float], angles_deg: list[float]
) -> Iterator[PipePath]:
    pp = PipePath(shape_info_dict, extrusion_lengths, angles_deg)
    pp.set_up()
    yield pp
    pp.tear_down()


def add_pipe_path(
    shape_info_dict: dict,
    extrusion_lengths: list[float],
    angles_deg: list[float],
    start_point: Point_co,
    start_direction: Vector_co = (0, 1, 0),
):
    with _pipe_path(shape_info_dict, extrusion_lengths, angles_deg) as pipe_path_inst:
        pipe_path_inst.add_pipe_path(start_point, start_direction)
