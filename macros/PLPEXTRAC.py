'''
PLPEXTRAC

This script creates the PLPEXTRAC.dat file
'''

from utils.utils import (timeit,
                         define_arg_parser,
                         get_iplp_input_path,
                         check_is_path)
from utils.logger import add_file_handler, create_logger
import pandas as pd
from pathlib import Path


logger = create_logger('PLPEXTRAC')


def create_plpextrac_file(iplp_file: Path, path_inputs: Path):

    # Read data from the specified excel sheet
    df = pd.read_excel(iplp_file, sheet_name="EXTRACCIONES",
                       usecols="C:E", engine='pyxlsb')

    # Read data from the DataFrame
    num_plants_name = df.iloc[3, 0]
    num_plants = df.iloc[3, 1]
    col_names = df.iloc[4, :].tolist()
    num_columns = 3  # len(col_names)
    info_data = []
    for i in range(num_plants):
        dict_values = {}
        for j in range(num_columns):
            cell_value = df.iloc[i + 5, j]
            if j == 1:  # Assuming first column is numeric
                cell_value = f"{cell_value:.1f}"
            else:
                cell_value = f"'{cell_value}'"
            dict_values[col_names[j]] = cell_value
        info_data.append(dict_values)

    # Create the plpextrac.dat file
    with open(path_inputs / "plpextrac.dat", "w") as f:
        f.write("# Archivo de Extracciones (plpextrac.dat)\n")
        f.write(f"# {num_plants_name}{' ' * 36}\n")
        f.write(f"{num_plants:0d}{' ' * 9}\n")

        for dict_values in info_data:
            for key, value in dict_values.items():
                f.write(f"# {key}{' ' * 36}\n")
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
        add_file_handler(logger, 'PLPEXTRAC', path_log)

        logger.info('Printing PLPEXTRAC.dat')
        create_plpextrac_file(iplp_path, path_inputs)

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
