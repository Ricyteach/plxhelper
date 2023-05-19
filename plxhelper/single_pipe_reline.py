"""standard routine for create a single pipe reline project"""

import pandas as pd
from plxhelper.plaxis_helper import connect_server, add_pipe, process_boreholes, phase, new_server, material_creator
from plxhelper.exceptions import PlaxisHelperError
import plxhelper.live_load as live_load


class SinglePipeRelineError(PlaxisHelperError):
    ...


def run_input(xmin, ymin, xmax, ymax, grade_el, h_cover_in, h_parent, h_AVG_in, xyz_live_load, lane_load,
              parent_shape_info_dict, reline_shape_info_dict, boreholes_dict,
              annular_fill_type, soil_layer_materials_list,
              short_term_reline_type, long_term_reline_type):
    connect_server()

    from plxhelper.plaxis_helper import s_i, g_i

    s_i.new()
    g_i.Project.setproperties("UnitForce", "lbf", "UnitLength", "in")
    g_i.SoilContour.initializerectangular(xmin, ymin, xmax, ymax)

    layer_soilmat_obj_list = [material_creator(*soil_layer_material_type)()
                              for soil_layer_material_type in soil_layer_materials_list]
    process_boreholes(boreholes_dict, layer_soilmat_obj_list)

    annular_fill_soilmat_creator = material_creator(*annular_fill_type)
    annular_fill_soilmat_obj = annular_fill_soilmat_creator()

    g_i.gotostructures()

    hl93_tandem_patch_group = live_load.surface_load_group("HL93 Tandem Axle", xyz_live_load)
    hl93_truck_patch_group = live_load.surface_load_group("HL93 Truck Axle", xyz_live_load)

    if lane_load == "AASHTO Lane Load":
        lane_load_width = 120.0

        lane_load_surface = g_i.surface(xmin, -lane_load_width / 2, grade_el,
                                        xmax, -lane_load_width / 2, grade_el,
                                        xmax, lane_load_width / 2, grade_el,
                                        xmin, lane_load_width / 2, grade_el,
                                        )

        lane_load_elastic_platemat_obj = material_creator("plate", lane_load)()

        lane_load_elastic_plate_obj = g_i.plate(lane_load_surface)
        lane_load_elastic_plate_obj.setmaterial(lane_load_elastic_platemat_obj)
    else:
        raise SinglePipeRelineError("unsupported land load type, {lane_load!r}")

    l_parent = (ymax - ymin)  # in
    # draw shape starting at crown z elevation
    z_parent_crown = grade_el - (h_cover_in - (h_parent - h_AVG_in) / 2)

    parent_pipe_curve = add_pipe(xyz=(0, ymin, z_parent_crown), xyz_direction=((1, 0, 0), (0, 0, 1)),
                                 shape_info_dict=parent_shape_info_dict)

    parent_pipe_x_section = g_i.surface(parent_pipe_curve)

    parent_pipe_surface, parent_pipe_volume, _ = g_i.extrude([parent_pipe_curve, parent_pipe_x_section],
                                                             0, l_parent, 0)

    parent_pipe_fixity = g_i.surfdispl(parent_pipe_surface, "Displacement_x", "Fixed",
                                       "Displacement_y", "Fixed", "Displacement_z", "Fixed")

    z_reline_crown = grade_el - h_cover_in

    print(f"z_parent_crown = {z_parent_crown}")
    print(f"z_reline_crown) = {z_reline_crown}")

    reline_pipe_curve = add_pipe(xyz=(0, ymin, z_reline_crown), xyz_direction=((1, 0, 0), (0, 0, 1)),
                                 shape_info_dict=reline_shape_info_dict)

    reline_pipe_surface = g_i.extrude(reline_pipe_curve, 0, l_parent, 0)

    reline_pipe_friction = g_i.neginterface(reline_pipe_surface)

    g_i.setmaterial(reline_pipe_friction, annular_fill_soilmat_obj)

    short_term_platemat_creator = material_creator(*short_term_reline_type)
    long_term_platemat_creator = material_creator(*long_term_reline_type)

    short_term_platemat_obj = short_term_platemat_creator()
    long_term_platemat_obj = long_term_platemat_creator()

    reline_pipe_plate_obj = g_i.plate(reline_pipe_surface)
    reline_pipe_plate_obj.setmaterial(short_term_platemat_obj)

    g_i.gotomesh()
    g_i.mesh("Coarseness", 0.05, "UseEnhancedRefinements", True,
             "EMRGlobalScale", 1.2, "EMRMinElementSize", 0.005, "UseSweptMeshing", False)

    g_i.gotostages()
    cut_parent_pipe_volumes = getattr(g_i, str(parent_pipe_volume.Name))

    void_cut_volume = cut_parent_pipe_volumes[0]
    grout_cut_volume = cut_parent_pipe_volumes[1]

    @phase()
    def initial_dry(phase_obj):
        """Initial Phase"""
        for cut_soil in g_i.Soils:
            cut_soil.WaterConditions.Conditions[phase_obj] = "dry"

    @phase(initial_dry)
    def phase_1(phase_obj):
        """Phase 1 - Excavate, Apply Lane Load and Void Fixities"""
        # deactivate parent pipe volumes
        for cut_parent_pipe_volume in cut_parent_pipe_volumes:
            cut_parent_pipe_volume.deactivate(phase_obj)
        # apply fixity
        getattr(g_i, str(parent_pipe_fixity.Name)).activate(phase_obj)
        getattr(g_i, str(lane_load_elastic_plate_obj.Name)).activate(phase_obj)

    @phase(phase_1)
    def phase_2(phase_obj):
        """Phase 2 - Install Pipe, Friction, Grout"""
        # activate reline pipe, friction, grout soil
        for obj in (reline_pipe_plate_obj, reline_pipe_friction, grout_cut_volume):
            getattr(g_i, str(obj.Name)).activate(phase_obj)
        getattr(g_i, str(grout_cut_volume.Name)).Soil.Material[phase_obj] = annular_fill_soilmat_obj

    @phase(phase_2)
    def phase_3(phase_obj):
        """Phase 3 - Remove Parent Pipe Fixity"""
        # deactivate fixity
        getattr(g_i, str(parent_pipe_fixity.Name)).deactivate(phase_obj)

    @phase(phase_3)
    def phase_4a(phase_obj):
        """Phase 4a - Long Term Dead Load"""
        getattr(g_i, str(reline_pipe_plate_obj.Name)).Material[phase_obj][0] = long_term_platemat_obj

    @phase(phase_4a)
    def phase_5a(phase_obj):
        """Phase 5a - Truck Live Load"""
        for obj in getattr(g_i, str(hl93_truck_patch_group.Name)):
            obj.activate(phase_obj)

    @phase(phase_4a)
    def phase_5b(phase_obj):
        """Phase 5b - Tandem Live Load"""
        for obj in getattr(g_i, str(hl93_tandem_patch_group.Name)):
            obj.activate(phase_obj)

    @phase(phase_3)
    def phase_4b(phase_obj):
        """Phase 4b - Short Term Flood Load"""
        for cut_soil in g_i.Soils:
            if str(void_cut_volume.Name) not in str(cut_soil.Name):
                cut_soil.WaterConditions.Conditions[phase_obj] = 'globallevel'

    initial_dry.process_phase_tree()

    return "stopped before calculation"

    g_i.calculate()

    output_port = g_i.view(phase_5b.phase_obj)
    s_o, g_o = new_server('localhost', port=output_port, password=s_i.connection._password)

    result_columns = dict(
        x=g_o.ResultTypes.Plate.X,
        y=g_o.ResultTypes.Plate.Y,
        z=g_o.ResultTypes.Plate.Z,
        n=g_o.ResultTypes.Plate.N22,
        m=g_o.ResultTypes.Plate.M22,
    )

    results = pd.DataFrame.from_dict({col_name: g_o.getresults(g_o.Plate_2, phase_5b.phase_obj, result_type, "node")
                                      for col_name, result_type in result_columns.items()})
