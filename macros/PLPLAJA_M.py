import pandas as pd
from pathlib import Path

from utils.logger import add_file_handler, create_logger
from utils.utils import (timeit,
                         check_is_path,
                         define_arg_parser,
                         get_iplp_input_path,
                         process_etapas_blocks)


logger = create_logger('PLPLAJA_M')


def create_plplaja_m(iplp_path: Path, path_inputs: Path):

    # Read the necessary sheets using pandas and pyxlsb
    path_df = pd.read_excel(iplp_path, sheet_name='Path', engine='pyxlsb')
    laja_df = pd.read_excel(iplp_path, sheet_name='LAJAm', engine='pyxlsb')

    # Verify initial condition
    if str(path_df.iloc[30, 0]).upper() == 'OFF':
        logger.info('Convenio Laja deshabilitado.')
        return
    logger.info('Convenio Laja habilitado.')

    # Directory and executable
    directorio = path_inputs

    # Open the output file for writing
    with open(directorio / "plplajam.dat", "w", encoding='latin1') as file:
        file.write(
            "# Archivo con la definicion del nuevo convenio de riego Laja\n")

        # Helper functions to format and write to file
        def write_str_line(df, row_idx, col_data_idx, col_format_idx):
            file.write(f"# {df.iloc[row_idx, col_data_idx]:<34}\n")
            ndata = int(df.iloc[row_idx, 4])
            if ndata > 1:
                for i in range(1, ndata + 1):
                    file.write(f"'{df.iloc[row_idx, 4 + i]}'".ljust(48) + "\n")
            else:
                file.write(
                    f"'{df.iloc[row_idx, col_format_idx]}'".ljust(48) + "\n")

        def write_int_line(df, row_idx, col_data_idx, col_format_idx):
            file.write(f"# {df.iloc[row_idx, col_data_idx]:<34}\n")
            ndata = int(df.iloc[row_idx, 4])
            if ndata > 1:
                for i in range(1, ndata + 1):
                    value = int(df.iloc[row_idx, 4 + i])
                    # if value is not nan
                    if value == value:
                        file.write(f"{value:<9} ")
                file.write("\n")
            else:
                file.write(f"{int(df.iloc[row_idx, col_format_idx]):<15}\n")

        def write_bool_line(df, row_idx, col_data_idx, col_format_idx):
            file.write(f"# {df.iloc[row_idx, col_data_idx]:<34}\n")
            ndata = int(df.iloc[row_idx, 4])
            if ndata > 1:
                for i in range(1, ndata + 1):
                    value = df.iloc[row_idx, 4 + i]
                    # if value is not nan
                    if value == value:
                        file.write(f"{str(value).upper():<} ")
                file.write("\n")
            else:
                file.write(f"{df.iloc[row_idx, col_format_idx]:<15}\n")

        def write_float_line(df, row_idx, col_data_idx, col_format_idx,
                             decimals=2):
            file.write(f"# {df.iloc[row_idx, col_data_idx]:<34}\n")
            ndata = int(df.iloc[row_idx, 4])
            if ndata > 1:
                for i in range(1, ndata + 1):
                    value = float(df.iloc[row_idx, 4 + i])
                    # if value is not nan
                    if value == value:
                        value_str_1f = f"{value:.1f}".replace(',', '.')
                        value_str_2f = f"{value:.2f}".replace(',', '.')
                        value_str_3f = f"{value:.3f}".replace(',', '.')
                        if decimals == 1:
                            file.write(f"{value_str_1f:<7} ")
                        elif decimals == 3:
                            file.write(f"{value_str_3f:<7} ")
                        else:
                            file.write(f"{value_str_2f:<7} ")
                file.write("\n")
            else:
                value = float(df.iloc[row_idx, col_format_idx])
                value_str_1f = f"{value:.1f}".replace(',', '.')
                value_str_2f = f"{value:.2f}".replace(',', '.')
                value_str_3f = f"{value:.3f}".replace(',', '.')
                if decimals == 1:
                    file.write(f"{value_str_1f:<15}\n")
                elif decimals == 3:
                    file.write(f"{value_str_3f:<15} ")
                else:
                    file.write(f"{value_str_2f:<15}\n")

        # Write the file
        write_str_line(laja_df, 3, 2, 5)
        write_int_line(laja_df, 4, 2, 5)
        write_str_line(laja_df, 5, 2, 5)
        write_int_line(laja_df, 6, 2, 5)
        write_int_line(laja_df, 7, 2, 5)
        write_int_line(laja_df, 8, 2, 5)
        write_float_line(laja_df, 9, 2, 5, decimals=2)
        write_float_line(laja_df, 10, 2, 5, decimals=2)
        write_float_line(laja_df, 11, 2, 5, decimals=2)
        write_int_line(laja_df, 12, 2, 5)
        write_int_line(laja_df, 13, 2, 5)
        write_int_line(laja_df, 14, 2, 5)
        write_float_line(laja_df, 15, 2, 5, decimals=1)
        write_float_line(laja_df, 16, 2, 5)
        write_float_line(laja_df, 17, 2, 5)
        write_float_line(laja_df, 18, 2, 5)
        write_float_line(laja_df, 19, 2, 5)
        write_float_line(laja_df, 20, 2, 5)
        write_float_line(laja_df, 21, 2, 5)
        write_float_line(laja_df, 22, 2, 5)
        write_float_line(laja_df, 23, 2, 5)
        write_float_line(laja_df, 24, 2, 5)
        write_int_line(laja_df, 25, 2, 5)
        write_int_line(laja_df, 26, 2, 5)
        write_str_line(laja_df, 27, 2, 5)
        write_str_line(laja_df, 28, 2, 5)
        write_float_line(laja_df, 29, 2, 5, decimals=3)
        write_str_line(laja_df, 30, 2, 5)
        write_str_line(laja_df, 31, 2, 5)
        write_float_line(laja_df, 32, 2, 5, decimals=3)
        write_str_line(laja_df, 33, 2, 5)
        write_str_line(laja_df, 34, 2, 5)
        write_float_line(laja_df, 35, 2, 5, decimals=3)
        write_float_line(laja_df, 36, 2, 5, decimals=1)
        write_float_line(laja_df, 37, 2, 5, decimals=1)
        write_float_line(laja_df, 38, 2, 5)
        write_float_line(laja_df, 39, 2, 5)
        write_float_line(laja_df, 40, 2, 5)
        write_float_line(laja_df, 41, 2, 5)
        write_int_line(laja_df, 42, 2, 5)

        file.write("# Retiros manuales de riego por etapa por retiro (m3/s)\n")
        file.write("# Etapas\n")
        file.write(f"{int(laja_df.iloc[44, 4])}\n")
        file.write("# Ind   1oReg     2oReg     Emer      Saltos\n")
        file.write("# Caudales forzados en El Toro (m3/s)\n")
        file.write("# Etapas\n")
        file.write(f"{int(laja_df.iloc[47, 4])}\n")

        file.write("# Ind  QGxElToro\n")
        file.write(f" 1         {laja_df.iloc[49, 5]:1.2f}".ljust(10) + "\n")
        file.write(f" 2         {laja_df.iloc[50, 5]:1.2f}".ljust(10) + "\n")
        file.write(f" 3         {laja_df.iloc[51, 5]:1.2f}".ljust(10) + "\n")


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
        add_file_handler(logger, 'PLPLAJA_M', path_log)

        # Get Hour-Blocks-Etapas definition
        logger.info('Processing block to etapas files')
        blo_eta, _, _ = process_etapas_blocks(path_dat, droptasa=False)

        # Create PLPLAJA_M files
        logger.info('Creating PLPLAJA_M files')
        create_plplaja_m(iplp_path, path_inputs)

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
