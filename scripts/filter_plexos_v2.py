# -*- coding: utf-8 -*-
"""
Filter Plexos

Take plexos outputs and print equivalent PLP outputs,
to be used by the Curtailment Model
"""
import os
import pandas as pd
import datetime


# Define global variables
Hydro = 20
folder_paths = 'Folder_Paths.csv'

# Define directories
# wDir = os.getcwd()
wDir = r"C:\Users\BH5873\OneDrive - ENGIE\Bureau\BE Mar24 PLP"
pDir = os.path.join(wDir, "PLP")
if not os.path.exists(pDir):
    # Warn the user and stop
    print("PLP folder not found. Cannot proceed.")
    # Indicate the folder that should exist
    print("Please create the folder 'PLP' in the working directory.")
    print("The folder should be located at: ", pDir)
    exit()
oDir = os.path.join(wDir, "Output_test")
if not os.path.exists(oDir):
    os.mkdir(oDir)

# Define input files
folder_paths_file = os.path.join(wDir, 'Folder_Paths.csv')
config_file = os.path.join(wDir, 'filter_plexos_config.csv')

# Check existence of input files
if not os.path.exists(folder_paths_file):
    print("Folder Paths file not found. Cannot proceed.")
    print("Please create the file 'Folder_Paths.csv' "
          "in the working directory.")
    exit()
if not os.path.exists(config_file):
    print("Filter Plexos Config file not found. Cannot proceed.")
    print("Please create the file 'filter_plexos_config.csv' "
          "in the working directory.")
    exit()

# Read folder paths file with paths to Plexos results
fp = pd.read_csv(folder_paths_file)
NPaths = len(fp)
RPaths = fp.to_numpy()
Yini = RPaths[0, 1]
Mini = RPaths[0, 2]
Yend = RPaths[NPaths - 1, 3]
Mend = RPaths[NPaths - 1, 4]


# Read configuration from filter_plexos_config.json
filter_config = pd.read_csv(config_file)

Hours = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
         13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
Blocks = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6,
          7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12]

B2H = pd.DataFrame()
B2H['Hour'] = Hours
B2H['Block'] = Blocks


def print_in_plp_format(df, new_indexes, csv_out, rows_to_skip):
    # Format as in PLP (set index, unstack, reset_index, add blank lines)
    df = df.set_index(new_indexes)
    df = df.unstack()
    # Drop level
    df.columns = df.columns.droplevel()
    df = df.reset_index()
    df.to_csv(csv_out, index=False)
    add_blank_lines(csv_out, rows_to_skip)


def groupby_func(df, by, func):
    if func == "avg":
        return df.groupby(by=by, as_index=False).mean()
    elif func == "sum":
        return df.groupby(by=by, as_index=False).sum()


def add_blank_lines(out_file, lines):
    with open(out_file, 'r') as original:
        data = original.read()
    with open(out_file, 'w') as modified:
        for i in range(lines):
            modified.write('\n')
        modified.write(data)


def define_outdata(f):
    print("---Defining outData: ", f)
    outData = pd.read_csv(os.path.join(wDir, RPaths[0, 0], "Interval", f))
    for i in range(NPaths - 1):
        csv_path = os.path.join(wDir, RPaths[i + 1, 0], "Interval", f)
        df = pd.read_csv(csv_path)
        outData = pd.concat([outData, df], ignore_index=True)
    outData = outData.copy().fillna(0)
    outData["DATETIME"] = pd.to_datetime(
        outData["DATETIME"], format="mixed")
    outData.insert(1, "Year", outData["DATETIME"].dt.year)
    outData.insert(2, "Month", outData["DATETIME"].dt.month)
    outData.insert(3, "Day", outData["DATETIME"].dt.day)
    outData.insert(4, "Hour", outData["DATETIME"].dt.hour)
    outData.to_csv(os.path.join(oDir, f), index=False)
    return outData


def print_outdata_12B(outData, Item_Name, Value_Name, Group_By, File_12B,
                      PLP_Row):
    print("---Printing outData 12B: ", File_12B)
    outData_12B = outData.copy()
    outData_12B = pd.merge(outData_12B, B2H, on='Hour', how='right')
    outData_12B = outData_12B.drop(['DATETIME', 'Day', 'Hour'], axis=1)
    outData_12B = pd.melt(outData_12B, id_vars=['Year', 'Month', 'Block'],
                          var_name=Item_Name, value_name=Value_Name)
    outData_12B = groupby_func(
        outData_12B, by=['Year', 'Month', 'Block', Item_Name], func=Group_By)
    # Format as in PLP
    csv_out = os.path.join(oDir, File_12B)
    print_in_plp_format(
        outData_12B, ['Year', 'Month', 'Block', Item_Name], csv_out,
        PLP_Row)


