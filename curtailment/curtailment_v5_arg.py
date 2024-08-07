# -*- coding: utf-8 -*-
'''
Curtailment script

Take PLP outputs and redistribute curtailment values
to be used by the Curtailment Model

Inputs (tr is the time resolution, B or H):
- outCurtail_%tr%.csv
- outEnerg_%tr%.csv

Dicts:
- BarsZones.csv
- enable_curtailment.csv

Files from df folder:
- df_centrales.csv
- df_ernc_rf_final.csv

Outputs:
- Block and Hour folders, each with:
    - curtailment.csv
    - curtailment_grouped.csv
    - curtailment_redistrib.csv
    - curtailment_redistrib_grouped.csv
    - outEnerg_B_redistrib.csv
'''

from argparse import ArgumentParser
from logger import create_logger, add_file_handler
import os
import pandas as pd
from pathlib import Path

TOLERANCE_GAP_PERCENTAGE = 0.0001

pd.set_option('display.precision', 2)

# Input Data files
INPUT_FILES = {
    "Block": {
        "cur_file_name": "outCurtail_B.csv",
        "ener_file_name": "outEnerg_B.csv"
    },
    "Hour": {
        "cur_file_name": "outCurtail_H.csv",
        "ener_file_name": "outEnerg_H.csv"
    }
}

# Hydrology to filter
HYD20 = 20

logger = create_logger('curtailment')


def load_data(time_resolution, inputs_path):
    """
    Load the data required for analysis.

    Returns:
    - df_cur: DataFrame containing CUR data filtered by Hyd
    - df_ener: DataFrame containing ENER data filtered by Hyd
    """
    # Define input file paths
    cur_file = Path(
        inputs_path, INPUT_FILES[time_resolution]["cur_file_name"])
    ener_file = Path(
        inputs_path, INPUT_FILES[time_resolution]["ener_file_name"])

    logger.info('--Loading data from:')
    logger.info(f'--CUR: {cur_file}')
    logger.info(f'--ENER: {ener_file}')

    df_cur = pd.read_csv(cur_file, encoding="latin1",
                         skiprows=3, low_memory=False)
    if "Hyd" in df_cur.columns:
        df_cur = df_cur[df_cur["Hyd"] == HYD20]
        df_cur = df_cur.drop(columns=["Hyd"])
    df_cur = df_cur.set_index(["Year", "Month", time_resolution])

    df_ener = pd.read_csv(ener_file, encoding="latin1",
                          skiprows=3, low_memory=False)
    if "Hyd" in df_ener.columns:
        df_ener = df_ener[df_ener["Hyd"] == HYD20]
        df_ener = df_ener.drop(columns=["Hyd"])
    df_ener = df_ener.set_index(["Year", "Month", time_resolution])

    return df_cur, df_ener


def load_dicts(zonas_file, df_centrales_file, tec2enable_file):
    """
    Load the data required for analysis.

    Returns:
    - dict_node2zone: Dictionary mapping Node to Zone
    - dict_gen2node: Dictionary mapping Gen to Node
    """
    # Define dict from Node to Zone in df_zonas
    df_zonas = pd.read_csv(zonas_file, encoding="latin1", low_memory=False)
    dict_node2zone = dict(zip(df_zonas["Node"], df_zonas["Zone"]))

    # Read df_centrales. It has already filtered the generators
    # with no participation in the dispatch
    df_centrales = pd.read_csv(df_centrales_file, encoding="latin1",
                               low_memory=False)

    # Define dict from Gen to Node in df_centrales
    dict_gen2node = dict(zip(df_centrales["Nombre"],
                             df_centrales["Barra"]))
    dict_gen2pmax = dict(zip(df_centrales["Nombre"],
                             df_centrales["Pmax"]))

    # Read tec2enable dictionary from file
    df_tec2enable = pd.read_csv(tec2enable_file, encoding="latin1",
                                low_memory=False)
    dict_tec2enable = dict(zip(df_tec2enable.iloc[:, 0],
                               df_tec2enable.iloc[:, 1]))
    # Add column Enable Curtailment mapping with Fuel column
    df_centrales["Enable Curtailment"] = df_centrales["Fuel"].map(
        dict_tec2enable)
    dict_gen2enable = dict(zip(df_centrales["Nombre"],
                               df_centrales["Enable Curtailment"]))
    return dict_node2zone, dict_gen2node, dict_gen2pmax, dict_gen2enable


