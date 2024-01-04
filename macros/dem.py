'''Demanda

Module to generate demand input files for PLP.

Ouput files are:

- plpdem.dat: Demand per Etapa for each node
- uni_plpdem.dat: Demand per Etapa for the uninodal case
- plpfal.prn: Define maximum power for each Failure Unit,
              based on the max demand of each node
'''
import pandas as pd
import numpy as np
from openpyxl.utils.datetime import from_excel
from pathlib import Path
from macros.bar import get_barras_info

from utils.utils import (timeit,
                         define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         process_etapas_blocks,
                         get_list_of_all_barras,
                         write_lines_from_scratch,
                         write_lines_appending,
                         translate_to_hydromonth)
from utils.logger import add_file_handler, create_logger

logger = create_logger('demanda')

MONTH_2_NUMBER = {
    'ene': 1,
    'feb': 2,
    'mar': 3,
    'abr': 4,
    'may': 5,
    'jun': 6,
    'jul': 7,
    'ago': 8,
    'sep': 9,
    'oct': 10,
    'nov': 11,
    'dic': 12
}

HORA_DICT = {'H%s' % i: i for i in range(1, 25)}

formatters_plpdem = {
    "Month":    "   {:02d}".format,
    "Etapa":    "  {:03d}".format,
    "Consumo":  "{:9.2f}".format
}

formatters_plpfal = {
    "Month":    "     {:02d}".format,
    "Etapa":    "   {:04d}".format,
    "NIntPot":  "{:9.2f}".format,
    "PotMin":   "{:8.2f}".format,
    "PotMax":   "{:8.2f}".format
}


def dda_por_barra_to_row_format(iplp_path: Path) -> pd.DataFrame:
    df = pd.read_excel(iplp_path, sheet_name="DdaPorBarra")
    keys = ["Coordinado", "Cliente", "Profile",
            "Barra Consumo", "Factor Barra Consumo"]
    df_as_dict = df.to_dict()
    new_dict = {key: {} for key in keys}
    idx = 0
    N_MAX_BARRAS = 23
    N_COORD_CLIENTE = len(df)
    for i in range(N_COORD_CLIENTE):
        for barra in range(1, N_MAX_BARRAS + 1):
            if df_as_dict["Barra Consumo %s" % barra][i] is not np.nan:
                new_dict["Coordinado"][idx] = df_as_dict["Coordinado"][i]
                new_dict["Cliente"][idx] = df_as_dict["Cliente"][i]
                new_dict["Profile"][idx] = df_as_dict["Perfil día tipo"][i]
                new_dict["Barra Consumo"][idx] = df_as_dict[
                    "Barra Consumo %s" % barra][i]
                new_dict["Factor Barra Consumo"][idx] = df_as_dict[
                    "Factor Barra Consumo %s" % barra][i]
            idx += 1
    df_dda_por_barra = pd.DataFrame(new_dict).reset_index(drop=True)
    df_dda_por_barra['Coordinado'] = \
        df_dda_por_barra['Coordinado'].fillna("NA")
    return df_dda_por_barra


def get_monthly_demand(iplp_path: Path, plexos: bool = False) -> pd.DataFrame:
    '''
    Get monthly demand and add timedata
    '''
    df = pd.read_excel(iplp_path, sheet_name='DdaEnergia')
    # Drop rows if column # is nan
    df = df.dropna(subset=['#'], how='any')
    # Clean data
    cols_to_drop = ['#', 'Coordinado.1', 'Cliente.1', 'Perfil',
                    'Clasificacion SEN', 'Clasificacion ENGIE']
    df = df.drop(cols_to_drop, axis=1)
    df = df.dropna(how='all', axis=1)
    df.loc[:, 'Coordinado'] = df['Coordinado'].fillna('NA')
    # Stack to get Demand series
    demand_series = df.set_index(['Coordinado', 'Cliente']).stack()
    demand_series.index.set_names(['Coordinado', 'Cliente', 'Date'],
                                  inplace=True)
    demand_series.name = 'Demand'
    df = demand_series.reset_index()
    # parse dates
    df['Date'] = df['Date'].apply(from_excel)
    # If plexos, filter out all BESS, Carnot and PHS clients
    if plexos:
        df = df[~df['Cliente'].str.contains('BESS|CARNOTx|PHSx')]
    # add timedata
    df = add_timedata_to_monthly_demand(df)
    return df


