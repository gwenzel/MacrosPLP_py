'''INFLOWS - AFLUENTES

Generate plpaflce.dat file with water inflows

Generate Storage_NaturalInflow files for Plexos

'''
from pathlib import Path
from utils.utils import (timeit,
                         define_arg_parser,
                         get_daily_indexed_df,
                         get_iplp_input_path,
                         get_plp_plx_booleans,
                         check_is_path,
                         process_etapas_blocks,
                         write_lines_appending,
                         write_lines_from_scratch,
                         read_plexos_end_date)
from utils.logger import add_file_handler, create_logger
from utils.utils import translate_to_hydromonth
import pandas as pd
from dateutil.relativedelta import relativedelta


logger = create_logger('water_inflows')

formatters_plpaflce = {
    "Month": "  {:03d}".format,
    "BLOCK": "   {:03d}".format,
    "1":     "{:7.2f}".format,
    "2":     "{:7.2f}".format,
    "3":     "{:7.2f}".format,
    "4":     "{:7.2f}".format,
    "5":     "{:7.2f}".format,
    "6":     "{:7.2f}".format,
    "7":     "{:7.2f}".format,
    "8":     "{:7.2f}".format,
    "9":     "{:7.2f}".format,
    "10":     "{:7.2f}".format,
    "11":     "{:7.2f}".format,
    "12":     "{:7.2f}".format,
    "13":     "{:7.2f}".format,
    "14":     "{:7.2f}".format,
    "15":     "{:7.2f}".format,
    "16":     "{:7.2f}".format,
    "17":     "{:7.2f}".format,
    "18":     "{:7.2f}".format,
    "19":     "{:7.2f}".format,
    "20":     "{:7.2f}".format,
}


def read_reduced_uncertainty_months(iplp_path: Path) -> int:
    value = pd.read_excel(iplp_path,
                          sheet_name="Path",
                          usecols='A',
                          skiprows=39
                          ).iloc[0].values[0]
    return int(value)


def read_inflow_data(iplp_path: Path) -> pd.Series:
    df = pd.read_excel(iplp_path,
                       sheet_name="Caudales_full",
                       skiprows=4,
                       usecols="A:AX")
    validate_inflow_data(df)
    # Get dict from hidroyear to hidrology and filter
    dict_hidroyears = read_dict_hidroyears(iplp_path)
    df = df[df['AÑO'].isin(dict_hidroyears.keys())]
    # Replace Year (AÑO) values for Hydrology Index (INDHID)
    df = df.replace({'AÑO': dict_hidroyears})
    series = df.set_index(['CENTRAL', 'AÑO']).stack()
    series.index.names = ['CENTRAL', 'INDHID', 'WEEK_NAME']
    series = series.rename('Inflows')
    return series


def validate_inflow_data(df: pd.DataFrame):
    '''
    Validate inflow data
    '''
    # Check for NaNs
    if df.isnull().values.any():
        raise ValueError('Inflow data contains NaNs')
    # Check for negative values
    if (df.iloc[:, 2:] < 0).values.any():
        raise ValueError('Inflow data contains negative values')
    # Check column names
    if df.columns[0] != 'CENTRAL':
        raise ValueError('Inflow data does not contain CENTRAL column')
    if df.columns[1] != 'AÑO':
        raise ValueError('Inflow data does not contain AÑO column')


def read_configsim(iplp_path: Path) -> pd.DataFrame:
    df = pd.read_excel(iplp_path,
                       sheet_name="ConfigSim",
                       usecols="A:U").set_index('Etapa')
    validate_configsim(df)
    return df


def validate_configsim(df: pd.DataFrame):
    '''
    Validate ConfigSim data
    '''
    # Check for NaNs
    if df.isnull().values.any():
        raise ValueError('ConfigSim data contains NaNs')
    # Check for negative values
    if (df < 0).values.any():
        raise ValueError('ConfigSim data contains negative values')


def read_days_per_week(iplp_path: Path) -> pd.DataFrame:
    df = pd.read_excel(iplp_path,
                       sheet_name="TimeData",
                       usecols="A:D")
    validate_timedata_1(df)
    df.dropna(inplace=True)
    return df