def get_df_rating_factors(rating_factor_file, final_year):
    '''
    Get rating factors dataframe, with Pmax per month for each generator
    '''
    # Read rating factors and clean
    df_rating_factor = pd.read_csv(rating_factor_file, encoding="latin1",
                                   low_memory=False)
    # Parse DateFrom as datetime
    df_rating_factor["DateFrom"] = pd.to_datetime(df_rating_factor["DateFrom"])
    # Filter by end year
    df_rating_factor = df_rating_factor[df_rating_factor["Year"] <= final_year]
    # Drop rows with NaN
    df_rating_factor = df_rating_factor.dropna()
    # Drop columns
    cols_to_drop = ["Day", "DaysInMonth", "Year-Month",
                    "Initial_Eta", "DateFrom"]
    df_rating_factor = df_rating_factor.drop(cols_to_drop, axis=1)
    # Rename Name to Gen, Value [Mw] to Pmax
    df_rating_factor = df_rating_factor.rename(
        columns={"Name": "Gen", "Value [MW]": "Pmax"})
    # Set Year, Month, Gen as index, and for duplicates, keep the last row
    df_rating_factor = df_rating_factor.drop_duplicates(
        subset=["Year", "Month", "Gen"], keep="last")
    df_rating_factor = df_rating_factor.set_index(["Year", "Month", "Gen"])
    return df_rating_factor


def load_gen2pmax_per_month(df_ener, dict_gen2pmax, dict_gen2enable,
                            rating_factor_file, output_folder):
    '''
    Get dataframe with Pmax per month for each generator
    '''
    # Get time limits
    # initial_year = df_ener.index.get_level_values("Year").min()
    # initial_month = df_ener.index.get_level_values("Month").min()
    final_year = df_ener.index.get_level_values("Year").max()
    # final_month = df_ener.index.get_level_values("Month").max()

    # Get clean rating factors dataframe
    df_rating_factor = get_df_rating_factors(rating_factor_file, final_year)

    # Build dataframe, using time indexes from df_ener, and columns from
    # dict_gen2pmax, if the generator is enabled for curtailment
    year_month_index = df_ener.index.droplevel(level=2).unique()
    enabled_gens = [
        gen for gen in dict_gen2pmax.keys() if dict_gen2enable[gen] == 1]
    df_pmax_per_month = pd.DataFrame(index=year_month_index,
                                     columns=enabled_gens)
    # Fill with Pmax values
    for gen in enabled_gens:
        first_index = df_pmax_per_month.index[0]
        df_pmax_per_month.loc[first_index, gen] = dict_gen2pmax[gen]
    # Name columns
    df_pmax_per_month.columns.name = 'Gen'
    # Turn df_rating_factor to wide format
    df_rating_factor = df_rating_factor.unstack()
    df_rating_factor.columns = df_rating_factor.columns.droplevel()
    # Update Pmax values with rating factors
    df_pmax_per_month.update(df_rating_factor)
    # Forward fill with previous value for each month
    # Specify as float to avoid future warning
    df_pmax_per_month = df_pmax_per_month.astype(float).ffill()
    # Drop columns if all nan
    df_pmax_per_month = df_pmax_per_month.dropna(axis=1, how='all')
    # Fill NaN with 0
    df_pmax_per_month = df_pmax_per_month.fillna(0)
    # Print to csv
    df_pmax_per_month.to_csv(Path(output_folder, "df_pmax_per_month.csv"),
                             encoding="latin1")
    return df_pmax_per_month