def print_outdata_24H(outData, Item_Name, Value_Name, Group_By, File_24H,
                      PLP_Row):
    print("---Printing outData 24H: ", File_24H)
    outData_24H = outData.copy()
    outData_24H = outData_24H.drop(['DATETIME', 'Day'], axis=1)
    outData_24H = pd.melt(outData_24H, id_vars=['Year', 'Month', 'Hour'],
                          var_name=Item_Name, value_name=Value_Name)
    outData_24H = groupby_func(
        outData_24H, by=['Year', 'Month', 'Hour', Item_Name], func=Group_By)
    csv_out = os.path.join(oDir, File_24H)
    print_in_plp_format(
        outData_24H, ['Year', 'Month', 'Hour', Item_Name], csv_out,
        PLP_Row)


def print_outdata(outData, Item_Name, Value_Name, Group_By, File_M, PLP_Row):
    print("---Printing outData: ", File_M)
    outData = outData.drop(['DATETIME', 'Day', 'Hour'], axis=1)
    outData = pd.melt(outData, id_vars=['Year', 'Month'], var_name=Item_Name,
                      value_name=Value_Name)
    outData = groupby_func(
        outData, by=['Year', 'Month', Item_Name], func=Group_By)
    # Print in PLP format
    csv_out = os.path.join(oDir, File_M)
    print_in_plp_format(
        outData, ['Year', 'Month', Item_Name], csv_out, PLP_Row)
    return outData


def print_out_plp(outData, Item_Name, Value_Name, File_M, PLP_Row, PLP_Div):
    print("---Printing outPLP: ", File_M)
    csv_in = os.path.join(pDir, File_M)
    outPLP = pd.read_csv(csv_in, low_memory=False, skiprows=PLP_Row)
    # Filtrar por Hyd
    outPLP = outPLP.loc[outPLP['Hyd'] == Hydro]

    outPLP = pd.melt(outPLP, id_vars=['Hyd', 'Year', 'Month'],
                     var_name=Item_Name, value_name=Value_Name)

    # Drop rows that are not in the range of interest
    outPLP['Year'] = pd.to_numeric(outPLP['Year'])
    outPLP['Month'] = pd.to_numeric(outPLP['Month'])
    outPLP['DateTime'] = pd.to_datetime(
        outPLP[['Year', 'Month']].assign(DAY=1), format="mixed")
    mask_ini = (outPLP.DateTime < datetime.datetime(Yini, Mini, 1))
    mask_end = (outPLP.DateTime > datetime.datetime(Yend, Mend, 1))
    outPLP = outPLP.loc[mask_ini | mask_end]

    # Drop columns that are not in the range of interest
    outPLP = outPLP.drop(['DateTime'], axis=1)
    # Add Hydro index
    outData.insert(0, "Hyd", Hydro)
    # Adjust magnitude of values
    outData[Value_Name] = outData[Value_Name].transform(
        lambda x: x / PLP_Div)

    # Concatenate outData and outPLP
    outPLP = pd.concat([outPLP, outData], ignore_index=True)
    outPLP.set_index(['Hyd', 'Year', 'Month', Item_Name]).unstack()
    outPLP = outPLP.reset_index()
    outPLP['Hyd'] = pd.to_numeric(outPLP['Hyd'])
    outPLP['Year'] = pd.to_numeric(outPLP['Year'])
    outPLP['Month'] = pd.to_numeric(outPLP['Month'])
    outPLP = outPLP.sort_values(['Hyd', 'Year', 'Month'])
    # Format as in PLP (set index, unstack, reset_index, add blank lines)
    csv_out = os.path.join(oDir, File_M)
    print_in_plp_format(
        outPLP, ['Hyd', 'Year', 'Month', Item_Name], csv_out, PLP_Row)


def main():
    print("--Start script Filter Plexos")
    print("---General Inputs directory: ", wDir)
    print("---PLP Inputs directory: ", pDir)
    print("---Folder paths file: ", folder_paths_file)
    print("---Config file: ", config_file)
    print("---Number of paths: ", NPaths)
    print("---Output directory: ", oDir)

    # Node Price
    for idx, row in filter_config.iterrows():
        print("--Processing file %s/%s: %s" %
              (idx + 1, len(filter_config), row['Origin']))
        f = row['Origin']
        Item_Name = row['Item']
        Value_Name = row['Value']
        Group_By = row['GroupBy']
        File_24H = row['File_24H']
        File_12B = row['File_12B']
        File_M = row['File_M']
        PLP_Row = row['PLP_Row']
        PLP_Div = row['PLP_Div']

        # Define outdata
        outData = define_outdata(f)

        # Print outdata 12B
        print_outdata_12B(
            outData, Item_Name, Value_Name, Group_By, File_12B, PLP_Row)

        # Print outdata 24H
        print_outdata_24H(
            outData, Item_Name, Value_Name, Group_By, File_24H, PLP_Row)

        # Print outData
        outData = print_outdata(
            outData, Item_Name, Value_Name, Group_By, File_M, PLP_Row)

        # Print plp files
        if row['PLP_Bool']:
            print_out_plp(
                outData, Item_Name, Value_Name, File_M, PLP_Row, PLP_Div)

    print("--Filter Plexos script ready")


if __name__ == "__main__":
    main()
