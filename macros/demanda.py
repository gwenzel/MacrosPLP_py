'''Demanda

Module to generate demand input files for PLP.

Ouput files are:

- plpdem.dat: Demand per Etapa for each node
- uni_plpdem.dat: Demand per Etapa for the uninodal case
- plpfal.prn: Define maximum power for each Failure Unit,
              based on the max demand of each node
'''
import pandas as pd
import numpy as np

from utils import (     get_project_root,
                        create_logger,
                        timeit,
                        get_iplp_input_path,
                        check_is_path,
                        process_etapas_blocks
)

root = get_project_root()
logger = create_logger('demanda')


MONTH_2_NUMBER = {  
    'ene': 1,
    'feb': 2,
    'mar': 3,
    'abr': 4,
    'may': 5,
    'jun': 6,
    'jul': 7,
    'ago': 8,
    'sep': 9,
    'oct': 10,
    'nov': 11,
    'dic': 11
}

HORA_DICT = {'H%s' % i: i for i in range(1, 25)}


def dda_por_barra_to_row_format(iplp_path, write_to_csv=False):
    df = pd.read_excel(iplp_path, sheet_name="DdaPorBarra")
    #print(df)
    keys = ["#", "Coordinado", "Cliente", "Perfil día tipo",
            "Verificador consumo", "Barra Consumo", "Factor Barra Consumo"]
    df_as_dict = df.to_dict()
    #print(df_as_dict["Coordinado"][0] is np.nan)
    new_dict = {key:{} for key in keys}
    idx = 0
    for i in range(598):
        for barra in range(1, 23+1): 
            #print(df_as_dict["Barra Consumo %s" % barra][i] is not np.nan)
            if df_as_dict["Barra Consumo %s" % barra][i] is not np.nan:
                new_dict["#"][idx] = i
                new_dict["Coordinado"][idx] = df_as_dict["Coordinado"][i]
                new_dict["Cliente"][idx] = df_as_dict["Cliente"][i]
                new_dict["Perfil día tipo"][idx] = df_as_dict["Perfil día tipo"][i]
                new_dict["Verificador consumo"][idx] = df_as_dict["Verificador consumo"][i]
                new_dict["Barra Consumo"][idx] = df_as_dict["Barra Consumo %s" % barra][i]
                new_dict["Factor Barra Consumo"][idx] = df_as_dict["Factor Barra Consumo %s" % barra][i]
            idx+=1
    #print(new_dict)
    df_dda_por_barra = pd.DataFrame(new_dict).reset_index(drop=True)
    if write_to_csv:
        df_dda_por_barra.to_csv(iplp_path.parent / 'DdaPorBarra_rows.csv')
    return df_dda_por_barra


def get_mappings(df_dda_por_barra):
    df_dda_por_barra['Coordinado'] = df_dda_por_barra['Coordinado'].fillna("NA")
    
    # Get Coord-Cliente to Profile mapping
    df_dda_por_barra['Coord-Cliente'] = df_dda_por_barra.apply(
        lambda x: (x['Coordinado'], x['Cliente']), axis=1)
    map_cc_to_profile = df_dda_por_barra[['Coord-Cliente', 'Perfil día tipo']]
    map_cc_to_profile = map_cc_to_profile.set_index('Coord-Cliente').to_dict()
    
    # Get Coord-Cliente-Barra to Factor Consumo mapping
    df_dda_por_barra['Coord-Cliente-Barra'] = df_dda_por_barra.apply(
        lambda x: (x['Coordinado'], x['Cliente'], x['Barra Consumo']), axis=1)
    map_ccb_to_cf = df_dda_por_barra[['Coord-Cliente-Barra', 'Factor Barra Consumo']]
    map_ccb_to_cf = map_ccb_to_cf.set_index('Coord-Cliente-Barra').to_dict()

    # Get list of Barras for each Coord-Cliente
    map_cc_to_barras = {}
    for cc in df_dda_por_barra['Coord-Cliente'].unique():
        map_cc_to_barras[cc] = df_dda_por_barra[
            df_dda_por_barra['Coord-Cliente']==cc]['Barra Consumo'].to_list()
    
    return map_cc_to_profile, map_ccb_to_cf, map_cc_to_barras


