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

from utils.utils import (define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         create_logger,
                         process_etapas_blocks,
                         write_lines_from_scratch,
                         write_lines_appending,
                         translate_to_hydromonth,
                         timeit
                         )


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
    "Pmin":     "{:8.2f}".format,
    "Pmax":     "{:8.2f}".format
}


def get_centrales(iplp_path):
    df = pd.read_excel(iplp_path, sheet_name="Centrales",
                       skiprows=4, usecols="B,C,AA,AB")
    # Filter out if X
    df = df[df['Tipo de Central'] != 'X']
    df = df.rename(columns={
        'CENTRALES': 'Nombre', 'Mínima.1': 'Pmin', 'Máxima.1': 'Pmax'})
    df = df[['Nombre', 'Pmin', 'Pmax']]
    return df


def get_mantcen_input(iplp_path):
    df = pd.read_excel(iplp_path, sheet_name="MantCEN",
                       skiprows=4, usecols="A:F")
    df = df.rename(
        columns={
            df.columns[0]: 'Description',
            'CENTRAL': 'Nombre',
            'MÍNIMA': 'Pmin',
            'MÁXIMA': 'Pmax'
        }
    )
    # Drop all rows without description
    df = df.dropna(how='any')
    df = df[df['Description'] != 'Mantenimientos']
    # Add columns with more info
    df['INICIAL'] = df['INICIAL'].apply(from_excel)
    df['FINAL'] = df['FINAL'].apply(from_excel)
    return df


def add_time_info(df_mantcen):
    df_mantcen['YearIni'] = df_mantcen['INICIAL'].dt.year
    df_mantcen['MonthIni'] = df_mantcen['INICIAL'].dt.month
    df_mantcen['DayIni'] = df_mantcen['INICIAL'].dt.day
    df_mantcen['YearEnd'] = df_mantcen['FINAL'].dt.year
    df_mantcen['MonthEnd'] = df_mantcen['FINAL'].dt.month
    df_mantcen['DayEnd'] = df_mantcen['FINAL'].dt.day
    return df_mantcen


def validate_centrales(df_centrales):
    if not df_centrales['Nombre'].is_unique:
        logger.error('List of Centrales has repeated values')
        sys.exit('List of Centrales has repeated values')
    logger.info('Validation process for Centrales successful')


def validate_mantcen(df_centrales, df_mantcen):
    # Names
    list_of_names_centrales = df_centrales['Nombre'].unique().tolist()
    list_of_names_mantcen = df_mantcen['Nombre'].unique().tolist()
    for name in list_of_names_mantcen:
        if name not in list_of_names_centrales:
            logger.error('Name of unit %s in MantCEN not valid' % name)
            sys.exit('Name of unit %s in MantCEN not valid' % name)
    # Values
    # TODO Check that INICIAL < FINAL
    # TODO Check that Pmin and Pmax are coherent and in range
    # TODO Check that DayIni and DayEnd equals DaysInMonth
    logger.info('Validation process for MantCEN successful')


def shape_extra_mant_no_gas(df, description='NA'):
    df['INICIAL'] = df['INICIAL'].apply(from_excel)
    df['FINAL'] = df['FINAL'].apply(from_excel)
    df['Description'] = description
    df['Pmin'] = 0
    reordered_cols = ['Description', 'Nombre',
                      'INICIAL', 'FINAL', 'Pmin', 'Pmax']
    return df[reordered_cols]


def read_extra_mant_no_ciclicos(iplp_path):
    # No ciclicos
    df_no_ciclicos = pd.read_excel(
        iplp_path, sheet_name="MantenimientosIM",
        skiprows=1, usecols="B:D,F").dropna(how='any')
    df_no_ciclicos = df_no_ciclicos.rename(
        columns={'Unidad': 'Nombre',
                 'Fecha Inicio': 'INICIAL',
                 'Fecha Término': 'FINAL',
                 'Potencia Maxima': 'Pmax'}
    )
    df_no_ciclicos = shape_extra_mant_no_gas(
        df_no_ciclicos, description='No Cíclicos')
    return df_no_ciclicos


