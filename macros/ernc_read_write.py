import pandas as pd
from shutil import copy
from pathlib import Path
from openpyxl.utils.datetime import from_excel

from utils.utils import (check_is_file,
                         remove_blank_lines,
                         write_lines_appending,
                         translate_to_hydromonth)

OUTPUT_FILENAME = 'plpmance.dat'

formatters = {
    "Month":    "     {:02d}".format,
    "Etapa":    "     {:04d}".format,
    "NIntPot":  "       {:01d}".format,
    "Pmin":     "{:8.2f}".format,
    "Pmax":     "{:8.2f}".format
}


def define_input_names(ernc_scenario: str) -> dict:
    '''
    Define input csv files to use
    ernc_scenario should be "Base", "WindHigh" or "WindLow"
    '''
    suffix_dict = {
        "Base": "mid",
        "WindHigh": "high",
        "WindLow": "low"
    }
    suffix = suffix_dict[ernc_scenario]
    names = {
        "MAX_CAPACITY_FILENAME": "ernc_MaxCapacity.csv",
        "MIN_CAPACITY_FILENAME": "ernc_MinCapacity.csv",
        "RATING_FACTOR_FILENAME": "ernc_RatingFactor.csv",
        "H_PROFILES_FILENAME": "ernc_profiles_H_%s.csv" % suffix,
        "HM_PROFILES_FILENAME": "ernc_profiles_HM_%s.csv" % suffix,
        "SCENARIO": suffix
    }
    return names


def read_ernc_files(path_df: Path, input_names: dict) -> dict:
    '''
    Read all input csv files to generate ernc profiles
    '''
    # Capacity and rating factor files
    path_max_capacity = Path(
        path_df, input_names["MAX_CAPACITY_FILENAME"])
    check_is_file(path_max_capacity)
    dict_max_capacity = pd.read_csv(
        path_max_capacity, index_col='Name').to_dict()['MaxCapacityFactor']

    path_min_capacity = Path(
        path_df, input_names["MIN_CAPACITY_FILENAME"])
    check_is_file(path_min_capacity)
    dict_min_capacity = pd.read_csv(
        path_min_capacity, index_col='Name').to_dict()['Pmin']

    path_rating_factor = Path(
        path_df, input_names["RATING_FACTOR_FILENAME"])
    check_is_file(path_rating_factor)
    df_rating_factor = pd.read_csv(
        path_rating_factor, parse_dates=['DateFrom'],
        date_format="%m/%d/%Y")

    # Profile files
    path_profiles_h = Path(
        path_df, input_names["H_PROFILES_FILENAME"])
    check_is_file(path_profiles_h)
    df_profiles_h = pd.read_csv(path_profiles_h).rename(
            columns={'MES': 'Month', 'PERIODO': 'Hour'})

    path_profiles_hm = Path(
        path_df, input_names["HM_PROFILES_FILENAME"])
    check_is_file(path_profiles_hm)
    df_profiles_hm = pd.read_csv(path_profiles_hm).rename(
            columns={'MES': 'Month', 'PERIODO': 'Hour'})

    # Build output dict
    ernc_data = {'dict_max_capacity': dict_max_capacity,
                 'dict_min_capacity': dict_min_capacity,
                 'rating_factor': df_rating_factor,
                 'profiles_h': df_profiles_h,
                 'profiles_hm': df_profiles_hm}
    return ernc_data


def write_plpmance_ernc_dat(ernc_data: dict, df_scaled_profiles: pd.DataFrame,
                            unit_names: list, iplp_path: Path):
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
    pmin = ernc_data['dict_min_capacity']

    # Translate month to hidromonth
    df_scaled_profiles = translate_to_hydromonth(df_scaled_profiles)

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
        df_aux['Pmin'] = df_aux.apply(lambda x: min(x['Pmin'], x['Pmax']),
                                      axis=1)
        df_aux['NIntPot'] = 1
        df_aux = df_aux[['Month', 'Etapa', 'NIntPot', 'Pmin', 'Pmax']]

        # Dataframe to string
        lines += [df_aux.to_string(index=False, header=False,
                                   formatters=formatters)]

        #  write data for current unit
        write_lines_appending(lines, dest)

    # Modify number of units
    new_units_number = len(unit_names)
    add_ernc_units(dest, new_units_number)
    # Make sure there are no blank lines
    remove_blank_lines(dest)
    # Warning if there are repeated generation units
    # check_plpmance(dest)


def add_ernc_units(plpmance_file: Path, new_units_number: int):
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


def generate_max_capacity_csv(iplp_path: Path, path_df: Path,
                              input_names: dict):
    '''
    Read iplp file, sheet ERNC, and extract max capacities
    '''
    df = pd.read_excel(iplp_path, sheet_name='ERNC', usecols="A:B")
    validate_max_capacity_csv(df)
    df = df.dropna()
    df.to_csv(Path(path_df, input_names["MAX_CAPACITY_FILENAME"]),
              index=False)


