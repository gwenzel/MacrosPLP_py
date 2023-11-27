'''
Generate Plexos files in CSV folder
'''

from macros.lin import read_df_lines
from macros.manli import (add_manli_data_row_by_row,
                          get_df_manli,
                          get_nominal_values_dict)
from macros.manlix import get_df_manlix
from utils.logger import create_logger
from utils.utils import (timeit,
                         define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         get_daily_indexed_df,
                         process_etapas_blocks,
                         read_plexos_end_date,
                         get_scenarios)
import pandas as pd
from pathlib import Path
from openpyxl.utils.datetime import from_excel

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


def read_df_mantcen_pmax(path_df: Path):
    return pd.read_csv(path_df / 'df_mantcen_pmax_plexos.csv')


def read_df_manlix_ab(path_df: Path):
    return pd.read_csv(path_df / 'df_manlix_ab.csv')


def read_df_manlix_ba(path_df: Path):
    return pd.read_csv(path_df / 'df_manlix_ba.csv')


def read_df_manli_ab(path_df: Path):
    return pd.read_csv(path_df / 'df_manli_ab.csv')


def read_df_manli_ba(path_df: Path):
    return pd.read_csv(path_df / 'df_manli_ba.csv')


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
                           path_csv: Path,
                           path_df: Path):
    df_centrales = read_centrales_plexos(iplp_path)
    dict_centrales_pmax = df_centrales.set_index('Nombre').to_dict()['Pmax']

    # Leer desde Temp/df/df_mantcen_pmax para no renovables
    # Para renovables, usar Pmax desde el vector en df_centrales
    df_gen_rating = df_daily.copy()
    df_pmax = read_df_mantcen_pmax(path_df)
    df_pmax = df_pmax.set_index(['Year', 'Month', 'Day'])\
                     .groupby(['Year', 'Month', 'Day']).max()\
                     .reset_index()\
                     .rename(columns={'Year': 'YEAR', 'Month': 'MONTH',
                                      'Day': 'DAY'})
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
                          path_csv: Path,
                          path_df: Path):
    # Generator_For
    print_generator_for(df_daily, iplp_path, path_csv)
    # Generator Rating
    print_generator_rating(df_daily, iplp_path, path_csv, path_df)


def build_df_nominal_plexos(df_daily: pd.DataFrame, line_names: list,
                            df_lineas: pd.DataFrame,
                            lines_value_col: str) -> pd.DataFrame:
    '''
    Build matrix with all nominal values for each line in line_names
    '''
    # Get nominal value dictionaries
    nominal_values_dict = get_nominal_values_dict(df_lineas, lines_value_col)
    # Get base dataframes
    df_nominal = df_daily.copy()
    # Add empty columns
    df_nominal = df_nominal.reindex(
        columns=df_nominal.columns.tolist() + line_names)
    # Add default values
    df_nominal[line_names] = [
        nominal_values_dict[line] for line in line_names]
    # Format to use add_manli_data_row_by_row
    df_nominal = df_nominal.rename(columns={'DATE': 'Date'})
    return df_nominal


def get_df_line_maxflow_minflow(
        iplp_path: Path,
        df_daily: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame):
    # Get Line_MaxFlow and Line_MinFlow
    # 0. Add PERIOD to df_daily
    df_daily['PERIOD'] = 1
    # 1. Get nominal data for all lines
    df_lines = read_df_lines(iplp_path)
    line_names = df_lines['Nombre A->B'].unique().tolist()
    df_nominal_ab = build_df_nominal_plexos(
        df_daily, line_names, df_lines, lines_value_col='A->B')
    df_nominal_ba = build_df_nominal_plexos(
        df_daily, line_names, df_lines, lines_value_col='B->A')
    # 2. Modify 0 with manli
    df_manli = get_df_manli(iplp_path, df_lines)
    df_ab_manli = add_manli_data_row_by_row(
        df_nominal_ab, df_manli, id_col='LÍNEA', manli_col='A-B')
    df_ba_manli = add_manli_data_row_by_row(
        df_nominal_ba, df_manli, id_col='LÍNEA', manli_col='B-A')
    # 3. Modify != nominal and !=0 with manlix
    df_manlix = get_df_manlix(iplp_path, df_lines)
    df_ab_manlix = add_manli_data_row_by_row(
        df_ab_manli, df_manlix, id_col='LÍNEA', manli_col='A-B')
    df_ba_manlix = add_manli_data_row_by_row(
        df_ba_manli, df_manlix, id_col='LÍNEA', manli_col='B-A')
    # 4. Set index
    new_index = ['YEAR', 'MONTH', 'DAY', 'PERIOD']
    df_ab_manlix = df_ab_manlix.set_index(new_index)
    df_ba_manlix = df_ba_manlix.set_index(new_index)
    # Finish formatting and return dataframes
    df_line_maxflow = df_ab_manlix.drop('Date', axis=1)
    df_line_minflow = df_ba_manlix.drop('Date', axis=1) * -1

    return df_line_maxflow, df_line_minflow