def validate_inputs(df_cur, df_ener, dict_node2zone, dict_gen2node,
                    dict_gen2enable):
    # Validate that generators are aligned
    '''
    for gen, node in dict_gen2node.items():
        #if gen not in df_cur.columns:
        #    logger.info(f"Gen {gen} not found in Curtailment file")
        if gen not in df_ener.columns:
            logger.info(f"Gen {gen} not found in Energy file")
    '''
    logger.info("--Checking if all generators are in all files")
    logger.info("--Generators not found will not be considered for curt.")
    for gen in df_ener.columns:
        if gen in dict_gen2enable.keys():
            if gen not in dict_gen2node.keys():
                logger.info(f"Gen {gen} not found in Gen2Node file")
            if gen not in df_cur.columns:
                logger.info(f"Gen {gen} not found in Curtailment file")
    for gen in df_cur.columns:
        if gen in dict_gen2enable.keys():
            if gen not in dict_gen2node.keys():
                logger.info(f"Gen {gen} not found in Gen2Node file")
            if gen not in df_ener.columns:
                logger.info(f"Gen {gen} not found in Energy file")


def process_inputs(df_cur, df_ener, dict_node2zone, dict_gen2node,
                   time_resolution="Block"):
    '''
    Process inputs to create a single dataframe with all the data
    '''
    new_indexes = ['Year', 'Month', time_resolution, 'Gen', 'Node', 'Zone']
    # Process curtailment data
    df_cur = df_cur.stack().reset_index()
    df_cur.columns = [
        'Year', 'Month', time_resolution, 'Gen', 'Curtailment Original']
    df_cur['Node'] = df_cur['Gen'].map(dict_gen2node).fillna('NoNode')
    df_cur['Zone'] = df_cur['Node'].map(dict_node2zone).fillna('NoZone')
    df_cur.set_index(new_indexes, inplace=True)

    # Process energy data
    df_ener = df_ener.stack().reset_index()
    df_ener.columns = [
        'Year', 'Month', time_resolution, 'Gen', 'Energy Original']
    df_ener['Node'] = df_ener['Gen'].map(dict_gen2node).fillna('NoNode')
    df_ener['Zone'] = df_ener['Node'].map(dict_node2zone).fillna('NoZone')
    df_ener.set_index(new_indexes, inplace=True)

    # Process total generation data
    df_all = pd.merge(df_cur, df_ener, left_on=new_indexes,
                      right_on=new_indexes)
    return df_all


def get_gen_data(dict_gen2node, dict_node2zone, dict_gen2enable):
    # Create dataframe with each generator by zone and its Pmax percentage
    df_gen_data = pd.DataFrame(dict_gen2node.items(), columns=['Gen', 'Node'])
    df_gen_data['Zone'] = df_gen_data['Node'].map(dict_node2zone)
    df_gen_data['Enable Curtailment'] = df_gen_data['Gen'].map(dict_gen2enable)
    return df_gen_data


def preprocess_curtailment(df_all, df_gen_data, df_pmax_per_month):
    '''
    Pasos previos a la redistribución de curtailment:
    1. Copiar el porcentaje de curtailment correspondiente a la zona
    2. Agregar las columnas Pmax y Enable de df_gen_data (con fillna 0)
    3. Para cada Year, Month, time_resolution, Zone, sumar el curtailment de
    las que no participan, y guardar en columna adicional
    '''
    # 1. Copiar el porcentaje de curtailment correspondiente a la zona
    df = df_all.copy().reset_index()
    df['Curtailment'] = df['Curtailment Original']
    df['Energy'] = df['Energy Original']
    df['Energy+Curtailment'] = df['Curtailment'] + df['Energy']

    # 2. Agregar las columnas Pmax y Enable de df_gen_data (con fillna 0)
    # 2.a df_pmax_per_month a formato largo, nombrando columnas Pmax
    df_pmax_per_month = df_pmax_per_month.stack().reset_index()
    df_pmax_per_month.columns = ['Year', 'Month', 'Gen', 'Pmax']
    # 2.b Merge con df
    df = pd.merge(df, df_pmax_per_month, on=['Year', 'Month', 'Gen'],
                  how='left').fillna(0)
    # 2.c Agregar Enable Curtailment
    df['Enable Curtailment'] = df['Gen'].map(
        dict(zip(df_gen_data['Gen'],
                 df_gen_data['Enable Curtailment']))).fillna(0)

    # 3. Determinar el curtailment de las que no participan,
    # y almacenar en columna adicional. Luego dejar en 0
    df['Curtailment Adicional 1'] = \
        df['Curtailment'] * (1 - df['Enable Curtailment'])
    df['Energy'] = df['Energy'] + df['Curtailment Adicional 1']
    df['Curtailment'] = df['Curtailment'] * df['Enable Curtailment']

    # 4. Si hay curtailment en unidades que participan pero con Pmax = 0,
    # guardar como Curtailment Adicional 2, y dejar en 0
    df['Curtailment Adicional 2'] = \
        df['Curtailment'] * (df['Pmax'] == 0)
    df['Energy'] = df['Energy'] + df['Curtailment Adicional 2']
    df['Curtailment'] = df['Curtailment'] * (df['Pmax'] > 0)

    return df


