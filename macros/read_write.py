import pandas as pd
from pathlib import Path
from datetime import datetime

from utils import timeit


MAX_CAPACITY_FILENAME = "ernc_MaxCapacity.csv"
RATING_FACTOR_FILENAME = "ernc_RatingFactor.csv"
H_PROFILES_FILENAME = "ernc_profiles_H.csv"
HM_PROFILES_FILENAME = "ernc_profiles_HM.csv"
M_PROFILES_FILENAME = "ernc_profiles_M.csv"
OUTPUT_FILENAME = 'plpmance_ernc.dat'

custom_date_parser = lambda x: datetime.strptime(x, "%m/%d/%Y")


@timeit
def read_ernc_files(path_inputs):
    '''
    Read all input csv files to generate ernc profiles
    '''
    dict_max_capacity = pd.read_csv(
        Path(path_inputs, MAX_CAPACITY_FILENAME),
        index_col='Name').to_dict()['MaxCapacityFactor']
    df_rating_factor = pd.read_csv(
        Path(path_inputs, RATING_FACTOR_FILENAME),
        parse_dates=['DateFrom'],
        date_parser=custom_date_parser)
    df_profiles_h = pd.read_csv(
        Path(path_inputs, H_PROFILES_FILENAME)).rename(
            columns={'MES': 'Month', 'PERIODO': 'Hour'})
    df_profiles_hm = pd.read_csv(
        Path(path_inputs, HM_PROFILES_FILENAME)).rename(
            columns={'MES': 'Month', 'PERIODO': 'Hour'})
    df_profiles_m = pd.read_csv(
        Path(path_inputs, M_PROFILES_FILENAME)).rename(
            columns={'MES': 'Month', 'PERIODO': 'Hour'})
    ernc_data = {'dict_max_capacity': dict_max_capacity,
                 'rating_factor': df_rating_factor,
                 'profiles_h': df_profiles_h,
                 'profiles_hm': df_profiles_hm,
                 'profiles_m': df_profiles_m}
    return ernc_data


@timeit
def write_dat_file(ernc_data, df_scaled_profiles):
    '''
    Write dat file in PLP format
    '''
    num_blo = len(df_scaled_profiles)
    unit_names = ernc_data['dict_max_capacity'].keys()
    lines = ['# Archivo de mantenimientos de centrales (plpmance.dat)',
             '# numero de centrales con matenimientos',
             ' %s ' % 9999]
    f = open(OUTPUT_FILENAME, 'w')
    f.write('\n'.join(lines))
    f.close()
    for unit in unit_names:
        lines = ['\n# Nombre de la central']
        lines += ["'%s'" % unit]
        lines += ['#   Numero de Bloques e Intervalos']
        lines += ['  %04d                 01' % num_blo]
        lines += ['#   Mes    Bloque  NIntPot   PotMin   PotMax']
        for _, row in df_scaled_profiles.iterrows():
            lines += ['      %02d     %04d        1      0.0   %6.1f' %
                       (row['Month'], row['Etapa'], row[unit])]
        # write data for current unit  
        f = open(OUTPUT_FILENAME, 'a')
        f.write('\n'.join(lines))
        f.close()
