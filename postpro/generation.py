'''Generation

Module to store all processing and writing functions related to Generation data
'''
from pathlib import Path
import pandas as pd


CEN_NAME = "plpcen.csv"
CHUNKSIZE = 1000000


def process_gen_data_optimized(path_case, blo_eta):
    '''
    Optimized function to read and process generation data for large files
    '''
    # Define data types for efficient loading
    dtypes = {
        "Hidro": "category",
        "CenNom": "category",
        "BarNom": "category",
        "CenTip": "category",
        "CenInyE": "float32",
        "CenEgen": "float32",
        "CurE": "float32",
        "Etapa": "int32"
    }

    # Drop 'Block_Len' column from blo_eta
    blo_eta = blo_eta.drop(columns=["Block_Len"])

    gen_data_list = []

    print("Reading generation data, chunksize: %d" % CHUNKSIZE)

    # Read CSV with specified data types, by chunks
    for gen_data_c in pd.read_csv(path_case / CEN_NAME,
                                  chunksize=CHUNKSIZE,
                                  dtype=dtypes,
                                  low_memory=False):

        print("Processing chunk %d" % len(gen_data_list))

        # Remove 'MEDIA' rows
        gen_data_c = gen_data_c[gen_data_c["Hidro"] != "MEDIA"]

        # Remove spaces from CenNom, BarNom
        gen_data_c["CenNom"] = gen_data_c["CenNom"].str.strip()
        gen_data_c["BarNom"] = gen_data_c["BarNom"].str.strip()

        # Keep only required columns
        gen_data_c = gen_data_c[
            ["Hidro", "CenNom", "BarNom", "CenTip", "CenInyE",
             "CenEgen", "CurE", "Etapa"]]

        # Rename 'Hidro' column to 'Hyd'
        gen_data_c = gen_data_c.rename(columns={"Hidro": "Hyd"})

        # Convert and calculate necessary columns
        gen_data_c["CenInyE"] /= 1000

        # Merge with blo_eta
        gen_data_c = pd.merge(gen_data_c, blo_eta, on="Etapa", how="left")

        # Calculate and round columns
        gen_data_c["CenEgen"] = gen_data_c["CenEgen"].round(3)

        gen_data_c["CenCMg"] = (
            1000 * gen_data_c["CenInyE"] *
            gen_data_c['Tasa'] /
            gen_data_c["CenEgen"]
            ).round(3)
        gen_data_c["CenInyE"] = (
            gen_data_c["CenInyE"] *
            gen_data_c['Tasa']
            ).round(3)
        gen_data_c["CurE"] = gen_data_c["CurE"].round(3)

        # Append to list
        gen_data_list.append(gen_data_c)

    # Concatenate all hyd data
    gen_data = pd.concat(gen_data_list, axis=0)

    # Sort values
    gen_data.sort_values(["Hyd", "Etapa", "CenNom"], inplace=True)

    # Drop Etapa column
    gen_data.drop(columns=["Etapa"], inplace=True)

    # Drop duplicates based on 'CenNom'
    gen_param = gen_data[
        ["CenNom", "BarNom", "CenTip"]].drop_duplicates(subset=["CenNom"])

    return gen_data, gen_param


def process_gen_data_m(gen_data):
    # Group by and aggregate
    gen_data_m = gen_data.groupby(["Hyd", "Year", "Month", "CenNom"]).agg(
        CenEgen=("CenEgen", "sum"),
        CenInyE=("CenInyE", "sum"),
        CurE=("CurE", "sum")
    ).reset_index()

    # Round aggregated results
    gen_data_m["CenEgen"] = gen_data_m["CenEgen"].round(3)
    gen_data_m["CenCMg"] = (
        1000 * gen_data_m["CenInyE"] / gen_data_m["CenEgen"]
        ).round(3)
    gen_data_m["CenInyE"] = gen_data_m["CenInyE"].round(3)
    gen_data_m["CurE"] = gen_data_m["CurE"].round(3)

    return gen_data_m


