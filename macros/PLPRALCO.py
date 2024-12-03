import pandas as pd
from pathlib import Path

from utils.logger import add_file_handler, create_logger
from utils.utils import (timeit,
                         check_is_path,
                         define_arg_parser,
                         get_iplp_input_path)


logger = create_logger('PLPRALCO')


def create_plpralco(iplp_path: Path, path_inputs: Path):

    df = pd.read_excel(iplp_path, sheet_name='RestRalco', engine='pyxlsb')

    # Read data from the DataFrame
    rest1_name = df.iloc[3, 2]
    rest1_value = df.iloc[3, 5]
    rest2_name = df.iloc[4, 2]
    rest2_value = df.iloc[4, 5]
    vcota_data = df.iloc[5:, 5:]

    # Create the plpralco.dat file
    with open(path_inputs / "plpralco.dat", "w", encoding="latin1") as f:
        f.write("# Archivo con la definicion de resrticcion de Ralco\n")

        # Lake name and restriction name
        f.write(f"# {rest1_name}{' ' * 40}\n")
        f.write(f"'{rest1_value}' \n")

        # Number of segments
        f.write(f"# {rest2_name}".ljust(40) + "\n")
        f.write(f"{rest2_value:0d}".ljust(14) + "\n")

        # Header row for Vcota data
        f.write("# Vol          a       b\n")

        # Vcota data with formatting
        for index, row in vcota_data.iterrows():
            vol = f"{row.iloc[0]:.1f}".ljust(15)
            a = f"{row.iloc[1]:.3f}".ljust(8)
            b = f"{row.iloc[2]}".ljust(11)
            f.write(f"{vol}{a}{b}\n")


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
        add_file_handler(logger, 'PLPRALCO', path_log)

        # Create PLPLAJA_M files
        logger.info('Creating PLPRALCO files')
        create_plpralco(iplp_path, path_inputs)

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
