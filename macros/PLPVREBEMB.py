'''
PLPVREBEMB'

This script creates the PLPVREBEMB.dat file
'''

from utils.utils import (timeit,
                         define_arg_parser,
                         get_iplp_input_path,
                         check_is_path)
from utils.logger import add_file_handler, create_logger
import pandas as pd
from pathlib import Path


logger = create_logger('PLPVREBEMB')


def create_plpvrebemb_file(iplp_file: Path, path_inputs: Path):

    # Read data from the specified excel sheet
    df = pd.read_excel(iplp_file, sheet_name="REBVERT", engine='pyxlsb')

    # Read data from the DataFrame
    num_dams_name = df.iloc[3, 2]
    num_dams = df.iloc[3, 3]

    # Information block loop
    offset = 5  # Starting cell for information block (adjust if needed)
    info_data = []
    for i in range(num_dams):
        dict_data = {}
        dict_data["Nombre del Embalse".ljust(35)] = \
            f"'{df.iloc[offset + i, 2]}'".ljust(48)  # String value
        dict_data["Volumen de Rebalse [ 10^3 m3 ]".ljust(35)] = \
            f"{round(df.iloc[offset + i, 3], 1):.2f}".ljust(37)
        dict_data["Costo de Rebalse".ljust(35)] = \
            f"{round(df.iloc[offset + i, 4], 1):.2f}".ljust(37)
        info_data.append(dict_data)

    # Create the plpvrebemb.dat file
    with open(path_inputs / "plpvrebemb.dat", "w", encoding="latin1") as f:
        f.write("# Archivo de volumenes de rebalses de embalses (plpvrebemb.dat)\n")
        f.write(f"# {num_dams_name}".ljust(48) + "\n")
        f.write(f"{num_dams:0d}".ljust(9) + "\n")

        for row in info_data:
            for key, value in row.items():
                f.write(f"# {key}\n")
                f.write(f"{value}\n")


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
        add_file_handler(logger, 'PLPVREBEMB', path_log)

        logger.info('Printing PLPVREBEMB.dat file')
        create_plpvrebemb_file(iplp_path, path_inputs)

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
