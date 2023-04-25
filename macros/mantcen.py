
import pandas as pd
import sys
from openpyxl.utils.datetime import from_excel
from datetime import datetime

from utils import ( get_project_root,
                    get_iplp_input_path,
                    check_is_path,
                    create_logger,
                    process_etapas_blocks
)


root = get_project_root()
logger = create_logger('mantcen')


def get_centrales(iplp_path):
    df = pd.read_excel(iplp_path, sheet_name="Centrales",
                       skiprows=4, usecols="B,C,AA,AB")
    # Filter out if X
    df = df[df['Tipo de Central'] != 'X']
    df = df.rename(columns={
        'CENTRALES': 'Nombre','Mínima.1': 'Pmin','Máxima.1': 'Pmax'})
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


def read_extra_mant_no_ciclicos(iplp_path):
    # No ciclicos
    df_no_ciclicos = pd.read_excel(
        iplp_path, sheet_name="MantenimientosIM",
        skiprows=1, usecols="B:F").dropna(how='any')
    df_no_ciclicos['Fecha Inicio'] = \
        df_no_ciclicos['Fecha Inicio'].apply(from_excel)
    df_no_ciclicos['Fecha Término'] = \
        df_no_ciclicos['Fecha Término'].apply(from_excel)
    df_no_ciclicos = df_no_ciclicos.rename(
        columns={'Unidad':'Nombre',
                 'Fecha Inicio': 'INICIAL',
                 'Fecha Término': 'FINAL',
                 'Potencia Maxima': 'Pmax'}
    )
    df_no_ciclicos['Pmin'] = 0
    df_no_ciclicos = df_no_ciclicos[['Nombre', 'INICIAL', 'FINAL', 'Pmin', 'Pmax']]
    return df_no_ciclicos


def read_extra_mant_ciclicos(iplp_path, blo_eta):
    # Ciclicos
    df_ciclicos = pd.read_excel(
        iplp_path, sheet_name="MantenimientosIM",
        skiprows=1, usecols="H:M").dropna(how='any')
    df_ciclicos['Fecha Inicio.1'] = \
        df_ciclicos['Fecha Inicio.1'].apply(from_excel)
    df_ciclicos['Fecha Término.1'] = \
        df_ciclicos['Fecha Término.1'].apply(from_excel)
    df_ciclicos = df_ciclicos.rename(
        columns={'Unidad.1':'Nombre',
                 'Fecha Inicio.1': 'INICIAL',
                 'Fecha Término.1': 'FINAL',
                 'Potencia Maxima.1': 'Pmax'}
    )
    df_ciclicos['Pmin'] = 0
    df_ciclicos = df_ciclicos[['Nombre', 'INICIAL', 'FINAL', 'Pmin', 'Pmax']]
    # Repeat yearly, making sure all years are covered
    ini_year = df_ciclicos['INICIAL'].min().year
    end_year = blo_eta.iloc[-1]['Year']
    period_length = end_year - ini_year + 1
    # Build list of df and concat all in one
    list_of_dfs = [df_ciclicos.copy()]
    for offset in range(1, period_length):
        df_offset = df_ciclicos.copy()
        df_offset['INICIAL'] += pd.offsets.DateOffset(years=offset)
        df_offset['FINAL'] += pd.offsets.DateOffset(years=offset)
        list_of_dfs.append(df_offset)
    df_ciclicos = pd.concat(list_of_dfs, ignore_index=True)
    return df_ciclicos


def read_extra_mant_gas(iplp_path):
    # Gas
    df_gas = pd.read_excel(
        iplp_path, sheet_name="MantenimientosIM",
        skiprows=1, usecols="O:AC").dropna(how='any')
    # TODO convert format

    return df_gas

def add_extra_mantcen(iplp_path, df_mantcen, blo_eta):
    '''
    Read directly from MantenimientosIM and add to 
    df_mantcen before generating output:
    No cíclicos, cíclicos, restricciones de gas, genmin
    '''
    df_no_ciclicos = read_extra_mant_no_ciclicos(iplp_path)
    df_ciclicos = read_extra_mant_ciclicos(iplp_path, blo_eta)
    #df_gas = read_extra_mant_gas(iplp_path)

    # Append new dataframes to df_mantcen
    #list_of_dfs = [df_mantcen, df_gas, df_no_ciclicos, df_ciclicos]
    list_of_dfs = [df_mantcen, df_no_ciclicos, df_ciclicos]
    df_mantcen = pd.concat(list_of_dfs, ignore_index=True)
    
    return df_mantcen


def get_pmin_pmax_dict(df_centrales):
    centrales_dict = df_centrales.set_index('Nombre').to_dict()
    return centrales_dict['Pmin'], centrales_dict['Pmax']


