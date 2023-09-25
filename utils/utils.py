'''Utils

Module to store all transversal utility functions
'''
import os
from calendar import monthrange
from typing import TypedDict
import pandas as pd
from functools import wraps
from pathlib import Path
from numpy import ceil
from argparse import ArgumentParser
from shutil import copyfile
import time
from datetime import datetime
from utils.logger import create_logger


logger = create_logger('utils')


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

MONTH_TO_HIDROMONTH = {
    1: 10, 2: 11, 3: 12,
    4: 1, 5: 2, 6: 3,
    7: 4, 8: 5, 9: 6,
    10: 7, 11: 8, 12: 9
}


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
        print(f'Function {func.__name__} Took {total_time:.4f} seconds')
        return result
    return timeit_wrapper


def process_etapas_blocks(path_dat: Path) -> (pd.DataFrame, pd.Series,
                                              pd.DataFrame):
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
    return blo_eta, tasa, block2day


def input_path(file_descrption: str) -> Path:
    file_path = input('Enter a file/path for %s: ' % file_descrption)
    file_path = file_path.replace('"', '')
    # e.g. C:\Users\Bob\Desktop\example.txt
    # or /home/Bob/Desktop/example.txt
    logger.info(file_path)

    if os.path.exists(file_path):
        logger.info('The file/path %s exists' % file_path)
    else:
        logger.error('The specified file/path does NOT exist')
    return Path(file_path)


def check_is_file(path: Path):
    if not path.is_file():
        logger.error("file %s does not exist" % path)


def check_is_path(path: Path):
    if not path.exists():
        logger.warning("Path is not valid: %s" % path)
        path.mkdir(parents=True, exist_ok=True)
        logger.info("Path was created: %s" % path)


def is_valid_file(parser: ArgumentParser, arg: str) -> Path:
    if not os.path.exists(arg):
        parser.error("The file or path %s does not exist!" % arg)
    else:
        return Path(arg)


def define_arg_parser(ext: bool = False) -> ArgumentParser:
    parser = ArgumentParser(description="Get PLP input filepaths")
    parser.add_argument('-f', dest='iplp_path', required=False,
                        help='IPLP input file path',
                        metavar="IPLP_FILE_PATH",
                        type=lambda x: is_valid_file(parser, x))
    if ext:
        parser.add_argument('-e', dest='ext_path', required=False,
                            help='External inputs path',
                            metavar="EXT_INPUTS_PATH",
                            type=lambda x: is_valid_file(parser, x))
    return parser


def get_iplp_input_path(parser: ArgumentParser) -> Path:
    args = parser.parse_args()
    if args.iplp_path:
        return args.iplp_path
    # Else, get input file from prompt
    iplp_path = input_path("IPLP file")
    check_is_file(iplp_path)
    return iplp_path


def get_ext_inputs_path(parser: ArgumentParser) -> Path:
    args = parser.parse_args()
    if args.ext_path:
        return args.ext_path
    # Else, get external inputs path from prompt
    ext_path = input_path("External inputs path")
    check_is_path(ext_path)
    return ext_path


def remove_blank_lines(text_file: Path):
    temp_file = 'temp.txt'
    # opening and creating new .txt file
    with open(text_file, 'r') as r, open(temp_file, 'w') as o:
        for line in r:
            # if line is not blank after stripping all spaces, keep line
            if line.strip():
                o.write(line)
    copyfile(temp_file, text_file)
    os.remove(temp_file)


def get_list_of_all_barras(iplp_path: Path) -> list:
    df = pd.read_excel(iplp_path, sheet_name="Barras",
                       skiprows=4, usecols="B")
    return df['BARRA'].tolist()


class ScenarioData(TypedDict):
    Demanda: str
    Combustible: str
    Eolico: str


def get_scenarios(iplp_path: Path) -> ScenarioData:
    '''
    Return dictionary with scenario data
    - Demanda: Base, DemHigh, DemLow, Risk_1, Risk_2
    - Combustible: Base, ComHigh, ComLow, Risk_1, Risk_2
    - Eolico: Base, WindLow, WindHigh
    '''

    df = pd.read_excel(iplp_path, sheet_name="Path",
                       skiprows=6, usecols="C:D",
                       header=None)
    df = df.dropna()
    scenario_data = df.set_index(2).to_dict()[3]
    scenario_data.pop('N° Iteraciones')
    return scenario_data


def write_lines_from_scratch(lines: str, filepath: Path):
    f = open(filepath, 'w')
    f.write('\n'.join(lines))
    f.close()


def write_lines_appending(lines: str, filepath: Path):
    f = open(filepath, 'a')
    f.write('\n'.join(lines))
    f.close()


def translate_to_hydromonth(df: pd.DataFrame) -> pd.DataFrame:
    return df.replace({'Month': MONTH_TO_HIDROMONTH})


def append_rows(df: pd.DataFrame, *rows: pd.Series) -> pd.DataFrame:
    '''
    Append row to dataframe using concat to avoid FutureWarning
    '''
    list_of_dfs = [df]
    for row in rows:
        list_of_dfs.append(pd.DataFrame(row).T)
    return pd.concat(list_of_dfs)


def add_time_info(df: pd.DataFrame) -> pd.DataFrame:
    df['YearIni'] = df['INICIAL'].dt.year
    df['MonthIni'] = df['INICIAL'].dt.month
    df['DayIni'] = df['INICIAL'].dt.day
    df['YearEnd'] = df['FINAL'].dt.year
    df['MonthEnd'] = df['FINAL'].dt.month
    df['DayEnd'] = df['FINAL'].dt.day
    return df


def get_daily_indexed_df(blo_eta: pd.DataFrame) -> pd.DataFrame:
    '''
    Get dataframe indexed by day within the timeframe
    '''
    # Get days in last month
    num_days = monthrange(
        blo_eta.iloc[-1]['Year'], blo_eta.iloc[-1]['Month'])[1]
    ini_date = datetime(
        blo_eta.iloc[0]['Year'], blo_eta.iloc[0]['Month'], 1)
    end_date = datetime(
        blo_eta.iloc[-1]['Year'], blo_eta.iloc[-1]['Month'], num_days)
    index = pd.date_range(start=ini_date, end=end_date, freq='D')
    df = pd.DataFrame(index=index, columns=['Year', 'Month', 'Day'])
    df['Year'] = df.index.year
    df['Month'] = df.index.month
    df['Day'] = df.index.day
    df['Date'] = df.index
    df = df.reset_index(drop=True)
    return df
