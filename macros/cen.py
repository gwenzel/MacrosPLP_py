'''plpcnfce

Generate plpcnfce.dat and plptec.dat files from IPLP input file with data from
sheet centrales.
'''
import math
from utils.utils import (timeit,
                         define_arg_parser,
                         get_iplp_input_path,
                         check_is_path,
                         write_lines_from_scratch)
from macros.bar import get_barras_info
from macros.func_cdec.lmaule import Vol_LMAULE, Rend_LMAULE
from macros.func_cdec.cipreses import Vol_CIPRESES, Rend_CIPRESES
from macros.func_cdec.pehuenche import Vol_PEHUENCHE, Rend_PEHUENCHE
from macros.func_cdec.colbun import Vol_COLBUN, Rend_COLBUN
from macros.func_cdec.eltoro import Vol_ELTORO, Rend_ELTORO
from macros.func_cdec.rapel import Vol_RAPEL, Rend_RAPEL
from macros.func_cdec.canutillar import Vol_CANUTILLAR, Rend_CANUTILLAR
from macros.func_cdec.ralco import Vol_RALCO, Rend_RALCO
from macros.func_cdec.pangue import Vol_PANGUE, Rend_PANGUE

from utils.logger import add_file_handler, create_logger
import pandas as pd
from pathlib import Path


logger = create_logger('cen')

dict_dam_volfunc = {
    "'LMAULE'": Vol_LMAULE,
    "'CIPRESES'": Vol_CIPRESES,
    "'PEHUENCHE'": Vol_PEHUENCHE,
    "'COLBUN'": Vol_COLBUN,
    "'ELTORO'": Vol_ELTORO,
    "'RAPEL'": Vol_RAPEL,
    "'CANUTILLAR'": Vol_CANUTILLAR,
    "'RALCO'": Vol_RALCO,
    "'PANGUE'": Vol_PANGUE
}

dict_dam_rendfunc = {
    "'LMAULE'": Rend_LMAULE,
    "'CIPRESES'": Rend_CIPRESES,
    "'PEHUENCHE'": Rend_PEHUENCHE,
    "'COLBUN'": Rend_COLBUN,
    "'ELTORO'": Rend_ELTORO,
    "'RAPEL'": Rend_RAPEL,
    "'CANUTILLAR'": Rend_CANUTILLAR,
    "'RALCO'": Rend_RALCO,
    "'PANGUE'": Rend_PANGUE
}


formatter_plpcnfce = {

}

formatter_plptec = {
    'Nombre': "{:<48}".format,
    'Fuel': "{:<23}".format,
    'FlagPerfil': "{:02d}".format
}


def read_df_centrales_all(iplp_path: Path) -> pd.DataFrame:
    '''
    Read Centrales sheet and get all required fields
    '''
    df = pd.read_excel(iplp_path, sheet_name="Centrales",
                       skiprows=4, usecols="A:AX,BG,CF")
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
    validate_column_names(df)
    # Filter out if X
    df = df[df['Tipo de Central'] != 'X']
    # Rename columns
    df = df.rename(columns={
        'INDICE': 'NumCen',
        'CENTRALES': 'Nombre',
        'Costo Variable': 'CosVar',
        'Rendimiento': 'Rendi',
        'Inicial': 'CotaIni',
        'Final': 'CotaFin',
        'Mínima': 'CotaMin',
        'Máxima': 'CotaMax',
        'Inicial.1': 'VolIni',
        'Final.1': 'VolFin',
        'Mínimo': 'VolMin',
        'Máximo': 'VolMax',
        'Mínima.1': 'Pmin',
        'Máxima.1': 'Pmax',
        'Mínimo.1': 'VertMin',
        'Máximo.1': 'VertMax',
        'Afluente Primera Semana': 'Afluen',
        'Función Costo Futuro': 'EmbCFUE',
        'Independencia Hidrológica': 'Hid_Indep'})
    # Fill data
    df['CosVar'] = df['CosVar'].fillna(0)
    df['Hid_Indep'] = df[
        'Hid_Indep'].apply(
        lambda x: 'T' if x == 1 else 'F')
    df['EmbCFUE'] = df[
        'EmbCFUE'].apply(
        lambda x: 'T' if x == 1 else 'F')
    df['Afluen'] = df[
        'Afluen'].fillna(0)
    df['Generación'] = df['Generación'].fillna(0)
    df['Vertimiento'] = df['Vertimiento'].fillna(0)
    df['VertMin'] = df['VertMin'].fillna(0)
    df['VertMax'] = df['VertMax'].fillna(0)
    # Add new fields
    # Select columns
    # Clean and format
    df = clean_and_format_df_centrales(df)
    validate_df_centrales(df)
    return df