def get_daily_indexed_df(blo_eta):
    ini_date = datetime(blo_eta.iloc[0]['Year'], blo_eta.iloc[0]['Month'], 1)
    end_date = datetime(blo_eta.iloc[-1]['Year'], blo_eta.iloc[-1]['Month'], 1)
    index = pd.date_range(start=ini_date, end=end_date, freq='D')
    df = pd.DataFrame(index=index, columns=['Year','Month','Day'])
    df['Year'] = df.index.year
    df['Month'] = df.index.month
    df['Day'] = df.index.day
    df['Date'] = df.index
    df = df.reset_index(drop=True)
    return df


def build_df_pmin_pmax(blo_eta, df_mantcen, df_centrales):
    # Get unit names
    mantcen_unit_names = df_mantcen['Nombre'].unique().tolist()
    # Get pmin/pmax dictionaries
    pmin_dict, pmax_dict = get_pmin_pmax_dict(df_centrales)
    # Get base dataframes
    df_pmin = get_daily_indexed_df(blo_eta)
    # Add empty columns
    df_pmin = df_pmin.reindex(columns=df_pmin.columns.tolist() + mantcen_unit_names)
    # Create df_pmax as copy of empty df_pmin
    df_pmax = df_pmin.copy()
    # Add default values
    df_pmin[mantcen_unit_names] = [pmin_dict[unit] for unit in mantcen_unit_names]
    df_pmax[mantcen_unit_names] = [pmax_dict[unit] for unit in mantcen_unit_names]
    return df_pmin, df_pmax


def get_mantcen_output(blo_eta, df_mantcen, df_centrales):
    # 1. Build default dataframes
    df_pmin, df_pmax = build_df_pmin_pmax(blo_eta, df_mantcen, df_centrales)
    # 2. Add df_mantcen data in row-by-row order
    # Note that filters have a daily resolution
    for _, row in df_mantcen.iterrows():
        mantcen_date_ini = datetime(row['YearIni'], row['MonthIni'], row['DayIni'])
        mantcen_date_end = datetime(row['YearEnd'], row['MonthEnd'], row['DayEnd'])
        pmax_mask_ini = mantcen_date_ini <= df_pmax['Date']
        pmax_mask_end = mantcen_date_end >= df_pmax['Date']
        pmin_mask_ini = mantcen_date_ini <= df_pmin['Date']
        pmin_mask_end = mantcen_date_end >= df_pmin['Date']
        df_pmax.loc[pmax_mask_ini & pmax_mask_end, row['Nombre']] = row['Pmax']
        df_pmin.loc[pmin_mask_ini & pmin_mask_end, row['Nombre']] = row['Pmin']
    # 3. Average per Etapa
    blo_eta = blo_eta.drop('Block_Len', axis=1)
    df_pmax = df_pmax.drop(['Date','Day'], axis=1)
    df_pmin = df_pmin.drop(['Date','Day'], axis=1)
    df_pmax = pd.merge(blo_eta, df_pmax, how='left').groupby(['Etapa','Year','Month','Block']).mean()
    df_pmin = pd.merge(blo_eta, df_pmin, how='left').groupby(['Etapa','Year','Month','Block']).mean()

    return df_pmin, df_pmax


def main():
    '''
    Main routine
    '''
    # Get input file path
    logger.info('Getting input file path')
    iplp_path = get_iplp_input_path()
    path_inputs = iplp_path.parent / "Temp"
    check_is_path(path_inputs)
    path_dat = iplp_path.parent / "Temp" / "Dat"
    check_is_path(path_dat)

    # Get Hour-Blocks-Etapas definition
    logger.info('Processing block to etapas files')
    blo_eta, _, block2day = process_etapas_blocks(path_dat)
    blo_eta = blo_eta.drop(['Tasa'], axis=1)

    # Read Centrales and get PnomMax and PnomMin
    logger.info('Reading data from sheet Centrales')
    df_centrales = get_centrales(iplp_path)
    validate_centrales(df_centrales)

    # Check which units have maintenance
    df_mantcen = get_mantcen_input(iplp_path)

    # LlenadoMantConvenc
    # Read directly from MantenimientosIM and add to df_mantcen before generating output
    # No cíclicos, cíclicos, restricciones de gas, genmin
    df_mantcen = add_extra_mantcen(iplp_path, df_mantcen, blo_eta)

    # Add time info
    df_mantcen = add_time_info(df_mantcen)

    # Validate mantcen
    validate_mantcen(df_centrales, df_mantcen)

    # Generate arrays with pmin/pmax data
    df_pmin, df_pmax = get_mantcen_output(blo_eta, df_mantcen, df_centrales)
    import pdb; pdb.set_trace()

    # Update units with maintenance

    # translate to Etapas/Bloques with HidroMonths

    # count Etapas with maintenance

    # write dat file

    # Write report in sheet (?)

    pass

if __name__ == "__main__":
    main()