def get_monthly_demand(iplp_path):
    date_converter={
        'DateFrom': lambda x: pd.to_datetime(x, unit='d', origin='1899-12-30')
    }
    df = pd.read_excel(iplp_path, sheet_name='DdaEnergia',
                       converters=date_converter)
    # Clean data
    cols_to_drop = ['#', 'Coordinado.1', 'Cliente.1', 'Perfil',
                    'Clasificacion SEN', 'Clasificacion ENGIE']
    df = df.drop(cols_to_drop, axis=1)
    df = df.dropna(how='all', axis=1)
    df['Coordinado'] = df['Coordinado'].fillna('NA')
    # Stack to get Demand series
    demand_series = df.set_index(['Coordinado','Cliente']).stack()
    demand_series.index.set_names(['Coordinado','Cliente','Date'], inplace=True)
    demand_series.name = 'Demand'
    df = demand_series.reset_index()
    # parse dates
    df['Date'] = pd.to_datetime(df['Date'], unit='d', origin='1899-12-30').dt.strftime("%m/%d/%Y")
    return df


def get_hourly_profiles(iplp_path):
    df = pd.read_excel(iplp_path, sheet_name='PerfilesDDA')
    # Clean data
    cols_to_drop = ['#', 'Año', 'Verificador consumo']
    df = df.drop(cols_to_drop, axis=1)
    # Process data
    profile_series = df.set_index(['Perfil día tipo', 'Mes']).stack()
    profile_series.index.set_names(['Perfil día tipo', 'Mes','Hora'], inplace=True)
    profile_series.name = 'PowerFactor'
    df = profile_series.reset_index()
    df = df.replace(to_replace={"Mes": MONTH_2_NUMBER, "Hora": HORA_DICT})
    return df


def get_all_profiles(map_cc_to_profile, map_ccb_to_cf, map_cc_to_barras,
                     df_monthly_demand, df_hourly_profiles):
    import pdb; pdb.set_trace()
    pass


@timeit
def main():
    '''
    Main routine
    '''
    # Get input file path
    logger.info('Getting input file path')
    iplp_path = get_iplp_input_path()
    path_inputs = iplp_path.parent / "Temp"
    check_is_path(path_inputs)
    path_dat = iplp_path.parent / "Temp" / "Dat"
    check_is_path(path_dat)

    # Get Hour-Blocks-Etapas definition
    logger.info('Processing block to etapas files')
    blo_eta, _, block2day = process_etapas_blocks(path_dat)
    blo_eta = blo_eta.drop(['Tasa'], axis=1)

    # Sheet "DdaPorBarra" to row format
    logger.info('Processing DdaPorBarra sheet')
    df_dda_por_barra = dda_por_barra_to_row_format(
        iplp_path, write_to_csv=True)

    # Get mappings
    map_cc_to_profile, map_ccb_to_cf, map_cc_to_barras = \
        get_mappings(df_dda_por_barra)

    # Get monthly demand from Sheet "DdaEnergia"
    logger.info('Processing DdaEnergia sheet')
    df_monthly_demand = get_monthly_demand(iplp_path)

    # Get hourly profiles from Sheet "PerfilesDDA"
    logger.info('Processing PerfilesDDA sheet')
    df_hourly_profiles = get_hourly_profiles(iplp_path)

    # Generate dataframe with profiles per Etapa
    logger.info('Generating dataframes with profiles per Etapa per Barra')
    df_all_profiles = get_all_profiles(
        map_cc_to_profile, map_ccb_to_cf, map_cc_to_barras,
        df_monthly_demand, df_hourly_profiles)


    # Print to plpdem and uni_plpdem
    logger.info('Printing plpdem.dat and uni_plpdem.dat')


    # Get failure units and generate plpfal.prn
    logger.info('Printing plpfal.prn')



if __name__ == "__main__":
    main()
