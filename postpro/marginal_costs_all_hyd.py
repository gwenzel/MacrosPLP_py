'''Marginal Costs

Module to store all functions related with marginal costs
'''
import pandas as pd
from pathlib import Path
import concurrent.futures


BAR_NAME = "plpbar.csv"
CHUNKSIZE = 100000

DTYPES = {
    "Hidro": "category",
    "BarNom": "category",
    "Etapa": "int32",
    "CMgBar": "float32",
    "DemBarE": "float32"
}


def read_plpbar_file(path_case: Path,
                     blo_eta: pd.DataFrame) -> tuple[
                     pd.DataFrame, pd.DataFrame]:
    '''
    Read and process marginal costs and demand data from plpbar file
    '''

    bar_data_list = []

    print("Reading marginal costs data, chunksize: %d" % CHUNKSIZE)

    for bar_data_c in pd.read_csv(path_case / BAR_NAME,
                                  chunksize=CHUNKSIZE,
                                  low_memory=False,
                                  dtype=DTYPES):

        # print("Processing chunk %d" % len(bar_data_list))

        # Remove spaces from BarNom
        bar_data_c["BarNom"] = bar_data_c["BarNom"].str.strip()

        # Filter out MEDIA
        bar_data_c = bar_data_c[bar_data_c["Hidro"] != "MEDIA"]
        # Hydro to numeric
        bar_data_c['Hidro'] = pd.to_numeric(bar_data_c['Hidro'])
        # Rename column
        bar_data_c = bar_data_c.rename(columns={"Hidro": "Hyd"})

        # Merge with blo_eta
        bar_data_c = pd.merge(bar_data_c, blo_eta, on="Etapa", how="left")
        bar_data_c = bar_data_c[
            ["Hyd", "Year", "Month", "Block", "Block_Len", "BarNom", "CMgBar",
             "DemBarE"]
        ]
        bar_data_c["CMgBar"] = bar_data_c["CMgBar"].round(3)
        bar_data_c["DemBarE"] = bar_data_c["DemBarE"].round(3)

        # Append to list
        bar_data_list.append(bar_data_c)

    # Concatenate all chunks data
    bar_data = pd.concat(bar_data_list, axis=0)
    # Sort
    bar_data = bar_data.sort_values(["Hyd", "Year", "Month",
                                     "Block", "BarNom"])
    # Get bar parameters
    bar_param = bar_data[["BarNom"]].drop_duplicates()

    return bar_data, bar_param


def bar_process(bar_data: pd.DataFrame, columns: list, indexes: list,
                values: str) -> pd.DataFrame:
    '''
    Bar process
    '''
    bar_data[values] = bar_data[values].round(3)
    bar_data = bar_data.reset_index(drop=False)
    bar_data.index = bar_data.index.astype('int32')
    return bar_data[columns].pivot_table(index=indexes, columns="BarNom",
                                         values=values)


