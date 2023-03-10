'''Utils

Module to store all transversal utility functions
'''
import os, sys
import pandas as pd
from functools import wraps
from pathlib import Path
from numpy import ceil
import time


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


def timeit(func):
    '''
    Wrapper to measure time
    '''
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        #print(f'Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds')
        print(f'Function {func.__name__} Took {total_time:.4f} seconds')
        return result
    return timeit_wrapper


def get_project_root() -> Path:
    return Path(__file__).parent


@timeit
def process_etapas_blocks(path_dat):
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
        block2day.groupby(["Month", "Block"]).size().reset_index(name="Block_Len")
    )
    blo_eta = pd.merge(plpetapas, block_len, on=["Month", "Block"])
    blo_eta = blo_eta.sort_values(by=["Etapa"])
    tasa = plpetapas["Tasa"]
    return blo_eta, tasa, block2day


def input_path(file_descrption):
    file_path = input('Enter a file path for %s: ' % file_descrption)
    file_path = file_path.replace('"','')
    # e.g. C:\Users\Bob\Desktop\example.txt
    # or /home/Bob/Desktop/example.txt
    print(file_path)

    if os.path.exists(file_path):
        print('The file %s exists' % file_path)
    else:
        print('The specified file does NOT exist')
    return Path(file_path)


def check_is_file(path):
    if not path.is_file():
        sys.exit("file %s does not exist" % path)


def check_is_path(path):
    if not path.exists():
        sys.exit("Dat path is not valid: %s" % path)
    return path


def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return Path(arg)