def validate_max_capacity_csv(df: pd.DataFrame):
    # Check if 'Name' and 'MaxCapacityFactor' are in columns
    if 'Name' not in df.columns or 'MaxCapacityFactor' not in df.columns:
        raise ValueError('Columns Name and MaxCapacityFactor are required')


def generate_min_capacity_csv(iplp_path: Path, path_df: Path,
                              input_names: list):
    '''
    Read iplp file, sheet Centrales, and extract pmin for all units

    Note: Only CSP units should have Pmin
    '''
    df = pd.read_excel(iplp_path, sheet_name='Centrales',
                       skiprows=4, usecols="B,AA")
    validate_min_capacity_csv(df)
    df = df.dropna()
    df = df.rename(columns={'CENTRALES': 'Name', 'Mínima.1': 'Pmin'})
    df.to_csv(Path(path_df, input_names["MIN_CAPACITY_FILENAME"]),
              index=False)


def validate_min_capacity_csv(df: pd.DataFrame):
    # Check if 'CENTRALES' and 'Mínima.1' are in columns
    if 'CENTRALES' not in df.columns or 'Mínima.1' not in df.columns:
        raise ValueError('Columns CENTRALES and Mínima are required')


def generate_rating_factor_csv(iplp_path: Path, path_df: Path,
                               input_names: list):
    '''
    Read iplp file, sheet ERNC, and extract rating factors
    '''
    df = pd.read_excel(iplp_path, sheet_name='ERNC', usecols="E:G")
    validate_rating_factor_csv(df)
    df['DateFrom'] = df['DateFrom'].apply(from_excel)
    df = df.dropna()
    df = df.rename(columns={'Name.1': 'Name'})
    df['DateFrom'] = df['DateFrom'].dt.strftime("%m/%d/%Y")
    df.to_csv(Path(path_df, input_names["RATING_FACTOR_FILENAME"]),
              index=False)


def validate_rating_factor_csv(df: pd.DataFrame):
    # Check if 'Name.1', 'DateFrom', 'DateTo' are in columns
    if 'Name.1' not in df.columns or 'DateFrom' not in df.columns or \
            'Value [MW]' not in df.columns:
        raise ValueError('Columns Name.1, DateFrom and Value [MW]'
                         'are required')


def generate_profiles_csv(iplp_path: Path, path_df: Path,
                          input_names: list):
    '''
    Read csv profiles from external inputs path and copy to path_df folder
    '''
    h_sheetname = 'ernc_H_%s' % input_names["SCENARIO"]
    hm_sheetname = 'ernc_MH_%s' % input_names["SCENARIO"]
    df_h = pd.read_excel(iplp_path, sheet_name=h_sheetname)
    validate_profiles_csv(df_h, resolution='h')
    df_h.to_csv(Path(path_df, input_names["H_PROFILES_FILENAME"]),
                index=False, header=True)
    df_hm = pd.read_excel(iplp_path, sheet_name=hm_sheetname)
    validate_profiles_csv(df_hm, resolution='hm')
    df_hm.to_csv(Path(path_df, input_names["HM_PROFILES_FILENAME"]),
                 index=False, header=True)


def validate_profiles_csv(df: pd.DataFrame, resolution='h'):
    # Check if 'MES' and 'PERIODO' are in columns
    if 'MES' not in df.columns or 'PERIODO' not in df.columns:
        raise ValueError('Columns MES and PERIODO are required')
    # Check if resolution is correct
    if resolution == 'h':
        assert len(df) == 24
        assert df['MES'].unique() == [1]
        assert (df['PERIODO'].unique() == range(1, 25)).all()
    elif resolution == 'hm':
        assert len(df) == 12 * 24
        assert (df['MES'].unique() == range(1, 13)).all()
        assert (df['PERIODO'].unique() == range(1, 25)).all()


def get_unit_type(iplp_path: Path) -> dict:
    '''
    Read iplp file, sheet Centrales, and extract unit type
    '''
    df = pd.read_excel(iplp_path, sheet_name='Centrales',
                       skiprows=4, usecols="B,C")
    df = df.dropna()
    df = df.rename(columns={'CENTRALES': 'Name', 'Tipo de Central': 'Type'})
    df = df.set_index('Name')
    return df.to_dict()['Type']


def get_valid_unit_names(ernc_data: dict, iplp_path: Path) -> list:
    '''
    Return list of units with type different than X
    '''
    unit_type_dict = get_unit_type(iplp_path)
    return [unit for unit in ernc_data['dict_max_capacity'].keys()
            if unit_type_dict[unit] != 'X']