def get_hourly_profiles(iplp_path: Path) -> pd.DataFrame:
    df = pd.read_excel(iplp_path, sheet_name='PerfilesDDA')
    # Clean data
    cols_to_drop = ['#', 'Año', 'Verificador consumo']
    df = df.drop(cols_to_drop, axis=1)
    # Process data
    profile_series = df.set_index(['Perfil día tipo', 'Mes']).stack()
    profile_series.index.set_names(['Perfil día tipo', 'Mes', 'Hora'],
                                   inplace=True)
    profile_series.name = 'PowerFactor'
    df = profile_series.reset_index()
    df = df.replace(to_replace={"Mes": MONTH_2_NUMBER, "Hora": HORA_DICT})
    df = df.rename(
        columns={'Perfil día tipo': 'Profile',
                 'Mes': 'Month',
                 'Hora': 'Hour'})
    return df


def get_blockly_profiles(df_hourly_profiles: pd.DataFrame,
                         block2day: pd.DataFrame) -> pd.DataFrame:
    df = pd.merge(df_hourly_profiles, block2day, on=['Month', 'Hour'],
                  how='left')
    df = df.drop('Hour', axis=1)
    df = df.groupby(['Profile', 'Month', 'Block']).sum().reset_index()
    return df


def calculate_consumption(x):
    # Consumption is calculated as follows:
    # [Monthly demand] * [% of demand in current bus] *
    #   [% of demand in current block] * 1000
    # divided by
    #  ([Days in Month] * [Hours per day in current block])
    num = x['Demand'] * x['Factor Barra Consumo'] * x['PowerFactor'] * 1000
    den = (x['DaysInMonth'] * x['Block_Len'])
    return num / den


def calculate_consumption_plexos(x):
    # Consumption is calculated as follows:
    # [Monthly demand] * [% of demand in current bus] *
    #   [% of demand in current block] * 1000
    # divided by
    #  ([Days in Month] * [Hours per day in current block])
    num = x['Demand'] * x['Factor Barra Consumo'] * x['PowerFactor'] * 1000
    den = (x['DaysInMonth'] * 1)
    return num / den


def add_timedata_to_monthly_demand(
        df_monthly_demand: pd.DataFrame) -> pd.DataFrame:
    # Add data to monthly demand df
    df_monthly_demand['Year'] = pd.to_datetime(
        df_monthly_demand['Date']).dt.year
    df_monthly_demand['Month'] = pd.to_datetime(
        df_monthly_demand['Date']).dt.month
    df_monthly_demand['DaysInMonth'] = pd.to_datetime(
        df_monthly_demand['Date']).dt.daysinmonth
    df_monthly_demand = df_monthly_demand.drop(['Date'], axis=1)
    return df_monthly_demand


