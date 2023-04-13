
import pandas as pd
import sys
from openpyxl.utils.datetime import from_excel

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


def get_mantcen(iplp_path):
    df = pd.read_excel(iplp_path, sheet_name="MantCEN",
                       skiprows=4, usecols="B:F")
    df = df.rename(columns={
        'CENTRAL': 'Nombre','MÍNIMA': 'Pmin','MÁXIMA': 'Pmax'})
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
    # TODO PENDING
    logger.info('Validation process for MantCEN successful')


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
    # Fill Mantcen with remaining mantcen
    # No cíclicos, cíclicos, restricciones de gas, genmin

    # Read Centrales and get PnomMax and PnomMin
    logger.info('Reading data from sheet Centrales')
    df_centrales = get_pmin_pmax(iplp_path)
    validate_centrales(df_centrales)

    # Check which units have maintenance, and validate their names
    df_mantcen = get_mantcen(iplp_path)
    validate_mantcen(df_centrales, df_mantcen)

    # Generate array with updated pmin/pmax data
    import pdb; pdb.set_trace()

    # translate to Etapas/Bloques

    # count Etapas with maintenance

    # write dat file

    # Write report in sheet (?)

    pass

if __name__ == "__main__":
    main()