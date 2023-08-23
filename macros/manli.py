'''MANLI

Generate PLPMANLI.dat file with line availability data

'''
import sys
from utils.utils import (define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         create_logger,
                         process_etapas_blocks,
                         add_time_info,
                         get_daily_indexed_df,
                         write_lines_from_scratch,
                         write_lines_appending)
import pandas as pd
from openpyxl.utils.datetime import from_excel
from macros.lin import read_df_lines


logger = create_logger('manli')


formatters_plpmanli = {
    "Etapa":        "    {:03d}".format,
    "PotMaxAB":     "        {:8.1f}".format,
    "PotMaxBA":     "  {:8.1f}".format,
    "Operativa":     "            {:>}".format
}


def get_manli_input(iplp_path):
    '''
    Read inputs from MantLIN sheet
    '''
    df_manli = pd.read_excel(iplp_path, sheet_name='MantLIN',
                             usecols='B:G', skiprows=4)
    df_manli['INICIAL'] = df_manli['INICIAL'].apply(from_excel)
    df_manli['FINAL'] = df_manli['FINAL'].apply(from_excel)
    return df_manli


def build_df_aux(df_capmax, line):
    df_aux_capmax = df_capmax[['Etapa', line]].copy()
    df_aux_capmax = df_aux_capmax.rename(columns={line: 'PotMaxAB'})
    df_aux_capmax['PotMaxBA'] = df_aux_capmax['PotMaxAB']
    df_aux_capmax['Operativa'] = 'F'
    # Filter only 0 rows
    df_aux_capmax = df_aux_capmax[df_aux_capmax['PotMaxAB'] == 0]
    # Select and reorder columns
    return df_aux_capmax[['Etapa', 'PotMaxAB', 'PotMaxBA', 'Operativa']]


def write_plpmanli(path_inputs, df_capmax, printdata=True):
    '''
    Write plpmanli.dat file
    '''
    list_manli = list(df_capmax.columns)

    # Get ['Etapa','Year','Month','Block'] as columns
    df_capmax = df_capmax.reset_index()

    # Print data if requested
    if printdata:
        df_capmax.to_csv(path_inputs / 'df_manli.csv')

    lines = ['# Archivo de mantenimientos de lineas (plpmanli.dat)']
    lines += ['# Numero de lineas con matenimientos']
    lines += ['  %s' % len(list_manli)]

    # Write dat file from scratch
    write_lines_from_scratch(lines, path_inputs / 'plpmanli.dat')

    for line in list_manli:
        # Build df_aux from both dataframes, for each line
        df_aux = build_df_aux(df_capmax, line)
        if len(df_aux) > 0:
            # Print data
            lines = ['\n# Nombre de las líneas']
            lines += ["'%s'" % line]
            lines += ['#   Numero de Bloques con mantenimiento']
            lines += ['  %04d' % len(df_aux)]
            lines += ['# Bloque         PotMaxAB   PotMaxBA     Operativa']
            # Add data as string using predefined format
            lines += [df_aux.to_string(
                index=False, header=False, formatters=formatters_plpmanli)]
        # Write data for current line
        write_lines_appending(lines, path_inputs / 'plpmanli.dat')


def write_uni_plpmanli(path_inputs):
    lines = ['# Archivo de mantenimientos de lineas (plpmanli.dat)']
    lines += ['# Numero de lineas con matenimientos']
    lines += ['0']
    write_lines_from_scratch(lines, path_inputs / 'uni_plpmanli.dat')


def filter_lines(df_lines, df_manli):
    '''
    Filter only non-operatiuve lines that exist
    '''
    filter1 = (df_manli['LÍNEA'].isin(df_lines['Nombre A->B'].tolist()))
    filter2 = (df_manli['OPERATIVA'].isin([False]))
    return df_manli[filter1 & filter2]


def validate_manli(df_manli):
    pass


