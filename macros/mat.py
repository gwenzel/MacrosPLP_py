'''PLPMAT

Generate PLPMAT.dat file from IPLP input file

'''
from utils.utils import (timeit,
                         define_arg_parser,
                         get_iplp_input_path,
                         check_is_path, write_lines_from_scratch)
from utils.logger import add_file_handler, create_logger
import pandas as pd
from pathlib import Path


logger = create_logger('plpmat')


def read_num_iter(iplp_path: pd.DataFrame) -> int:
    '''
    Read number of iterations from sheet Path, D10
    '''
    df = pd.read_excel(iplp_path, sheet_name="Path",
                       usecols="D", index_col=None, header=8, nrows=1)
    return df.iloc[0, 0]


def print_plpmat(path_inputs: Path, num_iter: int):
    '''
    Print plpmat.dat file
    '''
    path_plpmat = path_inputs / 'plpmat.dat'
    lines = ['# Archivo con Parametros Matematicos (plpmat.dat) ']
    lines += ['# PDMaxIte    PDError UmbIntConf NPlanosPorDefecto']
    lines += ['  %d          0.001       0.001                50' % num_iter]
    lines += ['# PMMaxIte    PMError']
    lines += ['  10          5.0']
    lines += ['# Lambda CTasa CCauFal  CVert CInter Ctransm FCotFinEF '
              'FPreProc FPrevia']
    lines += ['  0.00   0.0   7000.0   0.01  0.01   0.01    F         '
              'F        F']
    lines += ['# FFixTrasm  FSeparaFCF  FGrabaCSV   FGrabaRES']
    lines += ['  T          F           T           F']
    lines += ['# ABLMax   ABLEpsilon NumEtaCF']
    lines += ['  20       0.001      1']
    lines += ['# FConvPGradx FConvPVar UmbGradX UmbVar']
    lines += ['  F           F         0.5      100']
    write_lines_from_scratch(lines, path_plpmat)


@timeit
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

    # Add destination folder to logger
    path_log = iplp_path.parent / "Temp" / "log"
    check_is_path(path_log)
    add_file_handler(logger, 'plpmat', path_log)

    # Number of iterations
    num_iter = read_num_iter(iplp_path)
    logger.info('Selected number of iterations is: %s' % num_iter)

    logger.info('Printing plpmat.dat')
    print_plpmat(path_inputs, num_iter)

    logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
