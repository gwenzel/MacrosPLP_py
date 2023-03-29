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
                        process_etapas_blocks,
                        get_list_of_all_barras
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
    'dic': 12
}

HORA_DICT = {'H%s' % i: i for i in range(1, 25)}

MONTH_TO_HIDROMONTH = {
    1: 10, 2: 11, 3: 12,
    4: 1, 5: 2, 6: 3,
    7: 4, 8: 5, 9: 6,
    10: 7, 11: 8, 12: 9
}

formatters_plpdem = {
    "Month":    "   {:02d}".format,
    "Etapa":    "  {:03d}".format,
    "Consumo":  "{:9.2f}".format
}

formatters_plpfal = {
    "Month":    "     {:02d}".format,
    "Etapa":    "   {:04d}".format,
    "NIntPot":  "{:9.2f}".format,
    "PotMin":   "{:8.2f}".format,
    "PotMax":   "{:8.2f}".format
}


@timeit
def dda_por_barra_to_row_format(iplp_path, write_to_csv=False):
    df = pd.read_excel(iplp_path, sheet_name="DdaPorBarra")
    keys = ["Coordinado", "Cliente", "Profile",
            "Barra Consumo", "Factor Barra Consumo"]
    df_as_dict = df.to_dict()
    new_dict = {key:{} for key in keys}
    idx = 0
    N_MAX_BARRAS = 23
    N_COORD_CLIENTE = len(df)
    for i in range(N_COORD_CLIENTE):
        for barra in range(1, N_MAX_BARRAS + 1):
            if df_as_dict["Barra Consumo %s" % barra][i] is not np.nan:
                new_dict["Coordinado"][idx] = df_as_dict["Coordinado"][i]
                new_dict["Cliente"][idx] = df_as_dict["Cliente"][i]
                new_dict["Profile"][idx] = df_as_dict["Perfil día tipo"][i]
                new_dict["Barra Consumo"][idx] = df_as_dict["Barra Consumo %s" % barra][i]
                new_dict["Factor Barra Consumo"][idx] = df_as_dict["Factor Barra Consumo %s" % barra][i]
            idx+=1
    #print(new_dict)
    df_dda_por_barra = pd.DataFrame(new_dict).reset_index(drop=True)
    df_dda_por_barra['Coordinado'] = df_dda_por_barra['Coordinado'].fillna("NA")
    if write_to_csv:
        df_dda_por_barra.to_csv(iplp_path.parent / 'Temp' / 'DdaPorBarra_rows.csv')
    return df_dda_por_barra


@timeit
def get_monthly_demand(iplp_path):
    date_converter={
        'DateFrom': lambda x: pd.to_datetime(x, unit='d', origin='1899-12-30')
    }
    df = pd.read_excel(iplp_path, sheet_name='DdaEnergia',
                       converters=date_converter)
    
    # Drop rows if column # is nan
    df = df.dropna(subset=['#'], how='any')
    # Clean data
    cols_to_drop = ['#', 'Coordinado.1', 'Cliente.1', 'Perfil',
                    'Clasificacion SEN', 'Clasificacion ENGIE']
    df = df.drop(cols_to_drop, axis=1)
    df = df.dropna(how='all', axis=1)
    df.loc[:,'Coordinado'] = df['Coordinado'].fillna('NA')  
    # Stack to get Demand series
    demand_series = df.set_index(['Coordinado','Cliente']).stack()
    demand_series.index.set_names(['Coordinado','Cliente','Date'], inplace=True)
    demand_series.name = 'Demand'
    df = demand_series.reset_index()
    # parse dates
    df['Date'] = pd.to_datetime(df['Date'], unit='d', origin='1899-12-30').dt.strftime("%m/%d/%Y")
    return df


@timeit
def get_hourly_profiles(iplp_path):
    df = pd.read_excel(iplp_path, sheet_name='PerfilesDDA')
    # Clean data
    cols_to_drop = ['#', 'Año', 'Verificador consumo']
    df = df.drop(cols_to_drop, axis=1)
    # Process data
    profile_series = df.set_index(['Perfil día tipo','Mes']).stack()
    profile_series.index.set_names(['Perfil día tipo','Mes','Hora'], inplace=True)
    profile_series.name = 'PowerFactor'
    df = profile_series.reset_index()
    df = df.replace(to_replace={"Mes": MONTH_2_NUMBER, "Hora": HORA_DICT})
    return df