def process_gen_data_monthly(gen_data, type="B"):
    '''
    Optimized function to process generation data to monthly and indexed
    by blocks
    '''
    # Define base headers and index based on type
    if type == "B":
        base_headers = ["Hyd", "Year", "Month", "Block", "CenNom"]
        index = ["Hyd", "Year", "Month", "Block"]
    elif type == "M":
        base_headers = ["Hyd", "Year", "Month", "CenNom"]
        index = ["Hyd", "Year", "Month"]
    else:
        raise ValueError("type must be 'B' or 'M'")

    # Columns to pivot
    pivot_columns = ["CenEgen", "CenInyE", "CenCMg", "CurE"]

    # Using dictionary comprehension to create pivot tables for each column
    pivot_tables = {
        col: gen_data[base_headers + [col]].pivot_table(
            index=index, columns="CenNom", values=col
        ) for col in pivot_columns
    }

    return (pivot_tables["CenEgen"], pivot_tables["CenInyE"],
            pivot_tables["CenCMg"], pivot_tables["CurE"])


def write_gen_data_file(gen_param, path_out, item, df, type="B"):
    '''
    Optimized function to write generation data
    '''
    # Validate inputs
    if item not in ["Energy", "Revenue", "Cap Price", "Curtailment"]:
        raise ValueError("item must be in 'Energy', 'Revenue', 'Cap Price', "
                         "or 'Curtailment'")

    # Assuming gen_param is a DataFrame that has been defined earlier
    # in the code
    header_data = gen_param[["BarNom", "CenTip", "CenNom"]]

    if type == "B":
        head = pd.DataFrame(
            {
                "BarNom": ["", "", "", "Ubic:"],
                "CenTip": ["", "", "", "Comb:"],
                "CenNom": ["", "", "", "Firm:"],
            }
        )
        header = pd.concat([head, header_data], axis=0).transpose()
        suffix = "_B"
    elif type == "M":
        head = pd.DataFrame(
            {
                "BarNom": ["", "", "Ubic:"],
                "CenTip": ["", "", "Comb:"],
                "CenNom": ["", "", "Firm:"],
            }
        )
        header = pd.concat([head, header_data], axis=0).transpose()
        suffix = ""
    else:
        raise ValueError("type must be B or M")

    if item not in ["Energy", "Revenue", "Cap Price", "Curtailment"]:
        raise ValueError("item must be in Energy, Revenue, Cap Price"
                         " or Curtailment")

    filename = {
        "Energy": "outEnerg%s.csv" % suffix,
        "Revenue": "outReven%s.csv" % suffix,
        "Cap Price": "outCapPrice%s.csv" % suffix,
        "Curtailment": "outCurtail%s.csv" % suffix,
    }

    unit = {
        "Energy": "[GWh]",
        "Revenue": "[MUSD]",
        "Cap Price": "[USD/MWh]",
        "Curtailment": "[GWh]",
    }

    header.iloc[0, 0] = unit[item]
    header.to_csv(path_out / filename[item], na_rep=0, index=False,
                  header=False)
    df.to_csv(path_out / filename[item], na_rep=0, header=True, mode="a")


def generation_converter(path_case, path_out, blo_eta):
    '''
    Optimized function to wrap generation read, process, and write
    '''
    # Read data
    gen_data, gen_param = process_gen_data_optimized(
        path_case, blo_eta)
    gen_data_m = process_gen_data_m(gen_data)
    data_by_type = {
        "B": process_gen_data_monthly(gen_data, type="B"),
        "M": process_gen_data_monthly(gen_data_m, type="M")
    }

    # Clean up large data frames to free memory
    del gen_data, gen_data_m

    # Define items to be processed
    items = ["Energy", "Revenue", "Cap Price", "Curtailment"]

    # Write generation data for both types and all items
    for type_key, data_tuple in data_by_type.items():
        for item, data in zip(items, data_tuple):
            write_gen_data_file(
                gen_param, path_out, item, data, type=type_key)
