'''plpcnfce

Generate plpcnfce.dat file from IPLP input file with data from
sheet centrales.
'''
from utils.utils import (timeit,
                         define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         write_lines_from_scratch)
from macros.bar import get_barras_info
from utils.logger import add_file_handler, create_logger
import pandas as pd
from pathlib import Path


logger = create_logger('cen')

formatter_plpcnfce = {

}

formatter_plptec = {
    'Nombre': "{:<48}".format,
    'Fuel': "{:<23}".format,
    'FlagPerfil': "{:02d}".format
}


def read_df_centrales_all(iplp_path: Path):
    '''
    Read Centrales sheet and get all required fields
    '''
    df = pd.read_excel(iplp_path, sheet_name="Centrales",
                       skiprows=4, usecols="B:AX,BG,CF")
    '''
    'E EMBALSE
    'S PASADA EN SERIE HIDRÁULICA
    'R RIEGO
    'P PASADA
    'M PASADA CON REGULACIÓN
    'T TÉRMICA
    'F CENTRAL DE FALLA
    'X FUERA DE SERVICIO
    '''
    # Filter out if X
    df = df[df['Tipo de Central'] != 'X']
    # Rename columns
    df = df.rename(columns={'CENTRALES': 'Nombre'})
    # Select columns
    # df = df[['Nombre', 'Pmin', 'Pmax']]
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