def clean_and_format_df_centrales(df: pd.DataFrame):
    # Remove rows where Nombre is empty
    df = df[df['Nombre'].notna()]
    return df


def validate_column_names(df: pd.DataFrame):
    # Check if df_centrales has expected column names
    expected_columns = [
        'INDICE', 'CENTRALES', 'Tipo de Central', 'Costo Variable',
        'Rendimiento', 'Inicial', 'Final', 'Mínima', 'Máxima',
        'Inicial.1', 'Final.1', 'Mínimo', 'Máximo', 'Mínima.1', 'Máxima.1',
        'Mínimo.1', 'Máximo.1', 'Afluente Primera Semana',
        'Función Costo Futuro', 'Independencia Hidrológica']
    # Check if df columns contain expected columns
    for column in expected_columns:
        if column not in df.columns:
            logger.error('Centrales sheet must have column: %s' % column)
        assert column in expected_columns, \
            "Centrales sheet must have column: %s" % column


def validate_df_centrales(df_centrales: pd.DataFrame):
    # Check if there are repeated names
    if df_centrales['Nombre'].duplicated().any():
        logger.error('There are repeated names in Centrales sheet')
    # Check if there are repeated NumCen
    if df_centrales['NumCen'].duplicated().any():
        logger.error('There are repeated NumCen in Centrales sheet')
    # Check if there are empty names
    if df_centrales['Nombre'].isna().any():
        logger.error('There are empty names in Centrales sheet')
    # Check if there are empty NumCen
    if df_centrales['NumCen'].isna().any():
        logger.error('There are empty NumCen in Centrales sheet')
    # Check if there are empty CosVar
    if df_centrales['CosVar'].isna().any():
        logger.warning('There are empty CosVar in Centrales sheet')
    # Assert dtypes
    assert df_centrales.dtypes['NumCen'] == 'float64', \
        "NumCen must be float64"
    assert df_centrales.dtypes['CosVar'] == 'float64', \
        "CosVar must be float64"
    assert df_centrales.dtypes['CotaIni'] == 'float64', \
        "CotaIni must be float64"
    assert df_centrales.dtypes['CotaFin'] == 'float64', \
        "CotaFin must be float64"
    assert df_centrales.dtypes['CotaMin'] == 'float64', \
        "CotaMin must be float64"
    assert df_centrales.dtypes['CotaMax'] == 'float64', \
        "CotaMax must be float64"
    assert df_centrales.dtypes['Pmin'] == 'float64', \
        "Pmin must be float64"
    assert df_centrales.dtypes['Pmax'] == 'float64', \
        "Pmax must be float64"
    assert df_centrales.dtypes['VertMin'] == 'float64', \
        "VertMin must be float64"
    assert df_centrales.dtypes['VertMax'] == 'float64', \
        "VertMax must be float64"
    assert df_centrales.dtypes['Afluen'] == 'float64', \
        "Afluen must be float64"


