'''
Generate Plexos files in CSV folder
'''
from macros.cvar import (read_heatrate_and_unit_fuel_mapping,
                         read_unit_cvar_nominal)
from macros.dem import (dda_por_barra_to_row_format,
                        get_monthly_demand)
from macros.lin import read_df_lines
from macros.manli import (add_manli_data_row_by_row,
                          get_df_manli,
                          get_nominal_values_dict)
from macros.manlix import get_df_manlix
from macros.ernc import get_input_names
from utils.logger import add_file_handler, create_logger
from utils.utils import (timeit,
                         define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         get_daily_indexed_df,
                         get_hourly_indexed_df,
                         process_etapas_blocks,
                         read_plexos_end_date,
                         get_scenarios)
import pandas as pd
from pathlib import Path
from openpyxl.utils.datetime import from_excel

logger = create_logger('csv_plexos')


def get_df_daily_plexos(blo_eta: pd.DataFrame,
                        iplp_path: Path) -> pd.DataFrame:
    '''
    Get df_daily with all columns needed for plexos
    '''
    plexos_end_date = read_plexos_end_date(iplp_path)
    df_daily = get_daily_indexed_df(blo_eta, all_caps=True)
    year_mask = df_daily['YEAR'] <= plexos_end_date.year
    return df_daily[year_mask]


def get_df_hourly_plexos(blo_eta: pd.DataFrame,
                         iplp_path: Path) -> pd.DataFrame:
    '''
    Get df_hourly with all columns needed for plexos
    '''
    plexos_end_date = read_plexos_end_date(iplp_path)
    df_hourly = get_hourly_indexed_df(blo_eta, all_caps=False)
    year_mask = df_hourly['Year'] <= plexos_end_date.year
    return df_hourly[year_mask]


def read_centrales_plexos(iplp_path: Path,
                          add_specs: bool = False,
                          only_thermal: bool = False) -> pd.DataFrame:
    '''
    Read Centrales sheet from iplp_path and return df with generators
    '''
    if not add_specs:
        # Get only Pmax
        df = pd.read_excel(iplp_path, sheet_name="Centrales",
                           skiprows=4, usecols="B,C,AB")
        df = df.rename(columns={
            'CENTRALES': 'Nombre',
            'Máxima.1': 'Pmax'})
    else:
        # Get MinTecNeto, MinDown, MinUp, ShutDownCost, StartCost
        df = pd.read_excel(iplp_path, sheet_name="Centrales",
                           skiprows=4, usecols="B,C,AT:AX")
        df = df.rename(columns={
            'CENTRALES': 'Nombre',
            'MinTec Neto': 'MinTecNeto',
            'Start Cost': 'StartCost',
            'Shutdown Cost': 'ShutDownCost',
            'Min Up Time': 'MinUp',
            'Min Down Time': 'MinDown'})
        df = df.fillna(0)
    # Filter out if X
    df = df[df['Tipo de Central'] != 'X']
    if only_thermal:
        df = df[df['Tipo de Central'] == 'T']
    df = df.drop('Tipo de Central', axis=1)
    return df


def print_generator_for(df_daily: pd.DataFrame,
                        iplp_path: Path,
                        path_csv: Path):
    '''
    Print Generator For file with plexos format
    '''
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


def print_generator_other(df_daily: pd.DataFrame,
                          iplp_path: Path,
                          path_csv: Path):
    '''
    Print other Gen Specs:
    MinDown, MinUp, ShutDownCost, StartCost, MinTecNeto
    '''
    df_centrales = read_centrales_plexos(iplp_path, add_specs=True)

    list_of_specs = ['MinDown', 'MinUp', 'ShutDownCost',
                     'StartCost', 'MinTecNeto']
    for spec in list_of_specs:
        df_aux = df_centrales[['Nombre', spec]].copy()
        df_aux = df_aux.rename(columns={'Nombre': 'NAME',
                                        spec: 'VALUE'})
        df_aux['YEAR'] = df_daily['YEAR'][0]
        df_aux['MONTH'] = 1
        df_aux['DAY'] = 1
        df_aux['PERIOD'] = 1
        df_aux = df_aux[['NAME', 'YEAR', 'MONTH', 'DAY', 'PERIOD', 'VALUE']]
        df_aux.to_csv(path_csv / (spec + '.csv'), index=False)


