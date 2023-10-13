'''
Generate Plexos files in CSV folder
'''

from utils.logger import create_logger
from utils.utils import (define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         get_daily_indexed_df,
                         process_etapas_blocks, read_plexos_end_date)
import pandas as pd
from datetime import datetime
from pathlib import Path

logger = create_logger('csv_plexos')


def get_df_daily_plexos(blo_eta: pd.DataFrame,
                        iplp_path: Path) -> pd.DataFrame:
    plexos_end_date = read_plexos_end_date(iplp_path)
    df_daily = get_daily_indexed_df(blo_eta, all_caps=True)
    year_mask = df_daily.index.get_level_values('YEAR') <= \
        plexos_end_date.year
    return df_daily[year_mask]


def read_centrales_plexos(iplp_path: Path) -> pd.DataFrame:
    df = pd.read_excel(iplp_path, sheet_name="Centrales",
                       skiprows=4, usecols="B,C,AB")
    # Filter out if X
    df = df[df['Tipo de Central'] != 'X']
    df = df.rename(columns={
        'CENTRALES': 'Nombre', 'Máxima.1': 'Pmax'})
    df = df[['Nombre', 'Pmax']]
    return df


def print_generator_files(iplp_path: Path,
                          df_daily: pd.DataFrame):
    df_centrales = read_centrales_plexos(iplp_path)


    pass


def main():
    '''
    Main routine
    '''
    # Get input file path
    logger.info('Getting input file path')
    parser = define_arg_parser()
    iplp_path = get_iplp_input_path(parser)
    path_inputs = iplp_path.parent / "Temp"
    check_is_path(path_inputs)
    path_dat = iplp_path.parent / "Temp" / "Dat"
    check_is_path(path_dat)
    path_df = iplp_path.parent / "Temp" / "df"
    check_is_path(path_df)
    path_pib = iplp_path.parent / "Temp" / "CSV"
    check_is_path(path_pib)

    # Get Hour-Blocks-Etapas definition
    logger.info('Processing block to etapas files')
    blo_eta, _, _ = process_etapas_blocks(path_dat)
    blo_eta = blo_eta.drop(['Tasa'], axis=1)

    df_daily = get_df_daily_plexos(blo_eta, iplp_path)
    year_ini = df_daily['YEAR'][0]

    # GeneratorFor - lista de centrales
    # GeneratorRating - centrales con pmax inicial
    print_generator_files(iplp_path, blo_eta)

    # Line_MaxFlow
    # Line_MinFlow = -1*Line_MaxFlow

    # Line R - leer valor inicial y usar df_r
    # Line X - leer valor inicial y usar df_x


    # GNL Base - volumen mensual de cada estanque de gas


if __name__ == "__main__":
    main()
