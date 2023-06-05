from utils.utils import (   timeit,
                            define_arg_parser,
                            get_iplp_input_path,
                            check_is_path,
                            create_logger,
                            process_etapas_blocks
)
import pandas as pd

logger = create_logger('cvariable')


def get_input_paths():
    logger.info('Getting input file path')
    parser = define_arg_parser()
    iplp_path = get_iplp_input_path(parser)
    path_inputs = iplp_path.parent / "Temp"
    check_is_path(path_inputs)
    path_dat = iplp_path.parent / "Temp" / "Dat"
    check_is_path(path_dat)
    return iplp_path, path_inputs, path_dat


def get_inputs(path_dat):
    logger.info('Processing csv inputs')
    blo_eta, _, _ = process_etapas_blocks(path_dat)
    blo_eta = blo_eta.drop(['Tasa'], axis=1)
    return blo_eta


@timeit
def main():
    # Get input file path
    iplp_path, path_inputs, path_dat, ext_inputs_path =\
        get_input_paths()

    # Get Hour-Blocks-Etapas definition
    blo_eta = get_inputs(path_dat)

    # Llenado Costo Variable - IM_to_CostoVariable
    # Diesel, coal & gas


    # PLPCOSCE.dat + CO2 tax * emissions factor




if __name__ == "__main__":
    main()