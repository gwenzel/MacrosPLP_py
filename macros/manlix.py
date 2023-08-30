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
from pathlib import Path
from openpyxl.utils.datetime import from_excel
from macros.lin import read_df_lines
from macros.manli import (get_df_manli,
                          build_df_nominal,
                          add_manli_data_row_by_row,
                          apply_func_per_etapa)


logger = create_logger('manlix')
LINE_CHANGE_TOLERANCE = 0.1

formatters_plpmanlix = {
    "NomLin":   "'{}'".format,
    "EtaIni":   "{:d}".format,
    "EtaFin":   "{:04d}".format,
    "ManALin":  "{:.1f}".format,
    "ManBLin":  "{:.1f}".format,
    "VNomLin":  "{:.1f}".format,
    "ResLin":   "{:.3f}".format,
    "XImpLin":  "{:.3f}".format,
    "FOpeLin":  "{:>}".format
}


def get_manlix_input(iplp_path: Path) -> pd.DataFrame:
    '''
    Read inputs from MantLINX sheet
    '''
    df_manlix = pd.read_excel(iplp_path, sheet_name='MantLINX',
                              usecols='B:J', skiprows=4)
    df_manlix['INICIAL'] = df_manlix['INICIAL'].apply(from_excel)
    df_manlix['FINAL'] = df_manlix['FINAL'].apply(from_excel)
    return df_manlix


def filter_linesx(df_lines: pd.DataFrame,
                  df_manlix: pd.DataFrame) -> pd.DataFrame:
    '''
    Filter only operative lines that exist
    '''
    filter1 = (df_manlix['LÍNEA'].isin(df_lines['Nombre A->B'].tolist()))
    filter2 = (df_manlix['OPERATIVA'].isin([True]))
    return df_manlix[filter1 & filter2]


def validate_manlix(df_manlix: pd.DataFrame, df_lines: pd.DataFrame):
    for idx, row in df_manlix.iterrows():
        if row.isna().any():
            logger.error('Missing fields in row %s' % idx)
        if not row['LÍNEA'] in (df_lines['Nombre A->B'].tolist()):
            logger.error('Line %s in does not exist' % row['LÍNEA'])
        if row['A-B'] < 0:
            logger.error('Line %s has negative capacity' % row['LÍNEA'])
        if row['V [kV]'] < 0:
            logger.error('Line %s has negative V' % row['LÍNEA'])
        if row['R [ohms]'] < 0:
            logger.error('Line %s has negative R' % row['LÍNEA'])
        if row['X [ohms]'] < 0:
            logger.error('Line %s has negative X' % row['LÍNEA'])


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


def get_manlix_changes(df_capmax_manlix: pd.DataFrame,
                       df_v: pd.DataFrame,
                       df_r: pd.DataFrame,
                       df_x: pd.DataFrame,
                       path_inputs: Path,
                       print_values: bool = True) -> pd.DataFrame:
    '''
    Get dataframe with manlix format
    CSV with a row for each capacity change, with initial/final etapa,
    and V, R, X data
    '''
    manlix_lines = df_capmax_manlix.columns
    list_of_dfs = []

    for line in manlix_lines:
        # Get diff vector to detect changes
        # Filter when diff is not 0 and also keep nan row (first row)
        # (nominal value should be nan)
        # Then append results to main dataframe
        df_diff = df_capmax_manlix[line].diff()

        mask_changes = (abs(df_diff) >= LINE_CHANGE_TOLERANCE) |\
                       (df_diff.isna())
        if mask_changes.any():
            df_aux = build_df_aux(
                mask_changes, line, df_capmax_manlix, df_v, df_r, df_x)
            list_of_dfs.append(df_aux.copy())
    if len(list_of_dfs) > 0:
        df_manlix_changes = pd.concat(list_of_dfs).reset_index(drop=True)
        if print_values:
            df_manlix_changes.to_csv(path_inputs / 'df_manlix_changes.csv')
        return df_manlix_changes
    # else
    logger.error('No valid line changes in manlix')
    return pd.DataFrame()


