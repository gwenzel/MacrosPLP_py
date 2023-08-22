'''MANLIX

Generate PLPMANLIX.dat file with changes in line capacity
'''
from utils.utils import (define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         create_logger,
                         process_etapas_blocks,
                         add_time_info,
                         write_lines_from_scratch,
                         write_lines_appending)
import pandas as pd
from openpyxl.utils.datetime import from_excel
from macros.lin import read_df_lines
from macros.manli import build_df_capmax


logger = create_logger('manlix')


def get_manlix_input(iplp_path):
    '''
    Read inputs from MantLINX sheet
    '''
    df_manlix = pd.read_excel(iplp_path, sheet_name='MantLINX',
                              usecols='B:J', skiprows=4)
    df_manlix['INICIAL'] = df_manlix['INICIAL'].apply(from_excel)
    df_manlix['FINAL'] = df_manlix['FINAL'].apply(from_excel)
    return df_manlix


def filter_linesx(df_lines, df_manlix):
    '''
    Filter only operative lines that exist
    '''
    filter1 = (df_manlix['LÍNEA'].isin(df_lines['Nombre A->B'].tolist()))
    filter2 = (df_manlix['OPERATIVA'] == True)
    return df_manlix[filter1 & filter2]


def validate_manlix(df_manlix):
    pass


def get_manlix_output(blo_eta, df_manlix, df_lines):
    # 1. Build default dataframes
    df_capmax = build_df_capmax(blo_eta, df_manlix, df_lines)
    # 2. Add df_manlix data in row-by-row order
    # Note that filters have a daily resolution
    manlix_dates_ini = pd.to_datetime(
        df_manlix[['YearIni', 'MonthIni', 'DayIni']].rename(columns={
            'YearIni': 'year', 'MonthIni': 'month', 'DayIni': 'day'}))
    manlix_dates_end = pd.to_datetime(
        df_manlix[['YearEnd', 'MonthEnd', 'DayEnd']].rename(columns={
            'YearEnd': 'year', 'MonthEnd': 'month', 'DayEnd': 'day'}))
    for i in range(len(manlix_dates_ini)):
        capmax_mask_ini = manlix_dates_ini.iloc[i] <= df_capmax['Date']
        capmax_mask_end = manlix_dates_end.iloc[i] >= df_capmax['Date']
        name = df_manlix.iloc[i]['LÍNEA']
        df_capmax.loc[capmax_mask_ini & capmax_mask_end,
                      name] = df_manlix.iloc[i]['A-B']
    # 3. Average per Etapa and drop Day column
    on_cols = ['Month', 'Year']
    groupby_cols = ['Etapa', 'Year', 'Month', 'Block', 'Block_Len']
    df_capmax = pd.merge(blo_eta, df_capmax, how='left', on=on_cols).groupby(
        groupby_cols).mean(numeric_only=True).drop(['Day'], axis=1)
    return df_capmax


def write_plpmanlix(path_inputs):
    lines = ["#NomLin,EtaIni,EtaFin,ManALin,ManBLin,"
             "VNomLin,ResLin,XImpLin,FOpeLin"]
    lines += [""]
    # Write dat file from scratch
    write_lines_from_scratch(lines, path_inputs / 'plpmanlix.dat')


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

    logger.info('Read existing lines data')
    df_lines = read_df_lines(iplp_path)

    logger.info('Read line in/out input data')
    df_manlix = get_manlix_input(iplp_path)

    # Get Hour-Blocks-Etapas definition
    logger.info('Processing block to etapas files')
    blo_eta, _, _ = process_etapas_blocks(path_dat)
    blo_eta = blo_eta.drop(['Tasa'], axis=1)

    # Filter out non-existing lines
    logger.info('Filter out non-existing lines')
    df_manlix = filter_linesx(df_lines, df_manlix)

    # Add time info
    logger.info('Adding time info')
    df_manlix = add_time_info(df_manlix)

    # Validate manli data
    logger.info('Validating MantLINX data')
    validate_manlix(df_manlix)

    # Generate arrays with min/max capacity data
    logger.info('Generating min and max capacity data')
    df_capmax = get_manlix_output(blo_eta, df_manlix, df_lines)

    import pdb; pdb.set_trace()

    # Write data
    logger.info('Write manli data')
    write_plpmanlix(path_inputs, df_capmax)

    logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