def print_generator_rating(df_daily: pd.DataFrame,
                           iplp_path: Path,
                           path_csv: Path,
                           path_df: Path):
    '''
    Print Generator Rating with plexos format
    '''
    # Leer desde Temp/df/df_mantcen_pmax para no renovables
    df_gen_rating = df_daily.copy()
    try:
        df_pmax = pd.read_csv(path_df / 'df_mantcen_pmax_plexos.csv')
    except FileNotFoundError:
        logger.error('File df_mantcen_pmax_plexos.csv not found')
        logger.error('File Generator_Rating could not be printed')
        return
    df_pmax = df_pmax.set_index(['Year', 'Month', 'Day'])\
                     .groupby(['Year', 'Month', 'Day']).max()\
                     .reset_index()\
                     .rename(columns={'Year': 'YEAR', 'Month': 'MONTH',
                                      'Day': 'DAY'})
    df_gen_rating = df_gen_rating.merge(df_pmax)\
                                 .set_index(['YEAR', 'MONTH', 'DAY'])\
                                 .drop('DATE', axis=1)

    # Para renovables, usar Pmax desde el vector en df_centrales
    # filter out units in mantcen
    # This assumes that Pmax Net is ok for these units, no reserve added
    df_centrales = read_centrales_plexos(iplp_path)
    dict_centrales_pmax = df_centrales.set_index('Nombre').to_dict()['Pmax']
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
                                 .round(2)\
                                 .reset_index()
    # print
    df_gen_rating.to_csv(path_csv / 'Generator_Rating.csv', index=False)


def print_generator_heatrate(df_daily, iplp_path, path_csv, path_df):
    '''
    Read df_cvar_with_emissions.csv file and print
    Generator HeatRate (Variable Cost) with plexos format
    '''
    try:
        df = pd.read_csv(path_df / 'df_cvar_with_emissions.csv')
    except FileNotFoundError:
        logger.error('File df_cvar_with_emissions.csv not found')
        logger.error('File Generator_HeatRate could not be printed')
        return
    # Format dataframe
    # Recalculate Month (not hydromonth)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.month
    # Rename columns
    df = df.rename(columns={'Year': 'YEAR', 'Month': 'MONTH',
                            'Date': 'DATE', 'Central': 'NAME',
                            'Variable Cost + CO2 Tax USD/MWh': 'VALUE'})
    # Keep relevant columns
    df = df[['YEAR', 'MONTH', 'NAME', 'VALUE']]
    # Merge with df_daily
    df = df_daily.merge(df, on=['YEAR', 'MONTH'], how='left')
    df = df.sort_values(['NAME', 'YEAR', 'MONTH', 'DAY'])
    df = df.pivot(index=['YEAR', 'MONTH', 'DAY'],
                  columns='NAME', values='VALUE')
    df = df.reset_index()\
           .rename_axis(None, axis=1)
    # Read complete list of generators and add the ones that are missing
    # with their nominal variable cost
    # or 0 if they are EOLICA, SOLAR, BESS
    df_centrales = read_centrales_plexos(iplp_path, only_thermal=True)
    dict_cvar_nom = read_unit_cvar_nominal(iplp_path, ernc_zero=True)
    list_of_centrales = df_centrales['Nombre'].unique().tolist()
    list_of_centrales_in_df = df.columns.tolist()[3:]
    list_of_centrales_missing = [
        unit for unit in list_of_centrales
        if unit not in list_of_centrales_in_df
        ]
    dict_nominal_cvar_cen_missing = {
        unit: dict_cvar_nom[unit] if unit in dict_cvar_nom.keys() else 0
        for unit in list_of_centrales_missing
    }
    # Create dataframe repeating values in dict_nominal_cvar_cen_missing
    # using keys as columns, and repeating values, using same index as in df
    df_aux = pd.DataFrame(dict_nominal_cvar_cen_missing, index=df.index)
    # Concat df_aux to the right side of df
    df = pd.concat([df, df_aux], axis=1)
    # Format
    df['PERIOD'] = 1
    new_index = ['YEAR', 'MONTH', 'DAY', 'PERIOD']
    df = df.set_index(new_index)
    # Print
    df.to_csv(path_csv / 'Generator_HeatRate.csv')


