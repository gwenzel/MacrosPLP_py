'''
PLPCENPMAX

This script creates the PLPCENPMAX.dat file from the PMAXEmb sheet in the
IPLP file
'''

from utils.utils import (timeit,
                         define_arg_parser,
                         get_iplp_input_path,
                         check_is_path)
from utils.logger import add_file_handler, create_logger
import pandas as pd
from pathlib import Path


logger = create_logger('PLPCENPMAX')


def create_plpcenpmax_file(iplp_file: Path, path_inputs: Path):
    # Read data from the specified excel sheet
    df = pd.read_excel(iplp_file, sheet_name="PMAXEmb",
                       usecols="C:F", skiprows=3, engine='pyxlsb')

    # Get number of reservoirs
    num_reservoirs_value = int(df.iloc[0, 1])

    with open(path_inputs / "plpcenpmax.dat", "w", encoding='latin1') as f:
        f.write("# Archivo con cuva pmax en funcion del volumen\n")
        f.write("# Numero Embalses\n")
        f.write(f"{num_reservoirs_value}" + "\n")

        offset = 3  # to be updated in loop
        for _ in range(num_reservoirs_value):
            # Get reservoir central name
            cen_name = df.iloc[offset, 0].strip("'")
            # Get dam name
            dam_name = df.iloc[offset, 1].strip("'")
            # Get number of segments
            num_segments = int(df.iloc[offset, 2])
            # Write data to file
            f.write("# Nombre de Central".ljust(48) + "\n")
            f.write(f"'{cen_name}'".ljust(48) + "\n")
            f.write("# Nombre Embalse".ljust(48) + "\n")
            f.write(f"'{dam_name}'".ljust(48) + "\n")
            f.write("# Numero de Segmentos".ljust(48) + "\n")
            f.write(f"{num_segments}" + "\n")

            f.write("#Volumen       Pendiente     Coeficiente\n")
            for seg in range(num_segments):
                volume = df.iloc[offset + 1 + seg, 1]
                slope = df.iloc[offset + 1 + seg, 2]
                coef = df.iloc[offset + 1 + seg, 3]
                # Write al values in one row with 14 spaces each
                f.write(f"{volume:0.1f}".ljust(15) +
                        f"{slope:0.6f}".ljust(15) +
                        f"{coef:0.6f}".ljust(14) + "\n")

            # Offset for next reservoir
            offset += num_segments + 1


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
        add_file_handler(logger, 'PLPCENPMAX', path_log)

        logger.info('Printing PLPCENPMAX.dat')
        create_plpcenpmax_file(iplp_path, path_inputs)

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
