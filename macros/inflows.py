'''INFLOWS - AFLUENTES

Generate plpaflce.dat file with water inflows

Generate Storage_NaturalInflow files for Plexos

'''
from datetime import datetime
from pathlib import Path
from utils.utils import (define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         process_etapas_blocks)
from utils.logger import create_logger
from openpyxl.utils.datetime import from_excel
import pandas as pd


logger = create_logger('water_inflows')


def read_plexos_end_date(iplp_path: Path) -> datetime:
    value = pd.read_excel(iplp_path,
                          sheet_name="Path",
                          usecols='D',
                          skiprows=21
                          ).iloc[0].apply(from_excel).values[0]
    return pd.to_datetime(value)


def read_inflow_data(iplp_path: Path) -> pd.Series:
    df = pd.read_excel(iplp_path,
                       sheet_name="Caudales_full",
                       skiprows=4,
                       usecols="A:AX")
    # Get dict from hidroyear to hidrology and filter
    dict_hidroyears = read_dict_hidroyears(iplp_path)
    df = df[df['AÑO'].isin(dict_hidroyears.keys())]
    # Replace Year (AÑO) values for Hydrology Index (INDHID)
    df = df.replace({'AÑO': dict_hidroyears})
    series = df.set_index(['CENTRAL', 'AÑO']).stack()
    series.index.names = ['CENTRAL', 'INDHID', 'WEEK_NAME']
    series = series.rename('Inflows')
    return series


def read_configsim(iplp_path: Path) -> pd.DataFrame:
    return pd.read_excel(iplp_path,
                         sheet_name="ConfigSim",
                         usecols="A:U").set_index('Etapa')


def read_days_per_week(iplp_path: Path) -> pd.DataFrame:
    return pd.read_excel(iplp_path,
                         sheet_name="TimeData",
                         usecols="A:G")


def read_dict_hidroyears(iplp_path: Path) -> dict:
    df = pd.read_excel(iplp_path,
                       sheet_name="TimeData",
                       usecols="I:J")
    df = df.dropna().astype(int).set_index('AÑO')
    return df.to_dict()['INDHID']


def plexos_daily_indexed_df(blo_eta: pd.DataFrame,
                            plexos_end_date: datetime) -> pd.DataFrame:
    '''
    Get dataframe indexed by day within the timeframe of plexos
    '''
    ini_date = datetime(
        blo_eta.iloc[0]['Year'], blo_eta.iloc[0]['Month'], 1)
    index = pd.date_range(start=ini_date, end=plexos_end_date, freq='D')
    df = pd.DataFrame(index=index, columns=['YEAR', 'MONTH', 'DAY'])
    df['YEAR'] = df.index.year
    df['MONTH'] = df.index.month
    df['DAY'] = df.index.day
    # df['DATE'] = df.index
    df = df.reset_index(drop=True)
    return df


def get_week_name(row: pd.DataFrame,
                  df_days_per_week: pd.DataFrame) -> pd.DataFrame:
    mask1 = df_days_per_week['month'] == row['MONTH']
    mask2 = df_days_per_week['day'] <= row['DAY']
    return df_days_per_week[mask1 & mask2]['name'].values[-1]


def get_df_daily(blo_eta: pd.DataFrame,
                 iplp_path: Path) -> pd.DataFrame:
    df_days_per_week = read_days_per_week(iplp_path)
    plexos_end_date = read_plexos_end_date(iplp_path)
    df_daily = plexos_daily_indexed_df(blo_eta, plexos_end_date)
    df_daily['WEEK_NAME'] = df_daily.apply(
        lambda row: get_week_name(row, df_days_per_week), axis=1)
    year_ini = df_daily['YEAR'][0]
    df_daily['ETAPA'] = df_daily.apply(
        lambda row: (row['YEAR'] - year_ini) * 12 + row['MONTH'], axis=1)
    return df_daily


def get_list_of_units(df_all_inflows: pd.DataFrame) -> list:
    return df_all_inflows.index.get_level_values('CENTRAL').unique().tolist()


def get_list_of_hyd(df_all_inflows: pd.DataFrame) -> list:
    return df_all_inflows.index.get_level_values('INDHID').unique().tolist()


def get_df_all_inflows(iplp_path: Path,
                       blo_eta: pd.DataFrame) -> pd.DataFrame:
    series_inflows = read_inflow_data(iplp_path)
    df_daily = get_df_daily(blo_eta, iplp_path)
    # Join dataframes using outer to keep all data
    new_index = ['YEAR', 'MONTH', 'DAY', 'WEEK_NAME']
    df_all_inflows = df_daily.set_index(new_index)
    df_all_inflows = df_all_inflows.join(series_inflows, how='outer')
    # Remove WEEK_NAME from index
    df_all_inflows = df_all_inflows.reset_index().drop(
        ['WEEK_NAME', 'ETAPA'], axis=1)
    new_index = ['CENTRAL', 'YEAR', 'MONTH', 'DAY', 'INDHID']
    df_all_inflows = df_all_inflows.set_index(new_index)
    df_all_inflows = df_all_inflows.sort_index(
        level=['CENTRAL', 'YEAR', 'MONTH', 'DAY'])
    return df_all_inflows


