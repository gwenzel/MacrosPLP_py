'''
PLPCENRE

This script creates the PLPCENRE.dat file from the RENDIMIENTOS sheet in the
IPLP file
'''

from utils.utils import (timeit,
                         define_arg_parser,
                         get_iplp_input_path,
                         check_is_path)
from utils.logger import add_file_handler, create_logger
import pandas as pd
from pathlib import Path


logger = create_logger('PLPCENRE')


def create_plpcenre_file(iplp_file: Path, path_inputs: Path):
    """
    Creates a plpcenre.dat file from an Excel file.

    Args:
        excel_file: The path to the Excel file.
    """

    # Read data from the specified Excel sheet
    df = pd.read_excel(iplp_file, sheet_name="RENDIMIENTOS",
                       engine='pyxlsb')

    # Open output file for writing
    with open(path_inputs / "plpcenre.dat", "w", encoding='latin1') as f:
        # Write header lines
        f.write("# Archivo de Rendimiento de Embalses (plpcenre.dat)\n")
        f.write("# Número de Embalses con Rendimiento\n")
        num_embalses = df.iloc[4, 2]
        f.write(str(num_embalses) + "\n")

        # Iterate over each reservoir
        for i in range(num_embalses):
            row_index = 6 + i * 10
            f.write("# Nombre de Central\n")
            f.write(f"'{df.iloc[row_index, 2]}'\n")
            f.write("# Nombre del Embalse\n")
            f.write(f"'{df.iloc[row_index + 2, 2]}'\n")
            f.write("# Rendimiento Medio\n")
            f.write(f"{df.iloc[row_index + 4, 2]:.3f}\n")
            f.write("# Numero de Tramos\n")
            num_tramos = df.iloc[row_index + 6, 2]
            f.write(str(int(num_tramos)) + "\n")
            f.write("#Tramo\tVolumen\t\tPendiente\tConstante\tF.Escala\n")
            for j in range(num_tramos):
                value_row_index = row_index + 8
                tramo = j + 1
                vol = df.iloc[value_row_index, 3]
                pend = df.iloc[value_row_index, 4]
                const = df.iloc[value_row_index, 5]
                fe = df.iloc[value_row_index, 6]
                f.write(f" {tramo:5d}\t{vol:.7f}\t{pend:.7f}\t{const:.7f}\t{fe:.1E}\n")


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
        add_file_handler(logger, 'plpmat', path_log)

        logger.info('Printing PLPCENRE.dat')
        create_plpcenre_file(iplp_path, path_inputs)

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
