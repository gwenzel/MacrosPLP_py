'''Mantcen

Module to generate 'plpmance_ini.dat', which will be used later
to add the renewable energy profiles and generate the definitive
plpmance.dat file
'''
import pandas as pd
import sys
from openpyxl.utils.datetime import from_excel
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pathlib import Path

from utils.utils import (define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         process_etapas_blocks,
                         write_lines_from_scratch,
                         write_lines_appending,
                         translate_to_hydromonth,
                         get_daily_indexed_df,
                         timeit,
                         add_time_info
                         )
from utils.logger import add_file_handler, create_logger

POWER_CHANGE_TOLERANCE = 0.01

logger = create_logger('mantcen')

MONTH2NUMBER = {
    'Ene': 1, 'Feb': 2, 'Mar': 3,
    'Abr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Ago': 8, 'Sep': 9,
    'Oct': 10, 'Nov': 11, 'Dic': 12
}

formatters_plpmance = {
    "Month":    "     {:02d}".format,
    "Etapa":    "     {:04d}".format,
    "NIntPot":  "       {:01d}".format,
    "Pmin":     "{:8.1f}".format,
    "Pmax":     "{:8.1f}".format
}


def get_centrales(iplp_path: Path, plx: bool = False) -> pd.DataFrame:
    df = pd.read_excel(iplp_path, sheet_name="Centrales",
                       skiprows=4, usecols="B,C,AA,AB,DK").dropna(how='all')
    validate_centrales(df)
    # Filter out if X
    df = df[df['Tipo de Central'] != 'X']
    # Rename columns
    df = df.rename(columns={
        'CENTRALES': 'Nombre', 'Mínima.1': 'Pmin', 'Máxima.1': 'Pmax'})
    if plx:
        # Add Reserva to Pmax if Plexos
        df = df.fillna(0)
        df['Pmax'] += df['Reserva MW']
    # Drop all rows without name
    df = df[['Nombre', 'Pmin', 'Pmax']]
    return df


def validate_centrales(df: pd.DataFrame):
    # Check if all columns are present
    expected_columns = [
        'CENTRALES', 'Tipo de Central', 'Mínima.1', 'Máxima.1', 'Reserva MW']
    for col in expected_columns:
        if col not in df.columns:
            raise ValueError('Column %s not found in Centrales' % col)
    if not df['CENTRALES'].is_unique:
        logger.error('List of Centrales has repeated values')
        sys.exit('List of Centrales has repeated values')


def get_mantcen_input(iplp_path: Path) -> pd.DataFrame:
    df = pd.read_excel(iplp_path, sheet_name="MantCEN",
                       skiprows=4, usecols="A:F").dropna(how='any')
    validate_mantcen_ini(df)
    df = df.rename(
        columns={
            df.columns[0]: 'Description',
            'CENTRAL': 'Nombre',
            'MÍNIMA': 'Pmin',
            'MÁXIMA': 'Pmax'
        }
    )
    # Drop all rows without description
    df = df[df['Description'] != 'Mantenimientos']
    # Add columns with more info
    df['INICIAL'] = df['INICIAL'].apply(from_excel)
    df['FINAL'] = df['FINAL'].apply(from_excel)
    return df


def validate_mantcen_ini(df: pd.DataFrame):
    # Check if columns are present
    expected_columns = ['CENTRAL', 'INICIAL', 'FINAL', 'MÍNIMA', 'MÁXIMA']
    for col in expected_columns:
        if col not in df.columns:
            raise ValueError('Column %s not found in MantCen' % col)
    # Check if values in INICIAL and FINAL columns are integers or floats
    if not all([isinstance(x, int) or isinstance(x, float)
                for x in df['INICIAL']]):
        raise ValueError('INICIAL values are not integers')
    if not all([isinstance(x, int) or isinstance(x, float)
                for x in df['FINAL']]):
        raise ValueError('FINAL values are not integers')


