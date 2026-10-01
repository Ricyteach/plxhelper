"""helpers for plate materials and objects"""
from math import log

import pandas as pd
import numpy as np
import pathlib

tsv_path = pathlib.Path(__file__).parent / "tsv"


def build_plate_dataframe():
    elastic_path = tsv_path / "plate.tsv"

    df = pd.read_csv(elastic_path, delimiter="\t", index_col=[0, 1, 2])

    df.columns.name = "Parameter"

    return df


def build_weholite_dataframe():
    weholite_path = tsv_path / "weholite_pipe.tsv"

    df = pd.read_csv(weholite_path, delimiter="\t", index_col=[0, 1], header=[1], skiprows=[2])

    df.columns.name = "Parameter"

    return df


# dataframe for various plate types
PLATE_DATAFRAME = build_plate_dataframe()
WEHOLITE_DATAFRAME = build_weholite_dataframe()


def platemat_kwargs(*plate_type_args, **kwargs):
    if plate_type_args:
        platemat_dict = (
            PLATE_DATAFRAME.loc[plate_type_args].squeeze().dropna().to_dict()
        )
    else:
        platemat_dict = {}
    platemat_dict.update(*kwargs)
    return platemat_dict


HRS_CONVERSION_DICT = dict(
    year=365.25 * 24,
    yr=365.25 * 24,
    y=365.25 * 24,
    day=24,
    dy=24,
    d=24,
    hour=1,
    hr=1,
    h=1,
)


def weholite_long_term_modulus(time, time_unit="yr", short_term_modulus_psi=78000):
    hrs = time * HRS_CONVERSION_DICT[time_unit]
    # best fit quadratic equation for long term moduli; PPI Chapter 3, Table B.1.1, PE3XXX
    k2 = 0.7767
    k1 = -12.414
    k0 = 73.793
    log_hrs = log(hrs)
    if 0.5 <= log_hrs <= 6:
        return k2 * log_hrs ** 2 + k1 * log_hrs + k0
    else:
        raise ValueError(f"{time:.1f} {time_unit!s} out of bounds long term time frame for weholite modulus")


WEHOLITE_TIME_BASED_MODULI = [
    "E1",
    "E2",
    "G12",
    "G13",
    "G23",
]


def weholite_pipe_kwargs(*weholite_pipe_args, **kwargs):
    if weholite_pipe_args:
        platemat_dict = (
            WEHOLITE_DATAFRAME.loc[weholite_pipe_args].squeeze().dropna().to_dict()
        )
    else:
        platemat_dict = {}

    match weholite_pipe_args:
        case [float() | int(), float() | int(), "Short"]:
            weholite_long_term_modulus_args = []
        case [float() | int(), float() | int(), "Long", years]:
            weholite_long_term_modulus_args = [years]
        case [float() | int(), float() | int(), "Long", time, time_unit]:
            weholite_long_term_modulus_args = [time, time_unit]
        case _:
            raise TypeError('invalid weholite pipe arguments')

    for modulus_name in WEHOLITE_TIME_BASED_MODULI:
        short_term_modulus_psi = platemat_dict.get(modulus_name)
        if short_term_modulus_psi is not None and weholite_long_term_modulus_args:
            material_model_modulus = weholite_long_term_modulus(*weholite_long_term_modulus_args, short_term_modulus_psi)
        elif short_term_modulus_psi is not None and not weholite_long_term_modulus_args:
            material_model_modulus = short_term_modulus_psi
        else:
            continue
        platemat_dict[modulus_name] = material_model_modulus

    platemat_dict.update(*kwargs)
    return platemat_dict