def get_nominal_values_dict(df_lineas, value='A->B'):
    '''
    Get dictionary with Capmax for each line
    '''
    centrales_dict = df_lineas.set_index('Nombre A->B').to_dict()
    return centrales_dict[value]


def build_df_nominal(blo_eta, df_manli, df_lineas, id_col='LÍNEA',
                     lines_value_col='A->B'):
    '''
    Build matrix with all nominal values for each line in mantcen
    '''
    # Get line names
    manli_line_names = df_manli[id_col].unique().tolist()
    # Get capmax dictionaries
    nominal_values_dict = get_nominal_values_dict(df_lineas, lines_value_col)
    # Get base dataframes
    df_nominal = get_daily_indexed_df(blo_eta)
    # Add empty columns
    df_nominal = df_nominal.reindex(
        columns=df_nominal.columns.tolist() + manli_line_names)
    # Add default values
    df_nominal[manli_line_names] = [
        nominal_values_dict[line] for line in manli_line_names]
    return df_nominal


def get_manli_output(blo_eta, df_manli, df_lines, id_col='LÍNEA',
                     manli_col='A-B', lines_value_col='A->B', func='mean'):
    # 1. Build default dataframes
    df_nominal = build_df_nominal(blo_eta, df_manli, df_lines,
                                  id_col, lines_value_col)
    # 2. Add df_manli data in row-by-row order
    # Note that filters have a daily resolution
    manli_dates_ini = pd.to_datetime(
        df_manli[['YearIni', 'MonthIni', 'DayIni']].rename(columns={
            'YearIni': 'year', 'MonthIni': 'month', 'DayIni': 'day'}))
    manli_dates_end = pd.to_datetime(
        df_manli[['YearEnd', 'MonthEnd', 'DayEnd']].rename(columns={
            'YearEnd': 'year', 'MonthEnd': 'month', 'DayEnd': 'day'}))
    for i in range(len(manli_dates_ini)):
        manli_mask_ini = manli_dates_ini.iloc[i] <= df_nominal['Date']
        manli_mask_end = manli_dates_end.iloc[i] >= df_nominal['Date']
        name = df_manli.iloc[i][id_col]
        df_nominal.loc[manli_mask_ini & manli_mask_end, name] = \
            df_manli.iloc[i][manli_col]
    # 3. Apply func per Etapa
    on_cols = ['Month', 'Year']
    groupby_cols = ['Etapa', 'Year', 'Month', 'Block', 'Block_Len']
    if func == 'mean':
        df_final = pd.merge(
            blo_eta, df_nominal, how='left', on=on_cols).groupby(
            groupby_cols).mean(numeric_only=True)
    elif func == 'last':
        df_final = pd.merge(
            blo_eta, df_nominal, how='left', on=on_cols).groupby(
            groupby_cols).last(numeric_only=True)
    else:
        sys.exit('Invalid function: %s' % func)
    # 4. Drop Day column
    df_final = df_final.drop(['Day'], axis=1)
    return df_final


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
    df_manli = get_manli_input(iplp_path)

    # Get Hour-Blocks-Etapas definition
    logger.info('Processing block to etapas files')
    blo_eta, _, _ = process_etapas_blocks(path_dat)
    blo_eta = blo_eta.drop(['Tasa'], axis=1)

    # Filter out non-existing lines
    logger.info('Filter out non-existing lines')
    df_manli = filter_lines(df_lines, df_manli)

    # Add time info
    logger.info('Adding time info')
    df_manli = add_time_info(df_manli)

    # Validate manli data
    logger.info('Validating MantLin data')
    validate_manli(df_manli)

    # Generate arrays with min/max capacity data
    logger.info('Generating min and max capacity data')
    df_capmax = get_manli_output(blo_eta, df_manli, df_lines)

    # Write data
    logger.info('Write manli data')
    write_plpmanli(path_inputs, df_capmax)
    write_uni_plpmanli(path_inputs)

    logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
