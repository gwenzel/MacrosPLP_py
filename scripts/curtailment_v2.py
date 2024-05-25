import pandas as pd
from pathlib import Path

inputs_path = r"C:\Users\BH5873\OneDrive - ENGIE\Bureau\BE Mar24 PLP\Output_test"
# Input Data files
cmg_file = Path(inputs_path, "outBarCMg_12B.csv")
cur_file = Path(inputs_path, "outCurtail_12B.csv")
ener_file = Path(inputs_path, "outEnerg_12B.csv")
# Input Dict files
zonas_file = Path(inputs_path, "BarsZones.csv")
gen2zone_file = Path(inputs_path, "ID_Gen_PLP-Plexos.csv")
# Create output folder
output_folder = Path(inputs_path, "Curtailment_Outputs")
output_folder.mkdir(exist_ok=True)
# Output Data files
cur_out_file = Path(
    output_folder, 'curtailment.csv')
cur_grouped_out_file = Path(
    output_folder, 'curtailment_grouped.csv')
cur_redistrib_out_file = Path(
    output_folder, 'curtailment_redistrib.csv')
cur_redistrib_grouped_out_file = Path(
    output_folder, 'curtailment_redistrib_grouped.csv')
out_ener_redistrib_out_file = Path(
    output_folder, 'outEnerg_12B_redistrib.csv')

# Hydrology to filter
Hyd = 20


def load_data(cmg_file, cur_file, ener_file):
    """
    Load the data required for analysis.

    Returns:
    - df_cmg: DataFrame containing CMG data filtered by Hyd
    - df_cur: DataFrame containing CUR data filtered by Hyd
    - df_ener: DataFrame containing ENER data filtered by Hyd
    """

    df_cmg = pd.read_csv(cmg_file, encoding="latin1",
                         skiprows=1, low_memory=False)
    if "Hyd" in df_cmg.columns:
        df_cmg = df_cmg[df_cmg["Hyd"] == Hyd]
        df_cmg = df_cmg.drop(columns=["Hyd"])
    df_cmg = df_cmg.set_index(["Year", "Month", "Block"])

    df_cur = pd.read_csv(cur_file, encoding="latin1",
                         skiprows=3, low_memory=False)
    if "Hyd" in df_cur.columns:
        df_cur = df_cur[df_cur["Hyd"] == Hyd]
        df_cur = df_cur.drop(columns=["Hyd"])
    df_cur = df_cur.set_index(["Year", "Month", "Block"])

    df_ener = pd.read_csv(ener_file, encoding="latin1",
                          skiprows=3, low_memory=False)
    if "Hyd" in df_ener.columns:
        df_ener = df_ener[df_ener["Hyd"] == Hyd]
        df_ener = df_ener.drop(columns=["Hyd"])
    df_ener = df_ener.set_index(["Year", "Month", "Block"])

    return df_cmg, df_cur, df_ener


def load_dicts(zonas_file, gen2zone_file):
    """
    Load the data required for analysis.

    Returns:
    - dict_node2zone: Dictionary mapping Node to Zone
    - dict_gen2node: Dictionary mapping Gen to Node
    """
    # Define dict from Node to Zone in df_zonas
    df_zonas = pd.read_csv(zonas_file, encoding="latin1", low_memory=False)
    dict_node2zone = dict(zip(df_zonas["Node"], df_zonas["Zone"]))

    # Define dict from Gen to Node in df_gen2zone
    df_gen2zone = pd.read_csv(gen2zone_file, encoding="latin1",
                              low_memory=False)
    dict_gen2node = dict(zip(df_gen2zone["Gen_Name"], df_gen2zone["Bar"]))

    return dict_node2zone, dict_gen2node


def validate_inputs(df_cmg, df_cur, df_ener, dict_node2zone, dict_gen2node):
    # Validate that generators are aligned
    '''
    for gen, node in dict_gen2node.items():
        #if gen not in df_cur.columns:
        #    print(f"Gen {gen} not found in Curtailment file")
        if gen not in df_ener.columns:
            print(f"Gen {gen} not found in Energy file")
    '''
    for gen in df_ener.columns:
        if gen not in dict_gen2node.keys():
            print(f"Gen {gen} not found in Gen2Node file")
        if gen not in df_cur.columns:
            print(f"Gen {gen} not found in Curtailment file")
    for gen in df_cur.columns:
        if gen not in dict_gen2node.keys():
            print(f"Gen {gen} not found in Gen2Node file")
        if gen not in df_ener.columns:
            print(f"Gen {gen} not found in Energy file")

    # Validate that nodes are aligned
    '''
    for node, zone in dict_node2zone.items():
        if node not in df_cmg.columns:
            print(f"Node {node} not found in CMg file")
    for node in dict_gen2node.values():
        if node not in dict_node2zone.keys():
            print(f"Node {node} not found in Node2Zone file")
    for node in df_cmg.columns:
        if node not in dict_node2zone.keys():
            print(f"Node {node} not found in Node2Zone file")
    '''