def write_plpmanlix(path_inputs: Path, df_manlix_changes: pd.DataFrame):
    # Format columns
    for key, value in formatters_plpmanlix.items():
        df_manlix_changes[key] = df_manlix_changes[key].apply(value, axis=1)
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


def get_df_manlix(iplp_path: Path, df_lines: pd.DataFrame) -> pd.DataFrame:
    logger.info('Read line in/out input data')
    df_manlix = get_manlix_input(iplp_path)

    # Filter out non-existing lines
    logger.info('Filter out non-existing lines')
    df_manlix = filter_linesx(df_lines, df_manlix)

    # Add time info
    logger.info('Adding time info')
    df_manlix = add_time_info(df_manlix)

    # Validate manli data
    logger.info('Validating MantLINX data')
    validate_manlix(df_manlix, df_lines)
    return df_manlix


def get_manlix_output(blo_eta: pd.DataFrame,
                      df_manli: pd.DataFrame,
                      df_manlix: pd.DataFrame,
                      df_lines: pd.DataFrame,
                      id_col: str = 'LÍNEA',
                      manli_col: str = 'A-B',
                      lines_value_col: str = 'A->B',
                      func: str = 'mean') -> pd.DataFrame:
    # 1. Get nominal data for all lines in manlix
    df_nominal = build_df_nominal(
            blo_eta, df_manlix, df_lines, id_col, lines_value_col)
    if manli_col == 'A-B':
        # 2. If dealing with Max Capacity,
        # Add df_manli and manlix data in row-by-row order
        df_nominal_mod1 = add_manli_data_row_by_row(
            df_nominal, df_manli, id_col, manli_col)
        df_nominal_mod2 = add_manli_data_row_by_row(
            df_nominal_mod1, df_manlix, id_col, manli_col)
        # 3. Apply func per Etapa and drop day column
        return apply_func_per_etapa(blo_eta, df_nominal_mod2, func)
    else:
        # 2. If dealing with Voltage or other
        # Add only manlix data in row-by-row order
        df_nominal_mod = add_manli_data_row_by_row(
            df_nominal, df_manlix, id_col, manli_col)
        # 3. Apply func per Etapa and drop day column
        return apply_func_per_etapa(blo_eta, df_nominal_mod, func)


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

    # Get Hour-Blocks-Etapas definition
    logger.info('Processing block to etapas files')
    blo_eta, _, _ = process_etapas_blocks(path_dat)
    blo_eta = blo_eta.drop(['Tasa'], axis=1)

    # Get df_manlix
    logger.info('Getting df_manlix')
    df_manlix = get_df_manlix(iplp_path, df_lines)

    # Get data from Manli routine to know when lines exist
    logger.info('Getting df_manli')
    df_manli = get_df_manli(iplp_path, df_lines)

    # Generate dfs for capacity, V, R and X
    logger.info('Generating max capacity data')
    df_capmax_manlix = get_manlix_output(
        blo_eta, df_manli, df_manlix, df_lines,
        id_col='LÍNEA', manli_col='A-B',
        lines_value_col='A->B', func='mean')

    logger.info('Generating V data')
    df_v = get_manlix_output(
        blo_eta, df_manli, df_manlix, df_lines,
        id_col='LÍNEA', manli_col='V [kV]',
        lines_value_col='V [kV]', func='last')

    logger.info('Generating R data')
    df_r = get_manlix_output(
        blo_eta, df_manli, df_manlix, df_lines,
        id_col='LÍNEA', manli_col='R [ohms]',
        lines_value_col='R[ohm]', func='last')

    logger.info('Generating X data')
    df_x = get_manlix_output(
        blo_eta, df_manli, df_manlix, df_lines,
        id_col='LÍNEA', manli_col='X [ohms]',
        lines_value_col='X[ohm]', func='last')

    logger.info('Detect changes and get formatted dataframe')
    df_manlix_changes = get_manlix_changes(
        df_capmax_manlix,
        df_v, df_r, df_x, path_inputs)

    # Write data
    logger.info('Write manli data')
    write_plpmanlix(path_inputs, df_manlix_changes)

    logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