def validate_mantcen_processed(df_centrales: pd.DataFrame,
                               df_mantcen: pd.DataFrame):
    # Names
    list_of_names_centrales = df_centrales['Nombre'].unique().tolist()
    list_of_names_mantcen = df_mantcen['Nombre'].unique().tolist()
    for name in list_of_names_mantcen:
        if name not in list_of_names_centrales:
            raise ValueError('Name of unit %s in MantCEN not valid' % name)
    # Values
    if not all(df_mantcen['INICIAL'] < df_mantcen['FINAL']):
        logger.warning('INICIAL date values are not less than FINAL'
                       ' date values')
    # Check if Pmin and Pmax are floats
    if not all([isinstance(x, float) for x in df_mantcen['Pmin']]):
        raise ValueError('Pmin values are not floats')
    # Check if Pmin < Pmax
    if not all(df_mantcen['Pmin'] <= df_mantcen['Pmax']):
        raise ValueError('There are Pmin values greater than Pmax values')
    logger.info('Validation process for processed MantCEN successful')


def shape_extra_mant_no_gas(df: pd.DataFrame,
                            description: str = 'NA') -> pd.DataFrame:
    df['INICIAL'] = df['INICIAL'].apply(from_excel)
    df['FINAL'] = df['FINAL'].apply(from_excel)
    df['Description'] = description
    df['Pmin'] = 0
    reordered_cols = ['Description', 'Nombre',
                      'INICIAL', 'FINAL', 'Pmin', 'Pmax']
    return df[reordered_cols]


def read_extra_mant_no_ciclicos(iplp_path: Path) -> pd.DataFrame:
    # No ciclicos
    df_no_ciclicos = pd.read_excel(
        iplp_path, sheet_name="MantenimientosIM",
        skiprows=1, usecols="B:D,F").dropna(how='any')
    validate__mant_no_ciclicos(df_no_ciclicos)
    df_no_ciclicos = df_no_ciclicos.rename(
        columns={'Unidad': 'Nombre',
                 'Fecha Inicio': 'INICIAL',
                 'Fecha Término': 'FINAL',
                 'Potencia Maxima': 'Pmax'}
    )
    df_no_ciclicos = shape_extra_mant_no_gas(
        df_no_ciclicos, description='No Cíclicos')
    return df_no_ciclicos


def validate__mant_no_ciclicos(df: pd.DataFrame):
    # Check if columns are 'Unidad', 'Fecha Inicio', 'Fecha Término',
    # and 'Potencia Maxima'
    expected_columns = ['Unidad', 'Fecha Inicio', 'Fecha Término',
                        'Potencia Maxima']
    for col in expected_columns:
        if col not in df.columns:
            raise ValueError('Column %s not found in MantenimientosIM' % col)
    # Check if values in Fecha Inicio and Fecha Término columns are integers
    # or floats
    if not all([isinstance(x, int) or isinstance(x, float)
                for x in df['Fecha Inicio']]):
        raise ValueError('Fecha Inicio values are not integers')
    if not all([isinstance(x, int) or isinstance(x, float)
                for x in df['Fecha Término']]):
        raise ValueError('Fecha Término values are not integers')
    # Check if values in Potencia Maxima are floats
    if not all([isinstance(x, float) for x in df['Potencia Maxima']]):
        raise ValueError('Potencia Maxima values are not floats')
    logger.info('Validation process for MantCEN No Cíclicos successful')


