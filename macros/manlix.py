'''MANLIX

Generate PLPMANLIX.dat file with changes in line capacity
'''
from utils.utils import (define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         create_logger,
                         process_etapas_blocks,
                         add_time_info,
                         write_lines_from_scratch)
import pandas as pd
from openpyxl.utils.datetime import from_excel
from macros.lin import read_df_lines
from macros.manli import get_manli_output


logger = create_logger('manlix')
LINE_CHANGE_TOLERANCE = 0.1

formatters_plpmanlix = {
    "NomLin":   "{:<48},".format,
    "EtaIni":   "{:04d},".format,
    "EtaFin":   "{:04d},".format,
    "ManALin":  "{:6.1f},".format,
    "ManBLin":  "{:6.1f},".format,
    "VNomLin":  "{:03d},".format,
    "ResLin":   "{:5.3f},".format,
    "XImpLin":  "{:5.3f},".format,
    "FOpeLin":  "{:>}".format
}


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


def get_manlix_output(blo_eta, df_manli, df_lines, id_col='LÍNEA',
                      manli_col='A-B', lines_value_col='A->B', func='mean'):
    '''
    Wrapper for get_manli_output function
    '''
    return get_manli_output(blo_eta, df_manli, df_lines, id_col,
                            manli_col, lines_value_col, func)


def build_df_aux(mask_changes, line, df_capmax, df_v, df_r, df_x):
    '''
    Build dataframe with manlix changes for one line
    To be appended in the loop in get_manlix_changes
    '''
    n_blo = len(df_capmax)
    col_names = ['NomLin', 'EtaIni', 'EtaFin', 'ManALin', 'ManBLin',
                 'VNomLin', 'ResLin', 'XImpLin', 'FOpeLin']
    # Build dataframe with all data
    df_aux = pd.concat([
        df_capmax.loc[mask_changes, line].rename('ManALin'),
        df_capmax.loc[mask_changes, line].rename('ManBLin'),
        df_v.loc[mask_changes, line].rename('VNomLin'),
        df_r.loc[mask_changes, line].rename('ResLin'),
        df_x.loc[mask_changes, line].rename('XImpLin')
        ], axis=1)
    df_aux['NomLin'] = line
    df_aux['EtaIni'] = df_aux.index.get_level_values('Etapa')
    df_aux['EtaFin'] = n_blo  # TODO improve
    df_aux['FOpeLin'] = 'T'
    # Reorder columns
    return df_aux[col_names].reset_index(drop=True)


def get_manlix_changes(df_capmax, df_v, df_r, df_x, path_inputs,
                       print_values=True):
    '''
    Get dataframe with manlix format
    CSV with a row for each capacity change, with initial/final etapa,
    and V, R, X data
    '''
    manlix_lines = df_capmax.columns
    list_of_dfs = []
    for line in manlix_lines:
        # Get diff vector to detect changes
        # Filter when diff is not 0 and not nan
        # (nominal value should be nan)
        # Then append results to main dataframe
        df_diff = df_capmax[line].diff()
        mask_changes = (abs(df_diff) >= LINE_CHANGE_TOLERANCE) &\
                       (df_diff.notna())
        if mask_changes.any():
            df_aux = build_df_aux(mask_changes, line,
                                  df_capmax, df_v, df_r, df_x)
            list_of_dfs.append(df_aux.copy())
    df_manlix_changes = pd.concat(list_of_dfs).reset_index(drop=True)

    if print_values:
        df_manlix_changes.to_csv(path_inputs / 'df_manlix_changes.csv')

    return df_manlix_changes


def write_plpmanlix(path_inputs, df_manlix_changes):
    # Format columns
    df_manlix_changes['NomLin'] = df_manlix_changes['NomLin'].apply(
        "'{}'".format, axis=1)
    df_manlix_changes['ResLin'] = df_manlix_changes['ResLin'].apply(
        "{:5.3f}".format, axis=1)
    df_manlix_changes['XImpLin'] = df_manlix_changes['XImpLin'].apply(
        "{:5.3f}".format, axis=1)
    # Build file
    lines = ["#NomLin,EtaIni,EtaFin,ManALin,ManBLin,"
             "VNomLin,ResLin,XImpLin,FOpeLin"]
    lines += df_manlix_changes.to_csv(index=False, header=False).split('\r\n')
    '''
    lines += [df_manlix_changes.to_string(index=False, header=False,
                                          justify='left',
                                          formatters=formatters_plpmanlix)]
    '''
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

    # Generate dfs for capacity, V, R and X
    logger.info('Generating max capacity data')
    df_capmax = get_manlix_output(
        blo_eta, df_manlix, df_lines,
        id_col='LÍNEA', manli_col='A-B',
        lines_value_col='A->B', func='mean')

    logger.info('Generating V data')
    df_v = get_manlix_output(
        blo_eta, df_manlix, df_lines,
        id_col='LÍNEA', manli_col='V [kV]',
        lines_value_col='V [kV]', func='last')

    logger.info('Generating R data')
    df_r = get_manlix_output(
        blo_eta, df_manlix, df_lines,
        id_col='LÍNEA', manli_col='R [ohms]',
        lines_value_col='R[ohm]', func='last')

    logger.info('Generating X data')
    df_x = get_manlix_output(
        blo_eta, df_manlix, df_lines,
        id_col='LÍNEA', manli_col='X [ohms]',
        lines_value_col='X[ohm]', func='last')

    logger.info('Detect changes and get formatted dataframe')
    df_manlix_changes = get_manlix_changes(
        df_capmax, df_v, df_r, df_x, path_inputs)

    # Write data
    logger.info('Write manli data')
    write_plpmanlix(path_inputs, df_manlix_changes)

    logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
