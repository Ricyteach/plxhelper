"""helpers for duncan-selig parameter specific hardening soil materials and objects"""

import pandas as pd
import numpy as np
import pathlib

tsv_path = pathlib.Path(__file__).parent / "tsv"

# currently supported soil types - can add ML, CL, etc later
soil_types = ["SW"]


def build_Ms_dataframe():
    df_list = []
    Ms_dataframes_path = tsv_path / "Ms"

    for soil_type in soil_types:
        for Ms_tsv_file in Ms_dataframes_path.glob(f"{soil_type}*.tsv"):
            # print(f"Loading {Ms_tsv_file!s}...")
            df_list.append(
                pd.read_csv(
                    Ms_tsv_file,
                    header=0,
                    names=[Ms_tsv_file.stem],
                    delimiter="\t",
                    index_col=0,
                )
            )  # np.genfromtxt(Ms_tsv_file, delimiter="\t", names=True)

    df = pd.concat(df_list, axis=1)
    df.columns.name = "Ms (psi)"
    df.index.name = "σz (psi)"

    return df


# dataframe for Ms with increasing stress of each d-s soil type
Ms_DATAFRAME = build_Ms_dataframe()


def build_duncan_selig_dataframe():
    hardening_soil_duncan_selig_path = tsv_path / "hardening_soil_duncan_selig.tsv"

    df = pd.read_csv(
        hardening_soil_duncan_selig_path, delimiter="\t", index_col=[0, 1]
    )  # np.genfromtxt(Ms_tsv_file, delimiter="\t", names=True)

    df.columns.name = "Parameter"

    return df


# dataframe for interpolating plaxis hyperbolic soil parameters at custom density
DUNCAN_SELIG_INTERPOLATION_DATAFRAME = build_duncan_selig_dataframe()
# dataframe for plaxis hyperbolic soil parameters of each duncan selig soil type (canned densities)
DUNCAN_SELIG_DATAFRAME = DUNCAN_SELIG_INTERPOLATION_DATAFRAME.set_index(
    "Identification", drop=False
)


def build_hardening_soil_parameters(duncan_selig_soil_type, Ms_psi, σ_z_psi):
    """Create the interpolated parameters for a hardening soil model from:
    - soil_type (SW, CL, or ML)
    - Ms_psi (secant constrained modulus)
    - σ_z_psi (overburden pressure at springline of pipe)
    """
    # Lookup effective Ms values for given soil type at each compaction level
    Ms_soil_type_series = Ms_DATAFRAME.loc[round(-σ_z_psi, 1)]

    # Associate Ms with relative densities
    Ms_with_density_series = pd.Series(
        Ms_soil_type_series.index.str[2:].astype(float),
        index=Ms_soil_type_series,
        name="Density",
    )

    ## Interpolate relative density (ie, compaction level) for given Ms value

    # add row for target Ms and set density to nan
    Ms_with_density_series.loc[Ms_psi] = np.nan

    # sort, interpolate numerical values, obtain relative density for target Ms
    ρ_rel = (
        Ms_with_density_series.sort_index()
        .interpolate(method="piecewise_polynomial", order=1, axis=0)
        .loc[Ms_psi]
    )

    # interpolate Hardening Soil model parameters based on relative density
    interpolation_dataframe = DUNCAN_SELIG_INTERPOLATION_DATAFRAME.loc[
        duncan_selig_soil_type
    ]
    interpolation_dataframe.loc[ρ_rel] = interpolation_dataframe.iloc[
        0
    ]  # copy non-numerical values (will replace numerical)
    interpolation_dataframe.at[ρ_rel, "Identification"] = (
        duncan_selig_soil_type + f"{ρ_rel:.1f}"
    )  # update model name
    # return duncan_selig_soil_type_dataframe.loc[ρ_rel, duncan_selig_soil_type_dataframe.select_dtypes(np.number).columns]
    interpolation_dataframe.loc[
        ρ_rel, interpolation_dataframe.select_dtypes(np.number).columns
    ] = np.nan  # clear numerical values

    interpolated_row = (
        interpolation_dataframe.sort_index()  # sort
        .interpolate(
            method="piecewise_polynomial", order=1, axis=0
        )  # interpolate numerical values
        .loc[ρ_rel]  # grab interpolated row
    )
    return interpolated_row


def soilmat_interpolated_kwargs(*duncan_selig_soil_type_args, **kwargs):
    if duncan_selig_soil_type_args:
        assert duncan_selig_soil_type_args[0] in ["SW", "ML", "CL"]
        soilmat_dict = (
            build_hardening_soil_parameters(*duncan_selig_soil_type_args)
            .squeeze()
            .to_dict()
        )
    else:
        soilmat_dict = {}
    soilmat_dict.update(**kwargs)
    return soilmat_dict


def soilmat_kwargs(*duncan_selig_soil_type_args, **kwargs):
    if duncan_selig_soil_type_args:
        assert duncan_selig_soil_type_args[0][:2] in ["SW", "ML", "CL"]
        soilmat_dict = (
            DUNCAN_SELIG_DATAFRAME.loc[duncan_selig_soil_type_args].squeeze().to_dict()
        )
    else:
        soilmat_dict = {}
    soilmat_dict.update(*kwargs)
    return soilmat_dict