def print_generator_heatrate_fuel(df_daily, iplp_path, path_csv):
    '''
    Read df_cvar_with_emissions.csv file and print
    Generator HeatRate (pure Heatrate) with plexos format
    '''
    df = read_heatrate_and_unit_fuel_mapping(iplp_path)
    # Format dataframe
    df = df.drop(['Fuel Name', 'Non-Fuel Cost'], axis=1)
    df['YEAR'] = df_daily['YEAR'][0]
    df['MONTH'] = df_daily['MONTH'][0]
    df['DAY'] = 1
    df['PERIOD'] = 1
    df = df.set_index(['YEAR', 'MONTH', 'DAY', 'PERIOD'])
    df_daily = df_daily.drop('DATE', axis=1)
    df_daily['PERIOD'] = 1
    # Merge dataframes
    df = df_daily.merge(df, on=['YEAR', 'MONTH', 'DAY', 'PERIOD'], how='left')
    # Pass to wide format
    df = df.pivot(index=['YEAR', 'MONTH', 'DAY', 'PERIOD'],
                  columns='Central', values='Heat Rate')
    # Drop nan column
    df = df.dropna(axis=1, how='all')
    # Forward fill values - heatrate is the same in all the horizon
    df = df.fillna(method='ffill', axis=0)
    # Print file
    df.to_csv(path_csv / 'Generator_HeatRate_Fuel.csv')


def print_generator_files(iplp_path: Path,
                          df_daily: pd.DataFrame,
                          path_csv: Path,
                          path_df: Path,
                          path_inputs: Path):
    '''
    Print all generator files in CSV folder
    '''
    # Generator_For
    logger.info('Processing plexos Generator For')
    print_generator_for(df_daily, iplp_path, path_csv)
    # Generator Rating
    logger.info('Processing plexos Generator Rating')
    print_generator_rating(df_daily, iplp_path, path_csv, path_df)
    # Generator MaxCapacity
    logger.info('Processing plexos Generator MaxCapacity')
    print_generator_maxcapacity(path_df, path_csv)
    # Generator RatingFactor
    logger.info('Processing plexos Generator RatingFactor')
    print_generator_rating_factor(iplp_path, path_df, path_csv)
    # Generator HeatRate (Variable Cost)
    logger.info('Processing plexos Generator HeatRate')
    print_generator_heatrate(df_daily, iplp_path, path_csv, path_df)
    # Generator HeatRate (Pure HeatRate)
    logger.info('Processing plexos Generator HeatRate Fuel')
    print_generator_heatrate_fuel(df_daily, iplp_path, path_csv)
    logger.info('Processing plexos Generator Other')
    # Other (MinDown, MinUp, ShutDownCost, StartCost, MinTecNeto)
    print_generator_other(df_daily, iplp_path, path_csv)


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
        df_daily: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    '''
    Get df_line_maxflow and df_line_minflow
    '''
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


def add_per_unit_r_and_x(df: pd.DataFrame,
                         ohms_unit: str = '[ohm]') -> pd.DataFrame:
    '''
    Add per unit data for R and X to dataframe
    '''
    df['R [0/1]'] = df['R%s' % ohms_unit] * 100 / df['V [kV]']**2
    df['X [0/1]'] = df['X%s' % ohms_unit] * 100 / df['V [kV]']**2
    return df


