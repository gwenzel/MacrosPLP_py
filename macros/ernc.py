import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

from utils import get_project_root, timeit
from postpro.Filtro_PLP_Windows import process_etapas_blocks


'''
    # Archivo de mantenimientos de centrales (plpmance.dat)
    # numero de centrales con matenimientos
    301 
    # Nombre de la central
    'LMAULE'
    #   Numero de Bloques e Intervalos
    1344                 01
    #   Mes    Bloque  NIntPot   PotMin   PotMax
        06     0097        1      0.0      0.0
'''



MAX_CAPACITY_FILENAME = "ernc_MaxCapacity.csv"
RATING_FACTOR_FILENAME = "ernc_RatingFactor.csv"
H_PROFILES_FILENAME = "ernc_profiles_H.csv"
HM_PROFILES_FILENAME = "ernc_profiles_HM.csv"
M_PROFILES_FILENAME = "ernc_profiles_M.csv"

root = get_project_root()
path_inputs = Path(root, 'macros', 'inputs')
path_dat = Path(root, 'macros', 'inputs', 'Dat')


custom_date_parser = lambda x: datetime.strptime(x, "%m/%d/%Y")


def read_ernc_files(path_inputs):
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

def hour2block(df, block2day):
    '''
    Reshape dataframe to show energy per block
    '''
    df = pd.merge(df, block2day, on=['Month', 'Hour'])
    df = df.drop(['Hour'], axis=1)
    
    # Build dictionary with functions to apply
    # Get the first month (min) and sum all profiles
    agg_dict = {}
    colnames = df.columns.tolist()
    for colname in colnames:
        if 'fp_' in colname:
            agg_dict[colname] = 'sum'
    if len(agg_dict) > 0:
        df = df.groupby(['Month', 'Block']).agg(agg_dict)
        # Reset index to get Block and Month as columns
        return df.reset_index()
    return df


def get_profiles_blo(ernc_data, block2day):
    profiles_h_blo = hour2block(ernc_data['profiles_h'], block2day)
    profiles_hm_blo = hour2block(ernc_data['profiles_hm'], block2day)
    profiles_m_blo = hour2block(ernc_data['profiles_m'], block2day)
    profiles_dict = {'H': profiles_h_blo,
                     'HM': profiles_hm_blo,
                     'M': profiles_m_blo}
    return profiles_dict


def replicate_profiles(blo_eta, df, type= 'H'):
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


def get_all_profiles(blo_eta, profiles_dict):
    df_out = blo_eta.copy()
    for type, df in profiles_dict.items():
        if len(df) > 0:
            df_out = replicate_profiles(df_out, df, type=type)            
    return df_out

def get_ini_date(blo_eta):
    ini_year = blo_eta['Year'].min()
    ini_month = blo_eta['Month'].min()
    ini_day = 1
    return datetime(ini_year, ini_month, ini_day)

def get_rating_factors(ernc_data, blo_eta):
    ini_date = get_ini_date(blo_eta)
    df_rf = ernc_data['rating_factor']
    df_rf['Profile'] = df_rf['Name'].map(ernc_data['dict_max_capacity'])
    
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

    return df_rf

def get_scaled_profiles(df_all_profiles, df_rf):

    import pdb; pdb.set_trace()
    
    return ''

def write_dat_file(df_scaled_profiles):

    import pdb; pdb.set_trace()
    
    return ''


@timeit
def main():

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
    df_scaled_profiles = get_scaled_profiles(df_all_profiles, df_rf)

    # Write data in .dat format
    write_dat_file(df_scaled_profiles)



if __name__ == "__main__":
    main()

