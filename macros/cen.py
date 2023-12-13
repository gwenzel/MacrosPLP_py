'''plpcnfce

Generate plpcnfce.dat file from IPLP input file with data from
sheet centrales.
'''
from utils.utils import (timeit,
                         define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         process_etapas_blocks,
                         translate_to_hydromonthyear,
                         write_lines_from_scratch)
from utils.logger import add_file_handler, create_logger
import pandas as pd
from pathlib import Path


logger = create_logger('cen')


def read_df_centrales_all(iplp_path: Path):
    df = pd.read_excel(iplp_path, sheet_name="Centrales",
                       skiprows=4, usecols="B:AX")
    # Filter out if X
    df = df[df['Tipo de Central'] != 'X']
    # Rename columns
    df = df.rename(columns={
        'CENTRALES': 'Nombre',
        'Mínima.1': 'Pmin',
        'Máxima.1': 'Pmax'})
    # Select columns
    df = df[['Nombre', 'Pmin', 'Pmax']]
    return df


'''
'1) INDICE
'2) CENTRALES
'3) TIPO DE CENTRAL
'4) COSTO VARIABLE
'5) RENDIMIENTO
'6) CONECTADA A LA BARRA
'7) SERIE HIDRÁULICA GENERACIÓN
'8) SERIE HIDRÁULICA VERTIMIENTO
'9) FUNCIÓN COSTO FUTURO
'10) AFLUENTE ESTOCÁSTICO
'11) ESTADÍSTICA SEMANAL
'12) AFLUENTE PRIMERA SEMANA
'    INDEPENDENCIA HIDROLÓGICA - FLAG
'14) PRONÓSTICO DE DESHIELO - FLAG
'15) PRONÓSTICO DE DESHIELO - VOLUMEN MÍNIMO Hm3
'16) PRONÓSTICO DE DESHIELO - VOLUMEN MÁXIMO Hm3
'17) PRONÓSTICO DE DESHIELO - MES DEL PRONÓSTICO
'    PRONÓSTICO DE DESHIELO - PRONÓSTICO ASOCIADO
'19) COTA M.S.N.M. INICIAL
'20) COTA M.S.N.M. FINAL
'21) COTA M.S.N.M. MÍNIMA
'22) COTA M.S.N.M. MÁXIMA
'23) VOLUMEN DEL EMBALSE MILLONES DE M3 INICIAL
'24) VOLUMEN DEL EMBALSE MILLONES DE M3 FINAL
'25) VOLUMEN DEL EMBALSE MILLONES DE M3 MÍNIMO
'26) VOLUMEN DEL EMBALSE MILLONES DE M3 MÁXIMO
'27) POTENCIA NETA MÍNIMA
'28) POTENCIA NETA MÁXIMA
'29) VERTIMIENTO MÍNIMO
'30) VERTIMIENTO MÁXIMO

'E EMBALSE
'S PASADA EN SERIE HIDRÁULICA
'R RIEGO
'P PASADA
'M PASADA CON REGULACIÓN
'T TÉRMICA
'F CENTRAL DE FALLA
'X FUERA DE SERVICIO

'''

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
    add_file_handler(logger, 'cen', path_log)



    logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