def read_extra_mant_ciclicos(iplp_path: Path,
                             blo_eta: pd.DataFrame) -> pd.DataFrame:
    # Ciclicos
    df_ciclicos = pd.read_excel(
        iplp_path, sheet_name="MantenimientosIM",
        skiprows=1, usecols="I:K,M").dropna(how='any')
    validate_mant_ciclicos(df_ciclicos)
    df_ciclicos = df_ciclicos.rename(
        columns={'Unidad.1': 'Nombre',
                 'Fecha Inicio.1': 'INICIAL',
                 'Fecha Término.1': 'FINAL',
                 'Potencia Maxima.1': 'Pmax'}
    )
    df_ciclicos = shape_extra_mant_no_gas(
        df_ciclicos, description='Cíclicos')
    # Check if df is not empty
    if len(df_ciclicos) > 0:
        # Repeat yearly, making sure all years are covered
        ini_year = df_ciclicos['INICIAL'].min().year
        end_year = blo_eta.iloc[-1]['Year']
        period_length = end_year - ini_year + 1
        # Build list of df and concat all in one
        list_of_dfs = []
        for offset in range(period_length):
            df_offset = df_ciclicos.copy()
            df_offset['INICIAL'] += pd.offsets.DateOffset(years=offset)
            df_offset['FINAL'] += pd.offsets.DateOffset(years=offset)
            list_of_dfs.append(df_offset)
        df_ciclicos = pd.concat(list_of_dfs, ignore_index=True)
    return df_ciclicos


def validate_mant_ciclicos(df: pd.DataFrame):
    # Check if columns are 'Unidad.1', 'Fecha Inicio.1', 'Fecha Término.1',
    # and 'Potencia Maxima.1'
    expected_columns = ['Unidad.1', 'Fecha Inicio.1', 'Fecha Término.1',
                        'Potencia Maxima.1']
    for col in expected_columns:
        if col not in df.columns:
            raise ValueError('Column %s not found in MantenimientosIM' % col)
    # Check if values in Fecha Inicio and Fecha Término columns are integers
    # or floats
    if not all([isinstance(x, int) or isinstance(x, float)
                for x in df['Fecha Inicio.1']]):
        raise ValueError('Fecha Inicio values are not integers')
    if not all([isinstance(x, int) or isinstance(x, float)
                for x in df['Fecha Término.1']]):
        raise ValueError('Fecha Término values are not integers')
    # Check if values in Potencia Maxima are floats
    if not all([isinstance(x, float) for x in df['Potencia Maxima.1']]):
        raise ValueError('Potencia Maxima values are not floats')
    logger.info('Validation process for MantCEN Cíclicos successful')


