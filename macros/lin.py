'''Lin

Generate PLPCNFLI.dat file with information from tab Lineas

'''
from utils.utils import (define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         write_lines_from_scratch)
from utils.logger import create_logger
from pathlib import Path
import pandas as pd

logger = create_logger('lineas')

formatter_plpcnfli_full = {
    "Nombre A->B": "{:<48}".format,
    "Barra A": "{:8d}".format,
    "Barra B": "{:8d}".format,
    "A->B": "{:9.1f}".format,
    "B->A": "{:10.1f}".format,
    "V [kV]": "{:9.1f}".format,
    "R[ohm]": "{:7.3f}".format,
    "X[ohm]": "{:7.3f}".format,
    "Pérdidas": "{:>6}".format,
    "Nº de Tramos": "{:11d}".format,
    "Operativa": "{:>12}".format,
    "FlujoDC": "{:>12}".format
}


def read_losses(iplp_path: Path) -> (str, str):
    df = pd.read_excel(iplp_path, sheet_name='Líneas', usecols='M',
                       nrows=2, header=None, names=["Value"])
    bool_losses_value = df.iloc[0]["Value"]
    bool_losses = 'T' if bool_losses_value else 'F'
    point_losses = df.iloc[1]["Value"]
    return bool_losses, point_losses


def print_uni_plpcnfli(path_inputs: Path, iplp_path: Path):
    bool_losses, point_losses = read_losses(iplp_path)
    lines = ['# Archivo de configuracion de lineas (plpcnfli.dat)']
    lines += ['# Num.Lineas   Modela Perdidas  Perd.en.ERM   Ang. de Ref.']
    lines += ["           %s          %s             '%s'         1000.d0" %
              (0, bool_losses, point_losses)]
    write_lines_from_scratch(lines, path_inputs / 'uni_plpcnfli.dat')


def read_df_lines(iplp_path: Path) -> pd.DataFrame:
    df_lines = pd.read_excel(iplp_path, sheet_name='Líneas',
                             usecols='B:O', skiprows=4)
    # Filter out non-operative lines
    df_lines = df_lines[df_lines['Operativa']]
    # Check name length
    max_length = df_lines['Nombre A->B'].apply(lambda x: len(x)).max()
    if max_length > 48:
        logger.error('Los nombres de línea deben tener un largo'
                     'inferior a 48 caracteres')
    # Reorder columns
    reordered_cols = ['Nombre A->B', 'A->B', 'B->A', 'Barra A', 'Barra B',
                      'V [kV]', 'R[ohm]', 'X[ohm]', 'Pérdidas',
                      'Nº de Tramos', 'Operativa', 'FlujoDC']
    df_lines = df_lines[reordered_cols]
    # Replace boolean by string
    df_lines['Pérdidas'] = df_lines['Pérdidas'].replace(
        {True: 'T', False: 'F'})
    df_lines['Operativa'] = df_lines['Operativa'].replace(
        {True: 'T', False: 'F'})
    df_lines['FlujoDC'] = df_lines['FlujoDC'].replace(
        {True: 'T', False: 'F'})
    return df_lines


def print_plpcnfli(path_inputs: Path, iplp_path: Path, df_lines: pd.DataFrame):
    bool_losses, point_losses = read_losses(iplp_path)
    df_lines['Nombre A->B'] = df_lines['Nombre A->B'].apply(
        "'{}'".format, axis=1)
    lines = ['# Archivo de configuracion de lineas (plpcnfli.dat)']
    lines += ['# Num.Lineas   Modela Perdidas  Perd.en.ERM   Ang. de Ref.']
    lines += ["         %s          %s             '%s'         1000.d0" %
              (len(df_lines), bool_losses, point_losses)]
    lines += ["# Caracteristicas de las Lineas"]
    lines += ["# Nombre                                           "
              "FMaxA-B    FMaxB-A   BarraA   BarraB   Tension  R(Ohm)  X(ohm)"
              "   Mod.Perd.  Num.Tramos   Operativa    FlujoDC"]
    lines += [df_lines.to_string(
        index=False, header=False, formatters=formatter_plpcnfli_full)]
    lines += ['']
    write_lines_from_scratch(lines, path_inputs / 'plpcnfli.dat')


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

    logger.info('Write uni_plpcnfli.dat')
    print_uni_plpcnfli(path_inputs, iplp_path)

    logger.info('Read lines data')
    df_lines = read_df_lines(iplp_path)

    logger.info('Write plpcnfli.dat')
    print_plpcnfli(path_inputs, iplp_path, df_lines)

    logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