def add_failure_generators(iplp_path: Path,
                           df_centrales: pd.DataFrame) -> pd.DataFrame:
    '''
    Add failure generators to df_centrales
    '''
    df_buses = get_barras_info(iplp_path, add_flag_falla=True)
    df_buses_falla = df_buses[df_buses['FlagFalla']]

    df_gx_falla = pd.read_excel(iplp_path, sheet_name="GxFalla", skiprows=1)
    # Drop rows if any value is nan
    df_gx_falla = df_gx_falla.dropna()
    # Check shape
    if df_gx_falla.shape[0] != 1:
        logger.error('GxFalla sheet must have only 1 row')
    # Check column names
    if df_gx_falla.columns.tolist() != [
            'TRAMO', 'PROFUNDIDAD', 'COSTO DE FALLA']:
        logger.error('GxFalla sheet must have columns: '
                     'TRAMO, PROFUNDIDAD, COSTO DE FALLA')
    # tramo = df_gx_falla.iloc[0, 0]
    # prof = df_gx_falla.iloc[0, 1]
    cost = df_gx_falla.iloc[0, 2]

    # Build df_centrales falla for tramo*num_buses centrales
    # Each of them is called FALLA_i, with i = 1, ..., num_buses
    # and its cost is cost
    df_centrales_falla = pd.DataFrame()
    # Get list of names and connected buses
    list_failure_names = []
    # if tramo == 1:
    list_failure_names = ['FALLA_%03d' % i for i in df_buses_falla['Nº']]
    list_bus_conected = df_buses_falla['Nº'].tolist()
    '''
    else:
        list_bus_conected = []
        for b in df_buses_falla['Nº']:
            for t in range(1, tramo + 1):
                list_failure_names.append('FALLA_%03d_%s' % (b, t))
                list_bus_conected.append(b)
    '''
    # Add data to dataframe
    last_index = int(df_centrales['NumCen'].max())
    df_centrales_falla['NumCen'] = range(
        last_index + 1, last_index + 1 + len(list_failure_names))
    df_centrales_falla['Nombre'] = list_failure_names
    df_centrales_falla['Tipo de Central'] = 'F'
    df_centrales_falla['CosVar'] = cost
    df_centrales_falla['Rendi'] = 1
    df_centrales_falla['Conectada a la Barra'] = list_bus_conected
    df_centrales_falla['Pmax'] = 9999
    df_centrales_falla['Pmin'] = 0
    df_centrales_falla['VertMin'] = 0
    df_centrales_falla['VertMax'] = 0
    df_centrales_falla['Generación'] = 0
    df_centrales_falla['Vertimiento'] = 0
    df_centrales_falla['Afluen'] = 0
    df_centrales_falla['Hid_Indep'] = 'F'
    df = pd.concat([df_centrales, df_centrales_falla], axis=0)
    df = df.reset_index(drop=True)
    return df


def print_plpcnfce(path_inputs: Path, df_centrales: pd.DataFrame):
    '''
    Print plpcnfce.dat file
    '''
    num_gen = len(df_centrales)
    num_dam = len(df_centrales[df_centrales['Tipo de Central'] == 'E'])
    num_series = len(df_centrales[df_centrales['Tipo de Central'] == 'S']) +\
        len(df_centrales[df_centrales['Tipo de Central'] == 'R'])
    num_runofriver = len(df_centrales[df_centrales['Tipo de Central'] == 'P'])
    num_failure = len(df_centrales[df_centrales['Tipo de Central'] == 'F'])

    path_plpcnfce = path_inputs / 'plpcnfce.dat'
    lines = ['# Archivo de configuracion de las centrales (plpcnfce.dat)']
    lines += [
        '# Num.Centrales  Num.Embalses Num.Serie Num.Fallas Num.Pas.Pur.']
    lines += ["     %s             %s           %s       %s        %s" %
              (num_gen, num_dam, num_series, num_failure, num_runofriver)]
    lines += ['# Interm Min.Tec. Cos.Arr.Det. FFaseSinMT EtapaCambioFase']
    lines += ['  F      F        F            F          00']
    lines += ['# Caracteristicas Centrales']
    lines += lines_dam(df_centrales[df_centrales['Tipo de Central'] == 'E'])
    lines += lines_central(df_centrales, type='S')
    lines += lines_central(df_centrales, type='P')
    lines += lines_central(df_centrales, type='T')
    lines += lines_central(df_centrales, type='F')
    write_lines_from_scratch(lines, path_plpcnfce)