def print_plexos_inflows_all(df_all_inflows: pd.DataFrame,
                             path_pib:  Path):
    list_of_hyd = get_list_of_hyd(df_all_inflows)
    # format plexos, aux dataframe to unstack and print
    df_all_inflows['Inflows'] = df_all_inflows['Inflows'].apply(
        lambda x: round(x, 2))
    df_aux = df_all_inflows.squeeze().unstack('INDHID')
    df_aux = df_aux.reset_index()
    df_aux = df_aux.rename(columns={'CENTRAL': 'NAME'})
    df_aux['PERIOD'] = 1
    df_aux = df_aux[
        ['NAME', 'YEAR', 'MONTH', 'DAY', 'PERIOD'] + list_of_hyd]
    # print all data file
    df_aux.to_csv(path_pib / 'Storage_NaturalInflow.csv', index=False)


def print_plexos_inflows_separate(df_all_inflows: pd.DataFrame,
                                  path_pib: Path):
    list_of_hyd = get_list_of_hyd(df_all_inflows)
    for indhid in list_of_hyd:
        mask = (df_all_inflows.index.get_level_values('INDHID') == indhid)
        inflows_aux = df_all_inflows[mask]
        # format
        inflows_aux = inflows_aux.reset_index()
        inflows_aux = inflows_aux.rename(
            columns={'CENTRAL': 'NAME', 'Inflows': 'VALUE'})
        inflows_aux['BAND'] = 1
        inflows_aux['PERIOD'] = 1
        inflows_aux = inflows_aux[
            ['NAME', 'BAND', 'YEAR', 'MONTH', 'DAY', 'PERIOD', 'VALUE']]
        inflows_aux['VALUE'] = inflows_aux['VALUE'].apply(
            lambda x: round(x, 2))
        # print
        inflows_aux.to_csv(
            path_pib / f'Storage_NaturalInflow_{indhid:02d}.csv', index=False)


def get_shuffled_hydrologies(blo_eta: pd.DataFrame,
                             iplp_path: Path,
                             df_configsim: pd.DataFrame) -> pd.DataFrame:
    '''
    Get shuffled hydrologies per day

    Data from configsim refers to Etapas, so we need to turn it into
    YEAR-MONTH-DAY data and get rid of Etapas
    '''
    df_configsim.index.names = ['ETAPA']
    df_daily = get_df_daily(blo_eta, iplp_path).drop('WEEK_NAME', axis=1)
    df_shuffled_hyd = df_daily.join(df_configsim, on='ETAPA')
    df_shuffled_hyd = df_shuffled_hyd.drop('ETAPA', axis=1)
    df_shuffled_hyd = df_shuffled_hyd.set_index(['YEAR', 'MONTH', 'DAY'])

    df_shuffled_hyd = df_shuffled_hyd.stack()
    df_shuffled_hyd.index.names = ['YEAR', 'MONTH', 'DAY', 'SHUFFLED_HYD']
    df_shuffled_hyd.name = 'INDHID'
    df_shuffled_hyd = df_shuffled_hyd.reset_index()
    return df_shuffled_hyd


def shuffle_hidrologies(blo_eta: pd.DataFrame,
                        iplp_path: Path,
                        df_configsim: pd.DataFrame,
                        df_all_inflows: pd.DataFrame) -> pd.DataFrame:
    '''
    Shuffle hydrologies according to ConfigSim
    '''
    # Get stacked dataframe with mapping from original hydrology (INDHID) to
    # new shuffled hydrology (SHUFFLED_HYD) for each day
    df_shuffled_hyd = get_shuffled_hydrologies(
        blo_eta, iplp_path, df_configsim)

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
        ['CENTRAL', 'YEAR', 'MONTH', 'DAY', 'INDHID'])

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
    path_df = iplp_path.parent / "Temp" / "df"
    check_is_path(path_df)
    path_pib = iplp_path.parent / "Temp" / "PIB"
    check_is_path(path_pib)

    # Get Hour-Blocks-Etapas definition
    logger.info('Processing block to etapas files')
    blo_eta, _, _ = process_etapas_blocks(path_dat)
    blo_eta = blo_eta.drop(['Tasa'], axis=1)

    logger.info('Getting dataframe with all data')
    df_all_inflows = get_df_all_inflows(iplp_path, blo_eta)

    logger.info('Shuffling inflows according to ConfigSim')
    df_configsim = read_configsim(iplp_path)
    df_all_inflows = shuffle_hidrologies(
        blo_eta, iplp_path, df_configsim, df_all_inflows)

    logger.info('Printing inflows in plexos format')
    print_plexos_inflows_all(df_all_inflows, path_pib)
    print_plexos_inflows_separate(df_all_inflows, path_pib)

    logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