def redistribute_totals(df_all, time_resolution="Block", ITER_MAX=5):
    '''
    Algoritmo de redistribución de curtailment

    1. Copiar dataframe inicial
    2. Energía disponible es igual a Energy+Curtailment si participa
    3. Colocación de energía es igual a Energy si participa
    4. Colocación Total de energia es la suma de Colocación para todas
    las unidades participantes
    5. Pmax si participa es igual a Pmax si participa en la iteración 0
    6. Proceso iterativo:
        a. Calcular factor de prorrata
        b. Calcular Punto de Operación sugerido
        c. Calcular Punto de Operación saturando con la Energía Disponible
        d. Calcular la nueva energía disponible
        e. Calcular Energía Asignada, sumando Puntos Op. hasta el actual
        f. Calcular nueva colocación total
        g. Evaluar condición de término: si Energía Asignada Total ya
        alcanzó la Colocación Total #0
        f. Redefinir potencia máxima si participa en la sgte iteración
        Participa si Energía Disponible > 0
    7. Calcular Punto de Operación final
    8. Calcular curtailment como la diferencia entre Energy+Curtailment y
    el Punto de Operación final
    9. Formatear salidas
    '''
    # 1. Copiar dataframe inicial
    df = df_all.copy()

    # 2. Energía disponible es igual a Energy+Curtailment si participa
    df['Energía Disponible #0'] = \
        df['Energy+Curtailment'] * \
        (df['Energy+Curtailment'] > 0) * (df['Enable Curtailment'])

    # 3. Colocación de energía es igual a Energy si participa
    df['Colocación #0'] = \
        df['Energy'] * \
        (df['Energy+Curtailment'] > 0) * (df['Enable Curtailment'])

    # 4. Colocación Total de energia es la suma de Colocación para todas
    # las unidades participantes, menos el Curtailment Adicional, que viene
    # de las unidades que no participan
    df['Colocación Total #0'] = df.groupby(
        ['Year', 'Month', time_resolution, 'Zone'])[
            'Colocación #0'].transform(lambda x: x.sum()) - \
        df.groupby(
            ['Year', 'Month', time_resolution, 'Zone'])[
            'Curtailment Adicional 1'].transform(lambda x: x.sum()) - \
        df.groupby(
            ['Year', 'Month', time_resolution, 'Zone'])[
            'Curtailment Adicional 2'].transform(lambda x: x.sum())

    # 5. Pmax si participa es igual a Pmax si participa en la iteración 0
    df['Pmax si participa #0'] = \
        df['Pmax'] * \
        (df['Energy+Curtailment'] > 0) * (df['Enable Curtailment'])

    # 6. Proceso iterativo:
    for i in range(ITER_MAX):
        # a. Calcular factor de prorrata
        df['Factor Prorrata #%s' % i] = df.groupby(
            ['Year', 'Month', time_resolution, 'Zone'])[
                'Pmax si participa #%s' % i].transform(
            lambda x: x / x.sum() if x.sum() > 0 else 0)

        # b. Calcular punto de operación sugerido
        df['Punto Operación sugerido #%s' % i] = \
            df['Colocación Total #%s' % i] * df['Factor Prorrata #%s' % i]

        # c. Calcular punto de operación saturando con la Energía Disponible
        df['Punto Operación #%s' % i] = \
            df[['Punto Operación sugerido #%s' % i,
                'Energía Disponible #%s' % i]].min(axis=1)

        # d. Calcular la nueva energía disponible
        df['Energía Disponible #%s' % (i+1)] = \
            df['Energía Disponible #%s' % i] - df['Punto Operación #%s' % i]

        # Calcular Energía Asignada, sumando Puntos Op. hasta el actual
        df['Energía Asignada #<=%s' % i] = \
            df[['Punto Operación #%s' % j for j in range(i+1)]].sum(axis=1)

        # Calcular Energía Asignada Total hasta iteracion actual
        df['Energía Asignada Total #<=%s' % i] = \
            df.groupby(
                ['Year', 'Month', time_resolution, 'Zone'])[
                'Energía Asignada #<=%s' % i].transform(
                    lambda x: x.sum())

        # f. Calcular nueva colocación total
        # números particulares pueden ser negativos, pero la suma no
        df['Colocación #%s' % (i+1)] = \
            (df['Colocación #0'] - df['Energía Asignada #<=%s' % i])

        df['Colocación Total #%s' % (i+1)] = \
            df.groupby(
                ['Year', 'Month', time_resolution, 'Zone'])[
                'Colocación #%s' % (i+1)].transform(
                    lambda x: x.sum())

        # g. Evaluar condición de término: si Energía Asignada Total ya
        # alcanzó la Colocación Total #0
        df['Terminar #%s' % i] = \
            1 * (df['Energía Asignada Total #<=%s' % i] >=
                 df['Colocación Total #0'] * (1 - TOLERANCE_GAP_PERCENTAGE))

        # f. Redefinir potencia máxima si participa en la sgte iteración
        # Participa si Energía Disponible > 0
        df['Pmax si participa #%s' % (i+1)] = \
            df['Pmax'] * \
            (df['Energía Disponible #0'] > 0) * \
            (df['Energía Disponible #%s' % (i+1)] > 0) * \
            (1 - df['Terminar #%s' % i])

    # 7. Calcular Punto de Operación final
    df['Punto Operación Final'] = df[
        ['Punto Operación #%s' % j for j in range(ITER_MAX)]].sum(axis=1)

    # 8. Calcular curtailment como la diferencia entre Energy+Curtailment y
    # el punto de operación final
    df['Redistributed Curtailment'] = \
        (df['Energy+Curtailment'] - df['Punto Operación Final']) *\
        (df['Energía Disponible #0'] > 0)

    # 9. Formatear salidas
    df.set_index(
        ['Year', 'Month', time_resolution, 'Gen', 'Node', 'Zone'],
        inplace=True)
    df['Redistributed Energy'] = \
        df['Energy+Curtailment'] - df['Redistributed Curtailment']
    df['Original Curtailment %'] = \
        df['Curtailment'] / df['Energy+Curtailment']
    df['Redistributed Curtailment %'] = \
        df['Redistributed Curtailment'] / df['Energy+Curtailment']
    # Fill NaN with 0
    df['Original Curtailment %'] = \
        df['Original Curtailment %'].fillna(0)
    df['Redistributed Curtailment %'] = \
        df['Redistributed Curtailment %'].fillna(0)
    return df.round(4)