def apply_plp_functions(row: pd.Series) -> tuple[pd.Series, float]:
    '''
    Apply Vol and Rend functions to row
    '''
    # Apply Vol functions
    # If Macro function did not work, the result will be a string,
    # and therefore the python equivalent function will be used
    if row['Nombre'] in dict_dam_volfunc.keys():
        vol_func = dict_dam_volfunc[row['Nombre']]
        try:
            row['VolIni'] = vol_func(row['CotaIni']) * 1000000 if type(
                row['VolIni']) is str else row['VolIni'] * 1000000
            row['VolFin'] = vol_func(row['CotaFin']) * 1000000 if type(
                row['VolFin']) is str else row['VolFin'] * 1000000
            row['VolMin'] = vol_func(row['CotaMin']) * 1000000 if type(
                row['VolMin']) is str else row['VolMin'] * 1000000
            row['VolMax'] = vol_func(row['CotaMax']) * 1000000 if type(
                row['VolMax']) is str else row['VolMax'] * 1000000
        except Exception as e:
            logger.error('Error in PLP Volume function for %s' % row['Nombre'])
            logger.error('Change Cota or fix function in macros/func_cdec')
            logger.error(e)
            raise ValueError('Error in PLP Volume function for %s' %
                             row['Nombre'])
        factor_escala = 10**int(math.log10(row['VolMax']) + 0.5)
    else:
        logger.error('Vol function for %s not found' % row['Nombre'])
        factor_escala = 1
    # Apply Rend functions
    if row['Nombre'] in dict_dam_rendfunc.keys():
        rend_func = dict_dam_rendfunc[row['Nombre']]
        try:
            row['Rendi'] = rend_func(row['CotaIni']) if type(
                row['Rendi']) is str else row['Rendi']
        except Exception as e:
            logger.error('Error in PLP Rendi function for %s' % row['Nombre'])
            logger.error('Change CotaIni or fix function in macros/func_cdec')
            logger.error(e)
            raise ValueError('Error in PLP Rendi function for %s' %
                             row['Nombre'])
    else:
        logger.error('Rendi function for %s not found' % row['Nombre'])
        raise ValueError('Rendi function for %s not found' % row['Nombre'])
    return row, factor_escala


def lines_dam(df: pd.DataFrame) -> list:
    '''
    Get lines for each dam
    '''
    df.loc[:, 'Nombre'] = df['Nombre'].apply(lambda x: "'%s'" % x)
    lines = ['# Centrales de Embalse']
    for _, row in df.iterrows():
        # Calculations
        dict1, dict2, dict3 = calculate_cen_data(row, type='E')
        # Write lines
        lines += ["                                                      "
                  "IPot MinTec  Inter   FCAD    Cen_MTTdHrz Hid_Indep"
                  "  Cen_NEtaArr Cen_NEtaDet"]
        lines += [" {num_cen: >4d} {nom_cen:<47} {IPot:<4} {MinTec:<7} "
                  "{Inter:<7} {FCAD:<7} {Cen_MTTdHrz:<11} {Hid_Indep:<10} "
                  "{Cen_NEtaArr:<11} {Cen_NEtaDet:<}".format(**dict1)]
        lines += ["          PotMin  PotMax VertMin VertMax"]
        lines += ["           {PotMin:>05.1f}  {PotMax:>06.1f}"
                  "   {VertMin:>05.1f}  {VertMax:>06.1f}".format(**dict2)]
        lines += ["           Start   Stop ON(t<0) NEta_OnOff"]
        lines += ["             0.0    0.0 F       0     "
                  "          Pot.           Volumen    Volumen    Volumen"
                  "    Volumen  Factor"]
        lines += ["          CosVar  Rendi  Barra Genera Vertim    t<0"
                  "  Afluen    Inicial      Final     Minimo     Maximo"
                  "  Escala EmbCFUE"]
        lines += ["{CosVar:>16.1f} {Rendi:>6.3f} {Barra:>6} "
                  "{Genera:>6} {Vertim:>6} {pot:>6.1f}  {Afluen:>06.1f} "
                  "{VolIni:>10.7f} {VolFin:>10.7f} {VolMin:>10.7f} "
                  "{VolMax:>10.7f} "
                  "{FEscala: >8.1E} {EmbCFUE:>7}".format(**dict3)]
        # Remove leading zero of exponential numbers
        lines[-1] = lines[-1].replace("E-0", "E-").replace("E+0", "E+")
    return lines


