'''MANLIX

Generate PLPMANLIX.dat file with changes in line capacity
'''
import sys
from utils.utils import (define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         process_etapas_blocks,
                         add_time_info,
                         write_lines_from_scratch)
from utils.logger import create_logger
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
    "EtaFin":   "{:d}".format,
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


def build_df_aux(mask_changes: pd.Series, line: str,
                 df_capmax_ab: pd.DataFrame,
                 df_capmax_ba: pd.DataFrame,
                 df_v: pd.DataFrame,
                 df_r: pd.DataFrame,
                 df_x: pd.DataFrame) -> pd.DataFrame:
    '''
    Build dataframe with manlix changes for one line
    To be appended in the loop in get_manlix_changes
    '''
    n_blo = len(df_capmax_ab)
    col_names = ['NomLin', 'EtaIni', 'EtaFin', 'ManALin', 'ManBLin',
                 'VNomLin', 'ResLin', 'XImpLin', 'FOpeLin']
    # Build dataframe with all data
    df_aux = pd.concat([
        df_capmax_ab.loc[mask_changes, line].rename('ManALin'),
        df_capmax_ba.loc[mask_changes, line].rename('ManBLin'),
        df_v.loc[mask_changes, line].rename('VNomLin'),
        df_r.loc[mask_changes, line].rename('ResLin'),
        df_x.loc[mask_changes, line].rename('XImpLin')
        ], axis=1)
    # Calculate EtaIni / EtaFin
    list_eta_ini = df_aux.index.get_level_values('Etapa')
    list_eta_fin = (df_aux.index.get_level_values('Etapa').tolist()[1:])
    list_eta_fin = [item - 1 for item in list_eta_fin]
    list_eta_fin += [n_blo]
    # Fill remaining data
    df_aux['NomLin'] = line
    df_aux['EtaIni'] = list_eta_ini
    df_aux['EtaFin'] = list_eta_fin
    df_aux['FOpeLin'] = df_aux.apply(
        lambda row: 'F' if (
            (row['ManALin'] == 0) & (row['ManBLin'] == 0)) else 'T', axis=1)
    # Reorder columns
    return df_aux[col_names].reset_index(drop=True)


def get_manlix_changes(df_capmax_manlix_ab: pd.DataFrame,
                       df_capmax_manlix_ba: pd.DataFrame,
                       df_v: pd.DataFrame,
                       df_r: pd.DataFrame,
                       df_x: pd.DataFrame,
                       path_df: Path,
                       print_values: bool = True) -> pd.DataFrame:
    '''
    Get dataframe with manlix format
    CSV with a row for each capacity change, with initial/final etapa,
    and V, R, X data
    '''
    manlix_lines = df_capmax_manlix_ab.columns
    list_of_dfs = []

    if print_values:
        df_capmax_manlix_ab.to_csv(path_df / 'df_manlix_ab.csv')
        df_capmax_manlix_ba.to_csv(path_df / 'df_manlix_ba.csv')
        df_v.to_csv(path_df / 'df_manlix_v.csv')
        df_r.to_csv(path_df / 'df_manlix_r.csv')
        df_x.to_csv(path_df / 'df_manlix_x.csv')

    for line in manlix_lines:
        # Get diff vector to detect changes
        # Filter when diff is not 0 and also keep nan row (first row)
        # (nominal value should be nan)
        # Then append results to main dataframe
        df_diff_ab = df_capmax_manlix_ab[line].diff()
        df_diff_ba = df_capmax_manlix_ba[line].diff()

        mask_changes = (abs(df_diff_ab) >= LINE_CHANGE_TOLERANCE) |\
                       (abs(df_diff_ba) >= LINE_CHANGE_TOLERANCE) |\
                       (df_diff_ab.isna())
        if mask_changes.any():
            df_aux = build_df_aux(
                mask_changes, line, df_capmax_manlix_ab, df_capmax_manlix_ba,
                df_v, df_r, df_x)
            list_of_dfs.append(df_aux.copy())
    # Concat all dataframes
    if len(list_of_dfs) > 0:
        df_manlix_changes = pd.concat(list_of_dfs).reset_index(drop=True)
        if print_values:
            df_manlix_changes.to_csv(path_df / 'df_manlix_changes.csv')
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
    if manli_col == 'A-B' or manli_col == 'B-A':
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


def get_dict_centrales_trf(iplp_path: Path) -> pd.DataFrame:
    '''
    Get dictionary, where the keys are the transformers,
    and the values are lists of gas units

    Identify transformers with 'Trf_' prefix in field Barras,
    and identify gas units with prefix 'Gas-' in field Fuel
    '''
    df = pd.read_excel(iplp_path, sheet_name="Centrales",
                       skiprows=4, usecols="B,C,AP,BG")
    # Filter out if X
    df = df[df['Tipo de Central'] != 'X']
    # Keep only Gas units
    df = df[(df['Fuel'].str.startswith('Gas-')) & (~df['Fuel'].isna())]
    df = df.rename(columns={'CENTRALES': 'Nombre'})
    df = df[['Nombre', 'Barra']]
    # Keep only Centrales in Trf
    df = df[(df['Barra'].str.startswith('Trf_')) & (~df['Barra'].isna())]
    transformers = df['Barra'].unique().tolist()
    # Generate dict output
    dict_trf_units = {}
    for trf in transformers:
        dict_trf_units[trf] = df[df['Barra'] == trf]['Nombre'].tolist()
    return dict_trf_units


