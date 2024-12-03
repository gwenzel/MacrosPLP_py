import pandas as pd
from pathlib import Path

from utils.logger import add_file_handler, create_logger
from utils.utils import (timeit,
                         check_is_path,
                         define_arg_parser,
                         get_iplp_input_path,
                         process_etapas_blocks)


logger = create_logger('PLPMAULE_N')


def create_plpmaule_n(iplp_path: Path, path_inputs: Path):

    # Read the necessary sheets using pandas and pyxlsb
    path_df = pd.read_excel(iplp_path, sheet_name='Path', engine='pyxlsb')
    maulen_df = pd.read_excel(iplp_path, sheet_name='MAULEN', engine='pyxlsb')

    # Verify initial condition
    if str(path_df.iloc[31, 0]).upper() == 'OFF':
        logger.info('Convenio Maule deshabilitado.')
        return
    logger.info('Convenio Maule habilitado.')

    # Directory and executable
    directorio = path_inputs

    # Open the output file for writing
    with open(directorio / "plpmaulen.dat", "w", encoding='latin1') as file:
        file.write(
            "# Archivo de convenio del Maule actualizado (plpmaulen.dat)\n")

        # Helper functions to format and write to file
        def write_str_line(df, row_idx, col_data_idx, col_format_idx):
            file.write(f"# {df.iloc[row_idx, col_data_idx]:<32}\n")
            ndata = int(df.iloc[row_idx, 4])
            if ndata > 1:
                for i in range(1, ndata + 1):
                    file.write(f"'{df.iloc[row_idx, 4 + i]}'".ljust(48) + "\n")
            else:
                file.write(
                    f"'{df.iloc[row_idx, col_format_idx]}'".ljust(48) + "\n")

        def write_int_line(df, row_idx, col_data_idx, col_format_idx):
            file.write(f"# {df.iloc[row_idx, col_data_idx]:<32}\n")
            ndata = int(df.iloc[row_idx, 4])
            if ndata > 1:
                for i in range(1, ndata + 1):
                    value = int(df.iloc[row_idx, 4 + i])
                    # if value is not nan
                    if value == value:
                        file.write(f"{value:<7} ")
                file.write("\n")
            else:
                file.write(f"{int(df.iloc[row_idx, col_format_idx]):<15}\n")

        def write_bool_line(df, row_idx, col_data_idx, col_format_idx):
            file.write(f"# {df.iloc[row_idx, col_data_idx]:<32}\n")
            ndata = int(df.iloc[row_idx, 4])
            if ndata > 1:
                for i in range(1, ndata + 1):
                    value = df.iloc[row_idx, 4 + i]
                    # if value is not nan
                    if value == value:
                        file.write(f"{str(value).upper():<} ")
                file.write("\n")
            else:
                file.write(f"{df.iloc[row_idx, col_format_idx]:<9}\n")

        def write_float_line(df, row_idx, col_data_idx, col_format_idx,
                             decimals=2):
            file.write(f"# {df.iloc[row_idx, col_data_idx]:<32}\n")
            ndata = int(df.iloc[row_idx, 4])
            if ndata > 1:
                for i in range(1, ndata + 1):
                    value = float(df.iloc[row_idx, 4 + i])
                    # if value is not nan
                    if value == value:
                        value_str_1f = f"{value:.1f}".replace(',', '.')
                        value_str_2f = f"{value:.2f}".replace(',', '.')
                        if decimals == 1:
                            file.write(f"{value_str_1f:<5} ")
                        else:
                            file.write(f"{value_str_2f:<5} ")
                file.write("\n")
            else:
                value = float(df.iloc[row_idx, col_format_idx])
                value_str_1f = f"{value:.1f}".replace(',', '.')
                value_str_2f = f"{value:.2f}".replace(',', '.')
                if decimals == 1:
                    file.write(f"{value_str_1f:<15}\n")
                else:
                    file.write(f"{value_str_2f:<15}\n")

        for i in range(3, 7):
            write_str_line(maulen_df, i, 2, 5)
        write_int_line(maulen_df, 7, 2, 5)
        write_str_line(maulen_df, 8, 2, 5)
        for row_idx in range(9, 24):  # Rows 11 to 26
            write_int_line(maulen_df, row_idx, 2, 5)
        write_float_line(maulen_df, 24, 2, 5, decimals=1)
        write_float_line(maulen_df, 25, 2, 5, decimals=1)
        write_int_line(maulen_df, 26, 2, 5)
        write_bool_line(maulen_df, 27, 2, 5)
        write_float_line(maulen_df, 28, 2, 5, decimals=1)
        write_float_line(maulen_df, 29, 2, 5, decimals=1)
        write_int_line(maulen_df, 30, 2, 5)
        write_int_line(maulen_df, 31, 2, 5)
        write_float_line(maulen_df, 32, 2, 5, decimals=1)
        write_int_line(maulen_df, 33, 2, 5)
        write_float_line(maulen_df, 34, 2, 5, decimals=1)
        write_int_line(maulen_df, 35, 2, 5)
        write_float_line(maulen_df, 36, 2, 5, decimals=1)
        write_bool_line(maulen_df, 37, 2, 5)
        write_int_line(maulen_df, 38, 2, 5)
        write_int_line(maulen_df, 39, 2, 5)
        write_float_line(maulen_df, 40, 2, 5, decimals=1)
        write_float_line(maulen_df, 41, 2, 5, decimals=1)
        write_float_line(maulen_df, 42, 2, 5, decimals=1)
        write_int_line(maulen_df, 43, 2, 5)
        write_float_line(maulen_df, 44, 2, 5, decimals=1)
        write_int_line(maulen_df, 45, 2, 5)
        write_str_line(maulen_df, 46, 2, 5)
        write_float_line(maulen_df, 47, 2, 5)
        write_bool_line(maulen_df, 48, 2, 5)
        write_str_line(maulen_df, 49, 2, 5)
        write_float_line(maulen_df, 50, 2, 5, decimals=1)
        write_int_line(maulen_df, 51, 2, 5)
        write_int_line(maulen_df, 52, 2, 5)
        write_bool_line(maulen_df, 53, 2, 5)
        # write_int_line(maulen_df, 54, 2, 5)


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
        add_file_handler(logger, 'PLPMAULE_N', path_log)

        # Get Hour-Blocks-Etapas definition
        logger.info('Processing block to etapas files')
        blo_eta, _, _ = process_etapas_blocks(path_dat, droptasa=False)

        # Create PLPMAULE_N files
        logger.info('Creating PLPMAULE_N files')
        create_plpmaule_n(iplp_path, path_inputs)

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