def process_cmg_dem(bar_data: pd.DataFrame, resolution: str,
                    values: str) -> pd.DataFrame:
    '''
    Process CMg and Dem
    '''
    if resolution == 'B':
        bar_data_b = bar_data.copy()
        columns = ["Hyd", "Year", "Month", "Block", "BarNom"]
        indexes = ["Hyd", "Year", "Month", "Block"]
        return bar_process(bar_data_b, columns + [values], indexes,
                           values=values)
    elif resolution == 'H':
        bar_data_h = bar_data.copy()
        # Translate blocks to hours by extending each block into 2 hours
        # CMg data for block 1 is repeated for hour 1 and 2, and so on
        # Dem data for block 1 is divided by 2 and repeated for hour 1 and 2
        # This is done to match the number of hours in the block data
        # Filter Hyd 20
        # bar_data_h = bar_data_h[bar_data_h["Hyd"] == 20]
        # Set index
        bar_data_h.set_index(["Hyd", "Year", "Month", "Block", "BarNom"],
                             inplace=True)
        # Sort by index
        bar_data_h.sort_index(inplace=True)
        # Repeat values for each index
        bar_data_h = bar_data_h.reindex(bar_data_h.index.repeat(2))
        # Define hour
        bar_data_h["Hour"] = bar_data_h.groupby(
            ["Hyd", "Year", "Month", "BarNom"]).cumcount()
        # Replace Block index for Hour index
        bar_data_h.reset_index(inplace=True)
        bar_data_h.drop(columns=["Block"], inplace=True)
        bar_data_h.set_index(["Hyd", "Year", "Month", "Hour", "BarNom"],
                             inplace=True)
        # Sort again
        bar_data_h.sort_index(inplace=True)
        # Fill na with 0
        bar_data_h.fillna(0, inplace=True)
        # Reset index
        bar_data_h.reset_index(inplace=True)
        # Divide dem data, cmg data is the same
        bar_data_h["DemBarE"] = bar_data_h["DemBarE"] / 2
        # Select columns and indexes for bar_process
        columns = ["Hyd", "Year", "Month", "Hour", "BarNom"]
        indexes = ["Hyd", "Year", "Month", "Hour"]
        return bar_process(bar_data_h, columns + [values], indexes,
                           values=values)
    elif resolution == 'M':
        bar_data_m = bar_data.copy()
        # Group by using sum as aggregation, for CMg and Dem
        bar_data_m = \
            bar_data_m.groupby(["Hyd", "Year", "Month", "BarNom"]).agg(
                CMgBar=("CMgBar", "mean"), DemBarE=("DemBarE", "sum")
                )
        columns = ["Hyd", "Year", "Month", "BarNom"]
        indexes = ["Hyd", "Year", "Month"]
        return bar_process(bar_data_m, columns + [values], indexes,
                           values=values)
    else:
        raise ValueError("resolution must be B, H or M")


def write_marginal_costs_file(bar_param: pd.DataFrame, path_out: Path,
                              item: str, df: pd.DataFrame, type: str = 'B'):
    '''
    Write marginal costs data
    '''
    if type == "B":
        head = pd.DataFrame({"BarNom": ["", "", "", "Ubic:"]})
        header = pd.concat([head, bar_param]).T
        suffix = '_B'
    elif type == "H":
        head = pd.DataFrame({"BarNom": ["", "", "", "Ubic:"]})
        header = pd.concat([head, bar_param]).T
        suffix = '_H'
    elif type == "M":
        head = pd.DataFrame({"BarNom": ["", "", "Ubic:"]})
        header = pd.concat([head, bar_param]).T
        suffix = ''
    else:
        raise ValueError("type must be B, H or M")
    filename = {
        "CMg": "outBarCMg%s.csv" % suffix,
        "Dem": "outDemEne%s.csv" % suffix,
    }
    unit = {
        "CMg": "[USD/MWh]",
        "Dem": "[GWh]",
    }
    header.iloc[0, 0] = unit[item]
    header.to_csv(path_out / filename[item], na_rep=0, header=False,
                  index=False, mode="w")
    df.to_csv(path_out / filename[item], na_rep=0, header=True, mode="a")


def process_and_write_wrapper(bar_data: pd.DataFrame, resolution: str,
                              values: str, bar_param: pd.DataFrame,
                              path_out: Path, item: str):
    '''
    Group both process and write functions to multithread them
    '''
    df = process_cmg_dem(bar_data, resolution, values)
    write_marginal_costs_file(bar_param, path_out, item, df, resolution)

    print("Marginal costs written for %s, %s" % (item, resolution))


def marginal_costs_converter(path_case: Path, path_out: Path,
                             blo_eta: pd.DataFrame):
    '''
    Wrap marginal costs read, process and write
    '''
    # Read and process data
    bar_data, bar_param = read_plpbar_file(path_case, blo_eta)

    # Write files + multithreading
    list_of_args = [
        ('B', 'CMgBar', 'CMg'),
        ('B', 'DemBarE', 'Dem'),
        ('H', 'CMgBar', 'CMg'),
        ('H', 'DemBarE', 'Dem'),
        ('M', 'CMgBar', 'CMg'),
        ('M', 'DemBarE', 'Dem')
    ]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for resolution, values, item in list_of_args:
            executor.submit(process_and_write_wrapper, bar_data, resolution,
                            values, bar_param, path_out, item)