def validate_timedata_1(df: pd.DataFrame):
    # Check if column names are ok
    if not df.columns.tolist() == ['id_week', 'name', 'month', 'day']:
        raise ValueError('TimeData sheet does not contain id_week, name, '
                         ' month or day as columns. Exiting...')


def read_dict_hidroyears(iplp_path: Path) -> dict:
    df = pd.read_excel(iplp_path,
                       sheet_name="TimeData",
                       usecols="F:G")
    validate_timedata_2(df)
    df = df.dropna().astype(int).set_index('AÑO')
    return df.to_dict()['INDHID']


def validate_timedata_2(df: pd.DataFrame):
    # Check if column names are ok
    if not df.columns.tolist() == ['INDHID', 'AÑO']:
        logger.error('TimeData sheet does not contain INDHID and AÑO columns. '
                     'Exiting...')
        raise ValueError('TimeData sheet does not contain INDHID and AÑO '
                         'columns')


def get_week_name(row: pd.DataFrame,
                  df_days_per_week: pd.DataFrame) -> pd.DataFrame:
    mask1 = df_days_per_week['month'] == row['MONTH']
    mask2 = df_days_per_week['day'] <= row['DAY']
    return df_days_per_week[mask1 & mask2]['name'].values[-1]


def get_df_daily(blo_eta: pd.DataFrame,
                 iplp_path: Path,
                 plexos_short: bool) -> pd.DataFrame:
    df_days_per_week = read_days_per_week(iplp_path)
    df_daily = get_daily_indexed_df(blo_eta, all_caps=True)
    df_daily['WEEK_NAME'] = df_daily.apply(
        lambda row: get_week_name(row, df_days_per_week), axis=1)
    year_ini = df_daily['YEAR'][0]
    df_daily['ETAPA'] = df_daily.apply(
        lambda row: (row['YEAR'] - year_ini) * 12 + row['MONTH'], axis=1)
    # Filter by plexos_end_date
    if plexos_short:
        plexos_end_date = read_plexos_end_date(iplp_path)
        df_daily = df_daily[df_daily['DATE'] <= plexos_end_date]
    return df_daily


def get_list_of_units(df_all_inflows: pd.DataFrame) -> list:
    return df_all_inflows.index.get_level_values('CENTRAL').unique().tolist()


def get_list_of_hyd(df_all_inflows: pd.DataFrame) -> list:
    return df_all_inflows.index.get_level_values('INDHID').unique().tolist()


def get_df_all_inflows(iplp_path: Path,
                       blo_eta: pd.DataFrame,
                       plp_enable: bool,
                       plx_enable: bool) -> pd.DataFrame:
    series_inflows = read_inflow_data(iplp_path)
    # Use short df_daily if running only plexos process
    plexos_short = (not plp_enable) & plx_enable
    df_daily = get_df_daily(blo_eta, iplp_path, plexos_short)
    # Join dataframes using outer to keep all data
    new_index = ['YEAR', 'MONTH', 'DAY', 'WEEK_NAME', 'DATE']
    df_all_inflows = df_daily.set_index(new_index)
    df_all_inflows = df_all_inflows.join(series_inflows, how='outer')
    # Remove WEEK_NAME from index
    df_all_inflows = df_all_inflows.reset_index().drop(
        ['WEEK_NAME', 'ETAPA'], axis=1)
    new_index = ['CENTRAL', 'YEAR', 'MONTH', 'DAY', 'DATE', 'INDHID']
    df_all_inflows = df_all_inflows.set_index(new_index)
    df_all_inflows = df_all_inflows.sort_index(
        level=['CENTRAL', 'YEAR', 'MONTH', 'DAY'])
    return df_all_inflows