def validate_mant_gas(df: pd.DataFrame):
    # Check if columns are [AnoInic, AnoFinal, Ene, Feb, Mar, Abr, May, Jun,
    # Jul, Ago, Sep, Oct, Nov, Dic]
    expected_columns = ['AnoInic', 'AnoFinal', 'Ene', 'Feb', 'Mar', 'Abr',
                        'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    for col in expected_columns:
        if col not in df.columns:
            raise ValueError('Column %s not found in MantenimientosIM' % col)
    # Check if values in AnoInic and AnoFinal columns are integers
    if not all([isinstance(x, int) for x in df['AnoInic']]):
        raise ValueError('AnoInic values are not integers')
    if not all([isinstance(x, int) for x in df['AnoFinal']]):
        raise ValueError('AnoFinal values are not integers')
    # Check if values in other columns are floats
    for col in expected_columns[2:]:
        if not all([isinstance(x, float) for x in df[col]]):
            raise ValueError('%s values are not floats' % col)
    logger.info('Validation process for MantCEN Gas successful')


def add_extra_mantcen(iplp_path: Path, df_mantcen: pd.DataFrame,
                      blo_eta: pd.DataFrame) -> pd.DataFrame:
    '''
    Read directly from MantenimientosIM and add to
    df_mantcen before generating output:
    No cíclicos, cíclicos, restricciones de gas, genmin
    '''
    df_no_ciclicos = read_extra_mant_no_ciclicos(iplp_path)
    df_ciclicos = read_extra_mant_ciclicos(iplp_path, blo_eta)
    # Append new dataframes to df_mantcen if they are not empty
    list_of_dfs = []
    for df in [df_mantcen, df_no_ciclicos, df_ciclicos]:
        if len(df) > 0:
            list_of_dfs.append(df)
    df_mantcen = pd.concat(list_of_dfs, ignore_index=True)
    return df_mantcen


def filter_df_mantcen(df_mantcen: pd.DataFrame,
                      df_centrales: pd.DataFrame) -> pd.DataFrame:
    '''
    Filter out rows with non-existent Unit names and ERNC and BESS
    '''
    types_to_filter = ['SOLAR_', 'SOLARx_', 'ENGIE_PV',
                       'EOLICA_', 'EOLICAx_', 'ENGIE_Wind',
                       'BESS_', 'BESSx_', 'ENGIE_BESS_',
                       'CSP_', 'CSPx_']
    for type in types_to_filter:
        df_mantcen = df_mantcen[~df_mantcen['Nombre'].str.startswith(type)]
    return df_mantcen[df_mantcen['Nombre'].isin(df_centrales['Nombre'])]


def get_pmin_pmax_dict(df_centrales: pd.DataFrame) -> tuple[dict, dict]:
    '''
    Get dictionary with Pmin and Pmax for each unit
    '''
    centrales_dict = df_centrales.set_index('Nombre').to_dict()
    return centrales_dict['Pmin'], centrales_dict['Pmax']


def build_df_pmin_pmax(blo_eta: pd.DataFrame, df_mantcen: pd.DataFrame,
                       df_centrales: pd.DataFrame) -> \
                       tuple[pd.DataFrame, pd.DataFrame]:
    '''
    Build matrix with all pmin/pmax info in mantcen sheet
    '''
    # Get  unit names
    mantcen_unit_names = df_mantcen['Nombre'].unique().tolist()
    # Get pmin/pmax dictionaries
    pmin_dict, pmax_dict = get_pmin_pmax_dict(df_centrales)
    # Get base dataframes
    df_pmin = get_daily_indexed_df(blo_eta)
    # Add empty columns
    df_pmin = df_pmin.reindex(
        columns=df_pmin.columns.tolist() + mantcen_unit_names)
    # Create df_pmax as copy of empty df_pmin
    df_pmax = df_pmin.copy()
    # Add default values
    df_pmin[mantcen_unit_names] = [
        pmin_dict[unit] for unit in mantcen_unit_names]
    df_pmax[mantcen_unit_names] = [
        pmax_dict[unit] for unit in mantcen_unit_names]
    return df_pmin, df_pmax


def get_mantcen_output(blo_eta: pd.DataFrame, df_mantcen: pd.DataFrame,
                       df_centrales: pd.DataFrame,
                       plp_or_plexos: str = 'PLP') -> \
                       tuple[pd.DataFrame, pd.DataFrame]:
    # 1. Build default dataframes
    df_pmin, df_pmax = build_df_pmin_pmax(blo_eta, df_mantcen, df_centrales)
    # 2. Add df_mantcen data in row-by-row order
    # Note that filters have a daily resolution
    mantcen_dates_ini = pd.to_datetime(
        df_mantcen[['YearIni', 'MonthIni', 'DayIni']].rename(columns={
            'YearIni': 'year', 'MonthIni': 'month', 'DayIni': 'day'}))
    mantcen_dates_end = pd.to_datetime(
        df_mantcen[['YearEnd', 'MonthEnd', 'DayEnd']].rename(columns={
            'YearEnd': 'year', 'MonthEnd': 'month', 'DayEnd': 'day'}))
    for i in range(len(mantcen_dates_ini)):
        pmax_mask_ini = mantcen_dates_ini.iloc[i] <= df_pmax['Date']
        pmax_mask_end = mantcen_dates_end.iloc[i] >= df_pmax['Date']
        pmin_mask_ini = mantcen_dates_ini.iloc[i] <= df_pmin['Date']
        pmin_mask_end = mantcen_dates_end.iloc[i] >= df_pmin['Date']
        df_pmax.loc[pmax_mask_ini & pmax_mask_end,
                    df_mantcen.iloc[i]['Nombre']] = df_mantcen.iloc[i]['Pmax']
        df_pmin.loc[pmin_mask_ini & pmin_mask_end,
                    df_mantcen.iloc[i]['Nombre']] = df_mantcen.iloc[i]['Pmin']
    if plp_or_plexos == 'PLP':
        # 3. Average per Etapa and drop Day column
        on_cols = ['Month', 'Year']
        groupby_cols = ['Etapa', 'Year', 'Month', 'Block', 'Block_Len']
        df_pmax_plp = pd.merge(blo_eta, df_pmax, how='left', on=on_cols)\
            .groupby(groupby_cols)\
            .mean(numeric_only=True)\
            .drop(['Day'], axis=1)
        df_pmin_plp = pd.merge(blo_eta, df_pmin, how='left', on=on_cols)\
            .groupby(groupby_cols)\
            .mean(numeric_only=True)\
            .drop(['Day'], axis=1)
        return df_pmin_plp, df_pmax_plp
    elif plp_or_plexos == 'PLEXOS':
        # 3. Get daily output for plexos
        groupby_cols = ['Year', 'Month', 'Day']
        df_pmax_plexos = df_pmax.groupby(groupby_cols).mean(numeric_only=True)
        df_pmin_plexos = df_pmin.groupby(groupby_cols).mean(numeric_only=True)
        return df_pmin_plexos, df_pmax_plexos
    else:
        sys.exit('plp_or_plexos must be either PLP or PLEXOS')


def build_df_aux(df_pmin_unit: pd.DataFrame, df_pmax_unit: pd.DataFrame,
                 pmin_unit: float, pmax_unit: float) -> pd.DataFrame:
    df_aux = pd.merge(df_pmin_unit, df_pmax_unit)
    # Keep rows only if pmin or pmax are not default values
    pmin_not_default = (abs(df_pmin_unit['Pmin'] - pmin_unit) >=
                        POWER_CHANGE_TOLERANCE)
    pmax_not_default = (abs(df_pmax_unit['Pmax'] - pmax_unit) >=
                        POWER_CHANGE_TOLERANCE)
    df_aux = df_aux[pmin_not_default | pmax_not_default]
    # Reorder columns and add NIntPot
    df_aux['NIntPot'] = 1
    return df_aux[['Month', 'Etapa', 'NIntPot', 'Pmin', 'Pmax']]


def get_mantcen_data(list_mantcen: list,
                     df_pmin: pd.DataFrame, df_pmax: pd.DataFrame,
                     pmin_dict: dict, pmax_dict: dict) -> tuple[
                        list, int]:
    '''
    Return text lines with mantcen data for all units
    '''
    lines = []
    number_of_units = 0
    for unit in list_mantcen:
        # Build df_aux from both dataframes, for each unit
        df_pmin_unit = df_pmin[['Month', 'Etapa', unit]]\
            .rename(columns={unit: 'Pmin'})
        df_pmax_unit = df_pmax[['Month', 'Etapa', unit]]\
            .rename(columns={unit: 'Pmax'})
        df_aux = build_df_aux(df_pmin_unit, df_pmax_unit,
                              pmin_dict[unit], pmax_dict[unit])
        if len(df_aux) > 0:
            number_of_units += 1
            lines += ['# Nombre de la central']
            lines += ["'%s'" % unit]
            lines += ['#   Numero de Bloques e Intervalos']
            lines += ['  %04d                 01' % len(df_aux)]
            lines += ['#   Mes    Bloque  NIntPot   PotMin   PotMax']
            # Add data as string using predefined format
            lines += [df_aux.to_string(
                index=False, header=False, formatters=formatters_plpmance)]
    return lines, number_of_units


def get_header_data(number_of_units: int) -> list:
    '''
    Return text lines for dat file header
    '''
    lines = ['# Archivo de mantenimientos de centrales (plpmance.dat)']
    lines += ['# numero de centrales con matenimientos']
    lines += ['  %s\n' % number_of_units]
    return lines


def write_plpmance_ini_dat(df_centrales: pd.DataFrame,
                           df_pmin: pd.DataFrame, df_pmax: pd.DataFrame,
                           iplp_path: Path, path_df: Path,
                           printdata: bool = False):
    '''
    Write plpmance_ini.dat file, which will be used later to add the
    renewable energy profiles and generate the definitive
    plpmance.dat file
    '''
    plpmance_path = iplp_path.parent / 'Temp' / 'plpmance_ini.dat'

    list_mantcen = list(df_pmin.columns)

    # Get ['Etapa','Year','Month','Block'] as columns
    df_pmax = df_pmax.reset_index()
    df_pmin = df_pmin.reset_index()

    # Translate month to hidromonth
    df_pmax = translate_to_hydromonth(df_pmax)
    df_pmin = translate_to_hydromonth(df_pmin)

    # Print data if requested
    if printdata:
        df_pmax.to_csv(path_df / 'df_mantcen_pmax.csv', index=False)
        df_pmin.to_csv(path_df / 'df_mantcen_pmin.csv', index=False)

    # Read dicts
    pmin_dict, pmax_dict = get_pmin_pmax_dict(df_centrales)

    # Get mantcen data
    lines_units, number_of_units = get_mantcen_data(
        list_mantcen, df_pmin, df_pmax, pmin_dict, pmax_dict)
    lines_header = get_header_data(number_of_units)

    # Write dat file from scratch
    write_lines_from_scratch(lines_header, plpmance_path)
    # Write data for all units
    write_lines_appending(lines_units, plpmance_path)


def write_plexos(df_pmin_plexos: pd.DataFrame,
                 df_pmax_plexos: pd.DataFrame,
                 path_df: Path):
    '''
    Write dataframes in plexos format
    '''
    df_pmax_plexos.round(2).to_csv(path_df / 'df_mantcen_pmax_plexos.csv')
    df_pmin_plexos.round(2).to_csv(path_df / 'df_mantcen_pmin_plexos.csv')


@timeit
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

        # Add destination folder to logger
        path_log = iplp_path.parent / "Temp" / "log"
        check_is_path(path_log)
        add_file_handler(logger, 'mantcen', path_log)

        # Get Hour-Blocks-Etapas definition
        logger.info('Processing block to etapas files')
        blo_eta, _, _ = process_etapas_blocks(path_dat)

        # Read Centrales and get PnomMax and PnomMin
        logger.info('Reading data from sheet Centrales')
        df_centrales = get_centrales(iplp_path)

        # Get initial mantcen dataframe
        logger.info('Getting initial mantcen')
        df_mantcen = get_mantcen_input(iplp_path)

        # LlenadoMantConvenc
        # Read directly from MantenimientosIM and add to df_mantcen before
        # generating output
        # No cíclicos, cíclicos, restricciones de gas, genmin
        logger.info('Adding extra maintenance (order: non cyclic, cyclic)')
        df_mantcen = add_extra_mantcen(iplp_path, df_mantcen, blo_eta)

        logger.info('Filtering required')
        df_mantcen = filter_df_mantcen(df_mantcen, df_centrales)

        # Add time info
        logger.info('Adding time info')
        df_mantcen = add_time_info(df_mantcen)

        # Validate mantcen
        logger.info('Validating Mantcen processed data')
        validate_mantcen_processed(df_centrales, df_mantcen)

        # PLP
        # Generate arrays with pmin/pmax data
        logger.info('Generating pmin and pmax data PLP')
        df_pmin_plp, df_pmax_plp = \
            get_mantcen_output(blo_eta, df_mantcen, df_centrales,
                               plp_or_plexos='PLP')
        # Write data
        logger.info('Writing data to plpmance_ini.dat file')
        write_plpmance_ini_dat(df_centrales,
                               df_pmin_plp, df_pmax_plp,
                               iplp_path, path_df,
                               printdata=True)
        # Plexos
        # Generate arrays with pmin/pmax data
        # Redefine nominal Pmax for Plexos, adding reserves
        df_centrales = get_centrales(iplp_path, plx=True)
        logger.info('Generating pmin and pmax data Plexos')
        df_pmin_plexos, df_pmax_plexos = \
            get_mantcen_output(blo_eta, df_mantcen, df_centrales,
                               plp_or_plexos='PLEXOS')
        # Write data
        logger.info('Writing data to plexos csv files')
        write_plexos(df_pmin_plexos, df_pmax_plexos, path_df)

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