def group_data_redistrib(df_all_redistrib, time_resolution="Block"):
    # Group values by zone
    df_all_redistrib_grouped = df_all_redistrib.groupby(
        ['Year', 'Month', time_resolution, 'Zone']).sum()
    # Calculate grouped values per zone
    df_all_redistrib_grouped['Redistributed Curtailment %'] = \
        df_all_redistrib_grouped['Redistributed Curtailment'] / \
        df_all_redistrib_grouped['Energy+Curtailment']
    return df_all_redistrib_grouped


def process_redistributed_out(df_all_redistrib, time_resolution="Block",
                              value="Energy"):
    '''
    Turn file to outEner or outCurtail format
    '''
    value_header = f"Redistributed {value}"  # Energy or Curtailment
    df_out_redistrib = df_all_redistrib.copy()
    # Add Hyd column
    df_out_redistrib['Hyd'] = Hyd
    # Keep only Hyd, Year, Month, Block, Gen, Redistributed Value
    df_out_redistrib = df_out_redistrib.reset_index()
    new_indexes = ['Hyd', 'Year', 'Month', time_resolution, 'Gen',
                   value_header]
    df_out_redistrib = df_out_redistrib[new_indexes]
    # Unstack the data
    df_out_redistrib = df_out_redistrib.set_index(
        ['Hyd', 'Year', 'Month', time_resolution, 'Gen'])
    df_out_redistrib = df_out_redistrib.unstack()
    df_out_redistrib.columns = df_out_redistrib.columns.droplevel()
    return df_out_redistrib


