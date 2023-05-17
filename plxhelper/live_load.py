"""helpers for working with live loads"""

import pandas as pd
import numpy as np
import pathlib
import plxhelper.plaxis_helper as plaxis_helper

tsv_path = pathlib.Path(__file__).parent / "tsv"

def build_live_load_dataframe():
    elastic_path = tsv_path / "live_load.tsv"

    df = pd.read_csv(elastic_path, delimiter="\t", index_col=[0])

    df.columns.name = "Parameter"

    return df

# dataframe for various live loads
LIVE_LOAD_DATAFRAME = build_live_load_dataframe()

def build_patch_dataframe(xyz, df):
    x, y, z = xyz
    df_copy = df.copy()
    df_copy["x"] = df_copy["x"] + x
    df_copy["y"] = df_copy["y"] + y

    result_df = pd.DataFrame(index=df_copy.index, columns=["Pressure", 
                                                           "x1", "y1", "z1", 
                                                           "x2", "y2", "z2", 
                                                           "x3", "y3", "z3",
                                                           "x4", "y4", "z4", ])

    result_df["Pressure"] = df_copy["Load"] / (df_copy["Width"] * df_copy["Length"])

    result_df["x1"] = df_copy["x"] - df_copy["Length"] /2
    result_df["y1"] = df_copy["y"] - df_copy["Width"] /2
    result_df["x2"] = df_copy["x"] + df_copy["Length"] /2
    result_df["y2"] = df_copy["y"] - df_copy["Width"] /2
    result_df["x3"] = df_copy["x"] + df_copy["Length"] /2
    result_df["y3"] = df_copy["y"] + df_copy["Width"] /2
    result_df["x4"] = df_copy["x"] - df_copy["Length"] /2
    result_df["y4"] = df_copy["y"] + df_copy["Width"] /2
    result_df[["z1", "z2", "z3", "z4"]] = z

    return result_df

def _patch_series_to_surface_load_obj(patch_series):
    return plaxis_helper.g_i.surfload(*patch_series["x1":"z4"], "sigz", -patch_series["Pressure"])

def _patch_dataframe_to_surface_load_group(patch_dataframe):
    return plaxis_helper.g_i.group(list(patch_dataframe.loc[:].apply(_patch_series_to_surface_load_obj, axis=1, result_type="expand")[1]))

def surface_load_group(live_load_name, xyz):
    live_load_dataframe = LIVE_LOAD_DATAFRAME.loc[[live_load_name]]
    live_load_dataframe_patch_dataframe = build_patch_dataframe(xyz, live_load_dataframe)
    return _patch_dataframe_to_surface_load_group(live_load_dataframe_patch_dataframe)
