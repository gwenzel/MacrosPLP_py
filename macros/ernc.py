import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

from utils import get_project_root, timeit
from postpro.Filtro_PLP_Windows import process_etapas_blocks


PRINT_FILES = False

MAX_CAPACITY_FILENAME = "ernc_MaxCapacity.csv"
RATING_FACTOR_FILENAME = "ernc_RatingFactor.csv"
H_PROFILES_FILENAME = "ernc_profiles_H.csv"
HM_PROFILES_FILENAME = "ernc_profiles_HM.csv"
M_PROFILES_FILENAME = "ernc_profiles_M.csv"

OUTPUT_FILENAME = 'plpmance_ernc.dat'

root = get_project_root()
path_inputs = Path(root, 'macros', 'inputs')
path_dat = Path(root, 'macros', 'inputs', 'Dat')


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
def hour2block(df, block2day):
    '''
    Reshape dataframe to show energy per block
    '''
    df = pd.merge(df, block2day, on=['Month', 'Hour'])
    df = df.drop(['Hour'], axis=1)
    
    # Build dictionary with functions to apply
    # Use mean to get Pmax across hours in each block
    agg_dict = {}
    colnames = df.columns.tolist()
    for colname in colnames:
        if 'fp_' in colname:
            agg_dict[colname] = 'mean'
    if len(agg_dict) > 0:
        df = df.groupby(['Month', 'Block']).agg(agg_dict)
        # Reset index to get Block and Month as columns
        return df.reset_index()
    return df

@timeit
def get_profiles_blo(ernc_data, block2day):
    '''
    Get all hourly, hour-monthly and monthly profiles,
    with their blocks definition on one dictionary
    '''
    profiles_h_blo = hour2block(ernc_data['profiles_h'], block2day)
    profiles_hm_blo = hour2block(ernc_data['profiles_hm'], block2day)
    profiles_m_blo = hour2block(ernc_data['profiles_m'], block2day)
    profiles_dict = {'H': profiles_h_blo,
                     'HM': profiles_hm_blo,
                     'M': profiles_m_blo}
    return profiles_dict

@timeit
def replicate_profiles(blo_eta, df, type= 'H'):
    '''
    Use Merge left to match the generation on each block
    '''
    if type == 'H':
        df = df.drop(['Month'], axis=1)
        return pd.merge(blo_eta, df, how='left', on=['Block'])
    elif type =='HM':
        return pd.merge(blo_eta, df, how='left', on=['Month', 'Block'])
    elif type == 'M':
        df = df.drop(['Block'], axis=1)
        return pd.merge(blo_eta, df, how='left', on=['Month'])
    else:
        sys.exit("Invalid type: %s" % type)

@timeit
def get_all_profiles(blo_eta, profiles_dict, print_files=PRINT_FILES):
    '''
    Run the replicate_profiles function for all profiles and group data
    on one output dataframe
    '''
    df_out = blo_eta.copy()
    for type, df in profiles_dict.items():
        if len(df) > 0:
            df_out = replicate_profiles(df_out, df, type=type)
    if print_files:
        df_out.to_csv('df_all_profiles.csv')         
    return df_out

@timeit
def get_ini_date(blo_eta):
    '''
    Get initial date
    '''
    ini_year = blo_eta['Year'].min()
    ini_month = blo_eta['Month'].min()
    ini_day = 1
    return datetime(ini_year, ini_month, ini_day)

@timeit
def get_rating_factors(ernc_data, blo_eta, print_files=PRINT_FILES):
    '''
    Return Rating Factors dataframe
    '''
    ini_date = get_ini_date(blo_eta)
    df_rf = ernc_data['rating_factor']
    
    # Replace all dates before ini_date to match with 1st block
    df_rf['DateFrom'] = df_rf['DateFrom']
    mask = (df_rf['DateFrom'] <  ini_date)
    df_rf.loc[mask, 'DateFrom'] = ini_date
    
    # Get Month, Year
    df_rf['Year'] = df_rf['DateFrom'].dt.year
    df_rf['Month'] = df_rf['DateFrom'].dt.month
    
    blo_eta = blo_eta.drop(['Block', 'Block_Len'], axis=1)
    # Get initial etapa of each year-month
    df_rf['Year-Month'] = df_rf.apply(lambda x: (x['Year'], x['Month']), axis=1)
    ini_eta = blo_eta.groupby(['Year', 'Month']).min().to_dict()['Etapa']
    df_rf['Initial_Eta'] = df_rf['Year-Month'].map(ini_eta)

    # TO DO Simplify df_rf
    # remove repeated rows

    if print_files:
        df_rf.to_csv('df_rf.csv')

    return df_rf

@timeit
def get_scaled_profiles(ernc_data, df_all_profiles, df_rf, print_files=PRINT_FILES):
    '''
    Use all profiles data and rating factors to generate scaled profiles
    '''

    profile_dict = ernc_data['dict_max_capacity']
    # Base of output dataframe
    df_profiles = df_all_profiles[['Month', 'Etapa']].copy()
    df_profiles = df_profiles.join(pd.DataFrame(columns=profile_dict.keys()), how="outer")

    df_profiles_aux = df_all_profiles[['Etapa']].copy()
    
    # iterate units and add scaled profiles
    for unit, profile_name in profile_dict.items():
        df_profiles_aux['aux'] = df_all_profiles[profile_name]
        # iterate rating factors
        for _, row in df_rf[df_rf['Name'] == unit].iterrows():
            df_profiles.loc[df_profiles['Etapa'] >= row['Initial_Eta'], unit] = \
                df_profiles_aux.loc[df_profiles_aux['Etapa'] >= row['Initial_Eta'], 'aux'] * row['Value_MW']
    # Make sure nan values are turned to 0
    df_profiles = df_profiles.fillna(0)
    # Print profiles to file
    if print_files:
        df_profiles.to_csv('ernc_profiles.csv')    
    return df_profiles

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

@timeit
def main():
    '''
    Main routine
    '''

    # Get inputs
    ernc_data = read_ernc_files(path_inputs)
    blo_eta, _, block2day = process_etapas_blocks(path_dat)
    blo_eta = blo_eta.drop(['Tasa'], axis=1)

    # Convert hourly profiles to blocks
    profiles_dict = get_profiles_blo(ernc_data, block2day)
    # Replicate data for all Etapas
    df_all_profiles = get_all_profiles(blo_eta, profiles_dict)

    # Get Rating Factors
    df_rf = get_rating_factors(ernc_data, blo_eta)

    # Use RFs to scale profiles
    df_scaled_profiles = get_scaled_profiles(ernc_data, df_all_profiles, df_rf)

    # Write data in .dat format
    write_dat_file(ernc_data, df_scaled_profiles)


if __name__ == "__main__":
    main()