def add_blank_lines(out_file, lines):
    with open(out_file, 'r') as original:
        data = original.read()
    with open(out_file, 'w') as modified:
        for i in range(lines):
            modified.write('\n')
        modified.write(data)


def print_outputs_to_csv(output_folder, df_all,
                         df_all_redistrib, df_all_redistrib_grouped,
                         df_out_ener_redistrib, df_out_curtail_redistrib,
                         time_resolution="Block"):

    # Create output folder per time resolution
    output_folder_aux = Path(output_folder, time_resolution)
    output_folder_aux.mkdir(exist_ok=True)

    # Output suffix
    if time_resolution == "Block":
        suffix = "B"
    elif time_resolution == "Hour":
        suffix = "H"
    else:
        suffix = ""

    # Create Monthly versions for outEnerg and outCurtail
    df_out_ener_redistrib_monthly = df_out_ener_redistrib.copy()
    df_out_curtail_redistrib_monthly = df_out_curtail_redistrib.copy()
    df_out_ener_redistrib_monthly = \
        df_out_ener_redistrib_monthly.groupby(
            ['Hyd', 'Year', 'Month']).sum()
    df_out_curtail_redistrib_monthly = \
        df_out_curtail_redistrib_monthly.groupby(
            ['Hyd', 'Year', 'Month']).sum()

    # Output Data files
    cur_out_file = Path(
        output_folder_aux, 'curtailment_%s.csv' % suffix)
    cur_redistrib_out_file = Path(
        output_folder_aux, 'curtailment_redistrib_%s.csv' % suffix)
    cur_redistrib_grouped_out_file = Path(
        output_folder_aux, 'curtailment_redistrib_grouped_%s.csv' % suffix)
    out_ener_redistrib_out_file = Path(
        output_folder_aux, 'outEnerg_redistrib_%s.csv' % suffix)
    out_curtail_redistrib_out_file = Path(
        output_folder_aux, 'outCurtail_redistrib_%s.csv' % suffix)
    out_ener_redistrib_monthly_out_file = Path(
        output_folder_aux, 'outEnerg_redistrib_monthly_%s.csv' % suffix)
    out_curtail_redistrib_monthly_out_file = Path(
        output_folder_aux, 'outCurtail_redistrib_monthly_%s.csv' % suffix)

    df_all.to_csv(cur_out_file, encoding="latin1")
    df_all_redistrib.to_csv(
        cur_redistrib_out_file, encoding="latin1")
    df_all_redistrib_grouped.to_csv(
        cur_redistrib_grouped_out_file, encoding="latin1")
    df_out_ener_redistrib.to_csv(
        out_ener_redistrib_out_file, encoding="latin1")
    df_out_curtail_redistrib.to_csv(
        out_curtail_redistrib_out_file, encoding="latin1")
    df_out_ener_redistrib_monthly.to_csv(
        out_ener_redistrib_monthly_out_file, encoding="latin1")
    df_out_curtail_redistrib_monthly.to_csv(
        out_curtail_redistrib_monthly_out_file, encoding="latin1")

    # Add 2 blank lines at the beginning of all energy files
    # to match format
    add_blank_lines(out_ener_redistrib_out_file, 3)
    add_blank_lines(out_ener_redistrib_monthly_out_file, 3)
    add_blank_lines(out_curtail_redistrib_out_file, 3)
    add_blank_lines(out_curtail_redistrib_monthly_out_file, 3)


