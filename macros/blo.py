'''PLPBLO

Generate PLPBLO.dat file from IPLP input file, as well as
PLPETA.dat and Etapa2Dates.csv files.

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


logger = create_logger('plpblo')

formatter_plpblo = {
    'Bloque': "   {:03d}".format,
    'Etapa': "   {:03d}".format,
    'NHoras': "     {:03d}".format,
    'Ano': "   {:03d}".format,
    'Mes': "   {:03d}".format,
    'TipoBloque': "   '{:s}'".format,
}


formatter_plpetapas = {
    'Ano': "  {:03d}".format,
    'Mes': " {:03d}".format,
    'Etapa': "   {:03d}".format,
    'FDesh': "    {:s}".format,
    'NHoras': "     {:03d}".format,
    'FactTasa': "  {:.6f}".format,
    'TipoEtapa': "   '{:s}'".format
}


def get_df_bloques(blo_eta: pd.DataFrame) -> pd.DataFrame:
    '''
    Transform blo_eta to plpblo format
    '''
    df = blo_eta.copy()
    df['Date'] = pd.to_datetime(
        dict(year=df['Year'], month=df['Month'], day=1))
    df['DaysInMonth'] = df['Date'].dt.days_in_month
    df['NHoras'] = df['Block_Len'] * df['DaysInMonth']
    df['TipoBloque'] = df['Block'].apply(lambda x: "Bloque %02d" % x)
    df = df.rename(columns={'Etapa': 'Bloque'})
    # Add Etapa, as the index of each Year-Month pair
    df_year_month_to_etapa = df.groupby(['Year', 'Month'])\
                               .first().reset_index()
    df_year_month_to_etapa['Etapa'] = df_year_month_to_etapa.index + 1
    df_year_month_to_etapa = df_year_month_to_etapa[['Year', 'Month', 'Etapa']]
    df = df.merge(df_year_month_to_etapa, on=['Year', 'Month'], how='left')
    # Translate to hydromonth and hydroyear
    df = translate_to_hydromonthyear(df)
    # Rename columns
    df = df.rename(columns={'Year': 'Ano',
                            'Month': 'Mes'})
    return df[['Bloque', 'Etapa', 'NHoras',
               'Ano', 'Mes', 'TipoBloque']]


def get_df_etapas(blo_eta: pd.DataFrame) -> pd.DataFrame:
    '''
    Transform blo_eta to plpeta format
    '''
    df = blo_eta.copy()
    tipo_etapa = int(24 / df.loc[0, 'Block_Len'])
    # Groupby Year Month, redefine Etapa,
    # then keep Tasa, and add Hours in Month
    df = df.groupby(['Year', 'Month']).agg(
        {'Tasa': 'first'}).reset_index()
    df['Etapa'] = df.index + 1
    df['Date'] = pd.to_datetime(
        dict(year=df['Year'], month=df['Month'], day=1))
    df['DaysInMonth'] = df['Date'].dt.days_in_month
    df['NHoras'] = 24 * df['DaysInMonth']
    df['FDesh'] = 'F'
    df['TipoEtapa'] = "%02d Bloques" % tipo_etapa
    # Translate to hydromonth and hydroyear
    df = translate_to_hydromonthyear(df)
    # Rename columns
    df = df.rename(columns={'Year': 'Ano',
                            'Month': 'Mes',
                            'Tasa': 'FactTasa'})
    return df[['Ano', 'Mes', 'Etapa', 'FDesh',
               'NHoras', 'FactTasa', 'TipoEtapa']]


def get_df_etapa2dates(blo_eta: pd.DataFrame) -> pd.DataFrame:
    '''
    Transform blo_eta to Etapa2Dates.csv format
    '''
    df = blo_eta.copy()
    df = df.groupby(['Year', 'Month']).agg(
        {'Block': 'first'}).reset_index()
    df['Etapa'] = df.index + 1
    df['PERIOD'] = 1
    df['DR'] = 1
    df = df.rename(columns={'Etapa': 'Etapa',
                            'Year': 'YEAR',
                            'Month': 'MONTH',
                            'Block': 'DAY'})
    return df[['Etapa', 'YEAR', 'MONTH', 'DAY', 'PERIOD', 'DR']]


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


def print_plpeta(path_inputs: Path, df_etapas: pd.DataFrame):
    '''
    Print plpeta.dat file
    '''
    path_plpeta = path_inputs / 'plpeta.dat'
    lines = ['# Archivo con la duracion de las etapas']
    lines += ['# Etapas']
    lines += ["     %s   'H'" % len(df_etapas)]
    lines += ['# Ano  Mes  Etapa FDesh   NHoras    FactTasa    TipoEtapa']
    lines += [df_etapas.to_string(
        index=False, header=False, formatters=formatter_plpetapas)]
    write_lines_from_scratch(lines, path_plpeta)


def print_etapa2dates(path_inputs: Path, df_etapa2dates: pd.DataFrame):
    '''
    Print Etapa2Dates.csv file
    '''
    path_etapa2dates = path_inputs / 'Etapa2Dates.csv'
    df = df_etapa2dates.copy()
    df.to_csv(path_etapa2dates, index=False)


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
        add_file_handler(logger, 'plpblo', path_log)

        # Get Hour-Blocks-Etapas definition
        logger.info('Processing block to etapas files')
        blo_eta, _, _ = process_etapas_blocks(path_dat, droptasa=False)

        # Print blo_eta to file plpblo.dat
        logger.info('Printing blo_eta to file')
        df_bloques = get_df_bloques(blo_eta)
        print_plpblo(path_inputs, df_bloques)

        # Print plpeta.dat
        logger.info('Printing plpeta.dat')
        df_etapas = get_df_etapas(blo_eta)
        print_plpeta(path_inputs, df_etapas)

        # Pring Etapa2Dates.csv
        logger.info('Printing Etapa2Dates.csv')
        df_etapa2dates = get_df_etapa2dates(blo_eta)
        print_etapa2dates(path_inputs, df_etapa2dates)

        logger.info('Process finished successfully')
    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')


if __name__ == "__main__":
    main()