def read_extra_mant_ciclicos(iplp_path, blo_eta):
    # Ciclicos
    df_ciclicos = pd.read_excel(
        iplp_path, sheet_name="MantenimientosIM",
        skiprows=1, usecols="I:K,M").dropna(how='any')
    df_ciclicos = df_ciclicos.rename(
        columns={'Unidad.1': 'Nombre',
                 'Fecha Inicio.1': 'INICIAL',
                 'Fecha Término.1': 'FINAL',
                 'Potencia Maxima.1': 'Pmax'}
    )
    df_ciclicos = shape_extra_mant_no_gas(
        df_ciclicos, description='Cíclicos')
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


def read_extra_mant_gas(iplp_path, blo_eta):
    end_year = blo_eta.iloc[-1]['Year']
    # Gas
    df_gas = pd.read_excel(
        iplp_path, sheet_name="MantenimientosIM",
        skiprows=1, usecols="O:AC", index_col=0).dropna(how='any')
    df_gas = df_gas.replace('*', str(end_year))
    dict_out = {'Nombre': [], 'INICIAL': [], 'FINAL': [],
                'Pmin': [], 'Pmax': []}
    for idx_unit, row in df_gas.iterrows():
        for year in range(int(row['AnoInic']), int(row['AnoFinal']) + 1):
            for month, monthnum in MONTH2NUMBER.items():
                date_ini = datetime(year, monthnum, 1)
                date_end = date_ini + \
                    relativedelta(months=+1) - timedelta(days=1)
                dict_out['Nombre'].append(idx_unit)
                dict_out['INICIAL'].append(date_ini)
                dict_out['FINAL'].append(date_end)
                dict_out['Pmin'].append(0)
                dict_out['Pmax'].append(row[month])
    df_out = pd.DataFrame.from_dict(dict_out)
    df_out['Description'] = 'Gas'
    return df_out


def add_extra_mantcen(iplp_path, df_mantcen, blo_eta):
    '''
    Read directly from MantenimientosIM and add to
    df_mantcen before generating output:
    No cíclicos, cíclicos, restricciones de gas, genmin
    '''
    df_no_ciclicos = read_extra_mant_no_ciclicos(iplp_path)
    df_ciclicos = read_extra_mant_ciclicos(iplp_path, blo_eta)
    df_gas = read_extra_mant_gas(iplp_path, blo_eta)
    # Append new dataframes to df_mantcen
    list_of_dfs = [df_mantcen, df_gas, df_no_ciclicos, df_ciclicos]
    df_mantcen = pd.concat(list_of_dfs, ignore_index=True)
    return df_mantcen


def filter_df_mantcen(df_mantcen, df_centrales):
    '''
    Filter out rows with non-existent Unit names
    '''
    return df_mantcen[df_mantcen['Nombre'].isin(df_centrales['Nombre'])]


def get_pmin_pmax_dict(df_centrales):
    centrales_dict = df_centrales.set_index('Nombre').to_dict()
    return centrales_dict['Pmin'], centrales_dict['Pmax']


def get_daily_indexed_df(blo_eta):
    ini_date = datetime(blo_eta.iloc[0]['Year'], blo_eta.iloc[0]['Month'], 1)
    end_date = datetime(blo_eta.iloc[-1]['Year'], blo_eta.iloc[-1]['Month'], 1)
    index = pd.date_range(start=ini_date, end=end_date, freq='D')
    df = pd.DataFrame(index=index, columns=['Year', 'Month', 'Day'])
    df['Year'] = df.index.year
    df['Month'] = df.index.month
    df['Day'] = df.index.day
    df['Date'] = df.index
    df = df.reset_index(drop=True)
    return df


def build_df_pmin_pmax(blo_eta, df_mantcen, df_centrales):
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


def get_mantcen_output(blo_eta, df_mantcen, df_centrales):
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
    # 3. Average per Etapa and drop Day column
    on_cols = ['Month', 'Year']
    groupby_cols = ['Etapa', 'Year', 'Month', 'Block', 'Block_Len']
    df_pmax = pd.merge(blo_eta, df_pmax, how='left', on=on_cols).groupby(
        groupby_cols).mean(numeric_only=True).drop(['Day'], axis=1)
    df_pmin = pd.merge(blo_eta, df_pmin, how='left', on=on_cols).groupby(
        groupby_cols).mean(numeric_only=True).drop(['Day'], axis=1)
    return df_pmin, df_pmax