def process_inputs(df_cmg, df_cur, df_ener, dict_node2zone, dict_gen2node):
    new_indexes = ['Year', 'Month', 'Block', 'Gen', 'Node', 'Zone']
    # Process curtailment data
    df_cur = df_cur.stack().reset_index()
    df_cur.columns = ['Year', 'Month', 'Block', 'Gen', 'Curtailment']
    df_cur['Node'] = df_cur['Gen'].map(dict_gen2node)
    df_cur['Zone'] = df_cur['Node'].map(dict_node2zone)
    df_cur.set_index(new_indexes, inplace=True)

    # Process energy data
    df_ener = df_ener.stack().reset_index()
    df_ener.columns = ['Year', 'Month', 'Block', 'Gen', 'Energy']
    df_ener['Node'] = df_ener['Gen'].map(dict_gen2node)
    df_ener['Zone'] = df_ener['Node'].map(dict_node2zone)
    df_ener.set_index(new_indexes, inplace=True)

    # Process total generation data
    df_all = pd.merge(df_cur, df_ener, left_on=new_indexes,
                      right_on=new_indexes)
    df_all['Total Energy'] = df_all['Curtailment'] + df_all['Energy']
    return df_all


def group_data(df_all):
    # Group values by zone
    df_all_grouped = df_all.groupby(['Year', 'Month', 'Block', 'Zone']).sum()
    # Calculate grouped values per zone
    df_all_grouped['Curtailment %'] = \
        df_all_grouped['Curtailment'] / df_all_grouped['Total Energy']
    return df_all_grouped


def redistribute_totals(df_all, df_all_grouped):
    # First, copy the percentage of corresponding to the zone
    df_all_redistrib = df_all.copy().reset_index()
    df_all_redistrib = df_all_redistrib.join(
        df_all_grouped['Curtailment %'], on=['Year', 'Month', 'Block', 'Zone'])
    # Then, redistribute the total energy
    df_all_redistrib['Redistributed Curtailment'] = \
        df_all_redistrib['Curtailment %'] * df_all_redistrib['Total Energy']
    # Set index back
    df_all_redistrib.set_index(
        ['Year', 'Month', 'Block', 'Gen', 'Node', 'Zone'], inplace=True)
    # Drop original curtailment % column
    df_all_redistrib.drop(columns=['Curtailment %'], inplace=True)
    # Calculate redistributed total energy
    df_all_redistrib['Redistributed Energy'] = \
        df_all_redistrib['Total Energy'] - \
        df_all_redistrib['Redistributed Curtailment']
    return df_all_redistrib


def group_data_redistrib(df_all_redistrib):
    # Group values by zone
    df_all_redistrib_grouped = df_all_redistrib.groupby(
        ['Year', 'Month', 'Block', 'Zone']).sum()
    # Calculate grouped values per zone
    df_all_redistrib_grouped['Redistributed Curtailment %'] = \
        df_all_redistrib_grouped['Redistributed Curtailment'] / \
        df_all_redistrib_grouped['Total Energy']
    return df_all_redistrib_grouped


def process_redistributed_out_ener(df_all_redistrib):
    df_out_ener_redistrib = df_all_redistrib.copy()
    # Add Hyd column
    df_out_ener_redistrib['Hyd'] = Hyd
    # Keep only Hyd, Year, Month, Block, Gen, Redistributed Energy
    df_out_ener_redistrib = df_out_ener_redistrib.reset_index()
    new_indexes = ['Hyd', 'Year', 'Month', 'Block', 'Gen',
                   'Redistributed Energy']
    df_out_ener_redistrib = df_out_ener_redistrib[new_indexes]
    # Unstack the data
    df_out_ener_redistrib = df_out_ener_redistrib.set_index(
        ['Hyd', 'Year', 'Month', 'Block', 'Gen'])
    df_out_ener_redistrib = df_out_ener_redistrib.unstack()
    df_out_ener_redistrib.columns = df_out_ener_redistrib.columns.droplevel()
    return df_out_ener_redistrib


def add_blank_lines(out_file, lines):
    with open(out_file, 'r') as original:
        data = original.read()
    with open(out_file, 'w') as modified:
        for i in range(lines):
            modified.write('\n')
        modified.write(data)


def main():
    print('--Starting curtailment script')
    # Load Data
    print('--Loading data from:')
    print(f'--CMG: {cmg_file}')
    print(f'--CUR: {cur_file}')
    print(f'--ENER: {ener_file}')
    df_cmg, df_cur, df_ener = load_data(cmg_file, cur_file, ener_file)
    dict_node2zone, dict_gen2node = load_dicts(zonas_file, gen2zone_file)

    # Validate inputs
    print('--Validating inputs')
    validate_inputs(df_cmg, df_cur, df_ener, dict_node2zone, dict_gen2node)

    # Process data
    print('--Processing data')
    df_all = process_inputs(df_cmg, df_cur, df_ener,
                            dict_node2zone, dict_gen2node)
    df_all_grouped = group_data(df_all)

    # Redistribute totals
    print('--Redistributing totals')
    df_all_redistrib = redistribute_totals(df_all, df_all_grouped)
    df_all_redistrib_grouped = group_data_redistrib(df_all_redistrib)
    df_out_ener_redistrib = process_redistributed_out_ener(
        df_all_redistrib)

    # Print results
    print('--Printing results to csv files')
    df_all.to_csv(cur_out_file)
    df_all_grouped.to_csv(cur_grouped_out_file)
    df_all_redistrib.to_csv(cur_redistrib_out_file)
    df_all_redistrib_grouped.to_csv(cur_redistrib_grouped_out_file)
    df_out_ener_redistrib.to_csv(out_ener_redistrib_out_file)

    # Add 2 blank lines at the beginning of outEnerg_B_redistrib.csv
    # to match format
    add_blank_lines(out_ener_redistrib_out_file, 3)

    print('--Finished curtailment script')


if __name__ == "__main__":
    main()