def get_dict_trf_to_line(trf_list: list, df_lines: pd.DataFrame) -> dict:
    '''
    Get dictionary from transformer to line

    This assumes a 1-1 relationship between transformers and lines
    '''
    dict_trf_to_line = {}
    for trf in trf_list:
        mask = df_lines['Nombre A->B'].str.contains(trf)
        line_name = df_lines[mask]['Nombre A->B'].values[0]
        dict_trf_to_line[trf] = line_name
    return dict_trf_to_line


def get_trf_capacity(iplp_path: Path, path_df: Path,
                     df_lines: pd.DataFrame,
                     df_capmax_ab: pd.DataFrame,
                     df_capmax_ba: pd.DataFrame) -> (
                         pd.DataFrame, pd.DataFrame
                     ):
    '''
    Read mantcen data from existing csv file (coming from mantcen.py routine),
    and get max pmax for each group of gas units in each transformer.

    Paste additional columns to df_capmax_ab and df_capmax_ba dataframes

    For transformers, B->A capacity is 0
    '''
    dict_trf_units = get_dict_centrales_trf(iplp_path)
    trf_list = list(dict_trf_units.keys())
    dict_trf_to_line = get_dict_trf_to_line(trf_list, df_lines)
    try:
        df_mantcen_pmax = pd.read_csv(path_df / 'df_mantcen_pmax.csv')
    except Exception as e:
        logger.error(e)
        sys.exit('Error reading df/df_mantcen_pmax.csv')

    mantcen_cols = df_mantcen_pmax.columns.tolist()

    for trf, units_list in dict_trf_units.items():
        # Filter units list if they are present in df_mantcen_pmax
        units_list_filtered = [unit for unit in units_list
                               if unit in mantcen_cols]
        # Get pmax of all unit configurations
        df_pmax_units = df_mantcen_pmax[['Etapa'] + units_list_filtered]
        df_pmax_units = df_pmax_units.set_index('Etapa')
        # Summarize using max function, and create series with the name
        # of the transformer
        df_pmax_trf = df_pmax_units.max(axis=1)
        df_pmax_trf.name = dict_trf_to_line[trf]
        # Join series to A->B Capacity dataframe
        df_capmax_ab = df_capmax_ab.join(df_pmax_trf)
        # Add zeros to B->A Capacity dataframe
        df_capmax_ba[dict_trf_to_line[trf]] = 0.0

        # Check errors
        if df_capmax_ab[dict_trf_to_line[trf]].isna().any():
            logger.error('Transformer %s has nan values ' % trf)

    return df_capmax_ab, df_capmax_ba


def add_trf_data(iplp_path: Path,
                 df_lines: pd.DataFrame,
                 df_v: pd.DataFrame,
                 df_r: pd.DataFrame,
                 df_x: pd.DataFrame) -> (
                     pd.DataFrame, pd.DataFrame, pd.DataFrame
                 ):
    '''
    Add transformers data to Voltage, R and X dataframes
    '''
    trf_list = list(get_dict_centrales_trf(iplp_path).keys())
    dict_trf_to_line = get_dict_trf_to_line(trf_list, df_lines)

    for trf in trf_list:
        mask = df_lines['Nombre A->B'].str.contains(trf)
        df_v[dict_trf_to_line[trf]] = df_lines[mask]['V [kV]'].values[0]
        df_r[dict_trf_to_line[trf]] = df_lines[mask]['R[ohm]'].values[0]
        df_x[dict_trf_to_line[trf]] = df_lines[mask]['X[ohm]'].values[0]
    return df_v, df_r, df_x


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
    df_capmax_ab = get_manlix_output(
        blo_eta, df_manli, df_manlix, df_lines,
        id_col='LÍNEA', manli_col='A-B',
        lines_value_col='A->B', func='mean')
    df_capmax_ba = get_manlix_output(
        blo_eta, df_manli, df_manlix, df_lines,
        id_col='LÍNEA', manli_col='B-A',
        lines_value_col='B->A', func='mean')

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

    logger.info('Read MantCen Pmax data for gas units and '
                'add to transformers line capacity. Add them to '
                'V, R and X dataframes too.')
    df_capmax_ab, df_capmax_ba = get_trf_capacity(
        iplp_path, path_df, df_lines,
        df_capmax_ab, df_capmax_ba)

    logger.info('Add missing transformer data')
    df_v, df_r, df_x = add_trf_data(
        iplp_path, df_lines, df_v, df_r, df_x)

    logger.info('Detect changes and get formatted dataframe')
    df_manlix_changes = get_manlix_changes(
        df_capmax_ab, df_capmax_ba,
        df_v, df_r, df_x, path_df)

    # Write data
    logger.info('Write manli data')
    write_plpmanlix(path_inputs, df_manlix_changes)

    logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
