
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


def get_pmin_pmax(iplp_path):
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
    df['YearIni'] = df['INICIAL'].dt.year
    df['MonthIni'] = df['INICIAL'].dt.month
    df['DayIni'] = df['INICIAL'].dt.day
    df['YearEnd'] = df['FINAL'].dt.year
    df['MonthEnd'] = df['FINAL'].dt.month
    df['DayEnd'] = df['FINAL'].dt.day
    return df


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


def get_mantcen_output(blo_eta, df_mantcen, df_centrales):
    # 1. Build default dataframes
    mantcen_unit_names = df_mantcen['Nombre'].unique().tolist()
    #   Get pmin/pmax dictionaries
    pmin_dict = df_centrales.set_index('Nombre').to_dict()['Pmin']
    pmax_dict = df_centrales.set_index('Nombre').to_dict()['Pmax']
    #   Get base dataframes
    df_pmin = blo_eta.copy()
    df_pmax = blo_eta.copy()
    #   Add Ini/End of each month in datetime
    df_pmin['DateIni'] = df_pmin.apply(
        lambda x: datetime(x['Year'], x['Month'], 1), axis=1)
    df_pmin['DateEnd'] = df_pmin.apply(
        lambda x: datetime(x['Year'], x['Month'], x['DateIni'].days_in_month), axis=1)
    df_pmax['DateIni'] = df_pmax.apply(
        lambda x: datetime(x['Year'], x['Month'], 1), axis=1)
    df_pmax['DateEnd'] = df_pmax.apply(
        lambda x: datetime(x['Year'], x['Month'], x['DateIni'].days_in_month), axis=1)
    #   Build dataframes to concat
    new_cols = mantcen_unit_names
    new_vals_pmin = [pmin_dict[unit] for unit in mantcen_unit_names]
    new_vals_pmax = [pmax_dict[unit] for unit in mantcen_unit_names]
    #   Add empty columns
    df_pmin = df_pmin.reindex(columns=df_pmin.columns.tolist() + new_cols)
    df_pmax = df_pmax.reindex(columns=df_pmax.columns.tolist() + new_cols)
    #   Add default values
    df_pmin[new_cols] = new_vals_pmin
    df_pmax[new_cols] = new_vals_pmax

    # 2. Add df_mantcen data in row-by-row order
    for _, row in df_mantcen.iterrows():
        mantcen_date_ini = datetime(row['YearIni'], row['MonthIni'], row['DayIni'])
        mantcen_date_end = datetime(row['YearEnd'], row['MonthEnd'], row['DayEnd'])
        pmax_mask_ini = mantcen_date_ini <= df_pmax['DateIni']
        pmax_mask_end = mantcen_date_end >= df_pmax['DateEnd']
        pmin_mask_ini = mantcen_date_ini <= df_pmin['DateIni']
        pmin_mask_end = mantcen_date_end >= df_pmin['DateEnd']
        df_pmax.loc[pmax_mask_ini & pmax_mask_end, row['Nombre']] = row['Pmax']
        df_pmin.loc[pmin_mask_ini & pmin_mask_end, row['Nombre']] = row['Pmin']

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

    # LlenadoMantConvenc
    # Read directly from MantenimientosIM and add to df_mantcen before generating output
    # No cíclicos, cíclicos, restricciones de gas, genmin

    # Read Centrales and get PnomMax and PnomMin
    logger.info('Reading data from sheet Centrales')
    df_centrales = get_pmin_pmax(iplp_path)
    validate_centrales(df_centrales)

    # Check which units have maintenance, and validate their names
    df_mantcen = get_mantcen_input(iplp_path)
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