def build_df_aux(df_pmin, df_pmax, unit):
    df_aux_pmin = df_pmin[['Month', 'Etapa', unit]].copy()
    df_aux_pmin = df_aux_pmin.rename(columns={unit: 'Pmin'})
    df_aux_pmax = df_pmax[['Month', 'Etapa', unit]].copy()
    df_aux_pmax = df_aux_pmax.rename(columns={unit: 'Pmax'})
    df_aux = pd.merge(df_aux_pmin, df_aux_pmax)
    df_aux['NIntPot'] = 1
    # Reorder columns
    return df_aux[['Month', 'Etapa', 'NIntPot', 'Pmin', 'Pmax']]


def write_plpmance_ini_dat(df_pmin, df_pmax, iplp_path, printdata=False):
    '''
    Write plpmance_ini.dat file, which will be used later to add the
    renewable energy profiles and generate the definitive
    plpmance.dat file
    '''
    plpmance_path = iplp_path.parent / 'Temp' / 'plpmance_ini.dat'

    list_mantcen = list(df_pmin.columns)
    num_blo = len(df_pmin)

    # Get ['Etapa','Year','Month','Block'] as columns
    df_pmax = df_pmax.reset_index()
    df_pmin = df_pmin.reset_index()

    # Translate month to hidromonth
    df_pmax = translate_to_hydromonth(df_pmax)
    df_pmin = translate_to_hydromonth(df_pmin)

    # Print data if requested
    if printdata:
        df_pmax.to_csv(iplp_path.parent / 'Temp' / 'mantcen_pmax.csv')
        df_pmin.to_csv(iplp_path.parent / 'Temp' / 'mantcen_pmin.csv')

    lines = ['# Archivo de mantenimientos de centrales (plpmance.dat)']
    lines += ['# numero de centrales con matenimientos']
    lines += ['  %s' % len(list_mantcen)]

    # Write dat file from scratch
    write_lines_from_scratch(lines, plpmance_path)

    for unit in list_mantcen:
        lines = ['\n# Nombre de la central']
        lines += ["'%s'" % unit]
        lines += ['#   Numero de Bloques e Intervalos']
        lines += ['  %04d                 01' % num_blo]
        lines += ['#   Mes    Bloque  NIntPot   PotMin   PotMax']
        # Build df_aux from both dataframes, for each unit
        df_aux = build_df_aux(df_pmin, df_pmax, unit)
        # Add data as string using predefined format
        lines += [df_aux.to_string(
            index=False, header=False, formatters=formatters_plpmance)]
        # Write data for current unit
        write_lines_appending(lines, plpmance_path)


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

    # Get Hour-Blocks-Etapas definition
    logger.info('Processing block to etapas files')
    blo_eta, _, _ = process_etapas_blocks(path_dat)
    blo_eta = blo_eta.drop(['Tasa'], axis=1)

    # Read Centrales and get PnomMax and PnomMin
    logger.info('Reading data from sheet Centrales')
    df_centrales = get_centrales(iplp_path)

    logger.info('Validating list of centrales')
    validate_centrales(df_centrales)

    # Get initial mantcen dataframe
    logger.info('Getting initial mantcen')
    df_mantcen = get_mantcen_input(iplp_path)

    # LlenadoMantConvenc
    # Read directly from MantenimientosIM and add to df_mantcen before
    # generating output
    # No cíclicos, cíclicos, restricciones de gas, genmin
    logger.info('Adding extra maintenance (cyclic, non cyclic, gas)')
    df_mantcen = add_extra_mantcen(iplp_path, df_mantcen, blo_eta)

    df_mantcen = filter_df_mantcen(df_mantcen, df_centrales)

    # Add time info
    logger.info('Adding time info')
    df_mantcen = add_time_info(df_mantcen)

    # Validate mantcen
    logger.info('Validating mantcen data')
    validate_mantcen(df_centrales, df_mantcen)

    # Generate arrays with pmin/pmax data
    logger.info('Generating pmin and pmax data')
    df_pmin, df_pmax = get_mantcen_output(blo_eta, df_mantcen, df_centrales)

    # Write data
    logger.info('Writing data to plpmance_ini.dat file')
    write_plpmance_ini_dat(df_pmin, df_pmax, iplp_path, printdata=True)

    logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
