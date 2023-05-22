"""helpers for plate materials and objects"""

import pandas as pd
import numpy as np
import pathlib

tsv_path = pathlib.Path(__file__).parent / "tsv"


def build_plate_dataframe():
    elastic_path = tsv_path / "plate.tsv"

    df = pd.read_csv(elastic_path, delimiter="\t", index_col=[0, 1, 2])

    df.columns.name = "Parameter"

    return df


# dataframe for various plate types
PLATE_DATAFRAME = build_plate_dataframe()


def platemat_kwargs(*plate_type_args, **kwargs):
    if plate_type_args:
        platemat_dict = (
            PLATE_DATAFRAME.loc[plate_type_args].squeeze().dropna().to_dict()
        )
    else:
        platemat_dict = {}
    platemat_dict.update(*kwargs)
    return platemat_dict