def is_valid_file(parser: ArgumentParser, arg: str) -> Path:
    if not os.path.exists(arg):
        parser.error("The file or path %s does not exist!" % arg)
    else:
        return Path(arg)


def define_arg_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Get Curtailment input filepaths")
    parser.add_argument('-b', dest='zonas_file', required=True,
                        help='BarsZones file path',
                        metavar="BARS_ZONES",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument('-e', dest='tec2enable_file', required=True,
                        help='BarsZones file path',
                        metavar="BARS_ZONES",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument('-c', dest='df_centrales_file', required=True,
                        help='df_centrales file path',
                        metavar="DF_CENTRALES",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument('-r', dest='rating_factor_file', required=True,
                        help='df_ernc_rf_final file path',
                        metavar="RATING_FACTOR",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument('-i', dest='inputs_path', required=True,
                        help='Path to input files',
                        metavar="INPUTS_PATH",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument('-o', dest='output_folder', required=True,
                        help='Path to output files',
                        metavar="OUTPUTS_PATH",
                        type=str)
    parser.add_argument('-t', dest='time_resolution', required=True,
                        help='Time resolution, either Block or Hour',
                        metavar="TIME_RESOLUTION",
                        type=str,
                        choices=["Block", "Hour"])
    return parser


def main():
    logger.info('--Starting curtailment script')

    try:
        parser = define_arg_parser()
        args = parser.parse_args()
        # Inputs from dictionaries
        zonas_file = args.zonas_file
        tec2enable_file = args.tec2enable_file
        # Inputs from IPLP df
        df_centrales_file = args.df_centrales_file
        rating_factor_file = args.rating_factor_file
        # Inputs from IPLP outputs
        inputs_path = args.inputs_path
        # Outputs folder
        output_folder = args.output_folder
        # Time resolution (Block or Hour)
        time_resolution = args.time_resolution

        # Create output folder if it does not exist
        Path(output_folder).mkdir(exist_ok=True)

        # Add destination folder to logger
        add_file_handler(logger, 'log_curtailment', Path(output_folder))

        logger.info('--Processing curtailment with time resolution in: ' +
                    time_resolution + ' resolution')
        # Load Data
        logger.info('--Loading data')
        df_cur, df_ener = load_data(time_resolution, inputs_path)
        dict_node2zone, dict_gen2node, dict_gen2pmax, dict_gen2enable = \
            load_dicts(zonas_file, df_centrales_file, tec2enable_file)
        df_pmax_per_month = load_gen2pmax_per_month(
            df_ener, dict_gen2pmax, dict_gen2enable, rating_factor_file,
            output_folder)

        # Validate inputs
        logger.info('--Validating inputs')
        validate_inputs(df_cur, df_ener, dict_node2zone, dict_gen2node,
                        dict_gen2enable)

        # Process data
        logger.info('--Processing inputs')
        df_all = process_inputs(df_cur, df_ener,
                                dict_node2zone, dict_gen2node,
                                time_resolution)
        # Get generator data
        df_gen_data = get_gen_data(
            dict_gen2node, dict_node2zone, dict_gen2enable)
        # Preprocess curtailment data
        df_all = preprocess_curtailment(
            df_all, df_gen_data, df_pmax_per_month)

        # Redistribute totals
        logger.info('--Redistributing totals')
        df_all_redistrib = redistribute_totals(df_all, time_resolution)
        df_all_redistrib_grouped = group_data_redistrib(
            df_all_redistrib, time_resolution)
        df_out_ener_redistrib = process_redistributed_out(
            df_all_redistrib, time_resolution, "Energy")
        df_out_curtail_redistrib = process_redistributed_out(
            df_all_redistrib, time_resolution, "Curtailment")

        # Print results
        logger.info('--Printing results to csv files')
        print_outputs_to_csv(output_folder, df_all,
                             df_all_redistrib, df_all_redistrib_grouped,
                             df_out_ener_redistrib, df_out_curtail_redistrib,
                             time_resolution)
    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error('Process finished with errors. Check above for details')
    else:
        logger.info('Process finished successfully')

    logger.info('--Finished curtailment script')


if __name__ == "__main__":
    main()
