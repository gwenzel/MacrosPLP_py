# -*- coding: utf-8 -*-
'''
Curtailment script

Take PLP outputs and redistribute curtailment values
to be used by the Curtailment Model

Inputs (tr is the time resolution, 12B or 24H):
- outCurtail_%tr%.csv
- outEnerg_%tr%.csv

Dicts:
- BarsZones.csv
- ID_Gen_PLP-Plexos.csv

Outputs:
- Block and Hour folders, each with:
    - curtailment.csv
    - curtailment_grouped.csv
    - curtailment_redistrib.csv
    - curtailment_redistrib_grouped.csv
    - outEnerg_12B_redistrib.csv
'''

import os
import pandas as pd
from pathlib import Path

pd.set_option('display.precision', 2)

cur_dir = Path(r"C:\Users\BH5873\ENGIE\Equipo Estudios - Biblioteca Equipo Estudios\08. Modelos\202405 - Nuevo Curtailment\BE Mar24 PLP")
# cur_dir = Path(os.getcwd())
inputs_path = Path(cur_dir, "Output_Filter_Plexos")
# Input Data files
INPUT_FILES = {
    "Block": {
        "cur_file_name": "outCurtail_12B.csv",
        "ener_file_name": "outEnerg_12B.csv"
    },
    "Hour": {
        "cur_file_name": "outCurtail_24H.csv",
        "ener_file_name": "outEnerg_24H.csv"
    }
}
# Inputs from IPLP df
rating_factor_file = Path(cur_dir, "df_ernc_rf_final.csv")
df_centrales_file = Path(cur_dir, "df_centrales.csv")
# Input Dict files
zonas_file = Path(cur_dir, "BarsZones.csv")
tec2enable_file = Path(cur_dir, "enable_curtailment.csv")
# Create output folder
output_folder = Path(cur_dir, "Output_Curtailment")
output_folder.mkdir(exist_ok=True)

# Hydrology to filter
Hyd = 20


def load_data(time_resolution):
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

    print('--Loading data from:')
    print(f'--CUR: {cur_file}')
    print(f'--ENER: {ener_file}')

    df_cur = pd.read_csv(cur_file, encoding="latin1",
                         skiprows=3, low_memory=False)
    if "Hyd" in df_cur.columns:
        df_cur = df_cur[df_cur["Hyd"] == Hyd]
        df_cur = df_cur.drop(columns=["Hyd"])
    df_cur = df_cur.set_index(["Year", "Month", time_resolution])

    df_ener = pd.read_csv(ener_file, encoding="latin1",
                          skiprows=3, low_memory=False)
    if "Hyd" in df_ener.columns:
        df_ener = df_ener[df_ener["Hyd"] == Hyd]
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


def get_df_rating_factors(final_year):
    # Read rating factors and clean
    df_rating_factor = pd.read_csv(rating_factor_file, encoding="latin1",
                                   low_memory=False)
    # Parse DateFrom as datetime
    df_rating_factor["DateFrom"] = pd.to_datetime(df_rating_factor["DateFrom"])
    # Filter by end year
    df_rating_factor = df_rating_factor[df_rating_factor["Year"] <= final_year]
    # Drop Day, DaysInMonth, Year-Month
    df_rating_factor = df_rating_factor.drop(
        ["Day", "DaysInMonth", "Year-Month"], axis=1)
    initial_datefrom = df_rating_factor["DateFrom"].min()

    # For each row, replace DateFrom, with ini DateFrom + Initial_Eta - 1
    # Each Etapa represents a month
    df_rating_factor["DateFrom"] = df_rating_factor.apply(
        lambda x: initial_datefrom + pd.DateOffset(
            months=x["Initial_Eta"] - 1), axis=1)
    # Replace Year and Month with the ones from DateFrom
    df_rating_factor["Year"] = df_rating_factor["DateFrom"].dt.year
    df_rating_factor["Month"] = df_rating_factor["DateFrom"].dt.month
    # Drop Initial_Eta
    df_rating_factor = df_rating_factor.drop(["Initial_Eta", "DateFrom"], axis=1)
    # Rename Name to Gen, Value [Mw] to Pmax
    df_rating_factor = df_rating_factor.rename(
        columns={"Name": "Gen", "Value [MW]": "Pmax"})
    # Set Year, Month, Gen as index, and for duplicates, keep the last row
    df_rating_factor = df_rating_factor.drop_duplicates(
        subset=["Year", "Month", "Gen"], keep="last")
    df_rating_factor = df_rating_factor.set_index(["Year", "Month", "Gen"])
    return df_rating_factor