def calculate_cen_data(row: pd.Series, type: str) -> tuple[dict, dict, dict]:
    '''
    Calculate data for each central type
    '''
    # Build dicts
    if type == 'E':
        row, factor_escala = apply_plp_functions(row)
    dict1 = {'num_cen': int(row['NumCen']),
             'nom_cen': row['Nombre'],
             'IPot': 1,
             'MinTec': 'F',
             'Inter': 'F',
             'FCAD': 'F',
             'Cen_MTTdHrz': 'F',
             'Hid_Indep': row['Hid_Indep'],
             'Cen_NEtaArr': 0,
             'Cen_NEtaDet': 0
             }
    dict2 = {'PotMin': row['Pmin'],
             'PotMax': row['Pmax'],
             'VertMin': row['VertMin'],
             'VertMax': row['VertMax']
             }
    dict3 = {'CosVar': row['CosVar'],
             'Rendi': row['Rendi'],
             'Barra': row['Conectada a la Barra'],
             'pot': 0,
             'Afluen': row['Afluen']
             }
    if type == 'E':
        dict3['Genera'] = int(row['Generación'])
        dict3['Vertim'] = int(row['Vertimiento'])
        dict3['VolIni'] = row['VolIni'] / factor_escala
        dict3['VolFin'] = row['VolFin'] / factor_escala
        dict3['VolMin'] = row['VolMin'] / factor_escala
        dict3['VolMax'] = row['VolMax'] / factor_escala
        dict3['FEscala'] = factor_escala
        dict3['EmbCFUE'] = row['EmbCFUE']
    else:
        dict3['SerHid'] = int(row['Generación'])
        dict3['SerVer'] = int(row['Vertimiento'])
    return dict1, dict2, dict3


def lines_central(df: pd.DataFrame, type: str) -> list:
    '''
    Print lines for each central type
    Group S (Series) and R (Riego) types
    '''
    if type != 'S':
        df = df[df['Tipo de Central'] == type]
    else:
        df = df[(df['Tipo de Central'] == 'S') |
                (df['Tipo de Central'] == 'R')]
    df.loc[:, 'Nombre'] = df['Nombre'].apply(lambda x: "'%s'" % x)
    if type == 'S':
        lines = ['# Centrales Serie Hidraulica']
    elif type == 'P':
        lines = ['# Centrales Pasada Puras']
    elif type == 'T':
        lines = ['# Centrales Termicas o Embalses Equivalentes']
    elif type == 'F':
        # lines = ['# Centrales de Falla']
        lines = []
    else:
        logger.error('Tipo %s not valid' % type)
        lines = []
    for _, row in df.iterrows():
        # Calculations
        dict1, dict2, dict3 = calculate_cen_data(row, type)
        # Write lines
        lines += ["                                                      "
                  "IPot MinTec  Inter   FCAD    Cen_MTTdHrz Hid_Indep"
                  "  Cen_NEtaArr Cen_NEtaDet"]
        lines += [" {num_cen: >4d} {nom_cen:<47} {IPot:<4} {MinTec:<7} "
                  "{Inter:<7} {FCAD:<7} {Cen_MTTdHrz:<11} {Hid_Indep:<10} "
                  "{Cen_NEtaArr:<11} {Cen_NEtaDet:<}".format(**dict1)]
        lines += ["          PotMin  PotMax VertMin VertMax"]
        lines += ["           {PotMin:>05.1f}  {PotMax:>06.1f}"
                  "   {VertMin:>05.1f}  {VertMax:>06.1f}".format(**dict2)]
        lines += ["           Start   Stop ON(t<0) NEta_OnOff"]
        lines += ["             0.0    0.0 F       0     "
                  "          Pot."]
        lines += [
            "          CosVar  Rendi  Barra SerHid SerVer    t<0  Afluen"]
        lines += ["{CosVar:>16.1f} {Rendi:>6.3f} {Barra:>6} "
                  "{SerHid:>6} {SerVer:>6} {pot:>6.1f}  "
                  "{Afluen:>06.1f}".format(**dict3)]
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
        add_file_handler(logger, 'cen', path_log)

        # Read centrales data
        logger.info('Reading centrales data')
        df_centrales = read_df_centrales_all(iplp_path)

        # Print plptec
        logger.info('Printing plptec')
        print_plptec(path_inputs, df_centrales)

        # Add failure data
        logger.info('Adding failure data')
        df_centrales = add_failure_generators(iplp_path, df_centrales)

        # Print plpcnfce
        logger.info('Printing plpcnfce')
        print_plpcnfce(path_inputs, df_centrales)

    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')


if __name__ == "__main__":
    main()
