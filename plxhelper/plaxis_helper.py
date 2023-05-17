"""helpers for creating Plaxis 3D projects"""

from plxscripting.easy import new_server
import plxhelper.linear_elastic_soil as linear_elastic_soil
import plxhelper.duncan_selig as duncan_selig
import plxhelper.plate as plate


def connect_server():
    global s_i, g_i
    s_i, g_i = new_server(address='localhost', port=10000, password='python')


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
            for bv_layer_zone_obj in (getattr(g_i, f"BVLayerZone_{n + 1}") for n in range(len(layer_soilmat_obj_list))):
                bv_layer_zone_obj.Top = top_el
                for layer_th in borehole_info_dict["layers"]:
                    bv_layer_zone_obj.Bottom = top_el - layer_th


def add_pipe(xyz, xyz_direction, shape_info_dict):
    poly_curve_obj = g_i.polycurve(xyz, *xyz_direction)
    for segment_info in shape_info_dict["segments"]:
        _add_segment(poly_curve_obj, segment_info)
    return poly_curve_obj


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
        raise Exception("Unsupported; the return of an extended polycurve is a tad complex")


def _add_symmetric_close(poly_curve_obj, segment_info):
    poly_curve_obj.symmetricclose()
    # sometimes this can return multiple segments so...:
    if segment_info:
        raise Exception("Unsupported; the return of a closed polycurve is a tad complex")


_SEGMENT_ADD_DICT = dict(
    Arc=_add_arc,
    Line=_add_line,
    SymmetricExtend=_add_symmetric_extend,
    SymmetricClose=_add_symmetric_close,
)


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
            yield current_node := nodes_to_visit.pop()
            nodes_to_visit += current_node.children

    def __call__(self, func):
        self.func = func
        return self

    def process_phase_tree(self):
        if self.parentphase is not None:
            raise phase.PhaseException("Can only process starting with initial phase.")
        for p in self.traverse():
            # add phase to plaxis
            p.phase_obj = (g_i.Phases[0] if p.parentphase is None else g_i.phase(p.parentphase.phase_obj))
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
    duncan_selig_interpolated=(_g_i_method("soilmat"), duncan_selig.soilmat_interpolated_kwargs),
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
