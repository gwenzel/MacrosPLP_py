'''Generation

Module to store all processing and writing functions related to Generation data
'''
from pathlib import Path
import pandas as pd
import concurrent.futures


CEN_NAME = "plpcen.csv"
CHUNKSIZE = 100000

item2column_name = {
    "Energy": "CenEgen",
    "Revenue": "CenInyE",
    "Curtailment": "CurE"
}

item2unit = {
    "Energy": "[GWh]",
    "Revenue": "[MUSD]",
    "Curtailment": "[GWh]",
}

# Define data types for efficient loading
DTYPES = {
    "Hidro": "category",
    "CenNom": "category",
    "BarNom": "category",
    "CenTip": "category",
    "CenInyE": "float32",
    "CenEgen": "float32",
    "CurE": "float32",
    "Etapa": "int32"
}


def process_gen_data_optimized(path_case: Path,
                               blo_eta: pd.DataFrame) -> tuple[
                                   pd.DataFrame, pd.DataFrame]:
    '''
    Optimized function to read and process generation data for large files
    '''

    # Drop 'Block_Len' column from blo_eta
    blo_eta = blo_eta.drop(columns=["Block_Len"])

    gen_data_list = []

    print("Reading generation data, chunksize: %d" % CHUNKSIZE)

    # Read CSV with specified data types, by chunks
    for gen_data_c in pd.read_csv(path_case / CEN_NAME,
                                  chunksize=CHUNKSIZE,
                                  dtype=DTYPES,
                                  low_memory=False):

        # print("Processing chunk %d" % len(gen_data_list))

        # Remove 'MEDIA' rows
        gen_data_c = gen_data_c[gen_data_c["Hidro"] != "MEDIA"]

        # Rename 'Hidro' column to 'Hyd'
        gen_data_c = gen_data_c.rename(columns={"Hidro": "Hyd"})

        # Turn Hyd to numeric
        gen_data_c["Hyd"] = pd.to_numeric(gen_data_c["Hyd"])

        # Remove spaces from CenNom, BarNom
        gen_data_c["CenNom"] = gen_data_c["CenNom"].str.strip()
        gen_data_c["BarNom"] = gen_data_c["BarNom"].str.strip()

        # Keep only required columns
        gen_data_c = gen_data_c[
            ["Hyd", "CenNom", "BarNom", "CenTip", "CenInyE",
             "CenEgen", "CurE", "Etapa"]]

        # Convert and calculate necessary columns
        gen_data_c["CenInyE"] /= 1000

        # Merge with blo_eta
        gen_data_c = pd.merge(gen_data_c, blo_eta, on="Etapa", how="left")

        # Calculate and round columns
        gen_data_c["CenEgen"] = gen_data_c["CenEgen"].round(3)
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


def process_gen_data_h(gen_data: pd.DataFrame) -> pd.DataFrame:
    # Translate blocks to hours by extending each block into 2 hours
    # Data for block 1 is divided by 2 and repeated for hour 1 and 2, and so on
    # This is done to match the number of hours in the block data
    gen_data_h = gen_data.copy()
    # Filter Hyd 20
    gen_data_h = gen_data_h[gen_data_h["Hyd"] == 20]
    # Set index
    gen_data_h.set_index(["Hyd", "Year", "Month", "Block", "CenNom"],
                         inplace=True)
    # Sort by index
    gen_data_h.sort_index(inplace=True)
    # Repeat values for each index
    gen_data_h = gen_data_h.reindex(gen_data_h.index.repeat(2))
    # Define hour
    gen_data_h["Hour"] = gen_data_h.groupby(
        ["Hyd", "Year", "Month", "CenNom"]).cumcount() + 1
    # Replace Block index for Hour index
    gen_data_h.reset_index(inplace=True)
    gen_data_h.drop(columns=["Block"], inplace=True)
    gen_data_h.set_index(["Hyd", "Year", "Month", "Hour", "CenNom"],
                         inplace=True)
    # Sort again
    gen_data_h.sort_index(inplace=True)
    # Fill na with 0
    gen_data_h.fillna(0, inplace=True)
    # Divide values by 2
    gen_data_h["CenEgen"] = gen_data_h["CenEgen"] / 2.
    gen_data_h["CenInyE"] = gen_data_h["CenInyE"] / 2
    gen_data_h["CurE"] = gen_data_h["CurE"] / 2
    # Round values
    gen_data_h["CenEgen"] = gen_data_h["CenEgen"].round(3)
    gen_data_h["CenInyE"] = gen_data_h["CenInyE"].round(3)
    gen_data_h["CurE"] = gen_data_h["CurE"].round(3)

    gen_data_h.reset_index(inplace=True)

    return gen_data_h


