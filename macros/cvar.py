from utils.utils import (   timeit,
                            define_arg_parser,
                            get_iplp_input_path,
                            get_ext_inputs_path,
                            check_is_path,
                            process_etapas_blocks
)
from utils.logger import create_logger
import pandas as pd

logger = create_logger('cvariable')


def get_input_paths():
    logger.info('Getting input file path')
    parser = define_arg_parser(ext=True)
    iplp_path = get_iplp_input_path(parser)
    path_inputs = iplp_path.parent / "Temp"
    check_is_path(path_inputs)
    path_dat = iplp_path.parent / "Temp" / "Dat"
    check_is_path(path_dat)
    ext_inputs_path = get_ext_inputs_path(parser)
    check_is_path(ext_inputs_path)
    return iplp_path, path_inputs, path_dat, ext_inputs_path


def get_blo_eta(path_dat):
    logger.info('Processing csv inputs')
    blo_eta, _, _ = process_etapas_blocks(path_dat)
    return blo_eta


def read_fuel_price(ext_inputs_path, fuel, scen):
    df_fuel_price = pd.read_csv(
        ext_inputs_path / ('%s_%s.csv' % (fuel, scen)),
        header=[0, 1], index_col=[0, 1], encoding='latin1')
    return df_fuel_price


def validate_fuel_price(df_fuel_price):
    # TODO validate names and values
    pass


def read_all_fuel_prices(ext_inputs_path, scen='Base'):
    '''
    Build dictionary of dataframes with fuel price info
    for Carbon USD/ton, Gas USD/MMBtu, Diesel USD/ton
    '''
    fuel_prices = {}
    fuels_list = ['coal', 'gas', 'diesel']
    for fuel in fuels_list:
        fuel_prices[fuel] = read_fuel_price(
            ext_inputs_path, fuel=fuel, scen=scen)
        validate_fuel_price(fuel_prices[fuel])
    return fuel_prices


def read_unit_emissions_mapping(iplp_path):
    df = pd.read_excel(iplp_path, sheet_name='Centrales',
                       usecols='B,BY', skiprows=4,
                       index_col='CENTRALES')
    return df.to_dict()['Factor Emisiones CO2  TonCO2/MWh']


def read_rend_and_unit_fuel_mapping(iplp_path):
    '''
    Build dictionaries for performance (rend) and fuel price name
    Rend values: for Carbon ton/MWh, Gas MMBtu/MWh, Diesel ton/MWh
    '''
    df = pd.read_excel(iplp_path, sheet_name='Rendimientos y CVarNcomb',
                       usecols='B,D:E', index_col='Central')
    dict_unit_rend = df.to_dict()['Rendimiento']
    dict_unit_fuel_price_name = df.to_dict()['Combustible OSE']
    return dict_unit_rend, dict_unit_fuel_price_name


def read_year_co2_tax(iplp_path):
    df = pd.read_excel(iplp_path, sheet_name='CVariable',
                       usecols='J:K', skiprows=4,
                       index_col='Year').dropna(how='any')
    return df.to_dict()['CO2 Tax in USD/TonCO2']


def calculate_cvar(blo_eta, fuel_prices, dict_unit_rend,
                   dict_unit_fuel_price_name):

    df_coal_prices = fuel_prices['coal']
    df_gas_prices = fuel_prices['gas']
    df_diesel_prices = fuel_prices['diesel']

    year_ini = blo_eta.loc[0, 'Year']
    month_ini = blo_eta.loc[0, 'Month']

    year_end = blo_eta.loc[len(blo_eta) - 1, 'Year']
    month_end = blo_eta.loc[len(blo_eta) - 1, 'Month']

    # Merge dfs to keep the units we want
    for unit, rend in dict_unit_rend.items():
        fuel_price = dict_unit_fuel_price_name[unit]
        #stacked_fuel_price = fuel_prices['coal'].stack(level=[0, 1])


    df_unit_cvar = pd.DataFrame()
    return df_unit_cvar


@timeit
def main():
    # Get input file path
    iplp_path, path_inputs, path_dat, ext_inputs_path =\
        get_input_paths()

    # Get Hour-Blocks-Etapas definition
    blo_eta = get_blo_eta(path_dat)

    ##  Llenado Costo Variable - IM_to_CostoVariable
    # borrar datos
    fuel_prices =\
        read_all_fuel_prices(ext_inputs_path, scen='Base')

    # leer rendimientos y mapeo central-combustible
    dict_unit_rend, dict_unit_fuel_price_name =\
        read_rend_and_unit_fuel_mapping(iplp_path)

    # leer mapeo central - factor de emisiones
    dict_unit_emissions =\
        read_unit_emissions_mapping(iplp_path)

    # leer mapeo año - impuesto emisiones
    dict_year_co2_tax = read_year_co2_tax(iplp_path)

    import pdb; pdb.set_trace()

    # crear matriz de centrales - costos variables

    df_unit_cvar = calculate_cvar(blo_eta, fuel_prices, dict_unit_rend,
                                  dict_unit_fuel_price_name)

    # crear matriz sumando impuestos

    # imprimir matrices en csv

    # convertir a etapas y considerar resolución diaria

    # escribir en formato .dat
    
    # Mantener datos en IPLP? 
    # Escribir Costos variables en formato IPLP de carbón, diésel y GNL?


if __name__ == "__main__":
    main()