def get_consumption_per_barra(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Calculate consumption, group by Barra and sum
    Then reorder and sort
    '''
    df['Consumo'] = df.apply(lambda x: calculate_consumption(x), axis=1)
    cols_to_drop = ['Demand', 'Factor Barra Consumo', 'PowerFactor',
                    'Block_Len', 'DaysInMonth']
    cols_for_groupby = ['Year', 'Month', 'Block', 'Etapa', 'Barra Consumo']
    df = df.drop(cols_to_drop, axis=1)
    df = df.groupby(cols_for_groupby).sum(numeric_only=True).reset_index()
    # Reorder columns and sort
    cols_to_select = ['Barra Consumo', 'Year', 'Month', 'Block',
                      'Etapa', 'Consumo']
    cols_to_sort = ['Barra Consumo', 'Year', 'Month', 'Block', 'Etapa']
    df = df[cols_to_select]
    df = df.sort_values(by=cols_to_sort).reset_index(drop=True)
    return df


def get_consumption_per_barra_plexos(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Calculate consumption, group by Barra and sum
    Then reorder and sort
    '''
    df['Consumo'] = df.apply(lambda x: calculate_consumption_plexos(x), axis=1)
    cols_to_drop = ['Demand', 'Factor Barra Consumo', 'PowerFactor',
                    'DaysInMonth']
    cols_for_groupby = ['Year', 'Month', 'Hour', 'Barra Consumo']
    df = df.drop(cols_to_drop, axis=1)
    df = df.groupby(cols_for_groupby).sum(numeric_only=True).reset_index()
    # Reorder columns and sort
    cols_to_select = ['Barra Consumo', 'Year', 'Month', 'Hour', 'Consumo']
    cols_to_sort = ['Barra Consumo', 'Year', 'Month', 'Hour']
    df = df[cols_to_select]
    df = df.sort_values(by=cols_to_sort).reset_index(drop=True)
    return df


def get_all_profiles(blo_eta: pd.DataFrame, block2day: pd.DataFrame,
                     df_monthly_demand: pd.DataFrame,
                     df_hourly_profiles: pd.DataFrame,
                     df_dda_por_barra: pd.DataFrame) -> pd.DataFrame:
    '''
    Get all profiles with block resolution for PLP
    '''
    # Turn hourly profiles to profiles by block
    df_blockly_profiles = get_blockly_profiles(df_hourly_profiles, block2day)

    # Merge dataframes
    df = pd.merge(
        df_monthly_demand, df_dda_por_barra, on=['Coordinado', 'Cliente'])
    df = pd.merge(df, df_blockly_profiles, on=['Profile', 'Month'])
    df = pd.merge(df, blo_eta, on=['Year', 'Month', 'Block'])

    # Calculate consumption, group by Barra and sum, reorder and sort
    df = get_consumption_per_barra(df)
    return df


def get_all_profiles_plexos(df_monthly_demand: pd.DataFrame,
                            df_hourly_profiles: pd.DataFrame,
                            df_dda_por_barra: pd.DataFrame) -> pd.DataFrame:
    '''
    Get all profiles with hourly resolution for Plexos
    '''
    # Merge dataframes
    df = pd.merge(
        df_monthly_demand, df_dda_por_barra, on=['Coordinado', 'Cliente'])
    df = pd.merge(df, df_hourly_profiles, on=['Profile', 'Month'])
    # Calculate consumption, group by Barra and sum, reorder and sort
    df = get_consumption_per_barra_plexos(df)
    return df


def write_plpdem_dat(df_all_profiles: pd.DataFrame, iplp_path: Path):

    plpdem_path = iplp_path.parent / 'Temp' / 'plpdem.dat'

    list_all_barras = get_list_of_all_barras(iplp_path)
    list_dem_barras = df_all_profiles['Barra Consumo'].unique().tolist()

    # Translate month to hidromonth
    df_all_profiles = translate_to_hydromonth(df_all_profiles)

    lines = ['# Archivo de demandas por barra (plpdem.dat)']
    lines += ['#  Numero de barras']
    lines += ['%s' % len(list_all_barras)]

    #  Write data from scratch
    write_lines_from_scratch(lines, plpdem_path)

    for barra in list_all_barras:
        lines = ['\n# Nombre de la Barra']
        lines += ["'%s'" % barra]
        lines += ['# Numero de Demandas']
        if barra in list_dem_barras:
            df_aux = df_all_profiles[df_all_profiles['Barra Consumo'] == barra]
            df_aux = df_aux[['Month', 'Etapa', 'Consumo']]
            lines += ['%s' % len(df_aux)]
            if len(df_aux) > 0:
                lines += ['# Mes  Etapa   Demanda']
                # Dataframe to string
                lines += [df_aux.to_string(
                    index=False, header=False, formatters=formatters_plpdem)]
        else:
            lines += ['%s' % 0]
        #  write data for current barra
        write_lines_appending(lines, plpdem_path)


def write_uni_plpdem_dat(df_all_profiles: pd.DataFrame, iplp_path: Path):
    uni_plpdem_path = iplp_path.parent / 'Temp' / 'uni_plpdem.dat'

    # Sum demand of all barras
    df_aggregated = df_all_profiles.groupby(
        ['Year', 'Month', 'Block', 'Etapa']).sum(numeric_only=True)
    df_aggregated = df_aggregated.reset_index()
    df_aggregated = df_aggregated[['Month', 'Etapa', 'Consumo']]

    # Translate month to hidromonth
    df_aggregated = translate_to_hydromonth(df_aggregated)

    # Write lines
    lines = ['# Archivo de demandas por barra (plpdem.dat)']
    lines += ['#  Numero de barras']
    lines += ['001']
    lines += ['# Nombre de la Barra']
    lines += ["'UNINODAL'"]
    lines += ['# Numero de Demandas']
    lines += ['%s' % len(df_aggregated)]
    lines += ['# Mes  Etapa   Demanda']
    lines += [df_aggregated.to_string(
        index=False, header=False, formatters=formatters_plpdem)]

    # Write data from scratch
    write_lines_from_scratch(lines, uni_plpdem_path)


def write_plpfal_prn(blo_eta: pd.DataFrame, df_all_profiles: pd.DataFrame,
                     iplp_path: Path):
    plpfal_path = iplp_path.parent / 'Temp' / 'plpfal.prn'

    df_buses = get_barras_info(iplp_path, add_flag_falla=True)
    df_buses_falla = df_buses[df_buses['FlagFalla']]
    list_dem_barras = df_all_profiles['Barra Consumo'].unique().tolist()

    # Build df with zero-consumption barras
    df_zero_demand = blo_eta[['Month', 'Etapa']].copy()
    df_zero_demand['NIntPot'] = [1] * len(df_zero_demand)
    df_zero_demand['PotMin'] = [0.0] * len(df_zero_demand)
    df_zero_demand['PotMax'] = [0.0] * len(df_zero_demand)

    # Transform df
    df_all_profiles['NIntPot'] = [1] * len(df_all_profiles)
    df_all_profiles['PotMin'] = [0.0] * len(df_all_profiles)
    df_all_profiles = df_all_profiles.rename(columns={'Consumo': 'PotMax'})
    df_all_profiles = df_all_profiles[
        ['Barra Consumo', 'Month', 'Etapa', 'NIntPot', 'PotMin', 'PotMax']]

    # Translate month to hidromonth

    df_all_profiles = translate_to_hydromonth(df_all_profiles)
    df_zero_demand = translate_to_hydromonth(df_zero_demand)

    lines = ['# Archivo de maximos de centrales de falla (plpfal.prn)']

    # Write data from scratch
    write_lines_from_scratch(lines, plpfal_path)

    for _, row in df_buses_falla.iterrows():
        lines = ['\n# Nombre de la central']
        lines += ["'Falla_%03d'" % row['Nº']]
        lines += ['#   Numero de Etapas e Intervalos']
        if row['BARRA'] in list_dem_barras:
            df_aux = df_all_profiles[
                df_all_profiles['Barra Consumo'] == row['BARRA']]
            df_aux = df_aux.drop('Barra Consumo', axis=1)
        else:
            df_aux = df_zero_demand
        lines += ['  %s                 01' % len(df_aux)]
        lines += ['#   Mes    Etapa  NIntPot   PotMin   PotMax']
        lines += [df_aux.to_string(
            index=False, header=False, formatters=formatters_plpfal)]

        #  write data for current barra
        write_lines_appending(lines, plpfal_path)


def print_df_dda_por_barra(path_df: Path, df_dda_por_barra: pd.DataFrame):
    df_dda_por_barra.to_csv(path_df / 'df_dda_por_barra.csv', index=False)


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

    # Add destination folder to logger
    path_log = iplp_path.parent / "Temp" / "log"
    check_is_path(path_log)
    add_file_handler(logger, 'demanda', path_log)

    # Get Hour-Blocks-Etapas definition
    logger.info('Processing block to etapas files')
    blo_eta, _, block2day = process_etapas_blocks(path_dat)

    # Sheet "DdaPorBarra" to row format
    logger.info('Processing DdaPorBarra sheet')
    df_dda_por_barra = dda_por_barra_to_row_format(iplp_path)
    print_df_dda_por_barra(path_df, df_dda_por_barra)

    # Get monthly demand from Sheet "DdaEnergia"
    logger.info('Processing DdaEnergia sheet')
    df_monthly_demand = get_monthly_demand(iplp_path)

    # Get hourly profiles from Sheet "PerfilesDDA"
    logger.info('Processing PerfilesDDA sheet')
    df_hourly_profiles = get_hourly_profiles(iplp_path)

    # Generate dataframe with profiles per Etapa
    logger.info('Generating dataframes with profiles per Etapa per Barra')
    df_all_profiles = get_all_profiles(
        blo_eta, block2day,
        df_monthly_demand, df_hourly_profiles, df_dda_por_barra)

    # Print to plpdem and uni_plpdem
    logger.info('Printing plpdem.dat and uni_plpdem.dat')
    write_plpdem_dat(df_all_profiles, iplp_path)
    write_uni_plpdem_dat(df_all_profiles, iplp_path)

    # Get failure units and generate plpfal.prn
    logger.info('Printing plpfal.prn')
    write_plpfal_prn(blo_eta, df_all_profiles, iplp_path)

    # Plexos outputs
    # Get monthly demand from Sheet "DdaEnergia"
    logger.info('Processing DdaEnergia sheet for plexos')
    df_monthly_demand = get_monthly_demand(iplp_path, plexos=True)

    # Generate dataframe with profiles per Etapa
    logger.info('Generating dataframes with profiles per Etapa per'
                ' Barra for plexos')
    df_all_profiles = get_all_profiles_plexos(
        df_monthly_demand, df_hourly_profiles, df_dda_por_barra)

    # Print df_all_profiles to csv to be used in plexos
    logger.info('Printing df_all_profiles.csv for plexos')
    df_all_profiles.to_csv(path_df / 'df_dda_all_profiles_plexos.csv',
                           index=False)

    logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