def process_gen_data_m(gen_data: pd.DataFrame) -> pd.DataFrame:
    gen_data_m = gen_data.copy()
    # Group by and aggregate
    gen_data_m = gen_data_m.groupby(["Hyd", "Year", "Month", "CenNom"]).agg(
        CenEgen=("CenEgen", "sum"),
        CenInyE=("CenInyE", "sum"),
        CurE=("CurE", "sum")
    ).reset_index()

    # Round aggregated results
    gen_data_m["CenEgen"] = gen_data_m["CenEgen"].round(3)
    gen_data_m["CenInyE"] = gen_data_m["CenInyE"].round(3)
    gen_data_m["CurE"] = gen_data_m["CurE"].round(3)

    return gen_data_m


def process_gen_data(gen_data: pd.DataFrame,
                     resolution: str = "B",
                     column_name: str = "CenEgen") -> pd.DataFrame:
    '''
    Optimized function to process generation data to monthly and indexed
    by blocks or hours
    '''
    gen_data = gen_data.copy()
    # Define base headers and index based on resolution
    if resolution == "B":
        base_headers = ["Hyd", "Year", "Month", "Block", "CenNom"]
        index = ["Hyd", "Year", "Month", "Block"]
    elif resolution == "M":
        base_headers = ["Hyd", "Year", "Month", "CenNom"]
        index = ["Hyd", "Year", "Month"]
    elif resolution == "H":
        base_headers = ["Hyd", "Year", "Month", "Hour", "CenNom"]
        index = ["Hyd", "Year", "Month", "Hour"]
    else:
        raise ValueError("resolution must be 'B', 'H' or 'M'")

    if column_name not in ["CenEgen", "CenInyE", "CurE"]:
        raise ValueError("column_name must be in 'CenEgen', 'CenInyE', 'CurE'")

    # Using dictionary comprehension to create pivot tables for each column
    pivot_table = \
        gen_data[base_headers + [column_name]].pivot_table(
            index=index, columns="CenNom", values=column_name)

    return pivot_table


def write_gen_data_file(gen_param: pd.DataFrame, path_out: Path, item: str,
                        df: pd.DataFrame, resolution: str = "B"):
    '''
    Optimized function to write generation data
    '''
    # Validate inputs
    if item not in ["Energy", "Revenue", "Curtailment"]:
        raise ValueError("item must be in 'Energy', 'Revenue', "
                         "or 'Curtailment'")

    # Assuming gen_param is a DataFrame that has been defined earlier
    # in the code
    header_data = gen_param[["BarNom", "CenTip", "CenNom"]]

    if ((resolution == "B") or (resolution == "H")):
        head = pd.DataFrame(
            {
                "BarNom": ["", "", "", "Ubic:"],
                "CenTip": ["", "", "", "Comb:"],
                "CenNom": ["", "", "", "Firm:"],
            }
        )
        header = pd.concat([head, header_data], axis=0).transpose()
        suffix = "_%s" % resolution
    elif resolution == "M":
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
        raise ValueError("resolution must be B, H or M")

    filename = {
        "Energy": "outEnerg%s.csv" % suffix,
        "Revenue": "outReven%s.csv" % suffix,
        "Curtailment": "outCurtail%s.csv" % suffix,
    }

    header.iloc[0, 0] = item2unit[item]
    header.to_csv(path_out / filename[item], na_rep=0, index=False,
                  header=False)
    df.to_csv(path_out / filename[item], na_rep=0, header=True, mode="a")


def process_and_write_wrapper(path_out: Path,
                              gen_data: pd.DataFrame,
                              gen_param: pd.DataFrame,
                              item: str, resolution: str):
    '''
    Wrap generation, process and write
    '''
    if item not in ["Energy", "Revenue", "Curtailment"]:
        raise ValueError("item must be Energy, Revenue, or Curtailment")

    # Process data
    if resolution == "B":
        df = process_gen_data(gen_data, resolution, item2column_name[item])
    elif resolution == "M":
        gen_data_m = process_gen_data_m(gen_data)
        df = process_gen_data(gen_data_m, resolution, item2column_name[item])
    elif resolution == "H":
        gen_data_h = process_gen_data_h(gen_data)
        df = process_gen_data(gen_data_h, resolution, item2column_name[item])
    else:
        raise ValueError("resolution must be B, M or H")

    # Write generation data
    write_gen_data_file(gen_param, path_out, item, df, resolution)

    print("Generation data written for %s, %s" % (item, resolution))


def generation_converter(path_case: Path, path_out: Path,
                         blo_eta: pd.DataFrame):
    '''
    Optimized function to wrap generation read, process, and write
    '''
    # Read data
    gen_data, gen_param = process_gen_data_optimized(
        path_case, blo_eta)

    # Write data with multithreading
    list_of_args = [("Energy", "B"),
                    ("Energy", "M"),
                    ("Energy", "H"),
                    ("Revenue", "B"),
                    ("Revenue", "M"),
                    ("Revenue", "H"),
                    ("Curtailment", "B"),
                    ("Curtailment", "M"),
                    ("Curtailment", "H")]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for item, resolution in list_of_args:
            executor.submit(process_and_write_wrapper, path_out, gen_data,
                            gen_param, item, resolution)
