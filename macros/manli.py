'''MANLI

Generate PLPMANLI.dat file with line availability data

'''
from utils.utils import (define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         create_logger,
                         write_lines_from_scratch)
import pandas as pd

from macros.lin import read_df_lines


logger = create_logger('manli')


def read_df_manli(iplp_path):
    df_lines = pd.read_excel(iplp_path, sheet_name='MantLIN',
                             usecols='B:G', skiprows=4)

def print_plpmanli(iplp_path):
    lineas = read_df_lines(iplp_path)


def main():
    '''
    Main routine
    '''
    # Get input file path
    logger.info('Getting input file path')
    parser = define_arg_parser()
    iplp_path = get_iplp_input_path(parser)
    path_inputs = iplp_path.parent / "Temp"
    check_is_path(path_inputs)

    logger.info('Read manli data')
    df_manli = read_df_manli(iplp_path)


    logger.info('Print manli data')
    print_plpmanli()



if __name__ == "__main__":
    main()