def load_gen2pmax_per_month(df_ener, dict_gen2pmax, time_resolution="Block"):
    # Get time limits
    # initial_year = df_ener.index.get_level_values("Year").min()
    # initial_month = df_ener.index.get_level_values("Month").min()
    final_year = df_ener.index.get_level_values("Year").max()
    # final_month = df_ener.index.get_level_values("Month").max()

    # Get clean rating factors dataframe
    df_rating_factor = get_df_rating_factors(final_year)

    # Build dataframe, using time indexes from df_ener, and columns from
    # dict_gen2pmax
    df_pmax_per_month = pd.DataFrame(index=df_ener.index,
                                     columns=dict_gen2pmax.keys())
    # Fill with Pmax values
    for gen, pmax in dict_gen2pmax.items():
        df_pmax_per_month[gen] = pmax
    # Pass to long format
    df_pmax_per_month = df_pmax_per_month.stack().reset_index()
    df_pmax_per_month.columns = ["Year", "Month", time_resolution,
                                 "Gen", "Pmax"]
    import pdb; pdb.set_trace()
    # Overwrite Pmax with rating factors
    df_pmax_per_month = pd.merge(df_pmax_per_month, df_rating_factor,
                                 left_on=["Year", "Month", "Gen"],
                                 right_index=True, how="left")
    import pdb; pdb.set_trace()
    # Go back to wide format
    df_pmax_per_month = df_pmax_per_month.set_index(
        ["Year", "Month", time_resolution, "Gen"])
    df_pmax_per_month = df_pmax_per_month.unstack()
    df_pmax_per_month.columns = df_pmax_per_month.columns.droplevel()
    import pdb; pdb.set_trace()
    # Detect when value changes, and fill with previous value

    df_pmax_per_month = df_pmax_per_month.fillna(method="ffill")

    import pdb; pdb.set_trace()

    return df_pmax_per_month


def validate_inputs(df_cur, df_ener, dict_node2zone, dict_gen2node,
                    dict_gen2enable):
    # Validate that generators are aligned
    '''
    for gen, node in dict_gen2node.items():
        #if gen not in df_cur.columns:
        #    print(f"Gen {gen} not found in Curtailment file")
        if gen not in df_ener.columns:
            print(f"Gen {gen} not found in Energy file")
    '''
    print("Checking if all generators are in all files")
    print("Generators not found will not be considered for curtailment")
    for gen in df_ener.columns:
        if gen in dict_gen2enable.keys():
            if gen not in dict_gen2node.keys():
                print(f"Gen {gen} not found in Gen2Node file")
            if gen not in df_cur.columns:
                print(f"Gen {gen} not found in Curtailment file")
    for gen in df_cur.columns:
        if gen in dict_gen2enable.keys():
            if gen not in dict_gen2node.keys():
                print(f"Gen {gen} not found in Gen2Node file")
            if gen not in df_ener.columns:
                print(f"Gen {gen} not found in Energy file")


