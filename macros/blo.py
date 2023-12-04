'''PLPBLO

Generate PLPBLO.dat file from IPLP input file

'''
from utils.utils import (define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         process_etapas_blocks,
                         translate_to_hydromonth,
                         write_lines_from_scratch)
from utils.logger import create_logger
import pandas as pd
from pathlib import Path


logger = create_logger('plpblo')

formatter_plpblo = {
    'Bloque': "   {:03d}".format,
    'Etapa': "   {:03d}".format,
    'NHoras': "     {:03d}".format,
    'Ano': "   {:03d}".format,
    'Mes': "   {:03d}".format,
    'TipoBloque': "   '{:s}'".format,
}


def transform_blo_eta(blo_eta):
    '''
    Transform blo_eta to plpblo format
    '''
    blo_eta['Date'] = pd.to_datetime(
        dict(year=blo_eta['Year'], month=blo_eta['Month'], day=1))
    blo_eta['DaysInMonth'] = blo_eta['Date'].dt.days_in_month
    blo_eta['NHoras'] = blo_eta['Block_Len'] * blo_eta['DaysInMonth']
    blo_eta['TipoBloque'] = blo_eta['Block'].apply(lambda x: "Bloque %02d" % x)
    blo_eta = translate_to_hydromonth(blo_eta)
    blo_eta['Year'] = blo_eta['Year'] - blo_eta['Year'][0] + 1
    blo_eta = blo_eta.rename(columns={'Etapa': 'Bloque',
                                      'Block': 'Etapa',
                                      'Year': 'Ano',
                                      'Month': 'Mes'})
    return blo_eta[['Bloque', 'Etapa', 'NHoras',
                    'Ano', 'Mes', 'TipoBloque']]


def print_plpblo(path_inputs: Path, df_blo_eta: pd.DataFrame):
    '''
    Print plpblo.dat file
    '''
    path_plpblo = path_inputs / 'plpblo.dat'
    lines = ['# Archivo con la duracion de los bloques']
    lines += ['# Bloques']
    lines += ['    %s' % len(df_blo_eta)]
    lines += ['# Bloque   Etapa   NHoras  Ano   Mes  TipoBloque']
    lines += [df_blo_eta.to_string(
            index=False, header=False, formatters=formatter_plpblo)]
    write_lines_from_scratch(lines, path_plpblo)


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

    # Get Hour-Blocks-Etapas definition
    logger.info('Processing block to etapas files')
    blo_eta, _, _ = process_etapas_blocks(path_dat)

    # Transform blo_eta
    logger.info('Transforming blo_eta')
    df_blo_eta = transform_blo_eta(blo_eta)

    # Print blo_eta to file
    logger.info('Printing blo_eta to file')
    print_plpblo(path_inputs, df_blo_eta)

    logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
