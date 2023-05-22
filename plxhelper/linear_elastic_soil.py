"""helpers for linear elastic soil materials and objects"""

import pandas as pd
import numpy as np
import pathlib

tsv_path = pathlib.Path(__file__).parent / "tsv"


def build_linear_elastic_soil_dataframe():
    linear_elastic_path = tsv_path / "linear_elastic_soil.tsv"

    df = pd.read_csv(linear_elastic_path, delimiter="\t", index_col=[0, 1])

    df.columns.name = "Parameter"

    return df


# dataframe for various linear elastic soil types
LINEAR_ELASTIC_SOIL_DATAFRAME = build_linear_elastic_soil_dataframe()


def soilmat_kwargs(*linear_elastic_soil_type_args, **kwargs):
    if linear_elastic_soil_type_args:
        soilmat_dict = (
            LINEAR_ELASTIC_SOIL_DATAFRAME.loc[linear_elastic_soil_type_args]
            .squeeze()
            .to_dict()
        )
    else:
        soilmat_dict = {}
    soilmat_dict.update(*kwargs)
    return soilmat_dict
