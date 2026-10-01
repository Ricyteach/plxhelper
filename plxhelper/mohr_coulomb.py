"""helpers for mohr coulomb soil materials and objects"""
from math import asin, degrees

import pandas as pd
import pathlib

from scipy.special import sindg, cosdg

tsv_path = pathlib.Path(__file__).parent / "tsv"


def build_mohr_coulomb_soil_dataframe():
    mohr_coulomb_path = tsv_path / "mohr_coulomb_soil.tsv"

    df = pd.read_csv(mohr_coulomb_path, delimiter="\t", index_col=[0, 1])

    df.columns.name = "Parameter"

    return df


# dataframe for various mohr coulomb soil types
MOHR_COULOMB_SOIL_DATAFRAME = build_mohr_coulomb_soil_dataframe()


def soilmat_kwargs(*mohr_coulomb_soil_type_args, **kwargs):
    if mohr_coulomb_soil_type_args:
        soilmat_dict = (
            MOHR_COULOMB_SOIL_DATAFRAME.loc[mohr_coulomb_soil_type_args]
            .squeeze()
            .to_dict()
        )
    else:
        soilmat_dict = {}
    soilmat_dict.update(*kwargs)
    return soilmat_dict


def phi_and_c_from_fc(fc, fraction_tensile):
    """compute phi angle and cohesion for mohr-coulomb failure enveloped based on the compression strength (fc) and
    fraction of tensile strength of a material."""
    # todo: incorporate this into another mohr-coulomb type

    s_1 = fc/2
    s_2 = fraction_tensile * s_1
    sigma_m1 = -s_1
    sigma_m2 = s_2
    phi_deg = degrees(asin((s_1-s_2)/(sigma_m2-sigma_m1)))
    c = (s_1 + sigma_m1 * sindg(phi_deg)) / cosdg(phi_deg)
    return phi_deg, c
