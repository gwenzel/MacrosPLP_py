'''Filtro PLP Windows

Module to turn PLP outputs to Engie Format, to be used in other models and
visualizers.

These modules should be pasted in the project folder before being ran
'''
import os
import shutil
from pathlib import Path


from utils.utils import timeit, process_etapas_blocks
from postpro.marginal_costs import marginal_costs_converter
from postpro.generation import generation_converter
from postpro.transmission import transmission_converter
from postpro.fail import fail_converter


# Hidrologías en Hyd med
# N_HYD = 20
CASE_ID = 1


@timeit
def define_directories():
    '''
    Build main folder structure
    '''
    # Directorios y carpetas
    here = os.getcwd()
    path_dat = Path(here) / "Dat"
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
def main():
    '''
    Main routine
    '''
    path_dat, _, path_out, path_case = define_directories()

    # Block - Etapa definition
    blo_eta, tasa, _ = process_etapas_blocks(path_dat, droptasa=False)

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