def print_plexos_inflows_all(df_all_inflows: pd.DataFrame,
                             path_pib:  Path):

    # format plexos, aux dataframe to unstack and print
    list_of_hyd = get_list_of_hyd(df_all_inflows)
    df_all_inflows.loc[:, 'Inflows'] = df_all_inflows['Inflows'].apply(
        lambda x: round(x, 2))
    df_aux = df_all_inflows.squeeze().unstack('INDHID')
    df_aux = df_aux.reset_index().drop('DATE', axis=1)
    df_aux = df_aux.rename(columns={'CENTRAL': 'NAME'})
    df_aux['PERIOD'] = 1
    df_aux = df_aux[
        ['NAME', 'YEAR', 'MONTH', 'DAY', 'PERIOD'] + list_of_hyd]
    # print all data file
    df_aux.to_csv(path_pib / 'Storage_NaturalInflow.csv', index=False)


def print_plexos_inflows_separate(df_all_inflows: pd.DataFrame,
                                  path_pib: Path):
    # Remove next comment to print all hydrologies
    # list_of_hyd = get_list_of_hyd(df_all_inflows)
    list_of_hyd = [20]
    # Adjust to plexos data format
    for indhid in list_of_hyd:
        hyd_mask = (df_all_inflows.index.get_level_values('INDHID') == indhid)
        inflows_aux = df_all_inflows[hyd_mask]
        # format
        inflows_aux = inflows_aux.reset_index().drop('DATE', axis=1)
        inflows_aux = inflows_aux.rename(
            columns={'CENTRAL': 'NAME', 'Inflows': 'VALUE'})
        inflows_aux['BAND'] = 1
        inflows_aux['PERIOD'] = 1
        inflows_aux = inflows_aux[
            ['NAME', 'BAND', 'YEAR', 'MONTH', 'DAY', 'PERIOD', 'VALUE']]
        inflows_aux.loc[:, 'VALUE'] = inflows_aux['VALUE'].apply(
            lambda x: round(x, 2))
        # print
        inflows_aux.to_csv(
            path_pib / f'Storage_NaturalInflow_{indhid:02d}.csv', index=False)


def get_shuffled_hydrologies(df_daily: pd.DataFrame,
                             iplp_path: Path,
                             df_configsim: pd.DataFrame) -> pd.DataFrame:
    '''
    Get shuffled hydrologies per day

    Data from configsim refers to Etapas, so we need to turn it into
    YEAR-MONTH-DAY data and get rid of Etapas
    '''
    df_configsim.index.names = ['ETAPA']
    df_daily = df_daily.drop('WEEK_NAME', axis=1)
    df_shuffled_hyd = df_daily.join(df_configsim, on='ETAPA')
    df_shuffled_hyd = df_shuffled_hyd.drop('ETAPA', axis=1)
    df_shuffled_hyd = df_shuffled_hyd.set_index(
        ['YEAR', 'MONTH', 'DAY', 'DATE'])

    # Stack and set new index and column names
    df_shuffled_hyd = df_shuffled_hyd.stack()
    df_shuffled_hyd.index.names = [
        'YEAR', 'MONTH', 'DAY', 'DATE', 'SHUFFLED_HYD']
    df_shuffled_hyd.name = 'INDHID'
    df_shuffled_hyd = df_shuffled_hyd.reset_index()
    return df_shuffled_hyd


def shuffle_hidrologies(df_daily: pd.DataFrame,
                        iplp_path: Path,
                        df_configsim: pd.DataFrame,
                        df_all_inflows: pd.DataFrame) -> pd.DataFrame:
    '''
    Shuffle hydrologies according to ConfigSim
    '''
    # Get stacked dataframe with mapping from original hydrology (INDHID) to
    # new shuffled hydrology (SHUFFLED_HYD) for each day
    df_shuffled_hyd = get_shuffled_hydrologies(
        df_daily, iplp_path, df_configsim)

    # Shuffling hydrologies
    # For each unit, merge df_shuffled_hyd with inflows data coming from
    # df_df_all_inflows
    list_of_df = []
    list_of_units = get_list_of_units(df_all_inflows)
    for unit in list_of_units:
        #  merge for each unit and build new dataframe
        merge_cols = ['YEAR', 'MONTH', 'DAY', 'INDHID']
        df_shuffled_aux = df_shuffled_hyd.merge(
            df_all_inflows.loc[unit], how='left', on=merge_cols)
        df_shuffled_aux['CENTRAL'] = unit
        df_shuffled_aux = df_shuffled_aux.drop('INDHID', axis=1)
        df_shuffled_aux = df_shuffled_aux.rename(
            columns={'SHUFFLED_HYD': 'INDHID'})
        list_of_df.append(df_shuffled_aux)

    # Concatenate aux dataframes and reformat
    df_final = pd.concat(list_of_df)
    df_final = df_final.set_index(
        ['CENTRAL', 'YEAR', 'MONTH', 'DAY', 'DATE', 'INDHID'])

    return df_final


