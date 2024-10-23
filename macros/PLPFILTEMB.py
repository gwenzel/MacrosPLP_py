'''
PLPFILTEMB

This script creates the PLPFILTEMB.dat file
'''

from utils.utils import (timeit,
                         define_arg_parser,
                         get_iplp_input_path,
                         check_is_path)
from utils.logger import add_file_handler, create_logger
import pandas as pd
from pathlib import Path


logger = create_logger('PLPFILTEMB')


def create_plpfiltemb_file(iplp_file: Path, path_inputs: Path):

    # Read data from the specified excel sheet
    df = pd.read_excel(iplp_file, sheet_name="FILTRACIONES",
                       usecols="C:F", engine='pyxlsb')

    num_dams = df.iloc[3, 1]

    # Nombre de embalse, Filtraciones medias, Numero de Tramos,
    # Nombre Central Aguas abajo
    name_cols1 = df.iloc[4, :].tolist()
    # Tramo, Volumen, Pendiente, Constante
    name_cols2 = df.iloc[5, :].tolist()

    # Information block loop
    offset = 6  # Starting cell for information block (adjust if needed)
    info_data = []
    for i in range(num_dams):
        num_values = df.iloc[offset, 2]

        dict_values = {}
        # First information row (excluding reservoir ID)
        for j in range(len(name_cols1)):
            dict_values[name_cols1[j]] = df.iloc[offset, j]

        list_data = []
        # Filtration data loop for each reservoir
        for tramo in range(num_values):
            dict_values2 = {}
            for j in range(len(name_cols2)):
                dict_values2[name_cols2[j]] = df.iloc[offset + tramo + 1, j]
            list_data.append(dict_values2)

        dict_values["Data"] = list_data
        info_data.append(dict_values)

        '''
        # Filtration data loop for each reservoir
        for m in range(num_values):
            data_row = [" " * 5]  # Start with leading spaces
            for k in range(1, 5):
                cell_value = df.loc[offset + i + 1 + m, k + 2]
                if k == 1:
                    data_row.append(f"{cell_value:0d}{' ' * 5}")  # Integer format
                elif k <= 2:
                    data_row.append(f"{cell_value:.00f}{' ' * (10 if k == 2 else 12)}")  # Decimal format
                else:
                    data_row.append(f"{cell_value:.6f}{' ' * 12}")  # More decimal places format
            data_row[0] = data_row[0].replace(",", ".")  # Replace comma with dot
            info_data.append(data_row)

        # Last information row for each reservoir
        info_row = [f"{df.loc[6, 6]}{' ' * 37}"]
        info_row.append(f"'{df.loc[offset + i, 6]}'")  # String value with single quotes
        info_data.append(info_row)
        '''

        # Update offset for next reservoir block
        offset += num_values + 1

    # Create the plpfilemb.dat file
    with open(path_inputs / "plpfilemb.dat", "w", encoding="latin1") as f:
        f.write("# Archivo de Filtraciones de Embalses (plpfilemb.dat)\n")
        f.write("# Numero Embalses con filtraciones\n")
        f.write(f"{num_dams:0d}{' ' * 9}\n")

        for row in info_data:
            f.write(f"# {name_cols1[0]}{' ' * 36}\n")
            f.write(f"'{row[name_cols1[0]]}'{' ' * 36}\n")
            f.write(f"# {name_cols1[1]}{' ' * 36}\n")
            f.write(f"{row[name_cols1[1]]:.2f}{' ' * 9}\n")
            f.write(f"# {name_cols1[2]}{' ' * 36}\n")
            f.write(f"{row[name_cols1[2]]:0d}{' ' * 9}\n")
            names1 = f"{name_cols2[0]}{' ' * 4}{name_cols2[1]}{' ' * 2}"
            names2 = f"{name_cols2[2]}{' ' * 2}{name_cols2[3]}"
            f.write(f"#{names1}{names2}\n")
            for data in row["Data"]:
                tramo = f"{' ' * 5}{data[name_cols2[0]]:0d}{' ' * 5}"
                vol = f"{data[name_cols2[1]]:.2f}"
                len_spaces_vol = (10 - len(vol)) if len(vol) < 10 else 4
                pend = f"{data[name_cols2[2]]:.6f}{' ' * 4}"
                const = f"{data[name_cols2[3]]:.6f}"
                f.write(f"{tramo}{vol}{' ' * len_spaces_vol}{pend}{const}\n")
            f.write(f"# {name_cols1[3]}{' ' * 36}\n")
            f.write(f"'{row[name_cols1[3]]}'{' ' * 36}\n")


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

        logger.info('Printing PLPFILTEMB.dat')
        create_plpfiltemb_file(iplp_path, path_inputs)

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
