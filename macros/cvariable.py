from utils.utils import (   timeit,
                            define_arg_parser,
                            get_iplp_input_path,
                            get_ext_inputs_path,
                            check_is_path,
                            create_logger,
                            process_etapas_blocks
)
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
    blo_eta = blo_eta.drop(['Tasa'], axis=1)
    return blo_eta


def read_fuel_price(ext_inputs_path, fuel, scen):
    df_fuel_price = pd.read_csv(
        ext_inputs_path / ('%s_%s.csv' % (fuel, scen)),
        header=[0,1], index_col=[0,1], encoding='latin1')
    # TODO: validate names and format
    return df_fuel_price

def read_all_fuel_prices(ext_inputs_path, scen='Base'):
    # Carbon USD/ton, Gas USD/MMBtu, Diesel USD/ton
    fuel_prices = {}
    for fuel in ['coal', 'gas', 'diesel']:
        fuel_prices[fuel] = read_fuel_price(
            ext_inputs_path, fuel=fuel, scen=scen)
    return fuel_prices


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

    # leer mapeo central - factor de emisiones

    # leer mapeo año - impuesto emisiones

    # crear matriz de centrales - costos variables

    # crear matriz con impuestos

    # imprimir en csv

    # escribir en formato .dat

    
    import pdb; pdb.set_trace()



    # centrales,rendimientos y combustible asociado

    # Escribir Costos variables en formato IPLP de carbón

    # Escribir Costos variables en formato IPLP de Diesel

    # Escribir Costos variables en formato IPLP de GNL

    # formulas para impuesto CO2

    # formatos

    ##  PLPCOSCE.dat + CO2 tax * emissions factor




if __name__ == "__main__":
    main()