def reduce_uncertainty(iplp_path: Path,
                       df_all_inflows: pd.DataFrame) -> pd.DataFrame:
    ''' DEPRECATED
    For the first x months, use monthly average inflows for each week,
    instead of using weekly data
    '''
    ru_months = read_reduced_uncertainty_months(iplp_path)

    # Filter by date
    df_aux = df_all_inflows.copy()
    ini_date = df_aux.index.get_level_values('DATE')[0]
    end_date = ini_date + relativedelta(months=+ru_months)
    mask_date = df_aux.index.get_level_values('DATE') < end_date
    df_aux = df_aux[mask_date]

    # Get average per month (select all indexes except day and date)
    indexes_to_group = ['CENTRAL', 'YEAR', 'MONTH', 'INDHID']
    df_mean = df_aux.groupby(indexes_to_group).mean()

    # Use df_mean to replace data in original df
    df_ru = df_all_inflows.copy()
    for idx, row in df_all_inflows[mask_date].iterrows():
        cen, year, month, indhid = idx[0], idx[1], idx[2], idx[5]
        df_ru.loc[idx, 'Inflows'] = df_mean.loc[
            (cen, year, month, indhid), 'Inflows']
    return df_ru


def build_df_aux(df_all_inflows, unit, nblocks=12):
    '''
    Adjust df_all_inflows dataframe to print data in plp format
    '''
    # Get monthly mean
    cols_groupby = ['YEAR', 'MONTH', 'INDHID']
    df_mean = df_all_inflows.loc[unit].groupby(cols_groupby).mean()

    # format to square matrix
    df_mean = df_mean.squeeze().unstack('INDHID')

    # Add BLOCK index repeating Inflow values
    # First calculate new index (mux)
    nmonths = 12
    mux = pd.MultiIndex.from_product(
        [df_mean.index.get_level_values('YEAR').unique().tolist(),
         range(1, nmonths + 1),
         range(1, nblocks + 1),
         ], names=['YEAR', 'MONTH', 'BLOCK'])
    # Remove Year-Month entries after last date
    matrix_length = len(df_mean) * nblocks
    mux = mux[:matrix_length]

    # Then add BLOCK index using reindex with forward fill
    df_mean['BLOCK'] = 1
    df_mean = df_mean.reset_index().set_index(
        ['YEAR', 'MONTH', 'BLOCK'])
    df_mean = df_mean.reindex(mux, method='ffill')
    # Replace Block values by row number
    df_mean = df_mean.reset_index()
    df_mean['BLOCK'] = df_mean.index + 1
    # Format, remove year and rename MONTH to use translate_to_hydromonth
    df_mean = df_mean.rename(columns={'MONTH': 'Month'})
    df_mean = df_mean.drop('YEAR', axis=1)
    # update to hydromonths
    df_mean = translate_to_hydromonth(df_mean)

    # Column names as strings
    df_mean.columns = df_mean.columns.map(str)

    return df_mean


