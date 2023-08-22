'''Barras

Module to generate:
- plpbar.dat
- uni_plpbar.dat
- plpbar_full.dat
'''
from utils.utils import (define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         create_logger,
                         write_lines_from_scratch)
import pandas as pd

logger = create_logger('barras')

formatter_plpbar = {
    "index":    "{:8d}".format,
    "BARRA":   "'{:<}'".format,
}

formatter_plpbar_full = {
    "index":    "{:8d}".format,
    "BARRA":    "'{:<}'".format,
    "Tension":  "{:8d}".format,
    "FlagDDA":  "{:8d}".format,
    "FlagGx":   "{:8d}".format,
}


def print_uni_plpbar(path_inputs):
    #  write data from scratch
    path_uni_plpbar = path_inputs / 'uni_plpbar.dat'
    lines = ['# Archivo con definicion de barras (plpbar.dat)']
    lines += ['# Numero de Barras']
    lines += ['       1']
    lines += ['# Numero       Nombre']
    lines += ["       1       'UNINODAL'"]

    write_lines_from_scratch(lines, path_uni_plpbar)


def print_plpbar(path_inputs, df_barras):
    # shape data
    df_aux = df_barras.reset_index()
    df_aux = df_aux[['index', 'BARRA']]

    #  write data from scratch
    path_plpbar = path_inputs / 'plpbar.dat'
    lines = ['# Archivo con definicion de barras (plpbar.dat)']
    lines += ['# Numero de Barras']
    lines += ['       %s' % len(df_barras)]
    lines += ['# Numero       Nombre']
    lines += [df_aux.to_string(
            index=False, header=False, formatters=formatter_plpbar)]

    write_lines_from_scratch(lines, path_plpbar)


def print_plpbar_full(path_inputs, df_barras):
    # shape data
    df_aux = df_barras.fillna(0)  # convert empty values (Trf) to 0
    df_aux = df_aux.reset_index()
    df_aux['FlagDDA'] = df_aux['FlagDDA'].astype(int)
    df_aux['FlagGx'] = df_aux['FlagGx'].astype(int)
    df_aux = df_aux[['index', 'BARRA', 'Tension', 'FlagDDA', 'FlagGx']]

    #  write data from scratch
    path_plpbar_full = path_inputs / 'plpbar_full.dat'
    lines = ['# Archivo con definicion de barras (plpbar.dat)']
    lines += ['# Numero de Barras']
    lines += ['       %s' % len(df_barras)]
    lines += ['# Numero                    Nombre  Tension       FL       FI']
    lines += [df_aux.to_string(
        index=False, header=False, formatters=formatter_plpbar_full)]
    write_lines_from_scratch(lines, path_plpbar_full)


def get_barras_info(iplp_path):
    return pd.read_excel(iplp_path, sheet_name="Barras",
                         skiprows=4, usecols="A:C,E:F")


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
    path_dat = iplp_path.parent / "Temp" / "Dat"
    check_is_path(path_dat)

    # Get if uninodal or not
    # UNINODAL = False

    # If uninodal, print dat file directly
    logger.info('Printing uni_plpbar')
    print_uni_plpbar(path_inputs)

    # Else, get list of all barras
    logger.info('Get list of all barras')
    df_barras = get_barras_info(iplp_path)

    # Print to file
    logger.info('Printing plpbar')
    print_plpbar(path_inputs, df_barras)

    logger.info('Printing plpbar_full')
    print_plpbar_full(path_inputs, df_barras)


if __name__ == "__main__":
    main()