def process_inputs(df_cur, df_ener, dict_node2zone, dict_gen2node,
                   time_resolution="Block"):
    new_indexes = ['Year', 'Month', time_resolution, 'Gen', 'Node', 'Zone']
    # Process curtailment data
    df_cur = df_cur.stack().reset_index()
    df_cur.columns = ['Year', 'Month', time_resolution, 'Gen', 'Curtailment']
    df_cur['Node'] = df_cur['Gen'].map(dict_gen2node)
    df_cur['Zone'] = df_cur['Node'].map(dict_node2zone)
    df_cur.set_index(new_indexes, inplace=True)

    # Process energy data
    df_ener = df_ener.stack().reset_index()
    df_ener.columns = ['Year', 'Month', time_resolution, 'Gen', 'Energy']
    df_ener['Node'] = df_ener['Gen'].map(dict_gen2node)
    df_ener['Zone'] = df_ener['Node'].map(dict_node2zone)
    df_ener.set_index(new_indexes, inplace=True)

    # Process total generation data
    df_all = pd.merge(df_cur, df_ener, left_on=new_indexes,
                      right_on=new_indexes)
    df_all['Energy+Curtailment'] = df_all['Curtailment'] + df_all['Energy']
    return df_all


def get_pmax(dict_gen2node, dict_node2zone, dict_gen2pmax,
             dict_gen2enable):
    # Create dataframe with each generador by zone and its Pmax percentage
    df_gen_data = pd.DataFrame(dict_gen2node.items(), columns=['Gen', 'Node'])
    df_gen_data['Zone'] = df_gen_data['Node'].map(dict_node2zone)
    df_gen_data['Pmax'] = df_gen_data['Gen'].map(dict_gen2pmax)
    df_gen_data['Enable Curtailment'] = df_gen_data['Gen'].map(dict_gen2enable)
    # Add Pmax % as a the cuotient of Pmax and the sum of all Pmax per zone,
    # if generator is enabled
    df_gen_data['Pmax'] = df_gen_data['Pmax'].fillna(0)
    df_gen_data['Pmax'] = df_gen_data['Pmax'] * df_gen_data[
        'Enable Curtailment']
    # Fix Pmax value if Energy+Curtailment is > 0 and Enable Curtailment is 1
    # TODO
    return df_gen_data


def redistribute_totals(df_all, df_gen_data,
                        time_resolution="Block", ITER_MAX=5):
    '''
    Algoritmo de redistribución de curtailment

    1. Copiar el porcentaje de curtailment correspondiente a la zona
    2. Agregar las columnas Pmax y Enable de df_gen_data (con fillna 0)
    3. Llenar los valores NaN con 0
    4. Energía disponible es igual a Energy+Curtailment si participa
    5. Colocación de energía es igual a Energy si participa
    6. Colocación Total de energia es la suma de Colocación para todas
    las unidades participantes
    7. Pmax si participa es igual a Pmax si participa en la iteración 0
    8. Proceso iterativo:
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
    9. Calcular Punto de Operación final
    10. Calcular curtailment como la diferencia entre Energy+Curtailment y
    el Punto de Operación final
    11. Formatear salidas
    '''
    # 1. Copiar el porcentaje de curtailment correspondiente a la zona
    df = df_all.copy().reset_index()

    # 2. Agregar las columnas Pmax y Enable de df_gen_data (con fillna 0)
    df['Pmax'] = df['Gen'].map(
        dict(zip(df_gen_data['Gen'], df_gen_data['Pmax'])))
    df['Enable Curtailment'] = df['Gen'].map(
        dict(zip(df_gen_data['Gen'], df_gen_data['Enable Curtailment'])))
    df['Enable Curtailment'] = df[
        'Enable Curtailment'].fillna(0)

    # 3. Llenar los valores NaN con 0
    df['Pmax'] = df['Pmax'].fillna(0)

    # 4. Energía disponible es igual a Energy+Curtailment si participa
    df['Energía Disponible #0'] = \
        df['Energy+Curtailment'] * \
        (df['Energy+Curtailment'] > 0) * (df['Enable Curtailment'])

    # 5. Colocación de energía es igual a Energy si participa
    df['Colocación #0'] = \
        df['Energy'] * \
        (df['Energy+Curtailment'] > 0) * (df['Enable Curtailment'])

    # 6. Colocación Total de energia es la suma de Colocación para todas
    # las unidades participantes
    df['Colocación Total #0'] = df.groupby(
        ['Year', 'Month', time_resolution, 'Zone'])[
            'Colocación #0'].transform(lambda x: x.sum())

    df['Pmax si participa #0'] = \
        df['Pmax'] * \
        (df['Energy+Curtailment'] > 0) * (df['Enable Curtailment'])

    # Proceso iterativo:

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

        '''
        df['Energía Disponible Total #%s' % i] = \
            df.groupby(
                ['Year', 'Month', time_resolution, 'Zone'])[
                'Energía Disponible #%s' % (i+1)].transform(
                    lambda x: x.sum()) * \
            (df['Enable Curtailment'])
        '''
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

        # Asegurar que Colocación Total no sea negativa
        df['Colocación Total #%s' % (i+1)] = \
            df['Colocación Total #%s' % (i+1)]

        # g. Evaluar condición de término: si Energía Asignada Total ya
        # alcanzó la Colocación Total #0
        df['Terminar #%s' % i] = \
            1 * (df['Energía Asignada Total #<=%s' % i] >=
                 df['Colocación Total #0'])

        # f. Redefinir potencia máxima si participa en la sgte iteración
        # Participa si Energía Disponible > 0
        df['Pmax si participa #%s' % (i+1)] = \
            df['Pmax'] * \
            (df['Energía Disponible #0'] > 0) * \
            (df['Energía Disponible #%s' % (i+1)] > 0) * \
            (1 - df['Terminar #%s' % i])

    # Calcular Punto de Operación final
    df['Punto Operación Final'] = df[
        ['Punto Operación #%s' % j for j in range(ITER_MAX)]].sum(axis=1)

    # Calcular curtailment como la diferencia entre Energy+Curtailment y
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
    return df


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
        suffix = "12B"
    elif time_resolution == "Hour":
        suffix = "24H"
    else:
        suffix = ""

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

    df_all.to_csv(cur_out_file)
    df_all_redistrib.to_csv(cur_redistrib_out_file)
    df_all_redistrib_grouped.to_csv(cur_redistrib_grouped_out_file)
    df_out_ener_redistrib.to_csv(out_ener_redistrib_out_file)
    df_out_curtail_redistrib.to_csv(out_curtail_redistrib_out_file)

    # Add 2 blank lines at the beginning of outEnerg_B_redistrib.csv
    # to match format
    add_blank_lines(out_ener_redistrib_out_file, 3)