def write_plpaflce(path_inputs: Path,
                   df_all_inflows: pd.DataFrame):
    '''
    Write plpaflce.dat file
    '''
    list_of_units = get_list_of_units(df_all_inflows)
    list_of_hyd = get_list_of_hyd(df_all_inflows)

    lines = ['# Archivo de caudales por etapa']
    lines += ['# Nro. Cent. c/Caudales Estoc. (EstocNVar2) y Nro. Hidrologias'
              ' (NClase)']
    lines += ['  %s                                         %s' % (
        len(list_of_units), len(list_of_hyd))]

    # Write dat file from scratch
    write_lines_from_scratch(lines, path_inputs / 'plpaflce.dat')

    for unit in list_of_units:
        # Build df_aux from both dataframes, for each line
        df_aux = build_df_aux(df_all_inflows, unit)
        # Print data
        lines = ['\n# Nombre de la central']
        lines += ["'%s'" % unit]
        lines += ['#   Numero de bloques con caudales']
        lines += ['  %03d' % len(df_aux)]
        lines += ['# Mes   Bloque    Caudal']
        if len(df_aux) > 0:
            # Add data as string using predefined format
            lines += [df_aux.to_string(
                index=False, header=False, formatters=formatters_plpaflce)]
        # Write data for current line
        write_lines_appending(lines, path_inputs / 'plpaflce.dat')


def filter_df_all_inflows(iplp_path: Path,
                          df_all_inflows: pd.DataFrame):
    '''
    Filter df for plx process
    '''
    plexos_end_date = read_plexos_end_date(iplp_path)
    year_mask = df_all_inflows.index.get_level_values('YEAR') <= \
        plexos_end_date.year
    df_all_inflows = df_all_inflows[year_mask]

    return df_all_inflows


@timeit
def main(plp_enable=None, plx_enable=None):
    '''
    Main routine
    '''
    try:
        # Get input file path
        logger.info('Getting input file path')
        parser = define_arg_parser(plp=True, plx=True)
        iplp_path = get_iplp_input_path(parser)
        path_inputs = iplp_path.parent / "Temp"
        check_is_path(path_inputs)
        path_dat = iplp_path.parent / "Temp" / "Dat"
        check_is_path(path_dat)
        path_df = iplp_path.parent / "Temp" / "df"
        check_is_path(path_df)
        path_pib = iplp_path.parent / "Temp" / "PIB"
        check_is_path(path_pib)

        # Add destination folder to logger
        path_log = iplp_path.parent / "Temp" / "log"
        check_is_path(path_log)
        add_file_handler(logger, 'water_inflows', path_log)

        if (plp_enable is None) and (plx_enable is None):
            # Get PLP/PLX enabling booleans
            plp_enable, plx_enable = get_plp_plx_booleans(parser)
            if (plx_enable | plp_enable) is False:
                logger.error('No process enabled. Exiting...')
                exit()

        if plp_enable:
            logger.info('PLP enabled')
        else:
            logger.info('PLP disabled')
        if plx_enable:
            logger.info('PLX enabled')
        else:
            logger.info('PLX disabled')

        # Get Hour-Blocks-Etapas definition
        logger.info('Processing block to etapas files')
        blo_eta, _, _ = process_etapas_blocks(path_dat)

        logger.info('Getting dataframe with all data')
        df_all_inflows = get_df_all_inflows(iplp_path, blo_eta,
                                            plp_enable, plx_enable)
        # df_all_inflows.to_csv(path_df / 'df_all_inflows.csv')

        if plp_enable:
            logger.info('Printing inflows in plp format')
            write_plpaflce(path_inputs, df_all_inflows)

        if plx_enable:
            if plp_enable:
                logger.info('Filtering inflows dataframe (PLP was enabled)')
                # Otherwise, it was already filtered in get_df_all_inflows
                df_all_inflows = filter_df_all_inflows(
                    iplp_path, df_all_inflows)

            logger.info('Shuffling inflows according to ConfigSim')
            df_configsim = read_configsim(iplp_path)
            # Make sure df_daily is the plexos short version
            df_daily = get_df_daily(blo_eta, iplp_path, plexos_short=True)
            df_all_inflows = shuffle_hidrologies(
                df_daily, iplp_path, df_configsim, df_all_inflows)
            # df_all_inflows.to_csv(path_df / 'df_all_inflows_shuffled.csv',
            #   index=False)

            logger.info('Printing inflows in plexos format')
            print_plexos_inflows_all(df_all_inflows, path_pib)
            print_plexos_inflows_separate(df_all_inflows, path_pib)

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