def get_blockly_profiles(df_hourly_profiles, block2day):
    df = df_hourly_profiles.rename(
        columns={'Perfil día tipo': 'Profile',
                 'Mes': 'Month',
                 'Hora': 'Hour'})
    df = pd.merge(df, block2day, on=['Month','Hour'], how='left')
    df = df.drop('Hour', axis=1)
    df = df.groupby(['Profile','Month','Block']).sum().reset_index()
    return df


@timeit
def get_all_profiles(blo_eta, block2day,
                     df_monthly_demand, df_hourly_profiles, df_dda_por_barra):

    # Turn hourly profiles to profiles by block
    df_blockly_profiles = get_blockly_profiles(df_hourly_profiles, block2day)

    # Add data to monthly demand df
    df_monthly_demand['Year'] = pd.to_datetime(df_monthly_demand['Date']).dt.year
    df_monthly_demand['Month'] = pd.to_datetime(df_monthly_demand['Date']).dt.month
    df_monthly_demand['DaysInMonth'] = pd.to_datetime(df_monthly_demand['Date']).dt.daysinmonth
    df_monthly_demand = df_monthly_demand.drop(['Date'], axis=1)

    # Merge dataframes
    df = pd.merge(df_monthly_demand, df_dda_por_barra, on=['Coordinado','Cliente'])
    df = pd.merge(df, df_blockly_profiles, on=['Profile','Month'])
    df = pd.merge(df, blo_eta, on=['Year','Month','Block'])

    # Calculate consumption, group by Barra and sum
    # Consumption is calculated as follows:
    # [Monthly demand] * [% of demand in current bus] * [% of demand in current block] * 1000
    # / ([Days in Month] * [Hours per day in current block])
    df['Consumo'] = df.apply(
        lambda x: x['Demand'] * x['Factor Barra Consumo'] * x['PowerFactor'] * 1000 /
                  (x['DaysInMonth'] * x['Block_Len']), axis=1)
    
    cols_to_drop = ['Demand', 'Factor Barra Consumo', 'PowerFactor', 'Block_Len', 'DaysInMonth']
    df = df.drop(cols_to_drop, axis=1)
    df = df.groupby(['Year','Month','Block','Etapa','Barra Consumo']).sum(numeric_only=True).reset_index()

    # Reorder columns and sort
    df = df[['Barra Consumo','Year','Month','Block','Etapa','Consumo']]
    df = df.sort_values(by=['Barra Consumo','Year','Month','Block','Etapa']).reset_index(drop=True)
    return df


@timeit
def write_plpdem_dat(df_all_profiles, iplp_path):

    plpdem_path = iplp_path.parent / 'Temp' / 'plpdem.dat'

    list_all_barras = get_list_of_all_barras(iplp_path)
    list_dem_barras = df_all_profiles['Barra Consumo'].unique().tolist()

    # Translate month to hidromonth
    df_all_profiles = df_all_profiles.replace({'Month': MONTH_TO_HIDROMONTH})

    lines =  ['# Archivo de demandas por barra (plpdem.dat)']
    lines += ['#  Numero de barras']
    lines += ['%s' % len(list_all_barras)]

    #  write data from scratch
    f = open(plpdem_path, 'w')
    f.write('\n'.join(lines))
    f.close()

    for barra in list_all_barras:
        lines = ['\n# Nombre de la Barra']
        lines += ["'%s'" % barra]
        lines += ['# Numero de Demandas']
        if barra in list_dem_barras:
            df_aux = df_all_profiles[df_all_profiles['Barra Consumo']==barra]
            df_aux = df_aux[['Month','Etapa','Consumo']]
            lines += ['%s' % len(df_aux)]
            if len(df_aux) > 0:
                lines += ['# Mes  Etapa   Demanda']
                # Dataframe to string
                lines += [df_aux.to_string(
                    index=False, header=False, formatters=formatters_plpdem)]
        else:
            lines += ['%s' % 0]
        #  write data for current barra
        f = open(plpdem_path, 'a')
        f.write('\n'.join(lines))
        f.close()


