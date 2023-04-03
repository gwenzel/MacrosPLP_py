import pandas as pd
from shutil import copy
from pathlib import Path
from datetime import datetime
from openpyxl.utils.datetime import from_excel

from utils import timeit, check_is_file, remove_blank_lines


MAX_CAPACITY_FILENAME = "ernc_MaxCapacity.csv"
MIN_CAPACITY_FILENAME = "ernc_MinCapacity.csv"
RATING_FACTOR_FILENAME = "ernc_RatingFactor.csv"
H_PROFILES_FILENAME = "ernc_profiles_H.csv"
HM_PROFILES_FILENAME = "ernc_profiles_HM.csv"
M_PROFILES_FILENAME = "ernc_profiles_M.csv"
OUTPUT_FILENAME = 'plpmance.dat'

custom_date_parser = lambda x: datetime.strptime(x, "%m/%d/%Y")
formatters = {
    "Month":    "     {:02d}".format,
    "Etapa":    "     {:04d}".format,
    "NIntPot":  "       {:01d}".format,
    "Pmin":     "{:8.2f}".format,
    "Pmax":     "{:8.2f}".format
}
MONTH_TO_HIDROMONTH = {
    1: 10, 2: 11, 3: 12,
    4: 1, 5: 2, 6: 3,
    7: 4, 8: 5, 9: 6,
    10: 7, 11: 8, 12: 9
}


def read_ernc_files(path_inputs):
    '''
    Read all input csv files to generate ernc profiles
    '''
    path_max_capacity = Path(path_inputs, MAX_CAPACITY_FILENAME)
    check_is_file(path_max_capacity)
    dict_max_capacity = pd.read_csv(
        path_max_capacity, index_col='Name').to_dict()['MaxCapacityFactor']
    
    path_min_capacity = Path(path_inputs, MIN_CAPACITY_FILENAME)
    check_is_file(path_min_capacity)
    dict_min_capacity = pd.read_csv(
        path_min_capacity, index_col='Name').to_dict()['Pmin']
    
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
                 'dict_min_capacity': dict_min_capacity,
                 'rating_factor': df_rating_factor,
                 'profiles_h': df_profiles_h,
                 'profiles_hm': df_profiles_hm,
                 'profiles_m': df_profiles_m}
    return ernc_data


def write_plpmance_ernc_dat(ernc_data, df_scaled_profiles, iplp_path):
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
    pmin = ernc_data['dict_min_capacity']

    # Translate month to hidromonth
    df_scaled_profiles = df_scaled_profiles.replace({'Month': MONTH_TO_HIDROMONTH})

    # Append ernc profiles
    for unit in unit_names:
        lines = ['\n# Nombre de la central']
        lines += ["'%s'" % unit]
        lines += ['#   Numero de Bloques e Intervalos']
        lines += ['  %04d                 01' % num_blo]
        lines += ['#   Mes    Bloque  NIntPot   PotMin   PotMax']

        # Format unit dataframe
        df_aux = df_scaled_profiles[['Month', 'Etapa', unit]]
        df_aux = df_aux.rename(columns={unit: 'Pmax'})
        df_aux['Pmin'] = pmin[unit]
        df_aux['Pmin'] = df_aux.apply(lambda x: min(x['Pmin'], x['Pmax']), axis=1)
        df_aux['NIntPot'] = 1
        df_aux = df_aux[['Month', 'Etapa', 'NIntPot', 'Pmin', 'Pmax']]

        # Dataframe to string
        lines += [df_aux.to_string(index=False, header=False, formatters=formatters)]
        
        #  write data for current unit
        f = open(dest, 'a')
        f.write('\n'.join(lines))
        f.close()

    # Modify number of units
    new_units_number = len(unit_names)
    add_ernc_units(dest, new_units_number)
    # Make sure there are no blank lines
    remove_blank_lines(dest)
    # Warning if there are repeated generation units
    # check_plpmance(dest)


def add_ernc_units(plpmance_file, new_units_number):
    # open file in read mode
    file = open(plpmance_file, "r")
    lines = file.readlines()
    old_units_number = int(lines[2])
    lines[2] = "     %s\n" % (old_units_number + new_units_number)
    # close the file
    file.close()

    # Open file in write mode
    write_file = open(plpmance_file, "w")
    # overwriting the old file contents with the new/replaced content
    write_file.writelines(lines)
    # close the file
    write_file.close()


def generate_max_capacity_csv(iplp_path, path_inputs):
    '''
    Read iplp file, sheet ERNC, and extract max capacities
    '''
    df = pd.read_excel(iplp_path, sheet_name ='ERNC',
                       skiprows=13, usecols="A:B")
    df = df.dropna()
    df.to_csv(Path(path_inputs, MAX_CAPACITY_FILENAME), index=False)


def generate_min_capacity_csv(iplp_path, path_inputs):
    '''
    Read iplp file, sheet Centrales, and extract pmin for all units

    Note: Only CSP units should have Pmin
    '''
    df = pd.read_excel(iplp_path, sheet_name ='Centrales',
                       skiprows=4, usecols="B,AA")
    df = df.dropna()
    df = df.rename(columns={'CENTRALES': 'Name', 'Mínima.1': 'Pmin'})
    df.to_csv(Path(path_inputs, MIN_CAPACITY_FILENAME), index=False)


def generate_rating_factor_csv(iplp_path, path_inputs):
    '''
    Read iplp file, sheet ERNC, and extract rating factors
    '''
    #date_converter={
    #    'DateFrom': lambda x: pd.to_datetime(x, unit='d', origin='1899-12-30')
    #}
    df = pd.read_excel(iplp_path, sheet_name ='ERNC',
                       skiprows=13, usecols="E:G")
    df['DateFrom'] = df['DateFrom'].apply(from_excel)
    df = df.dropna()
    df = df.rename(columns={'Name.1': 'Name'})
    df['DateFrom'] = df['DateFrom'].dt.strftime("%m/%d/%Y")
    df.to_csv(Path(path_inputs, RATING_FACTOR_FILENAME), index=False)   


def generate_profiles_csv(iplp_path, path_inputs, root):
    '''
    For the moment, it is copying directly the csv profiles from the
    project folder.

    A possible change could be to make it read the
    iplp file, sheet ERNC, and extract the profiles directly
    '''
    profiles_source = Path(root, 'macros', 'inputs')
    profile_filenames = [H_PROFILES_FILENAME, HM_PROFILES_FILENAME, M_PROFILES_FILENAME]
    for filename in profile_filenames:
        copy(profiles_source / filename, path_inputs / filename)


def get_unit_type(iplp_path):
    '''
    Read iplp file, sheet Centrales, and extract unit type
    '''
    df = pd.read_excel(iplp_path, sheet_name ='Centrales',
                       skiprows=4, usecols="B,C")
    df = df.dropna()
    df = df.rename(columns={'CENTRALES': 'Name', 'Tipo de Central': 'Type'})
    df = df.set_index('Name')
    return df.to_dict()['Type']
