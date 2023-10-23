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
from pathlib import Path

logger = create_logger('csv_plexos')


def get_df_daily_plexos(blo_eta: pd.DataFrame,
                        iplp_path: Path) -> pd.DataFrame:
    plexos_end_date = read_plexos_end_date(iplp_path)
    df_daily = get_daily_indexed_df(blo_eta, all_caps=True)
    year_mask = df_daily['YEAR'] <= plexos_end_date.year
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


def read_df_mantcen_pmax(iplp_path: Path):
    path_df = iplp_path.parent / 'Temp' / 'df' / 'df_mantcen_pmax.csv'
    df = pd.read_csv(path_df)
    df = df.drop(df.columns[0], axis=1)
    return df


def print_generator_for(df_daily: pd.DataFrame,
                        iplp_path: Path,
                        path_csv: Path):
    df_centrales = read_centrales_plexos(iplp_path)
    df_gen_for = df_centrales.copy()
    df_gen_for = df_gen_for.drop('Pmax', axis=1)
    df_gen_for = df_gen_for.rename(columns={'Nombre': 'NAME'})
    df_gen_for['YEAR'] = df_daily['YEAR'][0]
    df_gen_for['MONTH'] = 1
    df_gen_for['DAY'] = 1
    df_gen_for['PERIOD'] = 1
    df_gen_for['VALUE'] = 0
    df_gen_for.to_csv(path_csv / 'Generator_For.csv', index=False)


def print_generator_rating(df_daily: pd.DataFrame,
                           iplp_path: Path,
                           path_csv: Path):
    df_centrales = read_centrales_plexos(iplp_path)
    dict_centrales_pmax = df_centrales.set_index('Nombre').to_dict()['Pmax']

    # Leer desde Temp/df/df_mantcen_pmax para no renovables
    # Para renovables, usar Pmax desde el vector en df_centrales
    df_gen_rating = df_daily.copy()
    df_pmax = read_df_mantcen_pmax(iplp_path)

    df_pmax = df_pmax.set_index(['Year', 'Month'])\
                     .groupby(['Year', 'Month']).max()\
                     .drop(['Etapa', 'Block', 'Block_Len'], axis=1)\
                     .reset_index()\
                     .rename(columns={'Year': 'YEAR', 'Month': 'MONTH'})
    df_gen_rating = df_gen_rating.merge(df_pmax)\
                                 .set_index(['YEAR', 'MONTH', 'DAY'])\
                                 .drop('DATE', axis=1)

    # Merge for non ernc units (those in mantcen)
    # filter out units in mantcen
    dict_centrales_pmax = {unit: pmax
                           for unit, pmax in dict_centrales_pmax.items()
                           if unit not in df_gen_rating.columns}
    dict_centrales_pmax['PERIOD'] = 1

    # concat column with pmax for ernc units
    list_of_dfs = [df_gen_rating]
    for unit, pmax in dict_centrales_pmax.items():
        df_aux = pd.DataFrame(pmax, index=df_gen_rating.index, columns=[unit])
        list_of_dfs.append(df_aux)
    # concat all
    df_gen_rating = pd.concat(list_of_dfs, axis=1)

    # format
    new_index = ['YEAR', 'MONTH', 'DAY', 'PERIOD']
    df_gen_rating = df_gen_rating.reset_index()\
                                 .set_index(new_index)\
                                 .round(1)\
                                 .reset_index()
    # print
    df_gen_rating.to_csv(path_csv / 'Generator_Rating.csv', index=False)


def print_generator_files(iplp_path: Path,
                          df_daily: pd.DataFrame,
                          path_csv: Path):
    # Generator_For
    print_generator_for(df_daily, iplp_path, path_csv)
    # Generator Rating
    print_generator_rating(df_daily, iplp_path, path_csv)


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
    path_csv = iplp_path.parent / "Temp" / "CSV"
    check_is_path(path_csv)

    # Get Hour-Blocks-Etapas definition
    logger.info('Processing block to etapas files')
    blo_eta, _, _ = process_etapas_blocks(path_dat)
    blo_eta = blo_eta.drop(['Tasa'], axis=1)

    df_daily = get_df_daily_plexos(blo_eta, iplp_path)

    # GeneratorFor - lista de centrales
    # GeneratorRating - centrales con pmax inicial
    print_generator_files(iplp_path, df_daily, path_csv)

    # Line_MaxFlow
    # Line_MinFlow = -1*Line_MaxFlow

    # Line R - leer valor inicial y usar df_r
    # Line X - leer valor inicial y usar df_x


    # GNL Base - volumen mensual de cada estanque de gas


if __name__ == "__main__":
    main()