@timeit
def write_uni_plpdem_dat(df_all_profiles, iplp_path):
    uni_plpdem_path = iplp_path.parent / 'Temp' / 'uni_plpdem.dat'
    
    # Sum demand of all barras
    df_aggregated = df_all_profiles.groupby(['Year','Month','Block','Etapa']).sum(numeric_only=True)
    df_aggregated = df_aggregated.reset_index()
    df_aggregated = df_aggregated[['Month','Etapa','Consumo']]

    # Translate month to hidromonth
    df_aggregated = df_aggregated.replace({'Month': MONTH_TO_HIDROMONTH})

    # Write lines
    lines =  ['# Archivo de demandas por barra (plpdem.dat)']
    lines += ['#  Numero de barras']
    lines += ['001']
    lines += ['# Nombre de la Barra']
    lines += ["'UNINODAL'"]
    lines += ['# Numero de Demandas']
    lines += ['%s' % len(df_aggregated)]
    lines += ['# Mes  Etapa   Demanda']
    lines += [df_aggregated.to_string(
        index=False, header=False, formatters=formatters_plpdem)]
    
    # Write data from scratch
    f = open(uni_plpdem_path, 'w')
    f.write('\n'.join(lines))
    f.close()


@timeit
def write_plpfal_prn(blo_eta, df_all_profiles, iplp_path):
    plpfal_path = iplp_path.parent / 'Temp' / 'plpfal.prn'

    list_all_barras = get_list_of_all_barras(iplp_path)
    list_dem_barras = df_all_profiles['Barra Consumo'].unique().tolist()

    # Build df with zero-consumption barras
    df_zero_demand = blo_eta[['Month','Etapa']]
    df_zero_demand['NIntPot'] = [1] * len(df_zero_demand)
    df_zero_demand['PotMin'] = [0.0] * len(df_zero_demand)
    df_zero_demand['PotMax'] = [0.0] * len(df_zero_demand)
    
    # Transform df
    df_all_profiles['NIntPot'] = [1] * len(df_all_profiles)
    df_all_profiles['PotMin'] = [0.0] * len(df_all_profiles)
    df_all_profiles = df_all_profiles.rename(columns={'Consumo': 'PotMax'})
    df_all_profiles = df_all_profiles[['Barra Consumo','Month','Etapa','NIntPot','PotMin','PotMax']]

    # Translate month to hidromonth
    df_all_profiles = df_all_profiles.replace({'Month': MONTH_TO_HIDROMONTH})
    df_zero_demand = df_zero_demand.replace({'Month': MONTH_TO_HIDROMONTH})

    lines =  ['# Archivo de maximos de centrales de falla (plpfal.prn)']
    #  write data from scratch
    f = open(plpfal_path, 'w')
    f.write('\n'.join(lines))
    f.close()

    for idx, barra in enumerate(list_all_barras, 1):
        lines = ['\n# Nombre de la central']
        lines += ["'Falla_%s'" % idx]
        lines += ['#   Numero de Etapas e Intervalos']
        if barra in list_dem_barras:
            df_aux = df_all_profiles[df_all_profiles['Barra Consumo']==barra]
            df_aux = df_aux.drop('Barra Consumo', axis=1)
        else:
            df_aux = df_zero_demand
        lines += ['  %s                 01' % len(df_aux)]
        lines += ['#   Mes    Etapa  NIntPot   PotMin   PotMax']
        lines += [df_aux.to_string(
            index=False, header=False, formatters=formatters_plpfal)]

        #  write data for current barra
        f = open(plpfal_path, 'a')
        f.write('\n'.join(lines))
        f.close()


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
    df_dda_por_barra  = dda_por_barra_to_row_format(
        iplp_path, write_to_csv=True)

    # Get monthly demand from Sheet "DdaEnergia"
    logger.info('Processing DdaEnergia sheet')
    df_monthly_demand = get_monthly_demand(iplp_path)

    # Get hourly profiles from Sheet "PerfilesDDA"
    logger.info('Processing PerfilesDDA sheet')
    df_hourly_profiles = get_hourly_profiles(iplp_path)

    # Generate dataframe with profiles per Etapa
    logger.info('Generating dataframes with profiles per Etapa per Barra')
    df_all_profiles = get_all_profiles(
        blo_eta, block2day,
        df_monthly_demand, df_hourly_profiles, df_dda_por_barra)

    # Print to plpdem and uni_plpdem
    logger.info('Printing plpdem.dat and uni_plpdem.dat')
    write_plpdem_dat(df_all_profiles, iplp_path)
    write_uni_plpdem_dat(df_all_profiles, iplp_path)

    # Get failure units and generate plpfal.prn
    logger.info('Printing plpfal.prn')
    write_plpfal_prn(blo_eta, df_all_profiles, iplp_path)


if __name__ == "__main__":
    main()
