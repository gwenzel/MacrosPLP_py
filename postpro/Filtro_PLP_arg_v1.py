'''Filtro PLP Windows

Module to turn PLP outputs to Engie Format, to be used in other models and
visualizers.

These modules should be pasted in the project folder before being ran
'''
from argparse import ArgumentParser
import shutil
from pathlib import Path
import pandas as pd
from functools import wraps
import traceback
from numpy import ceil

from marginal_costs import marginal_costs_converter
from generation import generation_converter
from transmission import transmission_converter
from fail import fail_converter


# Hidrologías en Hyd med
# N_HYD = 20
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

BLO2DAY_HOURS = [
    "Hour", "1", "2", "3", "4", "5", "6",
    "7", "8", "9", "10", "11", "12"
]


def process_etapas_blocks(path_dat: Path, droptasa: bool = True) -> tuple[
        pd.DataFrame, pd.Series, pd.DataFrame]:
    '''
    Get blocks to etapas definition and tasa
    '''
    plpetapas = pd.read_csv(path_dat / PLPETA_NAME)
    n_blo = plpetapas['Block'].max()
    plpetapas["Tasa"] = 1.1 ** (
        (ceil(plpetapas["Etapa"] / n_blo) - 1) / 12
        )
    block2day = pd.read_csv(path_dat / PLPB2D_NAME)
    block2day = block2day.rename(columns=BLO2DAY_COLS)
    block2day = block2day.loc[:, BLO2DAY_HOURS].melt(
        id_vars="Hour", var_name="Month", value_name="Block"
    )
    block2day["Month"] = pd.to_numeric(block2day["Month"])
    block2day["Hour"] = pd.to_numeric(block2day["Hour"])

    block_len = (
        block2day.groupby(
            ["Month", "Block"]).size().reset_index(name="Block_Len")
    )
    blo_eta = pd.merge(plpetapas, block_len, on=["Month", "Block"])
    blo_eta = blo_eta.sort_values(by=["Etapa"])
    blo_eta = blo_eta.reset_index(drop=True)
    tasa = plpetapas["Tasa"]
    # Drop Tasa from blo_eta if not needed
    if droptasa:
        blo_eta = blo_eta.drop(['Tasa'], axis=1)
    return blo_eta, tasa, block2day


def define_directories(wDir):
    '''
    Build main folder structure
    '''
    # Directorios y carpetas
    here = wDir
    path_dat = Path(here) / "Dat"
    path_out = Path(here) / "OutPLP2M"

    path_out.mkdir(parents=True, exist_ok=True)

    return path_dat, path_out


def define_arg_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Get Filter PLP input filepath")
    parser.add_argument(
        "-w", "--working_directory", help="Working directory",
        required=True, dest="wDir", type=str)
    return parser


def check_is_path(path: Path):
    if not path.exists():
        print("Path is not valid: %s" % path)
        path.mkdir(parents=True, exist_ok=True)
        print("Path was created: %s" % path)


def main():
    '''
    Main routine
    '''
    print('--Starting Filter PLP script')
    try:
        parser = define_arg_parser()
        args = parser.parse_args()

        # Define paths and files, and check
        wDir = Path(args.wDir)
        check_is_path(wDir)
        path_dat, path_out = define_directories(wDir)

        # Block - Etapa definition
        print('Processing Blocks and Stages (0/4)')
        blo_eta, _, _ = process_etapas_blocks(path_dat, droptasa=False)

        # Marginales
        print('Processing Marginal Costs (1/4)')
        marginal_costs_converter(wDir, path_out, blo_eta)

        # Generation
        print('Processing Generation (2/4)')
        generation_converter(wDir, path_out, blo_eta)

        # Transmission
        print('Processing Transmission (3/4)')
        transmission_converter(wDir, path_out, blo_eta)

        # Fallas
        print('Processing Failures (4/4)')
        fail_converter(wDir, path_out, blo_eta)

        # Copiar salidas extras
        shutil.copy(wDir / "plpfal.csv", path_out)
        shutil.copy(wDir / "plpplanos.csv", path_out)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        print('Process finished with errors. Check above for details')
    else:
        print('Process finished successfully')

    print('--Finished Filter PLP script')


if __name__ == "__main__":
    main()