def get_df_line_r_x(
        iplp_path: Path,
        df_daily: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    '''
    Get df_line_r and df_line_x
    '''
    # 0. Add PERIOD to df_daily
    df_daily['PERIOD'] = 1
    # 1. Get nominal data for all lines in p.u.
    df_lines = read_df_lines(iplp_path)
    line_names = df_lines['Nombre A->B'].unique().tolist()
    df_lines = add_per_unit_r_and_x(df_lines, ohms_unit='[ohm]')
    df_nominal_r = build_df_nominal_plexos(
        df_daily, line_names, df_lines, lines_value_col='R [0/1]')
    df_nominal_x = build_df_nominal_plexos(
        df_daily, line_names, df_lines, lines_value_col='X [0/1]')
    # 2. Modify != nominal and !=0 with manlix
    df_manlix = get_df_manlix(iplp_path, df_lines)
    df_manlix = add_per_unit_r_and_x(df_manlix, ohms_unit=' [ohms]')
    df_r_manlix = add_manli_data_row_by_row(
        df_nominal_r, df_manlix, id_col='LÍNEA', manli_col='R [0/1]')
    df_x_manlix = add_manli_data_row_by_row(
        df_nominal_x, df_manlix, id_col='LÍNEA', manli_col='X [0/1]')
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
    '''
    Print all line files
    '''
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
    df_gnl = df_gnl.dropna(axis=1, how='all')

    # Warn if there are any NaN values
    if df_gnl.dropna(axis=1, how='all').isna().any().any():
        logger.warning('There are NaN values in PLPGNL_PolCom sheet')
        logger.warning('Check the file and fix the NaN values')
        logger.warning('Missing gas volumes will be replaced by 0')

    df_gnl[('Unnamed: 1_level_0', 'Fecha')] = df_gnl[
        ('Unnamed: 1_level_0', 'Fecha')].apply(from_excel)
    df_gnl = df_gnl.set_index(('Unnamed: 1_level_0', 'Fecha'))
    df_gnl.index = df_gnl.index.rename('Fecha')

    # Get list of contracts and monthly volumes
    list_of_contracts = df_gnl.stack(future_stack=True).columns.tolist()

    # Finish reshaping
    df_gnl = df_gnl.stack(future_stack=True).reset_index()
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


def print_generator_maxcapacity(path_df: Path, path_csv: Path):
    '''
    Print file with ERNC generator max capacity, based on ERNC tab
    '''
    try:
        df = pd.read_csv(path_df / 'ernc_RatingFactor.csv')
    except FileNotFoundError:
        logger.error('File ernc_RatingFactor.csv not found')
        logger.error('File Generator_MaxCapacity could not be printed')
        return
    df = df.rename(
        columns={'Name': 'NAME', 'Value [MW]': 'VALUE'})
    df['DateFrom'] = pd.to_datetime(
        df['DateFrom'])
    df['YEAR'] = df['DateFrom'].dt.year
    df['MONTH'] = df['DateFrom'].dt.month
    df['DAY'] = df['DateFrom'].dt.day
    df['PERIOD'] = 1
    df['BAND'] = 1
    ordered_cols = ['NAME', 'BAND', 'YEAR', 'MONTH', 'DAY', 'PERIOD', 'VALUE']
    df = df[ordered_cols]
    df.to_csv(path_csv / 'Generator_MaxCapacity.csv', index=False)


def print_generator_rating_factor(iplp_path: Path,
                                  path_df: Path,
                                  path_csv: Path):
    '''
    Print file with ERNC profiles
    '''
    input_names = get_input_names(iplp_path)

    # Hourly Profiles
    try:
        h_profiles = pd.read_csv(
            path_df / input_names["H_PROFILES_FILENAME"])
    except FileNotFoundError:
        logger.error('File %s not found' % input_names["H_PROFILES_FILENAME"])
        logger.error('File Generator_RatingFactor could not be printed')
        return
    h_profiles = h_profiles.drop('MES', axis=1)\
                           .set_index('PERIODO')\
                           .stack()\
                           .reset_index()\
                           .rename(columns={'level_1': 'NAME',
                                            0: 'VALUE'})
    h_profiles = h_profiles.sort_values(['NAME', 'PERIODO'])
    h_profiles['PATTERN'] = h_profiles['PERIODO'].apply(
        lambda x: 'H%s' % x)
    h_profiles = h_profiles[['NAME', 'PATTERN', 'VALUE']]
    h_profiles['VALUE'] = h_profiles['VALUE'] * 100

    # Hourly-Monthly Profiles
    try:
        hm_profiles = pd.read_csv(
            path_df / input_names["HM_PROFILES_FILENAME"])
    except FileNotFoundError:
        logger.error('File %s not found' % input_names["HM_PROFILES_FILENAME"])
        logger.error('File Generator_RatingFactor could not be printed')
        return
    hm_profiles = hm_profiles.set_index(['MES', 'PERIODO'])\
                             .stack()\
                             .reset_index()\
                             .rename(columns={'level_2': 'NAME',
                                              0: 'VALUE'})
    hm_profiles = hm_profiles.sort_values(['NAME', 'MES', 'PERIODO'])
    hm_profiles['PATTERN'] = hm_profiles.apply(
        lambda x: 'M%s,H%s' % (x['MES'], x['PERIODO']), axis=1)
    hm_profiles = hm_profiles[['NAME', 'PATTERN', 'VALUE']]
    hm_profiles['VALUE'] = hm_profiles['VALUE'] * 100
    # Concat both dataframes
    df_profiles = pd.concat([h_profiles, hm_profiles])
    # Print to csv
    df_profiles.to_csv(path_csv / 'Generator_RatingFactor.csv', index=False)


def get_monthly_demand_plexos(iplp_path: Path,
                              year_ini: int, year_end: int) -> pd.DataFrame:
    df_monthly_demand = get_monthly_demand(iplp_path, plexos=True)
    # Filter dates
    mask_ini = df_monthly_demand['Year'] >= year_ini
    mask_end = df_monthly_demand['Year'] <= year_end
    df_monthly_demand = df_monthly_demand[mask_ini & mask_end]
    return df_monthly_demand


def format_node_load_file(df_hourly: pd.DataFrame, df: pd.DataFrame):
    '''
    Format Node Load file for plexos

    Start from df_hourly to make sure all real hours are considered,
    fill missing days (Feb-29) with previous day
    '''
    cols_to_merge_on = ['Year', 'Month', 'Day', 'Hour']
    df = pd.merge(df_hourly, df, on=cols_to_merge_on)
    df = df.drop('Date', axis=1)
    df = df.sort_values(cols_to_merge_on)
    # Use nodes as column names
    df = df.set_index(['Barra Consumo', 'Year', 'Month', 'Day', 'Hour'])\
           .unstack('Barra Consumo')
    # Drop level
    df.columns = df.columns.droplevel()
    # For each column, if entire Day has 0 Consumption, copy previous day
    df = df.fillna(0)
    for col in df.columns:
        mask = df.groupby(['Year', 'Month', 'Day'])[col].transform(
            'sum') == 0
        df.loc[mask, col] = df.loc[:, col].shift(24)
    df = df.round(4)
    # Rename index columns
    df.reset_index(inplace=True)
    df.columns.values[0] = 'YEAR'
    df.columns.values[1] = 'MONTH'
    df.columns.values[2] = 'DAY'
    df.columns.values[3] = 'PERIOD'
    return df


def print_node_load_new(df_hourly: pd.DataFrame, path_csv: Path,
                        iplp_path: Path, path_df: Path):
    '''
    Print Node Load New
    '''
    # Get initial and final year
    year_ini = df_hourly['Date'].iloc[0].year
    year_end = df_hourly['Date'].iloc[-1].year

    logger.info('Getting dem_por_barra, monthly demand and hourly profiles')
    df_dem_por_barra = dda_por_barra_to_row_format(iplp_path)
    df_monthly_demand = get_monthly_demand_plexos(
        iplp_path, year_ini, year_end)
    df_hourly_profiles_plexos = get_hourly_profiles_plexos(iplp_path)

    logger.info('Merging dataframes to get hourly demand per node')
    # Get all profiles with hourly resolution for Plexos
    df = get_all_profiles_plexos(df_monthly_demand,
                                 df_hourly_profiles_plexos,
                                 df_dem_por_barra)

    logger.info('Formatting Node Load file')
    df = format_node_load_file(df_hourly, df)

    logger.info('Printing Node Load file')
    df.to_csv(path_csv / 'Node_Load.csv', index=False)

    logger.info('Printing demand dataframes')
    df_dem_por_barra.to_csv(path_df / 'dem_dem_por_barra.csv', index=False)
    df_monthly_demand.to_csv(path_df / 'dem_monthly_demand.csv', index=False)
    df_hourly_profiles_plexos.to_csv(
        path_df / 'dem_hourly_profiles_plexos.csv', index=False)


def get_hourly_profiles_plexos(iplp_path: Path) -> pd.DataFrame:
    # Read PerfilesDDA_Plx sheet, skipping first column and first row,
    # and the using the 3 first rows as header,
    # and the 3 first columns as index
    df = pd.read_excel(iplp_path, sheet_name='PerfilesDDA_Plx',
                       skiprows=1, header=[0, 1], index_col=[1, 3])
    # Drop first two columns (Escenario, mes in str)
    df = df.drop([df.columns[0], df.columns[1]], axis=1)
    # Drop first rows (hora in str, column names)
    df = df.drop([df.index[0], df.index[1]])
    # Use pivot table to get the desired rows format
    df = df.stack([0, 1], future_stack=True).reset_index()
    # Rename columns
    df = df.rename(columns={'level_0': 'Profile', 'level_1': 'Month',
                            'dia': 'Day', 'hora': 'Hour', 0: 'PowerFactor'})
    # Drop rows is PowerFactor is 0 for the entire day
    mask = df.groupby(['Profile', 'Month', 'Day'])['PowerFactor'].transform(
        'sum') == 0
    df = df[~mask]
    return df


def get_all_profiles_plexos(df_monthly_demand: pd.DataFrame,
                            df_hourly_profiles_plexos: pd.DataFrame,
                            df_dem_por_barra: pd.DataFrame) -> pd.DataFrame:
    '''
    Get all profiles with hourly resolution for Plexos by merging
    the three dataframes given
    '''
    # First drop columns that won't be used, to accelerate merge
    df_monthly_demand = df_monthly_demand.drop(['DaysInMonth'], axis=1)
    # Set index to improve merge performance
    df_monthly_demand.set_index(['Coordinado', 'Cliente'],
                                inplace=True)
    df_dem_por_barra.set_index(['Coordinado', 'Cliente'],
                               inplace=True)
    # Then calculate yearly demand, as plexos profiles are % of monthly demand
    # Merge dataframes of demand and dda_por_barra
    df = pd.merge(
        df_monthly_demand, df_dem_por_barra, on=['Coordinado', 'Cliente'])
    # Make sure Profile is string on df and df_hourly_profiles_plexos
    df['Profile'] = df['Profile'].astype(str)
    df_hourly_profiles_plexos['Profile'] = df_hourly_profiles_plexos[
        'Profile'].astype(str)
    # Merge with hourly profiles
    # To avoid memory problems, merge by year, then concatenate
    list_of_df = []
    for year in df['Year'].unique():
        logger.info('Node Load - Processing year %s' % year)
        df_aux = pd.merge(df[df['Year'] == year],
                          df_hourly_profiles_plexos,
                          on=['Profile', 'Month'])
        # Calculate consumption, group by Barra and sum, reorder and sort
        df_cons = get_consumption_per_barra_plexos(df_aux)
        list_of_df.append(df_cons)
        # Free memory
        del df_aux, df_cons
    # Concatenate all dataframes
    df = pd.concat(list_of_df)
    return df


def get_consumption_per_barra_plexos(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Calculate consumption, group by Barra and sum
    Then reorder and sort
    '''
    df['Consumo'] = df.apply(lambda x: calculate_consumption_plexos(x), axis=1)
    cols_to_drop = ['Demand', 'Factor Barra Consumo', 'PowerFactor']
    cols_for_groupby = ['Year', 'Month', 'Day', 'Hour', 'Barra Consumo']
    df = df.drop(cols_to_drop, axis=1)
    df = df.groupby(cols_for_groupby).sum(numeric_only=True).reset_index()
    # Reorder columns and sort
    cols_to_select = ['Barra Consumo', 'Year', 'Month', 'Day', 'Hour',
                      'Consumo']
    cols_to_sort = ['Barra Consumo', 'Year', 'Month', 'Day', 'Hour']
    df = df[cols_to_select]
    df = df.sort_values(by=cols_to_sort).reset_index(drop=True)
    return df


def calculate_consumption_plexos(x):
    # Consumption is calculated as follows:
    # [Yearly demand] * [% of demand in current bus] *
    #   [% of demand in current hour] * 1000
    return x['Demand'] * x['Factor Barra Consumo'] * x['PowerFactor'] * 1000


def main():
    '''
    Main routine
    '''
    try:
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

        # Add destination folder to logger
        path_log = iplp_path.parent / "Temp" / "log"
        check_is_path(path_log)
        add_file_handler(logger, 'csv_plexos', path_log)

        # Get Hour-Blocks-Etapas definition
        logger.info('Processing block to etapas files')
        blo_eta, _, _ = process_etapas_blocks(path_dat)

        df_daily = get_df_daily_plexos(blo_eta, iplp_path)
        df_hourly = get_df_hourly_plexos(blo_eta, iplp_path)

        # Print Node Load (Demand)
        logger.info('Processing plexos Node Load')
        print_node_load_new(df_hourly, path_csv, iplp_path, path_df)

        # Generator files
        logger.info('Processing plexos Generator files')
        print_generator_files(iplp_path, df_daily, path_csv,
                              path_df, path_inputs)

        # Line files
        logger.info('Processing plexos Line files')
        print_line_files(iplp_path, df_daily, path_csv)

        # GNL Base - volumen mensual de cada estanque de gas
        logger.info('Processing plexos Gas volumes')
        print_gas_files(iplp_path, df_daily, path_csv)

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
