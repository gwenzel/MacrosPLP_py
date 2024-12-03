'''
PLPPLEM1

This script creates the PLPPLEM1.dat file
'''

from utils.utils import (timeit,
                         define_arg_parser,
                         get_iplp_input_path,
                         check_is_path)
from utils.logger import add_file_handler, create_logger
import pandas as pd
from pathlib import Path


logger = create_logger('PLPPLEM1')


def create_plpplem1_file(iplp_file: Path, path_inputs: Path):
    # Read the Excel file
    df = pd.read_excel(iplp_file, sheet_name='PLPPlanosEmb1', engine='pyxlsb',
                       usecols='A:K')

    # Remove spaces from column names
    df.columns = df.columns.str.strip()

    # Format the DataFrame for output
    df['Numero'] = df.index + 1
    df['Nombre'] = df['Nombre'].str.slice(stop=48).str.strip()
    df['Tipo'] = df['Tipo'].astype(str)
    df['Barra'] = df['Barra'].astype(int)
    df['N/A'] = '0'
    df['VolMin'] = df['VolMin'].astype(float).round(2)
    df['VolMax'] = df['VolMax'].astype(float).round(2)
    df['VolMinNECF'] = df['VolMinNECF'].astype(float).round(2)
    df['VolMaxNECF'] = df['VolMaxNECF'].astype(float).round(2)
    df['FEscala'] = df['FEscala'].astype(int)
    df['FactRendim'] = df['FactRendim'].astype(float).round(3)

    formatter_plpplem1_full = {
        "Numero": "{:3d},".format,
        "Nombre": "{:<48},".format,
        "Tipo": "{:<1},".format,
        "Barra": "{:>4},".format,
        "N/A": "{:>2},".format,
        "VolMin": "{:>11.2f},".format,
        "VolMax": "{:>11.2f},".format,
        "VolMinNECF": "{:>11.2f},".format,
        "VolMaxNECF": "{:>11.2f},".format,
        "FEscala": "{:>3},".format,
        "FactRendim": "{:>8.3f}".format
    }

    # Create the output string
    output_str = "#Numero, Nombre, Tipo, Barra, N/A, VolMin, VolMax, VolMinNECF, VolMaxNECF, FEscala, FactRendim\n"
    # output_str += df.to_csv(index=False, header=False, sep=',')
    output_str += df.to_string(index=False, header=False,
                               formatters=formatter_plpplem1_full)

    # Write the output to a file
    with open(path_inputs / 'plpplem1.dat', 'w', encoding='latin1') as f:
        f.write(output_str)


@timeit
def main():
    '''
    Main routine
    '''
    try:
        # Get input file path
        logger.info('Getting input file path')
        parser = define_arg_parser()
        iplp_path = get_iplp_input_path(parser)
        path_inputs = iplp_path.parent / "Temp"
        check_is_path(path_inputs)
        path_dat = iplp_path.parent / "Temp" / "Dat"
        check_is_path(path_dat)

        # Add destination folder to logger
        path_log = iplp_path.parent / "Temp" / "log"
        check_is_path(path_log)
        add_file_handler(logger, 'PLPPLEM1', path_log)

        logger.info('Printing PLPPLEM1.dat')
        create_plpplem1_file(iplp_path, path_inputs)

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
