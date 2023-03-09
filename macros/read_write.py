import pandas as pd
from shutil import copy
from pathlib import Path
from datetime import datetime

from utils import timeit, check_is_file


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
    path_max_capacity = Path(path_inputs, MAX_CAPACITY_FILENAME)
    check_is_file(path_max_capacity)
    dict_max_capacity = pd.read_csv(
        path_max_capacity,index_col='Name').to_dict()['MaxCapacityFactor']
    
    path_rating_factor = Path(path_inputs, RATING_FACTOR_FILENAME)
    check_is_file(path_rating_factor)
    df_rating_factor = pd.read_csv(
        path_rating_factor, parse_dates=['DateFrom'],
        date_parser=custom_date_parser)
    
    path_profiles_h = Path(path_inputs, H_PROFILES_FILENAME)
    check_is_file(path_profiles_h)
    df_profiles_h = pd.read_csv(path_profiles_h).rename(
            columns={'MES': 'Month', 'PERIODO': 'Hour'})
    
    path_profiles_hm = Path(path_inputs, HM_PROFILES_FILENAME)
    check_is_file(path_profiles_hm) 
    df_profiles_hm = pd.read_csv(path_profiles_hm).rename(
            columns={'MES': 'Month', 'PERIODO': 'Hour'})

    path_profiles_m = Path(path_inputs, M_PROFILES_FILENAME)
    check_is_file(path_profiles_m)   
    df_profiles_m = pd.read_csv(path_profiles_m).rename(
            columns={'MES': 'Month', 'PERIODO': 'Hour'})
    ernc_data = {'dict_max_capacity': dict_max_capacity,
                 'rating_factor': df_rating_factor,
                 'profiles_h': df_profiles_h,
                 'profiles_hm': df_profiles_hm,
                 'profiles_m': df_profiles_m}
    return ernc_data


@timeit
def write_dat_file(ernc_data, df_scaled_profiles, iplp_path):
    '''
    Write dat file in PLP format
    '''
    # Get initial file
    plpmance_ini_path = iplp_path.parent / 'Temp' / 'plpmance_ini.dat'
    check_is_file(plpmance_ini_path)
    # Copy initial file to output destination
    source = plpmance_ini_path
    dest = iplp_path.parent / 'Temp' / OUTPUT_FILENAME
    copy(source, dest)

    num_blo = len(df_scaled_profiles)
    unit_names = ernc_data['dict_max_capacity'].keys()
    # Append ernc profiles
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
        f = open(dest, 'a')
        f.write('\n'.join(lines))
        f.close()

    # Modify number of units
    new_units_number = len(unit_names)
    add_ernc_units(dest, new_units_number)
    

@timeit
def add_ernc_units(plpmance_file, new_units_number):
    # open file in read mode
    file = open(plpmance_file, "r")
    lines = file.readlines()
    old_units_number = int(lines[2])
    lines[2] = " %s \n" % (old_units_number + new_units_number)
    # close the file
    file.close()

    # Open file in write mode
    write_file = open(plpmance_file, "w")
    # overwriting the old file contents with the new/replaced content
    write_file.writelines(lines)
    # close the file
    write_file.close()


@timeit
def generate_max_capacity_csv(iplp_path, path_inputs):
    df = pd.read_excel(iplp_path, sheet_name ='ERNC',
                       skiprows=13, usecols="A:B")
    df = df.dropna()
    df.to_csv(Path(path_inputs, MAX_CAPACITY_FILENAME), index=False)


@timeit
def generate_rating_factor_csv(iplp_path, path_inputs):

    date_converter={
        'DateFrom': lambda x: pd.to_datetime(x, unit='d', origin='1899-12-30')
    }
    df = pd.read_excel(iplp_path, sheet_name ='ERNC',
                       skiprows=13, usecols="E:G",
                       converters=date_converter)
    df = df.dropna()
    df = df.rename(columns={'Name.1': 'Name'})
    df['DateFrom'] = df['DateFrom'].dt.strftime("%m/%d/%Y")
    df.to_csv(Path(path_inputs, RATING_FACTOR_FILENAME), index=False)   


@timeit
def generate_profiles_csv(iplp_path, path_inputs):
    #
    return ''
    