def get_df_line_r_x(
        iplp_path: Path,
        df_daily: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame):
    # 0. Add PERIOD to df_daily
    df_daily['PERIOD'] = 1
    # 1. Get nominal data for all lines
    df_lines = read_df_lines(iplp_path)
    line_names = df_lines['Nombre A->B'].unique().tolist()
    df_nominal_r = build_df_nominal_plexos(
        df_daily, line_names, df_lines, lines_value_col='R[ohm]')
    df_nominal_x = build_df_nominal_plexos(
        df_daily, line_names, df_lines, lines_value_col='X[ohm]')
    # 2. Modify != nominal and !=0 with manlix
    df_manlix = get_df_manlix(iplp_path, df_lines)
    df_r_manlix = add_manli_data_row_by_row(
        df_nominal_r, df_manlix, id_col='LÍNEA', manli_col='R [ohms]')
    df_x_manlix = add_manli_data_row_by_row(
        df_nominal_x, df_manlix, id_col='LÍNEA', manli_col='X [ohms]')
    # 3. Set index
    new_index = ['YEAR', 'MONTH', 'DAY', 'PERIOD']
    df_r_manlix = df_r_manlix.set_index(new_index)
    df_x_manlix = df_x_manlix.set_index(new_index)
    # Finish formatting and return dataframes
    df_line_r = df_r_manlix.drop('Date', axis=1)
    df_line_x = df_x_manlix.drop('Date', axis=1)

    return df_line_r, df_line_x


def print_line_files(
        iplp_path: Path,
        df_daily: pd.DataFrame,
        path_csv: Path):
    # Get line flow files and print them
    df_line_maxflow, df_line_minflow = get_df_line_maxflow_minflow(
        iplp_path, df_daily)
    df_line_maxflow.to_csv(path_csv / 'Line_MaxFlow.csv')
    df_line_minflow.to_csv(path_csv / 'Line_MinFlow.csv')
    # Get line R/X files and print them
    df_line_r, df_line_x = get_df_line_r_x(
        iplp_path, df_daily)
    df_line_r.to_csv(path_csv / 'Line_R.csv')
    df_line_x.to_csv(path_csv / 'Line_X.csv')


def print_gas_files(
        iplp_path: Path,
        df_daily: pd.DataFrame,
        path_csv: Path):
    '''
    Print all gas volumes
    '''
    # leer path d8 escenario combustible
    scenarios = get_scenarios(iplp_path)
    scen = scenarios['Combustible']
    check_is_path(path_csv / ('GNL_' + scen))

    # read gnl sheet PLPGNL_PolCom y seleccionar escenario
    df_gnl = pd.read_excel(iplp_path, sheet_name='PLPGNL_PolCom',
                           skiprows=1, header=[0, 1])
    df_gnl = df_gnl.dropna(axis=1)

    df_gnl[('Unnamed: 1_level_0', 'Fecha')] = df_gnl[
        ('Unnamed: 1_level_0', 'Fecha')].apply(from_excel)
    df_gnl = df_gnl.set_index(('Unnamed: 1_level_0', 'Fecha'))
    df_gnl.index = df_gnl.index.rename('Fecha')

    # Get list of contracts and monthly volumes
    list_of_contracts = df_gnl.stack().columns.tolist()

    # Finish reshaping
    df_gnl = df_gnl.stack().reset_index()
    df_gnl = df_gnl.rename(columns={'level_1': 'Scenario'})
    df_gnl = df_gnl.fillna(0)

    # Add new columns
    df_gnl['YEAR'] = df_gnl['Fecha'].dt.year
    df_gnl['MONTH'] = df_gnl['Fecha'].dt.month
    df_gnl['DAY'] = 1
    df_gnl['PERIOD'] = 1

    # filter dates
    mask_ini = df_gnl['Fecha'] >= df_daily['DATE'].iloc[0]
    mask_end = df_gnl['Fecha'] <= df_daily['DATE'].iloc[-1]
    df_gnl = df_gnl[mask_ini & mask_end]

    # filter scenario
    df_gnl = df_gnl[df_gnl['Scenario'] == scen]

    # for each contract, get:
    # YEAR	MONTH	DAY	PERIOD	VALUE
    # and print file to csv in folder

    for contract in list_of_contracts:
        list_of_cols = ['YEAR', 'MONTH', 'DAY', 'PERIOD', contract]
        df_aux = df_gnl[list_of_cols].copy()
        df_aux[contract] = df_aux[contract].round(2)
        df_aux = df_aux.rename(columns={contract: 'VALUE'})
        df_aux.to_csv(path_csv / ('GNL_' + scen) / (contract + '.csv'),
                      index=False)


@timeit
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
    logger.info('Processing plexos Generator files')
    print_generator_files(iplp_path, df_daily, path_csv, path_df)

    # Line files
    logger.info('Processing plexos Line files')
    print_line_files(iplp_path, df_daily, path_csv)

    # GNL Base - volumen mensual de cada estanque de gas
    logger.info('Processing plexos Gas volumes')
    print_gas_files(iplp_path, df_daily, path_csv)

    logger.info('CSV plexos completed successfully')


if __name__ == "__main__":
    main()