'''


def add_failure_generators(iplp_path: Path, df_centrales: pd.DataFrame):
    df_buses = get_barras_info(iplp_path, add_flag_falla=True)
    df_buses_falla = df_buses[df_buses['FlagFalla']]

    df_gx_falla = pd.read_excel(iplp_path, sheet_name="GxFalla", skiprows=1)
    tramo = df_gx_falla.iloc[0, 0]
    # prof = df_gx_falla.iloc[0, 1]
    cost = df_gx_falla.iloc[0, 2]

    # Build df_centrales falla for tramo*num_buses centrales
    # Each of them is called FALLA_i, with i = 1, ..., num_buses
    # and its cost is cost
    df_centrales_falla = pd.DataFrame()
    # Get list of names and connected buses
    list_failure_names = []
    if tramo == 1:
        list_failure_names = ['FALLA_%s' % i for i in df_buses_falla['Nº']]
        list_bus_conected = df_buses_falla['Nº'].tolist()
    else:
        list_bus_conected = []
        for b in df_buses_falla['Nº']:
            for t in range(1, tramo + 1):
                list_failure_names.append('FALLA_%s_%s' % (b, t))
                list_bus_conected.append(b)
    # Add data to dataframe
    df_centrales_falla['Nombre'] = list_failure_names
    df_centrales_falla['Tipo de Central'] = 'F'
    df_centrales_falla['Costo Variable'] = cost
    df_centrales_falla['Conectada a la Barra'] = list_bus_conected
    df_centrales_falla['Pmax'] = 9999
    df = pd.concat([df_centrales, df_centrales_falla], axis=0)
    return df


def print_plpcnfce(path_inputs: Path, df_centrales: pd.DataFrame):
    '''
    Print plpcnfce.dat file
    '''
    num_gen = len(df_centrales)
    num_dam = len(df_centrales[df_centrales['Tipo de Central'] == 'E'])
    num_series = len(df_centrales[df_centrales['Tipo de Central'] == 'S'])
    num_runofriver = len(df_centrales[df_centrales['Tipo de Central'] == 'P'])
    num_failure = len(df_centrales[df_centrales['Tipo de Central'] == 'F'])

    path_plpcnfce = path_inputs / 'print_plpcnfce.dat'
    lines = ['# Archivo de configuracion de las centrales (plpcnfce.dat)']
    lines += ['# Num.Centrales  Num.Embalses Num.Serie Num.Fallas Num.Pas.Pur.']
    lines += ["     %s             %s           %s       %s        %s" %
              (num_gen, num_dam, num_series, num_failure, num_runofriver)]
    lines += ['# Interm Min.Tec. Cos.Arr.Det. FFaseSinMT EtapaCambioFase']
    lines += ['  F      F        F            F          00']
    lines += ['# Caracteristicas Centrales']
    lines += lines_dam(df_centrales)
    lines += lines_series(df_centrales)
    lines += lines_runofriver(df_centrales)
    lines += lines_thermal(df_centrales)
    lines += lines_failure(df_centrales)
    write_lines_from_scratch(lines, path_plpcnfce)


def lines_dam(df_centrales: pd.DataFrame):
    # TODO format df
    lines = ['# Centrales de Embalse']
    lines += [df_centrales[df_centrales['Tipo de Central'] == 'E'].to_string(
                index=False, header=False, formatters=formatter_plpcnfce)]
    return lines


def lines_series(df_centrales: pd.DataFrame):
    # TODO format df
    lines = ['# Centrales Serie Hidraulica']
    lines += [df_centrales[df_centrales['Tipo de Central'] == 'S'].to_string(
                index=False, header=False, formatters=formatter_plpcnfce)]
    return lines


def lines_runofriver(df_centrales: pd.DataFrame):
    # TODO format df
    lines = ['# Centrales Pasada Puras']
    lines += [df_centrales[df_centrales['Tipo de Central'] == 'P'].to_string(
                index=False, header=False, formatters=formatter_plpcnfce)]
    return lines


def lines_thermal(df_centrales: pd.DataFrame):
    # TODO format df
    lines = ['# Centrales Termicas o Embalses Equivalentes']
    lines += [df_centrales[df_centrales['Tipo de Central'] == 'T'].to_string(
                index=False, header=False, formatters=formatter_plpcnfce)]
    return lines


def lines_failure(df_centrales: pd.DataFrame):
    # TODO format df
    lines = ['# Centrales de Falla']
    lines += [df_centrales[df_centrales['Tipo de Central'] == 'F'].to_string(
                index=False, header=False, formatters=formatter_plpcnfce)]
    return lines


def print_plptec(path_inputs: Path, df_centrales: pd.DataFrame):
    '''
    Print plptec.dat file
    '''
    # Filter data
    df_centrales = df_centrales[df_centrales['Tipo de Central'] != 'X']
    df_centrales = df_centrales[df_centrales['Tipo de Central'] != 'F']
    # Make sure Nombre is not longer than 48 characters and
    # surround it by simple quotes
    if len(df_centrales['Nombre'].max()) > 48:
        logger.error('There is at least 1 central name longer'
                     ' than 48 characters.')
    df_centrales['Nombre'] = df_centrales['Nombre'].apply(
        lambda x: x[:48] if len(x) > 48 else x).apply(
            lambda x: "'%s'" % x)
    df_centrales['Fuel'] = df_centrales['Fuel'].fillna('none')
    df_centrales['Fuel'] = df_centrales['Fuel'].apply(
        lambda x: "'%s'" % x)
    df_centrales['FlagPerfil'] = df_centrales['CHECK Perfil'].apply(
        lambda x: 1 if x is True else 0)
    # Select columns
    df_centrales = df_centrales[['Nombre', 'Fuel', 'FlagPerfil']]
    path_plptec = path_inputs / 'plptec.dat'
    lines = ['# Archivo de tecnologia de centrales (plptec.dat)']
    lines += ['# Numero de centrales']
    lines += ['  %s' % len(df_centrales)]
    lines += ['# Central        Tecnologia      FlagPerfil']
    lines += [df_centrales.to_string(
                index=False, header=False, formatters=formatter_plptec)]
    write_lines_from_scratch(lines, path_plptec)


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

    # Read centrales data
    logger.info('Reading centrales data')
    df_centrales = read_df_centrales_all(iplp_path)

    # Print plptec
    logger.info('Printing plptec')
    print_plptec(path_inputs, df_centrales)

    #import pdb; pdb.set_trace()

    # Add failure data
    logger.info('Adding failure data')
    df_centrales = add_failure_generators(iplp_path, df_centrales)

    # Print plpcnfce
    logger.info('Printing plpcnfce')
    #print_plpcnfce(path_inputs, df_centrales)



    logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
