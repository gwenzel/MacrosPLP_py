'''Filtro PLP Windows

Module to turn PLP outputs to Engie Format, to be used in other models and visualizers.

These modules should be pasted in the project folder before being ran
'''
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
import pandas as pd


from utils import timeit
from marginal_costs import process_marginal_costs, process_marginal_costs_monthly, write_marginal_costs_file
from generation import *
from transmission import *
from fail import *



# Hidrologías en Hyd med
N_HYD = 20
N_BLO = 12
CASE_ID = 0
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
    # Directorios y carpetas
    location = os.getcwd()
    path_dat = Path(location) /  "Dat"
    path_sal = Path(location) / "Sal"
    sal_folders = os.listdir(path_sal)
    g = location.rsplit(os.path.sep, 1)
    res_name = g[1].split(os.path.sep)[-1]

    (Path(location) / res_name).mkdir(parents=True, exist_ok=True)
    case_name = sal_folders[CASE_ID]
    path_out = Path(location) / res_name / case_name
    path_case = Path(path_sal) / case_name

    return path_dat, path_sal, path_out, path_case


@timeit
def process_etapas_blocks(path_dat):
    plpetapas = pd.read_csv(path_dat / PLPETA_NAME)
    plpetapas["Tasa"] = 1.1 ** ((plpetapas["Etapa"] // 12 - 1) / 12)

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


if __name__ == "__main__":

    # Tiempo inicial
    t_ini = datetime.now()
    print(t_ini)

    path_dat, path_sal, path_out, path_case = define_directories()

    # Block - Etapa definition
    blo_eta, tasa = process_etapas_blocks(path_dat)

    # Marginales
    bar_data, bar_param = process_marginal_costs(path_case, blo_eta)

    # Data mensual
    cmg_b, dem_b, cmg_m, dem_m = process_marginal_costs_monthly(bar_data)

    # Write files
    write_marginal_costs_file(bar_param, path_out, 'CMg', cmg_b, type = 'B')
    write_marginal_costs_file(bar_param, path_out, 'CMg', cmg_m, type = 'M')
    write_marginal_costs_file(bar_param, path_out, 'Dem', dem_b, type = 'B')
    write_marginal_costs_file(bar_param, path_out, 'Dem', dem_m, type = 'M')

    # Generación
    gen_data, gen_data_m, gen_param = process_gen_data(path_case, blo_eta, tasa)
    Energ_B, Reven_B, CapPrice_B, Curtail_B = process_gen_data_monthly(
        gen_data, type="B"
    )
    Energ_M, Reven_M, CapPrice_M, Curtail_M = process_gen_data_monthly(
        gen_data_m, type="M"
    )

    # remove large data frames
    del gen_data
    del gen_data_m

    # write gen data

    write_gen_data_file(gen_param, path_out, "Energy", Energ_B, type="B")
    write_gen_data_file(gen_param, path_out, "Revenue", Reven_B, type="B")
    write_gen_data_file(gen_param, path_out, "Cap Price", CapPrice_B, type="B")
    write_gen_data_file(gen_param, path_out, "Curtailment", Curtail_B, type="B")
    write_gen_data_file(gen_param, path_out, "Energy", Energ_M, type="M")
    write_gen_data_file(gen_param, path_out, "Revenue", Reven_M, type="M")
    write_gen_data_file(gen_param, path_out, "Cap Price", CapPrice_M, type="M")
    write_gen_data_file(gen_param, path_out, "Curtailment", Curtail_M, type="M")


    # Líneas Transmisión
    lin_data, lin_data_m, lin_param = process_lin_data(path_case, blo_eta)

    LinFlu_B, LinUse_B = process_lin_data_monthly(lin_data, type="B")
    LinFlu_M, LinUse_M = process_lin_data_monthly(lin_data_m, type="M")

    # Write Transmission data

    write_transmission_data(lin_param, path_out, "LinFlu", LinFlu_B, type="B")
    write_transmission_data(lin_param, path_out, "LinFlu", LinFlu_M, type="M")
    write_transmission_data(lin_param, path_out, "LinUse", LinUse_B, type="B")
    write_transmission_data(lin_param, path_out, "LinUse", LinUse_M, type="M")

    # Fallas
    process_and_write_fail_data(path_case, path_out, blo_eta)

    # Copiar salidas extras

    shutil.copy(path_case / "plpfal.csv", path_out)
    shutil.copy(path_case / "plpplanos.csv", path_out)

    # Tiempo final
    t_end = time.time()
    print(t_end)
    t = t_end - t_ini
    print("Process Time: " + str(int(t)) + ":" + str(int(60 * (t - int(t)))))