def main():
    print('--Starting curtailment script')

    for time_resolution in ["Block", "Hour"]:
        print('--Processing curtailment with time resolution in: ' +
              time_resolution + ' resolution')
        # Load Data
        print('--Loading data')
        df_cur, df_ener = load_data(time_resolution)
        dict_node2zone, dict_gen2node, dict_gen2pmax, dict_gen2enable = \
            load_dicts(zonas_file, df_centrales_file, tec2enable_file)
        df_pmax_per_month = load_gen2pmax_per_month(df_ener, dict_gen2pmax)

        # Validate inputs
        print('--Validating inputs')
        validate_inputs(df_cur, df_ener, dict_node2zone, dict_gen2node,
                        dict_gen2enable)

        # Process data
        print('--Processing data')
        df_all = process_inputs(df_cur, df_ener,
                                dict_node2zone, dict_gen2node,
                                time_resolution)

        # Get generator data - pmax percentage for curtailment
        df_gen_data = get_pmax(
            dict_gen2node, dict_node2zone, dict_gen2pmax, dict_gen2enable)

        # Redistribute totals
        print('--Redistributing totals')
        df_all_redistrib = redistribute_totals(
            df_all, df_gen_data, time_resolution)
        df_all_redistrib_grouped = group_data_redistrib(
            df_all_redistrib, time_resolution)
        df_out_ener_redistrib = process_redistributed_out(
            df_all_redistrib, time_resolution, "Energy")
        df_out_curtail_redistrib = process_redistributed_out(
            df_all_redistrib, time_resolution, "Curtailment")

        # Print results
        print('--Printing results to csv files')
        print_outputs_to_csv(output_folder, df_all,
                             df_all_redistrib, df_all_redistrib_grouped,
                             df_out_ener_redistrib, df_out_curtail_redistrib,
                             time_resolution)

    print('--Finished curtailment script')


if __name__ == "__main__":
    main()
