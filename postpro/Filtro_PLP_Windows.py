'''Filtro PLP Windows

Module to turn PLP outputs to Engie Format, to be used in other models and visualizers.

These modules should be pasted in the project folder before being ran
'''
import os
import shutil
from pathlib import Path
from numpy import ceil
import pandas as pd


from postpro.utils import timeit
from postpro.marginal_costs import marginal_costs_converter
from postpro.generation import generation_converter
from postpro.transmission import transmission_converter
from postpro.fail import fail_converter


# Hidrologías en Hyd med
N_HYD = 20
N_BLO = 12
CASE_ID = 1
# Archivo de etapas y block2day
PLPETA_NAME = "plpetapas.csv"
PLPB2D_NAME = "block2day.csv"

BLO2DAY_COLS = {
    "jan": "1",
    "feb": "2",
    "mar": "3",
    "apr": "4",
    "may": "5",
    "jun": "6",
    "jul": "7",
    "aug": "8",
    "sep": "9",
    "oct": "10",
    "nov": "11",
    "dec": "12",
    "Hour2Blo": "Hour",
}
BLO2DAY_HOURS = ["Hour", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]


@timeit
def define_directories():
    '''
    Build main folder structure
    '''
    # Directorios y carpetas
    here = os.getcwd()
    path_dat = Path(here) /  "Dat"
    path_sal = Path(here) / "Sal"
    sal_folders = os.listdir(path_sal)
    g = here.rsplit(os.path.sep, 1)
    res_name = g[1].split(os.path.sep)[-1]

    Path(here, res_name).mkdir(parents=True, exist_ok=True)

    # Choose case based on folder location
    case_name = sal_folders[CASE_ID]
    path_out = Path(here) / res_name / case_name
    path_case = Path(path_sal) / case_name

    return path_dat, path_sal, path_out, path_case


@timeit
def process_etapas_blocks(path_dat):
    '''
    Get blocks to etapas definition and tasa
    TO DO CHECK
    '''
    plpetapas = pd.read_csv(path_dat / PLPETA_NAME)
    plpetapas["Tasa"] = 1.1 ** ((ceil(plpetapas["Etapa"] / N_BLO) - 1) / 12)

    block2day = pd.read_csv(path_dat / PLPB2D_NAME)
    block2day = block2day.rename(columns=BLO2DAY_COLS)
    block2day = block2day.loc[:, BLO2DAY_HOURS].melt(
        id_vars="Hour", var_name="Month", value_name="Block"
    )
    block2day["Month"] = pd.to_numeric(block2day["Month"])
    block2day["Hour"] = pd.to_numeric(block2day["Hour"])

    block_len = (
        block2day.groupby(["Month", "Block"]).size().reset_index(name="Block_Len")
    )
    blo_eta = pd.merge(plpetapas, block_len, on=["Month", "Block"])
    tasa = plpetapas["Tasa"]
    return blo_eta, tasa


@timeit
def main():
    '''
    Main routine
    '''
    path_dat, _, path_out, path_case = define_directories()

    # Block - Etapa definition
    blo_eta, tasa = process_etapas_blocks(path_dat)

    # Marginales
    marginal_costs_converter(path_case, path_out, blo_eta)

    # Generation
    generation_converter(path_case, path_out, blo_eta, tasa)

    # Transmission
    transmission_converter(path_case, path_out, blo_eta)

    # Fallas
    fail_converter(path_case, path_out, blo_eta)

    # Copiar salidas extras
    shutil.copy(path_case / "plpfal.csv", path_out)
    shutil.copy(path_case / "plpplanos.csv", path_out)



if __name__ == "__main__":
    main()
